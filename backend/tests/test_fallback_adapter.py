from app.models.neural import StimulationIntent
from app.services.fallback_synthetic_adapter import FallbackSyntheticAdapter


def test_fallback_adapter_is_deterministic_and_labeled() -> None:
    intent = StimulationIntent(
        target_channels=[1, 2, 3],
        intensity=0.8,
        burst_frequency=20,
        encoded_planet_signature=[0.1] * 8,
        stimulation_intent="test",
        metadata={"simulator_non_causal": True},
    )
    first = FallbackSyntheticAdapter(seed=7)
    second = FallbackSyntheticAdapter(seed=7)
    first.start()
    second.start()
    first.send_stimulation_intent(intent)
    second.send_stimulation_intent(intent)
    first_spikes = first.read_tick()
    second_spikes = second.read_tick()
    assert [spike.channel for spike in first_spikes] == [spike.channel for spike in second_spikes]
    assert "fallback synthetic mode" in first.status.lower()
