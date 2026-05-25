"""Score calculation — events → category scores → total + grade."""
from __future__ import annotations

from core.schema import CategoryScore, Event, ScoreReport, SCORE_CATEGORY_DEFS

# A single category can drop at most this many points — keeps long videos
# from tanking one dimension to 0 just because the rule kept firing.
_MAX_CATEGORY_DROP = 40


def calculate_score(events: list[Event]) -> ScoreReport:
    """Each category starts at 100 and loses event.penalty per violation."""
    cat_drop: dict[str, int] = {key: 0 for key, _, _, _ in SCORE_CATEGORY_DEFS}

    for ev in events:
        if ev.category in cat_drop:
            cat_drop[ev.category] = min(_MAX_CATEGORY_DROP, cat_drop[ev.category] + ev.penalty)

    cat_scores = {k: 100 - v for k, v in cat_drop.items()}

    categories = [
        CategoryScore(name=en, name_ko=ko, icon=icon, score=cat_scores[key])
        for key, en, ko, icon in SCORE_CATEGORY_DEFS
    ]

    total = round(sum(c.score for c in categories) / len(categories))
    grade = _grade(total)
    focus = min(categories, key=lambda c: c.score) if categories else None
    if focus and focus.score >= 90:
        focus = None  # all green → no focus area needed

    return ScoreReport(total=total, grade=grade, categories=categories, focus_area=focus)


def _grade(total: int) -> str:
    if total >= 90: return "A"
    if total >= 80: return "B"
    if total >= 70: return "C"
    return "D"
