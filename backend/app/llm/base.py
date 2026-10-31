from typing import Protocol, Any

class LLMProvider(Protocol):
    """Protocol for LLM structured output extraction per architecture §7.1."""
    def complete_json(
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any] | None:
        ...

