from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "manual_screenshots"
VIEWPORT = {"width": 1365, "height": 820}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved", name, page.url)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)

        page.goto(f"{BASE}/login/", wait_until="networkidle")
        page.fill("#id_username", "student")
        page.fill("#id_password", "StudentPass!234")
        page.click('button[type="submit"]')
        page.wait_for_timeout(1500)
        print("after login", page.url)

        page.goto(f"{BASE}/my-exams/", wait_until="networkidle")
        shot(page, "10_student_my_exams")

        # create exam
        page.goto(f"{BASE}/my-exams/create/", wait_until="networkidle")
        page.wait_for_timeout(1000)
        shot(page, "11_student_exam_builder")

        # practice if possible
        url = page.url
        if "/my-exams/" in url:
            # try practice link
            practice = page.locator('a[href*="practice"]')
            if practice.count():
                practice.first.click()
                page.wait_for_timeout(1200)
                shot(page, "11b_student_practice")

        page.goto(f"{BASE}/my-lists/", wait_until="networkidle")
        shot(page, "12_student_my_lists")

        page.goto(f"{BASE}/my-lists/create/", wait_until="networkidle")
        page.wait_for_timeout(800)
        shot(page, "12b_student_list_builder")

        page.goto(f"{BASE}/question-forum/", wait_until="networkidle")
        shot(page, "08_public_chat")

        browser.close()


if __name__ == "__main__":
    main()
