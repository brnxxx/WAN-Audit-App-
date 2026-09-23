import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_MAX_AGE_SECONDS, FRONTEND_ORIGINS
from app.database import Base, engine
from app.routers import auth, gns3, devices, sites, backbone, interfaces

app = FastAPI(title="GNS3 Monitoring API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_missing_tables():
    # Keeps the new infrastructure log table available on existing installations.
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE_SECONDS,
    session_cookie="wan_audit_session",
    same_site="lax",
    https_only=False,
)

app.include_router(auth.router)
app.include_router(gns3.router)
app.include_router(devices.router)
app.include_router(sites.router)
app.include_router(backbone.router)
app.include_router(interfaces.router)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled API error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur"})


@app.get("/")
def root():
    return {"status": "ok"}