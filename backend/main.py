"""BRD — FastAPI entry point (Aakaar golden scaffold).

Routers are AUTO-DISCOVERED: every module in backend/routers/ that exposes a module-level
`router` is mounted at the /api prefix. Route decorators therefore declare paths relative
to /api (e.g. @router.post("/auth/login") serves POST /api/auth/login). Drop a new router
file in backend/routers/ and it is live — no wiring edits, no phantom imports.
"""
import importlib
import logging
import os
import pkgutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.config import check_db_health, init_db

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BRD", version="1.0.0", lifespan=lifespan)

_frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"detail": exc.errors()}, status_code=422)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db": check_db_health(),
        "time": datetime.now(timezone.utc).isoformat(),
    }


def _mount_routers() -> None:
    """Mount every backend/routers/*.py module that exposes `router`, at /api."""
    import backend.routers as routers_pkg

    for mod_info in pkgutil.iter_modules(routers_pkg.__path__):
        if mod_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"backend.routers.{mod_info.name}")
        router = getattr(module, "router", None)
        if router is not None:
            app.include_router(router, prefix="/api")
            logger.info("Mounted router: backend/routers/%s.py", mod_info.name)


_mount_routers()
