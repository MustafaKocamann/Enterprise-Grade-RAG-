import re
from typing import Optional, Tuple
import logfire

# Common prompt injection and adversarial patterns
_BLOCKED_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"(system\s+prompt|reveal\s+instructions)", re.IGNORECASE),
    re.compile(r"\b(jailbreak|dan\s+mode)\b", re.IGNORECASE),
]


def initialize_rails() -> None:
    """Initialize security guardrails and load safety policies."""
    logfire.info("🛡️ Guardrails initialized successfully.")


def guard(query: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluates input text against safety guardrails.
    Returns:
        (rail_fired, rail_response)
    """
    if not query or not query.strip():
        return True, "Boş istek gönderilemez / Query cannot be empty."

    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(query):
            logfire.warning(f"🛡️ Guardrail triggered: matched pattern {pattern.pattern}")
            return (
                True,
                "İsteğiniz güvenlik ve içerik politikaları nedeniyle engellendi. / Your request was blocked by security guardrails.",
            )

    return False, None
