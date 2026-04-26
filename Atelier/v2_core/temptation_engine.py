"""
Temptation & Prescription Engine for Phase 7.1.
Diagnoses narrative ailments and provides prescriptive luck cards.
"""
import random
from typing import Dict, List, Any, Optional
from .state_model import WorldState

class PrescriptionEngine:
    AILMENTS = {
        "STAGNATION": "전개 정체: 서사에 새로운 동력이 필요합니다.",
        "BLOATED": "서사 비대: 너무 많은 파편이 흩어져 있습니다.",
        "THIN_CAST": "인물 결핍: 이야기의 주역들에게 생명력이 부족합니다.",
        "CALM_STORM": "폭풍 전야: 너무 평화로운 상태가 지속되고 있습니다."
    }

    TREATMENTS = {
        "VITAMIN": {"name": "서사 비타민", "effect": "지속적 추진력 상향", "risk": 0.05},
        "PROSTHETIC": {"name": "강화 장치(Prosthetic)", "effect": "약점 강화 및 돌발 가속", "risk": 0.20},
        "ADRENALINE": {"name": "아드레날린 쇼트", "effect": "한계 돌파 및 마하 진입", "risk": 0.40}
    }

    @staticmethod
    def diagnose_state(state: WorldState) -> str:
        """Deep scan for narrative bottlenecks."""
        if state.stagnation_score > 7:
            return "STAGNATION"
        if len(state.active_canvas_cards) < 2 and len(state.story_beats) > 5:
            return "THIN_CAST"
        if state.momentum_level < 0.8:
            return "CALM_STORM"
        return "HEALTHY"

    @staticmethod
    def generate_prescription(state: WorldState) -> Optional[Dict[str, Any]]:
        """Creates a prescription card based on the diagnosis."""
        ailment = PrescriptionEngine.diagnose_state(state)
        state.narrative_ailment = ailment
        
        if ailment == "HEALTHY" and random.random() > 0.2:
            return None
            
        # Select treatment based on ailment intensity
        if ailment == "STAGNATION":
            t_key = "ADRENALINE"
        elif ailment == "THIN_CAST":
            t_key = "PROSTHETIC"
        else:
            t_key = "VITAMIN"
            
        treatment = PrescriptionEngine.TREATMENTS[t_key]
        return {
            "cid": f"RX_{random.randint(1000, 9999)}",
            "category": "LUCK",
            "name": f"[{treatment['name']}]",
            "summary": f"진단[{ailment}]: {treatment['effect']} (위험도: {treatment['risk']*100:.0f}%)",
            "tags": ["Prescription", ailment, t_key],
            "luck_type": t_key,
            "risk_value": treatment["risk"]
        }

    @staticmethod
    def process_treatment(state: WorldState, prescription: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates success or side effect of the prescription."""
        risk = prescription.get("risk_value", 0.1)
        # Add factor based on mutation rate
        effective_risk = risk + (state.side_effect_count * 0.05)
        
        if random.random() > effective_risk:
            # SUCCESS: Evolution
            state.momentum_level += 2.0 if prescription["luck_type"] == "ADRENALINE" else 0.8
            state.sync_intensity = min(1.0, state.sync_intensity + 0.3)
            state.side_effect_count = max(0, state.side_effect_count - 1)
            return {"status": "SUCCESS", "message": "처방이 완벽하게 작용하여 서사가 진화했습니다!"}
        else:
            # FAILURE: Side Effect
            state.side_effect_count += 2
            state.momentum_level = 0.5 # Stunned
            return {"status": "FAILURE", "message": "처방 부작용 발생! 서사가 뒤틀린 평행 세계로 튕겨 나갑니다."}
