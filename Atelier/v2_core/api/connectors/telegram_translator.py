"""
Telegram Bot Translator for Phase 9.
Converts CommonResponse to Telegram Bot API send_message payloads.
Supports rich formatting with Markdown and Inline Keyboards.
"""
from typing import Dict, Any, List
from ..schemas import CommonResponse


class TelegramTranslator:
    """Translates engine responses to Telegram Bot API payloads."""

    MAX_TEXT_LEN = 4000  # Telegram single message limit

    @staticmethod
    def to_send_message(chat_id: int, response: CommonResponse) -> Dict[str, Any]:
        """
        Converts a CommonResponse into a Telegram sendMessage-compatible dict.
        Returns a dict with 'method', 'chat_id', 'text', 'parse_mode', and optional 'reply_markup'.
        """
        text_parts = []
        
        # 1. Status Header & Pulse
        pulse = response.pulse_data or {}
        text_parts = []
        
        if response.world_state_summary:
            s = response.world_state_summary
            momentum_bar = TelegramTranslator._momentum_bar(s.get("momentum", 1.0))
            
            # Pulse Info
            tension_visual = pulse.get("pulse_visual", "░░░░░░░░░░")
            label = pulse.get("label", "평온")
            psych = pulse.get("psychology", "관찰")
            
            text_parts.append(
                f"🎬 *{s.get('ailment', 'Healthy')}* | 심리: _{psych}_\n"
                f"추진력: {momentum_bar} `{s.get('momentum', 1.0):.1f}x`\n"
                f"긴장도: {tension_visual} *{label}*\n"
                f"_{response.message}_"
            )
            
            if pulse.get("directors_note"):
                text_parts.append(f"\n💡 *Director's Note*\n_{pulse['directors_note']}_")
        else:
            text_parts.append(f"_{response.message}_")

        # 2. Payload-specific content
        payload = response.payload or {}

        # Card stream
        cards = payload.get("cards", [])
        if cards:
            text_parts.append("\n📋 *영감 카드 스트림*")
            for card in cards[:5]:  # Limit to 5 for readability
                v = card.get("visual_spec", {})
                shot_note = f"🎥 {v.get('shot_type', '?')}" if v else ""
                text_parts.append(
                    f"\n*[{card.get('category', '?').upper()}]* {card.get('name', '?')}\n"
                    f"  → {card.get('summary', '')}\n"
                    f"  {shot_note}"
                )
            if len(cards) > 5:
                text_parts.append(f"\n_...외 {len(cards) - 5}장 더 있습니다. 웹 허브에서 확인하세요._")

        # Rendered scene
        rendered_scene = payload.get("rendered_scene")
        if rendered_scene:
            scene_text = rendered_scene.get("scene_text", "")
            title = rendered_scene.get("title", "Scene")
            fallback_note = " _(Blueprint Fallback)_" if rendered_scene.get("is_fallback") else ""
            # Truncate if too long
            preview = scene_text[:800] + "..." if len(scene_text) > 800 else scene_text
            text_parts.append(f"\n🎞️ *{title}*{fallback_note}\n\n{preview}")

        # Export
        file_path = payload.get("file_path")
        if file_path:
            text_parts.append(f"\n📄 *Export 완료*\n`{file_path}`\n_서버에 저장되었습니다. 웹 허브에서 다운로드하세요._")

        # Status
        beats_count = payload.get("beats")
        rendered_count = payload.get("rendered")
        if beats_count is not None:
            text_parts.append(f"\n📊 *프로젝트 현황*\n  비트: {beats_count}개 | 렌더링: {rendered_count}개")

        # Warnings
        if response.warnings:
            for w in response.warnings:
                text_parts.append(f"\n⚠️ _{w}_")

        full_text = "\n".join(text_parts)
        # Hard truncate to Telegram limit
        if len(full_text) > TelegramTranslator.MAX_TEXT_LEN:
            full_text = full_text[:TelegramTranslator.MAX_TEXT_LEN] + "\n..._[텍스트 초과 — 웹 허브에서 전체 보기]_"

        # 3. Inline Keyboard (Quick Actions)
        keyboard = TelegramTranslator._build_keyboard(response, cards)

        result = {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": full_text,
            "parse_mode": "Markdown",
        }
        if keyboard:
            result["reply_markup"] = {"inline_keyboard": keyboard}

        return result

    @staticmethod
    def _momentum_bar(momentum: float) -> str:
        """Renders a text-based momentum bar."""
        filled = int(min(momentum / 5.0, 1.0) * 10)
        return "█" * filled + "░" * (10 - filled)

    @staticmethod
    def _build_keyboard(response: CommonResponse, cards: List[Dict]) -> List[List[Dict]]:
        """Builds an inline keyboard for common actions."""
        keyboard = []

        # Pick buttons for first 3 cards (to avoid overflow)
        if cards:
            pick_row = []
            for card in cards[:3]:
                pick_row.append({
                    "text": f"✅ {card.get('name', '?')[:10]}",
                    "callback_data": f"/pick {card.get('cid', '')}"
                })
            if pick_row:
                keyboard.append(pick_row)

        # Action row
        action_row = [
            {"text": "🔄 Stream", "callback_data": "/stream"},
            {"text": "⚡ Surge", "callback_data": "/surge"},
            {"text": "🎬 Render", "callback_data": "/render"},
        ]
        keyboard.append(action_row)

        # Export + Status row
        utility_row = [
            {"text": "📄 Export", "callback_data": "/export"},
            {"text": "📊 Status", "callback_data": "/status"},
        ]
        keyboard.append(utility_row)

        return keyboard
