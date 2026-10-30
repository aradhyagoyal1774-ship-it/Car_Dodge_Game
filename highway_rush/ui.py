"""Reusable UI pieces: glowing text, arcade buttons, and overlay panels."""

from __future__ import annotations

import pygame

from . import settings as S


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color, center=None, topleft=None, glow=None) -> pygame.Rect:
    """
    Draw text with an optional neon glow.

    glow should be a color tuple if you want a halo, or None for plain text.
    """
    if glow:
        base = font.render(text, True, glow)
        target = center or topleft
        for offset in ((-2, 0), (2, 0), (0, -2), (0, 2), (0, 0)):
            rect = base.get_rect()
            if center:
                rect.center = (center[0] + offset[0], center[1] + offset[1])
            else:
                rect.topleft = (topleft[0] + offset[0], topleft[1] + offset[1])
            faded = base.copy()
            faded.set_alpha(70 if offset != (0, 0) else 160)
            surface.blit(faded, rect)

    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = center
    else:
        rect.topleft = topleft
    surface.blit(label, rect)
    return rect


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Split a paragraph into lines that fit inside max_width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Button:
    """A rounded neon button that knows when the mouse is over it."""

    def __init__(self, text: str, center: tuple[int, int], size=(280, 56), accent=S.NEON_CYAN):
        self.text = text
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.center = center
        self.accent = accent
        self.hovered = False

    def update(self, mouse_pos: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, event: pygame.event.Event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        fill = S.BUTTON_HOVER if self.hovered else S.BUTTON_BG
        pygame.draw.rect(surface, fill, self.rect, border_radius=16)
        border = self.accent if self.hovered else S.BUTTON_BORDER
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=16)
        if self.hovered:
            glow = self.rect.inflate(10, 10)
            pygame.draw.rect(surface, self.accent, glow, width=1, border_radius=18)
        draw_text(surface, self.text, font, S.WHITE, center=self.rect.center)


class Panel:
    """Semi-transparent card used on the menu and game-over screens."""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface) -> None:
        card = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card, (10, 14, 32, 210), card.get_rect(), border_radius=22)
        pygame.draw.rect(card, S.NEON_CYAN, card.get_rect(), width=2, border_radius=22)
        surface.blit(card, self.rect.topleft)
