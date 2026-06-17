"""README용 스크린샷 캡처. 이미 떠 있는 Gradio 서버(127.0.0.1:7865)에 붙어
4-state 화면을 docs/img/ 에 PNG 로 저장한다.

    python app.py                       # 별도 터미널에서 먼저 실행
    python scripts/capture_screens.py
"""
from pathlib import Path
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7865"
OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1440, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"  saved {path.relative_to(OUT.parent.parent)}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.goto(URL, wait_until="domcontentloaded")

        # --- IDLE landing -------------------------------------------------
        page.wait_for_selector(".dc-v3-root", timeout=30_000)
        page.wait_for_timeout(2500)  # hero video first frame
        shot(page, "01_idle")

        # --- UPLOADED (Ready) ---------------------------------------------
        page.eval_on_selector(".dc-sample-hit", "el => el.click()")
        page.wait_for_selector(".ready-root", timeout=60_000)
        page.wait_for_timeout(2500)  # transcode + video poster
        shot(page, "02_ready")

        # --- ANALYZING -----------------------------------------------------
        page.eval_on_selector(".dc-ready-go-hit", "el => el.click()")
        page.wait_for_selector(".analyz-root", timeout=60_000)
        page.wait_for_timeout(4000)  # let bboxes + progress advance
        shot(page, "03_analyzing")

        # --- RESULTS -------------------------------------------------------
        page.wait_for_selector(".results-root", timeout=120_000)
        page.wait_for_timeout(3000)  # annotated video + timeline render
        shot(page, "04_results")
        # 결과 하단(타임라인/키 모먼트)까지 한 장 더
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        shot(page, "05_results_detail")

        browser.close()
    print("done.")


if __name__ == "__main__":
    main()
