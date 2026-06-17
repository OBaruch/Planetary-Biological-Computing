from fastapi.testclient import TestClient

from app.main import app
from app.services.encoder import PlanetEncoder
from app.services.planet_data import PlanetDataProvider
from app.services.planet_simulation import PlanetSimulation
from app.services.spike_decoder import SpikeDecoder


def test_planet_simulation_step() -> None:
    provider = PlanetDataProvider(seed=4)
    planet = provider.next()
    metrics, action = SpikeDecoder(window_seconds=1).decode([], planet)
    state = PlanetSimulation(seed=4).step(planet, metrics, action)
    assert 0 <= state.temperature <= 1
    assert state.planetary_mood_label


def test_demo_event_injection() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/control/demo-event",
        json={"type": "wildfire", "intensity": 0.8, "duration_seconds": 12},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
