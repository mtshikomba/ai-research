"""Filesystem-safe report locations for completed research runs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import unicodedata

REPORTS_DIRECTORY = "reports"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_report_path(topic: str, project_root: Path | None = None) -> Path:
    """Create a unique report directory for a research topic.

    Args:
        topic: User-supplied research topic.
        project_root: Repository root. Defaults to the installed project root.

    Returns:
        The absolute path for the run's `report.md` file.
    """
    root = (project_root or PROJECT_ROOT).resolve()
    reports_root = root / REPORTS_DIRECTORY
    reports_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    topic_slug = _slugify_topic(topic)
    run_directory = reports_root / f"{timestamp}-{topic_slug}"
    sequence = 1
    while run_directory.exists():
        run_directory = reports_root / f"{timestamp}-{topic_slug}-{sequence}"
        sequence += 1

    run_directory.mkdir()
    return run_directory / "report.md"


def report_output_file(report_path: Path) -> str:
    """Return a CrewAI-safe report path relative to the project root.

    Args:
        report_path: Absolute path allocated by :func:`create_report_path`.

    Returns:
        The report path relative to the repository root.

    Raises:
        ValueError: If the report path is outside the repository reports folder.
    """
    resolved_path = report_path.resolve()
    reports_root = (PROJECT_ROOT / REPORTS_DIRECTORY).resolve()
    if not resolved_path.is_relative_to(reports_root):
        raise ValueError(
            "Report output must be stored beneath the project reports directory."
        )
    return str(resolved_path.relative_to(PROJECT_ROOT))


def _slugify_topic(topic: str) -> str:
    """Produce a bounded ASCII directory label from a research topic."""
    normalized = unicodedata.normalize("NFKD", topic).encode("ascii", "ignore")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.decode().lower()).strip("-")
    return slug[:80] or "research"
