
from math import radians, sin, cos, sqrt
from itertools import product

import numpy

from OpenGL.GL import *

class Shape():

    def draw(self):
        raise NotImplementedError()

    def check_collision(self, other):
        raise NotImplementedError()

    def translate(self, dx, dy):
        raise NotImplementedError()


class PointShape(Shape):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def check_collision(self, other):
        #TODO: Use bounding box for quick rejection
        if isinstance(other, PolygonShape):
            return _collision_polygon_point(other, self)
        elif isinstance(other, PointShape):
            return False
        raise NotImplementedError()

    def translate(self, dx, dy):
        self.x += dx
        self.y += dy
        self._wrap_around()

    def _wrap_around(self):
        self.x = (self.x + 1)%2 - 1
        self.y = (self.y + 1)%2 - 1

    def draw(self):
        glBegin(GL_POINTS)
        glVertex2f(self.x, self.y)
        glEnd()


class PolygonShape(Shape):

    def __init__(self, points):
        self.raw_points = tuple(tuple(p) for p in points)
        self._points_cache = None
        self.yaw = 0
        self.center = numpy.array([0.0, 0.0])

        # Shift self.center to center of points
        #TODO: Change this to center of gravity
        center = self.get_center()
        self.center += center
        self.raw_points = tuple(
            (x - center[0], y - center[1]) for x, y in self.raw_points
        )

    @property
    def points(self):
        if self._points_cache is not None:
            return self._points_cache
        theta = radians(self.yaw)
        points = []
        for x, y in self.raw_points:
            points.append((
                x*cos(theta) - y*sin(theta) + self.center[0],
                x*sin(theta) + y*cos(theta) + self.center[1]
            ))
        self._points_cache = tuple(points)
        return self._points_cache

    @property
    def x(self):
        return self.center[0]

    @property
    def y(self):
        return self.center[1]

    def get_center(self):
        bb = self.get_bounding_box()
        return numpy.array((
            (bb[0][0] + bb[1][0]) / 2,
            (bb[0][1] + bb[1][1]) / 2
        ))

    def get_bounding_box(self):
        xs = [x for x, y in self.points]
        ys = [y for x, y in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return (
            (min_x, min_y),
            (max_x, max_y)
        )

    def get_lines(self):
        points = self.points
        for i in range(len(points)-1):
            yield (points[i], points[i+1])
        yield (points[-1], points[0])

    def check_collision(self, other):
        if isinstance(other, PolygonShape):
            return _collision_polygon_polygon(self, other)
        elif isinstance(other, PointShape):
            return _collision_polygon_point(self, other)
        return NotImplementedError()

    def rotate(self, dyaw):
        self.yaw = (self.yaw + dyaw) % 360
        self._points_cache = None

    def translate(self, dx, dy):
        self.center[0] = (self.center[0] + dx + 1)%2 - 1
        self.center[1] = (self.center[1] + dy + 1)%2 - 1
        self._points_cache = None

    def draw(self):
        glBegin(GL_LINE_LOOP)
        for x, y in self.points:
            glVertex2f(x, y)
        glEnd()

    def split(self):
        """Split polygon into two along a line."""
        lines = list(self.get_lines())

        def find_closest_intersection(start, direction, lines):
            """
            Return a tuple of: (line that intersects closest, point at which it
            intersects).
            """
            closest_t = float("inf")
            closest_line = None
            for line in lines:
                t1, t2 = _find_t_intersects(line, (start, start+direction))
                if t1 != None and t1 >= 0 and t1 <= 1:
                    if t2 is not None and t2 >= 0 and t2 < closest_t:
                        closest_t = t2
                        closest_line = line
            return closest_line, start + closest_t*direction

        best_dir = None
        best_dist = float("inf")
        for theta in range(0, 180, 10):
            direction = numpy.array([
                sin(radians(theta)),
                cos(radians(theta))
            ])
            l1, p1 = find_closest_intersection(self.center, direction, lines)
            l2, p2 = find_closest_intersection(self.center, -direction, lines)
            vec = p1 - p2
            dist = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            if dist < best_dist:
                best_dist = dist
                best_dir = direction
        l1, p1 = find_closest_intersection(self.center, best_dir, lines)
        l2, p2 = find_closest_intersection(self.center, -best_dir, lines)

        if not l1 or not l2:
            return (None, None)
        i1 = lines.index(l1)
        i2 = lines.index(l2)
        if i1 > i2:
            l1, l2 = l2, l1
            p1, p2 = p2, p1
            i1, i2 = i2, i1

        new_poly1 = self.points[:i1+1] + (p1, p2) + self.points[i2+1:]
        new_poly2 = (p2, p1) + self.points[i1+1:i2+1]

        return PolygonShape(new_poly1), PolygonShape(new_poly2)

    @property
    def area(self):
        xs = tuple(p[0] for p in self.points)
        ys = tuple(p[1] for p in self.points)
        summation = sum(
            [xs[i-1]*ys[i] - xs[i]*ys[i-1] for i in range(len(xs))]
        )
        return abs(0.5 * summation)


def _collision_polygon_polygon(poly1, poly2):
    #TODO: Collide if one polygon is inside another
    #TODO: Cleanup

    # Fail fast if bounding boxes don't overlap
    overlap = False
    box1 = poly1.get_bounding_box()
    box2 = poly2.get_bounding_box()
    if not _collision_bb_bb(box1, box2):
        return None

    for line1 in poly1.get_lines():
        for line2 in poly2.get_lines():
            for dx, dy in product((-2, 0, 2), repeat=2):
                result = _collision_line_line(
                    (
                        (line1[0][0] + dx, line1[0][1] + dy),
                        (line1[1][0] + dx, line1[1][1] + dy),
                    ),
                    line2
                )
                if result:
                    return (
                        (result[0] + 1)%2 - 1,
                        (result[1] + 1)%2 - 1,
                    )
    return None

def _collision_bb_bb(box1, box2):
    (x1, y1), (x2, y2) = box1
    (x3, y3), (x4, y4) = box2
    for dx, dy in product((-2, 0, 2), repeat=2):
        if x1 + dx <= x4 and y1 + dy <= y4 and \
            x2 + dx >= x3 and y2 + dy >= y3:
            return True
    return False

def _collision_polygon_point(poly, point):

    bb = poly.get_bounding_box()
    for dx, dy in product((-2, 0, 2), repeat=2):

        # Bounding box rejection
        if point.x + dx < bb[0][0] or point.x + dx > bb[1][0] or \
           point.y + dy < bb[0][1] or point.y + dy > bb[1][1]:
            continue

        n_lines_hit = 0
        for line in poly.get_lines():
            if _collision_line_line(line, ((-4, -4), (point.x+dx, point.y+dy))):
                n_lines_hit += 1
        if n_lines_hit % 2 == 1:
            return (point.x, point.y)

    return None

def _find_t_intersects(line1, line2):
    ax = line1[1][0] - line1[0][0]
    ay = line1[1][1] - line1[0][1]
    bx = line2[1][0] - line2[0][0]
    by = line2[1][1] - line2[0][1]
    cx = line1[0][0] - line2[0][0]
    cy = line1[0][1] - line2[0][1]
    denominator = ax*by - ay*bx
    if denominator == 0:
        return None, None
    t1 = (bx*cy - by*cx) / denominator
    t2 = (ax*cy - ay*cx) / denominator
    return t1, t2

def _collision_line_line(line1, line2):
    t1, t2 = _find_t_intersects(line1, line2)
    if t1 is None or t2 is None:
        return None
    if t1 >= 0 and t1 <= 1 and t2 >= 0 and t2 <= 1:
        return (
            line1[0][0] + t1*(line1[1][0] - line1[0][0]),
            line1[0][1] + t1*(line1[1][1] - line1[0][1])
        )
    else:
        return None
