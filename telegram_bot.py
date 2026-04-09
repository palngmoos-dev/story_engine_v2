import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
STATE_FILE = Path(__file__).resolve().parent / "user_states.json"

META_LABELS = {
    "genre": "장르",
    "theme": "주제",
    "intent": "작품 의도",
    "synopsis": "시놉시스",
    "title": "제목",
}
TRAIT_LABELS = {
    "role": "역할",
    "relation": "관계",
    "age": "나이",
    "personality": "성격",
    "appearance": "외형",
    "name": "이름",
}


def safe_value(v):
    return "" if v is None else str(v)


def load_states() -> Dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


user_states = defaultdict(
    lambda: {
        "project_id": None,
        "view_token": "",
        "awaiting_input": None,
        "awaiting_scene_location": "",
        "current_kind": "",
        "current_field": "",
        "current_value": "",
    }
)

for k, v in load_states().items():
    user_states[str(k)] = v


def save_states():
    STATE_FILE.write_text(
        json.dumps({str(k): v for k, v in user_states.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def state_of(user_id: int) -> dict:
    return user_states[str(user_id)]


def call_api(method: str, path: str, json_data=None, timeout: int = 120):
    url = f"{API_BASE_URL}{path}"
    if method == "GET":
        res = requests.get(url, timeout=timeout)
    elif method == "DELETE":
        res = requests.delete(url, timeout=timeout)
    else:
        res = requests.post(url, json=json_data, timeout=timeout)

    if not res.ok:
        try:
            detail = res.json()
        except Exception:
            detail = res.text
        raise Exception(f"{res.status_code} 오류: {detail}")

    return res.json()


def target_message(update: Update):
    if update.message:
        return update.message
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return None


async def send_text(update: Update, text: str, reply_markup=None):
    msg = target_message(update)
    if msg:
        await msg.reply_text(text, reply_markup=reply_markup)
        return
    chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
    await update.get_bot().send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def send_or_edit(update: Update, text: str, reply_markup=None):
    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.edit_text(text=text, reply_markup=reply_markup)
            return
        except Exception:
            pass
    await send_text(update, text, reply_markup=reply_markup)


async def send_document(update: Update, file_path: str, file_name: str):
    msg = target_message(update)
    if msg:
        with open(file_path, "rb") as f:
            await msg.reply_document(document=f, filename=file_name)
        return
    chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
    with open(file_path, "rb") as f:
        await update.get_bot().send_document(chat_id=chat_id, document=f, filename=file_name)


async def safe_answer(update: Update):
    q = update.callback_query
    if not q:
        return
    try:
        await q.answer()
    except Exception:
        pass


def kb_start():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("새 작업 시작", callback_data="boot:start")],
        [InlineKeyboardButton("기존 작업 이어가기", callback_data="boot:resume")],
        [InlineKeyboardButton("프로젝트 목록", callback_data="boot:projects")],
    ])


def kb_projects(items: list[dict]):
    rows = []
    for item in items[:10]:
        label = f"{item['title']} · 장면 {item['saved_scenes_count']}"
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"project:select:{item['project_id']}")])
    rows.append([InlineKeyboardButton("새 작업 시작", callback_data="boot:start")])
    return InlineKeyboardMarkup(rows)


def kb_meta(token: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("다음 추천", callback_data=f"meta:next:{token}")],
        [InlineKeyboardButton("이 추천으로 진행", callback_data=f"meta:accept:{token}")],
        [InlineKeyboardButton("직접 입력하기", callback_data=f"meta:direct:{token}")],
    ])


def kb_char(token: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("다음 추천", callback_data=f"char:next:{token}")],
        [InlineKeyboardButton("이 추천으로 진행", callback_data=f"char:accept:{token}")],
        [InlineKeyboardButton("직접 입력하기", callback_data=f"char:direct:{token}")],
    ])


def kb_char_ready(token: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("캐릭터 정리하기", callback_data=f"char:finalize:{token}")],
        [InlineKeyboardButton("다른 추천 받기", callback_data=f"char:next:{token}")],
        [InlineKeyboardButton("현재 상태 보기", callback_data="boot:resume")],
    ])


def kb_after_meta():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("주연 캐릭터 만들기", callback_data="char:start:lead")],
        [InlineKeyboardButton("조연 캐릭터 만들기", callback_data="char:start:support")],
        [InlineKeyboardButton("장면 시작하기", callback_data="scene_seed:start")],
        [InlineKeyboardButton("현재 상태 보기", callback_data="boot:resume")],
        [InlineKeyboardButton("프로젝트 목록", callback_data="boot:projects")],
    ])


def kb_after_character():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("주연 더 만들기", callback_data="char:start:lead")],
        [InlineKeyboardButton("조연 더 만들기", callback_data="char:start:support")],
        [InlineKeyboardButton("장면 시작하기", callback_data="scene_seed:start")],
        [InlineKeyboardButton("현재 상태 보기", callback_data="boot:resume")],
    ])


def kb_scene_seed(token: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("다음 추천", callback_data=f"scene_seed:next:{token}")],
        [InlineKeyboardButton("이 추천으로 진행", callback_data=f"scene_seed:accept:{token}")],
        [InlineKeyboardButton("직접 장소 입력", callback_data="scene:start")],
    ])


def kb_scene(token: str, allow_new: bool):
    toggle_label = "현재 인물만 유지" if allow_new else "새 인물 허용"
    toggle_value = "off" if allow_new else "on"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("다음 추천", callback_data=f"scene:next:{token}")],
        [InlineKeyboardButton("이 추천으로 진행", callback_data=f"scene:accept:{token}")],
        [InlineKeyboardButton(toggle_label, callback_data=f"scene:toggle:{toggle_value}:{token}")],
    ])


def kb_scene_review():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("다음 장면 추천 받기", callback_data="scene:again")],
        [InlineKeyboardButton("이 장면 저장", callback_data="scene:save")],
        [InlineKeyboardButton("새 장소 시작", callback_data="scene_seed:start")],
        [InlineKeyboardButton("현재 상태 보기", callback_data="boot:resume")],
    ])


def render_card(title: str, value: str, reason: str, effect: str) -> str:
    return (
        f"[{title}]\n\n"
        f"추천:\n{safe_value(value)}\n\n"
        f"이유:\n{safe_value(reason)}\n\n"
        f"기대 효과:\n{safe_value(effect)}"
    )


def render_scene_seed(data: dict) -> str:
    return (
        "[AI 장면 시작 추천]\n\n"
        f"장소:\n{safe_value(data.get('location'))}\n\n"
        f"장면 요약:\n{safe_value(data.get('summary'))}\n\n"
        f"이유:\n{safe_value(data.get('reason'))}\n\n"
        f"기대 효과:\n{safe_value(data.get('expected_effect'))}"
    )


def render_character_finalized(data: dict) -> str:
    traits = data.get("traits", {})
    lines = ["[캐릭터 정리 완료]"]
    for key in ["role", "relation", "age", "personality", "appearance", "name"]:
        val = safe_value(traits.get(key))
        if val:
            lines.append(f"- {TRAIT_LABELS[key]}: {val}")
    lines.append("")
    lines.append(safe_value(data.get("summary")))
    return "\n".join(lines)


def render_status(data: dict) -> str:
    active = data.get("active_view", {})
    stage = safe_value(active.get("stage")) or "대기"
    lines = [
        "[현재 상태]",
        f"- 현재 단계: {stage}",
        f"- 제목: {safe_value(data.get('title')) or '미정'}",
        f"- 장르: {safe_value(data.get('genre')) or '미정'}",
        f"- 주제: {safe_value(data.get('theme')) or '미정'}",
        f"- 작품 의도: {safe_value(data.get('intent')) or '미정'}",
        f"- 시놉시스: {'입력됨' if safe_value(data.get('synopsis')) else '미정'}",
        f"- 캐릭터 수: {len(data.get('characters', []))}",
        f"- 저장된 장면 수: {len(data.get('saved_scenes', []))}",
    ]
    return "\n".join(lines)


def remember(st: dict, token: str, kind: str, field: str, value: str):
    st["view_token"] = token
    st["current_kind"] = kind
    st["current_field"] = field
    st["current_value"] = safe_value(value)
    save_states()


def is_stale_error(e: Exception) -> bool:
    return "지나간 단계의 버튼" in str(e)


async def recover_latest(update: Update):
    await send_text(update, "최신 화면으로 다시 안내합니다.")
    await resume_flow(update)


async def show_projects(update: Update):
    items = call_api("GET", "/projects")
    if not items:
        await send_or_edit(update, "아직 저장된 프로젝트가 없습니다.", reply_markup=kb_start())
        return
    await send_or_edit(update, "[프로젝트 목록]", reply_markup=kb_projects(items))


async def start_flow(update: Update):
    st = state_of(update.effective_user.id)
    proj = call_api("POST", "/projects", {"mode": "guide"})
    st["project_id"] = proj["project_id"]
    save_states()

    rec = call_api("POST", f"/projects/{st['project_id']}/meta/recommend/genre")
    remember(st, rec["view_token"], "meta", rec["field"], rec["value"])

    await send_or_edit(
        update,
        render_card(f"AI {META_LABELS[rec['field']]} 추천", rec["value"], rec["reason"], rec["expected_effect"]),
        reply_markup=kb_meta(rec["view_token"]),
    )


async def resume_flow(update: Update):
    st = state_of(update.effective_user.id)
    if not st["project_id"]:
        await send_or_edit(update, "이어갈 작업이 아직 없습니다.", reply_markup=kb_start())
        return

    data = call_api("GET", f"/projects/{st['project_id']}/status")
    active = data.get("active_view", {})
    stage = safe_value(active.get("stage"))
    token = safe_value(active.get("view_token"))

    if stage.startswith("meta:"):
        pending = data.get("meta_pending") or {}
        rec = pending.get("recommendation") or {}
        field = pending.get("field") or stage.split(":", 1)[1]
        remember(st, token, "meta", field, rec.get("value", ""))
        await send_or_edit(
            update,
            render_card(f"AI {META_LABELS.get(field, field)} 추천", rec.get("value"), rec.get("reason"), rec.get("expected_effect")),
            reply_markup=kb_meta(token),
        )
        return

    if stage.startswith("char:"):
        target_id = safe_value(active.get("target_id"))
        ch = None
        for item in data.get("characters", []):
            if item["character_id"] == target_id:
                ch = item
                break
        rec = (ch or {}).get("pending_recommendation") or {}
        trait_key = stage.split(":", 1)[1]
        remember(st, token, "char", trait_key, rec.get("value", ""))
        await send_or_edit(
            update,
            render_card(f"캐릭터 추천 - {TRAIT_LABELS.get(trait_key, trait_key)}", rec.get("value"), rec.get("reason"), rec.get("expected_effect")),
            reply_markup=kb_char(token),
        )
        return

    if stage == "character_ready":
        await send_or_edit(update, "이 캐릭터 정보가 충분히 쌓였습니다. 이제 하나로 정리하시겠습니까?", reply_markup=kb_char_ready(token))
        return

    if stage == "scene_seed":
        seed = data.get("scene_seed") or {}
        remember(st, token, "scene_seed", "scene_seed", "")
        await send_or_edit(update, render_scene_seed(seed), reply_markup=kb_scene_seed(token))
        return

    if stage == "scene_recommend":
        scene = data.get("draft_scene") or {}
        rec = scene.get("last_recommendation") or {}
        remember(st, token, "scene", "scene", rec.get("value", ""))
        await send_or_edit(
            update,
            render_card("AI 장면 추천", rec.get("value"), rec.get("reason"), rec.get("expected_effect")),
            reply_markup=kb_scene(token, data.get("allow_new_character", False)),
        )
        return

    if stage == "scene_review":
        await send_or_edit(update, "방금 선택한 전개가 반영되었습니다.", reply_markup=kb_scene_review())
        return

    await send_or_edit(update, render_status(data), reply_markup=kb_after_meta())


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_text(update, "안녕하세요. 아래 버튼으로 시작하세요.", reply_markup=kb_start())


async def resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await resume_flow(update)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = state_of(update.effective_user.id)
    if not st["project_id"]:
        await send_text(update, "현재 프로젝트가 없습니다.")
        return
    data = call_api("GET", f"/projects/{st['project_id']}/status")
    await send_text(update, render_status(data))


async def projects_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_projects(update)


async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = state_of(update.effective_user.id)
    if not st["project_id"]:
        await send_text(update, "내보낼 프로젝트가 없습니다.")
        return
    data = call_api("GET", f"/projects/{st['project_id']}/export-markdown")
    await send_document(update, data["file_path"], data["file_name"])


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = state_of(update.effective_user.id)
    text = safe_value(update.message.text)

    if not st["project_id"]:
        return

    try:
        mode = st.get("awaiting_input")

        if mode == "meta":
            res = call_api("POST", f"/projects/{st['project_id']}/meta/direct", {
                "view_token": st["view_token"],
                "value": text,
            })
            st["awaiting_input"] = None
            save_states()

            if res["done"]:
                await send_text(update, f"제목이 확정되었습니다: {res['title']}", reply_markup=kb_after_meta())
            else:
                rec = res["recommendation"]
                remember(st, rec["view_token"], "meta", rec["field"], rec["value"])
                await send_text(
                    update,
                    render_card(f"AI {META_LABELS[rec['field']]} 추천", rec["value"], rec["reason"], rec["expected_effect"]),
                    reply_markup=kb_meta(rec["view_token"]),
                )
            return

        if mode == "char":
            res = call_api("POST", f"/projects/{st['project_id']}/characters/direct", {
                "view_token": st["view_token"],
                "value": text,
            })
            st["awaiting_input"] = None
            save_states()

            if res["done"]:
                await send_text(update, res["message"], reply_markup=kb_char_ready(res["view_token"]))
            else:
                rec = res["recommendation"]
                remember(st, rec["view_token"], "char", rec["trait_key"], rec["value"])
                await send_text(
                    update,
                    render_card(f"캐릭터 추천 - {rec['trait_label']}", rec["value"], rec["reason"], rec["expected_effect"]),
                    reply_markup=kb_char(rec["view_token"]),
                )
            return

        if mode == "scene_location":
            st["awaiting_scene_location"] = text
            st["awaiting_input"] = "scene_summary"
            save_states()
            await send_text(update, "이 장소에서 담고 싶은 장면 내용을 입력해 주세요.")
            return

        if mode == "scene_summary":
            res = call_api("POST", f"/projects/{st['project_id']}/scene/start", {
                "location": safe_value(st["awaiting_scene_location"]),
                "summary": text,
            })
            st["awaiting_input"] = None
            remember(st, res["view_token"], "scene", "scene", res["value"])
            await send_text(
                update,
                render_card("AI 장면 추천", res["value"], res["reason"], res["expected_effect"]),
                reply_markup=kb_scene(res["view_token"], res["allow_new_character"]),
            )
            return

    except Exception as e:
        if is_stale_error(e):
            await recover_latest(update)
            return
        await send_text(update, f"입력 처리 중 문제가 있었습니다.\n{e}")


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update)
    st = state_of(update.effective_user.id)
    data = update.callback_query.data if update.callback_query else ""

    try:
        if data == "boot:start":
            await start_flow(update)
            return

        if data == "boot:resume":
            await resume_flow(update)
            return

        if data == "boot:projects":
            await show_projects(update)
            return

        if data.startswith("project:select:"):
            project_id = data.split(":")[2]
            st["project_id"] = project_id
            save_states()
            await resume_flow(update)
            return

        if data.startswith("meta:"):
            parts = data.split(":")
            action = parts[1]
            token = parts[2]

            if action == "next":
                rec = call_api("POST", f"/projects/{st['project_id']}/meta/recommend-next", {"view_token": token})
                remember(st, rec["view_token"], "meta", rec["field"], rec["value"])
                await send_or_edit(
                    update,
                    render_card(f"AI {META_LABELS[rec['field']]} 추천", rec["value"], rec["reason"], rec["expected_effect"]),
                    reply_markup=kb_meta(rec["view_token"]),
                )
                return

            if action == "accept":
                res = call_api("POST", f"/projects/{st['project_id']}/meta/accept", {
                    "view_token": token,
                    "value": safe_value(st["current_value"]),
                })
                if res["done"]:
                    await send_or_edit(update, f"제목이 확정되었습니다: {res['title']}", reply_markup=kb_after_meta())
                else:
                    rec = res["recommendation"]
                    remember(st, rec["view_token"], "meta", rec["field"], rec["value"])
                    await send_or_edit(
                        update,
                        render_card(f"AI {META_LABELS[rec['field']]} 추천", rec["value"], rec["reason"], rec["expected_effect"]),
                        reply_markup=kb_meta(rec["view_token"]),
                    )
                return

            if action == "direct":
                st["awaiting_input"] = "meta"
                st["view_token"] = token
                save_states()
                await send_or_edit(update, "원하는 내용을 직접 입력해 주세요.")
                return

        if data.startswith("char:start:"):
            role_type = data.split(":")[2]
            rec = call_api("POST", f"/projects/{st['project_id']}/characters/start", {"role_type": role_type})
            remember(st, rec["view_token"], "char", rec["trait_key"], rec["value"])
            await send_or_edit(
                update,
                render_card(f"캐릭터 추천 - {rec['trait_label']}", rec["value"], rec["reason"], rec["expected_effect"]),
                reply_markup=kb_char(rec["view_token"]),
            )
            return

        if data.startswith("char:"):
            parts = data.split(":")
            action = parts[1]
            token = parts[2]

            if action == "next":
                res = call_api("POST", f"/projects/{st['project_id']}/characters/recommend-next", {"view_token": token})
                if res["stage"] == "character_ready":
                    await send_or_edit(update, res["message"], reply_markup=kb_char_ready(res["view_token"]))
                else:
                    remember(st, res["view_token"], "char", res["trait_key"], res["value"])
                    await send_or_edit(
                        update,
                        render_card(f"캐릭터 추천 - {res['trait_label']}", res["value"], res["reason"], res["expected_effect"]),
                        reply_markup=kb_char(res["view_token"]),
                    )
                return

            if action == "accept":
                res = call_api("POST", f"/projects/{st['project_id']}/characters/accept", {
                    "view_token": token,
                    "value": safe_value(st["current_value"]),
                })
                if res["done"]:
                    await send_or_edit(update, res["message"], reply_markup=kb_char_ready(res["view_token"]))
                else:
                    rec = res["recommendation"]
                    remember(st, rec["view_token"], "char", rec["trait_key"], rec["value"])
                    await send_or_edit(
                        update,
                        render_card(f"캐릭터 추천 - {rec['trait_label']}", rec["value"], rec["reason"], rec["expected_effect"]),
                        reply_markup=kb_char(rec["view_token"]),
                    )
                return

            if action == "direct":
                st["awaiting_input"] = "char"
                st["view_token"] = token
                save_states()
                await send_or_edit(update, "이 항목을 직접 입력해 주세요.")
                return

            if action == "finalize":
                res = call_api("POST", f"/projects/{st['project_id']}/characters/finalize", {"view_token": token})
                await send_or_edit(update, render_character_finalized(res), reply_markup=kb_after_character())
                return

        if data == "scene_seed:start":
            rec = call_api("POST", f"/projects/{st['project_id']}/scene/seed/start", {})
            remember(st, rec["view_token"], "scene_seed", "scene_seed", "")
            await send_or_edit(update, render_scene_seed(rec), reply_markup=kb_scene_seed(rec["view_token"]))
            return

        if data.startswith("scene_seed:"):
            parts = data.split(":")
            action = parts[1]
            token = parts[2]

            if action == "next":
                rec = call_api("POST", f"/projects/{st['project_id']}/scene/seed/next", {"view_token": token})
                remember(st, rec["view_token"], "scene_seed", "scene_seed", "")
                await send_or_edit(update, render_scene_seed(rec), reply_markup=kb_scene_seed(rec["view_token"]))
                return

            if action == "accept":
                rec = call_api("POST", f"/projects/{st['project_id']}/scene/seed/accept", {"view_token": token})
                remember(st, rec["view_token"], "scene", "scene", rec["value"])
                await send_or_edit(
                    update,
                    render_card("AI 장면 추천", rec["value"], rec["reason"], rec["expected_effect"]),
                    reply_markup=kb_scene(rec["view_token"], rec["allow_new_character"]),
                )
                return

        if data == "scene:start":
            st["awaiting_input"] = "scene_location"
            save_states()
            await send_or_edit(update, "새 장소 이름을 입력해 주세요. 예: 골목길, 카페, 옥상")
            return

        if data.startswith("scene:"):
            parts = data.split(":")
            action = parts[1]

            if action == "next":
                token = parts[2]
                res = call_api("POST", f"/projects/{st['project_id']}/scene/recommend-next", {"view_token": token})
                remember(st, res["view_token"], "scene", "scene", res["value"])
                await send_or_edit(
                    update,
                    render_card("AI 장면 추천", res["value"], res["reason"], res["expected_effect"]),
                    reply_markup=kb_scene(res["view_token"], res["allow_new_character"]),
                )
                return

            if action == "accept":
                token = parts[2]
                res = call_api("POST", f"/projects/{st['project_id']}/scene/accept", {
                    "view_token": token,
                    "value": safe_value(st["current_value"]),
                })
                item = res["accepted_recommendation"]
                await send_or_edit(
                    update,
                    render_card("반영된 장면 전개", item["value"], item["reason"], item["expected_effect"]),
                    reply_markup=kb_scene_review(),
                )
                return

            if action == "toggle":
                value = parts[2]
                token = parts[3]
                allow = value == "on"
                call_api("POST", f"/projects/{st['project_id']}/settings/allow-new-character", {"allow_new_character": allow})
                res = call_api("POST", f"/projects/{st['project_id']}/scene/recommend-next", {"view_token": token})
                remember(st, res["view_token"], "scene", "scene", res["value"])
                await send_or_edit(
                    update,
                    render_card("AI 장면 추천", res["value"], res["reason"], res["expected_effect"]),
                    reply_markup=kb_scene(res["view_token"], res["allow_new_character"]),
                )
                return

            if action == "again":
                status_data = call_api("GET", f"/projects/{st['project_id']}/status")
                token = safe_value(status_data.get("active_view", {}).get("view_token"))
                res = call_api("POST", f"/projects/{st['project_id']}/scene/recommend-next", {"view_token": token})
                remember(st, res["view_token"], "scene", "scene", res["value"])
                await send_or_edit(
                    update,
                    render_card("AI 장면 추천", res["value"], res["reason"], res["expected_effect"]),
                    reply_markup=kb_scene(res["view_token"], res["allow_new_character"]),
                )
                return

            if action == "save":
                res = call_api("POST", f"/projects/{st['project_id']}/scene/save", {})
                await send_or_edit(update, f"장면 저장이 완료되었습니다. 저장 장면 수: {res['saved_count']}", reply_markup=kb_after_meta())
                return

    except Exception as e:
        if is_stale_error(e):
            await recover_latest(update)
            return
        await send_or_edit(update, f"처리 중 문제가 있었습니다.\n{e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        if isinstance(update, Update):
            await send_text(update, f"오류가 발생했습니다.\n{context.error}")
    except Exception:
        pass


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 값이 없습니다. .env를 확인해 주세요.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("resume", resume_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("projects", projects_cmd))
    app.add_handler(CommandHandler("export_md", export_cmd))

    app.add_handler(CallbackQueryHandler(button_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
