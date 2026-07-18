import time
from collections import defaultdict
from typing import Dict, Tuple

_store: Dict[str, Tuple[int, float]] = {}
_CLEANUP_INTERVAL = 60.0
_LAST_CLEANUP = time.monotonic()


def _cleanup(now: float, window_sec: float):
    global _LAST_CLEANUP
    if now - _LAST_CLEANUP < _CLEANUP_INTERVAL:
        return
    _LAST_CLEANUP = now
    to_del = [k for k, (_, t) in _store.items() if now - t > window_sec]
    for k in to_del:
        del _store[k]


def is_rate_limited(key: str, max_requests: int, window_sec: float = 60.0) -> bool:
    now = time.monotonic()
    _cleanup(now, window_sec)
    count, start = _store.get(key, (0, now))
    if now - start > window_sec:
        _store[key] = (1, now)
        return False
    if count >= max_requests:
        return True
    _store[key] = (count + 1, start)
    return False
