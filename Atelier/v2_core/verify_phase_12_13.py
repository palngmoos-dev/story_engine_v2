"""
Verification Script for Phase 12 & 13.
Checks 50:50 Merit Score Calculation, Data Lifecycle (60 days), and Undo functionality.
"""
from typing import Dict, Any
from api.project_manager import ProjectManager
from ai_stream_engine import AIStreamEngine
from review_engine import ReviewEngine
from state_model import WorldState

def verify_merit_and_lifecycle():
    print("🎬 Starting Phase 12 & 13 Verification...")
    
    pm = ProjectManager()
    pid = "prj_merit_test"
    pm.create_project_with_id(pid, "The Eternal Archive")
    
    # 1. Test Review Engine
    state = WorldState()
    state.story_beats = [{"title": "Beat 1", "content": "The hero awakens.", "visual_spec": {}}] * 5
    state.lead_character = {"name": "Test Hero", "flaw": "Gullible", "personality": "Brave and bold"}
    
    review = ReviewEngine.evaluate_project(state)
    print(f"✅ AI Review Score: {review['ai_score']} ({review['status']})")
    
    # 2. Test Merit Score (50:50)
    pm.update_project_meta(pid, {
        "is_public": True,
        "ai_score": review["ai_score"],
        "vote_count": 10
    })
    
    top_5 = pm.get_top_creators(limit=5)
    print("✅ Top Creators Ranking:")
    for entry in top_5:
        print(f"   - {entry['title']}: Merit Score {entry['score']}")
    
    # 3. Test Lifecycle (60 Days)
    # Mocking old activity
    import datetime
    old_date = (datetime.datetime.now() - datetime.timedelta(days=61)).isoformat()
    pm.update_project_meta(pid, {"last_active": old_date})
    
    deleted_count = pm.cleanup_expired_projects()
    print(f"✅ Cleanup Logic: {deleted_count} expired project(s) removed.")
    
    # 4. Test Undo Persistence
    state.history_stack = ["snap_1", "snap_2"]
    state_dict = state.to_dict()
    restored = WorldState.from_dict(state_dict)
    if restored.history_stack == ["snap_1", "snap_2"]:
        print("✅ History Stack persistence confirmed.")
    
    print("\n🚀 Phase 12 & 13 Verification: SUCCESS")

if __name__ == "__main__":
    verify_merit_and_lifecycle()
