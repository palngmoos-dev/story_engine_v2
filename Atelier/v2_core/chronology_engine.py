"""
Chronology Engine for Infinite Narrative Canvas.
Handles narrative synthesis and exporting chronicles to Markdown.
"""
import os
import json
import re
import ollama_client
from datetime import datetime
from typing import List, Dict, Any
from .state_model import WorldState

class ChronologyEngine:
    def __init__(self, base_path: str = "v2_core/saves/chronicles"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    @staticmethod
    def summarize_beats(beats: List[Dict[str, Any]]) -> str:
        """
        Synthesizes multiple scene beats into a single coherent summary.
        Uses AI for narrative condensation.
        """
        if not beats:
            return "기록할 서사적 사건이 없습니다."
            
        beat_texts = [b.get("beat_text", "") for b in beats]
        prompt = f"""
아래는 최근 발생한 일련의 서사적 장면들(Scene Beats)입니다.
이들을 하나의 유기적이고 품격 있는 장면 요약(1~2문장)으로 합성하십시오.

[Scene Beats]
{chr(10).join(beat_texts)}

반드시 한국어로, 한 줄의 강렬한 요약으로 응답하십시오.
"""
        try:
            response = ollama_client.ollama_generate(prompt)
            summary = response.strip()
            # Basic cleaning
            summary = re.sub(r'\"', '', summary)
            return summary
        except Exception as e:
            print(f"\n[Chronology Engine] Synthesis fallback: {e}")
            return beats[-1].get("beat_text", "서사가 연결되는 중입니다.")[:50] + "..."

    def export_chronicle_md(self, state: WorldState, branch_name: str, narrative_log: List[Dict[str, Any]]):
        """
        Exports the entire narrative history of a branch to a Markdown file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Chronicle_{branch_name}_{timestamp}.md"
        file_path = os.path.join(self.base_path, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Infinite Narrative Archive: [{branch_name}]\n\n")
            f.write(f"**Generated on:** {datetime.now().isoformat()}\n")
            f.write(f"**Timeline Mode:** {state.timeline_mode}\n\n")
            f.write("--- \n\n")
            
            f.write("## 1. Narrative Chronicles (확정된 역사)\n\n")
            if not narrative_log:
                f.write("*아직 확정된 역사가 없습니다.*\n\n")
            else:
                for entry in narrative_log:
                    f.write(f"> **[{entry['timestamp'][:10]}]**  \n")
                    f.write(f"{entry['summary']}\n\n")
            
            f.write("--- \n\n")
            f.write("## 2. Active Canvas Context (현재 캔버스 상태)\n\n")
            f.write("### Active Cards\n")
            for card in state.active_canvas_cards:
                f.write(f"- **{card.get('name')}** : {card.get('summary', card.get('description', ''))}\n")
            
            f.write("\n### Latest Thinking Beats (미확정 비트)\n")
            for beat in state.story_beats:
                f.write(f"* {beat.get('beat_text')}\n")
                
            f.write("\n\n---\n*End of Chronicle*")
            
        return file_path

    def export_final_chronicle(self, state: WorldState):
        """
        Exports the finalized core narrative to a premium-formatted Markdown file.
        Focuses on committed elements and dominant story themes.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FINAL_WORK_{timestamp}.md"
        file_path = os.path.join(self.base_path, filename)
        
        core = state.committed_core
        profile = state.dominant_story_profile
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# FINAL NARRATIVE: {profile.get('core_theme', 'Unnamed Work')}\n\n")
            
            # 1. Narrative Logline & Theme Summary
            logline = f"'{profile.get('core_theme')}' 테마가 '{profile.get('core_tone')}'의 톤으로 응축된 평행 세계의 조각들입니다."
            f.write(f"## 📜 Narrative Logline\n> {logline}\n\n")
            
            f.write(f"## 🎭 Theme Summary\n")
            f.write(f"- **Primary Tone:** {profile.get('core_tone')}\n")
            f.write(f"- **Gravity Center:** {', '.join(profile.get('dominant_tags', []))}\n")
            f.write(f"- **Timeline Focus:** {profile.get('preferred_timeline')}\n\n")
            f.write("--- \n\n")
            
            f.write("## 🎬 The Core Narrative Beats\n\n")
            for beat in core.get("beats", []):
                f.write(f"### {beat.get('beat_text')[:40]}...\n")
                f.write(f"{beat.get('beat_text')}\n\n")
            
            f.write("## 2. Iconic Card Clusters (핵심 서사 군집)\n\n")
            for group in core.get("groups", []):
                f.write(f"#### {group.get('name')} ({group.get('alias_suggestion')})\n")
                f.write(f"*Elements: {', '.join(group.get('card_ids', []))}*\n\n")
            
            f.write("## 3. Key Inspiration Anchors (핵심 영감 앵커)\n\n")
            for card in core.get("cards", []):
                f.write(f"- **{card.get('name')}**: {card.get('summary')}\n")
                
            f.write("\n\n---\n*Created with Infinite Narrative Canvas Convergence Engine*")
            
        return file_path
