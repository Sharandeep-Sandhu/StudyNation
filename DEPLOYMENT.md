# Study Nation - Deployment Guide

This guide provides instructions for deploying the Study Nation application to various platforms.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Vercel Deployment](#vercel-deployment)
4. [Heroku Deployment](#heroku-deployment)
5. [AWS Deployment](#aws-deployment)
6. [Production Checklist](#production-checklist)

## Local Development

### Quick Start

1. **Clone and navigate to the project:**

   ```bash
   cd /path/to/learning-hub
   ```

2. **Run the setup script:**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the development server:**

   ```bash
   source .venv/bin/activate
   python manage.py runserver
   ```

4. **Access the application:**
   - Website: http://localhost:8000/
   - Admin: http://localhost:8000/admin/
   - API: http://localhost:8000/api/

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load sample data
python manage.py load_sample_data

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Docker Deployment

### Prerequisites

- Docker installed (https://docker.com)
- Docker Compose installed

### Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# The application will be available at http://localhost:8000
```

### Docker Commands

```bash
# View logs
docker-compose logs -f web

# Run migrations manually
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Stop services
docker-compose down

# Remove volumes (careful - deletes database)
docker-compose down -v
```

## Vercel Deployment

Vercel is optimized for Next.js applications. For a Django application, you'll need a different approach:

### Option 1: Using Vercel with Django (Serverless)

1. **Add Vercel configuration file:**
   Create `vercel.json`:

   ```json
   {
     "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic",
     "outputDirectory": "staticfiles",
     "env": {
       "DJANGO_SETTINGS_MODULE": "config.settings"
     }
   }
   ```

2. **Deploy to Vercel:**
   ```bash
   npm i -g vercel
   vercel deploy
   ```

### Option 2: Vercel with External Backend

Deploy Django separately and connect to Vercel frontend:

1. Deploy Django to Heroku, AWS, or DigitalOcean
2. Update API endpoints in frontend to point to your backend
3. Deploy frontend to Vercel

## Heroku Deployment

### Prerequisites

- Heroku CLI installed
- Heroku account created

### Setup

1. **Create a Procfile:**

   ```
   web: gunicorn config.wsgi --log-file -
   ```

2. **Create runtime.txt:**

   ```
   python-3.11.0
   ```

3. **Update requirements.txt:**

   ```bash
   pip install gunicorn
   pip freeze > requirements.txt
   ```

4. **Create Heroku app:**

   ```bash
   heroku create your-app-name
   ```

5. **Set environment variables:**

   ```bash
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```

6. **Add PostgreSQL:**

   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

7. **Deploy:**

   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py load_sample_data
   heroku run python manage.py createsuperuser
   ```

8. **View logs:**
   ```bash
   heroku logs -t
   ```

## AWS Deployment

### Using Elastic Beanstalk

1. **Install EB CLI:**

   ```bash
   pip install awsebcli
   ```

2. **Initialize Elastic Beanstalk:**

   ```bash
   eb init -p python-3.11 learning-hub
   ```

3. **Create environment:**

   ```bash
   eb create production
   ```

4. **Set environment variables:**

   ```bash
   eb setenv DEBUG=False SECRET_KEY=your-key
   ```

5. **Deploy:**
   ```bash
   eb deploy
   ```

### Using EC2

1. **Launch EC2 instance:**
   - Ubuntu 20.04 LTS
   - t3.micro or larger

2. **SSH into instance:**

   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   ```

3. **Install dependencies:**

   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv postgresql nginx
   ```

4. **Clone repository:**

   ```bash
   git clone your-repo-url
   cd learning-hub
   ```

5. **Setup application:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py load_sample_data
   ```

6. **Configure Gunicorn:**

   ```bash
   pip install gunicorn
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```

7. **Configure Nginx as reverse proxy:**
   Create `/etc/nginx/sites-available/default`:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /path/to/staticfiles/;
       }

       location /media/ {
           alias /path/to/media/;
       }
   }
   ```

8. **Restart Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

## DigitalOcean Deployment

### Using App Platform

1. **Connect GitHub repository**
2. **Configure:**
   - Build command: `pip install -r requirements.txt && python manage.py collectstatic`
   - Run command: `gunicorn config.wsgi:application --bind 0.0.0.0:8000`
3. **Add PostgreSQL database**
4. **Set environment variables**
5. **Deploy**

### Using Droplet (VPS)

Similar to AWS EC2 deployment above.

## Production Checklist

Before deploying to production, ensure the following:

### Security

- [ ] Set `DEBUG = False` in settings.py
- [ ] Generate a strong `SECRET_KEY`
- [ ] Set appropriate `ALLOWED_HOSTS`
- [ ] Configure HTTPS/SSL
- [ ] Set secure cookies: `SESSION_COOKIE_SECURE = True`
- [ ] Set secure CSRF: `CSRF_COOKIE_SECURE = True`
- [ ] Add security headers
- [ ] Use environment variables for sensitive data
- [ ] Validate and sanitize user inputs

### Database

- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up regular backups
- [ ] Create database indexes for frequently queried fields
- [ ] Run `python manage.py migrate`
- [ ] Test database connectivity

### Performance

- [ ] Enable caching
- [ ] Use CDN for static files
- [ ] Compress static assets
- [ ] Set up database connection pooling
- [ ] Configure appropriate logging
- [ ] Monitor application performance

### Deployment

- [ ] Use a process manager (Supervisor, systemd)
- [ ] Set up log rotation
- [ ] Configure email for alerts
- [ ] Test the deployment in staging first
- [ ] Have a rollback plan
- [ ] Document deployment procedures

### Monitoring

- [ ] Set up error tracking (Sentry)
- [ ] Configure monitoring and alerts
- [ ] Set up log aggregation
- [ ] Monitor resource usage
- [ ] Track API performance

### Backup and Recovery

- [ ] Automate database backups
- [ ] Test backup restoration
- [ ] Keep offsite backups
- [ ] Document recovery procedures

## Environment Variables Reference

```
DEBUG=False                          # Disable debug mode
SECRET_KEY=<strong-random-key>       # Django secret key
ALLOWED_HOSTS=example.com            # Allowed hosts
DATABASE_ENGINE=postgresql           # Database engine
DATABASE_NAME=learning_hub           # Database name
DATABASE_USER=<db-user>              # Database user
DATABASE_PASSWORD=<db-password>      # Database password
DATABASE_HOST=localhost              # Database host
DATABASE_PORT=5432                   # Database port
STATIC_URL=/static/                  # Static files URL
MEDIA_URL=/media/                    # Media files URL
CORS_ALLOW_ALL_ORIGINS=False         # CORS settings
EMAIL_BACKEND=django.core.mail       # Email backend
EMAIL_HOST=smtp.gmail.com            # Email host
EMAIL_PORT=587                       # Email port
EMAIL_HOST_USER=<email>              # Email user
EMAIL_HOST_PASSWORD=<password>       # Email password
```

## Troubleshooting

### Common Issues

**Static files not loading:**

```bash
python manage.py collectstatic --noinput
```

**Database migration errors:**

```bash
python manage.py migrate --fake-initial
```

**Permission denied errors:**

```bash
sudo chown -R www-data:www-data /path/to/app
chmod -R 755 /path/to/app
```

**Port already in use:**

```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

## Support

For deployment issues, refer to the official Django deployment documentation:
https://docs.djangoproject.com/en/stable/howto/deployment/

## Next Steps

- [ ] Configure SSL/TLS certificates
- [ ] Set up automated backups
- [ ] Configure monitoring and logging
- [ ] Set up CI/CD pipeline
- [ ] Document deployment procedures for your team
