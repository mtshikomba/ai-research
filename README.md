# My Research Crew

Welcome to the My Research Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed; Python 3.12 is recommended on
Intel macOS. This project uses [UV](https://docs.astral.sh/uv/) for dependency
management and package handling.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to the project directory, create the supported environment, and
install the locked dependencies:

```bash
uv venv --python 3.12 .venv
uv sync --system-certs
```

`--system-certs` lets UV use the macOS trust store when downloading dependencies.

### Customizing

**Configure your local Ollama server in the `.env` file**

```dotenv
MODEL=ollama/llama3.1:latest
API_BASE=http://192.168.1.153:11434
```

Start Ollama on the configured server and make the model available before
running the crew. For example:

```bash
ollama pull llama3.1
ollama serve
```

- Modify `src/my_research_crew/config/agents.yaml` to define your agents
- Modify `src/my_research_crew/config/tasks.yaml` to define your tasks
- Modify `src/my_research_crew/crew.py` to add your own logic, tools and specific args
- Modify `src/my_research_crew/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the my_research_crew Crew, assembling the agents and assigning them tasks as defined in your configuration.

Each research run saves its `report.md` beneath a unique
`reports/<timestamp>-<topic>/` directory. The `reports/` directory is ignored by Git.

## Streamlit Dashboard

Install the project dependencies, ensure the configured Ollama server is
reachable, then launch the dashboard from the repository root:

```bash
streamlit run src/my_research_crew/dashboard.py
```

The dashboard loads available models from the configured Ollama server. It
prefers `gpt-oss:120b-cloud` when available; otherwise it uses `MODEL` from
`.env` or the environment. The default endpoint is
`http://192.168.1.153:11434`.

## Reusing this workflow in another repo

The project now includes a generic `ProjectContext` discovery layer in `src/my_research_crew/project_context.py` that detects the target repository’s language, default branch, and validation commands. This allows the same backlog, branch, and validation workflow to be reused in other source-code projects instead of assuming a single fixed project layout.

## Understanding Your Crew

The my_research_crew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the My Research Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
