from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, Http404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django import forms as django_forms
import json
import os

from .forms import (
    CSVUploadForm,
    ManualQuestionForm,
    QuestionBankForm,
    BlogForm,
    CourseForm,
    CategoryForm,
    ResourceForm,
    ExamForm,
    PastPaperForm,
    PastPaperAnswerForm,
)
from .models import AdminUser, CSVUpload, ManualQuestionLog
from courses.models import (
    Question,
    QuestionOption,
    QuestionBank,
    Course,
    Blog,
    CourseCategory,
    Resource,
    Exam,
    ExamQuestion,
    QuestionList,
    QuestionListItem,
    PastPaper,
)
from courses.question_preview import question_preview_map as _question_preview_map
from courses.pagination_utils import paginate, pagination_context

# Question types that use dynamic Answers (options) in the wizard, as
# opposed to fill_blank/integer which capture the answer differently.
WIZARD_OPTION_TYPES = {"mcq", "true_false", "comprehension"}

# Older CSV/import types that store choices on option_a..d fields.
LEGACY_CHOICE_TYPES = {"single_choice", "multiple_choice", "true_false"}


def _wants_json(request):
    """True when the client expects a JSON response (AJAX create bank, etc.)."""
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return True
    if request.GET.get("format") == "json":
        return True
    if request.content_type and "application/json" in request.content_type:
        return True
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


# ==================== AUTHENTICATION ====================
def admin_login(request):
    """Legacy admin login URL — redirect to the single unified login form.

    Admins and students both sign in at /login/. Role decides the destination.
    """
    if request.user.is_authenticated:
        if hasattr(request.user, "admin_profile"):
            return redirect("admin_panel:dashboard")
        if request.user.is_superuser:
            AdminUser.objects.get_or_create(user=request.user)
            return redirect("admin_panel:dashboard")
        if hasattr(request.user, "student_profile"):
            return redirect("courses:student_exams")

    login_url = reverse("courses:student_login")
    next_url = request.GET.get("next") or reverse("admin_panel:dashboard")
    separator = "&" if "?" in login_url else "?"
    return redirect(f"{login_url}{separator}next={next_url}")


def admin_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("courses:student_login")


def admin_required(view_func):
    """Require login + admin_profile for all admin-panel views."""

    @login_required(login_url="courses:student_login")
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, "admin_profile"):
            # Superusers get an admin profile on the fly
            if request.user.is_superuser:
                AdminUser.objects.get_or_create(user=request.user)
            else:
                messages.error(request, "You do not have admin access")
                return redirect("courses:student_login")
        return view_func(request, *args, **kwargs)

    return wrapped_view


# ==================== DASHBOARD ====================
@admin_required
def dashboard(request):
    admin_user = request.user.admin_profile
    context = {
        "total_questions": Question.objects.count(),
        "total_courses": Course.objects.count(),
        "total_blogs": Blog.objects.count(),
        "total_uploads": CSVUpload.objects.filter(admin_user=admin_user).count(),
        "recent_uploads": CSVUpload.objects.filter(admin_user=admin_user)[:5],
        "admin_user": admin_user,
    }
    return render(request, "admin_panel/dashboard.html", context)


# ==================== CSV UPLOAD ====================
def _serve_sample_file(filename: str, download_name: str | None = None):
    """Serve a sample template from the project root as an attachment."""
    template_path = os.path.join(settings.BASE_DIR, filename)
    if not os.path.exists(template_path):
        raise Http404(f"Sample file not found: {filename}")
    return FileResponse(
        open(template_path, "rb"),
        as_attachment=True,
        filename=download_name or filename,
    )


@admin_required
def download_sample_template(request):
    """
    Serves the ready-to-use sample_questions.xlsx (project root) so admins
    have a working Excel template with the exact expected columns —
    including topic/paper_code/year/season/zone already filled in on every
    row, so an unmodified upload also shows up immediately in the Exam
    Builder (which only lists questions that have a paper_code).
    """
    return _serve_sample_file("sample_questions.xlsx")


@admin_required
def download_sample_docx(request):
    """
    Sample Word question paper (.docx) matching the importer format:
    numbered questions, (a)(b)(c)(d) options, and an Answer Sheet.
    """
    return _serve_sample_file("sample_questions.docx")


@admin_required
def download_sample_resource_docx(request):
    """Sample Word document for the Resources upload form (.doc/.docx)."""
    return _serve_sample_file("sample_resource.docx")


@admin_required
def download_sample_blog_pdf(request):
    """Sample PDF for the Blog form PDF upload field."""
    return _serve_sample_file("sample_blog.pdf")


@admin_required
def download_sample_blog_pptx(request):
    """Sample PowerPoint for the Blog form PPT/PPTX upload field."""
    return _serve_sample_file("sample_blog.pptx")


@admin_required
def download_sample_blog_docx(request):
    """Sample Word doc for blog-related attachments (optional reference)."""
    return _serve_sample_file("sample_blog.docx")


@admin_required
def download_sample_past_paper_question(request):
    """Sample question-paper PDF for Past Papers upload."""
    return _serve_sample_file(
        "sample_past_paper_question.pdf",
        download_name="sample_past_paper_question.pdf",
    )


@admin_required
def download_sample_past_paper_answer(request):
    """Sample answer / mark-scheme PDF for Past Papers upload."""
    return _serve_sample_file(
        "sample_past_paper_answer.pdf",
        download_name="sample_past_paper_answer.pdf",
    )


SESSION_IMPORT_PREVIEW = "admin_question_import_preview"

# Pipeline stages shown on upload / preview screens
UPLOAD_PIPELINE_STEPS = [
    ("upload", "DOC / DOCX Upload"),
    ("normalize", "Prepare / Normalize document"),
    ("convert", "DOC → DOCX"),
    ("equations", "Extract equations"),
    ("latex", "Equation → LaTeX"),
    ("parse_q", "Parse questions + A/B/C/D"),
    ("parse_a", "Parse answer sheet"),
    ("preview", "Preview questions"),
    ("edit", "Edit if required"),
    ("import", "Import Questions"),
    ("database", "Existing database"),
]


def _pipeline_stats_from_questions(questions, *, source_type: str, file_name: str):
    """Build status for the Word/CSV import pipeline UI."""
    latex_q = 0
    eq_img_q = 0
    eq_img_total = 0
    with_answers = 0
    for q in questions:
        blob = " ".join(
            str(q.get(k) or "")
            for k in (
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
            )
        )
        if "$" in blob or "\\(" in blob:
            latex_q += 1
        imgs = q.get("equation_images") or []
        if isinstance(imgs, list) and imgs:
            eq_img_q += 1
            eq_img_total += len(imgs)
        if (q.get("correct_answer") or "").strip():
            with_answers += 1

    is_word = source_type == "word"
    is_doc = file_name.lower().endswith(".doc") and not file_name.lower().endswith(
        ".docx"
    )
    return {
        "source_type": source_type,
        "file_name": file_name,
        "question_count": len(questions),
        "with_latex": latex_q,
        "with_eq_images": eq_img_q,
        "eq_image_total": eq_img_total,
        "with_answers": with_answers,
        "is_word": is_word,
        "doc_converted": bool(is_word and is_doc),
        # Step completion flags for the visual pipeline
        "steps_done": {
            "upload": True,
            "normalize": is_word,
            "convert": bool(is_word and (is_doc or file_name.lower().endswith(".docx"))),
            "equations": is_word and (latex_q > 0 or eq_img_q > 0 or len(questions) > 0),
            "latex": is_word and latex_q > 0,
            "parse_q": len(questions) > 0,
            "parse_a": with_answers > 0,
            "preview": True,
            "edit": False,
            "import": False,
            "database": False,
        },
    }


def _serialize_import_question(q: dict) -> dict:
    """JSON-safe question dict for session storage."""
    eq = q.get("equation_images") or []
    if not isinstance(eq, list):
        eq = []
    year = q.get("year")
    try:
        year = int(year) if year not in (None, "") else None
    except (TypeError, ValueError):
        year = None
    try:
        marks = int(float(q.get("marks") or 1))
    except (TypeError, ValueError):
        marks = 1
    return {
        "question_text": str(q.get("question_text") or ""),
        "question_type": str(q.get("question_type") or "single_choice"),
        "option_a": str(q.get("option_a") or ""),
        "option_b": str(q.get("option_b") or ""),
        "option_c": str(q.get("option_c") or ""),
        "option_d": str(q.get("option_d") or ""),
        "correct_answer": str(q.get("correct_answer") or ""),
        "marks": marks,
        "explanation": str(q.get("explanation") or ""),
        "video_solution_url": str(q.get("video_solution_url") or "")[:500],
        "topic": str(q.get("topic") or ""),
        "paper_code": str(q.get("paper_code") or ""),
        "year": year,
        "season": str(q.get("season") or ""),
        "zone": str(q.get("zone") or ""),
        "question_number": str(q.get("question_number") or ""),
        "equation_images": [str(u) for u in eq if u],
    }


def _import_questions_to_bank(question_bank, questions, admin_user, file_name, file_obj=None):
    """
    Write parsed/edited question dicts into the database.
    Returns (successful, failed, errors, stats_dict).
    """
    csv_upload = CSVUpload(
        admin_user=admin_user,
        file_name=file_name or "import",
        total_questions=len(questions),
        status="processing",
    )
    if file_obj:
        csv_upload.file = file_obj
    csv_upload.save()

    successful = 0
    failed = 0
    errors = []
    questions_with_latex = 0
    questions_with_eq_images = 0
    equation_image_total = 0

    with transaction.atomic():
        for idx, q_data in enumerate(questions, 1):
            try:
                eq_images = q_data.get("equation_images") or []
                if not isinstance(eq_images, list):
                    eq_images = []
                blob = " ".join(
                    [
                        str(q_data.get("question_text") or ""),
                        str(q_data.get("option_a") or ""),
                        str(q_data.get("option_b") or ""),
                        str(q_data.get("option_c") or ""),
                        str(q_data.get("option_d") or ""),
                    ]
                )
                if "$" in blob or "\\(" in blob:
                    questions_with_latex += 1
                if eq_images:
                    questions_with_eq_images += 1
                    equation_image_total += len(eq_images)

                paper_code = (q_data.get("paper_code") or "").strip()
                if not paper_code:
                    paper_code = f"IMPORT-{question_bank.id}"

                year = q_data.get("year")
                try:
                    year = int(year) if year not in (None, "") else None
                except (TypeError, ValueError):
                    year = None

                try:
                    marks = int(float(q_data.get("marks") or 1))
                except (TypeError, ValueError):
                    marks = 1

                Question.objects.create(
                    question_bank=question_bank,
                    question_text=q_data.get("question_text") or "",
                    question_type=q_data.get("question_type") or "single_choice",
                    option_a=q_data.get("option_a", "") or "",
                    option_b=q_data.get("option_b", "") or "",
                    option_c=q_data.get("option_c", "") or "",
                    option_d=q_data.get("option_d", "") or "",
                    correct_answer=q_data.get("correct_answer", "") or "",
                    marks=marks,
                    explanation=q_data.get("explanation", "") or "",
                    video_solution_url=(
                        (q_data.get("video_solution_url") or "").strip()[:500]
                    ),
                    topic=q_data.get("topic", "") or "",
                    paper_code=paper_code,
                    year=year,
                    season=q_data.get("season", "") or "",
                    zone=q_data.get("zone", "") or "",
                    question_number=q_data.get("question_number", "") or str(idx),
                    equation_images=(json.dumps(eq_images) if eq_images else ""),
                    order=idx,
                )
                successful += 1
            except (ValueError, TypeError, KeyError, OSError) as e:
                failed += 1
                errors.append(f"Row {idx}: {e}")
            except Exception as e:
                failed += 1
                errors.append(f"Row {idx}: {type(e).__name__}: {e}")

    csv_upload.successful_imports = successful
    csv_upload.failed_imports = failed
    csv_upload.error_details = "\n".join(errors[:20])
    csv_upload.status = (
        "success"
        if failed == 0 and successful > 0
        else ("partial" if successful else "failed")
    )
    csv_upload.save()

    question_bank.total_questions = question_bank.questions.count()
    question_bank.save(update_fields=["total_questions"])

    stats = {
        "questions_with_latex": questions_with_latex,
        "questions_with_eq_images": questions_with_eq_images,
        "equation_image_total": equation_image_total,
    }
    return successful, failed, errors, stats


def _normalize_import_question(raw: dict, index: int) -> dict | None:
    """Normalize one question dict from preview JSON / form. None = skip."""
    if not isinstance(raw, dict):
        return None
    if raw.get("skip") in (True, 1, "1", "true", "True"):
        return None
    try:
        marks = int(float(raw.get("marks") or 1))
    except (TypeError, ValueError):
        marks = 1
    year = raw.get("year")
    try:
        year = int(year) if year not in (None, "") else None
    except (TypeError, ValueError):
        year = None
    eq = raw.get("equation_images") or []
    if isinstance(eq, str):
        try:
            eq = json.loads(eq)
        except (TypeError, ValueError, json.JSONDecodeError):
            eq = []
    if not isinstance(eq, list):
        eq = []
    return {
        "question_text": str(raw.get("question_text") or ""),
        "question_type": str(raw.get("question_type") or "single_choice"),
        "option_a": str(raw.get("option_a") or ""),
        "option_b": str(raw.get("option_b") or ""),
        "option_c": str(raw.get("option_c") or ""),
        "option_d": str(raw.get("option_d") or ""),
        "correct_answer": str(raw.get("correct_answer") or "").strip(),
        "marks": marks,
        "explanation": str(raw.get("explanation") or ""),
        "video_solution_url": str(raw.get("video_solution_url") or "")[:500],
        "topic": str(raw.get("topic") or ""),
        "paper_code": str(raw.get("paper_code") or ""),
        "year": year,
        "season": str(raw.get("season") or ""),
        "zone": str(raw.get("zone") or ""),
        "question_number": str(raw.get("question_number") or str(index + 1)),
        "equation_images": [str(u) for u in eq if u],
    }


def _questions_from_preview_post(request, session_questions: list) -> list[dict]:
    """
    Rebuild questions for import.

    Prefer a single JSON field `import_payload` (avoids Django
    DATA_UPLOAD_MAX_NUMBER_FIELDS errors with 70+ questions).
    Fall back to session data when the payload is empty (import as-parsed).
    """
    payload_raw = (request.POST.get("import_payload") or "").strip()
    if payload_raw:
        try:
            payload = json.loads(payload_raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, list):
            out = []
            for i, raw in enumerate(payload):
                q = _normalize_import_question(raw, i)
                if q is not None:
                    out.append(q)
            return out

    # No payload / invalid → import original session questions (no skips)
    out = []
    for i, raw in enumerate(session_questions or []):
        q = _normalize_import_question(raw, i)
        if q is not None:
            out.append(q)
    return out


@admin_required
def csv_upload(request):
    """
    Step 1 of the question import pipeline:
      DOC/DOCX (or CSV/Excel) upload → normalize → parse → session preview.
    Import to the database happens on the preview confirm screen.
    """
    admin_user = request.user.admin_profile

    # Allow starting a fresh upload even if a preview is pending
    if request.method == "GET" and request.GET.get("fresh") == "1":
        old = request.session.pop(SESSION_IMPORT_PREVIEW, None)
        if old and old.get("upload_id"):
            CSVUpload.objects.filter(
                id=old["upload_id"], admin_user=admin_user
            ).update(
                status="failed",
                error_details="Replaced by a new upload before import.",
            )
        request.session.modified = True

    pending_preview = request.session.get(SESSION_IMPORT_PREVIEW)

    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            course = form.cleaned_data["course"]
            question_bank = form.cleaned_data["question_bank"]
            name_lower = csv_file.name.lower()

            try:
                questions = form.parse_csv()
                if not questions:
                    messages.error(request, "No questions were found in this file.")
                    return redirect("admin_panel:csv_upload")

                if name_lower.endswith((".docx", ".doc")):
                    source_type = "word"
                elif name_lower.endswith((".xlsx", ".xls")):
                    source_type = "excel"
                else:
                    source_type = "csv"

                serialized = [_serialize_import_question(q) for q in questions]
                pipeline = _pipeline_stats_from_questions(
                    serialized, source_type=source_type, file_name=csv_file.name
                )

                # Keep the original file on the upload log for audit (not yet imported)
                pending_upload = CSVUpload.objects.create(
                    admin_user=admin_user,
                    file_name=csv_file.name,
                    file=csv_file,
                    total_questions=len(serialized),
                    status="processing",
                )

                request.session[SESSION_IMPORT_PREVIEW] = {
                    "upload_id": pending_upload.id,
                    "file_name": csv_file.name,
                    "course_id": course.id,
                    "question_bank_id": question_bank.id,
                    "source_type": source_type,
                    "pipeline": pipeline,
                    "questions": serialized,
                }
                request.session.modified = True

                messages.success(
                    request,
                    f"Parsed {len(serialized)} question(s) from “{csv_file.name}”. "
                    f"Review and edit below, then import into the database.",
                )
                return redirect("admin_panel:csv_upload_preview")

            except (ValidationError, django_forms.ValidationError) as e:
                # Surface clean validation messages (e.g. .doc conversion failures)
                if hasattr(e, "messages"):
                    msg = "; ".join(str(m) for m in e.messages)
                else:
                    msg = str(e)
                messages.error(request, msg)
            except (OSError, ValueError, TypeError, UnicodeDecodeError) as e:
                messages.error(request, f"Error processing file: {e}")
            except Exception as e:
                messages.error(
                    request,
                    f"Unexpected error processing file ({type(e).__name__}): {e}",
                )
    else:
        form = CSVUploadForm()

    context = {
        "form": form,
        "uploads": CSVUpload.objects.filter(admin_user=admin_user)[:10],
        "pipeline_steps": UPLOAD_PIPELINE_STEPS,
        "pending_preview": pending_preview,
    }
    return render(request, "admin_panel/csv_upload.html", context)


@admin_required
def csv_upload_preview(request):
    """
    Steps 8–10: Preview parsed questions, edit if needed, then import to DB.
    """
    admin_user = request.user.admin_profile
    preview = request.session.get(SESSION_IMPORT_PREVIEW)
    if not preview or not preview.get("questions"):
        messages.info(request, "No file is waiting for preview. Upload a file first.")
        return redirect("admin_panel:csv_upload")

    question_bank = get_object_or_404(QuestionBank, id=preview["question_bank_id"])
    course = get_object_or_404(Course, id=preview["course_id"])
    questions = preview["questions"]
    pipeline = preview.get("pipeline") or {}

    if request.method == "POST":
        action = (request.POST.get("action") or "import").strip().lower()

        if action == "cancel":
            # Mark pending upload log as cancelled/failed
            upload_id = preview.get("upload_id")
            if upload_id:
                CSVUpload.objects.filter(id=upload_id, admin_user=admin_user).update(
                    status="failed",
                    error_details="Cancelled at preview (not imported).",
                )
            request.session.pop(SESSION_IMPORT_PREVIEW, None)
            request.session.modified = True
            messages.info(request, "Import cancelled. Nothing was saved to the database.")
            return redirect("admin_panel:csv_upload")

        # Apply edits from the preview form (single JSON payload preferred)
        edited = _questions_from_preview_post(request, questions)
        if not edited:
            messages.error(
                request,
                "No questions left to import (all were skipped or empty).",
            )
            return redirect("admin_panel:csv_upload_preview")

        # Re-use the pending CSVUpload row if present
        file_obj = None
        upload_id = preview.get("upload_id")
        pending = None
        if upload_id:
            pending = CSVUpload.objects.filter(
                id=upload_id, admin_user=admin_user
            ).first()
            if pending and pending.file:
                file_obj = pending.file

        try:
            if pending:
                # Import into bank; update the same audit row
                successful = 0
                failed = 0
                errors = []
                questions_with_latex = 0
                questions_with_eq_images = 0
                equation_image_total = 0

                with transaction.atomic():
                    for idx, q_data in enumerate(edited, 1):
                        try:
                            eq_images = q_data.get("equation_images") or []
                            if not isinstance(eq_images, list):
                                eq_images = []
                            blob = " ".join(
                                str(q_data.get(k) or "")
                                for k in (
                                    "question_text",
                                    "option_a",
                                    "option_b",
                                    "option_c",
                                    "option_d",
                                )
                            )
                            if "$" in blob or "\\(" in blob:
                                questions_with_latex += 1
                            if eq_images:
                                questions_with_eq_images += 1
                                equation_image_total += len(eq_images)

                            paper_code = (q_data.get("paper_code") or "").strip()
                            if not paper_code:
                                paper_code = f"IMPORT-{question_bank.id}"

                            year = q_data.get("year")
                            try:
                                year = int(year) if year not in (None, "") else None
                            except (TypeError, ValueError):
                                year = None
                            try:
                                marks = int(float(q_data.get("marks") or 1))
                            except (TypeError, ValueError):
                                marks = 1

                            Question.objects.create(
                                question_bank=question_bank,
                                question_text=q_data.get("question_text") or "",
                                question_type=q_data.get("question_type")
                                or "single_choice",
                                option_a=q_data.get("option_a", "") or "",
                                option_b=q_data.get("option_b", "") or "",
                                option_c=q_data.get("option_c", "") or "",
                                option_d=q_data.get("option_d", "") or "",
                                correct_answer=q_data.get("correct_answer", "") or "",
                                marks=marks,
                                explanation=q_data.get("explanation", "") or "",
                                video_solution_url=(
                                    (q_data.get("video_solution_url") or "").strip()[
                                        :500
                                    ]
                                ),
                                topic=q_data.get("topic", "") or "",
                                paper_code=paper_code,
                                year=year,
                                season=q_data.get("season", "") or "",
                                zone=q_data.get("zone", "") or "",
                                question_number=q_data.get("question_number", "")
                                or str(idx),
                                equation_images=(
                                    json.dumps(eq_images) if eq_images else ""
                                ),
                                order=idx,
                            )
                            successful += 1
                        except Exception as e:
                            failed += 1
                            errors.append(f"Row {idx}: {type(e).__name__}: {e}")

                pending.total_questions = len(edited)
                pending.successful_imports = successful
                pending.failed_imports = failed
                pending.error_details = "\n".join(errors[:20])
                pending.status = (
                    "success"
                    if failed == 0 and successful > 0
                    else ("partial" if successful else "failed")
                )
                pending.save()
                question_bank.total_questions = question_bank.questions.count()
                question_bank.save(update_fields=["total_questions"])
                stats = {
                    "questions_with_latex": questions_with_latex,
                    "questions_with_eq_images": questions_with_eq_images,
                    "equation_image_total": equation_image_total,
                }
            else:
                successful, failed, errors, stats = _import_questions_to_bank(
                    question_bank,
                    edited,
                    admin_user,
                    preview.get("file_name") or "import",
                    file_obj=None,
                )
        except Exception as e:
            messages.error(request, f"Import failed: {type(e).__name__}: {e}")
            return redirect("admin_panel:csv_upload_preview")

        request.session.pop(SESSION_IMPORT_PREVIEW, None)
        request.session.modified = True

        if successful == 0:
            messages.error(
                request,
                "No questions were saved. "
                + ("; ".join(errors[:3]) if errors else "Check the preview data."),
            )
            return redirect("admin_panel:csv_upload")

        success_msg = (
            f"✅ Import complete: {successful} question(s) saved"
            + (f", {failed} failed" if failed else "")
            + f" into “{question_bank.title}”."
        )
        if stats.get("questions_with_latex"):
            success_msg += (
                f" {stats['questions_with_latex']} question(s) use text + LaTeX."
            )
        if stats.get("questions_with_eq_images"):
            success_msg += (
                f" {stats['questions_with_eq_images']} question(s) still have "
                f"{stats.get('equation_image_total', 0)} fallback equation image(s)."
            )
        success_msg += " Open Manage Questions to review them."
        messages.success(request, success_msg)
        return redirect(
            reverse("admin_panel:manage_questions")
            + f"?question_bank={question_bank.id}"
        )

    # GET — show editable preview
    steps_done = dict(pipeline.get("steps_done") or {})
    steps_done["preview"] = True
    steps_done["edit"] = True
    active_keys = {"preview", "edit", "import"}
    pipeline_ui = [
        {
            "key": key,
            "label": label,
            "done": bool(steps_done.get(key)),
            "active": key in active_keys,
        }
        for key, label in UPLOAD_PIPELINE_STEPS
    ]
    equation_images_json = [
        (q.get("equation_images") if isinstance(q.get("equation_images"), list) else [])
        for q in questions
    ]

    context = {
        "course": course,
        "question_bank": question_bank,
        "questions": questions,
        "question_count": len(questions),
        "file_name": preview.get("file_name") or "",
        "source_type": preview.get("source_type") or "word",
        "pipeline": pipeline,
        "pipeline_ui": pipeline_ui,
        "equation_images_json": equation_images_json,
        "question_types": Question.QUESTION_TYPES,
    }
    return render(request, "admin_panel/csv_upload_preview.html", context)


SESSION_LAST_QUESTION_BANK = "admin_last_question_bank_id"


def _resolve_question_bank(request, bank_id=None):
    """Pick a durable question bank: explicit id → session → most recent.

    Question banks are permanent DB rows; they must never look "gone" after
    logout/login just because the URL no longer has ?question_bank=.
    """
    question_banks = QuestionBank.objects.select_related("course").order_by(
        "-created_at", "-id"
    )
    selected_bank = None

    # 1) Explicit query param
    if bank_id not in (None, ""):
        selected_bank = question_banks.filter(pk=bank_id).first()

    # 2) Last bank used in this browser session (survives navigation)
    if selected_bank is None:
        session_id = request.session.get(SESSION_LAST_QUESTION_BANK)
        if session_id:
            selected_bank = question_banks.filter(pk=session_id).first()

    # 3) Fall back to newest bank so Add Question always shows existing data
    if selected_bank is None:
        selected_bank = question_banks.first()

    if selected_bank is not None:
        request.session[SESSION_LAST_QUESTION_BANK] = selected_bank.id
        # Ensure session is saved even if only this key changed
        request.session.modified = True
    elif SESSION_LAST_QUESTION_BANK in request.session:
        del request.session[SESSION_LAST_QUESTION_BANK]
        request.session.modified = True

    return question_banks, selected_bank


# ==================== MANUAL QUESTION (Question Wizard) ====================
@admin_required
def manual_question(request):
    """Renders the Exam Builder 'Create Questions' wizard shell.

    Actual question creation/editing now happens through the AJAX
    endpoints below (question_wizard_bulk_create / _data / _save /
    _delete), driven by the modal UI in manual_question.html — this
    mirrors a 'select type -> set count & marks -> edit each question'
    flow instead of one static form for a single question.
    """
    question_banks, selected_bank = _resolve_question_bank(
        request, request.GET.get("question_bank")
    )

    # Canonical URL always includes the selected bank so refresh/share works
    raw_id = request.GET.get("question_bank")
    if selected_bank and str(selected_bank.id) != str(raw_id or ""):
        return redirect(
            f"{reverse('admin_panel:manual_question')}?question_bank={selected_bank.id}"
        )

    bank_questions = []
    page_obj = None
    pag_extra = {}
    if selected_bank:
        qs = selected_bank.questions.prefetch_related("options").order_by(
            "order", "id"
        )
        page_obj, per_page_label, choices = paginate(request, qs)
        bank_questions = page_obj.object_list
        pag_extra = pagination_context(request, page_obj, per_page_label, choices)

    bank_subjects = (
        QuestionBank.objects.exclude(subject_title="")
        .values_list("subject_title", flat=True)
        .distinct()
        .order_by("subject_title")
    )
    context = {
        "question_banks": question_banks,
        "selected_bank": selected_bank,
        "bank_questions": bank_questions,
        "question_types": Question.QUESTION_TYPES,
        "difficulty_levels": Question.DIFFICULTY_LEVELS,
        "recent_questions": Question.objects.order_by("-created_at")[:10],
        "courses": Course.objects.order_by("title"),
        "bank_subjects": list(bank_subjects),
        **pag_extra,
    }
    return render(request, "admin_panel/manual_question.html", context)


@admin_required
@require_POST
def create_question_bank(request):
    """Create a new Question Bank (AJAX JSON or form POST).

    Returns JSON when Content-Type is application/json or when
    ?format=json / Accept prefers JSON; otherwise redirects back to
    the manual-question page with the new bank selected.
    """
    if not hasattr(request.user, "admin_profile"):
        if _wants_json(request):
            return JsonResponse({"error": "Unauthorized"}, status=403)
        return redirect("courses:student_login")

    wants_json = _wants_json(request)

    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body or b"{}")
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid JSON body"}, status=400)
        data = {
            "course": payload.get("course") or payload.get("course_id"),
            "title": (payload.get("title") or "").strip(),
            "subject_title": (
                payload.get("subject_title")
                or payload.get("subject")
                or ""
            ).strip(),
            "description": (payload.get("description") or "").strip(),
            "difficulty": payload.get("difficulty") or "medium",
        }
    else:
        data = {
            "course": request.POST.get("course") or request.POST.get("course_id"),
            "title": (request.POST.get("title") or "").strip(),
            "subject_title": (
                request.POST.get("subject_title")
                or request.POST.get("subject")
                or ""
            ).strip(),
            "description": (request.POST.get("description") or "").strip(),
            "difficulty": request.POST.get("difficulty") or "medium",
        }

    form = QuestionBankForm(data)
    if not form.is_valid():
        # Flatten form errors for the UI
        errors = {
            field: [str(e) for e in errs] for field, errs in form.errors.items()
        }
        msg = "; ".join(
            f"{f}: {', '.join(es)}" for f, es in errors.items()
        ) or "Invalid form data"
        if wants_json:
            return JsonResponse({"error": msg, "errors": errors}, status=400)
        messages.error(request, msg)
        return redirect("admin_panel:manual_question")

    bank = form.save()
    # Remember selection so re-open / re-login (session) keeps this bank
    request.session[SESSION_LAST_QUESTION_BANK] = bank.id
    request.session.modified = True

    label = bank.display_label
    if wants_json:
        return JsonResponse(
            {
                "success": True,
                "question_bank": {
                    "id": bank.id,
                    "title": bank.title,
                    "subject_title": bank.subject_title,
                    "description": bank.description,
                    "difficulty": bank.difficulty,
                    "course_id": bank.course_id,
                    "course_title": bank.course.title,
                    "label": label,
                },
            }
        )

    messages.success(request, f'Question bank "{bank.title}" created successfully.')
    return redirect(
        reverse("admin_panel:manual_question") + f"?question_bank={bank.id}"
    )


def _serialize_question(question):
    """JSON-friendly representation of a Question + its options, used to
    populate the wizard editor modal (initial load, Previous/Next nav)."""
    options = [
        {
            "id": opt.id,
            "text": opt.text,
            "is_correct": opt.is_correct,
            "order": opt.order,
        }
        for opt in question.options.all()
    ]
    # Fall back to legacy A–D fields when no dynamic options exist.
    if not options and any(
        [question.option_a, question.option_b, question.option_c, question.option_d]
    ):
        correct = (question.correct_answer or "").upper().replace(" ", "")
        correct_letters = {c for c in correct.replace(",", "")}
        for letter, text in (
            ("A", question.option_a),
            ("B", question.option_b),
            ("C", question.option_c),
            ("D", question.option_d),
        ):
            if text:
                options.append(
                    {
                        "id": None,
                        "text": text,
                        "is_correct": letter in correct_letters,
                        "order": ord(letter) - ord("A"),
                    }
                )

    return {
        "id": question.id,
        "question_type": question.question_type,
        "question_type_label": question.get_question_type_display(),
        "question_text": question.question_text,
        "answer_type": question.answer_type,
        "difficulty_level": question.difficulty_level,
        "marks": question.marks,
        "negative_marks": str(question.negative_marks),
        "partial_marking": question.partial_marking,
        "explanation": question.explanation,
        "video_solution_url": question.video_solution_url or "",
        "passage": question.passage,
        "correct_answer": question.correct_answer,
        "numeric_tolerance": (
            str(question.numeric_tolerance)
            if question.numeric_tolerance is not None
            else ""
        ),
        "tags": question.tag_list,
        "option_a": question.option_a,
        "option_b": question.option_b,
        "option_c": question.option_c,
        "option_d": question.option_d,
        "equation_images": question.equation_image_list,
        "options": options,
    }


@admin_required
@require_POST
def question_wizard_bulk_create(request):
    """Step 2 of the wizard ('No. of Questions' / 'Marks per question' /
    negative & partial marking dialog): creates N blank placeholder
    Question rows of the chosen type ready for the editor modal to fill
    in one-by-one, and returns their ids in order."""
    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    bank_id = payload.get("question_bank_id")
    question_type = payload.get("question_type")
    count = int(payload.get("count") or 1)
    marks = int(payload.get("marks") or 1)
    negative_marks = payload.get("negative_marks") or 0
    partial_marking = bool(payload.get("partial_marking"))

    if question_type not in dict(Question.QUESTION_TYPES):
        return JsonResponse({"error": "Invalid question type"}, status=400)
    count = max(1, min(count, 100))
    question_bank = get_object_or_404(QuestionBank, id=bank_id)

    created_ids = []
    with transaction.atomic():
        start_order = question_bank.questions.count()
        for i in range(count):
            question = Question.objects.create(
                question_bank=question_bank,
                question_type=question_type,
                question_text="",
                marks=marks,
                negative_marks=negative_marks,
                partial_marking=partial_marking,
                order=start_order + i,
            )
            if question_type == "true_false":
                QuestionOption.objects.create(
                    question=question, text="True", order=0
                )
                QuestionOption.objects.create(
                    question=question, text="False", order=1
                )
            created_ids.append(question.id)

        question_bank.total_questions = question_bank.questions.count()
        question_bank.save(update_fields=["total_questions"])

    return JsonResponse(
        {
            "success": True,
            "question_ids": created_ids,
            "questions": [
                _serialize_question(q)
                for q in Question.objects.filter(id__in=created_ids).prefetch_related(
                    "options"
                ).order_by("order")
            ],
        }
    )


@admin_required
def question_wizard_data(request, question_id):
    """Fetches a single question's current data — used when the editor
    modal moves to Previous/Next or re-opens a question for editing."""
    question = get_object_or_404(
        Question.objects.prefetch_related("options"), id=question_id
    )
    return JsonResponse({"success": True, "question": _serialize_question(question)})


@admin_required
@require_POST
def question_wizard_save(request, question_id):
    """Saves the question currently open in the editor modal, including
    its full set of dynamic answer options and tags. Called on 'Save' as
    well as before navigating via 'Previous' / 'Next'."""
    question = get_object_or_404(Question, id=question_id)
    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    question.question_text = payload.get("question_text", "")
    question.answer_type = (
        payload.get("answer_type") if payload.get("answer_type") in dict(
            Question.ANSWER_TYPES
        ) else "single"
    )
    question.difficulty_level = payload.get("difficulty_level") or ""
    question.explanation = payload.get("explanation", "")
    # Optional video solution link (admin-only path)
    video_url = (payload.get("video_solution_url") or "").strip()
    if video_url and not (
        video_url.startswith("http://") or video_url.startswith("https://")
    ):
        video_url = "https://" + video_url
    question.video_solution_url = video_url[:500] if video_url else ""
    question.passage = payload.get("passage", "")
    question.marks = int(payload.get("marks") or question.marks or 1)
    question.negative_marks = payload.get("negative_marks") or 0
    question.partial_marking = bool(payload.get("partial_marking"))
    question.correct_answer = payload.get("correct_answer", "")

    tolerance = payload.get("numeric_tolerance")
    question.numeric_tolerance = tolerance if tolerance not in (None, "") else None

    tags = payload.get("tags") or []
    if isinstance(tags, list):
        question.tags = ", ".join(str(t).strip() for t in tags if str(t).strip())

    if not question.question_text.strip() and question.question_type not in (
        "fill_blank",
        "integer",
    ):
        return JsonResponse(
            {"error": "Question text is required."}, status=400
        )

    with transaction.atomic():
        # Always accept explicit legacy A–D fields when provided (CSV imports).
        if "option_a" in payload or "option_b" in payload:
            question.option_a = payload.get("option_a", question.option_a) or ""
            question.option_b = payload.get("option_b", question.option_b) or ""
            question.option_c = payload.get("option_c", question.option_c) or ""
            question.option_d = payload.get("option_d", question.option_d) or ""

        question.save()

        uses_dynamic_options = (
            question.question_type in WIZARD_OPTION_TYPES
            or question.question_type in LEGACY_CHOICE_TYPES
            or bool(payload.get("options"))
        )

        if uses_dynamic_options and question.question_type != "fill_blank":
            options = payload.get("options") or []
            # Build dynamic options from A–D if client only sent legacy fields.
            if not options and any(
                [question.option_a, question.option_b, question.option_c, question.option_d]
            ):
                correct = (question.correct_answer or "").upper().replace(" ", "")
                correct_letters = {c for c in correct.replace(",", "")}
                for letter, text in (
                    ("A", question.option_a),
                    ("B", question.option_b),
                    ("C", question.option_c),
                    ("D", question.option_d),
                ):
                    if text:
                        options.append(
                            {
                                "text": text,
                                "is_correct": letter in correct_letters,
                            }
                        )

            if question.question_type in ("mcq", "multiple_choice", "single_choice") and options:
                if not any(o.get("is_correct") for o in options):
                    return JsonResponse(
                        {"error": "Mark at least one option as correct."}, status=400
                    )
                if len(options) < 2 and question.question_type in (
                    "mcq",
                    "multiple_choice",
                    "single_choice",
                ):
                    return JsonResponse(
                        {"error": "Add at least two options."}, status=400
                    )

            question.options.all().delete()
            letters = []
            for idx, opt in enumerate(options):
                text = (opt.get("text") or "").strip()
                is_correct = bool(opt.get("is_correct"))
                QuestionOption.objects.create(
                    question=question,
                    text=opt.get("text", ""),
                    is_correct=is_correct,
                    order=idx,
                )
                # Keep legacy A–D columns in sync for the first four options.
                if idx < 4:
                    setattr(question, f"option_{chr(ord('a') + idx)}", text)
                    if is_correct:
                        letters.append(chr(ord("A") + idx))
            for idx in range(len(options), 4):
                setattr(question, f"option_{chr(ord('a') + idx)}", "")
            if letters and not payload.get("correct_answer"):
                question.correct_answer = ",".join(letters)
            question.save(
                update_fields=[
                    "option_a",
                    "option_b",
                    "option_c",
                    "option_d",
                    "correct_answer",
                ]
            )
        elif question.question_type == "fill_blank":
            question.options.all().delete()
            answers = payload.get("options") or []
            for idx, opt in enumerate(answers):
                text = opt.get("text", "").strip()
                if text:
                    QuestionOption.objects.create(
                        question=question, text=text, is_correct=True, order=idx
                    )

    question = Question.objects.prefetch_related("options").get(id=question.id)
    return JsonResponse({"success": True, "question": _serialize_question(question)})


@admin_required
@require_POST
def question_wizard_delete(request, question_id):
    """Deletes a question created in the wizard (e.g. an empty leftover
    placeholder, or via the 'Delete' action in the bank question list)."""
    question = get_object_or_404(Question, id=question_id)
    bank = question.question_bank
    question.delete()
    bank.total_questions = bank.questions.count()
    bank.save(update_fields=["total_questions"])
    return JsonResponse({"success": True})


@admin_required
@require_POST
def questions_bulk_delete(request):
    """Delete multiple questions by id (from Manage Questions select-all)."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    raw_ids = payload.get("ids") or payload.get("question_ids") or []
    if not isinstance(raw_ids, list) or not raw_ids:
        return JsonResponse({"error": "No questions selected"}, status=400)

    ids = []
    for x in raw_ids:
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            continue
    ids = list(dict.fromkeys(ids))  # unique, preserve order
    if not ids:
        return JsonResponse({"error": "No valid question ids"}, status=400)

    # Cap one request so a bad client cannot wipe the whole bank accidentally
    if len(ids) > 500:
        return JsonResponse(
            {"error": "Please delete at most 500 questions at a time"},
            status=400,
        )

    qs = Question.objects.filter(id__in=ids).select_related("question_bank")
    bank_ids = set(qs.values_list("question_bank_id", flat=True))
    deleted_count, _ = qs.delete()

    # Refresh question-bank counters
    for bank in QuestionBank.objects.filter(id__in=bank_ids):
        bank.total_questions = bank.questions.count()
        bank.save(update_fields=["total_questions"])

    return JsonResponse({"success": True, "deleted": deleted_count})


# ==================== MANAGE QUESTIONS ====================
@admin_required
def manage_questions(request):
    questions = (
        Question.objects.select_related("question_bank")
        .prefetch_related("options")
        .order_by("-created_at")
    )
    question_banks = QuestionBank.objects.all()

    qb_id = request.GET.get("question_bank")
    if qb_id:
        questions = questions.filter(question_bank_id=qb_id)

    page_obj, per_page_label, choices = paginate(request, questions)
    context = {
        "questions": page_obj.object_list,
        "question_banks": question_banks,
        "selected_qb": qb_id,
        **pagination_context(request, page_obj, per_page_label, choices),
    }
    return render(request, "admin_panel/manage_questions.html", context)


# ==================== BLOG MANAGEMENT ====================
@admin_required
def manage_blogs(request):
    blogs = Blog.objects.all().order_by("-created_at")
    return render(request, "admin_panel/manage_blogs.html", {"blogs": blogs})


@admin_required
def create_blog(request):
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog created successfully!")
            return redirect("admin_panel:manage_blogs")
    else:
        form = BlogForm()
    return render(
        request, "admin_panel/manage_blogs.html", {"form": form, "action": "Create"}
    )


@admin_required
def edit_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog updated successfully!")
            return redirect("admin_panel:manage_blogs")
    else:
        form = BlogForm(instance=blog)
    return render(
        request,
        "admin_panel/manage_blogs.html",
        {"form": form, "blog": blog, "action": "Edit"},
    )


@admin_required
@require_POST
def delete_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    blog.delete()
    messages.success(request, "Blog deleted successfully!")
    return redirect("admin_panel:manage_blogs")


# ==================== COURSE MANAGEMENT ====================
@admin_required
def manage_courses(request):
    courses = Course.objects.all().order_by("-created_at")
    categories = CourseCategory.objects.all()
    return render(
        request,
        "admin_panel/manage_courses.html",
        {"courses": courses, "categories": categories},
    )


@admin_required
def create_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully!")
            return redirect("admin_panel:manage_courses")
    else:
        form = CourseForm()
    return render(
        request, "admin_panel/manage_courses.html", {"form": form, "action": "Create"}
    )


@admin_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
            return redirect("admin_panel:manage_courses")
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "admin_panel/manage_courses.html",
        {"form": form, "course": course, "action": "Edit"},
    )


@admin_required
@require_POST
def delete_course(request, course_id):
    from django.db.models import ProtectedError

    course = get_object_or_404(Course, id=course_id)
    bank_count = course.question_banks.count()
    try:
        course.delete()
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete course "{course.title}" because it has '
            f"{bank_count} question bank(s). Delete or reassign those banks first "
            f"so your questions are not lost.",
        )
        return redirect("admin_panel:manage_courses")
    messages.success(request, "Course deleted successfully!")
    return redirect("admin_panel:manage_courses")


# ==================== CATEGORY MANAGEMENT ====================
@admin_required
def manage_categories(request):
    categories = CourseCategory.objects.all().order_by("name")
    return render(
        request, "admin_panel/manage_categories.html", {"categories": categories}
    )


@admin_required
def create_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return redirect("admin_panel:manage_categories")
    else:
        form = CategoryForm()
    return render(
        request,
        "admin_panel/manage_categories.html",
        {"form": form, "action": "Create"},
    )


@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(CourseCategory, id=category_id)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect("admin_panel:manage_categories")
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        "admin_panel/manage_categories.html",
        {"form": form, "category": category, "action": "Edit"},
    )


@admin_required
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(CourseCategory, id=category_id)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return redirect("admin_panel:manage_categories")


# ==================== RESOURCE MANAGEMENT ====================
@admin_required
def manage_resources(request):
    resources = Resource.objects.all().order_by("-created_at")
    return render(
        request, "admin_panel/manage_resources.html", {"resources": resources}
    )


@admin_required
def create_resource(request):
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource uploaded successfully!")
            return redirect("admin_panel:manage_resources")
    else:
        form = ResourceForm()
    return render(
        request, "admin_panel/manage_resources.html", {"form": form, "action": "Upload"}
    )


@admin_required
def edit_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated successfully!")
            return redirect("admin_panel:manage_resources")
    else:
        form = ResourceForm(instance=resource)
    return render(
        request,
        "admin_panel/manage_resources.html",
        {"form": form, "resource": resource, "action": "Edit"},
    )


@admin_required
@require_POST
def delete_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    resource.delete()
    messages.success(request, "Resource deleted successfully!")
    return redirect("admin_panel:manage_resources")


# ==================== PAST PAPERS (PDF browser) ====================
def _past_papers_page_context(
    form=None,
    action="Upload",
    paper=None,
    mode="question",
    answer_form=None,
):
    papers = PastPaper.objects.select_related("category").order_by(
        "-year", "subject", "title"
    )
    existing_subjects = (
        PastPaper.objects.exclude(subject="")
        .values_list("subject", flat=True)
        .distinct()
        .order_by("subject")
    )
    if form is None:
        form = PastPaperForm()
    if answer_form is None:
        answer_form = PastPaperAnswerForm()
    return {
        "form": form,
        "answer_form": answer_form,
        "papers": papers,
        "paper": paper,
        "action": action,
        "mode": mode,
        "existing_subjects": list(existing_subjects),
    }


@admin_required
def manage_past_papers(request):
    """Admin Past Papers hub: upload question paper or link answer sheet."""
    mode = (request.GET.get("mode") or "question").strip().lower()
    if mode not in ("question", "answer"):
        mode = "question"
    return render(
        request,
        "admin_panel/manage_past_papers.html",
        _past_papers_page_context(mode=mode),
    )


@admin_required
def create_past_paper(request):
    if request.method == "POST":
        form = PastPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save()
            answer_note = " with answer sheet" if paper.answer_pdf else ""
            messages.success(
                request,
                f'Question paper "{paper.title}" uploaded{answer_note} '
                f"({paper.category.name} · {paper.subject} · {paper.year}).",
            )
            return redirect("admin_panel:manage_past_papers")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = PastPaperForm()
    return render(
        request,
        "admin_panel/manage_past_papers.html",
        _past_papers_page_context(form=form, action="Upload", mode="question"),
    )


@admin_required
def upload_past_paper_answer(request):
    """Upload / replace answer sheet PDF linked to an existing question paper."""
    if request.method == "POST":
        answer_form = PastPaperAnswerForm(request.POST, request.FILES)
        if answer_form.is_valid():
            paper = answer_form.cleaned_data["past_paper"]
            new_file = answer_form.cleaned_data["answer_pdf"]
            if answer_form.cleaned_data.get("clear_existing") and paper.answer_pdf:
                paper.answer_pdf.delete(save=False)
            elif paper.answer_pdf:
                paper.answer_pdf.delete(save=False)
            paper.answer_pdf = new_file
            paper.save(update_fields=["answer_pdf", "updated_at"])
            messages.success(
                request,
                f'Answer paper linked to "{paper.title}" '
                f"({paper.category.name} · {paper.subject} · {paper.year}).",
            )
            return redirect(
                reverse("admin_panel:manage_past_papers") + "?mode=answer"
            )
        messages.error(request, "Please fix the errors below and try again.")
    else:
        answer_form = PastPaperAnswerForm()
    return render(
        request,
        "admin_panel/manage_past_papers.html",
        _past_papers_page_context(
            answer_form=answer_form, action="Upload", mode="answer"
        ),
    )


@admin_required
def edit_past_paper(request, paper_id):
    paper = get_object_or_404(PastPaper, id=paper_id)
    if request.method == "POST":
        form = PastPaperForm(request.POST, request.FILES, instance=paper)
        if form.is_valid():
            paper = form.save()
            messages.success(request, f'Past paper "{paper.title}" updated.')
            return redirect("admin_panel:manage_past_papers")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = PastPaperForm(instance=paper)
    return render(
        request,
        "admin_panel/manage_past_papers.html",
        _past_papers_page_context(
            form=form, action="Edit", paper=paper, mode="question"
        ),
    )


@admin_required
@require_POST
def delete_past_paper(request, paper_id):
    paper = get_object_or_404(PastPaper, id=paper_id)
    if paper.pdf:
        paper.pdf.delete(save=False)
    if paper.answer_pdf:
        paper.answer_pdf.delete(save=False)
    paper.delete()
    messages.success(request, "Past paper deleted successfully!")
    return redirect("admin_panel:manage_past_papers")


@admin_required
@require_POST
def clear_past_paper_answer(request, paper_id):
    """Remove only the answer sheet from a past paper (keep question PDF)."""
    paper = get_object_or_404(PastPaper, id=paper_id)
    if paper.answer_pdf:
        paper.answer_pdf.delete(save=False)
        paper.answer_pdf = None
        paper.save(update_fields=["answer_pdf", "updated_at"])
        messages.success(request, f'Answer sheet removed from "{paper.title}".')
    else:
        messages.info(request, "This paper has no answer sheet linked.")
    return redirect(reverse("admin_panel:manage_past_papers") + "?mode=answer")


# ==================== EXAM BUILDER ====================
@admin_required
def manage_exams(request):
    """List of all exams the admin has built, with a 'New Exam' entry point."""
    exams = Exam.objects.select_related("category", "created_by").all()
    return render(request, "admin_panel/manage_exams.html", {"exams": exams})


@admin_required
def create_exam(request):
    """Creates a blank draft exam and redirects straight into the builder."""
    default_category = CourseCategory.objects.first()
    exam = Exam.objects.create(
        name="Untitled Exam",
        category=default_category,
        created_by=request.user,
        status="draft",
    )
    return redirect("admin_panel:edit_exam", exam_id=exam.id)


@admin_required
def edit_exam(request, exam_id):
    """
    The main Exam Builder screen (mirrors the 'Edit Exam' UI):
      - top bar: exam name, tabs (Select Questions / Selected Questions / Settings / Export)
      - filter bar: Topic(s), Year(s), Type (Category) + Submit
      - left panel: paginated list of matching questions, with quick-add (+)
      - right panel: live preview of the highlighted question (question/answer toggle)

    All questions shown are pulled live from the database (Question model) —
    filtered by topic, year, and category (Type).
    """
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == "POST" and "rename_exam" in request.POST:
        new_name = request.POST.get("name", "").strip()
        if new_name:
            exam.name = new_name
            exam.save(update_fields=["name", "updated_at"])
            messages.success(request, "Exam name updated.")
        return redirect("admin_panel:edit_exam", exam_id=exam.id)

    categories = CourseCategory.objects.all()

    # ---- Filter bar state (Topic(s), Year(s), Type/Category) ----
    category_id = request.GET.get("category") or (exam.category_id or "")
    topic = request.GET.get("topic", "")
    year = request.GET.get("year", "")
    sort = request.GET.get(
        "sort", "desc"
    )  # desc = newest/highest question number first

    questions = Question.objects.select_related("question_bank__course__category")
    if category_id:
        questions = questions.filter(question_bank__course__category_id=category_id)
    if topic:
        questions = questions.filter(topic__icontains=topic)
    if year:
        questions = questions.filter(year=year)

    questions = questions.exclude(paper_code="")
    questions = (
        questions.order_by("-year", "-paper_code")
        if sort == "desc"
        else questions.order_by("year", "paper_code")
    )

    # Distinct filter option lists, scoped to the selected category
    option_scope = Question.objects.exclude(paper_code="")
    if category_id:
        option_scope = option_scope.filter(
            question_bank__course__category_id=category_id
        )

    topics = sorted(
        {
            t.strip()
            for q in option_scope.values_list("topic", flat=True)
            for t in q.split(",")
            if t.strip()
        }
    )
    years = sorted(
        option_scope.exclude(year__isnull=True)
        .values_list("year", flat=True)
        .distinct(),
        reverse=True,
    )

    page_obj, per_page_label, per_page_choices = paginate(request, questions)

    selected_ids = set(
        ExamQuestion.objects.filter(exam=exam).values_list("question_id", flat=True)
    )

    exam_questions = (
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .order_by("order", "added_at")
    )

    settings_form = ExamForm(instance=exam)

    context = {
        "exam": exam,
        "categories": categories,
        "questions": page_obj.object_list,
        "selected_ids": selected_ids,
        "exam_questions": exam_questions,
        "selected_count": exam_questions.count(),
        "total_marks": exam.total_marks,
        "filters": {
            "category": str(category_id) if category_id else "",
            "topic": topic,
            "year": year,
            "sort": sort,
            "per_page": per_page_label,
        },
        "topics": topics,
        "years": years,
        "settings_form": settings_form,
        "question_preview_data": _question_preview_map(page_obj.object_list),
        **pagination_context(request, page_obj, per_page_label, per_page_choices),
    }
    return render(request, "admin_panel/edit_exam.html", context)


@admin_required
@require_POST
def exam_toggle_question(request, exam_id):
    """AJAX endpoint: add/remove a single question from an exam (the '+' button)."""
    exam = get_object_or_404(Exam, id=exam_id)
    question_id = request.POST.get("question_id")
    question = get_object_or_404(Question, id=question_id)

    link = ExamQuestion.objects.filter(exam=exam, question=question).first()
    if link:
        link.delete()
        added = False
    else:
        next_order = ExamQuestion.objects.filter(exam=exam).count()
        ExamQuestion.objects.create(exam=exam, question=question, order=next_order)
        added = True

    return JsonResponse(
        {
            "added": added,
            "selected_count": ExamQuestion.objects.filter(exam=exam).count(),
            "total_marks": exam.total_marks,
        }
    )


@admin_required
@require_POST
def exam_reorder_questions(request, exam_id):
    """AJAX endpoint: persist drag-and-drop reordering from the Selected Questions tab."""
    exam = get_object_or_404(Exam, id=exam_id)
    try:
        ordered_ids = json.loads(request.body).get("question_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return HttpResponseBadRequest("Invalid payload")

    with transaction.atomic():
        for index, qid in enumerate(ordered_ids):
            ExamQuestion.objects.filter(exam=exam, question_id=qid).update(order=index)

    return JsonResponse({"ok": True})


@admin_required
def exam_settings(request, exam_id):
    """Settings tab: duration, layout, shuffle, subject/category."""
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam settings saved.")
            return redirect("admin_panel:exam_settings", exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)
    return render(
        request,
        "admin_panel/edit_exam.html",
        {
            "exam": exam,
            "settings_form": form,
            "active_tab": "settings",
            "categories": CourseCategory.objects.all(),
            "exam_questions": ExamQuestion.objects.filter(exam=exam).select_related(
                "question"
            ),
            "selected_count": ExamQuestion.objects.filter(exam=exam).count(),
            "total_marks": exam.total_marks,
        },
    )


@admin_required
@require_POST
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.delete()
    messages.success(request, "Exam deleted.")
    return redirect("admin_panel:manage_exams")


# ==================== BUILD QUESTION LIST (ADMIN) ====================
@admin_required
def manage_question_lists(request):
    """List of all admin-curated question lists, with a 'New List' entry point."""
    lists = QuestionList.objects.filter(is_admin_curated=True).select_related(
        "category", "created_by"
    )
    return render(request, "admin_panel/manage_question_lists.html", {"lists": lists})


@admin_required
def create_question_list(request):
    """Creates a blank admin-curated question list and opens the builder."""
    default_category = CourseCategory.objects.first()
    qlist = QuestionList.objects.create(
        name="Untitled Question List",
        category=default_category,
        created_by=request.user,
        is_admin_curated=True,
    )
    return redirect("admin_panel:edit_question_list", list_id=qlist.id)


@admin_required
def edit_question_list(request, list_id):
    """
    Admin-curated Build Question List screen — same filter/select/reorder
    workspace as the student builder, with no timer/settings/export.
    Filters: Topic(s), Year(s), Type (Category) + Submit. Questions are
    pulled live from the database.
    """
    qlist = get_object_or_404(QuestionList, id=list_id, is_admin_curated=True)

    if request.method == "POST" and "rename_list" in request.POST:
        new_name = request.POST.get("name", "").strip()
        if new_name:
            qlist.name = new_name
            qlist.save(update_fields=["name", "updated_at"])
            messages.success(request, "List name updated.")
        return redirect("admin_panel:edit_question_list", list_id=qlist.id)

    categories = CourseCategory.objects.all()

    category_id = request.GET.get("category") or (qlist.category_id or "")
    topic = request.GET.get("topic", "")
    year = request.GET.get("year", "")
    sort = request.GET.get("sort", "desc")

    questions = Question.objects.select_related("question_bank__course__category")
    if category_id:
        questions = questions.filter(question_bank__course__category_id=category_id)
    if topic:
        questions = questions.filter(topic__icontains=topic)
    if year:
        questions = questions.filter(year=year)

    questions = questions.exclude(paper_code="")
    questions = (
        questions.order_by("-year", "-paper_code")
        if sort == "desc"
        else questions.order_by("year", "paper_code")
    )

    option_scope = Question.objects.exclude(paper_code="")
    if category_id:
        option_scope = option_scope.filter(
            question_bank__course__category_id=category_id
        )

    topics = sorted(
        {
            t.strip()
            for q in option_scope.values_list("topic", flat=True)
            for t in q.split(",")
            if t.strip()
        }
    )
    years = sorted(
        option_scope.exclude(year__isnull=True)
        .values_list("year", flat=True)
        .distinct(),
        reverse=True,
    )

    page_obj, per_page_label, per_page_choices = paginate(request, questions)

    selected_ids = set(
        QuestionListItem.objects.filter(question_list=qlist).values_list(
            "question_id", flat=True
        )
    )
    list_items = (
        QuestionListItem.objects.filter(question_list=qlist)
        .select_related("question")
        .order_by("order", "added_at")
    )

    context = {
        "qlist": qlist,
        "categories": categories,
        "questions": page_obj.object_list,
        "selected_ids": selected_ids,
        "list_items": list_items,
        "selected_count": list_items.count(),
        "total_marks": qlist.total_marks,
        "filters": {
            "category": str(category_id) if category_id else "",
            "topic": topic,
            "year": year,
            "sort": sort,
            "per_page": per_page_label,
        },
        "topics": topics,
        "years": years,
        "question_preview_data": _question_preview_map(page_obj.object_list),
        **pagination_context(request, page_obj, per_page_label, per_page_choices),
    }
    return render(request, "admin_panel/edit_question_list.html", context)


@admin_required
@require_POST
def question_list_toggle_question(request, list_id):
    """AJAX endpoint: add/remove a single question from a question list."""
    qlist = get_object_or_404(QuestionList, id=list_id, is_admin_curated=True)
    question_id = request.POST.get("question_id")
    question = get_object_or_404(Question, id=question_id)

    link = QuestionListItem.objects.filter(
        question_list=qlist, question=question
    ).first()
    if link:
        link.delete()
        added = False
    else:
        next_order = QuestionListItem.objects.filter(question_list=qlist).count()
        QuestionListItem.objects.create(
            question_list=qlist, question=question, order=next_order
        )
        added = True

    return JsonResponse(
        {
            "added": added,
            "selected_count": QuestionListItem.objects.filter(
                question_list=qlist
            ).count(),
            "total_marks": qlist.total_marks,
        }
    )


@admin_required
@require_POST
def question_list_reorder(request, list_id):
    """AJAX endpoint: persist drag-and-drop reordering."""
    qlist = get_object_or_404(QuestionList, id=list_id, is_admin_curated=True)
    try:
        ordered_ids = json.loads(request.body).get("question_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return HttpResponseBadRequest("Invalid payload")

    with transaction.atomic():
        for index, qid in enumerate(ordered_ids):
            QuestionListItem.objects.filter(
                question_list=qlist, question_id=qid
            ).update(order=index)

    return JsonResponse({"ok": True})


@admin_required
@require_POST
def delete_question_list(request, list_id):
    qlist = get_object_or_404(QuestionList, id=list_id, is_admin_curated=True)
    qlist.delete()
    messages.success(request, "Question list deleted.")
    return redirect("admin_panel:manage_question_lists")
