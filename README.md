<div align="center">

<img src="docs/img/logo.svg" width="80" alt="BackMirror">

# BackMirror

YOLO–VLM 기반 주행 영상 분석·피드백 시스템

![BackMirror 결과 리포트](docs/img/results.gif)

</div>

기존 ADAS·블랙박스는 실시간 경고와 기록에 그치고, 정작 "왜 위험했고 무엇을 바꿔야 하는지"
사후 코칭은 비어 있습니다.
<br>BackMirror는 블랙박스 영상 한 편을 받아, 위험했던 순간을 찾아
그 이유와 개선점을 한 페이지 코칭 리포트로 돌려줍니다. 
<br>경고를 넘어 코칭으로.


## 데모

업로드 → 검토 → 라이브 분석 → 리포트의 4단계로 진행됩니다.

| | |
|---|---|
| ![IDLE](docs/img/01_idle.png) | ![Ready](docs/img/02_ready.png) |
| 시작 화면 | 영상 검토 + 메타데이터 |
| ![Analyzing](docs/img/03_analyzing.png) | ![Results](docs/img/04_results.png) |
| 라이브 분석 (검출 박스 + 진행 상황) | 점수·코칭·주석 영상 리포트 |


## 실행

```bash
pip install -r requirements.txt
python app.py          # http://127.0.0.1:7865
```

검출은 `weights/` 의 학습된 가중치가 있으면 실제 YOLO로 동작합니다(기본 `yolo26s_best.pt`).
VLM 코칭은 기본적으로 목업으로 돌고, 실제 Qwen2.5-VL을 쓰려면 별도 의존성을 설치한 뒤 켭니다.

```bash
# 실제 검출 추적용
pip install ultralytics lap

# 실제 VLM 코칭 (Qwen2.5-VL-7B, 4-bit · 약 5GB VRAM)
pip install "transformers>=4.49" accelerate bitsandbytes "qwen-vl-utils>=0.0.8"
USE_REAL_VLM=1 python app.py
```

`USE_REAL_YOLO=0` 으로 강제 목업, `YOLO_MODEL=rtdert_best.pt` 등으로 모델을 바꿀 수 있습니다.
모델 없이 파이프라인만 확인하려면 `python scripts/smoke_pipeline.py`.


## 데이터셋

사전 라벨링된 두 데이터셋을 합쳐 학습했습니다. VZC는 BDD100K 클래스 체계에 맞게
신호등(traffic light)을 매핑·통합해, BDD에서 부족했던 소형 객체 학습 신호를 보강했습니다.

| 출처 | 이미지 | 어노테이션 | 역할 |
|---|---|---|---|
| BDD100K | 10,000 | 185,930 | 도로 주행 장면 |
| VZC Traffic-Light | 2,954 | 25,497 | 신호등 소형 객체 보완 |
| **합계 (road_mix_vzc)** | **12,954** | **211,427** | Train 8,842 / Val 2,512 / Test 1,600 |


## 모델 비교

네 모델 모두 COCO 사전학습(Ultralytics) 후 BDD+VZC로 fine-tuning 했습니다.
공통 설정은 50 epoch, Optimizer Auto(AdamW, lr≈7.7e-4), 기본 augmentation.

| 모델 | 계열 | 파라미터 | Precision | Recall | mAP@50 | mAP@50-95 | 추론(GPU) | 학습 |
|---|---|---|---|---|---|---|---|---|
| YOLO26n | CNN nano | ~2.4M | 0.575 | 0.356 | 0.381 | 0.208 | 2.1 ms | 3.4 h |
| YOLO26s | CNN small | ~10M | 0.618 | 0.441 | 0.473 | 0.265 | 2.2 ms | 4.0 h |
| YOLO26l | CNN large | ~28M | 0.700 | 0.495 | 0.545 | 0.315 | 16.8 ms | 8.0 h |
| RT-DETR-l | Transformer | ~32M | 0.683 | 0.517 | 0.566 | 0.324 | 10.6 ms | 11.6 h |

정확도는 RT-DETR-l이 가장 높았지만 추론·학습 비용이 큽니다. 서비스에는 정확도와
속도의 균형이 좋은 **YOLO26s**를 기본 모델로 선정했습니다.

한계로, motor·rider·bike 같은 소수 클래스에서 Recall이 낮게 나왔고 이는 데이터 불균형과
직접 연결됩니다. 전반적으로 Precision > Recall 경향이라, 오검출보다는 미검출(FN)에 가깝습니다.


## 분석 파이프라인

영상 전체에 무거운 VLM을 돌리지 않고, 검출·추적으로 위험 후보를 먼저 추린 뒤
그 순간에만 VLM을 호출해 비용을 줄입니다.

```
YOLO 검출 → 객체 추적·모션 이벤트 → 이벤트 추출 → VLM 코칭 → 점수 리포트
```

- **이벤트 추출** — bbox 크기(앞차 급접근), 보행자 위치, 신호 변화, 객체 수 급증 등 규칙 기반
- **VLM 코칭** — 추출된 이벤트마다 Qwen2.5-VL을 3단계로 호출 (상황 묘사 → 위험 분석 → 행동 제안)
- **점수 리포트** — 카테고리별 점수·등급과 함께 검출 박스·코칭이 입혀진 영상 출력

모듈 간 데이터는 `core/schema.py` 의 dataclass로 주고받습니다.


## 한계와 결론

객체 탐지 결과를 바탕으로 위험 상황의 원인과 주행 맥락을 설명하고, 단순 점수 제공을 넘어
사고 예방용 피드백 리포트의 가능성을 확인했습니다. 다만 분석 품질이 VLM 출력에 크게
의존해 부정확한 설명이 생성될 수 있고, 안정적인 결과를 위해 추가 프롬프트 엔지니어링과
후처리가 필요합니다. 또 GPU 성능·API 응답·네트워크 환경에 따라 실시간 분석 성능이
제한될 수 있습니다.


## 참고

- BDD100K — https://huggingface.co/datasets/dgural/bdd100k
- VZC Traffic-Light — https://huggingface.co/datasets/vzc-research-chapter/vzc-traffic-light-dataset
- Ultralytics RT-DETR — https://docs.ultralytics.com/models/rtdetr
- Y. Zhao et al., "DETRs Beat YOLOs on Real-time Object Detection," CVPR 2024.

---

자동차인공지능 수업 팀 프로젝트 — 이지원 (Detection) · 김두훈 (VLM) · 박준형 (UI/UX)
