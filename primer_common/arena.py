"""Pygame window: the blob arena on top, the play-by-play feed underneath.

Primer's blobs are Blender metaballs with a squash-and-scoop eat animation. We
approximate that with soft-edged circles that squash when eating -- close enough
to read as his creatures without a 3D pipeline.
"""

import math

import pygame

from . import palette
from .feed import Feed

# Primer's per-phase animation durations, in seconds (DEFAULT_ANIM_DURATIONS).
PHASES = (("dawn", 0.5), ("morning", 0.25), ("day", 4.0), ("evening", 0.25), ("night", 0.5))

# Playback speed range. Purely a rendering concern -- speed multiplies how many
# sim steps (spatial) or how much phase time (non-spatial) a frame advances; it
# never touches a rule. Log scale so the slider gives fine control at 1x and
# still reaches the 100x fast-forward the long runs want.
SPEED_MIN = 0.125
SPEED_MAX = 100.0


def ease(t):
    """Smoothstep. Primer's movements accelerate and settle rather than snap."""
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class Arena:
    """Owns the window, the world->screen transform, and the frame loop.

    The sims drive this by calling begin_frame / draw_* / end_frame each frame.
    """

    def __init__(self, title, world_extent=150, size=(900, 900), feed_height=260, fps=60):
        pygame.init()
        pygame.display.set_caption(title)
        self.surface = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.world_extent = world_extent

        self.arena_rect = pygame.Rect(0, 0, size[0], size[1] - feed_height)
        self.feed_rect = pygame.Rect(0, size[1] - feed_height, size[0], feed_height)

        # The world->screen transform is fixed once the window exists, so cache
        # the scale and centre instead of recomputing min()/division per blob
        # per frame (to_screen is called for every food and creature each frame).
        side = min(self.arena_rect.width, self.arena_rect.height) - 24 * 2
        self._scale = side / (world_extent * 2)
        self._cx = self.arena_rect.centerx
        self._cy = self.arena_rect.centery

        # Halo surfaces depend only on (width, height, colour); allocating one
        # per blob per frame was the dominant per-frame cost. Cache and reuse.
        self._halo_cache = {}

        self.font = pygame.font.SysFont("menlo,dejavusansmono,monospace", 12)
        self.title_font = pygame.font.SysFont("helvetica,arial,sans-serif", 16)
        self.feed = Feed(self.font)

        self.running = True
        self.paused = False
        self.speed = 1.0
        self._pad = 24
        self._dragging_speed = False

    # -- transform ---------------------------------------------------------
    def to_screen(self, pos):
        """World (-extent..extent) -> screen pixels, preserving aspect."""
        return (self._cx + pos[0] * self._scale, self._cy - pos[1] * self._scale)

    def scale_len(self, length):
        return length * self._scale

    # -- speed slider ------------------------------------------------------
    def _slider_geom(self):
        """Track endpoints (x0, x1) and centre y for the speed slider, in the
        arena's top-right corner clear of the top-left HUD text."""
        y = self.arena_rect.top + 26
        x1 = self.arena_rect.right - 20
        x0 = x1 - 160
        return x0, x1, y

    def _speed_to_frac(self, speed):
        return math.log(speed / SPEED_MIN) / math.log(SPEED_MAX / SPEED_MIN)

    def _frac_to_speed(self, frac):
        frac = min(1.0, max(0.0, frac))
        return SPEED_MIN * (SPEED_MAX / SPEED_MIN) ** frac

    def _slider_hit(self, pos):
        """Is a click near the slider track? A generous vertical band so the
        thin track is easy to grab."""
        x0, x1, y = self._slider_geom()
        return x0 - 10 <= pos[0] <= x1 + 10 and y - 12 <= pos[1] <= y + 12

    def _set_speed_from_x(self, x):
        x0, x1, _ = self._slider_geom()
        self.speed = self._frac_to_speed((x - x0) / (x1 - x0))

    # -- loop --------------------------------------------------------------
    def pump(self):
        """Handle input. Space pauses, +/- or the slider changes speed, q/esc quits."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.speed = min(SPEED_MAX, self.speed * 2)
                elif event.key == pygame.K_MINUS:
                    self.speed = max(SPEED_MIN, self.speed / 2)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._slider_hit(event.pos):
                    self._dragging_speed = True
                    self._set_speed_from_x(event.pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging_speed = False
            elif event.type == pygame.MOUSEMOTION and self._dragging_speed:
                self._set_speed_from_x(event.pos[0])
        return self.running

    def begin_frame(self):
        self.surface.fill(palette.BG)

    def end_frame(self, log, hud=""):
        self.feed.draw(self.surface, self.feed_rect, log)
        if hud:
            text = f"{hud}   [{'PAUSED' if self.paused else 'space=pause'}]"
            self.surface.blit(
                self.title_font.render(text, True, palette.TEXT),
                (self.arena_rect.left + 12, self.arena_rect.top + 8),
            )
        self.draw_speed_slider()
        pygame.display.flip()
        return self.clock.tick(self.fps) / 1000.0

    def draw_speed_slider(self):
        """A draggable log-scale speed control in the arena's top-right corner."""
        x0, x1, y = self._slider_geom()
        frac = self._speed_to_frac(self.speed)
        hx = int(x0 + (x1 - x0) * frac)

        # Track: dim behind the handle, bright up to it, so fill reads as level.
        pygame.draw.line(self.surface, palette.GRAY, (x0, y), (x1, y), 2)
        pygame.draw.line(self.surface, palette.TEXT, (x0, y), (hx, y), 2)
        pygame.draw.circle(self.surface, palette.TEXT, (hx, y), 6)

        # Value sits left of the track (right of it would run off the window),
        # right-aligned so the digits don't jitter as the speed changes width.
        label = self.title_font.render(f"{self.speed:g}x speed", True, palette.TEXT)
        self.surface.blit(label, (x0 - 10 - label.get_width(), y - label.get_height() // 2))

    def quit(self):
        pygame.quit()

    # -- drawing -----------------------------------------------------------
    def draw_bounds(self):
        """The world edge. In natural selection this is 'home' -- worth seeing."""
        tl = self.to_screen((-self.world_extent, self.world_extent))
        br = self.to_screen((self.world_extent, -self.world_extent))
        rect = pygame.Rect(tl[0], tl[1], br[0] - tl[0], br[1] - tl[1])
        pygame.draw.rect(self.surface, palette.GRAY, rect, 1)

    def draw_food(self, pos, radius=3.0, color=palette.FOOD):
        x, y = self.to_screen(pos)
        r = max(2, self.scale_len(radius))
        pygame.draw.circle(self.surface, color, (int(x), int(y)), int(r))

    def draw_blob(self, pos, size=1.0, color=palette.CREATURE, squash=0.0, label=None):
        """A blob. `squash` in [0,1] flattens it, echoing Primer's eat animation."""
        x, y = self.to_screen(pos)
        r = max(3.0, self.scale_len(5.0 * size))
        rx = r * (1 + 0.35 * squash)
        ry = r * (1 - 0.35 * squash)

        # Soft halo, then the body -- reads closer to a metaball than a hard disc.
        # The halo bitmap depends only on its pixel size and colour, so build it
        # once per (w, h, colour) and reuse; allocating + drawing a fresh
        # SRCALPHA surface per blob per frame was the top per-frame cost.
        hw, hh = int(rx * 4), int(ry * 4)
        if hw > 0 and hh > 0:
            key = (hw, hh, color)
            halo = self._halo_cache.get(key)
            if halo is None:
                halo = pygame.Surface((hw, hh), pygame.SRCALPHA)
                pygame.draw.ellipse(halo, (*color, 60), halo.get_rect())
                self._halo_cache[key] = halo
            self.surface.blit(halo, (x - rx * 2, y - ry * 2))

        rect = pygame.Rect(0, 0, int(rx * 2), int(ry * 2))
        rect.center = (int(x), int(y + ry * 0.35 * squash))
        pygame.draw.ellipse(self.surface, color, rect)

        if label:
            self.surface.blit(
                self.font.render(label, True, palette.TEXT), (x + rx + 2, y - ry)
            )


class Walker:
    """Tweens a blob between points across a day's phases.

    Hawk/dove and RPS have no real spatial world -- Primer animates blobs walking
    out to a bush/tree, meeting, resolving, then walking home. This drives that.
    """

    def __init__(self, home, target):
        self.home = home
        self.target = target
        self.squash = 0.0

    def position(self, phase, t):
        if phase == "dawn":
            return self.home
        if phase == "morning":
            return self.home
        if phase == "day":
            # out for the first half, resolve, then home for the second half
            if t < 0.45:
                return lerp(self.home, self.target, ease(t / 0.45))
            if t < 0.6:
                return self.target
            return lerp(self.target, self.home, ease((t - 0.6) / 0.4))
        return self.home

    def eating(self, phase, t):
        return phase == "day" and 0.45 <= t < 0.6


def ring_positions(count, radius, jitter=0.0, rng=None):
    """Evenly spaced points on a circle -- Primer's creature home positions."""
    out = []
    for i in range(max(1, count)):
        angle = 2 * math.pi * i / max(1, count)
        r = radius
        if jitter and rng:
            r += rng.uniform(-jitter, jitter)
        out.append((math.cos(angle) * r, math.sin(angle) * r))
    return out
