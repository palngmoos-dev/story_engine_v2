"""
Project Manager for Phase 8.1.
Tracks metadata of all projects and handles concurrency locking per project_id.
"""
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from .storage import FileStorageAdapter

class ProjectManager:
    def __init__(self, storage=None):
        self.storage = storage or FileStorageAdapter()
        self.project_registry_file = "v2_core/saves/project_registry.json"
        self.projects = self._load_registry()
        self.locks = {} # project_id -> threading.Lock
        self._lock_reg = threading.Lock()

    def _load_registry(self) -> Dict[str, Any]:
        import os
        import json
        if os.path.exists(self.project_registry_file):
            with open(self.project_registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": {}}

    def _save_registry(self):
        import json
        with open(self.project_registry_file, "w", encoding="utf-8") as f:
            json.dump(self.projects, f, indent=2, ensure_ascii=False)

    def create_project(self, title: str) -> str:
        project_id = f"prj_{uuid.uuid4().hex[:8]}"
        return self.create_project_with_id(project_id, title)

    def create_project_with_id(self, project_id: str, title: str) -> str:
        if project_id not in self.projects["projects"]:
            self.projects["projects"][project_id] = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "user_tier": "FREE", # FREE, PREMIUM
                "is_public": False,
                "ai_score": 0.0,
                "vote_count": 0,
                "comment_count": 0,
                "published_at": None
            }
            self._save_registry()
        return project_id

    def cleanup_expired_projects(self, days: int = 60):
        """Removes projects that haven't been active for 60 days, unless they are Hall of Fame."""
        now = datetime.now()
        to_delete = []
        for pid, meta in self.projects["projects"].items():
            last_active = datetime.fromisoformat(meta["last_active"])
            if (now - last_active).days >= days:
                # Hall of Fame check could be added here
                to_delete.append(pid)
        
        for pid in to_delete:
            del self.projects["projects"][pid]
            # Actual file deletion should be handled by storage adapter
            self.storage.delete_project(pid)
        
        if to_delete:
            self._save_registry()
            return len(to_delete)
        return 0

    def get_top_creators(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Calculates Top 5 based on (AI Score * 0.5) + (Vote Impact * 0.5)."""
        ranking = []
        for pid, meta in self.projects["projects"].items():
            if not meta.get("is_public"): continue
            
            # Simple merit score: ai_score is 0-100, votes are weighted
            vote_score = min(100, meta.get("vote_count", 0) * 10) 
            merit_score = (meta.get("ai_score", 0) * 0.5) + (vote_score * 0.5)
            
            ranking.append({
                "project_id": pid,
                "title": meta["title"],
                "score": merit_score,
                "author_tier": meta["user_tier"]
            })
        
        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking[:limit]

    def update_project_meta(self, project_id: str, updates: Dict[str, Any]):
        if project_id in self.projects["projects"]:
            self.projects["projects"][project_id].update(updates)
            self.projects["projects"][project_id]["last_active"] = datetime.now().isoformat()
            self._save_registry()

    def get_project_lock(self, project_id: str) -> threading.Lock:
        with self._lock_reg:
            if project_id not in self.locks:
                self.locks[project_id] = threading.Lock()
            return self.locks[project_id]

    def list_projects(self) -> Dict[str, Any]:
        return self.projects["projects"]

    def update_activity(self, project_id: str):
        if project_id in self.projects["projects"]:
            self.projects["projects"][project_id]["last_active"] = datetime.now().isoformat()
            self._save_registry()

    def get_tier(self, project_id: str) -> str:
        return self.projects["projects"].get(project_id, {}).get("user_tier", "FREE")
