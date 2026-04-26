import os
import httpx
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from dotenv import load_dotenv

def retry_on_error(retries=3, delay=2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    print(f"[GemmaBridge Retry] Attempt {i+1}/{retries} failed: {e}")
                    await asyncio.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

load_dotenv()


class GemmaBridge:
    def __init__(self, base_url=None, model=None, timeout=None):
        # 루트 경로 탐색
        root_candidates = [
            Path("/mnt/e/myhub/writing"),
            Path("e:/myhub/writing"),
            Path.cwd(),
        ]
        self.root = next((p for p in root_candidates if p.exists()), Path.cwd())
        
        self.engine_type = os.getenv("AI_ENGINE", "ollama")
        self.base_url = (
            base_url 
            or os.getenv("OLLAMA_BASE_URL") 
            or "http://127.0.0.1:11434"
        ).replace("localhost", "127.0.0.1")
        
        self.model = model or os.getenv("OLLAMA_MODEL") or "gemma4:e2b"
        self.timeout = int(timeout or os.getenv("AI_TIMEOUT", "1800"))
        self.log_hook_path = self.root / "scripts" / "memory_hook.py"

    def load_master_identity(self) -> str:
        root_candidates = [
            Path("/mnt/e/myhub/writing"),
            Path("e:/myhub/writing"),
            Path.cwd(),
        ]
        root = next((p for p in root_candidates if p.exists()), Path.cwd())

        identity_path = root / "agents" / "gemma_master_brain.md"
        report_path = root / "memory" / "REPORT.md"
        next_task_path = root / "memory" / "NEXT_TASK.md"

        identity = (
            identity_path.read_text(encoding="utf-8")
            if identity_path.exists()
            else "너는 로컬 AI다. 모든 답변은 한국어로만 한다."
        )

        report = ""
        if report_path.exists():
            report = report_path.read_text(encoding="utf-8")[:1500]

        next_task = ""
        if next_task_path.exists():
            next_task = next_task_path.read_text(encoding="utf-8")[:600]

        return (
            f"{identity}\n\n"
            f"---현재 프로젝트 참고 자료---\n"
            f"[REPORT]\n{report}\n\n"
            f"[NEXT_TASK]\n{next_task}\n"
            f"------------------------\n\n"
            f"[MANDATORY BEHAVIOR]\n"
            f"위 자료는 현재 진행 중인 프로젝트의 참고용 배경 지식입니다.\n"
            f"사용자의 질문이나 대화 내용이 위 자료에 없더라도, 절대 '문맥에 없다'며 답변을 거부하지 마십시오.\n"
            f"당신은 스스로 사고할 수 있는 지능형 수석 엔지니어입니다. 자유롭고 창의적인 판단으로 답변하십시오.\n"
            f"모든 응답, 인사, 그리고 설명은 반드시 100% 한국어(한글)로만 작성해야 합니다."
        ).strip()

    async def health_check(self):
        url = f"{self.base_url}/api/tags"
        print(f"[통신망] 상태 점검 중 (Ollama): {url}")
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=10)
                r.raise_for_status()
            return True, "OK (ollama)"
        except Exception as e:
            return False, f"Health Check Failed (ollama): {e}"

    async def chat(self, messages, system_instruction=None):
        if system_instruction is None:
            system_instruction = self.load_master_identity()
        
        # [KOREAN ENFORCEMENT] 한국어 응답 초강력 강제 (시스템 명령 레벨)
        korean_override = (
            "\n\n[SUPREME RULE] ALWAYS ANSWER IN KOREAN (HANGEUL) ONLY. "
            "NEVER USE ENGLISH OR ANY OTHER LANGUAGE EXCEPT FOR CODE BLOCKS. "
            "모든 답변은 반드시 한국어로만 작성하십시오. 영어 사용을 엄격히 금지합니다."
        )
        
        if "한국어" not in system_instruction:
            system_instruction += korean_override
        else:
            system_instruction += "\n\n[MANDATORY] 모든 답변, 보고서, 기술 대화는 반드시 한국어(한글)로만 수행하십시오."
            
        return await self._chat_ollama(messages, system_instruction)

    @retry_on_error(retries=3, delay=2)
    async def _chat_ollama(self, messages, system_instruction):
        url = f"{self.base_url}/api/generate"

        # Ollama API's native system/prompt support is more robust
        user_prompt = "\n".join([m.get("content", "") for m in messages if m.get("role") == "user"])

        # [KOREAN ENFORCEMENT] 프롬프트 말미에 한국어 강제 문구 추가 (최우선순위 확보)
        if "한국어" not in user_prompt:
            user_prompt += "\n\n(반드시 한국어/한글로 답변해 주세요. English is prohibited.)"
            
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_instruction,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "num_ctx": 4096,
                "num_predict": 2048, # 5분 타임아웃 방지를 위해 출력 길이 제한 고도화
                "temperature": 0.4,
                "top_p": 0.9
            },
        }

        print(f"[AI 엔진] 데이터 요청 중: {url}")
        print(f"[GemmaBridge:Ollama] Model: {self.model} | Timeout: {self.timeout}s")

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=self.timeout)
                r.raise_for_status()
                
                # Robust JSON parsing for Ollama's occasional NDJSON or extra junk
                raw_text = r.text.strip()
                try:
                    # Try parsing the whole thing first
                    data = json.loads(raw_text)
                except json.JSONDecodeError:
                    # If it fails, take only the first line (common for NDJSON)
                    data = json.loads(raw_text.split('\n')[0])

                response_text = data.get("response", "").strip() or "[GemmaBridge] Empty response from Ollama."
                
                # 자율 주행 중이거나 판단 결과가 포함된 경우 자동 기억 동기화 시도 (별도 예외 처리)
                try:
                    if "[PLAN]" in response_text or "[EXPECTATION]" in response_text:
                        print("[분석] 계획이 감지되었습니다. 기억 자동 동기화를 시작합니다...")
                        self._sync_to_memory(response_text)
                except Exception as sync_e:
                    print(f"[오류] 자동 동기화 시작 실패: {sync_e}")
                
                return response_text
        except Exception as e:
            detail = ""
            if hasattr(e, "response") and e.response is not None:
                detail = f" | Details: {e.response.text}"
            return f"[GemmaBridge Error] Ollama Request Failed: {type(e).__name__}: {e}{detail}"

    async def interpret_voice_command(self, voice_text: str):
        """
        음성으로 인식된 텍스트를 시스템 명령어로 해석하거나 적절한 응답을 생성합니다.
        """
        system_instruction = (
            "너는 오너의 음성 명령을 해석하는 인공지능 비서 Antigravity다.\n"
            "사용자의 음성을 듣고, 다음 중 하나로 처리해라:\n"
            "1. 시스템 명령어: 사용자 의도가 '/쓰기', '/목록', '/타임라인' 등 명령어에 해당하면 해당 명령어로 변환\n"
            "2. 일반 대화: 명령어가 아니면 자연스러운 한국어 비서 말투로 응답\n"
            "\n[출력 형식]\n"
            "- 명령어인 경우: /명령어 내용\n"
            "- 대화인 경우: 답변 내용\n"
            "\n[언어 규칙] 모든 응답은 반드시 한국어로만 작성해야 합니다. 절대 영어를 섞지 마십시오."
        )
        
        return await self.chat([{"role": "user", "content": voice_text}], system_instruction=system_instruction)

    async def simple_prompt(self, prompt: str):
        return await self.chat([{"role": "user", "content": prompt}])

    def _sync_to_memory(self, report):
        """AI의 판단 결과를 기억 장치에 자동으로 동기화합니다."""
        try:
            # 리포트에서 핵심 내용 추출 (간이)
            task = "Autonomous Engineering Decision"
            result = "Success" if "[PLAN]" in report else "Partial"
            problem = "None"
            next_step = "Plan Implementation"
            
            cmd = [
                sys.executable,
                str(self.log_hook_path),
                task, result, problem, next_step
            ]
            # 비차단 방식으로 실행 (성능 고려)
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"[GemmaBridge] Auto-sync failed (non-blocking): {e}")


if __name__ == "__main__":
    import asyncio

    async def main():
        bridge = GemmaBridge()
        ok, msg = await bridge.health_check()
        print(f"[상태] {msg}")
        if not ok:
            sys.exit(1)

        print(f"[엔진] 종류: {bridge.engine_type}, 주소: {bridge.base_url}, 모델: {bridge.model}")
        res = await bridge.simple_prompt("안녕, 한 줄로만 답해줘.")
        print(res)

    asyncio.run(main())
