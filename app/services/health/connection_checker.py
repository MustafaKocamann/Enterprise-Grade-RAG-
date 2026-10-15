import time
from dataclasses import dataclass
from typing import Dict, Optional

import logfire
from qdrant_client import QdrantClient
import requests

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


def check_neon_auth() -> ConnectionStatus:
    """Check that Neon Auth's public JWKS endpoint is reachable."""
    if not settings.NEON_AUTH_JWKS_URL:
        return ConnectionStatus(healthy=True, message="Not configured")

    start = time.perf_counter()
    try:
        response = requests.get(settings.NEON_AUTH_JWKS_URL, timeout=5)
        response.raise_for_status()
        response.json()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionStatus(healthy=True, message="JWKS reachable", latency_ms=latency)
    except Exception as e:
        return ConnectionStatus(healthy=False, message=str(e))


def check_neon_object_storage() -> ConnectionStatus:
    """Check Neon S3-compatible Object Storage using deployed credentials."""
    if not settings.NEON_S3_ENDPOINT_URL:
        return ConnectionStatus(healthy=True, message="Not configured")

    start = time.perf_counter()
    try:
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=settings.NEON_S3_ENDPOINT_URL,
            region_name=settings.NEON_S3_REGION,
            aws_access_key_id=settings.NEON_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.NEON_S3_SECRET_ACCESS_KEY,
        )
        client.list_buckets()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionStatus(healthy=True, message="Connected", latency_ms=latency)
    except Exception as e:
        return ConnectionStatus(healthy=False, message=str(e))


def check_neon_function() -> ConnectionStatus:
    """Check the deployed Neon hello function endpoint."""
    if not settings.NEON_FUNCTION_HELLO_BASE_URL:
        return ConnectionStatus(healthy=True, message="Not configured")

    start = time.perf_counter()
    try:
        response = requests.get(settings.NEON_FUNCTION_HELLO_BASE_URL, timeout=5)
        response.raise_for_status()
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
        "Neon Auth": check_neon_auth(),
        "Neon Object Storage": check_neon_object_storage(),
        "Neon Function": check_neon_function(),
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


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("\n🔍 Servis baglantilari kontrol ediliyor...\n")
    results = check_all_connections()
    all_healthy = log_connection_summary(results)

    print("\n" + "=" * 55)
    for name, status in results.items():
        symbol = "[OK]" if status.healthy else "[FAIL]"
        latency = f" ({status.latency_ms:.1f}ms)" if status.latency_ms else ""
        print(f"{symbol:6} {name:22}: {status.message}{latency}")
    print("=" * 55)

    if all_healthy:
        print(">> Tum servisler saglikli!\n")
    else:
        print(">> Bazi servislerde baglanti sorunu var!\n")
