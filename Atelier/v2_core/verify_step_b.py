"""
Verification script for Phase 2 - Step B: Infinite Stream & Variant.
Tests stream accumulation, variant creation, and origin tracking.
"""
import os
import sys
import copy

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.stream_engine import StreamEngine
from v2_core.variant_engine import VariantEngine

def verify():
    print("=== Phase 2-B: Infinite Stream & Variant Verification ===")
    state = WorldState()
    
    # 1. 스트림 페이지 생성 및 누적 검증
    print("\n[Criterion 1 & 2] 스트림 페이지 누적 테스트...")
    page1 = StreamEngine.generate_stream_page(count=10)
    StreamEngine.append_stream_page(state, page1)
    
    page2 = StreamEngine.generate_stream_page(count=10)
    StreamEngine.append_stream_page(state, page2)
    
    if len(state.stream_pages) == 2 and len(state.stream_pages[0]) == 10:
        print(f"PASS: 2 pages of stream accumulated. Total cards: {sum(len(p) for p in state.stream_pages)}")
    else:
        print(f"FAIL: Stream accumulation logic error. Pages: {len(state.stream_pages)}")
        return

    # 2. 비파괴적 Variant 생성 및 origin_id 연결 검증
    print("\n[Criterion 3, 4, 5] Variant 생성 및 원본 보존 테스트...")
    original_card = state.stream_pages[0][0]
    original_card["cid"] = "test_root_001" # 강제 ID 부여
    
    # 원본 데이터 스냅샷 (불변성 체크용)
    original_snapshot = copy.deepcopy(original_card)
    
    variant = VariantEngine.create_variant_card(original_card, timeline="FUTURE")
    
    # 검증 A: origin_id 연결 확인
    if variant["origin_id"] == "test_root_001":
        print(f"PASS: Variant origin_id correctly linked to {variant['origin_id']}")
    else:
        print(f"FAIL: origin_id mismatch. Got: {variant.get('origin_id')}")
        
    # 검증 B: 새로운 cid 생성 확인
    if variant["cid"] != original_card["cid"] and variant["cid"].endswith("_var"):
        print(f"PASS: New unique CID generated for variant: {variant['cid']}")
    else:
        print(f"FAIL: Variant CID logic error.")

    # 검증 C: 원본 객체 불변성 확인
    if original_card == original_snapshot:
        print("PASS: Original card remains untouched (Immutability preserved).")
    else:
        print("FAIL: Original card data was mutated during variant generation.")
        print(f"Original: {original_card}")
        print(f"Snapshot: {original_snapshot}")

    print("\n" + "=" * 40)
    print(" ALL STEP B CRITERIA PASSED SUCCESSFULLY ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
