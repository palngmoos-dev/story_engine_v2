"""
API Request/Response Schemas for Phase 8.1.
Defines the consistent communication wrapper for all platforms.
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class CommonResponse(BaseModel):
    success: bool
    message: str
    project_id: Optional[str] = None
    world_state_summary: Optional[Dict[str, Any]] = None
    pulse_data: Optional[Dict[str, Any]] = None # Tension, Psychology, AI Note
    payload: Optional[Any] = None
    warnings: Optional[List[str]] = []

class ProjectCreateRequest(BaseModel):
    title: str = "새로운 서사 설계도"

class ProjectActionRequest(BaseModel):
    action_type: str # PICK, DISCARD, COMMIT, PRUNE, SURGE
    target_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}

class SecurityRequest(BaseModel):
    key: str

class ChangePasswordRequest(BaseModel):
    current_key: str
    new_key: str
    new_key_confirm: str
