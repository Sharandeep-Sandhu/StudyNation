from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.utils.text import slugify


class StudentProfile(models.Model):
    """Extended profile for public, student-facing accounts (Exam Builder, etc.)."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Student: {self.user.username}"


class CourseCategory(models.Model):
    """Course category/subject"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="book")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Course Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    """Course model"""

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        CourseCategory, on_delete=models.CASCADE, related_name="courses"
    )
    instructor = models.CharField(max_length=150, blank=True)
    duration = models.CharField(max_length=100, blank=True, help_text="e.g., 12 weeks")
    level = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
    )
    students_enrolled = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    thumbnail = models.ImageField(upload_to="course_thumbnails/", null=True, blank=True)

    what_youll_learn = models.TextField(
        blank=True,
        help_text="One point per line. Shown as bullet points under 'What You'll Learn'.",
    )
    prerequisites = models.TextField(
        blank=True,
        help_text="One point per line. Shown as bullet points under 'Prerequisites'.",
    )
    curriculum = models.TextField(
        blank=True,
        help_text=(
            "One module per line, format 'Module Title: Description'. "
            "Example: Module 1: Introduction and Fundamentals"
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class StudyMaterial(models.Model):
    """Study materials: notes, ebooks, etc."""

    MATERIAL_TYPES = [
        ("notes", "Course Notes"),
        ("ebook", "E-Book"),
        ("worksheet", "Worksheet"),
        ("summary", "Summary"),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="study_materials"
    )
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to="study_materials/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "txt"])
        ],
    )
    file_size = models.IntegerField(help_text="Size in KB")
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class QuestionBank(models.Model):
    """Collection of questions for a course"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="question_banks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_questions = models.IntegerField(default=0)
    difficulty = models.CharField(
        max_length=20,
        choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
        default="medium",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Question(models.Model):
    """Individual question"""

    QUESTION_TYPES = [
        ("single_choice", "Single Choice"),
        ("multiple_choice", "Multiple Choice"),
        ("true_false", "True/False"),
        ("numerical", "Numerical"),
        ("matching", "Matching"),
        ("structured", "Structured (multi-part, past paper style)"),
        # ---- Exam Builder question types (new question-creation wizard) ----
        ("mcq", "Multiple Choice Questions"),
        ("comprehension", "Comprehension Questions"),
        ("fill_blank", "Fill in the Blanks Questions"),
        ("integer", "Integer Type Questions"),
    ]

    ANSWER_TYPES = [
        ("single", "Single"),
        ("multiple", "Multiple"),
    ]

    DIFFICULTY_LEVELS = [
        ("", "Add difficulty level"),
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    SEASON_CHOICES = [
        ("summer", "Summer"),
        ("winter", "Winter"),
        ("specimen", "Specimen"),
    ]

    ZONE_CHOICES = [
        ("", "—"),
        ("zone_1", "Zone 1"),
        ("zone_2", "Zone 2"),
        ("zone_3", "Zone 3"),
    ]

    question_bank = models.ForeignKey(
        QuestionBank, on_delete=models.CASCADE, related_name="questions"
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField(
        help_text=(
            "Supports inline math using LaTeX delimiters: $x^2+1$ for inline, "
            "$$\\frac{a}{b}$$ for a centered block. Rendered with MathJax on "
            "the site and rasterized for PDF export."
        )
    )
    order = models.IntegerField(default=0)

    # Single/Multiple choice options
    option_a = models.CharField(max_length=5000, blank=True)
    option_b = models.CharField(max_length=5000, blank=True)
    option_c = models.CharField(max_length=5000, blank=True)
    option_d = models.CharField(max_length=5000, blank=True)

    # Correct answer(s)
    correct_answer = models.CharField(
        max_length=5000, blank=True, help_text="For choice: A/B/C/D or A,B for multiple"
    )
    marks = models.IntegerField(default=1)
    explanation = models.TextField(
        blank=True, help_text="Shown to students as the question 'Solution'."
    )

    # ---- New Exam Builder wizard fields ----
    difficulty_level = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, blank=True, default=""
    )
    answer_type = models.CharField(
        max_length=10,
        choices=ANSWER_TYPES,
        default="single",
        help_text="Whether one option ('single') or several options "
        "('multiple') can be marked correct.",
    )
    negative_marks = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text="Marks deducted for a wrong attempt.",
    )
    partial_marking = models.BooleanField(
        default=False,
        help_text="Award proportional marks for a partially-correct "
        "'multiple' answer instead of all-or-nothing.",
    )
    passage = models.TextField(
        blank=True,
        help_text="Shared comprehension passage this question belongs to "
        "(only used for 'comprehension' type questions).",
    )
    numeric_tolerance = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Allowed +/- tolerance for 'integer' type answers.",
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags, e.g. 'Algebra, Grade 10'",
    )

    # ---- Topical past-paper metadata (Exam Builder) ----
    topic = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated topics, e.g. 'Functions, Modulus'",
    )
    paper_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Subject/paper code, e.g. '0606/23'",
    )
    year = models.IntegerField(null=True, blank=True, help_text="e.g. 2019")
    season = models.CharField(
        max_length=20, choices=SEASON_CHOICES, blank=True
    )
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES, blank=True)
    question_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Question number within the paper, e.g. 'Q10' or '10'",
    )
    question_code = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
        help_text=(
            "Auto-generated display code, e.g. '0606/23_Winter_2019_Q10'. "
            "Leave blank to auto-generate from paper code, season, year, "
            "and question number."
        ),
    )

    # Populated when a question is imported from a Word (.doc/.docx) past
    # paper that contained embedded equation graphics (e.g. MS Equation
    # Editor / MathType objects) which could not be automatically converted
    # to text. Stores a JSON list of MEDIA-relative image URLs so an admin
    # can view the original equations and fill in the text/LaTeX by hand.
    equation_images = models.TextField(
        blank=True,
        help_text="JSON list of equation image URLs captured from a Word import (read-only reference).",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question_code or f"Q{self.order}: {self.question_text[:50]}"

    def save(self, *args, **kwargs):
        if not self.question_code:
            parts = [
                p
                for p in [
                    self.paper_code,
                    self.get_season_display() if self.season else "",
                    str(self.year) if self.year else "",
                ]
                if p
            ]
            code = "_".join(parts)
            if self.question_number:
                num = self.question_number
                if not num.upper().startswith("Q"):
                    num = f"Q{num}"
                code = f"{code}_{num}" if code else num
            self.question_code = code
        super().save(*args, **kwargs)

    @property
    def topic_list(self):
        return [t.strip() for t in self.topic.split(",") if t.strip()]

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def equation_image_list(self):
        """Deserialize the equation_images JSON list for template use."""
        if not self.equation_images:
            return []
        try:
            import json

            data = json.loads(self.equation_images)
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []


class QuestionOption(models.Model):
    """A single answer option belonging to a Question.

    Used by the Exam Builder question-creation wizard, which lets an admin
    add/remove any number of options (unlike the legacy fixed option_a..d
    fields on Question, kept for backward compatibility with older data).
    """

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.TextField(blank=True, help_text="Supports basic rich text (HTML).")
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.question_id} - option {self.order}"


# Add these fields to your Blog model in courses/models.py


class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    author = models.CharField(max_length=100, default="Study Nation Team")
    image = models.ImageField(upload_to="blog_images/", null=True, blank=True)

    # === NEW FIELDS FOR ADMIN PANEL ===
    video = models.FileField(upload_to="blog_media/", blank=True, null=True)
    pdf = models.FileField(upload_to="blog_media/", blank=True, null=True)
    ppt = models.FileField(upload_to="blog_media/", blank=True, null=True)

    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="resources/")
    author = models.CharField(max_length=100, blank=True)
    resource_type = models.CharField(
        max_length=20,
        choices=[
            ("ebook", "E-Book"),
            ("handwritten", "Handwritten Notes"),
            ("other", "Other"),
        ],
    )
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    course = models.ForeignKey(
        "Course", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ==================== EXAM BUILDER ====================
class Exam(models.Model):
    """A custom exam built by an admin/teacher from topical past-paper questions."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("finalized", "Finalized"),
    ]

    name = models.CharField(max_length=200, default="Untitled Exam")
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exams",
        help_text="Curriculum / Subject this exam is built from",
    )
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="exams"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    duration_minutes = models.IntegerField(
        default=60, help_text="Used for the built-in exam timer"
    )
    questions_per_page = models.IntegerField(
        default=1, help_text="How many questions to show per page in the exported PDF"
    )
    shuffle_questions = models.BooleanField(default=False)

    questions = models.ManyToManyField(
        Question, through="ExamQuestion", related_name="exams"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def total_marks(self):
        return sum(eq.question.marks for eq in self.exam_questions.select_related("question"))

    @property
    def question_count(self):
        return self.exam_questions.count()


class ExamQuestion(models.Model):
    """Through-model preserving the order in which questions were added to an exam."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_questions")
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="exam_links"
    )
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "added_at"]
        unique_together = ("exam", "question")

    def __str__(self):
        return f"{self.exam.name} - {self.question}"


class ExamAttempt(models.Model):
    """
    One timed 'Practice this exam' run through an Exam's selected questions.
    Created only once the student submits their answers (the start time is
    captured client-side when the quiz page loads and sent back on submit),
    so browsing away mid-attempt just leaves no record rather than an
    orphaned 'in progress' row.
    """

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="exam_attempts")

    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(default=0)

    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)

    total_marks = models.FloatField(default=0)
    marks_scored = models.FloatField(default=0)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} - {self.exam.name} ({self.marks_scored}/{self.total_marks})"

    @property
    def score_percent(self):
        if not self.total_marks:
            return 0
        return round(100 * self.marks_scored / self.total_marks, 1)

    @property
    def time_taken_display(self):
        minutes, seconds = divmod(self.time_taken_seconds, 60)
        return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


class ExamAttemptAnswer(models.Model):
    """A single question's recorded answer within an ExamAttempt."""

    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempt_answers")
    given_answer = models.TextField(blank=True)
    # True/False = auto-graded correct/incorrect. None = left blank (unanswered).
    is_correct = models.BooleanField(null=True)
    marks_awarded = models.FloatField(default=0)

    class Meta:
        ordering = ["id"]
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.attempt} - {self.question.question_code}"


# ==================== BUILD QUESTION LIST ====================
class QuestionList(models.Model):
    """
    A simpler, untimed companion to Exam: just a named, ordered set of
    questions filtered by topic/difficulty/paper. Used by both students
    (saved to their account) and admins (curated lists / templates).
    """

    name = models.CharField(max_length=200, default="Untitled Question List")
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_lists",
        help_text="Curriculum / Subject this list is built from",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_lists",
    )
    is_admin_curated = models.BooleanField(
        default=False,
        help_text="True for lists built by an admin (e.g. shared templates), False for student lists.",
    )

    questions = models.ManyToManyField(
        Question, through="QuestionListItem", related_name="question_lists"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def total_marks(self):
        return sum(
            item.question.marks for item in self.list_items.select_related("question")
        )

    @property
    def question_count(self):
        return self.list_items.count()


class QuestionListItem(models.Model):
    """Through-model preserving the order of questions within a QuestionList."""

    question_list = models.ForeignKey(
        QuestionList, on_delete=models.CASCADE, related_name="list_items"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="list_links"
    )
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "added_at"]
        unique_together = ("question_list", "question")

    def __str__(self):
        return f"{self.question_list.name} - {self.question}"


# ==================== PUBLIC DISCUSSION / CHAT BOARD ====================
class DiscussionBoard(models.Model):
    """A category/board on the Public Chat page, e.g. 'First Year Families'.

    Shown in the left-hand 'My Discussion Boards' sidebar. Posts belong to
    one board so families can browse by topic instead of one giant feed.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first in the sidebar"
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Discussion Board"
        verbose_name_plural = "Discussion Boards"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:100] or "board"
            slug = base_slug
            i = 1
            while DiscussionBoard.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class DiscussionPost(models.Model):
    """Public Q&A / Chat board posts (questions) by logged-in users on the Public Chat page"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="discussion_posts"
    )
    board = models.ForeignKey(
        DiscussionBoard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        help_text="Which discussion board this post belongs to",
    )
    title = models.CharField(
        max_length=200, help_text="Short title for the question or topic"
    )
    content = models.TextField(help_text="Detailed question or problem description")
    image = models.ImageField(
        upload_to="discussion_images/posts/",
        blank=True,
        null=True,
        help_text="Optional image attached to the post",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(
        default=False, help_text="Community or author can mark as resolved"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Discussion Post"
        verbose_name_plural = "Discussion Posts"

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class DiscussionReply(models.Model):
    """Replies, opinions, or solutions to discussion posts"""

    post = models.ForeignKey(
        DiscussionPost, on_delete=models.CASCADE, related_name="replies"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="discussion_replies"
    )
    content = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="discussion_images/replies/",
        blank=True,
        null=True,
        help_text="Optional image attached to the reply",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Discussion Reply"
        verbose_name_plural = "Discussion Replies"

    def __str__(self):
        return f"Reply by {self.user.username} to '{self.post.title[:40]}'"

    @property
    def was_edited(self):
        """True if the reply was saved after creation (allowing small clock skew)."""
        if not self.updated_at or not self.created_at:
            return False
        return (self.updated_at - self.created_at).total_seconds() > 2


class ContactMessage(models.Model):
    """Messages submitted via the public Contact Us form."""

    CATEGORY_CHOICES = [
        ("general", "General Inquiry"),
        ("technical", "Technical Support"),
        ("course", "Course Related"),
        ("partnership", "Partnership"),
        ("feedback", "Feedback"),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=200)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="general"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.subject} from {self.name}"
