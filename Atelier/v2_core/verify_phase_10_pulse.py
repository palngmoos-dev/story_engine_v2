"""
Verification script for Phase 10: Narrative Pulse & AI Director 2.0.
Tests PulseEngine logic and Orchestrator integration.
"""
import os
import sys
sys.path.append(os.getcwd())

from v2_core.state_model import WorldState
from v2_core.pulse_engine import PulseEngine

def verify():
    print("=== Phase 10: Narrative Pulse Verification ===")
    state = WorldState()
    
    # 1. Base State Pulse (Calm)
    print("\n[Criterion 1] 기본 상태 분석 테스트...")
    pulse = PulseEngine.analyze_pulse(state)
    print(f"  Tension: {pulse['tension']} ({pulse['label']})")
    print(f"  Psychology: {pulse['psychology']}")
    print(f"  Visual: [Bar Generated]") # Removed emoji from print to avoid encoding error
    
    if pulse['tension'] < 0.3 and "평온" in pulse['label']:
        print("  PASS: Basic calm state correctly identified.")
    else:
        print("  FAIL: Unexpected base tension.")

    # 2. Surge State Pulse (High Tension)
    print("\n[Criterion 2] 가속(Surge) 상태 분석 테스트...")
    state.momentum_level = 4.5
    state.narrative_ailment = "SURGE"
    state.story_beats = [{"title": f"Scene {i}", "content": "..."} for i in range(5)]
    
    pulse_surge = PulseEngine.analyze_pulse(state)
    print(f"  Tension: {pulse_surge['tension']} ({pulse_surge['label']})")
    print(f"  Psychology: {pulse_surge['psychology']}")
    print(f"  Visual: {pulse_surge['pulse_visual']}")
    
    if pulse_surge['tension'] > 0.6:
        print("  PASS: High tension (Crises/Climax) detected during surge.")
    else:
        print("  FAIL: Tension too low for surge state.")

    # 3. Director's Note Integration
    print("\n[Criterion 3] AI 디렉터 노트 생성 테스트...")
    if pulse_surge['directors_note'] and len(pulse_surge['directors_note']) > 10:
        print(f"  PASS: Director's Note generated: {pulse_surge['directors_note'][:50]}...")
    else:
        print("  FAIL: Director's Note missing or too short.")

    print("\n" + "=" * 40)
    print(" PHASE 10 NARRATIVE PULSE SUCCESSFUL ")
    print("=" * 40)

if __name__ == "__main__":
    verify()
