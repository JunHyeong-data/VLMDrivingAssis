"""Vision-Language Model interface (DriveVLM-style 3-stage CoT).

REPLACEMENT POINT (김두훈):
  When Qwen2.5-VL is integrated, set USE_REAL_VLM=1 and implement
  `_generate_real_coaching()` below. Output must follow the Coaching schema:
    ① scene_description  ② scene_analysis  ③ action_plan
"""
from __future__ import annotations

import os

from core.schema import Coaching, Event, FrameDetections
from mock_data import mock_coaching


def generate_coaching(
    event: Event,
    frame_bgr=None,
    context: list[FrameDetections] | None = None,
) -> Coaching:
    """Run the VLM on a single event frame and return 3-stage CoT output.

    Args:
        event: the driving event triggering the VLM call
        frame_bgr: optional BGR numpy frame (required for real VLM)
        context: surrounding FrameDetections for temporal grounding
    """
    if os.environ.get("USE_REAL_VLM") == "1":
        return _generate_real_coaching(event, frame_bgr, context or [])
    return mock_coaching(event)


def _generate_real_coaching(event: Event, frame_bgr, context: list[FrameDetections]) -> Coaching:
    """REPLACE ME — call Qwen2.5-VL with a 3-part prompt.

    Suggested prompt structure (from DriveVLM):
      ① Scene Description: "이 프레임에서 보이는 도로 상황을 한국어로 묘사하라."
      ② Scene Analysis:    "초보운전자 관점에서 위험 요소를 분석하라."
      ③ Action Planning:   "운전자가 즉시 취해야 할 행동을 3단계로 제안하라."

    Pass the event.type as context to bias the model toward the right concern.
    Return value must be a Coaching dataclass.
    """
    raise NotImplementedError(
        "Real VLM inference not wired up yet. Set USE_REAL_VLM=0 to use mock data, "
        "or implement core.vlm._generate_real_coaching()."
    )
