from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Ticket(BaseModel):
    id: str
    key: str
    summary: str
    description: str = ""
    status: str = "Unknown"
    assignee: str | None = None
    created: datetime
    updated: datetime
    resolution_date: datetime | None = None
    resolution_time_hours: float | None = None
    jira_url: str
    cluster: str
    organization: str
    issue_type: str = "Unknown"  # Jira issuetype metadata; grouping uses `category`
    category: str = "Others"  # Dynamically derived issue category from summary
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HierarchyNode(BaseModel):
    id: str
    label: str
    type: Literal["category", "ticket"]
    count: int
    children: list["HierarchyNode"] = Field(default_factory=list)
    ticket: Ticket | None = None


class DashboardSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    total_categories: int
    last_refresh_time: datetime | None


class CacheStatus(BaseModel):
    last_refresh_time: datetime | None
    total_cached_tickets: int
    cache_health_status: Literal["empty", "healthy", "refreshing", "error"]
    error: str | None = None


class DatasetResponse(BaseModel):
    days: int
    last_refresh_time: datetime | None
    data: list[HierarchyNode]


class SearchResponse(BaseModel):
    query: str
    count: int
    tickets: list[Ticket]


class DiagnosticFile(BaseModel):
    name: str
    modified_at: datetime


class DiagnosticRunRequest(BaseModel):
    ticket_id: str
    otp: str = Field(min_length=1)


class DiagnosticRunResponse(BaseModel):
    success: bool
    error_code: str | None = None
    message: str
    company: str | None = None
    host_name: str | None = None
    remote_path: str | None = None
    file_count: int = 0
    files: list[DiagnosticFile] = Field(default_factory=list)


class DiagnosticPrecheckResponse(BaseModel):
    success: bool
    error_code: str | None = None
    message: str
    company: str | None = None
    host_name: str | None = None
