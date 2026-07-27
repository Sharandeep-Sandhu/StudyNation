from django.core.management.base import BaseCommand
from courses.models import CourseCategory, Course, StudyMaterial, QuestionBank, Question


class Command(BaseCommand):
    help = 'Load sample data into the database'

    def handle(self, *args, **options):
        # Clear existing data
        CourseCategory.objects.all().delete()
        Course.objects.all().delete()
        StudyMaterial.objects.all().delete()
        QuestionBank.objects.all().delete()
        Question.objects.all().delete()

        self.stdout.write(self.style.WARNING('Cleared existing data'))

        # Create categories
        categories = [
            CourseCategory.objects.create(
                name="Programming",
                description="Learn to code with Python, JavaScript, and more",
                icon="💻"
            ),
            CourseCategory.objects.create(
                name="Data Science",
                description="Master data analysis, machine learning, and visualization",
                icon="📊"
            ),
            CourseCategory.objects.create(
                name="Web Development",
                description="Build modern web applications with HTML, CSS, and JavaScript",
                icon="🌐"
            ),
            CourseCategory.objects.create(
                name="Business",
                description="Develop essential business and management skills",
                icon="💼"
            ),
            CourseCategory.objects.create(
                name="Design",
                description="Create stunning designs with UI/UX principles",
                icon="🎨"
            ),
        ]
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))

        # Create courses
        courses_data = [
            {
                "title": "Python for Beginners",
                "description": "Learn Python programming from scratch. This comprehensive course covers variables, loops, functions, and object-oriented programming.",
                "category": categories[0],
                "instructor": "John Smith",
                "duration": "8 weeks",
                "level": "beginner",
                "students_enrolled": 5420,
                "rating": 4.8,
            },
            {
                "title": "Advanced Python Programming",
                "description": "Master advanced Python concepts including decorators, generators, async programming, and design patterns.",
                "category": categories[0],
                "instructor": "Sarah Johnson",
                "duration": "10 weeks",
                "level": "advanced",
                "students_enrolled": 2150,
                "rating": 4.9,
            },
            {
                "title": "JavaScript Essentials",
                "description": "Master JavaScript fundamentals and learn how to build interactive web applications.",
                "category": categories[2],
                "instructor": "Mike Davis",
                "duration": "6 weeks",
                "level": "beginner",
                "students_enrolled": 8900,
                "rating": 4.7,
            },
            {
                "title": "Data Science with Python",
                "description": "Learn data science using Python libraries like Pandas, NumPy, and Scikit-learn. Apply your skills to real-world datasets.",
                "category": categories[1],
                "instructor": "Dr. Emily Chen",
                "duration": "12 weeks",
                "level": "intermediate",
                "students_enrolled": 3210,
                "rating": 4.8,
            },
            {
                "title": "React.js Mastery",
                "description": "Build modern web applications with React. Learn hooks, state management, and best practices.",
                "category": categories[2],
                "instructor": "Alex Turner",
                "duration": "8 weeks",
                "level": "intermediate",
                "students_enrolled": 4560,
                "rating": 4.6,
            },
            {
                "title": "Business Strategy 101",
                "description": "Learn the fundamentals of business strategy and competitive analysis.",
                "category": categories[3],
                "instructor": "Robert Wilson",
                "duration": "4 weeks",
                "level": "beginner",
                "students_enrolled": 2890,
                "rating": 4.5,
            },
        ]

        courses = []
        for data in courses_data:
            course = Course.objects.create(**data)
            courses.append(course)
        self.stdout.write(self.style.SUCCESS(f'Created {len(courses)} courses'))

        # Create study materials
        materials_data = [
            {
                "course": courses[0],
                "title": "Python Basics Cheat Sheet",
                "material_type": "notes",
                "description": "Quick reference guide for Python syntax and common operations",
                "file_size": 250,
            },
            {
                "course": courses[0],
                "title": "Python Programming Guide",
                "material_type": "ebook",
                "description": "Comprehensive e-book covering Python fundamentals",
                "file_size": 5400,
            },
            {
                "course": courses[2],
                "title": "JavaScript Practice Exercises",
                "material_type": "worksheet",
                "description": "100 practice problems with solutions",
                "file_size": 1200,
            },
            {
                "course": courses[3],
                "title": "Data Science Summary",
                "material_type": "summary",
                "description": "Key concepts and algorithms overview",
                "file_size": 800,
            },
            {
                "course": courses[4],
                "title": "React Hooks Guide",
                "material_type": "notes",
                "description": "Complete guide to React hooks and custom hooks",
                "file_size": 350,
            },
        ]

        materials = []
        for data in materials_data:
            material = StudyMaterial.objects.create(**data)
            material.downloads = 150
            material.save()
            materials.append(material)
        self.stdout.write(self.style.SUCCESS(f'Created {len(materials)} study materials'))

        # Create question banks
        banks_data = [
            {
                "course": courses[0],
                "title": "Python Basics Quiz",
                "description": "Test your knowledge of Python fundamentals",
                "difficulty": "easy",
            },
            {
                "course": courses[2],
                "title": "JavaScript Advanced Quiz",
                "description": "Challenge yourself with advanced JavaScript questions",
                "difficulty": "hard",
            },
            {
                "course": courses[4],
                "title": "React Components Quiz",
                "description": "Questions about React components and hooks",
                "difficulty": "medium",
            },
        ]

        banks = []
        for data in banks_data:
            bank = QuestionBank.objects.create(**data)
            banks.append(bank)
        self.stdout.write(self.style.SUCCESS(f'Created {len(banks)} question banks'))

        # Create questions
        questions_data = [
            {
                "question_bank": banks[0],
                "question_type": "single_choice",
                "question_text": "What is the correct way to create a list in Python?",
                "option_a": "my_list = [1, 2, 3]",
                "option_b": "my_list = (1, 2, 3)",
                "option_c": "my_list = {1, 2, 3}",
                "option_d": "my_list = <1, 2, 3>",
                "correct_answer": "A",
                "marks": 1,
                "explanation": "Square brackets [] are used to create lists in Python.",
                "order": 1,
            },
            {
                "question_bank": banks[0],
                "question_type": "multiple_choice",
                "question_text": "Which of the following are Python data types? (Select all that apply)",
                "option_a": "Integer",
                "option_b": "String",
                "option_c": "Boolean",
                "option_d": "Character",
                "correct_answer": "A,B,C",
                "marks": 2,
                "explanation": "Integer, String, and Boolean are Python data types. 'Character' is not a built-in Python type.",
                "order": 2,
            },
            {
                "question_bank": banks[0],
                "question_type": "true_false",
                "question_text": "In Python, dictionaries are ordered collections.",
                "option_a": "True",
                "option_b": "False",
                "correct_answer": "A",
                "marks": 1,
                "explanation": "As of Python 3.7+, dictionaries maintain insertion order.",
                "order": 3,
            },
            {
                "question_bank": banks[1],
                "question_type": "single_choice",
                "question_text": "What does 'this' keyword refer to in JavaScript?",
                "option_a": "The object that called the function",
                "option_b": "The function itself",
                "option_c": "The global window object",
                "option_d": "The parent scope",
                "correct_answer": "A",
                "marks": 1,
                "explanation": "'this' refers to the object that called the function in most cases.",
                "order": 1,
            },
            {
                "question_bank": banks[2],
                "question_type": "single_choice",
                "question_text": "What is the purpose of React hooks?",
                "option_a": "To manage component state and side effects in functional components",
                "option_b": "To create class components",
                "option_c": "To optimize rendering performance",
                "option_d": "To handle API requests",
                "correct_answer": "A",
                "marks": 1,
                "explanation": "React hooks like useState and useEffect allow functional components to use state and lifecycle features.",
                "order": 1,
            },
        ]

        questions = []
        for data in questions_data:
            question = Question.objects.create(**data)
            questions.append(question)

        self.stdout.write(self.style.SUCCESS(f'Created {len(questions)} questions'))

        # Update question bank total_questions
        for bank in banks:
            bank.total_questions = bank.questions.count()
            bank.save()

        self.stdout.write(self.style.SUCCESS('\n✅ Sample data loaded successfully!'))
        self.stdout.write(f'Categories: {CourseCategory.objects.count()}')
        self.stdout.write(f'Courses: {Course.objects.count()}')
        self.stdout.write(f'Study Materials: {StudyMaterial.objects.count()}')
        self.stdout.write(f'Question Banks: {QuestionBank.objects.count()}')
        self.stdout.write(f'Questions: {Question.objects.count()}')
