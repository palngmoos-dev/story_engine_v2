import unittest
from unittest.mock import patch, MagicMock
import os
import json
from . import wizard_engine as wizard
from . import draft_manager as dm

class TestWizard(unittest.TestCase):
    def setUp(self):
        # Ensure a clean slate for persistence tests
        if os.path.exists(dm.DRAFT_FILE):
            os.remove(dm.DRAFT_FILE)

    def tearDown(self):
        if os.path.exists(dm.DRAFT_FILE):
            os.remove(dm.DRAFT_FILE)

    def test_safe_json_parse_success(self):
        """정상적인 JSON 및 마크다운 포함 JSON 파싱 성공 확인."""
        raw_json = '{"name": "테스트", "level": 1}'
        md_json = "이것은 응답입니다. ```json\n" + raw_json + "\n``` 확인 바랍니다."
        
        result1 = wizard._parse_ai_json(raw_json, {})
        result2 = wizard._parse_ai_json(md_json, {})
        
        self.assertEqual(result1["name"], "테스트")
        self.assertEqual(result2["name"], "테스트")

    def test_safe_json_parse_fallback(self):
        """깨진 JSON 입력 시 fallback 데이터 반환 확인."""
        broken_json = '{"name": "비정상", "level": ' # Unclosed
        fallback = {"name": "실패", "level": 0}
        
        result = wizard._parse_ai_json(broken_json, fallback)
        self.assertEqual(result["name"], "실패")

    @patch("ollama_client.ollama_generate")
    def test_direct_input_conversion(self, mock_generate):
        """사용자 자유 입력이 구조화된 스토리로 변환되는지 확인."""
        mock_response = '{"genre": "판타지", "one_liner": "사용자 스토리", "plot": "줄거리", "reason": "유저 입력"}'
        mock_generate.return_value = mock_response
        
        result = wizard.structure_user_input("용사가 마왕을 잡는 이야기", mode="STORY")
        self.assertEqual(result["genre"], "판타지")
        self.assertEqual(result["one_liner"], "사용자 스토리")
        self.assertIn("plot", result)

    def test_persistence_flow(self):
        """확정 시점에 데이터가 올바르게 저장되고 불러와지는지 확인."""
        test_draft = {
            "status": "story_confirmed",
            "story": {"genre": "SF", "one_liner": "우주 여행", "plot": "...", "reason": "..."},
            "character": None
        }
        
        # 1. 저장 테스트
        save_result = dm.save_draft(test_draft)
        self.assertTrue(save_result)
        self.assertTrue(os.path.exists(dm.DRAFT_FILE))
        
        # 2. 로드 테스트
        loaded = dm.load_draft()
        self.assertEqual(loaded["status"], "story_confirmed")
        self.assertEqual(loaded["story"]["one_liner"], "우주 여행")
        self.assertIn("plot", loaded["story"])

    @patch("ollama_client.ollama_generate")
    def test_character_recommendation_with_fallback(self, mock_generate):
        """AI 에러 메시지([Ollama...) 수신 시 Fallback 캐릭터 반환 확인."""
        mock_generate.return_value = "[Ollama] Connection Failed"
        
        result = wizard.generate_character_recommendation({"one_liner": "test", "plot": "test"})
        self.assertEqual(result["name"], wizard.FALLBACK_CHARACTER["name"])
        self.assertEqual(result["level"], 1)

if __name__ == "__main__":
    unittest.main()
