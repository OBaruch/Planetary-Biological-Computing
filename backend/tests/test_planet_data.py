from app.services.planet_data import PlanetDataProvider


def test_mock_planet_data_generation() -> None:
    provider = PlanetDataProvider(data_mode="demo", seed=123)
    data = provider.next()
    assert data.source_mode == "demo"
    assert 380 <= data.co2_ppm <= 470
    assert 0 <= data.planetary_stress_score <= 1
    assert 0 <= data.recovery_potential_score <= 1
    assert 0 <= data.chaos_score <= 1
    assert 0 <= data.resilience_score <= 1
