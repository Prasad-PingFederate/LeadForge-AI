import time
import logging
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

class TTLCache:
    """In-memory thread-safe TTL cache for LLM and Web Search responses."""

    def __init__(self, default_ttl_seconds: int = 86400):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        expires_at, value = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        self._cache.clear()

global_cache = TTLCache()
cache = global_cache
