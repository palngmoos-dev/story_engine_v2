"""
FastAPI Server for Phase 8.1: Universal Director's Hub.
Exposes the Narrative Engine as a central API.
"""
from fastapi import FastAPI, Request, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import bcrypt
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Load Solaris Master Key from .env
from .schemas import CommonResponse, ProjectCreateRequest, ProjectActionRequest, SecurityRequest, ChangePasswordRequest
from .project_manager import ProjectManager
from .orchestrator import NarrativeOrchestrator
from .user_sync import UserSyncManager
from .connectors.kakao_translator import KakaoTranslator
from ..state_model import WorldState
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from gemma_bridge import GemmaBridge

# --- KAKAO SCHEMAS ---
class KakaoUser(BaseModel):
    id: str

class KakaoUserRequest(BaseModel):
    user: KakaoUser
    utterance: str

class KakaoSkillRequest(BaseModel):
    userRequest: KakaoUserRequest

class EngineSwitchRequest(BaseModel):
    engine: str  # "ollama" or "lm_studio"
    model: Optional[str] = None
    base_url: Optional[str] = None

app = FastAPI(title="Infinite Narrative Canvas API", version="8.1.1-dev")

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton components
pm = ProjectManager()
gemma = GemmaBridge()
orchestrator = NarrativeOrchestrator(pm, gemma=gemma)
sync_manager = UserSyncManager()

# --- SECURITY CORE ---

class SecurityVault:
    VAULT_PATH = "security_vault.json"

    @classmethod
    def get_master_hash(cls):
        # 1. Check vault first (Priority)
        if os.path.exists(cls.VAULT_PATH):
            try:
                with open(cls.VAULT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("master_hash"), data.get("last_login")
            except Exception as e:
                print(f"VAULT READ ERROR: {str(e)}")
        
        # 2. Fallback to .env (1회성 Fallback)
        env_hash = os.getenv("SOLARIS_MASTER_HASH")
        if env_hash:
            return env_hash.strip("'").strip('"'), None
        return None, None

    @classmethod
    def update_last_login(cls):
        if not os.path.exists(cls.VAULT_PATH):
            return
        try:
            with open(cls.VAULT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["last_login"] = datetime.now().isoformat()
            
            with open(cls.VAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"VAULT UPDATE ERROR: {str(e)}")

    @classmethod
    def save_master_hash(cls, new_hash: str):
        """
        Saves the bcrypt hash to security_vault.json.
        Only the hash and metadata are stored; never the plain text.
        """
        data = {
            "master_hash": new_hash,
            "updated_at": datetime.now().isoformat(),
            "policy": {
                "auth_method": "bcrypt",
                "session_limit": 1
            }
        }
        
        try:
            # Atomic-like write using temporary file
            temp_path = cls.VAULT_PATH + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            # Atomic rename (on Windows os.replace handles overwrite)
            if os.path.exists(cls.VAULT_PATH):
                os.remove(cls.VAULT_PATH)
            os.rename(temp_path, cls.VAULT_PATH)

            # Simple permission warning for non-owner access (Windows specific)
            if os.name != 'nt':
                # Unix: set 600 (owner read/write only)
                os.chmod(cls.VAULT_PATH, 0o600)
                
            SecurityLogger.log("VAULT_INIT", "Master key successfully rotated/initialized")
            return True
        except Exception as e:
            SecurityLogger.log("VAULT_ERROR", f"Failed to save hash: {str(e)}", success=False)
            return False

    @classmethod
    def get_session(cls):
        if os.path.exists(cls.VAULT_PATH):
            try:
                with open(cls.VAULT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_session") # {token, last_seen}
            except: pass
        return None

    @classmethod
    def save_session(cls, token: Optional[str]):
        if not os.path.exists(cls.VAULT_PATH): return
        try:
            with open(cls.VAULT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if token:
                data["active_session"] = {"token": token, "at": datetime.now().isoformat()}
            else:
                data.pop("active_session", None)

            # Atomic write
            temp_path = cls.VAULT_PATH + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, cls.VAULT_PATH)
        except Exception as e:
            print(f"SESSION SAVE ERROR: {str(e)}")

class SecurityLogger:
    LOG_PATH = "logs/security.log"

    @classmethod
    def log(cls, eventType: str, message: str = "", success: bool = True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAIL"
        log_entry = f"[{timestamp}] [{eventType}] [{status}] {message}\n"
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls.LOG_PATH), exist_ok=True)
            with open(cls.LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Failure to log should not crash the main service
            print(f"CRITICAL: Failed to write security log: {str(e)}")

class SessionManager:
    # Single Session Policy: tokens[token] = timestamp
    # Persisted in security_vault.json for restart resilience
    
    @classmethod
    def create_session(cls):
        token = str(uuid.uuid4())
        SecurityVault.save_session(token)
        return token

    @classmethod
    def is_valid(cls, token: str):
        session = SecurityVault.get_session()
        return session and session.get("token") == token

    @classmethod
    def revoke_all(cls):
        SecurityVault.save_session(None)
        SecurityLogger.log("SESSION_REVOKED", "Force Logout: Persistent session cleared")

# --- SECURITY MIDDLEWARE (Phase 16) ---
from fastapi import Request

# 1단계: 로그인 전 허용 경로 목록 (Public Paths)
SAFE_PATHS = ["/", "/login", "/security/login", "/security/session", "/ai/gemma-test", "/ai/gemma-health", "/ai/harness-command", "/project/global_theatre/action", "/project/global_theatre/blueprint"]
SAFE_PREFIXES = ["/css/", "/js/", "/favicon.ico", "/assets/"]

@app.middleware("http")
async def director_key_check(request: Request, call_next):
    path = request.url.path
    
    # 허용 경로 및 정적 자산 예외 처리 (/docs 및 /openapi.json 포함)
    DOCS_PATHS = ["/docs", "/openapi.json"]
    is_safe = path in SAFE_PATHS or any(path.startswith(prefix) for prefix in SAFE_PREFIXES) or path in DOCS_PATHS
    if is_safe or "community" in path:
        return await call_next(request)
    
    # Token check: Support both X-Session-Token and Authorization: Bearer
    token = request.headers.get("X-Session-Token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token or not SessionManager.is_valid(token):
        SecurityLogger.log("UNAUTHORIZED_LOCKDOWN", f"Path: {path}", success=False)
        return JSONResponse(
            status_code=401, 
            content={"success": False, "message": "사용자 인증이 필요하거나 세션이 만료되었습니다."}
        )
            
    return await call_next(request)

# Root is handled by StaticFiles at the end of the file

@app.post("/security/login", response_model=CommonResponse)
@app.post("/security/session", response_model=CommonResponse)
async def login(req: SecurityRequest):
    master_hash, last_login = SecurityVault.get_master_hash()
    if not master_hash:
        return CommonResponse(success=False, message="시스템 보안 설정이 되어 있지 않습니다.")
    
    try:
        if bcrypt.checkpw(req.key.encode('utf-8'), master_hash.encode('utf-8')):
            token = SessionManager.create_session()
            SecurityVault.update_last_login()
            SecurityLogger.log("LOGIN_SUCCESS")
            return CommonResponse(
                success=True, 
                message="로그인 성공", 
                payload={
                    "token": token,
                    "last_login": last_login or datetime.now().isoformat()
                }
            )
        else:
            SecurityLogger.log("LOGIN_FAIL", "Invalid password", success=False)
            return CommonResponse(success=False, message="비밀번호가 틀렸습니다.")
    except Exception as e:
        SecurityLogger.log("LOGIN_FAIL", f"System Error: {str(e)}", success=False)
        return CommonResponse(success=False, message=f"인증 오류: {str(e)}")

@app.post("/security/log-event", response_model=CommonResponse)
async def log_security_event(req: Dict[str, str]):
    event = req.get("event", "UNKNOWN_EVENT")
    SecurityLogger.log(event, "Reported by frontend")
    return CommonResponse(success=True, message="Event logged")

@app.get("/security/session-info", response_model=CommonResponse)
async def get_session_info():
    _ , last_login = SecurityVault.get_master_hash()
    return CommonResponse(
        success=True,
        message="Session Info",
        payload={
            "status": "ACTIVE",
            "last_login": last_login,
            "idle_timeout": "10분",
            "policy": "단일 세션 (Single Session)"
        }
    )

@app.post("/security/change-password", response_model=CommonResponse)
async def change_password(req: ChangePasswordRequest):
    # 1. Validation: New password matching
    if req.new_key != req.new_key_confirm:
        return CommonResponse(success=False, message="새 비밀번호가 일치하지 않습니다.")
    
    # 2. Validation: Current password match
    master_hash, _ = SecurityVault.get_master_hash()
    if not master_hash:
        return CommonResponse(success=False, message="시스템 보안 설정을 로드할 수 없습니다.")
    
    try:
        # Check current password
        if not bcrypt.checkpw(req.current_key.encode('utf-8'), master_hash.encode('utf-8')):
            return CommonResponse(success=False, message="현재 비밀번호가 올바르지 않습니다.")
        
        # 3. Action: Hash and Save
        new_hash = bcrypt.hashpw(req.new_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if SecurityVault.save_master_hash(new_hash):
            # 4. Action: Revoke ALL sessions (Forced Logout)
            SessionManager.revoke_all()
            SecurityLogger.log("PASSWORD_CHANGED", "Credentials updated")
            return CommonResponse(
                success=True, 
                message="비밀번호가 성공적으로 변경되었습니다. 보안을 위해 모든 기기에서 로그아웃됩니다."
            )
        else:
            SecurityLogger.log("PASSWORD_CHANGED", "Failed to save hash", success=False)
            return CommonResponse(success=False, message="비밀번호 저장 중 오류가 발생했습니다.")
            
    except Exception as e:
        SecurityLogger.log("PASSWORD_CHANGED", f"System Error: {str(e)}", success=False)
        return CommonResponse(success=False, message=f"보안 처리 오류: {str(e)}")
async def create_project(req: ProjectCreateRequest):
    try:
        project_id = pm.create_project(req.title)
        # Initialize default state
        state = WorldState()
        state.metadata["summary"] = f"'{req.title}' 프로젝트가 시작되었습니다."
        pm.storage.save_project(project_id, state)
        
        # Save initial snapshot
        history = pm.storage.get_history_manager(project_id)
        history.save_snapshot(state, summary="Initial Project Creation")
        
        return CommonResponse(
            success=True,
            message="Project created successfully",
            project_id=project_id,
            world_state_summary=orchestrator._get_state_summary(state)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def list_projects():
    return pm.list_projects()

@app.post("/project/{id}/action", response_model=CommonResponse)
async def perform_action(id: str, req: ProjectActionRequest):
    return orchestrator.run_action(id, req.action_type, req.params)

# --- MESSENGER WEBHOOKS ---

@app.post("/webhook/kakao")
async def kakao_webhook(req: KakaoSkillRequest):
    """Receives requests from Kakao i Open Builder Skill."""
    user_id = req.userRequest.user.id
    utterance = req.userRequest.utterance

    # 1. Sync / Restore project_id
    project_id = sync_manager.get_or_create_project("kakao", user_id, pm)
    
    # 2. Parse Commands (Phase 15: Tarot & Weaver)
    response = None
    if utterance.startswith("/pick"):
        card_id = utterance.replace("/pick", "").strip()
        response = orchestrator.run_action(project_id, "PICK", {"card_id": card_id})
    elif utterance == "/deal":
        response = orchestrator.run_action(project_id, "DRAW_TAROT")
    elif utterance.startswith("/burn"):
        card_id = utterance.replace("/burn", "").strip()
        response = orchestrator.run_action(project_id, "DISCARD_CARD", {"card_id": card_id})
    elif utterance == "/board":
        # Returns current spread
        state = pm.storage.load_project(project_id)
        from .schemas import CommonResponse as CR
        response = CR(
            success=True, 
            message="현재 테이블 상태입니다.", 
            project_id=project_id,
            world_state_summary=orchestrator._get_state_summary(state),
            payload={"spread": state.tarot_spread}
        )
    elif "/surge" in utterance:
        response = orchestrator.run_action(project_id, "SURGE", {"surge_type": "NITRO_SWIFT"})
    elif "/status" in utterance:
        state = pm.storage.load_project(project_id)
        s = orchestrator._get_state_summary(state)
        from .schemas import CommonResponse as CR
        response = CR(success=True, message=f"🎬 '{state.metadata.get('summary', 'Project')}' 상태", project_id=project_id, world_state_summary=s)
    else:
        # Default: Show board
        state = pm.storage.load_project(project_id)
        s = orchestrator._get_state_summary(state)
        from .schemas import CommonResponse as CR
        response = CR(success=True, message="현재 상태 보고", project_id=project_id, world_state_summary=s)
    
    # 3. Enrich Response with Multimodal/Duration for Phase 15
    state = pm.storage.load_project(project_id)
    duration = orchestrator.get_duration_estimate(project_id, state.voice_speed)
    if response and response.success:
        response.payload = response.payload or {}
        response.payload["multimodal"] = state.current_multimodal_assets
        response.payload["duration"] = duration.get("scene_duration")

    # 4. Translate to Kakao UI
    return KakaoTranslator.to_skill_response(response)

@app.get("/project/{id}/blueprint", response_model=CommonResponse)
async def get_blueprint(id: str):
    """Fetches the full cinematic timeline for the workspace. Auto-provisions global_theatre if missing."""
    state = pm.storage.load_project(id)
    
    # Auto-initialization for the main theatre
    if not state and id == "global_theatre":
        pm.create_project_with_id(id, "Global Theatre")
        state = WorldState()
        
        # Seed with 3 starter cards as requested
        from ..tarot_engine import TarotEngine
        for _ in range(3):
            TarotEngine.draw_to_spread(state)
        
        pm.storage.save_project(id, state)
        SecurityLogger.log("PROJECT_INIT", f"Auto-provisioned {id} with 3 starter cards")
        
    if not state:
        return CommonResponse(success=False, message="Project not found", project_id=id)
        
    return CommonResponse(
        success=True, 
        message="Blueprint fetched", 
        project_id=id, 
        world_state_summary=orchestrator._get_state_summary(state)
    )

# ================================================================
# Phase 9 Endpoints: Rendering, Character, Export
# ================================================================

class CharacterSetRequest(BaseModel):
    character: Dict[str, Any]

class RenderBeatRequest(BaseModel):
    beat_index: int = 0

class RefineCharacterRequest(BaseModel):
    cid: str
    role: str

class GemmaPromptRequest(BaseModel):
    prompt: str

class HarnessCommandRequest(BaseModel):
    command: str

@app.get("/ai/gemma-health", response_model=CommonResponse)
async def gemma_health():
    """GemmaBridge의 현재 상태 및 연결성을 확인합니다."""
    success, data = await gemma.health_check()
    return CommonResponse(
        success=success,
        message="Gemma Health Check Result" if success else "Gemma Health Check Failed",
        payload={
            "base_url": gemma.base_url,
            "model": gemma.model,
            "models_response": data
        }
    )

@app.post("/ai/gemma-test", response_model=CommonResponse)
async def gemma_test(req: GemmaPromptRequest):
    """하네스 엔지니어링 자율 주행 루프를 가동합니다."""
    try:
        # 1. 자율 주행 엔진 초기화
        pilot = GemmaAutoPilot()
        
        # 2. 자율 주행 실행 (비동기)
        # BackgroundTasks를 사용하지 않고 직접 대기하여 결과를 리포트함 (15분 타임아웃 지원)
        await pilot.engage()
        
        return CommonResponse(
            success=True,
            message="하네스 엔지니어링 자율 주행 사이클이 성공적으로 완료되었습니다.",
            data={"status": "completed", "autopilot": "active"}
        )
    except Exception as e:
        return CommonResponse(
            success=False,
            message=f"하네스 엔지니어링 가동 실패: {str(e)}",
            data=None
        )

@app.post("/ai/harness-command", response_model=CommonResponse)
async def harness_command(req: HarnessCommandRequest, background_tasks: BackgroundTasks):
    """음성 또는 텍스트 명령을 수집하여 수석 엔지니어 자율 주행을 트리거합니다."""
    try:
        # 1. NEXT_TASK.md 업데이트
        next_task_path = "memory/NEXT_TASK.md"
        os.makedirs("memory", exist_ok=True)
        with open(next_task_path, "w", encoding="utf-8") as f:
            f.write(req.command)
        
        # 2. 자율 주행 엔진 및 라우터 가동
        from scripts.gemma_auto_pilot import GemmaAutoPilot
        from scripts.task_router import route_task
        pilot = GemmaAutoPilot()
        
        # 3. 모델에게 판단 요청 (로컬 gemma4:e2b 전용)
        decision = await gemma.simple_prompt(req.command)
        print(f"[Harness] Analysis completed via gemma4:e2b (Local).")
        
        # 4. 계획에 ACTION_CODE가 포함되어 있다면 실무 작업 라우팅 실행
        operational_result = None
        if "[ACTION_CODE]" in decision or any(k in decision for k in ["REPORT_UPDATE", "FILE_SCAN", "QUEUE_REFRESH"]):
            print(f"[Harness] Operational action detected in decision. Routing...")
            operational_result = route_task(decision)
        
        # 5. 기억 장치 동기화는 백그라운드 태스크로 처리
        background_tasks.add_task(pilot.sync_to_memory, decision)
        
        return CommonResponse(
            success=True,
            message="수석 엔지니어가 명령을 분석하고 작업을 수행했습니다." if operational_result else "수석 엔지니어가 명령 분석을 완료했습니다.",
            payload={
                "report": decision,
                "operational_result": operational_result
            }
        )
    except Exception as e:
        return CommonResponse(success=False, message=f"자율 주행 트리거 오류: {str(e)}")

@app.post("/project/{id}/character/set", response_model=CommonResponse)
async def set_lead_character(id: str, req: CharacterSetRequest):
    """Registers a lead character into the project WorldState."""
    return orchestrator.set_lead_character(id, req.character)

@app.post("/project/{id}/render/beat", response_model=CommonResponse)
async def render_beat(id: str, req: RenderBeatRequest):
    """Renders a single committed story beat into a full cinematic scene."""
    return orchestrator.render_beat(id, req.beat_index)

@app.post("/project/{id}/render/full", response_model=CommonResponse)
async def render_full(id: str):
    """Renders all committed story beats into a complete screenplay."""
    return orchestrator.render_full(id)

@app.post("/project/{id}/render-scene", response_model=CommonResponse)
async def render_scene(id: str):
    """Atelier-specific: Renders a scene based on current tarot interpretation."""
    return orchestrator.render_scene_from_interpretation(id)

@app.post("/project/{id}/refine-character", response_model=CommonResponse)
async def refine_character(id: str, req: RefineCharacterRequest):
    """AI를 호출하여 실제 캐릭터 프로필을 생성합니다."""
    try:
        profile = orchestrator.generate_refinement_profile(id, req.cid, req.role)
        return CommonResponse(
            success=True, 
            message="AI가 캐릭터를 생성했습니다.", 
            project_id=id, 
            payload={"profile": profile}
        )
    except Exception as e:
        return CommonResponse(success=False, message=f"AI 생성 실패: {str(e)}", project_id=id)

@app.get("/project/{id}/export")
async def export_project(id: str, format: str = "markdown"):
    """Exports the project screenplay as a downloadable file."""
    from fastapi.responses import FileResponse
    resp = orchestrator.export_project(id, format)
    if resp.success:
        file_path = resp.payload.get("file_path")
        return FileResponse(
            path=file_path,
            media_type="text/markdown",
            filename=os.path.basename(file_path)
        )
    raise HTTPException(status_code=500, detail=resp.message)

# ================================================================
# Telegram Webhook
# ================================================================
from .connectors.telegram_translator import TelegramTranslator

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None

@app.post("/webhook/telegram")
async def telegram_webhook(update: TelegramUpdate):
    """Receives updates from Telegram Bot webhook."""
    message = update.message or {}
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    user_id = str(message.get("from", {}).get("id", chat_id))

    if not chat_id or not text:
        return {"ok": True}

    # Sync / Restore project_id
    project_id = sync_manager.get_or_create_project("telegram", user_id, pm)

    # Route commands
    if text.startswith("/pick"):
        card_id = text.replace("/pick", "").strip()
        response = orchestrator.run_action(project_id, "PICK", {"card_id": card_id})
    elif text.startswith("/render"):
        parts = text.split()
        beat_idx = int(parts[1]) - 1 if len(parts) > 1 and parts[1].isdigit() else 0
        response = orchestrator.render_beat(project_id, beat_idx)
    elif text == "/surge":
        response = orchestrator.run_action(project_id, "SURGE", {"surge_type": "NITRO_SWIFT"})
    elif text == "/export":
        response = orchestrator.export_project(project_id)
    elif text == "/status":
        state = pm.storage.load_project(project_id)
        s = orchestrator._get_state_summary(state)
        from .schemas import CommonResponse as CR
        response = CR(success=True, message=f"🎬 Status", project_id=project_id, world_state_summary=s,
                      payload={"beats": len(state.story_beats), "rendered": len(state.rendered_scenes)})
    else:
        # Default: Status or empty
        state = pm.storage.load_project(project_id)
        s = orchestrator._get_state_summary(state)
        from .schemas import CommonResponse as CR
        response = CR(success=True, message="Status Update", project_id=project_id, world_state_summary=s)

    return TelegramTranslator.to_send_message(chat_id, response)

# ================================================================
# Phase 12 & 13: Community, Undo, Reset, Editability
# ================================================================
from .api_community import router as community_router, init_community
init_community(pm)
app.include_router(community_router)

class EntityUpdateRequest(BaseModel):
    entity_type: str # CHARACTER, BEAT
    entity_id: Any
    updates: Dict[str, Any]

@app.post("/project/{id}/undo", response_model=CommonResponse)
async def undo_action(id: str):
    return orchestrator.undo_last_action(id)

@app.post("/project/{id}/reset", response_model=CommonResponse)
async def reset_project(id: str):
    return orchestrator.reset_project(id)

@app.post("/project/{id}/update-entity", response_model=CommonResponse)
async def update_entity(id: str, req: EntityUpdateRequest):
    return orchestrator.update_entity(id, req.entity_type, req.entity_id, req.updates)

# --- Phase 14: Tarot & Weaver ---

@app.post("/project/{project_id}/tarot/init")
async def init_tarot(project_id: str):
    return orchestrator.init_tarot(project_id)

@app.post("/project/{project_id}/draw-card", response_model=CommonResponse)
async def atelier_draw_card(project_id: str):
    """Atelier-specific card draw with ritual metadata."""
    return orchestrator.run_action(project_id, "DRAW_TAROT")

@app.post("/project/{project_id}/tarot/burn")
async def burn_tarot(project_id: str, card_id: str):
    return orchestrator.run_action(project_id, "DISCARD_CARD", {"card_id": card_id})

@app.get("/project/{project_id}/duration-estimate")
async def get_duration_estimate(project_id: str, speed: float = 1.0):
    return orchestrator.get_duration_estimate(project_id, speed)

@app.post("/project/{project_id}/recall-assets")
async def recall_assets(project_id: str, scene_index: int):
    return orchestrator.recall_assets(project_id, scene_index)

@app.post("/project/{project_id}/multimodal-gen")
async def trigger_gen(project_id: str, type: str):
    return orchestrator.trigger_multimodal_generation(project_id, type)

@app.post("/project/{project_id}/manual-sync")
async def manual_sync(project_id: str, from_index: int):
    return orchestrator.manual_sync_downstream(project_id, from_index)

# --- Phase 16: Monetization & Wallet ---

class ChargeRequest(BaseModel):
    amount: float
    payment_method: str # CARD, KAKAO, TOSS

@app.post("/project/{id}/charge", response_model=CommonResponse)
async def charge_essence(id: str, req: ChargeRequest):
    """Mocks a successful payment and adds Essence to the wallet."""
    lock = pm.get_project_lock(id)
    with lock:
        state = pm.storage.load_project(id)
        if not state: raise HTTPException(status_code=404, detail="Project not found")
        
        state.wallet.essence_balance += req.amount
        state.transaction_history.append({
            "type": "CHARGE",
            "amount": req.amount,
            "method": req.payment_method,
            "at": datetime.now().isoformat()
        })
        pm.storage.save_project(id, state)
        
        return CommonResponse(
            success=True, 
            message=f"{req.payment_method}를 통한 {req.amount} 에센스 충전 완료!",
            project_id=id,
            world_state_summary=orchestrator._get_state_summary(state)
        )

@app.get("/project/{id}/sync-status", response_model=CommonResponse)
async def get_sync_status(id: str):
    """Checks if a project exists and returns basic status (for Resume flow)."""
    state = pm.storage.load_project(id)
    if not state:
        return CommonResponse(success=False, message="Project not found", project_id=id)
    return CommonResponse(
        success=True, 
        message="Session active", 
        project_id=id, 
        world_state_summary=orchestrator._get_state_summary(state),
        payload={"last_update": state.metadata.get("last_update")}
    )

@app.post("/ai/switch-engine", response_model=CommonResponse)
async def switch_engine(req: EngineSwitchRequest):
    """엔진을 동적으로 교체합니다 (Ollama <-> LM Studio)"""
    global gemma, orchestrator
    try:
        # 새로운 GemmaBridge 인스턴스 생성
        new_gemma = GemmaBridge(
            engine_type=req.engine,
            model=req.model,
            base_url=req.base_url
        )
        
        # 헬스체크 수행
        is_alive, health = new_gemma.health_check()
        if not is_alive:
             return CommonResponse(success=False, message=f"Engine health check failed: {health}")
        
        # 성공 시 글로벌 객체 업데이트
        gemma = new_gemma
        orchestrator.gemma = gemma
        
        return CommonResponse(
            success=True, 
            message=f"Engine successfully switched to {req.engine}",
            project_id=None,
            payload={"engine": req.engine, "model": gemma.model, "base_url": gemma.base_url}
        )
    except Exception as e:
        return CommonResponse(success=False, message=f"Engine switch error: {str(e)}")

# --- STATIC FILES (The Workshop) ---
for d in ["public", "public/css", "public/js", "public/assets", "public/assets/portraits"]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

# Mount specific folders first to avoid catch-all issues
app.mount("/css", StaticFiles(directory="public/css"), name="css")
app.mount("/js", StaticFiles(directory="public/js"), name="js")
app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    # 타임아웃을 1시간(3600초)으로 설정하여 장문 연산 중 연결 끊김 방지
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=3600, timeout_graceful_shutdown=3600)

