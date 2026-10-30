"""
All pictures and sounds are built in code.

That means the game runs without extra image or audio files.
Cars, the road glow, buttons, and tiny arcade beeps are generated
with Pygame drawing calls and simple sine-wave samples.
"""

from __future__ import annotations

import array
import math
import random

import pygame

from . import settings as S


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
def make_fonts() -> dict:
    """Pick a clean system font, then fall back if it is missing."""
    preferred = ["Segoe UI", "Arial", "Calibri", "Verdana"]
    name = None
    available = pygame.font.get_fonts()
    for candidate in preferred:
        if candidate.replace(" ", "").lower() in available:
            name = candidate
            break

    def font(size: int, bold: bool = False) -> pygame.font.Font:
        if name:
            return pygame.font.SysFont(name, size, bold=bold)
        return pygame.font.Font(None, size)

    return {
        "title": font(54, True),
        "subtitle": font(22, False),
        "button": font(26, True),
        "hud": font(22, True),
        "body": font(20, False),
        "small": font(16, False),
        "huge": font(40, True),
    }


# ---------------------------------------------------------------------------
# Glow helpers
# ---------------------------------------------------------------------------
def glow_circle(radius: int, color: tuple[int, int, int], layers: int = 5) -> pygame.Surface:
    """Soft neon blob used for headlights and lamp posts."""
    size = radius * 2 + 8
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    r, g, b = color
    for i in range(layers, 0, -1):
        alpha = int(28 + 40 * (i / layers))
        rad = int(radius * i / layers)
        pygame.draw.circle(surf, (r, g, b, alpha), (cx, cy), rad)
    pygame.draw.circle(surf, (min(255, r + 40), min(255, g + 40), min(255, b + 40), 220), (cx, cy), max(2, radius // 4))
    return surf


def rounded_rect(surface: pygame.Surface, color, rect, radius: int) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ---------------------------------------------------------------------------
# Vehicle art
# ---------------------------------------------------------------------------
def make_car(size: tuple[int, int], body: tuple[int, int, int], accent: tuple[int, int, int], facing_up: bool) -> pygame.Surface:
    """Draw a stylized top-down sports car. facing_up=True for the player."""
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Drop shadow
    pygame.draw.ellipse(surf, (0, 0, 0, 90), (4, h - 16, w - 8, 14))

    body_rect = pygame.Rect(6, 8, w - 12, h - 18)
    rounded_rect(surf, body, body_rect, 12)

    # Slightly darker roof
    roof = pygame.Rect(12, 22, w - 24, h - 46)
    roof_color = tuple(max(0, c - 35) for c in body)
    rounded_rect(surf, roof_color, roof, 8)

    # Windows
    glass = (40, 70, 110, 210)
    if facing_up:
        pygame.draw.polygon(surf, glass, [(14, 30), (w // 2, 14), (w - 14, 30), (w - 16, 42), (16, 42)])
        pygame.draw.rect(surf, glass, (14, h - 36, w - 28, 14), border_radius=4)
        # Headlights (top)
        pygame.draw.ellipse(surf, (255, 255, 210), (10, 10, 14, 10))
        pygame.draw.ellipse(surf, (255, 255, 210), (w - 24, 10, 14, 10))
        # Taillights (bottom)
        pygame.draw.rect(surf, (255, 50, 70), (10, h - 18, 14, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 50, 70), (w - 24, h - 18, 14, 6), border_radius=2)
    else:
        pygame.draw.polygon(surf, glass, [(14, h - 30), (w // 2, h - 14), (w - 14, h - 30), (w - 16, h - 42), (16, h - 42)])
        pygame.draw.rect(surf, glass, (14, 22, w - 28, 14), border_radius=4)
        pygame.draw.ellipse(surf, (255, 255, 210), (10, h - 20, 14, 10))
        pygame.draw.ellipse(surf, (255, 255, 210), (w - 24, h - 20, 14, 10))
        pygame.draw.rect(surf, (255, 50, 70), (10, 12, 14, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 50, 70), (w - 24, 12, 14, 6), border_radius=2)

    # Accent stripe
    stripe = pygame.Rect(w // 2 - 4, 24, 8, h - 48)
    rounded_rect(surf, accent, stripe, 3)

    # Side mirrors
    pygame.draw.rect(surf, body, (1, h // 2 - 8, 8, 10), border_radius=3)
    pygame.draw.rect(surf, body, (w - 9, h // 2 - 8, 8, 10), border_radius=3)

    return surf


def make_obstacle() -> pygame.Surface:
    """Traffic barrier / cone cluster drawn as a neon hazard."""
    w, h = S.OBSTACLE_SIZE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 20, 24, 80), (2, h - 10, w - 4, 8), border_radius=3)

    # Striped barrel
    pygame.draw.rect(surf, (255, 150, 20), (8, 4, w - 16, h - 10), border_radius=6)
    for i in range(3):
        y = 8 + i * 8
        pygame.draw.rect(surf, (30, 30, 36), (8, y, w - 16, 4))
    pygame.draw.rect(surf, (255, 230, 80), (8, 4, w - 16, h - 10), 2, border_radius=6)
    return surf


def make_player_glow() -> pygame.Surface:
    return glow_circle(28, S.NEON_CYAN, layers=6)


# ---------------------------------------------------------------------------
# Sound (tiny arcade beeps, no audio files needed)
# ---------------------------------------------------------------------------
def _sine_samples(freq: float, duration: float, volume: float = 0.28, sample_rate: int = 22050, decay: bool = True) -> array.array:
    n = max(1, int(sample_rate * duration))
    samples = array.array("h")
    for i in range(n):
        t = i / sample_rate
        envelope = 1.0
        if decay:
            envelope = max(0.0, 1.0 - t / duration)
            # Short attack so the click is not too harsh
            attack = min(1.0, i / 180)
            envelope *= attack
        value = int(volume * envelope * 32767 * math.sin(2 * math.pi * freq * t))
        samples.append(value)
    return samples


def _noise_crash(duration: float = 0.35, sample_rate: int = 22050) -> array.array:
    n = int(sample_rate * duration)
    samples = array.array("h")
    for i in range(n):
        t = i / sample_rate
        env = max(0.0, 1.0 - t / duration) ** 2
        rumble = math.sin(2 * math.pi * 70 * t) * 0.4
        hiss = (random.random() * 2 - 1) * 0.6
        value = int(0.45 * env * 32767 * (rumble + hiss))
        samples.append(max(-32767, min(32767, value)))
    return samples


def make_sounds() -> dict:
    """Build a small sound bank. Mixer must already be initialized."""
    click = pygame.mixer.Sound(buffer=_sine_samples(880, 0.07, 0.22))
    score = pygame.mixer.Sound(buffer=_sine_samples(660, 0.09, 0.18))
    score_hi = pygame.mixer.Sound(buffer=_sine_samples(990, 0.08, 0.16))
    crash = pygame.mixer.Sound(buffer=_noise_crash())
    start = pygame.mixer.Sound(buffer=_sine_samples(523.25, 0.16, 0.22))
    return {
        "click": click,
        "score": score,
        "score_hi": score_hi,
        "crash": crash,
        "start": start,
    }
