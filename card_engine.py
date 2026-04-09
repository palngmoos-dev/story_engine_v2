# card_engine.py

from copy import deepcopy


RELATION_LABELS = [
    (-999, -12, "완전 붕괴 직전"),
    (-11, -8, "파국 직전"),
    (-7, -4, "심한 긴장"),
    (-3, -1, "긴장"),
    (0, 0, "불확실"),
    (1, 3, "조심스러운 연결"),
    (4, 6, "강한 끌림"),
    (7, 9, "고백 직전"),
    (10, 999, "완전한 결속 직전"),
]

TEMPERATURE_LABELS = [
    (-999, -10, "빙점 붕괴"),
    (-9, -5, "냉각 위기"),
    (-4, -1, "차가운 긴장"),
    (0, 0, "중립"),
    (1, 4, "미세한 온기"),
    (5, 8, "가열 중"),
    (9, 999, "고온 결속"),
]


ENDING_RULES = [
    {
        "id": "healing_ss",
        "grade": "SS",
        "ending_type": "회복형 상위 엔딩",
        "title": "다시 이어진 숨결",
        "summary": "파열 직전의 관계를 여러 번 되살린 끝에, 회복이 단순한 미봉이 아니라 재연결로 완성된 엔딩.",
        "min_relation": 11,
        "min_goal": 90,
        "min_recovery_stack": 5,
        "min_recovery_success": 3,
        "epilogue_pool": [
            "무너졌던 장면은 완전히 지워지지 않았지만, 두 사람은 이번에는 같은 방향으로 걸어 나가기로 한다.",
            "상처의 흔적은 남아도, 이제는 그 틈을 다시 벌리기보다 함께 메우려는 의지가 더 크다.",
        ],
    },
    {
        "id": "happy_ss",
        "grade": "SS",
        "ending_type": "해결형 해피엔딩",
        "title": "끝내 마주본 두 사람",
        "summary": "감정과 목표가 모두 임계점에 도달해, 관계 회복과 진심 확인이 이루어진 엔딩.",
        "min_relation": 12,
        "min_goal": 95,
        "epilogue_pool": [
            "두 사람은 같은 장소를 떠나기 전, 더 이상 피하지 않기로 조용히 합의한다.",
            "끝나지 못했던 말들은 남아 있지만, 이제는 서로를 피할 이유보다 붙잡을 이유가 더 분명하다.",
        ],
    },
    {
        "id": "healing_a",
        "grade": "A",
        "ending_type": "회복형 엔딩",
        "title": "다시 닿은 온기",
        "summary": "완전한 해결에는 아직 이르지만, 다시 이어질 수 있다는 확신을 만든 엔딩.",
        "min_relation": 7,
        "min_goal": 75,
        "min_recovery_stack": 3,
        "min_recovery_success": 1,
        "epilogue_pool": [
            "두 사람은 아직 모든 오해를 다 풀지는 못했지만, 이번에는 정말 끝내지 않겠다는 마음만은 서로에게 남겼다.",
            "완벽한 화해는 아니어도, 적어도 이번에는 다시 등을 돌리지는 않겠다는 조심스러운 약속이 생겼다.",
        ],
    },
    {
        "id": "confession_a",
        "grade": "A",
        "ending_type": "고백형 엔딩",
        "title": "숨기지 못한 진심",
        "summary": "완전한 해결 직전이지만, 이미 고백과 상호 확인이 가능한 수준까지 도달한 엔딩.",
        "min_relation": 7,
        "min_goal": 70,
        "epilogue_pool": [
            "정답은 아직 멀더라도, 적어도 이번에는 진심을 숨기지 않았다는 사실이 둘을 붙잡는다.",
            "모든 게 해결된 건 아니지만, 이제는 관계를 움직이는 중심이 침묵이 아니라 진심이 되었다.",
        ],
    },
    {
        "id": "recovery_b",
        "grade": "B",
        "ending_type": "회복 직전 엔딩",
        "title": "다시 손이 닿기 시작한 거리",
        "summary": "완전한 회복에는 못 미쳤지만, 다시 이어질 수 있는 분명한 신호를 만든 엔딩.",
        "min_relation": 2,
        "min_goal": 45,
        "min_recovery_stack": 1,
        "epilogue_pool": [
            "완전히 풀린 건 아니지만, 다시 이어질 가능성은 분명히 살아남았다.",
            "정답은 아직 멀지만, 적어도 이번 장면은 단절이 아니라 유예로 끝난다.",
        ],
    },
    {
        "id": "open_b",
        "grade": "B",
        "ending_type": "열린 결말",
        "title": "아직 끝나지 않은 장면",
        "summary": "관계와 목표가 어느 한쪽으로 완전히 굳지 않아, 다음 장면을 남겨두는 엔딩.",
        "min_relation": 0,
        "min_goal": 35,
        "epilogue_pool": [
            "이 장면은 끝났지만, 다음 선택 하나가 전혀 다른 결말을 만들 수 있다.",
            "감정은 아직 흔들리고 있고, 다음 장면이 이 관계의 모양을 정하게 된다.",
        ],
    },
    {
        "id": "collapse_c",
        "grade": "C",
        "ending_type": "파국형 배드엔딩",
        "title": "돌아갈 수 없는 선",
        "summary": "관계와 목표가 완전히 붕괴해, 회복보다 단절이 확정된 엔딩.",
        "max_relation": -10,
        "max_goal": 10,
        "epilogue_pool": [
            "장면은 끝났지만, 둘 사이에 남은 건 미련보다 단절의 감각에 더 가깝다.",
            "멈춰 선 침묵은 더 이상 유예가 아니라, 관계의 종결선처럼 남는다.",
        ],
    },
]


def clone_cards(cards):
    return deepcopy(cards)


def create_character_card(name: str, emotion: int = 0, level: int = 1, goal: int = 50):
    return {
        "id": f"char_{name}",
        "type": "character",
        "name": name,
        "emotion": emotion,
        "level": level,
        "goal": goal,
        "goal_progress": 0,
        "skills": [],
        "speech_tag": "",
    }


def relation_label(score: int) -> str:
    for low, high, label in RELATION_LABELS:
        if low <= score <= high:
            return label
    return "불확실"


def relation_temperature(score: int) -> str:
    for low, high, label in TEMPERATURE_LABELS:
        if low <= score <= high:
            return label
    return "중립"

def scene_pressure(score: int) -> int:
    if score <= -9:
        return 2
    if score <= -1:
        return 1
    if score >= 9:
        return 2
    return 0


def ending_score_formula(relation_score: int, avg_goal: float, pressure: int, recovery_stack: int, diversity_score: float = 0.0) -> float:
    score = (relation_score * 4.0) + avg_goal - (pressure * 6.0) + (recovery_stack * 2.5) + diversity_score
    return round(score, 1)


def choose_ending(relation_score: int, avg_goal: float, recovery_stack: int, recovery_success: int, rng):
    for rule in ENDING_RULES:
        min_relation = rule.get("min_relation", -9999)
        min_goal = rule.get("min_goal", -9999)
        max_relation = rule.get("max_relation", 9999)
        max_goal = rule.get("max_goal", 9999)
        min_recovery_stack = rule.get("min_recovery_stack", -9999)
        min_recovery_success = rule.get("min_recovery_success", -9999)

        if (
            relation_score >= min_relation
            and avg_goal >= min_goal
            and relation_score <= max_relation
            and avg_goal <= max_goal
            and recovery_stack >= min_recovery_stack
            and recovery_success >= min_recovery_success
        ):
            selected = deepcopy(rule)
            selected["epilogue"] = rng.choice(selected["epilogue_pool"])
            return selected

    fallback = {
        "id": "fallback_open",
        "grade": "B",
        "ending_type": "열린 결말",
        "title": "아직 끝나지 않은 장면",
        "summary": "완전히 결론나지 않은 채, 다음 장면을 위한 여지를 남긴 엔딩.",
        "epilogue_pool": [
            "감정은 아직 흔들리고 있고, 다음 장면이 이 관계의 모양을 정하게 된다.",
        ],
    }
    fallback["epilogue"] = fallback["epilogue_pool"][0]
    return fallback


def build_character_status_card(chars):
    lines = ["=== 캐릭터 최종 상태 카드 ==="]
    for c in chars:
        lines.extend(
            [
                f"[{c['name']}]",
                f"- 감정: {c['emotion']}",
                f"- 레벨: {c['level']}",
                f"- 목표: {c['goal']}",
                f"- 목표 달성도: {c.get('goal_progress', 0)}",
                f"- 스킬: {', '.join(c.get('skills', []))}",
                f"- 말버릇 스타일: {c.get('speech_tag', '')}",
            ]
        )


def create_space_card(name: str, mood: str = "중립", pressure: int = 0, description: str = ""):
    return {
        "id": f"space_{name}",
        "type": "space",
        "name": name,
        "mood": mood,
        "pressure": pressure,
        "description": description,
    }

def create_event_card(name: str, impact: int = 0, description: str = ""):
    return {
        "id": f"event_{name}",
        "type": "event",
        "name": name,
        "impact": impact,
        "description": description,
    }

def create_object_card(name: str, symbolism: str = "", effect: str = "", description: str = ""):
    return {
        "id": f"object_{name}",
        "type": "object",
        "name": name,
        "symbolism": symbolism,
        "effect": effect,
        "description": description,
    }
    return "\n".join(lines)
