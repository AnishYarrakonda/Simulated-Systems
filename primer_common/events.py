"""Typed events emitted by the sim cores.

The sim logic stays headless and just appends events to a list; the arena and the
play-by-play feed consume them. This mirrors how Primer splits things -- his sim
files (natural_sim.py, hawk_dove.py, EvoGameTheorySim.cs) render nothing at all,
which is also what makes the rules testable without opening a window.
"""

from dataclasses import dataclass, field


@dataclass
class Event:
    """Base event. `text` is what the play-by-play feed prints."""

    text: str = ""

    def line(self):
        return self.text


@dataclass
class Encounter(Event):
    """Two creatures met at a food source and resolved a contest."""

    a: str = ""
    b: str = ""
    a_score: float = 0.0
    b_score: float = 0.0
    where: int = 0

    def line(self):
        return f"{self.a} vs {self.b} @ {self.where}  ->  {self.a_score:g} / {self.b_score:g}"


@dataclass
class Ate(Event):
    """A creature ate alone (no contest)."""

    who: str = ""
    score: float = 0.0
    where: int = 0

    def line(self):
        return f"{self.who} ate alone @ {self.where}  ->  {self.score:g}"


@dataclass
class Predation(Event):
    predator: str = ""
    prey: str = ""
    predator_size: float = 0.0
    prey_size: float = 0.0

    def line(self):
        return (
            f"{self.prey} eaten by {self.predator} "
            f"(size {self.predator_size:.2f} vs {self.prey_size:.2f})"
        )


@dataclass
class Born(Event):
    who: str = ""
    parent: str = ""

    def line(self):
        return f"{self.who} born from {self.parent}"


@dataclass
class Died(Event):
    who: str = ""
    cause: str = "starved"

    def line(self):
        return f"{self.who} {self.cause}"


@dataclass
class DaySummary(Event):
    day: int = 0
    population: int = 0
    births: int = 0
    deaths: int = 0
    stats: dict = field(default_factory=dict)

    def line(self):
        head = f"-- day {self.day}  pop {self.population}  (+{self.births}/-{self.deaths})"
        if not self.stats:
            return head
        body = "  ".join(f"{k} {v:.2f}" for k, v in self.stats.items())
        return f"{head}\n   {body}"


class EventLog:
    """Collects events for the current day, and keeps a rolling tail for the feed."""

    def __init__(self, tail=400):
        self.tail = tail
        self.events = []
        self.day_events = []

    def emit(self, event):
        self.events.append(event)
        self.day_events.append(event)
        if len(self.events) > self.tail:
            del self.events[: len(self.events) - self.tail]

    def start_day(self):
        self.day_events = []

    def lines(self):
        return [e.line() for e in self.events]
