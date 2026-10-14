import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.catalog import router as catalog_router
from app.config import get_settings
from app.database import get_engine
from app.evaluation import router as evaluation_router
from app.identity import router as identity_router
from app.requests import router as requests_router
from app.sessions import router as sessions_router
from app.trust import admin_router
from app.trust import router as trust_router

app = FastAPI(
    title="SkillSwap API",
    version="0.1.0",
    description="Time-banking and peer skill exchange for a local college demo.",
)
app.include_router(identity_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(requests_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(trust_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = str(uuid4())
    if request.method in {"POST", "PUT", "PATCH"}:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                return error_response(request, 413, "BODY_TOO_LARGE", "Request exceeds 64 KiB")
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def error_response(request, status, code, message, details=None):
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    detail = (
        exc.detail
        if isinstance(exc.detail, dict)
        else {"code": "HTTP_ERROR", "message": exc.detail}
    )
    response = error_response(request, exc.status_code, detail["code"], detail["message"])
    if exc.status_code == 401:
        response.headers["WWW-Authenticate"] = "Bearer"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    # Never echo Pydantic's raw input or context, which may include a password.
    details = [
        {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()
    ]
    return error_response(request, 422, "VALIDATION_ERROR", "Check the supplied fields", details)


@app.exception_handler(IntegrityError)
async def database_conflict(request, exc):
    return error_response(
        request, 409, "DATABASE_CONFLICT", "The operation conflicts with existing data"
    )


@app.exception_handler(OperationalError)
async def database_unavailable(request, exc):
    return error_response(request, 503, "DATABASE_UNAVAILABLE", "Please try again shortly")


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logging.error("Unhandled error %s request_id=%s", type(exc).__name__, request.state.request_id)
    return error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred")


@app.get("/health/live", tags=["Health"])
def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
def ready():
    try:
        with get_engine().connect() as conn:
            version = conn.scalar(text("SELECT version_num FROM alembic_version LIMIT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            503,
            detail={
                "code": "DATABASE_NOT_READY",
                "message": "Apply migrations and check the database connection",
            },
        ) from None
    if version != "002_integrity":
        raise HTTPException(
            503,
            detail={
                "code": "MIGRATIONS_REQUIRED",
                "message": "Apply the current database migrations",
            },
        )
    return {"status": "ready"}


# Keep CORS outside the request-size guard so browsers can read bounded-input errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
