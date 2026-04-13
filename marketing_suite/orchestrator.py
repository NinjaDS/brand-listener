"""
Orchestrator: WorkspaceManager and TaskQueue for the marketing suite.
"""

from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).parent.parent
QUEUE_PATH = REPO_ROOT / "reports" / "workspaces" / "task_queue.json"


def _slugify(name: str) -> str:
    """Convert brand name to filesystem-safe slug."""
    slug = name.lower()
    for ch in [" ", "'", "'", ".", "&", "/"]:
        slug = slug.replace(ch, "-")
    # Collapse multiple hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


class WorkspaceManager:
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.slug = _slugify(brand_name)
        self.workspace = REPO_ROOT / "reports" / "workspaces" / self.slug
        self.workspace.mkdir(parents=True, exist_ok=True)

    def path(self) -> Path:
        return self.workspace

    def __str__(self) -> str:
        return str(self.workspace)


class TaskQueue:
    def __init__(self):
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if QUEUE_PATH.exists():
            with open(QUEUE_PATH) as f:
                self._data: Dict[str, Any] = json.load(f)
        else:
            self._data = {"tasks": []}

    def _save(self):
        with open(QUEUE_PATH, "w") as f:
            json.dump(self._data, f, indent=2)

    def enqueue(self, brand: str, metadata: Optional[Dict] = None) -> str:
        task_id = f"{_slugify(brand)}-{int(time.time())}"
        task = {
            "id": task_id,
            "brand": brand,
            "status": "pending",
            "enqueued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": metadata or {},
        }
        self._data["tasks"].append(task)
        self._save()
        return task_id

    def complete(self, task_id: str, result_path: Optional[str] = None):
        for task in self._data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "complete"
                task["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if result_path:
                    task["result_path"] = result_path
                break
        self._save()

    def fail(self, task_id: str, error: str):
        for task in self._data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "failed"
                task["error"] = error
                task["failed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                break
        self._save()
