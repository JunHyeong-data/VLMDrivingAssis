"""Score panel — Toss-style giant number + SVG gauge + count-up animation.

Design choices:
  - SVG stroke-dashoffset animation gives the gauge a *living* fill — feels
    like the score is being decided, not displayed.
  - Number counts up from 0 to final value via inline JS (no external lib).
  - Single accent color throughout. Weak categories use semantic colors,
    but only as a 0.85-opacity overlay on the same teal — never a pure red bar.
  - Focus area sits below the gauge as a separate, calmer card.
"""
from __future__ import annotations

import math
from html import escape

from core.schema import ScoreReport


# Gauge geometry
_RADIUS = 88
_CIRCUMFERENCE = 2 * math.pi * _RADIUS   # ≈ 553


def render_score(report: ScoreReport | None) -> str:
    if report is None:
        return _empty_state()

    score = max(0, min(100, report.total))
    offset = _CIRCUMFERENCE * (1 - score / 100)

    return f"""
    <div class="dc-score-hero">
      {_gauge_svg(score, offset)}
      {_score_overlay(score, report.grade)}
      {_grade_label(report.grade)}
    </div>
    {_categories(report)}
    {_focus_area(report)}
    {_count_up_script(score)}
    """


def _gauge_svg(score: int, offset: float) -> str:
    """Animated SVG ring — track + filled arc with stroke-dashoffset spring."""
    return f"""
    <svg class="dc-gauge-svg" viewBox="0 0 200 200" aria-hidden="true">
      <defs>
        <linearGradient id="dc-gauge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"  stop-color="#00FFB0"/>
          <stop offset="100%" stop-color="#00C8FF"/>
        </linearGradient>
      </defs>
      <!-- Track -->
      <circle class="track" cx="100" cy="100" r="{_RADIUS}"
              stroke-width="10" fill="none"/>
      <!-- Animated fill -->
      <circle class="fill" cx="100" cy="100" r="{_RADIUS}"
              stroke="url(#dc-gauge-grad)" stroke-width="10" fill="none"
              stroke-dasharray="{_CIRCUMFERENCE:.2f}"
              stroke-dashoffset="{_CIRCUMFERENCE:.2f}"
              style="animation: dc-gauge-fill 1.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s forwards;
                     --gauge-target: {offset:.2f};"/>
    </svg>

    <style>
      @keyframes dc-gauge-fill {{
        to {{ stroke-dashoffset: var(--gauge-target); }}
      }}
    </style>
    """


def _score_overlay(score: int, grade: str) -> str:
    """The huge number floats over the SVG center."""
    return f"""
    <div class="dc-score-overlay">
      <div class="dc-score-number" id="dc-score-num" data-target="{score}">0</div>
      <div class="dc-score-denom">/ 100</div>
    </div>
    """


def _grade_label(grade: str) -> str:
    msg = {
        "A": "양호한 주행이었습니다",
        "B": "안정적이지만 개선 여지가 있어요",
        "C": "몇 가지 주의가 필요했어요",
        "D": "위험한 순간이 많았어요",
    }.get(grade, "")
    return f"""
    <div class="dc-grade-label">
      <span class="dot"></span>
      Grade {escape(grade)} · {escape(msg)}
    </div>
    """


def _categories(report) -> str:
    rows = "\n".join(_cat_row(c) for c in report.categories)
    return f"""
    <div class="dc-card" style="margin-top:24px;">
      <div class="dc-section-label">카테고리별 점수</div>
      {rows}
    </div>
    """


def _cat_row(cat) -> str:
    """One category row — bar animates from 0 to cat.score% via CSS var."""
    strength = _strength_class(cat.score)
    return f"""
    <div class="dc-cat-row">
      <span class="icon">{cat.icon}</span>
      <span class="name">{escape(cat.name_ko)}</span>
      <span class="track">
        <span class="fill {strength}" style="--bar-width: {cat.score}%;"></span>
      </span>
      <span class="num">{cat.score}</span>
    </div>
    """


def _strength_class(score: int) -> str:
    if score < 60: return "weak"
    if score < 80: return "medium"
    return ""  # default accent color


def _focus_area(report) -> str:
    if not report.focus_area:
        return ""
    f = report.focus_area
    return f"""
    <div class="dc-focus">
      <div class="tag">▼ FOCUS AREA</div>
      <div class="name">{f.icon} {escape(f.name_ko)}</div>
      <div class="desc">
        이 영역에서 {100 - f.score}점이 감점됐어요.
        해당 코칭을 우선 확인하고 다음 주행에서 개선해 보세요.
      </div>
    </div>
    """


def _count_up_script(target: int) -> str:
    """Animates the score number from 0 → target with ease-out cubic.

    Runs every time the HTML is rendered (Gradio replaces innerHTML on update).
    Scoped to the #dc-score-num element to avoid double-firing.
    """
    return f"""
    <script>
    (function() {{
      const el = document.getElementById('dc-score-num');
      if (!el) return;
      const target = {target};
      const duration = 1400;
      const start = performance.now();
      function tick(now) {{
        const t = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);   // ease-out cubic
        el.textContent = Math.round(target * eased);
        if (t < 1) requestAnimationFrame(tick);
      }}
      requestAnimationFrame(tick);
    }})();
    </script>
    """


def _empty_state() -> str:
    return """
    <div class="dc-empty">
      <div class="big">📊</div>
      <div class="msg">아직 분석된 점수가 없어요</div>
      <div class="sub">영상을 분석하면 운전 점수가 표시됩니다</div>
    </div>
    """
