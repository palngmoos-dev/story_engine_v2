"""
State Model for Infinite Narrative Canvas.
Encapsulates all narrative variables into a serializable WorldState.
Designed for Phase 18 (Multiverse Foundation & AI Writer).
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class UserWallet(BaseModel):
    essence_balance: float = 100.0
    tier: str = "DIRECTOR"
    is_infinite: bool = True

class SceneBlock(BaseModel):
    block_id: str  
    content: str = ""
    cards_used: List[Dict[str, Any]] = Field(default_factory=list)
    bridge_card: Optional[Dict[str, Any]] = None
    is_bridge_active: bool = False
    version: str = "v1"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WriterCard(BaseModel):
    writer_id: str
    name: str
    domain: str
    genre: str
    personality: str
    style_rules: List[str] = Field(default_factory=list)
    pacing: str = "balanced"
    is_locked: bool = False

class Scene(BaseModel):
    scene_id: int
    version: str = "v1"
    target_duration: str = "3M"
    style_card: Optional[Dict[str, Any]] = None
    blocks: List[SceneBlock] = Field(default_factory=list)
    is_complete: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class WorldState:
    def __init__(self):
        # 1. Deck & Spread
        self.tarot_spread = []
        
        # 2. Performance Metrics
        self.momentum_level = 1.0
        self.sync_intensity = 0.5

        # 3. Memory & Characters
        self.memory_db = {
            "characters": {},  # {cid: {name, role, description, cid}}
            "items": {}
        }
        
        # 4. Multiverse Registry
        self.scene_registry: Dict[int, List[Scene]] = {} # {idx: [v1, v2...]}
        self.current_scene_index: int = 1
        self.stagnation_score: float = 0.0
        self.active_canvas_cards: List[Any] = []
        self.story_beats: List[Any] = []
        self.rendered_scenes: List[Any] = []
        self.side_effect_count: int = 0
        self.stagnation_score: float = 0.0
        
        # 5. AI Writer System (Step 4)
        self.active_writer_card: Optional[WriterCard] = None
        self.writer_history: List[str] = []
        self.writer_recommendations: List[WriterCard] = []
        self.writer_switch_log: List[Dict[str, Any]] = []
        self._inject_default_writer()

        # 6. Performance & Context (Hardened)
        self.global_metrics = 0.5
        self.timeline_mode = "PRESENT"
        self.narrative_ailment = "NORMAL"
        self.stream_pages = []
        
        # 7. Evolutionary Taste Engine (Step 5)
        self.taste_vector: Dict[str, float] = {} 
        self.interaction_history: List[Dict[str, Any]] = []
        self.interaction_layers: Dict[str, List[Dict[str, Any]]] = {
            "hot": [], "warm": [], "cold": []
        }
        self.learning_rate: float = 0.05
        self.mutation_rate: float = 0.1

        # 7. Metadata & Wallet
        self.wallet = UserWallet()
        self.metadata = {
            "last_update": datetime.now().isoformat(),
            "summary": "새로운 서사가 시작되었습니다.",
            "stats": {
                "total_drawn": 0,
                "current_scene_draws": 0,
                "total_burned": 0,
                "current_scene_burns": 0
            }
        }

    def _inject_default_writer(self):
        if not self.active_writer_card:
            self.active_writer_card = WriterCard(
                writer_id="standard_director",
                name="상업 영화 작가",
                domain="영화/드라마",
                genre="보편적 드라마",
                personality="균형감 있는 흥행 지향형",
                style_rules=["기승전결의 명확함", "보편적 공감대"]
            )

    def to_dict(self) -> Dict[str, Any]:
        cur_idx = self.current_scene_index
        current_scene = self.scene_registry[cur_idx][-1] if cur_idx in self.scene_registry else None
        
        return {
            "active_cards": self.tarot_spread,
            "characters": list(self.memory_db["characters"].values()),
            "active_writer": self.active_writer_card.dict() if self.active_writer_card else None,
            "is_writer_locked": self.active_writer_card.is_locked if self.active_writer_card else False,
            "current_scene_index": cur_idx,
            "scene_registry": {str(k): [s.dict() for s in v] for k, v in self.scene_registry.items()},
            "current_scene": current_scene.dict() if current_scene else None,
            "writer_recommendations": [w.dict() for w in self.writer_recommendations],
            "writer_history": self.writer_history,
            "writer_switch_log": self.writer_switch_log,
            "wallet": self.wallet.dict(),
            "momentum": self.momentum_level,
            "sync": self.sync_intensity,
            "taste_vector": self.taste_vector,
            "learning_rate": self.learning_rate,
            "mutation_rate": self.mutation_rate,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        state = cls()
        state.tarot_spread = data.get("active_cards", [])
        
        chars = data.get("characters", [])
        for c in chars:
            cid = c.get("cid") or str(uuid.uuid4())
            state.memory_db["characters"][cid] = c
            
        state.current_scene_index = data.get("current_scene_index", 1)
        registry = data.get("scene_registry", {})
        for k, v in registry.items():
            state.scene_registry[int(k)] = [Scene(**s) for s in v]
        
        active = data.get("active_writer")
        if active:
            state.active_writer_card = WriterCard(**active)
            
        recs = data.get("writer_recommendations", [])
        state.writer_recommendations = [WriterCard(**w) for w in recs]
        
        state.writer_history = data.get("writer_history", [])
        state.writer_switch_log = data.get("writer_switch_log", [])
        
        if "wallet" in data:
            state.wallet = UserWallet(**data["wallet"])
            
        state.momentum_level = data.get("momentum", 1.0)
        state.sync_intensity = data.get("sync", 0.5)
        state.taste_vector = data.get("taste_vector", {})
        state.learning_rate = data.get("learning_rate", 0.05)
        state.mutation_rate = data.get("mutation_rate", 0.1)
        state.metadata = data.get("metadata", state.metadata)
        return state
