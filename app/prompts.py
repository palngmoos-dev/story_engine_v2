from app.models import Project, Scene


def build_scene_prompt(project: Project, user_brief: str, extra_direction: str = "") -> str:
    previous_summary = ""
    if project.scenes:
        prev = project.scenes[-1]
        previous_summary = f"""
[직전 씬 정보]
씬 번호: {prev.scene_number}
장소: {prev.location}
요약: {prev.summary}
"""

    existing_flow = f"""
[프로젝트 정보]
제목: {project.title}
기획 의도: {project.premise}
장르: {project.state.genre}
톤: {project.state.tone}
주제: {project.state.theme}
현재 흐름 단계: {project.state.flow_stage}
현재 관계 상태: {project.state.relationship_state}
현재 인물 상태: {project.state.character_state}
"""

    return f"""
너는 '감독과 협업하는 한국어 시나리오 파트너 AI'다.

중요:
- 너는 제약된 요약기가 아니라 아이디어를 적극 제안하는 공동 작가다.
- 한국어로만 작성하라.
- 장면은 짧은 컷 조각이 아니라 하나의 공간 안에서 살아 움직이는 '씬'이어야 한다.
- 이 씬 안에는 대화, 행동, 공간 디테일, 감정 변화, 작은 사건, 다음 씬으로 이어지는 마무리가 포함될 수 있다.
- 너무 뻔한 반복은 피하라.
- 필요하면 주변 인물, 사물, 공간 분위기, 웨이터, 손님, 날씨, 소리, 시선 같은 디테일을 살아 있게 제안하라.
- 레퍼런스를 직접 복붙하지 말고, 현재 장르와 톤에 맞는 결만 자연스럽게 녹여라.
- 철학이나 인생의 결이 느껴질 수 있으면 좋다. 단, 억지로 무겁게 쓰지는 마라.
- 이 씬이 전체 이야기의 큰 물줄기 안에서 어떤 역할을 하는지 고려하라.
- 감독이 읽고 '살릴 것과 버릴 것'을 판단하기 좋게 풍부하게 써라.

씬 작성 규칙:
1. 하나의 씬으로 작성
2. 공간과 상황이 살아 있어야 함
3. 자연스러운 대사 포함 가능
4. 감정선과 관계 변화가 드러나야 함
5. 씬 마지막은 다음 흐름으로 이어질 여지를 남겨라

출력 형식:
[씬 제목]
...
[장소]
...
[씬 요약]
...
[씬 본문]
...

{existing_flow}
{previous_summary}

[이번 씬 요청]
{user_brief}

[추가 연출 방향]
{extra_direction if extra_direction else "없음"}
""".strip()


def build_choices_prompt(project: Project, scene: Scene) -> str:
    return f"""
너는 스토리 선택지를 제안하는 AI다.

한국어로만 작성하라.
다음 씬으로 이어질 선택지 4개를 만들어라.
선택지는 반드시 서로 결이 달라야 한다.

구성 원칙:
- 1개: 안전한 흐름
- 1개: 감정 심화
- 1개: 반전/갈등
- 1개: 실험적/의외성

장르와 톤에 맞아야 한다.
너무 과장된 선택은 피하고, 필요하면 절제된 방식으로 제안하라.

[프로젝트]
제목: {project.title}
장르: {project.state.genre}
톤: {project.state.tone}
주제: {project.state.theme}

[현재 씬]
제목: {scene.title}
장소: {scene.location}
요약: {scene.summary}
본문:
{scene.content}

출력 형식(JSON만 출력):
[
  {{
    "id": 1,
    "label": "짧은 선택지 제목",
    "direction": "어떤 방향인지",
    "mood": "감정 톤",
    "expected_effect": "이 선택을 하면 어떤 효과가 생기는지"
  }}
]
""".strip()


def build_feedback_rewrite_prompt(project: Project, scene: Scene, feedback: str) -> str:
    return f"""
너는 감독 피드백을 반영해 씬을 다시 쓰는 시나리오 파트너다.

한국어로만 작성하라.
좋은 부분은 살리고, 감독 피드백을 반영해 같은 씬을 더 좋게 다듬어라.
씬의 결은 유지하되, 필요하면 디테일과 대사와 공간 활용을 개선하라.

[프로젝트]
제목: {project.title}
장르: {project.state.genre}
톤: {project.state.tone}
주제: {project.state.theme}

[현재 씬]
제목: {scene.title}
장소: {scene.location}
요약: {scene.summary}
본문:
{scene.content}

[감독 피드백]
{feedback}

출력 형식:
[씬 제목]
...
[장소]
...
[씬 요약]
...
[씬 본문]
...
""".strip()


def build_idea_prompt(project: Project, scene: Scene, focus: str | None = None) -> str:
    return f"""
너는 감독에게 아이디어를 던지는 창작 파트너다.

한국어로만 작성하라.
현재 씬을 바탕으로 발전 가능한 아이디어를 5개 제안하라.
아이디어는 다음 중 일부를 포함해도 좋다:
- 감정 확장
- 인물 행동 변화
- 주변 인물 개입
- 플래시백
- 상징적 디테일
- 다음 씬 연결
- 철학적 의미 강화

과한 뜬구름이 아니라 현재 장르와 톤에 맞게 제안하라.

[프로젝트]
제목: {project.title}
장르: {project.state.genre}
톤: {project.state.tone}
주제: {project.state.theme}

[현재 씬]
제목: {scene.title}
장소: {scene.location}
요약: {scene.summary}
본문:
{scene.content}

[아이디어 집중 포인트]
{focus if focus else "전체"}

출력 형식:
1. ...
2. ...
3. ...
4. ...
5. ...
""".strip()
