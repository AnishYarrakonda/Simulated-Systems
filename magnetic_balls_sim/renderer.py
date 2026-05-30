"""Pygame rendering for the sim canvas.

Balls are drawn by blitting pre-rendered, anti-aliased sprites from a hue
cache rather than calling gfxdraw per ball every frame. Blitting ~1000 small
surfaces is dramatically faster than 2000 gfxdraw calls, which is what keeps
the high ball counts smooth.
"""

import colorsys

import pygame
from pygame import gfxdraw

import config

N_HUE = 256  # number of cached hue sprites around the wheel

_sprite_cache = None
_cache_radius = None


def hue_to_rgb(h: float):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def _build_sprite(rgb, radius):
    pad = 1
    size = 2 * (radius + pad) + 1
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + pad
    gfxdraw.filled_circle(surf, c, c, radius, rgb)
    gfxdraw.aacircle(surf, c, c, radius, rgb)
    return surf


def _ensure_cache(radius):
    global _sprite_cache, _cache_radius
    if _sprite_cache is not None and _cache_radius == radius:
        return
    _sprite_cache = [
        _build_sprite(hue_to_rgb(i / N_HUE), radius) for i in range(N_HUE)
    ]
    _cache_radius = radius


def draw(screen, simulation, font, fps):
    box_rect = pygame.Rect(
        simulation.box_x,
        simulation.box_y,
        simulation.box_size,
        simulation.box_size,
    )
    pygame.draw.rect(screen, config.BG_COLOR, box_rect)
    pygame.draw.rect(screen, config.BORDER_COLOR, box_rect, config.BORDER_WIDTH)

    radius = int(simulation.radius)
    _ensure_cache(radius)
    offset = radius + 1  # top-left of each sprite relative to its center

    px = simulation.px
    py = simulation.py
    hue = simulation.hue
    cache = _sprite_cache
    blit = screen.blit
    for i in range(px.shape[0]):
        idx = int(hue[i] * N_HUE) % N_HUE
        blit(cache[idx], (int(px[i]) - offset, int(py[i]) - offset))

    overlay = f"Balls: {simulation.count()}    FPS: {fps:.0f}"
    text_surface = font.render(overlay, True, (225, 225, 230))
    screen.blit(text_surface, (simulation.box_x + 10, simulation.box_y + 8))

    if simulation.paused:
        paused_surface = font.render("PAUSED", True, (255, 180, 80))
        screen.blit(
            paused_surface,
            (
                simulation.box_x + simulation.box_size - paused_surface.get_width() - 12,
                simulation.box_y + 8,
            ),
        )
