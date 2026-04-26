"""
Kakao Skill Translator for Phase 8.2.
Converts CommonResponse to Kakao i Open Builder Skill JSON (Carousel).
"""
from typing import Dict, Any, List
from ..schemas import CommonResponse

class KakaoTranslator:
    @staticmethod
    def to_skill_response(response: CommonResponse) -> Dict[str, Any]:
        """Translates engine response to Kakao-friendly JSON."""
        outputs = []
        pulse = response.pulse_data or {}
        payload = response.payload or {}
        
        # 1. Main Text Section (Header, Pulse, Diagnosis, Aura)
        text_parts = []
        if response.world_state_summary:
            s = response.world_state_summary
            multi = payload.get("multimodal", {})
            dur = payload.get("duration", {})
            tempo = s.get("momentum", 1.0)
            
            text_parts.append(f"🎬 {s['ailment']} | 추진력: {tempo:.1f}x")
            
            if dur:
                text_parts.append(f"⏳ 예상 러닝타임: {dur.get('minutes', 0)}분 ({dur.get('seconds', 0)}초)")
            
            text_parts.append(f"\n{response.message}")
            
            if multi.get("bgm_prompt"):
                text_parts.append(f"\n🎶 Aura (BGM): {multi['bgm_prompt']}")
        else:
            text_parts.append(response.message)

        # 2. Rendered Scene Preview (if exists)
        rendered = payload.get("rendered_scene")
        if rendered:
            title = rendered.get("title", "Scene")
            text = rendered.get("scene_text", "")
            preview = (text[:300] + "...") if len(text) > 300 else text
            text_parts.append(f"\n🎞️ {title}\n{preview}")

        outputs.append({
            "simpleText": {"text": "\n".join(text_parts)}
        })

        # 3. Carousel Section (Tarot Cards or Stream)
        cards = payload.get("cards") or payload.get("spread", [])
        if cards:
            items = []
            for card in cards[:10]:
                title = card.get("name", "Unknown Symbol")
                desc = card.get("summary", "")[:100]
                img_url = card.get("image_url") 
                
                # Mock public URL if only local path exists (for Kakao Carousel)
                if img_url and not img_url.startswith("http"):
                    img_url = f"http://localhost:8000/assets/portraits/{img_url}"

                card_item = {
                    "title": title,
                    "description": desc,
                    "buttons": [
                        {
                            "action": "message",
                            "label": "뒤집기(Flip)",
                            "messageText": f"/flip {card['cid']}"
                        },
                        {
                            "action": "message",
                            "label": "태우기(Burn)",
                            "messageText": f"/burn {card['cid']}"
                        }
                    ]
                }
                if img_url:
                    card_item["thumbnail"] = {"imageUrl": img_url}
                
                items.append(card_item)
            
            outputs.append({
                "carousel": {
                    "type": "basicCard",
                    "items": items
                }
            })

        # 4. Quick Replies (Tarot Optimized)
        quick_replies = [
            {"label": "🃏 카드 드로우", "action": "message", "messageText": "/deal"},
            {"label": "👁️ 보드 보기", "action": "message", "messageText": "/board"},
            {"label": "🔄 스트림 전환", "action": "message", "messageText": "/stream"},
            {"label": "⚡ 가속(Surge)", "action": "message", "messageText": "/surge"},
            {"label": "📊 상태 요약", "action": "message", "messageText": "/status"}
        ]

        return {
            "version": "2.0",
            "template": {
                "outputs": outputs,
                "quickReplies": quick_replies
            }
        }
