from app.models.neural import NeuralSpike
from app.services.planet_data import PlanetDataProvider
from app.services.spike_decoder import SpikeDecoder


def test_decoder_with_fake_spikes() -> None:
    spikes = [NeuralSpike(channel=ch, timestamp=1000 + ch) for ch in [1, 2, 18, 19, 50, 51]]
    planet = PlanetDataProvider(seed=1).next()
    metrics, action = SpikeDecoder(window_seconds=1).decode(spikes, planet)
    assert metrics.spikes_per_second == 6
    assert metrics.active_channels_count == 6
    assert 0 <= metrics.channel_entropy <= 1
    assert action.primary_action in action.action_vector
