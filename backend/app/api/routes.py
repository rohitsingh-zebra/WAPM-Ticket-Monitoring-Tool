from fastapi import APIRouter, Depends, HTTPException, Query

from app.models import CacheStatus, DashboardSummary, DatasetResponse, SearchResponse, Ticket
from app.services.cache import TicketCache

router = APIRouter(prefix="/api")


def get_cache() -> TicketCache:
    from app.main import ticket_cache

    return ticket_cache


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
