import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.admin import router as admin
from backend.auth import router as auth
from backend.db import engine
from backend.impact import router as impact
from backend.locator import router as locator
from backend.municipality import router as municipality
from backend.rate_limit import limited
from backend.scans import router as scans

app = FastAPI(title="EcoCycle AI", version="1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
origin = os.getenv("WEB_ORIGIN", "http://localhost:3000").rstrip("/")
allowed = {origin}
if os.getenv("APP_ENV") != "production":
    allowed.add("http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def origin_check(request: Request, call_next):
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and request.headers.get("origin")
        and request.headers["origin"] not in allowed
    ):
        return JSONResponse({"detail": "Untrusted request origin."}, status_code=403)
    if limited(request):
        return JSONResponse(
            {"detail": "Too many requests. Try again in a minute."},
            status_code=429,
            headers={"Retry-After": "60"},
        )
    if request.url.path == "/api/scans":
        length = request.headers.get("content-length", "")
        if length.isdecimal() and int(length) > 8 * 1024 * 1024 + 65536:
            return JSONResponse({"detail": "Choose a photo under 8 MB."}, status_code=413)
    result = await call_next(request)
    result.headers["Cache-Control"] = "no-store"
    result.headers["X-Content-Type-Options"] = "nosniff"
    return result


app.include_router(auth)
app.include_router(scans)
app.include_router(impact)
app.include_router(locator)
app.include_router(municipality)
app.include_router(admin)


@app.get("/api/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
