"""Rule-based event extraction — the "smart filter" that decides when to call VLM.

Without this layer, we'd waste compute calling Qwen2.5-VL on every frame.
With it, VLM is only invoked at semantically interesting moments (5~10 per video).
"""
from __future__ import annotations

from core.schema import Detection, Event, FrameDetections

# Tuning knobs
_CLOSE_VEHICLE_AREA_RATIO = 0.18    # bbox area / frame area
_PEDESTRIAN_ROAD_Y_RATIO = 0.55     # pedestrian bbox top below this → on road
_OBJECT_COUNT_SURGE_DELTA = 4       # +N detections vs previous frame
_EVENT_COOLDOWN_FRAMES = 90         # debounce per event type (~3s at 30fps)
_PEDESTRIAN_BBOX_HEIGHT_MIN = 80    # ignore tiny far-away figures


def extract_events(frames: list[FrameDetections]) -> list[Event]:
    """Walk through frame detections and emit events when rules fire."""
    events: list[Event] = []
    last_fire: dict[str, int] = {}      # event_type -> last frame_idx fired
    prev_signal_count = 0
    prev_obj_count = 0

    for f in frames:
        area = f.width * f.height

        # Rule 1: close vehicle (large bbox)
        for d in f.detections:
            if d.cls in ("car", "truck", "bus"):
                bbox_area = (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1])
                if bbox_area / area >= _CLOSE_VEHICLE_AREA_RATIO:
                    if _cooldown_ok("close_vehicle", f.frame_idx, last_fire):
                        events.append(Event(
                            frame_idx=f.frame_idx,
                            timestamp=f.timestamp,
                            type="close_vehicle",
                            severity="danger",
                            title="앞차 급접근",
                            summary=f"전방 {d.cls} 화면 점유율 {bbox_area/area*100:.0f}%",
                            penalty=8,
                            category="distance",
                        ))
                        last_fire["close_vehicle"] = f.frame_idx
                    break

        # Rule 2: pedestrian on/near roadway
        for d in f.detections:
            if d.cls in ("person", "rider"):
                bbox_h = d.bbox[3] - d.bbox[1]
                if bbox_h < _PEDESTRIAN_BBOX_HEIGHT_MIN:
                    continue
                # heuristic: top of pedestrian bbox is below center → likely on road
                if d.bbox[1] / f.height >= _PEDESTRIAN_ROAD_Y_RATIO:
                    if _cooldown_ok("pedestrian_risk", f.frame_idx, last_fire):
                        events.append(Event(
                            frame_idx=f.frame_idx,
                            timestamp=f.timestamp,
                            type="pedestrian_risk",
                            severity="danger",
                            title="보행자 도로 진입",
                            summary="우측 인도→차도 방향 이동 감지",
                            penalty=10,
                            category="pedestrian",
                        ))
                        last_fire["pedestrian_risk"] = f.frame_idx
                    break

        # Rule 3: traffic-light state shift (simplified: count goes 0 ↔ 1)
        signal_count = sum(1 for d in f.detections if d.cls == "traffic light")
        if signal_count != prev_signal_count and signal_count > 0:
            if _cooldown_ok("signal_change", f.frame_idx, last_fire):
                events.append(Event(
                    frame_idx=f.frame_idx,
                    timestamp=f.timestamp,
                    type="signal_change",
                    severity="caution",
                    title="신호 전환 구간",
                    summary="교차로 신호등 인지 필요",
                    penalty=4,
                    category="signal",
                ))
                last_fire["signal_change"] = f.frame_idx
        prev_signal_count = signal_count

        # Rule 4: complex scene (object count surges)
        obj_count = len(f.detections)
        if obj_count - prev_obj_count >= _OBJECT_COUNT_SURGE_DELTA:
            if _cooldown_ok("complex_scene", f.frame_idx, last_fire):
                events.append(Event(
                    frame_idx=f.frame_idx,
                    timestamp=f.timestamp,
                    type="complex_scene",
                    severity="caution",
                    title="복잡 교차로 진입",
                    summary=f"동시 객체 {obj_count}개 검출",
                    penalty=5,
                    category="speed",
                ))
                last_fire["complex_scene"] = f.frame_idx
        prev_obj_count = obj_count

    return events


def _cooldown_ok(event_type: str, frame_idx: int, last_fire: dict[str, int]) -> bool:
    return (frame_idx - last_fire.get(event_type, -10**9)) >= _EVENT_COOLDOWN_FRAMES
