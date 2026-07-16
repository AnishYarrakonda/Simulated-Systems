"""Play-by-play panel: a scrolling feed of events plus the per-day summary."""

import pygame

from . import palette
from .events import DaySummary


class Feed:
    """Renders the tail of an EventLog into a rect, newest at the bottom."""

    def __init__(self, font, line_height=15, max_lines=None):
        self.font = font
        self.line_height = line_height
        self.max_lines = max_lines

    def draw(self, surface, rect, log):
        pygame.draw.rect(surface, palette.BG, rect)
        pygame.draw.line(surface, palette.GRAY, rect.topleft, rect.topright, 1)

        capacity = self.max_lines or max(1, (rect.height - 8) // self.line_height)

        lines = []
        for event in log.events:
            for part in event.line().split("\n"):
                lines.append((part, isinstance(event, DaySummary)))
        lines = lines[-capacity:]

        y = rect.top + 6
        for text, is_summary in lines:
            color = palette.TEXT if is_summary else palette.GRAY
            surface.blit(self.font.render(text, True, color), (rect.left + 10, y))
            y += self.line_height
