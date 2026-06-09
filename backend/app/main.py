import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes import router
from app.config import get_settings
from app.services.cache import TicketCache
from app.services.category_classifier import CategoryClassifier
from app.services.jira_client import JiraClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
ticket_cache = TicketCache(
    jira_client=JiraClient(settings),
    classifier=CategoryClassifier(),
)
scheduler = AsyncIOScheduler()


async def refresh_cache_job() -> None:
    try:
        await ticket_cache.refresh()
        logger.info("WAPM Jira cache refreshed successfully.")
    except Exception:
        logger.exception("WAPM Jira cache refresh failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        refresh_cache_job,
        "interval",
        minutes=settings.cache_refresh_interval_minutes,
        id="wapm-cache-refresh",
        replace_existing=True,
        next_run_time=None,
    )
    scheduler.start()
    await refresh_cache_job()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="WAPM Ticket Monitoring API",
    description="FastAPI backend for monitoring WAPM Jira tickets grouped by dynamic issue category.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_dev_cors_headers(request: Request, call_next) -> Response:
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = request.headers.get("access-control-request-headers", "*")
    return response


app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok, server running"}
