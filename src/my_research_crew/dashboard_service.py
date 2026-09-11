"""Configuration and execution boundary for the Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
import json

from dotenv import load_dotenv

from my_research_crew.report_storage import create_report_path

DEFAULT_OLLAMA_MODEL = "gpt-oss:120b-cloud"
DEFAULT_OLLAMA_API_BASE = "http://192.168.1.153:11434"


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
    """

    output: Any
    report_path: Path


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


def _create_crew(report_path: Path, model: str) -> Any:
    """Create the existing configured CrewAI crew on demand.

    Returns:
        The configured CrewAI crew instance.
    """
    from my_research_crew.crew import MyResearchCrew

    return MyResearchCrew(report_path=report_path, model=model).crew()


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


def run_crew(topic: str, model: str) -> CrewRunResult:
    """Run the configured CrewAI crew for a dashboard topic.

    Args:
        topic: Research topic supplied by the dashboard user.
        model: Ollama model selected for this run.

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

    report_path = create_report_path(normalized_topic)

    output = _create_crew(report_path, normalized_model).kickoff(
        inputs={
            "topic": normalized_topic,
            "current_year": str(datetime.now().year),
        }
    )
    return CrewRunResult(output=output, report_path=report_path)
