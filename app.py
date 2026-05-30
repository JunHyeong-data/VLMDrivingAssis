"""BackMirror — main Gradio app.

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
import time
import traceback
import uuid

import cv2
import gradio as gr

from core.detector import detect_video_stream
from core.event_extractor import extract_events
from core.history import delete_analysis, load_prior, load_recent, save_analysis
from core.overlay import render_annotated_video
from core.scorer import calculate_score
from core.video_utils import normalize_for_browser
from core.vlm import generate_coaching

from ui.screens import (
    analyzing_screen_html,
    error_results_html,
    faq_screen_html,
    history_screen_html,
    idle_hero_html,
    ready_screen_html,
    results_screen_html,
    team_screen_html,
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
    // RESULTS '← 기록' (HISTORY 드릴다운에서만 표시) → 기록 목록으로 복귀
    const resultsToHistory = document.getElementById('results-tohistory-btn');
    if (resultsToHistory && !resultsToHistory.__bound) {
      resultsToHistory.__bound = true;
      resultsToHistory.addEventListener('click', () => {
        document.querySelector('.dc-history-hit')?.click();
      });
    }

    // --- 3f. RESULTS timeline + moment cards → seek the annotated video ---
    // Any element with `data-tc` (timeline marker, label button, moment card)
    // becomes a seek target. Click → set video.currentTime + play. Also
    // updates the playhead position on timeupdate so the white tick rides
    // along with playback.
    const resultsVideo = document.getElementById('dc-results-video');
    const resultsTrack = document.getElementById('dc-results-track');
    if (resultsVideo && resultsTrack && !resultsTrack.__bound) {
      resultsTrack.__bound = true;
      const seekFromEl = (el) => {
        const tc = parseFloat(el.dataset.tc);
        if (!Number.isFinite(tc)) return;
        // 마커는 '그 순간'을 가리키므로 전체가 아니라 이벤트 구간만 재생한다:
        // 1.5초 앞(컨텍스트) ~ 3초 뒤. 구간 끝에서 자동 정지하고, 사용자가
        // 재생바를 직접 다시 누르면 일반 재생으로 돌아간다(핸들러가 1회성).
        const start = Math.max(0, tc - 1.5);
        const dur = resultsVideo.duration;
        const end = Number.isFinite(dur) ? Math.min(dur, tc + 3) : tc + 3;
        try {
          if (resultsVideo.__clipStop) {
            resultsVideo.removeEventListener('timeupdate', resultsVideo.__clipStop);
          }
          const stop = () => {
            if (resultsVideo.currentTime >= end) {
              resultsVideo.pause();
              resultsVideo.removeEventListener('timeupdate', stop);
              resultsVideo.__clipStop = null;
            }
          };
          resultsVideo.__clipStop = stop;
          resultsVideo.addEventListener('timeupdate', stop);
          resultsVideo.currentTime = start;
          resultsVideo.play().catch(() => {});
        } catch (e) { /* ignore */ }
        // visual feedback on labels
        document.querySelectorAll('.timeline-labels button').forEach(b =>
          b.classList.toggle('active', b === el)
        );
      };
      document.querySelectorAll(
        '.results-root [data-tc]'
      ).forEach(el => {
        if (el.__seekBound) return;
        el.__seekBound = true;
        el.addEventListener('click', e => {
          e.preventDefault();
          seekFromEl(el);
        });
      });

      // Playhead that rides with playback
      let ph = resultsTrack.querySelector('.playhead');
      if (!ph) {
        ph = document.createElement('span');
        ph.className = 'playhead';
        resultsTrack.appendChild(ph);
      }
      const updatePlayhead = () => {
        const dur = resultsVideo.duration || 0;
        if (dur > 0) {
          ph.style.left = (100 * resultsVideo.currentTime / dur) + '%';
        }
      };
      resultsVideo.addEventListener('timeupdate', updatePlayhead);
      resultsVideo.addEventListener('loadedmetadata', updatePlayhead);
    }

    // --- 3d. ANALYZING cancel button → reset to IDLE + cancel the run ---
    // The visible '분석 중단' button bridges to the hidden home button, which
    // both snaps the view back to IDLE and cancels the running run_analysis
    // generator (see home_btn.click cancels=[run_evt] server-side). A run
    // cancelled during analysis stops before save_analysis — no history row.
    const analyzCancel = document.getElementById('analyz-cancel-btn');
    if (analyzCancel && !analyzCancel.__bound) {
      analyzCancel.__bound = true;
      analyzCancel.addEventListener('click', () => {
        document.querySelector('.dc-home-hit')?.click();
      });
    }

    // --- 3e. HISTORY back button → reset to IDLE ---
    // The visible '← 홈' button in the history nav (and the history logo)
    // bridge to the hidden home button so there's always a way back.
    const historyBack = document.getElementById('history-back-btn');
    if (historyBack && !historyBack.__bound) {
      historyBack.__bound = true;
      historyBack.addEventListener('click', () => {
        document.querySelector('.dc-home-hit')?.click();
      });
    }

    // --- 3g. HISTORY node card → drill in (re-show past RESULTS) ---
    // Each .node-card carries data-session-id. Click anywhere on the card
    // (except on the × delete button) → fill hidden Textbox + click hidden
    // gr.Button → go_history_drilldown() server-side navigates to RESULTS
    // with that record's data.
    function fillTextboxAndClick(targetSelector, btnSelector, value) {
      const target = document.querySelector(
        targetSelector + ' textarea, ' + targetSelector + ' input'
      );
      if (!target) {
        console.warn('[DC] textbox not found:', targetSelector);
        return;
      }
      const proto = target.tagName === 'TEXTAREA'
        ? window.HTMLTextAreaElement.prototype
        : window.HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
      if (setter) setter.call(target, value);
      else target.value = value;
      target.dispatchEvent(new Event('input', { bubbles: true }));
      setTimeout(() => document.querySelector(btnSelector)?.click(), 40);
    }
    document.querySelectorAll('.node-card').forEach(card => {
      if (card.__bound) return;
      card.__bound = true;
      card.addEventListener('click', e => {
        // Don't fire when the user clicked the × delete button
        if (e.target.closest('.nc-del')) return;
        const sid = card.dataset.sessionId || '';
        if (!sid) return;
        fillTextboxAndClick(
          '#dc-history-drill-target',
          '.dc-history-drill-hit',
          sid
        );
      });
      // Keyboard activation (Enter / Space) since card has role="button"
      card.addEventListener('keydown', e => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        const sid = card.dataset.sessionId || '';
        if (!sid) return;
        fillTextboxAndClick(
          '#dc-history-drill-target',
          '.dc-history-drill-hit',
          sid
        );
      });
    });

    // --- 3e. HISTORY card × button → confirm + delete bridge ---
    // Each .nc-del (v6) or .history-card-del (legacy) carries data-session-id.
    // We confirm, fill the hidden Textbox (#dc-history-delete-target) with
    // that id, fire 'input' so Svelte picks it up, then click the hidden
    // gr.Button which calls go_history_delete() server-side. The handler
    // re-renders history_html so the card disappears in place.
    document.querySelectorAll('.history-card-del, .nc-del').forEach(btn => {
      if (btn.__bound) return;
      btn.__bound = true;
      btn.addEventListener('click', e => {
        e.stopPropagation();
        e.preventDefault();
        const sid = btn.dataset.sessionId || '';
        const nth = btn.dataset.nth || '';
        if (!sid) return;
        const label = nth && nth !== sid ? `#${nth} 분석` : '이 분석';
        if (!confirm(`${label}을 삭제할까요?\\n되돌릴 수 없습니다.`)) return;
        const target = document.querySelector(
          '#dc-history-delete-target textarea, ' +
          '#dc-history-delete-target input'
        );
        if (!target) {
          console.warn('[DC] delete target textbox not found');
          return;
        }
        const nativeSetter = Object.getOwnPropertyDescriptor(
          target.tagName === 'TEXTAREA'
            ? window.HTMLTextAreaElement.prototype
            : window.HTMLInputElement.prototype,
          'value'
        )?.set;
        if (nativeSetter) nativeSetter.call(target, sid);
        else target.value = sid;
        target.dispatchEvent(new Event('input', { bubbles: true }));
        // Give Svelte one tick to commit the value before clicking the btn
        setTimeout(() => {
          document.querySelector('.dc-history-delete-hit')?.click();
        }, 40);
      });
    });

    // --- 3c. HISTORY navigation bridges ---
    // The visible '기록' link in the IDLE nav → hidden gr.Button which calls
    // go_history() server-side. From the HISTORY page itself, the upload
    // CTA (both empty-state and bottom) sends the user back to IDLE so they
    // can drop a file into the v3 dropzone.
    const historyLink = document.getElementById('dc-history-link');
    if (historyLink && !historyLink.__bound) {
      historyLink.__bound = true;
      historyLink.addEventListener('click', e => {
        e.preventDefault();
        document.querySelector('.dc-history-hit')?.click();
      });
    }
    const historyUpload = document.getElementById('history-upload-btn');
    if (historyUpload && !historyUpload.__bound) {
      historyUpload.__bound = true;
      historyUpload.addEventListener('click', () => {
        // Return to IDLE — the dropzone lives there
        document.querySelector('.dc-home-hit')?.click();
      });
    }
    // '팀 소개' nav link → hidden dc-team-hit → go_team() server-side.
    const teamLink = document.getElementById('dc-team-link');
    if (teamLink && !teamLink.__bound) {
      teamLink.__bound = true;
      teamLink.addEventListener('click', e => {
        e.preventDefault();
        document.querySelector('.dc-team-hit')?.click();
      });
    }
    // TEAM '홈으로' button → reset to IDLE.
    const teamBack = document.getElementById('team-back-btn');
    if (teamBack && !teamBack.__bound) {
      teamBack.__bound = true;
      teamBack.addEventListener('click', () => {
        document.querySelector('.dc-home-hit')?.click();
      });
    }
    // '자주 묻는 질문' nav link → hidden dc-faq-hit → go_faq() server-side.
    const faqLink = document.getElementById('dc-faq-link');
    if (faqLink && !faqLink.__bound) {
      faqLink.__bound = true;
      faqLink.addEventListener('click', e => {
        e.preventDefault();
        document.querySelector('.dc-faq-hit')?.click();
      });
    }
    // FAQ '홈으로' button → reset to IDLE.
    const faqBack = document.getElementById('faq-back-btn');
    if (faqBack && !faqBack.__bound) {
      faqBack.__bound = true;
      faqBack.addEventListener('click', () => {
        document.querySelector('.dc-home-hit')?.click();
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

    // (ANALYZING progress is now rendered server-side by the run_analysis
    //  generator — no client-side animation. See app.run_analysis.)

    // --- 4. BRAND click → invisible home_btn → reset to IDLE ---
    // Covers every screen's logo variant (.brand on IDLE/Ready,
    // .analyz-brand / .results-brand / .history-brand on the others). On IDLE
    // the hero exists → we leave the anchor's scroll-to-top behavior; on any
    // other screen, clicking the logo resets to the first screen.
    const homeBtn = document.querySelector('.dc-home-hit');
    document.querySelectorAll(
      '.dc-v3-root .brand, .dc-v3-root .analyz-brand,'
      + ' .dc-v3-root .results-brand, .dc-v3-root .history-brand'
    ).forEach(brand => {
      if (brand.__bound) return;
      brand.__bound = true;
      brand.style.cursor = 'pointer';
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


def _extract_poster(video_path: str) -> str:
    """Write the first frame as a jpg in temp; return its absolute path.

    The ANALYZING screen shows this static poster (not an autoplaying clip)
    so that re-rendering the screen on every streaming progress update
    doesn't restart video playback. Returns "" if the frame can't be read.
    """
    if not video_path or not os.path.exists(video_path):
        return ""
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return ""
    out_path = os.path.join(
        tempfile.gettempdir(), f"dc_poster_{os.path.basename(video_path)}.jpg"
    )
    cv2.imwrite(out_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return out_path


# Brand colors in BGR (cv2 native order) for live bbox burn-in.
_BBOX_BGR_SIGNAL = (154, 229, 0)     # signal green
_BBOX_BGR_AMBER  = (71, 181, 255)    # amber
_LABEL_TEXT_DARK = (24, 34, 0)       # dark green for text on signal background
_LABEL_TEXT_AMBER_DARK = (0, 23, 42) # dark for text on amber background


def _draw_live_bboxes(frame, det) -> None:
    """Mutates `frame` in place: draws signal/amber bboxes + labels for the
    detections in `det`. Capped at 12 boxes so the frame never looks like
    graffiti. Used by _render_live_poster to give the analyzing screen its
    'system is actually looking at this frame' feel."""
    if not det or not det.detections:
        return
    for d in det.detections[:12]:
        x1, y1, x2, y2 = (int(v) for v in d.bbox)
        if (x2 - x1) < 4 or (y2 - y1) < 4:
            continue
        if d.cls in ("bike", "motor", "rider"):
            box_color, text_color = _BBOX_BGR_AMBER, _LABEL_TEXT_AMBER_DARK
        else:
            box_color, text_color = _BBOX_BGR_SIGNAL, _LABEL_TEXT_DARK
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        label = f"{d.cls.upper()} {d.confidence:.2f}"
        # Label background bar — width sized to text length, sitting above the bbox
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        bg_h = th + 6
        bg_y2 = max(0, y1)
        bg_y1 = max(0, y1 - bg_h)
        cv2.rectangle(frame, (x1, bg_y1), (x1 + tw + 8, bg_y2), box_color, -1)
        cv2.putText(frame, label, (x1 + 4, bg_y2 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1, cv2.LINE_AA)


def _render_live_poster(cap, fidx: int, det, slot_path: str) -> str:
    """Read frame `fidx` from an already-open cv2 capture, draw the current
    detections on it, write to `slot_path`. Returns the path on success, ""
    on failure. The caller rotates between two slot paths so the browser
    never serves a cached version."""
    if cap is None or not cap.isOpened():
        return ""
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ok, frame = cap.read()
    if not ok or frame is None:
        return ""
    _draw_live_bboxes(frame, det)
    try:
        cv2.imwrite(slot_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 78])
    except OSError:
        return ""
    return slot_path


# ─── State transitions ────────────────────────────────────────

def go_idle():
    """Return to IDLE — used by 'Analyze another video' / brand click."""
    return (
        gr.update(visible=True),       # idle_screen
        gr.update(visible=False),      # uploaded_screen
        gr.update(visible=False),      # analyzing_screen
        gr.update(visible=False),      # results_screen
        gr.update(visible=False),      # history_screen
        gr.update(visible=False),      # team_screen
        gr.update(visible=False),      # faq_screen
        gr.update(value=None),         # file_in (clear)
        None,                          # video_state
        ready_screen_html(),           # ready_html (reset)
    )


def go_history():
    """Any → HISTORY. Loads recent analyses fresh each time so the page
    reflects whatever was just saved by run_analysis."""
    records = load_recent(limit=20)
    return (
        gr.update(visible=False),      # idle_screen
        gr.update(visible=False),      # uploaded_screen
        gr.update(visible=False),      # analyzing_screen
        gr.update(visible=False),      # results_screen
        gr.update(visible=True),       # history_screen
        gr.update(visible=False),      # team_screen
        gr.update(visible=False),      # faq_screen
        history_screen_html(records=records),  # history_html
    )


def go_team():
    """Any → TEAM ('팀 소개'). Triggered by the '팀 소개' nav link in IDLE,
    bridged by DC_BOOT_JS to the hidden dc-team-hit button. The brand and
    #team-back-btn return to IDLE via dc-home-hit."""
    return (
        gr.update(visible=False),      # idle_screen
        gr.update(visible=False),      # uploaded_screen
        gr.update(visible=False),      # analyzing_screen
        gr.update(visible=False),      # results_screen
        gr.update(visible=False),      # history_screen
        gr.update(visible=True),       # team_screen
        gr.update(visible=False),      # faq_screen
        team_screen_html(),            # team_html
    )


def go_faq():
    """Any → FAQ ('자주 묻는 질문'). Triggered by the '자주 묻는 질문' nav link
    → hidden dc-faq-hit button. Brand and #faq-back-btn return to IDLE."""
    return (
        gr.update(visible=False),      # idle_screen
        gr.update(visible=False),      # uploaded_screen
        gr.update(visible=False),      # analyzing_screen
        gr.update(visible=False),      # results_screen
        gr.update(visible=False),      # history_screen
        gr.update(visible=False),      # team_screen
        gr.update(visible=True),       # faq_screen
        faq_screen_html(),             # faq_html
    )


def go_history_delete(target_session_id: str):
    """Delete the history record with the given session id, then re-render
    the HISTORY page in place. The target id comes from a hidden textbox
    that DC_BOOT_JS fills before triggering this. Stays on HISTORY screen
    (no visibility change) but refreshes the html so the card is gone."""
    delete_analysis((target_session_id or "").strip())
    records = load_recent(limit=20)
    return (
        history_screen_html(records=records),  # history_html
        "",                                    # clear delete_target textbox
    )


def go_history_drilldown(target_session_id: str):
    """HISTORY card click → re-show that past analysis as RESULTS.

    Looks up the record by session id, computes its prior (the analysis
    chronologically just before it), and re-renders results_screen_html
    with that data. Video path + event stills are empty (those temp files
    are long gone) — results_screen_html already handles that gracefully
    (no video block, fallback divs on cards). Stepper still shows all-done.
    """
    sid = (target_session_id or "").strip()
    records = load_recent(limit=99)
    target = next((r for r in records if r.session_id == sid), None)
    if target is None:
        # Record vanished (e.g. user deleted in another tab) — just re-render
        # HISTORY in place and don't navigate.
        return (
            gr.update(),                                # idle (no change)
            gr.update(),                                # uploaded
            gr.update(),                                # analyzing
            gr.update(),                                # results
            gr.update(),                                # history (stay)
            gr.update(),                                # team
            gr.update(),                                # faq
            history_screen_html(records=records),       # history_html refresh
            gr.update(),                                # results_html
            "",                                         # clear drill textbox
        )
    # Find prior: record immediately older (records is newest-first)
    idx = records.index(target)
    prior = records[idx + 1] if idx + 1 < len(records) else None

    html = results_screen_html(
        video_path="",                # annotated video file is long gone
        filename=target.video_name,
        duration=target.duration,
        score=target.score,
        events=target.events,
        coachings=target.coachings,
        event_stills={},              # event stills were temp jpgs, also gone
        session_id=target.session_id,
        prior=prior,
        from_history=True,            # show the '← 기록' back button in the nav
    )
    return (
        gr.update(visible=False),     # idle
        gr.update(visible=False),     # uploaded
        gr.update(visible=False),     # analyzing
        gr.update(visible=True),      # results ← navigate here
        gr.update(visible=False),     # history
        gr.update(visible=False),     # team
        gr.update(visible=False),     # faq
        gr.update(),                  # history_html (no change needed)
        html,                         # results_html ← past analysis
        "",                           # clear drill textbox
    )


def on_file_uploaded(file_obj, progress=gr.Progress()):
    """IDLE → UPLOADED. Normalize to browser-safe mp4 and build the Ready screen.

    Guards the demo against bad input: a file that can't be transcoded or
    opened (corrupt / unsupported codec) shows a gentle warning and stays on
    IDLE, instead of crashing or marching into a doomed analysis."""
    idle = (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),      # history_screen
        gr.update(visible=False),      # team_screen
        gr.update(visible=False),      # faq_screen
        None,                          # video_state (clear)
        ready_screen_html(),
    )
    if file_obj is None:
        return idle

    src = file_obj if isinstance(file_obj, str) else getattr(file_obj, "name", None)
    try:
        progress(0.3, desc="브라우저 호환 형식으로 변환 중…")
        normalized = normalize_for_browser(src) if src else None
    except Exception:
        normalized = None

    meta = _video_meta(normalized) if normalized else _video_meta("")
    # 열 수 없는 영상(손상·미지원 코덱)은 분석까지 가지 않고 여기서 우아하게 안내.
    # 오탐 방지: 해상도·길이가 '모두' 0일 때만 (부분 메타 누락은 통과시킨다).
    if not normalized or (meta["width"] == 0 and meta["height"] == 0 and meta["duration"] <= 0):
        gr.Warning("이 영상은 열 수 없어요. 다른 블랙박스 영상을 올려주세요.")
        return idle

    progress(1.0, desc="준비 완료")
    session_id = _new_session_id()

    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),                      # history_screen
        gr.update(visible=False),                      # team_screen
        gr.update(visible=False),                      # faq_screen
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
    """UPLOADED → ANALYZING. Shows the live screen at 0% and stashes session
    metadata (sid + poster frame + name) that run_analysis reuses on every
    streaming update, so the session id stays stable instead of flickering."""
    meta = _video_meta(video_path) if video_path else _video_meta("")
    sid = _new_session_id()
    poster = _extract_poster(video_path) if video_path else ""
    analyz_meta = {"sid": sid, "poster": poster, "name": meta["name"]}
    return (
        gr.update(visible=False),   # uploaded_screen
        gr.update(visible=True),    # analyzing_screen
        analyzing_screen_html(
            poster_path=poster,
            name=meta["name"],
            session_id=sid,
            phase="detect",
        ),                          # analyzing_html
        analyz_meta,                # analyz_state
    )


def go_results():
    """ANALYZING → RESULTS. Toggles visibility after pipeline completes."""
    return (
        gr.update(visible=False),   # analyzing_screen
        gr.update(visible=True),    # results_screen
    )


# ─── Analysis pipeline ────────────────────────────────────────

# Detection occupies 0–60% of the bar; the remaining phases map onto fixed
# marks past that, so the % only ever moves forward through real work.
_DETECT_PCT = 60

# events/vlm/score finish in milliseconds, so without a hold the stepper
# flashes 02→03→04 instantly after the long detection phase. This brief
# dwell lets each phase label stay readable. It is NOT fabricated progress —
# the real work runs during/right after each hold; we just pace the display.
_PHASE_DWELL = 0.45


def run_analysis(video_path: str, analyz_meta: dict | None = None):
    """Public entry — wraps the pipeline generator so a mid-analysis exception
    surfaces a graceful error screen instead of freezing the live ANALYZING
    screen during a demo. Streams the impl's yields through unchanged."""
    sid = (analyz_meta or {}).get("sid") or _new_session_id()
    try:
        yield from _run_analysis_impl(video_path, analyz_meta)
    except Exception:
        traceback.print_exc()
        yield (gr.update(), error_results_html(session_id=sid))


def _run_analysis_impl(video_path: str, analyz_meta: dict | None = None):
    """End-to-end pipeline as a GENERATOR that streams real progress.

    Each yield is `(analyzing_html_update, results_html_update)`. While the
    pipeline runs we update only the ANALYZING html with live, real numbers
    (frame counter, processing fps, per-class detection counts, pipeline
    phase). The final yield leaves ANALYZING untouched and fills RESULTS.

    Nothing here is faked — the bar reflects the detection generator's true
    position, and each phase label appears exactly when that work runs.
    """
    if not video_path:
        yield gr.update(), results_screen_html()
        return

    meta = analyz_meta or {}
    sid = meta.get("sid") or _new_session_id()
    poster = meta.get("poster", "")
    name = meta.get("name", "")

    # Two-slot rotation for the live-frame poster: alternating filenames
    # prevent the browser from serving a cached jpg when we overwrite.
    live_slots = [
        os.path.join(tempfile.gettempdir(), f"dc_live_{sid}_a.jpg"),
        os.path.join(tempfile.gettempdir(), f"dc_live_{sid}_b.jpg"),
    ]
    # Hold the video capture open across all live-poster reads so seek/read
    # cost is amortized (~6 reads total per video).
    live_cap = cv2.VideoCapture(video_path) if video_path else None

    def screen(**kw):
        return analyzing_screen_html(
            poster_path=kw.pop("poster_path", poster),
            name=name, session_id=sid, **kw,
        )

    # ── Phase 1: detection — streams real per-frame progress (0–60%) ──
    start = time.time()
    frames: list = []
    veh_cum = ped_cum = two_cum = 0  # cumulative across processed frames
    last_emit = -999
    live_version = 0
    current_poster = poster
    frame_w = frame_h = 0
    for fidx, total, det, frames in detect_video_stream(video_path, sample_every=2):
        # Track first known dimensions for the bbox SVG fallback
        if frame_w == 0 and det:
            frame_w, frame_h = det.width, det.height
        # Accumulate per-class detection counts. With no tracker, this is a
        # detection count (not unique-object count) — labels frame it as such.
        veh_cum += sum(1 for d in det.detections if d.cls in ("car", "truck", "bus"))
        ped_cum += sum(1 for d in det.detections if d.cls == "person")
        two_cum += sum(1 for d in det.detections if d.cls in ("bike", "motor", "rider"))
        n = len(frames)
        if n - last_emit >= 6:          # throttle: ~every 6 processed frames
            last_emit = n
            elapsed = max(1e-6, time.time() - start)
            proc_fps = n / elapsed
            pct = (fidx / total * _DETECT_PCT) if total else 0
            eta = int(elapsed * (100 - pct) / pct) if pct > 5 else 0
            # Burn the current frame + bboxes to the rotating slot so the
            # right-side video stage shows what the model is actually looking at.
            live_version += 1
            slot = live_slots[live_version % 2]
            new_poster = _render_live_poster(live_cap, fidx, det, slot)
            if new_poster:
                current_poster = new_poster
            yield (
                screen(pct=int(pct), frame_idx=fidx, total_frames=total,
                       proc_fps=proc_fps, eta_sec=eta,
                       veh=veh_cum, ped=ped_cum, two=two_cum,
                       risk=0, phase="detect",
                       poster_path=current_poster),
                gr.update(),
            )

    if live_cap is not None:
        live_cap.release()

    # ── Phase 2: event extraction ──
    yield (screen(pct=65, veh=veh_cum, ped=ped_cum, two=two_cum,
                  phase="events", poster_path=current_poster), gr.update())
    time.sleep(_PHASE_DWELL)  # keep "이벤트 추출" readable (work below is instant)
    events = extract_events(frames)
    n_risk = sum(1 for e in events if e.severity == "danger")

    # ── Phase 3: VLM coaching (event frames only) ──
    yield (screen(pct=72, veh=veh_cum, ped=ped_cum, two=two_cum, risk=n_risk,
                  phase="vlm", poster_path=current_poster), gr.update())
    time.sleep(_PHASE_DWELL)  # keep "코칭 작성" readable
    coachings = [generate_coaching(ev) for ev in events]

    # ── Phase 4a: score ──
    yield (screen(pct=80, veh=veh_cum, ped=ped_cum, two=two_cum, risk=n_risk,
                  phase="score", poster_path=current_poster), gr.update())
    time.sleep(_PHASE_DWELL)  # keep "점수 산정" readable
    score = calculate_score(events)

    # ── Phase 4b: annotated video + evidence stills ──
    # 95%: 인코딩이 가장 무거운 작업이라 그 직전에 "마무리 임박"으로 올려둔다.
    # (render_annotated_video 가 블로킹이라 인코딩 동안은 이 화면이 유지된다.)
    yield (screen(pct=95, veh=veh_cum, ped=ped_cum, two=two_cum, risk=n_risk,
                  phase="render", poster_path=current_poster), gr.update())
    det_by_idx = {f.frame_idx: f for f in frames}
    ev_by_idx = {ev.frame_idx: ev for ev in events}
    out_path = os.path.join(
        tempfile.gettempdir(),
        f"drivecoach_out_{os.path.basename(video_path)}.mp4",
    )
    annotated = render_annotated_video(video_path, out_path, det_by_idx, ev_by_idx)
    stills = _extract_event_stills(video_path, events)

    vmeta = _video_meta(video_path)

    # Load the previous analysis BEFORE saving the current one — otherwise
    # "prior" would be the just-finished run itself. Then persist this run
    # so the next analysis can compare against it.
    prior = load_prior()
    try:
        save_analysis(
            session_id=sid,
            video_name=vmeta["name"],
            duration=vmeta["duration"],
            score=score,
            events=events,
            coachings=coachings,
        )
    except OSError:
        pass  # history persistence is best-effort, never block the report

    # 인코딩까지 끝났으니 100% 를 잠깐 보여줘 95%→결과 점프 대신 완료감을 준다.
    yield (screen(pct=100, veh=veh_cum, ped=ped_cum, two=two_cum, risk=n_risk,
                  phase="render", poster_path=current_poster), gr.update())
    time.sleep(_PHASE_DWELL)

    # ── Done: fill the RESULTS screen (ANALYZING left as-is) ──
    yield (
        gr.update(),
        results_screen_html(
            video_path=annotated,
            filename=vmeta["name"],
            duration=vmeta["duration"],
            score=score,
            events=events,
            coachings=coachings,
            event_stills=stills,
            session_id=sid,
            prior=prior,
        ),
    )


# ─── UI assembly ──────────────────────────────────────────────

def build_app() -> gr.Blocks:
    # CRITICAL: inject the boot JS as a real <script> tag in <head>.
    # We do NOT rely solely on launch(js=...) because Gradio 6 sometimes
    # doesn't auto-invoke that function. A <script> tag is guaranteed to
    # execute as soon as the document loads.
    # favicon: 브라우저는 SVG 파비콘을 지원하지만 Gradio 의 favicon_path 는 SVG 를
    # 무시하므로, 사이드미러 로고를 <link> 로 직접 주입한다(assets 는 allowed_paths).
    head_html = (
        '<link rel="icon" type="image/svg+xml" href="/gradio_api/file=assets/favicon.svg">'
        f"<script>(function(){{ ({DC_BOOT_JS})(); }})();</script>"
    )
    with gr.Blocks(title="BackMirror", head=head_html) as app:
        # Invisible click targets bridged by DC_BOOT_JS. These MUST live at
        # the top level (not inside conditionally-visible Groups) because
        # Gradio 6 removes invisible-Group children from the DOM entirely,
        # so a button hidden via an enclosing group wouldn't exist to
        # receive .click() before the group's first reveal.
        # home_btn keeps its existing fixed-overlay positioning (see
        # .dc-home-hit CSS). history_btn lives in an always-mounted hidden
        # actions wrapper so it is in the DOM from boot but invisible.
        home_btn = gr.Button("home", elem_classes="dc-home-hit")
        with gr.Group(elem_classes="dc-hidden-actions"):
            history_btn = gr.Button("history", elem_classes="dc-history-hit")
            team_btn = gr.Button("team", elem_classes="dc-team-hit")
            faq_btn = gr.Button("faq", elem_classes="dc-faq-hit")
            # Carries the session_id JS just clicked × on. Read by go_history_delete.
            # Must be visible=True so Gradio actually mounts it — the enclosing
            # .dc-hidden-actions wrapper positions it off-screen anyway. With
            # visible=False the component never renders and elem_id is unused.
            history_delete_target = gr.Textbox(
                value="", visible=True, interactive=True,
                elem_id="dc-history-delete-target",
                label=None, container=False, show_label=False,
            )
            history_delete_btn = gr.Button(
                "history-delete", elem_classes="dc-history-delete-hit",
            )
            # Carries the session_id JS just clicked a node card on. Read
            # by go_history_drilldown to navigate HISTORY → RESULTS for
            # that record.
            history_drill_target = gr.Textbox(
                value="", visible=True, interactive=True,
                elem_id="dc-history-drill-target",
                label=None, container=False, show_label=False,
            )
            history_drill_btn = gr.Button(
                "history-drill", elem_classes="dc-history-drill-hit",
            )

        # State variable — currently unused (visibility drives everything),
        # but exposed in case we need to react to it from JS later.
        video_state = gr.State(None)
        # Carries {sid, poster, name} from go_analyzing into the run_analysis
        # generator so the live ANALYZING screen keeps a stable session id.
        analyz_state = gr.State(None)

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

        # ───── HISTORY — '내 주행 기록' page (5th state) ─────
        # Read-only view of past analyses, sparkline of score trend, and
        # the top-3 repeated event categories. Triggered by the visible
        # "기록" nav link in IDLE → top-level dc-history-hit button above.
        # The empty-state / bottom CTA bridges back to IDLE through dc-home-hit.
        with gr.Group(visible=False, elem_classes="dc-naked") as history_screen:
            history_html = gr.HTML(history_screen_html())

        # ───── TEAM — '팀 소개' page (6th state) ─────
        # Standalone team/project intro (hero → approach → members → Q&A).
        # "팀 소개" nav link in IDLE → top-level dc-team-hit button above.
        with gr.Group(visible=False, elem_classes="dc-naked") as team_screen:
            team_html = gr.HTML(team_screen_html())

        # ───── FAQ — '자주 묻는 질문' page (7th state) ─────
        with gr.Group(visible=False, elem_classes="dc-naked") as faq_screen:
            faq_html = gr.HTML(faq_screen_html())

        # ───── Wiring ───────────────────────────────────────
        # Both go_idle (reset) and on_file_uploaded (populate) share these
        # outputs: screen visibility + state + the single Ready HTML.
        screen_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            history_screen, team_screen, faq_screen,
            file_in, video_state, ready_html,
        ]
        upload_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            history_screen, team_screen, faq_screen,
            video_state, ready_html,
        ]
        history_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            history_screen, team_screen, faq_screen, history_html,
        ]
        team_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            history_screen, team_screen, faq_screen, team_html,
        ]
        faq_outputs = [
            idle_screen, uploaded_screen, analyzing_screen, results_screen,
            history_screen, team_screen, faq_screen, faq_html,
        ]

        # All transitions opt out of Gradio's built-in "processing | N.Ns"
        # status indicator that floats top-right; our own ANALYZING screen
        # carries the only progress UI the user should see. (Gradio 6 calls
        # this `show_progress="hidden"` per-listener.)

        # IDLE → UPLOADED
        file_in.upload(fn=on_file_uploaded, inputs=[file_in],
                       outputs=upload_outputs, show_progress="hidden")

        # UPLOADED → IDLE
        back_btn.click(fn=go_idle, outputs=screen_outputs,
                       show_progress="hidden")

        # UPLOADED → ANALYZING → RESULTS
        # run_evt 를 잡아두어 '분석 중단'(home_btn 으로 브릿지)이 이 제너레이터를
        # 실제로 취소할 수 있게 한다. (아래 home_btn.click 의 cancels 참고)
        analyze_evt = analyze_btn.click(
            fn=go_analyzing,
            inputs=[video_state],
            outputs=[uploaded_screen, analyzing_screen, analyzing_html, analyz_state],
            show_progress="hidden",
        )
        run_evt = analyze_evt.then(
            fn=run_analysis,
            inputs=[video_state, analyz_state],
            outputs=[analyzing_html, results_html],
            show_progress="hidden",
        )
        run_evt.then(
            fn=go_results,
            outputs=[analyzing_screen, results_screen],
            show_progress="hidden",
        )

        # RESULTS → IDLE
        new_analysis_btn.click(fn=go_idle, outputs=screen_outputs,
                               show_progress="hidden")

        # Any → HISTORY (triggered by visible "기록" link in IDLE nav,
        # bridged by DC_BOOT_JS to this hidden button)
        history_btn.click(fn=go_history, outputs=history_outputs,
                          show_progress="hidden")

        # Any → TEAM (triggered by visible "팀 소개" link → dc-team-hit)
        team_btn.click(fn=go_team, outputs=team_outputs,
                       show_progress="hidden")

        # Any → FAQ (triggered by visible "자주 묻는 질문" link → dc-faq-hit)
        faq_btn.click(fn=go_faq, outputs=faq_outputs,
                      show_progress="hidden")

        # × on a history card → delete that record + re-render the page.
        # DC_BOOT_JS sets the hidden Textbox value to the session_id, then
        # clicks this hidden button; we read the textbox and act.
        history_delete_btn.click(
            fn=go_history_delete,
            inputs=[history_delete_target],
            outputs=[history_html, history_delete_target],
            show_progress="hidden",
        )

        # Click on a node card → drill in to that past analysis (RESULTS).
        history_drill_btn.click(
            fn=go_history_drilldown,
            inputs=[history_drill_target],
            outputs=[
                idle_screen, uploaded_screen, analyzing_screen, results_screen,
                history_screen, team_screen, faq_screen,
                history_html, results_html, history_drill_target,
            ],
            show_progress="hidden",
        )

        # Header brand → IDLE (from any screen)
        # 분석 중 홈/중단으로 나가면 run_analysis 제너레이터를 실제로 취소한다
        # ('분석 중단'·brand·홈 모두 home_btn 으로 브릿지됨). 분석 도중 취소하면
        # generator 가 save_analysis 전에 멈춰, 그 분석은 HISTORY 에 남지 않는다.
        home_btn.click(fn=go_idle, outputs=screen_outputs,
                       show_progress="hidden", cancels=[run_evt])

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
