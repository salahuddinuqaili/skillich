"""Local LLM integration skill for privacy-preserving inference."""

import os
from typing import Any, Dict, List

from core.base import Skill, SkillResult, SkillStatus


class LocalLLMSkill(Skill):
    """Summarize text using a local LLM (e.g., Ollama, vLLM, llama.cpp).

    Use this when text summarization is needed and data must stay on-device
    for privacy, compliance, or latency reasons. Requires a local LLM server
    running on the configured endpoint.
    """

    @property
    def name(self) -> str:
        return "local_summarizer"

    @property
    def description(self) -> str:
        return (
            "Summarize text using a local LLM for privacy and speed. "
            "Requires a local model server (Ollama, vLLM, or llama.cpp) running. "
            "Set LOCAL_LLM_ENDPOINT env var to configure (default: http://localhost:11434)."
        )

    @property
    def tags(self) -> List[str]:
        return ["llm", "local", "summarization", "privacy"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to summarize."},
                "model": {
                    "type": "string",
                    "description": "The local model to use (default: llama3).",
                },
            },
            "required": ["text"],
        }

    def execute(self, text: str, model: str = "llama3", **kwargs) -> SkillResult:
        endpoint = os.environ.get("LOCAL_LLM_ENDPOINT", "http://localhost:11434")

        try:
            import requests

            response = requests.post(
                f"{endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": f"Summarize the following text concisely:\n\n{text}",
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return SkillResult(
                status=SkillStatus.SUCCESS,
                data={"summary": data.get("response", ""), "model": model},
                metadata={"endpoint": endpoint},
            )
        except ImportError:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="'requests' package not installed. Run: pip install requests",
            )
        except Exception as e:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Local LLM call failed: {e}. Is {endpoint} running with model '{model}'?",
                metadata={"endpoint": endpoint, "model": model},
            )
