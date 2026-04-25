"""
core/infrastructure/benchmarker.py
Runs standardized performance tests against LLM engines.
"""
import time
import httpx
import asyncio
import structlog
from typing import Dict, List, Any
from core.agents.base_agent import get_ollama_base

log = structlog.get_logger()

BENCHMARK_PROMPT = "Write a Python function to sort a list of dictionaries by a specific key."

class Benchmarker:
    async def run_benchmark(self, model_name: str) -> Dict[str, Any]:
        """Measure TPS and TTFT for a given model."""
        start_time = time.time()
        ttft = 0.0
        tokens = 0
        
        payload = {
            "model": model_name,
            "prompt": BENCHMARK_PROMPT,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", f"{get_ollama_base()}/api/generate", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line: continue
                        if ttft == 0:
                            ttft = time.time() - start_time
                        tokens += 1
            
            total_time = time.time() - start_time
            tps = tokens / total_time if total_time > 0 else 0
            
            return {
                "model": model_name,
                "ttft_ms": round(ttft * 1000, 2),
                "tps": round(tps, 2),
                "total_tokens": tokens,
                "status": "success"
            }
        except Exception as e:
            return {"model": model_name, "status": "failed", "error": str(e)}

    async def compare_all(self, models: List[str]) -> List[Dict[str, Any]]:
        """Run benchmarks against multiple models in sequence."""
        results = []
        for model in models:
            log.info("benchmarker.running", model=model)
            res = await self.run_benchmark(model)
            results.append(res)
        return results
