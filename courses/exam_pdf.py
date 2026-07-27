"""
PDF export for the Exam Builder.

Renders a question paper (and, optionally, a separate answer key) as a PDF.
Question text may contain inline LaTeX-style math delimited by $...$ (inline)
or $$...$$ (centered block). Because questions are stored as plain text with
math markers rather than structured rich text, each line is rasterized with
matplotlib's mathtext engine (a pure-Python LaTeX-subset renderer) and the
resulting image is placed into the PDF with reportlab. This keeps fractions,
exponents, set notation, etc. looking correct without requiring a system
LaTeX install.

If a line fails to parse as math (mathtext only supports a subset of LaTeX),
we fall back to rendering it as plain text with the math delimiters and
backslash commands stripped, so a single malformed line never breaks the
whole export.
"""
import io
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


PAGE_W, PAGE_H = A4
MARGIN_X = 20 * mm
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

# matplotlib mathtext doesn't recognise every LaTeX macro. Map the common
# aliases that show up in exam question text to mathtext-supported forms.
_MATHTEXT_ALIASES = {
    r"\le": r"\leq",
    r"\ge": r"\geq",
    r"\ne": r"\neq",
    r"\to": r"\rightarrow",
    r"\implies": r"\Rightarrow",
}


def _normalize_math(segment: str) -> str:
    # matplotlib mathtext only understands single-$ delimiters; it treats
    # the whole line as plain text with $...$ math runs inside it, and a
    # literal "$$" breaks its parser. Collapse any $$...$$ block markers
    # down to single $...$ so block-style formulas still render as math.
    segment = segment.replace("$$", "$")
    for old, new in _MATHTEXT_ALIASES.items():
        segment = segment.replace(old, new)
    return segment


def _render_line_to_image(line: str, fontsize=12.5, dpi=200, max_width_in=6.6):
    """
    Render a single line of text (which may contain $...$ math segments)
    to a tightly-cropped transparent PNG, returned as (PIL-compatible bytes
    buffer, width_px, height_px). Falls back to a math-free render of the
    same line if mathtext fails to parse it.
    """
    line = _normalize_math(line)

    def _try_render(text):
        fig = plt.figure(figsize=(max_width_in, 1))
        fig.patch.set_alpha(0.0)
        txt = fig.text(0.01, 0.5, text, fontsize=fontsize, va="center", ha="left")
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.03,
            transparent=True,
        )
        plt.close(fig)
        buf.seek(0)
        return buf

    try:
        return _try_render(line)
    except Exception:
        # Strip math delimiters and backslash commands, render as plain text.
        plain = re.sub(r"\$\$?(.*?)\$\$?", lambda m: _strip_latex(m.group(1)), line)
        try:
            return _try_render(plain)
        except Exception:
            return _try_render(re.sub(r"[^\x20-\x7E]", "", plain))


def _strip_latex(s: str) -> str:
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathbb\{([^}]*)\}", r"\1", s)
    s = s.replace(r"\quad", "  ").replace(r"\,", " ")
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("{", "").replace("}", "")
    return s


def _split_question_lines(question_text: str):
    """Split stored question text into renderable lines, preserving blank
    lines (used for spacing between parts/paragraphs)."""
    return question_text.replace("\r\n", "\n").split("\n")


class _PDFPager:
    """Small helper that tracks the current y-cursor and starts new pages."""

    def __init__(self, c: canvas.Canvas, title: str):
        self.c = c
        self.title = title
        self.page_num = 0
        self.y = PAGE_H - MARGIN_TOP
        self._new_page()

    def _new_page(self):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self.y = PAGE_H - MARGIN_TOP
        self.c.setFont("Helvetica-Bold", 9)
        self.c.setFillGray(0.4)
        self.c.drawString(MARGIN_X, PAGE_H - 10 * mm, self.title)
        self.c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 10 * mm, f"Page {self.page_num}")
        self.c.setFillGray(0)
        self.y = PAGE_H - MARGIN_TOP

    def ensure_space(self, height):
        if self.y - height < MARGIN_BOTTOM:
            self._new_page()

    def draw_image(self, img_buf, width_px, height_px, indent=0, dpi=200):
        w_pt = width_px / dpi * 72
        h_pt = height_px / dpi * 72
        max_w = CONTENT_W - indent
        if w_pt > max_w:
            scale = max_w / w_pt
            w_pt *= scale
            h_pt *= scale
        self.ensure_space(h_pt + 2)
        self.c.drawImage(
            ImageReader(img_buf),
            MARGIN_X + indent,
            self.y - h_pt,
            width=w_pt,
            height=h_pt,
            mask="auto",
        )
        self.y -= h_pt + 3

    def draw_text(self, text, size=11, bold=False, gap_before=4, gap_after=2):
        self.ensure_space(size + gap_before + gap_after)
        self.y -= gap_before
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.c.drawString(MARGIN_X, self.y, text)
        self.y -= size + gap_after

    def spacer(self, height):
        self.ensure_space(height)
        self.y -= height

    def hr(self):
        self.ensure_space(8)
        self.c.setStrokeGray(0.8)
        self.c.line(MARGIN_X, self.y, PAGE_W - MARGIN_X, self.y)
        self.c.setStrokeGray(0)
        self.y -= 8


def _render_question_block(pager: _PDFPager, index: int, eq, show_marks=True):
    question = eq.question
    label = f"Q{index}."
    if question.question_code:
        sub_label = f"  ({question.question_code})"
    else:
        sub_label = ""

    pager.draw_text(f"{label}{sub_label}", size=11, bold=True, gap_before=10, gap_after=4)

    lines = _split_question_lines(question.question_text)
    for line in lines:
        if not line.strip():
            pager.spacer(6)
            continue
        buf = _render_line_to_image(line)
        from PIL import Image

        with Image.open(buf) as im:
            w, h = im.size
        buf.seek(0)
        pager.draw_image(buf, w, h, indent=8 * mm)

    if show_marks:
        pager.draw_text(f"[Total: {question.marks} marks]", size=9, gap_before=4, gap_after=0)
    pager.hr()


def _render_answer_block(pager: _PDFPager, index: int, eq):
    question = eq.question
    pager.draw_text(f"Q{index}. {question.question_code}", size=11, bold=True, gap_before=10, gap_after=4)

    if question.question_type in ("single_choice", "multiple_choice", "true_false") and question.correct_answer:
        pager.draw_text(f"Correct answer: {question.correct_answer}", size=10.5, gap_after=2)
    elif question.correct_answer:
        pager.draw_text(f"Answer: {question.correct_answer}", size=10.5, gap_after=2)
    else:
        pager.draw_text("Answer: (mark scheme not provided)", size=10.5, gap_after=2)

    if question.explanation:
        for line in _split_question_lines(question.explanation):
            if not line.strip():
                pager.spacer(4)
                continue
            buf = _render_line_to_image(line, fontsize=10.5)
            from PIL import Image

            with Image.open(buf) as im:
                w, h = im.size
            buf.seek(0)
            pager.draw_image(buf, w, h, indent=8 * mm)

    pager.hr()


def build_exam_pdf(exam, include_answers=False):
    """
    Build the PDF for an Exam. If include_answers is False, produces the
    clean question paper. If True, produces the answer key instead.
    Returns an io.BytesIO positioned at the start.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    exam_questions = list(
        exam.exam_questions.select_related("question").order_by("order", "added_at")
    )

    title = f"{exam.name} — {'Answer Key' if include_answers else 'Question Paper'}"
    pager = _PDFPager(c, title)

    # ---- Cover header ----
    pager.draw_text(exam.name, size=18, bold=True, gap_before=0, gap_after=4)
    subtitle_bits = []
    if exam.category:
        subtitle_bits.append(exam.category.name)
    subtitle_bits.append(f"{len(exam_questions)} question(s)")
    subtitle_bits.append(f"{exam.total_marks} marks")
    subtitle_bits.append(f"{exam.duration_minutes} minutes")
    pager.draw_text(" • ".join(subtitle_bits), size=10.5, gap_before=0, gap_after=8)
    if include_answers:
        pager.draw_text("ANSWER KEY", size=11, bold=True, gap_before=0, gap_after=6)
    pager.hr()

    if not exam_questions:
        pager.draw_text(
            "No questions have been added to this exam yet.", size=11, gap_before=12
        )
    else:
        for i, eq in enumerate(exam_questions, start=1):
            if include_answers:
                _render_answer_block(pager, i, eq)
            else:
                _render_question_block(pager, i, eq)
                if exam.questions_per_page == 1 and i < len(exam_questions):
                    pager._new_page()

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
