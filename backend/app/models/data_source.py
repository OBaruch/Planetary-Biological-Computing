from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceCategory = Literal["geophysics", "atmosphere", "space", "society", "movement"]
SourceKind = Literal["geo_event", "signal"]


class CredentialField(BaseModel):
    """A single secret a user must paste for a source (e.g. an API key)."""

    key: str
    label: str
    help: str | None = None
    secret: bool = True
    placeholder: str | None = None


class SourceDescriptor(BaseModel):
    """Declarative description of a real-data source.

    This is the single source of truth consumed by both the Settings UI and
    the connector factory. It carries no secrets.
    """

    id: str
    name: str
    category: SourceCategory
    kind: SourceKind
    requires_key: bool
    description: str
    doc_url: str | None = None
    signup_url: str | None = None
    credential_fields: list[CredentialField] = Field(default_factory=list)
    # Planet-input field names a signal source feeds, or human labels for geo markers.
    feeds: list[str] = Field(default_factory=list)


class SourceHealth(BaseModel):
    """Last-known liveness of a source. ``ok=None`` means never fetched/tested."""

    ok: bool | None = None
    last_fetch: datetime | None = None
    error: str | None = None
    count: int | None = None


class SourceStatus(BaseModel):
    """A descriptor plus the current per-user state for it."""

    descriptor: SourceDescriptor
    configured: bool
    enabled: bool
    active: bool
    masked_credentials: dict[str, str] = Field(default_factory=dict)
    health: SourceHealth = Field(default_factory=SourceHealth)


class SourcesResponse(BaseModel):
    data_mode: str
    active_count: int
    total_count: int
    sources: list[SourceStatus] = Field(default_factory=list)


class CredentialUpdate(BaseModel):
    """Body for PUT /api/sources/{id}/credentials. Secrets are write-only."""

    secrets: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class ToggleRequest(BaseModel):
    enabled: bool


class TestRequest(BaseModel):
    """Optional secrets to validate before persisting (else stored ones are used)."""

    secrets: dict[str, str] = Field(default_factory=dict)


class TestResult(BaseModel):
    ok: bool
    count: int = 0
    error: str | None = None
    sample: str | None = None
