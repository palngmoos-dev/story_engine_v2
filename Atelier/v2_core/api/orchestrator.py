from typing import Dict, Any, Optional, List
from .project_manager import ProjectManager
from .schemas import CommonResponse
from ..state_model import WorldState, Scene, SceneBlock
from ..weaver_engine import WeaverEngine
from ..tarot_engine import TarotEngine
from ..writer_factory import WriterFactory

class NarrativeOrchestrator:
    def __init__(self, project_manager: ProjectManager, gemma: Optional[Any] = None):
        self.pm = project_manager
        self.storage = project_manager.storage
        self.gemma = gemma

    def _get_state_summary(self, state: WorldState) -> Dict[str, Any]:
        """Provides a consolidated summary for the stateless API client."""
        cur_idx = state.current_scene_index
        current_scene = state.scene_registry[cur_idx][-1].dict() if cur_idx in state.scene_registry else None
        return {
            "active_cards": state.tarot_spread,
            "characters": list(state.memory_db["characters"].values()),
            "active_writer": state.active_writer_card.dict() if state.active_writer_card else None,
            "is_writer_locked": state.active_writer_card.is_locked if state.active_writer_card else False,
            "current_scene_index": cur_idx,
            "scene_registry": {str(k): [s.dict() for s in v] for k, v in state.scene_registry.items()},
            "current_scene": current_scene,
            "writer_recommendations": [w.dict() for w in state.writer_recommendations],
            "wallet": state.wallet.dict(),
            "momentum": state.momentum_level,
            "sync": state.sync_intensity
        }

    def generate_gemma_story_block(self, state: WorldState, cards: List[Dict], prev_context: str) -> SceneBlock:
        """
        로컬 Gemma 엔진을 사용하여 서사 블록을 생성합니다.
        """
        if not self.gemma:
            # Fallback to WeaverEngine if gemma is not initialized
            return WeaverEngine.weave_block_v2(state, Scene(scene_id=state.current_scene_index), cards, prev_context=prev_context)

        card_names = ", ".join([c.get('name', 'Unknown') for c in cards])
        writer_name = state.active_writer_card.name if state.active_writer_card else "신비로운 작가"
        
        prompt = f"""
당신은 서사 보조 엔진 Gemma입니다. 다음 조건에 맞는 이야기 블록을 하나 생성하세요.

[조건]
1. 현재 활성화된 카드(상징): {card_names}
2. 이전 맥락: {prev_context}
3. 집필 스타일: {writer_name} 스타일 (생생하고 몰입감 넘치는 묘사)

[출력 형식]
- 서술형 텍스트만 출력하세요. 다른 설명은 생략합니다.
- 한국어로 작성하세요.
"""
        content = self.gemma.simple_prompt(prompt)
        
        import uuid
        return SceneBlock(
            block_id=str(uuid.uuid4())[:8],
            content=content.strip(),
            cards_used=cards,
            metadata={"engine": "gemma", "cards": card_names}
        )

    def run_action(self, project_id: str, action_type: str, params: Optional[Dict[str, Any]] = None) -> CommonResponse:
        """
        Executes a narrative action. 
        Note: params defaults to None and is initialized internally to avoid mutable default issues.
        """
        if params is None:
            params = {}
            
        lock = self.pm.get_project_lock(project_id)
        with lock:
            state = self.storage.load_project(project_id)
            if not state:
                return CommonResponse(success=False, message="상태 로드 실패.")
            
            payload, message = {}, "수행 완료."
            
            try:
                # --- [1] Card Logic (Safety Buffed) ---
                if action_type == "DRAW_TAROT":
                    # Defense: Handle None from engine and fallback to spread tail
                    card = TarotEngine.draw_to_spread(state)
                    if card is None and state.tarot_spread:
                        card = state.tarot_spread[-1]
                    
                    if card is None:
                        return CommonResponse(success=False, message="카드를 뽑을 수 있는 상태가 아닙니다.", project_id=project_id)
                    
                    payload["card"] = card
                    card_name = card.get('name', '알 수 없는 상징')
                    message = f"상징 '{card_name}'(이)가 보드에 배치되었습니다."
                
                elif action_type == "DISCARD_CARD":
                    cid = params.get("card_id")
                    TarotEngine.burn_card(state, cid)
                    state.tarot_spread = [c for c in state.tarot_spread if c["cid"] != cid]
                    message = "카드를 테이블에서 제거했습니다."
                
                elif action_type == "PICK":
                    cid = params.get("card_id")
                    card = next((c for c in state.tarot_spread if c["cid"] == cid), None)
                    if not card:
                        return CommonResponse(success=False, message="배치할 카드를 찾을 수 없습니다.", project_id=project_id)
                        
                    # [V2.2] Character Image Initialization
                    image_url = params.get("image_url", state.memory_db["characters"].get(cid, {}).get("image_url"))
                    
                    state.memory_db["characters"][cid] = {
                        "cid": cid, "name": card["name"], 
                        "role": params.get("role", "ACTOR"), "description": card.get("summary", ""),
                        "image_url": image_url
                    }
                    state.tarot_spread = [c for c in state.tarot_spread if c["cid"] != cid]
                    message = f"배우 '{card['name']}'(이)가 현장에 투입되었습니다. 곧 이미지가 생성됩니다."
                
                # --- [2] Narrative Logic (Gemma Connected) ---
                elif action_type == "WEAVE_BLOCK":
                    cur_idx = state.current_scene_index
                    scene = Scene(**params["current_scene"]) if params.get("current_scene") else Scene(scene_id=cur_idx)
                    prev_context = scene.blocks[-1].content if scene.blocks else ""
                    
                    # Gemma 엔진을 우선 사용하도록 변경
                    if self.gemma:
                        block = self.generate_gemma_story_block(state, params["cards"], prev_context)
                    else:
                        block = WeaverEngine.weave_block_v2(state, scene, params["cards"], prev_context=prev_context, bridge_card=params.get("bridge_card"))
                    
                    # [V2.2] Cinematic Metadata Injection
                    moods = ["dark", "warm", "tense", "divine", "melancholy"]
                    bgms = ["track_ambient_01", "track_tension_04", "track_divine_02"]
                    block.metadata.update({
                        "mood": random.choice(moods),
                        "bgm_id": random.choice(bgms),
                        "image_url": f"/media/scene_{cur_idx}_{block.block_id}.webp"
                    })
                    
                    scene.blocks.append(block)
                    if cur_idx not in state.scene_registry: state.scene_registry[cur_idx] = []
                    scene.version = f"v{len(state.scene_registry[cur_idx]) + 1}"
                    state.scene_registry[cur_idx].append(scene)
                    message = f"서사 블록이 '{'Gemma' if self.gemma else 'WeaverV2'}' 엔진에 의해 직조되었습니다 (Mood: {block.metadata['mood']})."
                
                elif action_type == "UPDATE_BLOCK_ORDER":
                    idx = int(params["scene_id"])
                    if idx not in state.scene_registry: return CommonResponse(success=False, message="장면 데이터 없음.")
                    base = state.scene_registry[idx][-1]; blocks = {b.block_id: b for b in base.blocks}
                    if not set(params.get("block_ids", [])).issubset(set(blocks.keys())):
                        return CommonResponse(success=False, message="ID 불일치가 감지되었습니다.")
                    new_scene = base.copy(deep=True)
                    new_scene.blocks = [blocks[bid] for bid in params["block_ids"] if bid in blocks]
                    new_scene.version = f"v{len(state.scene_registry[idx]) + 1}"
                    state.scene_registry[idx].append(new_scene)
                    message = f"장면 순서가 {new_scene.version} 버전으로 업데이트되었습니다."

                elif action_type == "GENERATE_IMAGE":
                    target_id = params.get("target_id")
                    target_type = params.get("target_type", "character") # "character" or "scene"
                    
                    if target_type == "character":
                        if target_id in state.memory_db["characters"]:
                            # In real world, call actual generate API here
                            new_url = f"/media/portrait_{target_id}_{random.randint(100,999)}.webp"
                            state.memory_db["characters"][target_id]["image_url"] = new_url
                            payload["image_url"] = new_url
                            message = "캐릭터 이미지가 성공적으로 재생성되었습니다."
                    else:
                        message = "이미지 생성 대상을 찾을 수 없거나 지원되지 않습니다."

                # --- [3] AI Writer System (Safety Recommended) ---
                elif action_type == "GET_WRITER_RECOMMENDATIONS":
                    recs = WriterFactory.get_random_pool(3); state.writer_recommendations = recs
                    payload["recommendations"] = [w.dict() for w in recs]

                elif action_type == "SELECT_WRITER_CARD":
                    writer_id = params.get("writer_id")
                    writer = WriterFactory.get_by_id(writer_id)
                    if not writer: return CommonResponse(success=False, message="초빙하려는 작가 정보를 찾을 수 없습니다.", project_id=project_id)
                    state.active_writer_card = writer
                    message = f"작가 '{writer.name}'(이)가 메인 집필진으로 선정되었습니다."
                    payload["active_writer"] = writer.dict()

                elif action_type == "SWITCH_WRITER_CARD":
                    if state.active_writer_card and state.active_writer_card.is_locked:
                        return CommonResponse(success=False, message="작가가 잠금 상태이므로 교체할 수 없습니다.")
                    new_w = WriterFactory.get_by_id(params.get("writer_id"))
                    if not new_w: return CommonResponse(success=False, message="대상 작가 정보를 찾을 수 없습니다.", project_id=project_id)
                    
                    cur_idx = state.current_scene_index; bridge_dict = None
                    if cur_idx in state.scene_registry and state.scene_registry[cur_idx]:
                        scene = state.scene_registry[cur_idx][-1].copy(deep=True)
                        bridge = WeaverEngine.generate_bridge_block(state, scene, new_w)
                        scene.blocks.append(bridge); scene.version = f"v{len(state.scene_registry[cur_idx]) + 1}"
                        state.scene_registry[cur_idx].append(scene); bridge_dict = bridge.dict()
                        message = f"작가진이 '{new_w.name}'(으)로 교체되었으며, 브릿지 블록이 생성되었습니다."
                    else: message = f"작가진이 '{new_w.name}'(으)로 교체되었습니다."
                    
                    state.active_writer_card = new_w
                    payload["active_writer"] = new_w.dict(); payload["bridge_block"] = bridge_dict

                elif action_type == "LOCK_WRITER_CARD":
                    if state.active_writer_card:
                        state.active_writer_card.is_locked = True
                        message = f"작가 '{state.active_writer_card.name}' 고정됨."; payload["is_locked"] = True

                elif action_type == "UNLOCK_WRITER_CARD":
                    if state.active_writer_card:
                        state.active_writer_card.is_locked = False
                        message = f"작가 '{state.active_writer_card.name}' 해제됨."; payload["is_locked"] = False

                self.storage.save_project(project_id, state)
                return CommonResponse(success=True, message=message, world_state_summary=self._get_state_summary(state), payload=payload)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return CommonResponse(success=False, message=f"오케스트레이터 에러: {str(e)}")
