import contextvars
from typing import Optional

_request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current async context."""
    _request_id_ctx_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id_ctx_var.get()
