from app.services.encoder import PlanetEncoder
from app.services.planet_data import PlanetDataProvider


def test_encoder_output_range() -> None:
    planet = PlanetDataProvider(seed=1).next()
    intent = PlanetEncoder().encode(planet)
    assert 0 <= intent.intensity <= 1
    assert intent.burst_frequency >= 0
    assert len(intent.encoded_planet_signature) == 8
    assert all(0 <= value <= 1 for value in intent.encoded_planet_signature)
    assert all(0 <= channel <= 63 for channel in intent.target_channels)
