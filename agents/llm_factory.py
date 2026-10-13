"""
Experimental deterministic mock responder; no remote model inference.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Padua Vte Prediction Score"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock responder]: No clinical analysis or external verification performed. Input: '{prompt[:60]}...'."


class LLMFactory:
    """Creates only the local mock responder, with limited identifier checks."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Padua Vte Prediction Score"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(f"Provider {provider!r} is not implemented; only the mock provider is available")
