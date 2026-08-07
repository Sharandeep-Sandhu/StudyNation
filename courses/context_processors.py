"""Template context: role flags so nav/pages can treat admins as full-access."""


def user_roles(request):
    """Expose is_admin_user / is_student_user / can_use_exam_builder."""
    user = getattr(request, "user", None)
    is_authenticated = bool(user and getattr(user, "is_authenticated", False))

    is_admin = False
    is_student = False
    if is_authenticated:
        is_admin = hasattr(user, "admin_profile") or bool(
            getattr(user, "is_superuser", False)
        )
        is_student = hasattr(user, "student_profile")

    return {
        "is_admin_user": is_admin,
        "is_student_user": is_student,
        # Student pages + exam builder: open to students and admins
        "can_use_exam_builder": is_admin or is_student,
    }
