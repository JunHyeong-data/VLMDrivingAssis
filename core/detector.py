"""Object detection interface.

REPLACEMENT POINT (이지원):
  When YOLO26n / RT-DETR weights are ready, set USE_REAL_YOLO=1 and
  implement `_detect_real_frame()` below. Everything downstream — event
  extraction, VLM, scoring, UI — uses the FrameDetections schema, so no
  other code needs to change.
"""
from __future__ import annotations

import os
from typing import Callable, Iterator

import cv2

from core.schema import FrameDetections
from mock_data import mock_detect


def detect_video(
    video_path: str,
    sample_every: int = 1,
    progress: Callable[[float, str], None] | None = None,
) -> list[FrameDetections]:
    """Run detection over every Nth frame.

    Args:
        video_path: path to input video
        sample_every: process 1 of every N frames (1 = all frames)
        progress: optional callback(fraction 0..1, status string)

    Returns:
        List of FrameDetections, in chronological order.
    """
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
    """Yield (frame_idx, timestamp, BGR frame) for every frame in the video."""
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


def _detect_real_frame(frame, frame_idx: int, fps: float, width: int, height: int) -> FrameDetections:
    """REPLACE ME — call YOLO26n / RT-DETR on `frame` (BGR numpy array).

    Expected return: FrameDetections with Detection entries.
    Class names must match core.schema.CLASS_NAMES.
    """
    raise NotImplementedError(
        "Real YOLO inference not wired up yet. Set USE_REAL_YOLO=0 to use mock data, "
        "or implement core.detector._detect_real_frame()."
    )
