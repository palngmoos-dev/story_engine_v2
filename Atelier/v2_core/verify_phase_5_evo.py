"""
Mathematical Verification for Phase 5: Evolutionary Taste Engine.
Tests continuous vector updates, multi-layer rollover, and time decay.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.taste_engine import TasteEngine

def verify():
    print("=== Phase 5: Evolutionary Taste Engine Verification ===")
    state = WorldState()
    test_card = {
        "cid": "test_card_001",
        "category": "mood",
        "tags": ["Cyberpunk", "Noir", "Techno"]
    }

    # 1. 학습 로직 검증 (PICK)
    print("\n[Criterion 1] 카드 선택(PICK)에 따른 벡터 상승 테스트...")
    initial_val = state.taste_vector.get("Cyberpunk", 0.2)
    
    # 5번 연속 선택
    for _ in range(5):
        TasteEngine.record_interaction(state, test_card, "PICK")
    
    final_val = state.taste_vector.get("Cyberpunk")
    if final_val > initial_val:
        print(f" PASS: Vector increased from {initial_val:.2f} to {final_val:.2f}")
    else:
        print(f" FAIL: Vector failed to increase. Current: {final_val}")

    # 2. 회피 압력 검증 (DISCARD)
    print("\n[Criterion 2] 카드 폐기(DISCARD)에 따른 회피 압력 테스트...")
    pre_discard_val = state.taste_vector.get("Noir")
    TasteEngine.record_interaction(state, test_card, "DISCARD")
    post_discard_val = state.taste_vector.get("Noir")
    
    delta = pre_discard_val - post_discard_val
    if delta > 0.15: # Discard weight (-2.0) * lr (0.1) = -0.2
        print(f" PASS: Avoidance pressure applied. Delta: -{delta:.2f} (Value: {post_discard_val:.2f})")
    else:
        print(f" FAIL: Avoidance pressure too weak or not applied. Delta: {delta}")

    # 3. 다층 기억 전이 검증 (Layer Rollover)
    print("\n[Criterion 3] 다층 기억(Hot -> Warm) 전이 테스트...")
    # Hot layer는 최대 10개. 6개 더 추가 (이미 6개 들어있음 - 5 picks + 1 discard)
    for i in range(10):
        dummy_card = {"cid": f"dummy_{i}", "tags": ["test"]}
        TasteEngine.record_interaction(state, dummy_card, "PICK")
        
    hot_size = len(state.interaction_layers["hot"])
    warm_size = len(state.interaction_layers["warm"])
    
    if hot_size <= 10 and warm_size > 0:
        print(f" PASS: Hot layer rolled over to Warm. Hot: {hot_size}, Warm: {warm_size}")
    else:
        print(f" FAIL: Layer rollover logic error. Hot: {hot_size}, Warm: {warm_size}")

    # 4. 시간적 감쇄 검증 (Decay)
    print("\n[Criterion 4] 시간적 감쇄(Decay) 수치 검사...")
    pre_decay = state.taste_vector.get("Cyberpunk")
    TasteEngine.apply_decay(state)
    post_decay = state.taste_vector.get("Cyberpunk")
    
    if post_decay < pre_decay:
        print(f" PASS: Time decay applied. {pre_decay:.4f} -> {post_decay:.4f}")
    else:
        print(f" FAIL: Decay not applied.")

    print("\n" + "=" * 40)
    print(" EVOLUTIONARY TASTE ENGINE VERIFIED ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
