"""Capture remaining admin + student exam builder screenshots."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "manual_screenshots"
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1365, "height": 820}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print("saved", path.name, "url=", page.url)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)

        # Student login
        page.goto(f"{BASE}/login/", wait_until="networkidle")
        page.fill('input[name="username"]', "student")
        page.fill('input[name="password"]', "student123")
        page.click('button[type="submit"]')
        page.wait_for_timeout(1200)
        print("student url", page.url)

        page.goto(f"{BASE}/my-exams/", wait_until="networkidle")
        shot(page, "10_student_my_exams")

        # Create or open exam
        create_btn = page.locator('a[href*="create"]')
        if create_btn.count():
            create_btn.first.click()
            page.wait_for_timeout(1500)
        else:
            links = page.locator('a[href*="/my-exams/"]')
            for i in range(links.count()):
                href = links.nth(i).get_attribute("href") or ""
                if href.rstrip("/").split("/")[-1].isdigit():
                    links.nth(i).click()
                    page.wait_for_timeout(1500)
                    break
        shot(page, "11_student_exam_builder")

        # Try practice if available
        practice = page.locator('a[href*="practice"]')
        if practice.count():
            practice.first.click()
            page.wait_for_timeout(1200)
            shot(page, "11b_student_practice")

        page.goto(f"{BASE}/my-lists/", wait_until="networkidle")
        shot(page, "12_student_my_lists")

        page.goto(f"{BASE}/logout/", wait_until="networkidle")

        # Admin login
        page.goto(f"{BASE}/admin-panel/login/", wait_until="networkidle")
        shot(page, "13_admin_login")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_timeout(1500)
        print("admin url", page.url)
        # dump error if any
        if "login" in page.url:
            body = page.inner_text("body")
            print("admin login page text:", body[:400])

        pages = [
            ("14_admin_dashboard", "/admin-panel/dashboard/"),
            ("15_admin_categories", "/admin-panel/manage-categories/"),
            ("16_admin_courses", "/admin-panel/manage-courses/"),
            ("17_admin_resources", "/admin-panel/manage-resources/"),
            ("18_admin_upload_questions", "/admin-panel/csv-upload/"),
            ("19_admin_add_question", "/admin-panel/manual-question/"),
            ("20_admin_manage_questions", "/admin-panel/manage-questions/"),
            ("21_admin_exams", "/admin-panel/exams/"),
            ("23_admin_question_lists", "/admin-panel/question-lists/"),
            ("24_admin_blogs", "/admin-panel/manage-blogs/"),
        ]
        for name, path in pages:
            page.goto(f"{BASE}{path}", wait_until="networkidle")
            page.wait_for_timeout(400)
            shot(page, name)

        # Exam builder detail
        page.goto(f"{BASE}/admin-panel/exams/", wait_until="networkidle")
        links = page.locator('a[href*="/admin-panel/exams/"]')
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href") or ""
            tail = href.rstrip("/").split("/")[-1]
            if tail.isdigit():
                page.goto(f"{BASE}{href}", wait_until="networkidle")
                page.wait_for_timeout(800)
                shot(page, "22_admin_exam_builder")
                break
        else:
            # create one
            page.goto(f"{BASE}/admin-panel/exams/create/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            shot(page, "22_admin_exam_builder")

        browser.close()
        print("done")


if __name__ == "__main__":
    main()
