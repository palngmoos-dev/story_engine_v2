"""
Tarot Engine for Phase 14: The Infinite Weaver.
Handles the mystical 'Tarot-like' card interaction logic: drawing, spreading, and interpretation.
"""
import random
import uuid
from typing import List, Dict, Any
from .state_model import WorldState
from .ai_stream_engine import AIStreamEngine

class TarotEngine:
    @staticmethod
    def initialize_tarot_session(state: WorldState):
        """Deals an initial 3-card spread to spark the narrative."""
        # 1. Clear current spread
        state.tarot_spread = []
        
        # 2. Get 3 random cards from the stream (using existing engine)
        cards = AIStreamEngine.generate_ai_stream_page(state, count=3)
        
        # 3. Add to spread with 'hidden' state (Tarot metaphor)
        for card in cards:
            card["is_revealed"] = False
            state.tarot_spread.append(card)
        
        state.metadata["summary"] = "AI 딜러가 3장의 운명을 제시했습니다. 카드를 뒤집어 해석을 확인하세요."

    @staticmethod
    def draw_to_spread(state: WorldState):
        """Draws one face-down card to the spread board. Increments stats."""
        # Check limit (user requested 'unlimited' but logic should handle hand-size for UI)
        # We don't enforce a hard block but log numbers.
        
        new_cards = AIStreamEngine.generate_ai_stream_page(state, count=1)
        for card in new_cards:
            card["is_revealed"] = False
            state.tarot_spread.append(card)
            
        # Update metrics
        state.metadata["stats"]["total_drawn"] += 1
        state.metadata["stats"]["current_scene_draws"] += 1

    @staticmethod
    def reveal_card(state: WorldState, card_id: str):
        """Flips a card on the spread board."""
        for card in state.tarot_spread:
            if card.get("cid") == card_id:
                card["is_revealed"] = True
                break
        
        # Interpretation is now handled asynchronously by Orchestrator

    @staticmethod
    def burn_card(state: WorldState, card_id: str):
        """Discards a card from the spread. Increments burn stats."""
        # Archive current spread to 'last deleted' for potential undo if needed
        state.tarot_spread = [c for c in state.tarot_spread if c.get("cid") != card_id]
        
        state.metadata["stats"]["total_burned"] += 1
        state.metadata["stats"]["current_scene_burns"] += 1
        
        # Interpretation is now handled asynchronously by Orchestrator

    @staticmethod
    def calculate_running_time(text: str, speed: float = 1.0) -> Dict[str, float]:
        """Estimates duration based on text length and speech speed (Words Per Minute)."""
        # Average reading speed: 130 words per minute (English) / 300 characters per minute (Korean)
        char_count = len(text)
        seconds = (char_count / 300) * 60 / speed
        return {
            "seconds": round(seconds, 1),
            "minutes": round(seconds / 60, 2)
        }

    @staticmethod
    def recall_scene_assets(state: WorldState, scene_index: int):
        """Clones assets from a previous scene to the current spread."""
        if scene_index < 0 or scene_index >= len(state.story_beats):
            return False
            
        scene = state.story_beats[scene_index]
        # Logic: Find cards associated with this scene or from history
        # For now, we assume the scene stores its card references
        recalled_cards = scene.get("cards", [])
        for card in recalled_cards:
            cloned = card.copy()
            cloned["cid"] = f"recall_{uuid.uuid4().hex[:4]}_{card['cid']}"
            cloned["is_revealed"] = True
            state.tarot_spread.append(cloned)
            
        TarotEngine.sync_interpretation(state)
        return True

    @staticmethod
    def sync_interpretation(state: WorldState):
        """
        Reads all revealed cards on the board and generates the AI's 'Interpretation' (Draft).
        Also generates a BGM prompt for the Cinematic Aura.
        """
        from .weaver_engine import WeaverEngine
        
        # Use revealed cards for interpretation (Single check)
        revealed_cards = [c for c in state.tarot_spread if c.get("is_revealed")]
        if not revealed_cards:
            state.current_interpretation = "아직 상징이 드러나지 않았습니다. 운명의 카드를 뒤집어 주세요."
            return

        # Take top 5 cards for MVP verification if many are revealed
        target_cards = revealed_cards[:5]
        
        try:
            story = WeaverEngine.weave_narrative_mvp(state, target_cards)
            state.current_interpretation = story
            
            # Simple BGM prompt update logic
            # Phase 16: Move this to a dedicated Audio Engine
            state.current_multimodal_assets["bgm_prompt"] = f"Cinematic atmosphere following: {story[:30]}..."
        except Exception as e:
            card_names = ", ".join([c.get("name", "Unknown") for c in target_cards])
            state.current_interpretation = f"[직조 실패: {e}] {card_names} 상징들이 얽혀 있습니다."

    @staticmethod
    def _get_duration_context(track: str) -> str:
        mapping = {
            "SHORTS": "컷 중심의 초고속 전개, 30초~1분 미학",
            "30M": "기승전결이 압축된 단편 영화의 미학",
            "1H": "깊이 있는 캐릭터 탐구와 에피소드 완성도",
            "PR": "장대한 서사시와 철학적 사유, 2시간의 대작"
        }
        return mapping.get(track, "표준 서사 전개")
