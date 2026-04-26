import unittest
from unittest.mock import patch
import sys
import io

# Windows 콘솔에서 UTF-8 출력을 보장하기 위한 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

from v2_core import core_engine as core
from v2_core import scene_engine as scene
from v2_core import card_engine as cards

# 테스트용 예외 클래스
class SimulatedError(Exception): pass

class TestRefactorV2(unittest.TestCase):
    def setUp(self):
        """매 테스트 시작 전 엔진 상태를 초기화합니다."""
        core.reset_core()

    def test_registry_lookup(self):
        """캐릭터, 공간, 소품, 카드 등 모든 프리셋 조회가 정상적인지 검증합니다."""
        char = cards.get_character("형사")
        self.assertIsNotNone(char)
        
        space = cards.get_space("카페")
        self.assertIsNotNone(space)
        self.assertIsNotNone(space.description)
        
        all_presets = cards.get_all_presets()
        self.assertIn("characters", all_presets)
        self.assertIn("spaces", all_presets)

    def test_play_turn_modular_setup(self):
        """play_turn 실행 시 각 구성 요소가 상태값에 정상적으로 반영되는지 검증합니다."""
        result = scene.play_turn(
            place="골목", 
            lead="연인", 
            support=["낯선 손님"], 
            prop="부엌칼", 
            card="침묵",
            user_input="편지를 숨긴다.", 
            test_mode=True
        )
        
        state = result['state']
        self.assertEqual(state['place'], "골목")
        self.assertEqual(state['lead_character']['name'], "연인")
        self.assertEqual(len(state['support_characters']), 1)
        self.assertEqual(len(state['active_props']), 1)
        
        # 2. 결과 데이터 구조 및 존재 여부 검증
        self.assertIn('state_tag', result)
        self.assertIsNotNone(result['scene_text'])
        # card_used가 한글 "침묵"인지 확인 (기존 "none"에서 "없음"으로 바뀐 일관성 체크 포함)
        self.assertEqual(result['card_used'], "침묵")

    def test_lead_without_place(self):
        """장소(place) 없이 주연(lead)만 설정했을 때의 정상 작동을 검증합니다. (버그 수정 확인)"""
        # 초기 상태 확인 (기본 장소는 보통 '카페' 또는 None)
        scene.play_turn(place="카페", test_mode=True)
        initial_state = core.get_state()
        self.assertEqual(initial_state['place'], "카페")
        
        # 장소 없이 캐릭터만 변경 호출
        result = scene.play_turn(lead="형사", test_mode=True)
        state = result['state']
        
        self.assertEqual(state['place'], "카페", "장소가 유지되어야 합니다.")
        self.assertEqual(state['lead_character']['name'], "형사", "주연 캐릭터가 '형사'로 변경되어야 합니다.")

    def test_impact_numerical_delta(self):
        """카드 사용 시 변화량(changes)이 숫자로 정확히 계산되는지 검증합니다."""
        scene.play_turn(place="방", lead="친구", test_mode=True)
        # 1. '질문' 카드 사용 (impact: {"suspicion": 2, "pressure": 1})
        result = scene.play_turn(card="질문", test_mode=True)
        changes = result['changes']
        self.assertEqual(changes["suspicion"], 2)
        self.assertEqual(changes["pressure"], 1)

    def test_card_impact_no_over_amplification(self):
        """캐릭터 설정 후 카드를 연속 사용해도 주연의 base_impact가 중복 합산되지 않는지 검증합니다."""
        # '형사' 캐릭터는 base_impact: {"suspicion": 1, "pressure": 1} 를 가짐 (card_engine.py 참고)
        # 1. 형사 설정 (이때 suspicion=1, pressure=1 이 됨)
        scene.play_turn(lead="형사", test_mode=True)
        state_after_setup = core.get_state()
        self.assertEqual(state_after_setup['timing']['suspicion'], 1)
        
        # 2. '침묵' 카드 사용 (impact: {"echo": 1} - card_engine.py 기준)
        # 수정된 로직에서는 suspicion/pressure에 형사의 수치가 더해지면 안 됨 (변화량 0이어야 함)
        result1 = scene.play_turn(card="침묵", test_mode=True)
        self.assertEqual(result1['changes'].get('suspicion', 0), 0, "카드 사용 시 주연 영향력이 중복 합산되었습니다.")
        self.assertEqual(result1['changes'].get('echo', 0), 1, "카드 고유 영향력 반영 수치가 기대와 다릅니다.")
        
        # 3. '관찰' 카드 사용 (impact: {"suspicion": 1})
        # 형사의 수치가 또 더해지면 suspicion 변화량이 1+1=2가 될 것이고, 정상이면 1이어야 함
        result2 = scene.play_turn(card="관찰", test_mode=True)
        self.assertEqual(result2['changes'].get('suspicion', 0), 1, "연속 카드 사용 시 주연 영향력이 중복 합산되었습니다.")

    def test_timeline_safety(self):
        """예외 발생 시에도 timeline_mode가 반드시 PRESENT로 복구되는지 검증합니다."""
        core.set_timeline_mode("PAST")
        
        with patch('v2_core.scene_engine.generate_next_scene', side_effect=SimulatedError("Test crash")):
            try:
                scene.play_turn(user_input="Error trigger", test_mode=True)
            except SimulatedError:
                pass
            
        final_state = core.get_state()
        self.assertEqual(final_state['timeline_mode'], "PRESENT")

if __name__ == "__main__":
    unittest.main()
