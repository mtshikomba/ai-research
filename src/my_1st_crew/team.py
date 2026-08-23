import os
import yaml
from typing import Dict, Any
from .llm_adapter import MockLLMAdapter
from .validator import Validator

class Crew:
    """Minimal orchestrator for the MVP.

    Loads config from the existing project config directory and specifically
    prefers the MVP files there when present.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.config_dir = os.path.join(project_root, "src", "my_1st_crew", "config")
        if not os.path.isdir(self.config_dir):
            self.config_dir = os.path.join(project_root, "config")

        agent_file = os.path.join(self.config_dir, "mvp_agents.yaml")
        task_file = os.path.join(self.config_dir, "mvp_tasks.yaml")

        if not os.path.exists(agent_file):
            agent_file = os.path.join(self.config_dir, "agents.yaml")
        if not os.path.exists(task_file):
            task_file = os.path.join(self.config_dir, "tasks.yaml")

        with open(agent_file, "r", encoding="utf-8") as f:
            self.agents = yaml.safe_load(f) or {}
        with open(task_file, "r", encoding="utf-8") as f:
            self.tasks = yaml.safe_load(f) or {}

        self.adapter = MockLLMAdapter()
        self.validator = Validator()
        self.artifacts = {}

    def kickoff(self, inputs: Dict[str, Any]):
        """Run tasks sequentially using the provided inputs."""
        context = {"inputs": inputs}
        results = {}

        for task_name, task_cfg in self.tasks.items():
            agent_id = task_cfg.get("agent")
            agent_cfg = self.agents.get(agent_id, {})
            prompt = self._build_prompt(task_name, task_cfg, agent_cfg, context)

            print(f"\n--- Running task: {task_name} (agent={agent_id}) ---")
            response = self.adapter.generate(prompt=prompt, expected=task_cfg.get("expected_output"))

            valid, errors = self.validator.validate(task_cfg.get("expected_output"), response)
            if not valid:
                print(f"Validation failed for {task_name}: {errors}")
                # Attach a simple review artifact and escalate (in MVP just stop)
                results[task_name] = {"status": "validation_failed", "errors": errors, "output": response}
                break

            print(f"Task {task_name} produced valid {task_cfg.get('expected_output')}")
            results[task_name] = {"status": "ok", "output": response}
            # update context for downstream tasks
            context[task_name] = response
            self.artifacts[task_name] = response

        return results

    def _build_prompt(self, task_name: str, task_cfg: Dict[str, Any], agent_cfg: Dict[str, Any], context: Dict[str, Any]) -> str:
        # Minimal prompt templating for the MVP
        prompt = (
            f"Agent role: {agent_cfg.get('role')}\n"
            f"Goal: {agent_cfg.get('goal')}\n\n"
            f"Task: {task_cfg.get('description')}\n\n"
            f"Inputs: {context.get('inputs')}\n\n"
            "Please produce structured JSON matching the expected output type."
        )
        return prompt
