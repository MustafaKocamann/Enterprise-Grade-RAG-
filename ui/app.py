import html
import os
import re
import sys
import time
import uuid
from datetime import datetime
from typing import Any

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import logfire
import requests
import streamlit as st
from dotenv import load_dotenv


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))

st.set_page_config(
    page_title="Enterprise RAG Workspace",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="auto",
)


def configure_observability() -> str:
    token = os.getenv("LOGFIRE_TOKEN")
    base_url = os.getenv("LOGFIRE_BASE_URL")
    send_to_logfire = os.getenv("LOGFIRE_SEND_TO_LOGFIRE", "true").strip().lower()
    if not token or send_to_logfire in {"0", "false", "no", "off"}:
        logfire.configure(
            service_name="enterprise-rag-ui",
            send_to_logfire=False,
            inspect_arguments=False,
        )
        return "Standby"

    if not base_url and "_eu_" in token:
        base_url = "https://logfire-eu.pydantic.dev"

    try:
        logfire.configure(
            token=token,
            service_name="enterprise-rag-ui",
            send_to_logfire="if-token-present",
            inspect_arguments=False,
            advanced=logfire.AdvancedOptions(base_url=base_url) if base_url else None,
        )
        logfire.instrument_requests()
        return "Active"
    except Exception as exc:
        print(f"Logfire UI initialization failed: {exc}")
        return "Standby"


LOGFIRE_STATUS = configure_observability()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
AI_AVATAR = ":material/auto_awesome:"
USER_AVATAR = ":material/person:"


DESIGN_SYSTEM = """
<style>
    :root {
        --navy-950: #07111f;
        --navy-900: #0b172a;
        --navy-800: #14243b;
        --blue-700: #1d4ed8;
        --blue-600: #2563eb;
        --blue-100: #dbeafe;
        --cyan-400: #22d3ee;
        --slate-900: #0f172a;
        --slate-700: #334155;
        --slate-500: #64748b;
        --slate-300: #cbd5e1;
        --slate-200: #e2e8f0;
        --slate-100: #f1f5f9;
        --surface: #ffffff;
        --success: #16a34a;
        --danger: #dc2626;
        --radius-lg: 20px;
        --radius-md: 14px;
        --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
        --shadow-md: 0 14px 34px rgba(15, 23, 42, 0.08);
    }

    html, body, [class*="css"] {
        font-family: Inter, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 92% 4%, rgba(37, 99, 235, 0.09), transparent 24rem),
            #f6f8fc;
        color: var(--slate-900);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 0%, rgba(34, 211, 238, 0.10), transparent 18rem),
            linear-gradient(180deg, var(--navy-950) 0%, var(--navy-900) 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.14);
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 1.4rem 1.1rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #b8c5d8;
    }

    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 1.8rem;
    }

    .brand-mark {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 13px;
        color: white;
        font-size: 1.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--blue-600), var(--cyan-400));
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
    }

    .brand-name {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 750;
        letter-spacing: -0.01em;
    }

    .brand-subtitle {
        color: #8fa2ba;
        font-size: 0.72rem;
        margin-top: 0.1rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .sidebar-label {
        color: #71859e;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.1em;
        margin: 1.3rem 0 0.65rem;
        text-transform: uppercase;
    }

    .sidebar-card {
        background: rgba(255, 255, 255, 0.055);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 14px;
        padding: 0.85rem 0.9rem;
        margin-bottom: 0.65rem;
    }

    .sidebar-card-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .sidebar-card-key {
        color: #93a4bb;
        font-size: 0.76rem;
    }

    .sidebar-card-value {
        color: #eef5ff;
        font-size: 0.78rem;
        font-weight: 650;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        margin-right: 0.38rem;
        background: var(--success);
        box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.14);
    }

    .status-dot.offline {
        background: var(--danger);
        box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.14);
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 2.75rem;
        color: #e8f0fb;
        background: rgba(255, 255, 255, 0.065);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        font-weight: 650;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        color: white;
        background: rgba(37, 99, 235, 0.3);
        border-color: rgba(96, 165, 250, 0.65);
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        padding: clamp(1.5rem, 3vw, 2.6rem);
        margin-bottom: 1.35rem;
        color: white;
        background:
            radial-gradient(circle at 88% 14%, rgba(34, 211, 238, 0.20), transparent 18rem),
            linear-gradient(125deg, #091628 0%, #102b50 58%, #164e78 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
    }

    .hero-shell::after {
        content: "";
        position: absolute;
        top: -70px;
        right: -55px;
        width: 230px;
        height: 230px;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 999px;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #bdeeff;
        font-size: 0.7rem;
        font-weight: 750;
        letter-spacing: 0.11em;
        text-transform: uppercase;
    }

    .eyebrow-line {
        width: 24px;
        height: 2px;
        background: var(--cyan-400);
        border-radius: 999px;
    }

    .hero-title {
        max-width: 760px;
        margin: 0.8rem 0 0.7rem;
        color: #ffffff;
        font-size: clamp(1.75rem, 4vw, 3rem);
        line-height: 1.08;
        letter-spacing: -0.045em;
    }

    .hero-description {
        max-width: 720px;
        margin: 0;
        color: #c5d4e8;
        font-size: clamp(0.92rem, 1.6vw, 1.05rem);
        line-height: 1.65;
    }

    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1.35rem;
    }

    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        padding: 0.5rem 0.72rem;
        color: #dce9f8;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.075);
        border: 1px solid rgba(255, 255, 255, 0.11);
        border-radius: 999px;
        backdrop-filter: blur(8px);
    }

    .section-heading {
        margin: 1.4rem 0 0.8rem;
    }

    .section-kicker {
        color: var(--blue-700);
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .section-title {
        margin: 0.25rem 0 0;
        color: var(--slate-900);
        font-size: 1.2rem;
        font-weight: 750;
        letter-spacing: -0.025em;
    }

    .empty-state {
        padding: 1.35rem 1.4rem 1rem;
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid var(--slate-200);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
    }

    .empty-title {
        color: var(--slate-900);
        font-size: 1.05rem;
        font-weight: 750;
    }

    .empty-copy {
        margin: 0.35rem 0 0.9rem;
        color: var(--slate-500);
        font-size: 0.88rem;
        line-height: 1.55;
    }

    [data-testid="stMainBlockContainer"] .stButton > button {
        min-height: 3.35rem;
        padding: 0.72rem 0.9rem;
        color: var(--slate-700) !important;
        background: var(--surface) !important;
        border: 1px solid var(--slate-200) !important;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        font-size: 0.83rem;
        font-weight: 650;
        text-align: left;
        transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease;
    }

    [data-testid="stMainBlockContainer"] .stButton > button:hover {
        color: var(--blue-700) !important;
        border-color: #93c5fd !important;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.10);
        transform: translateY(-1px);
    }

    [data-testid="stChatMessage"] {
        margin-bottom: 0.85rem;
        padding: 1rem 1.05rem;
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid var(--slate-200);
        border-radius: 16px;
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        color: var(--slate-900) !important;
    }

    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
        border-radius: 11px;
    }

    .message-label {
        margin-bottom: 0.36rem;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .message-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.42rem;
        margin-top: 0.8rem;
    }

    .message-pill {
        padding: 0.3rem 0.52rem;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 650;
        background: var(--slate-100);
        border: 1px solid var(--slate-200);
        border-radius: 999px;
    }

    [data-testid="stExpander"] {
        margin-top: 0.65rem;
        background: #fbfdff;
        border: 1px solid var(--slate-200);
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p {
        color: var(--slate-700) !important;
        background: #f8fafc !important;
    }

    [data-testid="stExpanderDetails"],
    [data-testid="stExpanderDetails"] p,
    [data-testid="stExpanderDetails"] li,
    [data-testid="stExpanderDetails"] strong {
        color: var(--slate-900) !important;
    }

    .source-item {
        padding: 0.8rem 0;
        border-bottom: 1px solid var(--slate-200);
    }

    .source-item:last-child {
        border-bottom: 0;
    }

    .source-title {
        color: var(--slate-700);
        font-size: 0.76rem;
        font-weight: 750;
    }

    .source-copy {
        margin-top: 0.35rem;
        color: var(--slate-500);
        font-size: 0.78rem;
        line-height: 1.55;
        white-space: pre-wrap;
    }

    [data-testid="stChatInput"] {
        border: 1px solid var(--slate-300);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.97) !important;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.13);
    }

    [data-testid="stChatInput"] textarea {
        color: var(--slate-900) !important;
        background: transparent !important;
        caret-color: var(--blue-600);
        -webkit-text-fill-color: var(--slate-900) !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--slate-500) !important;
        -webkit-text-fill-color: var(--slate-500) !important;
        opacity: 1;
    }

    [data-testid="stChatInput"] button {
        color: #ffffff !important;
        background: var(--blue-600) !important;
        border-radius: 10px !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--blue-600);
        box-shadow: 0 16px 42px rgba(37, 99, 235, 0.17);
    }

    .privacy-note {
        margin-top: 1.1rem;
        color: #7588a1;
        font-size: 0.7rem;
        line-height: 1.55;
    }

    .app-footer {
        padding: 1.5rem 0 0.25rem;
        color: var(--slate-500);
        font-size: 0.72rem;
        text-align: center;
    }

    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem 0.85rem 6.5rem;
        }

        .hero-shell {
            padding: 1.35rem 1.15rem;
            border-radius: 16px;
        }

        .hero-title {
            font-size: 1.8rem;
        }

        .hero-description {
            font-size: 0.9rem;
        }

        .hero-meta {
            gap: 0.4rem;
        }

        .hero-chip {
            font-size: 0.68rem;
        }

        [data-testid="stChatMessage"] {
            padding: 0.85rem;
            border-radius: 14px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            scroll-behavior: auto !important;
            transition: none !important;
        }
    }
</style>
"""

st.markdown(DESIGN_SYSTEM, unsafe_allow_html=True)


def initialize_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logfire.info("New UI session created", session_id=st.session_state.session_id)
    if "messages" not in st.session_state:
        st.session_state.messages = []


@st.cache_data(ttl=20, show_spinner=False)
def get_backend_health(base_url: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{base_url}/health", timeout=2.5)
        response.raise_for_status()
        payload = response.json()
        is_healthy = payload.get("status") == "healthy"
        return is_healthy, "Online" if is_healthy else "Needs attention"
    except (requests.RequestException, ValueError):
        return False, "Offline"


def strip_reasoning_tags(value: Any) -> str:
    content = "" if value is None else str(value)
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<think>.*$", "", content, flags=re.DOTALL | re.IGNORECASE)
    return content.strip() or "No answer was generated."


def request_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("RAG_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def parse_error_response(response: requests.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail") or payload.get("message") or payload.get("error")
        if detail:
            return str(detail)
    except ValueError:
        pass
    return f"The server returned status code {response.status_code}."


def fetch_query_result(prompt: str) -> dict[str, Any]:
    headers = request_headers()
    response = requests.post(
        f"{BACKEND_URL}/query",
        json={"q": prompt, "thread_id": st.session_state.session_id},
        headers=headers,
        timeout=180,
    )
    if not response.ok:
        raise RuntimeError(parse_error_response(response))

    data = response.json()
    if "answer" in data:
        return data

    job_id = data.get("job_id")
    if not job_id:
        raise RuntimeError("The API returned an unexpected response.")

    poll_url = f"{BACKEND_URL}/query/status/{job_id}"
    for _ in range(60):
        poll_response = requests.get(poll_url, headers=headers, timeout=30)
        if not poll_response.ok:
            raise RuntimeError(parse_error_response(poll_response))
        poll_data = poll_response.json()
        if poll_data.get("status") == "SUCCESS":
            result = poll_data.get("result")
            if isinstance(result, dict):
                return result
            raise RuntimeError("The job completed without a valid result.")
        if poll_data.get("status") == "FAILURE":
            raise RuntimeError(str(poll_data.get("error") or "The RAG job failed."))
        time.sleep(2)

    raise RuntimeError("The RAG job timed out.")


def source_parts(source: Any, index: int) -> tuple[str, str]:
    if isinstance(source, dict):
        metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
        title = (
            metadata.get("title")
            or metadata.get("source")
            or metadata.get("file_name")
            or source.get("title")
            or source.get("source")
            or f"Source {index}"
        )
        content = source.get("page_content") or source.get("content") or source.get("text") or source
    else:
        title = f"Source {index}"
        content = source
    return str(title), str(content)


def render_sources(sources: list[Any]) -> None:
    if not sources:
        return
    with st.expander(f"View sources · {len(sources)} items"):
        for index, source in enumerate(sources, start=1):
            title, content = source_parts(source, index)
            st.markdown(
                f"""
                <div class="source-item">
                    <div class="source-title">{html.escape(title)}</div>
                    <div class="source-copy">{html.escape(content)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_thought_process(steps: list[Any]) -> None:
    clean_steps = [str(step).strip() for step in steps if str(step).strip()]
    if not clean_steps:
        return
    with st.expander(f"Processing steps · {len(clean_steps)} stages"):
        for index, step in enumerate(clean_steps, start=1):
            st.markdown(f"**{index:02d}.** {step}")


def render_message(message: dict[str, Any]) -> None:
    role = message.get("role", "assistant")
    avatar = USER_AVATAR if role == "user" else AI_AVATAR
    label = "You" if role == "user" else "Enterprise AI"
    with st.chat_message(role, avatar=avatar):
        st.markdown(f'<div class="message-label">{label}</div>', unsafe_allow_html=True)
        st.markdown(strip_reasoning_tags(message.get("content")))

        if role == "assistant":
            latency = message.get("latency")
            status_text = message.get("status")
            meta_items = []
            if latency is not None:
                meta_items.append(f"{float(latency):.1f} sn")
            if status_text:
                meta_items.append(str(status_text))
            if meta_items:
                pills = "".join(
                    f'<span class="message-pill">{html.escape(item)}</span>' for item in meta_items
                )
                st.markdown(f'<div class="message-meta">{pills}</div>', unsafe_allow_html=True)
            render_thought_process(message.get("thought_process") or [])
            render_sources(message.get("sources") or [])


def reset_conversation() -> None:
    previous_session = st.session_state.session_id
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    get_backend_health.clear()
    logfire.info(
        "UI conversation reset",
        previous_session_id=previous_session,
        session_id=st.session_state.session_id,
    )


initialize_session()
backend_online, backend_status = get_backend_health(BACKEND_URL)
status_class = "" if backend_online else " offline"
safe_backend_status = html.escape(backend_status)
safe_session_id = html.escape(st.session_state.session_id[:8].upper())

with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-mark">R</div>
            <div>
                <div class="brand-name">Enterprise RAG</div>
                <div class="brand-subtitle">Knowledge Workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-label">System Status</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-row">
                <span class="sidebar-card-key">RAG API</span>
                <span class="sidebar-card-value"><span class="status-dot{status_class}"></span>{safe_backend_status}</span>
            </div>
        </div>
        <div class="sidebar-card">
            <div class="sidebar-card-row">
                <span class="sidebar-card-key">Observability</span>
                <span class="sidebar-card-value">{html.escape(LOGFIRE_STATUS)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-label">Active Session</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-row">
                <span class="sidebar-card-key">Session ID</span>
                <span class="sidebar-card-value">{safe_session_id}</span>
            </div>
            <div class="sidebar-card-row" style="margin-top: .65rem;">
                <span class="sidebar-card-key">Messages</span>
                <span class="sidebar-card-value">{len(st.session_state.messages)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Start a new conversation", width="stretch"):
        reset_conversation()
        st.rerun()

    st.markdown(
        """
        <div class="privacy-note">
            Responses are grounded in your enterprise knowledge base. Verify the cited sources before making critical decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


message_count = len(st.session_state.messages)
st.markdown(
    f"""
    <section class="hero-shell">
        <div class="eyebrow"><span class="eyebrow-line"></span>Enterprise Knowledge Assistant</div>
        <h1 class="hero-title">Find knowledge.<br>Turn it into decisions.</h1>
        <p class="hero-description">
            Get reliable answers from your documents, review supporting sources, and manage complex research workflows in one workspace.
        </p>
        <div class="hero-meta">
            <span class="hero-chip"><span class="status-dot{status_class}"></span>API {safe_backend_status}</span>
            <span class="hero-chip">Source-grounded answers</span>
            <span class="hero-chip">Enterprise security layer</span>
            <span class="hero-chip">{message_count} messages</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-heading">
        <div class="section-kicker">Intelligent Workspace</div>
        <div class="section-title">Ask your assistant</div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_prompt = None
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-title">Choose where to begin</div>
            <div class="empty-copy">Use a suggested prompt or enter your own question below.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    suggestion_columns = st.columns(2)
    suggestions = [
        "Summarize the documents as an executive brief",
        "Compare similarities and differences across sources",
        "List identified risks and recommended actions",
        "Show evidence for a topic with supporting sources",
    ]
    for index, suggestion in enumerate(suggestions):
        with suggestion_columns[index % 2]:
            if st.button(suggestion, key=f"suggestion_{index}", width="stretch"):
                selected_prompt = suggestion

for stored_message in st.session_state.messages:
    render_message(stored_message)

typed_prompt = st.chat_input("Ask a question about your enterprise documents…")
active_prompt = typed_prompt or selected_prompt

if active_prompt:
    user_message = {
        "role": "user",
        "content": active_prompt,
        "created_at": datetime.now().isoformat(),
    }
    st.session_state.messages.append(user_message)
    render_message(user_message)

    with st.chat_message("assistant", avatar=AI_AVATAR):
        st.markdown('<div class="message-label">Enterprise AI</div>', unsafe_allow_html=True)
        started_at = time.perf_counter()
        result = None
        request_error = None

        with st.status("Analyzing the knowledge base…", expanded=True) as request_status:
            try:
                with logfire.span(
                    "UI chat interaction",
                    user_query=active_prompt,
                    session_id=st.session_state.session_id,
                ):
                    result = fetch_query_result(active_prompt)
                result_status = str(result.get("status") or "Completed")
                is_blocked = result_status == "Blocked by guardrails."
                request_status.update(
                    label="Security policy applied" if is_blocked else "Answer ready",
                    state="complete",
                    expanded=False,
                )
            except Exception as exc:
                request_error = exc
                request_status.update(label="Connection failed", state="error", expanded=False)
                logfire.error(
                    "UI backend request failed",
                    error=str(exc),
                    session_id=st.session_state.session_id,
                )

        latency = time.perf_counter() - started_at
        if result is not None:
            answer = strip_reasoning_tags(result.get("answer"))
            steps = result.get("thought_process") or []
            sources = result.get("sources") or []
            result_status = str(result.get("status") or "Completed")
            is_blocked = result_status == "Blocked by guardrails."
            display_status = "Security filter" if is_blocked else result_status
            assistant_message = {
                "role": "assistant",
                "content": answer,
                "thought_process": steps,
                "sources": sources,
                "status": display_status,
                "latency": latency,
                "created_at": datetime.now().isoformat(),
            }
            st.markdown(answer)
            st.markdown(
                f"""
                <div class="message-meta">
                    <span class="message-pill">{latency:.1f} sec</span>
                    <span class="message-pill">{html.escape(display_status)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_thought_process(steps)
            render_sources(sources)
            st.session_state.messages.append(assistant_message)
            logfire.info("UI chat cycle completed", session_id=st.session_state.session_id)
        else:
            error_answer = (
                "The knowledge service is currently unavailable. Confirm that the API is running and try again."
            )
            st.error(error_answer)
            with st.expander("Technical details"):
                st.code(str(request_error))
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_answer,
                    "status": "Connection error",
                    "latency": latency,
                    "created_at": datetime.now().isoformat(),
                }
            )

st.markdown(
    """
    <div class="app-footer">Enterprise RAG Workspace · Source-grounded AI experience</div>
    """,
    unsafe_allow_html=True,
)
