from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods
from datetime import datetime
import json
import random
import re
import logging

from .models import (
    Course,
    CourseCategory,
    Resource,
    Blog,
    Question,
    Exam,
    ExamQuestion,
    ExamAttempt,
    ExamAttemptAnswer,
    QuestionList,
    QuestionListItem,
    StudentProfile,
    DiscussionBoard,
    DiscussionPost,
    DiscussionReply,
    ContactMessage,
    PastPaper,
)

logger = logging.getLogger(__name__)
from .forms import StudentSignupForm, StudentLoginForm, StudentExamForm, StudentQuestionListForm
from .math_content import sanitize_math_content
from .question_preview import question_preview_map
from .pagination_utils import paginate, pagination_context


# ==================== HOME PAGE ====================
class HomeView(TemplateView):
    template_name = "courses/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CourseCategory.objects.all()
        context["featured_courses"] = Course.objects.all()[:6]
        return context


# ==================== COURSES ====================
class CoursesListView(TemplateView):
    template_name = "courses/courses_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CourseCategory.objects.all()
        context["courses"] = Course.objects.all()
        return context


class CourseDetailView(TemplateView):
    template_name = "courses/course_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get("course_id")
        context["course"] = get_object_or_404(Course, pk=course_id)
        return context


# ==================== RESOURCES ====================
class ResourcesView(TemplateView):
    template_name = "courses/resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["latest_resources"] = Resource.objects.filter(is_paid=False).order_by(
            "-id"
        )

        context["latest_paid_resources"] = Resource.objects.filter(
            is_paid=True
        ).order_by("-id")

        return context


class ResourceDetailView(DetailView):
    model = Resource
    template_name = "courses/resource_detail.html"
    context_object_name = "resource"

    def get_context_data(self, **kwargs):
        from django.urls import reverse
        from .resource_protection import (
            resource_preview_kind,
            docx_to_protected_html,
            text_file_to_protected_html,
        )

        context = super().get_context_data(**kwargs)
        resource = self.object
        try:
            kind = resource_preview_kind(resource)
        except Exception:
            logger.exception("resource_preview_kind failed for resource %s", resource.pk)
            kind = "unknown"
        context["preview_kind"] = kind
        context["preview_html"] = ""
        context["stream_url"] = ""
        try:
            if resource.file and getattr(resource.file, "name", None):
                context["stream_url"] = reverse(
                    "courses:resource_file_stream", kwargs={"pk": resource.pk}
                )
        except (ValueError, OSError):
            context["stream_url"] = ""
        try:
            if kind == "docx":
                context["preview_html"] = docx_to_protected_html(resource.file)
            elif kind == "text":
                context["preview_html"] = text_file_to_protected_html(resource.file)
        except Exception:
            logger.exception("Protected preview failed for resource %s", resource.pk)
            context["preview_html"] = (
                "<p class='rd-preview-error'>Preview temporarily unavailable.</p>"
            )
            context["preview_kind"] = "unknown"

        # Watermark identity for anti-screenshot overlay
        user = self.request.user
        who = (
            user.get_username()
            if getattr(user, "is_authenticated", False)
            else "guest"
        )
        context["ns_mark"] = (
            f"Study Nation · {who} · {timezone.localtime().strftime('%Y-%m-%d %H:%M')} · No Screenshot"
        )
        return context


class ResourcesListView(ListView):
    model = Resource
    template_name = "courses/resources_list.html"
    context_object_name = "resources"
    paginate_by = 12

    def get_queryset(self):
        queryset = Resource.objects.all().order_by("-created_at")

        # Filtering
        resource_type = self.request.GET.get("type")
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        is_paid = self.request.GET.get("is_paid")
        if is_paid == "free":
            queryset = queryset.filter(is_paid=False)
        elif is_paid == "paid":
            queryset = queryset.filter(is_paid=True)

        return queryset

    def get_context_data(self, **kwargs):
        from .resource_protection import resource_preview_kind

        context = super().get_context_data(**kwargs)
        # List page: never embed raw files (avoids browser download UI)
        for r in context["resources"]:
            r.preview_kind = resource_preview_kind(r)
        return context


def resource_file_stream(request, pk):
    """
    Stream a resource file for the protected on-page viewer only.
    Blocks top-level navigation / Save-as style access.
    Never used as a public download URL.
    """
    from django.http import FileResponse, Http404
    from .resource_protection import (
        is_top_level_file_navigation,
        forbidden_download_response,
        guess_content_type,
        resource_file_ext,
        PDF_EXTS,
        IMAGE_EXTS,
    )

    resource = get_object_or_404(Resource, pk=pk)
    if not resource.file:
        raise Http404("File not found")

    # Always reject clear download / new-tab navigation
    if is_top_level_file_navigation(request):
        return forbidden_download_response()

    # PDF.js and image tags load with Sec-Fetch-Dest empty/image — allowed.
    # Extra guard: reject query flag that looks like forced download
    if request.GET.get("download") in ("1", "true", "yes"):
        return forbidden_download_response()

    try:
        fh = resource.file.open("rb")
    except Exception as exc:
        raise Http404(str(exc)) from exc

    name = resource.file.name or "resource"
    content_type = guess_content_type(name)
    ext = resource_file_ext(resource)
    if ext in PDF_EXTS:
        content_type = "application/pdf"
    elif ext in IMAGE_EXTS and content_type == "application/octet-stream":
        content_type = "image/jpeg"

    response = FileResponse(fh, content_type=content_type)
    # Generic filename — do not advertise original download name
    response["Content-Disposition"] = 'inline; filename="view-only"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store, no-cache, must-revalidate"
    response["X-Robots-Tag"] = "noindex, noarchive, nosnippet"
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


# ==================== BLOG ====================
class BlogListView(ListView):
    model = Blog
    template_name = "courses/blogs_list.html"
    context_object_name = "blogs"
    paginate_by = 10

    def get_queryset(self):
        return Blog.objects.filter(published=True).order_by("-created_at")


class BlogDetailView(DetailView):
    model = Blog
    template_name = "courses/blog_detail.html"
    context_object_name = "blog"
    slug_field = "slug"


# ==================== OTHER PAGES ====================
class ContactView(View):
    """Public contact form — stores messages in the database."""

    template_name = "courses/contact.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        category = (request.POST.get("category") or "general").strip()
        message = (request.POST.get("message") or "").strip()

        valid_categories = {c[0] for c in ContactMessage.CATEGORY_CHOICES}
        if category not in valid_categories:
            category = "general"

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not subject:
            errors.append("Subject is required.")
        if not message:
            errors.append("Message is required.")
        if len(name) > 150:
            errors.append("Name is too long.")
        if len(subject) > 200:
            errors.append("Subject is too long.")
        if len(message) > 10000:
            errors.append("Message is too long.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(
                request,
                self.template_name,
                {
                    "form_data": {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "subject": subject,
                        "category": category,
                        "message": message,
                    }
                },
                status=400,
            )

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone[:40],
            subject=subject,
            category=category,
            message=message,
        )
        messages.success(
            request,
            "Thank you for your message! We will get back to you soon.",
        )
        return redirect("courses:contact")


class PastPapersView(TemplateView):
    """Public Past Papers browser: filter by category / subject / year,
    list full exam PDFs on the left, preview the selected PDF on the right.
    """

    template_name = "courses/past_papers.html"

    def get_context_data(self, **kwargs):
        from django.db import DatabaseError

        context = super().get_context_data(**kwargs)
        request = self.request

        try:
            published = PastPaper.objects.filter(is_published=True).select_related(
                "category"
            )
            # Force evaluation early so missing migrations surface as empty
            # state rather than mid-template 500s.
            _ = published.count()
        except DatabaseError:
            logger.exception("PastPaper query failed (run migrations on Render)")
            context.update(
                {
                    "categories": CourseCategory.objects.order_by("name"),
                    "subjects": [],
                    "years": [],
                    "papers": PastPaper.objects.none(),
                    "total_papers": 0,
                    "selected_paper": None,
                    "filter_category": "",
                    "filter_subject": "",
                    "filter_year": "",
                    "view_mode": "question",
                    "has_filters": False,
                    "db_error": True,
                }
            )
            return context

        # All DB categories for the browse strip + filter dropdown
        try:
            categories = CourseCategory.objects.order_by("name").annotate(
                paper_count=Count(
                    "past_papers",
                    filter=Q(past_papers__is_published=True),
                )
            )
        except DatabaseError:
            categories = CourseCategory.objects.order_by("name")

        subjects = (
            published.exclude(subject="")
            .values_list("subject", flat=True)
            .distinct()
            .order_by("subject")
        )
        years = published.values_list("year", flat=True).distinct().order_by("-year")

        category_id = (request.GET.get("category") or "").strip()
        subject = (request.GET.get("subject") or "").strip()
        year = (request.GET.get("year") or "").strip()
        paper_id = (request.GET.get("paper") or "").strip()
        view_mode = (request.GET.get("view") or "question").strip().lower()
        if view_mode not in ("question", "answer"):
            view_mode = "question"

        papers = published
        if category_id.isdigit():
            papers = papers.filter(category_id=int(category_id))
        if subject:
            papers = papers.filter(subject__iexact=subject)
        if year.isdigit():
            papers = papers.filter(year=int(year))

        papers = papers.order_by("-year", "subject", "title")

        selected_paper = None
        if paper_id.isdigit():
            selected_paper = papers.filter(pk=int(paper_id)).first()
            if selected_paper is None:
                # Allow opening a paper even if filters don't match (deep link)
                selected_paper = published.filter(pk=int(paper_id)).first()
        if selected_paper is None and papers.exists() and (
            category_id or subject or year
        ):
            # After applying filters, auto-select first paper for convenience
            selected_paper = papers.first()

        # Fall back to question PDF if answer sheet requested but missing
        if (
            selected_paper
            and view_mode == "answer"
            and not selected_paper.answer_pdf
        ):
            view_mode = "question"

        context.update(
            {
                "categories": categories,
                "subjects": list(subjects),
                "years": list(years),
                "papers": papers,
                "total_papers": published.count(),
                "selected_paper": selected_paper,
                "filter_category": category_id,
                "filter_subject": subject,
                "filter_year": year,
                "view_mode": view_mode,
                "has_filters": bool(category_id or subject or year or paper_id),
            }
        )
        return context


# ==================== UNIFIED AUTHENTICATION ====================
def _user_is_admin(user):
    """True if user has admin panel access (AdminUser profile or superuser)."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if hasattr(user, "admin_profile"):
        return True
    return bool(getattr(user, "is_superuser", False))


def _user_is_student(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and hasattr(user, "student_profile")
    )


def _user_can_access_portal(user):
    """Student portal + exam builder: students and admins both allowed."""
    return _user_is_student(user) or _user_is_admin(user)


def _ensure_admin_profile(user):
    """Create AdminUser for superusers who lack a profile; return profile or None."""
    if hasattr(user, "admin_profile"):
        return user.admin_profile
    if getattr(user, "is_superuser", False):
        from admin_panel.models import AdminUser

        profile, _ = AdminUser.objects.get_or_create(user=user)
        return profile
    return None


def _safe_next_url(request, next_url, *, is_admin=False, is_student=False):
    """Return next_url only if it is same-host and allowed for this role.

    Admins may open any same-host page (including student portal routes).
    Students may open student routes but not the admin panel.
    """
    if not next_url:
        return None
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return None

    path = next_url.split("?", 1)[0]
    if path.startswith("/admin-panel") and not is_admin:
        return None
    # Student-only areas are open to admins as well (full-site admin access)
    student_only = ("/my-exams", "/my-lists")
    if any(path.startswith(p) for p in student_only) and not (
        is_student or is_admin
    ):
        return None
    return next_url


def _default_post_login_redirect(user):
    """Admin → admin panel; student → user portal; else home."""
    if _user_is_admin(user):
        return reverse("admin_panel:dashboard")
    if _user_is_student(user):
        return reverse("courses:student_exams")
    return reverse("courses:home")


def student_signup(request):
    if request.user.is_authenticated and hasattr(request.user, "student_profile"):
        return redirect("courses:student_exams")
    if request.user.is_authenticated and _user_is_admin(request.user):
        return redirect("admin_panel:dashboard")

    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Study Nation, {user.first_name or user.username}!")
            return redirect("courses:student_exams")
    else:
        form = StudentSignupForm()

    return render(request, "courses/student_signup.html", {"form": form})


def student_login(request):
    """Single login form for both admin and student accounts.

    - Admin / superuser → admin panel dashboard
    - Student role → user portal (My Exams)
    """
    if request.user.is_authenticated:
        next_url = _safe_next_url(
            request,
            request.GET.get("next") or "",
            is_admin=_user_is_admin(request.user),
            is_student=_user_is_student(request.user),
        )
        if next_url:
            return redirect(next_url)
        return redirect(_default_post_login_redirect(request.user))

    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["username"].strip()
            password = form.cleaned_data["password"]

            # Allow logging in with either username or email
            username = identifier
            if "@" in identifier:
                user_match = User.objects.filter(email__iexact=identifier).first()
                if user_match:
                    username = user_match.username

            user = authenticate(request, username=username, password=password)
            if user is not None:
                is_admin = _user_is_admin(user)
                is_student = _user_is_student(user)

                if not is_admin and not is_student:
                    messages.error(
                        request,
                        "This account is not set up as a student or admin. "
                        "Please contact support.",
                    )
                else:
                    login(request, user)

                    if is_admin:
                        admin_profile = _ensure_admin_profile(user)
                        if admin_profile is not None:
                            admin_profile.last_login = timezone.now()
                            admin_profile.save(update_fields=["last_login"])

                    messages.success(
                        request,
                        f"Welcome back, {user.first_name or user.username}!",
                    )

                    next_url = _safe_next_url(
                        request,
                        request.GET.get("next") or request.POST.get("next") or "",
                        is_admin=is_admin,
                        is_student=is_student,
                    )
                    if next_url:
                        return redirect(next_url)

                    # Role-based default destinations
                    if is_admin:
                        return redirect("admin_panel:dashboard")
                    return redirect("courses:student_exams")
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = StudentLoginForm()

    return render(request, "courses/student_login.html", {"form": form})


def student_logout(request):
    logout(request)
    messages.success(request, "You've been logged out.")
    return redirect("courses:student_login")


def student_required(view_func):
    """Allow student portal views for students and admin-role users.

    Admins have full-site access (exam builder, practice, lists, etc.)
    in addition to the admin panel.
    """

    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        if not _user_can_access_portal(request.user):
            messages.error(
                request,
                "Please log in with a student or admin account to continue.",
            )
            return redirect("courses:student_login")
        # Ensure superusers always have an admin profile for panel + nav links
        if _user_is_admin(request.user):
            _ensure_admin_profile(request.user)
        return view_func(request, *args, **kwargs)

    return wrapped


# ==================== STUDENT EXAM BUILDER ====================
@student_required
def student_exams(request):
    """List of the logged-in student's own exams."""
    exams = Exam.objects.filter(created_by=request.user).select_related("category")
    return render(request, "courses/student_exams.html", {"exams": exams})


@student_required
def student_create_exam(request):
    """Creates a blank draft exam owned by the student and opens the builder."""
    default_category = CourseCategory.objects.first()
    exam = Exam.objects.create(
        name="My Practice Exam",
        category=default_category,
        created_by=request.user,
        status="draft",
    )
    return redirect("courses:student_edit_exam", exam_id=exam.id)


def _get_owned_exam_or_404(request, exam_id):
    return get_object_or_404(Exam, id=exam_id, created_by=request.user)


def _question_type_choices():
    """All question types available for the generate-paper form."""
    return list(Question.QUESTION_TYPES)


def _difficulty_choices():
    return [c for c in Question.DIFFICULTY_LEVELS if c[0]]


def _available_topics(category_ids=None):
    """Distinct topic labels from the question bank (comma-separated fields split)."""
    option_scope = Question.objects.all()
    ids = []
    if category_ids:
        if isinstance(category_ids, (list, tuple, set)):
            ids = [c for c in category_ids if c]
        else:
            ids = [category_ids]
    if ids:
        option_scope = option_scope.filter(
            question_bank__course__category_id__in=ids
        )
    raw_topics = option_scope.exclude(topic="").values_list("topic", flat=True)
    return sorted(
        {
            part.strip()
            for blob in raw_topics
            for part in (blob or "").split(",")
            if part.strip()
        }
    )


def _exam_builder_form_defaults(exam):
    return {
        "categories": [str(exam.category_id)] if exam.category_id else [],
        "topics": [],
        "question_types": [],
        "num_sections": 1,
        # Defaults used to pre-fill the first section type row
        "num_questions": 10,
        "difficulties": [],
    }


@student_required
def student_edit_exam(request, exam_id):
    """Student Exam Builder: generate a paper from filters, then practice it.

    Students no longer browse the full bank or preview answers here. They
    choose category / topic / sections (count + per-section difficulty),
    click Create Question Paper, and the paper appears under the My List tab.
    Correct answers are shown only after a practice attempt is submitted.
    """
    exam = _get_owned_exam_or_404(request, exam_id)

    if request.method == "POST" and "rename_exam" in request.POST:
        new_name = request.POST.get("name", "").strip()
        if new_name:
            exam.name = new_name
            exam.save(update_fields=["name", "updated_at"])
            messages.success(request, "Exam name updated.")
        return redirect("courses:student_edit_exam", exam_id=exam.id)

    exam_questions = (
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .order_by("order", "added_at")
    )
    settings_form = StudentExamForm(instance=exam)
    active_tab = request.GET.get("tab") or ""

    context = {
        "exam": exam,
        "categories": CourseCategory.objects.all(),
        "topics": _available_topics(
            [exam.category_id] if exam.category_id else None
        ),
        "question_types": _question_type_choices(),
        "difficulty_levels": _difficulty_choices(),
        "exam_questions": exam_questions,
        "selected_count": exam_questions.count(),
        "total_marks": exam.total_marks,
        "settings_form": settings_form,
        "practice_attempts": ExamAttempt.objects.filter(
            exam=exam, student=request.user
        )[:20],
        "active_tab": active_tab,
        "form_defaults": _exam_builder_form_defaults(exam),
        "max_sections": 5,
    }
    return render(request, "courses/student_edit_exam.html", context)


@student_required
@require_POST
def student_generate_exam_paper(request, exam_id):
    """Auto-build a paper from multi-select filters + per-section type counts.

    Top filters (multi): category, topic, question type.
    Per section: multi difficulty + how many questions of each type.
    """
    exam = _get_owned_exam_or_404(request, exam_id)

    category_ids = [
        c.strip() for c in request.POST.getlist("category") if (c or "").strip()
    ]
    topics = [t.strip() for t in request.POST.getlist("topic") if (t or "").strip()]
    question_types = [
        t.strip()
        for t in request.POST.getlist("question_type")
        if (t or "").strip()
    ]
    paper_name = (request.POST.get("paper_name") or "").strip()

    try:
        num_sections = int(request.POST.get("num_sections") or 1)
    except (TypeError, ValueError):
        num_sections = 1
    num_sections = max(1, min(num_sections, 5))

    valid_types = {t[0] for t in Question.QUESTION_TYPES}
    for qt in question_types:
        if qt not in valid_types:
            messages.error(request, "Invalid question type selected.")
            return redirect("courses:student_edit_exam", exam_id=exam.id)

    valid_diff = {d[0] for d in Question.DIFFICULTY_LEVELS if d[0]}

    # Parse per-section difficulties (multi) + per-type question counts
    sections = []
    for i in range(1, num_sections + 1):
        sec_diffs = [
            d.strip()
            for d in request.POST.getlist(f"section_{i}_difficulty")
            if (d or "").strip()
        ]
        for d in sec_diffs:
            if d not in valid_diff:
                messages.error(request, f"Invalid difficulty for section {i}.")
                return redirect(
                    f"{reverse('courses:student_edit_exam', args=[exam.id])}?tab=create"
                )

        type_counts = {}
        for tval, _label in Question.QUESTION_TYPES:
            try:
                n = int(request.POST.get(f"section_{i}_type_{tval}") or 0)
            except (TypeError, ValueError):
                n = 0
            n = max(0, min(n, 100))
            if n > 0:
                type_counts[tval] = n

        # Legacy fallback: plain section count (no type breakdown)
        if not type_counts:
            try:
                sec_count = int(request.POST.get(f"section_{i}_count") or 0)
            except (TypeError, ValueError):
                sec_count = 0
            sec_count = max(0, min(sec_count, 100))
            if sec_count > 0:
                type_counts = {"": sec_count}  # empty key = any type

        if type_counts:
            sections.append(
                {
                    "index": i,
                    "difficulties": sec_diffs,
                    "type_counts": type_counts,
                    "count": sum(type_counts.values()),
                }
            )

    # Backward-compatible fallback: single count/difficulty fields
    if not sections:
        try:
            num_questions = int(request.POST.get("num_questions") or 10)
        except (TypeError, ValueError):
            num_questions = 10
        num_questions = max(1, min(num_questions, 100))
        difficulty = (request.POST.get("difficulty") or "").strip()
        if difficulty and difficulty not in valid_diff:
            messages.error(request, "Invalid difficulty level selected.")
            return redirect(
                f"{reverse('courses:student_edit_exam', args=[exam.id])}?tab=create"
            )
        sections = [
            {
                "index": 1,
                "difficulties": [difficulty] if difficulty else [],
                "type_counts": {"": num_questions},
                "count": num_questions,
            }
        ]

    requested_total = sum(s["count"] for s in sections)
    if requested_total < 1:
        messages.error(
            request,
            "Please set at least one question (pick a type count under each section).",
        )
        return redirect(
            f"{reverse('courses:student_edit_exam', args=[exam.id])}?tab=create"
        )

    base_qs = Question.objects.select_related("question_bank__course__category")

    if category_ids:
        base_qs = base_qs.filter(
            question_bank__course__category_id__in=category_ids
        )
        try:
            exam.category_id = int(category_ids[0])
        except (TypeError, ValueError):
            pass

    if topics:
        topic_q = Q()
        for t in topics:
            topic_q |= Q(topic__icontains=t)
        base_qs = base_qs.filter(topic_q)

    # Global type multi-select narrows which types can be picked
    if question_types:
        base_qs = base_qs.filter(question_type__in=question_types)

    # Treat closely related type keys as interchangeable so counts fill better
    type_aliases = {
        "multiple_choice": ("multiple_choice", "mcq"),
        "mcq": ("mcq", "multiple_choice"),
        "single_choice": ("single_choice", "mcq", "multiple_choice"),
        "numerical": ("numerical", "integer"),
        "integer": ("integer", "numerical"),
        "comprehension": ("comprehension", "structured"),
        "structured": ("structured", "comprehension"),
    }

    selected_ids = []
    used_ids = set()
    shortfalls = []

    for sec in sections:
        for qtype, want in sec["type_counts"].items():
            qs = base_qs
            if qtype:
                type_keys = type_aliases.get(qtype, (qtype,))
                qs = qs.filter(question_type__in=type_keys)
            if sec["difficulties"]:
                qs = qs.filter(
                    Q(difficulty_level__in=sec["difficulties"])
                    | Q(question_bank__difficulty__in=sec["difficulties"])
                )
            if used_ids:
                qs = qs.exclude(id__in=used_ids)

            candidate_ids = list(qs.values_list("id", flat=True))
            type_label = (
                dict(Question.QUESTION_TYPES).get(qtype, "Any type")
                if qtype
                else "Any type"
            )
            if not candidate_ids:
                shortfalls.append(
                    f"Section {sec['index']} · {type_label}: 0 of {want}"
                )
                continue

            # Always take as many as available (never fail the whole paper)
            pick = min(want, len(candidate_ids))
            picked = random.sample(candidate_ids, pick)
            selected_ids.extend(picked)
            used_ids.update(picked)
            if pick < want:
                shortfalls.append(
                    f"Section {sec['index']} · {type_label}: {pick} of {want}"
                )

    # Still create the paper whenever we have at least 1 matching question
    if not selected_ids:
        messages.error(
            request,
            "No questions match those filters, so the paper could not be "
            "created. Try other categories, topics, types, or difficulties.",
        )
        return redirect(
            f"{reverse('courses:student_edit_exam', args=[exam.id])}?tab=create"
        )

    pick_count = len(selected_ids)

    if paper_name:
        exam.name = paper_name[:200]
    elif exam.name in ("", "My Practice Exam"):
        cat_name = ""
        if exam.category_id:
            cat = CourseCategory.objects.filter(pk=exam.category_id).first()
            cat_name = cat.name if cat else ""
        if len(category_ids) > 1:
            cat_name = f"{cat_name}+" if cat_name else "Multi"
        type_label = "Mixed"
        if len(question_types) == 1:
            type_label = dict(Question.QUESTION_TYPES).get(
                question_types[0], "Mixed"
            )
        topic_bit = f" · {topics[0]}" if len(topics) == 1 else (
            f" · {len(topics)} topics" if topics else ""
        )
        sec_bit = f" · {num_sections} sec" if num_sections > 1 else ""
        exam.name = (
            f"{cat_name or 'Mixed'}{topic_bit} · {type_label} · "
            f"{pick_count}Q{sec_bit}"
        )[:200]

    with transaction.atomic():
        exam.save()
        ExamQuestion.objects.filter(exam=exam).delete()
        ExamQuestion.objects.bulk_create(
            [
                ExamQuestion(exam=exam, question_id=qid, order=index)
                for index, qid in enumerate(selected_ids)
            ]
        )

    # Always keep the paper; tell the user clearly when some counts were short
    if shortfalls or pick_count < requested_total:
        detail = "; ".join(shortfalls[:8]) if shortfalls else (
            f"{pick_count} of {requested_total} available in the bank"
        )
        if shortfalls and len(shortfalls) > 8:
            detail += f"; +{len(shortfalls) - 8} more"
        messages.success(
            request,
            f"✅ Exam created with {pick_count} available question(s) "
            f"(you asked for {requested_total}). "
            f"Not enough matching questions for: {detail}. "
            f"Open My List to review or Practice when ready.",
        )
    else:
        sec_msg = (
            f" across {num_sections} section(s)" if num_sections > 1 else ""
        )
        messages.success(
            request,
            f"✅ Question paper created with {pick_count} question(s){sec_msg}. "
            f"Open the My List tab to review, then Practice when ready.",
        )

    return redirect(
        f"{reverse('courses:student_edit_exam', args=[exam.id])}?tab=list"
    )


@student_required
def student_exam_toggle_question(request, exam_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    exam = _get_owned_exam_or_404(request, exam_id)
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


@student_required
def student_exam_reorder_questions(request, exam_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    exam = _get_owned_exam_or_404(request, exam_id)
    try:
        ordered_ids = json.loads(request.body).get("question_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return HttpResponseBadRequest("Invalid payload")

    with transaction.atomic():
        for index, qid in enumerate(ordered_ids):
            ExamQuestion.objects.filter(exam=exam, question_id=qid).update(order=index)

    return JsonResponse({"ok": True})


@student_required
def student_exam_settings(request, exam_id):
    exam = _get_owned_exam_or_404(request, exam_id)
    if request.method == "POST":
        form = StudentExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam settings saved.")
            return redirect("courses:student_exam_settings", exam_id=exam.id)
    else:
        form = StudentExamForm(instance=exam)

    exam_questions = (
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .order_by("order", "added_at")
    )
    return render(
        request,
        "courses/student_edit_exam.html",
        {
            "exam": exam,
            "settings_form": form,
            "active_tab": "settings",
            "categories": CourseCategory.objects.all(),
            "topics": _available_topics(
                [exam.category_id] if exam.category_id else None
            ),
            "question_types": _question_type_choices(),
            "difficulty_levels": _difficulty_choices(),
            "exam_questions": exam_questions,
            "selected_count": exam_questions.count(),
            "total_marks": exam.total_marks,
            "practice_attempts": ExamAttempt.objects.filter(
                exam=exam, student=request.user
            )[:20],
            "form_defaults": _exam_builder_form_defaults(exam),
            "max_sections": 5,
        },
    )


@student_required
@require_POST
def student_delete_exam(request, exam_id):
    exam = _get_owned_exam_or_404(request, exam_id)
    exam.delete()
    messages.success(request, "Exam deleted.")
    return redirect("courses:student_exams")


# ==================== STUDENT: PRACTICE THIS EXAM ====================
def _normalize_free_text(value: str) -> str:
    """Normalize free-text answers for more reliable auto-grading."""
    text = (value or "").strip().lower()
    # Unify unicode dashes/quotes common in pasted answers
    text = (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Drop trailing punctuation that rarely changes meaning
    text = text.rstrip(" .;,:")
    return text


def _resolve_correct_answer_key(question) -> str:
    """Best-effort answer key: correct_answer field, then dynamic options."""
    correct = (getattr(question, "correct_answer", None) or "").strip()
    if correct:
        return correct

    # Dynamic QuestionOption rows (wizard / mcq)
    try:
        opts = list(question.options.all())
    except Exception:
        opts = []
    if opts:
        ordered = sorted(opts, key=lambda o: (o.order, o.id))
        letters = [
            chr(65 + i)
            for i, o in enumerate(ordered)
            if getattr(o, "is_correct", False)
        ]
        if letters:
            return ",".join(letters)

    return ""


def _is_choice_question(question) -> bool:
    qtype = (question.question_type or "").lower()
    if qtype in (
        "single_choice",
        "multiple_choice",
        "true_false",
        "mcq",
        "comprehension",
    ):
        return True
    # Legacy banks may use option_a..d even with odd type labels
    if any(
        [
            question.option_a,
            question.option_b,
            question.option_c,
            question.option_d,
        ]
    ):
        return True
    try:
        return question.options.exists()
    except Exception:
        return False


def _is_multi_answer_question(question) -> bool:
    qtype = (question.question_type or "").lower()
    if qtype == "multiple_choice":
        return True
    return (getattr(question, "answer_type", "") or "").lower() == "multiple"


def _grade_answer(question, given):
    """
    Best-effort auto-grading for a single question's submitted answer.
    Returns (is_correct, marks_awarded):
      - is_correct = None   -> left blank (counts as "unanswered", not wrong)
      - is_correct = True/False -> counts as correct/wrong

    Choice questions (A/B/C/D or dynamic options) match by letter set.
    If an answer was given but no key exists, it is graded wrong (not unanswered).
    """
    given = (given or "").strip()
    if not given:
        return None, 0

    correct = _resolve_correct_answer_key(question)
    marks = float(question.marks or 0)
    qtype = (question.question_type or "").lower()

    if not correct:
        # Student answered, but this question has no answer key yet.
        # Must NOT count as unanswered (that was the practice bug).
        return False, 0

    if _is_choice_question(question) or qtype in (
        "single_choice",
        "true_false",
        "mcq",
        "comprehension",
        "multiple_choice",
    ):
        given_set = {x.strip().upper() for x in re.split(r"[,;\s]+", given) if x.strip()}
        correct_set = {
            x.strip().upper() for x in re.split(r"[,;\s]+", correct) if x.strip()
        }
        # Single-letter answers often arrive as "C"
        if not _is_multi_answer_question(question) and len(given_set) == 1:
            is_correct = given_set == correct_set or given.upper() == correct.upper()
        else:
            is_correct = bool(given_set) and given_set == correct_set
        return is_correct, (marks if is_correct else 0)

    if qtype in ("numerical", "integer"):
        try:
            tol = float(getattr(question, "numeric_tolerance", None) or 1e-6)
            is_correct = abs(float(given) - float(correct)) <= max(tol, 1e-9)
        except (TypeError, ValueError):
            is_correct = _normalize_free_text(given) == _normalize_free_text(correct)
        return is_correct, (marks if is_correct else 0)

    # structured, matching, fill_blank, free text, etc.
    given_n = _normalize_free_text(given)
    correct_n = _normalize_free_text(correct)
    is_correct = given_n == correct_n
    if not is_correct and "||" in correct:
        alts = {_normalize_free_text(a) for a in correct.split("||") if a.strip()}
        is_correct = given_n in alts
    return is_correct, (marks if is_correct else 0)


@student_required
def student_practice_start(request, exam_id):
    """Renders the actual timed quiz-taking screen for this exam's selected
    questions. Every question type gets an answer input (lettered buttons
    for choice-based questions, a text box for numerical/structured/
    matching) — all auto-graded on submit, on a best-effort basis for the
    free-text types."""
    exam = _get_owned_exam_or_404(request, exam_id)
    exam_questions = (
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .prefetch_related("question__options")
        .order_by("order", "added_at")
    )
    if not exam_questions.exists():
        messages.error(request, "Add some questions to this exam before practicing.")
        return redirect("courses:student_edit_exam", exam_id=exam.id)

    # Server-authoritative start time (not trustable from the client alone)
    started_at = timezone.now()
    request.session[f"practice_start_{exam.id}"] = started_at.isoformat()
    request.session.modified = True

    return render(
        request,
        "courses/student_practice_quiz.html",
        {
            "exam": exam,
            "exam_questions": exam_questions,
            "started_at_iso": started_at.isoformat(),
        },
    )


@student_required
@require_POST
def student_practice_submit(request, exam_id):
    """Grades the submitted answers and records an ExamAttempt."""
    exam = _get_owned_exam_or_404(request, exam_id)
    exam_questions = list(
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .prefetch_related("question__options")
        .order_by("order", "added_at")
    )
    if not exam_questions:
        messages.error(request, "This exam has no questions to grade.")
        return redirect("courses:student_edit_exam", exam_id=exam.id)

    session_key = f"practice_start_{exam.id}"
    started_at = None
    started_at_session = request.session.pop(session_key, None)
    if started_at_session:
        try:
            started_at = datetime.fromisoformat(started_at_session)
            if timezone.is_naive(started_at):
                started_at = timezone.make_aware(started_at)
        except (TypeError, ValueError):
            started_at = None

    # Fall back to POST value only if session missing (tab restore); still clamp
    if started_at is None:
        started_at_raw = request.POST.get("started_at")
        try:
            started_at = datetime.fromisoformat(started_at_raw)
            if timezone.is_naive(started_at):
                started_at = timezone.make_aware(started_at)
        except (TypeError, ValueError):
            started_at = timezone.now()

    submitted_at = timezone.now()
    # Never allow a client clock in the future or absurdly long sessions (> 12h)
    if started_at > submitted_at:
        started_at = submitted_at
    time_taken = max(0, min(int((submitted_at - started_at).total_seconds()), 12 * 3600))

    with transaction.atomic():
        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=request.user,
            started_at=started_at,
            time_taken_seconds=time_taken,
            total_questions=len(exam_questions),
        )

        correct = wrong = unanswered = 0
        marks_scored = 0.0
        total_marks = 0.0
        answer_rows = []
        for eq in exam_questions:
            q = eq.question
            total_marks += float(q.marks or 0)
            given = request.POST.get(f"answer_{q.id}", "").strip()
            is_correct, marks = _grade_answer(q, given)
            if is_correct is None:
                unanswered += 1
            elif is_correct:
                correct += 1
                marks_scored += marks
            else:
                wrong += 1
            answer_rows.append(
                ExamAttemptAnswer(
                    attempt=attempt,
                    question=q,
                    given_answer=given,
                    is_correct=is_correct,
                    marks_awarded=marks,
                )
            )
        ExamAttemptAnswer.objects.bulk_create(answer_rows)

        attempt.correct_count = correct
        attempt.wrong_count = wrong
        attempt.unanswered_count = unanswered
        attempt.total_marks = total_marks
        attempt.marks_scored = marks_scored
        attempt.save()

    return redirect("courses:student_practice_result", exam_id=exam.id, attempt_id=attempt.id)


@student_required
def student_practice_result(request, exam_id, attempt_id):
    exam = _get_owned_exam_or_404(request, exam_id)
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, exam=exam, student=request.user)
    answers = list(
        ExamAttemptAnswer.objects.filter(attempt=attempt)
        .select_related("question")
        .prefetch_related("question__options")
        .order_by("id")
    )

    # Attach resolved answer keys for display (legacy empty correct_answer)
    for ans in answers:
        ans.display_correct = _resolve_correct_answer_key(ans.question) or (
            ans.question.correct_answer or ""
        )

    chart_data = {
        "correct": attempt.correct_count,
        "wrong": attempt.wrong_count,
        "unanswered": attempt.unanswered_count,
        "score_percent": attempt.score_percent,
        "marks_scored": attempt.marks_scored,
        "total_marks": attempt.total_marks,
        "time_taken_seconds": attempt.time_taken_seconds,
    }

    return render(
        request,
        "courses/student_practice_result.html",
        {
            "exam": exam,
            "attempt": attempt,
            "answers": answers,
            "chart_data": chart_data,
        },
    )


# ==================== STUDENT: BUILD QUESTION LIST ====================
@student_required
def student_question_lists(request):
    """List of the logged-in student's own question lists."""
    lists = QuestionList.objects.filter(
        created_by=request.user, is_admin_curated=False
    ).select_related("category")
    return render(request, "courses/student_question_lists.html", {"lists": lists})


@student_required
def student_create_question_list(request):
    """Creates a blank question list owned by the student and opens the builder."""
    default_category = CourseCategory.objects.first()
    qlist = QuestionList.objects.create(
        name="My Question List",
        category=default_category,
        created_by=request.user,
        is_admin_curated=False,
    )
    return redirect("courses:student_edit_question_list", list_id=qlist.id)


def _get_owned_question_list_or_404(request, list_id):
    return get_object_or_404(
        QuestionList, id=list_id, created_by=request.user, is_admin_curated=False
    )


@student_required
def student_edit_question_list(request, list_id):
    """
    Simplified question-browsing builder: filter the question bank and save
    a named, ordered list to the student's account. No timer/settings/export
    — just Select Questions and Selected Questions.
    Filters: Topic(s), Year(s), Type (Category) + Submit. Questions are
    pulled live from the database.
    """
    qlist = _get_owned_question_list_or_404(request, list_id)

    if request.method == "POST" and "rename_list" in request.POST:
        new_name = request.POST.get("name", "").strip()
        if new_name:
            qlist.name = new_name
            qlist.save(update_fields=["name", "updated_at"])
            messages.success(request, "List name updated.")
        return redirect("courses:student_edit_question_list", list_id=qlist.id)

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
        option_scope = option_scope.filter(question_bank__course__category_id=category_id)

    # Single values_list query then split in Python (avoids N+1 ORM hits)
    raw_topics = option_scope.exclude(topic="").values_list("topic", flat=True)
    topics = sorted(
        {
            part.strip()
            for blob in raw_topics
            for part in (blob or "").split(",")
            if part.strip()
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
        QuestionListItem.objects.filter(question_list=qlist).values_list("question_id", flat=True)
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
        "question_preview_data": question_preview_map(page_obj.object_list),
        **pagination_context(request, page_obj, per_page_label, per_page_choices),
    }
    return render(request, "courses/student_edit_question_list.html", context)


@student_required
def student_question_list_toggle_question(request, list_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    qlist = _get_owned_question_list_or_404(request, list_id)
    question_id = request.POST.get("question_id")
    question = get_object_or_404(Question, id=question_id)

    link = QuestionListItem.objects.filter(question_list=qlist, question=question).first()
    if link:
        link.delete()
        added = False
    else:
        next_order = QuestionListItem.objects.filter(question_list=qlist).count()
        QuestionListItem.objects.create(question_list=qlist, question=question, order=next_order)
        added = True

    return JsonResponse(
        {
            "added": added,
            "selected_count": QuestionListItem.objects.filter(question_list=qlist).count(),
            "total_marks": qlist.total_marks,
        }
    )


@student_required
def student_question_list_reorder(request, list_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    qlist = _get_owned_question_list_or_404(request, list_id)
    try:
        ordered_ids = json.loads(request.body).get("question_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return HttpResponseBadRequest("Invalid payload")

    with transaction.atomic():
        for index, qid in enumerate(ordered_ids):
            QuestionListItem.objects.filter(question_list=qlist, question_id=qid).update(order=index)

    return JsonResponse({"ok": True})


@student_required
@require_POST
def student_delete_question_list(request, list_id):
    qlist = _get_owned_question_list_or_404(request, list_id)
    qlist.delete()
    messages.success(request, "Question list deleted.")
    return redirect("courses:student_question_lists")


def _clean_video_solution_url(raw: str | None) -> str:
    """Normalize optional video solution links. Empty string when blank/invalid."""
    url = (raw or "").strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    # Light validation: must look like a URL host path
    if not re.match(r"^https?://[^\s]+$", url, re.IGNORECASE):
        return ""
    return url[:500]


# ==================== QUESTION FORUM (DISCUSSION BOARDS) ====================
class QuestionForumView(TemplateView):
    """Dedicated Question Forum page: sidebar of topic boards + a feed of
    questions (each with its own reply thread) for the selected board.
    """

    template_name = "courses/question_forum.html"

    def get_context_data(self, **kwargs):
        from django.db import DatabaseError

        context = super().get_context_data(**kwargs)
        context["sort"] = "hot"
        context["boards"] = []
        context["active_board"] = None
        context["posts"] = []
        context["qf_error"] = None

        try:
            boards = list(DiscussionBoard.objects.all())
            context["boards"] = boards

            board_slug = (self.request.GET.get("board") or "").strip()
            active_board = None
            if board_slug:
                active_board = next(
                    (b for b in boards if b.slug == board_slug), None
                )
            if not active_board and boards:
                active_board = boards[0]
            context["active_board"] = active_board

            posts_qs = DiscussionPost.objects.select_related(
                "user", "board"
            ).prefetch_related("replies__user")
            if active_board:
                posts_qs = posts_qs.filter(board=active_board)

            sort = (self.request.GET.get("view") or "hot").strip()
            if sort == "new":
                posts_qs = posts_qs.order_by("-created_at")
            else:
                sort = "hot"
                # "Hot" = most replies first, then most recent
                posts_qs = posts_qs.annotate(
                    reply_count=Count("replies")
                ).order_by("-reply_count", "-created_at")

            # Force evaluation here so template does not raise mid-render
            context["posts"] = list(posts_qs[:100])
            context["sort"] = sort
        except DatabaseError:
            logger.exception(
                "Question Forum DB error — run migrate / ensure_schema on Render"
            )
            context["qf_error"] = (
                "Question Forum is updating. Please try again in a minute."
            )
            context["boards"] = []
            context["active_board"] = None
            context["posts"] = []
        except Exception:
            logger.exception("Question Forum unexpected error")
            context["qf_error"] = (
                "Something went wrong loading questions. Please refresh."
            )
            context["boards"] = []
            context["active_board"] = None
            context["posts"] = []

        return context


# Backward-compatible aliases
QuestionFormView = QuestionForumView
PublicChatView = QuestionForumView


@login_required
def discussion_create_post(request):
    """Logged-in users submit a new question via the Question Forum.

    Each question becomes its own thread with replies. An optional image
    can be attached. After posting, the user returns to the Question Forum
    page on the correct board with the new question visible.
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = sanitize_math_content(request.POST.get("content", ""))
        board_id = request.POST.get("board", "").strip()
        image = request.FILES.get("image")
        # Normal users may attach optional video solution links only on Question Forum
        video_solution_url = _clean_video_solution_url(
            request.POST.get("video_solution_url")
        )

        board = DiscussionBoard.objects.filter(pk=board_id).first() if board_id else None

        if title and content:
            post = DiscussionPost.objects.create(
                user=request.user,
                board=board,
                title=title,
                content=content,
                image=image,
                video_solution_url=video_solution_url,
            )
            messages.success(
                request, "✅ Your question has been submitted!"
            )
            redirect_url = reverse("courses:question_forum")
            params = f"open={post.id}"
            if board:
                params += f"&board={board.slug}"
            return redirect(f"{redirect_url}?{params}#post-{post.id}")
        else:
            messages.error(request, "Title and question details are required.")

        redirect_url = reverse("courses:question_forum")
        if board:
            return redirect(f"{redirect_url}?board={board.slug}")
        return redirect(redirect_url)

    return redirect("courses:question_forum")


def _question_forum_redirect(post, fragment=""):
    """Return to the Question Forum page, focused on the given question."""
    redirect_url = reverse("courses:question_forum")
    params = f"open={post.id}"
    if post.board:
        params += f"&board={post.board.slug}"
    anchor = fragment or f"post-{post.id}"
    return redirect(f"{redirect_url}?{params}#{anchor}")


# Backward-compatible aliases
_question_form_redirect = _question_forum_redirect
_public_chat_redirect = _question_forum_redirect


@login_required
def discussion_add_reply(request, post_id):
    """Logged-in users reply to a specific question on the Question Forum.

    `post_id` identifies exactly which question is being replied to, so a
    reply always lands on the question the user selected. An optional image
    can be attached.
    """
    post = get_object_or_404(DiscussionPost, pk=post_id)
    if request.method == "POST":
        content = sanitize_math_content(request.POST.get("content", ""))
        image = request.FILES.get("image")
        video_solution_url = _clean_video_solution_url(
            request.POST.get("video_solution_url")
        )
        if content or image or video_solution_url:
            DiscussionReply.objects.create(
                post=post,
                user=request.user,
                content=content,
                image=image,
                video_solution_url=video_solution_url,
            )
            messages.success(request, "✅ Your reply has been added!")
        else:
            messages.error(
                request, "Write something, attach an image, or add a video solution link."
            )

    return _question_forum_redirect(post)


@login_required
def discussion_edit_reply(request, reply_id):
    """Author can edit the text (and optional image) of their own reply."""
    reply = get_object_or_404(DiscussionReply, pk=reply_id)
    post = reply.post

    if reply.user_id != request.user.id:
        messages.error(request, "You can only edit your own replies.")
        return _question_forum_redirect(post, f"reply-{reply.id}")

    if request.method != "POST":
        return _question_forum_redirect(post, f"reply-{reply.id}")

    content = sanitize_math_content(request.POST.get("content", ""))
    image = request.FILES.get("image")
    clear_image = request.POST.get("clear_image") == "1"
    video_solution_url = _clean_video_solution_url(
        request.POST.get("video_solution_url")
    )

    has_image = bool(image) or (bool(reply.image) and not clear_image)
    if not content and not has_image and not video_solution_url:
        messages.error(
            request, "Write something, keep/attach an image, or add a video solution link."
        )
        return _question_forum_redirect(post, f"reply-{reply.id}")

    reply.content = content
    reply.video_solution_url = video_solution_url
    if clear_image and reply.image:
        reply.image.delete(save=False)
        reply.image = None
    if image:
        reply.image = image
    reply.save()
    messages.success(request, "✅ Your reply has been updated.")
    return _question_forum_redirect(post, f"reply-{reply.id}")


@login_required
@require_POST
def discussion_delete_reply(request, reply_id):
    """Author can permanently delete their own reply."""
    reply = get_object_or_404(DiscussionReply, pk=reply_id)
    post = reply.post

    if reply.user_id != request.user.id:
        messages.error(request, "You can only delete your own replies.")
        return _question_forum_redirect(post)

    if reply.image:
        reply.image.delete(save=False)
    reply.delete()
    messages.success(request, "🗑️ Your reply has been deleted.")
    return _question_forum_redirect(post)
