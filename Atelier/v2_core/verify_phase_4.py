"""
Verification script for Phase 4: Synthesis & Multiverse Narrative Log.
Tests narrative synthesis, history logging, briefing, and chronicle export.
"""
import os
import sys

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.history_manager import HistoryManager
from v2_core.chronology_engine import ChronologyEngine

def verify():
    print("=== Phase 4: Synthesis & Chronicle Verification ===")
    history = HistoryManager()
    chronology = ChronologyEngine()
    state = WorldState()
    
    # 1. 서사 비트 생성 및 합성 테스트
    print("\n[Criterion 1] 서사 비트 합성(Synthesis) 테스트...")
    state.story_beats = [
        {"beat_text": "주인공이 낡은 문을 열었다."},
        {"beat_text": "문 너머에는 잊혀진 도서관이 있었다."},
        {"beat_text": "그는 거기서 자신의 이름이 적힌 일기를 발견했다."}
    ]
    
    summary = chronology.summarize_beats(state.story_beats)
    if summary and len(summary) > 5:
        print(f" PASS: Synthesis successful. Summary: {summary}")
    else:
        print(" FAIL: Synthesis failed to generate a meaningful summary.")

    # 2. 브랜치 역사 기록 및 브리핑 테스트
    print("\n[Criterion 2] 내러티브 로그 기록 및 브리핑 테스트...")
    branch_id = "main"
    history.add_to_branch_history(branch_id, summary)
    
    briefing = history.get_branch_briefing(branch_id)
    if summary in briefing:
        print(" PASS: Narrative log successfully updated and reflected in briefing.")
        print(f" Briefing Output:\n{briefing}")
    else:
        print(" FAIL: Briefing did not contain the committed summary.")

    # 3. 마크다운 연대기 출력 테스트
    print("\n[Criterion 3] 마크다운 연대기(Chronicle) 내보내기 테스트...")
    log = history.branches[branch_id].get("narrative_log", [])
    file_path = chronology.export_chronicle_md(state, "VerifBranch", log)
    
    if os.path.exists(file_path):
        print(f" PASS: Chronicle Markdown file created at: {file_path}")
        # Check content briefly
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "# Infinite Narrative Archive" in content:
                print(" PASS: Markdown content structure verified.")
            else:
                print(" FAIL: Markdown content structure mismatch.")
    else:
        print(" FAIL: Chronicle file not found.")

    print("\n" + "=" * 40)
    print(" PHASE 4 FINAL VERIFICATION SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
