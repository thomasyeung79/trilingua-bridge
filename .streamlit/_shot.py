import sys

from playwright.sync_api import sync_playwright

URL = "http://localhost:8501/"
OUT = r"D:\PROJECT\practice\trilingua_product_upgrade\.streamlit\_demo_banner.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1400, "height": 1100})
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)

    try:
        page.wait_for_selector("text=Demo deployment", timeout=30000)
        print("banner found")
    except Exception as e:
        print(f"banner NOT found: {e}", file=sys.stderr)
        page.screenshot(path=OUT, full_page=False)
        print(f"diagnostic screenshot at {OUT}")
        sys.exit(2)

    page.wait_for_timeout(800)
    page.screenshot(path=OUT, full_page=False)
    print(f"screenshot saved: {OUT}")
    browser.close()
