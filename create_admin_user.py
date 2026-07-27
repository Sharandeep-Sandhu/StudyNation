#!/usr/bin/env python
"""
Script to create a test admin user for the Study Nation platform.
Usage: python create_admin_user.py
"""

import os
import django
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from admin_panel.models import AdminUser


def create_admin():
    """Create a test admin user"""

    # Check if admin already exists
    if User.objects.filter(username="admin").exists():
        print("❌ Admin user 'admin' already exists!")
        return

    # Create Django user
    user = User.objects.create_user(
        username="admin",
        email="admin@learninghub.com",
        password="admin123",
        first_name="Admin",
        last_name="User",
    )
    user.is_staff = True
    user.is_superuser = False
    user.save()

    # Create admin profile
    admin_profile = AdminUser.objects.create(
        user=user, is_admin=True, can_upload_csv=True, can_manage_questions=True
    )

    print("✅ Admin user created successfully!")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"   Email: admin@learninghub.com")
    print(f"\n🔐 Login at: http://localhost:8000/admin-panel/login/")


if __name__ == "__main__":
    create_admin()
