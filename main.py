"""
HIGHWAY RUSH
------------
Start this file to play the game.

    python main.py

See README.md for install steps, team roles, and viva questions.
"""

from highway_rush.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
