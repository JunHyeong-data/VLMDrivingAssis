# DriveCoach AI

YOLO 기반 실시간 객체 검출 + VLM(Qwen2.5-VL) 기반 상황 분석을 결합한
**이벤트 기반 하이브리드 주행 영상 분석 시스템**.

> FVE3011 자동차인공지능 Term Project · Team DriveCoach
> 이지원 (Detection) · 박준형 (UI/UX) · 김두훈 (VLM)

---

## 빠른 시작

```bash
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:7860 접속
```

파이프라인 전체 동작을 영상 없이 검증하려면:

```bash
python scripts/smoke_pipeline.py
```

## 아키텍처 — 4-Phase 이벤트 기반

```
Phase 1: YOLO 전체 스캔 ─────────── core/detector.py
        프레임별 객체 검출을 FrameDetections 리스트로 수집

Phase 2: 이벤트 추출 (Rule-based) ─ core/event_extractor.py
        bbox 크기 / 보행자 위치 / 신호 변화 / 객체수 급증 → Event

Phase 3: VLM 코칭 (이벤트만) ───── core/vlm.py
        DriveVLM-style 3-stage CoT:
          ① Scene description  ② Scene analysis  ③ Action plan

Phase 4: 종합 ─────────────────── core/scorer.py + ui/*
        카테고리별 점수 + Grade + Focus area + 주석 영상
```

VLM은 영상당 **5~10회**만 호출 → 실시간 가능 + 품질 확보.

## 폴더 구조

```
.
├── app.py                      # Gradio 3-panel 메인 앱
├── core/
│   ├── schema.py               # 모든 모듈 공통 데이터 contract
│   ├── detector.py             # ⚙️ YOLO 교체 지점 (이지원)
│   ├── vlm.py                  # ⚙️ Qwen2.5-VL 교체 지점 (김두훈)
│   ├── event_extractor.py      # Rule-based 이벤트 추출
│   ├── scorer.py               # 카테고리별 점수 + Grade
│   └── overlay.py              # OpenCV bbox + HUD bar + alert flash
├── ui/
│   ├── theme.py                # 다크 테마 + 전체 CSS
│   ├── coaching_panel.py       # 채팅 버블 스타일 VLM 코칭
│   ├── score_panel.py          # 원형 게이지 + 카테고리 바 + Focus area
│   ├── stats_panel.py          # 검출 통계 (count, conf, 분포)
│   └── timeline.py             # 영상 하단 리스크 타임라인
├── mock_data.py                # 한국어 코칭 + 가짜 YOLO bbox
└── scripts/
    └── smoke_pipeline.py       # 전체 파이프라인 단독 검증
```

## 팀원 교체 지점

실제 모델이 준비되면 **두 곳만** 수정하면 된다.
다운스트림(이벤트 추출 → 스코어 → UI)은 `core/schema.py` 의
dataclass 시그니처만 지키면 영향을 받지 않는다.

### 이지원 — YOLO26n / RT-DETR

`core/detector.py::_detect_real_frame()` 구현 후:

```bash
USE_REAL_YOLO=1 python app.py
```

입력: `frame: np.ndarray (BGR)`
출력: `FrameDetections` (schema.py 참고, 클래스명은 `CLASS_NAMES` 9종 중 하나)

### 김두훈 — Qwen2.5-VL

`core/vlm.py::_generate_real_coaching()` 구현 후:

```bash
USE_REAL_VLM=1 python app.py
```

3단계 프롬프트 구조(DriveVLM 논문 차용):

1. **Scene Description** — "이 프레임의 도로 상황을 한국어로 묘사하라"
2. **Scene Analysis** — "초보운전자 관점에서 위험 요소를 분석하라"
3. **Action Planning** — "운전자가 즉시 취할 행동을 3단계로 제안하라"

`event.type` 을 컨텍스트로 전달해 모델을 해당 위험에 집중시킬 수 있다.

## 채점 기준 대응 (총 100점)

| 항목 | 점수 | 본 프로젝트 대응 |
|---|---|---|
| 학습 데이터 | 30 | BDD100K + COCO, 9 classes, 분포 시각화는 `Detection Stats` 탭 |
| CNN 모델 | 30 | YOLO26n vs RT-DETR 비교, 데이터 증강 ablation (이지원) |
| SW 개발 | 20 | 본 Gradio 앱 — 3-panel, HUD, 타임라인, 다크 테마 |
| 분석 | 20 | 학습/처리속도/결론 — 최종 PPT |

> "**YOLO+VLM 조합은 좋다. 진짜 사용할 것 같은 앱을 만들어라.**" — 교수님

이 UI는 Tesla / Nauto / Motive 의 UX 패턴을 차용해 다음을 노린다:

- **다크 자동차 테마** + 미니멀 정보 밀도 → 실제 양산 앱 인상
- **Risk Timeline** → "내 주행 전체"를 한눈에
- **Goal Gradient Effect**: 82점 게이지 → "다음엔 더"
- **Focus Area 콜아웃**: 가장 낮은 카테고리 강조 → 재업로드 유도
- **HUD bar**: 차량 OEM 인포테인먼트 톤

## 데모 시나리오

1. 블랙박스 영상 업로드
2. ▶ **Analyze Drive** 클릭
3. 진행률 바 (YOLO → 이벤트 → VLM → 렌더)
4. 좌측: bbox + HUD가 입혀진 영상 + 하단 Risk Timeline
5. 우측 탭:
   - **💬 Coaching** — 시간순 채팅 버블, 위험도별 색상, CoT 3단계
   - **📊 Score** — 원형 게이지 + 카테고리 바 + Focus area
   - **📈 Detection Stats** — 검출 카운트, 평균 신뢰도, 클래스 분포

## 확장 로드맵 (발표 슬라이드용)

- 보험사 연계 UBI(Usage-Based Insurance) 점수 데이터
- 한국 블랙박스 보급률 88.9% (세계 1위) → 시장 잠재력
- 운전면허 학원 B2B
- TTS 실시간 음성 코칭
- 모바일 (DEVA 22~30FPS 실증)

## 참고 문헌

- DriveVLM (Tsinghua, 2024) — CoT 3-stage prompting
- DriveVLM-Dual (2024) — VLM + classical pipeline hybrid
- DEVA (2024) — mobile real-time blackbox analysis
