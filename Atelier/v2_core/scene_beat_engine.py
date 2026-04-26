"""
Scene Beat Engine for Infinite Narrative Canvas.
Generates focused narrative beats from canvas context and clusters.
"""
import json
import re
import ollama_client
from typing import Dict, Any, List, Optional
from .state_model import WorldState

class SceneBeatEngine:
    @staticmethod
    def generate_scene_beat(state: WorldState, 
                            selected_cards: Optional[List[Dict[str, Any]]] = None,
                            selected_group: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates a 2-4 sentence scene beat based on canvas context.
        Follows a strict output structure and timeline sensitivity.
        """
        # 1. Gather Context
        timeline = state.timeline_mode
        metrics = state.global_metrics
        
        # Determine the primary deck to analyze
        source_cards = selected_cards or state.active_canvas_cards
        if selected_group:
            # Add group cards to context if provided
            # Group info logic here... (Simplified for Step C/Phase 3)
            pass

        card_names = [c.get("name") for c in source_cards] if source_cards else ["미지의 공간"]
        
        # 2. Build Timeline-Specific Persona
        timeline_guidance = {
            "PAST": "아련한 회상, 빛바랜 질감, 고전적이고 정적인 문체를 사용하십시오.",
            "PRESENT": "현장감 있는 묘사, 현재 시제, 선명하고 직관적인 문체를 사용하십시오.",
            "FUTURE": "테크니컬한 예견, 차가운 분위기, 비현실적이거나 날카로운 문체를 사용하십시오."
        }.get(timeline, "중립적인 문체를 사용하십시오.")

        prompt = f"""
당신은 시네마틱 서사 엔진의 연출가입니다.
현재 타임라인은 '{timeline}'이며, 다음과 같은 요소를 바탕으로 하나의 강렬한 장면(Scene Beat)을 생성하십시오.
{timeline_guidance}

[사용 카드]
{", ".join(card_names)}

[엔진 지표]
수치: {metrics}

반드시 아래 JSON 형식으로만 응답하십시오.
{{
  "beat_text": "2~4문장의 강렬한 서사 묘사 및 대사",
  "directing_memo": "연출 무드 및 텐션 조절 가이드 (1문장)",
  "next_inspiration": "이 장면에 이어질 어울리는 카드 유형 추천 (1문장)"
}}
"""
        try:
            response = ollama_client.ollama_generate(prompt)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                raise ValueError("JSON parse error")
            
            beat_data = json.loads(match.group(0))
            return SceneBeatEngine._validate_structure(beat_data, timeline)
            
        except Exception as e:
            print(f"\n[Scene Beat Engine] Fallback used: {e}")
            return SceneBeatEngine._get_fallback_beat(timeline)

    @staticmethod
    def _validate_structure(data: Dict[str, Any], timeline: str) -> Dict[str, Any]:
        """Ensures the AI response meets the 3-field requirement."""
        return {
            "beat_text": data.get("beat_text") or f"[{timeline}] 서사의 공백이 깊어집니다..",
            "directing_memo": data.get("directing_memo") or "침묵을 유지하며 관찰하십시오.",
            "next_inspiration": data.get("next_inspiration") or "새로운 인물을 등장시켜 반전을 꾀하십시오."
        }

    @staticmethod
    def _get_fallback_beat(timeline: str) -> Dict[str, Any]:
        """Stability fallback."""
        texts = {
            "PAST": "오래된 기억의 한 조각이 수면 위로 떠오릅니다. 이미 끝난 이야기의 여운이 남습니다.",
            "PRESENT": "공간의 공기가 차갑게 가라앉습니다. 무언가 일어날 것 같은 예감이 듭니다.",
            "FUTURE": "차가운 금속음과 함께 어떤 파편이 선명해집니다. 예정된 충돌이 다가옵니다."
        }
        return {
            "beat_text": texts.get(timeline, texts["PRESENT"]),
            "directing_memo": "긴장감을 극도로 낮추고 정적인 무드에서 시작하십시오.",
            "next_inspiration": "장소 카드를 확인하여 공간의 디테일을 보완하십시오."
        }
