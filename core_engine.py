import json
import uuid
from typing import Any, Dict, List, Optional

from card_engine import clone_cards


class CoreEngine:
    """
    프로젝트 / 카드 / 메모리 / 관계 / 루트 / 로그 / 스냅샷 / JSON 저장복구 관리
    """

    def __init__(self) -> None:
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.current_project: Optional[str] = None

    def create_project(self, name: str = "default") -> str:
        pid = str(uuid.uuid4())
        self.projects[pid] = {
            "id": pid,
            "name": name,
            "cards": [],
            "active_scene_cards": [],
            "memory": {
                "last_choice": None,
                "scene_count": 0,
                "history": [],
                "scene_summaries": [],
                "branch": "main",
                "relations": {},
                "choice_log": [],
                "ending": None,
                "memory_notes": [],
                "seed_results": [],
                "stats": {
                    "branches": {},
                    "choices": {},
                    "endings": {},
                },
                "snapshots": [],
                "route_trace": [],
                "route_transitions": [],
                "recovery_count": 0,
                "integrity_notes": [],
                "used_lines": [],
                "epilogue": None,
            },
        }
        self.current_project = pid
        return pid

    def get_project(self) -> Dict[str, Any]:
        if self.current_project is None:
            raise RuntimeError("프로젝트가 없습니다. create_project()를 먼저 호출하세요.")
        return self.projects[self.current_project]

    def add_card(self, card: Dict[str, Any]) -> None:
        self.get_project()["cards"].append(card)

    def get_cards(self) -> List[Dict[str, Any]]:
        return self.get_project()["cards"]

    def set_scene_cards(self, card_ids: List[str]) -> None:
        selected: List[Dict[str, Any]] = []
        for cid in card_ids:
            for card in self.get_cards():
                if card["id"] == cid:
                    selected.append(card)
                    break
        self.get_project()["active_scene_cards"] = selected

    def get_scene_cards(self) -> List[Dict[str, Any]]:
        return self.get_project()["active_scene_cards"]

    def replace_scene_cards(self, cards: List[Dict[str, Any]]) -> None:
        self.get_project()["active_scene_cards"] = cards

    def get_characters(self) -> List[Dict[str, Any]]:
        return [c for c in self.get_scene_cards() if c["type"] == "character"]

    def save_scene(self, text: str) -> None:
        project = self.get_project()
        project["memory"]["history"].append(text)
        project["memory"]["scene_count"] += 1

    def get_history(self) -> List[str]:
        return self.get_project()["memory"]["history"]

    def add_scene_summary(self, summary: str) -> None:
        self.get_project()["memory"]["scene_summaries"].append(summary)

    def get_scene_summaries(self) -> List[str]:
        return self.get_project()["memory"]["scene_summaries"]

    def get_scene_count(self) -> int:
        return self.get_project()["memory"]["scene_count"]

    def set_last_choice(self, choice: str) -> None:
        self.get_project()["memory"]["last_choice"] = choice
        self._bump_stat("choices", choice)

    def get_last_choice(self) -> Optional[str]:
        return self.get_project()["memory"]["last_choice"]

    def log_choice(self, scene_no: int, choice: str) -> None:
        branch = self.get_branch()
        self.get_project()["memory"]["choice_log"].append({
            "scene_no": scene_no,
            "choice": choice,
            "branch": branch,
        })

    def get_choice_log(self) -> List[Dict[str, Any]]:
        return self.get_project()["memory"]["choice_log"]

    def get_recent_choices(self, limit: int = 3) -> List[str]:
        logs = self.get_choice_log()
        return [x["choice"] for x in logs[-limit:]]

    def set_branch(self, branch_name: str) -> None:
        memory = self.get_project()["memory"]
        old_branch = memory["branch"]
        memory["branch"] = branch_name
        memory["route_trace"].append(branch_name)
        if old_branch != branch_name:
            memory["route_transitions"].append({
                "from": old_branch,
                "to": branch_name,
                "scene_count": self.get_scene_count(),
            })
        self._bump_stat("branches", branch_name)

    def get_branch(self) -> str:
        return self.get_project()["memory"]["branch"]

    def get_route_trace(self) -> List[str]:
        return self.get_project()["memory"]["route_trace"]

    def get_route_transitions(self) -> List[Dict[str, Any]]:
        return self.get_project()["memory"]["route_transitions"]

    def update_relation(self, name1: str, name2: str, delta: int) -> None:
        key = self._relation_key(name1, name2)
        relations = self.get_project()["memory"]["relations"]
        relations[key] = relations.get(key, 0) + delta

    def set_relation(self, name1: str, name2: str, value: int) -> None:
        key = self._relation_key(name1, name2)
        self.get_project()["memory"]["relations"][key] = value

    def get_relation(self, name1: str, name2: str) -> int:
        key = self._relation_key(name1, name2)
        return self.get_project()["memory"]["relations"].get(key, 0)

    def get_relations(self) -> Dict[str, int]:
        return self.get_project()["memory"]["relations"]

    def update_goal_progress(self, character_name: str, delta: int) -> None:
        for c in self.get_scene_cards():
            if c["type"] == "character" and c["name"] == character_name:
                c["goal_progress"] = max(0, min(100, c.get("goal_progress", 0) + delta))
                return

    def set_goal_progress(self, character_name: str, value: int) -> None:
        for c in self.get_scene_cards():
            if c["type"] == "character" and c["name"] == character_name:
                c["goal_progress"] = max(0, min(100, value))
                return

    def average_goal_progress(self) -> float:
        chars = self.get_characters()
        if not chars:
            return 0.0
        total = sum(c.get("goal_progress", 0) for c in chars)
        return round(total / len(chars), 1)

    def level_up_characters(self) -> None:
        for c in self.get_scene_cards():
            if c["type"] == "character":
                c["level"] = c.get("level", 1) + 1

    def set_ending(self, ending_data: Dict[str, Any]) -> None:
        self.get_project()["memory"]["ending"] = ending_data
        self._bump_stat("endings", ending_data.get("ending_type", "미정"))

    def get_ending(self) -> Optional[Dict[str, Any]]:
        return self.get_project()["memory"]["ending"]

    def add_memory_note(self, text: str) -> None:
        self.get_project()["memory"]["memory_notes"].append(text)

    def get_memory_notes(self) -> List[str]:
        return self.get_project()["memory"]["memory_notes"]

    def add_seed_result(self, result: Dict[str, Any]) -> None:
        self.get_project()["memory"]["seed_results"].append(result)

    def get_seed_results(self) -> List[Dict[str, Any]]:
        return self.get_project()["memory"]["seed_results"]

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        return self.get_project()["memory"]["stats"]

    def bump_recovery_count(self) -> None:
        self.get_project()["memory"]["recovery_count"] += 1

    def get_recovery_count(self) -> int:
        return self.get_project()["memory"]["recovery_count"]

    def add_integrity_note(self, note: str) -> None:
        self.get_project()["memory"]["integrity_notes"].append(note)

    def get_integrity_notes(self) -> List[str]:
        return self.get_project()["memory"]["integrity_notes"]

    def remember_line(self, line: str) -> None:
        used = self.get_project()["memory"]["used_lines"]
        used.append(line)
        if len(used) > 60:
            del used[:20]

    def get_used_lines(self) -> List[str]:
        return self.get_project()["memory"]["used_lines"]

    def set_epilogue(self, text: str) -> None:
        self.get_project()["memory"]["epilogue"] = text

    def get_epilogue(self) -> Optional[str]:
        return self.get_project()["memory"]["epilogue"]

    def make_snapshot(self, label: str) -> None:
        snap = {
            "label": label,
            "branch": self.get_branch(),
            "last_choice": self.get_last_choice(),
            "scene_count": self.get_scene_count(),
            "relations": dict(self.get_relations()),
            "cards": clone_cards(self.get_scene_cards()),
            "choice_log": list(self.get_choice_log()),
            "memory_notes": list(self.get_memory_notes()),
            "route_trace": list(self.get_route_trace()),
            "route_transitions": list(self.get_route_transitions()),
            "recovery_count": self.get_recovery_count(),
            "scene_summaries": list(self.get_scene_summaries()),
            "used_lines": list(self.get_used_lines()),
            "epilogue": self.get_epilogue(),
        }
        self.get_project()["memory"]["snapshots"].append(snap)

    def get_snapshots(self) -> List[Dict[str, Any]]:
        return self.get_project()["memory"]["snapshots"]

    def restore_last_snapshot(self) -> bool:
        snaps = self.get_snapshots()
        if not snaps:
            return False

        snap = snaps[-1]
        project = self.get_project()
        project["active_scene_cards"] = clone_cards(snap["cards"])
        project["memory"]["branch"] = snap["branch"]
        project["memory"]["last_choice"] = snap["last_choice"]
        project["memory"]["scene_count"] = snap["scene_count"]
        project["memory"]["relations"] = dict(snap["relations"])
        project["memory"]["choice_log"] = list(snap["choice_log"])
        project["memory"]["memory_notes"] = list(snap["memory_notes"])
        project["memory"]["route_trace"] = list(snap["route_trace"])
        project["memory"]["route_transitions"] = list(snap["route_transitions"])
        project["memory"]["recovery_count"] = snap["recovery_count"]
        project["memory"]["scene_summaries"] = list(snap["scene_summaries"])
        project["memory"]["used_lines"] = list(snap["used_lines"])
        project["memory"]["epilogue"] = snap["epilogue"]
        return True

    def export_state_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.get_project()["name"],
            "scene_count": self.get_scene_count(),
            "branch": self.get_branch(),
            "relations": self.get_relations(),
            "cards": self.get_scene_cards(),
            "ending": self.get_ending(),
            "stats": self.get_stats(),
            "route_trace": self.get_route_trace(),
            "route_transitions": self.get_route_transitions(),
            "recovery_count": self.get_recovery_count(),
            "history": self.get_history(),
            "scene_summaries": self.get_scene_summaries(),
            "memory_notes": self.get_memory_notes(),
            "choice_log": self.get_choice_log(),
            "used_lines": self.get_used_lines(),
            "epilogue": self.get_epilogue(),
        }

    def export_state_json(self) -> str:
        return json.dumps(self.export_state_dict(), ensure_ascii=False, indent=2)

    def save_json_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export_state_json())

    def load_from_state_dict(self, state: Dict[str, Any]) -> None:
        self.create_project(state.get("project_name", "loaded_project"))
        project = self.get_project()
        project["active_scene_cards"] = state.get("cards", [])
        project["memory"]["scene_count"] = state.get("scene_count", 0)
        project["memory"]["branch"] = state.get("branch", "main")
        project["memory"]["relations"] = state.get("relations", {})
        project["memory"]["ending"] = state.get("ending")
        project["memory"]["stats"] = state.get("stats", {"branches": {}, "choices": {}, "endings": {}})
        project["memory"]["route_trace"] = state.get("route_trace", [])
        project["memory"]["route_transitions"] = state.get("route_transitions", [])
        project["memory"]["recovery_count"] = state.get("recovery_count", 0)
        project["memory"]["history"] = state.get("history", [])
        project["memory"]["scene_summaries"] = state.get("scene_summaries", [])
        project["memory"]["memory_notes"] = state.get("memory_notes", [])
        project["memory"]["choice_log"] = state.get("choice_log", [])
        project["memory"]["used_lines"] = state.get("used_lines", [])
        project["memory"]["epilogue"] = state.get("epilogue")

    def load_json_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_from_state_dict(data)

    def _bump_stat(self, group: str, key: str) -> None:
        stats = self.get_project()["memory"]["stats"][group]
        stats[key] = stats.get(key, 0) + 1

    def _relation_key(self, name1, name2) -> str:
        def normalize(value):
            if isinstance(value, dict):
                return str(value.get("name") or value.get("id") or "unknown")
            return str(value)

        pair = sorted([normalize(name1), normalize(name2)])
        return f"{pair[0]}::{pair[1]}"
