# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app (Gradio UI at http://127.0.0.1:7865).
# YOLO auto-enables when ./weights/*.pt exist and ultralytics is installed.
python app.py                 # real YOLO (if available) + mock VLM
USE_REAL_VLM=1 python app.py  # + real Qwen2.5-VL coaching

# Windows launchers (pin Python 3.13, where the heavy deps live):
#   run.bat       — real YOLO + mock VLM (team default)
#   run_full.bat  — real YOLO + real VLM (sets USE_REAL_VLM=1, YOLO_MODEL=yolo26s_best.pt)

# End-to-end pipeline smoke test (synthetic video through all 5 stages)
python scripts/smoke_pipeline.py

# Base deps (mock mode). Real inference also needs, installed separately:
#   pip install ultralytics lap                                    # YOLO + ByteTrack
#   pip install transformers accelerate bitsandbytes qwen-vl-utils # VLM
#   torch built with CUDA (e.g. a cu126 wheel)
pip install -r requirements.txt
```

## Architecture

### App state machine
`app.py` is a 4-state Gradio app: **IDLE → UPLOADED → ANALYZING → RESULTS**. Each state is a `gr.Group` toggled by visibility. State transitions are driven by:
- `file_in.upload` → `on_file_uploaded()` (IDLE → UPLOADED)
- `analyze_btn.click` → `go_analyzing()` then `run_analysis()` then `go_results()` (UPLOADED → ANALYZING → RESULTS)
- `home_btn` / `back_btn` / `new_analysis_btn` → `go_idle()` (any → IDLE)

Each non-IDLE screen is rendered as **one self-contained HTML blob** (e.g. `ready_screen_html()`, `analyzing_screen_html()`, `results_screen_html()`) returned into a single `gr.HTML` component. This is intentional — using `gr.Row`/`gr.Column` for layout caused Gradio's flex containers to break the custom CSS grids.

### Core pipeline (`run_analysis`)
```
detect_video() → extract_events() → generate_coaching() → calculate_score() → render_annotated_video()
```
All pipeline modules exchange data through the dataclasses defined in `core/schema.py` — this is the team's shared interface contract. Do not rename fields without team coordination.

### Mock vs real models
Both real backends are implemented and gated by env vars:
- `USE_REAL_YOLO` — unset: auto-enable real YOLO when the selected weights file exists under `./weights/` and `ultralytics` is importable; `=1` forces on; `=0` forces mock. See `core/detector._resolve_use_real()`.
- `USE_REAL_VLM=1` → real Qwen2.5-VL coaching (`core/vlm._generate_real_coaching()`); default uses canned coaching from `mock_data.py`.

`mock_data.py` is deterministic and now carries `track_id`s, so the trajectory-based rules still work in mock mode.

### Real model integration
- `core/detector.py` — YOLO (default `yolo26s_best.pt`; switch via `YOLO_MODEL`, e.g. `rtdert_best.pt`). Uses `model.track(persist=True)` (**ByteTrack**) for persistent IDs across frames and fills `Detection.track_id`; `_reset_tracker()` clears state per video. Maps detector names to `core.schema.CLASS_NAMES` (9 classes). Needs `ultralytics` + `lap`. On any inference error it switches to mock for the rest of the session (keeps the demo alive).
- `core/vlm.py` — Qwen2.5-VL-7B-Instruct, 4-bit NF4 (~6.5 GB VRAM). `max_pixels` caps vision tokens so it fits in 8 GB (without it, activations spill to shared memory → ~115 s/call instead of ~25 s). The prompt is grounded with the event's `title`/`summary` + frame object counts and an "image overrides text" safeguard; output passes through `_sanitize()` to drop occasional broken bytes (U+FFFD) from 4-bit decoding. Returns `Coaching(scene_description, scene_analysis, action_plan)`.

### JS ↔ Gradio bridge (`DC_BOOT_JS`)
The visible custom `<button>` elements inside the HTML blobs cannot trigger Gradio events directly. `DC_BOOT_JS` (defined at the top of `app.py`) bridges them to hidden `gr.Button` instances via class selectors:
- `#ready-back-btn` → `.dc-ready-back-hit`
- `#ready-go-btn` → `.dc-ready-go-hit`
- `#results-again-btn` → `.dc-results-again-hit`
- `.dc-v3-root .brand` → `.dc-home-hit`

`bootDC()` is called on mount and re-called via `MutationObserver` after every Gradio DOM re-render, because Gradio replaces DOM nodes on state changes.

### CSS scoping
All styles from `ui/theme.py` (`CUSTOM_CSS`) are scoped under `.dc-v3-root`. The IDLE landing page, Ready, Analyzing, and Results screens each root their HTML in `<div class="dc-v3-root ...">`. Styles outside this class are Gradio's own.

### Video handling
Dashcam files are often HEVC or fragmented MP4 that browsers refuse to play. `core/video_utils.normalize_for_browser()` re-encodes any upload to H.264 / yuv420p / `+faststart` via `imageio-ffmpeg` (bundled) or system `ffmpeg`. The `render_annotated_video()` function does the same two-stage process: write raw frames with OpenCV (mp4v), then transcode to H.264.

Korean text on video frames is rendered via PIL (`_put_text_ko` in `core/overlay.py`) because `cv2.putText` only supports ASCII.

### Event extraction (`core/event_extractor.py`)
Trajectory-based rules over tracked detections pick the moments worth coaching (top 3 per clip). Five event types: `close_vehicle` (앞차 근접/급접근, via per-track **looming** = bbox growth rate), `cut_in` (옆차 끼어들기 — a track's center crossing from the side into the ego lane), `pedestrian_risk` (보행자 근접/횡단), `signal_change` (신호 교차로 접근 — gated on the light bbox being large/near, since lights are visible ~⅔ of city driving), `complex_scene` (혼잡 — dynamic-agent count, excludes static signs/lights).

Tuning knobs are named constants at the top. Key design points:
- `_Episode` is **time-based** (persist/clear/cooldown in *seconds* via frame timestamps), so results are independent of `sample_every` — the app detects at `sample_every=2`, and frame-counted thresholds were silently dropping brief events. Per-type timing lives in `_EPISODE_CFG`.
- Rate signals (looming, cut-in, crossing direction) transfer across cameras; absolute thresholds (areas, counts, light height) are a **profile calibrated on a real Korean dashcam clip** — re-tune for a very different camera/FOV.
- Selection: `_suppress_neighbors()` (temporal NMS, one event per ~6 s) → `_cap_events()` (type-diversity first, then severity/penalty, `_MAX_EVENTS = 3`).
- What we deliberately do NOT claim (no IMU/lane/speed/light-color): 급제동, 차선 이탈, 과속, 신호 위반. The landing copy was scrubbed of these.

### Scoring
Each of the 4 categories (`signal`, `pedestrian`, `speed`, `distance`) starts at 100 and loses `event.penalty` per violation, capped at `_MAX_CATEGORY_DROP = 40`. Grade thresholds: A ≥ 90, B ≥ 80, C ≥ 70, D < 70. (No `lane` category — there is no lane detection, so it can't be scored honestly.)

## Coding Guidelines

### Think before coding
State assumptions explicitly before implementing. If multiple interpretations exist, surface them — don't pick silently. If something is unclear, name what's confusing and ask rather than guessing.

### Simplicity first
Minimum code that solves the problem. No speculative features, abstractions for single-use code, or "flexibility" that wasn't requested. If 200 lines could be 50, rewrite it.

### Surgical changes
Touch only what is directly required. Don't "improve" adjacent code, comments, or formatting. Match existing style even if you'd do it differently. If unrelated dead code is noticed, mention it — don't delete it. Remove only imports/variables/functions that *your* changes made unused.

### Verify before declaring done
Transform tasks into verifiable goals before starting. For the pipeline, run `python scripts/smoke_pipeline.py` after any change to `core/`. For UI changes that affect the Gradio app, verify by running `python app.py` and exercising the affected state transition.
