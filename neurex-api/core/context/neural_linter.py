"""
core/context/neural_linter.py
Phase 45: Sentient IDE (Autonomous Self-Repair)
Architectural validation layer that verifies proposed mutations against DESIGN_SYSTEM.md and ARCHITECTURE.md.
"""

import json
import os

import httpx
import structlog

log = structlog.get_logger()


class NeuralLinter:
    def __init__(self):
        self.workspace_path = os.getenv("WORKSPACE_PATH", os.getcwd())
        self.design_system_path = os.path.join(self.workspace_path, "DESIGN_SYSTEM.md")
        self.architecture_path = os.path.join(self.workspace_path, "ARCHITECTURE.md")

    async def verify_mutation(
        self, name: str, args: dict, conversation_id: str
    ) -> tuple[bool, str]:
        """
        Validates a file mutation against architectural standards.
        Returns: (is_valid, reason)
        """
        # Phase 2.1: Bypass in Mock Mode
        if os.getenv("NEUREX_MOCK_LLM") == "true":
            return True, "Mock mode bypass"
        # 1. Extraction of the proposed change
        target_file = args.get("path") or args.get("TargetFile") or args.get("target_file")
        content = args.get("content") or args.get("ReplacementContent") or args.get("CodeContent")

        if not target_file or not content:
            # If we can't see the content (e.g. simple delete), skip architectural linting
            return True, ""

        # 2. Context Loading
        standards = ""
        if os.path.exists(self.design_system_path):
            with open(self.design_system_path) as f:
                standards += f"### DESIGN SYSTEM\n{f.read()}\n\n"
        if os.path.exists(self.architecture_path):
            with open(self.architecture_path) as f:
                standards += f"### ARCHITECTURE\n{f.read()}\n\n"

        if not standards:
            return True, "No standards defined."

        # 3. Neural Validation
        # We use a specialized "Neural Linter" prompt
        prompt = f"""
You are the Neurex Neural Linter. Your task is to verify if a proposed code mutation follows the project's ARCHITECTURE and DESIGN SYSTEM.

PROPOSED MUTATION:
Tool: {name}
File: {target_file}
New Content Fragment:
{content[:2000]}

PROJECT STANDARDS:
{standards}

CRITICAL RULES:
1. If the change breaks a performance mandate (e.g. adds global re-renders, recursive walks), FAIL it.
2. If the change violates the design system (e.g. wrong colors, jerky animations), FAIL it.
3. If the change is architecturally sound, PASS it.

RESPONSE FORMAT:
You must respond with a JSON object:
{{
  "verdict": "PASS" | "FAIL",
  "reason": "Clear explanation of why it failed or empty if passed"
}}
"""
        try:
            from core.infrastructure.mesh import mesh_router

            # Use a fast but smart model for linting
            linter_model = os.getenv("LINTER_MODEL", "qwen2.5-coder:7b")

            # Use direct ollama call to avoid agent recursion loops
            ollama_url = await mesh_router.get_best_inference_node(linter_model)
            target_url = (
                f"{ollama_url}/api/chat"
                if "ollama_proxy" not in ollama_url
                else ollama_url.replace("ollama_proxy", "ollama_proxy/api/chat")
            )

            payload = {
                "model": linter_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(target_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    result_text = data.get("message", {}).get("content", "{}")
                    result = json.loads(result_text)
                    if result.get("verdict") == "FAIL":
                        log.warning(
                            "neural_linter_rejection", file=target_file, reason=result.get("reason")
                        )
                        return False, result.get("reason")
        except Exception as e:
            log.error("neural_linter_error", error=str(e))
            # On error, we default to PASS to avoid blocking development if linter is down
            return True, "Linter internal error."

        return True, ""
