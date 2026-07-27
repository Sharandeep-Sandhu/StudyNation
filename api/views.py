from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from courses.models import (
    CourseCategory,
    Course,
    StudyMaterial,
    QuestionBank,
    Question,
    Resource,
)
from .serializers import (
    CourseCategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    StudyMaterialSerializer,
    QuestionBankSerializer,
    QuestionSerializer,
    ResourceSerializer,
)


class CourseCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for course categories"""

    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for courses"""

    queryset = Course.objects.prefetch_related(
        "study_materials", "question_banks"
    ).all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    @action(detail=False, methods=["get"])
    def by_category(self, request):
        """Get courses by category"""
        category_id = request.query_params.get("category_id")
        if not category_id:
            return Response(
                {"error": "category_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        courses = self.queryset.filter(category_id=category_id)
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search courses by title or description"""
        query = request.query_params.get("q", "")
        if len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        courses = self.queryset.filter(
            models.Q(title__icontains=query) | models.Q(description__icontains=query)
        )
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


class StudyMaterialViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for study materials"""

    queryset = StudyMaterial.objects.all()
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")
        if course_id:
            return self.queryset.filter(course_id=course_id)
        return self.queryset


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for resources (e-books, handwritten notes, etc.) - Fetches from DB"""

    queryset = Resource.objects.all().order_by("-created_at")
    serializer_class = ResourceSerializer

    def get_queryset(self):
        queryset = self.queryset
        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        resource_type = self.request.query_params.get("resource_type")
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        is_paid = self.request.query_params.get("is_paid")
        if is_paid is not None:
            queryset = queryset.filter(is_paid=is_paid.lower() == "true")
        return queryset

    @action(detail=False, methods=["get"])
    def random(self, request):
        """Return a single random resource from DB"""
        import random

        resources = list(self.get_queryset())
        if not resources:
            return Response(
                {"error": "No resources available"}, status=status.HTTP_404_NOT_FOUND
            )
        random_resource = random.choice(resources)
        serializer = self.get_serializer(random_resource)
        return Response(serializer.data)


class QuestionBankViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for question banks"""

    queryset = QuestionBank.objects.prefetch_related("questions").all()
    serializer_class = QuestionBankSerializer

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")
        if course_id:
            return self.queryset.filter(course_id=course_id)
        return self.queryset


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for questions"""

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def get_queryset(self):
        question_bank_id = self.request.query_params.get("question_bank_id")
        if question_bank_id:
            return self.queryset.filter(question_bank_id=question_bank_id)
        return self.queryset
