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

# Default registry of elite open-source models
MODEL_REGISTRY: List[ModelProfile] = [
    ModelProfile(
        name="deepseek-r1:32b",
        engine="ollama",
        params="32B",
        context_window=128000,
        capabilities=[ModelCapability.THINKING, ModelCapability.REASONING, ModelCapability.CHAT],
        recommended_tasks=["logic", "planning", "deep_thinking"],
        vram_required_gb=20.0,
        description="DeepSeek-R1 is an elite reasoning model optimized for chain-of-thought processing. It excels at complex logic, mathematical proofs, and architectural planning.",
        benchmarks={"MMLU": "84.5", "HumanEval": "78.2", "GSM8K": "92.1"},
        repo_url="https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    ),
    ModelProfile(
        name="qwen2.5-coder:32b",
        engine="ollama",
        params="32B",
        context_window=128000,
        capabilities=[ModelCapability.CODING, ModelCapability.CHAT],
        recommended_tasks=["coding", "refactoring", "system_design"],
        vram_required_gb=20.0,
        description="The Qwen2.5-Coder series is the latest state-of-the-art coding model. It features significantly improved code generation, bug fixing, and multi-language support.",
        benchmarks={"Pass@1": "71.4", "MBPP": "75.8", "LiveCode": "68.2"},
        repo_url="https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct"
    ),
    ModelProfile(
        name="llama3.2-vision:11b",
        engine="ollama",
        params="11B",
        context_window=128000,
        capabilities=[ModelCapability.VISION, ModelCapability.CHAT],
        recommended_tasks=["vision", "image_analysis", "ocr"],
        vram_required_gb=8.5,
        description="Llama-3.2 Vision is a multi-modal powerhouse. It can reason about visual context, perform OCR on complex documents, and describe image-to-text transitions with high fidelity.",
        benchmarks={"MMMU": "42.1", "MathVista": "38.5", "DocVQA": "82.3"},
        repo_url="https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct"
    ),
    ModelProfile(
        name="stable-diffusion-v1.5",
        engine="vllm",
        params="1B",
        context_window=0,
        capabilities=[ModelCapability.IMAGE],
        recommended_tasks=["image_generation", "art"],
        vram_required_gb=6.0,
        description="The industry standard for image generation. SD 1.5 offers a perfect balance of speed and quality for creative asset generation.",
        benchmarks={"FID": "12.4", "ClipScore": "28.5"},
        repo_url="https://huggingface.co/runwayml/stable-diffusion-v1.5"
    ),
    ModelProfile(
        name="whisper-large-v3-turbo",
        engine="ollama",
        params="1.5B",
        context_window=0,
        capabilities=[ModelCapability.AUDIO],
        recommended_tasks=["audio", "transcription", "speech_to_text"],
        vram_required_gb=4.0,
        description="OpenAI's latest Whisper variant optimized for speed. It delivers near real-time transcription with high robustness to noise.",
        benchmarks={"WER": "4.2%", "Speed": "30x Realtime"},
        repo_url="https://huggingface.co/openai/whisper-large-v3-turbo"
    ),
    ModelProfile(
        name="ltx-video",
        engine="vllm",
        params="Multi-Modal",
        context_window=32768,
        capabilities=[ModelCapability.VIDEO],
        recommended_tasks=["video", "video_generation"],
        vram_required_gb=24.0,
        description="LTX-Video is an advanced video generation model capable of high-consistency motion and complex scene transitions.",
        benchmarks={"FVD": "180.2", "MotionScore": "0.85"},
        repo_url="https://huggingface.co/Lightricks/LTX-Video"
    )
]

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

