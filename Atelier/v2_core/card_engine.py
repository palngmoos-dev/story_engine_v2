"""
Card Engine for Narrative Simulation.
Manages Character, Space (Table), and Prop/Event cards.
"""

import uuid

class Character:
    def __init__(self, name, age=0, gender="", mbti="", occupation="", background="", relationship="", 
                 personality="", flaw="", skill="", level=1, role="Support",
                 speech_style="", secret="", base_impact=None,
                 cid=None, origin_id=None, variant_info=None):
        self.cid = cid or f"char_{uuid.uuid4().hex[:6]}"
        self.origin_id = origin_id
        self.variant_info = variant_info or {} # e.g. {"timeline": "PRESENT", "type": "ORIGINAL"}
        self.name = name
        self.age = age
        self.gender = gender
        self.mbti = mbti
        self.occupation = occupation
        self.background = background
        self.relationship = relationship
        self.personality = personality
        self.flaw = flaw
        self.skill = skill
        self.level = level
        self.role = role # "Lead" or "Support"
        self.speech_style = speech_style
        self.secret = secret
        
        if base_impact is None:
            self.base_impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.base_impact = base_impact

    def to_dict(self):
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "occupation": self.occupation,
            "background": self.background,
            "relationship": self.relationship,
            "personality": self.personality,
            "flaw": self.flaw,
            "skill": self.skill,
            "level": self.level,
            "role": self.role,
            "speech_style": self.speech_style,
            "secret": self.secret,
            "base_impact": self.base_impact,
            "cid": self.cid,
            "origin_id": self.origin_id,
            "variant_info": self.variant_info
        }

class Space:
    """The 'Table' card indicating the environment."""
    def __init__(self, name, description="", weight_modifiers=None, base_impact=None,
                 cid=None, origin_id=None, variant_info=None):
        self.cid = cid or f"space_{uuid.uuid4().hex[:6]}"
        self.origin_id = origin_id
        self.variant_info = variant_info or {}
        self.name = name
        self.description = description
        
        if weight_modifiers is None:
            self.weight_modifiers = {}
        else:
            self.weight_modifiers = weight_modifiers
            
        if base_impact is None:
            self.base_impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.base_impact = base_impact

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "weight_modifiers": self.weight_modifiers,
            "base_impact": self.base_impact,
            "cid": self.cid,
            "origin_id": self.origin_id,
            "variant_info": self.variant_info
        }

class Prop:
    """Mise-en-scène cards (Items, Objects)."""
    def __init__(self, name, description="", impact=None,
                 cid=None, origin_id=None, variant_info=None):
        self.cid = cid or f"prop_{uuid.uuid4().hex[:6]}"
        self.origin_id = origin_id
        self.variant_info = variant_info or {}
        self.name = name
        self.description = description
        
        if impact is None:
            self.impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.impact = impact

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "impact": self.impact,
            "cid": self.cid,
            "origin_id": self.origin_id,
            "variant_info": self.variant_info
        }

class Card:
    """Basic Event or Action cards."""
    def __init__(self, name, impact=None, description="",
                 cid=None, origin_id=None, variant_info=None):
        self.cid = cid or f"card_{uuid.uuid4().hex[:6]}"
        self.origin_id = origin_id
        self.variant_info = variant_info or {}
        self.name = name
        self.description = description
        
        if impact is None:
            self.impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.impact = impact

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "impact": self.impact
        }

# --- Card Registry System ---
# TODO: In the future, this Registry class could support loading data from JSON or YAML files.
class CardRegistry:
    def __init__(self):
        self._characters = {}
        self._spaces = {}
        self._props = {}
        self._cards = {}
        self._others = {} # For all other card types

    def register_character(self, key, char_obj):
        if key in self._characters:
            print(f"Warning: Character key '{key}' already exists. Overwriting.")
        self._characters[key] = char_obj

    def register_space(self, key, space_obj):
        if key in self._spaces:
            print(f"Warning: Space key '{key}' already exists. Overwriting.")
        self._spaces[key] = space_obj

    def register_prop(self, key, prop_obj):
        if key in self._props:
            print(f"Warning: Prop key '{key}' already exists. Overwriting.")
        self._props[key] = prop_obj

    def register_card(self, key, card_obj):
        if key in self._cards:
            print(f"Warning: Card key '{key}' already exists. Overwriting.")
        self._cards[key] = card_obj

    def register_other(self, category, key, value):
        if category not in self._others: self._others[category] = {}
        if key in self._others[category]:
            print(f"Warning: Key '{key}' already exists in category '{category}'. Overwriting.")
        self._others[category][key] = value

    def get_character(self, key): return self._characters.get(key)
    def get_space(self, key): return self._spaces.get(key)
    def get_prop(self, key): return self._props.get(key)
    def get_card(self, key): return self._cards.get(key)
    def get_other(self, category, key): return self._others.get(category, {}).get(key)
    
    def get_all_keys(self):
        """명시적 매핑 테이블을 사용하여 카테고리명을 정리합니다."""
        mapping = {
            "time": "times", "cinematic": "cinematics", "mood": "moods",
            "sense": "senses", "element": "elements", "relationship": "relationships",
            "lifestyle": "lifestyles", "audio": "audio", "music": "music",
            "chronos": "chronos", "concept": "concepts", "universal": "universals"
        }
        
        # 고정 카테고리
        keys = {
            "characters": list(self._characters.keys()),
            "spaces": list(self._spaces.keys()),
            "props": list(self._props.keys()),
            "cards": list(self._cards.keys())
        }
        
        # 동적/기타 카테고리 매핑 적용
        for cat, data in self._others.items():
            cat_lower = cat.lower()
            # 매핑 테이블에 있으면 해당 이름을 쓰고, 없으면 기본 복수형 처리
            mapped_name = mapping.get(cat_lower, cat_lower + "s")
            keys[mapped_name] = list(data.keys())
            
        return keys

REGISTRY = CardRegistry()

# --- Card Definitions (Legacy/Internal) ---
# These classes are kept for internal logic but their data is now managed by the Registry.
class CinematicCard:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description

class MoodCard:
    def __init__(self, name, impact=None):
        self.name = name
        if impact is None:
            self.impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.impact = impact

class SenseCard:
    def __init__(self, name, focus=""):
        self.name = name
        self.focus = focus

class ElementCard:
    def __init__(self, name, theme=""):
        self.name = name
        self.theme = theme

class RelationshipCard:
    def __init__(self, name, dynamic_description=""):
        self.name = name
        self.dynamic_description = dynamic_description

class LifestyleCard:
    def __init__(self, name, lifestyle_description=""):
        self.name = name
        self.lifestyle_description = lifestyle_description

class AudioCard:
    def __init__(self, name, audio_description=""):
        self.name = name
        self.audio_description = audio_description

class MusicCard:
    def __init__(self, name, mood_description=""):
        self.name = name
        self.mood_description = mood_description

class ChronosCard:
    def __init__(self, name, description="", color="⚪", aesthetic=""):
        self.name = name
        self.description = description
        self.color = color
        self.aesthetic = aesthetic

class ConceptCard:
    def __init__(self, name, core_theme="", impact=None):
        self.name = name
        self.core_theme = core_theme
        if impact is None:
            self.impact = {"suspicion": 0, "pressure": 0, "echo": 0}
        else:
            self.impact = impact

class UniversalCard:
    def __init__(self, name, scale_description=""):
        self.name = name
        self.scale_description = scale_description

# --- Preset Data Initialization ---
# --- Preset Data Initialization ---
def _init_characters():
    chars = {
        "심연의 집행자": Character(name="심연의 집행자", role="Lead", personality="무자비한 정의, 냉혹한 관찰", speech_style="묘비처럼 무거운 말투", secret="사실 신을 죽인 자의 후예", base_impact={"suspicion": 2}),
        "검은 드레스의 여인": Character(name="검은 드레스의 여인", role="Support", personality="금지된 지식에 대한 갈망", speech_style="속삭이는 듯한 선율", secret="그녀 자체가 살아있는 성배", base_impact={"pressure": 1, "echo": 1}),
        "강철의 방랑자": Character(name="강철의 방랑자", role="Support", personality="묵묵한 충성, 기계적인 감각", speech_style="금속이 마찰하는 듯한 목소리", secret="심장 대신 정교한 태엽이 박혀 있음", base_impact={"pressure": 2}),
        "그림자 속의 목격자": Character(name="그림자 속의 목격자", role="Support", personality="뒤틀린 호기심, 공포의 숭배", speech_style="불쾌한 웃음이 섞인 중얼거림", secret="모든 비극의 시작을 지켜본 자", base_impact={"suspicion": 3, "echo": 1})
    }
    for k, v in chars.items(): REGISTRY.register_character(k, v)

def _init_spaces():
    spaces = {
        "버려진 성소": Space("버려진 성소", "피로 물든 제단과 부서진 신상", {"기도": 0.5, "비명": 2.0}, {"suspicion": 1, "pressure": 3}),
        "영원한 겨울의 성": Space("영원한 겨울의 성", "차가운 은빛 고립과 서리 낀 기억", {"회상": 1.5, "배신": 1.8}, {"pressure": 2, "echo": 2}),
        "심연의 시장": Space("심연의 시장", "금지된 금속과 영혼이 거래되는 곳", {"거래": 1.0, "도난": 2.0}, {"suspicion": 3}),
        "비탄의 숲": Space("비탄의 숲", "통곡하는 나무들이 그림자를 드리우는 곳", {"방황": 2.0, "조회": 0.2}, {"pressure": 1, "echo": 1})
    }
    for k, v in spaces.items(): REGISTRY.register_space(k, v)

def _init_props():
    props = {
        "낡은 일기장": Prop("낡은 일기장", "누군가의 비밀이 적힌 빛바랜 노트", {"suspicion": 2}),
        "부엌칼": Prop("부엌칼", "날카롭고 위협적인 요리 도구", {"pressure": 2}),
        "검": Prop("검", "무인의 정신이 깃든 장검", {"pressure": 1})
    }
    for k, v in props.items(): REGISTRY.register_prop(k, v)

def _init_cards():
    cards = {
        "질문": Card("질문", {"suspicion": 2, "pressure": 1}),
        "침묵": Card("침묵", {"echo": 1}),
        "위로": Card("위로", {"pressure": -2, "echo": -1}),
        "관찰": Card("관찰", {"suspicion": 1})
    }
    for k, v in cards.items(): REGISTRY.register_card(k, v)

def _init_other_presets():
    times = {
        "낮": "밝고 에너지가 넘치는 시간대",
        "밤": "어둡고 비밀스러운 시간대",
        "새벽": "차갑고 적막한 시간대",
        "황혼": "아련하고 감성적인 시간대"
    }
    for k, v in times.items(): REGISTRY.register_other("time", k, v)

    cinematic = {
        "클로즈업": CinematicCard("클로즈업", "인물의 표정과 눈빛에 집중"),
        "롱샷": CinematicCard("롱샷", "주변 환경과 고립감을 강조"),
        "로우앵글": CinematicCard("로우앵글", "권위적이고 압도적인 구도"),
        "핸드헬드": CinematicCard("핸드헬드", "불안정하고 긴박한 움직임"),
        "하이키조명": CinematicCard("하이키조명", "밝고 희망찬 분위기"),
        "로우키조명": CinematicCard("로우키조명", "어둡고 그림자가 짙은 느와르 분위기")
    }
    for k, v in cinematic.items(): REGISTRY.register_other("cinematic", k, v)

    moods = {
        "공포": MoodCard("공포", {"pressure": 3, "suspicion": 1}),
        "희망": MoodCard("희망", {"pressure": -3, "echo": -1}),
        "용맹": MoodCard("용맹", {"pressure": -1, "suspicion": -1}),
        "비굴": MoodCard("비굴", {"pressure": 2, "echo": 1}),
        "슬픔": MoodCard("슬픔", {"echo": 2, "pressure": 1})
    }
    for k, v in moods.items(): REGISTRY.register_other("mood", k, v)

    senses = {
        "시각": SenseCard("시각", "색감과 빛의 대비"),
        "청각": SenseCard("청각", "작은 소음과 숨소리"),
        "후각": SenseCard("후각", "피 냄새나 향수 냄새"),
        "촉각": SenseCard("촉각", "차가운 금속이나 거친 질감"),
        "미각": SenseCard("미각", "쓴 맛이나 비린 맛")
    }
    for k, v in senses.items(): REGISTRY.register_other("sense", k, v)

    elements = {
        "불": ElementCard("불", "파괴적이고 뜨거운 열기"),
        "물": ElementCard("물", "유연하고 차가운 흐름"),
        "흙": ElementCard("흙", "단단하고 묵직한 무게감"),
        "바람": ElementCard("바람", "빠르고 종잡을 수 없는 흐름"),
        "번개": ElementCard("번개", "찰나의 강렬한 빛과 충격")
    }
    for k, v in elements.items(): REGISTRY.register_other("element", k, v)

    relationships = {
        "사랑": RelationshipCard("사랑", "애틋하고 헌신적인 유대감"),
        "이별": RelationshipCard("이별", "단절과 상실의 아픔"),
        "우정": RelationshipCard("우정", "신뢰와 동료애"),
        "배신": RelationshipCard("배신", "깨진 믿음과 분노"),
        "경쟁": RelationshipCard("경쟁", "질투와 향상심")
    }
    for k, v in relationships.items(): REGISTRY.register_other("relationship", k, v)

    lifestyle = {
        "블랙수트": LifestyleCard("블랙수트", "단정하고 차가운 블랙 포멀 의상"),
        "화려한드레스": LifestyleCard("화려한드레스", "파티를 위한 우아하고 화려한 복장"),
        "빈티지코트": LifestyleCard("빈티지코트", "오래되고 고풍스러운 분위기의 외투"),
        "짙은분장": LifestyleCard("짙은분장", "인격을 숨기거나 강조하는 강한 화장"),
        "따뜻한스프": LifestyleCard("따뜻한스프", "위로와 안식을 주는 소박한 음식"),
        "비린스테이크": LifestyleCard("비린스테이크", "본능적이고 원초적인 식사")
    }
    for k, v in lifestyle.items(): REGISTRY.register_other("lifestyle", k, v)

    audio = {
        "심장박동": AudioCard("심장박동", "두근거리는 긴박한 소리"),
        "빗소리": AudioCard("빗소리", "차분하거나 거센 빗소리"),
        "금속마찰": AudioCard("금속마찰", "서늘하고 날카로운 기계적 소음"),
        "군중의웅성임": AudioCard("군중의웅성임", "고립감을 강조하는 주변 소음")
    }
    for k, v in audio.items(): REGISTRY.register_other("audio", k, v)

    music = {
        "시네마천국": MusicCard("시네마천국", "향수와 아련함을 자극하는 피아노 선율"),
        "느와르재즈": MusicCard("느와르재즈", "무겁고 끈적한 트럼펫 소리"),
        "심포닉긴장": MusicCard("심포닉긴장", "웅장하고 압박감을 주는 관현악"),
        "미니멀적막": MusicCard("미니멀적막", "악기가 거의 배제된 고요")
    }
    for k, v in music.items(): REGISTRY.register_other("music", k, v)

    chronos = {
        "과거": ChronosCard("과거", "기억의 저편, 붉은 실의 메아리", "🔴", "Sepia/Dark/Grained"),
        "현재": ChronosCard("현재", "찰나의 선택, 황금빛 존재감", "🟡", "Vivid/Clear/Realtime"),
        "미래": ChronosCard("미래", "가능성의 수평선, 푸른 예견", "🔵", "Ethereal/Neon/Blur")
    }
    for k, v in chronos.items(): REGISTRY.register_other("chronos", k, v)

    concepts = {
        "천사": ConceptCard("천사", "숭고하고 자비로운 개입", {"pressure": -2, "echo": 1}),
        "악마": ConceptCard("악마", "파괴적이고 거부할 수 없는 유혹", {"pressure": 2, "suspicion": 2}),
        "조화": ConceptCard("조화", "대립하는 것들의 완벽한 균형", {"pressure": -1, "echo": -1}),
        "철학": ConceptCard("철학", "존재와 진리에 대한 깊은 사유", {"echo": 3}),
        "행복": ConceptCard("행복", "찰나의 빛나는 안식", {"pressure": -3}),
        "운명": ConceptCard("운명", "정해진 길을 향한 굴레", {"pressure": 1, "suspicion": 1})
    }
    for k, v in concepts.items(): REGISTRY.register_other("concept", k, v)

    universal = {
        "대자연": UniversalCard("대자연", "인간의 의지를 압도하는 웅장한 섭리"),
        "지구": UniversalCard("지구", "역동적이고 생명력이 넘치는 무대"),
        "우주": UniversalCard("우주", "끝없는 고요와 무한한 가능성"),
        "심연": UniversalCard("심연", "빛조차 삼키는 근원적 어둠")
    }
    for k, v in universal.items(): REGISTRY.register_other("universal", k, v)

def _init_presets():
    _init_characters()
    _init_spaces()
    _init_props()
    _init_cards()
    _init_other_presets()

_init_presets()

# --- Registry Accessors (Public Interface) ---
def get_character(name): return REGISTRY.get_character(name)
def get_space(name): return REGISTRY.get_space(name)
def get_card(name): return REGISTRY.get_card(name)
def get_prop(name): return REGISTRY.get_prop(name)
def get_time(name): return REGISTRY.get_other("time", name)
def get_cinematic(name): return REGISTRY.get_other("cinematic", name)
def get_mood(name): return REGISTRY.get_other("mood", name)
def get_sense(name): return REGISTRY.get_other("sense", name)
def get_element(name): return REGISTRY.get_other("element", name)
def get_relationship(name): return REGISTRY.get_other("relationship", name)
def get_lifestyle(name): return REGISTRY.get_other("lifestyle", name)
def get_audio(name): return REGISTRY.get_other("audio", name)
def get_music(name): return REGISTRY.get_other("music", name)
def get_chronos(name): return REGISTRY.get_other("chronos", name)
def get_concept(name): return REGISTRY.get_other("concept", name)
def get_universal(name): return REGISTRY.get_other("universal", name)

def get_all_presets():
    """Returns a full list of available preset names across all categories."""
    return REGISTRY.get_all_keys()
