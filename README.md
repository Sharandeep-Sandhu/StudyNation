# Study Nation - Django + React Full-Stack Application

A comprehensive learning management system built with Django backend and React components embedded in Django templates. This platform provides courses, study materials, and question banks for students.

## Features

- **Course Management**: Browse and explore courses organized by categories
- **Study Materials**: Access e-books, notes, worksheets, and summaries
- **Question Banks**: Practice with various types of questions (single choice, multiple choice, true/false, numerical, matching)
- **Responsive Design**: Modern, mobile-friendly interface
- **Admin Dashboard**: Easy content management through Django admin
- **REST API**: Full REST API for integration with external applications

## Technology Stack

### Backend

- **Django** 6.0.6 - Python web framework
- **Django REST Framework** 3.14.0 - REST API development
- **PostgreSQL** - Database (can use SQLite for development)
- **django-cors-headers** - CORS support for API requests

### Frontend

- **React** 19 - UI library (embedded in Django templates)
- **Vanilla JavaScript** - For interactive components
- **HTML5 & CSS3** - Responsive styling

## Project Structure

```
.
├── config/                 # Django project settings
│   ├── settings.py        # Project settings
│   ├── urls.py           # Main URL routing
│   └── wsgi.py           # WSGI configuration
├── courses/              # Courses app
│   ├── models.py         # Database models
│   ├── views.py          # View logic
│   ├── urls.py           # Course URL routing
│   ├── admin.py          # Admin configuration
│   └── templates/        # Django templates
├── api/                  # API app
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API viewsets
│   └── urls.py           # API URL routing
├── templates/            # Base templates
├── manage.py             # Django management command
└── requirements.txt      # Python dependencies
```

## Models

### CourseCategory

- Name, description, icon
- Used to organize courses by subject

### Course

- Title, description, category, instructor, duration, level
- Rating, students enrolled, thumbnail image
- Related: StudyMaterials, QuestionBanks

### StudyMaterial

- Title, type (notes, ebook, worksheet, summary)
- File attachment, file size, download count
- Related: Course

### QuestionBank

- Title, description, difficulty level
- Related: Questions, Course

### Question

- Question text, type (single choice, multiple choice, true/false, numerical, matching)
- Options (A, B, C, D), correct answer, marks, explanation
- Related: QuestionBank

## Setup Instructions

### Prerequisites

- Python 3.9+
- pip or virtual environment manager
- PostgreSQL (optional, SQLite works for development)

### Installation

1. **Clone the repository and navigate to the project:**

   ```bash
   cd /path/to/project
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations:**

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser for admin access:**

   ```bash
   python manage.py createsuperuser
   ```

6. **Collect static files (for production):**

   ```bash
   python manage.py collectstatic
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000/`

## Usage

### Admin Panel

Access the Django admin panel at `/admin/` with your superuser credentials to:

- Create and manage courses
- Add categories and instructors
- Upload study materials
- Create question banks and questions

### Frontend Pages

- **Home** (`/`) - Main landing page with featured courses
- **Courses** (`/courses/`) - Browse all courses with filtering
- **Course Detail** (`/courses/<id>/`) - View course details, materials, and questions
- **Resources** (`/resources/`) - Free learning materials
- **Contact** (`/contact/`) - Contact form and information

### API Endpoints

- `GET /api/categories/` - List all course categories
- `GET /api/courses/` - List all courses
- `GET /api/courses/<id>/` - Get course details
- `GET /api/courses/by_category/?category_id=<id>` - Courses by category
- `GET /api/courses/search/?q=<query>` - Search courses
- `GET /api/study-materials/?course_id=<id>` - Study materials for a course
- `GET /api/question-banks/?course_id=<id>` - Question banks for a course
- `GET /api/questions/?question_bank_id=<id>` - Questions for a bank

## Configuration

### Database Setup (PostgreSQL)

Update `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'learning_hub',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Environment Variables

Create a `.env` file in the project root:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/learning_hub
ALLOWED_HOSTS=localhost,127.0.0.1
```

Then load it in settings.py using `python-decouple`.

## API Examples

### Get all courses

```bash
curl http://localhost:8000/api/courses/
```

### Get courses by category

```bash
curl http://localhost:8000/api/courses/by_category/?category_id=1
```

### Search courses

```bash
curl http://localhost:8000/api/courses/search/?q=python
```

### Get course details with materials and questions

```bash
curl http://localhost:8000/api/courses/1/
```

## Frontend Components

The application uses React components embedded in Django templates:

- **Navigation** - Header with navigation links
- **Hero Section** - Landing page hero with call-to-action
- **Course Card** - Reusable course display component
- **Filters** - Category and level filtering
- **Tabs** - Course details with overview, materials, and questions tabs
- **Forms** - Contact form with validation

## Styling

The application uses custom CSS with a modern design featuring:

- Gradient purple theme (#667eea to #764ba2)
- Responsive grid layouts
- Card-based components
- Smooth transitions and hover effects
- Mobile-first responsive design

## Deployment

### Vercel Deployment

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Configure environment variables in Vercel dashboard
4. Set build command: `pip install -r requirements.txt && python manage.py collectstatic`
5. Set start command: `gunicorn config.wsgi`

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support, email support@studynation.com or create an issue on GitHub.

## Future Enhancements

- User authentication and course enrollment
- Certificate generation
- Discussion forums
- Progress tracking
- Video content integration
- Live classes and webinars
- Advanced analytics
- Mobile app
