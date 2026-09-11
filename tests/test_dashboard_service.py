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
    ExecutiveRunResult,
    OllamaSettings,
    get_safe_error_message,
    get_ollama_settings,
    list_ollama_models,
    run_crew,
    run_executive_crew,
    select_ollama_model,
)
from my_research_crew.peshiko_crew import PeshikoInvestmentsCrew
from my_research_crew.report_storage import (
    PROJECT_ROOT,
    create_report_path,
    report_output_file,
)
from my_research_crew.crew import MyResearchCrew


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
                result = run_crew("  local AI  ", "gpt-oss:120b-cloud")

        self.assertEqual(result, CrewRunResult("crew output", report_path))
        create_crew.assert_called_once_with(report_path, "gpt-oss:120b-cloud")
        kickoff.assert_called_once()
        inputs = kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["topic"], "local AI")
        self.assertTrue(inputs["current_year"].isdigit())

    def test_run_crew_does_not_mutate_environment_model_settings(self) -> None:
        """A dashboard selection stays scoped to its run rather than `.env`."""
        crew = MagicMock()
        crew.kickoff.return_value = "crew output"

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch.dict(
                    os.environ,
                    {"MODEL": "llama3.1:latest", "API_BASE": "http://ollama.test"},
                    clear=True,
                ),
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ),
            ):
                run_crew("local AI", "gpt-oss:120b-cloud")
                self.assertEqual(os.environ["MODEL"], "llama3.1:latest")
                self.assertEqual(os.environ["API_BASE"], "http://ollama.test")

    def test_run_executive_crew_passes_context_and_model(self) -> None:
        """The executive runner delegates the selected model and safe context."""
        kickoff = MagicMock(return_value="executive output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.peshiko_crew.PeshikoInvestmentsCrew",
                ) as executive_crew,
            ):
                executive_crew.return_value.crew.return_value = crew
                result = run_executive_crew(
                    "Should we expand?",
                    "Cash reserves are constrained.",
                    "llama3.1:latest",
                )

        self.assertEqual(result, ExecutiveRunResult("executive output", report_path))
        executive_crew.assert_called_once_with(
            report_path=report_path, model="llama3.1:latest"
        )
        self.assertEqual(
            kickoff.call_args.kwargs["inputs"]["executive_question"],
            "Should we expand?",
        )

    def test_peshiko_crew_has_ceo_context_for_specialist_tasks(self) -> None:
        """The CEO brief consumes the CFO, COO, and CIO task assessments."""
        crew = PeshikoInvestmentsCrew(model="llama3.1:latest")
        brief = crew.ceo_brief()

        self.assertEqual(len(brief.context), 3)
        self.assertEqual(
            brief.agent.role.strip(),
            "Peshiko Investments Group Chief Executive Officer",
        )

    def test_crew_normalizes_selected_ollama_model(self) -> None:
        """Raw Ollama model names become LiteLLM-compatible CrewAI identifiers."""
        crew = MyResearchCrew(model="gpt-oss:120b-cloud")

        self.assertEqual(crew._llm().model, "ollama/gpt-oss:120b-cloud")

    def test_run_crew_rejects_an_empty_topic(self) -> None:
        """The runner rejects invalid dashboard input before starting CrewAI."""
        with self.assertRaisesRegex(ValueError, "Enter a topic"):
            run_crew("   ", "gpt-oss:120b-cloud")

    def test_select_ollama_model_prefers_requested_default(self) -> None:
        """The requested default wins when it is available from Ollama."""
        selected = select_ollama_model(
            ["llama3.1:latest", "gpt-oss:120b-cloud"], "llama3.1:latest"
        )

        self.assertEqual(selected, "gpt-oss:120b-cloud")

    def test_select_ollama_model_uses_configured_fallback(self) -> None:
        """The configured model is used when the requested default is absent."""
        selected = select_ollama_model(["llama3.1:latest", "gemma4:26b"], "gemma4:26b")

        self.assertEqual(selected, "gemma4:26b")

    def test_list_ollama_models_removes_invalid_and_duplicate_names(self) -> None:
        """Inventory parsing exposes only unique, usable Ollama model names."""
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with (
            patch("my_research_crew.dashboard_service.urlopen", return_value=response),
            patch("my_research_crew.dashboard_service.json.load") as load,
        ):
            load.return_value = {
                "models": [
                    {"name": "gpt-oss:120b-cloud"},
                    {"name": " llama3.1:latest "},
                    {"name": "gpt-oss:120b-cloud"},
                    {"name": ""},
                    {},
                ]
            }
            models = list_ollama_models(
                OllamaSettings("fallback", "http://ollama.test")
            )

        self.assertEqual(models, ["gpt-oss:120b-cloud", "llama3.1:latest"])

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
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "My Research Crew")
        self.assertEqual(app.selectbox[0].value, "gpt-oss:120b-cloud")

        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.warning[0].value, "Enter a topic before starting the crew."
        )

    def test_dashboard_shows_peshiko_executive_workspace(self) -> None:
        """The executive workspace exposes labeled Peshiko briefing inputs."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[0].set_value("Executive briefing").run()

        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Peshiko Investments Group")
        self.assertEqual(app.text_area[0].label, "Executive question")
        self.assertEqual(app.text_area[1].label, "Business context (optional)")
        self.assertEqual(app.button[0].label, "Prepare executive brief")

    def test_dashboard_disables_run_when_models_are_unavailable(self) -> None:
        """The dashboard prevents execution when Ollama model inventory fails."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch.dict(os.environ, {"API_BASE": "http://127.0.0.1:1"}):
            app = AppTest.from_file(app_path, default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertTrue(app.button[0].disabled)
