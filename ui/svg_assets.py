"""SVG assets — hand-crafted minimal illustrations.

Why not use icon libraries? Toss-grade UIs use *bespoke* visuals that match
the domain. Generic icons (emojis, Material icons) instantly read as "demo".
These SVGs are kept lean: paths only, no rasters, ~1-2KB each.

All marks render via currentColor or explicit accent vars so the theme
controls them.
"""
from __future__ import annotations


# ─── Logo mark — DriveCoach signature ─────────────────────────
# Concept: minimalist play/forward chevron inside a gauge arc.
# The arc gap implies progress/measurement; the chevron implies motion forward.
LOGO_MARK = """
<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" aria-label="DriveCoach AI">
  <defs>
    <linearGradient id="dc-logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#00FFB0"/>
      <stop offset="100%" stop-color="#00C8FF"/>
    </linearGradient>
  </defs>
  <!-- Gauge arc (3/4 ring, opens at bottom-right — implies "in progress") -->
  <path d="M 20 4
           A 16 16 0 1 1 31.3 31.3"
        fill="none" stroke="url(#dc-logo-grad)" stroke-width="3"
        stroke-linecap="round"/>
  <!-- Forward chevron (centered, equilateral, properly weighted) -->
  <path d="M 16 13 L 26 20 L 16 27 Z"
        fill="url(#dc-logo-grad)"/>
</svg>
"""


# ─── IDLE hero illustration — road + HUD lines ────────────────
# Fills its container (aspect-ratio is fixed on the wrapper).
# Uses preserveAspectRatio="xMidYMid slice" so it crops gracefully if the
# wrapper aspect differs from the viewBox.
ROAD_HUD_ILLUSTRATION = """
<svg viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMid slice"
     class="dc-illust-road" aria-hidden="true">
  <defs>
    <linearGradient id="dc-road-grad" x1="50%" y1="100%" x2="50%" y2="0%">
      <stop offset="0%"  stop-color="rgba(0,229,154,0.35)"/>
      <stop offset="60%" stop-color="rgba(0,229,154,0.06)"/>
      <stop offset="100%" stop-color="rgba(0,229,154,0)"/>
    </linearGradient>
    <linearGradient id="dc-lane-grad" x1="50%" y1="100%" x2="50%" y2="0%">
      <stop offset="0%"  stop-color="rgba(255,255,255,0.60)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
    </linearGradient>
    <radialGradient id="dc-sky-grad" cx="50%" cy="40%" r="60%">
      <stop offset="0%"  stop-color="rgba(0,200,255,0.16)"/>
      <stop offset="100%" stop-color="rgba(0,200,255,0)"/>
    </radialGradient>
    <filter id="dc-soft-blur"><feGaussianBlur stdDeviation="4"/></filter>
  </defs>

  <!-- Sky/horizon glow -->
  <rect width="600" height="420" fill="url(#dc-sky-grad)"/>

  <!-- Road plane (trapezoid receding to horizon at y=210) -->
  <path d="M 100 420 L 270 210 L 330 210 L 500 420 Z"
        fill="url(#dc-road-grad)"
        stroke="rgba(255,255,255,0.08)" stroke-width="1"/>

  <!-- Center lane dashes — perspective scaling -->
  <g fill="url(#dc-lane-grad)">
    <rect x="297" y="218" width="6"  height="12" rx="1"/>
    <rect x="295" y="246" width="10" height="16" rx="1"/>
    <rect x="293" y="280" width="14" height="22" rx="1"/>
    <rect x="290" y="318" width="20" height="28" rx="2"/>
    <rect x="285" y="364" width="30" height="40" rx="2"/>
  </g>

  <!-- Side lane edges -->
  <line x1="270" y1="210" x2="100" y2="420"
        stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>
  <line x1="330" y1="210" x2="500" y2="420"
        stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>

  <!-- Far horizon glow -->
  <ellipse cx="300" cy="208" rx="120" ry="6"
           fill="rgba(0,229,154,0.45)" filter="url(#dc-soft-blur)"/>

  <!-- HUD: detection boxes -->
  <g style="animation: dc-illust-pulse 3.2s ease-in-out infinite;">
    <rect x="160" y="262" width="76" height="48" rx="3"
          fill="none" stroke="#00C8FF" stroke-width="1.5"/>
    <rect x="160" y="248" width="50" height="13" rx="2" fill="#00C8FF"/>
    <text x="165" y="259" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#000">car 0.92</text>
  </g>
  <g style="animation: dc-illust-pulse 3.2s ease-in-out 0.6s infinite;">
    <rect x="370" y="284" width="58" height="50" rx="3"
          fill="none" stroke="#00E59A" stroke-width="1.5"/>
    <rect x="370" y="270" width="70" height="13" rx="2" fill="#00E59A"/>
    <text x="375" y="281" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#000">person 0.88</text>
  </g>
  <g style="animation: dc-illust-pulse 3.2s ease-in-out 1.2s infinite;">
    <rect x="280" y="170" width="40" height="22" rx="3"
          fill="none" stroke="#FFB020" stroke-width="1.5"/>
    <circle cx="290" cy="181" r="4" fill="#FFB020"/>
    <text x="298" y="184" font-family="Pretendard Variable, sans-serif"
          font-size="8" font-weight="700" fill="#FFB020">SIGNAL</text>
  </g>

  <!-- Top HUD telemetry bars -->
  <g transform="translate(40,52)">
    <text x="0" y="0" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#A3A8B3"
          letter-spacing="2">DETECTION</text>
    <text x="170" y="0" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#00E59A"
          text-anchor="end">44%</text>
    <rect y="8" width="170" height="2" rx="1" fill="rgba(255,255,255,0.08)"/>
    <rect y="8" width="75"  height="2" rx="1" fill="#00E59A"/>
  </g>
  <g transform="translate(390,52)">
    <text x="0" y="0" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#A3A8B3"
          letter-spacing="2">CONFIDENCE</text>
    <text x="170" y="0" font-family="Pretendard Variable, sans-serif"
          font-size="9" font-weight="700" fill="#00C8FF"
          text-anchor="end">82%</text>
    <rect y="8" width="170" height="2" rx="1" fill="rgba(255,255,255,0.08)"/>
    <rect y="8" width="140" height="2" rx="1" fill="#00C8FF"/>
  </g>
</svg>
"""


# ─── Decorative grid backdrop (subtle, behind hero) ───────────
HERO_GRID_BG = """
<svg class="dc-grid-bg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <pattern id="dc-grid" width="80" height="80" patternUnits="userSpaceOnUse">
      <path d="M 80 0 L 0 0 0 80" fill="none"
            stroke="rgba(255,255,255,0.025)" stroke-width="1"/>
    </pattern>
    <radialGradient id="dc-glow-bg" cx="15%" cy="20%" r="55%">
      <stop offset="0%"  stop-color="rgba(0,229,154,0.08)"/>
      <stop offset="100%" stop-color="rgba(0,229,154,0)"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#dc-grid)"/>
  <rect width="100%" height="100%" fill="url(#dc-glow-bg)"/>
</svg>
"""


# ─── Step icons — proper domain glyphs ────────────────────────
# Each is 40x40, currentColor, for use inside .dc-step-glyph

# STEP 1: Detection — car silhouette inside a bounding box
ICON_DETECTION = """
<svg viewBox="0 0 40 40" width="40" height="40" fill="none"
     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Outer bbox -->
  <rect x="5" y="11" width="30" height="22" rx="2"/>
  <!-- Corner crops (yolo-style) -->
  <path d="M 5 16 L 5 11 L 10 11" stroke-width="2.5"/>
  <path d="M 30 11 L 35 11 L 35 16" stroke-width="2.5"/>
  <path d="M 35 28 L 35 33 L 30 33" stroke-width="2.5"/>
  <path d="M 10 33 L 5 33 L 5 28" stroke-width="2.5"/>
  <!-- Car silhouette inside -->
  <path d="M 11 27 L 11 24 L 13 19 L 27 19 L 29 24 L 29 27"
        fill="currentColor" fill-opacity="0.18"/>
  <circle cx="14" cy="27" r="1.5" fill="currentColor" stroke="none"/>
  <circle cx="26" cy="27" r="1.5" fill="currentColor" stroke="none"/>
</svg>
"""

# STEP 2: Event extraction — pulse / spike timeline
ICON_EVENTS = """
<svg viewBox="0 0 40 40" width="40" height="40" fill="none"
     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Baseline -->
  <line x1="4" y1="22" x2="36" y2="22"/>
  <!-- Spike events (3) -->
  <path d="M 4 22 L 9 22 L 11 14 L 13 22 L 19 22 L 21 8 L 23 22 L 29 22 L 31 16 L 33 22 L 36 22"
        stroke-width="2"/>
  <!-- Markers on top of spikes -->
  <circle cx="11" cy="14" r="2" fill="currentColor" stroke="none"/>
  <circle cx="21" cy="8"  r="2.5" fill="currentColor" stroke="none"/>
  <circle cx="31" cy="16" r="2" fill="currentColor" stroke="none"/>
</svg>
"""

# STEP 3: VLM coaching — speech bubble with sparkle (AI mark)
ICON_VLM = """
<svg viewBox="0 0 40 40" width="40" height="40" fill="none"
     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Speech bubble (rounded square with tail) -->
  <path d="M 7 9 Q 7 6 10 6 L 30 6 Q 33 6 33 9 L 33 22 Q 33 25 30 25 L 20 25 L 14 31 L 14 25 Q 11 25 9 23 Q 7 21 7 18 Z"/>
  <!-- Lines inside bubble -->
  <line x1="11" y1="13" x2="29" y2="13" stroke-width="1.5" opacity="0.6"/>
  <line x1="11" y1="17" x2="24" y2="17" stroke-width="1.5" opacity="0.6"/>
  <!-- AI sparkle in corner -->
  <path d="M 30 29 L 31.5 32 L 34.5 33.5 L 31.5 35 L 30 38 L 28.5 35 L 25.5 33.5 L 28.5 32 Z"
        fill="currentColor" stroke="none"/>
</svg>
"""


# ─── Partner logos (text-mark style, mono color via currentColor) ────────────
# Hand-set wordmarks for the tech stack — feels more legit than 3rd-party logos.

LOGO_BDD = """
<svg viewBox="0 0 110 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <text x="0" y="20" font-family="Inter, sans-serif" font-weight="900" font-size="20"
        letter-spacing="-0.5">BDD<tspan font-weight="500">100K</tspan></text>
</svg>
"""

LOGO_COCO = """
<svg viewBox="0 0 80 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <circle cx="11" cy="14" r="9" fill="none" stroke="currentColor" stroke-width="2.4"/>
  <text x="26" y="20" font-family="Inter, sans-serif" font-weight="800" font-size="18"
        letter-spacing="-0.4">COCO</text>
</svg>
"""

LOGO_YOLO = """
<svg viewBox="0 0 90 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <rect x="2" y="6" width="16" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="2.4"/>
  <text x="24" y="20" font-family="Inter, sans-serif" font-weight="900" font-size="19"
        letter-spacing="-0.5">YOLO26</text>
</svg>
"""

LOGO_QWEN = """
<svg viewBox="0 0 110 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <path d="M 4 22 L 14 6 L 24 22 Z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>
  <text x="30" y="20" font-family="Inter, sans-serif" font-weight="800" font-size="18"
        letter-spacing="-0.4">Qwen<tspan font-weight="500"> 2.5-VL</tspan></text>
</svg>
"""

LOGO_OPENCV = """
<svg viewBox="0 0 110 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <circle cx="10" cy="14" r="4.5" fill="none" stroke="currentColor" stroke-width="2.2"/>
  <circle cx="18" cy="14" r="4.5" fill="none" stroke="currentColor" stroke-width="2.2"/>
  <text x="30" y="20" font-family="Inter, sans-serif" font-weight="800" font-size="18"
        letter-spacing="-0.4">OpenCV</text>
</svg>
"""

LOGO_INHA = """
<svg viewBox="0 0 130 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <rect x="2" y="4" width="20" height="20" rx="3" fill="none" stroke="currentColor" stroke-width="2.4"/>
  <line x1="2" y1="14" x2="22" y2="14" stroke="currentColor" stroke-width="2"/>
  <line x1="12" y1="4" x2="12" y2="24" stroke="currentColor" stroke-width="2"/>
  <text x="28" y="20" font-family="Inter, sans-serif" font-weight="700" font-size="16"
        letter-spacing="-0.3">INHA · FVE3011</text>
</svg>
"""

LOGO_DRIVEVLM = """
<svg viewBox="0 0 130 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <path d="M 4 8 L 4 20 L 14 14 Z" fill="currentColor"/>
  <text x="22" y="20" font-family="Inter, sans-serif" font-weight="800" font-size="18"
        letter-spacing="-0.4">DriveVLM</text>
</svg>
"""

LOGO_PYTORCH = """
<svg viewBox="0 0 110 28" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
  <path d="M 8 22 Q 4 18 4 14 Q 4 9 9 6 L 9 12 Q 7 13.5 7 16 Q 7 19 9 20.5 Z"
        fill="currentColor"/>
  <circle cx="13" cy="9" r="1.5" fill="currentColor"/>
  <text x="22" y="20" font-family="Inter, sans-serif" font-weight="800" font-size="18"
        letter-spacing="-0.4">PyTorch</text>
</svg>
"""


# ─── 3-card research illustrations (16:9 aspect, fills card) ─────────────────
# Used inside the Runway-style research grid when no per-card video exists.

ILLUST_DETECTION = """
<svg viewBox="0 0 400 225" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="ill-det-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"  stop-color="#0A0B0E"/>
      <stop offset="100%" stop-color="#13151A"/>
    </linearGradient>
    <radialGradient id="ill-det-glow" cx="50%" cy="100%" r="60%">
      <stop offset="0%"  stop-color="rgba(0,229,154,0.18)"/>
      <stop offset="100%" stop-color="rgba(0,229,154,0)"/>
    </radialGradient>
  </defs>
  <rect width="400" height="225" fill="url(#ill-det-bg)"/>
  <rect width="400" height="225" fill="url(#ill-det-glow)"/>

  <!-- Receding road -->
  <path d="M 80 225 L 185 110 L 215 110 L 320 225 Z"
        fill="rgba(0,229,154,0.10)" stroke="rgba(255,255,255,0.10)" stroke-width="1"/>
  <line x1="200" y1="108" x2="200" y2="225" stroke="rgba(255,255,255,0.18)"
        stroke-width="1.5" stroke-dasharray="5 7"/>

  <!-- Detection bboxes -->
  <g stroke="#00C8FF" stroke-width="1.4" fill="none">
    <rect x="120" y="140" width="60" height="40" rx="2"/>
    <rect x="118" y="129" width="46" height="11" rx="1" fill="#00C8FF"/>
    <text x="121" y="137" font-family="Inter, sans-serif" font-size="8"
          font-weight="700" fill="#000">car  0.94</text>
  </g>
  <g stroke="#00E59A" stroke-width="1.4" fill="none">
    <rect x="244" y="148" width="48" height="42" rx="2"/>
    <rect x="242" y="137" width="60" height="11" rx="1" fill="#00E59A"/>
    <text x="245" y="145" font-family="Inter, sans-serif" font-size="8"
          font-weight="700" fill="#000">person 0.88</text>
  </g>
  <g stroke="#FFB020" stroke-width="1.4" fill="none">
    <rect x="186" y="88" width="34" height="18" rx="2"/>
    <circle cx="195" cy="97" r="3" fill="#FFB020"/>
  </g>

  <!-- HUD telemetry -->
  <g transform="translate(20,30)">
    <text x="0" y="0" font-family="Inter, sans-serif" font-size="8" font-weight="700"
          fill="#A3A8B3" letter-spacing="2">DETECTION</text>
    <rect x="0" y="6" width="120" height="2" rx="1" fill="rgba(255,255,255,0.10)"/>
    <rect x="0" y="6" width="58"  height="2" rx="1" fill="#00E59A"/>
  </g>
</svg>
"""

ILLUST_EVENTS = """
<svg viewBox="0 0 400 225" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="ill-ev-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"  stop-color="#0A0B0E"/>
      <stop offset="100%" stop-color="#13151A"/>
    </linearGradient>
  </defs>
  <rect width="400" height="225" fill="url(#ill-ev-bg)"/>

  <!-- Time axis baseline -->
  <line x1="40" y1="160" x2="360" y2="160" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>
  <!-- Tick marks -->
  <g stroke="rgba(255,255,255,0.10)" stroke-width="1">
    <line x1="40"  y1="160" x2="40"  y2="166"/>
    <line x1="120" y1="160" x2="120" y2="166"/>
    <line x1="200" y1="160" x2="200" y2="166"/>
    <line x1="280" y1="160" x2="280" y2="166"/>
    <line x1="360" y1="160" x2="360" y2="166"/>
  </g>

  <!-- Spike line + markers -->
  <polyline points="40,160 90,160 110,90 130,160 175,160 200,55 225,160 290,160 310,110 330,160 360,160"
            fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="1.4"/>

  <!-- Event markers (severity) -->
  <g>
    <circle cx="110" cy="90" r="6" fill="#FFB020"/>
    <text x="92" y="78" font-family="Inter, sans-serif" font-size="9"
          font-weight="700" fill="#FFB020">CAUTION</text>
  </g>
  <g>
    <circle cx="200" cy="55" r="7" fill="#FF4D5E"/>
    <text x="178" y="43" font-family="Inter, sans-serif" font-size="9"
          font-weight="700" fill="#FF4D5E">DANGER</text>
  </g>
  <g>
    <circle cx="310" cy="110" r="6" fill="#FFB020"/>
    <text x="290" y="98" font-family="Inter, sans-serif" font-size="9"
          font-weight="700" fill="#FFB020">CAUTION</text>
  </g>

  <!-- Frame thumbnails (small) -->
  <g stroke="rgba(255,255,255,0.18)" stroke-width="1" fill="rgba(255,255,255,0.04)">
    <rect x="90"  y="180" width="40" height="24" rx="2"/>
    <rect x="180" y="180" width="40" height="24" rx="2"/>
    <rect x="290" y="180" width="40" height="24" rx="2"/>
  </g>

  <!-- Top label -->
  <text x="40" y="30" font-family="Inter, sans-serif" font-size="9" font-weight="700"
        fill="#A3A8B3" letter-spacing="2">EVENT TIMELINE</text>
</svg>
"""

ILLUST_VLM = """
<svg viewBox="0 0 400 225" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="ill-vlm-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"  stop-color="#0A0B0E"/>
      <stop offset="100%" stop-color="#13151A"/>
    </linearGradient>
  </defs>
  <rect width="400" height="225" fill="url(#ill-vlm-bg)"/>

  <!-- Three stacked coaching bubbles -->
  <g>
    <rect x="40" y="36" width="320" height="44" rx="6"
          fill="rgba(255,255,255,0.04)" stroke="rgba(0,229,154,0.4)" stroke-width="1.2"/>
    <text x="56" y="55" font-family="Inter, sans-serif" font-size="10"
          font-weight="700" fill="#00E59A" letter-spacing="1">① SCENE</text>
    <rect x="56" y="62" width="200" height="3" rx="1" fill="rgba(255,255,255,0.18)"/>
    <rect x="56" y="69" width="140" height="3" rx="1" fill="rgba(255,255,255,0.10)"/>
  </g>
  <g>
    <rect x="40" y="91" width="320" height="44" rx="6"
          fill="rgba(255,255,255,0.04)" stroke="rgba(255,176,32,0.4)" stroke-width="1.2"/>
    <text x="56" y="110" font-family="Inter, sans-serif" font-size="10"
          font-weight="700" fill="#FFB020" letter-spacing="1">② ANALYSIS</text>
    <rect x="56" y="117" width="240" height="3" rx="1" fill="rgba(255,255,255,0.18)"/>
    <rect x="56" y="124" width="170" height="3" rx="1" fill="rgba(255,255,255,0.10)"/>
  </g>
  <g>
    <rect x="40" y="146" width="320" height="44" rx="6"
          fill="rgba(255,255,255,0.04)" stroke="rgba(0,200,255,0.4)" stroke-width="1.2"/>
    <text x="56" y="165" font-family="Inter, sans-serif" font-size="10"
          font-weight="700" fill="#00C8FF" letter-spacing="1">③ ACTION</text>
    <rect x="56" y="172" width="220" height="3" rx="1" fill="rgba(255,255,255,0.18)"/>
    <rect x="56" y="179" width="160" height="3" rx="1" fill="rgba(255,255,255,0.10)"/>
  </g>
</svg>
"""
