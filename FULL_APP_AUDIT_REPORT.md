# Full Application Audit Report

**Project:** Study Nation (Django web app)  
**Scope:** Frontend (templates/JS) + Backend (views, models, API, admin panel, settings)  
**Date:** 2026-07-27  
**Mode:** Read-only review — **no application code was changed** for this audit  
**Django system check:** `manage.py check` reported **0 issues**

---

## Executive Summary

The application is a feature-rich learning platform (courses, blogs, resources, exam builder, public chat, admin panel, REST API). Core features work at a structural level, but several **security and authorization issues** are serious enough that the app is **not production-safe** in its current configuration.

| Severity | Count (approx.) |
|----------|------------------|
| Critical | 6 |
| High | 8 |
| Medium | 10 |
| Low / Improvements | 8 |

---

## 1. Critical Issues

### 1.1 Admin panel privilege escalation (student can manage site content)

**Where:** `admin_panel/views.py` — many views use only `@login_required`, not `admin_required` / `admin_profile` checks.

**Verified in testing:** A normal student account received **HTTP 200** on:

- `/admin-panel/manage-blogs/`
- `/admin-panel/manage-courses/`
- `/admin-panel/manage-categories/`
- `/admin-panel/manage-resources/`
- `/admin-panel/exams/`
- `/admin-panel/question-lists/`

And could trigger **admin exam creation** via `/admin-panel/exams/create/` (redirect into builder).

Views that **do** check `admin_profile` (safer subset): dashboard, CSV upload, manual question, manage questions, question wizard endpoints.

**Impact:** Any logged-in student who knows admin URLs can create/edit/delete blogs, courses, categories, resources, exams, and question lists.

**Recommendation:** Apply `admin_required` (or equivalent staff/admin check) to **every** admin-panel view, including create/edit/delete and AJAX endpoints. Prefer a middleware or decorator used consistently.

---

### 1.2 Public API leaks correct answers and solutions

**Where:** `api/serializers.py` → `QuestionSerializer` includes `correct_answer` and `explanation`.  
`api/views.py` → `QuestionViewSet` / `QuestionBankViewSet` are unauthenticated `ReadOnlyModelViewSet`s (DRF default allow any).

**Verified:** Unauthenticated `GET /api/questions/` returns `correct_answer` for questions.

**Impact:** Anyone can harvest the full question bank with answers, defeating exams/practice integrity and leaking paid/private content.

**Recommendation:**

- Remove `correct_answer` / `explanation` from public serializers (or split public vs staff serializers).
- Require authentication + permissions for sensitive endpoints.
- Never nest full answer keys inside course detail serializers for anonymous clients.

---

### 1.3 Hardcoded Django `SECRET_KEY` in source

**Where:** `config/settings.py`

```python
SECRET_KEY = "django-insecure-+dxv3hg%z8=xn%2x=6ol3jw6%p-s7b#+s^3c!)23s5vmvbuz-5"
```

**Impact:** Session forgery, signed-cookie attacks, CSRF token prediction risk if key is public (repo/deploy artifacts).

**Recommendation:** Load from environment (`os.environ["SECRET_KEY"]`); never commit real keys.

---

### 1.4 `DEBUG = True` for deployment-oriented settings

**Where:** `config/settings.py`

**Impact:** Detailed error pages leak paths, settings, stack traces, and query data to end users.

**Recommendation:** `DEBUG` only from env; force `False` in production.

---

### 1.5 Open redirect after student login

**Where:** `courses/views.py` → `student_login`

```python
next_url = request.GET.get("next") or "courses:student_exams"
return redirect(next_url)
```

**Verified:** Login with `?next=https://evil.example/` redirects to `https://evil.example/`.

**Impact:** Phishing via trusted domain login flow.

**Recommendation:** Allow only relative paths on same host (`url_has_allowed_host_and_scheme`).

---

### 1.6 Destructive actions allowed via GET (CSRF bypass)

**Where (examples):**

- `student_delete_exam` — no `@require_POST`; **verified:** `GET /my-exams/<id>/delete/` deleted the exam.
- Admin `delete_blog`, `delete_course`, `delete_category`, `delete_resource`, `delete_exam`, `delete_question_list` — same pattern (GET-capable deletes).

**Impact:** CSRF: an image/link can trigger deletes for a logged-in victim. Accidental deletes via prefetch/bookmarks.

**Recommendation:** `@require_POST` (or form POST + CSRF) for all create/update/delete mutations.

---

## 2. High Issues

### 2.1 CORS allows all origins

**Where:** `config/settings.py` → `CORS_ALLOW_ALL_ORIGINS = True`

**Impact:** Browser-based cross-origin clients can call the API freely (worsens API answer leak).

**Recommendation:** Restrict to known frontend origins.

---

### 2.2 XSS risk: question content rendered with `|safe`

**Where (examples):**

- `courses/templates/courses/course_detail.html` — `question_text|safe`, options `|safe`, `explanation|safe`
- Admin/student preview JS uses `innerHTML` with rich/HTML question content

**Impact:** Stored XSS if malicious HTML is imported or entered as question text (Word/CSV/admin wizard). Can steal sessions of admins/students viewing courses or builders.

**Note:** Public Chat uses `chat_math` which **escapes** HTML (safer path).

**Recommendation:** Escape by default; allow only a sanitized subset of tags if HTML is required (e.g. bleach). Avoid `|safe` on untrusted fields.

---

### 2.3 Default / documented weak admin password

**Where:** `create_admin_user.py`, docs (`ADMIN_PANEL_GUIDE.md`, etc.) promote `admin123`.

**Impact:** If scripts/docs are followed in production without rotation, trivial account takeover.

**Recommendation:** Force strong password on first setup; never ship default credentials.

---

### 2.4 Student password policy weaker than Django validators

**Where:** `StudentSignupForm` uses `min_length=6` only; does not run full `AUTH_PASSWORD_VALIDATORS` on signup.

**Impact:** Weak student passwords.

**Recommendation:** Use `validate_password()` from Django auth validators.

---

### 2.5 Media files only served when `DEBUG=True`

**Where:** `config/urls.py` → `static(MEDIA_URL...)` only if `DEBUG`.

**Impact:** In production (`DEBUG=False`), uploaded images/PDFs/videos may 404 unless nginx/S3 is configured (not present in app settings).

**Recommendation:** Document and configure production media serving (object storage or reverse proxy).

---

### 2.6 WhiteNoise disabled; static production path incomplete

**Where:** `config/settings.py` — `WhiteNoiseMiddleware` commented out; `whitenoise` is in `requirements.txt`.

**Impact:** Gunicorn Docker deploy may not serve static assets correctly without extra config.

**Recommendation:** Enable WhiteNoise + compressed storage, or serve static via CDN/nginx.

---

### 2.7 Paid resources still listed via API without access control

**Where:** `ResourceViewSet` returns all resources including `is_paid` + `file` URLs with no auth/payment gate.

**Impact:** “Paid” content is effectively free if file URL is known.

**Recommendation:** Gate paid file downloads; hide file URL until entitlement is proven.

---

### 2.8 Contact form is a frontend-only fake

**Where:** `courses/templates/courses/contact.html` — JS `preventDefault`, shows success message, **does not send data to backend**.

**Impact:** Users believe messages were received; support loses inquiries; misleading UX.

**Recommendation:** Real backend endpoint + email/ticket storage, or remove “submit” claim.

---

## 3. Medium Issues

### 3.1 Duplicate URL for Resources

**Where:** `courses/urls.py`

```python
path("resources/", ResourcesView.as_view(), name="resources"),
...
path("resources/", ResourcesListView.as_view(), name="resources_list"),
```

**Impact:** Second route never handles the path (first match wins). `resources_list.html` template is effectively dead for `/resources/`. Confusing maintenance.

---

### 3.2 `ALLOWED_HOSTS` conflict / production domain overwritten

**Where:** `config/settings.py` sets production domains then overwrites:

```python
ALLOWED_HOSTS = ["studynation.com", "www.studynation.com"]
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
```

**Impact:** Production domain would reject requests unless this is fixed before deploy. Also blocks Django test client host `testserver` without config.

---

### 3.3 SQLite used with production Docker/Postgres intent

**Where:** Active DB is SQLite; Postgres/`dj-database-url` is commented. Docker installs `postgresql-client` but app may still use SQLite file.

**Impact:** Concurrency limits, file durability issues on ephemeral containers, multi-instance data loss.

---

### 3.4 No automated tests

**Where:** `tests.py` files empty / no real `test_*` coverage found.

**Impact:** Regressions (auth, grading, imports) ship unnoticed.

---

### 3.5 Admin decorator defined but largely unused

**Where:** `admin_required` exists in `admin_panel/views.py` but most views re-check inconsistently or not at all.

**Impact:** Same as 1.1 — inconsistent security model.

---

### 3.6 Discussion posts: no rate limiting / content size limits on body

**Where:** `DiscussionPost.content` / `DiscussionReply.content` are unlimited `TextField`s; no rate limit.

**Impact:** Spam, storage abuse, large payload DoS.

---

### 3.7 Image uploads (chat, blogs, resources) — limited validation

**Where:** Models use `ImageField`/`FileField` with little MIME/content scanning; extension-only checks in some forms.

**Impact:** Malicious uploads (polyglot files), large files, wrong types renamed as images.

---

### 3.8 Practice timer depends on client-supplied `started_at`

**Where:** `student_practice_submit` trusts POST `started_at`.

**Impact:** Students can fake short/long time taken; metrics unreliable (scoring still uses answers).

---

### 3.9 Free-text auto-grading is approximate

**Where:** `_grade_answer` for structured/matching uses case-insensitive exact string match.

**Impact:** Correct answers marked wrong (spacing/formatting); not a security issue, but UX/grading quality issue.

---

### 3.10 Dockerfile runs `collectstatic` at build without ensuring production settings

**Where:** `Dockerfile` — `collectstatic` during image build; no migrate at runtime; SQLite file may not match volume.

**Impact:** Deploy footguns (missing migrate, empty media volume, wrong static settings).

---

## 4. Low Issues / Code Quality

| # | Issue | Notes |
|---|--------|------|
| 4.1 | Shared session for student + admin on same User model | OK if roles gated strictly; currently not |
| 4.2 | Broad `except Exception` in parsers/import | Hides root causes; harder ops debugging |
| 4.3 | N+1 risk on some list pages | e.g. topic aggregation loops over querysets |
| 4.4 | `resources_list` / dead templates | Cleanup after fixing URL map |
| 4.5 | No CSRF for GET deletes | Covered under critical/high |
| 4.6 | Docs still say Learning Hub / old passwords | Operational confusion |
| 4.7 | `InlineMediaMiddleware` Office block is partial | Depends on `Sec-Fetch-Dest`; not full DRM |
| 4.8 | No logging/monitoring config | Harder to detect abuse in production |

---

## 5. Frontend-Specific Notes

### Strengths

- Clear page structure: home, courses, blogs, resources, past papers, public chat, student exam builder.
- Public Chat uses math sanitization + escaped rendering (`chat_math`).
- Many admin forms include `{% csrf_token %}` for normal POSTs.
- AJAX exam toggle/reorder generally sends CSRF token in admin templates.

### Issues

| Area | Finding |
|------|---------|
| Contact page | Fake success; no server integration |
| Course detail | XSS via `|safe` on questions |
| Resources routing | Dual `/resources/` registration; list template orphaned |
| Client-side preview | Heavy `innerHTML` usage — safe only if server data is trusted |
| Responsive/UX | Large inline CSS in templates — maintainability risk (not a functional bug) |
| Auth UX | Student vs admin are separate login ULs; students can still hit admin URLs if logged in |

---

## 6. Backend-Specific Notes

### Strengths

- Ownership checks on **student** exams/lists (`created_by=request.user`) are generally solid.
- Public chat create/reply requires login; reply edit/delete checks author.
- CSV/Word import has extension + size validation.
- Exam practice flow creates attempt records and grades answers.
- Django `manage.py check` is clean.

### Issues

| Area | Finding |
|------|---------|
| Authorization | Admin panel incomplete (Critical 1.1) |
| API | Open + answer leak (Critical 1.2) |
| Config | Secret, DEBUG, CORS, hosts (Critical/High) |
| Mutations | GET deletes (Critical 1.6) |
| Authn | Open redirect (Critical 1.5) |
| Data | SQLite vs production intent |

---

## 7. What Was Explicitly Tested

| Test | Result |
|------|--------|
| `manage.py check` | Pass (0 issues) |
| Student access to admin blog/course/category/resource/exam/list pages | **200 (unauthorized access)** |
| Student access to admin dashboard / manage-questions / csv-upload | 302 to login (profile check present) |
| Unauthenticated API questions include `correct_answer` | **Yes** |
| Login open redirect to external URL | **Yes** |
| GET delete student exam | **Yes, deleted** |

---

## 8. Recommended Fix Priority

### P0 — before any public/production deploy

1. Enforce `admin_required` on **all** admin-panel endpoints.  
2. Stop exposing `correct_answer` / solutions on public API.  
3. Move `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, DB, CORS to environment-based production settings.  
4. Block open redirect on login.  
5. Require POST for all delete (and other state-changing) actions.

### P1 — shortly after

6. Fix XSS (`|safe` / HTML sanitization).  
7. Gate paid resource files.  
8. Real contact form backend.  
9. Production static + media serving.  
10. Stronger student password validation.

### P2 — quality & maintainability

11. Remove duplicate resources URL; wire correct list view.  
12. Add automated tests for authz, API leakage, deletes, login redirect.  
13. Rate limits on chat and auth.  
14. Postgres + proper Docker entrypoint (migrate, collectstatic).

---

## 9. Scope Limitations

This was a **static + targeted dynamic** audit (code review + a few authenticated HTTP probes). It did **not** include:

- Full browser UI regression on every page  
- Load/performance testing  
- Penetration testing of file upload parsers beyond review  
- Third-party dependency CVE scanning beyond `requirements.txt` inventory  
- Live production server configuration  

---

## 10. Conclusion

The application has substantial product functionality, but **authorization gaps in the admin panel**, **public answer leakage via the API**, and **production-insecure defaults** are blocking issues. Fixing the P0 items first will close the highest risk holes without redesigning the product.

**No application source was modified as part of this audit** (temporary test account used for probes was removed afterward).
