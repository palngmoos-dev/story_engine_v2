import json
import os
from typing import Optional
from app.config import DATA_DIR
from app.models import Project

os.makedirs(DATA_DIR, exist_ok=True)


def _project_path(project_id: str) -> str:
    return os.path.join(DATA_DIR, f"{project_id}.json")


def save_project(project: Project) -> None:
    path = _project_path(project.project_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(project.model_dump_json(indent=2))


def load_project(project_id: str) -> Optional[Project]:
    path = _project_path(project_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Project(**data)
