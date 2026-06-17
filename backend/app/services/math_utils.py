from __future__ import annotations

import math


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize(value: float, low: float, high: float) -> float:
    if math.isclose(high, low):
        return 0.0
    return clamp((value - low) / (high - low))


def lerp(current: float, target: float, alpha: float) -> float:
    return current + (target - current) * clamp(alpha)
