"""
Clustering Engine for Infinite Narrative Canvas.
Handles grouping and narrative linking of cards in Step C.
"""
import uuid
from typing import List, Dict, Any, Optional
from .state_model import WorldState

class ClusteringEngine:
    @staticmethod
    def create_group(cards: List[Dict[str, Any]], 
                     group_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a cluster (group) object from a list of cards.
        Non-destructive: Only stores pointers (card_ids).
        """
        if len(cards) < 2:
            raise ValueError("A group must contain at least 2 cards.")
            
        group_id = f"group_{uuid.uuid4().hex[:8]}"
        card_ids = [c.get("cid") or c.get("name") for c in cards]
        
        # Placeholder for AI-driven alias suggestion in future steps
        alias_suggestion = f"Cluster of {len(cards)} inspirations"
        
        group_obj = {
            "group_id": group_id,
            "name": group_name or f"Group #{group_id[-4:]}",
            "alias_suggestion": alias_suggestion,
            "card_ids": card_ids,
            "summary": "서사적 연관성을 가진 카드들의 묶음입니다.",
            "timeline": cards[0].get("variant_info", {}).get("timeline", "PRESENT")
        }
        
        return group_obj

    @staticmethod
    def add_group_to_state(state: WorldState, group_obj: Dict[str, Any]):
        """Registers a new group in the world state."""
        state.card_groups.append(group_obj)

    @staticmethod
    def get_cards_in_group(state: WorldState, group_id: str) -> List[Dict[str, Any]]:
        """Resolves card IDs in a group to actual card objects if available."""
        # Note: Some cards might be in archives or discarded. 
        # For Step C, we assume they are discoverable in current canvas or stream.
        target_group = next((g for g in state.card_groups if g["group_id"] == group_id), None)
        if not target_group:
            return []
            
        # Simplified resolution logic for Step C proof
        found_cards = []
        all_active_cards = state.active_canvas_cards + [c for p in state.stream_pages for c in p]
        
        for cid in target_group["card_ids"]:
            card = next((c for c in all_active_cards if c.get("cid") == cid), None)
            if card:
                found_cards.append(card)
                
        return found_cards
