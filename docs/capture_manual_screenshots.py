"""Capture UI screenshots for the Study Nation user manual."""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "manual_screenshots"
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1365, "height": 820}


def shot(page, name: str, full_page: bool = False):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    print("saved", path.name)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()

        # ----- Public / Student pages -----
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        shot(page, "01_home")

        page.goto(f"{BASE}/signup/", wait_until="networkidle")
        shot(page, "02_student_signup")

        page.goto(f"{BASE}/login/", wait_until="networkidle")
        shot(page, "03_student_login")

        page.goto(f"{BASE}/courses/", wait_until="networkidle")
        shot(page, "04_courses")

        page.goto(f"{BASE}/resources/", wait_until="networkidle")
        shot(page, "05_resources")

        page.goto(f"{BASE}/blogs/", wait_until="networkidle")
        shot(page, "06_blogs")

        page.goto(f"{BASE}/past-papers/", wait_until="networkidle")
        shot(page, "07_past_papers")

        page.goto(f"{BASE}/question-forum/", wait_until="networkidle")
        shot(page, "08_public_chat")

        page.goto(f"{BASE}/contact/", wait_until="networkidle")
        shot(page, "09_contact")

        # Student login (create temp if needed via form)
        page.goto(f"{BASE}/login/", wait_until="networkidle")
        # Try common demo credentials; if fail, still capture guest pages
        for username, password in [
            ("student", "student123"),
            ("demo", "demo1234"),
            ("test", "test1234"),
        ]:
            page.goto(f"{BASE}/login/", wait_until="networkidle")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(800)
            if "/my-exams" in page.url or "Welcome" in page.content():
                print("logged in as", username)
                break
        else:
            # Sign up a temporary student for screenshots
            uname = "manual_demo_student"
            page.goto(f"{BASE}/signup/", wait_until="networkidle")
            page.fill('input[name="full_name"]', "Manual Demo Student")
            page.fill('input[name="username"]', uname)
            page.fill('input[name="email"]', "manual.demo@example.com")
            page.fill('input[name="password"]', "DemoPass!234")
            page.click('button[type="submit"]')
            page.wait_for_timeout(1200)
            if "already" in page.content().lower() or page.url.endswith("/signup/"):
                page.goto(f"{BASE}/login/", wait_until="networkidle")
                page.fill('input[name="username"]', uname)
                page.fill('input[name="password"]', "DemoPass!234")
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)

        page.goto(f"{BASE}/my-exams/", wait_until="networkidle")
        shot(page, "10_student_my_exams")

        # Create exam if empty
        create = page.locator('a[href*="my-exams/create"], button:has-text("New"), a:has-text("Create")')
        if create.count():
            create.first.click()
            page.wait_for_timeout(1500)

        if "/my-exams/" in page.url and page.url.rstrip("/").count("/") >= 3:
            shot(page, "11_student_exam_builder")
        else:
            # open first exam if listed
            link = page.locator('a[href*="/my-exams/"]').filter(has_text="Edit").first
            if link.count() == 0:
                link = page.locator('a[href*="/my-exams/"]').first
            if link.count():
                link.click()
                page.wait_for_timeout(1200)
                shot(page, "11_student_exam_builder")

        page.goto(f"{BASE}/my-lists/", wait_until="networkidle")
        shot(page, "12_student_my_lists")

        # Logout student
        page.goto(f"{BASE}/logout/", wait_until="networkidle")

        # ----- Admin -----
        page.goto(f"{BASE}/admin-panel/login/", wait_until="networkidle")
        shot(page, "13_admin_login")

        logged_admin = False
        for username, password in [
            ("admin", "admin123"),
            ("admin", "Admin123!"),
            ("superadmin", "admin123"),
        ]:
            page.goto(f"{BASE}/admin-panel/login/", wait_until="networkidle")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(1000)
            if "dashboard" in page.url or "Dashboard" in page.content():
                logged_admin = True
                print("admin logged in as", username)
                break

        if logged_admin:
            page.goto(f"{BASE}/admin-panel/dashboard/", wait_until="networkidle")
            shot(page, "14_admin_dashboard")

            page.goto(f"{BASE}/admin-panel/manage-categories/", wait_until="networkidle")
            shot(page, "15_admin_categories")

            page.goto(f"{BASE}/admin-panel/manage-courses/", wait_until="networkidle")
            shot(page, "16_admin_courses")

            page.goto(f"{BASE}/admin-panel/manage-resources/", wait_until="networkidle")
            shot(page, "17_admin_resources")

            page.goto(f"{BASE}/admin-panel/csv-upload/", wait_until="networkidle")
            shot(page, "18_admin_upload_questions")

            page.goto(f"{BASE}/admin-panel/manual-question/", wait_until="networkidle")
            shot(page, "19_admin_add_question")

            page.goto(f"{BASE}/admin-panel/manage-questions/", wait_until="networkidle")
            shot(page, "20_admin_manage_questions")

            page.goto(f"{BASE}/admin-panel/exams/", wait_until="networkidle")
            shot(page, "21_admin_exams")

            # open first exam if any
            exam_link = page.locator('a[href*="/admin-panel/exams/"]').filter(has_not_text="create")
            if exam_link.count():
                # prefer edit links with numeric id
                for i in range(min(exam_link.count(), 8)):
                    href = exam_link.nth(i).get_attribute("href") or ""
                    if href.rstrip("/").split("/")[-1].isdigit():
                        exam_link.nth(i).click()
                        page.wait_for_timeout(1200)
                        shot(page, "22_admin_exam_builder")
                        break

            page.goto(f"{BASE}/admin-panel/question-lists/", wait_until="networkidle")
            shot(page, "23_admin_question_lists")

            page.goto(f"{BASE}/admin-panel/manage-blogs/", wait_until="networkidle")
            shot(page, "24_admin_blogs")
        else:
            print("WARNING: admin login failed — only public screenshots captured")

        browser.close()
        print("Done. Screenshots in", OUT)


if __name__ == "__main__":
    main()
