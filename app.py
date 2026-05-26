"""DriveCoach AI — main Gradio app.

The app is a 4-state machine:

    IDLE       File 업로드를 기다림. 큰 질문 + how-it-works.
       ↓ (file.upload)
    UPLOADED   영상 미리보기 + 분석 결과 preview cards + Analyze CTA.
       ↓ (analyze_btn.click)
    ANALYZING  살아있는 로더 + Gradio Progress + 인격적 메시지.
       ↓ (pipeline completes)
    RESULTS    점수 hero가 최상단. 그 아래 영상 + 코칭 + 통계.

Each state is its own gr.Group, visible-toggled by transition functions.
This makes every state feel like its own *experience*, not a hide/show.
"""
from __future__ import annotations

import os
import tempfile
import uuid

import cv2
import gradio as gr

from core.detector import detect_video
from core.event_extractor import extract_events
from core.overlay import render_annotated_video
from core.scorer import calculate_score
from core.video_utils import normalize_for_browser
from core.vlm import generate_coaching

from ui.screens import (
    analyzing_screen_html,
    idle_hero_html,
    ready_screen_html,
    results_screen_html,
)
from ui.theme import CUSTOM_CSS, build_theme


# ─── Boot JS — runs once after Gradio mounts the page ─────────
# Responsibilities (v3 — editorial / cinematic landing):
#   • Toggle .scrolled on the fixed nav when window.scrollY > 24
#   • Reveal hero title lines (slide up from below) on load
#   • IntersectionObserver fade-up for [data-reveal] elements
#   • Count-up animation for [data-count] numbers on reveal
#   • Bridge the visible v3 .dz dropzone to the hidden gr.File
#   • Brand click → invisible home_btn (reset to IDLE)
DC_BOOT_JS = """
() => {
  console.log('[DC] boot script attached');

  // ─── ANALYZING-screen demo animation ───
  // Plays a 12-second timeline that loops: progress, live bboxes, counters,
  // pipeline steps. Cleaned up — no preview cards, no toasts, no scan beam.
  // The four main signals (title rotation, progress bar, counters ramping,
  // live bboxes) tell the story; everything else was noise.
  // Triggered by bootDC() when .analyz-root first becomes visible.
  function startAnalyzAnim(root) {
    const $ = (id) => root.querySelector('#' + id);
    const TOTAL_FRAMES = 300;
    const DURATION_MS = 12000;
    // easeOutQuart — fast start, smooth settle (feels more "alive" than linear)
    const ease = (x) => 1 - Math.pow(1 - x, 4);

    // 5 keyframes of bbox positions for the live overlay
    const bboxFrames = [
      [
        { x:720,  y:430, w:200, h:130, label:'VEHICLE · ID#04 · 0.97', cls:'' },
        { x:1100, y:500, w:260, h:160, label:'VEHICLE · ID#07 · 0.93', cls:'' },
        { x:760,  y:410, w:80,  h:56,  label:'VEHICLE · ID#12 · FAR · 0.81', cls:'amber' },
      ],
      [
        { x:700,  y:440, w:215, h:135, label:'VEHICLE · ID#04 · 0.96', cls:'' },
        { x:1130, y:510, w:260, h:160, label:'VEHICLE · ID#07 · 0.94', cls:'' },
        { x:760,  y:415, w:80,  h:56,  label:'VEHICLE · ID#12 · 0.83', cls:'amber' },
        { x:540,  y:580, w:70,  h:70,  label:'TWO-WHEELED · ID#15 · 0.88', cls:'amber' },
      ],
      [
        { x:690,  y:446, w:224, h:142, label:'VEHICLE · ID#04 · 0.95', cls:'' },
        { x:1150, y:514, w:264, h:164, label:'VEHICLE · ID#07 · 0.94', cls:'' },
        { x:520,  y:575, w:80,  h:76,  label:'TWO-WHEELED · ID#15 · 0.90', cls:'amber' },
        { x:950,  y:600, w:60,  h:80,  label:'PEDESTRIAN · ID#21 · 0.84', cls:'' },
      ],
      [
        { x:680,  y:450, w:232, h:148, label:'VEHICLE · ID#04 · 0.96', cls:'' },
        { x:1170, y:520, w:268, h:168, label:'VEHICLE · ID#07 · 0.92', cls:'' },
        { x:500,  y:568, w:92,  h:84,  label:'TWO-WHEELED · ID#15 · CLOSE', cls:'risk' },
        { x:940,  y:595, w:64,  h:86,  label:'PEDESTRIAN · ID#21 · 0.86', cls:'' },
      ],
      [
        { x:668,  y:458, w:244, h:152, label:'VEHICLE · ID#04 · 0.97', cls:'' },
        { x:1200, y:528, w:270, h:170, label:'VEHICLE · ID#07 · 0.95', cls:'' },
        { x:480,  y:560, w:102, h:90,  label:'TWO-WHEELED · ID#15 · RISK', cls:'risk' },
      ],
    ];
    const overlay = $('analyz-overlay');
    const NS = 'http://www.w3.org/2000/svg';
    function drawFrame(idx) {
      if (!overlay) return;
      overlay.innerHTML = '';
      bboxFrames[idx % bboxFrames.length].forEach((b, i) => {
        const r = document.createElementNS(NS,'rect');
        r.setAttribute('class','analyz-bbox' + (b.cls ? ' ' + b.cls : ''));
        r.setAttribute('x', b.x); r.setAttribute('y', b.y);
        r.setAttribute('width', b.w); r.setAttribute('height', b.h);
        r.style.animationDelay = (i*40) + 'ms';
        overlay.appendChild(r);
        const t = document.createElementNS(NS,'text');
        t.setAttribute('class','analyz-tag' + (b.cls ? ' ' + b.cls : ''));
        t.setAttribute('x', b.x); t.setAttribute('y', b.y - 6);
        t.textContent = b.label;
        t.style.animationDelay = ((i*40) + 80) + 'ms';
        overlay.appendChild(t);
      });
    }

    const titleStages = [
      { until: 0.25, text: '읽고 있습니다.' },
      { until: 0.65, text: '추적하고 있습니다.' },
      { until: 0.90, text: '패턴을 분석합니다.' },
      { until: 1.00, text: '코칭을 작성합니다.' },
      { until: 99,   text: '거의 완성됐어요.' },
    ];
    const accent = $('analyz-title-accent');
    if (accent) {
      accent.style.transition = 'opacity .55s ease, transform .55s ease';
      accent.style.display = 'inline-block';
    }
    function updateTitle(p) {
      const stage = titleStages.find(s => p < s.until) || titleStages.at(-1);
      if (accent && accent.dataset.cur !== stage.text) {
        accent.style.opacity = '0';
        accent.style.transform = 'translateY(6px)';
        setTimeout(() => {
          accent.textContent = stage.text;
          accent.style.opacity = '1';
          accent.style.transform = 'translateY(0)';
          accent.dataset.cur = stage.text;
        }, 280);
      }
    }

    const plSteps = [$('analyz-pl0'), $('analyz-pl1'), $('analyz-pl2'), $('analyz-pl3')];
    function setPl(idx, state, text) {
      const el = plSteps[idx];
      if (!el) return;
      el.className = 'analyz-pl-step ' + state;
      const s = el.querySelector('.analyz-pl-status');
      if (state === 'current') s.innerHTML = '<span class="analyz-pulse-dot"></span>진행 중';
      else if (state === 'done') s.textContent = text || '완료';
      else s.textContent = '대기';
    }
    function updatePipeline(p) {
      if (p < 0.18)       { setPl(0,'current'); setPl(1,'pending'); setPl(2,'pending'); setPl(3,'pending'); }
      else if (p < 0.68)  { setPl(0,'done','완료 · 4.8s'); setPl(1,'current'); setPl(2,'pending'); setPl(3,'pending'); }
      else if (p < 0.92)  { setPl(0,'done','완료 · 4.8s'); setPl(1,'done','완료 · 14.6s'); setPl(2,'current'); setPl(3,'pending'); }
      else if (p < 1)     { setPl(0,'done','완료 · 4.8s'); setPl(1,'done','완료 · 14.6s'); setPl(2,'done','완료 · 7.9s'); setPl(3,'current'); }
      else                { setPl(0,'done','완료 · 4.8s'); setPl(1,'done','완료 · 14.6s'); setPl(2,'done','완료 · 7.9s'); setPl(3,'done','완료 · 2.1s'); }
    }

    let startT = performance.now();
    let lastBbox = 0, bboxIdx = 0;
    function tick(now) {
      // If the screen got hidden / removed, stop
      if (!root.isConnected || root.offsetParent === null) {
        root.__animated = false;
        return;
      }
      let elapsed = now - startT;
      if (elapsed > DURATION_MS + 1500) {
        // Loop while we wait for Gradio to swap to RESULTS
        startT = now; elapsed = 0; bboxIdx = 0; lastBbox = 0;
      }
      const t  = Math.min(1, elapsed / DURATION_MS);  // raw linear progress
      const p  = ease(t);                              // eased for display
      const pct = Math.min(100, Math.floor(p*100));
      const fr  = Math.min(TOTAL_FRAMES, Math.floor(p*TOTAL_FRAMES));

      const setText = (id, v) => { const e = $(id); if (e) e.textContent = v; };
      setText('analyz-pct', pct);
      const fill = $('analyz-fill'); if (fill) fill.style.width = pct + '%';
      const etaSec = Math.max(0, Math.ceil((1 - t) * 12));
      setText('analyz-eta', etaSec > 0 ? '약 ' + etaSec + '초' : '마무리');
      setText('analyz-frame', fr + ' / ' + TOTAL_FRAMES);
      setText('analyz-fps', (28 + Math.sin(elapsed/420)*2).toFixed(0));

      // Counters ramp up smoothly via the eased progress
      const veh  = Math.min(18, Math.round(p * 18));
      const ped  = Math.round(p * 6);
      const two  = Math.round(p * 4);
      const risk = t < 0.4 ? 0 : Math.round((t - 0.4) * 5);
      setText('analyz-c-veh', veh);
      setText('analyz-c-ped', ped);
      setText('analyz-c-two', two);
      setText('analyz-c-risk', risk);
      const det = $('analyz-hud-det');
      if (det) det.innerHTML = 'DET <span style="color:var(--signal)">' + (veh+ped+two) + '</span>';
      setText('analyz-hud-tc', (t*10).toFixed(2).padStart(5,'0') + 's');
      setText('analyz-hud-frame', 'FRAME ' + fr + ' / ' + TOTAL_FRAMES);
      setText('analyz-sub', '지금 ' + fr + '번째 프레임 · 차량 ' + veh + '개 추적 중');

      updateTitle(t);
      updatePipeline(t);

      if (now - lastBbox > 750) { drawFrame(bboxIdx++); lastBbox = now; }
      requestAnimationFrame(tick);
    }
    drawFrame(0);
    requestAnimationFrame(tick);
  }

  function bootDC() {
    // --- 1. NAV scrolled state ---
    const nav = document.getElementById('dc-nav');
    if (nav && !nav.__bound) {
      nav.__bound = true;
      const onScroll = () =>
        nav.classList.toggle('scrolled', window.scrollY > 24);
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }

    // --- 2. HERO title line reveal ---
    const heroTitle = document.getElementById('dc-heroTitle');
    if (heroTitle && !heroTitle.__revealed) {
      heroTitle.__revealed = true;
      const lines = heroTitle.querySelectorAll('.line');
      lines.forEach((l, i) =>
        setTimeout(() => l.classList.add('in'), 220 + i * 240));
    }

    // --- 3. IntersectionObserver fade-up + count-up ---
    function runCountUp(el) {
      const targets = el.matches('[data-count]')
        ? [el]
        : Array.from(el.querySelectorAll('[data-count]'));
      targets.forEach(t => {
        if (t.__counted) return;
        t.__counted = true;
        const goal = parseFloat(t.dataset.count);
        const start = performance.now();
        const dur = 1200;
        const ease = (x) => 1 - Math.pow(1 - x, 3);
        const tick = (now) => {
          const p = Math.min(1, (now - start) / dur);
          const v = Math.round(goal * ease(p));
          const first = t.firstChild;
          if (first && first.nodeType === 3) first.nodeValue = v;
          else t.insertBefore(document.createTextNode(v), t.firstChild);
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }
    if (!window.__dcReveal) {
      window.__dcReveal = new IntersectionObserver((entries) => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            e.target.classList.add('in');
            runCountUp(e.target);
            window.__dcReveal.unobserve(e.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    }
    document.querySelectorAll('.dc-v3-root [data-reveal]:not(.in)').forEach(el => {
      window.__dcReveal.observe(el);
    });

    // --- 3b. READY screen buttons → hidden gr.Buttons ---
    // The v4 Ready (UPLOADED) screen renders custom <button>s inside its
    // HTML blob. We bridge their clicks to the hidden gr.Button instances
    // (.dc-ready-back-hit / .dc-ready-go-hit) so Gradio still drives the
    // state machine.
    const readyBack = document.getElementById('ready-back-btn');
    if (readyBack && !readyBack.__bound) {
      readyBack.__bound = true;
      readyBack.addEventListener('click', () => {
        document.querySelector('.dc-ready-back-hit')?.click();
      });
    }
    const readyGo = document.getElementById('ready-go-btn');
    if (readyGo && !readyGo.__bound) {
      readyGo.__bound = true;
      readyGo.addEventListener('click', () => {
        document.querySelector('.dc-ready-go-hit')?.click();
      });
    }
    // RESULTS "또 다른 주행 분석하기" → hidden home button (back to IDLE)
    const resultsAgain = document.getElementById('results-again-btn');
    if (resultsAgain && !resultsAgain.__bound) {
      resultsAgain.__bound = true;
      resultsAgain.addEventListener('click', () => {
        document.querySelector('.dc-results-again-hit')?.click();
      });
    }
    // Enter while the Ready screen is visible → start analysis
    if (!window.__readyEnterBound) {
      window.__readyEnterBound = true;
      document.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const ready = document.querySelector('.ready-root');
        if (ready && ready.offsetParent !== null) {
          // Skip if the user is typing in a field
          const t = e.target;
          if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' ||
                    t.isContentEditable)) return;
          e.preventDefault();
          document.querySelector('.dc-ready-go-hit')?.click();
        }
      });
    }

    // --- 3c. ANALYZING screen demo animation ---
    // The v4 Analyzing layout has counters / progress / live bboxes / pipeline
    // steps / preview cards that all animate over ~30s. The real analysis
    // runs in Python and may finish before or after that — we just loop
    // the animation until Gradio swaps to the RESULTS screen.
    const analyzRoot = document.querySelector('.analyz-root');
    if (analyzRoot && !analyzRoot.__animated && analyzRoot.offsetParent !== null) {
      analyzRoot.__animated = true;
      startAnalyzAnim(analyzRoot);
    }

    // --- 4. BRAND click → invisible home_btn → reset to IDLE ---
    const homeBtn = document.querySelector('.dc-home-hit');
    document.querySelectorAll('.dc-v3-root .brand').forEach(brand => {
      if (brand.__bound) return;
      brand.__bound = true;
      brand.addEventListener('click', e => {
        const idleVisible = document.querySelector('.dc-v3-root .hero');
        if (!idleVisible && homeBtn) {
          e.preventDefault();
          homeBtn.click();
        }
      });
    });

    // --- 5. UPLOAD bridge → hidden gr.File (multiple triggers) ---
    // Try a few selectors because Gradio 6 may not always expose a bare
    // <input type=file>. We fall back to any clickable element inside the
    // hidden wrapper.
    function findHiddenUploader() {
      return (
        document.querySelector('.dc-hidden-uploader input[type=file]') ||
        document.querySelector('.dc-hidden-uploader input') ||
        document.querySelector('.dc-hidden-uploader button')
      );
    }
    function triggerUpload() {
      const target = findHiddenUploader();
      if (target) {
        target.click();
      } else {
        console.warn('[DC] hidden uploader not found');
      }
    }

    // 5a + 5b. Any anchor pointing at #dc-upload (top-nav CTA, hero CTA,
    // closing CTA section) → smooth-scroll the upload section into view.
    // The user then drops/picks the file at the actual dropzone, which
    // gives them context (section copy + format bullets) before the file
    // dialog opens.
    // Manual rAF-based smooth scroll — Chromium's behavior:'smooth' is
    // disabled in some embedded contexts (headless preview, certain
    // accessibility modes). Animating ourselves works everywhere.
    function smoothScrollTo(targetY, duration) {
      const startY = window.scrollY
                  || document.documentElement.scrollTop || 0;
      const delta  = targetY - startY;
      if (Math.abs(delta) < 4) { window.scrollTo(0, targetY); return; }
      const startT = performance.now();
      const ease = (t) => 1 - Math.pow(1 - t, 3);  // ease-out cubic
      function step(now) {
        const p = Math.min(1, (now - startT) / duration);
        window.scrollTo(0, startY + delta * ease(p));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    function scrollToUpload() {
      const target = document.getElementById('dc-upload');
      if (!target) { triggerUpload(); return; }  // fallback if section missing
      const rect    = target.getBoundingClientRect();
      const current = window.scrollY
                   || document.documentElement.scrollTop || 0;
      const targetY = Math.max(0, rect.top + current - 60); // leave nav room
      smoothScrollTo(targetY, 600);
      // Nudge attention to the dropzone briefly once scroll lands
      setTimeout(() => {
        const dz = document.getElementById('dc-dropzone');
        if (dz) {
          dz.classList.add('dz-flash');
          setTimeout(() => dz.classList.remove('dz-flash'), 1200);
        }
      }, 700);
    }
    document.querySelectorAll('.dc-v3-root .nav .btn-primary,'
                             + ' .dc-v3-root a[href="#dc-upload"]').forEach(el => {
      if (el.__upbound) return;
      el.__upbound = true;
      el.addEventListener('click', e => {
        e.preventDefault();
        scrollToUpload();
      });
    });

    // 5c. The dropzone itself + its inner "파일 선택하기" pseudo-button
    const dz = document.getElementById('dc-dropzone');
    if (dz && !dz.__bridged) {
      dz.__bridged = true;
      const setMeta = (name, size) => {
        const t = document.getElementById('dc-dz-title');
        const m = document.getElementById('dc-dz-meta');
        if (t && name) t.textContent = '분석 준비 중 — ' + name;
        if (m && size != null) {
          let s = size, u = ['B','KB','MB','GB'], i = 0;
          while (s >= 1024 && i < u.length - 1) { s /= 1024; i++; }
          m.textContent = s.toFixed(1) + ' ' + u[i] + ' · 업로드 중';
        }
      };
      dz.addEventListener('click', e => { e.preventDefault(); triggerUpload(); });
      dz.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault(); triggerUpload();
        }
      });
      ['dragenter', 'dragover'].forEach(ev =>
        dz.addEventListener(ev, e => {
          e.preventDefault(); dz.classList.add('drag');
        })
      );
      dz.addEventListener('dragleave', e => {
        e.preventDefault(); dz.classList.remove('drag');
      });
      dz.addEventListener('drop', e => {
        e.preventDefault();
        dz.classList.remove('drag');
        const files = e.dataTransfer && e.dataTransfer.files;
        const hiddenInput =
          document.querySelector('.dc-hidden-uploader input[type=file]');
        if (files && files.length && hiddenInput) {
          try {
            const dt = new DataTransfer();
            dt.items.add(files[0]);
            hiddenInput.files = dt.files;
            hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            setMeta(files[0].name, files[0].size);
          } catch (err) {
            console.warn('[DC] Drop bridge failed:', err);
          }
        }
      });
      // Reflect filename back into the dropzone UI when user picks via dialog
      const hiddenInput =
        document.querySelector('.dc-hidden-uploader input[type=file]');
      if (hiddenInput) {
        hiddenInput.addEventListener('change', e => {
          const f = e.target.files && e.target.files[0];
          if (f) setMeta(f.name, f.size);
        });
      }
    }
  }

  // Run on mount + after every Gradio state change (re-rendered DOM).
  bootDC();
  setTimeout(bootDC, 600);
  setTimeout(bootDC, 1800);
  const mo = new MutationObserver(() => bootDC());
  mo.observe(document.body, { childList: true, subtree: true });
}
"""


# ─── Helpers ───────────────────────────────────────────────────

def _empty_html(msg: str) -> str:
    return f'<div class="dc-empty"><div class="big">🚗</div><div class="msg">{msg}</div></div>'


def _video_meta(path: str) -> dict:
    """Returns a dict of metadata for the v4 Ready screen.

    Keys: name, duration, width, height, fps, codec, size_bytes.
    Missing values become 0 / '' so the UI shows '—' downstream.
    """
    if not path or not os.path.exists(path):
        return {"name": "", "duration": 0.0, "width": 0, "height": 0,
                "fps": 0.0, "codec": "—", "size_bytes": 0}
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    cap.release()
    codec = "".join(chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)).strip()
    if not codec or not codec.isprintable():
        codec = "—"
    name = os.path.basename(path)
    if name.startswith("dc_norm_"):
        name = name[len("dc_norm_"):]
    try:
        size_bytes = os.path.getsize(path)
    except OSError:
        size_bytes = 0
    duration = (frames / fps) if fps > 0 else 0.0
    return {
        "name": name, "duration": duration,
        "width": width, "height": height, "fps": fps,
        "codec": codec, "size_bytes": size_bytes,
    }


def _new_session_id() -> str:
    return uuid.uuid4().hex[:6].upper()


def _extract_event_stills(video_path: str, events) -> dict[int, str]:
    """For each event, grab the raw frame at event.frame_idx and write a jpg
    to tmp. Returns {frame_idx: absolute_path}. Used by the RESULTS screen
    to fill in the key-moment cards. Falls back silently if cv2 can't seek."""
    out: dict[int, str] = {}
    if not video_path or not os.path.exists(video_path) or not events:
        return out
    tmp = tempfile.gettempdir()
    cap = cv2.VideoCapture(video_path)
    try:
        for ev in events[:3]:  # we only ever show 3 cards
            cap.set(cv2.CAP_PROP_POS_FRAMES, ev.frame_idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            out_path = os.path.join(tmp, f"dc_event_{ev.frame_idx}.jpg")
            cv2.imwrite(out_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            out[ev.frame_idx] = out_path
    finally:
        cap.release()
    return out


# ─── State transitions ────────────────────────────────────────

def go_idle():
    """Return to IDLE — used by 'Analyze another video' / brand click."""
    return (
        gr.update(visible=True),       # idle_screen
        gr.update(visible=False),      # uploaded_screen
        gr.update(visible=False),      # analyzing_screen
        gr.update(visible=False),      # results_screen
        gr.update(value=None),         # file_in (clear)
        None,                          # video_state
        ready_screen_html(),           # ready_html (reset)
    )


def on_file_uploaded(file_obj, progress=gr.Progress()):
    """IDLE → UPLOADED. Normalize to browser-safe mp4 and build the Ready screen."""
    if file_obj is None:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            None,
            ready_screen_html(),
        )

    src = file_obj if isinstance(file_obj, str) else getattr(file_obj, "name", None)
    progress(0.3, desc="브라우저 호환 형식으로 변환 중…")
    normalized = normalize_for_browser(src) if src else None
    progress(1.0, desc="준비 완료")

    meta = _video_meta(normalized) if normalized else _video_meta("")
    session_id = _new_session_id()

    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        normalized,                                    # video_state
        ready_screen_html(
            video_path=normalized or "",
            name=meta["name"],
            duration=meta["duration"],
            width=meta["width"],
            height=meta["height"],
            fps=meta["fps"],
            codec=meta["codec"],
            size_bytes=meta["size_bytes"],
            session_id=session_id,
        ),
    )


def go_analyzing(video_path):
    """UPLOADED → ANALYZING. Toggles visibility AND populates the live
    analysis screen with the current video's name + a fresh session id."""
    meta = _video_meta(video_path) if video_path else _video_meta("")
    sid = _new_session_id()
    return (
        gr.update(visible=False),   # uploaded_screen
        gr.update(visible=True),    # analyzing_screen
        analyzing_screen_html(
            video_path=video_path or "",
            name=meta["name"],
            session_id=sid,
        ),                          # analyzing_html
    )


def go_results():
    """ANALYZING → RESULTS. Toggles visibility after pipeline completes."""
    return (
        gr.update(visible=False),   # analyzing_screen
        gr.update(visible=True),    # results_screen
    )


# ─── Analysis pipeline ────────────────────────────────────────

def _progress_msg(phase: str, detail: str = "") -> str:
    """Toss-style narrative progress copy."""
    base = {
        "detect":   "🚗  도로 위 객체를 찾고 있어요",
        "events":   "✨  의미 있는 순간을 골라내는 중이에요",
        "vlm":      "💬  VLM이 위험 상황을 분석하고 있어요",
        "score":    "📊  운전 점수를 계산하고 있어요",
        "render":   "🎬  주석 영상을 만드는 중이에요",
        "done":     "✅  분석이 끝났어요",
    }[phase]
    return f"{base}{f' · {detail}' if detail else ''}"


def run_analysis(video_path: str, progress=gr.Progress()):
    """End-to-end pipeline. Returns the single RESULTS HTML blob."""
    if not video_path:
        return results_screen_html()

    # Phase 1 — detection
    progress(0.05, desc=_progress_msg("detect"))
    frames = detect_video(
        video_path,
        sample_every=2,
        progress=lambda p, msg: progress(0.05 + p * 0.55,
                                          desc=_progress_msg("detect", msg)),
    )

    # Phase 2 — events
    progress(0.65, desc=_progress_msg("events"))
    events = extract_events(frames)

    # Phase 3 — VLM coaching (event frames only)
    progress(0.72, desc=_progress_msg("vlm", f"{len(events)}건"))
    coachings = [generate_coaching(ev) for ev in events]

    # Phase 4a — score
    progress(0.80, desc=_progress_msg("score"))
    score = calculate_score(events)

    # Phase 4b — annotated video
    progress(0.85, desc=_progress_msg("render"))
    det_by_idx = {f.frame_idx: f for f in frames}
    ev_by_idx = {ev.frame_idx: ev for ev in events}
    out_path = os.path.join(
        tempfile.gettempdir(),
        f"drivecoach_out_{os.path.basename(video_path)}.mp4",
    )
    annotated = render_annotated_video(video_path, out_path, det_by_idx, ev_by_idx)

    # Phase 4c — pull one still per event for the key-moment cards
    progress(0.92, desc=_progress_msg("render", "evidence frames"))
    stills = _extract_event_stills(video_path, events)

    meta = _video_meta(video_path)
    progress(1.0, desc=_progress_msg("done"))

    return results_screen_html(
        video_path=annotated,
        filename=meta["name"],
        duration=meta["duration"],
        score=score,
        events=events,
        coachings=coachings,
        event_stills=stills,
        session_id=_new_session_id(),
    )


# ─── UI assembly ──────────────────────────────────────────────

def build_app() -> gr.Blocks:
    # CRITICAL: inject the boot JS as a real <script> tag in <head>.
    # We do NOT rely solely on launch(js=...) because Gradio 6 sometimes
    # doesn't auto-invoke that function. A <script> tag is guaranteed to
    # execute as soon as the document loads.
    head_html = f"<script>(function(){{ ({DC_BOOT_JS})(); }})();</script>"
    with gr.Blocks(title="DrivingAssis AI", head=head_html) as app:
        # Invisible click target that the JS bridge calls when the brand
        # is clicked from any non-IDLE screen (resets to IDLE).
        home_btn = gr.Button("home", elem_classes="dc-home-hit")

        # State variable — currently unused (visibility drives everything),
        # but exposed in case we need to react to it from JS later.
        video_state = gr.State(None)

        # ───── IDLE — Runway-style landing page ─────────────
        # elem_classes="dc-naked" strips Gradio's gr.Group chrome
        # (background, padding, border, overflow) so the v2 hero's
        # 100vw breakout can actually escape — without this the group's
        # rounded corners + overflow:hidden clipped everything.
        with gr.Group(visible=True, elem_classes="dc-naked") as idle_screen:
            gr.HTML(idle_hero_html())
            with gr.Group(elem_classes="dc-hidden-uploader"):
                file_in = gr.File(
                    label="주행 영상 업로드",
                    file_types=["video"],
                    file_count="single",
                    height=120,
                )

        # ───── UPLOADED — v4 "Ready" layout (single HTML blob) ─────
        # Everything is rendered as one self-contained .dc-v3-root div, the
        # same pattern IDLE uses. The native <video> tag inside the HTML
        # plays directly via /gradio_api/file=<path>. The two action buttons
        # are <button>s in the HTML; their clicks are bridged to the hidden
        # gr.Button instances below by DC_BOOT_JS.
        with gr.Group(visible=False, elem_classes="dc-naked") as uploaded_screen:
            ready_html = gr.HTML(ready_screen_html())
            with gr.Group(elem_classes="dc-hidden-actions"):
                back_btn = gr.Button("back", elem_classes="dc-ready-back-hit")
                analyze_btn = gr.Button("analyze", elem_classes="dc-ready-go-hit")

        # ───── ANALYZING — v4 live-analysis screen (single HTML blob) ─
        with gr.Group(visible=False, elem_classes="dc-naked") as analyzing_screen:
            analyzing_html = gr.HTML(analyzing_screen_html())

        # ───── RESULTS — v4 cinematic finale (single HTML blob) ─────
        # All chrome (nav, stepper, hero sentence, key moments, video,
        # categories, CTA, footer) is rendered in ONE gr.HTML. The visible
        # "또 다른 주행 분석하기" button is in the HTML; its click is bridged
        # by JS to the hidden gr.Button below.
        with gr.Group(visible=False, elem_classes="dc-naked") as results_screen:
            results_html = gr.HTML(results_screen_html())
            with gr.Group(elem_classes="dc-hidden-actions"):
                new_analysis_btn = gr.Button(
                    "again", elem_classes="dc-results-again-hit",
                )

        # ───── Wiring ───────────────────────────────────────
        # Both go_idle (reset) and on_file_uploaded (populate) share these
        # outputs: screen visibility + state + the single Ready HTML.
        screen_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            file_in, video_state, ready_html,
        ]
        upload_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            video_state, ready_html,
        ]

        # IDLE → UPLOADED
        file_in.upload(fn=on_file_uploaded, inputs=[file_in],
                       outputs=upload_outputs)

        # UPLOADED → IDLE
        back_btn.click(fn=go_idle, outputs=screen_outputs)

        # UPLOADED → ANALYZING → RESULTS
        analyze_btn.click(
            fn=go_analyzing,
            inputs=[video_state],
            outputs=[uploaded_screen, analyzing_screen, analyzing_html],
        ).then(
            fn=run_analysis,
            inputs=[video_state],
            outputs=[results_html],
        ).then(
            fn=go_results,
            outputs=[analyzing_screen, results_screen],
        )

        # RESULTS → IDLE
        new_analysis_btn.click(fn=go_idle, outputs=screen_outputs)

        # Header brand → IDLE (from any screen)
        home_btn.click(fn=go_idle, outputs=screen_outputs)

    return app


if __name__ == "__main__":
    app = build_app()
    # The Ready (UPLOADED) screen embeds the user's uploaded clip via a
    # plain <video src="/gradio_api/file=…"/> tag. normalize_for_browser
    # writes the transcoded mp4 to tempfile.gettempdir(), so that directory
    # must be in allowed_paths for the URL to resolve.
    _assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    _tmp_dir = tempfile.gettempdir()
    app.launch(
        server_name="127.0.0.1",
        server_port=7865,
        show_error=True,
        inbrowser=False,
        theme=build_theme(),
        css=CUSTOM_CSS,
        js=DC_BOOT_JS,
        allowed_paths=[_assets_dir, _tmp_dir],
    )
