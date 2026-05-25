"""Realistic mock outputs so the UI runs end-to-end without trained models.

Used by:
  - core.detector when YOLO weights are not available
  - core.vlm when Qwen2.5-VL is not loaded

When the real models land, mock_data is bypassed via env vars
(USE_REAL_YOLO=1, USE_REAL_VLM=1) — see core/detector.py and core/vlm.py.
"""
from __future__ import annotations

import random
from core.schema import Detection, FrameDetections, Coaching, Event


# ---------- Mock YOLO ----------

# Hand-tuned trajectories that look plausible on a 1280x720 dashcam frame.
# Each entry: (class, base_bbox, drift_per_frame, confidence)
_MOCK_TRACKS = [
    ("car",           (520, 280, 760, 460),  ( -1,  2,  -1,  2),  0.92),  # front car, slowly approaching
    ("car",           (200, 340, 360, 440),  (  2,  1,   2,  1),  0.88),  # left lane car
    ("car",           (900, 360, 1060, 460), ( -2,  1,  -2,  1),  0.84),  # right lane car
    ("traffic light", (610, 100, 670, 180),  (  0,  0,   0,  0),  0.95),  # static signal
    ("traffic sign",  (1100, 150, 1180, 240),(  0,  0,   0,  0),  0.79),
    ("person",        (180, 420, 230, 560),  (  1,  0,   1,  0),  0.86),  # sidewalk pedestrian
]


def mock_detect(frame_idx: int, fps: float, width: int, height: int) -> FrameDetections:
    """Generate plausible bounding boxes for one frame."""
    dets: list[Detection] = []
    for cls, base, drift, conf in _MOCK_TRACKS:
        x1 = max(0, min(width - 10, base[0] + drift[0] * frame_idx))
        y1 = max(0, min(height - 10, base[1] + drift[1] * frame_idx))
        x2 = max(x1 + 10, min(width, base[2] + drift[2] * frame_idx))
        y2 = max(y1 + 10, min(height, base[3] + drift[3] * frame_idx))
        # Small confidence jitter
        c = max(0.3, min(0.99, conf + random.uniform(-0.04, 0.04)))
        dets.append(Detection(cls=cls, bbox=(int(x1), int(y1), int(x2), int(y2)), confidence=c))

    # Add a pedestrian that walks into the road around frame 90 (event trigger)
    if 90 <= frame_idx <= 140:
        crossing_x = 400 + (frame_idx - 90) * 6
        dets.append(Detection(
            cls="person",
            bbox=(crossing_x, 380, crossing_x + 60, 540),
            confidence=0.91,
        ))

    return FrameDetections(
        frame_idx=frame_idx,
        timestamp=frame_idx / fps,
        width=width,
        height=height,
        detections=dets,
    )


# ---------- Mock VLM coaching ----------
# Keyed by event.type — gives realistic Korean CoT-style output.

MOCK_COACHING_BY_TYPE: dict[str, dict[str, str]] = {
    "close_vehicle": {
        "scene_description": (
            "전방 약 8~10m 거리에 차량이 위치하고 있으며, 화면 점유율이 30% 이상으로 "
            "급격히 증가하고 있습니다. 현재 차간거리가 안전기준 이하로 좁혀지는 상황입니다."
        ),
        "scene_analysis": (
            "앞차와의 거리가 권장 안전거리(속도 km/h ÷ 2 = m 기준)보다 짧습니다. "
            "앞차가 급제동할 경우 추돌 사고 위험이 매우 높습니다. "
            "초보운전자의 경우 반응시간이 0.8~1.2초로 길어 위험이 가중됩니다."
        ),
        "action_plan": (
            "1) 가속 페달에서 발을 떼고 엔진 브레이크로 감속하세요. "
            "2) 최소 2초 룰(앞차 통과 후 2초 경과)을 확보하세요. "
            "3) 우천 시에는 3초, 야간에는 4초까지 거리를 늘리는 것을 권장합니다."
        ),
    },
    "pedestrian_risk": {
        "scene_description": (
            "우측 인도에서 보행자가 도로 방향으로 이동 중이며, "
            "횡단보도 약 30m 전방에서 횡단 의도가 감지됩니다. "
            "차량과의 충돌 예측 시간(TTC)이 빠르게 감소하고 있습니다."
        ),
        "scene_analysis": (
            "보행자는 운전자의 예측보다 빠르게 도로에 진입할 수 있습니다. "
            "특히 어린이와 노인은 차량 속도 인지가 어렵습니다. "
            "도로교통법상 횡단보도 일시정지 의무가 있으며, 위반 시 보행자 사고는 100% 운전자 과실에 가깝습니다."
        ),
        "action_plan": (
            "1) 즉시 가속을 멈추고 브레이크에 발을 올려 준비하세요(커버링 브레이크). "
            "2) 보행자와 시선을 마주치고 의도를 확인하세요. "
            "3) 횡단보도 정지선 앞에서 완전히 정지하고 보행자가 안전하게 횡단을 마칠 때까지 대기하세요."
        ),
    },
    "signal_change": {
        "scene_description": (
            "전방 교차로 신호등이 황색으로 전환되었습니다. "
            "교차로까지 남은 거리는 약 20~25m이며, 정지선 통과 여부 판단이 필요한 상황입니다."
        ),
        "scene_analysis": (
            "황색 신호는 '주의'가 아닌 '정지'가 원칙입니다(도로교통법 시행규칙 별표2). "
            "딜레마 존(Dilemma Zone)에서 무리한 통과는 신호위반 + 교차로 내 측면충돌 위험을 동시에 야기합니다. "
            "특히 좌회전 차량이 출발 대기 중일 가능성이 있습니다."
        ),
        "action_plan": (
            "1) 정지선까지 안전하게 멈출 수 있다면 부드럽게 제동하세요. "
            "2) 이미 정지선을 지났거나 급제동이 위험한 경우에만 신속하게 교차로를 통과하세요. "
            "3) 평소 황색신호 대비 거리를 의식적으로 인지하는 습관이 중요합니다."
        ),
    },
    "complex_scene": {
        "scene_description": (
            "교차로 진입 구간으로, 차량 5대 이상, 보행자 2명, "
            "교통신호 1개가 동시에 검출되고 있습니다. "
            "정보 처리 부하가 급격히 증가하는 시점입니다."
        ),
        "scene_analysis": (
            "복잡한 교차로는 초보운전자에게 가장 위험한 구간입니다. "
            "터널 비전(Tunnel Vision) 현상으로 시야가 좁아져 측면/후방 정보를 놓치기 쉽습니다. "
            "여러 변수가 동시에 발생하면 의사결정 지연이 사고로 이어집니다."
        ),
        "action_plan": (
            "1) 교차로 진입 전 충분히 감속하여 판단 시간을 확보하세요. "
            "2) 좌우 사이드미러를 의도적으로 확인하세요(3초 룰). "
            "3) 우선순위: 보행자 → 직진차량 → 신호 → 좌회전차량 순으로 인지하세요."
        ),
    },
}


def mock_coaching(event: Event) -> Coaching:
    """Look up canned CoT output for the event type."""
    template = MOCK_COACHING_BY_TYPE.get(event.type, MOCK_COACHING_BY_TYPE["close_vehicle"])
    return Coaching(
        event=event,
        scene_description=template["scene_description"],
        scene_analysis=template["scene_analysis"],
        action_plan=template["action_plan"],
    )
