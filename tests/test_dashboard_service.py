"""Focused tests for dashboard configuration and CrewAI execution."""

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from my_research_crew.dashboard_service import (
    DEFAULT_OLLAMA_API_BASE,
    DEFAULT_OLLAMA_MODEL,
    CrewRunResult,
    get_safe_error_message,
    get_ollama_settings,
    run_crew,
)
from my_research_crew.report_storage import (
    PROJECT_ROOT,
    create_report_path,
    report_output_file,
)


class DashboardServiceTests(unittest.TestCase):
    """Verify dashboard settings and CrewAI execution delegation."""

    def test_get_ollama_settings_uses_defaults(self) -> None:
        """The dashboard falls back to the approved local Ollama settings."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("my_research_crew.dashboard_service.load_dotenv"),
        ):
            settings = get_ollama_settings()

        self.assertEqual(settings.model, DEFAULT_OLLAMA_MODEL)
        self.assertEqual(settings.api_base, DEFAULT_OLLAMA_API_BASE)

    def test_run_crew_sets_ollama_settings_and_passes_inputs(self) -> None:
        """The runner configures Ollama and delegates to the existing crew."""
        kickoff = MagicMock(return_value="crew output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch.dict(
                    os.environ,
                    {
                        "MODEL": "ollama/test-model",
                        "API_BASE": "http://ollama.test:11434",
                    },
                    clear=True,
                ),
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ) as create_crew,
            ):
                result = run_crew("  local AI  ")

        self.assertEqual(result, CrewRunResult("crew output", report_path))
        create_crew.assert_called_once_with(report_path)
        kickoff.assert_called_once()
        inputs = kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["topic"], "local AI")
        self.assertTrue(inputs["current_year"].isdigit())

    def test_run_crew_rejects_an_empty_topic(self) -> None:
        """The runner rejects invalid dashboard input before starting CrewAI."""
        with self.assertRaisesRegex(ValueError, "Enter a topic"):
            run_crew("   ")

    def test_safe_error_message_hides_provider_details(self) -> None:
        """Provider exceptions become actionable messages without raw details."""
        message = get_safe_error_message(Exception("Connection refused: secret-value"))

        self.assertIn("Could not reach Ollama", message)
        self.assertNotIn("secret-value", message)

    def test_safe_error_message_explains_a_missing_model(self) -> None:
        """Unavailable models produce a safe, actionable message."""
        message = get_safe_error_message(Exception("Model not found: private-model"))

        self.assertIn("model is unavailable", message)
        self.assertNotIn("private-model", message)

    def test_create_report_path_is_unique_and_contained(self) -> None:
        """Report directories are unique, topic-derived, and remain under reports."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory).resolve()
            first_path = create_report_path("../../Local LLM research!", project_root)
            second_path = create_report_path("../../Local LLM research!", project_root)

            self.assertEqual(first_path.name, "report.md")
            self.assertEqual(second_path.name, "report.md")
            self.assertNotEqual(first_path.parent, second_path.parent)
            self.assertTrue(first_path.parent.is_relative_to(project_root / "reports"))
            self.assertTrue(second_path.parent.is_relative_to(project_root / "reports"))
            self.assertIn("local-llm-research", first_path.parent.name)

    def test_report_output_file_rejects_paths_outside_reports(self) -> None:
        """CrewAI output paths cannot point outside the project reports folder."""
        outside_path = PROJECT_ROOT.parent / "report.md"

        with self.assertRaisesRegex(ValueError, "reports directory"):
            report_output_file(outside_path)

    def test_dashboard_shows_renamed_title_and_empty_input_message(self) -> None:
        """The dashboard renders the renamed crew and validates empty input."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        app = AppTest.from_file(app_path, default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "My Research Crew")

        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.warning[0].value, "Enter a topic before starting the crew."
        )
