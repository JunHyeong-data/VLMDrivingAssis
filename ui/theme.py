"""DriveCoach AI design system.

Design philosophy (Toss-inspired):
  - Information hierarchy is expressed by type scale, not color
  - One accent color (deep teal) carries every interaction
  - Numbers are alive — they count up, gauges fill in with spring motion
  - White space is luxury — every screen has one primary action
  - All motion uses spring easing, never linear

The system is built on an 8px spacing grid and a 1.25 type scale.
"""
from __future__ import annotations

from pathlib import Path

import gradio as gr

# ─── Color tokens ──────────────────────────────────────────────
# Pure black surfaces + signal-green accent. Inspired by Toss Invest dark
# theme — the accent is *bright* against the deepest black so the eye
# locks on intent, never on chrome.
BG          = "#000000"            # pure black — maximum contrast
BG_RAISED   = "#0A0B0E"            # barely-lifted surface
PANEL       = "#0E1014"            # solid panel
PANEL_HI    = "#15181E"            # hover state
BORDER      = "rgba(255,255,255,0.06)"
BORDER_HI   = "rgba(255,255,255,0.14)"

TEXT_HI     = "#FFFFFF"
TEXT_MID    = "#A3A8B3"
TEXT_LOW    = "#5C6370"

ACCENT      = "#00E59A"            # signal green — high saturation, high luma
ACCENT_HI   = "#00FFB0"            # hover/peak
ACCENT_SOFT = "rgba(0,229,154,0.12)"
ACCENT_GLOW = "rgba(0,229,154,0.40)"

# Secondary accent — electric cyan, used sparingly for HUD/data callouts
DATA_CYAN   = "#00C8FF"
DATA_GLOW   = "rgba(0,200,255,0.32)"

DANGER      = "#FF4D5E"
CAUTION     = "#FFB020"
SAFE        = "#00E59A"

# ─── Spacing scale (8px grid) ─────────────────────────────────
# Exposed for HTML generators that prefer Python constants over CSS vars.
S1, S2, S3, S4, S5, S6, S7, S8 = 4, 8, 12, 16, 24, 32, 48, 64


def build_theme() -> gr.themes.Base:
    # Note: Pretendard Variable is loaded via <link> tags emitted from
    # idle_hero_html() (see ui/screens.py) because Gradio injects our CSS
    # via CSSStyleSheet.replaceSync() which forbids @import. Our global CSS
    # (ui/landing.css) overrides font-family anyway, so the list below only
    # acts as the SSR fallback before our stylesheet hits.
    return gr.themes.Base(
        primary_hue="teal",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"],
    ).set(
        body_background_fill=BG,
        body_text_color=TEXT_HI,
        block_background_fill=PANEL,
        block_border_color=BORDER,
        block_border_width="1px",
        block_label_text_color=TEXT_MID,
        button_primary_background_fill=ACCENT,
        button_primary_background_fill_hover=ACCENT_HI,
        button_primary_text_color="#ffffff",
        input_background_fill=PANEL,
        input_border_color=BORDER,
    )


# ─── Global CSS (the design system) ───────────────────────────
# All styles live in ui/landing.css (next to this file). Pulled in here so
# app.py can keep using `css=CUSTOM_CSS`. To edit the design, open landing.css
# directly — this module only needs touching for Python-side tokens / themes.
CUSTOM_CSS = (Path(__file__).with_name("landing.css")).read_text(encoding="utf-8")
