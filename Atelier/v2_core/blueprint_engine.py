"""
Cinematic Blueprint Engine for Phase 8.3.
Translates narrative content into visual specs and AI image prompts.
"""
import random
from typing import Dict, Any, List

class BlueprintEngine:
    SHOT_TYPES = ["Extreme Close-up", "Close-up", "Medium Shot", "Full Shot", "Wide Shot", "Bird's Eye View"]
    CAMERA_MOVEMENTS = ["Static", "Slow Zoom In", "Pan Left to Right", "Low Angle Tilt", "Handheld Shake", "Dolly Tracking"]
    LIGHTING_MOODS = ["Natural Soft Light", "Cinematic Noir (High Contrast)", "Golden Hour Glow", "Moody Cold Blue", "Neon Cyberpunk Lights", "Dreamy Hazy Sun"]

    @staticmethod
    def generate_visual_spec(content: str, momentum: float = 1.0) -> Dict[str, Any]:
        """Maps narrative content to cinematic parameters."""
        # Simple heuristic mapping for MVP
        # High momentum -> more dynamic shots
        if momentum > 2.0:
            shot = random.choice(["Extreme Close-up", "Handheld Shake"])
            move = "Rapid Tracking" if momentum > 3.0 else random.choice(BlueprintEngine.CAMERA_MOVEMENTS)
        else:
            shot = random.choice(BlueprintEngine.SHOT_TYPES)
            move = random.choice(BlueprintEngine.CAMERA_MOVEMENTS)

        # Keyword based lighting
        lighting = BlueprintEngine.LIGHTING_MOODS[0]
        lower_content = content.lower()
        if any(w in lower_content for w in ["어둠", "어두운", "비밀", "그림자", "배신"]):
            lighting = "Cinematic Noir (High Contrast)"
        elif any(w in lower_content for w in ["희망", "태양", "발견", "기쁨"]):
            lighting = "Golden Hour Glow"
        elif any(w in lower_content for w in ["긴장", "추격", "도시", "차가운"]):
            lighting = "Moody Cold Blue"
            
        spec = {
            "shot_type": shot,
            "movement": move,
            "lighting": lighting,
            "mood": "Cinematic"
        }
        
        # Build Professional Image Prompt (The 'Visual Blueprint')
        spec["image_prompt"] = BlueprintEngine._build_image_prompt(content, spec)
        return spec

    @staticmethod
    def _build_image_prompt(content: str, spec: Dict[str, Any]) -> str:
        """Constructs a high-quality prompt for Image Generation AI."""
        # Clean up content for prompt
        summary = content.split('.')[0] # Use first sentence as base
        
        prompt = (
            f"Cinematic {spec['shot_type']} photography of {summary}. "
            f"{spec['lighting']}, {spec['movement']} effect. "
            f"Super-detailed, 8k, shot on 35mm lens, highly atmospheric, professional color grading --ar 21:9"
        )
        return prompt

    @staticmethod
    def attach_blueprints_to_cards(cards: List[Dict[str, Any]], momentum: float = 1.0):
        """Batch attaches visual specs to a list of card objects."""
        for card in cards:
            if "visual_spec" not in card:
                card["visual_spec"] = BlueprintEngine.generate_visual_spec(card["summary"], momentum)
