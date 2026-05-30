"""BackMirror AI landing page — v3 editorial / cinematic.

The IDLE screen is a 7-section marketing page based on the v3 HTML mock
(BackMirror v3.html — real photos + SVG annotations):

    1. Fixed top nav (brand + primary CTA)
    2. Hero — split dual-frame (raw / AI-analyzed) + bottom stat strip
    3. Upload band — copy + bullets + custom dropzone (.dz)
    4. What we see — 3 capability tiles with photo + SVG overlay
    5. Sample report — timeline + 3 key moments + score footer
    6. Numbers — 4-tile proof strip
    7. CTA — fullbleed bg photo + glow headline
    8. Footer — 4-col links + bar

All v3 styles live under `.dc-v3-root` (see theme.py). The visible
`.dz` is just HTML; an `init` JS in app.py bridges its click/drop to
the hidden `gr.File` so Gradio still handles the actual upload.
"""
from __future__ import annotations

import re


# ─── Shared bits ──────────────────────────────────────────────

def _arrow_svg() -> str:
    return ('<svg class="arrow" viewBox="0 0 12 12" fill="none" '
            'stroke="currentColor" stroke-width="1.6">'
            '<path d="M2 6h8M7 2l4 4-4 4"/></svg>')


# BackMirror logo — a car side mirror: rounded glass on an arm reaching back
# from the car body, with the reflected road converging to a vanishing-point
# dot (the moment the AI looks back at).
_BRAND_SVG = (
    '<svg viewBox="0 0 32 32" fill="none">'
    '<rect x="10.5" y="7" width="17" height="16" rx="5.5" stroke="#00E59A" stroke-width="1.8"/>'
    '<path d="M10.5 15 L5 17" stroke="#00E59A" stroke-width="1.8" stroke-linecap="round"/>'
    '<path d="M5 13 L5 21" stroke="#00E59A" stroke-width="1.8" stroke-linecap="round"/>'
    '<path d="M15 19 L18 12.5" stroke="#00E59A" stroke-width="1.3" stroke-linecap="round"/>'
    '<path d="M22 19 L19 12.5" stroke="#00E59A" stroke-width="1.3" stroke-linecap="round"/>'
    '<circle cx="18.5" cy="11.3" r="1.35" fill="#00E59A"/>'
    '</svg>'
)


# (role, 이름, 로마자, 한 줄 소개, 역량 칩[첫 칩이 lead]) — team_screen_html()이 사용.
_TEAM_MEMBERS = [
    ("Detection", "이지원", "Jiwon Lee",
     "YOLO26n / RT-DETR 객체 검출 모델 학습·비교, 데이터 증강 실험",
     ["YOLO26n", "RT-DETR", "BDD100K"]),
    ("UI / UX", "박준형", "JunHyeong Park",
     "4-state 시네마틱 앱, 디자인 시스템, 실시간 분석·리포트 화면 설계",
     ["Gradio", "Design System", "Report UX"]),
    ("VLM", "김두훈", "Duhum Kim",
     "Qwen2.5-VL 기반 3단계 추론 코칭(상황→위험→행동) 설계·연동",
     ["Qwen2.5-VL", "DriveVLM", "CoT"]),
]

# role → 멤버 카드 아이콘 (m-role-ic). approach 플로우의 같은 단계 아이콘과 짝.
_MEMBER_ICONS = {
    "Detection": '<svg viewBox="0 0 24 24"><path d="M3 3 L3 8 M3 3 L8 3 M21 3 L21 8 M21 3 L16 3 M3 21 L3 16 M3 21 L8 21 M21 21 L21 16 M21 21 L16 21"/><rect x="9" y="10" width="6" height="5" stroke-dasharray="2 2"/></svg>',
    "UI / UX": '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="1.5"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="15" y2="21"/></svg>',
    "VLM": '<svg viewBox="0 0 24 24"><path d="M4 5 h16 v11 h-9 l-5 4 v-4 h-2 z"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="12" x2="13" y2="12"/></svg>',
}


def team_screen_html() -> str:
    """'팀 소개' standalone page — cinematic hero → 4단계 approach → 멤버 카드.

    Scoped under `.team2` so its styles never touch the FAQ page, which shares
    the base `.team-hero` / `.team-foot` classes. Reached via the '팀 소개' nav
    link (dc-team-link → dc-team-hit). The brand and #team-back-btn both return
    to IDLE via dc-home-hit."""
    cards = []
    for i, (role, name, name_en, contrib, tags) in enumerate(_TEAM_MEMBERS, 1):
        chips = "".join(
            f'<span class="chip{" lead" if j == 0 else ""}">{t}</span>'
            for j, t in enumerate(tags)
        )
        cards.append(f'''
      <article class="member">
        <div class="m-top">
          <div class="m-role-ic">{_MEMBER_ICONS.get(role, "")}</div>
          <span class="m-idx">{i:02d} / 03</span>
        </div>
        <div class="m-body">
          <div class="m-role">{role}</div>
          <h3 class="m-name">{name}<span class="en">{name_en}</span></h3>
          <p class="m-desc">{contrib}</p>
          <div class="m-stack">{chips}</div>
        </div>
      </article>''')
    members = "".join(cards)
    return f"""
<div class="dc-v3-root team-root team2">
  <div class="team-bar">
    {_brand_html()}
    <button class="history-back" type="button" id="team-back-btn" aria-label="홈으로 돌아가기">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12 L5 12 M11 6 L5 12 L11 18"/>
      </svg>
      홈
    </button>
  </div>

  <section class="team-hero">
    <div class="team-hero-inner">
      <span class="team-kicker">우리가 만드는 것 / THE TEAM</span>
      <h1>운전을 가르치는<br/><span class="accent">백미러.</span></h1>
      <p class="lede">
        BackMirror는 블랙박스 영상 한 편에서 <b>위험했던&nbsp;순간</b>을 찾아냅니다.
        그리고 <b>왜&nbsp;위험했는지</b>, <b>다음에&nbsp;뭘&nbsp;바꿀지</b>까지 짚어주는 운전 코치예요.
        점수만 매기는 도구가 아니라, 운전을 돌아보고 싶은 누구에게나 곁에서 함께 봐주는 코치입니다.
      </p>
      <div class="team-hero-meta">
        <div class="hm"><span class="n">4단계</span><span class="l">검출 · 이벤트 · 코칭 · 리포트</span></div>
        <div class="hm"><span class="n">3명</span><span class="l">Detection · UI/UX · VLM</span></div>
        <div class="hm"><span class="n">1색</span><span class="l">Signal Green</span></div>
      </div>
    </div>
    <div class="team-scroll-cue"><span>Scroll</span><span class="line"></span></div>
  </section>

  <section class="team-approach">
    <div class="approach-head">
      <span class="label">접근 방식 / HOW IT WORKS</span>
      <h2>한 편의 영상이 <em>코칭&nbsp;한&nbsp;줄</em>이 되기까지.</h2>
      <p>네 단계를 거칩니다. 각 단계는 다음 단계가 더 정확해지도록 맥락을 넘겨줘요. 마지막에 남는 건 숫자가 아니라, 다음 주행에서 바꿔볼 수 있는 한 문장입니다.</p>
    </div>

    <div class="approach-flow">
      <div class="af-step">
        <span class="af-num">01 · Detect</span>
        <div class="af-ic"><svg viewBox="0 0 24 24"><path d="M3 3 L3 8 M3 3 L8 3 M21 3 L21 8 M21 3 L16 3 M3 21 L3 16 M3 21 L8 21 M21 21 L21 16 M21 21 L16 21"/><rect x="9" y="10" width="6" height="5" stroke-dasharray="2 2"/></svg></div>
        <h3>객체 검출</h3>
        <p>차량·보행자·이륜차·차선·신호를 프레임마다 찾아냅니다.</p>
        <div class="af-tag">YOLO26n · RT-DETR</div>
      </div>
      <div class="af-step">
        <span class="af-num">02 · Event</span>
        <div class="af-ic"><svg viewBox="0 0 24 24"><line x1="3" y1="20" x2="21" y2="20"/><rect x="5" y="12" width="3" height="8"/><rect x="10" y="6" width="3" height="14"/><rect x="15" y="14" width="3" height="6"/></svg></div>
        <h3>이벤트 추출</h3>
        <p>검출 결과를 규칙으로 읽어 급제동·차선 이탈 같은 위험 구간을 가려냅니다.</p>
        <div class="af-tag">Rule-based</div>
      </div>
      <div class="af-step">
        <span class="af-num">03 · Coach</span>
        <div class="af-ic"><svg viewBox="0 0 24 24"><path d="M4 5 h16 v11 h-9 l-5 4 v-4 h-2 z"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="12" x2="13" y2="12"/></svg></div>
        <h3>3단계 코칭</h3>
        <p>장면 묘사 → 원인 분석 → 행동 제안. VLM이 그 순간을 사람처럼 설명합니다.</p>
        <div class="af-tag">Qwen2.5-VL</div>
      </div>
      <div class="af-step">
        <span class="af-num">04 · Report</span>
        <div class="af-ic"><svg viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg></div>
        <h3>점수 리포트</h3>
        <p>카테고리별 점수와 핵심 순간, 다음 주행을 위한 코칭을 한 장으로 정리합니다.</p>
        <div class="af-tag">Score · Summary</div>
      </div>
    </div>

    <p class="approach-diff">TMAP UBI는 <b>운전&nbsp;점수</b>를 줍니다.<br/>
       BackMirror는 <span class="accent">왜&nbsp;위험했고 다음에&nbsp;뭘&nbsp;바꿀지</span>를 줍니다.</p>
  </section>

  <section class="team-members">
    <div class="members-head">
      <div>
        <span class="label">팀 / WHO WE ARE</span>
        <h2>세 사람이 한 대를 만듭니다.</h2>
      </div>
      <span class="hint">BackMirror · 2026</span>
    </div>
    <div class="members-grid">{members}</div>
  </section>

  <section class="team-closing">
    <p class="tc-quote">좋은 코치는 점수를 매기지 않습니다.<br/><span class="accent">다음을 알려줍니다.</span></p>
    <p class="tc-sub">BackMirror가 만들고 싶은 건 평가가 아니라, 다음 주행이 조금 더 안전해지는 한 문장입니다.</p>
  </section>

  <footer class="team-foot">© 2026 BACKMIRROR · 운전을 다시 보는 모두를 위한 코치</footer>
</div>
"""


def faq_screen_html() -> str:
    """'자주 묻는 질문' standalone page — 시네마틱 아코디언 (.faq2 네임스페이스).

    모든 스타일이 `.faq2` 하위로 스코프돼 팀 페이지의 .team-*/.team2 와 충돌하지
    않음. dc-faq-link → dc-faq-hit 로 도달하고, brand 와 #faq-back-btn 은
    dc-home-hit 으로 IDLE 복귀. 답변 레이아웃이 문항마다 달라(Q2의 3단계 리스트
    등) 콘텐츠는 의도적으로 하드코딩."""
    chev = ('<span class="q-chevron"><svg viewBox="0 0 24 24">'
            '<path d="M6 9 L12 15 L18 9" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg></span>')
    return f"""
<div class="dc-v3-root faq2">
  <div class="faq2-bar">
    {_brand_html()}
    <button class="history-back" type="button" id="faq-back-btn" aria-label="홈으로 돌아가기">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12 L5 12 M11 6 L5 12 L11 18"/>
      </svg>
      홈
    </button>
  </div>

  <section class="faq2-hero">
    <div class="faq2-hero-inner">
      <span class="faq2-kicker">Q &amp; A / FREQUENTLY ASKED</span>
      <h1>자주 묻는<br/><span class="accent">질문.</span></h1>
      <p class="lede">
        BackMirror가 영상을 어떻게 보고, 무엇을 지키며, 점수를 어떻게 매기는지 —
        <b>가장&nbsp;많이&nbsp;받은&nbsp;질문</b>을 모았습니다.
      </p>
    </div>
  </section>

  <section class="faq2-list">
    <div class="faq2-list-head">
      <span class="label">자주 묻는 질문 / FAQ</span>
      <span class="count">05 Questions</span>
    </div>

    <details class="faq2-item">
      <summary>
        <span class="q-idx">01</span>
        <span class="q-text">내 블랙박스 영상은 어디에 저장되나요?</span>
        {chev}
      </summary>
      <div class="a-wrap">
        <div class="a-rail"></div>
        <p class="a-text">
          분석은 사용자 PC에서 <b>로컬로 처리</b>됩니다. 영상이 외부 서버로 전송되지 않으며,
          분석 기록은 본인 기기(<b>~/.drivingassis</b>)에만 저장돼요.
        </p>
      </div>
    </details>

    <details class="faq2-item">
      <summary>
        <span class="q-idx">02</span>
        <span class="q-text">BackMirror는 영상을 어떻게 분석하나요?</span>
        {chev}
      </summary>
      <div class="a-wrap">
        <div class="a-rail"></div>
        <div class="a-text">
          세 단계를 거칩니다.
          <ul class="a-steps">
            <li><span class="st-n">①</span><span><b>YOLO 검출</b> — 차량·보행자·신호를 프레임 단위로 찾아냅니다.</span></li>
            <li><span class="st-n">②</span><span><b>이벤트 추출</b> — 룰 기반으로 급제동·차선&nbsp;이탈·차간거리&nbsp;부족 같은 위험 이벤트를 가려냅니다.</span></li>
            <li><span class="st-n">③</span><span><b>VLM 코칭</b> — 그 순간을 <span class="sig">상황 → 위험 → 행동</span> 3단계로 해석해 코칭 문장을 만듭니다.</span></li>
          </ul>
        </div>
      </div>
    </details>

    <details class="faq2-item">
      <summary>
        <span class="q-idx">03</span>
        <span class="q-text">TMAP 운전점수랑 뭐가 다른가요?</span>
        {chev}
      </summary>
      <div class="a-wrap">
        <div class="a-rail"></div>
        <p class="a-text">
          TMAP UBI는 <b>'몇 점'</b>이라는 결과를 줍니다. BackMirror는
          <span class="sig">왜&nbsp;위험했고</span> 다음 주행에서 <span class="sig">무엇을&nbsp;바꿔야&nbsp;하는지</span>라는
          맥락 코칭을 줍니다. 점수가 아니라 코치예요.
        </p>
      </div>
    </details>

    <details class="faq2-item">
      <summary>
        <span class="q-idx">04</span>
        <span class="q-text">점수는 어떻게 매겨지나요?</span>
        {chev}
      </summary>
      <div class="a-wrap">
        <div class="a-rail"></div>
        <p class="a-text">
          신호·차선·보행자·속도·안전거리 <b>5개 카테고리</b>가 각 100점에서 시작하고,
          위험 이벤트마다 감점됩니다. 카테고리별 <b>최대 감점 폭은 제한</b>돼,
          한 종류의 실수가 점수를 완전히 무너뜨리지 않도록 했어요.
        </p>
      </div>
    </details>

    <details class="faq2-item">
      <summary>
        <span class="q-idx">05</span>
        <span class="q-text">객체를 추적(tracking)하나요?</span>
        {chev}
      </summary>
      <div class="a-wrap">
        <div class="a-rail"></div>
        <p class="a-text">
          현재는 <b>프레임 단위 검출</b> 기반입니다. 같은 객체에 ID를 부여하는 추적(ByteTrack 등)은
          로드맵에 있으며, 지금은 <span class="sig">추적된 척하는 가짜 ID를 보여주지 않습니다.</span>
        </p>
      </div>
    </details>
  </section>

  <section class="faq2-closing">
    <p class="tc-quote">궁금한 게 더 있나요?<br/><span class="accent">영상 한 편이면 충분해요.</span></p>
    <p class="tc-sub">대부분의 질문은 직접 분석해보면 풀립니다. 블랙박스 영상을 올리면 BackMirror가 그 자리에서 답을 보여드려요.</p>
  </section>

  <footer class="faq2-foot">© 2026 BACKMIRROR · 운전을 다시 보는 모두를 위한 코치</footer>
</div>
"""


def _brand_html() -> str:
    """Shared brand mark — used in nav + footer."""
    return (
        '<a class="brand" href="#dc-top" aria-label="BackMirror">'
        f'<span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>'
        '<span>BACK<span style="color:var(--signal)">MIRROR</span></span>'
        '</a>'
    )


def error_results_html(session_id: str = "—") -> str:
    """Graceful failure screen shown in place of RESULTS when the analysis
    pipeline raises (unsupported/corrupt video, transcode failure, etc.) — so
    the app never freezes on the live ANALYZING screen during a demo. The
    '다른 영상으로' button reuses #results-again-btn → resets to IDLE."""
    return f"""
<div class="dc-v3-root results-root">
  <section class="results-error">
    <div class="results-error-mark" aria-hidden="true">{_BRAND_SVG}</div>
    <span class="label label-signal">분석 실패 · ANALYSIS FAILED</span>
    <h1>이 영상은 분석하지 못했어요.</h1>
    <p>영상 형식이 지원되지 않거나 처리 중 문제가 생겼어요.<br/>
       다른 영상으로 다시 시도해 주세요.</p>
    <button class="ready-btn-go" type="button" id="results-again-btn">
      다른 영상으로
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 12 L19 12 M13 6 L19 12 L13 18"/>
      </svg>
    </button>
  </section>
  <footer class="ready-foot">© 2026 BACKMIRROR · 세션 {session_id}</footer>
</div>
"""


# ─── 1. NAV ───────────────────────────────────────────────────

def _nav_html() -> str:
    arrow = _arrow_svg()
    return f"""
    <header class="nav" id="dc-nav">
      {_brand_html()}
      <div class="nav-actions">
        <a class="nav-link" id="dc-team-link" href="#">팀 소개</a>
        <a class="nav-link" id="dc-faq-link" href="#">자주 묻는 질문</a>
        <a class="nav-link" id="dc-history-link" href="#">기록</a>
        <a class="btn btn-primary" href="#dc-upload">영상 업로드 {arrow}</a>
      </div>
    </header>
    """


# ─── 2. HERO — dual-frame ─────────────────────────────────────

def _hero_section() -> str:
    # Local hero.mp4 (in assets/) — served by Gradio via allowed_paths.
    # We use the gradio_api/file route which Gradio exposes for static files.
    hero_video = "/gradio_api/file=assets/hero.mp4"
    hero_ai_video = "/gradio_api/file=assets/hero_ai.mp4"
    return f"""
    <section class="hero" id="dc-top">
      <div class="hero-top">
        <div>
          <div class="hero-eyebrow">
            <span class="label label-signal">A driving intelligence platform</span>
          </div>
          <h1 class="hero-title" id="dc-heroTitle">
            <span class="line"><span class="inner">주행을 다시 보다,</span></span>
            <span class="line"><span class="inner"><em class="accent">프레임 단위로.</em></span></span>
          </h1>
        </div>
        <p class="hero-sub" data-reveal style="--rd:500ms">
          블랙박스 영상을 올리면 BackMirror가 급제동·차선 이탈·차간거리 부족 같은
          위험 이벤트를 자동으로 찾아내고, 그 순간의 운전 습관을 한 페이지 리포트로 정리합니다.
        </p>
      </div>

      <div class="hero-stage" data-reveal style="--rd:200ms">
        <div class="frame frame-raw"><i></i>
          <span class="frame-tag mono">Raw footage</span>
          <span class="frame-tc">00:00:13:21</span>
          <video autoplay muted loop playsinline preload="auto"
                 aria-label="야간 주행 POV — 원본"
                 src="{hero_video}"></video>
        </div>

        <div class="frame frame-ai"><i></i>
          <span class="frame-tag mono">AI · BackMirror</span>
          <span class="frame-tc">00:00:13:21 · 24 fps</span>
          <video autoplay muted loop playsinline preload="auto"
                 aria-label="야간 주행 POV — AI 분석"
                 src="{hero_ai_video}"></video>

          <svg class="ai-overlay" viewBox="0 0 1600 900" preserveAspectRatio="none">
            <defs>
              <radialGradient id="dcv3-attnGrad" cx="50%" cy="55%" r="35%">
                <stop offset="0%"   stop-color="rgba(0,229,154,0.30)"/>
                <stop offset="60%"  stop-color="rgba(0,229,154,0.08)"/>
                <stop offset="100%" stop-color="rgba(0,229,154,0)"/>
              </radialGradient>
            </defs>
            <ellipse class="attn" cx="800" cy="460" rx="480" ry="220"/>
          </svg>

          <div class="frame-ai-hud">
            <div class="hud-pill"><span class="dot"></span>LANE <b>STABLE</b></div>
            <div class="hud-pill">LEAD <b>14.2m</b></div>
            <div class="hud-pill risk"><span class="dot"></span>RISK <b>LOW</b></div>
          </div>
        </div>

        <div class="frame-divider" aria-hidden="true"></div>
      </div>

      <div class="hero-bottom">
        <div class="hero-stat" data-reveal style="--rd:600ms">
          <div class="label" style="margin-bottom:14px">01 · Detect</div>
          <div class="d" style="font-size:15px;color:rgba(255,255,255,0.86);max-width:32ch">
            급제동·차선 이탈·차간거리 부족 같은 위험 이벤트를 영상에서 자동으로 찾아냅니다.
          </div>
        </div>
        <div class="hero-stat" data-reveal style="--rd:720ms">
          <div class="label" style="margin-bottom:14px">02 · Contextualize</div>
          <div class="d" style="font-size:15px;color:rgba(255,255,255,0.86);max-width:32ch">
            사건 직전·직후의 운전 결정을 같이 봅니다. 결과만이 아니라 그 결정이 만들어진 순간을 함께.
          </div>
        </div>
        <div class="hero-stat" data-reveal style="--rd:840ms">
          <div class="label" style="margin-bottom:14px">03 · Coach</div>
          <div class="d" style="font-size:15px;color:rgba(255,255,255,0.86);max-width:32ch">
            반복되는 습관에 한 줄 피드백을 붙여, 다음 주행에서 무엇을 바꿔볼지 알려드립니다.
          </div>
        </div>
      </div>
    </section>
    """


# ─── 3. UPLOAD BAND — custom dropzone bridges to gr.File ─────

def _upload_section() -> str:
    arrow = _arrow_svg()
    return f"""
    <section class="upload" id="dc-upload">
      <div class="upload-grid">
        <div class="upload-copy">
          <span class="label label-signal">Step 01 — Upload</span>
          <h2>영상 한 편,<br/>리포트 한 장.</h2>
          <p>대시캠·블랙박스·휴대폰 어떤 영상이든 받습니다. 업로드된 영상은 안전하게
            처리되고, 분석이 끝나면 주요 이벤트·근거 클립·코칭이 한 페이지로 정리됩니다.</p>
          <ul class="upload-bullets">
            <li><span><b>MP4 · MOV · HEVC</b> 주요 블랙박스 포맷 그대로 올리면 됩니다.</span></li>
            <li><span><b>이벤트 자동 검출</b> 급제동·차선 이탈·차간거리 부족·신호 미준수 등.</span></li>
          </ul>
        </div>

        <div class="dz" id="dc-dropzone" tabindex="0" role="button"
             aria-label="주행 영상 업로드">
          <div class="dz-head">
            <span>upload · drag &amp; drop</span>
            <span class="dz-status"><i class="dot"></i>READY</span>
          </div>
          <div class="dz-body dz-idle">
            <div class="dz-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 16V4"/><path d="M6 10l6-6 6 6"/><path d="M4 20h16"/>
              </svg>
            </div>
            <h3 id="dc-dz-title">여기에 블랙박스 영상을 끌어다 놓으세요</h3>
            <div class="dz-meta en" id="dc-dz-meta">또는 파일 선택 · MP4 · MOV · HEVC</div>
            <div class="dz-cta">
              <span class="btn btn-primary">파일 선택하기 {arrow}</span>
              <span class="btn btn-ghost">샘플 영상으로 체험</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    """


# ─── 4. WHAT WE SEE — 3 capability tiles ──────────────────────

def _see_section() -> str:
    return """
    <section class="see" id="dc-see">
      <div class="see-head">
        <div>
          <span class="label label-signal">What we see</span>
          <h2 data-reveal>모델은 단순한 객체 검출이 아닙니다.<br/><em>맥락을 봅니다.</em></h2>
        </div>
        <p data-reveal style="--rd:200ms">
          한 장의 프레임에서 차선·차량·보행자·표지판을 분리해내고, 30초 윈도우 안에서
          그것들이 만들어내는 의사결정의 결을 추적합니다.
        </p>
      </div>

      <div class="see-grid">
        <article class="tile" data-reveal>
          <img alt="스티어링 POV — 운전자 조작 추적"
            src="https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?auto=format&fit=crop&w=1600&q=80"/>
          <div class="tile-overlay">
            <svg viewBox="0 0 400 500" preserveAspectRatio="none">
              <rect class="bbox" x="120" y="260" width="170" height="110"/>
              <text x="120" y="254">HANDS · 0.96</text>
              <rect class="bbox amber" x="240" y="180" width="60" height="40"/>
              <text x="240" y="174" style="fill:var(--amber)">GAZE · FORWARD</text>
            </svg>
          </div>
          <div class="tile-shade"></div>
          <div class="tile-body">
            <div class="tile-num">CAPABILITY · 01</div>
            <h3>운전자의 시선과 조작을 함께 본다</h3>
            <p>스티어링 입력의 미세한 진동·시선 방향·페달 압력을 시간축에 정렬합니다.</p>
          </div>
        </article>

        <article class="tile" data-reveal style="--rd:120ms">
          <img alt="앞차 추적 — 전방 차량 검출"
            src="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1600&q=80"/>
          <div class="tile-overlay">
            <svg viewBox="0 0 400 500" preserveAspectRatio="none">
              <rect class="bbox" x="110" y="230" width="190" height="130"/>
              <text x="110" y="224">VEHICLE · 0.98 · 14.2m</text>
              <path class="lane" d="M40,500 C120,380 180,300 200,240" style="stroke-dasharray:8 6"/>
              <path class="lane" d="M380,500 C320,380 240,300 220,240" style="stroke-dasharray:8 6"/>
            </svg>
          </div>
          <div class="tile-shade"></div>
          <div class="tile-body">
            <div class="tile-num">CAPABILITY · 02</div>
            <h3>앞차와의 거리·상대 속도를 본다</h3>
            <p>전방 차량을 프레임마다 추적해 차간거리·상대 가감속을 0.1초 단위로 계산합니다.</p>
          </div>
        </article>

        <article class="tile" data-reveal style="--rd:240ms">
          <img alt="차선·도로 인지 — 다양한 환경"
            src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1600&q=80"/>
          <div class="tile-overlay">
            <svg viewBox="0 0 400 500" preserveAspectRatio="none">
              <path class="lane" d="M50,500 C140,360 200,270 215,200"/>
              <path class="lane" d="M350,500 C280,360 230,270 225,200"/>
              <ellipse cx="220" cy="260" rx="140" ry="60"
                style="fill:rgba(0,229,154,0.08); stroke:none"/>
              <text x="160" y="195">LANE · STABLE</text>
            </svg>
          </div>
          <div class="tile-shade"></div>
          <div class="tile-body">
            <div class="tile-num">CAPABILITY · 03</div>
            <h3>차선과 도로 형상을 끊김 없이 인지한다</h3>
            <p>차선 마킹이 흐릿하거나 비대칭인 환경에서도 도로 형상을 안정적으로 추정합니다.</p>
          </div>
        </article>
      </div>
    </section>
    """


# ─── 5. SAMPLE REPORT ─────────────────────────────────────────

def _report_section() -> str:
    arrow = _arrow_svg()
    return f"""
    <section class="report" id="dc-report">
      <div class="report-head">
        <div>
          <span class="label label-signal">What you get</span>
          <h2 data-reveal>당신이 받는 한 페이지<br/>분석 리포트.</h2>
        </div>
        <p data-reveal style="--rd:200ms">
          검출된 위험 이벤트, 그 순간의 근거 클립, 그리고 다음 주행에서 바꿔볼 수 있는
          짧은 코칭이 한 페이지로 정리됩니다.
        </p>
      </div>

      <div class="report-card" data-reveal>
        <div class="rc-head">
          <div class="rc-head-left">
            <span class="rc-id">REPORT · #DA-20260524-2419</span>
          </div>
          <div class="rc-head-right">
            <span>DURATION <b>12:34</b></span>
            <span>EVENTS <b>3</b></span>
            <span>SCORE <b style="color:var(--signal)">82</b></span>
          </div>
        </div>

        <div class="rc-timeline">
          <div class="rc-timeline-label">
            <h4>Timeline · 검출된 의사결정</h4>
            <div class="rc-tl-ticks" style="width:280px">
              <span>00:00</span><span>06:17</span><span>12:34</span>
            </div>
          </div>
          <div class="rc-tl">
            <div class="rc-tl-bar" style="left:0; width:18%"></div>
            <div class="rc-tl-bar" style="left:32%; width:14%"></div>
            <div class="rc-tl-bar" style="left:64%; width:22%"></div>
            <div class="rc-tl-marker" data-l="02:14 · LANE CHANGE" style="left:18%"></div>
            <div class="rc-tl-marker amber" data-l="06:47 · CLOSE GAP" style="left:46%"></div>
            <div class="rc-tl-marker risk" data-l="10:32 · LATE BRAKE" style="left:78%"></div>
          </div>
        </div>

        <div class="rc-moments">
          <article class="km">
            <div class="km-img">
              <img alt="02:14 차선 변경"
                src="/gradio_api/file=assets/sample_lane.jpg"/>
              <svg class="km-overlay" viewBox="0 0 400 225" preserveAspectRatio="none">
                <rect x="168" y="96" width="108" height="70"/>
                <text x="168" y="90">HANDS · 0.96</text>
                <rect x="220" y="50" width="56" height="30"/>
                <text x="220" y="44">GAZE · FWD</text>
              </svg>
              <span class="km-tc mono">02:14</span>
              <span class="km-badge mono">GOOD</span>
            </div>
            <div class="km-cat">LANE CHANGE · LEFT</div>
            <h4>충분한 거리에서 한 번에 들어갔습니다.</h4>
            <p>차선 변경 1.6초 전부터 사이드미러를 확인했고, 깜빡이를 1.2초 유지한 뒤 진입했습니다.</p>
            <div class="km-coach"><b>코칭</b><span>같은 패턴을 야간에도 유지해 보세요. 평균 1.4초 → 1.6초로 안정적.</span></div>
          </article>

          <article class="km">
            <div class="km-img">
              <img alt="06:47 차간거리"
                src="/gradio_api/file=assets/sample_gap.jpg"/>
              <svg class="km-overlay" viewBox="0 0 400 225" preserveAspectRatio="none">
                <rect class="amber" x="130" y="94" width="140" height="82"/>
                <text class="amber" x="130" y="88">VEHICLE · 1.4s</text>
                <rect class="amber" x="300" y="180" width="70" height="22"/>
                <text class="amber" x="308" y="194">GAP · LOW</text>
              </svg>
              <span class="km-tc mono">06:47</span>
              <span class="km-badge amber mono">REVIEW</span>
            </div>
            <div class="km-cat">FOLLOWING DISTANCE</div>
            <h4>앞차와의 간격이 1.4초로 좁아졌습니다.</h4>
            <p>고속도로 권장 간격은 2.0초입니다. 차간거리 부족 상태가 9초간 지속됐습니다.</p>
            <div class="km-coach"><b>코칭</b><span>오른발을 액셀에서 떼는 것만으로 0.6초가 다시 확보됩니다.</span></div>
          </article>

          <article class="km">
            <div class="km-img">
              <img alt="10:32 급제동"
                src="/gradio_api/file=assets/sample_brake.jpg"/>
              <svg class="km-overlay" viewBox="0 0 400 225" preserveAspectRatio="none">
                <rect class="risk" x="150" y="86" width="120" height="92"/>
                <text class="risk" x="150" y="80">VEHICLE · BRAKE</text>
                <rect class="risk" x="280" y="180" width="80" height="22"/>
                <text class="risk" x="288" y="194">DECEL · -0.42g</text>
              </svg>
              <span class="km-tc mono">10:32</span>
              <span class="km-badge risk mono">RISK</span>
            </div>
            <div class="km-cat">LATE BRAKING</div>
            <h4>0.7초 늦은 제동, –0.42g.</h4>
            <p>30초 전 앞 차량의 브레이크등이 두 번 점멸했지만 페달 입력은 7초 뒤에 시작됐습니다.</p>
            <div class="km-coach"><b>코칭</b><span>앞차의 두 번째 브레이크등이 곧 제동의 신호입니다. 미리 시선을 두세요.</span></div>
          </article>
        </div>

        <div class="rc-foot">
          <div class="rc-score">
            <div class="rc-score-item"><div class="l">OVERALL</div><div class="v signal">82<small>/100</small></div></div>
            <div class="rc-score-item"><div class="l">ATTENTION</div><div class="v">88<small>/100</small></div></div>
            <div class="rc-score-item"><div class="l">SPACING</div><div class="v">72<small>/100</small></div></div>
            <div class="rc-score-item"><div class="l">SMOOTHNESS</div><div class="v">79<small>/100</small></div></div>
          </div>
          <a class="btn btn-ghost" href="#dc-upload">내 영상으로 받아보기 {arrow}</a>
        </div>
      </div>
    </section>
    """


# ─── 6. NUMBERS ───────────────────────────────────────────────

def _numbers_section() -> str:
    big = ("font-size:clamp(30px,3.2vw,44px);"
           "line-height:1.05;letter-spacing:-0.025em")
    return f"""
    <section class="numbers" id="dc-numbers">
      <div class="numbers-head">
        <span class="label label-signal">What we detect</span>
        <h2 data-reveal>리포트가 짚어주는<br/><em>세 가지 순간.</em></h2>
      </div>
      <div class="numbers-grid">
        <div class="num" data-reveal>
          <div class="l">Event · 01</div>
          <div class="v" style="{big}">차선 이탈</div>
          <div class="d">방향지시등 없이 차선을 넘어가거나, 차선 안에서 좌우 흔들림이 큰 구간을 표시합니다.</div>
        </div>
        <div class="num" data-reveal style="--rd:120ms">
          <div class="l">Event · 02</div>
          <div class="v" style="{big}">차간거리 부족</div>
          <div class="d">앞 차량과의 시간 간격이 권장 수준 아래로 떨어져 지속된 구간을 따로 모아 보여드립니다.</div>
        </div>
        <div class="num" data-reveal style="--rd:240ms">
          <div class="l">Event · 03</div>
          <div class="v" style="{big}">신호·정지선</div>
          <div class="d">신호 전환 시점의 정지·통과 결정과 정지선 위치를 함께 기록합니다.</div>
        </div>
      </div>
    </section>
    """


# ─── 7. CTA ───────────────────────────────────────────────────

def _cta_section() -> str:
    arrow = _arrow_svg()
    return f"""
    <section class="cta" id="dc-cta">
      <div class="cta-overlay"></div>
      <div class="cta-inner">
        <div>
          <span class="label label-signal">Try it now</span>
          <h2>지난 주행이,<br/>다음 주행의<br/><span class="glow">코칭이 됩니다.</span></h2>
        </div>
        <div class="cta-side">
          <p>블랙박스 영상 한 편이면 충분합니다. 위험 이벤트와 근거 클립, 그리고
             다음 주행에서 바꿔볼 한 줄을 정리해 돌려드립니다.</p>
          <div class="cta-actions">
            <a class="btn btn-primary btn-lg" href="#dc-upload">영상 업로드 시작 {arrow}</a>
            <a class="btn btn-ghost btn-lg" href="#dc-report">샘플 리포트 보기</a>
          </div>
          <div class="cta-fine">No setup · No hardware · Early access</div>
        </div>
      </div>
    </section>
    """


# ─── 8. FOOTER ────────────────────────────────────────────────

def _footer_section() -> str:
    return f"""
    <footer class="footer-min" id="dc-footer">
      {_brand_html()}
      <p class="foot-tag">블랙박스 영상 한 편을 한 페이지 리포트로 바꾸는 운전 코칭 프로젝트.</p>
      <div class="foot-mini mono">© 2026 BACKMIRROR</div>
    </footer>
    """


# ─── Top-level IDLE HTML (assembled) ──────────────────────────

def _font_links() -> str:
    """Emit <link> tags for the v3 fonts.

    We cannot use `@import` inside CUSTOM_CSS because Gradio injects styles
    via `CSSStyleSheet.replaceSync()` which forbids @import directives. So
    we inline the <link> tags at the top of the idle HTML — gr.HTML appends
    them to the document and the browser fetches the fonts normally.
    """
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" '
        'href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/'
        'dist/web/variable/pretendardvariable-dynamic-subset.min.css">'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2'
        '?family=Inter:wght@400;500;600;700'
        '&family=JetBrains+Mono:wght@400;500;600'
        '&family=Noto+Sans+KR:wght@400;500;600;700;800;900'
        '&display=swap">'
    )


def idle_hero_html() -> str:
    """The whole v3 landing page, wrapped in `.dc-v3-root` for CSS scoping."""
    return (
        _font_links()
        + '<div class="dc-v3-root">'
        + _nav_html()
        + _hero_section()
        + _upload_section()
        + _see_section()
        + _report_section()
        + _numbers_section()
        + _cta_section()
        + _footer_section()
        + '</div>'
    )


# ─── UPLOADED — v4 "Ready" screen ──────────────────────────────
# Built as a SINGLE HTML blob (not split across multiple gr.HTML + gr.Row).
# Reason: when we used gr.Row/gr.Column to lay out nav / stepper / stage /
# action bar, Gradio's own flex containers fought our CSS grid and the
# stepper collapsed to a vertical stack, the rail vanished, etc. The IDLE
# landing works because it's a single self-contained `.dc-v3-root` div —
# we use the same pattern here.
#
# Custom <button> elements inside the HTML are bridged by JS in app.py
# to the hidden gr.Button instances (see `.dc-hidden-actions`).

import urllib.parse


def _fmt_size(bytes_: int | float) -> str:
    n = float(bytes_)
    if n <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return f"{n:.1f} {units[i]}"


def _fmt_duration(sec: float) -> str:
    if sec <= 0:
        return "00:00"
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def _video_url(abs_path: str) -> str:
    """Build the /gradio_api/file= URL for a path inside `allowed_paths`."""
    if not abs_path:
        return ""
    return "/gradio_api/file=" + urllib.parse.quote(
        abs_path.replace("\\", "/"), safe="/:."
    )


def _file_icon_svg() -> str:
    return (
        '<svg class="file-icon" width="14" height="14" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="1.6">'
        '<rect x="3" y="6" width="14" height="12" rx="1"/>'
        '<path d="M17 10 L21 8 L21 16 L17 14 Z" fill="currentColor"/>'
        '</svg>'
    )


def _arrow_go_svg() -> str:
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M5 12 L19 12 M13 6 L19 12 L13 18"/></svg>'
    )


def ready_screen_html(
    video_path: str = "",
    name: str = "",
    duration: float = 0.0,
    width: int = 0,
    height: int = 0,
    fps: float = 0.0,
    codec: str = "—",
    size_bytes: int = 0,
    session_id: str = "—",
) -> str:
    """Full v4 Ready screen — nav · stepper · stage · action bar · footer.

    All wrapped in one `.dc-v3-root.ready-root` so Gradio's component
    containers can't break the internal grid layout.
    """
    dur_str = _fmt_duration(duration)
    size_str = _fmt_size(size_bytes)
    res_str = f"{width}×{height}" if width and height else "—"
    fps_str = f"{fps:.0f} FPS" if fps > 0 else "—"
    if duration > 0 and size_bytes > 0:
        bitrate_str = f"{(size_bytes * 8 / duration) / 1e6:.1f} Mb/s"
    else:
        bitrate_str = "—"
    safe_name = name or "—"
    meta_line = f"방금 · {size_str}" if size_bytes > 0 else "준비 중"
    vurl = _video_url(video_path)
    video_el = (
        f'<video src="{vurl}" controls preload="metadata" playsinline></video>'
        if vurl else
        '<div class="ready-video-empty">영상 미리보기를 준비 중입니다…</div>'
    )

    return f"""
<div class="dc-v3-root ready-root">

  <nav class="ready-nav">
    <a class="brand" href="#dc-top" aria-label="BackMirror">
      <span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>BACK<span style="color:var(--signal)">MIRROR</span></span>
    </a>
    <div class="ready-nav-right">
      <span class="ready-session">SESSION · {session_id}</span>
    </div>
  </nav>

  <div class="ready-stepper-wrap">
    <div class="ready-stepper" role="list">
      <div class="ready-step done" role="listitem">
        <span class="num">01</span><span class="check">✓</span><span>업로드</span>
      </div>
      <div class="ready-step current" role="listitem">
        <span class="num">02</span><span class="pulse" aria-hidden="true"></span><span>검토</span>
      </div>
      <div class="ready-step" role="listitem">
        <span class="num">03</span><span>분석</span>
      </div>
      <div class="ready-step" role="listitem">
        <span class="num">04</span><span>리포트</span>
      </div>
    </div>
  </div>

  <section class="ready-stage">
    <div class="ready-rail">
      <div class="ready-rail-status">
        <span class="dot"></span>
        <span class="label label-signal">Ready · 검토 중</span>
      </div>
      <h1>
        <span>{dur_str}.</span><br/>
        <span class="accent">이 영상.</span>
        <span class="em">받았습니다. 한 프레임도 빠짐없이 분석해 드릴 준비가 되었습니다.</span>
      </h1>
      <div class="ready-filename">
        {_file_icon_svg()}
        <div>
          {safe_name}
          <span class="file-meta">{meta_line}</span>
        </div>
      </div>
    </div>

    <div class="ready-video-stage">
      <div class="ready-video-frame">
        {video_el}
        <span class="ready-br ready-br-tl"></span>
        <span class="ready-br ready-br-tr"></span>
        <span class="ready-br ready-br-bl"></span>
        <span class="ready-br ready-br-br"></span>
        <div class="ready-hud ready-hud-tl">
          <span class="ready-hud-tag"><span class="ready-rec-dot"></span>REC · CH1</span>
        </div>
        <div class="ready-hud ready-hud-tr">
          <span class="ready-hud-tag">{res_str} · {fps_str}</span>
        </div>
      </div>
      <div class="ready-meta-strip">
        <div class="ready-meta-cell"><span class="k">Duration</span><span class="v">{dur_str}</span></div>
        <div class="ready-meta-cell"><span class="k">Resolution</span><span class="v">{res_str}</span></div>
        <div class="ready-meta-cell"><span class="k">Frame rate</span><span class="v">{fps_str}</span></div>
        <div class="ready-meta-cell"><span class="k">Codec</span><span class="v">{codec} <span class="ok">✓</span></span></div>
        <div class="ready-meta-cell"><span class="k">Bitrate</span><span class="v">{bitrate_str}</span></div>
        <div class="ready-meta-cell"><span class="k">Size</span><span class="v">{size_str}</span></div>
      </div>
    </div>
  </section>

  <section class="ready-action-wrap">
    <div class="ready-action-bar">
      <div class="ready-action-summary">
        <div class="lbl">Ready to analyze</div>
        <div class="ttl">위 영상으로 분석을 시작합니다.</div>
      </div>
      <button class="ready-btn-secondary" type="button" id="ready-back-btn">다른 영상으로</button>
      <button class="ready-btn-go" type="button" id="ready-go-btn">
        분석 시작 {_arrow_go_svg()}
        <span class="go-eta">약 30초</span>
      </button>
    </div>
    <div class="ready-kbd-hint">
      <span class="kbd">⏎</span> Enter 키로 즉시 시작
    </div>
  </section>

  <footer class="ready-foot">© 2026 BACKMIRROR · 분석 세션 {session_id}</footer>

</div>
"""


# ─── ANALYZING — v5 redesign ──────────────────────────────────
# Soul of the screen: the LIVE FRAME with real bboxes burned in (or SVG-
# overlaid from FrameDetections). Everything else (% / ETA / counters /
# stepper) is small mono chrome. The phase-driven H1 changes verb with
# each stage of the pipeline:
#   detect → 보고 / events → 추리고 / vlm → 쓰고 / score → 계산 / render → 만들고
# All values come from real run_analysis generator yields; no faked client
# animation. The screen is one self-contained .dc-v3-root blob (no gr.Row).

# Ordered phase definitions — drives stepper / phase list / H1 narrative.
_ANALYZ_PHASE_DEFS = [
    # (key, stepper_short, list_full,  h1_pre,        h1_verb,                  nav_label)
    ("detect", "검출",       "객체 검출",    "프레임을",     "보고 있습니다.",            "DETECT"),
    ("events", "이벤트",     "이벤트 추출",  "위험 구간을",   "추리고 있습니다.",          "EVENTS"),
    ("vlm",    "코칭",       "코칭 작성",    "코칭 문장을",   "쓰고 있습니다.",            "VLM"),
    ("score",  "점수",       "점수 산정",    "점수를",       "계산하고 있습니다.",        "SCORE"),
    ("render", "출력",       "영상 출력",    "주석 영상을",   "만들고 있습니다.",          "RENDER"),
]


def _phase_index(phase: str) -> int:
    for i, (key, *_rest) in enumerate(_ANALYZ_PHASE_DEFS):
        if key == phase:
            return i
    return 0


def _stepper_html(phase: str) -> str:
    idx = _phase_index(phase)
    out = []
    for i, (key, short, *_rest) in enumerate(_ANALYZ_PHASE_DEFS):
        cls = "current" if i == idx else ("done" if i < idx else "")
        pulse = '<span class="pulse"></span>' if i == idx else ""
        out.append(
            f'<div class="analyz-step {cls}" data-phase="{key}">'
            f'<span class="num">{i + 1:02d}</span>{pulse}'
            f'<span>{short}</span>'
            f'</div>'
        )
    return "".join(out)


def _phase_list_html(phase: str) -> str:
    idx = _phase_index(phase)
    out = []
    for i, (key, _short, full, *_rest) in enumerate(_ANALYZ_PHASE_DEFS):
        if i < idx:
            cls, status = "done", "완료"
        elif i == idx:
            cls, status = "current", "진행 중"
        else:
            cls, status = "pending", "대기"
        out.append(
            f'<li class="{cls}" data-phase="{key}">'
            f'<span class="num">{i + 1:02d}</span>'
            f'<span class="name">{full}</span>'
            f'<span class="stt">{status}</span>'
            f'</li>'
        )
    return "".join(out)


# Class → severity mapping for the live bbox overlay. Matches the counter
# strip color language: vehicles/pedestrians = signal, two-wheeled = amber,
# traffic markers stay muted (default signal). Risk tone is reserved for
# bboxes inside a flagged event region (not detected here per-frame).
_BBOX_CLS_TIER = {
    "car": "signal", "truck": "signal", "bus": "signal",
    "person": "signal",
    "bike": "amber", "motor": "amber", "rider": "amber",
    "traffic light": "signal", "traffic sign": "signal",
}


def _bbox_overlay_svg(det, frame_w: int, frame_h: int) -> str:
    """Live bbox layer over the static poster. Uses the latest FrameDetections
    object so the boxes sync exactly with what the model just emitted.
    Returns empty string when there are no detections to draw."""
    if not det or not det.detections or frame_w <= 0 or frame_h <= 0:
        return ""
    # Label box geometry — sized to fit "VEHICLE 0.94" at 9px mono
    LABEL_H = max(14, int(frame_h * 0.020))
    parts = []
    for d in det.detections[:12]:  # cap so the frame never looks like graffiti
        x1, y1, x2, y2 = d.bbox
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        if w < 4 or h < 4:
            continue
        tier = _BBOX_CLS_TIER.get(d.cls, "signal")
        cls_extra = "" if tier == "signal" else f" {tier}"
        label = f"{d.cls.upper()} {d.confidence:.2f}"
        # Label background bar sits just above the bbox top edge
        label_w = min(int(w), max(60, len(label) * 7))
        label_y = max(0, y1 - LABEL_H - 2)
        text_cls = "dark" if tier == "signal" else "amber-dark"
        parts.append(
            f'<rect class="{tier}" x="{x1}" y="{y1}" width="{w}" height="{h}"/>'
            f'<rect class="label-bg{cls_extra}" x="{x1}" y="{label_y}" '
            f'width="{label_w}" height="{LABEL_H}"/>'
            f'<text class="{text_cls}" x="{x1 + 5}" y="{label_y + LABEL_H - 4}">{label}</text>'
        )
    if not parts:
        return ""
    return (f'<svg class="svg-overlay" viewBox="0 0 {frame_w} {frame_h}" '
            f'preserveAspectRatio="none">{"".join(parts)}</svg>')


def analyzing_screen_html(
    poster_path: str = "",
    name: str = "",
    session_id: str = "—",
    pct: int = 0,
    frame_idx: int = 0,
    total_frames: int = 0,
    proc_fps: float = 0.0,
    eta_sec: int = 0,
    veh: int = 0,
    ped: int = 0,
    two: int = 0,
    risk: int = 0,
    phase: str = "detect",
    det=None,
    frame_w: int = 0,
    frame_h: int = 0,
) -> str:
    """Live-analysis screen — v5 redesign.

    Every number here (pct, frame counter, processing fps, ETA, cumulative
    per-class detection counts, phase) reflects the actual run_analysis
    generator's state at the moment of yield. The right-side frame shows a
    poster jpg that the server periodically overwrites with the most-recent
    processed frame; on top of it, an SVG overlay draws bboxes from the
    latest FrameDetections (passed via `det`). No fake client animation.

    Counter labels read 차량·보행자·이륜차·위험 ··· but the numbers are
    cumulative across processed frames (vs the previous per-frame snapshot).
    With no tracker present this overstates unique objects, so labels are
    framed as "검출된 N건" rather than "고유 차량 N대".
    """
    safe_name = name or "—"
    idx = _phase_index(phase)
    _, _short, _full, h1_pre, h1_verb, nav_label = _ANALYZ_PHASE_DEFS[idx]
    pct = max(0, min(100, int(pct)))
    eta_str = f"약 {eta_sec}초" if eta_sec > 0 else "마무리"
    frame_str = f"{frame_idx:,} / {total_frames:,}" if total_frames else f"{frame_idx:,}"
    det_now = veh + ped + two

    poster_url = _video_url(poster_path)
    poster_el = (
        f'<img class="poster" src="{poster_url}" alt="현재 처리 중인 프레임"/>'
        if poster_url else
        '<div class="poster poster-empty"></div>'
    )
    bbox_svg = _bbox_overlay_svg(det, frame_w, frame_h)

    return f"""
<div class="dc-v3-root analyz-root">

  <nav class="analyz-nav">
    <a class="analyz-brand" href="#dc-top" aria-label="BackMirror">
      <span class="mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>BACK<span class="accent">MIRROR</span></span>
    </a>
    <div class="analyz-nav-right">
      <span class="live-pill"><span class="dot"></span>LIVE · {nav_label}</span>
      <span>SESSION · {session_id}</span>
      <button class="analyz-cancel" type="button" id="analyz-cancel-btn">분석 중단</button>
    </div>
  </nav>

  <div class="analyz-stepper">
    {_stepper_html(phase)}
  </div>

  <section class="analyz-stage">

    <aside class="analyz-rail">
      <div>
        <span class="phase-kicker">PHASE {idx + 1:02d} <span class="of">/ 05</span></span>
        <h1 class="analyz-h1">
          <span>{h1_pre}</span>
          <em>{h1_verb}</em>
        </h1>
        <div class="analyz-filename">
          {_file_icon_svg()}
          <span>{safe_name}</span>
        </div>
      </div>

      <div class="analyz-progress">
        <div class="row">
          <span class="pct">{pct}<span class="unit">%</span></span>
          <span class="eta">남은 시간 · <b>{eta_str}</b></span>
        </div>
        <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
        <div class="meta">
          <span>프레임 · <b>{frame_str}</b></span>
          <span><b>{proc_fps:.0f}</b> f/s</span>
        </div>
      </div>

      <ul class="analyz-phases">
        {_phase_list_html(phase)}
      </ul>
    </aside>

    <div class="analyz-frame">
      {poster_el}
      {bbox_svg}

      <span class="br br-tl"></span>
      <span class="br br-tr"></span>
      <span class="br br-bl"></span>
      <span class="br br-br"></span>

      <div class="hud hud-tl">
        <span class="hud-chip"><span class="dot"></span>ANALYZING · CH1</span>
      </div>
      <div class="hud hud-tr">
        <span class="hud-chip">FRAME {frame_str}</span>
      </div>
      <div class="hud hud-bl">
        <span class="hud-chip">PHASE · <span class="accent">{nav_label}</span></span>
      </div>
      <div class="hud hud-br">
        <span class="hud-chip">DET <span class="accent">{det_now}</span></span>
      </div>
    </div>
  </section>

  <div class="analyz-counters">
    <div class="analyz-counter signal"><span class="k">차량 · Vehicle</span><span class="v">{veh}</span></div>
    <div class="analyz-counter"      ><span class="k">보행자 · Pedestrian</span><span class="v">{ped}</span></div>
    <div class="analyz-counter amber"><span class="k">이륜차 · Two-wheeled</span><span class="v">{two}</span></div>
    <div class="analyz-counter risk" ><span class="k">위험 이벤트 · Risk</span><span class="v">{risk}</span></div>
  </div>

</div>
"""


# ─── RESULTS — v5 redesign ────────────────────────────────────
# Soul: the coaching SENTENCE is the hero. The score is small and tucked
# under the still. The annotated video is promoted to "Evidence" with a
# clickable timeline. Cards adapt to 0/1/2/3/many. Breakdown shows prior
# tick + delta chip + focus highlight. All in one self-contained .dc-v3-root.

# Helpers that survive from v4 (still used elsewhere):
#   _hero_sentence / _hero_with_history / _secondary_with_delta —
#     reused to populate the .hero-prior block.
#   _score_delta_html — superseded inline by _score_block_html below.
#   _category_tier — used to color the breakdown bars.
#   _count_by_category / _name_ko_to_key — used by _hero_with_history.


def _pick_hero_event_idx(events) -> int | None:
    """Pick the single event that becomes the hero's reference frame.
    Priority: danger > caution > safe; tie-break by penalty desc."""
    if not events:
        return None
    sev_order = {"danger": 3, "caution": 2, "safe": 1}
    best_i, best_key = 0, (sev_order.get(events[0].severity, 0),
                           events[0].penalty or 0)
    for i, e in enumerate(events[1:], start=1):
        k = (sev_order.get(e.severity, 0), e.penalty or 0)
        if k > best_key:
            best_i, best_key = i, k
    return best_i


def _sev_cls(severity: str) -> str:
    return "risk" if severity == "danger" else (
        "amber" if severity == "caution" else "safe"
    )


def _sev_label(severity: str) -> str:
    return "RISK" if severity == "danger" else (
        "CAUTION" if severity == "caution" else "SAFE"
    )


def _first_coach_sentence(text: str, max_len: int = 70) -> str:
    """First actionable sentence of a (possibly multi-step) coaching plan.

    Mock/real VLM action plans can read '1) … . 2) … . 3) …'. The hero quote
    is the screen's one-line soul — it must stay one punchy sentence, not the
    whole plan, or it blows the layout out vertically. Defensive against any
    length: strips a leading enumerator, cuts at the first sentence boundary,
    hard-caps as a last resort."""
    t = (text or "").strip()
    t = re.sub(r"^\s*\d+[).．.]\s*", "", t)         # drop leading "1) " / "1. "
    m = re.search(r"[.!?。](\s|$)", t)               # first sentence boundary
    if m:
        t = t[: m.start() + 1].strip()
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def _hero_quote_text(hero_event, hero_coaching) -> str:
    """One-sentence coaching line for the hero. Prefers VLM action_plan,
    falls back to a soft message when there's nothing to coach about."""
    if hero_event and hero_coaching and (hero_coaching.action_plan or "").strip():
        # hero 는 큰 폰트라 캡을 더 짧게(55) — 장황한 첫 문장도 4줄 이내로.
        return _first_coach_sentence(hero_coaching.action_plan, max_len=55)
    if hero_event:
        # event found but no coaching text — minimal fallback per severity
        if hero_event.severity == "danger":
            return "이 순간을 다시 보고, 다음엔 한 박자 먼저 반응해보세요."
        if hero_event.severity == "caution":
            return "이 패턴이 반복되지 않게 조금만 여유를 두세요."
        return "이 톤을 다음 주행에도 그대로 가져가 보세요."
    return "위험 없이, 부드럽게 흘러갔어요."


def _hero_quote_html(text: str) -> str:
    """Wrap each whitespace-separated token in a .word span with --i index
    so CSS can stagger the per-word slideUp entrance animation."""
    tokens = re.findall(r"\S+|\s+", text)
    spans = "".join(
        f'<span class="word" style="--i:{i}">{t}</span>'
        for i, t in enumerate(tokens)
    )
    return f'<h1 class="hero-quote">{spans}</h1>'


def _hero_ref_html(hero_event) -> str:
    """The mono chip beneath the quote: timestamp · severity · short note."""
    if hero_event is None:
        return (
            '<div class="hero-ref">'
            '<span class="ref-tc">—</span>'
            '<span class="ref-sev safe">SAFE · 위험 없음</span>'
            '<span>0개 위험 이벤트</span>'
            '</div>'
        )
    sev_cls = _sev_cls(hero_event.severity)
    sev_label = _sev_label(hero_event.severity)
    tc = _fmt_duration(hero_event.timestamp)
    note = (hero_event.summary or "")
    if len(note) > 36:
        note = note[:36] + "…"
    return f"""
    <div class="hero-ref">
      <span class="ref-tc">{tc}</span>
      <span class="ref-sev {sev_cls}">{sev_label} · {hero_event.title}</span>
      <span>{note}</span>
    </div>
    """


def _hero_prior_block_html(score, events, prior) -> str:
    """The italic-bordered block beneath hero-ref carrying the longitudinal
    'we remember you' narrative. Hidden entirely when there is no prior."""
    if prior is None:
        return ""
    hero, secondary = _hero_sentence(score, events, prior=prior)
    return f"""
    <div class="hero-prior">
      <div class="prior-line">{hero}</div>
      <div class="prior-sec">{secondary}</div>
    </div>
    """


def _hero_still_html(still_path: str, hero_event) -> str:
    """The 16:11 framed image of the decisive moment. Corner brackets + a
    monospaced bottom-left tc/severity badge. We don't draw bboxes here —
    the still itself is the evidence; bboxes belong on the annotated video."""
    url = _video_url(still_path) if still_path else ""
    if hero_event is None or not url:
        # No event or no still — render an empty dark frame with brackets so
        # the hero column doesn't visually collapse.
        return (
            '<div class="hero-still hero-still-empty">'
            '<span class="br br-tl"></span><span class="br br-tr"></span>'
            '<span class="br br-bl"></span><span class="br br-br"></span>'
            '</div>'
        )
    sev_cls = _sev_cls(hero_event.severity)
    label = "BRAKE" if hero_event.severity == "danger" else (
        "CAUTION" if hero_event.severity == "caution" else "SAFE"
    )
    tc = _fmt_duration(hero_event.timestamp)
    return f"""
    <div class="hero-still">
      <img alt="결정적 순간 프레임" src="{url}"/>
      <span class="br br-tl"></span>
      <span class="br br-tr"></span>
      <span class="br br-bl"></span>
      <span class="br br-br"></span>
      <span class="hero-still-tc">
        <span class="dot {sev_cls}"></span>{tc} · {label}
      </span>
    </div>
    """


def _score_block_html(score, prior) -> str:
    """Score chip tucked under the hero still. Big number + grade + delta
    vs prior. Smaller than the hero quote — score is supporting cast."""
    if not score:
        return ""
    if prior is None:
        prior_label = "첫 분석 · "
        delta_chip = '<span class="delta-chip first">비교 없음</span>'
    else:
        delta = score.total - prior.score.total
        prior_label = f"지난번 {prior.score.total} · "
        if delta > 0:
            delta_chip = f'<span class="delta-chip">▲ {delta}</span>'
        elif delta < 0:
            delta_chip = f'<span class="delta-chip down">▼ {-delta}</span>'
        else:
            delta_chip = '<span class="delta-chip">— 0</span>'
    return f"""
    <div class="score-block">
      <div class="score-num">{score.total}<span class="unit">/100</span></div>
      <div class="score-meta">
        <div class="row">
          <span>이번 주행</span>
          <span class="grade">{score.grade}</span>
        </div>
        <div class="row">
          <span>{prior_label}</span>
          {delta_chip}
        </div>
      </div>
    </div>
    """


def _timeline_html_v5(events, duration_s: float) -> str:
    """Track with ±1s severity bands + clickable markers + readable labels.
    The data-tc on markers/labels is read by DC_BOOT_JS to seek the video."""
    if duration_s <= 0:
        return ""
    bands, markers, labels = [], [], []
    for e in events:
        sev_cls = _sev_cls(e.severity)
        start = max(0.0, e.timestamp - 1)
        end = min(duration_s, e.timestamp + 1)
        left = 100 * start / duration_s
        width = 100 * (end - start) / duration_s
        bands.append(
            f'<span class="band {sev_cls}" '
            f'style="left:{left:.2f}%; width:{width:.2f}%"></span>'
        )
        mleft = 100 * e.timestamp / duration_s
        title = f"{_fmt_duration(e.timestamp)} · {e.title}"
        markers.append(
            f'<span class="marker {sev_cls}" '
            f'style="left:{mleft:.2f}%" '
            f'data-tc="{e.timestamp:.2f}" title="{title}"></span>'
        )
        labels.append(
            f'<button type="button" data-tc="{e.timestamp:.2f}">'
            f'<span class="dot {sev_cls}"></span>'
            f'{_fmt_duration(e.timestamp)} · {e.title}'
            f'</button>'
        )
    return f"""
    <div class="timeline">
      <div class="timeline-row">
        <span class="tc">00:00</span>
        <div class="timeline-track" id="dc-results-track">
          <span class="bar"></span>
          {''.join(bands)}
          {''.join(markers)}
        </div>
        <span class="tc right">{_fmt_duration(duration_s)}</span>
      </div>
      <div class="timeline-labels">
        {''.join(labels)}
      </div>
    </div>
    """


def _cot_details_html(coaching) -> str:
    """DriveVLM-style 3-stage reasoning (상황 묘사 → 위험 분석 → 행동 제안),
    collapsed by default. The one-line action above is the takeaway; this
    discloses the VLM's full chain-of-thought — the 'why' that separates
    contextual coaching from a bare score. Native <details>, no JS."""
    if not coaching:
        return ""
    stages = [
        ("상황", "desc", (coaching.scene_description or "").strip()),
        ("위험", "risk", (coaching.scene_analysis or "").strip()),
        ("행동", "act",  (coaching.action_plan or "").strip()),
    ]
    rows = "".join(
        f'<div class="cot-stage cot-{key}">'
        f'<span class="cot-label">{label}</span>'
        f'<p>{text}</p>'
        f'</div>'
        for label, key, text in stages if text
    )
    if not rows:
        return ""
    return f"""
        <details class="m-cot">
          <summary>
            <span class="cot-sum-label">AI 추론 과정</span>
            <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9 L12 15 L18 9"/>
            </svg>
          </summary>
          <div class="cot-body">{rows}</div>
        </details>
    """


def _moment_card_v5_html(event, coaching, still_path: str) -> str:
    sev_cls = _sev_cls(event.severity)
    sev_label = _sev_label(event.severity)
    tc = _fmt_duration(event.timestamp)
    still_url = _video_url(still_path) if still_path else ""
    still_block = (
        f'<img alt="{tc}" src="{still_url}"/>'
        if still_url else '<div class="m-still-fallback"></div>'
    )
    # Visible line = the one-sentence takeaway; the full 3-stage reasoning
    # lives in the collapsible "AI 추론 과정" disclosure below it.
    action = ""
    if coaching:
        raw = (coaching.action_plan or coaching.scene_analysis
               or coaching.scene_description or "")
        action = _first_coach_sentence(raw) if raw else ""
    action_block = (
        f'<div class="m-action">{action}</div>' if action.strip() else ""
    )
    cot_block = _cot_details_html(coaching)
    return f"""
    <article class="moment" data-tc="{event.timestamp:.2f}">
      <div class="m-still">
        {still_block}
        <span class="m-tc"><span class="dot {sev_cls}"></span>{tc}</span>
        <span class="m-sev {sev_cls}">{sev_label}</span>
      </div>
      <div class="m-body">
        <div class="m-title">{event.title}</div>
        <p class="m-summary">{event.summary}</p>
        {action_block}
        {cot_block}
      </div>
    </article>
    """


def _moments_section_html(events, coachings, event_stills, duration) -> str:
    n = len(events)
    if n == 0:
        grid_cls = "n-0"
    elif n == 1:
        grid_cls = "n-1"
    elif n == 2:
        grid_cls = "n-2"
    elif n == 3:
        grid_cls = "n-3"
    else:
        grid_cls = "n-many"

    if n == 0:
        h2_html = "큰 위험 없이 부드럽게 흘러갔어요."
        body = """
        <div class="moments-empty">
          <span class="em-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="5 12 10 17 19 8"/>
            </svg>
          </span>
          <h3>위험 없이 부드럽게 흘러갔어요.</h3>
          <p>이 영상에서는 짚어둘 만한 위험 순간이 없었습니다.
             다음 주행에서도 이 톤을 유지해보세요.</p>
        </div>
        """
    else:
        h2_html = f'짚어둘 <em>{n}</em>개의 순간.'
        body = "".join(
            _moment_card_v5_html(
                e,
                coachings[i] if i < len(coachings) else None,
                event_stills.get(e.frame_idx, ""),
            )
            for i, e in enumerate(events)
        )

    return f"""
    <section class="results-moments">
      <div class="results-section-head">
        <div>
          <span class="label">순간 · Moments</span>
          <h2>{h2_html}</h2>
        </div>
      </div>
      <div class="moments-grid {grid_cls}">
        {body}
      </div>
    </section>
    """


# Korean long name → short label (design uses condensed names in the rail)
_CAT_SHORT = {
    "신호 인지": "신호", "차선 준수": "차선", "보행자 주의": "보행자",
    "속도 관리": "속도", "안전거리": "안전거리",
}
# Korean name → icon key (matches _CATEGORY_ICONS below)
_CAT_ICON_KEY = {
    "신호 인지": "signal", "차선 준수": "lane",
    "보행자 주의": "pedestrian", "속도 관리": "speed",
    "안전거리": "distance",
}
_CATEGORY_ICONS = {
    "signal": ('<svg viewBox="0 0 24 24"><rect x="6" y="3" width="12" height="18" rx="2"/>'
               '<circle cx="12" cy="8" r="1.5"/><circle cx="12" cy="13" r="1.5"/>'
               '<circle cx="12" cy="18" r="1.5"/></svg>'),
    "lane": ('<svg viewBox="0 0 24 24"><line x1="6" y1="3" x2="6" y2="21"/>'
             '<line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="10" x2="12" y2="14"/>'
             '<line x1="12" y1="18" x2="12" y2="21"/><line x1="18" y1="3" x2="18" y2="21"/></svg>'),
    "pedestrian": ('<svg viewBox="0 0 24 24"><circle cx="12" cy="4" r="2"/>'
                   '<path d="M12 7 v8 M12 15 l-3 6 M12 15 l3 6 M9 10 l-3 -1 M15 10 l3 -1"/></svg>'),
    "speed": ('<svg viewBox="0 0 24 24"><path d="M4 14 a8 8 0 0 1 16 0"/>'
              '<path d="M12 14 l4 -4"/><circle cx="12" cy="14" r="1.5"/></svg>'),
    "distance": ('<svg viewBox="0 0 24 24"><rect x="3" y="13" width="6" height="6"/>'
                 '<rect x="15" y="13" width="6" height="6"/>'
                 '<line x1="9" y1="16" x2="15" y2="16" stroke-dasharray="1.5 2"/></svg>'),
}


def _breakdown_section_html(score, prior) -> str:
    if not score or not score.categories:
        return ""

    prior_by_ko: dict[str, int] = {}
    if prior and prior.score and prior.score.categories:
        prior_by_ko = {c.name_ko: c.score for c in prior.score.categories}

    focus_ko = score.focus_area.name_ko if score.focus_area else None

    rows, deltas = [], []
    for cat in score.categories:
        short = _CAT_SHORT.get(cat.name_ko, cat.name_ko)
        ic_key = _CAT_ICON_KEY.get(cat.name_ko, "signal")
        tier = _category_tier(cat.score)
        fill_cls = "bad" if tier == "tier-bad" else ("warn" if tier == "tier-warn" else "")
        focus_cls = "focus" if focus_ko and cat.name_ko == focus_ko else ""

        prior_score = prior_by_ko.get(cat.name_ko)
        if prior_score is not None:
            prior_mark = f'<span class="prior" style="left:{prior_score}%"></span>'
            d = cat.score - prior_score
            deltas.append(d)
            if d > 0:
                delta_html = f'<span class="bd-delta up">▲ {d}</span>'
            elif d < 0:
                delta_html = f'<span class="bd-delta down">▼ {-d}</span>'
            else:
                delta_html = '<span class="bd-delta same">— 0</span>'
        else:
            prior_mark = ""
            delta_html = '<span class="bd-delta none">처음</span>'

        rows.append(f"""
        <div class="bd-row {focus_cls}">
          <div class="bd-name">
            <span class="ic">{_CATEGORY_ICONS[ic_key]}</span>
            <span>{short}</span>
          </div>
          <div class="bd-bar">
            <span class="fill {fill_cls}" style="--w:{cat.score}%;width:{cat.score}%"></span>
            {prior_mark}
          </div>
          <span class="bd-score">{cat.score}</span>
          {delta_html}
        </div>
        """)

    if focus_ko:
        h2_text = f'가장 약한 곳은 <em>{focus_ko}</em>예요.'
    else:
        h2_text = '모든 카테고리가 안정적이었어요.'

    meta_html = ""
    if deltas:
        avg = sum(deltas) / len(deltas)
        sign = "+" if avg >= 0 else ""
        meta_html = f'<div class="meta">지난번 대비 <b>{sign}{avg:.1f}점</b></div>'

    return f"""
    <section class="results-breakdown">
      <div class="results-section-head">
        <div>
          <span class="label">카테고리 · Breakdown</span>
          <h2>{h2_text}</h2>
        </div>
        {meta_html}
      </div>
      <div class="bd-list">
        {''.join(rows)}
      </div>
    </section>
    """


# ─── Surviving v4 helpers (still used by hero-prior block) ─────────────

def _count_by_category(events) -> dict[str, int]:
    """Tally event counts keyed by score-category short key (e.g. 'distance')."""
    out: dict[str, int] = {}
    for e in events or []:
        out[e.category] = out.get(e.category, 0) + 1
    return out


def _name_ko_to_key() -> dict[str, str]:
    from core.schema import SCORE_CATEGORY_DEFS
    return {ko: key for key, _en, ko, _icon in SCORE_CATEGORY_DEFS}


def _category_tier(s: int) -> str:
    if s >= 85:
        return "tier-good"
    if s >= 70:
        return "tier-warn"
    return "tier-bad"


def _hero_sentence(score, events, prior=None) -> tuple[str, str]:
    """4-branch history-aware narrative used to populate the hero-prior block.
    Same logic as v4 — preserved verbatim because it's already battle-tested."""
    if not score:
        return ("분석이 완료되었어요.", "결과를 정리하고 있어요.")

    overall = score.total
    focus = score.focus_area
    n_total = len(events) if events else 0
    n_risk    = sum(1 for e in (events or []) if e.severity == "danger")
    n_caution = sum(1 for e in (events or []) if e.severity == "caution")

    if prior is not None:
        return _hero_with_history(score, events, prior,
                                  overall, focus, n_total, n_risk, n_caution)

    # First analysis ever
    if overall >= 88 and n_risk == 0:
        hero = "오늘 주행, <em>정말 안정적</em>이었어요."
    elif overall >= 75:
        if focus:
            hero = f"평균 이상이지만,<br/><em>{focus.name_ko}</em>에서 살짝 아쉬웠어요."
        else:
            hero = "평균 이상으로 <em>안정적인 주행</em>이었어요."
    elif overall >= 60:
        if focus:
            hero = (f"몇 군데 주의가 필요했어요.<br/>"
                    f"특히 <em>{focus.name_ko}</em>를 다음에 신경 써 보세요.")
        else:
            hero = "조금 더 안정적으로 갈 수 있을 것 같아요."
    else:
        if focus:
            hero = (f"다음 주행에서 바꿀 것이 있어요.<br/>"
                    f"<em>{focus.name_ko}</em>가 오늘의 가장 큰 이슈예요.")
        else:
            hero = "오늘은 평소보다 <em>거친 주행</em>이었어요."

    if n_total == 0:
        secondary = "큰 위험 없이 부드럽게 흘러갔어요. 다음 주행부터 비교가 시작됩니다."
    elif n_risk > 0:
        secondary = (f"총 {n_total}건의 핵심 순간, 그 중 {n_risk}건이 위험 구간이었어요. "
                     f"다음 주행과 비교해 볼게요.")
    elif n_caution > 0:
        secondary = (f"총 {n_total}건의 핵심 순간, {n_caution}건이 주의가 필요했어요. "
                     f"다음 주행과 비교해 볼게요.")
    else:
        secondary = f"총 {n_total}건의 핵심 순간이 있었어요. 다음 주행과 비교해 볼게요."

    return (hero, secondary)


def _hero_with_history(score, events, prior,
                       overall: int, focus, n_total: int,
                       n_risk: int, n_caution: int) -> tuple[str, str]:
    prior_score = prior.score.total
    delta = overall - prior_score
    prior_focus = prior.score.focus_area
    now_cats = _count_by_category(events)
    prior_cats = _count_by_category(prior.events)

    same_focus = (focus is not None and prior_focus is not None
                  and focus.name_ko == prior_focus.name_ko)
    ko2key = _name_ko_to_key()

    if same_focus and focus is not None:
        key = ko2key.get(focus.name_ko, "")
        now_n = now_cats.get(key, 0)
        prior_n = prior_cats.get(key, 0)
        if now_n and prior_n and now_n < prior_n:
            hero = (f"지난번에 얘기한 <em>{focus.name_ko}</em>,<br/>"
                    f"이번엔 {prior_n}건 → {now_n}건으로 좋아졌어요.")
        elif now_n and prior_n and now_n > prior_n:
            hero = (f"지난번에도 <em>{focus.name_ko}</em>가 이슈였는데,<br/>"
                    f"이번엔 더 자주 나왔어요 ({prior_n} → {now_n}건).")
        else:
            hero = (f"지난번에도 같은 패턴이 보였어요.<br/>"
                    f"<em>{focus.name_ko}</em>를 한 번 더 신경 써 볼 시간이에요.")
        secondary = _secondary_with_delta(delta, n_total, n_risk, n_caution)
        return (hero, secondary)

    if (prior_focus is not None
            and (focus is None or focus.name_ko != prior_focus.name_ko)
            and delta >= -2):
        prior_key = ko2key.get(prior_focus.name_ko, "")
        prior_n = prior_cats.get(prior_key, 0)
        now_n = now_cats.get(prior_key, 0)
        if now_n == 0 and prior_n > 0:
            hero = (f"지난번 가장 큰 이슈였던 <em>{prior_focus.name_ko}</em>,<br/>"
                    f"오늘은 한 번도 나오지 않았어요.")
            secondary = _secondary_with_delta(delta, n_total, n_risk, n_caution)
            return (hero, secondary)

    if delta >= 3:
        if focus:
            hero = (f"지난번보다 <em>+{delta}점</em>.<br/>"
                    f"다음엔 {focus.name_ko}만 손보면 더 좋을 것 같아요.")
        else:
            hero = f"지난번보다 <em>+{delta}점</em>,<br/>전반적으로 안정적이었어요."
    elif delta <= -3:
        if focus:
            hero = (f"지난번보다 <em>{delta}점</em>.<br/>"
                    f"오늘은 <em>{focus.name_ko}</em>에서 아쉬웠어요.")
        else:
            hero = f"지난번보다 <em>{delta}점</em>,<br/>오늘은 평소만큼은 아니었어요."
    else:
        if overall >= 88 and n_risk == 0:
            hero = f"지난번과 비슷하게 <em>안정적</em>이었어요."
        elif focus:
            hero = (f"비슷한 점수, 같은 톤의 주행이에요.<br/>"
                    f"<em>{focus.name_ko}</em>에서 조금 더 여유를 가져 보세요.")
        else:
            hero = "지난번과 비슷한 흐름으로 안정적이었어요."

    secondary = _secondary_with_delta(delta, n_total, n_risk, n_caution)
    return (hero, secondary)


def _secondary_with_delta(delta: int, n_total: int,
                          n_risk: int, n_caution: int) -> str:
    sign = "+" if delta > 0 else ""
    delta_str = f"점수 변화 {sign}{delta}점" if delta != 0 else "점수 변화 없음"
    if n_total == 0:
        return f"이번엔 큰 위험 없이 부드럽게 흘러갔어요 · {delta_str}."
    if n_risk > 0:
        return (f"총 {n_total}건의 핵심 순간, 그 중 {n_risk}건이 위험 구간이었어요 · "
                f"{delta_str}.")
    if n_caution > 0:
        return (f"총 {n_total}건의 핵심 순간, {n_caution}건이 주의가 필요했어요 · "
                f"{delta_str}.")
    return f"총 {n_total}건의 핵심 순간이 있었어요 · {delta_str}."


# ─── The screen ───────────────────────────────────────────────

def results_screen_html(
    video_path: str = "",
    filename: str = "",
    duration: float = 0.0,
    score=None,
    events=None,
    coachings=None,
    event_stills: dict | None = None,
    session_id: str = "—",
    prior=None,
    from_history: bool = False,
) -> str:
    """RESULTS v5 — coaching sentence is the hero, score is supporting,
    annotated video is the evidence. One self-contained HTML blob.

    Sections top-to-bottom: nav · 4-step stepper (all done) · HERO (kicker +
    word-by-word quote + ref chip + prior block + still + score block) ·
    Evidence (annotated video + clickable timeline) · adaptive moments grid ·
    Breakdown (icon + bar + prior tick + delta chip + focus highlight) · CTA.

    `prior`: AnalysisRecord | None — when present, populates the .hero-prior
    block (longitudinal narrative) and the delta/prior-tick visuals.
    """
    events = events or []
    coachings = coachings or []
    event_stills = event_stills or {}

    # Pick the hero event + its coaching + its still
    hi = _pick_hero_event_idx(events)
    hero_event = events[hi] if hi is not None else None
    hero_coaching = coachings[hi] if (hi is not None and hi < len(coachings)) else None
    hero_still_path = event_stills.get(hero_event.frame_idx, "") if hero_event else ""

    quote_text = _hero_quote_text(hero_event, hero_coaching)
    hero_quote = _hero_quote_html(quote_text)
    hero_ref = _hero_ref_html(hero_event)
    prior_block = _hero_prior_block_html(score, events, prior)
    hero_still = _hero_still_html(hero_still_path, hero_event)
    score_block = _score_block_html(score, prior)

    # Evidence section — annotated video + timeline
    vurl = _video_url(video_path)
    if vurl:
        video_el = (f'<video controls preload="metadata" playsinline '
                    f'src="{vurl}" id="dc-results-video"></video>')
    else:
        video_el = ('<div class="video-stage-empty">'
                    '주석 영상이 준비되지 않았어요.</div>')
    timeline = _timeline_html_v5(events, duration)
    dur_str = _fmt_duration(duration)

    evidence_section = f"""
    <section class="results-evidence">
      <div class="results-section-head">
        <div>
          <span class="label">증거 · Evidence</span>
          <h2>AI가 본 <em>{dur_str}</em>, 그대로.</h2>
        </div>
        <div class="meta"><b>00:00</b> — <b>{dur_str}</b> · <b>{len(events)}</b>개 순간</div>
      </div>
      <div class="video-stage" id="dc-results-stage">
        {video_el}
      </div>
      {timeline}
    </section>
    """

    moments_section = _moments_section_html(events, coachings, event_stills, duration)
    breakdown_section = _breakdown_section_html(score, prior)

    safe_name = filename or "주행 영상"
    # HISTORY 드릴다운으로 열렸을 때만 '← 기록' 버튼을 노출 (dc-history-hit 로 브릿지).
    # 분석 직후의 RESULTS 에는 기록 목록이 맥락에 없으므로 표시하지 않는다.
    back_to_history = (
        '<button class="history-back" type="button" id="results-tohistory-btn" '
        'aria-label="기록으로 돌아가기">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M19 12 L5 12 M11 6 L5 12 L11 18"/></svg>기록</button>'
    ) if from_history else ""

    return f"""
<div class="dc-v3-root results-root">

  <nav class="results-nav">
    <a class="results-brand" href="#dc-top" aria-label="BackMirror">
      <span class="mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>BACK<span class="accent">MIRROR</span></span>
    </a>
    <div class="results-nav-right">
      {back_to_history}
      <span class="ready-pill"><span class="dot"></span>리포트 준비됨</span>
      <span>SESSION · {session_id}</span>
    </div>
  </nav>

  <div class="results-stepper">
    <div class="results-step done"><span class="num">01</span><span class="check">✓</span><span>업로드</span></div>
    <div class="results-step done"><span class="num">02</span><span class="check">✓</span><span>검토</span></div>
    <div class="results-step done"><span class="num">03</span><span class="check">✓</span><span>분석</span></div>
    <div class="results-step done"><span class="num">04</span><span class="check">✓</span><span>리포트</span></div>
  </div>

  <section class="results-hero">
    <div class="hero-copy">
      <span class="kicker">이번 주행의 한 마디 <span class="of">/ COACH&rsquo;S NOTE</span></span>
      {hero_quote}
      {hero_ref}
      {prior_block}
    </div>
    <div class="hero-still-wrap">
      {hero_still}
      {score_block}
    </div>
  </section>

  {evidence_section}

  {moments_section}

  {breakdown_section}

  <section class="results-cta">
    <div class="cta-line">다음 주행, 더 나아지려면</div>
    <button class="ready-btn-go" type="button" id="results-again-btn">
      다른 영상으로 다시 시작
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 12 L19 12 M13 6 L19 12 L13 18"/>
      </svg>
    </button>
  </section>

  <footer class="results-foot">© 2026 BACKMIRROR · 세션 {session_id}</footer>

</div>
"""


# ─── HISTORY — v6 SPINE redesign ─────────────────────────────
# Soul: not a dashboard. A single vertical spine (운전 여정). Each analysis
# is a node on the spine; the gap between adjacent nodes carries the
# narrative of what improved or kept repeating. Milestones glow on the
# spine. The structure itself proves "기억하는 코치".
#
# Three states:
#   • n == 0  → empty-state (clock icon + first-drive CTA)
#   • n == 1  → sparse-state (one-card welcome + focus area note)
#   • n >= 2  → full journey (overview card + milestone ribbon + spine)

from datetime import datetime as _dt


def _relative_date(iso_ts: str) -> str:
    """ISO timestamp → human-friendly Korean relative date.
    Matches the design's whenLabel ranges so node copy reads natural."""
    try:
        then = _dt.fromisoformat(iso_ts)
    except (TypeError, ValueError):
        return iso_ts or "—"
    diff = _dt.now() - then
    days = diff.days
    if days < 0:
        return then.strftime("%Y.%m.%d")
    if days == 0:
        hours = diff.seconds // 3600
        if hours <= 0:
            return "방금 전"
        return f"{hours}시간 전"
    if days == 1:
        return "어제"
    if days < 7:
        return f"{days}일 전"
    if days < 14:
        return "지난주"
    if days < 30:
        return f"{days // 7}주 전"
    if days < 365:
        return f"{days // 30}개월 전"
    return then.strftime("%Y.%m.%d")


def _spine_sparkline_svg(scores: list[int]) -> str:
    """Compact sparkline for the overview card.
    Renders the score series oldest→newest left-to-right inside a 100x90
    viewBox (CSS handles actual width); auto-scales Y so visit-to-visit
    differences stay visible even on flat ranges."""
    if not scores:
        return ""
    pts = scores
    n = len(pts)
    # Wide viewBox (≈6.7:1). The SVG renders with width:100% + height:auto so
    # the element keeps THIS aspect ratio — that's what stops preserveAspect
    # ratio="none" from squashing the dots into horizontal ovals. Padding
    # leaves room for edge dots + the latest-dot halo (r=7).
    W, H, pad_x, pad_y = 600, 90, 40, 16
    raw_lo, raw_hi = min(pts), max(pts)
    # Minimum visible span so a tight cluster (e.g. 94..97) doesn't span the
    # entire chart height and exaggerate small differences. Re-centers the
    # data within the expanded range, clamped to 0..100.
    MIN_SPAN = 12
    span = max(MIN_SPAN, raw_hi - raw_lo)
    mid = (raw_lo + raw_hi) / 2
    lo = max(0.0, min(100.0 - span, mid - span / 2))
    hi = lo + span
    def xs(i: int) -> float:
        if n == 1:
            return W / 2
        return pad_x + (W - 2 * pad_x) * (i / (n - 1))
    def ys(v: int) -> float:
        return pad_y + (H - 2 * pad_y) * (1 - (v - lo) / span)
    d = ""
    for i, v in enumerate(pts):
        d += ("M" if i == 0 else "L") + f"{xs(i):.2f},{ys(v):.2f} "
    area = (d + f"L{xs(n-1):.2f},{H} L{xs(0):.2f},{H} Z")
    last_x, last_y = xs(n - 1), ys(pts[-1])
    dots = "".join(
        f'<circle class="spark-dot{ " last" if i == n - 1 else ""}" '
        f'cx="{xs(i):.2f}" cy="{ys(v):.2f}" r="{3 if i == n - 1 else 2}"/>'
        for i, v in enumerate(pts)
    )
    return f"""
      <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none">
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(0,229,154,0.35)"/>
            <stop offset="100%" stop-color="rgba(0,229,154,0)"/>
          </linearGradient>
        </defs>
        <path class="spark-area" d="{area.strip()}"/>
        <path class="spark-line" d="{d.strip()}"/>
        <circle class="spark-halo" cx="{last_x:.2f}" cy="{last_y:.2f}" r="7"/>
        {dots}
      </svg>
    """


# Korean short labels for focus_area (matches RESULTS breakdown short names).
_HISTORY_CAT_SHORT = {
    "신호 인지": "신호", "차선 준수": "차선", "보행자 주의": "보행자",
    "속도 관리": "속도", "안전거리": "안전거리",
}
_HISTORY_CAT_KEY = {
    "신호 인지": "signal", "차선 준수": "lane",
    "보행자 주의": "pedestrian", "속도 관리": "speed",
    "안전거리": "distance",
}
# Same 5 icons as RESULTS — kept here as a small standalone copy so the
# HISTORY screen has no cross-section dependency on the RESULTS helpers.
_HISTORY_CAT_ICONS = {
    "signal": ('<svg viewBox="0 0 24 24"><rect x="6" y="3" width="12" height="18" rx="2"/>'
               '<circle cx="12" cy="8" r="1.5"/><circle cx="12" cy="13" r="1.5"/>'
               '<circle cx="12" cy="18" r="1.5"/></svg>'),
    "lane": ('<svg viewBox="0 0 24 24"><line x1="6" y1="3" x2="6" y2="21"/>'
             '<line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="10" x2="12" y2="14"/>'
             '<line x1="12" y1="18" x2="12" y2="21"/><line x1="18" y1="3" x2="18" y2="21"/></svg>'),
    "pedestrian": ('<svg viewBox="0 0 24 24"><circle cx="12" cy="4" r="2"/>'
                   '<path d="M12 7 v8 M12 15 l-3 6 M12 15 l3 6 M9 10 l-3 -1 M15 10 l3 -1"/></svg>'),
    "speed": ('<svg viewBox="0 0 24 24"><path d="M4 14 a8 8 0 0 1 16 0"/>'
              '<path d="M12 14 l4 -4"/><circle cx="12" cy="14" r="1.5"/></svg>'),
    "distance": ('<svg viewBox="0 0 24 24"><rect x="3" y="13" width="6" height="6"/>'
                 '<rect x="15" y="13" width="6" height="6"/>'
                 '<line x1="9" y1="16" x2="15" y2="16" stroke-dasharray="1.5 2"/></svg>'),
}


def _grade_cls(grade: str) -> str:
    g = (grade or "").upper()
    if g.startswith("A"):
        return ""
    if g.startswith("B"):
        return "b"
    if g.startswith("C"):
        return "c"
    return "d"


def _gap_narrative(newer, older) -> str:
    """One-line narrative between two adjacent records (newer above older
    in the spine). Compares focus_area + score delta to surface 'pattern
    repeated' vs 'focus shifted' vs 'big jump'. Uses .imp (signal green)
    for improvements and .pat (amber) for repeated weaknesses."""
    new_focus = newer.score.focus_area
    old_focus = older.score.focus_area
    new_ko = new_focus.name_ko if new_focus else None
    old_ko = old_focus.name_ko if old_focus else None
    d = newer.score.total - older.score.total
    # Same focus_area on both → pattern continued
    if new_ko and old_ko and new_ko == old_ko:
        short = _HISTORY_CAT_SHORT.get(new_ko, new_ko)
        if d >= 4:
            return (f'<span class="imp">+{d}점</span> · 그래도 '
                    f'<span class="pat">{short}</span>가 계속 약점이에요')
        if d <= -4:
            return (f'<span class="pat">{-d}점 하락</span> · '
                    f'<span class="pat">{short}</span>가 반복되고 있어요')
        return f'<span class="pat">{short}</span> 약점이 이어졌어요'
    # Focus shifted
    if new_ko and old_ko:
        old_short = _HISTORY_CAT_SHORT.get(old_ko, old_ko)
        new_short = _HISTORY_CAT_SHORT.get(new_ko, new_ko)
        sign = f'<span class="imp">+{d}점</span> · ' if d >= 0 else f'{d}점 · '
        return (f'{sign}약점이 <span class="pat">{old_short}</span> → '
                f'<span class="imp">{new_short}</span>로 옮겨갔어요')
    # One side had no focus → essentially clean
    if not new_ko:
        return f'<span class="imp">+{d}점</span> · 이번엔 약점이 없었어요' if d >= 0                else f'{d}점 · 이번엔 약점이 없었어요'
    short = _HISTORY_CAT_SHORT.get(new_ko, new_ko)
    sign = f'<span class="imp">+{d}점</span> · ' if d >= 0 else f'{d}점 · '
    return f'{sign}새 약점 <span class="pat">{short}</span>가 보였어요'


def _milestones(records) -> list[str]:
    """Up to 4 milestone strings to show in the ribbon. records newest-first.
    Pure derivations — no fake data, only what the records actually say."""
    n = len(records)
    if n == 0:
        return []
    out: list[str] = []
    # 1) Count milestone
    if n >= 10:
        out.append(f'<b>{n}번째</b> 분석 — 꾸준함이 데이터가 됐어요')
    elif n >= 5:
        out.append(f'<b>{n}번째</b> 분석 기록')
    # 2) First A-grade (oldest → newest scan)
    for r in reversed(records):
        if (r.score.grade or "").upper().startswith("A"):
            out.append('첫 <b>A등급</b> 달성')
            break
    # 3) Best score
    best = max(r.score.total for r in records)
    out.append(f'최고 점수 <b>{best}점</b>')
    # 4) Recent upswing — compare newest vs ~3rd most recent
    if n >= 3:
        recent = records[0].score.total
        older = records[min(n - 1, 2)].score.total
        if recent - older >= 6:
            out.append(f'최근 <b>+{recent - older}점</b> 상승세')
    return out[:4]


def _score_tier(total: int) -> str:
    """Spine bullet color tier by score, aligned to the A / B–C / D grade
    bands: green (good) ≥ 90, amber (warn) 70–89, red (bad) < 70."""
    if total >= 90:
        return "tier-good"
    if total >= 70:
        return "tier-warn"
    return "tier-bad"


def _node_card_html(record, is_latest: bool, is_milestone: bool) -> str:
    """One node on the spine — bullet colored by score tier (green/amber/red)
    + card with date / name / score / focus / event pip counts."""
    score = record.score
    grade = score.grade or "—"
    grade_class = _grade_cls(grade)
    focus = score.focus_area
    if focus:
        focus_ko = focus.name_ko
        focus_short = _HISTORY_CAT_SHORT.get(focus_ko, focus_ko)
        focus_key = _HISTORY_CAT_KEY.get(focus_ko, "signal")
        focus_html = (
            f'<span class="ic">{_HISTORY_CAT_ICONS[focus_key]}</span>'
            f'가장 약함 · <b>{focus_short}</b>'
        )
    else:
        focus_html = '<span style="color:var(--signal)">약점 없음</span>'

    risk = sum(1 for e in record.events if e.severity == "danger")
    caution = sum(1 for e in record.events if e.severity == "caution")
    pips = ""
    if risk:
        pips += f'<span class="pip risk"></span>{risk}'
    if caution:
        pips += f'<span class="pip amber"></span>{caution}'
    if not pips:
        pips = '<span class="pip safe"></span>0'

    when = _relative_date(record.analyzed_at)
    latest_tag = '<span class="latest-tag">최근</span>' if is_latest else ''

    cls_extras = [_score_tier(score.total)]
    if is_latest:
        cls_extras.append("latest")
    if is_milestone:
        cls_extras.append("milestone-node")
    extra = " " + " ".join(cls_extras)

    return f"""
    <div class="node{extra}">
      <div class="node-bullet"></div>
      <div class="node-card" data-session-id="{record.session_id}"
           role="button" tabindex="0">
        <button class="nc-del" data-session-id="{record.session_id}"
                data-nth="{record.session_id}" title="삭제" aria-label="삭제">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round">
            <path d="M6 6 L18 18 M18 6 L6 18"/>
          </svg>
        </button>
        <div class="nc-top">
          <div class="nc-meta">
            <div class="nc-when">{when}{latest_tag}</div>
            <div class="nc-name">{record.video_name or '주행 영상'}</div>
          </div>
          <div class="nc-score">
            <span class="num">{score.total}</span>
            <span class="grade {grade_class}">{grade}</span>
          </div>
        </div>
        <div class="nc-bottom">
          <div class="nc-focus">{focus_html}</div>
          <div class="nc-events">{pips}</div>
        </div>
      </div>
    </div>
    """


def _node_gap_html(narrative_html: str) -> str:
    """Small one-line narrative between two adjacent nodes."""
    return f"""
    <div class="node-gap">
      <div class="gap-spacer"></div>
      <div class="gap-text">{narrative_html}</div>
    </div>
    """


def _history_cta_footer_html(n: int) -> str:
    return f"""
    <section class="history-cta">
      <button class="ready-btn-go" type="button" id="history-upload-btn">
        새 영상 분석하기
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12 L19 12 M13 6 L19 12 L13 18"/>
        </svg>
      </button>
    </section>
    <footer class="history-foot">© 2026 BACKMIRROR · 당신의 운전을 기억합니다</footer>
    """


def _history_nav_html(n: int) -> str:
    return f"""
    <nav class="history-nav">
      <div class="history-nav-left">
        <button class="history-back" type="button" id="history-back-btn"
                aria-label="홈으로 돌아가기">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12 L5 12 M11 6 L5 12 L11 18"/>
          </svg>
          홈
        </button>
        <a class="history-brand" href="#dc-top" aria-label="BackMirror">
          <span class="mark" aria-hidden="true">{_BRAND_SVG}</span>
          <span>BACK<span class="accent">MIRROR</span></span>
        </a>
      </div>
      <div class="history-nav-right">
        <span class="count-pill">MY HISTORY · <b>{n}</b>건</span>
      </div>
    </nav>
    """


def history_screen_html(records=None, session_id: str = "—") -> str:
    """v6 spine layout. Three branches by record count: 0 (empty), 1 (sparse),
    2+ (full journey with overview + milestones + spine).

    Node cards carry `data-session-id` so DC_BOOT_JS can wire card click →
    drilldown (re-show that past analysis). The × button keeps the same
    `data-session-id` interface used by the delete bridge.
    """
    records = list(records or [])
    n = len(records)
    nav = _history_nav_html(n)

    # ── n == 0 : empty state ──
    if n == 0:
        return f"""
<div class="dc-v3-root history-root">
  {nav}
  <section class="history-empty">
    <span class="em-mark">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 8v4l3 2"/><circle cx="12" cy="12" r="9"/>
      </svg>
    </span>
    <h2>아직 기억할 주행이 없어요.</h2>
    <p>첫 영상을 분석하면 이 자리에 당신의 운전 여정이<br/>
       한 줄로 쌓이기 시작합니다.</p>
    <button class="ready-btn-go" type="button" id="history-upload-btn">
      첫 주행 분석하기
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 12 L19 12 M13 6 L19 12 L13 18"/>
      </svg>
    </button>
  </section>
</div>
"""

    # ── n == 1 : sparse state ──
    if n == 1:
        r = records[0]
        focus = r.score.focus_area
        focus_ko = focus.name_ko if focus else None
        focus_short = _HISTORY_CAT_SHORT.get(focus_ko, focus_ko) if focus_ko else None
        focus_line = (
            f'가장 약한 부분은 <b style="color:var(--ink)">{focus_short}</b>였어요. '
            f'다음 주행에서 이 부분이 좋아지는지 같이 지켜볼게요.'
        ) if focus_short else (
            '큰 약점 없이 부드럽게 흘러간 주행이었어요. '
            '다음 주행과 비교해 어떤 톤이 이어지는지 같이 볼게요.'
        )
        return f"""
<div class="dc-v3-root history-root">
  {nav}

  <section class="history-header">
    <span class="kicker">내 주행 기록 / MY JOURNEY</span>
    <h1>여정이 <span class="accent">시작됐어요.</span></h1>
    <p class="sub">첫 분석을 기록했습니다. 다음 주행부터 지난번과
       무엇이 달라졌는지, 어떤 패턴이 반복되는지 이 자리에서 이어서 보여드릴게요.</p>
  </section>

  <section class="history-sparse">
    <div class="sparse-card">
      <span class="sc-mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 17 L9 11 L13 15 L21 7"/>
          <path d="M21 7 h-5 M21 7 v5"/>
        </svg>
      </span>
      <h2>{r.video_name or '주행 영상'}</h2>
      <p>{focus_line}</p>
      <div class="sc-score">
        <span class="num" style="color:var(--signal)">{r.score.total}</span>
        <span class="unit">/100 · {r.score.grade}</span>
      </div>
    </div>
  </section>

  {_history_cta_footer_html(n)}
</div>
"""

    # ── n >= 2 : full journey ──
    first = records[-1]
    latest = records[0]
    delta_total = latest.score.total - first.score.total
    best = max(r.score.total for r in records)
    best_session_ids = {r.session_id for r in records if r.score.total == best}

    # Sparkline: oldest → newest left-to-right
    scores_chrono = [r.score.total for r in reversed(records)]
    spark = _spine_sparkline_svg(scores_chrono)

    # Milestone ribbon
    ms_lines = _milestones(records)
    star_svg = ('<svg viewBox="0 0 24 24" fill="currentColor">'
                '<path d="M12 2l2.39 6.95L21 9.27l-5.45 4.73L17.18 21'
                ' 12 17.27 6.82 21l1.63-6.99L3 9.27l6.61-.32z"/></svg>')
    ms_html = "".join(
        f'<div class="milestone"><span class="ms-mark">{star_svg}</span>'
        f'<span class="ms-text">{m}</span></div>'
        for m in ms_lines
    )

    # Spine nodes + gap narratives
    spine_parts: list[str] = []
    for i, r in enumerate(records):
        is_latest = (i == 0)
        # milestone glow if: (a) A-grade, or (b) tied best score and not latest
        is_milestone = (
            (r.score.grade or "").upper().startswith("A")
            or (r.score.total == best and not is_latest
                and r.session_id in best_session_ids)
        )
        spine_parts.append(_node_card_html(r, is_latest, is_milestone))
        if i + 1 < len(records):
            spine_parts.append(_node_gap_html(_gap_narrative(r, records[i + 1])))

    latest_focus = latest.score.focus_area
    latest_focus_short = (_HISTORY_CAT_SHORT.get(latest_focus.name_ko, latest_focus.name_ko)
                          if latest_focus else "없음")

    delta_chip = (
        f'<span class="chip up">▲ +{delta_total}</span>' if delta_total >= 0
        else f'<span class="chip down">▼ {-delta_total}</span>'
    )

    first_when = _relative_date(first.analyzed_at)

    return f"""
<div class="dc-v3-root history-root">
  {nav}

  <section class="history-header">
    <span class="kicker">내 주행 기록 / MY JOURNEY</span>
    <h1>{n}번의 주행,<br/><span class="accent">패턴이 보이기 시작해요.</span></h1>
    <p class="sub">BackMirror는 매 분석을 기억합니다. 점수만이 아니라,
       무엇이 좋아졌고 어떤 약점이 반복되는지를 한 줄의 여정으로 이어드려요.</p>
  </section>

  <section class="history-overview">
    <div class="ov-card">
      <div class="ov-spark">
        <div class="ov-label">
          <span>점수 추이 · SCORE TREND</span>
          <span class="range">{first_when} → 오늘</span>
        </div>
        <div class="spark-wrap">{spark}</div>
      </div>
      <div class="ov-stats">
        <div class="ov-stat">
          <span class="k">처음 → 최근</span>
          <span class="v">{first.score.total} → {latest.score.total} {delta_chip}</span>
        </div>
        <div class="ov-stat">
          <span class="k">최고 점수</span>
          <span class="v">{best}<span style="color:var(--muted-2);font-size:12px">/100</span></span>
        </div>
        <div class="ov-stat">
          <span class="k">지금 가장 약한 곳</span>
          <span class="v" style="color:var(--amber)">{latest_focus_short}</span>
        </div>
      </div>
    </div>
  </section>

  {f'<div class="history-milestones">{ms_html}</div>' if ms_html else ''}

  <section class="history-spine">
    <div class="spine-head">
      <div>
        <span class="label">여정 · Timeline</span>
        <h2>최근부터 <em>처음</em>까지.</h2>
      </div>
    </div>
    <div class="spine">
      {''.join(spine_parts)}
    </div>
  </section>

  {_history_cta_footer_html(n)}
</div>
"""


# ─── Always-on header / footer for non-IDLE screens ───────────
# When IDLE is hidden, the v3 nav (inside idle_hero_html) is also hidden
# — so we render a minimal header/footer here for UPLOADED/ANALYZING/RESULTS.
# Both are wrapped in .dc-v3-root so v3 styles apply.

def app_header_html() -> str:
    """Minimal always-visible header for non-IDLE screens.

    The full v3 fixed nav lives inside `idle_hero_html()`; that one is
    visible only on the IDLE screen. This one is a *static* (non-fixed)
    header that shows on UPLOADED/ANALYZING/RESULTS so the user can still
    click the brand to go home.
    """
    return f"""
    <div class="dc-v3-root" style="background: transparent;">
      <div style="padding: 18px var(--v3-pad); display: flex;
                  align-items: center; justify-content: space-between;">
        {_brand_html()}
      </div>
    </div>
    """


def footer_html() -> str:
    """Compact footer for non-IDLE screens (the full v3 footer lives in IDLE)."""
    return """
    <div class="dc-v3-root" style="background: transparent;">
      <div class="foot-bar" style="padding: 28px var(--v3-pad); margin-top: 0;
                                    border-top: 1px solid var(--line);">
        <div class="left">© 2026 BackMirror</div>
        <div class="right">
          <span>KR · KO</span>
          <a href="#">Status</a>
          <a href="#">Security</a>
        </div>
      </div>
    </div>
    """
