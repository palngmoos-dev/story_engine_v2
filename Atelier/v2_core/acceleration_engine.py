"""
Acceleration & Luck Engine for Phase 7.
Manages narrative momentum (The Surge), stagnation detection, and luck cards.
"""
import random
from typing import Dict, List, Any, Optional
from .state_model import WorldState

class AccelerationEngine:
    # Luck Card Definitions
    LUCK_CARD_TYPES = {
        "NITRO_SWIFT": {
            "name": "행운: 질주(Nitro Swift)",
            "summary": "서사의 속도를 폭발시킵니다. 3턴간 생성 밀도 2배.",
            "tags": ["Speed", "Pulse"]
        },
        "PRISM_BREAK": {
            "name": "행운: 프리즘(Prism Break)",
            "summary": "취향의 경계를 허뭅니다. 실험적이고 참신한 아이디어 주입.",
            "tags": ["Novelty", "Rainbow"]
        },
        "WORLD_LEAP": {
            "name": "행운: 도약(World Leap)",
            "summary": "평행 세계의 경계를 깹니다. 전혀 다른 장르의 파편 주입.",
            "tags": ["Chaos", "Dimension"]
        }
    }

    @staticmethod
    def update_stagnation(state: WorldState, action_taken: bool = False):
        """Monitors user activity and increments stagnation if no core action."""
        if action_taken:
            state.stagnation_score = max(0, state.stagnation_score - 2)
        else:
            state.stagnation_score += 1
        
        # Slowly decay momentum if stagnant
        if state.stagnation_score > 5:
            state.momentum_level = max(0.5, state.momentum_level - 0.05)

    @staticmethod
    def check_for_luck_opportunity(state: WorldState) -> Optional[Dict[str, Any]]:
        """Determines if a luck card should be spawned based on stagnation."""
        chance = 0.05 + (state.stagnation_score * 0.05) # Higher stagnation = higher luck
        if random.random() < min(0.3, chance):
            card_key = random.choice(list(AccelerationEngine.LUCK_CARD_TYPES.keys()))
            card_info = AccelerationEngine.LUCK_CARD_TYPES[card_key]
            return {
                "cid": f"LUCK_{random.randint(100, 999)}",
                "category": "LUCK",
                "name": card_info["name"],
                "summary": card_info["summary"],
                "tags": card_info["tags"],
                "luck_type": card_key
            }
        return None

    @staticmethod
    def trigger_surge(state: WorldState, luck_type: str):
        """Activates the specific surge/limit-break effect."""
        if luck_type == "NITRO_SWIFT":
            state.momentum_level += 1.5
            state.sync_intensity += 0.2
        elif luck_type == "PRISM_BREAK":
            state.mutation_rate *= 3
            state.sync_intensity += 0.4
        elif luck_type == "WORLD_LEAP":
            state.momentum_level += 0.5
            state.sync_intensity -= 0.3 # High chaos, low sync
            
        # Add to inventory (soft-hold)
        state.luck_card_inventory.append({"type": luck_type, "timestamp": str(random.random())})
        
        # Reset stagnation on luck trigger
        state.stagnation_score = 0

    @staticmethod
    def apply_momentum_decay(state: WorldState):
        """Natural decay of momentum back to baseline 1.0."""
        if state.momentum_level > 1.0:
            state.momentum_level -= 0.1
        elif state.momentum_level < 1.0:
            state.momentum_level += 0.05
