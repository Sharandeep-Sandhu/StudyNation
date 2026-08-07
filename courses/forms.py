from django import forms
from courses.models import (
    Question,
    QuestionBank,
    Course,
    Blog,
    CourseCategory,
    Resource,
    QuestionList,
)


# ==================== ADMIN AUTHENTICATION ====================
class AdminLoginForm(forms.Form):
    """Admin login form"""

    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your username",
                "required": True,
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
                "required": True,
            }
        )
    )


# ==================== CSV UPLOAD ====================
class CSVUploadForm(forms.Form):
    """CSV file upload form for bulk question import"""

    csv_file = forms.FileField(
        label="Upload CSV File",
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".csv", "required": True}
        ),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        label="Select Course",
        widget=forms.Select(attrs={"class": "form-control", "required": True}),
    )
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        label="Select Question Bank",
        widget=forms.Select(attrs={"class": "form-control", "required": True}),
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get("csv_file")
        if csv_file:
            if not csv_file.name.endswith(".csv"):
                raise forms.ValidationError("Please upload a valid CSV file")
            if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File size must be less than 5MB")
        return csv_file

    def parse_csv(self):
        """Parse CSV file and return list of question dictionaries"""
        import csv
        from io import StringIO

        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            return []

        questions = []
        try:
            decoded_file = csv_file.read().decode("utf-8")
            csv_reader = csv.DictReader(StringIO(decoded_file))

            for row in csv_reader:
                question = {
                    "question_text": row.get("question_text", "").strip(),
                    "question_type": row.get("question_type", "single_choice").strip(),
                    "option_a": row.get("option_a", "").strip(),
                    "option_b": row.get("option_b", "").strip(),
                    "option_c": row.get("option_c", "").strip(),
                    "option_d": row.get("option_d", "").strip(),
                    "correct_answer": row.get("correct_answer", "").strip(),
                    "marks": int(row.get("marks", 1) or 1),
                    "explanation": row.get("explanation", "").strip(),
                }
                questions.append(question)
        except Exception as e:
            raise forms.ValidationError(f"Error parsing CSV: {str(e)}")

        return questions


# ==================== MANUAL QUESTION ENTRY ====================
class ManualQuestionForm(forms.ModelForm):
    """Form for manually adding questions"""

    QUESTION_TYPES = [
        ("single_choice", "Single Choice (A/B/C/D)"),
        ("multiple_choice", "Multiple Choice (A,B,C)"),
        ("true_false", "True/False"),
        ("numerical", "Numerical Answer"),
        ("matching", "Matching"),
    ]

    question_type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        widget=forms.Select(attrs={"class": "form-control", "id": "questionType"}),
    )

    class Meta:
        model = Question
        fields = [
            "question_text",
            "question_type",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "marks",
            "explanation",
        ]
        widgets = {
            "question_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter the question text",
                }
            ),
            "option_a": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Option A"}
            ),
            "option_b": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Option B"}
            ),
            "option_c": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Option C"}
            ),
            "option_d": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Option D"}
            ),
            "correct_answer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., A or A,B or numerical value",
                }
            ),
            "marks": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "value": 1}
            ),
            "explanation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Explanation for the answer (optional)",
                }
            ),
        }


# ==================== QUESTION BANK ====================
class QuestionBankForm(forms.ModelForm):
    """Form for creating/editing question banks"""

    class Meta:
        model = QuestionBank
        fields = ["title", "description", "difficulty"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter question bank title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Brief description",
                }
            ),
            "difficulty": forms.Select(attrs={"class": "form-control"}),
        }


# ==================== BLOG ====================
class BlogForm(forms.ModelForm):
    """Form for creating/editing blog posts (with media support)"""

    video = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "video/*"}),
        label="Upload Video (MP4, WebM, etc.)",
    )
    pdf = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".pdf"}),
        label="Upload PDF Document",
    )
    ppt = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".ppt,.pptx"}),
        label="Upload PowerPoint (PPT/PPTX)",
    )

    class Meta:
        model = Blog
        fields = [
            "title",
            "content",
            "author",
            "image",
            "published",
            "video",
            "pdf",
            "ppt",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Blog Title"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 12,
                    "placeholder": "Write your blog content here...",
                }
            ),
            "author": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Author Name"}
            ),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }


# ==================== COURSE ====================
class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "category",
            "instructor",
            "duration",
            "level",
            "thumbnail",
            "students_enrolled",
            "rating",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "thumbnail": forms.FileInput(attrs={"class": "form-control"}),
        }


# ==================== COURSE CATEGORY ====================
class CategoryForm(forms.ModelForm):
    """Form for Course Categories / Subjects"""

    class Meta:
        model = CourseCategory
        fields = ["name", "description", "icon"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Mathematics, Physics, Programming",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Short description of this category",
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional icon class (e.g., fa-book)",
                }
            ),
        }


# ==================== RESOURCE ====================
class ResourceForm(forms.ModelForm):
    """Form for E-books, Handwritten Notes & Study Materials"""

    RESOURCE_TYPES = [
        ("ebook", "E-Book (PDF)"),
        ("handwritten", "Handwritten Notes"),
        ("other", "Other Study Material"),
    ]

    resource_type = forms.ChoiceField(
        choices=RESOURCE_TYPES, widget=forms.Select(attrs={"class": "form-control"})
    )

    is_paid = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="This is a Paid Resource",
    )

    price = forms.DecimalField(
        required=False,
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
        ),
        label="Price (if paid)",
    )

    class Meta:
        model = Resource
        fields = [
            "title",
            "description",
            "file",
            "author",
            "resource_type",
            "is_paid",
            "price",
            "course",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Resource Title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Brief description",
                }
            ),
            "file": forms.FileInput(
                attrs={"class": "form-control", "accept": ".pdf,.doc,.docx,image/*"}
            ),
            "author": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Author / Teacher Name"}
            ),
            "course": forms.Select(attrs={"class": "form-control"}),
        }


# ==================== STUDENT AUTHENTICATION ====================
from django.contrib.auth.models import User
from courses.models import Exam


class StudentSignupForm(forms.Form):
    """Signup form for public, student-facing accounts."""

    full_name = forms.CharField(
        max_length=150,
        label="Full name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your full name"}
        ),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Choose a username"}
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "you@example.com"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Create a password"}
        ),
        min_length=8,
        help_text="At least 8 characters. Avoid common or overly simple passwords.",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        # Run Django's AUTH_PASSWORD_VALIDATORS (similarity, common, numeric, etc.)
        from django.contrib.auth.password_validation import validate_password

        user = User(
            username=self.cleaned_data.get("username") or "",
            email=self.cleaned_data.get("email") or "",
            first_name=(self.cleaned_data.get("full_name") or "").split(" ")[0],
        )
        validate_password(password, user=user)
        return password

    def save(self):
        full_name = self.cleaned_data["full_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=first_name,
            last_name=last_name,
        )
        from courses.models import StudentProfile

        StudentProfile.objects.create(user=user)
        return user


class StudentLoginForm(forms.Form):
    """Unified login form for student and admin accounts."""

    username = forms.CharField(
        max_length=150,
        label="Username or email",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username or email", "autocomplete": "username"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password", "autocomplete": "current-password"}
        ),
    )


# ==================== STUDENT EXAM BUILDER ====================
class StudentExamForm(forms.ModelForm):
    """Settings tab of the student-facing Exam Builder."""

    class Meta:
        model = Exam
        fields = [
            "name",
            "category",
            "duration_minutes",
            "questions_per_page",
            "shuffle_questions",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. My Practice Exam"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "duration_minutes": forms.NumberInput(
                attrs={"class": "form-control", "min": 5, "step": 5}
            ),
            "questions_per_page": forms.Select(
                choices=[
                    (1, "One question per page"),
                    (2, "Two questions per page"),
                    (0, "All on continuous pages"),
                ],
                attrs={"class": "form-control"},
            ),
            "shuffle_questions": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class StudentQuestionListForm(forms.ModelForm):
    """Rename/re-categorise form for the simplified Build Question List tool."""

    class Meta:
        model = QuestionList
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Functions Practice Set"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
        }
