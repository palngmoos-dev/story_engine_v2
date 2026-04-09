import random
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


SYSTEM_PHILOSOPHY = """
이 시스템은 카드 기반 누적형 창작 엔진이다.
- AI는 방향과 추천을 만든다.
- 사용자는 선택과 강제 개입으로 흐름을 바꾼다.
- 감정 / 관계 / 목표 / 기억 / 루트가 동시 누적된다.
- 장면은 이전 선택의 결과를 먹고 자란다.
- 엔딩은 감이 아니라 규칙과 점수로 판정한다.
- 최종 출력은 장면, 추천, 상태, 엔딩, 리포트, Markdown, JSON 저장까지 이어진다.
""".strip()


@dataclass
class EndingState:
    relation: int
    avg_goal: float
    branch: str
    pressure: int
    recovery: int


ENDING_RULES = [
    {
        "ending_type": "해결형 해피엔딩",
        "title": "끝내 마주본 두 사람",
        "summary": "감정과 목표가 모두 임계점에 도달해, 관계 회복과 진심 확인이 이루어진 엔딩.",
        "condition": lambda s: s.relation >= 10 and s.avg_goal >= 90,
        "grade": lambda s: "SS" if s.relation >= 12 and s.avg_goal >= 97 else "S",
    },
    {
        "ending_type": "고백형 엔딩",
        "title": "숨기지 못한 진심",
        "summary": "완전한 해결 직전이지만, 이미 고백과 상호 확인이 가능한 수준까지 도달한 엔딩.",
        "condition": lambda s: s.relation >= 7 and s.avg_goal >= 70,
        "grade": lambda s: "A",
    },
    {
        "ending_type": "회복형 엔딩",
        "title": "금 간 틈을 다시 메우다",
        "summary": "무너졌던 관계를 다시 붙잡아, 최소한 회복 가능 상태까지 복원한 엔딩.",
        "condition": lambda s: s.recovery >= 2 and s.relation >= 2 and s.avg_goal >= 45,
        "grade": lambda s: "A",
    },
    {
        "ending_type": "회복 직전 엔딩",
        "title": "다시 손이 닿기 시작한 거리",
        "summary": "완전한 회복에는 못 미쳤지만, 다시 이어질 수 있는 분명한 신호를 만든 엔딩.",
        "condition": lambda s: s.recovery >= 1 and s.relation >= 0 and s.avg_goal >= 35,
        "grade": lambda s: "B",
    },
    {
        "ending_type": "파국형 배드엔딩",
        "title": "돌아갈 수 없는 선",
        "summary": "관계와 목표가 완전히 붕괴해, 회복보다 단절이 확정된 엔딩.",
        "condition": lambda s: s.relation <= -10 and s.avg_goal <= 10,
        "grade": lambda s: "C",
    },
    {
        "ending_type": "붕괴 직전 엔딩",
        "title": "끊어지기 직전의 관계",
        "summary": "아직 완전 종료는 아니지만, 다음 선택 하나면 파국으로 굳어질 상태의 엔딩.",
        "condition": lambda s: s.relation <= -7,
        "grade": lambda s: "C",
    },
    {
        "ending_type": "열린 결말",
        "title": "아직 끝나지 않은 장면",
        "summary": "관계와 목표가 어느 한쪽으로 완전히 굳지 않아, 다음 장면을 남겨두는 엔딩.",
        "condition": lambda s: True,
        "grade": lambda s: "B",
    },
]


CHOICE_WEIGHTS = {
    "main": {
        "다가간다": 1.20,
        "웃어버린다": 1.00,
        "감정을 터뜨린다": 0.95,
        "과거를 꺼낸다": 1.05,
        "침묵을 유지한다": 0.85,
        "거짓말을 한다": 0.75,
        "해결을 시도한다": 0.95,
        "회복을 시도한다": 1.00,
    },
    "closer_route": {
        "다가간다": 1.50,
        "고백한다": 1.35,
        "해결을 시도한다": 1.25,
        "과거를 꺼낸다": 1.10,
        "웃어버린다": 0.85,
        "회복을 시도한다": 0.95,
    },
    "resolution_route": {
        "해결을 시도한다": 1.75,
        "고백한다": 1.40,
        "다가간다": 1.10,
        "회복을 시도한다": 1.10,
    },
    "confession_route": {
        "고백한다": 1.55,
        "해결을 시도한다": 1.45,
        "다가간다": 1.00,
    },
    "memory_route": {
        "과거를 꺼낸다": 1.45,
        "해결을 시도한다": 1.25,
        "다가간다": 1.10,
        "회복을 시도한다": 1.15,
    },
    "silent_route": {
        "침묵을 유지한다": 1.35,
        "거짓말을 한다": 1.20,
        "자리를 떠난다": 1.10,
        "다가간다": 0.80,
        "회복을 시도한다": 1.20,
    },
    "leave_route": {
        "자리를 떠난다": 1.45,
        "파국을 선언한다": 1.20,
        "다가간다": 0.90,
        "회복을 시도한다": 1.35,
        "해결을 시도한다": 1.00,
    },
    "lie_route": {
        "거짓말을 한다": 1.45,
        "파국을 선언한다": 1.20,
        "침묵을 유지한다": 1.00,
        "회복을 시도한다": 1.25,
    },
    "collapse_route": {
        "파국을 선언한다": 1.75,
        "거짓말을 한다": 1.20,
        "자리를 떠난다": 1.10,
        "회복을 시도한다": 1.30,
    },
    "comeback_route": {
        "회복을 시도한다": 1.90,
        "해결을 시도한다": 1.50,
        "다가간다": 1.20,
        "과거를 꺼낸다": 1.10,
        "고백한다": 0.90,
    },
}


PERSONALITY_BIAS = {
    "차분": {
        "침묵을 유지한다": 1.20,
        "과거를 꺼낸다": 1.15,
        "해결을 시도한다": 1.10,
        "고백한다": 0.90,
        "회복을 시도한다": 1.10,
    },
    "직진": {
        "다가간다": 1.20,
        "감정을 터뜨린다": 1.15,
        "고백한다": 1.20,
        "파국을 선언한다": 1.05,
        "회복을 시도한다": 1.05,
    },
    "솔직": {
        "고백한다": 1.15,
        "해결을 시도한다": 1.10,
        "회복을 시도한다": 1.10,
    },
}


SCENE_TEMPLATES = {
    "main": [
        "같은 장소인데도 아직 감정의 좌표가 맞지 않는다.",
        "오래 묵은 말들이 아직 입 밖으로 나오지 못하고 맴돈다.",
    ],
    "closer_route": [
        "경계 속에서도 묘하게 둘 사이의 간격이 줄어든다.",
        "조심스러운 접근이 장면의 결을 바꾸기 시작한다.",
    ],
    "resolution_route": [
        "정면으로 대화하려는 의지가 장면을 조금씩 안정시킨다.",
        "감정의 매듭을 풀려는 기색이 서서히 드러난다.",
    ],
    "confession_route": [
        "말 한마디가 모든 균형을 뒤집을 수 있는 순간이다.",
        "진심이 더는 뒤로 물러설 수 없는 지점까지 밀려왔다.",
    ],
    "silent_route": [
        "침묵이 대화보다 더 많은 것을 말하고 있다.",
        "아무 말도 하지 않는 선택이 더 큰 긴장을 만든다.",
    ],
    "leave_route": [
        "멀어지려는 발걸음과 붙잡으려는 감정이 동시에 충돌한다.",
        "한 걸음 물러나는 움직임이 더 큰 균열을 부른다.",
    ],
    "lie_route": [
        "숨기려는 말이 오히려 장면을 더 무겁게 만든다.",
        "진실을 비껴간 대가가 공기 속에 쌓이기 시작한다.",
    ],
    "collapse_route": [
        "조금만 더 건드리면 완전히 부서질 것 같은 위태로움이 감돈다.",
        "장면 전체가 더는 되돌리기 어려운 선으로 밀려간다.",
    ],
    "comeback_route": [
        "한 번 금이 간 자리에서 다시 맞춰 보려는 신호가 생긴다.",
        "작지만 분명한 복원의 움직임이 장면 안으로 들어온다.",
    ],
}


def sort_cards(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(cards, key=lambda x: x.get("priority", 999))


def get(cards: List[Dict[str, Any]], t: str) -> List[Dict[str, Any]]:
    return [c for c in cards if c["type"] == t]


def relation_label(score: int) -> str:
    if score >= 10:
        return "완전한 결속 직전"
    if score >= 7:
        return "고백 직전"
    if score >= 5:
        return "강한 끌림"
    if score >= 2:
        return "조심스러운 연결"
    if score >= 1:
        return "미세한 완화"
    if score == 0:
        return "불확실"
    if score <= -10:
        return "완전 붕괴 직전"
    if score <= -7:
        return "파국 직전"
    if score <= -4:
        return "심한 긴장"
    return "긴장"


def relation_temperature(score: int) -> str:
    if score >= 10:
        return "고온 결속"
    if score >= 5:
        return "가열 중"
    if score >= 1:
        return "미세한 온기"
    if score == 0:
        return "중립"
    if score <= -10:
        return "빙점 붕괴"
    if score <= -5:
        return "냉각 위기"
    return "차가운 긴장"


def goal_progress_label(value: int) -> str:
    if value >= 90:
        return "목표 임계점"
    if value >= 70:
        return "거의 도달"
    if value >= 40:
        return "절반 이상 전진"
    if value >= 15:
        return "조금씩 접근 중"
    return "아직 멀다"


def scene_pressure(score: int, avg_goal: float) -> int:
    pressure = 0
    if score <= -4:
        pressure += 2
    elif score <= -1:
        pressure += 1
    if avg_goal >= 70:
        pressure += 1
    if score >= 8:
        pressure += 1
    return pressure


def relation_line(score: int) -> str:
    if score >= 4:
        return "상대를 밀어내기보다는 붙잡고 싶은 기색이 분명해진다."
    if score >= 1:
        return "경계는 남아 있지만, 예전보다 한 걸음 가까워진 공기가 있다."
    if score <= -4:
        return "말 한마디마다 상처와 반발이 먼저 튀어 오른다."
    if score <= -1:
        return "쉽게 믿지 못하는 긴장이 대사 사이에 남아 있다."
    return "아직 어느 쪽으로 기울지 모르는 거리감이 흐른다."


def skill_line(character: Dict[str, Any]) -> str:
    skills = character.get("skills", [])
    if "관찰" in skills:
        return "상대의 작은 표정 변화까지 놓치지 않는다."
    if "직감" in skills:
        return "말보다 먼저 분위기의 균열을 감지한다."
    if "회피" in skills:
        return "핵심을 바로 말하지 않고 비켜 나가려 한다."
    if "돌파" in skills:
        return "머뭇거리지 않고 감정의 핵심을 찌르려 한다."
    if "설득" in skills:
        return "감정을 정리해 상대를 움직일 말을 고른다."
    return "자기 방식대로 이 장면을 버티고 있다."


def pick_line(engine: Any, relation_score: int = 0) -> str:
    neutral = [
        "잠깐 침묵이 흐른다.",
        "시선이 엇갈린다.",
        "공기가 묘하게 무거워진다.",
        "아무 말도 하지 않지만 감정은 움직인다.",
        "짧은 숨이 서로의 말보다 더 크게 들린다.",
        "말보다 먼저 분위기가 감정을 밀어 올린다.",
    ]
    positive = [
        "서로의 거리 안에 잠깐 따뜻한 틈이 열린다.",
        "차갑던 장면 안에 미세한 온기가 섞인다.",
        "서늘했던 공기 속에 아주 약한 신뢰가 돌아온다.",
    ]
    negative = [
        "말끝마다 상처가 묻어나온다.",
        "공기 자체가 서로를 밀어내는 듯하다.",
        "같은 공간인데도 서로 다른 세계에 선 듯 멀다.",
    ]

    pool = neutral
    if relation_score >= 3:
        pool = neutral + positive
    elif relation_score <= -3:
        pool = neutral + negative

    used = set(engine.get_used_lines())
    fresh = [x for x in pool if x not in used]
    line = random.choice(fresh if fresh else pool)
    engine.remember_line(line)
    return line


def memory_bias(choice_memory: List[str], candidate: str) -> float:
    if not choice_memory:
        return 1.0

    bias = 1.0
    last = choice_memory[-1]
    recent = choice_memory[-3:]

    if last == candidate:
        bias *= 0.88
    if recent.count(candidate) >= 2:
        bias *= 0.85
    if candidate == "해결을 시도한다" and "과거를 꺼낸다" in recent:
        bias *= 1.10
    if candidate == "고백한다" and "다가간다" in recent:
        bias *= 1.08
    if candidate == "파국을 선언한다" and "거짓말을 한다" in recent:
        bias *= 1.12
    if candidate == "회복을 시도한다" and ("자리를 떠난다" in recent or "거짓말을 한다" in recent or "파국을 선언한다" in recent):
        bias *= 1.18

    return bias


def memory_note_bias(engine: Any, action: str) -> float:
    notes = " / ".join(engine.get_memory_notes()[-3:])
    if not notes:
        return 1.0

    weight = 1.0
    if action == "회복을 시도한다" and ("거짓말" in notes or "파국" in notes or "자리를 떠난다" in notes):
        weight *= 1.20
    if action == "해결을 시도한다" and ("과거를 꺼낸다" in notes or "회복을 시도한다" in notes):
        weight *= 1.12
    if action == "고백한다" and ("다가간다" in notes or "해결을 시도한다" in notes):
        weight *= 1.10
    if action == "파국을 선언한다" and ("거짓말" in notes and "관계 -" in notes):
        weight *= 1.15
    return weight


def choose_branch_name(choice: str, relation_score: int) -> str:
    route_table = {
        "고백한다": "confession_route",
        "해결을 시도한다": "resolution_route",
        "파국을 선언한다": "collapse_route",
        "침묵을 유지한다": "silent_route",
        "거짓말을 한다": "lie_route",
        "과거를 꺼낸다": "memory_route",
        "선을 넘는다": "break_route",
        "자리를 떠난다": "leave_route",
        "감정을 터뜨린다": "burst_route",
        "웃어버린다": "mask_route",
        "회복을 시도한다": "comeback_route",
    }
    if choice == "다가간다":
        return "closer_route" if relation_score >= 0 else "comeback_route"
    return route_table.get(choice, "main")


def apply_choice_to_relation(engine: Any, cards: List[Dict[str, Any]], choice: str) -> None:
    chars = get(cards, "character")
    if len(chars) < 2:
        return

    a = chars[0]["name"]
    b = chars[1]["name"]

    delta_map = {
        "다가간다": 2,
        "침묵을 유지한다": -1,
        "거짓말을 한다": -2,
        "과거를 꺼낸다": 1,
        "선을 넘는다": -3,
        "감정을 터뜨린다": -1,
        "자리를 떠난다": -2,
        "웃어버린다": 1,
        "고백한다": 3,
        "해결을 시도한다": 2,
        "파국을 선언한다": -4,
        "회복을 시도한다": 4,
    }
    engine.update_relation(a, b, delta_map.get(choice, 0))


def apply_choice_to_goal_progress(engine: Any, cards: List[Dict[str, Any]], choice: str) -> None:
    chars = get(cards, "character")
    if len(chars) < 2:
        return

    a = chars[0]["name"]
    b = chars[1]["name"]

    delta_map = {
        "다가간다": (10, 10),
        "과거를 꺼낸다": (15, 15),
        "침묵을 유지한다": (-5, -5),
        "거짓말을 한다": (-10, -10),
        "자리를 떠난다": (-10, -5),
        "감정을 터뜨린다": (5, 0),
        "고백한다": (25, 20),
        "웃어버린다": (5, 5),
        "해결을 시도한다": (20, 20),
        "파국을 선언한다": (-20, -20),
        "회복을 시도한다": (22, 22),
    }
    da, db = delta_map.get(choice, (0, 0))
    engine.update_goal_progress(a, da)
    engine.update_goal_progress(b, db)


def apply_choice_to_emotions(cards: List[Dict[str, Any]], choice: str) -> List[Dict[str, Any]]:
    if not choice:
        return cards

    chars = get(cards, "character")

    if len(chars) >= 1:
        chars[0]["emotion"] = {
            "고백한다": "결심과 두려움이 동시에 생김",
            "해결을 시도한다": "정면으로 마주할 준비가 생김",
            "파국을 선언한다": "완전히 무너질 각오를 함",
            "다가간다": "망설이면서도 끌림",
            "침묵을 유지한다": "감정을 더 숨김",
            "자리를 떠난다": "회피와 죄책감이 동시에 생김",
            "웃어버린다": "아픔을 감춘 채 웃음으로 넘김",
            "과거를 꺼낸다": "억눌렀던 감정이 떠오름",
            "거짓말을 한다": "불안이 더 짙어짐",
            "감정을 터뜨린다": "참고 있던 감정이 무너짐",
            "회복을 시도한다": "후회 끝에 붙잡을 용기가 생김",
        }.get(choice, chars[0].get("emotion", "흔들림"))

    if len(chars) >= 2:
        chars[1]["emotion"] = {
            "고백한다": "당황과 흔들림이 크게 번짐",
            "해결을 시도한다": "경계 속에서도 풀어보려는 마음이 생김",
            "파국을 선언한다": "붙잡고 싶은 마음과 분노가 충돌함",
            "다가간다": "기대와 경계가 함께 생김",
            "침묵을 유지한다": "답답함이 커짐",
            "자리를 떠난다": "붙잡고 싶은 마음이 커짐",
            "웃어버린다": "허탈함과 미련이 함께 남음",
            "과거를 꺼낸다": "상처와 기대가 동시에 살아남",
            "거짓말을 한다": "의심이 커짐",
            "감정을 터뜨린다": "당황과 분노가 교차함",
            "회복을 시도한다": "조심스럽게 다시 믿어볼 여지가 생김",
        }.get(choice, chars[1].get("emotion", "긴장"))

    return cards


def record_memory_after_choice(engine: Any, cards: List[Dict[str, Any]], choice: str) -> None:
    chars = get(cards, "character")
    if len(chars) < 2:
        return

    a = chars[0]["name"]
    b = chars[1]["name"]
    relation_score = engine.get_relation(a, b)
    avg_goal = engine.average_goal_progress()
    note = f"{choice} 이후 관계 {relation_score}, 평균 목표 {avg_goal}, 현재 루트 {engine.get_branch()}"
    engine.add_memory_note(note)


def build_memory_summary(engine: Any) -> str:
    notes = engine.get_memory_notes()[-2:]
    if not notes:
        return "아직 강한 누적 기억은 형성되지 않았다."
    return " / ".join(notes)


def _style_prefix(character: Dict[str, Any]) -> str:
    style = character.get("speech_style", "")
    if style:
        return style
    if character.get("name") == "지훈":
        return "..."
    if character.get("name") == "수아":
        return ""
    return ""


def choose_dialogue(
    character: Dict[str, Any],
    last_choice: str,
    relation_score: int = 0,
    goal_progress: int = 0,
    memory_summary: str = "",
) -> str:
    name = character["name"]
    personality = character.get("personality", "")
    goal = character.get("goal", "")
    prefix = _style_prefix(character)

    if last_choice == "고백한다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}좋아한다고 말하면, 이제는 피할 수 없겠지."'
        return f'{name}: "{prefix}이제는 숨기지 않을게."'

    if last_choice == "해결을 시도한다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}끝내지 말고, 여기서부터 다시 풀어보자."'
        return f'{name}: "{prefix}전부 되돌릴 순 없어도, 정리할 수는 있어."'

    if last_choice == "파국을 선언한다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}이대로면 우리 진짜 끝이야."'
        return f'{name}: "{prefix}여기서 더 가면 아무것도 못 되돌려."'

    if last_choice == "다가간다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}이번엔 피하지 말고, 내 눈 보고 말해."'
        return f'{name}: "{prefix}생각보다 가까이 오네."'

    if last_choice == "침묵을 유지한다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}또 그렇게 아무 말도 안 하네."'
        return f'{name}: "{prefix}"'

    if last_choice == "자리를 떠난다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}도망치지 마. 이번엔 여기서 끝내."'
        return f'{name}: "{prefix}잠깐만. 난 아직 정리가 안 돼."'

    if last_choice == "웃어버린다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}웃기지? 결국 또 여기서 마주쳤네."'
        return f'{name}: "{prefix}헛웃음밖에 안 나오네."'

    if last_choice == "과거를 꺼낸다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}그때 왜 아무 말도 안 했는지, 난 아직 기억해."'
        return f'{name}: "{prefix}그날의 일은 아직 끝난 적이 없어."'

    if last_choice == "회복을 시도한다":
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}이번엔 정말 다시 맞춰 보자."'
        return f'{name}: "{prefix}아직 늦지 않았다면, 다시 해보고 싶어."'

    if relation_score >= 8 and goal_progress >= 70:
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}이제는 정말 숨기고 싶지 않아."'
        return f'{name}: "{prefix}{goal} 쪽으로 거의 다 왔어."'

    if relation_score <= -8 and goal_progress <= 10:
        if "직진" in personality or "솔직" in personality:
            return f'{name}: "{prefix}이건 그냥 끝이라고 봐야 해."'
        return f'{name}: "{prefix}여기서 멈추는 게 마지막일지도 몰라."'

    if "차분" in personality and "관계 -" in memory_summary:
        return f'{name}: "{prefix}계속 어긋난 기억이 남아 있어."'

    if "차분" in personality:
        return f'{name}: "{prefix}이 상황, 피할 수는 없겠네."'
    if "직진" in personality or "솔직" in personality:
        return f'{name}: "{prefix}이번엔 그냥 넘어가지 않을 거야."'
    return f'{name}: "이상하게 꼬이네."'



def choose_space_variant(base_mood: str, branch: str, pressure: int) -> str:
    branch_mood = {
        "confession_route": "말 한마디가 모든 걸 바꿔버릴 것 같은 정적이 흐른다.",
        "resolution_route": "오래 멈춰 있던 감정이 조금씩 제자리를 찾는 기류가 감돈다.",
        "collapse_route": "지금 건드리면 모든 게 무너질 것 같은 위태로움이 맴돈다.",
        "leave_route": "떠나려는 발걸음과 붙잡으려는 시선이 공기를 갈라놓는다.",
        "silent_route": "침묵이 소리보다 더 날카롭게 둘 사이를 가른다.",
        "closer_route": "경계 속에서도 이상하게 거리가 조금씩 좁아진다.",
        "comeback_route": "부서졌던 기류 사이로 아주 미세한 복원 신호가 감돈다.",
    }.get(branch, "")

    pressure_line = ""
    if pressure >= 3:
        pressure_line = "지금 선택 하나가 장면 전체를 무너뜨리거나 살릴 수 있다."
    elif pressure == 2:
        pressure_line = "감정의 밀도가 높아져 작은 말도 크게 흔들린다."

    parts = [x for x in [base_mood, branch_mood, pressure_line] if x]
    return ", ".join(parts)


def choose_event_variant(base_event_name: str, last_choice: str) -> str:
    if last_choice == "고백한다":
        return f"{base_event_name}가 더 이상 숨길 수 없는 진심의 순간으로 번진다"
    if last_choice == "해결을 시도한다":
        return f"{base_event_name}가 정면 대화와 복구의 순간으로 번진다"
    if last_choice == "파국을 선언한다":
        return f"{base_event_name}가 돌이킬 수 없는 파열의 순간으로 번진다"
    if last_choice == "자리를 떠난다":
        return f"{base_event_name}가 이탈과 추격의 기류로 번지는 순간"
    if last_choice == "다가간다":
        return f"{base_event_name}가 거리의 변화를 드러내기 시작한 순간"
    if last_choice == "과거를 꺼낸다":
        return f"{base_event_name}가 묻혀 있던 기억을 다시 건드리는 순간"
    if last_choice == "회복을 시도한다":
        return f"{base_event_name}가 다시 맞춰 보려는 움직임으로 번지는 순간"
    return base_event_name or "이름 없는 사건"


def pick_scene_template(branch: str) -> str:
    pool = SCENE_TEMPLATES.get(branch, SCENE_TEMPLATES["main"])
    return random.choice(pool)


def generate_scene(
    cards: List[Dict[str, Any]],
    engine: Any,
    relation_score: int = 0,
    scene_no: int = 1,
    branch: str = "main",
) -> str:
    cards = sort_cards(cards)
    last_choice = engine.get_last_choice()
    cards = apply_choice_to_emotions(cards, last_choice)

    chars = get(cards, "character")
    space = get(cards, "space")
    event = get(cards, "event")
    obj = get(cards, "object")

    avg_goal = round(sum(c.get("goal_progress", 0) for c in chars) / len(chars), 1) if chars else 0.0
    pressure = scene_pressure(relation_score, avg_goal)
    place = space[0]["name"] if space else "어딘가"
    mood = choose_space_variant(space[0].get("mood", "") if space else "", branch, pressure)
    event_name = choose_event_variant(event[0]["name"] if event else "", last_choice)
    event_effect = event[0].get("effect", "") if event else ""
    memory_summary = build_memory_summary(engine)
    template_line = pick_scene_template(branch)

    text = f"[장면 {scene_no} 시작]\n"
    text += f"장소: {place}\n"
    text += f"분위기: {mood}\n"
    text += f"핵심 사건: {event_name}\n"
    text += f"사건 의미: {event_effect}\n"
    text += f"장면 템플릿: {template_line}\n"
    text += f"현재 루트: {branch}\n"
    text += f"현재 관계 단계: {relation_label(relation_score)} ({relation_score})\n"
    text += f"관계 온도: {relation_temperature(relation_score)}\n"
    text += f"장면 압력: {pressure}\n"
    text += f"평균 목표 달성도: {avg_goal}\n"
    text += f"누적 기억 요약: {memory_summary}\n"
    if last_choice:
        text += f"이전 선택 반영: {last_choice}\n"
    text += "\n"

    for ch in chars:
        text += choose_dialogue(
            ch,
            last_choice,
            relation_score,
            ch.get("goal_progress", 0),
            memory_summary,
        ) + "\n"
        text += f"(속마음: {ch.get('internal', '')})\n"
        text += f"(현재 감정: {ch.get('emotion', '')})\n"
        text += f"(말투: {ch.get('tone', '')})\n"
        text += f"(현재 목표: {ch.get('goal', '')})\n"
        text += f"(목표 달성도: {ch.get('goal_progress', 0)} / {goal_progress_label(ch.get('goal_progress', 0))})\n"
        text += f"(관계 기류: {relation_line(relation_score)})\n"
        text += f"(스킬 작동: {skill_line(ch)})\n"
        text += pick_line(engine, relation_score) + "\n\n"

    if obj:
        text += f"(소품: {obj[0]['name']} — {obj[0].get('purpose', '')})\n"
        text += "그 소품이 장면의 감정선을 미세하게 흔든다.\n\n"

    text += f"[장면 {scene_no} 끝]"
    return text


def build_base_actions(relation_score: int, avg_goal: float) -> List[str]:
    if relation_score >= 4 and avg_goal >= 20:
        return ["고백한다", "해결을 시도한다", "다가간다", "과거를 꺼낸다", "회복을 시도한다"]
    if relation_score <= -3 and avg_goal <= 20:
        return ["파국을 선언한다", "자리를 떠난다", "거짓말을 한다", "침묵을 유지한다", "회복을 시도한다"]
    return ["다가간다", "웃어버린다", "감정을 터뜨린다", "과거를 꺼낸다", "침묵을 유지한다", "회복을 시도한다"]


def weighted_next_choices(engine: Any, cards: List[Dict[str, Any]], relation_score: int) -> Tuple[List[str], List[Tuple[str, float, str]]]:
    chars = get(cards, "character")
    avg_goal = round(sum(c.get("goal_progress", 0) for c in chars) / len(chars), 1) if chars else 0.0
    branch = engine.get_branch()
    base_actions = build_base_actions(relation_score, avg_goal)
    recent_choices = engine.get_recent_choices(limit=3)

    scored: List[Tuple[str, float, str]] = []

    for action in base_actions:
        reason_bits: List[str] = []
        weight = 1.0

        route_weight = CHOICE_WEIGHTS.get(branch, {}).get(action, 1.0)
        weight *= route_weight
        if route_weight != 1.0:
            reason_bits.append(f"루트 보정 {route_weight}")

        for ch in chars:
            personality = ch.get("personality", "")
            if personality in PERSONALITY_BIAS:
                p_weight = PERSONALITY_BIAS[personality].get(action, 1.0)
                weight *= p_weight
                if p_weight != 1.0:
                    reason_bits.append(f"{ch['name']} 성향 보정 {p_weight}")

        m_weight = memory_bias(recent_choices, action)
        weight *= m_weight
        if m_weight != 1.0:
            reason_bits.append(f"기억 보정 {round(m_weight, 2)}")

        note_weight = memory_note_bias(engine, action)
        weight *= note_weight
        if note_weight != 1.0:
            reason_bits.append(f"기억 노트 보정 {round(note_weight, 2)}")

        if action == "해결을 시도한다" and relation_score >= 3:
            weight *= 1.2
            reason_bits.append("관계 회복 보정 1.2")
        if action == "고백한다" and relation_score >= 6 and avg_goal >= 50:
            weight *= 1.25
            reason_bits.append("고백 임계 보정 1.25")
        if action == "파국을 선언한다" and relation_score <= -6:
            weight *= 1.25
            reason_bits.append("붕괴 임계 보정 1.25")
        if action == "회복을 시도한다" and relation_score <= -2:
            weight *= 1.22
            reason_bits.append("회복 필요 보정 1.22")
        if action == "회복을 시도한다" and branch in ["leave_route", "collapse_route", "lie_route", "silent_route"]:
            weight *= 1.18
            reason_bits.append("붕괴 루트 회복 보정 1.18")

        weight = max(weight, 0.05)
        scored.append((action, round(weight, 4), ", ".join(reason_bits) if reason_bits else "기본값"))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _, _ in scored[:3]], scored


def generate_recommendation(engine: Any, cards: List[Dict[str, Any]], relation_score: int = 0) -> Dict[str, Any]:
    chars = get(cards, "character")
    avg_goal = round(sum(c.get("goal_progress", 0) for c in chars) / len(chars), 1) if chars else 0.0
    next_choices, scored = weighted_next_choices(engine, cards, relation_score)

    if relation_score >= 4 and avg_goal >= 20:
        principle = "가까워진 관계와 올라간 목표 진행도는 해결·고백 계열 선택을 강하게 밀어준다."
        reason = "관계와 목표 진행도가 모두 올라와 있어서 해결·고백 계열 선택이 가장 자연스럽다."
    elif relation_score <= -3 and avg_goal <= 20:
        principle = "금이 간 관계와 멈춘 목표 진행도는 파국·이탈 계열 선택을 강하게 부른다."
        reason = "관계와 목표 진행도가 모두 낮아서 파국·이탈·방어 계열 선택이 가장 자연스럽다."
    else:
        principle = "불확실한 관계는 작은 선택 하나가 장면의 결을 크게 바꾼다."
        reason = "관계와 목표가 아직 중간 구간이라 여러 방향으로 갈 수 있다."

    return {
        "suggestion": next_choices[0],
        "reason": reason,
        "principle": principle,
        "direction": "이번 선택이 감정, 관계, 목표, 다음 루트를 동시에 바꾸게 설계하라.",
        "next_choices": next_choices,
        "weights": scored,
    }


def evaluate_ending(engine: Any) -> Dict[str, Any]:
    chars = engine.get_characters()
    if len(chars) < 2:
        return {
            "ending_type": "미정",
            "title": "판정 불가",
            "summary": "캐릭터가 부족해 엔딩을 판정할 수 없다.",
            "score": {"relation": 0, "avg_goal_progress": 0.0, "branch": engine.get_branch(), "ending_score": 0},
            "grade": "C",
        }

    relation_score = engine.get_relation(chars[0]["name"], chars[1]["name"])
    avg_goal = engine.average_goal_progress()
    branch = engine.get_branch()
    pressure = scene_pressure(relation_score, avg_goal)
    recovery_count = engine.get_recovery_count()

    ending_score = round((relation_score * 4) + (avg_goal * 0.8) - (pressure * 3) + (recovery_count * 7), 1)

    state = EndingState(
        relation=relation_score,
        avg_goal=avg_goal,
        branch=branch,
        pressure=pressure,
        recovery=recovery_count,
    )

    for rule in ENDING_RULES:
        if rule["condition"](state):
            return {
                "ending_type": rule["ending_type"],
                "title": rule["title"],
                "summary": rule["summary"],
                "score": {
                    "relation": relation_score,
                    "avg_goal_progress": avg_goal,
                    "branch": branch,
                    "ending_score": ending_score,
                    "pressure": pressure,
                    "recovery_count": recovery_count,
                },
                "grade": rule["grade"](state),
            }

    return {
        "ending_type": "열린 결말",
        "title": "아직 끝나지 않은 장면",
        "summary": "관계와 목표가 어느 한쪽으로 완전히 굳지 않아, 다음 장면을 남겨두는 엔딩.",
        "score": {
            "relation": relation_score,
            "avg_goal_progress": avg_goal,
            "branch": branch,
            "ending_score": ending_score,
            "pressure": pressure,
            "recovery_count": recovery_count,
        },
        "grade": "B",
    }


def render_ending_card(ending_data: Dict[str, Any]) -> str:
    return (
        "=== 엔딩 카드 ===\n"
        f"등급: {ending_data['grade']}\n"
        f"엔딩 타입: {ending_data['ending_type']}\n"
        f"엔딩 제목: {ending_data['title']}\n"
        f"엔딩 요약: {ending_data['summary']}\n"
        f"최종 루트: {ending_data['score']['branch']}\n"
        f"최종 관계 수치: {ending_data['score']['relation']}\n"
        f"최종 평균 목표 달성도: {ending_data['score']['avg_goal_progress']}\n"
        f"엔딩 점수: {ending_data['score']['ending_score']}\n"
        f"장면 압력: {ending_data['score']['pressure']}\n"
        f"회복 시도 누적: {ending_data['score']['recovery_count']}\n"
    )


def build_epilogue(engine: Any) -> str:
    ending = engine.get_ending()
    if not ending:
        return "에필로그 없음"

    ending_type = ending["ending_type"]

    if ending_type == "해결형 해피엔딩":
        return "두 사람은 같은 장소를 떠나기 전, 더 이상 피하지 않기로 조용히 합의한다."
    if ending_type == "고백형 엔딩":
        return "정답은 아직 다 나오지 않았지만, 최소한 진심만큼은 서로에게 도착했다."
    if ending_type == "회복형 엔딩":
        return "금이 간 자리는 남아 있지만, 이번에는 그 틈을 함께 메워 보기로 한다."
    if ending_type == "회복 직전 엔딩":
        return "완전히 풀린 건 아니지만, 다시 이어질 가능성은 분명히 살아남았다."
    if ending_type == "파국형 배드엔딩":
        return "장면은 끝났지만, 둘 사이에 남은 건 미련보다 단절의 감각에 더 가깝다."
    if ending_type == "붕괴 직전 엔딩":
        return "아직 끝났다고 말하긴 이르지만, 다시 붙잡기엔 너무 많은 금이 가 있다."
    return "이 장면은 닫혔지만, 이야기는 아직 완전히 끝나지 않았다."


def render_epilogue_card(engine: Any) -> str:
    text = build_epilogue(engine)
    engine.set_epilogue(text)
    return "=== 에필로그 카드 ===\n" + text


def render_character_final_cards(engine: Any) -> str:
    chars = engine.get_characters()
    lines = ["=== 캐릭터 최종 상태 카드 ==="]
    for c in chars:
        lines.append(f"[{c['name']}]")
        lines.append(f"- 감정: {c.get('emotion', '')}")
        lines.append(f"- 레벨: {c.get('level', 1)}")
        lines.append(f"- 목표: {c.get('goal', '')}")
        lines.append(f"- 목표 달성도: {c.get('goal_progress', 0)}")
        lines.append(f"- 스킬: {', '.join(c.get('skills', []))}")
        lines.append(f"- 말버릇 스타일: {c.get('speech_style', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def render_final_report(engine: Any) -> str:
    chars = engine.get_characters()
    lines: List[str] = []
    lines.append("=== 최종 요약 리포트 ===")
    lines.append(f"프로젝트명: {engine.get_project()['name']}")
    lines.append(f"누적 장면 수: {engine.get_scene_count()}")
    lines.append(f"최종 루트: {engine.get_branch()}")
    lines.append(f"평균 목표 달성도: {engine.average_goal_progress()}")
    lines.append(f"통계: {engine.get_stats()}")
    lines.append("")

    for c in chars:
        lines.append(str({
            "name": c["name"],
            "emotion": c["emotion"],
            "level": c["level"],
            "goal": c.get("goal", ""),
            "goal_progress": c.get("goal_progress", 0),
        }))

    lines.append("")
    lines.append("선택 로그:")
    for item in engine.get_choice_log():
        lines.append(str(item))

    lines.append("")
    lines.append("기억 로그:")
    for note in engine.get_memory_notes():
        lines.append(f"- {note}")

    lines.append("")
    lines.append("루트 전이 로그:")
    for item in engine.get_route_transitions():
        lines.append(str(item))

    if engine.get_epilogue():
        lines.append("")
        lines.append("에필로그:")
        lines.append(engine.get_epilogue())

    return "\n".join(lines)


def render_comparison_summary(results: List[Dict[str, Any]]) -> str:
    lines = ["=== 3루트 비교 요약 ==="]
    for r in results:
        lines.append(
            f"{r['name']} | 등급 {r['grade']} | {r['ending_type']} | "
            f"루트 {r['branch']} | 관계 {r['relation']} | 목표 {r['avg_goal']} | 점수 {r['ending_score']}"
        )
    return "\n".join(lines)


def render_seed_summary(seed_results: List[Dict[str, Any]]) -> str:
    lines = ["=== 멀티 시드 자동 테스트 요약 ==="]
    if not seed_results:
        lines.append("시드 결과 없음")
        return "\n".join(lines)

    counter = Counter([r["ending_type"] for r in seed_results])
    for ending_name, count in counter.items():
        lines.append(f"{ending_name}: {count}")

    lines.append("")
    lines.append("상세:")
    for r in seed_results:
        lines.append(
            f"seed={r['seed']} | {r['ending_type']} | grade={r['grade']} | "
            f"branch={r['branch']} | relation={r['relation']} | goal={r['avg_goal']} | score={r['ending_score']}"
        )
    return "\n".join(lines)


def render_status(cards: List[Dict[str, Any]], engine: Any) -> str:
    chars = get(cards, "character")
    relation_score = 0
    if len(chars) >= 2:
        relation_score = engine.get_relation(chars[0]["name"], chars[1]["name"])

    avg_goal = engine.average_goal_progress()

    lines = [
        "=== 상태창 ===",
        f"현재 루트: {engine.get_branch()}",
        f"누적 장면 수: {engine.get_scene_count()}",
        f"평균 목표 달성도: {avg_goal}",
        f"관계 단계: {relation_label(relation_score)} ({relation_score})",
        f"관계 온도: {relation_temperature(relation_score)}",
        f"장면 압력: {scene_pressure(relation_score, avg_goal)}",
        f"회복 시도 누적: {engine.get_recovery_count()}",
        ""
    ]

    for c in chars:
        lines.append(str({
            "name": c["name"],
            "emotion": c["emotion"],
            "level": c["level"],
            "goal": c.get("goal", ""),
            "goal_progress": c.get("goal_progress", 0),
            "skills": c.get("skills", []),
            "last_choice": engine.get_last_choice(),
        }))
    return "\n".join(lines)


def export_markdown(engine: Any) -> str:
    lines: List[str] = []
    lines.append(f"# 프로젝트: {engine.get_project()['name']}")
    lines.append("")
    lines.append("## 시스템 철학")
    lines.append(SYSTEM_PHILOSOPHY)
    lines.append("")
    lines.append("## 상태")
    lines.append(f"- 루트: {engine.get_branch()}")
    lines.append(f"- 장면 수: {engine.get_scene_count()}")
    lines.append(f"- 평균 목표 달성도: {engine.average_goal_progress()}")
    lines.append(f"- 회복 시도 누적: {engine.get_recovery_count()}")
    lines.append("")
    lines.append("## 장면 히스토리")
    for idx, scene in enumerate(engine.get_history(), start=1):
        lines.append(f"### Scene {idx}")
        lines.append("```text")
        lines.append(scene)
        lines.append("```")
        lines.append("")
    if engine.get_ending():
        lines.append("## 엔딩")
        lines.append("```text")
        lines.append(render_ending_card(engine.get_ending()))
        lines.append("```")
    if engine.get_epilogue():
        lines.append("## 에필로그")
        lines.append(engine.get_epilogue())
    return "\n".join(lines)


def validate_system(engine: Any) -> List[str]:
    errors: List[str] = []
    chars = engine.get_characters()

    if len(chars) < 2:
        errors.append("캐릭터 카드가 2개 미만")
    if not engine.get_scene_cards():
        errors.append("활성 카드 없음")
    if engine.get_scene_count() < 0:
        errors.append("scene_count 음수")
    avg_goal = engine.average_goal_progress()
    if avg_goal < 0 or avg_goal > 100:
        errors.append("평균 목표 달성도 범위 오류")
    if engine.get_branch() == "":
        errors.append("branch 비어 있음")
    if engine.get_recovery_count() < 0:
        errors.append("recovery_count 음수")
    return errors
