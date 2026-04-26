"""
Verification script for Phase 2 - Step A: Multiverse Foundation.
Tests the 4 success criteria defined by the user.
"""
import os
import sys
import json

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.history_manager import HistoryManager

def verify():
    print("=== Phase 2-A: Multiverse Foundation Verification ===")
    history = HistoryManager()
    
    # 1. WorldState 저장 성공 여부 검증
    print("\n[Criterion 1] WorldState 저장 테스트...")
    state = WorldState()
    state.timeline_mode = "FUTURE"
    state.metadata["summary"] = "시간의 지평선 너머"
    
    sid = history.save_snapshot(state, summary="Criterion 1 Test")
    if os.path.exists(os.path.join(history.snapshots_path, f"{sid}.json")):
        print(f"PASS: Snapshot {sid} saved to disk.")
    else:
        print("FAIL: Snapshot file not found.")
        return

    # 2. WorldState 로드 성공 여부 검증
    print("\n[Criterion 2] WorldState 로드 테스트...")
    loaded_state = history.load_snapshot(sid)
    if loaded_state and loaded_state.timeline_mode == "FUTURE" and loaded_state.metadata["summary"] == "Criterion 1 Test":
        print(f"PASS: Data integrity maintained. Timeline: {loaded_state.timeline_mode}")
    else:
        print(f"FAIL: Data mismatch or load failed. Summary: {loaded_state.metadata['summary'] if loaded_state else 'None'}")
        return

    # 3. Snapshot 기반 branch 생성 성공 여부 검증
    print("\n[Criterion 3] Snapshot 기반 Branch 생성 테스트...")
    bid = history.create_branch(sid, branch_name="Horizon Branch")
    branches = history.list_branches()
    if bid in branches and branches[bid]["parent_snapshot_id"] == sid:
        print(f"PASS: Branch '{bid}' created from snapshot {sid}.")
    else:
        print("FAIL: Branch creation failed or metadata incorrect.")
        return

    # 4. Branch 전환 시 요약 표시 성공 여부 검증
    print("\n[Criterion 4] Branch 전환 및 요약 로드 테스트...")
    switched_state = history.switch_branch(bid)
    if switched_state and switched_state.metadata["summary"] == "Criterion 1 Test":
        print(f"PASS: Switch successful. Current Branch: {history.current_branch_id}")
        print(f"      Loaded Summary: {switched_state.metadata['summary']}")
    else:
        print("FAIL: Branch switch or summary restoration failed.")
        return

    print("\n" + "=" * 40)
    print(" ALL 4 CRITERIA PASSED SUCCESSFULLY ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
