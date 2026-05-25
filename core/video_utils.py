"""Video utilities shared by detector / overlay / upload handler.

The recurring problem: dashcam mp4 files often ship with HEVC video, exotic
audio, or unusual fragmentation that Chromium/Firefox refuse to play inline
via <video> tags. OpenCV reads them fine, so analysis works — but the
upload preview and the annotated output both stay blank.

`normalize_for_browser()` re-encodes any input to H.264 / yuv420p mp4 with
+faststart, which is the lowest-common-denominator format every browser plays.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

_NORM_PREFIX = "dc_norm_"


def find_ffmpeg() -> str | None:
    """Prefer the bundled imageio-ffmpeg binary; fall back to system PATH."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def normalize_for_browser(src_path: str) -> str:
    """Re-encode `src_path` to a browser-playable mp4 in the temp directory.

    Returns the new path. If we can't transcode (no ffmpeg), returns the
    original — analysis still works, just no preview. If the input is already
    a normalized file (filename starts with `dc_norm_`), returns it as-is.
    """
    if not src_path or not os.path.exists(src_path):
        return src_path

    base = os.path.basename(src_path)
    if base.startswith(_NORM_PREFIX):
        return src_path  # already normalized

    # Force .mp4 extension on the output so the browser sniffs it correctly.
    stem = os.path.splitext(base)[0]
    out_name = f"{_NORM_PREFIX}{stem}.mp4"
    out_path = os.path.join(tempfile.gettempdir(), out_name)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path  # cached from a prior upload of the same file

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        return src_path  # no transcoder available — return original

    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", src_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-an",  # drop audio — dashcam audio tracks are a common source of inline-playback failure
        out_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Transcoding failed — return original. The user will still see the
        # red toast for the upload preview, but Analyze Drive will still work.
        return src_path

    return out_path
