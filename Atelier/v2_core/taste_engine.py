"""
Evolutionary Taste Engine for Infinite Narrative Canvas.
Handles vector learning, multi-layer memory, and time decay in Phase 5.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from .state_model import WorldState

class TasteEngine:
    # Action weights for Learning
    PICK_WEIGHT = 1.0
    FAV_WEIGHT = 1.5
    DISCARD_WEIGHT = -2.0 # Strong avoidance pressure

    # Decay rates per layer
    HOT_DECAY = 0.85
    WARM_DECAY = 0.98
    COLD_DECAY = 0.999

    @staticmethod
    def record_interaction(state: WorldState, card: Dict[str, Any], action: str):
        """
        Records an interaction and updates the taste vector based on selection pressure.
        action: 'PICK', 'FAVORITE', 'DISCARD'
        """
        # 1. Log Raw History
        entry = {
            "timestamp": datetime.now().isoformat(),
            "card_id": card.get("cid"),
            "action": action,
            "tags": card.get("tags", []),
            "category": card.get("category")
        }
        state.interaction_history.append(entry)

        # 2. Update Hot Layer
        state.interaction_layers["hot"].append(entry)
        if len(state.interaction_layers["hot"]) > 10:
            # Rollover to warm
            oldest = state.interaction_layers["hot"].pop(0)
            state.interaction_layers["warm"].append(oldest)
            
        if len(state.interaction_layers["warm"]) > 50:
            # Rollover to cold
            oldest_warm = state.interaction_layers["warm"].pop(0)
            state.interaction_layers["cold"].append(oldest_warm)

        # 3. Vector Learning Update
        TasteEngine._update_vector(state, card, action)

    @staticmethod
    def _update_vector(state: WorldState, card: Dict[str, Any], action: str):
        """Adjusts the taste_vector using continuous values."""
        multiplier = {
            "PICK": TasteEngine.PICK_WEIGHT,
            "FAVORITE": TasteEngine.FAV_WEIGHT,
            "DISCARD": TasteEngine.DISCARD_WEIGHT
        }.get(action, 0.1)

        lr = state.learning_rate
        tags = card.get("tags", [])
        category = card.get("category")

        # Update category weight
        if category:
            current_val = state.taste_vector.get(category, 0.5)
            # Sigmoid-like update or simple bounded add
            new_val = current_val + (lr * multiplier)
            state.taste_vector[category] = max(0.0, min(1.0, new_val))

        # Update tag weights
        for tag in tags:
            current_val = state.taste_vector.get(tag, 0.2)
            new_val = current_val + (lr * multiplier)
            state.taste_vector[tag] = max(0.0, min(1.0, new_val))

    @staticmethod
    def apply_decay(state: WorldState):
        """Periodically reduces weights based on differential time decay."""
        # Note: In a real long-running app, this would be tied to timestamps.
        # For Phase 5 CLI, we call this periodically or on certain events.
        for key in state.taste_vector:
            # Simple uniform decay for baseline (enhanced by layers in context generation)
            state.taste_vector[key] *= TasteEngine.WARM_DECAY

    @staticmethod
    def get_evolutionary_context(state: WorldState) -> str:
        """Translates the numerical vector into a cinematic prompt for AI."""
        # Sort by weight
        sorted_taste = sorted(state.taste_vector.items(), key=lambda x: x[1], reverse=True)
        
        top_likes = [t for t, v in sorted_taste if v > 0.6][:5]
        hates = [t for t, v in sorted_taste if v < 0.2][:3]
        
        context = "[Evolutionary Context]\n"
        if top_likes:
            context += f"- 현재 창작자는 다음 핵심 태그에 높은 반응을 보임: {', '.join(top_likes)}\n"
        if hates:
            context += f"- 다음 요소는 서사적 회피 대상으로 분류됨: {', '.join(hates)}\n"
            
        # Add Mutation tip
        if state.mutation_rate > 0:
            context += f"- (System) {state.mutation_rate*100}% 확률로 기존 취향과 상반된 '돌연변이' 영감을 섞으십시오.\n"
            
        return context

    @staticmethod
    def get_hot_picks(state: WorldState) -> List[str]:
        """Returns the most immediate recent interests (from Hot Layer)."""
        hot_tags = []
        for entry in state.interaction_layers["hot"]:
            hot_tags.extend(entry.get("tags", []))
        
        # Count frequencies
        freq = {}
        for t in hot_tags:
            freq[t] = freq.get(t, 0) + 1
            
        sorted_hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [t for t, f in sorted_hot][:5]
