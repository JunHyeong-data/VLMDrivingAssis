"""Risk timeline — markers pop in with spring on render."""
from __future__ import annotations

from html import escape

from core.schema import Event


def render_timeline(events: list[Event], duration_sec: float) -> str:
    if duration_sec <= 0:
        return ""

    markers = "\n".join(_marker(ev, duration_sec, i) for i, ev in enumerate(events))

    return f"""
    <div class="dc-timeline-wrap">
      <div class="dc-timeline-head">
        <span class="label">Risk Timeline</span>
        <span class="range">0:00 ─ {_fmt_ts(duration_sec)}  ·  {len(events)} 이벤트</span>
      </div>
      <div class="dc-timeline">
        {markers}
      </div>
      <div class="dc-timeline-legend">
        <span><span class="dot" style="background: var(--dc-safe);"></span>Safe</span>
        <span><span class="dot" style="background: var(--dc-caution);"></span>Caution</span>
        <span><span class="dot" style="background: var(--dc-danger);"></span>Danger</span>
      </div>
    </div>
    """


def _marker(ev: Event, duration_sec: float, idx: int) -> str:
    pct = max(0.0, min(100.0, (ev.timestamp / duration_sec) * 100))
    tip = f"{_fmt_ts(ev.timestamp)} · {escape(ev.title)}"
    # Stagger each marker's pop-in
    delay = 0.4 + idx * 0.06
    return f"""
    <div class="marker {ev.severity}"
         style="left: {pct:.2f}%; animation-delay: {delay:.2f}s;">
      <div class="tip">{tip}</div>
    </div>
    """


def _fmt_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
