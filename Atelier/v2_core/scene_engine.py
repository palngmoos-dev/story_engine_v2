"""
Scene Engine for Narrative Simulation (Refactored V2 - Refined)
Coordinates Core and Card engines to generate scenes and manage turns.
"""

import random
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from . import core_engine as core
    from . import card_engine as cards
except ImportError:
    import core_engine as core
    import card_engine as cards
import ollama_client

# --- Load Master Prompt ---
def _load_master_prompt():
    try:
        current_dir = os.path.dirname(__file__)
        path = os.path.join(current_dir, "master_prompt.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Warning: Master prompt loading failed: {e}")
        pass
    return "당신은 서사 엔진의 화자입니다."

MASTER_PROMPT = _load_master_prompt()

# --- Label Mappings (Restored Korean Tone) ---
def _emotion_label(level: int) -> str:
    mapping = {
        -1: "모든 감정이 마모되고 비현실적 공허감에 휩싸인 파국 상태 (Void)",
        0: "매우 건조하고 감정이 거의 없는 상태",
        1: "조용하고 차분한 상태",
        2: "약한 긴장과 미묘한 변화가 있는 상태",
        3: "불안하거나 의미가 흔들리는 상태",
        4: "강한 긴장과 감정이 올라오는 상태",
        5: "폭발 직전의 감정 상태",
    }
    return mapping.get(level, "차분한 상태")

def _apply_foreshadow_recovery(line: str, scene_no: int) -> str:
    score = core._TIMING_STATE["suspicion"] * 2 + core._TIMING_STATE["pressure"] + core._TIMING_STATE["echo"]
    if scene_no < 6 or score < 6: return line
    released = [m for m in core._FORESHADOW_QUEUE if m["release_at"] <= scene_no]
    if released:
        picked = released[0]["scene"]
        core._MEMORY_LONG.append(picked)
        core._FORESHADOW_QUEUE.remove(released[0])
        core._TIMING_STATE["suspicion"] = max(0, core._TIMING_STATE["suspicion"] - 2)
        core._TIMING_STATE["pressure"] = max(0, core._TIMING_STATE["pressure"] - 1)
        core._TIMING_STATE["echo"] = max(0, core._TIMING_STATE["echo"] - 1)
        return line.rstrip(". ") + f". [순간, 과거의 잔상('{picked}')이 뇌리를 스치고 지나간다.]"
    return line

def _apply_peaceful_atmosphere(line: str, state_tag: str) -> str:
    if state_tag == "STILLNESS":
        phrases = [
            " 주변에 고요한 정적이 찾아오며 마음이 한결 가벼워진다.",
            " 창밖의 햇살이 부드럽게 내리쬐며 평온한 갈무리가 시작된다.",
            " 모든 소란이 잦아들고 아스라한 여운만이 방 안을 채운다."
        ]
        return line.rstrip(". ") + random.choice(phrases)
    return line

def _apply_void_atmosphere(line: str, effective_emotion: int) -> str:
    if effective_emotion == -1:
        phrases = [
            " 주변의 모든 소리가 사라지고 오직 기괴한 공허함만이 맴돈다.",
            " 의미를 잃어버린 풍경 속에서 끝없는 붕괴의 감각이 밀려든다.",
            " 더 이상 아무것도 덧붙일 수 없는 텅 빈 파국이 내려앉았다."
        ]
        return line.rstrip(". ") + random.choice(phrases)
    return line

# --- Atmospheric Hooks (Extension Points) ---
def _hook_void_prompt(prompt: str) -> str:
    """TODO: Future expansion point for custom VOID prompts."""
    return prompt

def _hook_stillness_prompt(prompt: str) -> str:
    """TODO: Future expansion point for custom STILLNESS prompts."""
    return prompt

# --- Refactored Components ---
def _build_scene_prompt(user_input, scene_no, duration):
    state = core.get_state()
    lead = state["lead_character"]
    # TODO: Move to setter/getter in core_engine
    if lead:
        lead_text = f"{lead['name']} (나이:{lead['age']}, 성별:{lead['gender']}, MBTI:{lead['mbti']}, 직업:{lead['occupation']}, 성격:{lead['personality']}, 단점:{lead['flaw']}, 스킬:{lead['skill']})"
    else:
        lead_text = "없음"
    
    prompt = f"""
{MASTER_PROMPT}
[Environment]
- Place: {state['place']}{f" ({cards.get_space(state['place']).description})" if cards.get_space(state['place']) and cards.get_space(state['place']).description else ""}
- Lead: {lead_text}
- Support: {state['support_characters']}
- Props: {state['active_props']}

[Timeline]: {state.get('timeline_mode', 'PRESENT')}
[Status]
- Duration: {duration} min
- Input: {user_input}
""".strip()

    # [LANGUAGE ENFORCEMENT]
    prompt += "\n\n[MANDATORY] 반드시 한국어(한글)로만 작성하십시오. 기술적 묘사와 콘티 내용도 모두 한국어를 사용하십시오."

    # Apply hooks based on state tag
    tag = core.get_current_state_tag()
    if tag == "VOID": prompt = _hook_void_prompt(prompt)
    elif tag == "STILLNESS": prompt = _hook_stillness_prompt(prompt)
    
    return prompt

def _call_scene_llm(prompt, emotion_text, place):
    try:
        response = ollama_client.ollama_generate(prompt)
        # TODO: Replace string-based error detection with robust exception handling
        if "[Ollama" in response: raise ConnectionError("LLM offline")
        return response
    except Exception as e:
        return f"[{emotion_text}] {place}의 차가운 정적 속에서 이야기가 멈춥니다. (Error: {e})"

def _extract_event_summary(line, scene_no, test_mode):
    summary = "중요 사건이 식별되지 않음"
    if "[Narrative Memory]" in line:
        try:
            summary = line.split("[Narrative Memory]")[-1].strip().split("\n")[0].strip(": ")
        except: pass
    elif test_mode:
        summary = f"테스트 장면 {scene_no} 생성됨"
    return summary

def generate_next_scene(user_input: str, scene_no: int, duration: int = 5, test_mode: bool = False) -> str:
    if scene_no % 2 == 0 and core._CURRENT_EMOTION < 5:
        core._CURRENT_EMOTION += 1
    
    is_void = core._is_void_moment()
    effective_emotion = -1 if is_void else core._CURRENT_EMOTION
    emotion_text = _emotion_label(effective_emotion)
    
    if test_mode:
        line = f"[{emotion_text}] 테스트 문구입니다."
    else:
        # TODO: Handle state access through core_engine getters
        prompt = _build_scene_prompt(user_input, scene_no, duration)
        line = _call_scene_llm(prompt, emotion_text, core.get_state()['place'])

    core._update_timing_state(line, scene_no)
    core._update_reaction_intensity()
    
    impact = core.calculate_scene_impact(line, duration)
    event_summary = _extract_event_summary(line, scene_no, test_mode)
    core.add_narrative_memory(event_summary, impact)
    
    tag = core.get_current_state_tag()
    line = _apply_foreshadow_recovery(line, scene_no)
    line = _apply_peaceful_atmosphere(line, tag)
    line = _apply_void_atmosphere(line, effective_emotion)
    return line

def resolve_choice_weights():
    """Resolves weights based on current place and character context."""
    weights = {"suspicion": 1.0, "pressure": 1.0, "echo": 1.0}
    # TODO: Move to setter/getter in core_engine
    space_obj = cards.get_space(core._CURRENT_PLACE)
    if space_obj:
        for key, mult in space_obj.weight_modifiers.items():
            if key == "대화": weights["pressure"] *= mult
            if key == "침묵": weights["echo"] *= mult
            if key == "관찰": weights["suspicion"] *= mult
    return weights

# --- Internal Helper Functions for play_turn ---
def _setup_place_and_lead(place, lead):
    """Initializes place and lead character independently."""
    if place:
        space_obj = cards.get_space(place)
        if space_obj:
            core.reset_core()
            # TODO: Move to setter function in core_engine
            core._CURRENT_PLACE = place
            core.update_timing(**space_obj.base_impact)
        else:
            print(f"Warning: Space '{place}' not found.")

    if lead:
        if isinstance(lead, str):
            char_obj = cards.get_character(lead)
            if char_obj: 
                # TODO: Move to setter function in core_engine
                core._LEAD_CHARACTER = char_obj.to_dict()
                core.update_timing(**char_obj.base_impact)
            else:
                print(f"Warning: Lead character '{lead}' not found.")
        else:
            # TODO: Move to setter function in core_engine
            core._LEAD_CHARACTER = lead
            if "base_impact" in lead:
                core.update_timing(**lead["base_impact"])

def _setup_supports(support):
    """Adds support characters to the scene. (Accumulative append is intentional)"""
    if not support: return
    
    # TODO: Future - Add check for existing support to avoid unintentional duplicates
    supports = support if isinstance(support, list) else [support]
    for s in supports:
        if isinstance(s, str):
            char_obj = cards.get_character(s)
            if char_obj: 
                # TODO: Move to setter function in core_engine
                core._SUPPORT_CHARACTERS.append(char_obj.to_dict())
            else: print(f"Warning: Support character '{s}' not found.")
        else:
            # TODO: Move to setter function in core_engine
            core._SUPPORT_CHARACTERS.append(s)

def _setup_props(prop):
    """Adds props to the scene. (Accumulative append is intentional)"""
    if not prop: return
    
    # TODO: Future - Add check for existing props to avoid unintentional duplicates
    props = prop if isinstance(prop, list) else [prop]
    for p in props:
        if isinstance(p, str):
            prop_obj = cards.get_prop(p)
            if prop_obj: 
                # TODO: Move to setter function in core_engine
                core._ACTIVE_PROPS.append({"name": prop_obj.name, "description": prop_obj.description})
            else: print(f"Warning: Prop '{p}' not found.")
        else:
            # TODO: Move to setter function in core_engine
            core._ACTIVE_PROPS.append(p)

def _apply_card_impact(card):
    """Applies a card's impact and tracks delta changes. (Lead impact is separate and handled in setup)"""
    if not card: return None
    
    card_obj = cards.get_card(card)
    if card_obj:
        changes = {}
        for key in ["suspicion", "pressure", "echo"]:
            total_mod = card_obj.impact.get(key, 0)
            
            if total_mod != 0:
                # TODO: core_engine에 델타 업데이트 인터페이스 추가 검토
                old_val = core._TIMING_STATE[key]
                core.update_timing(**{key: total_mod})
                changes[key] = core._TIMING_STATE[key] - old_val
        
        return {"card": card, "changes": changes}
    else:
        print(f"Warning: Card '{card}' not found.")
    return None

def play_turn(place=None, lead=None, support=None, prop=None, card=None, user_input="", scene_no=1, duration=5, test_mode=False) -> dict:
    """Main entry point for a narrative turn."""
    try:
        # 1. Setup Environment and Characters
        _setup_place_and_lead(place, lead)
        _setup_supports(support)
        _setup_props(prop)

        # 2. Apply Event Card (Returns meaningful changes)
        card_result = _apply_card_impact(card)

        # 3. Resolve weights and generate scene
        weights = resolve_choice_weights()
        scene_text = generate_next_scene(user_input, scene_no, duration=duration, test_mode=test_mode)
        
        return {
            "state": core.get_state(),
            "card_used": card_result["card"] if card_result else "없음",
            "changes": card_result.get("changes", {}) if card_result else {},
            "state_tag": core.get_current_state_tag(),
            "scene_text": scene_text,
            "weights": weights,
            "duration": duration,
            "impact_score": core._CUMULATIVE_IMPACT,
            "impact": core._LAST_SCENE_IMPACT,
            "event_summary": core._LAST_EVENT_SUMMARY
        }
    except Exception as e:
        print(f"Error during play_turn: {e}")
        raise
    finally:
        # Ensure timeline mode is always reset, regardless of errors
        try:
            core.set_timeline_mode("PRESENT")
        except:
            pass

def reset_engine():
    core.reset_core()

# --- Legacy Compatibility ---
def apply_card(card_name: str): return play_turn(card=card_name)
def set_place(place_name: str): return play_turn(place=place_name)
def set_character(char_name: str): return play_turn(lead=char_name)
