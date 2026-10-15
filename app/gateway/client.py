import logfire
from langchain_openai import ChatOpenAI
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL

from app.config import settings

# If a saved config ID (pc-...) is configured, use it. Otherwise, rely on virtual key routing.
PORTKEY_CONFIG = settings.PORTKEY_PRIMARY_CONFIG_ID or None

portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY,
    config=PORTKEY_CONFIG,
)


def get_langchain_llm(feature: str = "rag", user: str = "rag-system") -> ChatOpenAI:
    """
    Returns a Portkey-backed ChatOpenAI — a drop-in for ChatGroq in LangChain nodes.
    Routes through Portkey Gateway with virtual key slug and user tracking.
    """
    header_kwargs = {
        "api_key": settings.PORTKEY_API_KEY,
        "metadata": {
            "feature": feature,
            "_user": user,
            "environment": "production",
        },
    }
    if PORTKEY_CONFIG:
        header_kwargs["config"] = PORTKEY_CONFIG

    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=f"@{settings.GROQ_SLUG}/openai/gpt-oss-120b",
        temperature=0,
        default_headers=createHeaders(**header_kwargs),
    )


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey native client response headers.
    Tries multiple attribute paths defensively — returns 'MISS' if not found.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"