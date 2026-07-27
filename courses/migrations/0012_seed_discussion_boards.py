from django.db import migrations
from django.utils.text import slugify


DEFAULT_BOARDS = [
    ("Fall 2026 Admitted Families", "Welcome and general chat for the Fall 2026 incoming class.", 1),
    ("First-Gen Families", "A space for first-generation college families to connect.", 2),
    ("First Year Families", "For families of first-year / freshman students.", 3),
    ("Out-of-State Families", "For families relocating from out of state.", 4),
]


def seed_boards(apps, schema_editor):
    DiscussionBoard = apps.get_model("courses", "DiscussionBoard")
    for name, description, order in DEFAULT_BOARDS:
        if not DiscussionBoard.objects.filter(name=name).exists():
            DiscussionBoard.objects.create(
                name=name,
                slug=slugify(name)[:100],
                description=description,
                order=order,
            )


def unseed_boards(apps, schema_editor):
    DiscussionBoard = apps.get_model("courses", "DiscussionBoard")
    DiscussionBoard.objects.filter(
        name__in=[b[0] for b in DEFAULT_BOARDS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0011_discussionboard_discussionpost_image_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_boards, unseed_boards),
    ]
