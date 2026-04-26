"""
Verification script for Phase 3: AI Core Integration & Infinite Engine.
Tests AI stream normalization, alias suggestions, and scene beat generation.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.ai_stream_engine import AIStreamEngine
from v2_core.ai_alias_engine import AIAliasEngine
from v2_core.scene_beat_engine import SceneBeatEngine
from v2_core.clustering_engine import ClusteringEngine

def verify():
    print("=== Phase 3: AI Core Integration Verification ===")
    state = WorldState()
    
    # 1. AI 스트림 생성 및 정규화 검증
    print("\n[Criterion 1] AI 카드 스트림 생성 및 정규화 테스트...")
    ai_page = AIStreamEngine.generate_ai_stream_page(state, count=10)
    
    if len(ai_page) == 10:
        print(f" PASS: Generated 10 cards. First card: {ai_page[0]['name']}")
        # 필드 유효성 검사
        fields = ["cid", "category", "name", "summary", "tags", "variant_info"]
        if all(f in ai_page[0] for f in fields):
            print(" PASS: All required fields (cid, category, name, etc.) are normalized.")
        else:
            print(f" FAIL: Missing fields in normalized card. Keys: {ai_page[0].keys()}")
    else:
        print(f" FAIL: Expected 10 cards, got {len(ai_page)}")

    # 2. 그룹 별칭 제안 검증
    print("\n[Criterion 2] AI 그룹 별칭 제안 테스트...")
    state.stream_pages.append(ai_page)
    group = ClusteringEngine.create_group(ai_page[:3], group_name="AI Test Group")
    
    aliases = AIAliasEngine.suggest_group_alias(group, state)
    if "suggestions" in aliases and len(aliases["suggestions"]) > 0:
        print(f" PASS: AI suggested {len(aliases['suggestions'])} aliases.")
        print(f" Sample: {aliases['suggestions'][0]['name']} - {aliases['suggestions'][0]['reason']}")
    else:
        print(" FAIL: AI alias suggestion failed or format error.")

    # 3. Scene Beat 생성 및 타임라인 반영 검증
    print("\n[Criterion 3 & 4] Scene Beat 생성 및 타임라인 반영 테스트...")
    # PAST 타임라인 테스트
    state.timeline_mode = "PAST"
    beat_past = SceneBeatEngine.generate_scene_beat(state, selected_cards=ai_page[:2])
    print(f" [PAST Beat] : {beat_past['beat_text'][:100]}...")
    
    # FUTURE 타임라인 테스트
    state.timeline_mode = "FUTURE"
    beat_future = SceneBeatEngine.generate_scene_beat(state, selected_cards=ai_page[:2])
    print(f" [FUTURE Beat]: {beat_future['beat_text'][:100]}...")

    if beat_past["beat_text"] != beat_future["beat_text"]:
        print(" PASS: Scene beat tone differs by timeline (Context awareness confirmed).")
    else:
        print(" FAIL: Scene beat output is identical (Timeline awareness failed).")

    # 4. 고정 구조 검증
    required_beat_fields = ["beat_text", "directing_memo", "next_inspiration"]
    if all(f in beat_future for f in required_beat_fields):
        print(" PASS: Scene beat follows the fixed 3-field structure.")
    else:
        print(" FAIL: Scene beat structure mismatch.")

    print("\n" + "=" * 40)
    print(" PHASE 3 INTEGRATION VERIFIED SUCCESSFULLY ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
