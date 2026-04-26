"""
Review Engine for Phase 13.
Uses AI to evaluate the technical and creative quality of a narrative project.
Provides a merit score (0-100) and directorial feedback.
"""
from typing import Dict, Any, List
from .state_model import WorldState

class ReviewEngine:
    """The 'Director's Eye' that reviews published scenarios."""

    @staticmethod
    def evaluate_project(state: WorldState) -> Dict[str, Any]:
        """
        Analyzes the project based on the specific Target Duration track.
        """
        target = state.target_duration
        beat_count = len(state.story_beats)
        
        # 1. Base Structure Score (Depends on Track)
        if target == "SHORTS":
            # Shorts: 1-5 beats is ideal. Too many beats dilutes impact.
            structure_score = min(40, beat_count * 8)
            if beat_count > 10: structure_score -= (beat_count - 10) * 2 # Penalty for bloat
        else:
            # Long forms: Needs more beats
            structure_score = min(40, beat_count * 4) 
            if beat_count < 15 and target in ["1H", "PR"]: structure_score -= 10 # Penalty for thinness

        # 2. Vision & Blueprint Score (Weight depends on track)
        vision_count = sum(1 for b in state.story_beats if "visual_spec" in b)
        vision_weight = 4 if target in ["1H", "PR"] else 2
        vision_score = min(30, vision_count * vision_weight)
        
        # 3. Character & Contextual Depth
        char_score = 0
        if state.lead_character:
            char_score += 15
            if state.lead_character.get("flaw"): char_score += 10
        
        # 4. Momentum & Sync (Alchemist's Efficiency)
        # Factor in draw/burn ratio as 'Curation Efficiency'
        draws = state.metadata["stats"].get("total_drawn", 1)
        burns = state.metadata["stats"].get("total_burned", 0)
        efficiency = max(0, 10 - (burns / (draws + 1)) * 5) # Up to 10 pts for efficient curation
        
        resonance_score = (state.momentum_level / 5.0) * 5 + efficiency
        
        total_score = structure_score + vision_score + char_score + resonance_score
        total_score = min(100, max(0, total_score))

        feedback = ReviewEngine._generate_track_feedback(total_score, target, state)

        return {
            "ai_score": round(total_score, 1),
            "track": target,
            "feedback": feedback,
            "stats": state.metadata["stats"]
        }

    @staticmethod
    def _generate_track_feedback(score: float, track: str, state: WorldState) -> str:
        if score < 40:
            return f"[{track}] 'Solaris365'의 시선으로 볼 때, 서사의 기저가 아직 흔들리고 있습니다. 상징의 밀도를 더 높여보십시오."
        if score < 80:
            return f"[{track}] 훌륭한 변주입니다. 관객들이 이 { '강렬한 컷' if track=='SHORTS' else '서사적 흐름' }에 공명하기 시작했습니다."
        return f"[{track}] 전율이 느껴지는 마스터피스입니다. 'Solaris365'의 명예의 전당 최상단에 기록될 준비가 되었습니다."

    @staticmethod
    def _generate_mock_feedback(score: float, state: WorldState) -> str:
        if score < 40:
            return "서사의 뼈대가 아직 부족합니다. Solaris365 감독님, 카드의 영혼을 더 깊이 들여다보십시오."
        if score < 70:
            return "흥미로운 전개입니다. 인물 간의 갈등과 시각적 연출(Blueprint)을 보강하면 역작이 될 것입니다."
        if score < 90:
            return "매우 훌륭한 시나리오입니다! 몰입감과 일관성이 뛰어납니다. Solaris365의 이름이 빛나고 있습니다."
        return "완벽에 가까운 서사 설계입니다. AI 디렉터로서 경의를 표합니다. 명예의 전당 등재가 확정되었습니다."
