from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.data_source import SourceDescriptor, SourceHealth, SourceStatus
from app.services.data_sources.catalog import get_descriptor, list_descriptors
from app.services.data_sources.credentials import CredentialStore
from app.services.data_sources.signals.base import SignalConnector
from app.services.data_sources.signals.gdelt import GdeltConnector
from app.services.data_sources.signals.noaa_swpc import NoaaSwpcConnector
from app.services.data_sources.signals.open_meteo import OpenMeteoConnector
from app.services.data_sources.signals.openaq import OpenAqConnector
from app.services.data_sources.signals.openweather import OpenWeatherConnector
from app.services.geo_events.base import GeoEventConnector
from app.services.geo_events.eonet import EonetConnector
from app.services.geo_events.firms import FirmsConnector
from app.services.geo_events.gdacs import GdacsConnector
from app.services.geo_events.iss import IssConnector
from app.services.geo_events.usgs_earthquakes import UsgsEarthquakeConnector

logger = logging.getLogger(__name__)


def _required_fields(descriptor: SourceDescriptor) -> list[str]:
    return [field.key for field in descriptor.credential_fields]


class SourceRegistry:
    """Resolves the source catalog + per-user credentials into live connectors.

    A source is *active* when it is enabled and (if it needs a key) configured.
    Only active sources are instantiated and polled, so the globe shows strictly
    the data the user has connected.
    """

    def __init__(self, store: CredentialStore) -> None:
        self.store = store
        self._health: dict[str, SourceHealth] = {}

    # -- state -------------------------------------------------------------
    def is_configured(self, source_id: str) -> bool:
        descriptor = get_descriptor(source_id)
        if descriptor is None:
            return False
        return self.store.is_configured(source_id, _required_fields(descriptor))

    def is_enabled(self, source_id: str) -> bool:
        flag = self.store.enabled_flag(source_id)
        return True if flag is None else bool(flag)

    def is_active(self, source_id: str) -> bool:
        return self.is_enabled(source_id) and self.is_configured(source_id)

    def status(self, source_id: str) -> SourceStatus | None:
        descriptor = get_descriptor(source_id)
        if descriptor is None:
            return None
        return SourceStatus(
            descriptor=descriptor,
            configured=self.is_configured(source_id),
            enabled=self.is_enabled(source_id),
            active=self.is_active(source_id),
            masked_credentials=self.store.masked(source_id, _required_fields(descriptor)),
            health=self._health.get(source_id, SourceHealth()),
        )

    def statuses(self) -> list[SourceStatus]:
        return [s for s in (self.status(d.id) for d in list_descriptors()) if s is not None]

    def active_ids(self) -> set[str]:
        return {d.id for d in list_descriptors() if self.is_active(d.id)}

    # -- health ------------------------------------------------------------
    def record_health(self, source_id: str, *, ok: bool, count: int | None = None, error: str | None = None) -> None:
        self._health[source_id] = SourceHealth(
            ok=ok,
            last_fetch=datetime.now(timezone.utc),
            error=error,
            count=count,
        )

    # -- connector factories ----------------------------------------------
    def build_geo_connector(
        self, source_id: str, secrets: dict[str, str] | None = None
    ) -> GeoEventConnector | None:
        descriptor = get_descriptor(source_id)
        if descriptor is None or descriptor.kind != "geo_event":
            return None
        if secrets is None:
            secrets = self.store.get_secrets(source_id, _required_fields(descriptor))
        if source_id == "usgs":
            return UsgsEarthquakeConnector()
        if source_id == "eonet":
            return EonetConnector()
        if source_id == "gdacs":
            return GdacsConnector()
        if source_id == "iss":
            return IssConnector()
        if source_id == "firms":
            map_key = secrets.get("map_key")
            return FirmsConnector(map_key) if map_key else None
        return None

    def build_signal_connector(
        self, source_id: str, secrets: dict[str, str] | None = None
    ) -> SignalConnector | None:
        descriptor = get_descriptor(source_id)
        if descriptor is None or descriptor.kind != "signal":
            return None
        if secrets is None:
            secrets = self.store.get_secrets(source_id, _required_fields(descriptor))
        if source_id == "open_meteo":
            return OpenMeteoConnector()
        if source_id == "gdelt":
            return GdeltConnector()
        if source_id == "noaa_swpc":
            return NoaaSwpcConnector()
        if source_id == "openweather":
            api_key = secrets.get("api_key")
            return OpenWeatherConnector(api_key) if api_key else None
        if source_id == "openaq":
            api_key = secrets.get("api_key")
            return OpenAqConnector(api_key) if api_key else None
        return None

    def active_geo_connectors(self) -> list[GeoEventConnector]:
        connectors: list[GeoEventConnector] = []
        for descriptor in list_descriptors():
            if descriptor.kind != "geo_event" or not self.is_active(descriptor.id):
                continue
            connector = self.build_geo_connector(descriptor.id)
            if connector is not None:
                connectors.append(connector)
        return connectors

    def active_signal_connectors(self) -> list[SignalConnector]:
        connectors: list[SignalConnector] = []
        for descriptor in list_descriptors():
            if descriptor.kind != "signal" or not self.is_active(descriptor.id):
                continue
            connector = self.build_signal_connector(descriptor.id)
            if connector is not None:
                connectors.append(connector)
        return connectors

    def build_one(self, source_id: str, secrets: dict[str, str] | None = None):
        """Build a single connector regardless of enabled state (for the test endpoint).

        ``secrets`` overlays the stored credentials so a key can be validated
        before it is persisted.
        """
        descriptor = get_descriptor(source_id)
        if descriptor is None:
            return None
        merged: dict[str, str] | None = None
        if secrets:
            merged = self.store.get_secrets(source_id, _required_fields(descriptor))
            merged.update({k: v for k, v in secrets.items() if v})
        if descriptor.kind == "geo_event":
            return self.build_geo_connector(source_id, merged)
        return self.build_signal_connector(source_id, merged)
