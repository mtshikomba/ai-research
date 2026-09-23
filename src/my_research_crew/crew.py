from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from my_research_crew.dashboard_service import get_ollama_settings
from my_research_crew.research_sources import InternetSearchTool, ResearchSource
from my_research_crew.report_storage import create_report_path, report_output_file

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class MyResearchCrew:
    """MyResearchCrew crew."""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(
        self,
        report_path: Path | None = None,
        model: str | None = None,
        source: ResearchSource = ResearchSource.INTERNET,
        source_context: str = "Internet research enabled.",
    ) -> None:
        """Initialize the crew with an optional run-specific report path.

        Args:
            report_path: Destination for the reporting task output.
            model: Ollama model selected for this crew run.
            source: Exclusive evidence source selected for this run.
            source_context: Prepared source instructions or local file content.
        """
        self.report_path = report_path
        self.model = model
        self.source = ResearchSource.parse(source)
        self.source_context = source_context

    def _llm(self) -> LLM:
        """Create an LLM configured for the local Ollama service.

        Returns:
            A CrewAI LLM client for the configured local Ollama model.
        """
        settings = get_ollama_settings()
        model = self.model or settings.model
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        return LLM(model=model, base_url=settings.api_base)

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        tools = [InternetSearchTool()] if self.source is ResearchSource.INTERNET else []
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            llm=self._llm(),
            tools=tools,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            llm=self._llm(),
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def reporting_task(self) -> Task:
        report_path = self.report_path or create_report_path("research")
        return Task(
            config=self.tasks_config["reporting_task"],
            output_file=report_output_file(report_path),
        )

    @crew
    def crew(self) -> Crew:
        """Create the MyResearchCrew crew."""
        # To learn how to add knowledge sources, see the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical,
            # See https://docs.crewai.com/how-to/Hierarchical/ for this option.
        )
