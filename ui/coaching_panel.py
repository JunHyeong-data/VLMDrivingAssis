"""Coaching panel — Toss-style staggered bubble entrance.

Each VLM coaching response renders as a card with the DriveVLM 3-stage CoT
(Scene → Analysis → Action). Bubbles fade-up with a 0.08s stagger that gives
the panel a sense of *receiving* messages, not just *displaying* them.
"""
from __future__ import annotations

from html import escape

from core.schema import Coaching


_SEVERITY_KO = {"safe": "안전", "caution": "주의", "danger": "위험"}


def render_coaching(coachings: list[Coaching]) -> str:
    if not coachings:
        return _empty_state()

    header = f"""
    <div class="dc-card" style="margin-bottom: 20px;">
      <div style="display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
          <div class="dc-section-label" style="margin-bottom:4px;">VLM 코칭</div>
          <div style="font-size: 20px; font-weight: 700; letter-spacing: -0.02em;">
            {len(coachings)}건의 분석 결과
          </div>
          <div style="font-size:12px; color: var(--dc-text-mid); margin-top:4px;">
            DriveVLM CoT · Scene → Analysis → Action
          </div>
        </div>
        <div style="font-size:10px; letter-spacing:.08em; text-transform:uppercase;
                    color: var(--dc-accent-hi); font-weight:600;">
          Qwen 2.5-VL
        </div>
      </div>
    </div>
    """

    # Wrap bubbles in a container so the stagger nth-child rules apply.
    bubbles = "\n".join(_bubble(c) for c in coachings)
    return header + f"<div class='dc-bubble-list'>{bubbles}</div>"


def _bubble(c: Coaching) -> str:
    ev = c.event
    sev = ev.severity  # safe | caution | danger
    ts = _fmt_ts(ev.timestamp)
    sev_ko = _SEVERITY_KO[sev]

    return f"""
    <div class="dc-bubble {sev}">
      <div class="head">
        <span class="title">{escape(ev.title)}</span>
        <span class="ts">{ts}</span>
      </div>

      <div class="stage-label">① 상황 묘사</div>
      <p>{escape(c.scene_description)}</p>

      <div class="stage-label">② 위험 분석</div>
      <p>{escape(c.scene_analysis)}</p>

      <div class="stage-label">③ 행동 제안</div>
      <p>{escape(c.action_plan)}</p>

      <span class="chip">{sev_ko} · −{ev.penalty}점</span>
    </div>
    """


def _fmt_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _empty_state() -> str:
    return """
    <div class="dc-empty">
      <div class="big">💬</div>
      <div class="msg">아직 받은 코칭이 없어요</div>
      <div class="sub">영상을 분석하면 위험 구간별 코칭이 표시됩니다</div>
    </div>
    """
