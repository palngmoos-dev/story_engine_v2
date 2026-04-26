"""
Community API Endpoints for Phase 13.
Handles publishing, voting, commenting, and ranking.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from .schemas import CommonResponse
from .project_manager import ProjectManager
from ..review_engine import ReviewEngine

router = APIRouter()
_pm: Optional[ProjectManager] = None

def init_community(pm_instance: ProjectManager):
    global _pm
    _pm = pm_instance

@router.post("/project/{project_id}/publish")
async def publish_project(project_id: str):
    """Publishes a project to the community with AI Review."""
    if not _pm: raise HTTPException(status_code=500, detail="Community not initialized")
    lock = _pm.get_project_lock(project_id)
    with lock:
        state = pm.storage.load_project(project_id)
        if not state:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # 1. AI Review
        review = ReviewEngine.evaluate_project(state)
        
        # 2. Update Registry
        _pm.update_project_meta(project_id, {
            "is_public": True,
            "ai_score": review["ai_score"],
            "published_at": datetime.now().isoformat()
        })
        
        return CommonResponse(
            success=True,
            message="서사가 커뮤니티에 공개되었습니다!",
            project_id=project_id,
            payload={"review": review}
        )

@router.get("/community/list")
async def list_community_projects(sort_by: str = "rank"):
    """Lists all public projects with ranking/sorting."""
    if not _pm: raise HTTPException(status_code=500, detail="Community not initialized")
    projects = _pm.list_projects()
    public_list = []
    for pid, meta in projects.items():
        if meta.get("is_public"):
            p_data = meta.copy()
            p_data["project_id"] = pid
            p_data["votes"] = meta.get("vote_count", 0)
            public_list.append(p_data)

    # Sort logic with 30/70 Weighting (Phase 13 Mastery)
    for p in public_list:
        ai_part = p.get("ai_score", 0) * 0.3
        vote_part = min(100, p.get("votes", 0) * 10) * 0.7
        p["merit_score"] = round(ai_part + vote_part, 1)
        p["author"] = "Solaris365" # Fixed Pseudonym
    
    if sort_by == "rank":
        public_list.sort(key=lambda x: x["merit_score"], reverse=True)
    
    return {"success": True, "projects": public_list}

@router.post("/project/{project_id}/comment")
async def add_comment(project_id: str, content: str):
    """Adds a comment which will be processed into a Narrative Report."""
    if not _pm: raise HTTPException(status_code=500, detail="Community not initialized")
    # For MVP: Store comment, then AI will summarize it in the project meta
    # Real implementation would use a database; here we update project_meta
    meta = _pm.list_projects().get(project_id, {})
    comments = meta.get("raw_comments", [])
    comments.append({"content": content, "at": datetime.now().isoformat()})
    
    # Simple Narrative Summary (Internal Trigger)
    positives = sum(1 for c in comments if any(word in c["content"] for word in ["좋아", "멋져", "대박", "good", "wow"]))
    summary = f"관객들의 반응: {len(comments)}개의 목소리가 얽혀 있습니다. (약 {int(positives/len(comments)*100)}%의 전율)"
    
    _pm.update_project_meta(project_id, {
        "raw_comments": comments,
        "comment_count": len(comments),
        "narrative_feedback": summary
    })
    return {"success": True, "narrative_report": summary}

@router.post("/project/{project_id}/vote")
async def vote_project(project_id: str):
    """Votes for a public project."""
    if not _pm: raise HTTPException(status_code=500, detail="Community not initialized")
    projects = _pm.list_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    meta = projects[project_id]
    new_votes = meta.get("vote_count", 0) + 1
    _pm.update_project_meta(project_id, {"vote_count": new_votes})
    
    return {"success": True, "new_vote_count": new_votes}

@router.get("/community/hall-of-fame")
async def get_hall_of_fame():
    """Returns Top 5 projects."""
    if not _pm: raise HTTPException(status_code=500, detail="Community not initialized")
    top_5 = _pm.get_top_creators(limit=5)
    return {"success": True, "top_5": top_5}
