"""Smoke test the core pipeline end-to-end against a synthetic video.

Run:
    python scripts/smoke_pipeline.py

Generates a 5-second 1280x720 dummy mp4, runs detect → events → VLM → score,
and prints a summary. Verifies all data contracts hold up.
"""
import io
import os
import sys
import tempfile

# Make project root importable when invoked as `python scripts/smoke_pipeline.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows cp949 console can't render Korean / emoji — force UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import cv2
import numpy as np

from core.detector import detect_video
from core.event_extractor import extract_events
from core.overlay import render_annotated_video
from core.scorer import calculate_score
from core.vlm import generate_coaching


def make_dummy_video(path: str, seconds: int = 5, fps: int = 30, w: int = 1280, h: int = 720) -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
    for i in range(seconds * fps):
        # Gradient sky → road backdrop with a moving horizon
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        # sky
        for y in range(h // 2):
            shade = int(40 + (y / (h // 2)) * 30)
            frame[y, :] = (shade + 20, shade + 5, shade - 5)
        # road
        frame[h // 2:, :] = (35, 35, 40)
        # center lane stripes
        for x in range(0, w, 80):
            cv2.line(frame, (x + (i * 4) % 80, h - 80), (x + 40 + (i * 4) % 80, h - 80),
                     (200, 200, 200), 3)
        writer.write(frame)
    writer.release()


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="drivecoach_smoke_")
    src = os.path.join(tmp, "dummy.mp4")
    print(f"[1/5] generating dummy video → {src}")
    make_dummy_video(src)

    print("[2/5] running detector (mock)…")
    frames = detect_video(src, sample_every=2)
    print(f"      got {len(frames)} frames, {sum(len(f.detections) for f in frames)} detections")

    print("[3/5] extracting events…")
    events = extract_events(frames)
    print(f"      {len(events)} events:")
    for ev in events:
        print(f"        - t={ev.timestamp:5.2f}s [{ev.severity:7s}] {ev.title}")

    print("[4/5] running VLM coaching (mock)…")
    coachings = [generate_coaching(ev) for ev in events]
    print(f"      {len(coachings)} coaching responses generated")

    print("[5/5] scoring + rendering annotated video…")
    score = calculate_score(events)
    print(f"      total = {score.total}/100  grade = {score.grade}")
    for c in score.categories:
        print(f"        {c.icon} {c.name_ko:<12s} {c.score:>3d}")
    if score.focus_area:
        print(f"      📌 focus area: {score.focus_area.name_ko}")

    out = os.path.join(tmp, "annotated.mp4")
    det_by_idx = {f.frame_idx: f for f in frames}
    ev_by_idx = {ev.frame_idx: ev for ev in events}
    render_annotated_video(src, out, det_by_idx, ev_by_idx)
    size = os.path.getsize(out)
    print(f"      annotated video: {out} ({size/1024:.0f} KB)")

    print("\nOK  pipeline smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
