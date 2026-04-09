import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
STORE_FILE = BASE_DIR / "projects_store.json"
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip()
USE_OLLAMA = os.getenv("USE_OLLAMA", "1").strip() == "1"

META_ORDER = ["genre", "theme", "intent", "synopsis", "title"]
META_LABELS = {
    "genre": "장르",
    "theme": "주제",
    "intent": "작품 의도",
    "synopsis": "시놉시스",
    "title": "제목",
}

TRAIT_ORDER = ["role", "relation", "age", "personality", "appearance", "name"]
TRAIT_LABELS = {
    "role": "역할",
    "relation": "관계",
    "age": "나이",
    "personality": "성격",
    "appearance": "외형",
    "name": "이름",
}


class CreateProjectRequest(BaseModel):
    mode: str = "guide"


class RenameProjectRequest(BaseModel):
    title: str


class TokenRequest(BaseModel):
    view_token: str


class ValueRequest(BaseModel):
    view_token: str
    value: str | int | float | None = ""


class StartCharacterRequest(BaseModel):
    role_type: str = "lead"


class FinalizeCharacterRequest(BaseModel):
    view_token: str


class StartSceneRequest(BaseModel):
    location: str
    summary: str


class ToggleNewCharacterRequest(BaseModel):
    allow_new_character: bool


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def safe_str(v: Any) -> str:
    return "" if v is None else str(v).strip()


def new_token() -> str:
    return uuid.uuid4().hex[:12]


def safe_filename(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", safe_str(text)).strip() or "story"


def clean_response(text: str) -> str:
    text = safe_str(text)
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    if "Thinking..." in text and "...done thinking." in text:
        text = text.split("...done thinking.", 1)[-1].strip()
    return text


def extract_json(text: str) -> dict:
    text = safe_str(text)
    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        return json.loads(m.group(1))

    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        return json.loads(m.group(1))

    raise ValueError("JSON 파싱 실패")


def generate_json(prompt: str, fallback: dict, num_predict: int = 700) -> dict:
    if not USE_OLLAMA or not OLLAMA_MODEL:
        return fallback

    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.82,
                    "top_p": 0.92,
                    "repeat_penalty": 1.08,
                    "num_predict": num_predict,
                },
            },
            timeout=120,
        )
        res.raise_for_status()
        raw = clean_response(res.json().get("response", ""))
        parsed = extract_json(raw)
        return parsed if isinstance(parsed, dict) else fallback
    except Exception:
        return fallback


def pick_non_duplicate(candidates: List[dict], seen_values: List[str], value_key: str = "value") -> dict:
    seen = {safe_str(x) for x in seen_values if safe_str(x)}
    for item in candidates:
        if safe_str(item.get(value_key)) not in seen:
            return item
    return candidates[0]


def load_store() -> Dict[str, dict]:
    if not STORE_FILE.exists():
        return {}
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


PROJECTS: Dict[str, dict] = load_store()


def save_store() -> None:
    STORE_FILE.write_text(json.dumps(PROJECTS, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_project_shape(project: dict) -> None:
    project.setdefault("project_id", str(uuid.uuid4()))
    project.setdefault("mode", "guide")
    project.setdefault("genre", "")
    project.setdefault("theme", "")
    project.setdefault("intent", "")
    project.setdefault("synopsis", "")
    project.setdefault("title", "")
    project.setdefault("meta_pending", None)
    project.setdefault("meta_seen", {field: [] for field in META_ORDER})
    project.setdefault("scene_counter", 0)
    project.setdefault("characters", [])
    project.setdefault("current_character_id", "")
    project.setdefault("draft_scene", None)
    project.setdefault("scene_seed", None)
    project.setdefault("scene_seed_seen", [])
    project.setdefault("saved_scenes", [])
    project.setdefault("allow_new_character", False)
    project.setdefault("active_view", {"view_token": "", "stage": "menu", "target_id": ""})
    project.setdefault("created_at", now_iso())
    project.setdefault("updated_at", now_iso())


def touch_project(project: dict) -> None:
    project["updated_at"] = now_iso()


def get_project(project_id: str) -> dict:
    project = PROJECTS.get(project_id)
    if not project:
        raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")
    ensure_project_shape(project)
    return project


def set_active_view(project: dict, stage: str, target_id: str = "") -> str:
    token = new_token()
    project["active_view"] = {"view_token": token, "stage": stage, "target_id": target_id}
    touch_project(project)
    return token


def is_valid_token(project: dict, token: str) -> bool:
    return token == project.get("active_view", {}).get("view_token", "")


def stale_button_error() -> ValueError:
    return ValueError("지나간 단계의 버튼입니다. 현재 화면 기준으로 다시 눌러 주세요.")


def character_by_id(project: dict, character_id: str) -> Optional[dict]:
    for ch in project.get("characters", []):
        if ch["character_id"] == character_id:
            return ch
    return None


def current_trait_key(ch: dict) -> Optional[str]:
    traits = ch.get("traits", {})
    for key in TRAIT_ORDER:
        if not safe_str(traits.get(key)):
            return key
    return None


def current_character_names(project: dict) -> List[str]:
    result: List[str] = []
    for ch in project.get("characters", []):
        name = safe_str(ch.get("traits", {}).get("name"))
        if name:
            result.append(name)
    return result


SYSTEM_RULES = """
너는 스토리 설계 파트너 AI다.

[절대 규칙]
- 항상 추천은 1개만 한다.
- 반드시 "추천 / 이유 / 기대 효과"를 분리해서 준다.
- 이유 없는 추천은 금지한다.
- 현재까지 확정된 정보만 근거로 삼는다.
- 현재 인물 중심으로 설계한다.
- 새 인물은 허용된 경우가 아니면 만들지 않는다.
- 감정 / 관계 / 갈등 중심으로 설계한다.
- 반드시 한국어만 사용한다.
- 반드시 JSON만 출력한다.

출력 형식:
{
  "value": "추천 내용",
  "reason": "왜 이렇게 추천하는지",
  "expected_effect": "이 추천을 고르면 어떤 효과가 있는지"
}
""".strip()

META_FALLBACKS = {
    "genre": [
        {"value": "감정 멜로", "reason": "감정선과 관계를 초반부터 쌓기 좋습니다.", "expected_effect": "몰입감 있는 출발이 가능합니다."},
        {"value": "현실 로맨스 드라마", "reason": "인물 간 거리감과 변화가 잘 드러납니다.", "expected_effect": "장면과 대사가 현실적으로 살아납니다."},
    ],
    "theme": [
        {"value": "재회 뒤의 어색함과 미련", "reason": "관계 중심 장면을 만들기 좋습니다.", "expected_effect": "감정선이 선명해집니다."},
        {"value": "끝난 줄 알았던 관계의 잔여 감정", "reason": "겉과 속의 감정 차이를 다루기 좋습니다.", "expected_effect": "긴장과 여운이 생깁니다."},
    ],
    "intent": [
        {"value": "인물의 감정을 천천히 쌓아가며 긴장을 만드는 이야기", "reason": "급한 사건보다 감정 누적에 강합니다.", "expected_effect": "독자가 정서에 깊게 들어갑니다."},
        {"value": "말하지 못한 감정을 장면마다 조금씩 드러내는 이야기", "reason": "장면 누적형 구조와 잘 맞습니다.", "expected_effect": "이어쓰기 동력이 강해집니다."},
    ],
    "synopsis": [
        {
            "value": "오랜 시간 연락이 끊겼던 두 사람이 비 오는 밤 우연히 다시 마주친다. 처음에는 어색한 인사와 짧은 대화로 시작되지만, 끝내 말하지 못했던 감정과 오해가 조금씩 드러난다. 서로는 많이 변했다고 느끼면서도 아직 끝나지 않은 감정이 남아 있음을 부정하지 못한다. 이 재회는 오래 묻어둔 후회와 미련을 다시 끌어올리는 사건이 된다.",
            "reason": "장르와 주제, 의도를 반영해 감정 중심 구조로 정리했습니다.",
            "expected_effect": "캐릭터와 장면 추천이 더 구체적으로 이어집니다.",
        }
    ],
    "title": [
        {"value": "비 오는 날, 다시", "reason": "재회와 여운을 짧게 담기 좋습니다.", "expected_effect": "정서가 선명하게 각인됩니다."},
        {"value": "끝나지 않은 거리", "reason": "관계의 어긋남과 감정의 잔여를 담습니다.", "expected_effect": "작품의 중심 정서를 상징합니다."},
    ],
}

CHAR_FALLBACKS = {
    "role": [
        {"value": "이야기의 감정선을 끌고 가는 중심 인물", "reason": "관계와 감정이 중심인 구조에 적합합니다.", "expected_effect": "장면의 중심축이 생깁니다."},
        {"value": "관계를 흔드는 선택의 중심에 선 인물", "reason": "갈등의 무게를 담당하기 좋습니다.", "expected_effect": "이야기 밀도가 높아집니다."},
    ],
    "relation": [
        {"value": "상대 주인공과 과거에 가까웠지만 지금은 어색해진 관계", "reason": "긴장과 미련을 동시에 만들 수 있습니다.", "expected_effect": "대사와 시선에 힘이 생깁니다."},
        {"value": "한때 가장 편했지만 지금은 말을 고르며 대해야 하는 관계", "reason": "편안함과 거리감이 공존합니다.", "expected_effect": "미묘한 감정 변화가 잘 드러납니다."},
    ],
    "age": [
        {"value": "30", "reason": "감정과 현실의 무게가 함께 느껴집니다.", "expected_effect": "선택의 현실감이 살아납니다."},
        {"value": "29", "reason": "흔들리는 시기를 담기 좋습니다.", "expected_effect": "생활감 있는 캐릭터가 됩니다."},
    ],
    "personality": [
        {"value": "겉으로는 차분하지만 속으로는 감정이 깊은 성격", "reason": "겉과 속의 차이가 장면 밀도를 높입니다.", "expected_effect": "침묵과 시선에도 감정이 실립니다."},
        {"value": "신중해 보이지만 익숙한 사람 앞에서는 쉽게 흔들리는 성격", "reason": "관계 장면에서 변화가 잘 드러납니다.", "expected_effect": "장면 긴장감이 살아납니다."},
    ],
    "appearance": [
        {"value": "단정한 인상에 움직임이 깔끔한 사람", "reason": "현재 흐름에 자연스럽게 어울립니다.", "expected_effect": "외형과 행동의 결이 맞아집니다."},
        {"value": "무심해 보이지만 가까이 보면 피곤한 기색이 남아 있는 인상", "reason": "겉과 속의 온도 차를 보여줍니다.", "expected_effect": "시각 묘사에 깊이가 생깁니다."},
    ],
    "name": [
        {"value": "이하늘", "reason": "차분하면서 여백이 느껴지는 이름입니다.", "expected_effect": "캐릭터가 빨리 각인됩니다."},
        {"value": "서윤재", "reason": "현실감과 정서가 함께 느껴집니다.", "expected_effect": "톤과 자연스럽게 맞습니다."},
    ],
}

SCENE_SEED_FALLBACKS = [
    {
        "location": "비 오는 골목길",
        "summary": "오랜만에 마주친 두 사람이 쉽게 말을 꺼내지 못한 채 서로의 분위기를 살핀다.",
        "reason": "감정과 거리감을 자연스럽게 드러내기 좋습니다.",
        "expected_effect": "정서와 긴장을 한 번에 잡을 수 있습니다.",
    },
    {
        "location": "늦은 밤 카페 앞",
        "summary": "헤어지기 직전의 망설임 속에서 한 사람이 먼저 말을 붙일 타이밍을 재고 있다.",
        "reason": "멈춰 서서 감정을 드러내기 좋은 전환 지점입니다.",
        "expected_effect": "대사 중심 장면으로 이어지기 쉽습니다.",
    },
]

SCENE_RECOMMEND_FALLBACKS = [
    {
        "value": "현재 인물 중 한 사람이 먼저 침묵을 깨고, 지금 가장 피하고 싶은 감정을 건드리는 질문을 던진다.",
        "reason": "현재 장면은 감정선이 중심이라 직접 대화가 강하게 작동합니다.",
        "expected_effect": "관계의 긴장과 다음 갈등이 자연스럽게 열립니다.",
    },
    {
        "value": "한 사람이 아무렇지 않은 척 과거를 언급하지만, 상대의 반응에서 아직 정리되지 않은 감정이 드러난다.",
        "reason": "우회적인 언급이 더 자연스럽게 긴장을 만듭니다.",
        "expected_effect": "대화 속 감정의 결이 더 섬세해집니다.",
    },
]


def build_meta_prompt(project: dict, field: str, seen_values: List[str]) -> str:
    seen_text = ", ".join([x for x in seen_values if x]) or "없음"
    return f"""
{SYSTEM_RULES}

현재 작품 정보:
- 장르: {project.get('genre') or '미정'}
- 주제: {project.get('theme') or '미정'}
- 작품 의도: {project.get('intent') or '미정'}
- 시놉시스: {project.get('synopsis') or '미정'}
- 제목: {project.get('title') or '미정'}

이번 추천 항목:
- {META_LABELS[field]}

추가 지시:
- 아래와 완전히 같은 추천은 피하라: {seen_text}
""".strip()


def build_character_trait_prompt(project: dict, ch: dict, trait_key: str, seen_values: List[str]) -> str:
    existing = "\n".join(
        f"- {TRAIT_LABELS[k]}: {safe_str(v)}"
        for k, v in ch.get("traits", {}).items()
        if safe_str(v)
    ) or "- 아직 확정 없음"
    seen_text = ", ".join([x for x in seen_values if x]) or "없음"

    return f"""
{SYSTEM_RULES}

작품 정보:
- 제목: {project.get('title') or '제목 미정'}
- 장르: {project.get('genre') or '미정'}
- 주제: {project.get('theme') or '미정'}
- 작품 의도: {project.get('intent') or '미정'}
- 시놉시스: {project.get('synopsis') or '미정'}

현재 캐릭터 종류:
- {ch.get('role_type', 'lead')}

지금까지 확정된 캐릭터 정보:
{existing}

이번 추천 항목:
- {TRAIT_LABELS[trait_key]}

추가 지시:
- 아래와 완전히 같은 추천은 피하라: {seen_text}
""".strip()


def build_character_summary_prompt(project: dict, ch: dict) -> str:
    existing = "\n".join(
        f"- {TRAIT_LABELS[k]}: {safe_str(v)}"
        for k, v in ch.get("traits", {}).items()
        if safe_str(v)
    ) or "- 아직 확정 없음"

    return f"""
너는 스토리 설계 파트너 AI다.

작품 정보:
- 제목: {project.get('title') or '제목 미정'}
- 장르: {project.get('genre') or '미정'}
- 주제: {project.get('theme') or '미정'}
- 작품 의도: {project.get('intent') or '미정'}

캐릭터 정보:
{existing}

규칙:
- 4~6문장
- 감정과 관계가 보이게 정리
- 한국어만 사용
- 반드시 JSON만 출력

출력 형식:
{{
  "summary": "정리된 캐릭터 설명"
}}
""".strip()


def build_scene_seed_prompt(project: dict, seen_locations: List[str]) -> str:
    chars = []
    for ch in project.get("characters", []):
        t = ch.get("traits", {})
        name = safe_str(t.get("name"))
        if name:
            chars.append(
                f"- {name}: 역할 {safe_str(t.get('role'))}, 관계 {safe_str(t.get('relation'))}, 성격 {safe_str(t.get('personality'))}"
            )
    chars_text = "\n".join(chars) if chars else "- 확정된 인물 없음"
    seen_text = ", ".join([x for x in seen_locations if x]) or "없음"

    return f"""
너는 스토리 설계 파트너 AI다.

작품 정보:
- 제목: {project.get('title') or '제목 미정'}
- 장르: {project.get('genre') or '미정'}
- 주제: {project.get('theme') or '미정'}
- 작품 의도: {project.get('intent') or '미정'}
- 시놉시스: {project.get('synopsis') or '미정'}

현재 인물:
{chars_text}

규칙:
- 새 장면을 시작하기 좋은 "장소" 1개와 "장면 요약" 1개를 추천한다.
- 현재 인물 중심으로 이어져야 한다.
- 아래와 같은 장소는 피하라: {seen_text}
- 한국어만 사용
- 반드시 JSON만 출력

출력 형식:
{{
  "location": "추천 장소",
  "summary": "그 장소에서 담을 핵심 장면 요약",
  "reason": "왜 이 장소와 요약을 추천하는지",
  "expected_effect": "이 장면을 시작하면 어떤 효과가 있는지"
}}
""".strip()


def build_scene_prompt(project: dict, scene: dict, seen_values: List[str]) -> str:
    char_lines = []
    for ch in project.get("characters", []):
        traits = ch.get("traits", {})
        nm = safe_str(traits.get("name"))
        if nm:
            char_lines.append(
                f"- {nm}: 역할 {safe_str(traits.get('role'))}, 관계 {safe_str(traits.get('relation'))}, 성격 {safe_str(traits.get('personality'))}"
            )
    chars_text = "\n".join(char_lines) if char_lines else "- 확정된 캐릭터 없음"
    accepted = scene.get("accepted_recommendations", [])
    accepted_text = "\n".join(f"- {safe_str(x.get('value'))}" for x in accepted) or "- 아직 없음"
    new_rule = "새 인물 허용 가능" if project.get("allow_new_character", False) else "새 인물 생성 금지, 현재 인물 중심"
    seen_text = ", ".join([x for x in seen_values if x]) or "없음"

    return f"""
{SYSTEM_RULES}

현재 장면:
- 장소 번호: {scene['scene_number']}
- 장소: {scene['location']}
- 장면 요약: {scene['summary']}

현재 인물:
{chars_text}

이미 확정한 장면 전개:
{accepted_text}

작품 정보:
- 제목: {project.get('title') or '제목 미정'}
- 장르: {project.get('genre') or '미정'}
- 주제: {project.get('theme') or '미정'}
- 작품 의도: {project.get('intent') or '미정'}

추가 지시:
- {new_rule}
- 아래와 완전히 같은 추천은 피하라: {seen_text}
""".strip()


def list_projects() -> List[dict]:
    items: List[dict] = []
    for project_id, project in PROJECTS.items():
        ensure_project_shape(project)
        items.append({
            "project_id": project_id,
            "title": project.get("title") or "제목 미정",
            "updated_at": project.get("updated_at", ""),
            "characters_count": len(project.get("characters", [])),
            "saved_scenes_count": len(project.get("saved_scenes", [])),
        })
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items


def create_project(req: CreateProjectRequest) -> dict:
    project_id = str(uuid.uuid4())
    project = {
        "project_id": project_id,
        "mode": req.mode,
        "genre": "",
        "theme": "",
        "intent": "",
        "synopsis": "",
        "title": "",
        "meta_pending": None,
        "meta_seen": {field: [] for field in META_ORDER},
        "scene_counter": 0,
        "characters": [],
        "current_character_id": "",
        "draft_scene": None,
        "scene_seed": None,
        "scene_seed_seen": [],
        "saved_scenes": [],
        "allow_new_character": False,
        "active_view": {"view_token": "", "stage": "menu", "target_id": ""},
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    PROJECTS[project_id] = project
    save_store()
    return project


def rename_project(project_id: str, req: RenameProjectRequest) -> dict:
    p = get_project(project_id)
    p["title"] = safe_str(req.title)
    touch_project(p)
    save_store()
    return p


def delete_project(project_id: str) -> dict:
    if project_id not in PROJECTS:
        raise ValueError("프로젝트를 찾을 수 없습니다.")
    del PROJECTS[project_id]
    save_store()
    return {"deleted": True, "project_id": project_id}


def status(project_id: str) -> dict:
    p = get_project(project_id)
    save_store()
    return p


def _recommend_meta(project: dict, field: str) -> dict:
    seen_values = list(project.get("meta_seen", {}).get(field, []))
    current_value = safe_str(project.get(field))
    if current_value and current_value not in seen_values:
        seen_values.append(current_value)

    fallback = pick_non_duplicate(META_FALLBACKS[field], seen_values, "value")
    rec = generate_json(build_meta_prompt(project, field, seen_values), fallback, 1200 if field == "synopsis" else 500)

    value = safe_str(rec.get("value"))
    if not value or value in seen_values:
        rec = fallback
        value = safe_str(rec.get("value"))

    project.setdefault("meta_seen", {}).setdefault(field, [])
    if value and value not in project["meta_seen"][field]:
        project["meta_seen"][field].append(value)

    token = set_active_view(project, f"meta:{field}")
    project["meta_pending"] = {
        "field": field,
        "label": META_LABELS[field],
        "recommendation": {
            "value": value,
            "reason": safe_str(rec.get("reason")),
            "expected_effect": safe_str(rec.get("expected_effect")),
        },
    }
    touch_project(project)
    save_store()

    return {
        "view_token": token,
        "stage": f"meta:{field}",
        "field": field,
        "label": META_LABELS[field],
        "value": value,
        "reason": safe_str(rec.get("reason")),
        "expected_effect": safe_str(rec.get("expected_effect")),
    }


def recommend_meta(project_id: str, field: str) -> dict:
    if field not in META_ORDER:
        raise ValueError("지원하지 않는 meta 항목입니다.")
    return _recommend_meta(get_project(project_id), field)


def recommend_next_meta(project_id: str, req: TokenRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()
    stage = p["active_view"]["stage"]
    if not stage.startswith("meta:"):
        raise ValueError("지금은 메타 추천 단계가 아닙니다.")
    field = stage.split(":", 1)[1]
    return _recommend_meta(p, field)


def _accept_meta_value(project: dict, field: str, value: str) -> dict:
    project[field] = value
    touch_project(project)

    idx = META_ORDER.index(field)
    if idx < len(META_ORDER) - 1:
        next_field = META_ORDER[idx + 1]
        rec = _recommend_meta(project, next_field)
        return {"done": False, "next_field": next_field, "recommendation": rec}

    set_active_view(project, "menu")
    save_store()
    return {"done": True, "title": project.get("title", "")}


def accept_meta(project_id: str, req: ValueRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()
    stage = p["active_view"]["stage"]
    if not stage.startswith("meta:"):
        raise ValueError("지금은 메타 추천 단계가 아닙니다.")
    field = stage.split(":", 1)[1]
    return _accept_meta_value(p, field, safe_str(req.value))


def direct_meta(project_id: str, req: ValueRequest) -> dict:
    return accept_meta(project_id, req)


def _make_character_recommendation(project: dict, character_id: str, trait_key: Optional[str] = None) -> dict:
    ch = character_by_id(project, character_id)
    if not ch:
        raise ValueError("현재 작업 중인 캐릭터가 없습니다.")

    ch.setdefault("seen_by_trait", {key: [] for key in TRAIT_ORDER})
    key = trait_key or current_trait_key(ch)

    if not key:
        token = set_active_view(project, "character_ready", ch["character_id"])
        save_store()
        return {
            "view_token": token,
            "stage": "character_ready",
            "character_id": ch["character_id"],
            "message": "이 캐릭터 정보가 충분히 쌓였습니다. 이제 하나로 정리하시겠습니까?",
        }

    seen_values = list(ch["seen_by_trait"].get(key, []))
    current_value = safe_str(ch.get("traits", {}).get(key))
    if current_value and current_value not in seen_values:
        seen_values.append(current_value)

    fallback = pick_non_duplicate(CHAR_FALLBACKS[key], seen_values, "value")
    rec = generate_json(build_character_trait_prompt(project, ch, key, seen_values), fallback, 500)

    value = safe_str(rec.get("value"))
    if not value or value in seen_values:
        rec = fallback
        value = safe_str(rec.get("value"))

    ch["seen_by_trait"].setdefault(key, [])
    if value and value not in ch["seen_by_trait"][key]:
        ch["seen_by_trait"][key].append(value)

    token = set_active_view(project, f"char:{key}", ch["character_id"])
    ch["pending_recommendation"] = {
        "value": value,
        "reason": safe_str(rec.get("reason")),
        "expected_effect": safe_str(rec.get("expected_effect")),
    }
    ch["pending_trait"] = key
    touch_project(project)
    save_store()

    return {
        "view_token": token,
        "stage": f"char:{key}",
        "character_id": ch["character_id"],
        "trait_key": key,
        "trait_label": TRAIT_LABELS[key],
        "value": value,
        "reason": safe_str(rec.get("reason")),
        "expected_effect": safe_str(rec.get("expected_effect")),
    }


def start_character(project_id: str, req: StartCharacterRequest) -> dict:
    p = get_project(project_id)
    character_id = uuid.uuid4().hex[:10]
    ch = {
        "character_id": character_id,
        "role_type": req.role_type,
        "traits": {},
        "summary": "",
        "locked": False,
        "pending_recommendation": {},
        "pending_trait": "",
        "seen_by_trait": {key: [] for key in TRAIT_ORDER},
        "created_at": now_iso(),
    }
    p["characters"].append(ch)
    p["current_character_id"] = character_id
    touch_project(p)
    save_store()
    return _make_character_recommendation(p, character_id)


def recommend_next_character_trait(project_id: str, req: TokenRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    stage = p["active_view"]["stage"]
    if stage == "character_ready":
        target_id = p["active_view"]["target_id"]
        ch = character_by_id(p, target_id)
        return _make_character_recommendation(p, target_id, current_trait_key(ch) if ch else None)

    if not stage.startswith("char:"):
        raise ValueError("지금은 캐릭터 추천 단계가 아닙니다.")

    target_id = p["active_view"]["target_id"]
    trait_key = stage.split(":", 1)[1]
    return _make_character_recommendation(p, target_id, trait_key)


def _advance_character(project: dict, ch: dict) -> dict:
    next_key = current_trait_key(ch)
    if not next_key:
        token = set_active_view(project, "character_ready", ch["character_id"])
        save_store()
        return {
            "done": True,
            "ready": True,
            "view_token": token,
            "character_id": ch["character_id"],
            "message": "이 캐릭터 정보가 충분히 쌓였습니다. 이제 하나로 정리하시겠습니까?",
        }

    rec = _make_character_recommendation(project, ch["character_id"], next_key)
    return {"done": False, "recommendation": rec}


def accept_character_trait(project_id: str, req: ValueRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    stage = p["active_view"]["stage"]
    if not stage.startswith("char:"):
        raise ValueError("지금은 캐릭터 추천 단계가 아닙니다.")

    trait_key = stage.split(":", 1)[1]
    ch = character_by_id(p, p["active_view"]["target_id"])
    if not ch:
        raise ValueError("캐릭터를 찾지 못했습니다.")

    ch["traits"][trait_key] = safe_str(req.value)
    touch_project(p)
    save_store()
    return _advance_character(p, ch)


def direct_character_trait(project_id: str, req: ValueRequest) -> dict:
    return accept_character_trait(project_id, req)


def finalize_character(project_id: str, req: FinalizeCharacterRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    if p["active_view"]["stage"] != "character_ready":
        raise ValueError("지금은 캐릭터 정리 단계가 아닙니다.")

    ch = character_by_id(p, p["active_view"]["target_id"])
    if not ch:
        raise ValueError("캐릭터를 찾지 못했습니다.")

    fallback = {
        "summary": "이 캐릭터는 겉으로는 차분하지만 내면에는 복잡한 감정을 품고 있는 인물입니다. 관계의 거리감과 감정의 결이 함께 살아 있어 장면마다 긴장을 만들 수 있습니다. 선택과 반응에 일관성이 있어 이야기를 끌고 가기 좋습니다."
    }

    res = generate_json(build_character_summary_prompt(p, ch), fallback, 700)
    ch["summary"] = safe_str(res.get("summary"))
    ch["locked"] = True
    token = set_active_view(p, "character_finalized", ch["character_id"])
    touch_project(p)
    save_store()

    return {
        "view_token": token,
        "stage": "character_finalized",
        "character_id": ch["character_id"],
        "traits": ch["traits"],
        "summary": ch["summary"],
    }


def start_scene_seed(project_id: str) -> dict:
    p = get_project(project_id)
    seen_locations = list(p.get("scene_seed_seen", []))
    fallback = pick_non_duplicate(SCENE_SEED_FALLBACKS, seen_locations, "location")
    seed = generate_json(build_scene_seed_prompt(p, seen_locations), fallback, 700)

    location = safe_str(seed.get("location"))
    if not location or location in seen_locations:
        seed = fallback
        location = safe_str(seed.get("location"))

    if location and location not in p["scene_seed_seen"]:
        p["scene_seed_seen"].append(location)

    token = set_active_view(p, "scene_seed")
    p["scene_seed"] = {
        "location": location,
        "summary": safe_str(seed.get("summary")),
        "reason": safe_str(seed.get("reason")),
        "expected_effect": safe_str(seed.get("expected_effect")),
    }
    touch_project(p)
    save_store()

    return {"view_token": token, "stage": "scene_seed", **p["scene_seed"]}


def next_scene_seed(project_id: str, req: TokenRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()
    return start_scene_seed(project_id)


def accept_scene_seed(project_id: str, req: TokenRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    seed = p.get("scene_seed")
    if not seed:
        raise ValueError("확정할 장면 시작 추천이 없습니다.")

    p["scene_counter"] += 1
    p["draft_scene"] = {
        "scene_id": uuid.uuid4().hex[:10],
        "scene_number": p["scene_counter"],
        "location": seed["location"],
        "summary": seed["summary"],
        "last_recommendation": {},
        "accepted_recommendations": [],
        "seen_recommendations": [],
        "created_at": now_iso(),
    }
    p["scene_seed"] = None
    touch_project(p)
    save_store()
    return _make_scene_recommendation(p)


def _make_scene_recommendation(project: dict) -> dict:
    scene = project.get("draft_scene")
    if not scene:
        raise ValueError("먼저 장면을 시작해 주세요.")

    scene.setdefault("seen_recommendations", [])
    seen_values = list(scene["seen_recommendations"])
    fallback = pick_non_duplicate(SCENE_RECOMMEND_FALLBACKS, seen_values, "value")
    rec = generate_json(build_scene_prompt(project, scene, seen_values), fallback, 700)

    value = safe_str(rec.get("value"))
    if not value or value in seen_values:
        rec = fallback
        value = safe_str(rec.get("value"))

    if value and value not in scene["seen_recommendations"]:
        scene["seen_recommendations"].append(value)

    token = set_active_view(project, "scene_recommend", scene["scene_id"])
    scene["last_recommendation"] = {
        "value": value,
        "reason": safe_str(rec.get("reason")),
        "expected_effect": safe_str(rec.get("expected_effect")),
    }
    touch_project(project)
    save_store()

    return {
        "view_token": token,
        "stage": "scene_recommend",
        "scene_number": scene["scene_number"],
        "location": scene["location"],
        "allow_new_character": project["allow_new_character"],
        **scene["last_recommendation"],
    }


def start_scene(project_id: str, req: StartSceneRequest) -> dict:
    p = get_project(project_id)
    p["scene_counter"] += 1
    p["draft_scene"] = {
        "scene_id": uuid.uuid4().hex[:10],
        "scene_number": p["scene_counter"],
        "location": safe_str(req.location),
        "summary": safe_str(req.summary),
        "last_recommendation": {},
        "accepted_recommendations": [],
        "seen_recommendations": [],
        "created_at": now_iso(),
    }
    touch_project(p)
    save_store()
    return _make_scene_recommendation(p)


def recommend_next_scene(project_id: str, req: TokenRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    stage = p["active_view"]["stage"]
    if stage not in {"scene_recommend", "scene_review"}:
        raise ValueError("지금은 장면 추천 단계가 아닙니다.")
    return _make_scene_recommendation(p)


def accept_scene(project_id: str, req: ValueRequest) -> dict:
    p = get_project(project_id)
    if not is_valid_token(p, req.view_token):
        raise stale_button_error()

    if p["active_view"]["stage"] != "scene_recommend":
        raise ValueError("지금은 장면 추천 단계가 아닙니다.")

    scene = p.get("draft_scene")
    if not scene:
        raise ValueError("현재 작업 중인 장면이 없습니다.")

    item = {
        "value": safe_str(req.value),
        "reason": safe_str(scene.get("last_recommendation", {}).get("reason")),
        "expected_effect": safe_str(scene.get("last_recommendation", {}).get("expected_effect")),
    }
    scene["accepted_recommendations"].append(item)
    token = set_active_view(p, "scene_review", scene["scene_id"])
    touch_project(p)
    save_store()

    return {
        "view_token": token,
        "stage": "scene_review",
        "scene_number": scene["scene_number"],
        "location": scene["location"],
        "accepted_recommendation": item,
        "accepted_count": len(scene["accepted_recommendations"]),
    }


def save_scene(project_id: str) -> dict:
    p = get_project(project_id)
    scene = p.get("draft_scene")
    if not scene:
        raise ValueError("저장할 장면이 없습니다.")

    p["saved_scenes"].append(scene)
    p["draft_scene"] = None
    token = set_active_view(p, "menu")
    touch_project(p)
    save_store()

    return {
        "view_token": token,
        "saved_scene_number": scene["scene_number"],
        "saved_count": len(p["saved_scenes"]),
    }


def toggle_new_character(project_id: str, req: ToggleNewCharacterRequest) -> dict:
    p = get_project(project_id)
    p["allow_new_character"] = req.allow_new_character
    touch_project(p)
    save_store()
    return p


def render_markdown(project_id: str) -> str:
    p = get_project(project_id)
    lines: List[str] = []

    lines.append(f"# {p.get('title') or '제목 미정'}")
    lines.append("")
    lines.append(f"- 장르: {p.get('genre') or '미정'}")
    lines.append(f"- 주제: {p.get('theme') or '미정'}")
    lines.append(f"- 작품 의도: {p.get('intent') or '미정'}")
    lines.append("")
    lines.append("## 시놉시스")
    lines.append("")
    lines.append(p.get("synopsis") or "없음")
    lines.append("")
    lines.append("## 캐릭터")
    lines.append("")

    if not p["characters"]:
        lines.append("- 아직 없음")
        lines.append("")
    else:
        for idx, ch in enumerate(p["characters"], start=1):
            name = safe_str(ch.get("traits", {}).get("name")) or f"캐릭터 {idx}"
            lines.append(f"### {idx}. {name}")
            lines.append("")
            lines.append(f"- 종류: {ch['role_type']}")
            for key in TRAIT_ORDER:
                val = safe_str(ch.get("traits", {}).get(key))
                if val:
                    lines.append(f"- {TRAIT_LABELS[key]}: {val}")
            if ch.get("summary"):
                lines.append("")
                lines.append(ch["summary"])
            lines.append("")

    lines.append("## 장면")
    lines.append("")
    if not p["saved_scenes"]:
        lines.append("- 아직 저장된 장면 없음")
        lines.append("")
    else:
        for scene in p["saved_scenes"]:
            lines.append(f"### 장소 {scene['scene_number']}: {scene['location']}")
            lines.append("")
            lines.append(f"- 핵심: {scene['summary']}")
            lines.append("")
            for i, item in enumerate(scene.get("accepted_recommendations", []), start=1):
                lines.append(f"#### 추천 {i}")
                lines.append("")
                lines.append(f"- 추천: {safe_str(item.get('value'))}")
                lines.append(f"- 이유: {safe_str(item.get('reason'))}")
                lines.append(f"- 기대 효과: {safe_str(item.get('expected_effect'))}")
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def export_markdown(project_id: str) -> dict:
    p = get_project(project_id)
    file_name = f"{safe_filename(p.get('title') or 'story')}_{project_id[:8]}.md"
    file_path = EXPORT_DIR / file_name
    file_path.write_text(render_markdown(project_id), encoding="utf-8")
    return {"project_id": project_id, "file_name": file_name, "file_path": str(file_path)}
