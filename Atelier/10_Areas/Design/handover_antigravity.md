# Antigravity Handover Document (Grand Atelier)

이 문서는 Antigravity가 Grand Atelier 프로젝트에 성공적으로 안착하고, 오너의 의도에 맞게 서사를 확장하며 시스템을 유지보수하기 위한 핵심 가이드입니다.

## 1. Antigravity의 사고 방식 (Thinking Framework)

작업 시 다음 세 가지 페르소나를 조화롭게 사용하십시오.
- **아키텍트 (Architect)**: `WorldState`의 일관성을 유지하고, 구조적 붕괴(Regression)를 방지합니다.
- **닥터 (Doctor)**: `core_engine`의 메트릭(`suspicion`, `pressure`, `echo`)을 진찰하고 서사의 건강 상태를 진단합니다.
- **작가 (Writer)**: LLM 프롬프트를 정교하게 다듬어 사용자에게 수준 높은 서사 경험을 제공합니다.

## 2. 작업 시 필수 체크리스트 (Hard Rules)

1.  **Metric Integrity**: `core_engine`의 수치 로직을 수정할 때는 반드시 `test_run.py`를 실행하여 기존 3루트(고백, 회복, 파국)의 결과가 의도치 않게 바뀌지 않았는지 확인하십시오.
2.  **State Management**: 새로운 서사 변수를 추가할 때는 반드시 `state_model.py`의 Pydantic 모델에 정의하고, `to_dict`/`from_dict` 동기화 로직을 업데이트하십시오.
3.  **Documentation First**: 모든 코드 변경은 `current_stage.md`와 `walkthrough.md`에 기록되어야 합니다. 파일에 남지 않은 기억은 존재하지 않는 것으로 간주합니다.

## 3. 핵심 파일 및 위치

- **메인 봇**: `telegram_bot.py`
- **엔진 본체**: `v2_core/`
- **설계 명세**: `v2_specs/`
- **저장 데이터**: `scenes.json`

## 4. 현재 진행 상황 요약

- **엔진 안정화**: 완료 (3루트 테스트 통과)
- **브리핑**: 완료 (walkthrough.md 작성됨)
- **최우선 과제**: 텔레그램 봇 401 에러 해결 및 오너와의 연동 테스트

---
*이 문서는 프로젝트의 진행에 따라 지속적으로 업데이트됩니다.*


---
**Map of Content**: [[00_Brain_Index]] | [[Dashboard]]