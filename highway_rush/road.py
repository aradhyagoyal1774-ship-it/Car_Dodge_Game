"""Scrolling night highway: asphalt, neon dashes, lamps, and side scenery."""

from __future__ import annotations

import random

import pygame

from . import settings as S


class Highway:
    """
    The road does not actually move the world.

    Instead we slide dashed lines and lamps downward every frame.
    That cheap trick makes it look like the player is racing forward.
    """

    def __init__(self):
        self.dash_offset = 0.0
        self.lamp_offset = 0.0
        self.stars = [
            (random.randint(0, S.WIDTH), random.randint(0, S.HEIGHT), random.randint(1, 2), random.randint(80, 180))
            for _ in range(50)
        ]
        # Distant city windows on the left and right shoulders
        self.windows = []
        for _ in range(40):
            side = random.choice([-1, 1])
            if side < 0:
                x = random.randint(8, S.ROAD_LEFT - 18)
            else:
                x = random.randint(S.ROAD_LEFT + S.ROAD_WIDTH + 10, S.WIDTH - 10)
            y = random.randint(0, S.HEIGHT)
            self.windows.append((x, y, random.choice([(255, 210, 90), (180, 220, 255), (255, 140, 80)])))

    def update(self, speed: float) -> None:
        self.dash_offset = (self.dash_offset + speed) % 52
        self.lamp_offset = (self.lamp_offset + speed) % 220
        moved = []
        for x, y, color in self.windows:
            y += speed * 0.25
            if y > S.HEIGHT:
                y = -10
            moved.append((x, y, color))
        self.windows = moved

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(S.NIGHT)

        # Night sky gradient
        for y in range(0, S.HEIGHT, 8):
            shade = int(6 + 10 * (y / S.HEIGHT))
            pygame.draw.rect(surface, (shade, shade + 2, 18 + shade), (0, y, S.WIDTH, 8))

        for x, y, size, alpha in self.stars:
            pygame.draw.circle(surface, (alpha, alpha, min(255, alpha + 30)), (x, y), size)

        for x, y, color in self.windows:
            pygame.draw.rect(surface, color, (x, int(y), 4, 6))

        # Shoulders / rumble
        pygame.draw.rect(surface, (22, 18, 16), (0, 0, S.ROAD_LEFT, S.HEIGHT))
        pygame.draw.rect(surface, (22, 18, 16), (S.ROAD_LEFT + S.ROAD_WIDTH, 0, S.WIDTH, S.HEIGHT))

        # Asphalt
        pygame.draw.rect(surface, S.ASPHALT, (S.ROAD_LEFT, 0, S.ROAD_WIDTH, S.HEIGHT))

        # Edge neon glow
        pygame.draw.rect(surface, S.LANE_NEON, (S.ROAD_LEFT - 4, 0, 4, S.HEIGHT))
        pygame.draw.rect(surface, S.NEON_MAGENTA, (S.ROAD_LEFT + S.ROAD_WIDTH, 0, 4, S.HEIGHT))

        # Inner lane dashes
        dash_h = 28
        gap = 24
        period = dash_h + gap
        for lane in range(1, S.LANE_COUNT):
            x = S.ROAD_LEFT + lane * S.LANE_WIDTH
            y = -period + (self.dash_offset % period)
            while y < S.HEIGHT:
                pygame.draw.rect(surface, S.LANE_NEON, (x - 2, int(y), 4, dash_h), border_radius=2)
                y += period

        # Center faint highlight
        highlight = pygame.Surface((S.ROAD_WIDTH, S.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(highlight, (255, 255, 255, 8), highlight.get_rect())
        surface.blit(highlight, (S.ROAD_LEFT, 0))

        # Street lamps
        self._draw_lamps(surface)

    def _draw_lamps(self, surface: pygame.Surface) -> None:
        y = -40 + (self.lamp_offset % 220)
        while y < S.HEIGHT + 40:
            for x in (S.ROAD_LEFT - 22, S.ROAD_LEFT + S.ROAD_WIDTH + 22):
                pygame.draw.rect(surface, (50, 55, 70), (x - 3, int(y), 6, 70))
                glow = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 220, 120, 50), (35, 18), 22)
                pygame.draw.circle(glow, (255, 240, 180, 140), (35, 18), 7)
                surface.blit(glow, (x - 35, int(y) - 18))
            y += 220
