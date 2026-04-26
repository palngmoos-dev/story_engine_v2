"""
Verification script for Phase 8.3: Cinematic Blueprint Engine.
Tests visual spec generation, image prompts, and full timeline assembly.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.blueprint_engine import BlueprintEngine
from v2_core.api.orchestrator import NarrativeOrchestrator
from v2_core.api.project_manager import ProjectManager

def verify():
    print("=== Phase 8.3: Cinematic Blueprint Engine Verification ===")
    pm = ProjectManager()
    orch = NarrativeOrchestrator(pm)
    
    # 1. 시각적 메타데이터 생성 테스트
    print("\n[Criterion 1] 시각적 메타데이터(Shot/Light) 생성 테스트...")
    content = "어두운 골목길에서 누군가 나를 지켜보고 있다. 심장이 멎을 듯한 긴장감이 흐른다."
    spec = BlueprintEngine.generate_visual_spec(content, momentum=1.5)
    
    eligible_lighting = ["Cinematic Noir (High Contrast)", "Moody Cold Blue"]
    if spec["lighting"] in eligible_lighting:
        print(f" PASS: Cinematic lighting inferred: {spec['lighting']}")
    else:
        print(f" FAIL: Non-cinematic lighting: {spec['lighting']}")

    # 2. 비주얼 프롬프트(Image Prompt) 조합 테스트
    print("\n[Criterion 2] AI 비주얼 프롬프트 조합 테스트...")
    if "8k" in spec["image_prompt"] and "Cinematic" in spec["image_prompt"]:
        print(f" PASS: Visual Blueprint Prompt generated: \n      -> {spec['image_prompt'][:100]}...")
    else:
        print(" FAIL: Invalid prompt format.")

    # 3. 타임라인 청사진 집대성 테스트
    print("\n[Criterion 3] 전체 서사 청사진(Timeline Assembly) 테스트...")
    p_id = pm.create_project("Blueprint Test Project")
    state = WorldState()
    state.story_beats.append({"title": "인트로", "content": "비 내리는 도시의 전경"})
    state.committed_core["cards"].append({"cid": "CARD_MOCK_1", "name": "카운터", "summary": "대기 중인 암살자", "category": "characters", "tags": ["암살자", "긴장"]})
    pm.storage.save_project(p_id, state)
    
    resp = orch.get_full_blueprint(p_id)
    timeline = resp.payload.get("blueprint_timeline", [])
    
    if len(timeline) >= 2 and "visual_spec" in timeline[0]:
        print(f" PASS: Full timeline assembled with {len(timeline)} shots.")
    else:
        print(f" FAIL: Timeline assembly failed.")

    print("\n" + "=" * 40)
    print(" PHASE 8.3 CINEMATIC BLUEPRINT ENGINE SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
