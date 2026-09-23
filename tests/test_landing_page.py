"""Static checks for the public AI Research landing page."""

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANDING_DIR = PROJECT_ROOT / "landing"


class LandingPageTests(unittest.TestCase):
    """Verify public landing content and deployment boundaries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (LANDING_DIR / "index.html").read_text(encoding="utf-8")
        cls.styles = (LANDING_DIR / "styles.css").read_text(encoding="utf-8")
        cls.config_example = (LANDING_DIR / "config.example.js").read_text(
            encoding="utf-8"
        )

    def test_landing_page_describes_verified_workflows(self) -> None:
        """Public copy includes the product use case and supported features."""
        for phrase in (
            "AI Research",
            "Research Crew",
            "Executive Briefing",
            "Internet or session knowledge",
            "Session knowledge",
            "Markdown source",
            "generate a PDF",
            "Cooperative stop",
            "Open dashboard",
        ):
            self.assertIn(phrase, self.html)

    def test_landing_page_does_not_expose_private_or_development_details(self) -> None:
        """Public HTML contains no local endpoint or filesystem disclosure."""
        for forbidden in (
            "192.168.",
            "localhost:8501",
            "knowledge/",
            "report.md",
            "session_id",
            "MODEL=",
            "API_BASE=",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_dashboard_cta_is_configured_without_a_hardcoded_destination(self) -> None:
        """CTA destinations come from generated deployment configuration."""
        self.assertIn("config.js", self.html)
        self.assertIn("data-dashboard-link", self.html)
        self.assertIn("dashboardUrl", self.config_example)
        self.assertNotIn("http://localhost", self.html)
        self.assertNotIn("https://192.168", self.html)

    def test_landing_page_has_responsive_and_focus_styles(self) -> None:
        """The page declares mobile layout and keyboard focus behavior."""
        self.assertIn("@media (max-width: 430px)", self.styles)
        self.assertIn(":focus-visible", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)


if __name__ == "__main__":
    unittest.main()
