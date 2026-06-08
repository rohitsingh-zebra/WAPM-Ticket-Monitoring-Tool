from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jira_base_url: str = Field(..., alias="JIRA_BASE_URL")
    jira_pat: str = Field(..., alias="JIRA_PAT")
    jira_project_key: str = Field("Workforce AppMonitoring", alias="JIRA_PROJECT_KEY")
    jira_cluster_field: str = Field(..., alias="JIRA_CLUSTER_FIELD")
    jira_client_env_fields: str = Field(
        ...,
        validation_alias=AliasChoices("JIRA_CLIENT_ENV_FIELDS", "JIRA_CLIENT_ENV_FIELD", "JIRA_ORG_FIELD"),
    )
    jira_page_size: int = Field(100, alias="JIRA_PAGE_SIZE")
    jira_max_results: int = Field(5000, alias="JIRA_MAX_RESULTS")
    cache_refresh_interval_minutes: int = Field(5, alias="CACHE_REFRESH_INTERVAL_MINUTES")
    alert_type_rules_file: Path = Field(
        Path("alert_type_rules.json"),
        validation_alias=AliasChoices("ALERT_TYPE_RULES_FILE", "CATEGORY_RULES_FILE"),
    )
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig", extra="ignore")

    @field_validator("jira_base_url")
    @classmethod
    def normalize_jira_url(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def jira_client_env_field_ids(self) -> list[str]:
        return [field.strip() for field in self.jira_client_env_fields.split(",") if field.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
