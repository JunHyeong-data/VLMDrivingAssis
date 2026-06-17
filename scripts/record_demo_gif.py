"""검토 → 라이브 분석 → 리포트(스크롤)까지 흐름을 ~13초 워크스루 GIF 로.

    python app.py                          # 별도 터미널
    python scripts/record_demo_gif.py      # → docs/img/results.gif

분석 단계가 실시간으로 ~30초 걸리므로, 전체를 연속 녹화하면서 각 화면이 보이기 시작한
시각을 기록해 두고 ffmpeg trim+concat 으로 필요한 구간만 잘라 이어붙인다.

playwright webm 은 시작부에 약간의 패딩이 붙어 monotonic 시각과 영상 시각 사이에
일정한 오프셋이 생긴다. 녹화 종료 시각 ↔ 영상 길이로 오프셋을 구해 모든 구간에 보정한다.
"""
import re
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7865"
OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = {"width": 1280, "height": 720}

# (구간 시작 보정초, 길이초) — 합 ≈ 12초
READY_PAD, READY_DUR = 0.4, 2.8
ANAL_PAD, ANAL_DUR = 0.8, 3.6
RES_PAD, RES_DUR = 0.4, 5.6
FPS, WIDTH = 11, 680


def _record():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=SIZE, record_video_dir=str(OUT), record_video_size=SIZE
        )
        t0 = time.monotonic()
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".dc-v3-root", timeout=30_000)

        # ── 검토 (Ready) ──
        page.eval_on_selector(".dc-sample-hit", "el => el.click()")
        page.wait_for_selector(".ready-root", timeout=60_000)
        t_ready = time.monotonic() - t0
        page.wait_for_timeout(int((READY_PAD + READY_DUR + 0.5) * 1000))

        # ── 라이브 분석 (Analyzing) ──
        page.eval_on_selector(".dc-ready-go-hit", "el => el.click()")
        page.wait_for_selector(".analyz-root", timeout=60_000)
        t_anal = time.monotonic() - t0

        # ── 리포트 (Results) — 영상 재생 + 천천히 스크롤 ──
        page.wait_for_selector(".results-root", timeout=180_000)
        t_res = time.monotonic() - t0
        page.wait_for_timeout(200)
        page.evaluate(
            """() => { const v = document.querySelector('.results-root video');
                       if (v) { v.muted = true; v.loop = true; v.currentTime = 0; v.play(); } }"""
        )
        # 상단(코칭+영상+점수) 잠깐 → 바닥(키 모먼트·카테고리)까지 단계 스크롤
        page.wait_for_timeout(1600)
        steps = 26
        for i in range(1, steps + 1):
            page.evaluate(
                f"() => window.scrollTo(0, document.body.scrollHeight * {i/steps})"
            )
            page.wait_for_timeout(150)
        page.wait_for_timeout(700)
        t_end = time.monotonic() - t0

        video_path = page.video.path()
        context.close()
        browser.close()
        return video_path, t_ready, t_anal, t_res, t_end


def _duration(ff, webm):
    """webm 길이(초)를 ffmpeg stderr 의 Duration 줄에서 파싱."""
    r = subprocess.run([ff, "-i", webm], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def _to_gif(webm, t_ready, t_anal, t_res, t_end):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    fps, w = FPS, WIDTH
    offset = _duration(ff, webm) - t_end  # 영상 시작 패딩 보정
    segs = [
        (t_ready + offset + READY_PAD, READY_DUR),
        (t_anal + offset + ANAL_PAD, ANAL_DUR),
        (t_res + offset + RES_PAD, RES_DUR),
    ]
    parts = "".join(
        f"[0:v]trim={s:.2f}:{s+d:.2f},setpts=PTS-STARTPTS[v{i}];"
        for i, (s, d) in enumerate(segs)
    )
    concat = "".join(f"[v{i}]" for i in range(len(segs)))
    walk = str(OUT / "_walk.mp4")
    subprocess.run(
        [ff, "-y", "-i", webm, "-filter_complex",
         f"{parts}{concat}concat=n={len(segs)}:v=1[w]", "-map", "[w]",
         "-r", str(fps), walk],
        check=True, capture_output=True,
    )
    palette = str(OUT / "_palette.png")
    out = str(OUT / "results.gif")
    vf = f"fps={fps},scale={w}:-1:flags=lanczos"
    subprocess.run([ff, "-y", "-i", walk, "-vf",
                    vf + ",palettegen=stats_mode=diff", "-update", "1", palette],
                   check=True, capture_output=True)
    subprocess.run([ff, "-y", "-i", walk, "-i", palette, "-lavfi",
                    vf + "[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3", out],
                   check=True, capture_output=True)
    for f in (palette, walk, webm):
        Path(f).unlink(missing_ok=True)
    print(out)


if __name__ == "__main__":
    path, tr, ta, tre, te = _record()
    print(f"ready={tr:.1f}s analyzing={ta:.1f}s results={tre:.1f}s end={te:.1f}s")
    _to_gif(path, tr, ta, tre, te)
