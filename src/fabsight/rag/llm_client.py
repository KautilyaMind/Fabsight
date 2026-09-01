"""Small provider abstraction and Google Gemini REST implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import quote

import requests

from fabsight.rag.config import LLMSettings


class LLMConfigurationError(RuntimeError):
    pass


class LLMClient(ABC):
    model_name: str

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, response_schema: dict[str, Any]) -> str:
        """Return a structured JSON string."""


class GoogleLLMClient(LLMClient):
    def __init__(self, settings: LLMSettings) -> None:
        error = settings.validation_error()
        if error:
            raise LLMConfigurationError(error)
        self.model_name = settings.model
        self._api_key = settings.api_key
        self._timeout = settings.timeout_seconds

    def generate(self, system_prompt: str, user_prompt: str, response_schema: dict[str, Any]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(self.model_name, safe='')}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            },
        }
        try:
            response = requests.post(url, headers={"x-goog-api-key": self._api_key}, json=payload, timeout=self._timeout)
            if not response.ok:
                try:
                    provider_message = response.json().get("error", {}).get("message", "")
                except ValueError:
                    provider_message = ""
                detail = f" Google API HTTP {response.status_code}."
                if provider_message:
                    detail += f" {provider_message[:300]}"
                raise RuntimeError(
                    "Configured LLM model is unavailable." + detail +
                    "\n\nCheck:\nLLM_PROVIDER\nLLM_MODEL\nLLM_API_KEY or GOOGLE_API_KEY"
                )
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except RuntimeError:
            raise
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(
                "Configured LLM model is unavailable.\n\nCheck:\nLLM_PROVIDER\nLLM_MODEL\nLLM_API_KEY or GOOGLE_API_KEY"
            ) from exc
