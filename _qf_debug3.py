import os, django, traceback
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# Simulate missing column by monkeypatching
django.setup()
from django.db.models.query import QuerySet
from courses.models import DiscussionPost
from django.db import connection
from django.db.utils import ProgrammingError

# Render template with a post that has no user (deleted user) 
from django.contrib.auth.models import User
from courses.models import DiscussionBoard, DiscussionPost, DiscussionReply
# orphan user access
posts = DiscussionPost.objects.select_related("user", "board").prefetch_related("replies__user")
for p in posts:
    print(p.id, p.user_id, p.user.username if p.user_id else None)
    for r in p.replies.all():
        print("  reply", r.id, r.user_id, getattr(r.user, "username", None))
