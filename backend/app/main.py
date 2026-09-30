import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app import models
from app.database import Base, engine
from app.plaid import router as plaid_router
from app.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Ensuring table %s exists", models.Transaction.__tablename__)
        Base.metadata.create_all(bind=engine)
    except OperationalError:
        logger.warning("PostgreSQL is not reachable. The API will respond once the database is up.")
    yield


app = FastAPI(title="Financial Autopsy", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(plaid_router)


@app.exception_handler(OperationalError)
async def database_unavailable(_request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "PostgreSQL is not running."},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Financial Autopsy API", "docs": "/docs"}
