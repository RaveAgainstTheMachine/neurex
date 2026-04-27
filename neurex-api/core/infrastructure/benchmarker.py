"""
core/infrastructure/benchmarker.py
Runs standardized performance tests against LLM engines using native telemetry.
"""
import time
import httpx
import asyncio
import structlog
import os
from typing import Dict, List, Any
from core.agents.base_agent import get_ollama_base

log = structlog.get_logger()

BENCHMARK_PROMPT = "Write a 500-word essay on the history of decentralized computing."
BENCHMARK_MODEL = "qwen2.5-coder:1.5b" # Default for auto-discovery

class Benchmarker:
    def __init__(self):
        self.last_results: Dict[str, Any] = {}

    async def run_benchmark(self, model_name: str | None = None) -> Dict[str, Any]:
        """Measure TPS (Tokens Per Second) and TTFT (Time To First Token) using native Ollama metrics."""
        model = model_name or BENCHMARK_MODEL
        log.info("benchmarker.start", model=model)
        
        payload = {
            "model": model,
            "prompt": BENCHMARK_PROMPT,
            "stream": False,
            "options": {"num_predict": 256}
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Ensure model exists
                await client.post(f"{get_ollama_base()}/api/pull", json={"name": model, "stream": False})
                
                start_time = time.time()
                resp = await client.post(f"{get_ollama_base()}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                
                # Ollama returns ns, convert to s
                eval_count = data.get("eval_count", 0)
                eval_duration_s = data.get("eval_duration", 0) / 1e9
                load_duration_ms = data.get("load_duration", 0) / 1e6
                
                tps = eval_count / eval_duration_s if eval_duration_s > 0 else 0.0
                
                result = {
                    "model": model,
                    "tps": round(tps, 2),
                    "load_ms": int(load_duration_ms),
                    "total_tokens": eval_count,
                    "status": "success",
                    "timestamp": time.time()
                }
                
                self.last_results = result
                log.info("benchmarker.complete", model=model, tps=result["tps"])
                return result
                
        except Exception as e:
            log.error("benchmarker.failed", model=model, error=str(e))
            return {"model": model, "status": "failed", "error": str(e)}

    async def compare_all(self, models: List[str]) -> List[Dict[str, Any]]:
        """Run benchmarks against multiple models in sequence."""
        results = []
        for model in models:
            res = await self.run_benchmark(model)
            results.append(res)
        return results

benchmarker = Benchmarker()
