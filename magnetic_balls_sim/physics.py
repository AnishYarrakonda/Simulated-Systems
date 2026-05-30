"""Vectorized color-wheel magnetism, wall reflection, and ball-ball collisions.

Everything operates on numpy arrays so the simulation stays smooth at up to
~1000 balls (the all-pairs interaction is O(n^2), which is far too slow in a
plain Python loop but trivial for numpy).

Force model
-----------
For two balls with hues a, b in [0, 1), the signed coupling is
    k(a, b) = cos(2 * pi * (a - b))
which is +1 at identical hues, 0 at a quarter turn, -1 at opposite hues.
Magnitude follows 1 / (r^2 + softening). Positive coupling => attraction
along the connecting line.
"""

import math

import numpy as np

TWO_PI = 2.0 * math.pi


def hue_distance(a: float, b: float) -> float:
    """Shortest distance around the color wheel, in [0, 0.5] (scalar helper)."""
    d = abs(a - b) % 1.0
    return d if d <= 0.5 else 1.0 - d


def hue_coupling(a: float, b: float) -> float:
    """Smooth signed coupling: +1 same hue, -1 opposite, 0 at quarter turn."""
    return math.cos(TWO_PI * (a - b))


def apply_forces(px, py, vx, vy, hue, strength, softening, dt):
    """Add the pairwise hue-coupled inverse-square impulses to vx, vy in place."""
    n = px.shape[0]
    if n < 2 or strength == 0.0:
        return

    dx = px[None, :] - px[:, None]            # dx[i, j] = px[j] - px[i]
    dy = py[None, :] - py[:, None]
    r2 = dx * dx + dy * dy + softening
    r = np.sqrt(r2)
    inv_r3 = 1.0 / (r2 * r)

    k = np.cos(TWO_PI * (hue[:, None] - hue[None, :]))
    coef = strength * k * inv_r3              # scalar per pair, sign = attract/repel
    fx = coef * dx
    fy = coef * dy
    np.fill_diagonal(fx, 0.0)
    np.fill_diagonal(fy, 0.0)

    vx += fx.sum(axis=1) * dt
    vy += fy.sum(axis=1) * dt


def resolve_walls(px, py, vx, vy, radius, x0, y0, size):
    x1 = x0 + size
    y1 = y0 + size

    left = px - radius < x0
    px[left] = x0 + radius
    vx[left & (vx < 0.0)] *= -1.0

    right = px + radius > x1
    px[right] = x1 - radius
    vx[right & (vx > 0.0)] *= -1.0

    top = py - radius < y0
    py[top] = y0 + radius
    vy[top & (vy < 0.0)] *= -1.0

    bottom = py + radius > y1
    py[bottom] = y1 - radius
    vy[bottom & (vy > 0.0)] *= -1.0


def resolve_collisions(px, py, vx, vy, radius):
    """Vectorized equal-mass elastic collisions: separate overlapping pairs and
    exchange the velocity components along each contact normal."""
    n = px.shape[0]
    if n < 2:
        return

    min_d = 2.0 * radius
    min_d2 = min_d * min_d

    dx = px[None, :] - px[:, None]            # i -> j
    dy = py[None, :] - py[:, None]
    dist2 = dx * dx + dy * dy
    np.fill_diagonal(dist2, np.inf)

    mask = dist2 < min_d2
    if not mask.any():
        return

    dist = np.sqrt(dist2)
    inv_dist = np.where(mask, 1.0 / dist, 0.0)
    nx = dx * inv_dist                         # unit normal i -> j (0 outside mask)
    ny = dy * inv_dist

    # Positional separation: push i away from each overlapping neighbour.
    overlap = np.where(mask, min_d - dist, 0.0)
    px -= 0.5 * (overlap * nx).sum(axis=1)
    py -= 0.5 * (overlap * ny).sum(axis=1)

    # Velocity exchange along the normal, only for approaching pairs.
    dvx = vx[None, :] - vx[:, None]            # v[j] - v[i]
    dvy = vy[None, :] - vy[:, None]
    vrel = dvx * nx + dvy * ny
    imp = np.where(mask & (vrel < 0.0), vrel, 0.0)
    vx += (imp * nx).sum(axis=1)
    vy += (imp * ny).sum(axis=1)
