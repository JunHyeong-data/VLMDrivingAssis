"""Object detection interface.

REPLACEMENT POINT (이지원):
  Real YOLO auto-enables when a weights file exists under ./weights/.
  Override with USE_REAL_YOLO=0 (force mock) or YOLO_MODEL=<filename>.

Uses ByteTrack (model.track) for persistent track IDs across frames — the event
rules need trajectories. Real tracking needs: `pip install ultralytics lap`
(ultralytics will otherwise auto-download `lap` on first run).
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Callable, Iterator

import cv2

from core.schema import Detection, FrameDetections, CLASS_NAMES
from mock_data import mock_detect

# ── Real YOLO model (lazy-loaded once) ──────────────────
_model = None
_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"

# Production model: yolo26n_best.pt (nano — fast, small, team-selected).
# Also available for comparison/ablation:
#   yolo26s_best.pt (small), yolo26l_best.pt (large), rtdert_best.pt (RT-DETR baseline)
# Switch via env: YOLO_MODEL=rtdert_best.pt
_DEFAULT_MODEL = "yolo26s_best.pt"

# Memoize the backend decision so the import check and the one-time warning
# only happen once per process.
_use_real_cached: bool | None = None


def _resolve_use_real() -> bool:
    """Pick the detection backend.

    Explicit USE_REAL_YOLO env wins. Otherwise auto-enable real YOLO when
    the selected weights file is present — so `python app.py` Just Works
    after weights land, without anyone having to remember the env var.

    If real YOLO is requested but `ultralytics` isn't importable, falls
    back to mock with a one-time warning instead of letting the pipeline
    crash mid-analysis. This keeps the UI demoable on machines that have
    weights checked in but didn't `pip install -r requirements.txt`.
    """
    global _use_real_cached
    if _use_real_cached is not None:
        return _use_real_cached

    env = os.environ.get("USE_REAL_YOLO")
    if env is not None:
        requested = (env == "1")
    else:
        model_name = os.environ.get("YOLO_MODEL", _DEFAULT_MODEL)
        requested = (_WEIGHTS_DIR / model_name).exists()

    if requested and importlib.util.find_spec("ultralytics") is None:
        print("[detector] ultralytics not installed — falling back to mock "
              "detector. To enable real YOLO: `pip install ultralytics`, or "
              "set USE_REAL_YOLO=0 to silence this and keep mock.")
        _use_real_cached = False
        return False

    _use_real_cached = requested
    return requested


def _load_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        model_name = os.environ.get("YOLO_MODEL", _DEFAULT_MODEL)
        weight_path = _WEIGHTS_DIR / model_name
        if not weight_path.exists():
            raise FileNotFoundError(f"Weight file not found: {weight_path}")
        _model = YOLO(str(weight_path))
    return _model


def _reset_tracker() -> None:
    """Clear ByteTrack state so each video starts with fresh track IDs.

    The YOLO model is a process-wide singleton, so without this the tracker
    would carry IDs over from a previously analyzed video.
    """
    if _model is None:
        return
    predictor = getattr(_model, "predictor", None)
    trackers = getattr(predictor, "trackers", None) if predictor is not None else None
    if trackers:
        for t in trackers:
            t.reset()


def detect_video_stream(
    video_path: str,
    sample_every: int = 1,
) -> Iterator[tuple[int, int, FrameDetections, list[FrameDetections]]]:
    """Generator variant of detect_video for live-progress UIs.

    Yields `(frame_idx, total_frames, latest_det, results_so_far)` after each
    processed frame, so a caller can render real progress (frame count, per-
    frame detections) as detection runs. `results_so_far` is the same list
    object across yields; once the generator is exhausted it holds the
    complete detection list — identical to what detect_video returns.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    results: list[FrameDetections] = []

    # Fresh track IDs for this video (model is a singleton; tracker state persists).
    if _resolve_use_real():
        _reset_tracker()

    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % sample_every == 0:
                # Resolve per-frame so a mid-run YOLO failure that flips
                # _use_real_cached to False immediately switches to mock.
                if _resolve_use_real():
                    det = _detect_real_frame(frame, frame_idx, fps, width, height)
                else:
                    det = mock_detect(frame_idx, fps, width, height)
                results.append(det)
                yield frame_idx, total, det, results
            frame_idx += 1
    finally:
        cap.release()


def detect_video(
    video_path: str,
    sample_every: int = 1,
    progress: Callable[[float, str], None] | None = None,
) -> list[FrameDetections]:
    """Run detection over every Nth frame. Returns the full FrameDetections list.

    Thin wrapper over detect_video_stream for non-streaming callers (smoke
    test, batch use). The streaming generator owns the detection loop.
    """
    results: list[FrameDetections] = []
    for frame_idx, total, _det, results in detect_video_stream(video_path, sample_every):
        if progress and total > 0:
            progress(frame_idx / total, f"Frame {frame_idx:,} / {total:,}")
    return results


def iter_video_frames(video_path: str) -> Iterator[tuple[int, float, "cv2.typing.MatLike"]]:
    """Yield (frame_idx, timestamp, BGR frame) for every frame."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        yield idx, idx / fps, frame
        idx += 1
    cap.release()


# ── Class name mapping (safety net) ─────────────────────
_CLS_MAP = {
    "bicycle": "bike",
    "motorcycle": "motor",
}


def _detect_real_frame(frame, frame_idx: int, fps: float, width: int, height: int) -> FrameDetections:
    """Run YOLO26n / YOLO26s / RT-DETR on a single BGR frame.

    If model loading or inference fails for any reason (missing dep, corrupt
    weights, CUDA error, etc.), we flip the global backend cache to mock
    and return a mock detection — so the next frame onward stays on mock
    and the demo doesn't crash mid-analysis.
    """
    global _use_real_cached
    try:
        model = _load_model()
        # track() (ByteTrack) gives persistent IDs across frames; persist=True
        # keeps tracker state between these per-frame calls within one video.
        results = model.track(frame, persist=True, verbose=False)[0]
    except Exception as e:
        print(f"[detector] real YOLO failed ({type(e).__name__}: {e}) — "
              f"switching to mock for the rest of this session.")
        _use_real_cached = False
        return mock_detect(frame_idx, fps, width, height)

    dets: list[Detection] = []
    for box in results.boxes:
        raw_name = results.names[int(box.cls)]
        cls_name = _CLS_MAP.get(raw_name, raw_name)
        if cls_name not in CLASS_NAMES:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        dets.append(Detection(
            cls=cls_name,
            bbox=(int(x1), int(y1), int(x2), int(y2)),
            confidence=float(box.conf),
            track_id=int(box.id.item()) if box.id is not None else None,
        ))

    return FrameDetections(
        frame_idx=frame_idx,
        timestamp=frame_idx / fps,
        width=width,
        height=height,
        detections=dets,
    )