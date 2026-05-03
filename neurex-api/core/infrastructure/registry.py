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
                        
                        # Extract all GGUF variants
                        variants = []
                        siblings = m.get("siblings", [])
                        for s in siblings:
                            fname = s.get("rfilename", "")
                            if fname.endswith(".gguf"):
                                variants.append({
                                    "name": fname,
                                    "size_gb": round(s.get("size", 0) / (1024 ** 3), 2),
                                    "params": size_tag # Default to repo tag
                                })
                        
                        # Default size from first variant
                        size_gb = variants[0]["size_gb"] if variants else 0.0
                        
                        results.append({
                            "name": m["id"],
                            "engine": "llamacpp",
                            "params": size_tag,
                            "size_gb": size_gb,
                            "variants": variants,
                            "context_window": 32768,
                            "vram_required_gb": 8.0 if "7B" in size_tag else 20.0 if "30B" in size_tag else 12.0,
                            "recommended_tasks": ["community_model"],
                            "downloads": m.get("downloads", 0),
                            "likes": m.get("likes", 0),
                            "is_community": True,
                            "repo_url": f"https://huggingface.co/{m['id']}"
                        })
                    return results
    except Exception as e:
        log.error("hf_search_error", error=str(e))
    return []

