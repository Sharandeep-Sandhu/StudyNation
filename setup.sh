#!/bin/bash

# Study Nation Setup Script
# This script sets up the Django development environment

echo "🚀 Setting up Study Nation..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "✨ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Run migrations
echo "🗄️  Applying database migrations..."
python manage.py migrate

# Load sample data
echo "📖 Loading sample data..."
python manage.py load_sample_data

# Create superuser
echo ""
echo "👤 Create a superuser account for admin access"
python manage.py createsuperuser

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server, run:"
echo "  source .venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Then visit:"
echo "  http://localhost:8000/ - Main website"
echo "  http://localhost:8000/admin/ - Admin panel"
echo "  http://localhost:8000/api/ - API endpoints"
