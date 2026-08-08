"""
Ensure critical columns/tables exist on production databases.

Render deploys sometimes have incomplete migration history; missing columns
like discussion video_solution_url cause 500s on /question-form/.

Safe to run repeatedly (idempotent). Called from build.sh after migrate.
"""

from django.core.management.base import BaseCommand
from django.db import connection


def _table_exists(cursor, table: str) -> bool:
    vendor = connection.vendor
    if vendor == "postgresql":
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s AND table_schema = current_schema()
            """,
            [table],
        )
    elif vendor == "sqlite":
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
            [table],
        )
    else:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s
            """,
            [table],
        )
    return cursor.fetchone() is not None


def _column_exists(cursor, table: str, column: str) -> bool:
    vendor = connection.vendor
    if vendor == "postgresql":
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
              AND table_schema = current_schema()
            """,
            [table, column],
        )
    elif vendor == "sqlite":
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
    else:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            [table, column],
        )
    return cursor.fetchone() is not None


def _add_column(cursor, table: str, column: str, ddl_type: str):
    """Add column if missing. ddl_type is the SQL type + optional DEFAULT/NULL."""
    if _column_exists(cursor, table, column):
        return False
    # SQLite / Postgres both accept ADD COLUMN
    cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {ddl_type}')
    return True


class Command(BaseCommand):
    help = "Ensure discussion / past-paper columns exist (fixes Render 500s)"

    def handle(self, *args, **options):
        added = []
        with connection.cursor() as cursor:
            # Discussion posts
            if _table_exists(cursor, "courses_discussionpost"):
                if _add_column(
                    cursor,
                    "courses_discussionpost",
                    "video_solution_url",
                    "varchar(500) DEFAULT ''",
                ):
                    added.append("courses_discussionpost.video_solution_url")
                if _add_column(
                    cursor,
                    "courses_discussionpost",
                    "image",
                    "varchar(100) NULL",
                ):
                    added.append("courses_discussionpost.image")
                if _add_column(
                    cursor,
                    "courses_discussionpost",
                    "board_id",
                    "integer NULL",
                ):
                    added.append("courses_discussionpost.board_id")
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Table courses_discussionpost missing — run full migrate"
                    )
                )

            # Discussion replies
            if _table_exists(cursor, "courses_discussionreply"):
                if _add_column(
                    cursor,
                    "courses_discussionreply",
                    "video_solution_url",
                    "varchar(500) DEFAULT ''",
                ):
                    added.append("courses_discussionreply.video_solution_url")
                if _add_column(
                    cursor,
                    "courses_discussionreply",
                    "updated_at",
                    "timestamp with time zone NULL"
                    if connection.vendor == "postgresql"
                    else "datetime NULL",
                ):
                    added.append("courses_discussionreply.updated_at")
                if _add_column(
                    cursor,
                    "courses_discussionreply",
                    "image",
                    "varchar(100) NULL",
                ):
                    added.append("courses_discussionreply.image")

            # Past paper answer PDF
            if _table_exists(cursor, "courses_pastpaper"):
                if _add_column(
                    cursor,
                    "courses_pastpaper",
                    "answer_pdf",
                    "varchar(100) NULL",
                ):
                    added.append("courses_pastpaper.answer_pdf")

            # Question video_solution_url
            if _table_exists(cursor, "courses_question"):
                if _add_column(
                    cursor,
                    "courses_question",
                    "video_solution_url",
                    "varchar(500) DEFAULT ''",
                ):
                    added.append("courses_question.video_solution_url")

            # Seed boards if table empty
            if _table_exists(cursor, "courses_discussionboard"):
                cursor.execute("SELECT COUNT(*) FROM courses_discussionboard")
                count = cursor.fetchone()[0]
                if count == 0:
                    from django.utils.text import slugify

                    boards = [
                        (
                            "General Questions",
                            "general-questions",
                            "Ask anything about courses and exams.",
                            1,
                        ),
                        (
                            "Math & Formulas",
                            "math-formulas",
                            "Math help and formula questions.",
                            2,
                        ),
                        (
                            "Exam Prep",
                            "exam-prep",
                            "Past papers and exam strategies.",
                            3,
                        ),
                    ]
                    for name, slug, desc, order in boards:
                        cursor.execute(
                            """
                            INSERT INTO courses_discussionboard
                                (name, slug, description, "order")
                            VALUES (%s, %s, %s, %s)
                            """,
                            [name, slug, desc, order],
                        )
                    added.append(f"seeded {len(boards)} discussion boards")

        if added:
            self.stdout.write(self.style.SUCCESS("Schema fixes applied:"))
            for item in added:
                self.stdout.write(f"  + {item}")
        else:
            self.stdout.write(self.style.SUCCESS("Schema OK — nothing to add."))
