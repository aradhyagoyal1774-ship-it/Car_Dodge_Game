"""
Game-wide constants.

Keeping numbers in one file makes it easy to tune difficulty,
colors, and layout without hunting through the rest of the code.
"""

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WIDTH = 540
HEIGHT = 800
FPS = 60
TITLE = "HIGHWAY RUSH"

# ---------------------------------------------------------------------------
# Road / lanes  (three lanes in the middle of the screen)
# ---------------------------------------------------------------------------
ROAD_LEFT = 90
ROAD_WIDTH = 360
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT  # 120 px


def lane_center_x(lane_index: int) -> int:
    """Return the horizontal center of a lane (0, 1, or 2)."""
    return ROAD_LEFT + lane_index * LANE_WIDTH + LANE_WIDTH // 2


# ---------------------------------------------------------------------------
# Arcade neon palette
# ---------------------------------------------------------------------------
BLACK = (0, 0, 0)
WHITE = (240, 246, 255)
NIGHT = (6, 8, 18)
ASPHALT = (28, 32, 44)
ASPHALT_EDGE = (18, 20, 30)
LANE_NEON = (80, 230, 255)
NEON_CYAN = (0, 230, 255)
NEON_MAGENTA = (255, 50, 180)
NEON_YELLOW = (255, 220, 70)
NEON_GREEN = (80, 255, 160)
HUD_BG = (8, 12, 28, 180)
BUTTON_BG = (16, 22, 48)
BUTTON_HOVER = (28, 40, 80)
BUTTON_BORDER = (0, 220, 255)

PLAYER_COLOR = (0, 210, 255)
PLAYER_ACCENT = (180, 250, 255)

ENEMY_PALETTE = [
    ((230, 60, 70), (255, 180, 160)),     # red
    ((255, 160, 40), (255, 230, 160)),    # orange
    ((120, 80, 255), (200, 190, 255)),    # purple
    ((40, 200, 90), (170, 255, 200)),     # green
    ((255, 70, 160), (255, 190, 220)),    # pink
    ((70, 140, 255), (180, 210, 255)),    # blue
]

OBSTACLE_COLOR = (255, 170, 30)

# ---------------------------------------------------------------------------
# Difficulty presets
# spawn_ms = time between enemy waves
# base_speed = how fast traffic starts
# max_speed = speed cap as the score grows
# gap_lanes = always leave at least this many empty lanes in a wave
# ---------------------------------------------------------------------------
DIFFICULTIES = {
    "Easy": {
        "spawn_ms": 1450,
        "base_speed": 4.2,
        "max_speed": 9.0,
        "speed_per_score": 0.012,
        "two_car_chance": 0.18,
        "obstacle_chance": 0.08,
        "player_speed": 8.0,
    },
    "Medium": {
        "spawn_ms": 1100,
        "base_speed": 5.4,
        "max_speed": 12.5,
        "speed_per_score": 0.016,
        "two_car_chance": 0.38,
        "obstacle_chance": 0.14,
        "player_speed": 8.5,
    },
    "Hard": {
        "spawn_ms": 850,
        "base_speed": 6.6,
        "max_speed": 16.0,
        "speed_per_score": 0.022,
        "two_car_chance": 0.55,
        "obstacle_chance": 0.22,
        "player_speed": 9.2,
    },
}

# Scoring
POINTS_PER_SECOND = 10
POINTS_PER_AVOID = 25
POINTS_PER_OBSTACLE = 15

# Player / enemy sizes
PLAYER_SIZE = (54, 92)
ENEMY_SIZE = (52, 88)
OBSTACLE_SIZE = (44, 36)

HIGHSCORE_FILE = "highscore.json"
