"""
Canvas Engine for Infinite Narrative System.
Handles 3-Zone CLI Dashboard and Branch Visualization.
"""
import os
import sys
from typing import Dict, List, Any, Optional
from .state_model import WorldState
from .history_manager import HistoryManager

class CanvasUI:
    """Handles the rendering of the 3-Zone CLI Layout."""
    
    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def draw_line(char="-", length=60):
        print(char * length)

    @staticmethod
    def render_header(branch_name: str, total_scenes: int):
        print(f"\n[ Infinite Narrative Canvas ] - Branch: {branch_name}")
        print(f"Current Progress: Sequence #{total_scenes}")
        CanvasUI.draw_line("=")

    @staticmethod
    def render_canvas_zone(state: WorldState):
        """Zone 1: Current Active Cards and Story Beat."""
        print("\n<<< ZONE 1: CURRENT CANVAS >>>")
        print(f"Place: {state.current_place} | Timeline: {state.timeline_mode}")
        
        lead = state.lead_character['name'] if state.lead_character else "None"
        supports = ", ".join([c['name'] for c in state.support_characters]) or "None"
        print(f"Characters: [Lead] {lead} | [Support] {supports}")
        
        props = ", ".join([p['name'] for p in state.active_props]) or "None"
        print(f"Active Props: {props}")
        
        print(f"\n[Latest Story Beat]")
        summary = state.story_beat_summary or "새로운 서사가 이곳에서 시작됩니다..."
        print(f"> {summary}")
        CanvasUI.draw_line()

    @staticmethod
    def render_stream_zone(stream_history: List[List[Dict]]):
        """Zone 2: AI Card Stream (Paged)."""
        print("\n<<< ZONE 2: AI CARD STREAM >>>")
        if not stream_history:
            print("(현재 스트림이 비어 있습니다. [R] 카드를 뽑아 영감을 채우세요.)")
        else:
            current_page = stream_history[-1] # Show the latest page
            print(f"[ Latest Inspiring Cards ] - Page {len(stream_history)}")
            for i, card in enumerate(current_page):
                name = card.get('name', 'Unknown')
                cat = card.get('category', 'Misc')
                print(f"  {i+1}. [{cat}] {name}")
        CanvasUI.draw_line()

    @staticmethod
    def render_archive_zone(archive: Dict[str, List]):
        """Zone 3: Archive, Discard, Favorites."""
        print("\n<<< ZONE 3: ARCHIVE & HISTORY >>>")
        favs = ", ".join([c['name'] for c in archive.get('favorites', [])]) or "Empty"
        stashed = ", ".join([c['name'] for c in archive.get('stashed', [])]) or "Empty"
        discarded_count = len(archive.get('discarded', []))
        
        print(f"Favorites: {favs}")
        print(f"Stashed: {stashed}")
        print(f"Discarded: {discarded_count} cards")
        CanvasUI.draw_line("=")

class CanvasEngine:
    def __init__(self):
        self.history = HistoryManager()
        self.state = WorldState()
        self.ui = CanvasUI()

    def load_current_state(self):
        """Loads the last state of the current branch."""
        snap_data = self.history.switch_branch(self.history.current_branch_id)
        if snap_data:
            self.state = WorldState.from_dict(snap_data["state"])

    def display_branch_jump(self, target_branch_name: str, summary: str):
        """Visual effect for branch switching."""
        self.ui.clear_screen()
        print("\n" + "!" * 60)
        print(f" 세계선 도약: {target_branch_name}으로 이동 중...")
        print("!" * 60)
        print(f"\n[이전 세계선 요약]\n> {summary}")
        print("\n" + "." * 60)
        # input("\n계속하려면 엔터를 누르세요...") # Skip for logic

    def run_dashboard(self):
        self.load_current_state()
        self.ui.clear_screen()
        
        branch = self.history.get_current_branch()
        self.ui.render_header(branch.name, self.state.total_scenes)
        self.ui.render_canvas_zone(self.state)
        self.ui.render_stream_zone(self.state.stream_history)
        self.ui.render_archive_zone(self.state.archive)
        
        print("\n[Commands] (S)ave Snapshot | (B)ranch | (R)efresh Stream | (Q)uit")
        # For prototype, only UI is rendered. Interaction will be added in next steps.

if __name__ == "__main__":
    engine = CanvasEngine()
    engine.run_dashboard()
