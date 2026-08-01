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
    template_name = "courses/past_papers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam_boards"] = [
            {"name": "Cambridge IGCSE", "icon": "fi-sr-graduation-cap"},
            {"name": "Edexcel International GCSE", "icon": "fi-sr-diploma"},
            {"name": "Cambridge A Level", "icon": "fi-sr-book-open"},
            {"name": "Edexcel IAL", "icon": "fi-sr-document"},
            {"name": "IB (International Baccalaureate)", "icon": "fi-sr-globe"},
            {"name": "AQA", "icon": "fi-sr-clipboard"},
            {"name": "OCR", "icon": "fi-sr-pen"},
        ]
        context["subjects"] = [
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "English",
            "Computer Science",
            "Economics",
            "History",
            "Geography",
            "Business Studies",
            "Literature",
            "Art & Design",
        ]
        context["question_types"] = [
            "SINGLE",
            "MULTIPLE",
            "NUMERICAL",
            "TRUE_FALSE",
            "MATCHING",
        ]
        return context


# ==================== STUDENT AUTHENTICATION ====================
def student_signup(request):
    if request.user.is_authenticated and hasattr(request.user, "student_profile"):
        return redirect("courses:student_exams")

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
    if request.user.is_authenticated and hasattr(request.user, "student_profile"):
        return redirect("courses:student_exams")

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
            if user is not None and hasattr(user, "student_profile"):
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next") or request.POST.get("next") or ""
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect("courses:student_exams")
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = StudentLoginForm()

    return render(request, "courses/student_login.html", {"form": form})


def student_logout(request):
    logout(request)
    messages.success(request, "You've been logged out.")
    return redirect("courses:past_papers")


def student_required(view_func):
    """Decorator ensuring the user is logged in with a student profile."""

    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        if not hasattr(request.user, "student_profile"):
            messages.error(request, "Please log in with a student account to continue.")
            return redirect("courses:student_login")
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


@student_required
def student_edit_exam(request, exam_id):
    """
    Student-facing Exam Builder (mirrors the admin builder, scoped to the
    logged-in student's own exam, with no enrollment restriction on which
    questions can be browsed).
    Filters: Topic(s), Year(s), Type (Category) + Submit. Questions are
    pulled live from the database.
    """
    exam = _get_owned_exam_or_404(request, exam_id)

    if request.method == "POST" and "rename_exam" in request.POST:
        new_name = request.POST.get("name", "").strip()
        if new_name:
            exam.name = new_name
            exam.save(update_fields=["name", "updated_at"])
            messages.success(request, "Exam name updated.")
        return redirect("courses:student_edit_exam", exam_id=exam.id)

    categories = CourseCategory.objects.all()

    category_id = request.GET.get("category") or (exam.category_id or "")
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
        ExamQuestion.objects.filter(exam=exam).values_list("question_id", flat=True)
    )
    exam_questions = (
        ExamQuestion.objects.filter(exam=exam)
        .select_related("question")
        .order_by("order", "added_at")
    )

    settings_form = StudentExamForm(instance=exam)

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
        "practice_attempts": ExamAttempt.objects.filter(exam=exam, student=request.user)[:20],
        "question_preview_data": question_preview_map(page_obj.object_list),
        **pagination_context(request, page_obj, per_page_label, per_page_choices),
    }
    return render(request, "courses/student_edit_exam.html", context)


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

    return render(
        request,
        "courses/student_edit_exam.html",
        {
            "exam": exam,
            "settings_form": form,
            "active_tab": "settings",
            "categories": CourseCategory.objects.all(),
            "exam_questions": ExamQuestion.objects.filter(exam=exam).select_related("question"),
            "selected_count": ExamQuestion.objects.filter(exam=exam).count(),
            "total_marks": exam.total_marks,
            "practice_attempts": ExamAttempt.objects.filter(exam=exam, student=request.user)[:20],
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


def _grade_answer(question, given):
    """
    Best-effort auto-grading for a single question's submitted answer.
    Returns (is_correct, marks_awarded):
      - is_correct = None   -> left blank (counts as "unanswered", not wrong)
      - is_correct = True/False -> counts as correct/wrong

    single_choice / true_false : exact letter match (case-insensitive)
    multiple_choice            : exact set-of-letters match, comma-separated
    numerical                  : numeric match with small tolerance, falls
                                  back to exact text if not parseable as a number
    structured / matching      : normalized free-text match (case/whitespace/
                                  light punctuation tolerant)
    """
    given = (given or "").strip()
    correct = (question.correct_answer or "").strip()

    if not given:
        return None, 0

    if not correct:
        # No answer key on file for this question — can't grade it, but it
        # was answered, so don't count it as wrong either.
        return None, 0

    qtype = question.question_type
    marks = float(question.marks or 0)

    if qtype in ("single_choice", "true_false"):
        is_correct = given.upper() == correct.upper()
    elif qtype == "multiple_choice":
        given_set = {x.strip().upper() for x in given.split(",") if x.strip()}
        correct_set = {x.strip().upper() for x in correct.split(",") if x.strip()}
        is_correct = bool(given_set) and given_set == correct_set
    elif qtype == "numerical":
        try:
            # Prefer question numeric_tolerance when set
            tol = float(getattr(question, "numeric_tolerance", None) or 1e-6)
            is_correct = abs(float(given) - float(correct)) <= max(tol, 1e-9)
        except (TypeError, ValueError):
            is_correct = _normalize_free_text(given) == _normalize_free_text(correct)
    else:  # structured, matching, fill_blank, etc.
        given_n = _normalize_free_text(given)
        correct_n = _normalize_free_text(correct)
        is_correct = given_n == correct_n
        # Accept any of several correct alternatives separated by "||"
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
        ExamQuestion.objects.filter(exam=exam).select_related("question").order_by("order", "added_at")
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
    answers = (
        ExamAttemptAnswer.objects.filter(attempt=attempt)
        .select_related("question")
        .order_by("id")
    )
    return render(
        request,
        "courses/student_practice_result.html",
        {"exam": exam, "attempt": attempt, "answers": answers},
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


# ==================== QUESTION FORM (DISCUSSION BOARDS) ====================
class QuestionFormView(TemplateView):
    """Dedicated Question Form page: sidebar of topic boards + a feed of
    questions (each with its own reply thread) for the selected board.
    """

    template_name = "courses/question_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        boards = DiscussionBoard.objects.all()
        context["boards"] = boards

        board_slug = self.request.GET.get("board", "").strip()
        active_board = None
        if board_slug:
            active_board = boards.filter(slug=board_slug).first()
        if not active_board:
            active_board = boards.first()
        context["active_board"] = active_board

        posts_qs = DiscussionPost.objects.select_related("user", "board").prefetch_related(
            "replies__user"
        )
        if active_board:
            posts_qs = posts_qs.filter(board=active_board)

        sort = self.request.GET.get("view", "hot")
        if sort == "new":
            posts_qs = posts_qs.order_by("-created_at")
        else:
            sort = "hot"
            # "Hot" = most replies first, then most recent
            posts_qs = posts_qs.annotate(reply_count=Count("replies")).order_by(
                "-reply_count", "-created_at"
            )

        context["posts"] = posts_qs
        context["sort"] = sort
        return context


# Backward-compatible alias
PublicChatView = QuestionFormView


@login_required
def discussion_create_post(request):
    """Logged-in users submit a new question via the Question Form.

    Each question becomes its own thread with replies. An optional image
    can be attached. After posting, the user returns to the Question Form
    page on the correct board with the new question visible.
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = sanitize_math_content(request.POST.get("content", ""))
        board_id = request.POST.get("board", "").strip()
        image = request.FILES.get("image")

        board = DiscussionBoard.objects.filter(pk=board_id).first() if board_id else None

        if title and content:
            post = DiscussionPost.objects.create(
                user=request.user,
                board=board,
                title=title,
                content=content,
                image=image,
            )
            messages.success(
                request, "✅ Your question has been submitted!"
            )
            redirect_url = reverse("courses:question_form")
            params = f"open={post.id}"
            if board:
                params += f"&board={board.slug}"
            return redirect(f"{redirect_url}?{params}#post-{post.id}")
        else:
            messages.error(request, "Title and question details are required.")

        redirect_url = reverse("courses:question_form")
        if board:
            return redirect(f"{redirect_url}?board={board.slug}")
        return redirect(redirect_url)

    return redirect("courses:question_form")


def _question_form_redirect(post, fragment=""):
    """Return to the Question Form page, focused on the given question."""
    redirect_url = reverse("courses:question_form")
    params = f"open={post.id}"
    if post.board:
        params += f"&board={post.board.slug}"
    anchor = fragment or f"post-{post.id}"
    return redirect(f"{redirect_url}?{params}#{anchor}")


# Backward-compatible alias
_public_chat_redirect = _question_form_redirect


@login_required
def discussion_add_reply(request, post_id):
    """Logged-in users reply to a specific question on the Question Form.

    `post_id` identifies exactly which question is being replied to, so a
    reply always lands on the question the user selected. An optional image
    can be attached.
    """
    post = get_object_or_404(DiscussionPost, pk=post_id)
    if request.method == "POST":
        content = sanitize_math_content(request.POST.get("content", ""))
        image = request.FILES.get("image")
        if content or image:
            DiscussionReply.objects.create(
                post=post, user=request.user, content=content, image=image
            )
            messages.success(request, "✅ Your reply has been added!")
        else:
            messages.error(request, "Write something or attach an image to reply.")

    return _question_form_redirect(post)


@login_required
def discussion_edit_reply(request, reply_id):
    """Author can edit the text (and optional image) of their own reply."""
    reply = get_object_or_404(DiscussionReply, pk=reply_id)
    post = reply.post

    if reply.user_id != request.user.id:
        messages.error(request, "You can only edit your own replies.")
        return _question_form_redirect(post, f"reply-{reply.id}")

    if request.method != "POST":
        return _question_form_redirect(post, f"reply-{reply.id}")

    content = sanitize_math_content(request.POST.get("content", ""))
    image = request.FILES.get("image")
    clear_image = request.POST.get("clear_image") == "1"

    if not content and not image and not reply.image:
        messages.error(request, "Reply cannot be empty.")
        return _question_form_redirect(post, f"reply-{reply.id}")

    # Allow empty text only if an image remains or is newly uploaded
    if not content and not image and (clear_image or not reply.image):
        messages.error(request, "Write something or keep/attach an image.")
        return _question_form_redirect(post, f"reply-{reply.id}")

    reply.content = content
    if clear_image and reply.image:
        reply.image.delete(save=False)
        reply.image = None
    if image:
        reply.image = image
    reply.save()
    messages.success(request, "✅ Your reply has been updated.")
    return _question_form_redirect(post, f"reply-{reply.id}")


@login_required
@require_POST
def discussion_delete_reply(request, reply_id):
    """Author can permanently delete their own reply."""
    reply = get_object_or_404(DiscussionReply, pk=reply_id)
    post = reply.post

    if reply.user_id != request.user.id:
        messages.error(request, "You can only delete your own replies.")
        return _question_form_redirect(post)

    if reply.image:
        reply.image.delete(save=False)
    reply.delete()
    messages.success(request, "🗑️ Your reply has been deleted.")
    return _question_form_redirect(post)
