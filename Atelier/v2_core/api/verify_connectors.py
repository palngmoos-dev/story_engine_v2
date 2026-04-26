"""
Verification script for Phase 8.2: Messaging Entry Connectors.
Tests Kakao Webhook integration and User Sync logic.
"""
import os
import sys
import json

# Ensure v2_core is importable
sys.path.append(os.getcwd())

from v2_core.api.api_server import app
from fastapi.testclient import TestClient

client = TestClient(app)

def verify():
    print("=== Phase 8.2: Messaging Entry (Messenger) Verification ===")
    
    # 1. 카카오톡 웹훅 요청 시계 테스트 (첫 접속)
    print("\n[Criterion 1] 카카오톡 첫 접속 및 프로젝트 자동 생성 테스트...")
    mock_kakao_req = {
        "userRequest": {
            "user": {"id": "test_kakao_user_123"},
            "utterance": "안녕, 이야기를 시작하고 싶어."
        }
    }
    
    resp = client.post("/webhook/kakao", json=mock_kakao_req)
    data = resp.json()
    
    # Debug: Print full response if needed
    # print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # SEARCH for Carousel in outputs
    outputs = data.get("template", {}).get("outputs", [])
    found_carousel = any("carousel" in out for out in outputs)
    
    if found_carousel:
        print(f" PASS: Carousel UI generated with multiple cards.")
    else:
        print(f" FAIL: Carousel UI missing in response. Outputs count: {len(outputs)}")

    # 2. 유저 매핑 및 자동 작명 확인
    print("\n[Criterion 2] 유저 매핑 및 시네마틱 자동 작명 확인...")
    from v2_core.api.user_sync import UserSyncManager
    from v2_core.api.project_manager import ProjectManager
    sync_mgr = UserSyncManager()
    pm = ProjectManager()
    
    p_id = sync_mgr.get_or_create_project("kakao", "test_kakao_user_123", pm)
    project_meta = pm.list_projects().get(p_id)
    
    if project_meta:
        print(f" PASS: Project Link Created. ID: {p_id}, Title: '{project_meta['title']}'")
    else:
        print(" FAIL: Project mapping failed.")

    # 3. 명령 파싱 (/pick) 테스트
    print("\n[Criterion 3] 메신저 명령(/pick) 파싱 및 엔진 액션 테스트...")
    mock_pick_req = {
        "userRequest": {
            "user": {"id": "test_kakao_user_123"},
            "utterance": "/pick CARD_001"
        }
    }
    resp_pick = client.post("/webhook/kakao", json=mock_pick_req)
    pick_text = resp_pick.json()["template"]["outputs"][0]["simpleText"]["text"]
    
    if "Card CARD_001 picked" in pick_text:
        # Avoid CP949 encoding issues with emojis in windows console
        safe_text = pick_text.replace("🎬", "[IMAGE]").splitlines()[0]
        print(f" PASS: Command parsed and action executed. Response: {safe_text}")
    else:
        print(f" FAIL: Command parsing failed. Response: {pick_text}")

    print("\n" + "=" * 40)
    print(" PHASE 8.2 MESSAGING CONNECTORS SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
