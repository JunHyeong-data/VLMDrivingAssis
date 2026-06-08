"""Rule-based event extraction — the "smart filter" that decides when to call VLM.

Without this layer, we'd waste compute calling Qwen2.5-VL on every frame.
With it, VLM is only invoked at semantically interesting moments.

Design constraints (and what we deliberately do NOT claim):
  We have per-frame YOLO boxes *with ByteTrack IDs* — no IMU, no ego speed, no
  lane lines, no depth, no light color. Every rule is grounded in bbox geometry
  over time. We don't fake "급제동(g)" or signal-color logic.

Tracking lets us read real motion from trajectories, honestly:
  - per-vehicle looming (the lead car's own box growing) → 앞차 급접근 vs 근접
  - a vehicle's center crossing from the side into the ego lane → 옆차 끼어들기
  - a pedestrian's center moving toward the road → 보행자 도로 횡단
These are far more robust than single-frame size thresholds, which depend on
camera FOV/mount. Rate-of-change signals transfer across cameras better than
absolute sizes; the absolute thresholds below are a profile for typical Korean
dashcam framing, calibrated on a real 90s clip (yolo26s).

Over-extraction guardrails:
  1. Persistence — a condition must hold for a short time (seconds, not frames).
  2. Rising-edge / hysteresis — each episode fires once until it clears.
  3. Neighbor suppression + diversity-aware cap — collapse clusters, then keep a
     small, time-spread, type-diverse set.
"""
from __future__ import annotations

from collections import deque

from core.schema import Detection, Event, FrameDetections

# ── Rule 1: ego-lane lead vehicle — proximity + per-track looming ─────
_LEAD_CENTER_BAND = (0.32, 0.68)   # bbox center-x / width → ego lane
_LEAD_BOTTOM_MIN = 0.55            # bbox bottom-y / height ≥ this (near, on road)
_CLOSE_NEAR_RATIO = 0.10           # lead area / frame ≥ this → "near"
_CLOSE_LOOM_MIN_RATIO = 0.06       # min lead area before looming is considered
_CLOSE_LOOM_DELTA = 0.05           # lead area growth over the window → approaching
_CLOSE_DANGER_RATIO = 0.14         # very near → danger
_CLOSE_DANGER_LOOM = 0.07          # fast approach → danger
_LOOM_WINDOW_SEC = 0.4

# ── Rule 1b: cut-in — a tracked vehicle entering the ego lane from the side ──
_CUTIN_MIN_AREA = 0.04             # must be near enough to matter
_CUTIN_WINDOW_SEC = 0.6            # look-back to confirm it came from outside
_CUTIN_SIDE_MARGIN = 0.04          # how far outside the band it had to be

# ── Rule 2: pedestrian / rider close to the road, with crossing direction ──
_PEDESTRIAN_HEIGHT_RATIO = 0.12    # bbox height ≥ 12% of frame → close enough
_PEDESTRIAN_BOTTOM_MIN = 0.50      # bbox bottom in lower half → near roadway
_PED_CROSS_WINDOW_SEC = 0.8
_PED_CROSS_DELTA = 0.06            # center moved this much toward image center → crossing

# ── Rule 3: approaching a signalized intersection ────────────────────
_SIGNAL_NEAR_HEIGHT = 0.05         # traffic-light bbox height / frame ≥ this (near)

# ── Rule 4: congestion — many *dynamic* agents at once ───────────────
_DYNAMIC_CLASSES = ("car", "truck", "bus", "person", "rider", "bike")
_COMPLEX_SCENE_MIN_OBJECTS = 11    # busy (between p75≈10 and p90≈12); 11 is stabler at the boundary
_COMPLEX_SCENE_WINDOW_SEC = 0.33   # smooth the count over this long (time-based, frame-rate agnostic)

# ── Selection ────────────────────────────────────────────────────────
_MAX_EVENTS = 3
_MIN_EVENT_GAP_FRAMES = 180        # min spacing between any two kept events (~6s)
_SEVERITY_RANK = {"danger": 3, "caution": 2, "safe": 1}

_TRACK_HIST_SEC = 1.3              # how long to retain each track's trajectory

# Per-type episode timing in SECONDS (persist / clear / cooldown). Time-based, not
# frame-counted, so the rules behave identically at any sample_every (the app uses
# 2; a brief pedestrian was being lost when these were frame counts). Motion events
# fire fast; signal/complex are stickier so one intersection / stretch is one event.
_EPISODE_CFG: dict[str, tuple[float, float, float]] = {
    "close_vehicle":   (0.13, 0.4, 5.0),
    "cut_in":          (0.10, 0.4, 5.0),
    "pedestrian_risk": (0.17, 0.4, 5.0),
    "signal_change":   (0.40, 1.0, 10.0),
    "complex_scene":   (0.40, 0.6, 5.0),
}


class _Episode:
    """Rising-edge state machine for one event type (persistence + hysteresis).

    Time-based: a condition must hold continuously for `persist` seconds before it
    counts; brief dropouts are tolerated until it's been absent `clear` seconds; and
    the same type can't re-fire within `cooldown` seconds. Driven by frame
    timestamps, so it's independent of frame rate / sample_every.
    """
    __slots__ = ("persist", "clear", "cooldown", "start_ts", "last_true_ts", "fired", "last_fire_ts")

    def __init__(self, persist: float, clear: float, cooldown: float) -> None:
        self.persist = persist
        self.clear = clear
        self.cooldown = cooldown
        self.start_ts: float | None = None     # when the current true-run began
        self.last_true_ts: float | None = None  # last timestamp the condition was true
        self.fired = False
        self.last_fire_ts = -1e9

    def update(self, cond: bool, ts: float) -> bool:
        if cond:
            if self.start_ts is None:
                self.start_ts = ts
            self.last_true_ts = ts
            if (not self.fired
                    and ts - self.start_ts >= self.persist
                    and ts - self.last_fire_ts >= self.cooldown):
                self.fired = True
                self.last_fire_ts = ts
                return True
            return False
        # condition false: reset the episode once it's been absent long enough
        if self.last_true_ts is not None and ts - self.last_true_ts >= self.clear:
            self.start_ts = None
            self.fired = False
        return False


def _value_at(dq: deque, ts_now: float, back_sec: float):
    """Latest trajectory entry at least `back_sec` before now (≈ that long ago).

    Returns None if the track is younger than `back_sec` — in which case any
    motion rule that needs history simply doesn't fire (no fallback guess).
    """
    target = ts_now - back_sec
    chosen = None
    for e in dq:                 # dq is time-ascending
        if e[0] <= target:
            chosen = e
        else:
            break
    return chosen


def _cx(d: Detection, width: int) -> float:
    return (d.bbox[0] + d.bbox[2]) / 2 / width


def _in_ego_lane(d: Detection, width: int, height: int) -> bool:
    return (_LEAD_CENTER_BAND[0] <= _cx(d, width) <= _LEAD_CENTER_BAND[1]
            and d.bbox[3] / height >= _LEAD_BOTTOM_MIN)


def extract_events(frames: list[FrameDetections]) -> list[Event]:
    """Walk through tracked detections and emit events when rules fire (sustained)."""
    events: list[Event] = []
    ep = {t: _Episode(*cfg) for t, cfg in _EPISODE_CFG.items()}
    hist: dict[int, deque] = {}                       # track_id → deque[(ts, cx, area, bottom)]
    recent_counts: deque[tuple[float, int]] = deque()  # (ts, dynamic-agent count)

    for f in frames:
        ts = f.timestamp
        area_px = (f.width * f.height) or 1

        # Update per-track trajectories (only tracked detections)
        for d in f.detections:
            if d.track_id is None:
                continue
            ar = (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]) / area_px
            dq = hist.setdefault(d.track_id, deque())
            dq.append((ts, _cx(d, f.width), ar, d.bbox[3] / f.height))
            while dq and ts - dq[0][0] > _TRACK_HIST_SEC:
                dq.popleft()

        # Rule 1: ego-lane lead vehicle — proximity OR per-track looming
        lead, lead_area = None, 0.0
        for d in f.detections:
            if d.cls in ("car", "truck", "bus") and d.track_id is not None and _in_ego_lane(d, f.width, f.height):
                ar = (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]) / area_px
                if ar > lead_area:
                    lead, lead_area = d, ar
        loom = 0.0
        if lead is not None:
            past = _value_at(hist[lead.track_id], ts, _LOOM_WINDOW_SEC)
            if past is not None:
                loom = lead_area - past[2]
        approaching = lead_area >= _CLOSE_LOOM_MIN_RATIO and loom >= _CLOSE_LOOM_DELTA
        close_cond = lead is not None and (lead_area >= _CLOSE_NEAR_RATIO or approaching)
        if ep["close_vehicle"].update(close_cond, ts) and lead is not None:
            danger = lead_area >= _CLOSE_DANGER_RATIO or loom >= _CLOSE_DANGER_LOOM
            fast = loom >= _CLOSE_LOOM_DELTA
            events.append(Event(
                frame_idx=f.frame_idx, timestamp=ts, type="close_vehicle",
                severity="danger" if danger else "caution",
                title="앞차 급접근" if danger else "앞차 근접",
                summary=f"전방 {lead.cls} 점유율 {lead_area * 100:.0f}%" + (", 빠르게 접근" if fast else ""),
                penalty=8 if danger else 5, category="distance",
            ))

        # Rule 1b: cut-in — a near vehicle now in the ego lane that came from the side
        cutin, cutin_side = None, ""
        for d in f.detections:
            if d.cls not in ("car", "truck", "bus") or d.track_id is None:
                continue
            ar = (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]) / area_px
            if ar < _CUTIN_MIN_AREA or not _in_ego_lane(d, f.width, f.height):
                continue
            prev = _value_at(hist[d.track_id], ts, _CUTIN_WINDOW_SEC)
            if prev is not None and (prev[1] < _LEAD_CENTER_BAND[0] - _CUTIN_SIDE_MARGIN
                                     or prev[1] > _LEAD_CENTER_BAND[1] + _CUTIN_SIDE_MARGIN):
                cutin = d
                cutin_side = "좌측" if prev[1] < 0.5 else "우측"
                break
        if ep["cut_in"].update(cutin is not None, ts) and cutin is not None:
            events.append(Event(
                frame_idx=f.frame_idx, timestamp=ts, type="cut_in",
                severity="danger", title="옆차 끼어들기",
                summary=f"{cutin_side} 차량이 앞 차선으로 진입",
                penalty=8, category="distance",
            ))

        # Rule 2: pedestrian/rider near the road; flag crossing if moving inward
        ped, ped_cross = None, False
        for d in f.detections:
            if (d.cls in ("person", "rider")
                    and (d.bbox[3] - d.bbox[1]) / f.height >= _PEDESTRIAN_HEIGHT_RATIO
                    and d.bbox[3] / f.height >= _PEDESTRIAN_BOTTOM_MIN):
                ped = d
                if d.track_id is not None:
                    past = _value_at(hist[d.track_id], ts, _PED_CROSS_WINDOW_SEC)
                    if past is not None and abs(past[1] - 0.5) - abs(_cx(d, f.width) - 0.5) >= _PED_CROSS_DELTA:
                        ped_cross = True
                break
        if ep["pedestrian_risk"].update(ped is not None, ts):
            events.append(Event(
                frame_idx=f.frame_idx, timestamp=ts, type="pedestrian_risk",
                severity="danger",
                title="보행자 도로 횡단" if ped_cross else "보행자 근접",
                summary="보행자가 도로 쪽으로 이동 중" if ped_cross else "전방·주변 보행자 감지",
                penalty=10, category="pedestrian",
            ))

        # Rule 3: approaching a signalized intersection (light visible AND near)
        signal_near = any(
            d.cls == "traffic light" and (d.bbox[3] - d.bbox[1]) / f.height >= _SIGNAL_NEAR_HEIGHT
            for d in f.detections
        )
        if ep["signal_change"].update(signal_near, ts):
            events.append(Event(
                frame_idx=f.frame_idx, timestamp=ts, type="signal_change",
                severity="caution", title="신호 교차로 접근",
                summary="전방 신호등 확인 필요", penalty=4, category="signal",
            ))

        # Rule 4: congestion — many dynamic agents at once (excl signs/lights)
        dyn_count = sum(1 for d in f.detections if d.cls in _DYNAMIC_CLASSES)
        recent_counts.append((ts, dyn_count))
        while recent_counts and ts - recent_counts[0][0] > _COMPLEX_SCENE_WINDOW_SEC:
            recent_counts.popleft()
        smoothed = sum(c for _, c in recent_counts) / len(recent_counts)
        if ep["complex_scene"].update(smoothed >= _COMPLEX_SCENE_MIN_OBJECTS, ts):
            events.append(Event(
                frame_idx=f.frame_idx, timestamp=ts, type="complex_scene",
                severity="caution", title="혼잡 구간 진입",
                summary=f"주변 차량·보행자 {dyn_count}대 동시 검출",
                penalty=5, category="speed",
            ))

    return _cap_events(_suppress_neighbors(events))


def _suppress_neighbors(events: list[Event]) -> list[Event]:
    """Temporal non-max suppression across all event types — one per ~6s window."""
    ordered = sorted(
        events,
        key=lambda e: (-_SEVERITY_RANK.get(e.severity, 0), -e.penalty, e.frame_idx),
    )
    kept: list[Event] = []
    for e in ordered:
        if all(abs(e.frame_idx - k.frame_idx) >= _MIN_EVENT_GAP_FRAMES for k in kept):
            kept.append(e)
    kept.sort(key=lambda e: e.frame_idx)
    return kept


def _cap_events(events: list[Event]) -> list[Event]:
    """Keep at most _MAX_EVENTS, favoring type diversity then severity/penalty."""
    if len(events) <= _MAX_EVENTS:
        return events
    ranked = sorted(
        events,
        key=lambda e: (_SEVERITY_RANK.get(e.severity, 0), e.penalty),
        reverse=True,
    )
    kept: list[Event] = []
    chosen: set[int] = set()
    for e in ranked:                       # pass 1: one per type (diversity)
        if len(kept) >= _MAX_EVENTS:
            break
        if e.type not in {k.type for k in kept}:
            kept.append(e)
            chosen.add(id(e))
    for e in ranked:                       # pass 2: fill remaining by priority
        if len(kept) >= _MAX_EVENTS:
            break
        if id(e) not in chosen:
            kept.append(e)
            chosen.add(id(e))
    kept.sort(key=lambda e: e.frame_idx)
    return kept
