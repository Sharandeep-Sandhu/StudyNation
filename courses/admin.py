from django.contrib import admin
from .models import (
    CourseCategory,
    Course,
    StudyMaterial,
    QuestionBank,
    Question,
    QuestionOption,
    Blog,
    Resource,
    PastPaper,
    DiscussionBoard,
    DiscussionPost,
    DiscussionReply,
    ContactMessage,
)


# ==================== COURSE CATEGORY ====================
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "icon", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]


# ==================== COURSE ====================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "level",
        "instructor",
        "students_enrolled",
        "rating",
        "created_at",
    ]
    list_filter = ["category", "level", "created_at"]
    search_fields = ["title", "description", "instructor"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "category")}),
        ("Course Details", {"fields": ("instructor", "duration", "level")}),
        ("Statistics", {"fields": ("students_enrolled", "rating")}),
        ("Media", {"fields": ("thumbnail",)}),
        (
            "Course Overview (Public Page)",
            {
                "fields": ("what_youll_learn", "prerequisites", "curriculum"),
                "description": (
                    "These show on the public course page. Enter one item per "
                    "line for 'What You'll Learn' and 'Prerequisites'. For "
                    "'Course Curriculum', use one module per line in the format "
                    "'Module 1: Description'."
                ),
            },
        ),
    )


# ==================== STUDY MATERIAL ====================
@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "course",
        "material_type",
        "file_size",
        "downloads",
        "created_at",
    ]
    list_filter = ["material_type", "course", "created_at"]
    search_fields = ["title", "course__title", "description"]
    ordering = ["-created_at"]


# ==================== QUESTION BANK ====================
@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject_title",
        "course",
        "difficulty",
        "total_questions",
        "created_at",
    ]
    list_filter = ["difficulty", "course", "subject_title", "created_at"]
    search_fields = ["title", "subject_title", "course__title", "description"]
    ordering = ["-created_at"]


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ["text", "is_correct", "order"]


# ==================== QUESTION ====================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "question_text_short",
        "question_bank",
        "question_type",
        "difficulty_level",
        "marks",
        "order",
        "created_at",
    ]
    list_filter = ["question_type", "difficulty_level", "question_bank", "created_at"]
    search_fields = ["question_text", "question_bank__title", "tags"]
    ordering = ["question_bank", "order"]
    inlines = [QuestionOptionInline]

    fieldsets = (
        (
            "Question Details",
            {
                "fields": (
                    "question_bank",
                    "question_text",
                    "question_type",
                    "answer_type",
                    "difficulty_level",
                    "tags",
                    "order",
                )
            },
        ),
        (
            "Legacy Options (old data)",
            {
                "fields": ("option_a", "option_b", "option_c", "option_d"),
                "classes": ("collapse",),
            },
        ),
        (
            "Answer & Explanation",
            {
                "fields": (
                    "correct_answer",
                    "marks",
                    "negative_marks",
                    "partial_marking",
                    "numeric_tolerance",
                    "explanation",
                    "video_solution_url",
                )
            },
        ),
        (
            "Comprehension",
            {"fields": ("passage",), "classes": ("collapse",)},
        ),
    )

    def question_text_short(self, obj):
        return (
            obj.question_text[:60] + "..."
            if len(obj.question_text) > 60
            else obj.question_text
        )

    question_text_short.short_description = "Question"


# ==================== BLOG (NEW) ====================
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "published", "created_at", "updated_at"]
    list_filter = ["published", "created_at"]
    search_fields = ["title", "content", "author"]
    ordering = ["-created_at"]
    prepopulated_fields = {"slug": ("title",)}  # Auto-generate slug from title
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Info", {"fields": ("title", "slug", "author", "published")}),
        ("Content", {"fields": ("content", "image")}),
        ("Media Files", {"fields": ("video", "pdf")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# ==================== RESOURCE (NEW) ====================
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "resource_type",
        "is_paid",
        "price",
        "course",
        "author",
        "created_at",
    ]
    list_filter = ["resource_type", "is_paid", "created_at"]
    search_fields = ["title", "description", "author"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "author")}),
        ("File", {"fields": ("file", "resource_type")}),
        ("Pricing", {"fields": ("is_paid", "price")}),
        ("Related Course", {"fields": ("course",)}),
    )


# ==================== PAST PAPERS (PDF browser) ====================
@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "subject",
        "year",
        "season",
        "paper_code",
        "has_answer",
        "is_published",
        "created_at",
    ]
    list_filter = ["category", "subject", "year", "is_published", "season"]
    search_fields = ["title", "subject", "paper_code", "description"]
    ordering = ["-year", "subject", "title"]
    list_editable = ["is_published"]
    fields = [
        "title",
        "category",
        "subject",
        "year",
        "season",
        "paper_code",
        "pdf",
        "answer_pdf",
        "description",
        "is_published",
        "created_at",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(boolean=True, description="Answer")
    def has_answer(self, obj):
        return bool(obj.answer_pdf)


# ==================== QUESTION FORM (TOPIC BOARDS) ====================
@admin.register(DiscussionBoard)
class DiscussionBoardAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "post_count"]
    search_fields = ["name", "description"]
    ordering = ["order", "name"]
    prepopulated_fields = {"slug": ("name",)}

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = "Questions"


class DiscussionReplyInline(admin.TabularInline):
    model = DiscussionReply
    extra = 0
    fields = ["user", "content", "image", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "board", "is_resolved", "reply_count", "created_at"]
    list_filter = ["board", "is_resolved", "created_at"]
    search_fields = ["title", "content", "user__username"]
    ordering = ["-created_at"]
    inlines = [DiscussionReplyInline]

    def reply_count(self, obj):
        return obj.replies.count()

    reply_count.short_description = "Replies"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "name", "email", "category", "is_read", "created_at"]
    list_filter = ["category", "is_read", "created_at"]
    search_fields = ["subject", "name", "email", "message"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "user__username", "post__title"]
    ordering = ["-created_at"]
