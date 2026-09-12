import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_MAX_AGE_SECONDS
from app.routers import auth, gns3, devices, sites, backbone, interfaces

app = FastAPI(title="GNS3 Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500", "http://localhost:5500",
        "http://127.0.0.1:5173", "http://localhost:5173",
    ],
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
app.include_router(gns3.router)
app.include_router(devices.router)
app.include_router(sites.router)
app.include_router(backbone.router)
app.include_router(interfaces.router)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(tb)
    return JSONResponse(status_code=500, content={"error": str(exc), "traceback": tb})


@app.get("/")
def root():
    return {"status": "ok"}