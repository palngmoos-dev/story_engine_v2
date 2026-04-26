import random
import json
import re
import os
import ollama_client

# --- Configuration & Fallbacks ---
GENRES = ["판타지", "로맨스", "스릴러", "미스터리", "액션", "드라마", "성장", "호러", "SF", "일상"]

FALLBACK_STORY = {
    "genre": "드라마",
    "one_liner": "길 끝에서 만난 뜻밖의 인연",
    "plot": "평범한 주말, 여행지에서 우연히 만난 지혜로운 노인과의 대화를 통해 삶의 진정한 가치를 깨닫게 되는 따뜻한 휴먼 드라마.",
    "reason": "대중적이고 따뜻한 정서를 담고 있어 초보자가 시작하기 가장 좋은 구조입니다."
}

FALLBACK_CHARACTER = {
    "name": "김하늘",
    "age": "28",
    "gender": "여성",
    "mbti": "INFP",
    "occupation": "프리랜서 작가",
    "background": "도시의 소음에서 벗어나 작은 마을에서 성장하며 관찰력을 키움",
    "personality": "조용하고 사색적이며 타인의 감정에 민감함",
    "flaw": "현실적인 문제 앞에서 결정적인 용기가 부족함",
    "skill": "사소한 단서에서 이야기의 흐름을 읽어내는 통찰력",
    "level": 1,
    "reason": "스토리의 서정적인 분위기에 가장 잘 어울리는 섬세한 주인공입니다."
}

# --- Internal Helpers ---
def _parse_ai_json(response, fallback):
    try:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return fallback
    except Exception: # TODO: 나중에 구체적인 JSONDecodeError 등으로 교체 예정
        return fallback

def _clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Core API (Step 1 & 2) ---

def generate_story_recommendation(genre=None):
    """
    STEP 1: Generates a story recommendation.
    Returns: { "genre": "", "one_liner": "", "plot": "", "reason": "" }
    """
    selected_genre = genre if genre else random.choice(GENRES)
    prompt = f"""
당신은 베테랑 시네마 스토리 작가입니다. 초보 사용자를 위해 '{selected_genre}' 장르의 스토리 1개를 제안하십시오.
반드시 아래 JSON 형식으로만 응답하십시오.

{{
  "genre": "{selected_genre}",
  "one_liner": "한 줄 핵심 요약",
  "plot": "줄거리 요약 (2~3문장)",
  "reason": "추천 이유 (1문장)"
}}
    """
    try:
        response = ollama_client.ollama_generate(prompt)
        if "[Ollama" in response: return FALLBACK_STORY
        return _parse_ai_json(response, FALLBACK_STORY)
    except Exception: # TODO: 네트워크 오류 또는 타임아웃 구체화 예정
        return FALLBACK_STORY

def generate_character_recommendation(story):
    """
    STEP 2: Generates a lead character fitting the story.
    Returns: Character dictionary consistent with card_engine.Character
    """
    prompt = f"""
아래 스토리 보드에 가장 어울리는 주인공 캐릭터 카드 1개를 생성하십시오.
스토리 요약: {story.get('one_liner', '')} - {story.get('plot', '')}

반드시 아래 JSON 형식으로만 응답하십시오.

{{
  "name": "이름",
  "age": "나이(숫자만)",
  "gender": "성별",
  "mbti": "MBTI",
  "occupation": "직업/역할",
  "background": "배경 (가족/환경)",
  "personality": "성격",
  "flaw": "단점",
  "skill": "스킬",
  "level": 1,
  "reason": "추천 이유 (1문장)"
}}
    """
    try:
        response = ollama_client.ollama_generate(prompt)
        if "[Ollama" in response: return FALLBACK_CHARACTER
        return _parse_ai_json(response, FALLBACK_CHARACTER)
    except Exception: # TODO: LLM 응답 필터링 예외 추가 예정
        return FALLBACK_CHARACTER

def structure_user_input(text, mode="STORY"):
    """Parses raw text into structured JSON for Story or Character."""
    prompt = f"사용자의 자유로운 입력을 분석하여 {mode} 구조의 JSON으로 변환하십시오: {text}"
    try:
        response = ollama_client.ollama_generate(prompt)
        fallback = FALLBACK_STORY if mode == "STORY" else FALLBACK_CHARACTER
        return _parse_ai_json(response, fallback)
    except Exception: # TODO: 파싱 실패 시 사용자 재입력 유도 로직 추가 예정
        return FALLBACK_STORY if mode == "STORY" else FALLBACK_CHARACTER

# --- Interaction Flow (Moved to main_wizard.py) ---
# The logic below is kept for internal logic reference but the main CLI entry point
# is now v2_core/main_wizard.py. Please run that file for the user interaction.

"""
def run_wizard():
    # Deprecated: use main_wizard.py for user CLI interaction.
    pass

if __name__ == "__main__":
    run_wizard()
"""
