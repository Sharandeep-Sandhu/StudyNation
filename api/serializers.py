from rest_framework import serializers
from courses.models import (
    CourseCategory,
    Course,
    StudyMaterial,
    QuestionBank,
    Question,
    Resource,
)


class CourseCategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseCategory
        fields = ["id", "name", "description", "icon", "courses_count", "created_at"]

    def get_courses_count(self, obj):
        return obj.courses.count()


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "marks",
            "explanation",
            "order",
        ]


class QuestionBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = QuestionBank
        fields = [
            "id",
            "title",
            "description",
            "difficulty",
            "question_count",
            "questions",
            "created_at",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class StudyMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMaterial
        fields = [
            "id",
            "title",
            "material_type",
            "description",
            "file",
            "file_size",
            "downloads",
            "created_at",
        ]


class ResourceSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    resource_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            "id",
            "title",
            "description",
            "file",
            "author",
            "resource_type",
            "resource_type_display",
            "is_paid",
            "price",
            "course",
            "course_name",
            "created_at",
        ]

    def get_course_name(self, obj):
        return obj.course.title if obj.course else None

    def get_resource_type_display(self, obj):
        return obj.get_resource_type_display()


class CourseDetailSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    study_materials = StudyMaterialSerializer(many=True, read_only=True)
    question_banks = QuestionBankSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "category",
            "instructor",
            "duration",
            "level",
            "students_enrolled",
            "rating",
            "thumbnail",
            "study_materials",
            "question_banks",
            "created_at",
            "updated_at",
        ]


class CourseListSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "category",
            "level",
            "students_enrolled",
            "rating",
            "thumbnail",
            "created_at",
        ]
