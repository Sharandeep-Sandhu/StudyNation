"""Reprocess Word-imported equation PNGs to body-text pixel height.

Usage:
    python manage.py normalize_equation_images
    python manage.py normalize_equation_images --dir media/question_equations
"""
from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crop + scale all equation PNGs to a uniform ~40px height so the "
        "1.15em .eq-math display box matches body text."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            default="",
            help="Directory of PNGs (default: MEDIA_ROOT/question_equations)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Process at most N files (0 = all)",
        )

    def handle(self, *args, **options):
        from admin_panel.docx_question_parser import _enhance_equation_png

        media_root = Path(settings.MEDIA_ROOT)
        target = options["dir"] or str(media_root / "question_equations")
        root = Path(target)
        if not root.is_dir():
            self.stderr.write(self.style.ERROR(f"Not a directory: {root}"))
            return

        files = sorted(root.glob("*.png"))
        limit = options["limit"] or 0
        if limit > 0:
            files = files[:limit]

        total = len(files)
        self.stdout.write(f"Normalizing {total} equation PNG(s) in {root} ...")

        ok = 0
        fail = 0
        for i, path in enumerate(files, 1):
            try:
                _enhance_equation_png(str(path), padding=3)
                ok += 1
            except Exception as exc:
                fail += 1
                self.stderr.write(f"  fail {path.name}: {exc}")
            if i % 200 == 0 or i == total:
                self.stdout.write(f"  {i}/{total} ...")

        self.stdout.write(
            self.style.SUCCESS(f"Done. ok={ok} fail={fail} total={total}")
        )
