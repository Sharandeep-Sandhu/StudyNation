"""Template context: role flags so nav/pages can treat admins as full-access."""


def user_roles(request):
    """Expose is_admin_user / is_student_user / can_use_exam_builder."""
    try:
        user = getattr(request, "user", None)
        is_authenticated = bool(user and getattr(user, "is_authenticated", False))

        is_admin = False
        is_student = False
        if is_authenticated:
            is_admin = bool(getattr(user, "is_superuser", False))
            if not is_admin:
                try:
                    from admin_panel.models import AdminUser

                    is_admin = AdminUser.objects.filter(user_id=user.pk).exists()
                except Exception:
                    is_admin = False
            try:
                from courses.models import StudentProfile

                is_student = StudentProfile.objects.filter(user_id=user.pk).exists()
            except Exception:
                is_student = False

        return {
            "is_admin_user": is_admin,
            "is_student_user": is_student,
            # Student pages + exam builder: open to students and admins
            "can_use_exam_builder": is_admin or is_student,
        }
    except Exception:
        # Never 500 an entire page because role flags failed
        return {
            "is_admin_user": False,
            "is_student_user": False,
            "can_use_exam_builder": False,
        }
