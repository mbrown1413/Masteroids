
from time import time

from OpenGL.GL import *
from OpenGL.GLUT import *

from masteroids.game import Game
from masteroids.inputstate import InputState


class GameInterface():

    def __init__(self):
        self.game = Game()
        self.keyboard = InputState()
        self.last_update_time = None
        self.win_width = 700
        self.win_height = 700

        # GLUT init
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGB)
        glutInitWindowSize(self.win_width, self.win_height)
        glutInitWindowPosition(0, 0)
        glutCreateWindow(b"Masteroids")
        glutSetCursor(GLUT_CURSOR_NONE)

        # GL init
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glPointSize(2)
        glDisable(GL_DITHER)
        glDisable(GL_MULTISAMPLE)

        # Callbacks
        glutDisplayFunc(self.draw)
        glutReshapeFunc(self.reshape)
        glutTimerFunc(0, self.update, None)
        glutIgnoreKeyRepeat(1)
        glutKeyboardFunc(self.keyboard.key_down)
        glutKeyboardUpFunc(self.keyboard.key_up)
        glutSpecialFunc(self.keyboard.key_down)
        glutSpecialUpFunc(self.keyboard.key_up)
        glutWindowStatusFunc(self.on_window_status)

    def draw(self):

        # Default projection matrix puts the screen bounds at -1 to 1.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glClear(GL_COLOR_BUFFER_BIT)

        self.draw_bounding_box()
        self.game.draw()

        glFlush()
        glutSwapBuffers()

    def draw_bounding_box(self):
        #TODO: Only draw lines that aren't at the edge of the screen (ex: if
        #      width > height, draw only vertical lines to the left and right.
        if self.win_width > self.win_height:
            glColor3f(0.2, 0.2, 0.2)
            glBegin(GL_LINES)
            glVertex2f(-1.0, -1.0)
            glVertex2f(-1.0,  1.0)
            glVertex2f( 1.0, -1.0)
            glVertex2f( 1.0,  1.0)
            glEnd()
        elif self.win_width < self.win_height:
            glColor3f(0.2, 0.2, 0.2)
            glBegin(GL_LINES)
            glVertex2f(-1.0, -1.0)
            glVertex2f( 1.0, -1.0)
            glVertex2f(-1.0,  1.0)
            glVertex2f( 1.0,  1.0)
            glEnd()

    def reshape(self, win_width, win_height):
        self.win_width = win_width
        self.win_height = win_height
        if win_width > win_height:
            width = win_height
            height = win_height
            x = (win_width - win_height) / 2
            y = 0
        else:
            width = win_width
            height = win_width
            x = 0
            y = (win_height - win_width) / 2
        glViewport(int(x), int(y), width, height)

    def update(self, data=None):
        glutTimerFunc(20, self.update, None)
        t = time()
        if self.last_update_time:
            dt = t - self.last_update_time
        else:
            dt = 0
        game_finished = self.game.update(dt, self.keyboard)
        if game_finished:
            self.game = Game()
        self.last_update_time = t

        self.keyboard.tick()
        glutPostRedisplay()

    def on_window_status(self, status):
        self.keyboard.all_keys_up()

    def main_loop(self):
        glutMainLoop()

if __name__ == "__main__":
    GameInterface().main_loop()
