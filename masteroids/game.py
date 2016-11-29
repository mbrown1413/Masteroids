import sys

from OpenGL.GL import *

from masteroids import screens
from masteroids import entities

class Game():

    def __init__(self):
        self.player = None
        self.current_screen = None
        self._init_title_screen()

    def _init_title_screen(self):
        self.level_number = 0
        self.player = entities.PlayerEntity()
        self.starting_asteroids = [entities.AsteroidEntity() for i in range(3)]
        self.current_screen = screens.TitleScreen(self.starting_asteroids)

    def update(self, dt, keyboard):
        result = self.current_screen.update(dt, keyboard)

        if isinstance(result, screens.Screen):
            self.current_screen = result

        elif result == "title_screen":
            self._init_title_screen()

        elif result == "next_level":
            self.level_number += 1
            self.current_screen = screens.GameplayScreen(
                self.player,
                self.level_number,
                self.starting_asteroids
            )
            self.starting_asteroids = None

        elif result == "reset_game":
            return True

        elif result == "quit":
            sys.exit(0)

        elif result is not None:
            raise RuntimeError('Invalid result "{}" returned from a screen object.'.format(result))

    def draw(self):
        self.current_screen.draw()
