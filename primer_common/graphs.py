"""Live matplotlib graphs, styled after Primer's.

Primer renders his graphs as 3D objects inside Blender; we can't reproduce that
exactly, so these are flat matplotlib equivalents that keep his palette, his axis
labels ("Days" / "N" / "Creatures"), and his choice of chart per sim.
"""

import math

import matplotlib.pyplot as plt
import numpy as np

from . import palette

BG = palette.to_mpl(palette.BG)
FG = palette.to_mpl(palette.TEXT)


def _style(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(BG)
    ax.set_title(title, color=FG)
    ax.set_xlabel(xlabel, color=FG)
    ax.set_ylabel(ylabel, color=FG)
    ax.tick_params(colors=FG)
    for spine in ax.spines.values():
        spine.set_color(FG)
    return ax


def new_figure(title, figsize=(11, 7)):
    fig = plt.figure(figsize=figsize, facecolor=BG)
    fig.canvas.manager.set_window_title(title)
    return fig


def draw():
    """Pump the matplotlib event loop without blocking the pygame window."""
    plt.pause(0.001)


def show():
    plt.show()


class LineGraph:
    """Population-style line chart. Primer: x='Days', y='N' or 'Creatures'."""

    def __init__(self, ax, series, title="", xlabel="Days", ylabel="N"):
        _style(ax, title, xlabel, ylabel)
        self.ax = ax
        self.lines = {}
        for name, color in series.items():
            (line,) = ax.plot([], [], label=name, color=palette.to_mpl(color), lw=2)
            self.lines[name] = line
        legend = ax.legend(loc="upper right", facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

    def update(self, days, values):
        top = 1
        for name, line in self.lines.items():
            ys = values.get(name, [])
            line.set_data(days[: len(ys)], ys)
            if ys:
                top = max(top, max(ys))
        self.ax.set_xlim(0, max(10, len(days)))
        self.ax.set_ylim(0, top * 1.15 + 1)


class Histogram:
    """Bar histogram. Primer's speed chart bins 0.0-2.2 by 0.1 with dx=0.08."""

    def __init__(self, ax, bins, title="", xlabel="", ylabel="N", colors=None, width=0.08):
        _style(ax, title, xlabel, ylabel)
        self.ax = ax
        self.bins = list(bins)
        colors = colors or [palette.to_mpl(palette.CREATURE)] * len(self.bins)
        self.bars = ax.bar(self.bins, [0] * len(self.bins), width=width, color=colors)
        ax.set_xlim(min(self.bins) - 0.1, max(self.bins) + 0.1)

    def update(self, counts):
        top = 1
        for bar, b in zip(self.bars, self.bins):
            h = counts.get(b, 0)
            bar.set_height(h)
            top = max(top, h)
        self.ax.set_ylim(0, top * 1.15 + 1)


class BarChart:
    """Fixed-category bar chart. RPS uses this with values shown as percentages."""

    def __init__(self, ax, categories, colors, title="", ylabel="%", ymax=100):
        _style(ax, title, "", ylabel)
        self.ax = ax
        self.categories = list(categories)
        xs = range(1, len(self.categories) + 1)
        self.bars = ax.bar(xs, [0] * len(self.categories),
                           color=[palette.to_mpl(c) for c in colors], width=0.6)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(self.categories, color=FG)
        ax.set_ylim(0, ymax)

    def update(self, values):
        for bar, cat in zip(self.bars, self.categories):
            bar.set_height(values.get(cat, 0))


class Scatter3D:
    """Trait cloud. Primer: x=Size, y=Sense, z=Speed, each axis 0-2."""

    def __init__(self, ax, title="", labels=("Size", "Sense", "Speed"), rng=(0, 2)):
        self.ax = ax
        self.labels = labels
        self.rng = rng
        self._reset(title)

    def _reset(self, title=""):
        ax = self.ax
        ax.set_facecolor(BG)
        # 3D panes ignore set_facecolor, so they'd stay light against the dark theme.
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_pane_color((*BG, 1.0))
            axis._axinfo["grid"]["color"] = (*FG, 0.15)
        ax.set_title(title or "Traits", color=FG)
        ax.set_xlabel(self.labels[0], color=FG)
        ax.set_ylabel(self.labels[1], color=FG)
        ax.set_zlabel(self.labels[2], color=FG)
        ax.set_xlim(*self.rng)
        ax.set_ylim(*self.rng)
        ax.set_zlim(*self.rng)
        ax.tick_params(colors=FG)

    def update(self, xs, ys, zs):
        self.ax.cla()
        self._reset()
        self.ax.scatter(xs, ys, zs, c=[palette.to_mpl(palette.CREATURE)], s=14, alpha=0.7)


class TernaryPlot:
    """Simplex plot -- the centrepiece of Primer's RPS video.

    A composition (r, p, s) summing to 1 maps onto a triangle, so the whole state
    of the population is one point. The RPS cycle then shows up directly as an
    orbit: a closed loop when tie_cost=0, an outward spiral when tie_cost>0.
    """

    CORNERS = np.array([[0.5, math.sqrt(3) / 2], [0.0, 0.0], [1.0, 0.0]])  # R, P, S

    def __init__(self, ax, title="", labels=("Rock", "Paper", "Scissors"),
                 colors=palette.STRATEGY_COLORS, trail=True):
        self.ax = ax
        self.trail = trail
        ax.set_facecolor(BG)
        ax.set_title(title, color=FG)
        ax.set_aspect("equal")
        ax.axis("off")

        outline = np.vstack([self.CORNERS, self.CORNERS[:1]])
        ax.plot(outline[:, 0], outline[:, 1], color=FG, lw=1.5)

        for i in range(1, 5):  # faint interior gridlines, every 20%
            t = i / 5
            for a, b in ((0, 1), (1, 2), (2, 0)):
                p1 = self.CORNERS[a] + (self.CORNERS[b] - self.CORNERS[a]) * t
                p2 = self.CORNERS[a] + (self.CORNERS[(a + 2) % 3] - self.CORNERS[a]) * t
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=FG, lw=0.4, alpha=0.18)

        offsets = ((0, 0.04), (-0.05, -0.04), (0.05, -0.04))
        for corner, label, color, (dx, dy) in zip(self.CORNERS, labels, colors, offsets):
            ax.text(corner[0] + dx, corner[1] + dy, label, color=palette.to_mpl(color),
                    ha="center", va="center", fontsize=11)

        centre = self.project(1 / 3, 1 / 3, 1 / 3)
        ax.plot(*centre, marker="+", color=FG, ms=9, alpha=0.5)  # (1/3,1/3,1/3) equilibrium

        (self.path,) = ax.plot([], [], color=palette.to_mpl(palette.TEXT), lw=1.2, alpha=0.65)
        (self.head,) = ax.plot([], [], marker="o", ms=7,
                               color=palette.to_mpl(palette.ORANGE), lw=0)
        self.xs, self.ys = [], []
        ax.set_xlim(-0.12, 1.12)
        ax.set_ylim(-0.12, 1.0)

    @classmethod
    def project(cls, r, p, s):
        total = r + p + s
        if total <= 0:
            return (0.5, math.sqrt(3) / 6)
        v = (cls.CORNERS[0] * r + cls.CORNERS[1] * p + cls.CORNERS[2] * s) / total
        return (v[0], v[1])

    def update(self, r, p, s):
        x, y = self.project(r, p, s)
        if self.trail:
            self.xs.append(x)
            self.ys.append(y)
            self.path.set_data(self.xs, self.ys)
        self.head.set_data([x], [y])
