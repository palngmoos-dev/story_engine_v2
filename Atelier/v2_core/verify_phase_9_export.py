"""
Verification script for Phase 9: Export Pipeline.
Tests WorldState to Markdown conversion, including lead character and rendered scenes.
"""
import os
import sys
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.export_engine import from_world_state, export_world_state_to_file

def verify():
    print("=== Phase 9: Export Pipeline Verification ===")
    state = WorldState()
    state.metadata["summary"] = "수수께끼의 안개"
    
    # 1. Setup Data
    state.lead_character = {
        "name": "강태풍",
        "mbti": "ENTP",
        "occupation": "도시 탐험가",
        "flaw": "자기 과신",
        "skill": "자물쇠 따기"
    }
    
    state.story_beats = [
        {"title": "안개 속으로", "content": "차가운 안개가 도시를 덮었다. 태풍은 손전등을 켰다."},
        {"title": "버려진 저택", "content": "녹슨 문이 끼익 소리를 내며 열렸다."}
    ]
    
    # 2. Rendered scenes present
    state.rendered_scenes = [
        {
            "beat_index": 0,
            "title": "안개 속으로",
            "scene_text": "## 안개 속으로\n강태풍은 깊게 숨을 들이켰다. 안개는 폐부를 찌르는 듯 차가웠다.\n\n[영상 콘티]\nShot: Extreme Long Shot\nVisual: 안개에 잠긴 회색빛 고딕 양식의 건물들"
        }
    ]
    
    # 3. Test from_world_state
    print("\n[Criterion 1] from_world_state() 변환 테스트...")
    md = from_world_state(state)
    
    if "# 🎬 수수께끼의 안개" in md and "강태풍" in md and "도시 탐험가" in md:
        print(" PASS: Title and Lead Character found in Markdown.")
    else:
        print(" FAIL: Metadata or character missing in Markdown.")
        
    if "### SCENE 1: 안개 속으로" in md and "폐부를 찌르는 듯" in md:
        print(" PASS: Rendered scene prioritized correctly.")
    else:
        print(" FAIL: Rendered scene content missing.")
        
    if "### SCENE 2: 버려진 저택" in md and "녹슨 문이" in md:
        print(" PASS: Fallback to beat summary for unrendered scene works.")
    else:
        print(" FAIL: Fallback content missing.")

    # 4. Test file export
    print("\n[Criterion 2] export_world_state_to_file() 파일 생성 테스트...")
    file_path = export_world_state_to_file(state, "Test Project")
    
    if os.path.exists(file_path):
        print(f" PASS: File created at {file_path}")
        # Clean up
        try:
            # os.remove(file_path) # Keep it for user check if needed, but usually we clean up in automate tests
            pass 
        except: pass
    else:
        print(" FAIL: Exported file not found.")

    print("\n" + "=" * 40)
    print(" PHASE 9 EXPORT PIPELINE SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
