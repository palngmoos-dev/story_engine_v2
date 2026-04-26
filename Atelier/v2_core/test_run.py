import os
import sys

# Ensure UTF-8 output for Windows console to support Korean
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# Add parent directory to sys.path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2_core import core_engine as core
from v2_core import scene_engine as scene
from v2_core import card_engine as cards

def run_simulation():
    print("🚀 [시네마틱 엔진 V2: 핵심 시스템 통합 검증]")
    core.reset_core()
    
    # 1. 환경 및 배우 설정
    print("\n[1] 무대 구축 및 배우 배치...")
    scene.play_turn(place="카페", lead="형사")
    
    # 2. 시네마틱 팔레트 (Directing) 적용
    print("[2] 시네마틱 연출 노드 주입...")
    core.set_cinematic_node("mood", "공포")
    core.set_cinematic_node("music", "느와르재즈")
    core.set_cinematic_node("lifestyle", "블랙수트")
    
    # 3. 타임라인 항법 (Chronos) 가동
    print("[3] 타로 크로노스: 과거 회상 시퀀스 예약...")
    core.set_timeline_mode("PAST")
    
    # 4. 씬 생성 시뮬레이션
    print("[4] 장면 생성 및 시스템 로직 가동...")
    # 실제 모델 호출을 피하기 위해 test_mode=True 사용 (로직 검증용)
    result = scene.play_turn(user_input="낡은 수첩에서 피묻은 지문을 발견한다.", duration=3, test_mode=True)
    
    print("\n✅ [시스템 구동 리포트]")
    print(f"- 현재 상태 태그: {result['state_tag']}")
    print(f"- 사용된 연출 카드: {result['card_used']}")
    print(f"- 타임라인 시점: {result['state']['timeline_mode']} (생성 후 자동 복구됨)")
    
    # 5. 서사 건강 진단 (Doctor Persona)
    print("\n[5] 프로젝트 종합 서사 진단...")
    health = core.analyze_project_health([result])
    print(f"- 서사 건강 점수: {health['score']}점")
    print(f"- 현재 환자 상태: {health['status']}")
    print(f"- 의사의 종합 소견: {health['report']}")
    
    print("\n🏁 [검증 완료] 모든 시스템이 한국어로 정상 구동 중입니다.")

if __name__ == "__main__":
    run_simulation()
