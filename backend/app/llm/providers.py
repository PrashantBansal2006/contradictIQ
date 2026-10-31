import os
import json
import time
from typing import Any
from backend.app.llm.base import LLMProvider

class NoneProvider:
    """Deterministic fallback provider when LLM is disabled or unavailable."""
    def complete_json(
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any] | None:
        return None

class GeminiProvider:
    """Google Gemini provider with JSON schema enforcement and retry logic."""
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def complete_json(
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any] | None:
        if not self.api_key or not self.client:
            return None

        from google.genai import types

        # Architecture §7.1: 2 retry attempts with backoff on failure
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=temperature,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
        return None

def get_llm_provider() -> LLMProvider:
    """Factory returning configured LLM provider or fallback NoneProvider."""
    provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    
    if provider_name == "gemini" and api_key:
        return GeminiProvider(api_key=api_key)
    return NoneProvider()

