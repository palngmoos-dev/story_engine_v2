"""
Demonstration script for Infinite Narrative Canvas Phase 2.
Shows the flow: Snapshot -> Branch -> Switch with UI Transition -> Dashboard.
"""
import os
import sys
import time

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.canvas_engine import CanvasEngine

def run_demo():
    engine = CanvasEngine()
    
    # 1. Start in Main
    print("1. [Main] 초기 스냅샷 생성 중...")
    state_main = WorldState()
    state_main.total_scenes = 1
    state_main.story_beat_summary = "조용한 카페에서 시작된 의문의 대화."
    
    # Add dummy stream and archive
    state_main.stream_history = [[
        {"category": "character", "name": "수수께끼의 여인"},
        {"category": "prop", "name": "오래된 시계"}
    ]]
    
    sid = engine.history.create_snapshot(state_main, summary="메인 타임라인: 첫 만남")
    
    # 2. Create and Switch to New Branch
    target_branch_name = "미스테리 루트"
    print(f"2. [Branch] '{target_branch_name}' 생성 중...")
    bid = engine.history.create_branch(target_branch_name, sid)
    
    # 3. Simulate Transition
    print("3. [Switch] 세계선 도약 연출 실행...")
    # time.sleep(1) # Skip sleep for fast log
    engine.display_branch_jump(target_branch_name, "조용한 카페에서 수수께끼의 여인이 건넨 시계는 멈춰 있었다. 진실은 무엇일까?")
    
    # 4. Show Dashboard
    print("\n4. [Dashboard] 최신 상태 렌더링...")
    engine.history.current_branch_id = bid
    engine.run_dashboard()

if __name__ == "__main__":
    run_demo()
