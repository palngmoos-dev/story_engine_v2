"""
Convergence Engine for Infinite Narrative Canvas.
Computes narrative gravity, scoring, and commitment suggestions in Phase 6.
"""
from typing import List, Dict, Any, Optional
from .state_model import WorldState

class ConvergenceEngine:
    # Tuned Thresholds for Phase 6
    COMMIT_THRESHOLD = 0.65 # Lowered to see nodes converging
    PRUNE_THRESHOLD = 0.45  # Increased to prune noise faster
    
    # Weighted Scoring System
    WEIGHTS = {
        "taste_alignment": 0.35, 
        "narrative_alignment": 0.35,
        "profile_boost": 0.20, # Extra reward for matching core profile
        "recency": 0.05,
        "novelty": 0.05
    }

    @staticmethod
    def compute_narrative_vector(state: WorldState) -> Dict[str, Any]:
        """
        Infers the current 'Dominant Story Profile' from narrative log and taste.
        Cumulative inference logic.
        """
        # 1. Analyze Core Themes from Narrative Log
        history = [entry.get("summary", "") for entry in state.interaction_history if entry.get("action") == "PICK"]
        
        # Simple theme inference (placeholder for AI enhanced version)
        dominant_tags = sorted(state.taste_vector.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Update state profile
        profile = {
            "core_theme": "수렴 중인 서사",
            "core_tone": "침울한 누아르" if state.taste_vector.get("Noir", 0) > 0.6 else "중립",
            "dominant_tags": [t for t, v in dominant_tags],
            "preferred_timeline": state.timeline_mode,
            "gravity_center": state.taste_vector
        }
        state.dominant_story_profile = profile
        return profile

    @staticmethod
    def get_narrative_score(item: Dict[str, Any], state: WorldState, item_type: str = "card") -> Dict[str, Any]:
        """
        Calculates a score (0.0 to 1.0) for an item and provides a reason.
        """
        # 1. Taste Alignment
        tags = item.get("tags", [])
        cid = item.get("cid")
        taste_sum = sum(state.taste_vector.get(t, 0.2) for t in tags)
        taste_score = (taste_sum / len(tags)) if tags else 0.4
        
        # 2. Narrative Alignment (Connection to committed themes)
        dominant_tags = state.dominant_story_profile.get("dominant_tags", [])
        overlap = [t for t in tags if t in dominant_tags]
        narrative_score = (len(overlap) / len(dominant_tags)) if dominant_tags else 0.5
        
        # 3. Repetition Weight (Learning from history)
        repetition_count = sum(1 for h in state.interaction_history if h.get("card_id") == cid and h.get("action") == "PICK")
        repetition_boost = min(0.3, repetition_count * 0.1)
        
        # 4. Profile Boost (Theme alignment reward)
        profile_boost = 0.2 if overlap else 0.0
        
        # 5. Aggregation
        final_score = (
            taste_score * ConvergenceEngine.WEIGHTS["taste_alignment"] +
            narrative_score * ConvergenceEngine.WEIGHTS["narrative_alignment"] +
            profile_boost + repetition_boost
        )
        final_score = max(0.0, min(1.0, final_score))
        
        # 6. Avoidance Cap (Strong penalty for discarded tags)
        discarded_tags = [h.get("tags", []) for h in state.interaction_history if h.get("action") == "DISCARD"]
        flat_discarded = [tag for sublist in discarded_tags for tag in sublist]
        if any(t in flat_discarded for t in tags):
            final_score = min(0.3, final_score) # Force to prune zone
            reason = "과거에 폐기한 태그가 포함되어 서사적 회피 대상으로 분류되었습니다."
        else:
            # 7. Reason Generation
            if final_score >= ConvergenceEngine.COMMIT_THRESHOLD:
                reason = f"핵심 테마({', '.join(overlap[:2])})와 반복된 선택에 의한 'Soft Commit' 대상입니다."
            elif final_score < ConvergenceEngine.PRUNE_THRESHOLD:
                reason = "현 서사 중심축과 멀어져 정리를 추천합니다."
            else:
                reason = "서사의 잠재적 후보군입니다."

        return {
            "score": final_score,
            "reason": reason
        }

    @staticmethod
    def classify_narrative_layers(state: WorldState):
        """
        Pruning strategy: classify items into commit candidates or prune candidates.
        """
        # Reset candidates
        state.commit_candidates = {"cards": [], "groups": [], "beats": []}
        state.prune_candidates = {"cards": [], "groups": [], "beats": []}
        
        # Analyze Stream Cards
        for page in state.stream_pages:
            for card in page:
                result = ConvergenceEngine.get_narrative_score(card, state)
                if result["score"] >= ConvergenceEngine.COMMIT_THRESHOLD:
                    state.commit_candidates["cards"].append({"card": card, "reason": result["reason"]})
                elif result["score"] < ConvergenceEngine.PRUNE_THRESHOLD:
                    state.prune_candidates["cards"].append({"card": card, "reason": result["reason"]})

        # Analyze Groups
        for group in state.card_groups:
            # Score based on avg of cards inside
            # Simplified for Phase 6 proof
            if len(group.get("card_ids", [])) >= 3:
                state.commit_candidates["groups"].append({"group": group, "reason": "3회 이상 반복 선택된 서사적 군집입니다."})

    @staticmethod
    def suggest_commitments(state: WorldState):
        """Prepares a finalized proposal for the user."""
        ConvergenceEngine.compute_narrative_vector(state)
        ConvergenceEngine.classify_narrative_layers(state)
