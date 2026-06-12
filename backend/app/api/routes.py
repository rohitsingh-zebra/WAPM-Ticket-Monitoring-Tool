from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.models import (
    CacheStatus,
    DashboardSummary,
    DatasetResponse,
    DiagnosticPrecheckResponse,
    DiagnosticRunRequest,
    DiagnosticRunResponse,
    SearchResponse,
    Ticket,
)
from app.services.cache import TicketCache
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/api")


def get_cache() -> TicketCache:
    from app.main import ticket_cache

    return ticket_cache


def get_diagnostic_service(settings: Settings = Depends(get_settings)) -> DiagnosticService:
    return DiagnosticService(settings)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    days: int = Query(2, enum=[2, 7]),
    cache: TicketCache = Depends(get_cache),
) -> DashboardSummary:
    return cache.get_summary(days)


@router.get("/hierarchy", response_model=DatasetResponse)
def hierarchy(
    days: int = Query(2, enum=[2, 7]),
    cache: TicketCache = Depends(get_cache),
) -> DatasetResponse:
    status = cache.get_status()
    return DatasetResponse(days=days, last_refresh_time=status.last_refresh_time, data=cache.get_hierarchy(days))


@router.get("/tickets/{ticket_id}", response_model=Ticket)
def ticket_details(ticket_id: str, cache: TicketCache = Depends(get_cache)) -> Ticket:
    ticket = cache.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found in cache.")
    return ticket


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query("", min_length=0),
    cache: TicketCache = Depends(get_cache),
) -> SearchResponse:
    tickets = cache.search(q)
    return SearchResponse(query=q, count=len(tickets), tickets=tickets)


@router.get("/cache/status", response_model=CacheStatus)
def cache_status(cache: TicketCache = Depends(get_cache)) -> CacheStatus:
    return cache.get_status()


@router.post("/cache/refresh", response_model=CacheStatus)
async def refresh_cache(cache: TicketCache = Depends(get_cache)) -> CacheStatus:
    await cache.refresh()
    return cache.get_status()


@router.post("/diagnostics/run", response_model=DiagnosticRunResponse)
def run_diagnostic(
    payload: DiagnosticRunRequest,
    cache: TicketCache = Depends(get_cache),
    diagnostics: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticRunResponse:
    ticket = cache.get_ticket(payload.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {payload.ticket_id} was not found in cache.")

    return diagnostics.run_for_ticket(ticket=ticket, otp=payload.otp)


@router.get("/diagnostics/precheck", response_model=DiagnosticPrecheckResponse)
def diagnostic_precheck(
    ticket_id: str = Query(...),
    cache: TicketCache = Depends(get_cache),
    diagnostics: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticPrecheckResponse:
    ticket = cache.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found in cache.")

    return diagnostics.precheck_ticket(ticket=ticket)
