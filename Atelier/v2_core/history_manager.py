"""
History Manager for Multiverse Branching & Snapshotting.
Manages the storage and lifecycle of WorldStates in Phase 2 - Step A.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from .state_model import WorldState

class HistoryManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.branches_path = os.path.join(base_path, "branches")
        self.snapshots_path = os.path.join(base_path, "snapshots")
        self.cache_path = os.path.join(base_path, "cache")
        self.tree_file = os.path.join(base_path, "multiverse_tree.json")
        self.current_canvas_file = os.path.join(base_path, "current_canvas.json")
        
        self.current_branch_id = "main"
        self.branches = {} # branch_id -> branch_metadata
        
        self.init_save_structure()
        self._load_tree()

    def init_save_structure(self):
        """Creates the directory structure for saves if it doesn't exist."""
        for path in [self.branches_path, self.snapshots_path, self.cache_path]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

    def _load_tree(self):
        """Loads or initializes the multiverse metadata tree."""
        if os.path.exists(self.tree_file):
            try:
                with open(self.tree_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_branch_id = data.get("current_branch_id", "main")
                    self.branches = data.get("branches", {})
            except Exception as e:
                print(f"Error loading multiverse tree: {e}")
                self._init_default_tree()
        else:
            self._init_default_tree()

    def _init_default_tree(self):
        """Sets up the initial main branch."""
        self.current_branch_id = "main"
        self.branches = {
            "main": {
                "name": "Main Timeline",
                "created_at": datetime.now().isoformat(),
                "snapshots": [],
                "parent_snapshot_id": None,
                "narrative_log": [] # List of finalized scene summaries
            }
        }
        self._save_tree()

    def _save_tree(self):
        """Saves multiverse metadata to disk."""
        data = {
            "current_branch_id": self.current_branch_id,
            "branches": self.branches
        }
        with open(self.tree_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_snapshot(self, world_state: WorldState, summary: str = None) -> str:
        """Saves current state as a snapshot in the current branch."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"
        state_dict = world_state.to_dict()
        
        # Capture summary in metadata if provided
        if summary:
            state_dict["metadata"]["summary"] = summary
            
        file_path = os.path.join(self.snapshots_path, f"{snapshot_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
        # Register in current branch
        self.branches[self.current_branch_id]["snapshots"].append(snapshot_id)
        self._save_tree()
        
        # Update current canvas for persistent tracking
        with open(self.current_canvas_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> Optional[WorldState]:
        """Loads a specific snapshot and returns a WorldState object."""
        file_path = os.path.join(self.snapshots_path, f"{snapshot_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WorldState.from_dict(data)
        return None

    def create_branch(self, from_snapshot_id: str, branch_name: str = None) -> str:
        """Creates a parallel world from a specific snapshot."""
        branch_id = f"branch_{uuid.uuid4().hex[:8]}"
        if not branch_name:
            # AI Name generation TODO, using placeholder
            branch_name = f"평행 세계 {uuid.uuid4().hex[:4]}"
            
        self.branches[branch_id] = {
            "name": branch_name,
            "created_at": datetime.now().isoformat(),
            "snapshots": [from_snapshot_id],
            "parent_snapshot_id": from_snapshot_id,
            "narrative_log": [] # New branches start with fresh history
        }
        self._save_tree()
        return branch_id

    def switch_branch(self, branch_id: str) -> Optional[WorldState]:
        """Switches current focus to a different branch."""
        if branch_id in self.branches:
            self.current_branch_id = branch_id
            self._save_tree()
            
            # Load the latest snapshot of the target branch
            snapshots = self.branches[branch_id]["snapshots"]
            if snapshots:
                return self.load_snapshot(snapshots[-1])
        return None

    def list_branches(self) -> Dict[str, Any]:
        """Returns all branches metadata."""
        return self.branches

    def add_to_branch_history(self, branch_id: str, entry: str):
        """Adds a finalized narrative summary to the branch log."""
        if branch_id in self.branches:
            if "narrative_log" not in self.branches[branch_id]:
                self.branches[branch_id]["narrative_log"] = []
            self.branches[branch_id]["narrative_log"].append({
                "timestamp": datetime.now().isoformat(),
                "summary": entry
            })
            self._save_tree()

    def get_branch_briefing(self, branch_id: str) -> str:
        """Returns a briefing string about the branch's past history."""
        if branch_id not in self.branches:
            return "존재하지 않는 세계입니다."
            
        branch = self.branches[branch_id]
        log = branch.get("narrative_log", [])
        
        briefing = f"--- [{branch['name']}] 세계선 브리핑 ---\n"
        if not log:
            briefing += "아직 이 세계에서는 기록된 역사가 없습니다. 당신이 첫 페이지를 써보세요."
        else:
            briefing += f"최근 기록된 {len(log)}개의 서사적 이정표가 있습니다:\n"
            for i, entry in enumerate(log[-3:]): # Show last 3 entries
                briefing += f" - {entry['summary']}\n"
        
        return briefing
