"""
core/infrastructure/registry.py
Model Registry and Resource Definitions.
Data Sources:
- Hugging Face Open LLM Leaderboard (https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
- Artificial Analysis (https://artificialanalysis.ai)
- Official Model Cards: Alibaba (Qwen), Meta (Llama), Stability AI, OpenAI (Whisper)
"""

from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel

log = structlog.get_logger()


class ModelCapability(str, Enum):
    CODING = "coding"
    REASONING = "reasoning"
    THINKING = "thinking"
    CHAT = "chat"
    VISION = "vision"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    EMBEDDING = "embedding"


class ModelProfile(BaseModel):
    name: str
    engine: str  # "ollama", "vllm", "llamacpp"
    params: str  # e.g. "8B", "70B"
    size_gb: float = 0.0
    context_window: int
    capabilities: list[ModelCapability]
    recommended_tasks: list[str]
    vram_required_gb: float
    description: str | None = "No description available."
    benchmarks: dict[str, str] | None = {}
    repo_url: str | None = None
    variants: list[dict[str, Any]] | None = []


# Abandoning predefined library in favor of real-time infrastructure discovery.
# Suggestions are now handled directly in the UI or via specialized recommendation logic.
MODEL_REGISTRY: list[ModelProfile] = []


class LLMRecommender:
    _cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    @classmethod
    async def discover_best_in_class(cls, task_role: str, available_vram_gb: float = 0.0) -> dict[str, Any] | None:
        import re
        import time

        import aiohttp

        now = time.time()
        if task_role in cls._cache:
            ts, cached_result = cls._cache[task_role]
            if now - ts < 3600:
                log.info("registry.recommend_cached", role=task_role)
                return cls._filter_by_vram(cached_result, available_vram_gb)

        query_map = {
            "Coding": "coder",
            "Planning": "r1",
            "Testing": "coder",
            "Researching": "instruct",
            "Reviewing": "r1",
        }
        query = query_map.get(task_role, "instruct")
        url = f"https://huggingface.co/api/models?search={query}&filter=gguf&sort=downloads&direction=-1&limit=8&full=true"
        
        models_data = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        models_data = await resp.json()
        except Exception as e:
            log.error("registry.hf_fetch_failed", error=str(e))
            return None

        candidates = []
        for m in models_data:
            model_id = m.get("id", "")
            downloads = m.get("downloads", 0)
            likes = m.get("likes", 0)
            trending = m.get("trendingScore", 0.0)
            created_at = m.get("createdAt", "")
            
            freshness = 0.0
            if created_at:
                try:
                    from datetime import datetime
                    created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    age_days = (datetime.now(created_date.tzinfo) - created_date).days
                    freshness = max(0.0, 1.0 - (age_days / 180.0))
                except Exception:
                    pass
            
            tags = m.get("tags", [])
            params_str = next((t for t in tags if "B" in t and any(c.isdigit() for c in t)), "Unknown").upper()
            p_match = re.search(r"([0-9.]+)", params_str)
            params_val = float(p_match.group(1)) if p_match else 0.0
            if params_val == 0.0:
                p_match = re.search(r"([0-9.]+)[bB]", model_id)
                params_val = float(p_match.group(1)) if p_match else 7.0
            
            vram_required = params_val * 0.65 + 2.0
            
            benchmark_score = 0.0
            card_data = m.get("cardData", {}) or {}
            eval_results = card_data.get("model-index", []) or []
            
            metrics_found = []
            if isinstance(eval_results, list):
                for er in eval_results:
                    for result in er.get("results", []):
                        for metric in result.get("metrics", []):
                            try:
                                val = float(metric.get("value", 0))
                                metrics_found.append(val)
                            except (ValueError, TypeError):
                                pass
            
            if metrics_found:
                benchmark_score = sum(metrics_found) / len(metrics_found)
                if benchmark_score < 1.0:
                    benchmark_score *= 100
            else:
                if "coder" in model_id.lower():
                    benchmark_score = 70.0 + (params_val * 0.5)
                elif "r1" in model_id.lower() or "reason" in model_id.lower():
                    benchmark_score = 75.0 + (params_val * 0.4)
                else:
                    benchmark_score = 65.0 + (params_val * 0.3)
            
            candidates.append({
                "id": model_id,
                "downloads": downloads,
                "likes": likes,
                "trending": trending,
                "freshness": freshness,
                "params": f"{params_val}B",
                "params_val": params_val,
                "vram_required_gb": vram_required,
                "benchmark_score": min(100.0, benchmark_score),
            })
            
        if not candidates:
            return None
            
        max_downloads = max(c["downloads"] for c in candidates) or 1
        max_trending = max(c["trending"] for c in candidates) or 1
        
        for c in candidates:
            norm_pop = c["downloads"] / max_downloads
            norm_trend = c["trending"] / max_trending
            norm_fresh = c["freshness"]
            norm_bench = c["benchmark_score"] / 100.0
            c["score"] = (0.1 * norm_pop) + (0.1 * norm_fresh) + (0.2 * norm_trend) + (0.6 * norm_bench)
            
        candidates.sort(key=lambda x: x["score"], reverse=True)
        cls._cache[task_role] = (now, candidates)
        return cls._filter_by_vram(candidates, available_vram_gb)

    @staticmethod
    def _filter_by_vram(candidates: list[dict[str, Any]], available_vram: float) -> dict[str, Any] | None:
        if available_vram <= 0:
            try:
                from core.infrastructure.vram_pool import vram_pool
                available_vram = vram_pool.total_capacity_gb
            except Exception:
                available_vram = 8.0
        
        fit = [c for c in candidates if c["vram_required_gb"] <= available_vram]
        return fit[0] if fit else candidates[0]

    @staticmethod
    def recommend(task_type: str, available_vram_gb: float = 0.0) -> ModelProfile | None:
        # Backward compatibility fallback
        return None


async def search_huggingface(query: str) -> list[dict[str, Any]]:
    """
    Search Hugging Face for models compatible with the Neurex ecosystem.
    """
    import aiohttp

    # Search for GGUF models primarily as they are most portable. Include siblings for size info.
    api_url = f"https://huggingface.co/api/models?search={query}&filter=gguf&sort=downloads&direction=-1&limit=15&full=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for m in data:
                        tags = m.get("tags", [])
                        size_tag = next(
                            (t for t in tags if "B" in t and any(c.isdigit() for c in t)), "Unknown"
                        )

                        # Primary repository record
                        results.append(
                            {
                                "id": m["id"],
                                "name": m["id"],
                                "engine": "llamacpp",
                                "params": size_tag,
                                "size_gb": 0,  # Will populate below
                                "context_window": 32768,
                                "vram_required_gb": 0,
                                "recommended_tasks": tags[:5],
                                "is_downloaded": False,
                                "is_community": True,
                                "origin": "HF",
                                "downloads": m.get("downloads", 0),
                                "likes": m.get("likes", 0),
                                "repo_url": f"https://huggingface.co/{m['id']}",
                                "variants": [
                                    {"name": s.get("rfilename"), "size_gb": 0.0, "params": size_tag}
                                    for s in m.get("siblings", [])
                                    if s.get("rfilename", "").endswith(".gguf")
                                ],
                            }
                        )

                    # Parallel fetch tree info for top results to get actual LFS sizes
                    async def fetch_sizes(model_idx):
                        m_obj = data[model_idx]
                        repo_id = m_obj["id"]
                        tree_url = f"https://huggingface.co/api/models/{repo_id}/tree/main?lfs=true"
                        try:
                            async with session.get(tree_url, timeout=5) as t_resp:
                                if t_resp.status == 200:
                                    tree_data = await t_resp.json()
                                    if not isinstance(tree_data, list):
                                        return

                                    variants = []
                                    import re

                                    for item in tree_data:
                                        if isinstance(item, dict) and item.get("path", "").endswith(
                                            ".gguf"
                                        ):
                                            fname = item["path"]
                                            # Try to extract params from filename if repo tag is Unknown
                                            p_match = re.search(r"([0-9.]+[bB])", fname)
                                            v_params = (
                                                p_match.group(1).upper()
                                                if p_match
                                                else results[model_idx]["params"]
                                            )

                                            variants.append(
                                                {
                                                    "name": fname,
                                                    "size_gb": round(
                                                        item.get("size", 0) / (1024**3), 2
                                                    ),
                                                    "params": v_params,
                                                }
                                            )

                                    if variants:
                                        results[model_idx]["variants"] = variants
                                        results[model_idx]["size_gb"] = variants[0]["size_gb"]
                                        # Update top-level params if we found a better one
                                        if (
                                            results[model_idx]["params"] == "Unknown"
                                            and variants[0]["params"] != "Unknown"
                                        ):
                                            results[model_idx]["params"] = variants[0]["params"]
                        except Exception:
                            pass

                    import asyncio

                    tasks = [fetch_sizes(i) for i in range(len(results))]
                    await asyncio.gather(*tasks)

                    return results
    except Exception as e:
        log.error("hf_search_error", error=str(e))
    return []
