# Study Nation - API Documentation

## Overview

The Study Nation API provides REST endpoints for accessing courses, study materials, question banks, and other educational content.

**Base URL:** `http://localhost:8000/api/`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible. In a future version, authentication can be implemented using token-based authentication.

## Response Format

All responses are in JSON format. Successful responses include:

```json
{
  "count": 10,
  "next": "http://localhost:8000/api/courses/?page=2",
  "previous": null,
  "results": [...]
}
```

Error responses include:

```json
{
  "error": "Description of the error"
}
```

## Pagination

List endpoints support pagination with 20 items per page by default.

**Query Parameters:**

- `page`: Page number (default: 1)

Example: `/api/courses/?page=2`

## Endpoints

### Course Categories

#### List All Categories

```
GET /api/categories/
```

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Programming",
      "description": "Learn to code with Python, JavaScript, and more",
      "icon": "💻",
      "courses_count": 2,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Query Parameters:**

- `search`: Search by name or description
- `ordering`: Order by field (e.g., `?ordering=name`)

#### Get Category Details

```
GET /api/categories/{id}/
```

**Response:**

```json
{
  "id": 1,
  "name": "Programming",
  "description": "Learn to code with Python, JavaScript, and more",
  "icon": "💻",
  "courses_count": 2,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Courses

#### List All Courses

```
GET /api/courses/
```

**Response:**

```json
{
  "count": 6,
  "results": [
    {
      "id": 1,
      "title": "Python for Beginners",
      "description": "Learn Python programming from scratch...",
      "category": {
        "id": 1,
        "name": "Programming",
        "description": "...",
        "icon": "💻",
        "courses_count": 2,
        "created_at": "2024-01-15T10:30:00Z"
      },
      "level": "beginner",
      "students_enrolled": 5420,
      "rating": 4.8,
      "thumbnail": "http://localhost:8000/media/course_thumbnails/python.jpg",
      "created_at": "2024-01-20T15:45:00Z"
    }
  ]
}
```

**Query Parameters:**

- `search`: Search by title or description
- `category`: Filter by category ID (e.g., `?category=1`)
- `level`: Filter by level (beginner, intermediate, advanced)
- `ordering`: Order results (e.g., `?ordering=-created_at`)

#### Get Course Details

```
GET /api/courses/{id}/
```

**Response:**

```json
{
  "id": 1,
  "title": "Python for Beginners",
  "description": "Learn Python programming from scratch...",
  "category": {...},
  "instructor": "John Smith",
  "duration": "8 weeks",
  "level": "beginner",
  "students_enrolled": 5420,
  "rating": 4.8,
  "thumbnail": "...",
  "study_materials": [
    {
      "id": 1,
      "title": "Python Basics Cheat Sheet",
      "material_type": "notes",
      "description": "Quick reference guide...",
      "file": "http://localhost:8000/media/study_materials/cheatsheet.pdf",
      "file_size": 250,
      "downloads": 150,
      "created_at": "2024-01-20T16:00:00Z"
    }
  ],
  "question_banks": [
    {
      "id": 1,
      "title": "Python Basics Quiz",
      "description": "Test your knowledge...",
      "difficulty": "easy",
      "question_count": 5,
      "questions": [...]
    }
  ],
  "created_at": "2024-01-20T15:45:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

#### Get Courses by Category

```
GET /api/courses/by_category/?category_id={id}
```

**Required Parameters:**

- `category_id`: Category ID

**Response:** Same as list courses

#### Search Courses

```
GET /api/courses/search/?q={query}
```

**Required Parameters:**

- `q`: Search query (minimum 2 characters)

**Response:** Same as list courses

---

### Study Materials

#### List Study Materials

```
GET /api/study-materials/
```

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "title": "Python Basics Cheat Sheet",
      "material_type": "notes",
      "description": "Quick reference guide for Python syntax...",
      "file": "http://localhost:8000/media/study_materials/cheatsheet.pdf",
      "file_size": 250,
      "downloads": 150,
      "created_at": "2024-01-20T16:00:00Z"
    }
  ]
}
```

**Query Parameters:**

- `course_id`: Filter by course ID (e.g., `?course_id=1`)

#### Get Study Material Details

```
GET /api/study-materials/{id}/
```

---

### Question Banks

#### List Question Banks

```
GET /api/question-banks/
```

**Response:**

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "title": "Python Basics Quiz",
      "description": "Test your knowledge of Python fundamentals",
      "difficulty": "easy",
      "question_count": 5,
      "questions": [
        {
          "id": 1,
          "question_type": "single_choice",
          "question_text": "What is the correct way to create a list?",
          "option_a": "my_list = [1, 2, 3]",
          "option_b": "my_list = (1, 2, 3)",
          "option_c": "my_list = {1, 2, 3}",
          "option_d": "my_list = <1, 2, 3>",
          "correct_answer": "A",
          "marks": 1,
          "explanation": "Square brackets [] are used for lists",
          "order": 1
        }
      ],
      "created_at": "2024-01-20T16:15:00Z"
    }
  ]
}
```

**Query Parameters:**

- `course_id`: Filter by course ID (e.g., `?course_id=1`)

#### Get Question Bank Details

```
GET /api/question-banks/{id}/
```

---

### Questions

#### List Questions

```
GET /api/questions/
```

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "question_type": "single_choice",
      "question_text": "What is the correct way to create a list?",
      "option_a": "my_list = [1, 2, 3]",
      "option_b": "my_list = (1, 2, 3)",
      "option_c": "my_list = {1, 2, 3}",
      "option_d": "my_list = <1, 2, 3>",
      "correct_answer": "A",
      "marks": 1,
      "explanation": "Square brackets [] are used for lists",
      "order": 1
    }
  ]
}
```

**Query Parameters:**

- `question_bank_id`: Filter by question bank ID

#### Get Question Details

```
GET /api/questions/{id}/
```

---

## Question Types

The API supports the following question types:

### Single Choice (single_choice)

Users select one correct answer from multiple options.

**Fields:**

- `option_a`, `option_b`, `option_c`, `option_d`: Available options
- `correct_answer`: Single letter (A, B, C, or D)

### Multiple Choice (multiple_choice)

Users select multiple correct answers.

**Fields:**

- `option_a`, `option_b`, `option_c`, `option_d`: Available options
- `correct_answer`: Comma-separated letters (e.g., "A,B,C")

### True/False (true_false)

Users select true or false.

**Fields:**

- `option_a`: "True"
- `option_b`: "False"
- `correct_answer`: "A" for true, "B" for false

### Numerical (numerical)

Users enter a numerical answer.

**Fields:**

- `correct_answer`: Expected numerical value

### Matching (matching)

Users match items from two columns.

**Fields:**

- `correct_answer`: JSON format with mappings

---

## HTTP Status Codes

| Code | Meaning                                     |
| ---- | ------------------------------------------- |
| 200  | OK - Request successful                     |
| 201  | Created - Resource created                  |
| 204  | No Content - Request successful, no content |
| 400  | Bad Request - Invalid parameters            |
| 404  | Not Found - Resource not found              |
| 500  | Internal Server Error - Server error        |

---

## Example Requests

### Python

```python
import requests

# Get all courses
response = requests.get('http://localhost:8000/api/courses/')
courses = response.json()

# Get courses by category
params = {'category_id': 1}
response = requests.get('http://localhost:8000/api/courses/by_category/', params=params)
courses = response.json()

# Search courses
params = {'q': 'python'}
response = requests.get('http://localhost:8000/api/courses/search/', params=params)
courses = response.json()

# Get course details
response = requests.get('http://localhost:8000/api/courses/1/')
course = response.json()
```

### JavaScript/Fetch

```javascript
// Get all courses
fetch("http://localhost:8000/api/courses/")
  .then((response) => response.json())
  .then((data) => console.log(data));

// Get course details
fetch("http://localhost:8000/api/courses/1/")
  .then((response) => response.json())
  .then((course) => console.log(course));

// Search courses
fetch("http://localhost:8000/api/courses/search/?q=python")
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### cURL

```bash
# Get all courses
curl http://localhost:8000/api/courses/

# Get course details
curl http://localhost:8000/api/courses/1/

# Search courses
curl 'http://localhost:8000/api/courses/search/?q=python'

# Get courses by category
curl 'http://localhost:8000/api/courses/by_category/?category_id=1'
```

---

## Rate Limiting

Currently, there is no rate limiting. In production, rate limiting should be implemented to prevent abuse.

## CORS

The API has CORS enabled for all origins in development. In production, configure CORS to only allow your frontend domain.

## Error Handling

### Example Error Response

```json
{
  "error": "category_id is required"
}
```

### HTTP 404 Not Found

```json
{
  "detail": "Not found."
}
```

---

## Future API Features

Planned features for future versions:

- [ ] User authentication and authorization
- [ ] Course enrollment and progress tracking
- [ ] User ratings and reviews
- [ ] Bookmarking and favorites
- [ ] Quiz submissions and scoring
- [ ] Discussion forums and comments
- [ ] Search filters and advanced filtering
- [ ] Export course data (PDF, CSV)
- [ ] Rate limiting and throttling
- [ ] API versioning
- [ ] WebSocket support for real-time features

---

## Support

For API issues or questions, please:

1. Check this documentation
2. Review the code examples
3. Check the Django admin panel at `/admin/`
4. Create an issue on GitHub

---

## Version History

### v1.0 (Current)

- Initial API release
- Courses, categories, study materials, and question banks
- Public read-only endpoints
