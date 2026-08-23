Minimal runnable MVP for my_1st_crew

Structure
- config/agents.yaml  : agent definitions
- config/tasks.yaml   : task definitions and expected outputs
- src/my_1st_crew/team.py : minimal orchestrator
- src/my_1st_crew/llm_adapter.py : deterministic mock LLM adapter
- src/my_1st_crew/validator.py : JSON Schema-based validator
- src/my_1st_crew/cli.py : CLI entrypoint for demo
- requirements-mvp.txt : minimal Python deps

Quickstart (local, recommended inside virtualenv):

1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements-mvp.txt
3. python -m my_1st_crew.src.my_1st_crew.cli  # or: python src/my_1st_crew/cli.py

Notes
- This MVP uses a mock LLM adapter that returns deterministic structured outputs.
- The validator uses jsonschema to enforce structured outputs; failing validation halts the run and signals a manual review point.
- Replace MockLLMAdapter with a real LLM adapter when ready; ensure outputs are validated before accepting.
- The backlog is loaded from `backlog.md`, and engineering tasks create a feature branch before validation and commit flow.
- Pull requests are targeted at `develop` when GitHub auth is available; otherwise the workflow logs a skip rather than failing the run.

Story-first git workflow

1. Load the current backlog from `backlog.md`.
2. Create a feature branch from the repo’s base branch (`develop`, falling back to `main`/`master`).
3. Run the local validation command for the task.
4. Commit the changes with a story-scoped commit message when validation passes.
5. Open a pull request into `develop` when GitHub credentials are configured.

Next steps (suggested):
- Add persistence (artifact store) and provenance metadata
- Add a mock adapter config to switch between mock/real adapters
- Add unit tests for validator and orchestrator
