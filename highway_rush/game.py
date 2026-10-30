"""
Main game controller.

The program is a state machine. One of these screens is active at a time:

    menu -> difficulty -> playing <-> paused
                         playing -> gameover -> menu / playing

That design keeps restart simple: we just call start_run() again and
rebuild the lists of cars, so leftover enemies cannot crash a new game.
"""

from __future__ import annotations

import random
import sys

import pygame

from . import settings as S
from .assets import make_car, make_fonts, make_player_glow, make_sounds
from .entities import Enemy, Obstacle, Particle, Player
from .highscore import load_highscore, save_highscore
from .road import Highway
from .ui import Button, Panel, draw_text, wrap_text

MENU = "menu"
INSTRUCTIONS = "instructions"
DIFFICULTY = "difficulty"
PLAYING = "playing"
PAUSED = "paused"
GAMEOVER = "gameover"


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        try:
            self.sounds = make_sounds()
        except pygame.error:
            self.sounds = {}

        self.highway = Highway()
        self.player_image = make_car(S.PLAYER_SIZE, S.PLAYER_COLOR, S.PLAYER_ACCENT, facing_up=True)
        self.player_glow = make_player_glow()
        self.player = Player(self.player_image, S.DIFFICULTIES["Medium"]["player_speed"])

        self.state = MENU
        self.difficulty_name = "Medium"
        self.settings = S.DIFFICULTIES[self.difficulty_name]
        self.highscore = load_highscore()
        self.score = 0
        self.survival_ms = 0
        self.shake = 0
        self.spawn_timer = 0
        self.last_occupied = set()
        self.enemies: list[Enemy] = []
        self.obstacles: list[Obstacle] = []
        self.particles: list[Particle] = []

        self._build_buttons()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _build_buttons(self) -> None:
        cx = S.WIDTH // 2
        self.menu_buttons = [
            Button("START GAME", (cx, 430), accent=S.NEON_CYAN),
            Button("INSTRUCTIONS", (cx, 500), accent=S.NEON_YELLOW),
            Button("EXIT", (cx, 570), accent=S.NEON_MAGENTA),
        ]
        self.diff_buttons = [
            Button("EASY", (cx, 340), accent=S.NEON_GREEN),
            Button("MEDIUM", (cx, 410), accent=S.NEON_YELLOW),
            Button("HARD", (cx, 480), accent=S.NEON_MAGENTA),
            Button("BACK", (cx, 560), size=(220, 50), accent=S.NEON_CYAN),
        ]
        self.back_button = Button("BACK TO MENU", (cx, 700), size=(260, 50))
        self.pause_buttons = [
            Button("RESUME", (cx, 380), accent=S.NEON_GREEN),
            Button("MAIN MENU", (cx, 450), accent=S.NEON_CYAN),
        ]
        self.over_buttons = [
            Button("RESTART", (cx, 500), accent=S.NEON_GREEN),
            Button("MAIN MENU", (cx, 570), accent=S.NEON_CYAN),
        ]

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def current_speed(self) -> float:
        """Traffic speeds up as the score rises, but never past the cap."""
        cfg = self.settings
        return min(cfg["max_speed"], cfg["base_speed"] + self.score * cfg["speed_per_score"])

    def start_run(self, difficulty: str) -> None:
        """Reset everything for a fresh race. Safe to call after Game Over."""
        self.difficulty_name = difficulty
        self.settings = S.DIFFICULTIES[difficulty]
        self.player = Player(self.player_image, self.settings["player_speed"])
        self.enemies.clear()
        self.obstacles.clear()
        self.particles.clear()
        self.score = 0
        self.survival_ms = 0
        self.spawn_timer = 400
        self.shake = 0
        self.last_occupied = set()
        self.state = PLAYING
        self.play("start")

    # ------------------------------------------------------------------
    # Traffic spawning
    # ------------------------------------------------------------------
    def spawn_wave(self) -> None:
        """
        Place 1 or 2 cars (never all 3 lanes) so the player always has a gap.

        Harder difficulties more often block two lanes. Obstacles sometimes
        appear in the remaining open lane a little later in the same area,
        but we never fully wall the road.
        """
        speed = self.current_speed()
        lanes = [0, 1, 2]

        # Avoid repeating the exact same blocked pair twice in a row
        two_car = random.random() < self.settings["two_car_chance"]
        if two_car:
            blocked = set(random.sample(lanes, 2))
            if blocked == self.last_occupied:
                blocked = set(random.sample(lanes, 2))
        else:
            blocked = {random.choice(lanes)}

        self.last_occupied = set(blocked)
        for lane in blocked:
            self.enemies.append(Enemy(lane, speed + random.uniform(-0.4, 0.8)))

        open_lanes = [lane for lane in lanes if lane not in blocked]
        if open_lanes and random.random() < self.settings["obstacle_chance"]:
            # Put the barrel slightly above the cars so it is a separate dodge
            barrel = Obstacle(random.choice(open_lanes), speed * 0.92)
            barrel.rect.bottom = -110
            self.obstacles.append(barrel)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update_playing(self, dt: int) -> None:
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        speed = self.current_speed()
        self.highway.update(speed)

        self.spawn_timer += dt
        spawn_every = max(420, int(self.settings["spawn_ms"] - self.score * 0.35))
        if self.spawn_timer >= spawn_every:
            self.spawn_timer = 0
            self.spawn_wave()

        # Survival points: +10 each second
        self.survival_ms += dt
        if self.survival_ms >= 1000:
            self.survival_ms -= 1000
            self.score += S.POINTS_PER_SECOND
            self.play("score")

        player_box = self.player.hitbox()

        for enemy in self.enemies:
            enemy.speed = max(enemy.speed, speed * 0.85)
            enemy.update()
            if enemy.passed_player(self.player):
                enemy.counted = True
                self.score += S.POINTS_PER_AVOID
                self.play("score_hi")
            if player_box.colliderect(enemy.hitbox()):
                self.crash()
                return

        for obstacle in self.obstacles:
            obstacle.update()
            if obstacle.passed_player(self.player):
                obstacle.counted = True
                self.score += S.POINTS_PER_OBSTACLE
            if player_box.colliderect(obstacle.hitbox()):
                self.crash()
                return

        self.enemies = [e for e in self.enemies if not e.offscreen()]
        self.obstacles = [o for o in self.obstacles if not o.offscreen()]

        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.life > 0]

        if self.shake:
            self.shake -= 1

    def crash(self) -> None:
        self.play("crash")
        center = self.player.rect.center
        self.particles = [Particle(center) for _ in range(28)]
        self.shake = 18
        self.highscore = save_highscore(self.score)
        self.state = GAMEOVER

    def update_particles_only(self) -> None:
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.life > 0]
        if self.shake:
            self.shake -= 1
        self.highway.update(1.4)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if self.state == PLAYING:
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        self.state = PLAYING
                if event.key == pygame.K_RETURN and self.state == MENU:
                    self.state = DIFFICULTY

            if self.state == MENU:
                for button in self.menu_buttons:
                    button.update(mouse)
                if self.menu_buttons[0].clicked(event):
                    self.play("click")
                    self.state = DIFFICULTY
                elif self.menu_buttons[1].clicked(event):
                    self.play("click")
                    self.state = INSTRUCTIONS
                elif self.menu_buttons[2].clicked(event):
                    pygame.quit()
                    sys.exit()

            elif self.state == INSTRUCTIONS:
                self.back_button.update(mouse)
                if self.back_button.clicked(event):
                    self.play("click")
                    self.state = MENU

            elif self.state == DIFFICULTY:
                for button in self.diff_buttons:
                    button.update(mouse)
                mapping = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}
                for button in self.diff_buttons[:3]:
                    if button.clicked(event):
                        self.play("click")
                        self.start_run(mapping[button.text])
                if self.diff_buttons[3].clicked(event):
                    self.play("click")
                    self.state = MENU

            elif self.state == PAUSED:
                for button in self.pause_buttons:
                    button.update(mouse)
                if self.pause_buttons[0].clicked(event):
                    self.play("click")
                    self.state = PLAYING
                elif self.pause_buttons[1].clicked(event):
                    self.play("click")
                    self.state = MENU

            elif self.state == GAMEOVER:
                for button in self.over_buttons:
                    button.update(mouse)
                if self.over_buttons[0].clicked(event):
                    self.play("click")
                    self.start_run(self.difficulty_name)
                elif self.over_buttons[1].clicked(event):
                    self.play("click")
                    self.state = MENU

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def world_surface(self) -> pygame.Surface:
        canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        self.highway.draw(canvas)
        for obstacle in self.obstacles:
            obstacle.draw(canvas)
        for enemy in self.enemies:
            enemy.draw(canvas)
        if self.state != GAMEOVER or self.particles:
            if self.player.alive:
                self.player.draw(canvas, self.player_glow if self.state == PLAYING else None)
        for particle in self.particles:
            particle.draw(canvas)
        return canvas

    def blit_with_shake(self, canvas: pygame.Surface) -> None:
        if self.shake:
            ox = random.randint(-6, 6)
            oy = random.randint(-6, 6)
            self.screen.blit(canvas, (ox, oy))
        else:
            self.screen.blit(canvas, (0, 0))

    def draw_hud(self) -> None:
        bar = pygame.Surface((S.WIDTH, 56), pygame.SRCALPHA)
        pygame.draw.rect(bar, (6, 8, 20, 200), bar.get_rect())
        self.screen.blit(bar, (0, 0))
        draw_text(self.screen, f"SCORE  {self.score}", self.fonts["hud"], S.WHITE, topleft=(18, 16), glow=S.NEON_CYAN)
        draw_text(self.screen, f"BEST  {self.highscore}", self.fonts["hud"], S.NEON_YELLOW, center=(S.WIDTH // 2, 28))
        draw_text(self.screen, self.difficulty_name.upper(), self.fonts["hud"], S.NEON_MAGENTA, topleft=(S.WIDTH - 130, 16))
        draw_text(self.screen, "P / ESC pause", self.fonts["small"], (180, 190, 210), topleft=(18, S.HEIGHT - 28))

    def draw_menu(self) -> None:
        canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        self.highway.update(2.2)
        self.highway.draw(canvas)
        self.screen.blit(canvas, (0, 0))

        panel = Panel(pygame.Rect(50, 90, S.WIDTH - 100, 520))
        panel.draw(self.screen)
        draw_text(self.screen, "HIGHWAY RUSH", self.fonts["title"], S.WHITE, center=(S.WIDTH // 2, 150), glow=S.NEON_CYAN)
        draw_text(self.screen, "NEON ARCADE  ·  THREE LANES  ·  DODGE EVERYTHING", self.fonts["small"], S.NEON_YELLOW, center=(S.WIDTH // 2, 200))
        draw_text(self.screen, f"Local high score  {self.highscore}", self.fonts["body"], S.WHITE, center=(S.WIDTH // 2, 250))
        draw_text(self.screen, "Arrow keys or A / D to steer", self.fonts["small"], (190, 200, 220), center=(S.WIDTH // 2, 290))

        mouse = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.update(mouse)
            button.draw(self.screen, self.fonts["button"])

    def draw_instructions(self) -> None:
        canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        self.highway.update(1.4)
        self.highway.draw(canvas)
        self.screen.blit(canvas, (0, 0))

        panel = Panel(pygame.Rect(40, 70, S.WIDTH - 80, 680))
        panel.draw(self.screen)
        draw_text(self.screen, "HOW TO PLAY", self.fonts["huge"], S.WHITE, center=(S.WIDTH // 2, 120), glow=S.NEON_CYAN)

        paragraphs = [
            "Stay in your cyan car at the bottom of the highway.",
            "Move LEFT / RIGHT with the arrow keys or A and D.",
            "Enemy cars and striped barrels come from the top. Never let them touch you.",
            "Score grows every second you survive. Extra points are awarded for each car or obstacle you slip past.",
            "Traffic gets faster as your score climbs. Hard mode fills two lanes more often.",
            "Press P or ESC to pause. Beat the local high score saved on this computer.",
        ]
        y = 180
        for paragraph in paragraphs:
            for line in wrap_text("•  " + paragraph, self.fonts["body"], S.WIDTH - 140):
                draw_text(self.screen, line, self.fonts["body"], S.WHITE, topleft=(70, y))
                y += 28
            y += 10

        self.back_button.update(pygame.mouse.get_pos())
        self.back_button.draw(self.screen, self.fonts["button"])

    def draw_difficulty(self) -> None:
        canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        self.highway.update(1.8)
        self.highway.draw(canvas)
        self.screen.blit(canvas, (0, 0))

        panel = Panel(pygame.Rect(50, 120, S.WIDTH - 100, 520))
        panel.draw(self.screen)
        draw_text(self.screen, "SELECT DIFFICULTY", self.fonts["huge"], S.WHITE, center=(S.WIDTH // 2, 180), glow=S.NEON_YELLOW)
        draw_text(self.screen, "Harder traffic, tighter gaps, higher speed.", self.fonts["small"], (200, 210, 230), center=(S.WIDTH // 2, 230))

        mouse = pygame.mouse.get_pos()
        for button in self.diff_buttons:
            button.update(mouse)
            button.draw(self.screen, self.fonts["button"])

    def draw_paused(self) -> None:
        canvas = self.world_surface()
        self.screen.blit(canvas, (0, 0))
        self.draw_hud()
        dim = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, "PAUSED", self.fonts["title"], S.WHITE, center=(S.WIDTH // 2, 260), glow=S.NEON_CYAN)
        mouse = pygame.mouse.get_pos()
        for button in self.pause_buttons:
            button.update(mouse)
            button.draw(self.screen, self.fonts["button"])

    def draw_gameover(self) -> None:
        canvas = self.world_surface()
        self.blit_with_shake(canvas)
        dim = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))
        panel = Panel(pygame.Rect(50, 180, S.WIDTH - 100, 460))
        panel.draw(self.screen)
        draw_text(self.screen, "GAME OVER", self.fonts["title"], S.WHITE, center=(S.WIDTH // 2, 250), glow=S.NEON_MAGENTA)
        draw_text(self.screen, f"Final score  {self.score}", self.fonts["huge"], S.NEON_YELLOW, center=(S.WIDTH // 2, 330))
        draw_text(self.screen, f"Best  {self.highscore}    ·    {self.difficulty_name}", self.fonts["body"], S.WHITE, center=(S.WIDTH // 2, 390))
        if self.score >= self.highscore and self.score > 0:
            draw_text(self.screen, "NEW HIGH SCORE!", self.fonts["hud"], S.NEON_GREEN, center=(S.WIDTH // 2, 430))
        mouse = pygame.mouse.get_pos()
        for button in self.over_buttons:
            button.update(mouse)
            button.draw(self.screen, self.fonts["button"])

    def draw_playing(self) -> None:
        canvas = self.world_surface()
        self.blit_with_shake(canvas)
        self.draw_hud()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while True:
            dt = self.clock.tick(S.FPS)
            self.handle_events()

            if self.state == PLAYING:
                self.update_playing(dt)
            elif self.state == GAMEOVER:
                self.update_particles_only()
            elif self.state in (MENU, INSTRUCTIONS, DIFFICULTY):
                pass

            if self.state == MENU:
                self.draw_menu()
            elif self.state == INSTRUCTIONS:
                self.draw_instructions()
            elif self.state == DIFFICULTY:
                self.draw_difficulty()
            elif self.state == PLAYING:
                self.draw_playing()
            elif self.state == PAUSED:
                self.draw_paused()
            elif self.state == GAMEOVER:
                self.draw_gameover()

            pygame.display.flip()
