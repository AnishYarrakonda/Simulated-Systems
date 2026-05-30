"""Hue samplers for the color-wheel distribution choices.

Every sampler returns a list of hues in [0.0, 1.0). The caller shuffles
before placing them on the spawn grid so the starting frame is not sorted.
"""

import random


def _wrap(h: float) -> float:
    """Wrap a hue into [0, 1)."""
    return h - int(h) if h >= 0.0 else (h - int(h)) + 1.0


def sample_uniform(n: int):
    return [random.random() for _ in range(n)]


def sample_gaussian(n: int, mean: float, stddev: float):
    return [_wrap(random.gauss(mean, stddev)) for _ in range(n)]


def sample_bimodal(n: int, center: float, stddev: float):
    other = _wrap(center + 0.5)
    half = n // 2
    out = [_wrap(random.gauss(center, stddev)) for _ in range(half)]
    out += [_wrap(random.gauss(other, stddev)) for _ in range(n - half)]
    return out


def sample(distribution: str, n: int, params: dict):
    """Dispatch to the right sampler. params keys vary by distribution."""
    if distribution == "Uniform":
        return sample_uniform(n)
    if distribution == "Gaussian":
        return sample_gaussian(n, params["mean"], params["stddev"])
    if distribution == "Bimodal":
        return sample_bimodal(n, params["center"], params["stddev"])
    return sample_uniform(n)
