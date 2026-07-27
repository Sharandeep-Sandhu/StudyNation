from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AdminUser(models.Model):
    """Extended admin user with custom permissions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    is_admin = models.BooleanField(default=True)
    can_upload_csv = models.BooleanField(default=True)
    can_manage_questions = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Admin: {self.user.username}"


class CSVUpload(models.Model):
    """Track CSV uploads for audit trail"""
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='uploads')
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='csv_uploads/')
    total_questions = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    error_details = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success')
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"

    class Meta:
        ordering = ['-uploaded_at']


class ManualQuestionLog(models.Model):
    """Track manually added questions"""
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='manual_questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived')
        ],
        default='draft'
    )

    def __str__(self):
        return f"{self.question_text[:50]} by {self.admin_user.user.username}"

    class Meta:
        ordering = ['-created_at']
