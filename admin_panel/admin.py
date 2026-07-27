from django.contrib import admin
from .models import AdminUser, CSVUpload, ManualQuestionLog


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "is_admin",
        "can_upload_csv",
        "can_manage_questions",
        "created_at",
        "last_login",
    ]
    list_filter = ["is_admin", "can_upload_csv", "can_manage_questions", "created_at"]
    search_fields = ["user__username", "user__email", "user__first_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "last_login"]

    def user(self, obj):
        return obj.user.username

    user.short_description = "Username"


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "admin_user",
        "total_questions",
        "successful_imports",
        "failed_imports",
        "status",
        "uploaded_at",
    ]
    list_filter = ["status", "uploaded_at"]
    search_fields = ["file_name", "admin_user__user__username"]
    ordering = ["-uploaded_at"]
    readonly_fields = [
        "uploaded_at",
        "total_questions",
        "successful_imports",
        "failed_imports",
        "status",
        "error_details",
    ]

    def admin_user(self, obj):
        return obj.admin_user.user.username

    admin_user.short_description = "Uploaded By"


@admin.register(ManualQuestionLog)
class ManualQuestionLogAdmin(admin.ModelAdmin):
    list_display = [
        "question_text_short",
        "admin_user",
        "question_type",
        "status",
        "created_at",
    ]
    list_filter = ["status", "question_type", "created_at"]
    search_fields = ["question_text", "admin_user__user__username"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]

    def question_text_short(self, obj):
        return (
            obj.question_text[:60] + "..."
            if len(obj.question_text) > 60
            else obj.question_text
        )

    question_text_short.short_description = "Question"

    def admin_user(self, obj):
        return obj.admin_user.user.username

    admin_user.short_description = "Added By"
