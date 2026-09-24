from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DeploymentFilesTests(unittest.TestCase):
    def test_production_compose_declares_runtime_contract(self) -> None:
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        self.assertIn("8003:8000", compose)
        self.assertIn(".env.production", compose)
        self.assertIn("proxy-tier", compose)
        self.assertIn("external: true", compose)
        self.assertIn("reports_volume", compose)
        self.assertIn("sessions_volume", compose)

    def test_dockerfile_runs_dashboard_on_container_port_8000(self) -> None:
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()

        self.assertIn("EXPOSE 8000", dockerfile)
        self.assertIn('"run", "src/my_research_crew/dashboard.py"', dockerfile)
        self.assertIn('"--server.port", "8000"', dockerfile)
        self.assertIn("/_stcore/health", dockerfile)


if __name__ == "__main__":
    unittest.main()
