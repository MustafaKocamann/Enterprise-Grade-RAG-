import logfire
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from app.agents.state import AgentState
from app.config import settings
from app.gateway import extract_cache_status, portkey_client


def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.
    Uses the native Portkey client (not LangChain) so we can read the
    x-portkey-cache-status response header and surface Cache: Hit in the UI.
    """
    query = state["current_query"]

    history_str = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    user_msg = state["messages"][-1]["content"] if state["messages"] else ""

    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory.")
        prompt = f"""
        You are a friendly and helpful Enterprise AI Assistant.
        Answer the user's latest message using the CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history_str}

        LATEST MESSAGE:
        "{user_msg}"
        """
    else:
        logfire.info("Generating technical RAG response.")
        max_context_chars = 25000
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are a Senior Technical Architect.
        Answer the question using the TECHNICAL CONTEXT provided.

        TECHNICAL CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history_str}

        USER QUESTION:
        "{user_msg}"
        """

    with logfire.span("✍️ LLM Synthesis"):
        try:
            user_id = state.get("thread_id", "default-user")
            response = _generate_response(prompt, user=user_id)
            content = response.choices[0].message.content
            cache_status = extract_cache_status(response)
            is_cache_hit = cache_status == "HIT"

            cleaned_content = content
            thought = None
            if "<think>" in content:
                import re
                think_match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL | re.IGNORECASE)
                if think_match:
                    thought = think_match.group(1).strip()
                cleaned_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
                cleaned_content = re.sub(r"<think>.*$", "", cleaned_content, flags=re.DOTALL | re.IGNORECASE).strip()

            plan_update = list(state["plan"])
            if thought:
                plan_update.append(f"Thought: {thought}")

            if is_cache_hit:
                logfire.info("⚡ Gateway Cache Hit — response served from Portkey cache.")
                plan_update.append("Cache: Hit ⚡")
                status = "Cache hit — instant response."
            else:
                logfire.info("✅ Response synthesised via LLM.")
                status = "Response generated."

            return {
                "final_answer": cleaned_content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": cleaned_content}],
            }

        except Exception as e:
            logfire.error(f"LLM Generation failed after retries: {e}")
            raise e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
    before_sleep=before_sleep_log(logfire, "warning"),
)
def _generate_response(prompt: str, user: str = "default-user"):
    """Call the LLM gateway with retry logic for transient failures."""
    from portkey_ai import createHeaders
    from app.gateway.client import PORTKEY_CONFIG

    headers = createHeaders(
        metadata={
            "feature": "responder",
            "_user": user,
            "environment": "production",
        }
    )
    if PORTKEY_CONFIG:
        headers["x-portkey-config"] = PORTKEY_CONFIG

    return portkey_client.chat.completions.create(
        model=f"@{settings.GROQ_SLUG}/openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        user=user,
        extra_headers=headers,
    )