"""Validated and isolated data sources for research crew runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field

MAX_ARCHIVE_FILES = 500
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_CONTEXT_CHARACTERS = 200_000
SUPPORTED_LOCAL_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}


class LocalKnowledgeError(ValueError):
    """Raised when local knowledge cannot be prepared safely."""


class ResearchSource(str, Enum):
    """Permitted, mutually exclusive research data sources."""

    INTERNET = "internet"
    LOCAL = "local"

    @property
    def label(self) -> str:
        """Return the user-facing source label."""
        return "Internet" if self is self.INTERNET else "Local knowledge"

    @classmethod
    def parse(cls, value: ResearchSource | str) -> ResearchSource:
        """Validate and normalize a research source value."""
        if isinstance(value, cls):
            return value
        normalized = value.strip().lower()
        aliases = {
            "internet": cls.INTERNET,
            "local": cls.LOCAL,
            "local knowledge": cls.LOCAL,
        }
        try:
            return aliases[normalized]
        except (AttributeError, KeyError) as error:
            raise ValueError(
                "Select a valid research source: Internet or Local knowledge."
            ) from error


@dataclass(frozen=True)
class PreparedLocalKnowledge:
    """Safe local context prepared for one research run."""

    context: str
    file_count: int


@dataclass(frozen=True)
class LocalKnowledgeStatus:
    """Non-sensitive readiness state for the local knowledge directory."""

    usable_file_count: int
    archive_count: int

    @property
    def is_ready(self) -> bool:
        """Return whether local mode has potential source material."""
        return self.usable_file_count > 0 or self.archive_count > 0


class InternetSearchInput(BaseModel):
    """Input accepted by the approved internet search tool."""

    query: str = Field(..., min_length=1, description="Research query to search")


class InternetSearchTool(BaseTool):
    """Search public internet sources without reading local knowledge files."""

    name: str = "internet_search"
    description: str = (
        "Search public internet sources for current evidence. Use this tool only "
        "when the selected research source is Internet."
    )
    args_schema: type[BaseModel] = InternetSearchInput

    def _run(self, query: str) -> str:
        """Return a concise set of public web search results."""
        results = DDGS().text(query, max_results=5)
        lines = []
        for result in results:
            title = str(result.get("title", "Untitled source")).strip()
            url = str(result.get("href", "")).strip()
            summary = str(result.get("body", "")).strip()
            lines.append(f"- {title}\n  URL: {url}\n  Summary: {summary}")
        return "\n".join(lines) or "No internet results were found."


def inspect_local_knowledge(knowledge_dir: Path) -> LocalKnowledgeStatus:
    """Return a non-sensitive readiness summary without reading file contents."""
    if not knowledge_dir.is_dir():
        return LocalKnowledgeStatus(usable_file_count=0, archive_count=0)

    files = [path for path in knowledge_dir.rglob("*") if path.is_file()]
    usable_count = sum(
        path.suffix.lower() in SUPPORTED_LOCAL_SUFFIXES
        and ".extracted" not in path.parts
        for path in files
    )
    archive_count = sum(path.suffix.lower() == ".zip" for path in files)
    return LocalKnowledgeStatus(usable_count, archive_count)


def prepare_local_knowledge(knowledge_dir: Path) -> PreparedLocalKnowledge:
    """Safely extract archives and load supported local files as research context."""
    root = knowledge_dir.resolve()
    if not root.is_dir():
        raise LocalKnowledgeError(
            "Local knowledge is unavailable. Add supported files under knowledge/."
        )

    for archive_path in sorted(root.rglob("*.zip")):
        if ".extracted" not in archive_path.parts:
            _extract_archive(archive_path, root)

    source_paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_LOCAL_SUFFIXES
    )
    if not source_paths:
        raise LocalKnowledgeError(
            "No usable local knowledge files were found. Add supported text, "
            "Markdown, CSV, JSON, or YAML files under knowledge/."
        )

    sections: list[str] = []
    remaining_characters = MAX_CONTEXT_CHARACTERS
    for source_path in source_paths:
        if source_path.stat().st_size > MAX_FILE_BYTES:
            raise LocalKnowledgeError(
                "A local knowledge file exceeds the supported size limit."
            )
        try:
            content = source_path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as error:
            raise LocalKnowledgeError(
                "A local knowledge file could not be read safely."
            ) from error
        if not content:
            continue
        relative_path = source_path.relative_to(root)
        section = f"Source: {relative_path}\n{content}"
        if len(section) > remaining_characters:
            break
        sections.append(section)
        remaining_characters -= len(section)

    if not sections:
        raise LocalKnowledgeError(
            "No usable local knowledge content was found under knowledge/."
        )
    return PreparedLocalKnowledge("\n\n".join(sections), len(sections))


def _extract_archive(archive_path: Path, knowledge_root: Path) -> None:
    """Extract one ZIP beneath a generated directory after validating all entries."""
    relative_archive = archive_path.relative_to(knowledge_root)
    destination = (
        knowledge_root / ".extracted" / relative_archive.parent / archive_path.stem
    ).resolve()
    if not destination.is_relative_to(knowledge_root):
        raise LocalKnowledgeError("A local archive resolved outside knowledge/.")

    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_FILES:
                raise LocalKnowledgeError(
                    "A local archive contains too many files to process safely."
                )
            if sum(entry.file_size for entry in entries) > MAX_ARCHIVE_BYTES:
                raise LocalKnowledgeError(
                    "A local archive exceeds the supported extraction size."
                )
            for entry in entries:
                _validate_archive_entry(entry, destination)
            for entry in entries:
                target = (destination / PurePosixPath(entry.filename)).resolve()
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except (OSError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise LocalKnowledgeError(
            "A local ZIP archive is corrupt, encrypted, or unreadable."
        ) from error


def _validate_archive_entry(entry: zipfile.ZipInfo, destination: Path) -> None:
    """Reject unsafe, encrypted, linked, or escaping ZIP entries."""
    entry_path = PurePosixPath(entry.filename)
    if entry.flag_bits & 0x1:
        raise LocalKnowledgeError("Encrypted local ZIP archives are not supported.")
    if entry_path.is_absolute() or ".." in entry_path.parts:
        raise LocalKnowledgeError("A local ZIP archive contains an unsafe path.")
    mode = entry.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise LocalKnowledgeError("Local ZIP archive links are not supported.")
    target = (destination / entry_path).resolve()
    if not target.is_relative_to(destination):
        raise LocalKnowledgeError("A local ZIP archive contains an unsafe path.")
