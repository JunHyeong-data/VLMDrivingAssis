"""Object detection interface.

REPLACEMENT POINT (이지원):
  Set USE_REAL_YOLO=1 to use trained weights.
  YOLO_MODEL env var selects which model (default: yolo26n_best.pt).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterator

import cv2

from core.schema import Detection, FrameDetections, CLASS_NAMES
from mock_data import mock_detect

# ── Real YOLO model (lazy-loaded once) ──────────────────
_model = None
_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"

# Available models: yolo26n_best.pt, yolo26s_best.pt, rtdert_best.pt
_DEFAULT_MODEL = "yolo26n_best.pt"


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


def detect_video(
    video_path: str,
    sample_every: int = 1,
    progress: Callable[[float, str], None] | None = None,
) -> list[FrameDetections]:
    """Run detection over every Nth frame."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    use_real = os.environ.get("USE_REAL_YOLO") == "1"
    results: list[FrameDetections] = []

    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % sample_every == 0:
            if use_real:
                det = _detect_real_frame(frame, frame_idx, fps, width, height)
            else:
                det = mock_detect(frame_idx, fps, width, height)
            results.append(det)
            if progress and total > 0:
                progress(frame_idx / total, f"Frame {frame_idx:,} / {total:,}")
        frame_idx += 1

    cap.release()
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
    """Run YOLO26n / YOLO26s / RT-DETR on a single BGR frame."""
    model = _load_model()
    results = model(frame, verbose=False)[0]

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
        ))

    return FrameDetections(
        frame_idx=frame_idx,
        timestamp=frame_idx / fps,
        width=width,
        height=height,
        detections=dets,
    )