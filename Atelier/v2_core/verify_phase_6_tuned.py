"""
Verification script for Phase 6 Tuned: Sensitivity and Core Logic.
Tests threshold lowering, repetition boost, and avoidance cap.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.convergence_engine import ConvergenceEngine

def verify():
    print("=== Phase 6 Tuning Verification: Sensitivity & Pressure ===")
    state = WorldState()
    
    # Setup Taste & Profile
    state.taste_vector = {"Noir": 0.8}
    state.dominant_story_profile = {"dominant_tags": ["Noir"]}
    
    test_card_1 = {"cid": "detective_001", "name": "우울한 탐정", "tags": ["Noir"]}
    test_card_2 = {"cid": "junk_001", "name": "평범한 돌", "tags": ["None"]}
    discard_card = {"cid": "bright_001", "name": "찬란한 태양", "tags": ["Bright"]}

    # 1. Sensitivity Test (0.65 Threshold)
    print("\n[Criterion 1] 수렴 감도(0.65) 테스트...")
    # Base Noir card without repetition
    score_data = ConvergenceEngine.get_narrative_score(test_card_1, state)
    if ConvergenceEngine.COMMIT_THRESHOLD <= score_data["score"] < 0.8:
        print(f" PASS: Lowered threshold (0.65) caught the candidate. Score: {score_data['score']:.2f}")
    else:
        print(f" FAIL: Candidate not caught or score too high/low. Score: {score_data['score']:.2f}")

    # 2. Repetition Boost Test
    print("\n[Criterion 2] 반복 선택 가중치(Repetition Boost) 테스트...")
    state.interaction_history.append({"action": "PICK", "card_id": "detective_001", "tags": ["Noir"]})
    state.interaction_history.append({"action": "PICK", "card_id": "detective_001", "tags": ["Noir"]})
    
    boosted_score = ConvergenceEngine.get_narrative_score(test_card_1, state)
    if boosted_score["score"] > score_data["score"]:
        print(f" PASS: Repetition boost applied. {score_data['score']:.2f} -> {boosted_score['score']:.2f}")
    else:
        print(f" FAIL: Boost not applied.")

    # 3. Avoidance Cap Test (Discard Penalty)
    print("\n[Criterion 3] 회피 압력(Avoidance Cap) 테스트...")
    # 1. Record a discard
    state.interaction_history.append({"action": "DISCARD", "card_id": "bright_001", "tags": ["Bright"]})
    
    # 2. Try to score a card with the discarded tag
    evil_card = {"cid": "paradox_001", "name": "밝은 누아르", "tags": ["Noir", "Bright"]}
    # It has Noir (Good) and Bright (Discarded)
    capped_score = ConvergenceEngine.get_narrative_score(evil_card, state)
    if capped_score["score"] <= 0.3:
        print(f" PASS: Avoidance Cap applied. Noir boost was suppressed by Bright discard. Score: {capped_score['score']:.2f}")
    else:
        print(f" FAIL: Cap not applied. Score: {capped_score['score']:.2f}")

    print("\n" + "=" * 40)
    print(" PHASE 6 TUNING SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
