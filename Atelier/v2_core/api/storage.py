"""
Storage Layer for Phase 8.1.
Defines the interface and local file implementation for Project persistence.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..state_model import WorldState
from ..history_manager import HistoryManager

class StorageAdapter(ABC):
    @abstractmethod
    def save_project(self, project_id: str, state: WorldState):
        pass

    @abstractmethod
    def load_project(self, project_id: str) -> Optional[WorldState]:
        pass

    @abstractmethod
    def get_history_manager(self, project_id: str) -> HistoryManager:
        pass

class FileStorageAdapter(StorageAdapter):
    def __init__(self, root_path: str = "v2_core/saves"):
        self.root_path = root_path
        if not os.path.exists(root_path):
            os.makedirs(root_path, exist_ok=True)

    def _get_project_path(self, project_id: str) -> str:
        path = os.path.join(self.root_path, project_id)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def save_project(self, project_id: str, state: WorldState):
        path = self._get_project_path(project_id)
        content_file = os.path.join(path, "latest_state.json")
        with open(content_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def load_project(self, project_id: str) -> Optional[WorldState]:
        path = os.path.join(self.root_path, project_id)
        content_file = os.path.join(path, "latest_state.json")
        if os.path.exists(content_file):
            with open(content_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WorldState.from_dict(data)
        return None

    def get_history_manager(self, project_id: str) -> HistoryManager:
        project_path = self._get_project_path(project_id)
        return HistoryManager(base_path=project_path)
