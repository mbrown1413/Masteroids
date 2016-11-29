
from collections import deque
from itertools import combinations, product, chain
from math import sqrt
from time import time
from copy import copy

from OpenGL.GL import *
from OpenGL.GLUT import *

from masteroids import text
from masteroids import shapes
from masteroids import entities


def draw_bar(x, y, width, percent=1):
    glColor(1, 0, 0)
    glBegin(GL_LINES)
    glVertex2f(x, y)
    glVertex2f(x+width*min(1, percent), y)
    glColor(0, 1, 0)
    glVertex2f(x+width*min(1, percent), y)
    glVertex2f(x+width, y)
    glEnd()


class Screen():

    def update(self, dt, keyboard):
        pass

    def draw(self):
        pass


class EntityScreen(Screen):

    def __init__(self, entities=None):
        self.frame_count = 0
        self.entities = []
        self.particles = deque(maxlen=1000)
        self.add_entities(entities)

        for entity in self.entities:
            entity.setup(self)

    def update(self, dt, keyboard):

        for entity in copy(self.entities):
            entity.update(dt, keyboard, self)

        for particle in copy(self.particles):
            particle.update(dt, keyboard, self)

        # Collision Checking
        to_check = combinations(self.entities, 2)
        if self.frame_count % 10 == 0:
            to_check = chain(to_check, product(self.entities, self.particles))
        for e1, e2 in to_check:
            point = e1.shape.check_collision(e2.shape)
            if point:
                e1.on_collision(e2, point, dt, self)
                e2.on_collision(e1, point, dt, self)

        self.frame_count += 1

    def draw(self):

        # Draw each entity 9 times for wraparound effect
        glMatrixMode(GL_MODELVIEW)
        for x in range(-2, 4, 2):
            for y in range(-2, 4, 2):
                glPushMatrix()
                glTranslate(x, y, 0)
                for entity in self.entities:
                    entity.draw()
                glPopMatrix()

        glBegin(GL_POINTS)
        for particle in self.particles:
            glColor(*particle.color)
            glVertex2f(particle.x, particle.y)
        glEnd()

    def add_entity(self, entity):
        if isinstance(entity, entities.ParticleEntity):
            self.particles.append(entity)
        else:
            self.entities.append(entity)

    def add_entities(self, entities):
        for entity in entities:
            self.add_entity(entity)

    def remove_entity(self, entity):
        if isinstance(entity, entities.ParticleEntity):
            list_to_remove_from = self.particles
        else:
            list_to_remove_from = self.entities
        try:
            list_to_remove_from.remove(entity)
        except ValueError:
            pass  # Must already be removed


class TitleScreen(EntityScreen):

    def __init__(self, entities, *args):
        super().__init__(entities, *args)
        self.selected = 0
        self.title_color = (0, 0, 0)

    def update(self, dt, keyboard):
        super().update(dt, keyboard)

        if keyboard.key_just_pressed(b'\r') or keyboard.key_just_pressed(b' '):
            if self.selected == 0:
                return "next_level"
            elif self.selected == 1:
                return HighScoreScreen()
            elif self.selected == 2:
                return "quit"
        if keyboard.key_just_pressed(GLUT_KEY_DOWN):
            self.selected = (self.selected + 1) % 3
        if keyboard.key_just_pressed(GLUT_KEY_UP):
            self.selected = (self.selected - 1) % 3


    def draw(self):
        super().draw()

        # RGB bouncing between 0 and 1 at rates that are relatively prime
        t = time()
        triangle_func = lambda x: 1 - abs(x % 2 - 1)  # width=2, height=1
        glColor(
            triangle_func(t*0.77),
            triangle_func(t*0.39),
            triangle_func(t*0.53)
        )
        text.draw_str("MASTEROIDS", (-0.925, 0.6), 1.4)

        color = (0, 1, 0) if self.selected == 0 else (1, 1, 1)
        text.draw_str(" NEW GAME  ", (-0.65, 0.2), color=color)

        color = (0, 1, 0) if self.selected == 1 else (1, 1, 1)
        text.draw_str("HIGH SCORES", (-0.73, 0.0), color=color)

        color = (0, 1, 0) if self.selected == 2 else (1, 1, 1)
        text.draw_str("   QUIT    ", (-0.65, -0.2), color=color)

        glColor(0, 1, 0)
        text.draw_str(">", (-0.9, (1-self.selected)*0.2))
        text.draw_str("<", (0.78, (1-self.selected)*0.2))


class HighScoreScreen(Screen):

    def update(self, dt, keyboard):
        if keyboard.key_just_pressed(b'\r') or keyboard.key_just_pressed(b' '):
            return "title_screen"

    def draw(self):
        text.draw_sample_str()


class GameplayScreen(EntityScreen):
    RESPAWN_DELAY = 2

    def __init__(self, player, level, extra_entities=None):

        start_entities = []
        if level > 1:
            start_entities.extend([entities.AsteroidEntity() for i in range(4)])
        if extra_entities:
            start_entities.extend(extra_entities)
        super().__init__(start_entities)

        self.player = player
        self.level = level
        self.death_time = -1
        self.game_over_time = 0
        self.level_complete_time = -1
        self.first_spawn = True

    def update(self, dt, keyboard):
        super().update(dt, keyboard)

        # Handle death and game over
        if self.death_time == -1 and self.player not in self.entities:
            self.death_time = time()
        elif self.death_time != -1 and time() > self.death_time + self.RESPAWN_DELAY:
            if self.player.lives <= 0 and not self.first_spawn:
                if not self.game_over_time:
                    self.game_over_time = time()
                if time() - self.game_over_time > 1.75 and keyboard.any_key_just_pressed():
                    return "title_screen"
            elif self.is_safe_to_spawn():
                self.player.setup(self)
                if not self.first_spawn:
                    self.player.lives -= 1
                else:
                    self.first_spawn = False
                self.add_entity(self.player)
                self.death_time = -1
        
        # Handle Level Complete
        elif self.is_level_complete():
            return "next_level"

    def is_level_complete(self):
        if self.player not in self.entities:
            return False

        for entity in self.entities:
            if isinstance(entity, entities.AsteroidEntity):
                return False

        if self.level_complete_time == -1:
            self.level_complete_time = time()
        elif time() - self.level_complete_time > 3:
            return True
        
        return False

    def is_safe_to_spawn(self):
        for entity in self.entities:
            if isinstance(entity, entities.AsteroidEntity):
                if sqrt(entity.x**2 + entity.y**2) < 0.3:
                    return False
        return True

    def draw(self):
        self.draw_hud()
        super().draw()

        if self.game_over_time:
            blink = ( (time()-self.game_over_time)*2 % 2 <= 1 )
            if blink:
                glColor(1, 0, 0)
                text.draw_str("GAME OVER", (-0.6, 0))
            if time() - self.game_over_time > 1.75:
                glColor(1, 1, 1)
                text.draw_str("PRESS ANY KEY TO CONTINUE", (-0.3, -0.1), 0.2)

    def draw_hud(self):
        #TODO: Cleanup

        # Weapon Cooldown
        draw_bar(.22, .95, 0.7, self.player.cooldown / self.player.COOLDOWN_MAX)

        # Lives
        blink_active = False
        if self.death_time != -1 and not self.first_spawn:
            blink_active = ( time()*5 % 2 <= 1 )
        glColor(0, 1, 0)
        text.draw_str("LIVES", (-0.9, 0.9), 0.25)
        player_shape = shapes.PolygonShape(entities.PlayerEntity.SHIP_VERTEXES)
        player_shape.translate(-0.88, 0.82)
        if self.player.lives <= 0:
            text.draw_str("-", (-0.83, 0.83), 0.25)
        elif self.player.lives > 3:
            if not blink_active:
                player_shape.draw()
            text.draw_str("X {}".format(self.player.lives), (-0.83, 0.83), 0.25)
        else:
            n_lives_to_show = self.player.lives
            if blink_active:
                n_lives_to_show -= 1
            if n_lives_to_show > 0:
                for i in range(n_lives_to_show):
                    player_shape.draw()
                    player_shape.translate(0.058, 0)

        # Level
        text.draw_str("LEVEL {}".format(self.level), (-0.65, 0.9), 0.25)

        # Score
        text.draw_str("SCORE {}".format(int(self.player.score)), (-0.3, 0.9), 0.25)
