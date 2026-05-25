"""DrivingAssis AI landing page — v3 editorial / cinematic.

The IDLE screen is a 7-section marketing page based on the v3 HTML mock
(DrivingAssis v3.html — real photos + SVG annotations):

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


# ─── Shared bits ──────────────────────────────────────────────

def _arrow_svg() -> str:
    return ('<svg class="arrow" viewBox="0 0 12 12" fill="none" '
            'stroke="currentColor" stroke-width="1.6">'
            '<path d="M2 6h8M7 2l4 4-4 4"/></svg>')


_BRAND_SVG = (
    '<svg viewBox="0 0 32 32" fill="none">'
    '<path d="M2 8 L2 2 L8 2" stroke="#00E59A" stroke-width="1.6" stroke-linecap="square"/>'
    '<path d="M24 2 L30 2 L30 8" stroke="#00E59A" stroke-width="1.6" stroke-linecap="square"/>'
    '<path d="M30 24 L30 30 L24 30" stroke="#00E59A" stroke-width="1.6" stroke-linecap="square"/>'
    '<path d="M8 30 L2 30 L2 24" stroke="#00E59A" stroke-width="1.6" stroke-linecap="square"/>'
    '<path d="M6 28 L14.5 14" stroke="#00E59A" stroke-width="2" stroke-linecap="round"/>'
    '<path d="M26 28 L17.5 14" stroke="#00E59A" stroke-width="2" stroke-linecap="round"/>'
    '<path d="M16 28 L16 22" stroke="#00E59A" stroke-width="1.6" stroke-linecap="round"/>'
    '<path d="M16 19 L16 15.5" stroke="#00E59A" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>'
    '<circle cx="16" cy="13" r="1.6" fill="#00E59A"/>'
    '</svg>'
)


def _brand_html() -> str:
    """Shared brand mark — used in nav + footer."""
    return (
        '<a class="brand" href="#dc-top" aria-label="DrivingAssis">'
        f'<span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>'
        '<span>DRIVING<span style="color:var(--signal)">ASSIS</span></span>'
        '</a>'
    )


# ─── 1. NAV ───────────────────────────────────────────────────

def _nav_html() -> str:
    arrow = _arrow_svg()
    return f"""
    <header class="nav" id="dc-nav">
      {_brand_html()}
      <a class="btn btn-primary" href="#dc-upload">영상 업로드 {arrow}</a>
    </header>
    """


# ─── 2. HERO — dual-frame ─────────────────────────────────────

def _hero_section() -> str:
    # Local hero.mp4 (in assets/) — served by Gradio via allowed_paths.
    # We use the gradio_api/file route which Gradio exposes for static files.
    hero_video = "/gradio_api/file=assets/hero.mp4"
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
          블랙박스 영상을 올리면 DrivingAssis가 급제동·차선 이탈·차간거리 부족 같은
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
          <span class="frame-tag mono">AI · DrivingAssis</span>
          <span class="frame-tc">00:00:13:21 · 24 fps</span>
          <video autoplay muted loop playsinline preload="auto"
                 aria-label="야간 주행 POV — AI 분석"
                 src="{hero_video}"></video>

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
                src="https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?auto=format&fit=crop&w=900&q=80"/>
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
                src="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80"/>
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
                src="https://images.unsplash.com/photo-1485463611174-f302f6a5c1c9?auto=format&fit=crop&w=900&q=80"/>
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
        <h2 data-reveal>리포트가 짚어주는<br/><em>네 가지 순간.</em></h2>
      </div>
      <div class="numbers-grid">
        <div class="num" data-reveal>
          <div class="l">Event · 01</div>
          <div class="v" style="{big}">급제동</div>
          <div class="d">앞 차량 감속·보행자 진입 등으로 짧은 시간에 큰 감속이 발생한 구간을 찾습니다.</div>
        </div>
        <div class="num" data-reveal style="--rd:120ms">
          <div class="l">Event · 02</div>
          <div class="v" style="{big}">차선 이탈</div>
          <div class="d">방향지시등 없이 차선을 넘어가거나, 차선 안에서 좌우 흔들림이 큰 구간을 표시합니다.</div>
        </div>
        <div class="num" data-reveal style="--rd:240ms">
          <div class="l">Event · 03</div>
          <div class="v" style="{big}">차간거리 부족</div>
          <div class="d">앞 차량과의 시간 간격이 권장 수준 아래로 떨어져 지속된 구간을 따로 모아 보여드립니다.</div>
        </div>
        <div class="num" data-reveal style="--rd:360ms">
          <div class="l">Event · 04</div>
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
      <div class="foot-mini mono">© 2026 DRIVINGASSIS</div>
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


# Back-compat empty stubs — referenced from app.py.
IDLE_DROPZONE_INTRO = ""
IDLE_HOWITWORKS_HTML = ""
IDLE_HERO_HTML = ""
HERO_GRID_BG = ""


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
    <a class="brand" href="#dc-top" aria-label="DrivingAssis">
      <span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>DRIVING<span style="color:var(--signal)">ASSIS</span></span>
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

  <footer class="ready-foot">© 2026 DRIVINGASSIS · 분석 세션 {session_id}</footer>

</div>
"""


# Legacy stubs — kept so existing imports don't break.
def uploaded_header_html(filename: str = "", duration: float = 0.0) -> str:
    return ready_screen_html(name=filename, duration=duration)


UPLOADED_PREVIEW_CARDS_HTML = ""


# ─── ANALYZING — v4 live-analysis screen ──────────────────────
# Mirrors DrivingAssis Analyzing.html: nav (with LIVE pill) · stepper
# (steps 01-02 done, 03 current, 04 pending) · stage (progress + pipeline
# mini on left, video with live bbox overlay + scan beam on right) ·
# counter strip · 3 preview cards (score / key moments / coaching) ·
# toast layer · footer.
#
# The actual analysis runs in Python; this screen plays a 30-second
# animated demo loop on the client (driven by JS in DC_BOOT_JS) until
# Gradio swaps in the RESULTS screen.

def analyzing_screen_html(video_path: str = "", name: str = "",
                          session_id: str = "—") -> str:
    vurl = _video_url(video_path)
    video_el = (
        f'<video class="analyz-still" src="{vurl}" autoplay muted loop'
        f' playsinline preload="metadata"></video>'
        if vurl else
        '<div class="analyz-still analyz-still-empty"></div>'
    )
    safe_name = name or "—"
    return f"""
<div class="dc-v3-root analyz-root">

  <nav class="ready-nav">
    <a class="brand" href="#dc-top" aria-label="DrivingAssis">
      <span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>DRIVING<span style="color:var(--signal)">ASSIS</span></span>
    </a>
    <div class="ready-nav-right">
      <span class="analyz-live-dot">LIVE</span>
      <span class="ready-session">SESSION · {session_id}</span>
    </div>
  </nav>

  <div class="ready-stepper-wrap">
    <div class="ready-stepper" role="list">
      <div class="ready-step done" role="listitem">
        <span class="num">01</span><span class="check">✓</span><span>업로드</span>
      </div>
      <div class="ready-step done" role="listitem">
        <span class="num">02</span><span class="check">✓</span><span>검토</span>
      </div>
      <div class="ready-step current" role="listitem">
        <span class="num">03</span><span class="pulse" aria-hidden="true"></span><span>분석</span>
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
        <span class="label label-signal">Analyzing · 분석 중</span>
      </div>
      <h1>
        프레임을<br/>
        <span class="accent" id="analyz-title-accent">읽고 있습니다.</span>
        <span class="em" id="analyz-sub">지금 0번째 프레임 · 차량 0개 추적 중</span>
      </h1>
      <div class="ready-filename">
        {_file_icon_svg()}
        <div>{safe_name}</div>
      </div>

      <div class="analyz-progress-block">
        <div class="analyz-progress-head">
          <div class="analyz-pct"><span id="analyz-pct">0</span><span class="unit">%</span></div>
          <div class="analyz-eta">남은 시간 · <b id="analyz-eta">약 30초</b></div>
        </div>
        <div class="analyz-progress-bar">
          <div class="analyz-progress-fill" id="analyz-fill"></div>
          <div class="analyz-progress-scan"></div>
        </div>
        <div class="analyz-progress-foot">
          <span>처리 프레임 · <b id="analyz-frame">0 / 300</b></span>
          <span><b id="analyz-fps">0</b> 프레임/초</span>
        </div>
      </div>

      <div class="analyz-pl-mini">
        <div class="analyz-pl-step done" id="analyz-pl0">
          <span class="analyz-pl-num">01</span>
          <span class="analyz-pl-name">프레임 추출</span>
          <span class="analyz-pl-status">완료 · 4.8s</span>
        </div>
        <div class="analyz-pl-step current" id="analyz-pl1">
          <span class="analyz-pl-num">02</span>
          <span class="analyz-pl-name">객체 검출</span>
          <span class="analyz-pl-status"><span class="analyz-pulse-dot"></span>진행 중</span>
        </div>
        <div class="analyz-pl-step pending" id="analyz-pl2">
          <span class="analyz-pl-num">03</span>
          <span class="analyz-pl-name">위험 구간 분류</span>
          <span class="analyz-pl-status">대기</span>
        </div>
        <div class="analyz-pl-step pending" id="analyz-pl3">
          <span class="analyz-pl-num">04</span>
          <span class="analyz-pl-name">리포트 생성</span>
          <span class="analyz-pl-status">대기</span>
        </div>
      </div>
    </div>

    <div class="ready-video-stage">
      <div class="ready-video-frame analyz-video-frame">
        {video_el}
        <span class="ready-br ready-br-tl"></span>
        <span class="ready-br ready-br-tr"></span>
        <span class="ready-br ready-br-bl"></span>
        <span class="ready-br ready-br-br"></span>
        <div class="ready-hud ready-hud-tl">
          <span class="ready-hud-tag"><span class="analyz-live-dot-inline"></span>ANALYZING · CH1</span>
        </div>
        <div class="ready-hud ready-hud-tr">
          <span class="ready-hud-tag" id="analyz-hud-frame">FRAME 0 / 300</span>
        </div>
        <div class="ready-hud ready-hud-bl" style="bottom:22px;left:50px">
          <span class="ready-hud-tag" id="analyz-hud-tc">00:00.00s</span>
        </div>
        <div class="ready-hud ready-hud-br" style="bottom:22px;right:50px">
          <span class="ready-hud-tag" id="analyz-hud-det">DET <span style="color:var(--signal)">0</span></span>
        </div>
        <svg class="analyz-overlay" viewBox="0 0 1600 900" preserveAspectRatio="none" id="analyz-overlay"></svg>
      </div>

      <div class="analyz-counter-strip">
        <div class="analyz-counter-cell signal">
          <span class="k">차량 · Vehicles</span>
          <span class="v"><span id="analyz-c-veh">0</span></span>
        </div>
        <div class="analyz-counter-cell">
          <span class="k">보행자 · Pedestrians</span>
          <span class="v"><span id="analyz-c-ped">0</span></span>
        </div>
        <div class="analyz-counter-cell amber">
          <span class="k">이륜차 · Two-wheeled</span>
          <span class="v"><span id="analyz-c-two">0</span></span>
        </div>
        <div class="analyz-counter-cell risk">
          <span class="k">위험 이벤트 · Risk</span>
          <span class="v"><span id="analyz-c-risk">0</span></span>
        </div>
      </div>
    </div>
  </section>

  <footer class="ready-foot">© 2026 DRIVINGASSIS · 분석 세션 {session_id}</footer>

</div>
"""


# Legacy stub — kept so existing imports keep resolving.
ANALYZING_HTML = ""


# ─── RESULTS — v4 cinematic finale ────────────────────────────
# Score becomes a sentence, key moments become evidence cards, annotated
# video sits below as proof. All in one self-contained .dc-v3-root blob —
# same pattern as Ready / Analyzing. The "또 다른 주행" custom button is
# bridged by JS to a hidden gr.Button.

def _score_comment(score) -> str:
    """One-line emotional comment shown next to the big score number.
    Bracket thresholds chosen so the user feels rewarded above 80 and
    challenged below 70 — the rough A/B/C/D bands of the existing scorer."""
    if not score:
        return ""
    s = score.total
    if s >= 90:
        return "정말 안정적이었어요"
    if s >= 80:
        return "대체로 안정적이었지만 아쉬운 순간이 있었어요"
    if s >= 70:
        return "몇 가지 주의할 점이 발견되었어요"
    return "개선이 필요한 구간이 많았어요"


def _category_tier(s: int) -> str:
    """Return the tier class for a category score — drives the bar color.
    Brackets match the visual / verbal language of _score_comment."""
    if s >= 85:
        return "tier-good"
    if s >= 70:
        return "tier-warn"
    return "tier-bad"


def _hero_sentence(score, events) -> tuple[str, str]:
    """Returns (hero_html, secondary_text) — 2-line natural language summary
    of the drive. The hero may contain a single <em> tag for the focus area."""
    if not score:
        return ("분석이 완료되었어요.", "결과를 정리하고 있어요.")

    overall = score.total
    focus = score.focus_area  # CategoryScore | None — the weakest category
    n_total = len(events) if events else 0
    n_risk    = sum(1 for e in (events or []) if e.severity == "danger")
    n_caution = sum(1 for e in (events or []) if e.severity == "caution")

    # ─ Hero sentence — voice changes with score bracket
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

    # ─ Secondary — what we found
    if n_total == 0:
        secondary = "큰 위험 없이 부드럽게 흘러갔어요."
    elif n_risk > 0:
        secondary = f"총 {n_total}건의 핵심 순간, 그 중 {n_risk}건이 위험 구간이었어요."
    elif n_caution > 0:
        secondary = f"총 {n_total}건의 핵심 순간, {n_caution}건이 주의가 필요했어요."
    else:
        secondary = f"총 {n_total}건의 핵심 순간이 있었어요."

    return (hero, secondary)


_SEVERITY_TO_BADGE = {
    "safe":    ("GOOD",   ""),
    "caution": ("REVIEW", "amber"),
    "danger":  ("RISK",   "risk"),
}


def _event_card_html(event, coaching, still_url: str, duration_s: float) -> str:
    """One key-moment card — still image + classification + headline +
    summary + a single line of VLM coaching."""
    badge_text, badge_cls = _SEVERITY_TO_BADGE.get(event.severity, ("EVENT", ""))
    tc = _fmt_duration(event.timestamp)
    coach_line = ""
    if coaching:
        # Action plan is the actionable take-away — use it as the coach line.
        coach_line = (coaching.action_plan or coaching.scene_analysis
                      or coaching.scene_description or "")
    img_el = (
        f'<img src="{still_url}" alt="{tc} {event.title}"/>'
        if still_url else
        '<div class="results-moment-fallback"></div>'
    )
    return f"""
    <article class="results-moment-card">
      <div class="results-moment-img">
        {img_el}
        <span class="results-moment-tc">{tc}</span>
        <span class="results-moment-badge {badge_cls}">{badge_text}</span>
      </div>
      <div class="results-moment-cat">{(event.category or '').upper()}</div>
      <h4>{event.title}</h4>
      <p>{event.summary}</p>
      {f'<div class="results-moment-coach"><b>코칭</b><span>{coach_line}</span></div>' if coach_line else ''}
    </article>
    """


def _timeline_markers_html(events, duration_s: float) -> str:
    """Build timeline DOM: a colored ±1-second band UNDER each event +
    the marker line above. Bands come first so markers sit on top."""
    if duration_s <= 0 or not events:
        return ""
    bands, markers = [], []
    for e in events:
        pct = max(0.0, min(100.0, (e.timestamp / duration_s) * 100))
        _, cls = _SEVERITY_TO_BADGE.get(e.severity, ("", ""))
        # ±1 second window — the moment "around" the event
        band_start = max(0.0, ((e.timestamp - 1) / duration_s) * 100)
        band_end   = min(100.0, ((e.timestamp + 1) / duration_s) * 100)
        band_w = max(0.0, band_end - band_start)
        bands.append(
            f'<div class="results-tl-band {cls}" '
            f'style="left:{band_start:.2f}%; width:{band_w:.2f}%"></div>'
        )
        label = f"{_fmt_duration(e.timestamp)} · {e.title}"
        markers.append(
            f'<div class="results-tl-marker {cls}" '
            f'style="left:{pct:.1f}%" data-l="{label}"></div>'
        )
    return "".join(bands) + "".join(markers)


def _ticks_html(duration_s: float, count: int = 3) -> str:
    if duration_s <= 0:
        return "<span>00:00</span>" * count
    parts = []
    for i in range(count):
        t = duration_s * (i / (count - 1))
        parts.append(f"<span>{_fmt_duration(t)}</span>")
    return "".join(parts)


def _category_bars_html(score) -> str:
    if not score or not score.categories:
        return ""
    rows = []
    for cat in score.categories:
        w = max(0, min(100, cat.score))
        tier = _category_tier(cat.score)
        rows.append(f"""
        <div class="results-cat-row {tier}">
          <span class="results-cat-name">{cat.name_ko}</span>
          <span class="results-cat-bar"><span class="results-cat-fill" style="width:{w}%"></span></span>
          <span class="results-cat-num">{cat.score}</span>
        </div>
        """)
    return "".join(rows)


def results_screen_html(
    video_path: str = "",
    filename: str = "",
    duration: float = 0.0,
    score=None,
    events=None,
    coachings=None,
    event_stills: dict | None = None,
    session_id: str = "—",
) -> str:
    """The cinematic RESULTS finale — one HTML blob in v4 tone.

    Sections, top to bottom:
      nav · stepper (all done) · hero sentence + score · timeline ·
      key-moment cards · annotated video · category breakdown · CTA · footer.
    """
    hero, secondary = _hero_sentence(score, events)
    score_comment = _score_comment(score)
    overall = score.total if score else 0
    grade = score.grade if score else "—"
    safe_name = filename or "주행 영상"
    events = events or []
    coachings = coachings or []
    event_stills = event_stills or {}
    vurl = _video_url(video_path)

    # Pair events with their coachings — assume same order
    moment_cards = ""
    for i, ev in enumerate(events[:3]):  # show up to 3 cards
        co = coachings[i] if i < len(coachings) else None
        still = event_stills.get(ev.frame_idx, "")
        still_url = _video_url(still) if still else ""
        moment_cards += _event_card_html(ev, co, still_url, duration)

    if not moment_cards:
        moment_cards = (
            '<div class="results-moments-empty">'
            '큰 이벤트 없이 부드럽게 흘러간 주행이었어요.'
            '</div>'
        )

    video_block = ""
    if vurl:
        video_block = f"""
        <section class="results-video-wrap">
          <div class="results-section-head">
            <span class="label label-signal">Annotated · 주석 영상</span>
            <h3>검출 결과를 영상 위에 직접 표시했어요.</h3>
          </div>
          <div class="results-video-frame">
            <video src="{vurl}" controls preload="metadata" playsinline></video>
            <span class="ready-br ready-br-tl"></span>
            <span class="ready-br ready-br-tr"></span>
            <span class="ready-br ready-br-bl"></span>
            <span class="ready-br ready-br-br"></span>
          </div>
        </section>
        """

    cat_bars = _category_bars_html(score)
    cat_section = ""
    if cat_bars:
        cat_section = f"""
        <section class="results-categories">
          <div class="results-section-head">
            <span class="label label-signal">Breakdown · 카테고리</span>
            <h3>5개 항목으로 본 오늘의 주행.</h3>
          </div>
          <div class="results-cat-grid">{cat_bars}</div>
        </section>
        """

    return f"""
<div class="dc-v3-root results-root">

  <nav class="ready-nav">
    <a class="brand" href="#dc-top" aria-label="DrivingAssis">
      <span class="brand-mark" aria-hidden="true">{_BRAND_SVG}</span>
      <span>DRIVING<span style="color:var(--signal)">ASSIS</span></span>
    </a>
    <div class="ready-nav-right">
      <span class="ready-session">SESSION · {session_id}</span>
    </div>
  </nav>

  <div class="ready-stepper-wrap">
    <div class="ready-stepper" role="list">
      <div class="ready-step done"><span class="num">01</span><span class="check">✓</span><span>업로드</span></div>
      <div class="ready-step done"><span class="num">02</span><span class="check">✓</span><span>검토</span></div>
      <div class="ready-step done"><span class="num">03</span><span class="check">✓</span><span>분석</span></div>
      <div class="ready-step current"><span class="num">04</span><span class="pulse"></span><span>리포트</span></div>
    </div>
  </div>

  <section class="results-hero">
    <div class="results-hero-left">
      <span class="label label-signal">Drive Report · {safe_name}</span>
      <h1 class="results-hero-sentence">{hero}</h1>
      <p class="results-hero-secondary">{secondary}</p>
    </div>
    <div class="results-hero-score">
      <div class="results-score-num">{overall}<span class="results-score-unit">/100</span></div>
      <div class="results-score-comment">{score_comment}</div>
      <div class="results-score-grade">GRADE · <b>{grade}</b></div>
    </div>
  </section>

  <section class="results-timeline-wrap">
    <div class="results-timeline-label">
      <h4>Timeline · 검출된 의사결정</h4>
      <div class="results-tl-ticks">{_ticks_html(duration)}</div>
    </div>
    <div class="results-tl">
      {_timeline_markers_html(events, duration)}
    </div>
  </section>

  <section class="results-moments-wrap">
    <div class="results-section-head">
      <span class="label label-signal">Key Moments · 핵심 순간</span>
      <h3>다시 봐야 할 순간과 한 줄 코칭.</h3>
    </div>
    <div class="results-moments-grid">
      {moment_cards}
    </div>
  </section>

  {video_block}

  {cat_section}

  <section class="results-cta">
    <button class="ready-btn-go" type="button" id="results-again-btn">
      또 다른 주행 분석하기 {_arrow_go_svg()}
    </button>
  </section>

  <footer class="ready-foot">© 2026 DRIVINGASSIS · 분석 세션 {session_id}</footer>

</div>
"""


# Legacy stub — kept so existing imports keep resolving.
RESULTS_HEADER_HTML = ""


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
        <div class="left">© 2026 DrivingAssis</div>
        <div class="right">
          <span>KR · KO</span>
          <a href="#">Status</a>
          <a href="#">Security</a>
        </div>
      </div>
    </div>
    """
