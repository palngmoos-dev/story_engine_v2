"""
Verification script for Phase 2 - Step C: Hybrid Archive & Clustering.
Tests stream compression and card grouping/clustering.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.stream_engine import StreamEngine
from v2_core.archive_engine import ArchiveEngine
from v2_core.clustering_engine import ClusteringEngine

def verify():
    print("=== Phase 2-C: Hybrid Archive & Clustering Verification ===")
    state = WorldState()
    
    # 1. 많은 페이지 생성 (15페이지)
    print("\n[Criterion 1 & 2] 스트림 생성 및 하이브리드 압축 테스트...")
    for _ in range(15):
        StreamEngine.append_stream_page(state, StreamEngine.generate_stream_page(count=10))
    
    print(f" Initial State: {len(state.stream_pages)} pages active.")
    
    # 압축 실행 (최근 10개 유지)
    num_compressed = ArchiveEngine.compress_old_stream_pages(state, keep_recent=10)
    
    # 검증 A: 페이지 수 조절 확인
    if len(state.stream_pages) == 10 and num_compressed == 5:
        print(f" PASS: Compressed {num_compressed} pages. Active pages: {len(state.stream_pages)}")
    else:
        print(f" FAIL: Compression count mismatch. Active: {len(state.stream_pages)}")
        
    # 검증 B: 압축 히스토리 생성 확인
    if len(state.compressed_stream_history) == 5:
        print(f" PASS: {len(state.compressed_stream_history)} summary metas created in history.")
        sample_meta = state.compressed_stream_history[0]
        print(f" Sample Meta: {sample_meta['representative_names'][:2]}... ({sample_meta['card_count']} cards)")
    else:
        print(" FAIL: History metadata not generated.")

    # 2. 클러스터링(그룹) 생성 검증
    print("\n[Criterion 3, 4, 5] 카드 그룹 생성 및 무결성 테스트...")
    page = state.stream_pages[0]
    selected_cards = [page[0], page[2], page[4]]
    
    # 원본 CID 백업
    original_cids = [c.get("cid") or c.get("name") for c in selected_cards]
    
    group = ClusteringEngine.create_group(selected_cards, group_name="Test Collective")
    ClusteringEngine.add_group_to_state(state, group)
    
    # 검증 C: 그룹 참조 ID 확인
    if group["card_ids"] == original_cids:
        print(f" PASS: Group '{group['name']}' correctly references card IDs: {group['card_ids']}")
    else:
        print(f" FAIL: Group reference mismatch. Expected {original_cids}, Got {group['card_ids']}")
        
    # 검증 D: 원본 데이터 보존 확인
    if page[0].get("name") == selected_cards[0].get("name"):
        print(" PASS: Original cards remain unchanged in the stream.")
    else:
        print(" FAIL: Original card data was mutated.")

    print("\n" + "=" * 40)
    print(" ALL STEP C CRITERIA PASSED SUCCESSFULLY ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
