"""Detection Stats panel — Toss-style summary tiles + class histogram."""
from __future__ import annotations

from html import escape

from core.schema import FrameDetections


def render_stats(frames: list[FrameDetections]) -> str:
    if not frames:
        return _empty_state()

    total_dets = sum(len(f.detections) for f in frames)
    class_counts: dict[str, int] = {}
    confidences: list[float] = []
    for f in frames:
        for d in f.detections:
            class_counts[d.cls] = class_counts.get(d.cls, 0) + 1
            confidences.append(d.confidence)

    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0
    avg_per_frame = total_dets / len(frames) if frames else 0.0

    tiles = f"""
    <div class="dc-stat-grid">
      <div class="dc-stat-tile">
        <div class="lbl">Frames</div>
        <div class="val">{len(frames):,}</div>
        <div class="sub">분석된 프레임</div>
      </div>
      <div class="dc-stat-tile">
        <div class="lbl">Detections</div>
        <div class="val">{total_dets:,}</div>
        <div class="sub">{avg_per_frame:.1f} / frame</div>
      </div>
      <div class="dc-stat-tile">
        <div class="lbl">Avg conf</div>
        <div class="val">{avg_conf:.2f}</div>
        <div class="sub">평균 신뢰도</div>
      </div>
    </div>
    """

    # Class distribution
    sorted_cls = sorted(class_counts.items(), key=lambda kv: -kv[1])
    max_cnt = sorted_cls[0][1] if sorted_cls else 1
    bars = "\n".join(
        f"""
        <div class="dc-bar-h">
          <span class="lbl">{escape(name)}</span>
          <span class="track"><span class="fill" style="--bar-width: {(cnt/max_cnt)*100:.1f}%;"></span></span>
          <span class="n">{cnt}</span>
        </div>
        """
        for name, cnt in sorted_cls
    )

    histogram = f"""
    <div class="dc-card">
      <div class="dc-section-label">클래스별 검출 분포</div>
      {bars}
    </div>
    """

    note = """
    <div style="margin-top: 16px; text-align: center;
                font-size: 11px; color: var(--dc-text-low);
                letter-spacing: 0.04em;">
      YOLO26n · BDD100K + COCO · 9 classes
    </div>
    """

    return tiles + histogram + note


def _empty_state() -> str:
    return """
    <div class="dc-empty">
      <div class="big">📈</div>
      <div class="msg">검출 통계가 비어 있어요</div>
      <div class="sub">영상을 분석하면 객체 검출 결과가 표시됩니다</div>
    </div>
    """
