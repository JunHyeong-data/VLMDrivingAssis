"""Data contracts shared across modules.

These dataclasses define the interface between teammates' modules.
Do not change field names without coordinating with the team.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# 9 classes from BDD100K + COCO subset
CLASS_NAMES = [
    "bike", "bus", "car", "motor", "person",
    "rider", "traffic light", "traffic sign", "truck",
]

Severity = Literal["safe", "caution", "danger"]


@dataclass
class Detection:
    """One bounding box from YOLO/RT-DETR."""
    cls: str                       # one of CLASS_NAMES
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2) in pixel coords
    confidence: float              # 0.0 ~ 1.0


@dataclass
class FrameDetections:
    """All detections from a single video frame."""
    frame_idx: int
    timestamp: float               # seconds from start
    width: int
    height: int
    detections: list[Detection] = field(default_factory=list)


@dataclass
class Event:
    """A meaningful driving event extracted from detection sequence."""
    frame_idx: int
    timestamp: float
    type: str                      # e.g. "close_vehicle", "pedestrian_risk"
    severity: Severity
    title: str                     # Korean short label, e.g. "앞차 급접근"
    summary: str                   # one-line description for timeline tooltip
    penalty: int                   # points deducted from category
    category: str                  # which SCORE_CATEGORY this event affects


@dataclass
class Coaching:
    """3-stage CoT output from VLM (DriveVLM-style)."""
    event: Event
    scene_description: str         # ① 상황 묘사
    scene_analysis: str            # ② 위험 분석
    action_plan: str               # ③ 행동 제안


@dataclass
class CategoryScore:
    name: str                      # e.g. "Safe distance"
    name_ko: str                   # e.g. "안전거리"
    icon: str                      # emoji
    score: int                     # 0~100


@dataclass
class ScoreReport:
    total: int                     # 0~100
    grade: str                     # "A", "B", "C", "D"
    categories: list[CategoryScore]
    focus_area: CategoryScore | None  # weakest category (or None if all >= 90)


# Five scoring categories — change here to retune the rubric
SCORE_CATEGORY_DEFS = [
    ("signal",     "Signal awareness",  "신호 인지",   "🚦"),
    ("lane",       "Lane discipline",   "차선 준수",   "🛣️"),
    ("pedestrian", "Pedestrian caution", "보행자 주의", "🚸"),
    ("speed",      "Speed management",  "속도 관리",   "⚡"),
    ("distance",   "Safe distance",     "안전거리",    "🚗"),
]
