"""Shared helpers for embedding question text (with inline equation images) in previews."""

from __future__ import annotations

import json
from typing import Any, Iterable


def question_preview_map(questions: Iterable[Any]) -> dict[str, dict]:
    """
    Build {id: preview_fields} for admin/student exam & list builders.
    Use with Django's json_script so equation HTML is not broken by escapejs.
    """
    data: dict[str, dict] = {}
    for q in questions:
        eq_images: list[str] = []
        raw_eq = getattr(q, "equation_images", None) or ""
        if raw_eq:
            try:
                parsed = json.loads(raw_eq)
                if isinstance(parsed, list):
                    eq_images = [str(u) for u in parsed if u]
            except (TypeError, ValueError, json.JSONDecodeError):
                eq_images = []
        # Prefer dynamic QuestionOption rows (supports 1..N choices); fall back to A–D.
        dyn_opts = []
        try:
            for i, opt in enumerate(q.options.all()):
                letter = chr(65 + i) if i < 26 else str(i + 1)
                dyn_opts.append(
                    {
                        "letter": letter,
                        "text": opt.text or "",
                        "is_correct": bool(getattr(opt, "is_correct", False)),
                    }
                )
        except Exception:
            dyn_opts = []

        options_map = {
            "A": q.option_a or "",
            "B": q.option_b or "",
            "C": q.option_c or "",
            "D": q.option_d or "",
        }
        if dyn_opts:
            options_map = {o["letter"]: o["text"] for o in dyn_opts if o.get("text")}

        data[str(q.id)] = {
            "code": getattr(q, "question_code", None)
            or getattr(q, "question_number", None)
            or "",
            "topic": q.topic or "",
            "marks": q.marks or 0,
            "text": q.question_text or "",
            "answer": q.correct_answer or "",
            "explanation": q.explanation or "",
            "video_solution_url": getattr(q, "video_solution_url", None) or "",
            "type": q.question_type or "",
            "options": options_map,
            "optionsList": dyn_opts
            or [
                {"letter": k, "text": v, "is_correct": False}
                for k, v in options_map.items()
                if v
            ],
            "equationImages": eq_images,
        }
    return data
