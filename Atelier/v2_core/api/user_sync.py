"""
User Sync & ID Mapping Engine for Phase 8.2.
Maps Platform-specific User IDs (Kakao/Telegram) to Project IDs.
"""
import os
import json
import uuid
import random
from typing import Optional, Dict
from ..state_model import WorldState

class UserSyncManager:
    def __init__(self, mapping_file: str = "v2_core/saves/user_mapping.json"):
        self.mapping_file = mapping_file
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> Dict[str, str]:
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_mappings(self):
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.mappings, f, indent=2, ensure_ascii=False)

    def get_or_create_project(self, platform: str, user_id: str, pm_instance) -> str:
        """Finds existing project_id for a platform user or creates a new one."""
        mapping_key = f"{platform}:{user_id}"
        project_id = self.mappings.get(mapping_key)
        
        # Check if project exists and has state, if not, treat as new or repair
        if project_id:
            state = pm_instance.storage.load_project(project_id)
            if state:
                return project_id
            else:
                # Repair: mapping exists but no state file!
                print(f"[REPAIR] Project {project_id} found in mapping but missing state file. Re-initializing.")
                # We reuse the ID but re-init the state below
        else:
            # New project ID
            project_id = f"prj_{uuid.uuid4().hex[:8]}"
            # We will use pm_instance's metadata tracking too
            pm_instance.create_project_with_id(project_id, "심야의 서사시") # We'll add this to PM
        
        # Auto-naming for the 'Director' feeling (Phase 8.2)
        prefixes = ["심야의", "가려진", "피어오르는", "고독한", "흔들리는", "뒤틀린"]
        suffixes = ["조용한 추격자", "비밀의 캔버스", "운명의 부재", "시네마틱 코드", "평행의 그림자"]
        auto_title = f"{random.choice(prefixes)} {random.choice(suffixes)}"
        
        # Initialize default state and save (Internal Orchestration for user/repair)
        state = WorldState()
        state.metadata["summary"] = f"'{auto_title}' 메신저 프로젝트가 시작/복구되었습니다."
        pm_instance.storage.save_project(project_id, state)
        
        # Save initial snapshot
        history = pm_instance.storage.get_history_manager(project_id)
        history.save_snapshot(state, summary="Messenger System Entry/Repair")
        
        # Update/Link mapping
        self.mappings[mapping_key] = project_id
        self._save_mappings()
        
        return project_id
