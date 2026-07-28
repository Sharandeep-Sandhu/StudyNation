# Generated manually for option_a–d and correct_answer max_length 500 -> 5000

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0015_discussion_reply_updated_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="option_a",
            field=models.CharField(blank=True, max_length=5000),
        ),
        migrations.AlterField(
            model_name="question",
            name="option_b",
            field=models.CharField(blank=True, max_length=5000),
        ),
        migrations.AlterField(
            model_name="question",
            name="option_c",
            field=models.CharField(blank=True, max_length=5000),
        ),
        migrations.AlterField(
            model_name="question",
            name="option_d",
            field=models.CharField(blank=True, max_length=5000),
        ),
        migrations.AlterField(
            model_name="question",
            name="correct_answer",
            field=models.CharField(
                blank=True,
                help_text="For choice: A/B/C/D or A,B for multiple",
                max_length=5000,
            ),
        ),
    ]
