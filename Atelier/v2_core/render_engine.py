"""
Cinematic Scene Render Engine for Phase 9.
Takes committed story beats + WorldState context and renders full cinematic scenes
using master_prompt.md directives via Ollama.
Falls back to a structured spec-based output when Ollama is unavailable.
"""
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

import ollama_client
from .state_model import WorldState
from .blueprint_engine import BlueprintEngine

# --- Fallback Renderer ---

def _build_fallback_scene(beat: Dict[str, Any], spec: Dict[str, Any], char: Optional[Dict] = None) -> str:
    """Constructs a structured fallback scene when Ollama is unavailable."""
    title = beat.get("title", "Scene")
    content = beat.get("content", "")
    shot = spec.get("shot_type", "Medium Shot")
    light = spec.get("lighting", "Natural Soft Light")
    move = spec.get("movement", "Static")
    prompt = spec.get("image_prompt", "")

    char_note = ""
    if char:
        char_note = (
            f"\n[주연] {char.get('name', '주인공')} | {char.get('mbti', 'N/A')} | "
            f"치명적 단점: {char.get('flaw', '없음')} | 스킬: {char.get('skill', '없음')}"
        )

    return f"""## {title}
{char_note}

{content}

---
**[영상 콘티]**
- **Shot**: {shot}
- **Move**: {move}
- **Light**: {light}

**[Visual Blueprint Prompt]**
> {prompt}

**[Director's Review]** ⭐⭐⭐
*[Fallback Mode: Ollama 미연결 상태에서 Blueprint 기반으로 생성된 씬입니다.]*
"""


# --- Master Prompt Builder ---

def _build_render_prompt(beat: Dict[str, Any], state: WorldState, spec: Dict[str, Any]) -> str:
    """Assembles the full master_prompt.md-style rendering prompt."""
    char = state.lead_character or {}
    supports = getattr(state, "support_characters", [])
    supports_str = ", ".join(c.get("name", "?") for c in supports) if supports else "없음"

    # Props from active_canvas_cards (category == 'props')
    props = [c.get("name") for c in state.active_canvas_cards if c.get("category") == "props"]
    props_str = ", ".join(props) if props else "없음"

    # Cinematic palette from visual settings
    style = state.visual_settings.get("style", "Cinematic")
    grading = state.visual_settings.get("grading", "Modern Film")
    aspect = state.visual_settings.get("aspect_ratio", "21:9")

    # 1.5. Target Duration & Pacing Context (Phase 14)
    target = state.target_duration
    pacing_note = {
        "SHORTS": "이 장면은 쇼츠(Shorts)입니다. 장소의 깊이보다는 '단 하나의 강력한 미묘한 컷'이나 '충격적인 임팩트'에 집중하여 극단적인 밀도로 작성하십시오.",
        "30M": "단편 영화의 기승전결을 고려하여 전개 속도를 빠르게 유지하십시오.",
        "1H": "TV 에피소드 분량의 호흡입니다. 인물간의 티키타카와 감정의 굴곡을 충분히 묘사하십시오.",
        "PR": "장편 영화(Feature) 호흡입니다. 거대한 서사시의 일환으로 복선과 상징, 느린 호흡의 미학을 활용하십시오."
    }.get(target, "")

    metrics = state.global_metrics
    momentum = state.momentum_level
    timeline = state.timeline_mode
    ailment = state.narrative_ailment

    # Pacing guide
    beats_total = len(state.story_beats)
    if beats_total <= 3:
        pacing = "단기 (1~3분): 핵심 사건과 감각에 집중하십시오. 문장은 짧고 강렬해야 합니다."
    elif beats_total <= 8:
        pacing = "중기 (5~10분): 인물 간의 대사와 심리적 갈등을 균형 있게 다루십시오."
    else:
        pacing = "장기 (15분 이상): 환경의 디테일과 공기감, 인물의 깊은 내면 독백을 담으십시오."

    intensity = "폭발적이고 파격적인" if momentum > 2.0 else "안정적이고 개연성 있는"

    lead_block = ""
    if char:
        lead_block = f"""[Table - Lead Character]:
  이름: {char.get('name', '미지정')}
  나이: {char.get('age', '?')} / 성별: {char.get('gender', '?')} / MBTI: {char.get('mbti', '?')}
  직업: {char.get('occupation', '?')}
  배경: {char.get('background', '?')}
  성격: {char.get('personality', '?')}
  치명적 단점 (Flaw): {char.get('flaw', '?')} ← 반드시 이 씬에 반영할 것
  특별 스킬 (Skill): {char.get('skill', '?')}"""
    else:
        lead_block = "[Table - Lead Character]: 미설정 (일반적인 주인공으로 처리하십시오.)"

    return f"""당신은 시네마틱 서사 엔진의 최고 연출 AI 파트너입니다. 아래 데이터를 바탕으로 완전한 영화 장면 하나를 렌더링하십시오.

[Current Tag]: {ailment}
[Current Stats]: Suspicion={metrics.get('suspicion',0)}, Pressure={metrics.get('pressure',0)}, Echo={metrics.get('echo',0)}
[Scene Title]: {beat.get('title', 'Untitled Scene')}
[Scene Core]: {beat.get('content', '')}
[Momentum]: {momentum:.1f}x ({intensity} 전개)
[Timeline Mode]: {timeline}
[Scene Metadata]: {pacing}
[Cinematic Style]: {style} | {grading} | {aspect}

{lead_block}

[Table - Support Characters]: {supports_str}
[Table - Props]: {props_str}
[Cinematic Blueprint]:
  Shot: {spec.get('shot_type', 'Medium Shot')}
  Movement: {spec.get('movement', 'Static')}
  Lighting: {spec.get('lighting', 'Natural Soft Light')}
  Image Prompt: {spec.get('image_prompt', '')}

위 데이터를 바탕으로 아래 포맷으로 완전한 시네마틱 장면을 출력하십시오:
1. (서사 본문) - 깊이 있는 장면 묘사와 대사
2. [영상 콘티] - Shot / Visual / Sound/Mood
3. [BGM/OST Recommendation]
4. [Director's Review & Diagnosis] - 별점(⭐) / 평론 / 진단
"""


# --- Core Engine ---

class RenderEngine:
    """Phase 9: Cinematic Scene Render Engine."""

    @staticmethod
    def render_beat(state: WorldState, beat_index: int) -> Dict[str, Any]:
        """
        Renders a single committed story beat into a full cinematic scene.
        Returns a rendered_scene dict with 'beat_index', 'title', 'scene_text', 'spec', 'timestamp'.
        Falls back gracefully when Ollama is unavailable.
        """
        beats = state.story_beats
        if beat_index < 0 or beat_index >= len(beats):
            return {"error": f"Beat index {beat_index} out of range (total: {len(beats)})"}

        beat = beats[beat_index]
        content = beat.get("content", "")
        spec = BlueprintEngine.generate_visual_spec(content, state.momentum_level)

        try:
            prompt = _build_render_prompt(beat, state, spec)
            scene_text = ollama_client.ollama_generate(prompt)

            # Validate Ollama response quality
            if not scene_text or len(scene_text) < 100 or "[Ollama" in scene_text or "[연결 실패]" in scene_text:
                raise ValueError("Ollama returned empty or error response")

        except Exception as e:
            print(f"[RenderEngine] Fallback activated: {e}")
            scene_text = _build_fallback_scene(beat, spec, state.lead_character)

        result = {
            "beat_index": beat_index,
            "title": beat.get("title", f"Scene {beat_index + 1}"),
            "scene_text": scene_text,
            "spec": spec,
            "timestamp": datetime.now().isoformat(),
            "is_fallback": "[Fallback Mode" in scene_text
        }
        return result

    @staticmethod
    def render_full_screenplay(state: WorldState) -> List[Dict[str, Any]]:
        """
        Renders all committed story beats into a complete screenplay.
        Results are cached to state.rendered_scenes.
        """
        rendered = []
        for i in range(len(state.story_beats)):
            scene = RenderEngine.render_beat(state, i)
            rendered.append(scene)

        # Cache to state
        state.rendered_scenes = rendered
        return rendered

    @staticmethod
    def get_screenplay_markdown(rendered_scenes: List[Dict[str, Any]], title: str = "Untitled") -> str:
        """Assembles rendered scenes into a single Markdown screenplay document."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# 🎬 {title}",
            f"*Rendered by Cinematic Narrative Engine V2 | {now}*",
            "\n---\n"
        ]
        for i, scene in enumerate(rendered_scenes):
            lines.append(f"## SCENE {i + 1}: {scene.get('title', 'Untitled')}")
            lines.append(scene.get("scene_text", ""))
            lines.append("\n---\n")

        lines.append("*End of Screenplay — Infinite Narrative Canvas*")
        return "\n".join(lines)
