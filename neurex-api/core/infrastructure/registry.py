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
    context_window: int
    capabilities: List[ModelCapability]
    recommended_tasks: List[str]
    vram_required_gb: float
    description: Optional[str] = "No description available."
    benchmarks: Optional[Dict[str, str]] = {}
    repo_url: Optional[str] = None

# Abandoning predefined library in favor of real-time infrastructure discovery.
# Suggestions are now handled directly in the UI or via specialized recommendation logic.
MODEL_REGISTRY: List[ModelProfile] = []

class LLMRecommender:
    @staticmethod
    def recommend(task_type: str, available_vram_gb: float = 24.0) -> Optional[ModelProfile]:
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
    # Search for GGUF models primarily as they are most portable
    api_url = f"https://huggingface.co/api/models?search={query}&filter=gguf&sort=downloads&direction=-1&limit=15"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for m in data:
                        # Estimate VRAM and context from tags if available, else defaults
                        tags = m.get("tags", [])
                        size_tag = next((t for t in tags if "B" in t and any(c.isdigit() for c in t)), "Unknown")
                        
                        results.append({
                            "name": m["id"],
                            "engine": "llamacpp",
                            "params": size_tag,
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
        print(f"HF Search Error: {e}")
    return []

