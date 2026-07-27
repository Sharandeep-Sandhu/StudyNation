from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseCategoryViewSet,
    CourseViewSet,
    StudyMaterialViewSet,
    QuestionBankViewSet,
    QuestionViewSet,
    ResourceViewSet,
)

router = DefaultRouter()
router.register(r"categories", CourseCategoryViewSet, basename="category")
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"study-materials", StudyMaterialViewSet, basename="study-material")
router.register(r"question-banks", QuestionBankViewSet, basename="question-bank")
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"resources", ResourceViewSet, basename="resource")

urlpatterns = [
    path("", include(router.urls)),
]
