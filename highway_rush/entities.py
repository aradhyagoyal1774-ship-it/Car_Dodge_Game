"""Moving objects: the player car, oncoming traffic, hazards, and crash sparks."""

from __future__ import annotations

import math
import random

import pygame

from . import settings as S
from .assets import make_car, make_obstacle


class Player:
    def __init__(self, image: pygame.Surface, speed: float):
        self.image = image
        self.speed = speed
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self) -> None:
        self.rect.centerx = S.lane_center_x(1)
        self.rect.bottom = S.HEIGHT - 36
        self.alive = True

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        dx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        self.rect.x += int(dx)

        # Stay on the asphalt, not in the grass
        min_x = S.ROAD_LEFT + 6
        max_x = S.ROAD_LEFT + S.ROAD_WIDTH - self.rect.width - 6
        self.rect.x = max(min_x, min(max_x, self.rect.x))

    def hitbox(self) -> pygame.Rect:
        """A slightly smaller box so grazing a bumper is not an instant crash."""
        return self.rect.inflate(-12, -16)

    def draw(self, surface: pygame.Surface, glow: pygame.Surface | None = None) -> None:
        if glow:
            g_rect = glow.get_rect(center=self.rect.center)
            surface.blit(glow, g_rect, special_flags=pygame.BLEND_ADD)
        surface.blit(self.image, self.rect)


class Enemy:
    def __init__(self, lane: int, speed: float):
        body, accent = random.choice(S.ENEMY_PALETTE)
        self.image = make_car(S.ENEMY_SIZE, body, accent, facing_up=False)
        self.rect = self.image.get_rect()
        self.rect.centerx = S.lane_center_x(lane)
        self.rect.bottom = -8
        self.speed = speed
        self.lane = lane
        self.counted = False  # becomes True after we award avoid points

    def update(self) -> None:
        self.rect.y += int(self.speed)

    def offscreen(self) -> bool:
        return self.rect.top > S.HEIGHT + 10

    def passed_player(self, player: Player) -> bool:
        return (not self.counted) and self.rect.top > player.rect.bottom

    def hitbox(self) -> pygame.Rect:
        return self.rect.inflate(-10, -14)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)


class Obstacle:
    """A barrel / cone that occupies one lane and must be dodged."""

    def __init__(self, lane: int, speed: float):
        self.image = make_obstacle()
        self.rect = self.image.get_rect()
        self.rect.centerx = S.lane_center_x(lane)
        self.rect.bottom = -8
        self.speed = speed
        self.counted = False

    def update(self) -> None:
        self.rect.y += int(self.speed)

    def offscreen(self) -> bool:
        return self.rect.top > S.HEIGHT + 10

    def passed_player(self, player: Player) -> bool:
        return (not self.counted) and self.rect.top > player.rect.bottom

    def hitbox(self) -> pygame.Rect:
        return self.rect.inflate(-6, -6)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)


class Particle:
    def __init__(self, pos: tuple[int, int]):
        self.x, self.y = float(pos[0]), float(pos[1])
        angle = random.uniform(0, 6.283)
        power = random.uniform(2.0, 7.5)
        self.vx = math.cos(angle) * power
        self.vy = math.sin(angle) * power
        self.life = random.randint(22, 40)
        self.color = random.choice([S.NEON_CYAN, S.NEON_MAGENTA, S.NEON_YELLOW, (255, 120, 60)])
        self.size = random.randint(2, 5)

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.life -= 1

    def draw(self, surface: pygame.Surface) -> None:
        if self.life > 0:
            pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.size, self.size))
