"""Render the analyzed video: bounding boxes + Tesla-style HUD bar + risk flashes.

Browser playback note:
    OpenCV's default mp4v fourcc encodes MPEG-4 Part 2, which Chrome/Brave
    refuse to play inline. We write a raw mp4 with mp4v, then transcode to
    H.264 / yuv420p via imageio-ffmpeg so the browser can stream it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.schema import Event, FrameDetections
from core.video_utils import find_ffmpeg


# ─── Korean text support ──────────────────────────────────────
# cv2.putText only renders ASCII. For Korean event titles we
# overlay text via PIL + a Korean-capable TrueType font.

_KOREAN_FONT_CANDIDATES = [
    # Windows — Malgun Gothic is shipped with Win10/11
    r"C:\Windows\Fonts\malgunbd.ttf",
    r"C:\Windows\Fonts\malgun.ttf",
    # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    # Linux (commonly installed Korean fonts)
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


@lru_cache(maxsize=8)
def _ko_font(size: int) -> ImageFont.ImageFont:
    """Return a Korean-capable PIL font at `size` px. Cached because PIL
    font loading is expensive (~1ms) and we'd otherwise reload it per frame."""
    for path in _KOREAN_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    # Last resort — bitmap default font (no Korean glyphs, but won't crash)
    return ImageFont.load_default()


def _put_text_ko(frame: np.ndarray, text: str, pos: tuple[int, int],
                 size: int = 24, color_bgr: tuple[int, int, int] = (255, 255, 255),
                 ) -> None:
    """Draw `text` onto a BGR OpenCV frame using PIL. Mutates `frame` in-place.
    `color_bgr` is in OpenCV's BGR order so it matches the rest of this file."""
    # OpenCV stores BGR; PIL expects RGB
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img)
    ImageDraw.Draw(pil).text(
        pos, text, font=_ko_font(size),
        fill=(color_bgr[2], color_bgr[1], color_bgr[0]),
    )
    frame[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


# Class-color mapping (BGR, OpenCV order)
_CLASS_COLOR = {
    "car":           (255, 200, 80),    # cyan-ish
    "truck":         (180, 140, 255),   # purple
    "bus":           (100, 180, 255),   # orange-ish
    "person":        (110, 230, 110),   # green
    "rider":         ( 80, 200, 255),
    "bike":          (255, 255, 120),
    "motor":         (200, 120, 255),
    "traffic light": (120, 220, 255),
    "traffic sign":  (160, 160, 255),
}

_SEVERITY_BGR = {
    "safe":    ( 86, 174,  91),   # #5BAE5B-ish, BGR
    "caution": ( 32, 170, 230),   # amber
    "danger":  ( 67,  86, 220),   # coral red
}


def render_annotated_video(
    src_path: str,
    dst_path: str,
    detections_by_frame: dict[int, FrameDetections],
    events_by_frame: dict[int, Event],
) -> str:
    """Write a new video with overlays. Returns the browser-playable mp4 path."""
    cap = cv2.VideoCapture(src_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {src_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)

    # Stage 1: write raw overlay video via OpenCV (mp4v — fast, not browser-playable)
    raw_path = dst_path + ".raw.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(raw_path, fourcc, fps, (w, h))

    idx = 0
    last_det: FrameDetections | None = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # Use closest available detection (sample_every may skip frames)
        det = detections_by_frame.get(idx, last_det)
        last_det = det or last_det

        if det:
            _draw_boxes(frame, det)
            _draw_hud_bar(frame, det, idx, total)

        if idx in events_by_frame:
            _flash_alert(frame, events_by_frame[idx])

        writer.write(frame)
        idx += 1

    cap.release()
    writer.release()

    # Stage 2: transcode to H.264 + yuv420p so <video> tag plays it
    _transcode_to_browser_mp4(raw_path, dst_path, fps)
    try:
        os.remove(raw_path)
    except OSError:
        pass
    return dst_path


def _transcode_to_browser_mp4(src: str, dst: str, fps: float) -> None:
    """H.264 / yuv420p / +faststart — required for Chrome/Brave inline playback."""
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        # Fallback: just copy. Browser will likely still refuse, but app won't crash.
        shutil.copyfile(src, dst)
        return

    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", src,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",          # required by Safari and many players
        "-preset", "veryfast",
        "-crf", "23",
        "-movflags", "+faststart",      # let browser start playback before full DL
        "-r", f"{fps:.3f}",
        dst,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Surface ffmpeg stderr so the UI can show something useful
        msg = e.stderr.decode(errors="replace") if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg transcode failed: {msg}") from e


def _draw_boxes(frame: np.ndarray, det: FrameDetections) -> None:
    for d in det.detections:
        x1, y1, x2, y2 = d.bbox
        color = _CLASS_COLOR.get(d.cls, (200, 200, 200))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{d.cls} {d.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 8, y1), color, -1)
        cv2.putText(frame, label, (x1 + 4, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 15, 15), 1, cv2.LINE_AA)


def _draw_hud_bar(frame: np.ndarray, det: FrameDetections, idx: int, total: int) -> None:
    """Bottom HUD strip: detection counts + frame progress."""
    h, w = frame.shape[:2]
    bar_h = 44

    # Semi-transparent black strip
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # Left side: class counts
    counts: dict[str, int] = {}
    for d in det.detections:
        counts[d.cls] = counts.get(d.cls, 0) + 1
    left_parts = []
    for cls in ("car", "person", "traffic light", "truck"):
        if cls in counts:
            left_parts.append(f"{cls}: {counts[cls]}")
    left_text = "  |  ".join(left_parts) if left_parts else "no detections"
    cv2.putText(frame, left_text, (16, h - bar_h // 2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    # Right side: frame counter
    right_text = f"Frame {idx:,} / {total:,}" if total else f"Frame {idx:,}"
    (tw, _), _ = cv2.getTextSize(right_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.putText(frame, right_text, (w - tw - 16, h - bar_h // 2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 220, 200), 1, cv2.LINE_AA)

    # Brand mark
    cv2.putText(frame, "DriveCoach AI", (w // 2 - 70, h - bar_h + 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 200, 180), 1, cv2.LINE_AA)


def _flash_alert(frame: np.ndarray, ev: Event) -> None:
    """Pulse border + top-strip text when an event fires on this frame.

    The title is Korean — drawn via PIL because cv2.putText only renders
    ASCII and would otherwise show '?' boxes for every hangul character.
    """
    h, w = frame.shape[:2]
    color = _SEVERITY_BGR.get(ev.severity, (255, 255, 255))

    # Thick colored border around the frame
    thickness = 8
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, thickness)

    # Top alert strip
    strip_h = 44
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, strip_h), color, -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Korean-capable text rendering — PIL handles hangul, cv2 doesn't.
    _put_text_ko(
        frame,
        f"⚠  {ev.title}",
        pos=(16, 8),
        size=24,
        color_bgr=(255, 255, 255),
    )
