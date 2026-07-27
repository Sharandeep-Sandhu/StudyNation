# from django import forms
# from django.contrib.auth.models import User
# from courses.models import Question, QuestionBank, Course
# import csv
# from io import StringIO


# class AdminLoginForm(forms.Form):
#     """Admin login form"""
#     username = forms.CharField(
#         max_length=100,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your username',
#             'required': True
#         })
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your password',
#             'required': True
#         })
#     )


# class CSVUploadForm(forms.Form):
#     """CSV file upload form"""
#     csv_file = forms.FileField(
#         label='Upload CSV File',
#         widget=forms.FileInput(attrs={
#             'class': 'form-control',
#             'accept': '.csv',
#             'required': True
#         })
#     )
#     course = forms.ModelChoiceField(
#         queryset=Course.objects.all(),
#         label='Select Course',
#         widget=forms.Select(attrs={
#             'class': 'form-control',
#             'required': True
#         })
#     )
#     question_bank = forms.ModelChoiceField(
#         queryset=QuestionBank.objects.all(),
#         label='Select Question Bank',
#         widget=forms.Select(attrs={
#             'class': 'form-control',
#             'required': True
#         })
#     )

#     def clean_csv_file(self):
#         csv_file = self.cleaned_data.get('csv_file')
#         if csv_file:
#             if not csv_file.name.endswith('.csv'):
#                 raise forms.ValidationError('Please upload a valid CSV file')
#             if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
#                 raise forms.ValidationError('File size must be less than 5MB')
#         return csv_file

#     def parse_csv(self):
#         """Parse CSV file and return questions"""
#         csv_file = self.cleaned_data.get('csv_file')
#         if not csv_file:
#             return []

#         questions = []
#         try:
#             decoded_file = csv_file.read().decode('utf-8')
#             csv_reader = csv.DictReader(StringIO(decoded_file))

#             for row in csv_reader:
#                 question = {
#                     'question_text': row.get('question_text', '').strip(),
#                     'question_type': row.get('question_type', 'single_choice').strip(),
#                     'option_a': row.get('option_a', '').strip(),
#                     'option_b': row.get('option_b', '').strip(),
#                     'option_c': row.get('option_c', '').strip(),
#                     'option_d': row.get('option_d', '').strip(),
#                     'correct_answer': row.get('correct_answer', '').strip(),
#                     'marks': int(row.get('marks', 1)),
#                     'explanation': row.get('explanation', '').strip(),
#                 }
#                 questions.append(question)
#         except Exception as e:
#             raise forms.ValidationError(f'Error parsing CSV: {str(e)}')

#         return questions


# class ManualQuestionForm(forms.ModelForm):
#     """Form for manually adding questions"""
#     QUESTION_TYPES = [
#         ('single_choice', 'Single Choice (A/B/C/D)'),
#         ('multiple_choice', 'Multiple Choice (A,B,C)'),
#         ('true_false', 'True/False'),
#         ('numerical', 'Numerical Answer'),
#         ('matching', 'Matching'),
#     ]

#     question_type = forms.ChoiceField(
#         choices=QUESTION_TYPES,
#         widget=forms.Select(attrs={
#             'class': 'form-control',
#             'id': 'questionType'
#         })
#     )

#     class Meta:
#         model = Question
#         fields = ['question_text', 'question_type', 'option_a', 'option_b',
#                   'option_c', 'option_d', 'correct_answer', 'marks', 'explanation']
#         widgets = {
#             'question_text': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 4,
#                 'placeholder': 'Enter the question text'
#             }),
#             'option_a': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Option A (for choice questions)'
#             }),
#             'option_b': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Option B'
#             }),
#             'option_c': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Option C'
#             }),
#             'option_d': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Option D'
#             }),
#             'correct_answer': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'e.g., A or A,B or numerical value'
#             }),
#             'marks': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'min': 1,
#                 'value': 1
#             }),
#             'explanation': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Explanation for the answer (optional)'
#             }),
#         }


# class QuestionBankForm(forms.ModelForm):
#     """Form for creating/editing question banks"""
#     class Meta:
#         from courses.models import QuestionBank
#         model = QuestionBank
#         fields = ['title', 'description', 'difficulty']
#         widgets = {
#             'title': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Enter question bank title'
#             }),
#             'description': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Brief description'
#             }),
#             'difficulty': forms.Select(attrs={
#                 'class': 'form-control'
#             }),
#         }

# from django import forms
# from courses.models import Blog, Course, CourseCategory

# class BlogForm(forms.ModelForm):
#     # Extra media fields (add these fields to your Blog model in courses/models.py for full support)
#     video = forms.FileField(
#         required=False,
#         widget=forms.FileInput(attrs={
#             'class': 'form-control',
#             'accept': 'video/*'
#         }),
#         label="Upload Video (MP4, WebM, etc.)"
#     )
#     pdf = forms.FileField(
#         required=False,
#         widget=forms.FileInput(attrs={
#             'class': 'form-control',
#             'accept': '.pdf'
#         }),
#         label="Upload PDF Document"
#     )
#     ppt = forms.FileField(
#         required=False,
#         widget=forms.FileInput(attrs={
#             'class': 'form-control',
#             'accept': '.ppt,.pptx,application/vnd.ms-powerpoint'
#         }),
#         label="Upload PowerPoint (PPT/PPTX)"
#     )
#     images = forms.FileField(
#         required=False,
#         widget=forms.FileInput(attrs={
#             'class': 'form-control',
#             'accept': 'image/*'
#         }),
#         label="Upload Multiple Images (hold Ctrl/Cmd to select many)"
#     )

#     class Meta:
#         model = Blog
#         fields = ['title', 'content', 'author', 'image', 'published']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blog Title'}),
#             'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your blog content here...'}),
#             'author': forms.TextInput(attrs={'class': 'form-control'}),
#             'image': forms.FileInput(attrs={'class': 'form-control'}),
#         }

# class CourseForm(forms.ModelForm):
#     class Meta:
#         model = Course
#         fields = ['title', 'description', 'category', 'instructor', 'duration', 'level', 'thumbnail', 'students_enrolled', 'rating']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#             'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
#         }


# # ==================== NEW FORMS ====================

# class CategoryForm(forms.ModelForm):
#     """Form for Course Categories (Subjects)"""
#     class Meta:
#         from courses.models import CourseCategory
#         model = CourseCategory
#         fields = ['name', 'description', 'icon']  # icon optional if your model has it
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'e.g., Mathematics, Physics, Programming'
#             }),
#             'description': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Short description of this category/subject'
#             }),
#             'icon': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Optional icon class or emoji'
#             }),
#         }


# class ResourceForm(forms.ModelForm):
#     """Form for E-books and Handwritten Notes"""
#     RESOURCE_TYPES = [
#         ('ebook', 'E-Book (PDF)'),
#         ('handwritten', 'Handwritten Notes (PDF/Images)'),
#         ('other', 'Other Study Material'),
#     ]

#     resource_type = forms.ChoiceField(
#         choices=RESOURCE_TYPES,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     is_paid = forms.BooleanField(
#         required=False,
#         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         label="This is a Paid Resource"
#     )
#     price = forms.DecimalField(
#         required=False,
#         max_digits=8,
#         decimal_places=2,
#         widget=forms.NumberInput(attrs={
#             'class': 'form-control',
#             'step': '0.01',
#             'placeholder': '0.00'
#         }),
#         label="Price (if paid)"
#     )

#     class Meta:
#         from courses.models import Resource  # You need to create this model in courses/models.py
#         model = Resource
#         fields = ['title', 'description', 'file', 'author', 'resource_type', 'is_paid', 'price', 'course']
#         widgets = {
#             'title': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Resource Title'
#             }),
#             'description': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 4,
#                 'placeholder': 'Brief description of this resource'
#             }),
#             'file': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.pdf,.doc,.docx,image/*'
#             }),
#             'author': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Author / Teacher Name'
#             }),
#             'course': forms.Select(attrs={'class': 'form-control'}),
#         }


from django import forms
from courses.models import (
    Question,
    QuestionBank,
    Course,
    Blog,
    CourseCategory,
    Resource,
    Exam,
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
    """Bulk question import form — accepts CSV, Excel, or Word (.doc/.docx) files."""

    ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".docx", ".doc")
    # Word docs are heavier (hundreds of embedded equation images are common
    # in older past papers), so they get a larger ceiling than plain CSV/XLSX.
    MAX_SIZE_DEFAULT = 5 * 1024 * 1024  # 5MB
    MAX_SIZE_WORD = 25 * 1024 * 1024  # 25MB

    csv_file = forms.FileField(
        label="Upload CSV, Excel, or Word File",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".csv,.xlsx,.xls,.docx,.doc",
                "required": True,
            }
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

    # ---- Optional batch metadata, only used for Word imports ----
    # Word question banks (unlike the CSV/Excel template) don't carry
    # topic/paper_code/year/season/zone columns per-row, so we let the admin
    # set them once for the whole file. This is what lets imported questions
    # show up immediately in the user-facing Exam Builder, which filters by
    # these fields.
    topic = forms.CharField(
        required=False,
        label="Topic(s) (Word imports only)",
        help_text="Comma-separated, e.g. 'Vectors, 3D Geometry'. Applied to every question in the file.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 3D Geometry"}),
    )
    paper_code = forms.CharField(
        required=False,
        label="Paper Code (required for Word imports)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 0606/23"}),
    )
    year = forms.IntegerField(
        required=False,
        label="Year (Word imports only)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2019"}),
    )
    season = forms.ChoiceField(
        required=False,
        choices=[("", "—")] + list(Question.SEASON_CHOICES),
        label="Season (Word imports only)",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    zone = forms.ChoiceField(
        required=False,
        choices=Question.ZONE_CHOICES,
        label="Zone (Word imports only)",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean_csv_file(self):
        uploaded_file = self.cleaned_data.get("csv_file")
        if uploaded_file:
            name_lower = uploaded_file.name.lower()
            if not name_lower.endswith(self.ALLOWED_EXTENSIONS):
                raise forms.ValidationError(
                    "Please upload a valid CSV (.csv), Excel (.xlsx, .xls), "
                    "or Word (.docx, .doc) file"
                )
            is_word = name_lower.endswith((".doc", ".docx"))
            max_size = self.MAX_SIZE_WORD if is_word else self.MAX_SIZE_DEFAULT
            if uploaded_file.size > max_size:
                limit_mb = max_size // (1024 * 1024)
                raise forms.ValidationError(f"File size must be less than {limit_mb}MB")
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("csv_file")
        if uploaded_file and uploaded_file.name.lower().endswith((".doc", ".docx")):
            # The Exam Builder only lists questions that have a paper_code,
            # and Word files don't carry that per-row like CSV/Excel does —
            # so for Word imports it must be supplied here, or the imported
            # questions will silently never show up in the user-facing
            # Exam Builder.
            if not (cleaned_data.get("paper_code") or "").strip():
                self.add_error(
                    "paper_code",
                    "Required for Word imports — questions without a paper code "
                    "won't appear in the Exam Builder.",
                )
        return cleaned_data

    # Columns every row dict is normalised to, regardless of source format.
    _FIELDS = [
        "question_text",
        "question_type",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "marks",
        "explanation",
        "topic",
        "paper_code",
        "year",
        "season",
        "zone",
        "question_number",
    ]

    def parse_csv(self):
        """
        Parse the uploaded file (CSV, Excel, or Word) and return a list of
        question dictionaries. Kept as 'parse_csv' (rather than renaming) so
        existing call sites don't need to change; it now dispatches by file
        extension.
        """
        uploaded_file = self.cleaned_data.get("csv_file")
        if not uploaded_file:
            return []

        name_lower = uploaded_file.name.lower()
        if name_lower.endswith((".docx", ".doc")):
            return self._parse_word_rows(uploaded_file)
        elif name_lower.endswith((".xlsx", ".xls")):
            rows = self._parse_excel_rows(uploaded_file)
        else:
            rows = self._parse_csv_rows(uploaded_file)

        questions = []
        for row in rows:
            questions.append(self._normalize_row(row))
        return questions

    def _parse_word_rows(self, uploaded_file):
        """
        Parse a .doc/.docx past-paper file via docx_question_parser, then
        apply the optional batch metadata (topic/paper_code/year/season/zone)
        entered on this form to every question, since Word docs don't carry
        that per-row like the CSV/Excel template does.
        """
        from .docx_question_parser import parse_docx_questions

        rows = parse_docx_questions(uploaded_file)

        batch_topic = (self.cleaned_data.get("topic") or "").strip()
        batch_paper_code = (self.cleaned_data.get("paper_code") or "").strip()
        batch_year = self.cleaned_data.get("year")
        batch_season = (self.cleaned_data.get("season") or "").strip()
        batch_zone = (self.cleaned_data.get("zone") or "").strip()

        questions = []
        for row in rows:
            normalized = self._normalize_row(row)
            normalized["equation_images"] = row.get("equation_images", [])
            if batch_topic:
                normalized["topic"] = batch_topic
            if batch_paper_code:
                normalized["paper_code"] = batch_paper_code
            if batch_year:
                normalized["year"] = batch_year
            if batch_season:
                normalized["season"] = batch_season
            if batch_zone:
                normalized["zone"] = batch_zone
            questions.append(normalized)
        return questions

    def _parse_csv_rows(self, uploaded_file):
        import csv
        from io import StringIO

        try:
            decoded_file = uploaded_file.read().decode("utf-8-sig")
            return list(csv.DictReader(StringIO(decoded_file)))
        except UnicodeDecodeError:
            raise forms.ValidationError(
                "Could not read this CSV file — please save it with UTF-8 encoding and try again."
            )
        except Exception as e:
            raise forms.ValidationError(f"Error parsing CSV: {str(e)}")

    def _parse_excel_rows(self, uploaded_file):
        """
        Read the first worksheet of an .xlsx/.xls file with openpyxl and
        return a list of dicts keyed by the header row (row 1), matching
        the shape produced by csv.DictReader so downstream code is
        format-agnostic.
        """
        try:
            import openpyxl
        except ImportError:
            raise forms.ValidationError(
                "Excel support isn't installed on this server. Install the "
                "'openpyxl' package, or upload a .csv file instead."
            )

        if uploaded_file.name.lower().endswith(".xls"):
            raise forms.ValidationError(
                "Legacy .xls files aren't supported — please re-save as .xlsx or .csv and re-upload."
            )

        try:
            workbook = openpyxl.load_workbook(
                uploaded_file, read_only=True, data_only=True
            )
            sheet = workbook.worksheets[0]
            rows_iter = sheet.iter_rows(values_only=True)

            try:
                header = next(rows_iter)
            except StopIteration:
                return []

            headers = [
                (str(h).strip() if h is not None else f"column_{i}")
                for i, h in enumerate(header)
            ]

            rows = []
            for raw_row in rows_iter:
                if raw_row is None or all(cell is None for cell in raw_row):
                    continue  # skip fully blank rows
                row_dict = {}
                for i, header_name in enumerate(headers):
                    value = raw_row[i] if i < len(raw_row) else None
                    row_dict[header_name] = "" if value is None else value
                rows.append(row_dict)
            return rows
        except forms.ValidationError:
            raise
        except Exception as e:
            raise forms.ValidationError(f"Error parsing Excel file: {str(e)}")

    def _normalize_row(self, row):
        """Coerce a raw row dict (from CSV or Excel) into the canonical
        question dict shape, tolerating extra/missing columns and Excel's
        native (non-string) cell types."""

        def s(key, default=""):
            value = row.get(key, default)
            if value is None:
                return default
            return str(value).strip()

        marks_raw = row.get("marks", 1)
        try:
            marks = int(float(marks_raw)) if marks_raw not in (None, "") else 1
        except (TypeError, ValueError):
            marks = 1

        year_raw = row.get("year")
        year = None
        if year_raw not in (None, ""):
            try:
                year = int(float(year_raw))
            except (TypeError, ValueError):
                year = None

        return {
            "question_text": s("question_text"),
            "question_type": s("question_type", "single_choice") or "single_choice",
            "option_a": s("option_a"),
            "option_b": s("option_b"),
            "option_c": s("option_c"),
            "option_d": s("option_d"),
            "correct_answer": s("correct_answer"),
            "marks": marks,
            "explanation": s("explanation"),
            "topic": s("topic"),
            "paper_code": s("paper_code"),
            "year": year,
            "season": s("season").lower(),
            "zone": s("zone").lower(),
            "question_number": s("question_number"),
            "equation_images": row.get("equation_images", []),
        }



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
        fields = ["course", "title", "description", "difficulty"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-control"}),
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
                    "placeholder": "Brief description (optional)",
                }
            ),
            "difficulty": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.order_by("title")
        self.fields["course"].empty_label = "-- Select a course --"
        self.fields["description"].required = False
        self.fields["title"].required = True
        self.fields["course"].required = True


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
            "what_youll_learn",
            "prerequisites",
            "curriculum",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "thumbnail": forms.FileInput(attrs={"class": "form-control"}),
            "what_youll_learn": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "One point per line, e.g.\nComprehensive understanding of JEE\nPractical skills and real-world applications",
                }
            ),
            "prerequisites": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "One point per line, e.g.\nBasic understanding of JEE\nWillingness to learn and practice",
                }
            ),
            "curriculum": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "One module per line, e.g.\nModule 1: Introduction and Fundamentals\nModule 2: Core Concepts and Techniques",
                }
            ),
        }
        labels = {
            "what_youll_learn": "What You'll Learn",
            "prerequisites": "Prerequisites",
            "curriculum": "Course Curriculum",
            "students_enrolled": "Students Enrolled",
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


# ==================== EXAM BUILDER ====================
class ExamForm(forms.ModelForm):
    """Form for the exam name + the Settings tab of the Exam Builder"""

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
                attrs={"class": "form-control", "placeholder": "e.g. Mock Exam 1"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "duration_minutes": forms.NumberInput(
                attrs={"class": "form-control", "min": 5, "step": 5}
            ),
            "questions_per_page": forms.Select(
                choices=[(1, "One question per page"), (2, "Two questions per page"), (0, "All on continuous pages")],
                attrs={"class": "form-control"},
            ),
            "shuffle_questions": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
