from __future__ import annotations

from app.models.data_source import CredentialField, SourceDescriptor


# Declarative catalog of every real-data source. This is the single source of
# truth consumed by both the Settings UI (GET /api/sources) and the connector
# factory (registry.py). Adding a new source = one entry here + one connector.
#
# v1 ships 10 sources: 7 key-free and 3 key-based. The remaining ~40 from the
# research catalog are added later by appending entries + connectors.
SOURCE_CATALOG: dict[str, SourceDescriptor] = {
    "usgs": SourceDescriptor(
        id="usgs",
        name="USGS Earthquakes",
        category="geophysics",
        kind="geo_event",
        requires_key=False,
        description="Real-time earthquakes (M2.5+) over the past day from the public USGS GeoJSON feed.",
        doc_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        feeds=["Earthquake markers", "earthquake_frequency", "earthquake_magnitude"],
    ),
    "eonet": SourceDescriptor(
        id="eonet",
        name="NASA EONET",
        category="geophysics",
        kind="geo_event",
        requires_key=False,
        description="Open natural events from NASA Earth Observatory: wildfires, storms, volcanoes, ice, floods.",
        doc_url="https://eonet.gsfc.nasa.gov/docs/v3",
        feeds=["Wildfire / storm / volcano markers"],
    ),
    "gdacs": SourceDescriptor(
        id="gdacs",
        name="GDACS Disaster Alerts",
        category="geophysics",
        kind="geo_event",
        requires_key=False,
        description="Global Disaster Alert and Coordination System: earthquakes, cyclones, floods, volcanoes, droughts.",
        doc_url="https://www.gdacs.org/",
        feeds=["Disaster alert markers"],
    ),
    "iss": SourceDescriptor(
        id="iss",
        name="ISS Position",
        category="movement",
        kind="geo_event",
        requires_key=False,
        description="Live position of the International Space Station (wheretheiss.at), rendered as a moving marker.",
        doc_url="https://wheretheiss.at/w/developer",
        feeds=["ISS position marker"],
    ),
    "firms": SourceDescriptor(
        id="firms",
        name="NASA FIRMS Active Fires",
        category="geophysics",
        kind="geo_event",
        requires_key=True,
        description="Near-real-time active fire detections (MODIS/VIIRS). Free MAP_KEY required.",
        doc_url="https://firms.modaps.eosdis.nasa.gov/api/area/",
        signup_url="https://firms.modaps.eosdis.nasa.gov/api/map_key/",
        credential_fields=[
            CredentialField(
                key="map_key",
                label="MAP_KEY",
                help="Free key from firms.modaps.eosdis.nasa.gov/api/map_key/",
            )
        ],
        feeds=["Active fire markers", "wildfire_risk_index"],
    ),
    "open_meteo": SourceDescriptor(
        id="open_meteo",
        name="Open-Meteo",
        category="atmosphere",
        kind="signal",
        requires_key=False,
        description="Free weather + air-quality forecasts (no key). Sampled across world cities into global indices.",
        doc_url="https://open-meteo.com/en/docs",
        feeds=["air_quality_index", "precipitation_index"],
    ),
    "openweather": SourceDescriptor(
        id="openweather",
        name="OpenWeatherMap Air Pollution",
        category="atmosphere",
        kind="signal",
        requires_key=True,
        description="Real-time air pollution (PM2.5/PM10, NO2, O3...) sampled across world cities. Free API key.",
        doc_url="https://openweathermap.org/api/air-pollution",
        signup_url="https://home.openweathermap.org/users/sign_up",
        credential_fields=[
            CredentialField(
                key="api_key",
                label="API key",
                help="Free key from openweathermap.org (activation can take up to 2h).",
            )
        ],
        feeds=["air_quality_index"],
    ),
    "openaq": SourceDescriptor(
        id="openaq",
        name="OpenAQ Stations",
        category="atmosphere",
        kind="signal",
        requires_key=True,
        description="Air-quality measurements from physical monitoring stations worldwide. Free API key (X-API-Key).",
        doc_url="https://docs.openaq.org/",
        signup_url="https://explore.openaq.org/register",
        credential_fields=[
            CredentialField(
                key="api_key",
                label="API key",
                help="Free key from explore.openaq.org/register (sent as X-API-Key).",
            )
        ],
        feeds=["air_quality_index"],
    ),
    "gdelt": SourceDescriptor(
        id="gdelt",
        name="GDELT Global News Tone",
        category="society",
        kind="signal",
        requires_key=False,
        description="Worldwide news tone/sentiment (no key), updated every 15 min, mapped to tension/sentiment indices.",
        doc_url="https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/",
        feeds=[
            "global_news_tension_index",
            "sentiment_index",
            "conflict_index",
            "cooperation_index",
        ],
    ),
    "noaa_swpc": SourceDescriptor(
        id="noaa_swpc",
        name="NOAA Space Weather (SWPC)",
        category="space",
        kind="signal",
        requires_key=False,
        description="Geomagnetic activity (planetary Kp index) from NOAA SWPC (no key), mapped to a solar-storm signal.",
        doc_url="https://www.swpc.noaa.gov/content/data-access",
        feeds=["storm_intensity_index"],
    ),
}


def list_descriptors() -> list[SourceDescriptor]:
    return list(SOURCE_CATALOG.values())


def get_descriptor(source_id: str) -> SourceDescriptor | None:
    return SOURCE_CATALOG.get(source_id)
