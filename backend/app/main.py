import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.api import auth, customers, dashboard, inventory, notifications, orders, reports, system

logger = logging.getLogger("anand")
app = FastAPI(
    title="Anand Jewellers API",
    version="1.1.0",
    description="Customer, order, inventory, notification, and report API for Anand Jewellers staff.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for module in (auth, customers, orders, inventory, notifications, dashboard, reports, system):
    app.include_router(module.router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        loc = ".".join(str(item) for item in err.get("loc", []) if item != "body")
        parts.append(f"{loc}: {err.get('msg')}" if loc else err.get("msg", "Invalid value"))
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Check the form and try again."})


@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, exc: IntegrityError):
    logger.warning("database constraint")
    return JSONResponse(status_code=409, content={"detail": "That record conflicts with existing data."})


@app.get("/api/health", tags=["system"], summary="Health check")
def health():
    return {"status": "ok"}
