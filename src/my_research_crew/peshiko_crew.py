"""CrewAI assembly for Peshiko Investments Group executive briefings."""

from __future__ import annotations

from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from my_research_crew.dashboard_service import get_ollama_settings
from my_research_crew.report_storage import create_report_path, report_output_file


@CrewBase
class PeshikoInvestmentsCrew:
    """Produce CEO-led Peshiko executive briefings from specialist assessments."""

    agents_config = "config/peshiko_agents.yaml"
    tasks_config = "config/peshiko_tasks.yaml"

    def __init__(
        self, report_path: Path | None = None, model: str | None = None
    ) -> None:
        """Initialize an executive crew run.

        Args:
            report_path: Destination for the completed executive brief.
            model: Ollama model selected for this run.
        """
        self.report_path = report_path
        self.model = model

    def _llm(self) -> LLM:
        """Create the run-specific Ollama LLM client."""
        settings = get_ollama_settings()
        model = self.model or settings.model
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        return LLM(model=model, base_url=settings.api_base)

    @agent
    def ceo(self) -> Agent:
        """Create the CEO synthesis agent."""
        return Agent(config=self.agents_config["ceo"], llm=self._llm(), verbose=True)

    @agent
    def cfo(self) -> Agent:
        """Create the CFO assessment agent."""
        return Agent(config=self.agents_config["cfo"], llm=self._llm(), verbose=True)

    @agent
    def coo(self) -> Agent:
        """Create the COO assessment agent."""
        return Agent(config=self.agents_config["coo"], llm=self._llm(), verbose=True)

    @agent
    def cio(self) -> Agent:
        """Create the CIO assessment agent."""
        return Agent(config=self.agents_config["cio"], llm=self._llm(), verbose=True)

    @task
    def cfo_assessment(self) -> Task:
        """Create the CFO assessment task."""
        return Task(config=self.tasks_config["cfo_assessment"])

    @task
    def coo_assessment(self) -> Task:
        """Create the COO assessment task."""
        return Task(config=self.tasks_config["coo_assessment"])

    @task
    def cio_assessment(self) -> Task:
        """Create the CIO assessment task."""
        return Task(config=self.tasks_config["cio_assessment"])

    @task
    def ceo_brief(self) -> Task:
        """Create the CEO synthesis task from all specialist assessments."""
        report_path = self.report_path or create_report_path("peshiko-executive")
        return Task(
            config=self.tasks_config["ceo_brief"],
            context=[
                self.cfo_assessment(),
                self.coo_assessment(),
                self.cio_assessment(),
            ],
            output_file=report_output_file(report_path),
        )

    @crew
    def crew(self) -> Crew:
        """Create the sequential Peshiko executive crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
