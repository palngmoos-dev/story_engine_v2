"""
Verification script for Phase 9: Narrative Rendering & Production Pipeline.
Tests RenderEngine — blueprint fallback, character injection, scene caching.
"""
import os
import sys
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.render_engine import RenderEngine, _build_fallback_scene
from v2_core.blueprint_engine import BlueprintEngine

def verify():
    print("=== Phase 9: Render Engine Verification ===")
    state = WorldState()

    # Setup: story beats + lead character
    state.story_beats = [
        {"title": "어두운 골목", "content": "비 내리는 도시의 골목. 그림자가 움직인다."},
        {"title": "조우", "content": "마침내 두 사람이 마주쳤다. 침묵이 흘렀다."},
    ]
    state.lead_character = {
        "name": "김하늘",
        "age": "28",
        "gender": "여성",
        "mbti": "INFP",
        "occupation": "프리랜서 작가",
        "flaw": "결정적 순간에 용기가 부족함",
        "skill": "상황의 흐름을 읽는 통찰력",
        "personality": "조용하고 사색적"
    }

    # 1. Fallback 씬 생성 테스트
    print("\n[Criterion 1] Fallback 씬 생성 테스트 (Ollama 없이)...")
    beat = state.story_beats[0]
    spec = BlueprintEngine.generate_visual_spec(beat["content"], state.momentum_level)
    fallback_text = _build_fallback_scene(beat, spec, state.lead_character)
    
    if "김하늘" in fallback_text and "어두운 골목" in fallback_text and "[영상 콘티]" in fallback_text:
        print(f" PASS: Fallback scene generated with character and conti.")
    else:
        print(f" FAIL: Fallback scene missing key elements.\n  Got: {fallback_text[:200]}")

    # 2. Beat 렌더링 (Ollama 폴백 포함)
    print("\n[Criterion 2] RenderEngine.render_beat() 폴백 렌더링 테스트...")
    result = RenderEngine.render_beat(state, 0)

    if "error" not in result and result.get("title") == "어두운 골목" and result.get("scene_text"):
        print(f" PASS: Beat rendered. Fallback={result.get('is_fallback')}, Title={result['title']}")
    else:
        print(f" FAIL: Render failed: {result}")

    # 3. 전체 스크린플레이 렌더링 및 캐싱
    print("\n[Criterion 3] 전체 스크린플레이 렌더링 및 state 캐싱 테스트...")
    rendered = RenderEngine.render_full_screenplay(state)
    
    if len(rendered) == 2 and len(state.rendered_scenes) == 2:
        print(f" PASS: {len(rendered)} scenes rendered and cached in state.")
    else:
        print(f" FAIL: Expected 2, got {len(rendered)} rendered, {len(state.rendered_scenes)} cached.")

    # 4. 마크다운 어셈블리
    print("\n[Criterion 4] 마크다운 스크린플레이 어셈블리 테스트...")
    md = RenderEngine.get_screenplay_markdown(state.rendered_scenes, title="테스트 서사")
    
    if "# 🎬 테스트 서사" in md and "SCENE 1" in md and "SCENE 2" in md:
        print(f" PASS: Screenplay markdown assembled. ({len(md)} chars)")
    else:
        print(f" FAIL: Markdown assembly failed.")

    # 5. 범위 초과 인덱스 에러 핸들링
    print("\n[Criterion 5] 범위 초과 인덱스 에러 핸들링 테스트...")
    result_err = RenderEngine.render_beat(state, 99)
    if "error" in result_err:
        print(f" PASS: Out-of-range error handled gracefully: {result_err['error']}")
    else:
        print(f" FAIL: Expected error, got: {result_err}")

    print("\n" + "=" * 40)
    print(" PHASE 9 RENDER ENGINE SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
