import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.api import ai, auth, curriculum, exercises, health, learners, lessons, vocabulary
from app.core.config import get_settings
from app.core.db import engine

settings = get_settings()
logger = logging.getLogger("igboai")

# The single most common first-run failure: the app connects to a real,
# reachable Postgres database that simply has no tables yet (migrations
# never applied). Left unchecked, that surfaces as an opaque 500 on the
# first request (e.g. "relation users does not exist") with no clue why.
# Fail loudly at startup instead, with the actual fix.
_REQUIRED_TABLE = "users"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if _REQUIRED_TABLE not in table_names:
        raise RuntimeError(
            f"Database schema is not initialized (no '{_REQUIRED_TABLE}' table found). "
            "Run migrations before starting the server: `alembic upgrade head` "
            "(from the backend/ directory, with your venv active)."
        )
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # e.g. a race on the unique email constraint — never leak raw SQL/DB detail.
    logger.warning("IntegrityError on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=400, content={"detail": "The request conflicts with existing data"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(learners.router)
app.include_router(curriculum.router)
app.include_router(lessons.router)
app.include_router(exercises.router)
app.include_router(vocabulary.router)
