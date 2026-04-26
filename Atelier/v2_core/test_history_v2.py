"""
Verification script for HistoryManager and Multiverse Branching.
Ensures snapshot saving, branch creation, and switching work correctly.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.history_manager import HistoryManager

def run_verification():
    print("=== Multiverse History Verification ===")
    
    # 1. Initialize
    history = HistoryManager(base_path="v2_core/saves")
    print(f"Current Branch: {history.current_branch_id} ({history.get_current_branch().name})")
    
    # 2. Create Initial State
    state_main = WorldState()
    state_main.total_scenes = 1
    state_main.story_beat_summary = "메인 타임라인의 시작"
    
    # 3. Create Snapshot in Main
    print("\nCreating snapshot in Main...")
    sid_main = history.create_snapshot(state_main, summary="Main Snapshot #1")
    print(f"Saved Snapshot ID: {sid_main}")
    
    # 4. Create New Branch 'Parallel' from Main's Snapshot
    print("\nCreating 'Parallel' branch from Main's snapshot...")
    bid_parallel = history.create_branch("Parallel World", sid_main)
    print(f"New Branch ID: {bid_parallel}")
    
    # 5. Switch to Parallel Branch
    print(f"\nSwitching to {bid_parallel}...")
    state_dict = history.switch_branch(bid_parallel)
    print(f"Switched. Current Branch: {history.current_branch_id}")
    
    # 6. Modify State in Parallel and Save
    state_parallel = WorldState.from_dict(state_dict["state"] if state_dict else state_main.to_dict())
    state_parallel.total_scenes = 10
    state_parallel.story_beat_summary = "평행 세계에서 발생한 대격변"
    
    print("\nCreating snapshot in Parallel...")
    sid_parallel = history.create_snapshot(state_parallel, summary="Parallel Snapshot #1")
    print(f"Saved Snapshot ID: {sid_parallel}")
    
    # 7. Verification Results
    print("\n--- Summary ---")
    print(f"Main Branch Snapshots: {history.branches['main'].snapshots}")
    print(f"Parallel Branch Snapshots: {history.branches[bid_parallel].snapshots}")
    
    # Reload and Check switch
    print("\nSwitching back to Main...")
    main_load = history.switch_branch("main")
    print(f"Main loaded summary: {main_load['summary'] if main_load else 'None'}")
    
    print("\nSwitching back to Parallel...")
    parallel_load = history.switch_branch(bid_parallel)
    print(f"Parallel loaded summary: {parallel_load['summary'] if parallel_load else 'None'}")
    
    print("\nVerification Complete.")

if __name__ == "__main__":
    run_verification()
