"""
AI Stream Engine for Infinite Narrative Canvas.
Generates AI-powered card streams with normalization and fallbacks.
"""
import json
import re
import uuid
import ollama_client
from typing import List, Dict, Any
from .state_model import WorldState
from .stream_engine import StreamEngine
from .taste_engine import TasteEngine
from .acceleration_engine import AccelerationEngine
from .temptation_engine import PrescriptionEngine
from .blueprint_engine import BlueprintEngine

class AIStreamEngine:
    @staticmethod
    def generate_ai_stream_page(state: WorldState, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generates 10 AI-powered cards based on current state context.
        Provides robust normalization and fallback.
        """
        # 1. Context extraction
        timeline = state.timeline_mode
        metrics = state.global_metrics
        evo_context = TasteEngine.get_evolutionary_context(state)
        momentum = state.momentum_level
        intensity = "폭발적이고 파격적인" if momentum > 2.0 else "안정적이고 개연성 있는"
        
        # 2. Check for Luck or Prescription Opportunity (Phase 7.1)
        # Prescription takes precedence if ailment is detected
        luck_card = PrescriptionEngine.generate_prescription(state)
        if not luck_card:
            luck_card = AccelerationEngine.check_for_luck_opportunity(state)
        
        ailment_context = f"현재 서사 진단: {state.narrative_ailment}"
        
        prompt = f"""
당신은 시네마틱 서사 엔진의 영감 공급기입니다. 
{evo_context}
{ailment_context}
현재 서사 추진력은 {momentum:.1f}입니다 ({intensity} 전개 필요).
현재 타임라인 '{timeline}'과 긴장도 수치 {metrics}에 어울리는 새로운 영감 카드 {count if not luck_card else count-1}장을 생성하십시오.
카드들은 서로 유기적으로 연결되어야 하며, 인상적인 시네마틱 이미지를 연상시켜야 합니다.

반드시 아래 JSON 리스트 형식으로만 응답하십시오. 다른 설명은 생략하십시오.

[
  {{
    "category": "characters|places|props|mood|events",
    "name": "카드 이름",
    "summary": "핵심 서사 요약 (1문장)",
    "style_mood": "시각/청각적 분위기 (예: 차가운 네온 레트로, 신비로운 숲의 정적)",
    "tags": ["태그1", "태그2"]
  }},
  ...
]
"""
        try:
            response = ollama_client.ollama_generate(prompt)
            # Parse JSON list
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if not match:
                raise ValueError("AI response format error")
            
            raw_cards = json.loads(match.group(0))
            normalized = AIStreamEngine._normalize_cards(raw_cards, timeline)
            
            # 3. Inject Luck Card if spawned (Phase 7)
            if luck_card:
                import random
                normalized.insert(random.randint(0, len(normalized)), luck_card)
            
            # 4. Attach Blueprints (Phase 8.3)
            BlueprintEngine.attach_blueprints_to_cards(normalized, momentum=state.momentum_level)
            
            # Update stagnation (active use resets score)
            AccelerationEngine.update_stagnation(state, action_taken=True)
            
            return normalized
            
        except Exception as e:
            # Fallback to preset-based stream on error
            print(f"\n[AI Stream Engine] Fallback activated due to: {e}")
            fallback_page = StreamEngine.generate_stream_page(count=count)
            return AIStreamEngine._normalize_cards(fallback_page, timeline)

    @staticmethod
    def _normalize_cards(raw_cards: List[Dict[str, Any]], timeline: str) -> List[Dict[str, Any]]:
        """Ensures all cards follow the official schema."""
        normalized = []
        for card in raw_cards:
            # Generate stable defaults for missing fields
            n_card = {
                "cid": card.get("cid") or f"ai_{uuid.uuid4().hex[:6]}",
                "category": card.get("category") or "events",
                "name": card.get("name") or "말할 수 없는 영감",
                "summary": card.get("summary") or card.get("description") or "서사의 빈칸을 채우는 조각입니다.",
                "style_mood": card.get("style_mood") or "균형 잡힌 시네마틱 무드",
                "tags": card.get("tags") or [],
                "origin_id": card.get("origin_id"),
                "variant_info": card.get("variant_info") or {"timeline": timeline, "type": "AI_GENERATED"}
            }
            normalized.append(n_card)
        return normalized[:10] # Ensure exactly or max 10
