"""
Verification script for Phase 9: Telegram Connector.
Tests translation of CommonResponse to Telegram-friendly JSON payloads.
"""
import os
import sys
sys.path.append(os.getcwd())

from v2_core.api.schemas import CommonResponse
from v2_core.api.connectors.telegram_translator import TelegramTranslator

def verify():
    print("=== Phase 9: Telegram Connector Verification ===")
    
    # 1. Basic Status Response
    print("\n[Criterion 1] 기본 상태 응답 변환 테스트...")
    resp = CommonResponse(
        success=True,
        message="스트림이 생성되었습니다.",
        project_id="prj_test",
        world_state_summary={"momentum": 1.2, "ailment": "Healthy"}
    )
    payload = TelegramTranslator.to_send_message(123456, resp)
    
    if payload["chat_id"] == 123456 and "Healthy" in payload["text"] and "1.2x" in payload["text"]:
        print(" PASS: Basic header and momentum bar translated.")
    else:
        print(f" FAIL: Header translation mismatch.\n  Text: {payload['text']}")

    # 2. Card Stream Response
    print("\n[Criterion 2] 카드 스트림 응답 변환 테스트...")
    cards = [
        {"cid": "c1", "name": "카드 1", "summary": "설명 1", "category": "events"},
        {"cid": "c2", "name": "카드 2", "summary": "설명 2", "category": "characters"}
    ]
    resp_cards = CommonResponse(
        success=True,
        message="카드를 선택하세요.",
        project_id="prj_test",
        world_state_summary={"momentum": 1.0, "ailment": "Healthy"},
        payload={"cards": cards}
    )
    payload_cards = TelegramTranslator.to_send_message(123456, resp_cards)
    
    if "카드 1" in payload_cards["text"] and "EVENTS" in payload_cards["text"]:
        print(" PASS: Card list found in text.")
    else:
        print(" FAIL: Card list missing in text.")
        
    # Check Inline Keyboard
    ik = payload_cards.get("reply_markup", {}).get("inline_keyboard", [])
    if len(ik) >= 2 and any("카드 1" in b["text"] for b in ik[0]):
        print(" PASS: Inline keyboard for picking generated.")
    else:
        print(f" FAIL: Inline keyboard mismatch.\n  IK: {ik}")

    # 3. Rendered Scene Response
    print("\n[Criterion 3] 렌더링된 장면 응답 변환 테스트...")
    scene = {
        "title": "폭풍전야",
        "scene_text": "폭풍이 몰아치기 시작했다.\n\n[영상 콘티]\nShot: WS",
        "is_fallback": False
    }
    resp_scene = CommonResponse(
        success=True,
        message="장면이 렌더링되었습니다.",
        project_id="prj_test",
        payload={"rendered_scene": scene}
    )
    payload_scene = TelegramTranslator.to_send_message(123456, resp_scene)
    
    if "폭풍전야" in payload_scene["text"] and "몰아치기 시작했다" in payload_scene["text"]:
        print(" PASS: Rendered scene text found in message.")
    else:
        print(" FAIL: Scene text missing.")

    print("\n" + "=" * 40)
    print(" PHASE 9 TELEGRAM CONNECTOR SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
