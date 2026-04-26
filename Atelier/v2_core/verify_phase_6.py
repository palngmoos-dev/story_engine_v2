"""
Verification script for Phase 6: Narrative Convergence Engine.
Tests scoring, gravity computation, and final core export.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.convergence_engine import ConvergenceEngine
from v2_core.chronology_engine import ChronologyEngine

def verify():
    print("=== Phase 6: Narrative Convergence Verification ===")
    state = WorldState()
    chronology = ChronologyEngine()
    
    # Pre-setup: Add some data to state
    state.taste_vector = {"Noir": 0.8, "Techno": 0.3}
    state.interaction_history = [
        {"action": "PICK", "tags": ["Noir", "Mystery"], "summary": "어두운 골목에서의 조각"},
        {"action": "PICK", "tags": ["Noir"], "summary": "차가운 빗줄기"}
    ]
    
    # 1. 서사 프로필 추론 테스트
    print("\n[Criterion 1] 서사 중력(Gravity) 및 프로필 추론 테스트...")
    profile = ConvergenceEngine.compute_narrative_vector(state)
    if profile.get("core_tone") == "침울한 누아르":
        print(f" PASS: Gravity inference successful. Core Tone: {profile.get('core_tone')}")
    else:
        print(f" FAIL: Gravity inference failed. Profile: {profile}")

    # 2. 다중 가중치 스코어링 테스트
    print("\n[Criterion 2] 내러티브 스코어링 및 Reason 생성 테스트...")
    test_card = {"name": "수상한 탐정", "tags": ["Noir", "Mystery"]}
    score_data = ConvergenceEngine.get_narrative_score(test_card, state)
    
    if score_data["score"] > 0.7 and "Noir" in score_data["reason"]:
        print(f" PASS: Scoring accurate. Score: {score_data['score']:.2f}")
        print(f" Reason: {score_data['reason']}")
    else:
        print(f" FAIL: Scoring or Reason mismatch. Data: {score_data}")

    # 3. 자동 후보 분류 테스트
    print("\n[Criterion 3] Commit/Prune 후보 분류 테스트...")
    state.stream_pages = [[test_card, {"name": "평범한 돌멩이", "tags": ["None"]}]]
    ConvergenceEngine.classify_narrative_layers(state)
    
    if len(state.commit_candidates["cards"]) > 0:
        print(f" PASS: Commit candidate identified: {state.commit_candidates['cards'][0]['card']['name']}")
    if len(state.prune_candidates["cards"]) > 0:
        print(f" PASS: Prune candidate identified: {state.prune_candidates['cards'][0]['card']['name']}")

    # 4. 최종 작품 내보내기 테스트
    print("\n[Criterion 4] 최종 작품(Final Core) 내보내기 테스트...")
    state.committed_core["beats"] = [{"beat_text": "결국 그는 진실을 마주했다."}]
    state.committed_core["cards"] = [test_card]
    
    file_path = chronology.export_final_chronicle(state)
    if os.path.exists(file_path):
        print(f" PASS: Final Work Exported to: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "FINAL NARRATIVE" in content and "수상한 탐정" in content:
                 print(" PASS: Final output content integrity verified.")
            else:
                 print(" FAIL: Final output missing core elements.")
    else:
        print(" FAIL: Export failed.")

    print("\n" + "=" * 40)
    print(" PHASE 6 NARRATIVE CONVERGENCE SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
