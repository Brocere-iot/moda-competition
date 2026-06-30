import time
from collections import deque
from fastapi import HTTPException

RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SEC = 60
_rate_limit_store: dict[str, deque] = {}


def check_rate_limit(key: str):
    now = time.time()
    if key not in _rate_limit_store:
        _rate_limit_store[key] = deque()
    window = _rate_limit_store[key]
    while window and now - window[0] > RATE_LIMIT_WINDOW_SEC:
        window.popleft()
    if not window:
        del _rate_limit_store[key]
    if len(window) >= RATE_LIMIT_MAX_CALLS:
        oldest = window[0]
        retry_after = int(RATE_LIMIT_WINDOW_SEC - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail=f"請求過於頻繁，請於 {retry_after} 秒後再試（每 {RATE_LIMIT_WINDOW_SEC} 秒限 {RATE_LIMIT_MAX_CALLS} 次）"
        )
    if key not in _rate_limit_store:
        _rate_limit_store[key] = deque()
    _rate_limit_store[key].append(now)
