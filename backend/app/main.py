import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api import ai, auth, health, learners
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("igboai")

app = FastAPI(title=settings.app_name)


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
