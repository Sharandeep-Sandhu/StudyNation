import os, django, traceback
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("PRAGMA table_info(courses_discussionpost)")
    print("post cols", [r[1] for r in cur.fetchall()])
from courses.models import DiscussionBoard, DiscussionPost
print("boards", DiscussionBoard.objects.count(), "posts", DiscussionPost.objects.count())
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from courses.views import QuestionFormView
rf = RequestFactory()
req = rf.get("/question-form/")
req.user = AnonymousUser()
try:
    resp = QuestionFormView.as_view()(req)
    if hasattr(resp, "render"):
        resp.render()
    print("view ok", resp.status_code, len(resp.content))
except Exception:
    traceback.print_exc()
