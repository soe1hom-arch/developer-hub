"""
Caching system for Developer Hub.

Provides:
- In-memory cache with TTL
- File-based cache persistence
- Cache invalidation on data changes
"""

import json
import os
import time
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".cache"


class Cache:
    """Simple TTL-based cache with file persistence."""

    def __init__(self, ttl_seconds=300, namespace="default"):
        self.ttl = ttl_seconds
        self.namespace = namespace
        self._memory = {}
        CACHE_DIR.mkdir(exist_ok=True)
        self._load()

    def _cache_path(self):
        return CACHE_DIR / f"{self.namespace}.json"

    def _load(self):
        path = self._cache_path()
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                    # Only load entries that haven't expired
                    now = time.time()
                    for key, entry in data.items():
                        if entry.get("expires", 0) > now:
                            self._memory[key] = entry
            except:
                pass

    def _save(self):
        path = self._cache_path()
        try:
            # Only persist what fits in reasonable size
            if len(self._memory) > 1000:
                return
            with open(path, "w") as f:
                json.dump(self._memory, f)
        except:
            pass

    def get(self, key):
        entry = self._memory.get(key)
        if entry and entry.get("expires", 0) > time.time():
            return entry["value"]
        if entry:
            del self._memory[key]
        return None

    def set(self, key, value, ttl=None):
        self._memory[key] = {
            "value": value,
            "expires": time.time() + (ttl or self.ttl),
            "created": time.time(),
        }
        self._save()

    def invalidate(self, key=None):
        if key:
            self._memory.pop(key, None)
        else:
            self._memory.clear()
        self._save()

    def invalidate_by_prefix(self, prefix):
        keys = [k for k in self._memory if k.startswith(prefix)]
        for k in keys:
            del self._memory[k]
        self._save()

    def stats(self):
        return {
            "entries": len(self._memory),
            "ttl": self.ttl,
            "namespace": self.namespace,
        }


# Global cache instances
search_cache = Cache(ttl_seconds=60, namespace="search")
api_cache = Cache(ttl_seconds=30, namespace="api")
data_cache = Cache(ttl_seconds=300, namespace="data")
