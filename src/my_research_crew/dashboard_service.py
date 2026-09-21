"""Configuration and execution boundary for the Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from dotenv import load_dotenv

from my_research_crew.research_sources import (
    MAX_ARCHIVE_BYTES,
    MAX_FILE_BYTES,
    LocalKnowledgeError,
    ResearchSource,
    SUPPORTED_LOCAL_SUFFIXES,
    prepare_local_knowledge,
)
from my_research_crew.report_storage import PROJECT_ROOT, create_report_path

DEFAULT_OLLAMA_MODEL = "gpt-oss:120b-cloud"
DEFAULT_OLLAMA_API_BASE = "http://192.168.1.153:11434"
SESSION_TIMEOUT_MINUTES = 10
KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


@dataclass(frozen=True)
class OllamaSettings:
    """Settings used by CrewAI to connect to an Ollama server.

    Attributes:
        model: LiteLLM-compatible Ollama model identifier.
        api_base: Base URL for the Ollama server.
    """

    model: str
    api_base: str


@dataclass(frozen=True)
class CrewRunResult:
    """Output and saved report location for one completed crew run.

    Attributes:
        output: Value returned by CrewAI kickoff.
        report_path: Final report path reserved for the run.
        source: User-facing label for the selected evidence source.
    """

    output: Any
    report_path: Path
    source: str


@dataclass(frozen=True)
class ExecutiveRunResult:
    """Output, saved report location, and evidence source for one executive crew run."""

    output: Any
    report_path: Path
    source: str = ResearchSource.LOCAL.label


@dataclass(frozen=True)
class SessionUploadResult:
    """Summary of one session knowledge upload operation."""

    accepted_files: int
    rejected_files: tuple[str, ...]


class OllamaModelInventoryError(Exception):
    """Raised when an Ollama model inventory cannot be loaded safely."""


def get_ollama_settings() -> OllamaSettings:
    """Load Ollama settings from the environment with local-network defaults.

    Returns:
        The configured model and Ollama API base URL.
    """
    load_dotenv()
    return OllamaSettings(
        model=os.getenv("MODEL", DEFAULT_OLLAMA_MODEL),
        api_base=os.getenv("API_BASE", DEFAULT_OLLAMA_API_BASE),
    )


def list_ollama_models(settings: OllamaSettings | None = None) -> list[str]:
    """Load available model names from the configured Ollama server.

    Args:
        settings: Ollama connection settings. Defaults to environment settings.

    Returns:
        Sorted, unique model names reported by Ollama.

    Raises:
        OllamaModelInventoryError: If Ollama is unreachable or returns an
            invalid model inventory.
    """
    configured_settings = settings or get_ollama_settings()
    endpoint = f"{configured_settings.api_base.rstrip('/')}/api/tags"
    try:
        with urlopen(endpoint, timeout=5) as response:
            payload = json.load(response)
    except (OSError, URLError, ValueError, json.JSONDecodeError) as error:
        raise OllamaModelInventoryError(
            "Could not load available Ollama models."
        ) from error

    models = payload.get("models")
    if not isinstance(models, list):
        raise OllamaModelInventoryError("Ollama returned an invalid model inventory.")

    names = {
        model["name"].strip()
        for model in models
        if isinstance(model, dict)
        and isinstance(model.get("name"), str)
        and model["name"].strip()
    }
    return sorted(names)


def select_ollama_model(available_models: list[str], configured_model: str) -> str:
    """Choose the preferred model with safe configured and list fallbacks.

    Args:
        available_models: Model names currently available from Ollama.
        configured_model: Environment-configured fallback model.

    Returns:
        The selected model name.

    Raises:
        OllamaModelInventoryError: If no usable model is available.
    """
    if not available_models:
        raise OllamaModelInventoryError("No Ollama models are available.")
    if DEFAULT_OLLAMA_MODEL in available_models:
        return DEFAULT_OLLAMA_MODEL
    if configured_model in available_models:
        return configured_model
    return available_models[0]


def _create_crew(
    report_path: Path,
    model: str,
    source: ResearchSource,
    source_context: str,
) -> Any:
    """Create the existing configured CrewAI crew on demand.

    Returns:
        The configured CrewAI crew instance.
    """
    from my_research_crew.crew import MyResearchCrew

    return MyResearchCrew(
        report_path=report_path,
        model=model,
        source=source,
        source_context=source_context,
    ).crew()


def session_has_expired(
    started_at: datetime | str | None,
    timeout_minutes: int = SESSION_TIMEOUT_MINUTES,
) -> bool:
    """Return whether a session has exceeded the configured inactivity window."""
    if started_at is None:
        return True
    if isinstance(started_at, str):
        started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    cutoff = started_at + timedelta(minutes=timeout_minutes)
    return datetime.now(timezone.utc) >= cutoff


def purge_session_knowledge(session_id: str, project_root: Path | None = None) -> None:
    """Delete only the session-scoped knowledge folder for one browser session."""
    root = (project_root or PROJECT_ROOT).resolve()
    session_dir = root / "sessions" / session_id / "knowledge"
    if not session_dir.exists():
        return
    shutil.rmtree(session_dir, ignore_errors=True)
    session_root = session_dir.parent.parent
    if session_root.exists() and not any(session_root.iterdir()):
        try:
            session_root.rmdir()
        except OSError:
            pass


def session_knowledge_dir(session_id: str, project_root: Path | None = None) -> Path:
    """Return the contained knowledge directory for one browser session.

    Args:
        session_id: Identifier assigned to the current browser session.
        project_root: Optional project root used by tests.

    Returns:
        The session-scoped knowledge directory.

    Raises:
        ValueError: If the session identifier could escape the sessions root.
    """
    root = (project_root or PROJECT_ROOT).resolve()
    sessions_root = (root / "sessions").resolve()
    session_root = (sessions_root / session_id).resolve()
    if not session_root.is_relative_to(sessions_root):
        raise ValueError("Invalid session identifier.")
    return session_root / "knowledge"


def save_session_knowledge(
    session_id: str,
    uploaded_files: list[Any],
    project_root: Path | None = None,
) -> SessionUploadResult:
    """Persist supported uploaded files inside one session knowledge directory.

    Args:
        session_id: Identifier assigned to the current browser session.
        uploaded_files: Streamlit uploaded-file objects with ``name`` and
            ``getvalue`` attributes.
        project_root: Optional project root used by tests.

    Returns:
        Counts of accepted files and filenames rejected by validation.
    """
    knowledge_dir = session_knowledge_dir(session_id, project_root)
    accepted_files = 0
    rejected_files: list[str] = []
    for uploaded_file in uploaded_files:
        filename = Path(str(getattr(uploaded_file, "name", ""))).name
        suffix = Path(filename).suffix.lower()
        if not filename or suffix not in SUPPORTED_LOCAL_SUFFIXES | {".zip"}:
            rejected_files.append(filename or "unnamed file")
            continue
        destination = knowledge_dir / filename
        try:
            content = uploaded_file.getvalue()
            max_upload_bytes = MAX_ARCHIVE_BYTES if suffix == ".zip" else MAX_FILE_BYTES
            if not isinstance(content, bytes) or len(content) > max_upload_bytes:
                rejected_files.append(filename)
                continue
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            if suffix == ".zip":
                prepare_local_knowledge(knowledge_dir)
        except (OSError, LocalKnowledgeError):
            destination.unlink(missing_ok=True)
            rejected_files.append(filename)
            continue
        accepted_files += 1
    return SessionUploadResult(accepted_files, tuple(rejected_files))


def get_safe_error_message(error: Exception) -> str:
    """Convert a provider failure into a safe, actionable dashboard message.

    Args:
        error: Exception raised while starting or running the crew.

    Returns:
        A message that guides the user without exposing provider details.
    """
    error_text = str(error).lower()
    if any(
        term in error_text for term in ("connection", "connect", "refused", "timeout")
    ):
        return (
            "Could not reach Ollama. Confirm the configured server is running "
            "and reachable."
        )
    if any(term in error_text for term in ("model", "not found", "404")):
        return (
            "The configured Ollama model is unavailable. Pull the model, then "
            "try again."
        )
    return (
        "The crew could not complete this run. Check the local Ollama "
        "configuration and try again."
    )


def run_crew(
    topic: str,
    model: str,
    source: ResearchSource | str = ResearchSource.INTERNET,
    *,
    knowledge_dir: Path | None = None,
) -> CrewRunResult:
    """Run the configured CrewAI crew for a dashboard topic.

    Args:
        topic: Research topic supplied by the dashboard user.
        model: Ollama model selected for this run.
        source: Mutually exclusive Internet or Local knowledge source.
        knowledge_dir: Explicit local knowledge directory for local runs.

    Returns:
        The CrewAI output and path of its saved report.

    Raises:
        ValueError: If the supplied topic is empty.
        Exception: If CrewAI or the configured Ollama service cannot complete
            the run.
    """
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("Enter a topic before starting the crew.")
    normalized_model = model.strip()
    if not normalized_model:
        raise ValueError("Select an Ollama model before starting the crew.")
    selected_source = ResearchSource.parse(source)

    report_path = create_report_path(normalized_topic)
    if selected_source is ResearchSource.LOCAL:
        source_context = prepare_local_knowledge(knowledge_dir or KNOWLEDGE_DIR).context
    else:
        source_context = (
            "Internet research enabled. Local knowledge files were not read."
        )

    output = _create_crew(
        report_path,
        normalized_model,
        selected_source,
        source_context,
    ).kickoff(
        inputs={
            "topic": normalized_topic,
            "current_year": str(datetime.now().year),
            "research_source": selected_source.label,
            "source_context": source_context,
        }
    )
    return CrewRunResult(
        output=output,
        report_path=report_path,
        source=selected_source.label,
    )


def run_executive_crew(
    executive_question: str,
    business_context: str,
    model: str,
    source: ResearchSource | str = ResearchSource.LOCAL,
    *,
    knowledge_dir: Path | None = None,
) -> ExecutiveRunResult:
    """Run a CEO-led Peshiko executive briefing.

    Args:
        executive_question: Business decision or question for the executive crew.
        business_context: Optional non-sensitive context supplied by the user.
        model: Ollama model selected for this run.
        source: Evidence source selected for the briefing, either Internet or
            Local knowledge.
        knowledge_dir: Explicit local knowledge directory for local briefings.

    Returns:
        The executive brief and its saved report path.

    Raises:
        ValueError: If the question, model, or selected source is invalid.
    """
    question = executive_question.strip()
    selected_model = model.strip()
    selected_source = ResearchSource.parse(source)
    if not question:
        raise ValueError("Enter an executive question before starting the briefing.")
    if not selected_model:
        raise ValueError("Select an Ollama model before starting the briefing.")

    report_path = create_report_path(f"peshiko-executive-{question}")
    from my_research_crew.peshiko_crew import PeshikoInvestmentsCrew

    if selected_source is ResearchSource.LOCAL:
        if knowledge_dir is None:
            raise ValueError(
                "A session knowledge directory is required for local briefings."
            )
        local_knowledge = prepare_local_knowledge(knowledge_dir)
        local_knowledge_summary = (
            "Session knowledge was used as the primary source.\n\n"
            + local_knowledge.context
        )
        source_context = "Session knowledge was used as the primary source."
    else:
        local_knowledge_summary = (
            "Internet research was selected; local Peshiko knowledge was not used "
            "for this run."
        )
        source_context = (
            "Internet research was selected for this briefing; local knowledge "
            "was not consulted."
        )

    effective_context = business_context.strip() or "No additional context provided."
    effective_context = f"{source_context}\n\n{effective_context}"
    if local_knowledge_summary:
        effective_context = f"{local_knowledge_summary}\n\n{effective_context}"

    output = (
        PeshikoInvestmentsCrew(report_path=report_path, model=selected_model)
        .crew()
        .kickoff(
            inputs={
                "executive_question": question,
                "business_context": effective_context,
                "local_knowledge_summary": local_knowledge_summary,
                "research_source": selected_source.label,
            }
        )
    )
    return ExecutiveRunResult(
        output=output,
        report_path=report_path,
        source=selected_source.label,
    )
