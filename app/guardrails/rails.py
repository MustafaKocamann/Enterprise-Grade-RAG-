import re
import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS


_rails: LLMRails | None = None


def extract_thinking(text: str) -> tuple[str, str | None]:
    """
    Extracts text inside <think>...</think> tags and returns (cleaned_text, thinking_text).
    """
    if not text:
        return text, None

    think_pattern = re.compile(r"<think>(.*?)</think>", flags=re.DOTALL | re.IGNORECASE)
    thoughts = [t.strip() for t in think_pattern.findall(text) if t.strip()]
    cleaned_text = think_pattern.sub("", text).strip()

    # Handle unclosed <think> tag if output was truncated
    unclosed_pattern = re.compile(r"<think>(.*)$", flags=re.DOTALL | re.IGNORECASE)
    unclosed_match = unclosed_pattern.search(cleaned_text)
    if unclosed_match:
        unclosed_thought = unclosed_match.group(1).strip()
        if unclosed_thought:
            thoughts.append(unclosed_thought)
        cleaned_text = unclosed_pattern.sub("", cleaned_text).strip()

    combined_thoughts = " | ".join(thoughts) if thoughts else None
    return cleaned_text, combined_thoughts


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.
    Uses openai/gpt-oss-120b for fast intent classification at the gate.
    """
    global _rails

    guard_llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="openai/gpt-oss-120b",
        temperature=0,  
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT
    )

    _rails = LLMRails(config, llm=guard_llm)
    logfire.info("🛡️ NeMo Guardrails initialised (openai/gpt-oss-120b).")


def guard(message: str) -> tuple[bool, str | None, str | None]:
    """
    Run a user message through the NeMo rails gate.

    Returns:
        (True,  clean_response, thought) — a rail fired; return this response immediately,
                                           skip the RAG pipeline entirely.
        (False, None, None)              — message is clean; proceed to LangGraph.
    """
    if _rails is None:
        logfire.warning("⚠️ Guardrails not initialised — skipping gate.")
        return False, None, None

    with logfire.span("🛡️ Guardrails Check"):
        result = _rails.generate(messages=[{"role": "user", "content": message}])

        # NeMo returns {'role': 'assistant', 'content': '...'} — extract text
        raw_content = result.get("content", "") if isinstance(result, dict) else str(result)
        content, thought = extract_thinking(raw_content)

        fired = any(indicator in raw_content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info(f"🛡️ Guardrails fired | query='{message[:80]}'")
            return True, content, thought

        logfire.info("✅ Guardrails passed.")
        return False, None, None