"""Primer's colour palette, from constants.py `color_scheme = 2` ("Main")."""

BG = (47, 51, 54)
TEXT = (243, 242, 240)
BLUE = (62, 126, 160)
ORANGE = (255, 148, 0)
YELLOW = (231, 226, 71)
RED = (214, 59, 80)
GREEN = (105, 143, 63)
PINK = (219, 90, 186)
GRAY = (145, 147, 147)
BLACK = (0, 0, 0)

# Role aliases used by the sims.
CREATURE = BLUE
FOOD = GREEN
DOVE = BLUE
HAWK = RED
ROCK = RED
PAPER = BLUE
SCISSORS = YELLOW

STRATEGY_COLORS = (ROCK, PAPER, SCISSORS)


def mix_colors(a, b, t):
    """Blend a -> b. t is clamped to [0, 1]. Primer mixes dove/hawk by fight_chance."""
    t = min(1.0, max(0.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def mix_by_weight(colors, weights):
    """Weighted blend, for blobs carrying several alleles. Falls back to GRAY if weightless."""
    total = sum(weights)
    if total <= 0:
        return GRAY
    return tuple(
        round(sum(c[i] * w for c, w in zip(colors, weights)) / total) for i in range(3)
    )


def to_mpl(color):
    """(0-255) tuple -> matplotlib 0-1 float tuple."""
    return tuple(c / 255 for c in color)
