from typing import Any, Optional
import logfire
from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.config import settings


class _PortkeyCompatibleClient:
    """
    Wrapper around Portkey / OpenAI clients.
    If Portkey is configured, delegates directly to the Portkey client.
    Otherwise, proxies to Evren LLM (OpenAI-compatible) and translates Portkey-style slugs.
    """

    def __init__(self):
        if settings.PORTKEY_API_KEY:
            try:
                from portkey_ai import Portkey

                self._client = Portkey(api_key=settings.PORTKEY_API_KEY)
                self._is_portkey = True
                logfire.info("🌐 Initialized Portkey Gateway client.")
            except Exception as e:
                logfire.warning(f"Failed to initialize Portkey: {e}. Falling back to Evren.")
                self._client = OpenAI(
                    base_url=settings.EVREN_BASE_URL,
                    api_key=settings.EVREN_API_KEY,
                )
                self._is_portkey = False
        else:
            self._client = OpenAI(
                base_url=settings.EVREN_BASE_URL,
                api_key=settings.EVREN_API_KEY,
            )
            self._is_portkey = False
            logfire.info(f"Initialized Evren LLM client ({settings.EVREN_MODEL}).")

    @property
    def chat(self):
        return self._ChatProxy(self)

    class _ChatProxy:
        def __init__(self, parent: "_PortkeyCompatibleClient"):
            self.parent = parent
            self.completions = self._CompletionsProxy(parent)

        class _CompletionsProxy:
            def __init__(self, parent: "_PortkeyCompatibleClient"):
                self.parent = parent

            def create(self, *args, **kwargs):
                if not self.parent._is_portkey:
                    # Translate Portkey model alias to Evren model
                    model = kwargs.get("model", "")
                    if model.startswith("@") or "gpt-" in model:
                        kwargs["model"] = settings.EVREN_MODEL
                return self.parent._client.chat.completions.create(*args, **kwargs)


portkey_client = _PortkeyCompatibleClient()


def extract_cache_status(response: Any) -> Optional[str]:
    """Extract cache status header from LLM response if available."""
    headers = getattr(response, "_headers", {}) or {}
    if hasattr(headers, "get"):
        return headers.get("x-portkey-cache-status")
    return None


def get_langchain_llm(feature: str = "default") -> ChatOpenAI:
    """
    Returns a LangChain-compatible LLM for agent nodes.
    Defaults to Evren LLM or Portkey if configured.
    """
    if settings.PORTKEY_API_KEY:
        return ChatOpenAI(
            base_url="https://api.portkey.ai/v1",
            api_key=settings.PORTKEY_API_KEY,
            model=settings.EVREN_MODEL,
        )
    return ChatOpenAI(
        base_url=settings.EVREN_BASE_URL,
        api_key=settings.EVREN_API_KEY,
        model=settings.EVREN_MODEL,
        temperature=0.0,
    )
