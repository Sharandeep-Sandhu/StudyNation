# Study Nation - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites

- Python 3.9+ installed
- Virtual environment support

### Step 1: Activate Environment (1 minute)

```bash
cd /vercel/share/v0-project
source .venv/bin/activate
```

### Step 2: Database is Ready ✓

✅ Database migrations already applied
✅ Sample data already loaded

### Step 3: Start Server (30 seconds)

```bash
python manage.py runserver
```

### Step 4: Open Browser (30 seconds)

```
Home: http://localhost:8000/
Admin: http://localhost:8000/admin/
API: http://localhost:8000/api/
```

## 📱 Main Pages

| Page               | URL              | Features                                     |
| ------------------ | ---------------- | -------------------------------------------- |
| **Home**           | `/`              | Featured courses, statistics, categories     |
| **Courses**        | `/courses/`      | Browse all courses, filter by category/level |
| **Course Details** | `/courses/{id}/` | Materials, question banks, course info       |
| **Resources**      | `/resources/`    | Free materials download                      |
| **Contact**        | `/contact/`      | Contact form and info                        |
| **Admin**          | `/admin/`        | Content management panel                     |

## 🔑 Admin Access

**Username:** (created during setup)
**Password:** (created during setup)

Or create new superuser:

```bash
python manage.py createsuperuser
```

## 📊 Sample Data Included

✅ 5 Course Categories
✅ 6 Sample Courses  
✅ 5 Study Materials
✅ 3 Question Banks
✅ 5 Sample Questions

All ready to explore!

## 🔌 API Examples

### Get All Courses

```bash
curl http://localhost:8000/api/courses/
```

### Get Courses by Category

```bash
curl "http://localhost:8000/api/courses/by_category/?category_id=1"
```

### Search Courses

```bash
curl "http://localhost:8000/api/courses/search/?q=python"
```

### Get Course Details

```bash
curl http://localhost:8000/api/courses/1/
```

## 🐳 Alternative: Docker Quick Start

If you prefer Docker:

```bash
docker-compose up -d
```

Then visit: http://localhost:8000

## 📚 Documentation

- **README.md** - Full documentation
- **DEPLOYMENT.md** - Deploy to production
- **API_DOCUMENTATION.md** - API reference
- **PROJECT_SUMMARY.md** - Architecture overview

## ⚡ Common Commands

```bash
# Start server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py load_sample_data

# Create database backups
python manage.py dumpdata > backup.json

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Django shell
python manage.py shell

# Run tests (when added)
python manage.py test
```

## 🎯 Next Steps

1. **Explore** - Browse the interface at http://localhost:8000/
2. **Login** - Use admin credentials at /admin/
3. **Customize** - Add your own courses and content
4. **Integrate** - Use the REST API for your applications
5. **Deploy** - Follow DEPLOYMENT.md for production

## 🚨 Troubleshooting

**Port 8000 already in use?**

```bash
python manage.py runserver 8001
```

**Want fresh data?**

```bash
python manage.py load_sample_data
```

**Permission issues?**

```bash
chmod +x setup.sh
```

## 📖 Key Features

✨ **Django Backend**

- 5 database models
- RESTful API
- Admin interface
- File uploads
- Database migrations

✨ **React Frontend**

- Responsive design
- Course filtering
- Interactive forms
- Mobile-friendly
- Modern UI

✨ **Documentation**

- 1600+ lines of guides
- API examples
- Deployment instructions
- Architecture overview

## 📞 Need Help?

1. Check README.md for common issues
2. Review DEPLOYMENT.md for setup problems
3. See API_DOCUMENTATION.md for API questions
4. Check Django docs: https://docs.djangoproject.com/

## 🎓 Learning Resources

- **Django Docs**: https://docs.djangoproject.com/
- **DRF Docs**: https://www.django-rest-framework.org/
- **React Docs**: https://react.dev/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

**Ready to go!** 🚀

Start the server and begin exploring Study Nation.
