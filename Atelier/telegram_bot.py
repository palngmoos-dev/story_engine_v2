import os
from dotenv import load_dotenv
# Load .env using relative path to support both Windows and WSL
load_dotenv(override=True)

import sys
import json
import re
import time
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional

import requests
import io
import asyncio

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

from v2_core import scene_engine as scene
from v2_core import wizard_engine as wizard
from v2_core import export_engine as exporter
from v2_core import canvas_engine as canvas
from scripts.voice_processor import VoiceProcessor
from gemma_bridge import GemmaBridge
from scripts.tts_engine import generate_voice

# Global engines for voice/AI (Lazy initialized)
VOICE_ENGINE = None
GEMMA_BRIDGE = None # 지연 초기화 예정

# =========================
# 유저 상태 관리
# =========================
def send_document(chat_id: int, file_path: str, caption: str = "") -> None:
    """텔레그램 API를 사용하여 문서를 전송함"""
    logging.info(f"send_document 호출: chat_id={chat_id}, file={file_path}")
    url = f"{API_BASE}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': caption}
        r = requests.post(url, files=files, data=data, timeout=60)
        r.raise_for_status()

def send_voice(chat_id: int, file_path: str) -> None:
    """텔레그램 API를 사용하여 음성 메시지를 전송함"""
    logging.info(f"send_voice 호출: chat_id={chat_id}, file={file_path}")
    url = f"{API_BASE}/sendVoice"
    with open(file_path, 'rb') as f:
        files = {'voice': f}
        data = {'chat_id': chat_id}
        r = requests.post(url, files=files, data=data, timeout=60)
        r.raise_for_status()
# 상태: IDLE (일반), WIZARD_STORY (스토리 추천), WIZARD_CHAR (캐릭터 추천)
USER_STATE = {} # {chat_id: {"state": "IDLE", "data": {}}}
CURRENT_USER_INPUT = "" # 현재 처리 중인 업데이트의 원문

def get_user_state(chat_id: int):
    return USER_STATE.get(chat_id, {"state": "IDLE", "data": {}})

def set_user_state(chat_id: int, state: str, data: dict = None):
    USER_STATE[chat_id] = {"state": state, "data": data or {}}

def send_message_with_buttons(chat_id: int, text: str, buttons: list) -> None:
    """
    buttons: [[{"text": "A", "callback_data": "a"}, {"text": "B", ...}], [...]]
    """
    logging.info(f"send_message_with_buttons: chat_id={chat_id}")
    reply_markup = {"inline_keyboard": buttons}
    safe_post(
        f"{API_BASE}/sendMessage",
        json={
            "chat_id": chat_id, 
            "text": text,
            "reply_markup": reply_markup
        },
        timeout=30,
    )

def answer_callback_query(callback_query_id: str, text: str = ""):
    safe_post(
        f"{API_BASE}/answerCallbackQuery",
        json={
            "callback_query_id": callback_query_id,
            "text": text
        }
    )


# =========================
# 기본 설정
# =========================
os.makedirs("logs", exist_ok=True)

log_path = "logs/app.log"
handler = RotatingFileHandler(
    log_path,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)


HELP_TEXT = """
[기본 창작]
/start 또는 /초기화
- 셋업 마법사 시작 (초보자 추천 모드)

/시놉시스 [줄거리]
- 시놉시스 분석 후 세계관 자동 구축 (전문가 모드)

/쓰기 내용
/이어쓰기 내용
- 새로운 씬 생성

/목록
- 지금까지의 씬 요약 목록 보기

[타임라인 & 캔버스 편집]
/타임라인
- 전체 시퀀스 및 씬 지도(Canvas) 보기

/이동 [현재번호] [목표번호]
- 씬의 위치 이동 및 타임라인 재정렬

/바꾸기 [A번] [B번]
- 두 씬의 위치를 서로 맞교환

/묶기 [시작] [종료] [이름]
- 지정된 범위를 하나의 시퀀스(묶음)로 지정

/수정 [번호] [내용]
- 씬 내용을 직접 수정하고 서사 영향 분석 받기

/메모 [내용]
- AI가 반드시 지켜야 할 창작 대원칙 추가 (예: 주인공은 울지 않는다)

/싱크
- 현재 서사와 메모를 분석하여 향후 전개 방향 제안

/다시쓰기 / 삭제 / 넣기 / 압축 / 확장
- 전문적인 서사 편집 명령 (사용법은 /도움말 참고)

/시간 [타입]
- 시간대 설정 (낮, 밤, 새벽, 황혼)

/카메라 [타입]
- 촬영 기법 설정 (클로즈업, 롱샷, 로우앵글 등)

/분위기 [타입]
- 메커니즘 설정 (공포, 희망, 용맹, 비굴)

/감각 [타입]
- 오감 강조 (시각, 청각, 후각, 촉각, 미각)

/속성 [타입]
- 5원소 주입 (불, 물, 흙, 바람, 번개)

/관계 [사랑/우정 등] /의상 [룩] /음식 [메뉴]
- 세밀한 연출 정체성 부여

/음악 [분위기] /효과음 [효과]
- 청각적 미장센 및 BGM 설정

/추천카드
- AI가 현재 서사에 어울리는 연출 카드 5장을 무작위 추천 (AI의 연출 의도 포함)

/개념 [이름]
- 추상적/철학적 주제 주입 (천사, 악마, 조화, 철학 등)

/우주 [이름]
- 서사적 스케일 조절 (대자연, 우주, 심연 등)

[타임라인 내비게이션]
/과거
- 회상(Flashback) 시점으로 전환 (🔴 붉은 실의 메아리)
/현재
- 다시 현재 시점으로 복귀 (🟡 황금빛 존재감)
/미래
- 환상(Vision) 시점으로 전환 (🔵 푸른 예견)

/추천
- 아이디어 뱅크에서 무작위 창작 소재(영감) 3개 추천

/타임라인
- 전체 시퀀스 지도 및 총 예상 상영 시간 보기

/수출 또는 /다운로드
- 현재 서사를 프로페셔널 마크다운(.md) 파일로 출력

[시간 조절]
명령 뒤에 [X분]을 넣으면 해당 분량에 맞춰 전개
예: /쓰기 [10분] 긴 대화를 나눈다

[참고사항 넣는 법]
명령 뒤에 괄호로 원하는 방향을 적으면 반영
예: /쓰기 지하철에서 우연히 만난다 (잔잔하게)
""".strip()


def load_bot_token() -> str:
    """.env 파일에서 텔레그램 봇 토큰을 로드함"""
    # load_dotenv가 최상단에서 override=True로 호출되었으므로 최신 값을 읽습니다.
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if token:
        masked = token[:6] + "..." + token[-4:]
        logging.info(f"환경 변수에서 토큰 로딩 성공: {masked}")
        print(f"정보: 봇 토큰 사용: {masked}")
        return token.strip()

    print("CRITICAL: TELEGRAM_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해 주세요.")
    sys.exit(1)

# 가동 시 토큰 로드
BOT_TOKEN = load_bot_token()
print(f"디버그: 토큰 로딩 상태: {bool(BOT_TOKEN)}")

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
AI_TIMEOUT = 1800
DISABLE_GEMINI = True
SCENES_FILE = "scenes.json"


# =========================
# 공통 유틸
# =========================
def load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.exception(f"JSON 로드 실패: {e}")
        return default


def save_json(path: str, data: Any) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.exception(f"JSON 저장 실패: {e}")
        raise


def renumber_scenes(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for i, scene in enumerate(scenes, start=1):
        scene["scene_number"] = i
    return scenes


def get_scenes() -> List[Dict[str, Any]]:
    scenes = load_json(SCENES_FILE, [])
    if not isinstance(scenes, list):
        scenes = []
    return renumber_scenes(scenes)


def set_scenes(scenes: List[Dict[str, Any]]) -> None:
    save_json(SCENES_FILE, renumber_scenes(scenes))


def build_story_history(scenes: List[Dict[str, Any]]) -> str:
    if not scenes:
        return "아직 작성된 씬이 없습니다."
    parts = []
    for s in scenes:
        n = s.get("scene_number", "?")
        text = s.get("text", "")
        parts.append(f"[{n}씬]\n{text}")
    return "\n\n".join(parts)


def parse_text_and_note(raw_text: str):
    raw_text = raw_text.strip()
    match = re.match(r"^(.*?)(?:\((.*?)\))?$", raw_text)
    if not match:
        return raw_text, ""

    main_text = (match.group(1) or "").strip()
    note = (match.group(2) or "").strip()
    return main_text, note


def parse_range_command(text: str) -> Optional[tuple]:
    parts = text.split()
    if len(parts) != 3:
        return None
    if not parts[1].isdigit() or not parts[2].isdigit():
        return None
    start_scene = int(parts[1])
    end_scene = int(parts[2])
    if start_scene < 1 or end_scene < 1 or start_scene > end_scene:
        return None
    return start_scene, end_scene


def split_command_and_note(text: str):
    text = text.strip()
    match = re.match(r"^(.*?)(?:\((.*?)\))?$", text)
    if not match:
        return text, ""
    command_part = (match.group(1) or "").strip()
    note = (match.group(2) or "").strip()
    return command_part, note


def chunk_text(text: str, max_len: int = 3800) -> List[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    lines = text.splitlines()
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current.strip())
            current = line
        else:
            current += ("\n" if current else "") + line

    if current.strip():
        chunks.append(current.strip())

    return chunks


# =========================
# HTTP 안전 호출
# =========================
def safe_get(url, params=None, timeout=30, retries=5, delay=3):
    current_delay = delay
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logging.error(f"[!] 401 Unauthorized: 토큰이 올바르지 않습니다. 설정을 확인해 주세요.")
                print(f"[!] 401 Unauthorized: Invalid Token. Please check your TELEGRAM_BOT_TOKEN.")
                raise # 401은 토큰 문제이므로 즉시 중단
            
            if e.response.status_code == 409:
                logging.warning(f"[!] 409 Conflict: 다른 곳에서 봇이 가동 중일 수 있습니다. 5초 후 재시도... ({attempt}/{retries})")
                time.sleep(5)
                continue

            logging.exception(f"GET 실패 {attempt}/{retries}: {e}")
            if attempt == retries:
                raise
            time.sleep(current_delay)
            current_delay *= 2 # 지수 백오프
        except Exception as e:
            print(f"[DEBUG] GET 실패 {attempt}/{retries}: {e}")
            logging.exception(f"GET 실패 {attempt}/{retries}: {e}")
            if attempt == retries:
                raise
            time.sleep(current_delay)
            current_delay *= 2


def safe_post(url, data=None, json=None, timeout=30, retries=5, delay=3):
    current_delay = delay
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, data=data, json=json, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logging.error(f"[!] 401 Unauthorized: 토큰이 올바르지 않습니다. 설정을 확인해 주세요.")
                raise 
            
            if e.response.status_code == 409:
                logging.warning(f"[!] 409 Conflict: 충동 발생. 5초 후 재시도... ({attempt}/{retries})")
                time.sleep(5)
                continue

            logging.exception(f"POST 실패 {attempt}/{retries}: {e}")
            if attempt == retries:
                raise
            time.sleep(current_delay)
            current_delay *= 2
        except Exception as e:
            print(f"[DEBUG] POST 실패 {attempt}/{retries}: {e}")
            logging.exception(f"POST 실패 {attempt}/{retries}: {e}")
            if attempt == retries:
                raise
            time.sleep(current_delay)
            current_delay *= 2

# =========================
# 셋업 마법사 주요 로직
# =========================
def start_wizard(chat_id: int):
    """마법사 시작: 스토리 추천 단계로 진입"""
    set_user_state(chat_id, "WIZARD_STORY")
    show_story_recommendation(chat_id)

def show_story_recommendation(chat_id: int):
    """AI에게 스토리를 추천받아 유저에게 제시"""
    send_message(chat_id, "🪄 당신의 창작 파트너가 멋진 이야기를 구상 중입니다...")
    rec = wizard.recommend_story()
    
    # 세션 데이터에 현재 제안 저장
    set_user_state(chat_id, "WIZARD_STORY", {"current_rec": rec})
    
    text = f"✨ [추천 스토리]\n\n장르: {rec['genre']}\n줄거리: {rec['plot']}\n\n💡 추천 이유: {rec['reason']}\n\n이 이야기가 마음에 드시나요?"
    buttons = [
        [
            {"text": "✅ 확정 (이대로 시작)", "callback_data": "story_ok"},
            {"text": "🔄 다시 추천 (Pass)", "callback_data": "story_pass"}
        ],
        [{"text": "✍️ 내가 직접 입력하기", "callback_data": "story_direct"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)

def ask_char_step(chat_id: int, step_index: int):
    """캐릭터 설정의 특정 단계를 물어봄"""
    steps = ["name", "age", "gender", "occupation", "personality"]
    labels = {
        "name": "이름 (한국식 성함)",
        "age": "나이 (숫자만도 가능)",
        "gender": "성별 (남성/여성/기타)",
        "occupation": "직업",
        "personality": "핵심 성격 및 특징"
    }
    
    if step_index >= len(steps):
        show_char_review(chat_id)
        return

    trait_key = steps[step_index]
    state = get_user_state(chat_id)
    state["data"]["wizard_step"] = step_index
    set_user_state(chat_id, f"WIZARD_CHAR_{trait_key.upper()}", state["data"])
    
    text = f"🎭 [캐릭터 설정 {step_index + 1}/5]\n\n주인공의 **{labels[trait_key]}**을(를) 입력해 주세요.\n\n적절한 아이디어가 생각나지 않는다면 아래 버튼을 눌러 AI 선생님의 추천을 받을 수 있습니다."
    
    # 버튼 구성: 랜덤 추천 + 이전 단계
    row1 = [{"text": "🎲 랜덤 추천", "callback_data": f"char_rand_{trait_key}"}]
    buttons = [row1]
    
    if step_index > 0:
        buttons.append([{"text": "⬅️ 이전 단계로", "callback_data": f"char_back_{step_index - 1}"}])
    else:
        # 1단계(이름)에서 뒤로 가기는 스토리 확정 단계로 돌아가기
        buttons.append([{"text": "⬅️ 스토리 확정 단계로", "callback_data": "story_back"}])

    send_message_with_buttons(chat_id, text, buttons)

def show_char_review(chat_id: int):
    """최종 입력된 캐릭터 정보를 요약해서 보여주고 수정 기회 제공"""
    state = get_user_state(chat_id)
    char = state["data"].get("lead_character", {})
    
    set_user_state(chat_id, "WIZARD_CHAR_REVIEW", state["data"])
    
    text = (
        f"📝 [캐릭터 최종 확인]\n\n"
        f"성함: {char.get('name', '미정')}\n"
        f"나이: {char.get('age', '미정')}\n"
        f"성별: {char.get('gender', '미정')}\n"
        f"직업: {char.get('occupation', '미정')}\n"
        f"성격: {char.get('personality', '미정')}\n\n"
        f"💡 이대로 캐스팅을 확정할까요? 수정하고 싶은 부분이 있다면 아래 버튼을 눌러주세요."
    )
    
    buttons = [
        [
            {"text": "✏️ 이름 수정", "callback_data": "edit_name"},
            {"text": "✏️ 나이 수정", "callback_data": "edit_age"}
        ],
        [
            {"text": "✏️ 성별 수정", "callback_data": "edit_gender"},
            {"text": "✏️ 직업 수정", "callback_data": "edit_occupation"}
        ],
        [{"text": "✏️ 성격 수정", "callback_data": "edit_personality"}],
        [{"text": "✅ 캐스팅 최종 확정 (시작!)", "callback_data": "char_final_ok"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)

def show_char_recommendation(chat_id: int):
    """현재 결정된 스토리에 맞는 캐릭터 추천"""
    state = get_user_state(chat_id)
    story_context = state["data"].get("story", {})
    
    send_message(chat_id, "🎭 이 이야기에 딱 맞는 주인공을 캐스팅 중입니다...")
    rec = wizard.recommend_character(story_context)
    
    # 세션 데이터에 현재 제안 저장 (기존 스토리 정보 유지)
    state["data"]["current_rec"] = rec
    set_user_state(chat_id, "WIZARD_CHAR", state["data"])
    
    text = (
        f"👤 [추천 주연 배우]\n\n"
        f"이름: {rec['name']} (나이: {rec['age']}, {rec['gender']})\n"
        f"MBTI: {rec['mbti']} | 직업: {rec['occupation']}\n"
        f"핵심 성격: {rec['personality']}\n"
        f"단점: {rec['flaw']} / 스킬: {rec['skill']}\n\n"
        f"💡 주연인 이유: {rec['reason']}\n\n"
        f"이 캐릭터를 주인공으로 캐스팅할까요?"
    )
    buttons = [
        [
            {"text": "✅ 캐스팅 확정", "callback_data": "char_ok"},
            {"text": "🔄 다른 배우 추천", "callback_data": "char_pass"}
        ],
        [{"text": "✍️ 직접 캐릭터 만들기", "callback_data": "char_direct"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)


# =========================
# 텔레그램 통신
# =========================
def send_message(chat_id: int, text: str) -> None:
    logging.info(f"send_message 호출: chat_id={chat_id}, text_len={len(text)}")
    for part in chunk_text(text):
        safe_post(
            f"{API_BASE}/sendMessage",
            data={"chat_id": chat_id, "text": part},
            timeout=30,
        )
    
    # TTS Trigger (Global Context)
    if "말해줘" in CURRENT_USER_INPUT:
        def tts_task():
            try:
                temp_voice_path = f"logs/voice_{chat_id}_{int(time.time())}.ogg"
                import asyncio
                asyncio.run(generate_voice(text, temp_voice_path))
                
                if os.path.exists(temp_voice_path):
                    send_voice(chat_id, temp_voice_path)
                    os.remove(temp_voice_path)
            except Exception as e:
                logging.error(f"TTS 스레드 실패: {e}")

        import threading
        threading.Thread(target=tts_task, daemon=True).start()

def get_updates(offset: int = None) -> List[Dict[str, Any]]:
    params = {"timeout": 25}
    if offset is not None:
        params["offset"] = offset

    try:
        r = safe_get(
            f"{API_BASE}/getUpdates",
            params=params,
            timeout=35
        )
        if r is None:
            return []
        data = r.json()
        return data.get("result", [])
    except Exception as e:
        logging.error(f"업데이트 가져오기 중 오류가 발생했습니다: {e}")
        return []


# =========================
# AI 호출 래퍼
# story_engine.generate_next_scene 시그니처가 달라도
# 여기 한 곳만 수정하면 됨
# =========================
def call_writer_model(prompt: str) -> str:
    try:
        return generate_next_scene(prompt)
    except TypeError:
        pass

    try:
        return generate_next_scene([], prompt)
    except TypeError:
        pass

    try:
        return generate_next_scene({"prompt": prompt})
    except TypeError:
        pass

    raise RuntimeError("generate_next_scene 함수 시그니처를 확인해줘.")


# =========================
# 스토리 엔진
# =========================
def parse_duration(text: str) -> tuple:
    """텍스트에서 [X분] 형식을 찾아 분량(int)과 남은 텍스트 반환"""
    import re
    match = re.search(r"\[(\d+)분\]", text)
    if match:
        duration = int(match.group(1))
        clean_text = text.replace(match.group(0), "").strip()
        return duration, clean_text
    return 5, text # 기본값 5분

def handle_scene(chat_id: int, text: str, note: str = "") -> None:
    def scene_task():
        try:
            scenes = get_scenes()
            next_number = len(scenes) + 1
            
            duration, clean_input = parse_duration(text)
            user_input = clean_input.strip()
            if note:
                user_input += f" (참고사항: {note})"

            logging.info(f"🧠 스토리 생성 시작 (씬 {next_number}, {duration}분)")
            
            result = scene.play_turn(user_input=user_input, scene_no=next_number, duration=duration)
            
            scene_text = result.get("scene_text", "생성 실패")
            state = result.get("state", {})
            logging.info("✅ 스토리 생성 완료")

            new_scene = {
                "scene_number": next_number,
                "text": scene_text,
                "metadata": {
                    "place": state.get("place"),
                    "lead_character": state.get("lead_character"),
                    "tag": result.get("state_tag"),
                    "duration": duration,
                    "impact": result.get("impact", 1),
                    "event_summary": result.get("event_summary", "사건 요약 없음")
                }
            }
            scenes.append(new_scene)
            set_scenes(scenes)

            # 상태 정보 요약 전송
            status_info = f"[상태: {result['state_tag']}] [{duration}분] [P:{state['timing']['pressure']} E:{state['timing']['echo']} S:{state['timing']['suspicion']}] [I: {result['impact_score']}]"
            send_message(chat_id, f"✅ {next_number}씬 생성이 완료되었습니다!\n\n{status_info}\n\n{scene_text}")
        except Exception as e:
            logging.error(f"장면 생성 태스크 실패: {e}")
            send_message(chat_id, f"⚠️ 스토리 생성 중 오류가 발생했습니다: {e}")

    import threading
    send_message(chat_id, "🧠 파트너가 새로운 장면을 구상하고 있습니다... 소요 시간이 걸릴 수 있으니 잠시만 기다려 주세요.")
    threading.Thread(target=scene_task, daemon=True).start()


# =========================
# 편집 명령
# =========================
def cmd_list_scenes(chat_id: int):
    scenes = get_scenes()
    if not scenes:
        send_message(chat_id, "아직 저장된 씬이 없어.")
        return

    lines = ["[현재 씬 목록]"]
    for s in scenes:
        n = s.get("scene_number", "?")
        text = (s.get("text", "") or "").replace("\n", " ").strip()
        preview = text[:60] + ("..." if len(text) > 60 else "")
        lines.append(f"{n}씬 - {preview}")

    send_message(chat_id, "\n".join(lines))


def cmd_rewrite(chat_id: int, start_scene: int):
    scenes = get_scenes()
    kept = [s for s in scenes if s.get("scene_number", 0) < start_scene]
    set_scenes(kept)
    send_message(chat_id, f"{start_scene}씬부터 다시 쓰도록 정리했어. 이제 /쓰기 또는 /이어쓰기 해줘!")


def cmd_delete_range(chat_id: int, start_scene: int, end_scene: int):
    scenes = get_scenes()
    kept = [
        s for s in scenes
        if not (start_scene <= s.get("scene_number", 0) <= end_scene)
    ]
    set_scenes(kept)
    send_message(chat_id, f"{start_scene}씬부터 {end_scene}씬까지 삭제했어. 번호도 다시 정리했어.")


def cmd_insert_after(chat_id: int, scene_number: int, text: str, note: str = "", duration: int = 5):
    scenes = get_scenes()

    if scene_number < 0 or scene_number > len(scenes):
        send_message(chat_id, f"넣을 위치를 찾을 수 없어. 현재 씬 수: {len(scenes)}")
        return

    history = build_story_history(scenes[:scene_number])

    user_input = text.strip()
    if note:
        user_input += f"\n\n[참고사항]\n{note}"

    prompt = f"""
너는 영화 시나리오 작가다.

아래 기존 이야기 흐름 뒤에 자연스럽게 들어갈
새 씬 1개를 작성해라.

규칙:
- 삽입씬처럼 어색하지 않게 자연스러울 것
- 장면이 눈에 보이듯 쓸 것
- 필요하면 대사 포함
- 결과에는 씬 본문만 출력
- 반드시 한국어(한글)로 작성할 것

[이전 흐름]
{history}

[삽입 요청]
{user_input}
""".strip()

    new_scene_text = call_writer_model(prompt).strip()

    new_scene = {
        "scene_number": scene_number + 1,
        "text": new_scene_text
    }

    scenes.insert(scene_number, new_scene)
    set_scenes(scenes)

    send_message(chat_id, f"{scene_number + 1}씬 위치에 새 씬을 넣었어.\n\n{new_scene_text}")


def cmd_compress_range(chat_id: int, start_scene: int, end_scene: int, note: str = ""):
    scenes = get_scenes()
    selected = [
        s for s in scenes
        if start_scene <= s.get("scene_number", 0) <= end_scene
    ]

    if not selected:
        send_message(chat_id, "압축할 씬 구간을 찾을 수 없어.")
        return

    source_text = "\n\n".join(f"[{s['scene_number']}씬]\n{s['text']}" for s in selected)

    prompt = f"""
너는 영화 시나리오 편집자다.

아래 여러 씬을 하나의 더 짧고 응축된 씬으로 압축해라.

규칙:
- 핵심 흐름은 유지
- 군더더기는 줄이기
- 감정과 의미는 살아 있게
- 결과는 "씬 본문 1개"만 출력
- 출력 언어: 한국어

[추가 지시]
{note if note else "없음"}

[원본 씬들]
{source_text}
""".strip()

    compressed_text = call_writer_model(prompt).strip()

    kept_before = [s for s in scenes if s.get("scene_number", 0) < start_scene]
    kept_after = [s for s in scenes if s.get("scene_number", 0) > end_scene]

    new_scene = {
        "scene_number": start_scene,
        "text": compressed_text
    }

    new_scenes = kept_before + [new_scene] + kept_after
    set_scenes(new_scenes)

    send_message(chat_id, f"{start_scene}~{end_scene}씬을 압축했어.\n\n{compressed_text}")


def cmd_expand_scene(chat_id: int, scene_number: int, note: str = ""):
    scenes = get_scenes()
    target = next((s for s in scenes if s.get("scene_number") == scene_number), None)

    if not target:
        send_message(chat_id, "확장할 씬을 찾을 수 없어.")
        return

    prompt = f"""
너는 영화 시나리오 작가다.

아래 씬을 더 풍성하고 길게 확장해라.

규칙:
- 같은 장면의 핵심은 유지
- 묘사, 행동, 대사, 감정선을 더 풍부하게
- 불필요하게 다른 장면으로 튀지 말 것
- 결과는 확장된 씬 본문만 출력
- 반드시 한국어(한글)로 작성

[추가 지시]
{note if note else "없음"}

[원본 씬]
[{scene_number}씬]
{target['text']}
""".strip()

    expanded_text = call_writer_model(prompt).strip()
    target["text"] = expanded_text
    set_scenes(scenes)

    send_message(chat_id, f"{scene_number}씬을 확장했어.\n\n{expanded_text}")


def cmd_reset(chat_id: int, silent: bool = False):
    set_scenes([])
    if not silent:
        send_message(chat_id, "모든 씬을 초기화했어. 처음부터 다시 시작!")

def cmd_start(chat_id: int):
    """/start 명령 처리: 기존 서사 여부 확인 후 메뉴 제시"""
    history = scene.core.get_history()
    if history:
        # 동기화: 기존 기록으로부터 임팩트와 기억을 복구
        scene.core.sync_from_history(history)
        
        text = (
            "🎞️ **기존 진행 중인 서사가 발견되었습니다.**\n\n"
            f"현재 서사 임팩트: {scene.core._CUMULATIVE_IMPACT}\n"
            "이전의 이야기를 계속 이어가시겠습니까, 아니면 완전히 새롭게 시작하시겠습니까?"
        )
        buttons = [
            [
                {"text": "🎞️ 이어하기 (Resume)", "callback_data": "resume_yes"},
                {"text": "🆕 새로운 시작 (New Start)", "callback_data": "resume_no"}
            ]
        ]
        send_message_with_buttons(chat_id, text, buttons)
    else:
        # 데이터가 없으면 바로 새로운 시작(경로 선택)으로 진행
        show_path_selection(chat_id)

def show_path_selection(chat_id: int):
    """전문가용 vs 초보자용 갈림길 제시"""
    text = (
        "🚀 **새로운 서사를 위한 첫 발걸음입니다.**\n\n"
        "오너님은 어떤 방식으로 이야기를 구상하고 싶으신가요?"
    )
    buttons = [
        [
            {"text": "🎓 전문가용 (Synopsis 분석)", "callback_data": "path_expert"},
            {"text": "🐥 초보자용 (Setup Wizard)", "callback_data": "path_beginner"}
        ]
    ]
    send_message_with_buttons(chat_id, text, buttons)


# =========================
# 전문가 모드 (시놉시스 분석 및 캔버스 편집)
# =========================
def cmd_synopsis(chat_id: int, text: str):
    """시놉시스를 분석하여 세계관을 자동 구축함"""
    send_message(chat_id, "🔍 시놉시스를 정밀 분석하여 세계관을 구축 중입니다... (전문가 모드)")
    data = wizard.analyze_treatment(text)
    
    if not data:
        send_message(chat_id, "❌ 시놉시스 분석에 실패했습니다. 내용을 조금 더 자세히 적어주세요.")
        return

    # 엔진 초기화 및 데이터 주입
    scene.reset_engine()
    
    story = data.get("story", {})
    lead = data.get("lead")
    supports = data.get("support", [])
    props = data.get("props", [])
    space = data.get("space", "카페")

    # 유저 상태 업데이트
    set_user_state(chat_id, "IDLE", {
        "story": story,
        "lead_character": lead,
        "support_characters": supports,
        "active_props": props,
        "place": space
    })

    # 엔진 상태 동기화
    scene.play_turn(lead=lead, place=space)
    for s in supports: core.add_support_character(s)
    for p in props: core.add_prop(p)

    msg = (
        f"✅ 세계관 구축 완료!\n\n"
        f"🎬 장르: {story.get('genre')}\n"
        f"👤 주연: {lead.get('name')} ({lead.get('occupation')})\n"
        f"👥 조연: {', '.join([s.get('name') for s in supports])}\n"
        f"📍 장소: {space}\n\n"
        f"이제 첫 번째 장면을 시작하시거나, /타임라인 을 확인해 보세요."
    )
    send_message(chat_id, msg)

def cmd_move_scene(chat_id: int, from_no: int, to_no: int):
    """캔버스 편집: 씬의 위치를 이동시킴 (canvas_engine 사용)"""
    scenes = get_scenes()
    new_scenes, success = canvas.move_scene(scenes, from_no, to_no)
    
    if not success:
        send_message(chat_id, "❌ 유효하지 않은 씬 번호입니다.")
        return
    
    set_scenes(new_scenes)
    send_message(chat_id, f"🔄 {from_no}번 씬을 {to_no}번 위치로 이동했습니다. 전체 타임라인이 재조정되었습니다.")

def cmd_swap_scenes(chat_id: int, a_no: int, b_no: int):
    """두 씬의 위치를 서로 바꿈"""
    scenes = get_scenes()
    new_scenes, success = canvas.swap_scenes(scenes, a_no, b_no)
    
    if not success:
        send_message(chat_id, "❌ 유효하지 않은 씬 번호입니다.")
        return
        
    set_scenes(new_scenes)
    send_message(chat_id, f"🔄 {a_no}번 씬과 {b_no}번 씬의 위치를 서로 교환했습니다.")

def cmd_group_scenes(chat_id: int, start_no: int, end_no: int, name: str):
    """씬들을 묶음(Sequence)으로 지정함"""
    scenes = get_scenes()
    new_scenes, success = canvas.group_sequence(scenes, start_no, end_no, name)
    
    if not success:
        send_message(chat_id, "❌ 선택한 범위에 씬이 존재하지 않습니다.")
        return
        
    set_scenes(new_scenes)
    send_message(chat_id, f"📦 {start_no}~{end_no}번 씬을 '{name}' 시퀀스로 묶었습니다.")

def cmd_timeline(chat_id: int):
    """현재 서사의 흐름을 시각적으로 표시 (canvas_engine 기반 지도)"""
    scenes = get_scenes()
    if not scenes:
        send_message(chat_id, "텅 빈 도화지입니다. 스토리를 시작해 주세요.")
        return

    visual_map = canvas.generate_timeline_map(scenes)
    total_min = core.get_total_duration(scenes)
    
    footer = f"\n\n⏱️ [총 예상 상영 시간: {total_min}분]"
    send_message(chat_id, f"📍 [시네마틱 타임라인]\n{visual_map}{footer}")

def cmd_recommend_ideas(chat_id: int):
    """아이디어 뱅크에서 영감 추천"""
    ideas = core.get_random_ideas(3)
    text = "💡 [아이디어 뱅크 추천 영감]\n\n" + "\n".join([f"• {i}" for i in ideas])
    send_message(chat_id, text)

def cmd_edit_scene(chat_id: int, scene_no: int, new_text: str):
    """씬 내용 직접 수정 및 영향 분석"""
    scenes = get_scenes()
    new_scenes, success = canvas.edit_scene_content(scenes, scene_no, new_text)
    
    if not success:
        send_message(chat_id, f"❌ {scene_no}번 씬을 찾을 수 없습니다.")
        return
        
    set_scenes(new_scenes)
    send_message(chat_id, f"✅ {scene_no}번 씬이 수정되었습니다.")
    
    # 영향 분석 (Wisdom Analysis)
    send_message(chat_id, "🧐 수정된 내용이 전체 서사에 미치는 영향을 분석 중입니다...")
    history = build_story_history(new_scenes)
    analysis = wizard.analyze_edit_impact(scene_no, new_text, history)
    send_message(chat_id, f"📝 [편집자 분석]\n\n{analysis}")

def cmd_add_memo(chat_id: int, text: str):
    """창작 대원칙(메모) 추가"""
    core.add_global_note(text)
    send_message(chat_id, f"📌 새로운 창작 원칙이 추가되었습니다: '{text}'\n이제 AI가 이 규칙을 준수하며 이야기를 전개합니다.")

def cmd_sync_story(chat_id: int):
    """현재까지의 서사 흐름 싱크 및 제안"""
    scenes = get_scenes()
    if not scenes:
        send_message(chat_id, "싱크할 서사가 없습니다.")
        return
        
    send_message(chat_id, "🔄 현재 타임라인과 창작 원칙을 동기화하여 향후 방향을 구상 중입니다...")
    history = build_story_history(scenes)
    memos = core.get_global_notes()
    plan = wizard.sync_storyline(history, memos)
    send_message(chat_id, f"💡 [싱크 플랜 제안]\n\n{plan}")

def cmd_set_cinematic(chat_id: int, category: str, value: str):
    """시네마틱 연출 노드 설정"""
    # Validation
    valid = False
    if category == "time": valid = (cards.get_time(value) is not None)
    elif category == "cinematic": valid = (cards.get_cinematic(value) is not None)
    elif category == "music": valid = (cards.get_music(value) is not None)
    elif category == "chronos": valid = (cards.get_chronos(value) is not None)
    elif category == "concept": valid = (cards.get_concept(value) is not None)
    elif category == "universal": valid = (cards.get_universal(value) is not None)
    
    if not valid:
        send_message(chat_id, f"❌ '{value}'은(는) 유효한 {category} 설정이 아닙니다.")
        return
        
    core.set_cinematic_node(category, value)
    
    # Impact for Mood/Concept cards
    impact = None
    if category == "mood": impact = cards.get_mood(value).impact
    elif category == "concept": impact = cards.get_concept(value).impact
    
    if impact:
        core.update_timing(**impact)
        send_message(chat_id, f"🔮 '{category}' 설정이 '{value}'(으)로 변경되었습니다. (서사적 처방 적용)")
    else:
        emoji = "⏰" if category == "time" else "🎥" if category == "cinematic" else "👂" if category == "sense" else "🔥" if category == "element" else "🤝" if category == "relationship" else "👔" if category == "lifestyle" else "🔊" if category == "audio" else "🎵" if category == "music" else "🌌"
        send_message(chat_id, f"{emoji} {category} 설정이 '{value}'(으)로 변경되었습니다.")

def cmd_recommend_cards(chat_id: int):
    """AI가 현재 서사에 어울리는 연출 카드 추천 (추천 사유 포함)"""
    recs = core.get_recommended_cards(5)
    text = "🔬 [AI 시네마틱 처방 및 추천]\n\n"
    for r in recs:
        text += f"• **{r['name']}** ({r['category'].upper()})\n"
        text += f"  └ 💡 {r['reason']}\n\n"
    text += "원하는 카드가 있다면 명령어를 통해 적용해 보세요!"
    send_message(chat_id, text)

def cmd_set_timeline(chat_id: int, mode: str):
    """타로 크로노스 카드: 타임라인 시점 전환"""
    core.set_timeline_mode(mode)
    card_obj = cards.get_chronos(mode.lower() if mode != "PRESENT" else "현재")
    
    if not card_obj:
        color, name, desc = "🟡", "현재", "찰나의 선택"
    else:
        color, name, desc = card_obj.color, card_obj.name, card_obj.description

    text = f"🃏 [타로 크로노스: {name}]\n{color} {desc}\n\n"
    if mode == "PAST":
        text += "다음 장면은 **과거의 기억(Flashback)**으로 생성됩니다."
    elif mode == "FUTURE":
        text += "다음 장면은 **미래의 편린(Vision)**으로 생성됩니다."
    else:
        text += "시점이 **현재**로 복귀했습니다."
    
    send_message(chat_id, text)

def cmd_evaluate_project(chat_id: int):
    """프로젝트 전체 건강 검진 (Doctor Persona)"""
    scenes = get_scenes()
    health = core.analyze_project_health(scenes)
    
    text = f"🩺 [서사 건강 검진 리포트]\n\n"
    text += f"🏠 현재 환 상태: **{health['status']}**\n"
    text += f"📊 서사 건강 점수: **{health['score']}점**\n\n"
    text += f"📝 **의사의 종합 소견**:\n{health['report']}\n"
    
    if health['score'] > 80:
        text += "\n✨ 환자의 상태가 매우 우수합니다. 아름답게 마무리할 준비가 되었습니다."
    
    send_message(chat_id, text)

def cmd_sync_indices(chat_id: int):
    """편집 후 씬 번호를 동기화함"""
    scenes = get_scenes()
    new_scenes = canvas.reorder_scenes(scenes)
    set_scenes(new_scenes)
    send_message(chat_id, "✨ 모든 씬 번호 동기화가 완료되었습니다.")

# =========================
# 서사 수출 (Export) 명령
# =========================
def parse_multi_range(text: str) -> list:
    """기호와 범위를 파싱하여 씬 번호 리스트 반환 (예: 1, 3, 5-7 -> [1, 3, 5, 6, 7])"""
    numbers = []
    text = text.replace(",", " ")
    parts = text.split()
    for p in parts:
        if "-" in p:
            try:
                start, end = map(int, p.split("-"))
                numbers.extend(range(start, end + 1))
            except: pass
        elif p.isdigit():
            numbers.append(int(p))
    return sorted(list(set(numbers)))

def cmd_export(chat_id: int, range_str: str = ""):
    scenes = get_scenes()
    if not scenes:
        send_message(chat_id, "수출할 씬이 없습니다.")
        return

    selected = []
    if not range_str:
        selected = scenes
    else:
        target_nums = parse_multi_range(range_str)
        selected = [s for s in scenes if s.get("scene_number") in target_nums]

    if not selected:
        send_message(chat_id, "선택한 범위에 해당하는 씬이 없습니다.")
        return

    # 유저 세션에서 정보 가져오기 (마법사 결과 데이터)
    user_state = get_user_state(chat_id)
    story_context = user_state["data"].get("story", {})
    lead_char = user_state["data"].get("lead_character")

    # 1. 마크다운 생성
    md_content = exporter.generate_markdown(selected, lead_char, story_context)
    filename = f"story_export_{datetime.now().strftime('%m%d_%H%M')}.md"
    file_path = exporter.save_to_file(md_content, filename)

    # 2. 파일 전송
    send_message(chat_id, f"🎬 시네마틱 서사 수출을 시작합니다... (선택된 씬: {len(selected)}개)")
    send_document(chat_id, file_path, caption="✨ 당신의 이야기가 마크다운 파일로 완성되었습니다.")
def get_scene_text_range(start_scene: int, end_scene: int) -> str:
    scenes = get_scenes()
    selected = [
        s for s in scenes
        if start_scene <= s.get("scene_number", 0) <= end_scene
    ]
    if not selected:
        return ""
    return "\n\n".join(f"[{s['scene_number']}씬]\n{s['text']}" for s in selected)


def get_scene_text_by_numbers(scene_numbers: List[int]) -> str:
    scenes = get_scenes()
    selected = [s for s in scenes if s.get("scene_number") in scene_numbers]
    selected.sort(key=lambda x: scene_numbers.index(x["scene_number"]))
    if not selected:
        return ""
    return "\n\n".join(f"[{s['scene_number']}씬]\n{s['text']}" for s in selected)


def generate_storyboard(scene_text: str, note: str = "") -> str:
    prompt = f"""
너는 영화 콘티 작가다.

아래 씬을 “촬영용 스토리보드”로 변환해라.

형식:

[컷 1]
- 카메라: (샷 종류)
- 화면: (보이는 장면)
- 행동: (인물 행동)
- 대사: (있으면)
- 분위기: (조명, 감정)

[컷 2]
...

규칙:
- 최소 3컷 이상
- 실제 촬영 가능한 구도
- 카메라 움직임 포함
- 장면을 잘게 나눌 것
- 모든 텍스트는 한국어로 작성

[원본 씬]
{scene_text}
""".strip()

    return call_writer_model(prompt).strip()


def generate_shorts(scene_text: str, note: str = "") -> str:
    prompt = f"""
너는 쇼츠/릴스 전문 연출가다.

아래 시나리오를 30초~60초 사이의 강한 임팩트 쇼츠 구성으로 바꿔라.

반드시 포함:
- 짧은 제목
- 시작 1~3초 훅
- 컷별 시간 배분
- 컷별 샷/무빙/감정
- 마지막 여운이나 반전 포인트
- 짧고 강하게

출력은 한국어로.

[추가 연출 지시]
{note if note else "없음"}

[원본 시나리오]
{scene_text}
""".strip()

    return call_writer_model(prompt).strip()


def generate_trailer(scene_text: str, note: str = "") -> str:
    prompt = f"""
너는 영화 예고편 편집 감독이다.

아래 여러 씬을 바탕으로 영화 트레일러 구성을 만들어라.

반드시 포함:
- 트레일러 제목 후보
- 전체 감정 흐름
- 컷 순서 재배치
- 컷별 샷/무빙/분위기
- 예고편용 강한 대사
- 마지막 블랙아웃 또는 후킹 문구

중요:
- 원본 씬 번호가 떨어져 있어도 하나의 예고편처럼 재편집할 것
- 임팩트 있게 만들 것

출력은 한국어로.

[추가 연출 지시]
{note if note else "없음"}

[원본 씬들]
{scene_text}
""".strip()

    return call_writer_model(prompt).strip()


# =========================
# 명령 처리
# =========================
# =========================
# 콜백 및 상태 처리
# =========================
def handle_callback_query(chat_id: int, callback_query_id: str, data: str):
    user_state = get_user_state(chat_id)
    state = user_state["state"]
    current_data = user_state["data"]

    if data == "story_ok" and state == "WIZARD_STORY":
        # 스토리 확정 -> 캐릭터 추천 단계로
        current_data["story"] = current_data["current_rec"]
        set_user_state(chat_id, "WIZARD_CHAR", current_data)
        answer_callback_query(callback_query_id, "스토리가 확정되었습니다!")
        show_char_recommendation(chat_id)

    elif data == "story_pass" and state == "WIZARD_STORY":
        answer_callback_query(callback_query_id, "새로운 스토리를 구상합니다.")
        show_story_recommendation(chat_id)

    elif data == "story_direct" and state == "WIZARD_STORY":
        answer_callback_query(callback_query_id)
        send_message(chat_id, "✍️ 원하시는 스토리의 줄거리를 직접 입력해 주세요.")

    elif data == "char_ok" and state == "WIZARD_CHAR":
        # 캐릭터 확정 -> 게임 시작!
        char = current_data["current_rec"]
        current_data["lead_character"] = char
        set_user_state(chat_id, "IDLE", current_data)
        answer_callback_query(callback_query_id, "캐스팅이 완료되었습니다!")
        
        # 엔진 초기화 및 첫 씬 생성
        scene.reset_engine()
        # 주연 배우 설정 (엔진에 주입)
        scene.play_turn(lead=char)
        
        greeting = (
            f"🎬 모든 준비가 끝났습니다!\n\n"
            f"선택하신 스토리: {current_data['story']['genre']}\n"
            f"주연 배우: {char['name']}\n\n"
            f"이제 이야기를 시작합니다. 첫 번째 상황을 만들려면 /쓰기 또는 내용을 입력해 주세요."
        )
        send_message(chat_id, greeting)

    elif data == "char_pass" and state == "WIZARD_CHAR":
        answer_callback_query(callback_query_id, "다른 배우를 섭외합니다.")
        show_char_recommendation(chat_id)

    elif data == "char_direct" and state == "WIZARD_CHAR":
        # 수동 생성 시작 (첫 번째 단계: 이름)
        answer_callback_query(callback_query_id)
        current_data["lead_character"] = {}
        ask_char_step(chat_id, 0)

    elif data == "story_back":
        answer_callback_query(callback_query_id)
        show_story_recommendation(chat_id)

    elif data.startswith("char_back_"):
        prev_step = int(data.replace("char_back_", ""))
        answer_callback_query(callback_query_id)
        ask_char_step(chat_id, prev_step)

    elif data == "resume_yes":
        answer_callback_query(callback_query_id, "서사를 계속 이어갑니다.")
        set_user_state(chat_id, "IDLE", current_data)
        send_message(chat_id, "✅ 이전 기록이 복구되었습니다. 이제 다음 명령을 입력해 주세요.")

    elif data == "resume_no":
        answer_callback_query(callback_query_id, "새로운 서사를 시작합니다.")
        cmd_reset(chat_id, silent=True)
        show_path_selection(chat_id)

    elif data == "path_expert":
        answer_callback_query(callback_query_id, "전문가 모드로 진입합니다.")
        set_user_state(chat_id, "WIZARD_EXPERT")
        send_message(chat_id, "🎓 **전문가 모드입니다.**\n\n구상하신 시나리오나 트리트먼트를 자유롭게 들려주세요. AI 선생님이 정밀 분석하여 카드 테이블을 구성해 드릴 것입니다.")

    elif data == "path_beginner":
        answer_callback_query(callback_query_id, "초보자 모드로 시작합니다.")
        start_wizard(chat_id)

    elif data.startswith("char_rand_"):
        trait_key = data.replace("char_rand_", "")
        answer_callback_query(callback_query_id, "AI 선생님이 고민 중입니다...")
        
        # modular recommendation 호출
        rec_val = wizard.recommend_trait(trait_key, current_data.get("story", {}), current_data.get("lead_character"))
        send_message(chat_id, f"💡 추천 내용: **{rec_val}**\n\n이 내용을 사용하시겠습니까? 아니면 직접 다시 입력해 주세요.")
        
        # 추천 값을 넣어두고 확인 버튼 제공 (또는 그냥 텍스트로 치라고 유도)
        buttons = [[{"text": "✅ 이대로 사용", "callback_data": f"char_use_{trait_key}_{rec_val}"}]]
        send_message_with_buttons(chat_id, "선택해 주세요:", buttons)

    elif data.startswith("char_use_"):
        # 추천 값 사용 확정
        parts = data.split("_")
        trait_key = parts[2]
        val = "_".join(parts[3:])
        answer_callback_query(callback_query_id, "반영되었습니다!")
        
        current_data["lead_character"][trait_key] = val
        step_index = current_data.get("wizard_step", 0)
        ask_char_step(chat_id, step_index + 1)

    elif data.startswith("edit_"):
        trait_key = data.replace("edit_", "")
        steps = ["name", "age", "gender", "occupation", "personality"]
        if trait_key in steps:
            answer_callback_query(callback_query_id)
            ask_char_step(chat_id, steps.index(trait_key))

    elif data == "char_final_ok" and state == "WIZARD_CHAR_REVIEW":
        char = current_data["lead_character"]
        set_user_state(chat_id, "IDLE", current_data)
        answer_callback_query(callback_query_id, "캐스팅이 최종 확정되었습니다!")
        
        scene.reset_engine()
        scene.play_turn(lead=char)
        
        greeting = (
            f"🎬 모든 준비가 끝났습니다!\n\n"
            f"선택하신 스토리: {current_data['story']['genre']}\n"
            f"주연 배우: {char['name']}\n\n"
            f"이제 이야기를 시작합니다. 첫 번째 상황을 만들려면 /쓰기 또는 내용을 입력해 주세요."
        )
        send_message(chat_id, greeting)

    else:
        answer_callback_query(callback_query_id, "알 수 없는 요청입니다.")

def handle_voice(chat_id: int, voice_data: dict):
    """음성 메시지를 처리하여 텍스트로 변환하고 Gemma에게 전달"""
    global VOICE_ENGINE
    
    file_id = voice_data.get("file_id")
    if not file_id:
        return

    send_message(chat_id, "🎙️ 음성을 분석하고 있습니다... 잠시만 기다려 주세요.")
    
    try:
        # 1. 파일 경로 획득
        r = requests.get(f"{API_BASE}/getFile", params={"file_id": file_id})
        r.raise_for_status()
        file_path = r.json().get("result", {}).get("file_path")
        
        # 2. 파일 다운로드
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        voice_file = requests.get(download_url)
        voice_file.raise_for_status()
        
        local_path = f"scratch/voice_{chat_id}_{int(time.time())}.ogg"
        os.makedirs("scratch", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(voice_file.content)
            
        # 3. STT 엔진 로드 (Lazy & Non-blocking)
        global VOICE_ENGINE
        if VOICE_ENGINE is None:
            def load_voice_model():
                global VOICE_ENGINE
                try:
                    # 'base' 모델로 변경하여 로딩 속도 최적화
                    VOICE_ENGINE = VoiceProcessor(model_size="base")
                    logging.info("음성 인식 엔진(Whisper)이 백그라운드에서 성공적으로 로드되었습니다.")
                except Exception as e:
                    logging.error(f"Background voice model loading failed: {e}")

            import threading
            # 중복 실행 방지를 위한 체크
            if not hasattr(load_voice_model, "_started"):
                logging.info("음성 인식 엔진 백그라운드 로드 시작...")
                threading.Thread(target=load_voice_model, daemon=True).start()
                load_voice_model._started = True
            
            send_message(chat_id, "🎙️ 음성 엔진을 백그라운드에서 준비 중입니다. 잠시만 기다려 주신 후 다시 메시지를 보내주세요.")
            return
            
        # 4. 음성 인식 및 의도 해석 통합 태스크 (전체 비동기화)
        def voice_processing_task():
            global VOICE_ENGINE, GEMMA_BRIDGE
            try:
                # STT 수행
                prompt = "Antigravity, 안티그라비티, /쓰기, /목록, /타임라인, /싱크, 시놉시스, 서사, 씬, 캐릭터"
                transcribed_text = VOICE_ENGINE.transcribe(local_path, language="ko", initial_prompt=prompt)
                logging.info(f"VOICE-STT: {transcribed_text}")
                
                if not transcribed_text or transcribed_text.startswith("[Error]"):
                    send_message(chat_id, f"❌ 음성 인식에 실패했습니다: {transcribed_text}")
                    return

                send_message(chat_id, f"📝 인식 결과: \"{transcribed_text}\"")
                
                # 전역 변수 동기화
                global CURRENT_USER_INPUT
                CURRENT_USER_INPUT = transcribed_text

                # AI 판단 수행
                if GEMMA_BRIDGE is None:
                    logging.info("음성 해석을 위해 AI 두뇌(GemmaBridge)를 초기화합니다...")
                    GEMMA_BRIDGE = GemmaBridge()

                interpretation = asyncio.run(GEMMA_BRIDGE.interpret_voice_command(transcribed_text))
                logging.info(f"GEMMA-INTENT: {interpretation}")
                
                # 결과 처리
                if interpretation.startswith("/"):
                    send_message(chat_id, f"🤖 명령 실행: {interpretation}")
                    process_update({"message": {"chat": {"id": chat_id}, "text": interpretation}})
                else:
                    send_message(chat_id, f"💬 Antigravity: {interpretation}")
                
            except Exception as e:
                logging.error(f"Voice Processing Task failed: {e}")
                send_message(chat_id, "⚠️ 음성 처리 중 오류가 발생했습니다.")
            finally:
                # 7. 임시 파일 정리
                if os.path.exists(local_path):
                    os.remove(local_path)

        import threading
        threading.Thread(target=voice_processing_task, daemon=True).start()
            
        # 7. 정리
        if os.path.exists(local_path):
            os.remove(local_path)
            
    except Exception as e:
        logging.exception("Voice handling failed")
        send_message(chat_id, f"🚨 음성 처리 중 오류가 발생했습니다: {e}")

def process_update(update: Dict[str, Any]) -> None:
    # 1. 콜백 쿼리 처리 (버튼 클릭)
    callback_query = update.get("callback_query")
    if callback_query:
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        data = callback_query.get("data")
        query_id = callback_query.get("id")
        if chat_id and data:
            handle_callback_query(chat_id, query_id, data)
        return

    # 2. 일반 메시지 처리
    message = update.get("message") or {}
    if not message: return

    chat_id = message.get("chat", {}).get("id")
    
    # 음성 메시지 감지
    voice = message.get("voice")
    if voice and chat_id:
        handle_voice(chat_id, voice)
        return

    text = (message.get("text", "") or "").strip()
    if not chat_id or not text: return
    
    global CURRENT_USER_INPUT
    CURRENT_USER_INPUT = text # 전역 트리거 갱신

    user_state = get_user_state(chat_id)
    state = user_state["state"]

    logging.info(f"📩 [{state}] {chat_id}: {text}")

    try:
        # 전문가 시놉시스 직접 입력 처리
        if state == "WIZARD_EXPERT" and not text.startswith("/"):
            set_user_state(chat_id, "IDLE") # 상태 해제 후 분석
            cmd_synopsis(chat_id, text)
            return

        # 마법사 도중 직접 입력 처리
        if state == "WIZARD_STORY" and not text.startswith("/"):
            user_state["data"]["story"] = {"genre": "사용자 정의", "plot": text, "reason": "직접 입력"}
            set_user_state(chat_id, "WIZARD_CHAR", user_state["data"])
            send_message(chat_id, "✅ 스토리가 직접 입력되었습니다. 다음은 캐릭터 설정입니다.")
            show_char_recommendation(chat_id)
            return

        # 캐릭터 수동 단계별 매칭
        char_steps = {
            "WIZARD_CHAR_NAME": "name",
            "WIZARD_CHAR_AGE": "age",
            "WIZARD_CHAR_GENDER": "gender",
            "WIZARD_CHAR_OCCUPATION": "occupation",
            "WIZARD_CHAR_PERSONALITY": "personality"
        }
        
        if state in char_steps and not text.startswith("/"):
            trait_key = char_steps[state]
            if "lead_character" not in user_state["data"]:
                user_state["data"]["lead_character"] = {}
            
            user_state["data"]["lead_character"][trait_key] = text
            step_idx = user_state["data"].get("wizard_step", 0)
            
            # 다음 단계로
            ask_char_step(chat_id, step_idx + 1)
            return

        if state == "WIZARD_CHAR_REVIEW" and not text.startswith("/"):
            send_message(chat_id, "💡 버튼을 눌러 수정하거나 확정해 주세요. 직접 채팅 입력은 무시됩니다.")
            return

        # 공통 명령어
        if text == "/start" or text == "/초기화":
            cmd_start(chat_id)
            return

        if text.startswith("/다시쓰기"):
            parts = text.split()
            if len(parts) != 2 or not parts[1].isdigit():
                send_message(chat_id, "사용법: /다시쓰기 35")
                return

            start_scene = int(parts[1])
            if start_scene < 1:
                send_message(chat_id, "씬 번호는 1 이상이어야 해.")
                return

            cmd_rewrite(chat_id, start_scene)
            return

        if text.startswith("/삭제"):
            parsed = parse_range_command(text)
            if not parsed:
                send_message(chat_id, "사용법: /삭제 35 40")
                return

            start_scene, end_scene = parsed
            cmd_delete_range(chat_id, start_scene, end_scene)
            return

        if text.startswith("/쓰기") or text.startswith("/이어쓰기"):
            if text.startswith("/쓰기"):
                raw_body = text[len("/쓰기"):].strip()
            else:
                raw_body = text[len("/이어쓰기"):].strip()

            if not raw_body:
                send_message(chat_id, "사용법: /쓰기 내용\n예: /쓰기 카페에서 재회한다 (잔잔하게)")
                return

            main_text, note = parse_text_and_note(raw_body)
            handle_scene(chat_id, main_text, note)
            return

        if text == "/목록":
            cmd_list_scenes(chat_id)
            return

        if text.startswith("/넣기"):
            command_part, note = split_command_and_note(text)
            parts = command_part.split(maxsplit=2)
            if len(parts) < 3 or not parts[1].isdigit():
                send_message(chat_id, "사용법: /넣기 3 제주도 바닷가에 돌고래가 나타난다 (신비롭게)")
                return
            scene_number = int(parts[1])
            insert_text = parts[2].strip()
            if not insert_text:
                send_message(chat_id, "넣을 내용을 같이 적어줘.")
                return
            
            duration, clean_input = parse_duration(insert_text)
            cmd_insert_after(chat_id, scene_number, clean_input, note, duration=duration)
            return

        if text.startswith("/압축"):
            command_part, note = split_command_and_note(text)
            parsed = parse_range_command(command_part)

            if not parsed:
                send_message(chat_id, "사용법: /압축 10 15 (빠르게)")
                return

            start_scene, end_scene = parsed
            cmd_compress_range(chat_id, start_scene, end_scene, note)
            return

        if text.startswith("/확장"):
            command_part, note = split_command_and_note(text)
            parts = command_part.split()

            if len(parts) != 2 or not parts[1].isdigit():
                send_message(chat_id, "사용법: /확장 8 (감정 깊게)")
                return

            scene_number = int(parts[1])
            cmd_expand_scene(chat_id, scene_number, note)
            return

        if text.startswith("/영상화"):
            command_part, note = split_command_and_note(text)
            parts = command_part.split()

            if len(parts) < 2:
                send_message(chat_id, "사용법: /영상화 10 또는 /영상화 10 12")
                return

            if len(parts) == 2 and parts[1].isdigit():
                start_scene = int(parts[1])
                end_scene = start_scene
            elif len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                start_scene = int(parts[1])
                end_scene = int(parts[2])
            else:
                send_message(chat_id, "사용법: /영상화 10 또는 /영상화 10 12")
                return

            scene_text = get_scene_text_range(start_scene, end_scene)
            if not scene_text:
                send_message(chat_id, "해당 씬을 찾을 수 없어.")
                return

            result = generate_storyboard(scene_text, note)
            send_message(chat_id, f"[영상화 결과]\n\n{result}")
            return

        if text.startswith("/쇼츠화"):
            command_part, note = split_command_and_note(text)
            parts = command_part.split()

            if len(parts) < 2:
                send_message(chat_id, "사용법: /쇼츠화 12 또는 /쇼츠화 10 12")
                return

            if len(parts) == 2 and parts[1].isdigit():
                start_scene = int(parts[1])
                end_scene = start_scene
            elif len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                start_scene = int(parts[1])
                end_scene = int(parts[2])
            else:
                send_message(chat_id, "사용법: /쇼츠화 12 또는 /쇼츠화 10 12")
                return

            scene_text = get_scene_text_range(start_scene, end_scene)
            if not scene_text:
                send_message(chat_id, "해당 씬을 찾을 수 없어.")
                return

            result = generate_shorts(scene_text, note)
            send_message(chat_id, f"[쇼츠화 결과]\n\n{result}")
            return

        if text.startswith("/트레일러"):
            command_part, note = split_command_and_note(text)
            parts = command_part.split()

            if len(parts) < 2:
                send_message(chat_id, "사용법: /트레일러 8 50 70")
                return

            scene_numbers = []
            for p in parts[1:]:
                if not p.isdigit():
                    send_message(chat_id, "사용법: /트레일러 8 50 70")
                    return
                scene_numbers.append(int(p))

            scene_text = get_scene_text_by_numbers(scene_numbers)
            if not scene_text:
                send_message(chat_id, "해당 씬들을 찾을 수 없어.")
                return

            result = generate_trailer(scene_text, note)
            send_message(chat_id, f"[트레일러 결과]\n\n{result}")
            return

        if text.startswith("/수출") or text.startswith("/export") or text.startswith("/다운로드"):
            range_str = ""
            if text.startswith("/export"): range_str = text[len("/export"):].strip()
            elif text.startswith("/다운로드"): range_str = text[len("/다운로드"):].strip()
            elif text.startswith("/수출"): range_str = text[len("/수출"):].strip()
            cmd_export(chat_id, range_str)
            return

        if text.startswith("/시놉시스"):
            synopsis_text = text[len("/시놉시스"):].strip()
            if not synopsis_text:
                send_message(chat_id, "사용법: /시놉시스 [이야기 줄거리...]")
                return
            cmd_synopsis(chat_id, synopsis_text)
            return

        if text.startswith("/이동"):
            parts = text.split()
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                send_message(chat_id, "사용법: /이동 [현재번호] [목표번호]")
                return
            cmd_move_scene(chat_id, int(parts[1]), int(parts[2]))
            return

        if text.startswith("/바꾸기"):
            parts = text.split()
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                send_message(chat_id, "사용법: /바꾸기 [A번] [B번]")
                return
            cmd_swap_scenes(chat_id, int(parts[1]), int(parts[2]))
            return

        if text.startswith("/묶기"):
            parts = text.split(maxsplit=3)
            if len(parts) < 4 or not parts[1].isdigit() or not parts[2].isdigit():
                send_message(chat_id, "사용법: /묶기 [시작] [종료] [이름]")
                return
            cmd_group_scenes(chat_id, int(parts[1]), int(parts[2]), parts[3].strip())
            return

        if text.startswith("/수정"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3 or not parts[1].isdigit():
                send_message(chat_id, "사용법: /수정 [번호] [새 내용]")
                return
            cmd_edit_scene(chat_id, int(parts[1]), parts[2].strip())
            return

        if text.startswith("/메모"):
            memo_text = text[len("/메모"):].strip()
            if not memo_text:
                send_message(chat_id, "사용법: /메모 [추가할 창작 원칙]")
                return
            cmd_add_memo(chat_id, memo_text)
            return

        if text == "/싱크":
            cmd_sync_story(chat_id)
            return

        if text == "/타임라인":
            cmd_timeline(chat_id)
            return

        if text == "/추천":
            cmd_recommend_ideas(chat_id)
            return

        if text.startswith("/시간"):
            val = text[len("/시간"):].strip()
            if not val: send_message(chat_id, "사용법: /시간 [낮/밤/새벽/황혼]"); return
            cmd_set_cinematic(chat_id, "time", val)
            return

        if text.startswith("/카메라"):
            val = text[len("/카메라"):].strip()
            if not val: send_message(chat_id, "사용법: /카메라 [클로즈업/롱샷/로우앵글 등]"); return
            cmd_set_cinematic(chat_id, "cinematic", val)
            return

        if text.startswith("/분위기"):
            val = text[len("/분위기"):].strip()
            if not val: send_message(chat_id, "사용법: /분위기 [공포/희망/용맹/비굴/슬픔]"); return
            cmd_set_cinematic(chat_id, "mood", val)
            return

        if text.startswith("/감각"):
            val = text[len("/감각"):].strip()
            if not val: send_message(chat_id, "사용법: /감각 [시각/청각/후각/촉각/미각]"); return
            cmd_set_cinematic(chat_id, "sense", val)
            return

        if text.startswith("/속성"):
            val = text[len("/속성"):].strip()
            if not val: send_message(chat_id, "사용법: /속성 [불/물/흙/바람/번개]"); return
            cmd_set_cinematic(chat_id, "element", val)
            return

        if text.startswith("/관계"):
            val = text[len("/관계"):].strip()
            if not val: send_message(chat_id, "사용법: /관계 [사랑/이별/우정/배신/경쟁]"); return
            cmd_set_cinematic(chat_id, "relationship", val)
            return

        if text.startswith("/의상"):
            val = text[len("/의상"):].strip()
            if not val: send_message(chat_id, "사용법: /의상 [블랙수트/화려한드레스/빈티지코트/짙은분장 등]"); return
            cmd_set_cinematic(chat_id, "lifestyle", val)
            return

        if text.startswith("/음식"):
            val = text[len("/음식"):].strip()
            if not val: send_message(chat_id, "사용법: /음식 [따뜻한스프/비린스테이크 등]"); return
            cmd_set_cinematic(chat_id, "lifestyle", val)
            return

        if text.startswith("/효과음"):
            val = text[len("/효과음"):].strip()
            if not val: send_message(chat_id, "사용법: /효과음 [심장박동/빗소리/금속마찰 등]"); return
            cmd_set_cinematic(chat_id, "audio", val)
            return

        if text.startswith("/음악"):
            val = text[len("/음악"):].strip()
            if not val: send_message(chat_id, "사용법: /음악 [시네마천국/느와르재즈/심포닉긴장/미니멀적막]"); return
            cmd_set_cinematic(chat_id, "music", val)
            return

        if text == "/추천카드":
            cmd_recommend_cards(chat_id)
            return

        if text.startswith("/개념"):
            val = text[len("/개념"):].strip()
            if not val: send_message(chat_id, "사용법: /개념 [이름]"); return
            cmd_set_cinematic(chat_id, "concept", val)
            return

        if text.startswith("/우주"):
            val = text[len("/우주"):].strip()
            if not val: send_message(chat_id, "사용법: /우주 [이름]"); return
            cmd_set_cinematic(chat_id, "universal", val)
            return

        if text == "/과거":
            cmd_set_timeline(chat_id, "PAST")
            return
        
        if text == "/현재":
            cmd_set_timeline(chat_id, "PRESENT")
            return
        
        if text.startswith("/미래"):
            cmd_set_timeline(chat_id, "FUTURE")
            return

        if text == "/평가":
            cmd_evaluate_project(chat_id)
            return

        if text == "/동기화":
            cmd_sync_indices(chat_id)
            return

        if text in ["안녕", "안녕하세요", "hi", "hello"]:
            send_message(
                chat_id,
                "안녕! 😊 나는 스토리 작성 봇이야.\n"
                "스토리를 쓰려면 /쓰기 또는 /이어쓰기 를 써줘.\n"
                "명령어가 궁금하면 /도움말"
            )
            return

        send_message(
            chat_id,
            "무슨 작업을 할지 알려줘 😊\n"
            "예: /쓰기 카페에서 다시 만난다 (설렘 강조)\n"
            "명령어 전체 보기: /도움말"
        )

    except Exception as e:
        logging.exception(f"처리 오류: {e}")
        try:
            send_message(chat_id, f"오류 발생: {e}")
        except Exception:
            pass


# =========================
# 메인 루프
# =========================
def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 환경변수가 없습니다.")

    if not os.path.exists(SCENES_FILE):
        save_json(SCENES_FILE, [])

    logging.info("봇 서버 시작됨 (Bot Server Started)")
    print("\n" + "="*50)
    print(" [시네마틱 엔진 V2] 텔레그램 서버 가동 중...")
    print("    - 파트너가 오너님의 명령을 기다리고 있습니다.")
    print("    - 스마트폰 텔레그램에서 메시지를 보내보세요!")
    print("="*50 + "\n")

    last_update_id = None

    while True:
        try:
            updates = get_updates(None if last_update_id is None else last_update_id + 1)

            for upd in updates:
                last_update_id = upd["update_id"]
                process_update(upd)

        except Exception as e:
            logging.exception(f"polling error: {e}")
            print(f"[DEBUG] polling error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        logging.exception(f"FATAL ERROR on startup: {e}")
        traceback.print_exc()
        sys.exit(1)
