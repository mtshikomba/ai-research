import os
import json
from datetime import datetime
from typing import Any, Dict, Optional


class ArtifactStore:
    """Save provenance artifacts inside the target repository under `artifacts/`.

    Each saved artifact is stored in its own timestamped folder:
      artifacts/<iso_ts>-<task_name>/
    containing:
      - metadata.json (task, created_at, git refs)
      - prompt.txt
      - output.json (or output.txt)
      - validation.json (when present)
      - git.json (when present)

    The class ensures artifacts are stored inside the provided project_root.
    """

    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.artifacts_dir = os.path.join(self.project_root, "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def _artifact_path(self, task_name: str) -> str:
        ts = datetime.utcnow().isoformat(timespec="seconds").replace(':', '-')
        safe_task = ''.join(c if c.isalnum() or c in '-_' else '-' for c in (task_name or 'task'))
        name = f"{ts}-{safe_task}"
        path = os.path.join(self.artifacts_dir, name)
        return path

    def save(self, task_name: str, prompt: Optional[str], output: Any, validation: Optional[Dict[str, Any]] = None, git_meta: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Persist prompt, output, validation and git metadata for a task run.

        Returns a small dict with the artifact folder path and metadata path.
        """
        path = self._artifact_path(task_name)
        os.makedirs(path, exist_ok=True)

        meta = {
            "task": task_name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "project_root": self.project_root,
        }

        if git_meta:
            meta["git"] = git_meta

        # Save prompt
        try:
            if prompt is not None:
                with open(os.path.join(path, "prompt.txt"), "w", encoding="utf-8") as f:
                    f.write(str(prompt))
        except Exception:
            # best-effort; do not crash agent if artifact saving fails
            pass

        # Save output
        try:
            out_path = os.path.join(path, "output.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, default=str)
        except Exception:
            # fallback to text
            try:
                with open(os.path.join(path, "output.txt"), "w", encoding="utf-8") as f:
                    f.write(str(output))
            except Exception:
                pass

        # Save validation
        if validation is not None:
            try:
                with open(os.path.join(path, "validation.json"), "w", encoding="utf-8") as f:
                    json.dump(validation, f, indent=2, default=str)
            except Exception:
                pass

        # Save metadata
        try:
            with open(os.path.join(path, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, default=str)
        except Exception:
            pass

        # Save git meta as separate file if provided
        if git_meta is not None:
            try:
                with open(os.path.join(path, "git.json"), "w", encoding="utf-8") as f:
                    json.dump(git_meta, f, indent=2, default=str)
            except Exception:
                pass

        return {"artifact_path": path, "metadata": os.path.join(path, "metadata.json")}
