import time
from dataclasses import dataclass
from typing import Dict, Optional

import logfire
from qdrant_client import QdrantClient

from app.config import settings


@dataclass
class ConnectionStatus:
    healthy: bool
    message: Optional[str] = None
    latency_ms: Optional[float] = None


def check_qdrant() -> ConnectionStatus:
    """Check connectivity to Qdrant Vector DB."""
    start = time.perf_counter()
    try:
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=5)
        client.get_collections()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionStatus(healthy=True, message="Connected", latency_ms=latency)
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return ConnectionStatus(healthy=False, message=str(e), latency_ms=latency)


def check_redis() -> ConnectionStatus:
    """Check Redis connectivity if configured."""
    if not settings.UPSTASH_REDIS_REST_URL:
        return ConnectionStatus(healthy=True, message="Not configured (in-memory mode)")

    start = time.perf_counter()
    try:
        from limits.storage import RedisStorage

        storage = RedisStorage(settings.redis_url)
        if storage.check() and storage.storage.ping():
            latency = (time.perf_counter() - start) * 1000
            return ConnectionStatus(healthy=True, message="Connected", latency_ms=latency)
        return ConnectionStatus(healthy=False, message="Ping failed")
    except Exception as e:
        return ConnectionStatus(healthy=False, message=str(e))


def check_postgres() -> ConnectionStatus:
    """Check Postgres connectivity if configured."""
    if not settings.NEON_DB_URL:
        return ConnectionStatus(healthy=True, message="Not configured (MemorySaver fallback)")

    start = time.perf_counter()
    try:
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(conninfo=settings.postgres_uri, min_size=1, max_size=1, timeout=5)
        with pool.connection() as conn:
            conn.execute("SELECT 1")
        latency = (time.perf_counter() - start) * 1000
        return ConnectionStatus(healthy=True, message="Connected", latency_ms=latency)
    except Exception as e:
        return ConnectionStatus(healthy=False, message=str(e))


def check_all_connections() -> Dict[str, ConnectionStatus]:
    """Verify connectivity to all external dependencies."""
    return {
        "Qdrant": check_qdrant(),
        "Redis": check_redis(),
        "Postgres": check_postgres(),
    }


def log_connection_summary(results: Dict[str, ConnectionStatus]) -> bool:
    """
    Logs status for each dependency and returns whether all are healthy.
    """
    all_healthy = True
    for name, status in results.items():
        if status.healthy:
            latency_str = f" ({status.latency_ms:.1f}ms)" if status.latency_ms else ""
            logfire.info(f"✅ {name}: healthy - {status.message}{latency_str}")
        else:
            all_healthy = False
            logfire.warning(f"❌ {name}: unhealthy - {status.message}")

    return all_healthy
