"""
Narrative Pulse Engine for Phase 10.
Analyzes story beats and state to derive tension index, character psychology,
and AI-driven directorial notes.
"""
from typing import Dict, Any, List
from .state_model import WorldState

class PulseEngine:
    """The 'heartbeat' analyzer for the cinematic narrative."""

    TENSION_LABELS = [
        "평온(Calm)", "빌드업(Build-up)", "긴장(Tension)", "위기(Crisis)", "절정(Climax)"
    ]

    PSYCHOLOGY_MODES = {
        "STAGNATION": ["나태", "권태", "막막함", "정체"],
        "NORMAL": ["관찰", "탐색", "평온", "호기심"],
        "SURGE": ["고무됨", "광기", "질주", "압도"],
        "STRESS": ["불안", "압박", "강박", "편집증"]
    }

    @staticmethod
    def analyze_pulse(state: WorldState) -> Dict[str, Any]:
        """
        Main entry point for Pulse analysis.
        Calculates tension based on momentum, stagnation, and story length.
        """
        tension_score = PulseEngine._calculate_tension(state)
        psychology = PulseEngine._infer_psychology(state, tension_score)
        
        # Determine the label based on score (0.0 to 1.0)
        label_idx = min(len(PulseEngine.TENSION_LABELS) - 1, int(tension_score * len(PulseEngine.TENSION_LABELS)))
        tension_label = PulseEngine.TENSION_LABELS[label_idx]

        directors_note = PulseEngine._get_directors_note(state, tension_score, tension_label)

        return {
            "tension": round(tension_score, 2),
            "label": tension_label,
            "psychology": psychology,
            "directors_note": directors_note,
            "pulse_visual": PulseEngine._get_pulse_visual(tension_score)
        }

    @staticmethod
    def _calculate_tension(state: WorldState) -> float:
        """
        Calculates a 0.0-1.0 tension score.
        Formula factors: Momentum, Stagnation (inverse), and Beat count % 5 (cycle).
        """
        # Momentum contributes up to 0.5 (at level 5.0)
        momentum_factor = min(0.5, (state.momentum_level / 5.0) * 0.5)
        
        # Stagnation penalty (higher stagnation lowers tension/energy)
        stagnation_factor = max(-0.2, (state.stagnation_score / 10.0) * -0.2)
        
        # Story narrative arc cycle (simplified sin-wave-like using beat count)
        beat_count = len(state.story_beats)
        cycle_factor = (beat_count % 8) / 8.0 * 0.4 # Cycle every 8 beats
        
        # Meta factors (Ailment impact)
        meta_impact = 0.0
        if state.narrative_ailment == "SURGE": meta_impact = 0.2
        elif state.narrative_ailment == "STAGNATION": meta_impact = -0.1

        total = 0.2 + momentum_factor + stagnation_factor + cycle_factor + meta_impact
        return max(0.0, min(1.0, total))

    @staticmethod
    def _infer_psychology(state: WorldState, tension: float) -> str:
        """Infers character's current predominant emotion based on state."""
        ailment = state.narrative_ailment
        if ailment in PulseEngine.PSYCHOLOGY_MODES:
            modes = PulseEngine.PSYCHOLOGY_MODES[ailment]
        else:
            modes = PulseEngine.PSYCHOLOGY_MODES["NORMAL"]
            
        # Select sub-mode based on tension
        idx = min(len(modes)-1, int(tension * len(modes)))
        return modes[idx]

    @staticmethod
    def _get_directors_note(state: WorldState, score: float, label: str) -> str:
        """Returns a short AI directorial tip based on tension."""
        if score < 0.3:
            return "서사가 너무 평탄합니다. 예상치 못한 갈등을 투입하거나 주인공의 약점(Flaw)을 건드리세요."
        if score < 0.6:
            return "좋은 빌드업입니다. 이제 서서히 '대가(Cost)'를 요구할 시점이 다가오고 있습니다."
        if score < 0.8:
            return "긴장감이 최고조입니다! 여기서 주인공을 승리하게 할지, 더 큰 나락으로 떨어뜨릴지 결정하십시오."
        return "현재 '절정' 상태입니다. 연출 지시서(Blueprint)의 조명과 구도를 극단적으로 활용하십시오."

    @staticmethod
    def _get_pulse_visual(score: float) -> str:
        """Renders an emoji-based tension bar."""
        filled = int(score * 10)
        return "🔥" * filled + "░" * (10 - filled)
