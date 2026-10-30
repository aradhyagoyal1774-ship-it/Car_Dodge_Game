# HIGHWAY RUSH

A 2D neon arcade car-dodge game built with **Python 3** and **Pygame** for a first-year B.Tech CSE team project.

You steer a cyan sports car down a three-lane night highway. Oncoming traffic and hazard barrels get faster as your score climbs. Survive, weave, and beat the local high score.

No image or audio files are required. Cars, the road, lamps, and sound effects are generated in code.

---

## 1. Project description (college submission)

**Title:** Highway Rush — An Interactive 2D Car Dodge Game using Python and Pygame

**Abstract:**  
Highway Rush is a real-time 2D arcade game that demonstrates core programming concepts: loops, conditionals, lists, randomization, collision detection, file I/O, and object-oriented design. The player controls a car on a scrolling three-lane highway and must avoid randomly spawned enemy vehicles and obstacles. Difficulty increases with score. A main menu, pause system, game-over flow, and locally saved high score make the project feel like a complete mini-game rather than a classroom sketch.

**Tools:** Python 3, Pygame  
**Team size:** 4 members  
**Outcome:** A playable game plus documented source code suitable for a lab/viva evaluation.

---

## 2. Install Pygame

1. Install **Python 3.10 or newer** from https://www.python.org/downloads/  
   During setup on Windows, tick **Add python.exe to PATH**.
2. Open a terminal (PowerShell or Command Prompt).
3. Go to this folder:

```text
cd "C:\Users\Aradhya Goyal\car-dodge-game"
```

4. (Recommended) Create a virtual environment:

```text
python -m venv .venv
.venv\Scripts\activate
```

5. Install the only extra library:

```text
python -m pip install -r requirements.txt
```

That installs **pygame-ce** (Community Edition). You still write `import pygame` — the API is the same as classic Pygame. It is used here because it has ready-made Windows wheels for newer Python versions (including 3.14). There are no other third-party dependencies.

If your lab PC already has classic Pygame, `python -m pip install pygame` is also fine.

---

## 3. Run the game in VS Code (step by step)

1. Open **VS Code**.
2. **File → Open Folder…** and select `car-dodge-game`.
3. Open the integrated terminal: **Terminal → New Terminal**.
4. If you created a venv, activate it:

```text
.venv\Scripts\activate
```

5. Confirm Python can see Pygame:

```text
python -c "import pygame; print(pygame.version.ver)"
```

6. Start the game:

```text
python main.py
```

7. A window titled **HIGHWAY RUSH** should open. Use the mouse on the menu. Use **← / →** or **A / D** in play. **P** or **ESC** pauses.

If the window does not appear, make sure the terminal is in the project folder and that `pip install pygame` finished without errors.

---

## 4. How to play

| Control | Action |
| --- | --- |
| ← or A | Move left |
| → or D | Move right |
| P or ESC | Pause / resume |
| Mouse | Menu buttons |

**Scoring**

- +10 every second you survive
- +25 for each enemy car you pass
- +15 for each barrel you pass

Traffic speed and spawn rate rise with your score. Easy / Medium / Hard change the starting speed and how often two lanes are blocked at once. The best score is stored in `highscore.json` in this folder.

---

## 5. Project structure

```text
car-dodge-game/
  main.py                 # entry point — run this
  requirements.txt        # pygame
  README.md               # this file
  highway_rush/
    settings.py           # window size, colors, difficulty numbers
    assets.py             # drawn cars + generated beep/crash sounds
    road.py               # scrolling highway, lamps, stars
    entities.py           # Player, Enemy, Obstacle, Particle
    ui.py                 # buttons, glowing text, panels
    highscore.py          # load/save JSON high score
    game.py               # menus, loop, collisions, states
```

---

## 6. Important functions and game logic

**Game loop (`Game.run` in `game.py`)**  
Each frame: process events → update the active state → draw → `pygame.display.flip()`. The clock is locked at 60 FPS.

**State machine**  
`MENU`, `INSTRUCTIONS`, `DIFFICULTY`, `PLAYING`, `PAUSED`, `GAMEOVER`. Restart always calls `start_run()`, which rebuilds the player and empties enemy lists so a previous crash cannot leak into a new race.

**Player movement (`Player.handle_input`)**  
Arrow keys and A/D change `rect.x`. The car is clamped to the asphalt so it cannot leave the road.

**Scrolling road (`Highway.update` / `draw`)**  
Dashed lane lines and lamp posts slide downward. That is cheaper than moving a huge background image and still reads as forward motion.

**Spawning (`Game.spawn_wave`)**  
A wave occupies one or two lanes, never three, so there is always a gap. A barrel may appear in an open lane. Randomization plus a “do not repeat the same blocked pair” check keeps traffic from feeling stuck.

**Difficulty (`current_speed`)**  
`speed = min(max_speed, base_speed + score * speed_per_score)`. Spawn delay also shrinks slowly with score.

**Collision (`Game.update_playing`)**  
Each sprite has a slightly inset `hitbox()` rectangle. If the player box overlaps an enemy or obstacle, `crash()` plays a sound, spawns particles, saves the high score, and switches to Game Over.

**High score (`highscore.py`)**  
`load_highscore()` / `save_highscore()` read and write JSON. A missing or broken file is treated as score 0 so the game never crashes on disk errors.

**Graphics and audio (`assets.py`)**  
`make_car()` draws a top-down vehicle with windows, lights, and a stripe. `make_sounds()` builds short sine-wave and noise buffers so the mixer can play beeps without `.wav` files.

---

## 7. Suggested work split (4 team members)

| Member | Role | Typical tasks |
| --- | --- | --- |
| **1 — Gameplay lead** | Core logic | `game.py` loop, states, pause, restart, collision, scoring |
| **2 — World & entities** | Simulation | `entities.py`, `road.py`, spawning, difficulty table in `settings.py` |
| **3 — UI & polish** | Look and feel | `assets.py` cars/sounds, `ui.py` menus, HUD, particles, colors |
| **4 — Docs & QA** | Delivery | README, viva notes, playtesting all difficulties, high-score file checks |

Everyone should play the game and be able to explain `spawn_wave`, `hitbox`, and the state machine in the viva.

---

## 8. Five viva questions (with answers)

**Q1. How does the game detect a crash?**  
**A.** Each car has a Pygame `Rect`. We shrink it with `inflate` to make a fair hitbox, then call `colliderect` between the player and every enemy/obstacle. If any pair overlaps, `crash()` runs.

**Q2. Why use classes instead of only functions?**  
**A.** A `Player` or `Enemy` keeps its own image, position, and speed together. The main loop can store them in lists and call `update()` / `draw()` without copying the same code for every car.

**Q3. How is the high score remembered after you close the window?**  
**A.** `save_highscore` writes a JSON file (`highscore.json`) on disk. Next launch, `load_highscore` reads it. If the file is missing, the game starts from 0.

**Q4. How does difficulty increase during a single run?**  
**A.** Base speed comes from Easy/Medium/Hard. Each frame, `current_speed()` adds `score * speed_per_score` up to a cap. Spawn delay also drops as the score grows, so traffic is both faster and more frequent.

**Q5. How can the player always have a way through?**  
**A.** `spawn_wave` never fills all three lanes. It blocks one or two lanes at random and leaves at least one empty. That is a design rule implemented with `random.sample` and a list of open lanes.

---

## 9. Controls recap for the demo

1. Run `python main.py`.
2. Click **START GAME** → pick **EASY** for a calm demo, **HARD** to show the full challenge.
3. Dodge until you crash, point out the live score and high score.
4. Press **RESTART**, then **MAIN MENU**, then **EXIT**.
