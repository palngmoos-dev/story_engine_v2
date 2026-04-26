"""
Weaver Engine V2.1 for Grand Atelier.
Implements the 4-step interpretation hierarchy and style-driven generation with AI Writer support.
"""
from typing import List, Dict, Any, Optional
import uuid
from .ai_client_hub import AIClientHub
from .state_model import WorldState, Scene, SceneBlock, WriterCard

DEFAULT_WRITER = WriterCard(
    writer_id="standard_director",
    name="상업 영화 작가",
    domain="영화/드라마",
    genre="보편적 드라마",
    personality="균형감 있는 흥행 지향형",
    style_rules=["기승전결의 명확함", "보편적 공감대"],
    pacing="balanced"
)

class WeaverEngine:
    @staticmethod
    def weave_block_v2(state: WorldState, current_scene: Scene, cards: List[Dict[str, Any]], prev_context: str = "", bridge_card: Optional[Dict[str, Any]] = None) -> SceneBlock:
        """
        Executes the Weaver V2 pipeline:
        1. Card Analysis | 2. Relationship Mapping | 3. Situation Interpretation | 4. Narrative Generation
        """
        style = current_scene.style_card.get("name", "일반") if current_scene.style_card else "일반"
        duration = current_scene.target_duration
        block_id = f"{current_scene.scene_id}-{chr(65 + len(current_scene.blocks))}"
        
        # Mandatory Fallback
        writer = state.active_writer_card or DEFAULT_WRITER
        writer_prompt = f"[WRITER: {writer.name}]\n[STYLE: {writer.genre}]\n[PERSONALITY: {writer.personality}]"

        # 1. Card Analysis
        names = ", ".join([c["name"] for c in cards])
        analysis = AIClientHub.generate(f"상징들({names})에서 서사적 갈등 요소 한 줄 추출.")

        # 2. Relationship Mapping
        relationships = AIClientHub.generate(f"분석({analysis}) 기반 인물/사물의 역학 정의.")
        
        # 3. Situation Interpretation
        bridge_logic = f"브릿지({bridge_card.get('name')})를 통한 시각적 전이." if bridge_card else ""
        interpretation = AIClientHub.generate(f"{writer_prompt}\n관계: {relationships}\n스타일: {style}\n이전 상황: {prev_context}\n{bridge_logic}")
        
        # 4. Narrative Generation
        content = AIClientHub.generate(f"해석: {interpretation}\n조건: {duration} 기준, {style} 및 {writer.pacing} 전개, 한국어.")

        return SceneBlock(
            block_id=block_id, content=content, cards_used=cards, bridge_card=bridge_card,
            is_bridge_active=bool(bridge_card), version=current_scene.version, metadata={"writer_id": writer.writer_id}
        )

    @staticmethod
    def generate_bridge_block(state: WorldState, current_scene: Scene, target_writer: WriterCard) -> SceneBlock:
        """Generates a transition block when switching writers (Bridge Mode)."""
        # Mandatory Fallback
        prev_writer = state.active_writer_card or DEFAULT_WRITER
        last_block = current_scene.blocks[-1] if current_scene.blocks else None
        prev_context = last_block.content if last_block else "서사가 시작됩니다."
        
        prompt = f"작가 {target_writer.name}로서 작가 {prev_writer.name}의 장면을 이어받는 전환 블록을 2문장 내로 작성.\n이전 내용: {prev_context}"
        content = AIClientHub.generate(prompt)
        return SceneBlock(
            block_id=f"{current_scene.scene_id}-BRIDGE", content=content, is_bridge_active=True,
            version=current_scene.version, metadata={"type": "writer_switch", "to": target_writer.writer_id}
        )
