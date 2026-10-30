"""
Save and load the best score on this computer.

Scores are stored in a small JSON file next to the game so they
survive closing the window. If the file is missing or damaged,
we simply start from zero instead of crashing.
"""

from __future__ import annotations

import json
import os

from .settings import HIGHSCORE_FILE


def load_highscore() -> int:
    """Return the saved high score, or 0 if none exists yet."""
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return int(data.get("highscore", 0))
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return 0


def save_highscore(score: int) -> int:
    """
    Keep the high score if this run beat it.

    Returns the (possibly updated) high score so the UI can show it.
    """
    current = load_highscore()
    best = max(current, int(score))
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as file:
            json.dump({"highscore": best}, file, indent=2)
    except OSError:
        # Saving is nice-to-have; never block gameplay if the disk fails.
        pass
    return best
