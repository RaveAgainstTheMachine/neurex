"""
core/infrastructure/registry.py
Model Registry and Resource Definitions.
Data Sources: 
- Hugging Face Open LLM Leaderboard (https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
- Artificial Analysis (https://artificialanalysis.ai)
- Official Model Cards: Alibaba (Qwen), Meta (Llama), Stability AI, OpenAI (Whisper)
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import structlog

log = structlog.get_logger()

class ModelCapability(str, Enum):
    CODING      = "coding"
    REASONING   = "reasoning"
    THINKING    = "thinking"
    CHAT        = "chat"
    VISION      = "vision"
    AUDIO       = "audio"
    VIDEO       = "video"
    IMAGE       = "image"
    EMBEDDING   = "embedding"

class ModelProfile(BaseModel):
    name: str
    engine: str  # "ollama", "vllm", "llamacpp"
    params: str  # e.g. "8B", "70B"
    size_gb: float = 0.0
    context_window: int
    capabilities: List[ModelCapability]
    recommended_tasks: List[str]
    vram_required_gb: float
    description: Optional[str] = "No description available."
    benchmarks: Optional[Dict[str, str]] = {}
    repo_url: Optional[str] = None
    variants: Optional[List[Dict[str, Any]]] = []

# Abandoning predefined library in favor of real-time infrastructure discovery.
# Suggestions are now handled directly in the UI or via specialized recommendation logic.
MODEL_REGISTRY: List[ModelProfile] = []

class LLMRecommender:
    @staticmethod
    def recommend(task_type: str, available_vram_gb: float = 0.0) -> Optional[ModelProfile]:
        # If available_vram_gb is not provided, use the global mesh pool
        if available_vram_gb <= 0:
            from core.infrastructure.vram_pool import vram_pool
            available_vram_gb = vram_pool.total_capacity_gb

        candidates = [m for m in MODEL_REGISTRY if m.vram_required_gb <= available_vram_gb]
        
        # Priority mapping
        task_map = {
            "think": ModelCapability.THINKING,
            "logic": ModelCapability.THINKING,
            "code": ModelCapability.CODING,
            "vision": ModelCapability.VISION,
            "image": ModelCapability.IMAGE,
            "audio": ModelCapability.AUDIO,
            "video": ModelCapability.VIDEO,
            "chat": ModelCapability.CHAT
        }
        
        target_cap = next((cap for key, cap in task_map.items() if key in task_type.lower()), None)
        
        if target_cap:
            best = next((m for m in candidates if target_cap in m.capabilities), None)
            if best: return best
            
        return candidates[0] if candidates else None

async def search_huggingface(query: str) -> List[Dict[str, Any]]:
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
                        size_tag = next((t for t in tags if "B" in t and any(c.isdigit() for c in t)), "Unknown")
                        
                        # Primary repository record
                        results.append({
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
                                for s in m.get("siblings", []) if s.get("rfilename", "").endswith(".gguf")
                            ]
                        })

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
                                        if isinstance(item, dict) and item.get("path", "").endswith(".gguf"):
                                            fname = item["path"]
                                            # Try to extract params from filename if repo tag is Unknown
                                            p_match = re.search(r'([0-9.]+[bB])', fname)
                                            v_params = p_match.group(1).upper() if p_match else results[model_idx]["params"]
                                            
                                            variants.append({
                                                "name": fname,
                                                "size_gb": round(item.get("size", 0) / (1024 ** 3), 2),
                                                "params": v_params
                                            })
                                    
                                    if variants:
                                        results[model_idx]["variants"] = variants
                                        results[model_idx]["size_gb"] = variants[0]["size_gb"]
                                        # Update top-level params if we found a better one
                                        if results[model_idx]["params"] == "Unknown" and variants[0]["params"] != "Unknown":
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

