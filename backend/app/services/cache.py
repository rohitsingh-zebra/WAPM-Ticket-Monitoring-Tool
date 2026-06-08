import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.models import CacheStatus, DashboardSummary, HierarchyNode, Ticket
from app.services.category_classifier import CategoryClassifier
from app.services.jira_client import JiraClient


@dataclass(frozen=True)
class CachedDataset:
    tickets: list[Ticket]
    hierarchy: list[HierarchyNode]
    summary: DashboardSummary


class TicketCache:
    def __init__(self, jira_client: JiraClient, classifier: CategoryClassifier) -> None:
        self.jira_client = jira_client
        self.classifier = classifier
        self._datasets: dict[int, CachedDataset] = {}
        self._ticket_index: dict[str, Ticket] = {}
        self._last_refresh_time: datetime | None = None
        self._health_status: str = "empty"
        self._error: str | None = None
        self._lock = asyncio.Lock()

    async def refresh(self) -> None:
        async with self._lock:
            self._health_status = "refreshing"
            try:
                seven_day_tickets = await self.jira_client.fetch_recent_tickets(days=7)
                categorized_tickets = [self._categorize(ticket) for ticket in seven_day_tickets]
                refresh_time = datetime.now(timezone.utc)

                new_datasets = {
                    days: self._build_dataset(self._filter_by_days(categorized_tickets, days), refresh_time)
                    for days in (2, 7)
                }
                self._datasets = new_datasets
                self._ticket_index = {ticket.key.upper(): ticket for ticket in categorized_tickets}
                self._last_refresh_time = refresh_time
                self._health_status = "healthy"
                self._error = None
            except Exception as exc:
                self._health_status = "error"
                self._error = str(exc)
                raise

    def get_summary(self, days: int) -> DashboardSummary:
        return self._get_dataset(days).summary

    def get_hierarchy(self, days: int) -> list[HierarchyNode]:
        return self._get_dataset(days).hierarchy

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        return self._ticket_index.get(ticket_id.upper())

    def search(self, query: str) -> list[Ticket]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        return [
            ticket
            for ticket in self._ticket_index.values()
            if normalized_query in ticket.key.lower()
            or normalized_query in ticket.cluster.lower()
            or normalized_query in ticket.organization.lower()
            or normalized_query in ticket.category.lower()
            or normalized_query in ticket.summary.lower()
        ]

    def get_status(self) -> CacheStatus:
        total_cached_tickets = len(self._ticket_index)
        status = self._health_status
        if status == "healthy" and total_cached_tickets == 0:
            status = "empty"

        return CacheStatus(
            last_refresh_time=self._last_refresh_time,
            total_cached_tickets=total_cached_tickets,
            cache_health_status=status,  # type: ignore[arg-type]
            error=self._error,
        )

    def _get_dataset(self, days: int) -> CachedDataset:
        if days not in (2, 7):
            raise ValueError("Only days=2 and days=7 are supported.")

        return self._datasets.get(days) or self._build_dataset([], self._last_refresh_time)

    def _categorize(self, ticket: Ticket) -> Ticket:
        return ticket.model_copy(update={"category": self.classifier.classify(ticket)})

    def _filter_by_days(self, tickets: list[Ticket], days: int) -> list[Ticket]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return [ticket for ticket in tickets if ticket.created >= cutoff]

    def _build_dataset(self, tickets: list[Ticket], refresh_time: datetime | None) -> CachedDataset:
        return CachedDataset(
            tickets=tickets,
            hierarchy=self._build_hierarchy(tickets),
            summary=self._build_summary(tickets, refresh_time),
        )

    def _build_summary(self, tickets: list[Ticket], refresh_time: datetime | None) -> DashboardSummary:
        status_counts = {ticket.status.lower(): 0 for ticket in tickets}
        for ticket in tickets:
            status_counts[ticket.status.lower()] = status_counts.get(ticket.status.lower(), 0) + 1

        return DashboardSummary(
            total_tickets=len(tickets),
            open_tickets=status_counts.get("open", 0) + status_counts.get("to do", 0),
            in_progress_tickets=status_counts.get("in progress", 0),
            resolved_tickets=status_counts.get("resolved", 0) + status_counts.get("done", 0) + status_counts.get("closed", 0),
            total_clusters=len({ticket.cluster for ticket in tickets}),
            total_organizations=len({ticket.organization for ticket in tickets}),
            last_refresh_time=refresh_time,
        )

    def _build_hierarchy(self, tickets: list[Ticket]) -> list[HierarchyNode]:
        clusters: dict[str, dict[str, dict[str, list[Ticket]]]] = {}

        for ticket in tickets:
            clusters.setdefault(ticket.cluster, {}).setdefault(ticket.organization, {}).setdefault(ticket.category, []).append(ticket)

        cluster_nodes: list[HierarchyNode] = []
        for cluster_name in sorted(clusters):
            org_nodes: list[HierarchyNode] = []
            cluster_count = 0

            for org_name in sorted(clusters[cluster_name]):
                category_nodes: list[HierarchyNode] = []
                org_count = 0

                for category_name in sorted(clusters[cluster_name][org_name]):
                    category_tickets = sorted(
                        clusters[cluster_name][org_name][category_name],
                        key=lambda ticket: ticket.created,
                        reverse=True,
                    )
                    org_count += len(category_tickets)
                    category_nodes.append(
                        HierarchyNode(
                            id=f"{cluster_name}/{org_name}/{category_name}",
                            label=category_name,
                            type="category",
                            count=len(category_tickets),
                            children=[
                                HierarchyNode(
                                    id=ticket.key,
                                    label=f"{ticket.key}: {ticket.summary}",
                                    type="ticket",
                                    count=1,
                                    ticket=ticket,
                                )
                                for ticket in category_tickets
                            ],
                        )
                    )

                cluster_count += org_count
                org_nodes.append(
                    HierarchyNode(
                        id=f"{cluster_name}/{org_name}",
                        label=org_name,
                        type="organization",
                        count=org_count,
                        children=category_nodes,
                    )
                )

            cluster_nodes.append(
                HierarchyNode(
                    id=cluster_name,
                    label=cluster_name,
                    type="cluster",
                    count=cluster_count,
                    children=org_nodes,
                )
            )

        return cluster_nodes
