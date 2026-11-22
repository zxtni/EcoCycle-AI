from threading import Lock
from time import monotonic

from fastapi import Request

buckets: dict[tuple[str, str], tuple[int, int]] = {}
lock = Lock()


def limited(request: Request) -> bool:
    if request.method != "POST":
        return False
    path = request.url.path
    if path.startswith("/api/auth/"):
        group, limit = "identity", 20
    elif path == "/api/scans":
        group, limit = "scan", 18
    elif path == "/api/admin/forecast/refresh":
        group, limit = "train", 3
    else:
        return False
    window = int(monotonic() // 60)
    host = request.client.host if request.client else "unknown"
    key = (host, group)
    with lock:
        if len(buckets) >= 1024:
            for expired in [item for item, (stamp, _) in buckets.items() if stamp != window]:
                del buckets[expired]
        if key not in buckets and len(buckets) >= 8192:
            return True
        stamp, count = buckets.get(key, (window, 0))
        count = count + 1 if stamp == window else 1
        buckets[key] = (window, count)
    return count > limit
