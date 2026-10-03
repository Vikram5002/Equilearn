"""Captures dashboard + Airflow screenshots for the evaluation deck.

Needs: dashboard on :8599 (streamlit run src/dashboard/app.py --server.port 8599)
       Airflow on :8080 (infra/airflow, user airflow / pass airflow)
Run:   python rsp/ppt/capture_screens.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screens"
DASH = "http://localhost:8599"
VIEW = {"width": 1600, "height": 1000}


def settle(page):
    page.wait_for_selector("[data-testid='stApp']", timeout=60000)
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=60000)
    page.wait_for_timeout(2000)
    # wait until every Plotly chart on the page has drawn its SVG
    page.wait_for_function(
        "() => [...document.querySelectorAll('.js-plotly-plot')]"
        ".every(el => el.querySelector('.main-svg'))", timeout=60000)
    page.wait_for_timeout(2500)


def dashboard(p):
    browser = p.chromium.launch()
    page = browser.new_page(viewport=VIEW, color_scheme="dark", device_scale_factor=1.5)
    for path, name in [("", "student"), ("cohort", "cohort"), ("market", "market"),
                       ("model", "model"), ("data", "data")]:
        page.goto(f"{DASH}/{path}")
        settle(page)
        page.screenshot(path=OUT / f"{name}.png")
        print("saved", name)

    page.goto(DASH)
    settle(page)
    page.get_by_role("tab", name="What-if simulator").click()
    page.wait_for_timeout(3500)
    page.get_by_role("tab", name="What-if simulator").scroll_into_view_if_needed()
    page.mouse.wheel(0, 650)
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / "simulator.png")
    print("saved simulator")
    browser.close()


def airflow(p):
    browser = p.chromium.launch()
    page = browser.new_page(viewport=VIEW, device_scale_factor=1.5)
    page.goto("http://localhost:8080/login/")
    page.fill("input[name=username]", "airflow")
    page.fill("input[name=password]", "airflow")
    page.click("input[type=submit], button[type=submit]")
    page.wait_for_load_state("networkidle")
    # graph view only colours tasks once a run is selected: click the latest run bar
    page.goto("http://localhost:8080/dags/skillbridge_pipeline/grid")
    page.wait_for_timeout(4000)
    page.locator("[data-testid='run']").last.click()
    page.wait_for_timeout(2000)
    page.get_by_role("tab", name="Graph").click()
    page.wait_for_timeout(5000)
    page.screenshot(path=OUT / "airflow.png")
    print("saved airflow")
    browser.close()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        dashboard(p)
        airflow(p)
