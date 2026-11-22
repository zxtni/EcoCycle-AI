import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.auth import router as auth
from backend.db import engine
from backend.impact import router as impact
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
    result = await call_next(request)
    result.headers["Cache-Control"] = "no-store"
    result.headers["X-Content-Type-Options"] = "nosniff"
    return result


app.include_router(auth)
app.include_router(scans)
app.include_router(impact)


@app.get("/api/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}

