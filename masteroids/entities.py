
import random
from time import time
from math import sqrt, radians, sin, cos

from OpenGL.GL import *
from OpenGL.GLUT import *

from masteroids import shapes


class Entity():

    def __init__(self):
        self.shape = None

    def setup(self, screen):
        pass

    def on_collision(self, other, point, dt, screen):
        pass

    def update(self, dt, keyboard, screen):
        pass

    def draw(self):
        raise NotImplementedError()

    @property
    def x(self):
        return self.shape.x

    @property
    def y(self):
        return self.shape.y


class BulletEntity(Entity):
    VELOCITY = 1  # Units / Second
    LIFETIME = 1  # Seconds

    def __init__(self, owner):
        self.owner = owner
        self.start_time = time()

        self.shape = shapes.PointShape(owner.x, owner.y)

        player_velocity_mag = sqrt(owner.dx**2 + owner.dy**2)
        dir_x = -sin(radians(owner.shape.yaw))
        dir_y = cos(radians(owner.shape.yaw))
        self.dx = dir_x*self.VELOCITY + owner.dx
        self.dy = dir_y*self.VELOCITY + owner.dy

    def update(self, dt, keyboard, screen):
        self.shape.translate(self.dx * dt, self.dy * dt)

        if time() - self.start_time > self.LIFETIME:
            screen.remove_entity(self)

    def draw(self):
        glColor(0, 1, 0)
        self.shape.draw()

    def on_collision(self, other, point, dt, screen):
        if isinstance(other, AsteroidEntity):
            screen.remove_entity(self)


class PlayerEntity(Entity):
    TURN_RATE = 200
    THRUST_RATE = 0.02
    RECOIL_RATE = 0.008
    VELOCITY_MAX = float("inf") # 10 is reasonable
    COOLDOWN_RATE = 2
    COOLDOWN_MAX = 3
    EXTRA_LIFE_SCORE = 10000

    SHIP_VERTEXES = (
        (-0.02, 0),
        (0, 0.06),
        (0.02, 0),
        (0, 0.01),
    )

    def __init__(self):
        super().__init__()
        self.setup(None)

        self.lives = 3
        self.score = 0

    def setup(self, screen):
        self.dx = 0
        self.dy = 0
        self.cooldown = 0

        self.shape = shapes.PolygonShape(self.SHIP_VERTEXES)

    @property
    def yaw(self):
        return self.shape.yaw

    def update(self, dt, keyboard, screen):
        self.shape.translate(self.dx * dt, self.dy * dt)

        if self.can_fire() and keyboard.key_just_pressed(b' ', repeat=0.4):
            self.fire(dt, screen)
        if keyboard.is_key_down(GLUT_KEY_LEFT):
            self.shape.rotate(self.TURN_RATE * dt)
        if keyboard.is_key_down(GLUT_KEY_RIGHT):
            self.shape.rotate(-self.TURN_RATE * dt)
        if keyboard.is_key_down(GLUT_KEY_UP):
            self.dx += -sin(radians(self.yaw)) * self.THRUST_RATE
            self.dy += cos(radians(self.yaw)) * self.THRUST_RATE

            # Thruster Particles
            for i in range(2):
                theta = self.yaw + random.uniform(-10, 10)
                x = sin(radians(theta))*0.03 + self.x - self.dx*dt
                y = -cos(radians(theta))*0.03 + self.y - self.dy*dt
                dx = sin(radians(theta))*0.18 + self.dx
                dy = -cos(radians(theta))*0.18 + self.dy
                particle = ParticleEntity(x, y, dx, dy, (0.5, 0, 0))
                screen.add_entity(particle)

        # Cap Velocity
        dmag = sqrt(self.dx**2 + self.dy**2)
        if dmag > self.VELOCITY_MAX:
            self.dx = self.dx / dmag * self.VELOCITY_MAX
            self.dy = self.dy / dmag * self.VELOCITY_MAX

        self.cooldown = max(0, self.cooldown - self.COOLDOWN_RATE*dt)

    def can_fire(self):
        return self.cooldown <= self.COOLDOWN_MAX - 1

    def add_score(self, amount):
        prev_score = self.score
        self.score += amount
        if prev_score % self.EXTRA_LIFE_SCORE > self.score % self.EXTRA_LIFE_SCORE:
            self.lives += 1

    def fire(self, dt, screen):
        if not self.can_fire():
            return
        self.cooldown += 1

        bullet = BulletEntity(self)
        screen.add_entity(bullet)

        # Recoil
        self.dx -= -sin(radians(self.yaw)) * self.RECOIL_RATE
        self.dy -= cos(radians(self.yaw)) * self.RECOIL_RATE

    def draw(self):
        glColor(0, 1, 0)
        self.shape.draw()

    def on_collision(self, other, point, dt, screen):
        if isinstance(other, AsteroidEntity):
            screen.remove_entity(self)
            particles = ParticleEntity.create_from_entity(self, (0, 1, 0), 20)
            screen.add_entities(particles)
            self.cooldown = 0


class AsteroidEntity(Entity):

    def __init__(self, size=1, x=None, y=None, dx=None, dy=None, dyaw=None, polygon=None):
        super().__init__()
        self.dx = dx if dx is not None else random.uniform(-0.2, 0.2)
        self.dy = dy if dy is not None else random.uniform(-0.2, 0.2)
        self.dyaw = dyaw if dyaw is not None else random.uniform(-2, 2)
        self.size = size

        scale = size*0.05
        if polygon is None:
            s = scale
            l = ( 1+sqrt(2) ) * scale
            r = lambda: random.uniform(-scale, scale)
            points = (
                (-l+r(), -s+r()),
                (-l+r(),  s+r()),
                (-s+r(),  l+r()),
                ( s+r(),  l+r()),
                ( l+r(),  s+r()),
                ( l+r(), -s+r()),
                ( s+r(), -l+r()),
                (-s+r(), -l+r()),
            )
            self.shape = shapes.PolygonShape(points)
        else:
            self.shape = polygon

        x = random.uniform(-1, 1) if x is None else x
        y = random.uniform(-1, 1) if y is None else y
        self.shape.translate(x, y)

    def draw(self):
        glColor(1, 1, 1)
        self.shape.draw()

    def update(self, dt, keyboard, screen):
        self.shape.translate(self.dx * dt, self.dy * dt)
        self.shape.rotate(self.dyaw)

    def on_collision(self, other, point, dt, screen):
        if isinstance(other, (PlayerEntity, BulletEntity)):
            screen.remove_entity(self)
            screen.add_entities(self.split(other))
            if isinstance(other, BulletEntity):
                other.owner.add_score(25 / self.size)
            elif isinstance(other, PlayerEntity):
                other.add_score(25 / self.size)

    def split(self, entity):

        if self.size < 0.25:
            return ParticleEntity.create_from_entity(self, (1, 1, 1))

        poly1, poly2 = self.shape.split(
            #(self.x, self.y),
            #(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))
        )
        if poly1 is None or poly2 is None:
            return []

        d_impulse = poly1.center - self.shape.center
        d_impulse /= sqrt(d_impulse[0]**2 + d_impulse[1]**2)
        d_impulse *= 0.1
        dx1 = d_impulse[0] + self.dx
        dy1 = d_impulse[1] + self.dy
        dx2 = -d_impulse[0] + self.dx
        dy2 = -d_impulse[1] + self.dy
        dyaw1 = self.dyaw
        dyaw2 = -self.dyaw
        a1 = AsteroidEntity(self.size / 2, 0, 0, dx1, dy1, dyaw1, poly1)
        a2 = AsteroidEntity(self.size / 2, 0, 0, dx2, dy2, dyaw2, poly2)

        entities = []
        MIN_AREA = 0.001
        for a in (a1, a2):
            if a.shape.area >= MIN_AREA:
                entities.append(a)

        return entities


class ParticleEntity(Entity):

    @classmethod
    def create_from_entity(cls, entity, color, number=10):
        dx = entity.dx if hasattr(entity, "dx") else 0
        dy = entity.dy if hasattr(entity, "dy") else 0
        for i in range(number):
            yield cls(
                entity.x, entity.y,
                dx + random.uniform(-0.2, 0.2),
                dy + random.uniform(-0.2, 0.2),
                color
            )

    def __init__(self, x, y, dx, dy, color):
        self.shape = shapes.PointShape(x, y)
        self.dx = dx
        self.dy = dy
        self.color = color

    def update(self, dt, keyboard, screen):
        self.shape.translate(self.dx * dt, self.dy * dt)
        self.color = (
            max(0, self.color[0] - 0.4*dt),
            max(0, self.color[1] - 0.4*dt),
            max(0, self.color[2] - 0.4*dt)
        )
        if self.color == (0, 0, 0):
            screen.remove_entity(self)

    def draw(self):
        glColor(*self.color)
        self.shape.draw()

    def on_collision(self, other, point, dt, screen):
        if isinstance(other, (AsteroidEntity, PlayerEntity)):
            screen.remove_entity(self)
