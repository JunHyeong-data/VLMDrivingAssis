"""Vision-Language Model interface (DriveVLM-style 3-stage CoT).

Implemented with Qwen2.5-VL-7B-Instruct (4-bit NF4 quantization, ~5GB VRAM).
Activate with: USE_REAL_VLM=1 python app.py

Required packages (pip install):
  pip install "transformers>=4.49" accelerate bitsandbytes "qwen-vl-utils>=0.0.8"

Note: app.py currently calls generate_coaching(event) without frame_bgr.
When frame_bgr is None, the model runs text-only using detection context.
For full visual coaching, also pass the BGR frame from app.py.
"""
from __future__ import annotations

import os
import re

import numpy as np
from PIL import Image

from core.schema import Coaching, Event, FrameDetections
from mock_data import mock_coaching

# ── Lazy singletons — loaded once on first USE_REAL_VLM=1 call ──────────────
_model = None
_processor = None
_MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"

_EVENT_CONTEXT = {
    "close_vehicle":   "전방 차량과의 거리가 위험 수준으로 좁혀진 상황",
    "pedestrian_risk": "보행자가 차도 방향으로 이동 중인 상황",
    "signal_change":   "교차로 신호등이 전환되는 상황",
    "complex_scene":   "여러 차량·보행자가 동시에 등장한 복잡한 교차로 상황",
}

_SEVERITY_KO = {"danger": "위험", "caution": "주의", "safe": "안전"}

_SYSTEM_PROMPT = """\
당신은 초보운전자를 위한 주행 코칭 AI입니다. 블랙박스 프레임을 분석하여 DriveVLM 방식의 3단계 코칭을 작성합니다.
반드시 아래 형식을 정확히 지켜 한국어로만 답변하세요. 형식 외의 내용은 출력하지 마세요.

[상황묘사]
(2~3문장으로 화면에 보이는 도로 상황을 객관적으로 묘사)

[위험분석]
(초보운전자 관점에서 위험 요소와 사고 가능성을 2~3문장으로 분석)

[행동제안]
(운전자가 즉시 취해야 할 행동을 1) 2) 3) 형식으로 3단계 제안)"""


def _load_model():
    """Load Qwen2.5-VL-7B with 4-bit NF4 quantization. Called once, cached."""
    global _model, _processor
    if _model is not None:
        return

    import torch
    from transformers import (
        AutoProcessor,
        BitsAndBytesConfig,
        Qwen2_5_VLForConditionalGeneration,
    )

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,  # 추가 메모리 절약 (~0.5GB)
    )
    _model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        _MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
    )
    _processor = AutoProcessor.from_pretrained(_MODEL_ID)


def _bgr_to_pil(frame_bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR frame to PIL RGB image."""
    return Image.fromarray(frame_bgr[:, :, ::-1].astype(np.uint8))


def _build_user_text(event: Event, context: list[FrameDetections]) -> str:
    """Compose the text part of the user prompt from event + detection context."""
    ctx_desc = _EVENT_CONTEXT.get(event.type, event.title)
    severity = _SEVERITY_KO.get(event.severity, event.severity)

    lines = [
        f"감지된 이벤트: {ctx_desc}",
        f"위험도: {severity} | 발생 시각: {event.timestamp:.1f}초",
    ]

    # 주변 프레임에서 객체 정보 추출 (중간 프레임 기준)
    if context:
        mid = context[len(context) // 2]
        cls_counts: dict[str, int] = {}
        for d in mid.detections:
            cls_counts[d.cls] = cls_counts.get(d.cls, 0) + 1
        if cls_counts:
            obj_str = ", ".join(f"{cls} {n}대" for cls, n in cls_counts.items())
            lines.append(f"탐지된 객체: {obj_str}")

    lines.append("\n위 정보를 참고하여 이 블랙박스 프레임을 분석하세요.")
    return "\n".join(lines)


def _build_messages(
    event: Event,
    pil_image: Image.Image | None,
    context: list[FrameDetections],
) -> list[dict]:
    """Build the messages list for Qwen2.5-VL's chat template."""
    user_content = []
    if pil_image is not None:
        user_content.append({"type": "image", "image": pil_image})
    user_content.append({"type": "text", "text": _build_user_text(event, context)})

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _parse_sections(raw: str) -> tuple[str, str, str]:
    """Extract [상황묘사]/[위험분석]/[행동제안] sections from VLM output."""
    pat = re.compile(
        r'\[(상황묘사|위험분석|행동제안)\]\s*(.*?)(?=\[(?:상황묘사|위험분석|행동제안)\]|$)',
        re.DOTALL,
    )
    parts = {m.group(1): m.group(2).strip() for m in pat.finditer(raw)}

    if len(parts) == 3:
        return parts["상황묘사"], parts["위험분석"], parts["행동제안"]

    # 마커가 없으면 텍스트를 3등분해서 폴백
    chunk = max(len(raw) // 3, 1)
    return raw[:chunk].strip(), raw[chunk : chunk * 2].strip(), raw[chunk * 2 :].strip()


def generate_coaching(
    event: Event,
    frame_bgr=None,
    context: list[FrameDetections] | None = None,
    video_path: str | None = None,  # [김두훈] 추가 — frame_bgr 없을 때 직접 프레임 추출용
) -> Coaching:
    """Run the VLM on a single event frame and return 3-stage CoT output.

    Args:
        event: the driving event triggering the VLM call
        frame_bgr: optional BGR numpy frame (직접 넘길 경우)
        context: surrounding FrameDetections for temporal grounding
        video_path: 영상 파일 경로 — frame_bgr이 None일 때 event.frame_idx로 프레임 추출
    """
    if os.environ.get("USE_REAL_VLM") == "1":
        return _generate_real_coaching(event, frame_bgr, context or [], video_path)
    return mock_coaching(event)


# [김두훈] frame_bgr이 None이고 video_path가 있으면 직접 프레임을 추출하는 헬퍼
def _extract_frame(video_path: str, frame_idx: int):
    """video_path에서 frame_idx번째 프레임을 BGR numpy 배열로 반환."""
    import cv2
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def _generate_real_coaching(
    event: Event,
    frame_bgr,
    context: list[FrameDetections],
    video_path: str | None,  # [김두훈] 추가
) -> Coaching:
    """Call Qwen2.5-VL-7B-Instruct (4-bit NF4) with a DriveVLM 3-stage prompt."""
    import torch
    from qwen_vl_utils import process_vision_info

    _load_model()

    # [김두훈] frame_bgr이 없으면 video_path + frame_idx로 직접 추출
    if frame_bgr is None and video_path is not None:
        frame_bgr = _extract_frame(video_path, event.frame_idx)

    pil_image = _bgr_to_pil(frame_bgr) if frame_bgr is not None else None
    messages = _build_messages(event, pil_image, context)

    text = _processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = _processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cuda")

    with torch.no_grad():
        generated_ids = _model.generate(**inputs, max_new_tokens=400, do_sample=False)

    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
    raw = _processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    scene_description, scene_analysis, action_plan = _parse_sections(raw)
    return Coaching(
        event=event,
        scene_description=scene_description,
        scene_analysis=scene_analysis,
        action_plan=action_plan,
    )
