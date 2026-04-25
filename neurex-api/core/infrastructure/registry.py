"""
core/infrastructure/registry.py
Model profiles and recommendation logic.
"""
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel

class ModelCapability(str, Enum):
    CODING      = "coding"
    REASONING   = "reasoning"
    CHAT        = "chat"
    EXTRACTION  = "extraction"
    EMBEDDING   = "embedding"

class ModelProfile(BaseModel):
    name: str
    engine: str  # "ollama", "vllm", "llamacpp"
    params: str  # e.g. "8B", "70B"
    context_window: int
    capabilities: List[ModelCapability]
    recommended_tasks: List[str]
    vram_required_gb: float

# Default registry of high-performing open-source models
MODEL_REGISTRY: List[ModelProfile] = [
    ModelProfile(
        name="qwen2.5-coder:7b",
        engine="ollama",
        params="7B",
        context_window=32768,
        capabilities=[ModelCapability.CODING, ModelCapability.CHAT],
        recommended_tasks=["autocomplete", "inline_fix", "refactor_small"],
        vram_required_gb=5.5
    ),
    ModelProfile(
        name="deepseek-coder-v2:lite",
        engine="ollama",
        params="16B",
        context_window=128000,
        capabilities=[ModelCapability.CODING, ModelCapability.REASONING],
        recommended_tasks=["architecture", "complex_refactor", "bug_hunt"],
        vram_required_gb=12.0
    ),
    ModelProfile(
        name="llama3.1:8b",
        engine="ollama",
        params="8B",
        context_window=128000,
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
        recommended_tasks=["explanation", "summarization", "chat"],
        vram_required_gb=6.0
    ),
    ModelProfile(
        name="codellama:34b",
        engine="ollama",
        params="34B",
        context_window=100000,
        capabilities=[ModelCapability.CODING, ModelCapability.REASONING],
        recommended_tasks=["complex_logic", "long_context"],
        vram_required_gb=20.0
    )
]

class LLMRecommender:
    @staticmethod
    def recommend(task_type: str, available_vram_gb: float = 24.0) -> Optional[ModelProfile]:
        """
        Determine the best model for a specific task based on capabilities and VRAM.
        """
        # Filter by VRAM
        candidates = [m for m in MODEL_REGISTRY if m.vram_required_gb <= available_vram_gb]
        
        # Priority 1: Match recommended_tasks
        best = next((m for m in candidates if task_type in m.recommended_tasks), None)
        if best:
            return best
            
        # Priority 2: Match capabilities
        if "code" in task_type or "refactor" in task_type:
            best = next((m for m in candidates if ModelCapability.CODING in m.capabilities), None)
        else:
            best = next((m for m in candidates if ModelCapability.REASONING in m.capabilities), None)
            
        return best or (candidates[0] if candidates else None)
