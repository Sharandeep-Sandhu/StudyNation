from django.urls import path
from django.views.generic import RedirectView
from .views import (
    HomeView,
    CoursesListView,
    CourseDetailView,
    ResourcesView,
    ContactView,
    PastPapersView,
    BlogListView,
    BlogDetailView,
    ResourcesListView,
    ResourceDetailView,
    resource_file_stream,
    QuestionForumView,
    PublicChatView,
    student_signup,
    student_login,
    student_logout,
    student_exams,
    student_create_exam,
    student_edit_exam,
    student_generate_exam_paper,
    student_exam_toggle_question,
    student_exam_reorder_questions,
    student_exam_settings,
    student_delete_exam,
    student_practice_start,
    student_practice_submit,
    student_practice_result,
    student_question_lists,
    student_create_question_list,
    student_edit_question_list,
    student_question_list_toggle_question,
    student_question_list_reorder,
    student_delete_question_list,
    discussion_create_post,
    discussion_add_reply,
    discussion_edit_reply,
    discussion_delete_reply,
)

app_name = "courses"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("courses/", CoursesListView.as_view(), name="courses_list"),
    path("courses/<int:course_id>/", CourseDetailView.as_view(), name="course_detail"),
    # Resources: list is the canonical page; keep legacy name for reverse()
    path("resources/", ResourcesListView.as_view(), name="resources_list"),
    path("resources/", ResourcesListView.as_view(), name="resources"),
    path("past-papers/", PastPapersView.as_view(), name="past_papers"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("blogs/", BlogListView.as_view(), name="blog_list"),
    path("blogs/<slug:slug>/", BlogDetailView.as_view(), name="blog_detail"),
    path("resources/<int:pk>/", ResourceDetailView.as_view(), name="resource_detail"),
    path(
        "resources/<int:pk>/stream/",
        resource_file_stream,
        name="resource_file_stream",
    ),
    # Question Forum (topic boards for community Q&A)
    path("question-forum/", QuestionForumView.as_view(), name="question_forum"),
    # Legacy URLs — keep bookmarks/old links working
    path(
        "question-form/",
        RedirectView.as_view(
            pattern_name="courses:question_forum",
            permanent=False,
            query_string=True,
        ),
        name="question_form",
    ),
    path("public-chat/", PublicChatView.as_view(), name="public_chat"),
    path("discussion/create/", discussion_create_post, name="discussion_create"),
    path("discussion/<int:post_id>/reply/", discussion_add_reply, name="discussion_reply"),
    path(
        "discussion/reply/<int:reply_id>/edit/",
        discussion_edit_reply,
        name="discussion_edit_reply",
    ),
    path(
        "discussion/reply/<int:reply_id>/delete/",
        discussion_delete_reply,
        name="discussion_delete_reply",
    ),
    # Student authentication
    path("signup/", student_signup, name="student_signup"),
    path("login/", student_login, name="student_login"),
    path("logout/", student_logout, name="student_logout"),
    # Student Exam Builder
    path("my-exams/", student_exams, name="student_exams"),
    path("my-exams/create/", student_create_exam, name="student_create_exam"),
    path("my-exams/<int:exam_id>/", student_edit_exam, name="student_edit_exam"),
    path(
        "my-exams/<int:exam_id>/generate/",
        student_generate_exam_paper,
        name="student_generate_exam_paper",
    ),
    path(
        "my-exams/<int:exam_id>/settings/",
        student_exam_settings,
        name="student_exam_settings",
    ),
    path(
        "my-exams/<int:exam_id>/delete/",
        student_delete_exam,
        name="student_delete_exam",
    ),
    path(
        "my-exams/<int:exam_id>/practice/",
        student_practice_start,
        name="student_practice_start",
    ),
    path(
        "my-exams/<int:exam_id>/practice/submit/",
        student_practice_submit,
        name="student_practice_submit",
    ),
    path(
        "my-exams/<int:exam_id>/practice/attempt/<int:attempt_id>/",
        student_practice_result,
        name="student_practice_result",
    ),
    path(
        "my-exams/<int:exam_id>/toggle-question/",
        student_exam_toggle_question,
        name="student_exam_toggle_question",
    ),
    path(
        "my-exams/<int:exam_id>/reorder/",
        student_exam_reorder_questions,
        name="student_exam_reorder_questions",
    ),
    # Student Question Lists (Build Question List)
    path("my-lists/", student_question_lists, name="student_question_lists"),
    path(
        "my-lists/create/",
        student_create_question_list,
        name="student_create_question_list",
    ),
    path(
        "my-lists/<int:list_id>/",
        student_edit_question_list,
        name="student_edit_question_list",
    ),
    path(
        "my-lists/<int:list_id>/delete/",
        student_delete_question_list,
        name="student_delete_question_list",
    ),
    path(
        "my-lists/<int:list_id>/toggle-question/",
        student_question_list_toggle_question,
        name="student_question_list_toggle_question",
    ),
    path(
        "my-lists/<int:list_id>/reorder/",
        student_question_list_reorder,
        name="student_question_list_reorder",
    ),
]
