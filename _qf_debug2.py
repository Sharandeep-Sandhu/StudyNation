import os, django, traceback
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from courses.models import DiscussionPost, DiscussionReply
from courses.templatetags.course_extras import chat_math
for p in DiscussionPost.objects.all():
    try:
        out = chat_math(p.content)
        print("post", p.id, "ok", len(out))
    except Exception as e:
        print("post", p.id, "FAIL", e)
        traceback.print_exc()
for r in DiscussionReply.objects.all():
    try:
        print("reply", r.id, "was_edited", r.was_edited, "vid", r.video_solution_url)
        chat_math(r.content)
    except Exception as e:
        print("reply FAIL", r.id, e)
        traceback.print_exc()
# simulate missing video_solution_url field access pattern
from django.db import connection
print("SQL", str(DiscussionPost.objects.all().query)[:200])
