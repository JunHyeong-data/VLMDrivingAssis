"""RESULTS 화면(주석 영상 재생 + 점수 + 코칭)을 짧게 녹화해 README hero GIF 로.

    python app.py                          # 별도 터미널
    python scripts/record_demo_gif.py      # → docs/img/results.gif

결과 화면의 주석 영상은 autoplay 가 아니므로(컨트롤만), 녹화 중 JS 로 재생시킨다.
webm 의 '마지막 구간'이 결과 화면이므로 ffmpeg 의 -sseof 로 잘라 GIF 변환한다.
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7865"
OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = {"width": 1280, "height": 720}
CAPTURE_MS = 9000


def _record():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=SIZE, record_video_dir=str(OUT), record_video_size=SIZE
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".dc-v3-root", timeout=30_000)

        page.eval_on_selector(".dc-sample-hit", "el => el.click()")
        page.wait_for_selector(".ready-root", timeout=60_000)
        page.wait_for_timeout(1200)

        page.eval_on_selector(".dc-ready-go-hit", "el => el.click()")
        page.wait_for_selector(".results-root", timeout=180_000)
        page.wait_for_timeout(1500)

        # 주석 영상 강제 재생 (muted 로 autoplay 정책 회피)
        page.evaluate(
            """() => {
                const v = document.querySelector('.results-root video');
                if (v) { v.muted = true; v.currentTime = 0; v.loop = true; v.play(); }
            }"""
        )
        page.wait_for_timeout(CAPTURE_MS)

        video_path = page.video.path()
        context.close()
        browser.close()
        return video_path


def _to_gif(webm):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    palette = str(OUT / "_palette.png")
    out = str(OUT / "results.gif")
    vf = "fps=12,scale=760:-1:flags=lanczos"
    subprocess.run([ff, "-y", "-sseof", "-9", "-i", webm, "-vf",
                    vf + ",palettegen=stats_mode=diff", "-update", "1", palette],
                   check=True, capture_output=True)
    subprocess.run([ff, "-y", "-sseof", "-9", "-i", webm, "-i", palette, "-lavfi",
                    vf + "[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3", out],
                   check=True, capture_output=True)
    Path(palette).unlink(missing_ok=True)
    Path(webm).unlink(missing_ok=True)
    print(out)


if __name__ == "__main__":
    _to_gif(_record())
