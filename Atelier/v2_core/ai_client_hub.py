from typing import Dict, Any, List, Optional
from gemma_bridge import GemmaBridge

class AIClientHub:
    _bridge = None

    @classmethod
    def get_bridge(cls):
        if cls._bridge is None:
            cls._bridge = GemmaBridge()
        return cls._bridge

    @staticmethod
    async def generate(prompt: str, model_tier: str = "LOCAL", options: Optional[Dict[str, Any]] = None) -> str:
        """
        Routes the generation request to the local GemmaBridge.
        External/Commercial tiers are disabled for full offline autonomy.
        """
        bridge = AIClientHub.get_bridge()
        # model_tier argument is kept for compatibility but forced to LOCAL logic
        try:
            return await bridge.simple_prompt(prompt)
        except Exception as e:
            return f"[AI_CLIENT_HUB ERROR] Failed to connect to local Gemma: {e}"
