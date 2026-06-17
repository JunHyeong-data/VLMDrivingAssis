"""ANALYZING 화면(라이브 bbox + HUD + 대시캠)을 짧게 녹화해 README hero GIF 로.

    python app.py                          # 별도 터미널
    python scripts/record_demo_gif.py      # → docs/img/demo.webm (마지막 ~9초 = 분석 화면)

webm 의 '마지막 구간'이 분석 화면이므로 ffmpeg 의 -sseof 로 잘라 GIF 변환한다.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7865"
OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = {"width": 1280, "height": 720}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=SIZE,
            record_video_dir=str(OUT),
            record_video_size=SIZE,
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector(".dc-v3-root", timeout=30_000)

        page.eval_on_selector(".dc-sample-hit", "el => el.click()")
        page.wait_for_selector(".ready-root", timeout=60_000)
        page.wait_for_timeout(1500)

        page.eval_on_selector(".dc-ready-go-hit", "el => el.click()")
        page.wait_for_selector(".analyz-root", timeout=60_000)
        # 분석 화면 모션을 ~9초 캡처 (webm 의 마지막 구간이 된다)
        page.wait_for_timeout(9000)

        video_path = page.video.path()
        context.close()  # flush video
        browser.close()
        print(video_path)


if __name__ == "__main__":
    main()
