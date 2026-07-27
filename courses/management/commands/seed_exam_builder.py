"""
Management command that seeds topical past-paper-style questions for the
Exam Builder feature (CIE IGCSE Additional Mathematics 0606 sample data).

Usage:
    python manage.py seed_exam_builder
"""
from django.core.management.base import BaseCommand
from courses.models import CourseCategory, Course, QuestionBank, Question


SEED_QUESTIONS = [
    dict(
        topic="Functions, Modulus",
        paper_code="0606/23",
        season="winter",
        year=2019,
        question_number="10",
        marks=11,
        question_type="structured",
        question_text=(
            "The functions f and g are defined by\n"
            "$$f(x) = \\ln(3x+2) \\quad \\text{for } x > -\\frac{2}{3}$$\n"
            "$$g(x) = e^{2x} - 4 \\quad \\text{for } x \\in \\mathbb{R}.$$\n\n"
            "(i) Solve $gf(x) = 5$. [5]\n"
            "(ii) Find $f^{-1}(x)$. [2]\n"
            "(iii) Solve $f^{-1}(x) = g(x)$. [4]"
        ),
    ),
    dict(
        topic="Functions, Modulus",
        paper_code="0606/23",
        season="winter",
        year=2019,
        question_number="9",
        marks=8,
        question_type="structured",
        question_text=(
            "It is given that $f(x) = |2x - 5|$ for $x \\in \\mathbb{R}$.\n\n"
            "(i) Sketch the graph of $y = f(x)$, stating the coordinates of points "
            "where the graph meets the axes. [3]\n"
            "(ii) Solve $f(x) = x + 1$. [5]"
        ),
    ),
    dict(
        topic="Quadratic Functions",
        paper_code="0606/22",
        season="winter",
        year=2019,
        question_number="6",
        marks=6,
        question_type="numerical",
        question_text=(
            "The quadratic equation $2x^2 + (k-4)x + k = 0$ has equal roots.\n\n"
            "Find the possible values of $k$. [6]"
        ),
    ),
    dict(
        topic="Indices and Surds",
        paper_code="0606/22",
        season="winter",
        year=2019,
        question_number="3",
        marks=5,
        question_type="numerical",
        question_text=(
            "Solve the equation $3^{2x+1} = 5^{x}$, giving your answer correct "
            "to 3 significant figures. [5]"
        ),
    ),
    dict(
        topic="Differentiation",
        paper_code="0606/23",
        season="summer",
        year=2019,
        question_number="11",
        marks=9,
        question_type="structured",
        question_text=(
            "A curve has equation $y = \\frac{x^2 + 1}{x - 2}$.\n\n"
            "(i) Find $\\frac{dy}{dx}$, simplifying your answer. [4]\n"
            "(ii) Find the coordinates of the stationary points on the curve and "
            "determine their nature. [5]"
        ),
    ),
    dict(
        topic="Integration",
        paper_code="0606/22",
        season="summer",
        year=2019,
        question_number="8",
        marks=7,
        question_type="numerical",
        question_text=(
            "Find $\\int (3x - 1)^4 \\, dx$. [3]\n\n"
            "Hence evaluate $\\int_{0}^{1} (3x-1)^4 \\, dx$. [4]"
        ),
    ),
    dict(
        topic="Trigonometry",
        paper_code="0606/21",
        season="winter",
        year=2018,
        question_number="5",
        marks=6,
        question_type="numerical",
        question_text=(
            "Solve $2\\sin^2\\theta + \\cos\\theta = 1$ for "
            "$0^{\\circ} \\le \\theta \\le 360^{\\circ}$. [6]"
        ),
    ),
    dict(
        topic="Vectors",
        paper_code="0606/21",
        season="winter",
        year=2018,
        question_number="12",
        marks=10,
        question_type="structured",
        question_text=(
            "Relative to an origin $O$, the position vectors of points $A$ and "
            "$B$ are $\\mathbf{a} = 2\\mathbf{i} + 3\\mathbf{j}$ and "
            "$\\mathbf{b} = 5\\mathbf{i} - \\mathbf{j}$.\n\n"
            "(i) Find the unit vector in the direction of $\\overrightarrow{AB}$. [4]\n"
            "(ii) Find the position vector of the point $C$ on $AB$ such that "
            "$AC:CB = 2:1$. [6]"
        ),
    ),
    dict(
        topic="Series",
        paper_code="0606/22",
        season="summer",
        year=2018,
        question_number="4",
        marks=5,
        question_type="numerical",
        question_text=(
            "The first three terms of an arithmetic progression are "
            "$2k, k+8, 3k-4$. Find the value of $k$ and the common difference "
            "of the progression. [5]"
        ),
    ),
    dict(
        topic="Permutations and Combinations",
        paper_code="0606/23",
        season="summer",
        year=2018,
        question_number="7",
        marks=6,
        question_type="structured",
        question_text=(
            "A committee of 5 people is to be selected from 6 men and 4 women.\n\n"
            "(i) Find the number of different committees that can be selected. [2]\n"
            "(ii) Find the number of different committees that contain at least "
            "3 women. [4]"
        ),
    ),
]


class Command(BaseCommand):
    help = (
        "Seed topical past-paper-style questions for the Exam Builder "
        "(CIE IGCSE Additional Mathematics 0606 sample data)."
    )

    def handle(self, *args, **options):
        category, _ = CourseCategory.objects.get_or_create(
            name="Additional Mathematics (0606)",
            defaults={"description": "CIE IGCSE Additional Mathematics"},
        )

        course, _ = Course.objects.get_or_create(
            title="CIE IGCSE Additional Mathematics (0606)",
            category=category,
            defaults={
                "description": (
                    "Topical past paper question bank for CIE IGCSE "
                    "Additional Mathematics (0606)."
                ),
                "instructor": "Study Nation",
                "duration": "Self-paced",
                "level": "intermediate",
            },
        )

        bank, _ = QuestionBank.objects.get_or_create(
            course=course,
            title="0606 Topical Past Papers",
            defaults={
                "description": "Past paper questions organised by topic.",
                "difficulty": "medium",
            },
        )

        # Idempotent: clear previously seeded rows for this bank, then re-add.
        Question.objects.filter(question_bank=bank).exclude(paper_code="").delete()

        created = 0
        for i, q in enumerate(SEED_QUESTIONS, start=1):
            Question.objects.create(question_bank=bank, order=i, **q)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} topical questions into bank '{bank.title}' "
                f"(course id={course.id}, bank id={bank.id})"
            )
        )
