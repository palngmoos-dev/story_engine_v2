"""
AI Alias Engine for Infinite Narrative Canvas.
Suggests creative names and meanings for card clusters.
"""
import json
import re
import ollama_client
from typing import Dict, Any, List, Optional
from .state_model import WorldState

class AIAliasEngine:
    @staticmethod
    def suggest_group_alias(group: Dict[str, Any], state: WorldState) -> Dict[str, Any]:
        """
        Analyzes cards in a group and suggests 3 creative aliases.
        Includes fallbacks for stability.
        """
        # 1. Prepare data for AI
        # Note: We need the actual names/summaries of the cards in the group
        # This assumes card_ids can be resolved within the current state
        card_info = []
        all_cards = state.active_canvas_cards + [c for p in state.stream_pages for c in p]
        
        for cid in group.get("card_ids", []):
            card = next((c for c in all_cards if c.get("cid") == cid), None)
            if card:
                card_info.append(f"- {card.get('name')}: {card.get('summary')}")

        if not card_info:
            return AIAliasEngine._get_fallback_alias(group)

        prompt = f"""
당신은 서사의 조각들을 연결하는 스토리 설계자입니다. 
아래 카드들의 조합을 보고, 이 묶음에 어울리는 창의적이고 감각적인 '별칭(Alias)'을 3개 제안하십시오.
서사적 맥락을 함축하고 시각적인 이미지를 떠올리게 하는 이름을 선호합니다.

[카드 목록]
{chr(10).join(card_info)}

반드시 아래 JSON 형식으로만 응답하십시오.
{{
  "suggestions": [
     {{"name": "별칭 1", "reason": "이 이름인 이유 (1문장)"}},
     {{"name": "별칭 2", "reason": "이 이름인 이유"}},
     {{"name": "별칭 3", "reason": "이 이름인 이유"}}
  ]
}}
"""
        try:
            response = ollama_client.ollama_generate(prompt)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                raise ValueError("JSON parse error")
            
            suggestions = json.loads(match.group(0))
            return suggestions
        except Exception as e:
            print(f"\n[AI Alias Engine] Fallback used: {e}")
            return AIAliasEngine._get_fallback_alias(group)

    @staticmethod
    def _get_fallback_alias(group: Dict[str, Any]) -> Dict[str, Any]:
        """Stability fallback."""
        num = len(group.get("card_ids", []))
        return {
            "suggestions": [
                {"name": f"결속된 {num}개의 조각", "reason": "선택된 영감들이 하나의 서사 단위를 형성합니다."},
                {"name": f"임시 그룹 {group.get('group_id')[-4:]}", "reason": "새로운 맥락의 발견을 기다리는 조합입니다."}
            ]
        }
