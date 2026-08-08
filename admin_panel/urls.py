from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("login/", views.admin_login, name="login"),
    path("logout/", views.admin_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # CSV & Questions
    path("csv-upload/", views.csv_upload, name="csv_upload"),
    path(
        "csv-upload/sample-template/",
        views.download_sample_template,
        name="download_sample_template",
    ),
    path(
        "csv-upload/sample-docx/",
        views.download_sample_docx,
        name="download_sample_docx",
    ),
    path(
        "resources/sample-docx/",
        views.download_sample_resource_docx,
        name="download_sample_resource_docx",
    ),
    path(
        "blogs/sample-pdf/",
        views.download_sample_blog_pdf,
        name="download_sample_blog_pdf",
    ),
    path(
        "blogs/sample-pptx/",
        views.download_sample_blog_pptx,
        name="download_sample_blog_pptx",
    ),
    path(
        "blogs/sample-docx/",
        views.download_sample_blog_docx,
        name="download_sample_blog_docx",
    ),
    path("manual-question/", views.manual_question, name="manual_question"),
    path("manage-questions/", views.manage_questions, name="manage_questions"),
    path(
        "question-banks/create/",
        views.create_question_bank,
        name="create_question_bank",
    ),
    # Question Wizard (Exam Builder question-creation modal)
    path(
        "questions/bulk-create/",
        views.question_wizard_bulk_create,
        name="question_wizard_bulk_create",
    ),
    path(
        "questions/<int:question_id>/data/",
        views.question_wizard_data,
        name="question_wizard_data",
    ),
    path(
        "questions/<int:question_id>/save/",
        views.question_wizard_save,
        name="question_wizard_save",
    ),
    path(
        "questions/<int:question_id>/delete/",
        views.question_wizard_delete,
        name="question_wizard_delete",
    ),
    path(
        "questions/bulk-delete/",
        views.questions_bulk_delete,
        name="questions_bulk_delete",
    ),
    # Blogs
    path("manage-blogs/", views.manage_blogs, name="manage_blogs"),
    path("manage-blogs/create/", views.create_blog, name="create_blog"),
    path("manage-blogs/<int:blog_id>/edit/", views.edit_blog, name="edit_blog"),
    path("manage-blogs/<int:blog_id>/delete/", views.delete_blog, name="delete_blog"),
    # Courses
    path("manage-courses/", views.manage_courses, name="manage_courses"),
    path("manage-courses/create/", views.create_course, name="create_course"),
    path("manage-courses/<int:course_id>/edit/", views.edit_course, name="edit_course"),
    path(
        "manage-courses/<int:course_id>/delete/",
        views.delete_course,
        name="delete_course",
    ),
    # Categories
    path("manage-categories/", views.manage_categories, name="manage_categories"),
    path("manage-categories/create/", views.create_category, name="create_category"),
    path(
        "manage-categories/<int:category_id>/edit/",
        views.edit_category,
        name="edit_category",
    ),
    path(
        "manage-categories/<int:category_id>/delete/",
        views.delete_category,
        name="delete_category",
    ),
    # Resources
    path("manage-resources/", views.manage_resources, name="manage_resources"),
    path("manage-resources/create/", views.create_resource, name="create_resource"),
    path(
        "manage-resources/<int:resource_id>/edit/",
        views.edit_resource,
        name="edit_resource",
    ),
    path(
        "manage-resources/<int:resource_id>/delete/",
        views.delete_resource,
        name="delete_resource",
    ),
    # Past Papers (full exam PDFs for public browser)
    path("manage-past-papers/", views.manage_past_papers, name="manage_past_papers"),
    path(
        "manage-past-papers/create/",
        views.create_past_paper,
        name="create_past_paper",
    ),
    path(
        "manage-past-papers/upload-answer/",
        views.upload_past_paper_answer,
        name="upload_past_paper_answer",
    ),
    path(
        "manage-past-papers/sample-question-pdf/",
        views.download_sample_past_paper_question,
        name="download_sample_past_paper_question",
    ),
    path(
        "manage-past-papers/sample-answer-pdf/",
        views.download_sample_past_paper_answer,
        name="download_sample_past_paper_answer",
    ),
    path(
        "manage-past-papers/<int:paper_id>/edit/",
        views.edit_past_paper,
        name="edit_past_paper",
    ),
    path(
        "manage-past-papers/<int:paper_id>/clear-answer/",
        views.clear_past_paper_answer,
        name="clear_past_paper_answer",
    ),
    path(
        "manage-past-papers/<int:paper_id>/delete/",
        views.delete_past_paper,
        name="delete_past_paper",
    ),
    # Exam Builder
    path("exams/", views.manage_exams, name="manage_exams"),
    path("exams/create/", views.create_exam, name="create_exam"),
    path("exams/<int:exam_id>/", views.edit_exam, name="edit_exam"),
    path("exams/<int:exam_id>/settings/", views.exam_settings, name="exam_settings"),
    path("exams/<int:exam_id>/delete/", views.delete_exam, name="delete_exam"),
    path(
        "exams/<int:exam_id>/toggle-question/",
        views.exam_toggle_question,
        name="exam_toggle_question",
    ),
    path(
        "exams/<int:exam_id>/reorder/",
        views.exam_reorder_questions,
        name="exam_reorder_questions",
    ),
    # Build Question List
    path("question-lists/", views.manage_question_lists, name="manage_question_lists"),
    path(
        "question-lists/create/",
        views.create_question_list,
        name="create_question_list",
    ),
    path(
        "question-lists/<int:list_id>/",
        views.edit_question_list,
        name="edit_question_list",
    ),
    path(
        "question-lists/<int:list_id>/delete/",
        views.delete_question_list,
        name="delete_question_list",
    ),
    path(
        "question-lists/<int:list_id>/toggle-question/",
        views.question_list_toggle_question,
        name="question_list_toggle_question",
    ),
    path(
        "question-lists/<int:list_id>/reorder/",
        views.question_list_reorder,
        name="question_list_reorder",
    ),
]
