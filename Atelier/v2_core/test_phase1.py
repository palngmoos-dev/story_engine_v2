import sys
import io

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

from v2_core import core_engine as core
from v2_core import scene_engine as scene

def run_phase1_test():
    print("🧪 [Phase 1: Stability (Impact & Memory) Verification]")
    core.reset_core()
    
    # 1. First Turn: Initialization and state check
    print("\n[Turn 1] Initializing story engine...")
    result1 = scene.play_turn(place="카페", lead="형사", user_input="의문의 편지를 읽는다.", duration=5, test_mode=True)
    
    assert result1['state_tag'] is not None, "State tag must be present."
    assert result1['event_summary'] != "중요 사건이 식별되지 않음", "Event summary should be generated."
    print(f"✅ Turn 1 OK: Tag={result1['state_tag']}, Memory='{result1['event_summary']}'")
    
    # 2. Second Turn: Suspicion tracking
    print("\n[Turn 2] Verifying suspicion and impact tracking...")
    result2 = scene.play_turn(user_input="편지를 태운다.", duration=10, test_mode=True)
    
    assert core._TIMING_STATE["suspicion"] > 0, "Suspicion should increase after detective's action."
    assert core._LAST_SCENE_IMPACT > 0, "Current scene impact should be calculated."
    print(f"✅ Turn 2 OK: Suspicion={core._TIMING_STATE['suspicion']}, Scene Impact={core._LAST_SCENE_IMPACT}")
    
    # 3. Third Turn: Accumulation check
    print("\n[Turn 3] Verifying impact score accumulation...")
    old_cumulative = core._CUMULATIVE_IMPACT
    scene.play_turn(user_input="누군가 밖에서 지켜보고 있다.", duration=5, test_mode=True)
    
    assert core._CUMULATIVE_IMPACT > old_cumulative, "Cumulative impact must always increase."
    assert core.get_memory_prompt() != "", "Memory prompt should not be empty."
    print(f"✅ Turn 3 OK: Total Impact={core._CUMULATIVE_IMPACT}")

    # 4. Sync Verification
    print("\n[Turn 4] Verifying Sync logic (Data Integrity)...")
    mock_scenes = [
        {"scene_number": 1, "text": "...", "metadata": {"impact": 5, "event_summary": "Sync Test Event 1"}},
        {"scene_number": 2, "text": "...", "metadata": {"impact": 3, "event_summary": "Sync Test Event 2"}}
    ]
    core.sync_from_history(mock_scenes)
    
    assert core._CUMULATIVE_IMPACT == 8, f"Restored impact mismatch: {core._CUMULATIVE_IMPACT} != 8"
    assert len(core._NARRATIVE_MEMORY) == 2, "Restored memory count mismatch."
    print(f"✅ Sync Test OK: Restored Memory Count={len(core._NARRATIVE_MEMORY)}")

    print("\n✨ [테스트 시나리오 실행 완료]")

if __name__ == "__main__":
    run_phase1_test()
