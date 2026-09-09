import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_MAX_AGE_SECONDS
from app.routers import auth

app = FastAPI(title="GNS3 Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE_SECONDS,
    session_cookie="wan_audit_session",
    same_site="lax",
    https_only=False,
)

app.include_router(auth.router)


# ⚠️ TEMPORAIRE — à retirer avant toute mise en prod.
# Affiche la traceback complète en réponse JSON au lieu d'un 500 opaque.
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(tb)  # toujours visible dans le terminal aussi
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": tb},
    )


@app.get("/")
def root():
    return {"status": "ok"}