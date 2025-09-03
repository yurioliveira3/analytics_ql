"""
Adaptadores para diferentes provedores de LLM.
"""

from .gemini_adapter import GeminiAdapter
from .ollama_adapter import OllamaAdapter

__all__ = ["GeminiAdapter", "OllamaAdapter"]
