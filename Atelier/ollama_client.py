from __future__ import annotations
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

def ollama_generate(prompt: str, system: str = "") -> str:
    """Compatibility function for scene_engine and other modules."""
    client = OllamaClient()
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import threading
        result = [None]
        exc = [None]
        def run_in_thread():
            try:
                result[0] = asyncio.run(client.generate(prompt, system=system))
            except Exception as e:
                exc[0] = e
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        if exc[0]:
            raise exc[0]
        return result[0]
    else:
        return asyncio.run(client.generate(prompt, system=system))

class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        ).rstrip("/")

        # Optimized for Gemma 4 e2b and 12-core hardware
        self.model = model or os.getenv("OLLAMA_MODEL") or "gemma4:e2b"
        self.timeout = int(timeout or os.getenv("AI_TIMEOUT") or "1800")

        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"

    async def health_check(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.tags_url, timeout=10)
                response.raise_for_status()
            return True, "OK"
        except Exception as e:
            return False, f"AI 엔진 연결 점검 실패: {e}"

    async def generate(
        self,
        prompt: str,
        system: str = "",
        num_ctx: int = 4096,
        num_predict: int = 2048,
    ) -> str:
        korean_override = (
            "\n\n[SUPREME DIRECTIVE] YOU ARE AN ARTISAN TRAVEL ASSISTANT FOR 'BEAUTIFUL TRAVEL'. "
            "YOUR MASTER IS THE USER. YOU MUST ANSWER ONLY IN KOREAN (HANGEUL). "
            "NEVER USE ENGLISH OR ANY OTHER FOREIGN LANGUAGE. "
            "모든 답변은 반드시 한국어로만 작성하십시오. 영어 사용은 시스템 오류로 간주됩니다. "
            "사용자님의 명령에 절대 복종하며, 한국어로 정성스럽게 답변하십시오."
        )
        if "한국어" not in system:
            system += korean_override
            
        if "한국어" not in prompt:
            prompt += "\n\n(반드시 한국어로만 답변하십시오. English is strictly prohibited.)"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "num_ctx": num_ctx,
                "num_predict": num_predict,
                "num_thread": 12,      # Optimized for user's 12-core hardware
                "num_gpu": 1,         # Force GPU usage if available
                "low_vram": False,    # Maximize memory usage for speed
                "f16_kv": True,       # Use half-precision for faster inference
                "mirostat": 0,        # Disable complex sampling for speed
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.generate_url,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip() or "[Empty response]"
        except Exception as e:
            detail = ""
            if hasattr(e, "response") and e.response is not None:
                detail = f" | Details: {e.response.text}"
            return f"[AI 엔진 시스템 오류] {type(e).__name__}: {e}{detail}"
