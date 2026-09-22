"""In-memory download formats for completed report artifacts."""

from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path
import re

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from my_research_crew.report_storage import PROJECT_ROOT, REPORTS_DIRECTORY

PDF_FONT_NAME = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT_NAME))


def _read_report(report_path: Path, project_root: Path | None = None) -> str:
    """Read a completed report after validating its reports-directory boundary."""
    root = (project_root or PROJECT_ROOT).resolve()
    reports_root = (root / REPORTS_DIRECTORY).resolve()
    resolved_path = report_path.resolve()
    if not resolved_path.is_relative_to(reports_root):
        raise ValueError("Report downloads must use a path in the reports directory.")
    if resolved_path.name != "report.md" or not resolved_path.is_file():
        raise ValueError("The completed report is unavailable for download.")
    try:
        return resolved_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(
            "The completed report could not be read for download."
        ) from error


def report_download_filename(report_path: Path, extension: str) -> str:
    """Return a safe filename based only on the report's generated directory."""
    normalized_extension = extension.lower()
    if normalized_extension not in {".md", ".pdf"}:
        raise ValueError("Unsupported report download format.")
    report_name = re.sub(r"[^A-Za-z0-9._-]+", "-", report_path.parent.name).strip(".-")
    return f"{report_name or 'research-report'}{normalized_extension}"


def markdown_download(report_path: Path, project_root: Path | None = None) -> bytes:
    """Return the completed Markdown report as UTF-8 download bytes."""
    return _read_report(report_path, project_root).encode("utf-8")


def pdf_download(report_path: Path, project_root: Path | None = None) -> bytes:
    """Generate a readable PDF in memory from the completed Markdown report."""
    report_text = _read_report(report_path, project_root)
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=report_path.parent.name,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName=PDF_FONT_NAME,
        alignment=TA_LEFT,
        leading=14,
        spaceAfter=8,
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontName=PDF_FONT_NAME,
        leading=18,
        spaceBefore=8,
        spaceAfter=8,
    )
    story = []
    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        heading_match = re.match(r"^#{1,6}\s+(.+)$", line)
        if heading_match:
            content = escape(heading_match.group(1))
            story.append(Paragraph(content, heading_style))
            continue
        if line.startswith("- ") or line.startswith("* "):
            content = f"&bull; {escape(line[2:])}"
        else:
            content = escape(line)
        story.append(Paragraph(content, body_style))
    if not story:
        story.append(Paragraph("Empty report", body_style))
    document.build(story)
    return output.getvalue()
