from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "enterprise-agentic-rag"}


@router.get("/healthz")
def healthz():
    """Liveness probe endpoint."""
    return {"status": "healthy"}


@router.get("/readyz")
def readyz():
    """Readiness probe endpoint."""
    return {"status": "ready"}
