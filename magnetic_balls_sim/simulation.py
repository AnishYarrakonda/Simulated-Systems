"""Simulation: owns the ball state (as numpy arrays) and advances it."""

import math
import random

import numpy as np

import config
import physics
from distributions import sample


class Simulation:
    def __init__(self, box_x: float, box_y: float, box_size: float):
        self.box_x = box_x
        self.box_y = box_y
        self.box_size = box_size

        self.paused = False
        self.n = config.DEFAULT_N
        self.distribution = config.DEFAULT_DISTRIBUTION
        self.params = {
            "mean": config.GAUSS_DEFAULT_MEAN,
            "stddev": config.GAUSS_DEFAULT_STD,
            "center": config.BIMO_DEFAULT_CENTER,
            "bimo_stddev": config.BIMO_DEFAULT_STD,
        }
        self.force_strength = config.DEFAULT_FORCE
        self.radius = config.BALL_RADIUS

        # State arrays (filled by restart()).
        self.px = np.zeros(0)
        self.py = np.zeros(0)
        self.vx = np.zeros(0)
        self.vy = np.zeros(0)
        self.hue = np.zeros(0)

        self.restart()

    # ------------------------------------------------------------------
    def _sampler_params(self) -> dict:
        if self.distribution == "Gaussian":
            return {"mean": self.params["mean"], "stddev": self.params["stddev"]}
        if self.distribution == "Bimodal":
            return {"center": self.params["center"], "stddev": self.params["bimo_stddev"]}
        return {}

    def restart(self):
        hues = sample(self.distribution, self.n, self._sampler_params())
        random.shuffle(hues)

        positions = self._grid_positions(len(hues))
        m = len(positions)
        hues = hues[:m]

        self.px = np.array([p[0] for p in positions], dtype=np.float64)
        self.py = np.array([p[1] for p in positions], dtype=np.float64)
        self.vx = np.zeros(m, dtype=np.float64)
        self.vy = np.zeros(m, dtype=np.float64)
        self.hue = np.array(hues, dtype=np.float64)

    def _grid_positions(self, n: int):
        if n <= 0:
            return []
        cols = max(1, int(math.ceil(math.sqrt(n))))
        rows = max(1, int(math.ceil(n / cols)))
        margin = self.radius * 2.5
        usable = self.box_size - 2.0 * margin
        cell_w = usable / cols
        cell_h = usable / rows
        positions = []
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= n:
                    break
                x = self.box_x + margin + cell_w * (c + 0.5)
                y = self.box_y + margin + cell_h * (r + 0.5)
                positions.append((x, y))
                idx += 1
            if idx >= n:
                break
        return positions

    # ------------------------------------------------------------------
    def step(self, dt: float):
        if self.paused or dt <= 0.0 or self.px.shape[0] == 0:
            return

        physics.apply_forces(
            self.px, self.py, self.vx, self.vy, self.hue,
            self.force_strength, config.SOFTENING, dt,
        )

        # Fixed internal damping keeps the system stable / lets it settle.
        damp = math.exp(-config.DAMPING * dt)
        self.vx *= damp
        self.vy *= damp

        # Speed cap.
        speed = np.hypot(self.vx, self.vy)
        too_fast = speed > config.MAX_SPEED
        if too_fast.any():
            scale = config.MAX_SPEED / speed[too_fast]
            self.vx[too_fast] *= scale
            self.vy[too_fast] *= scale

        self.px += self.vx * dt
        self.py += self.vy * dt

        physics.resolve_walls(
            self.px, self.py, self.vx, self.vy, self.radius,
            self.box_x, self.box_y, self.box_size,
        )
        physics.resolve_collisions(self.px, self.py, self.vx, self.vy, self.radius)

    def count(self) -> int:
        return int(self.px.shape[0])
