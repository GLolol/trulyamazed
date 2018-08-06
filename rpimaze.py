import sys
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
#from PyQt5.QtCore import *

GPIO_PIN = 18
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
INTENSITY = 12
SHOW_DUMMY_VALUES = False

try:
    from neopixel import *
except ImportError:
    print("neopixel NOT FOUND - using dummy placeholder library instead.")
    class Dummy_NeoPixel:
        def __init__(self, npixels, *args, **kwargs):
            self._npixels = npixels
            self._data = [None for _ in range(npixels)]

        def begin(self):
            pass

        def show(self):
            if SHOW_DUMMY_VALUES:
                for idx, color in enumerate(self._data):
                    print("Pixel #%s: %s" % (idx, color))

        def setPixelColorRGB(self, target, *color):
            try:
                self._data[target] = color
            except IndexError:
                print("Out of range target %s" % target)
            print("Setting pixel %s to %s" % (target, str(color)))

    Adafruit_NeoPixel = Dummy_NeoPixel

from mazegame import MazeGame

class RPiMaze(MazeGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up NeoPixel
        self.np = Adafruit_NeoPixel(NUM_PIXELS, GPIO_PIN, brightness=INTENSITY)
        self.np.begin()

    @staticmethod
    @functools.lru_cache(maxsize=512)
    def _get_serpentine_point(x, y):
        """
        Returns the point in the serpentine LED pattern given x and y coordinates.
        """
        # The LEDs on a matrix are wired so that the array of LEDs are sorted this way:

        #top left
        #  7  6  5  4  3  2  1  0
        #  8  9 10 11 12 13 14 15
        # 23 22 21 20 19 18 17 16
        # 24 25 26 27 28 29 30 31
        # 39 38 37 36 35 34 33 32
        #                  bottom right

        # ..., where every even row (indexing from 0) is in reverse

        result = (y * MATRIX_WIDTH) + ((MATRIX_WIDTH - x - 1) if (y % 2 == 0) else (x))
        return result

    def draw_point_at(self, x, y, color):
        # Don't try to draw out of bounds
        if y > (MATRIX_HEIGHT-1) or y < 0:
            print("Ignoring out of bound point %s, %s" % (x, y))
            return
        if x > (MATRIX_WIDTH-1) or x < 0:
            print("Ignoring out of bound point %s, %s" % (x, y))
            return

        target = self._get_serpentine_point(x, y)
        self.np.setPixelColorRGB(target, *color)

    def _draw_walls(self, wall_points_to_draw):
        for point in wall_points_to_draw:
            print("Drawing LED point %s, %s as a wall" % (point[0], point[1]))
            self.draw_point_at(point[0], point[1], (255, 255, 255))

    def draw_maze_leds(self):
        """
        Draws the maze on an LED strip.
        """
        for pixel in range(NUM_PIXELS):
            self.np.setPixelColorRGB(pixel, 0, 0, 0)
        for ypos, row in enumerate(self.maze):
            for xpos, point in enumerate(row):
                if point.is_finish:
                    color = (0, 0, 255)
                elif point.is_start:
                    color = (255, 255, 0)
                else:
                    # Empty tile
                    color = (0, 0, 0)

                for sprite in self.sprites:
                    if sprite.x == xpos and sprite.y == ypos:
                        # https://stackoverflow.com/a/29643643 TODO: abstract this out some more
                        color = tuple(int(sprite.color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        print("Setting color to %s for sprite %s at %s, %s" % (color, sprite, xpos, ypos))

                if point.is_selected:
                    color = (130, 0, 250)

                led_xpos = xpos * 2
                led_ypos = ypos * 2
                print("Translating player position (%s, %s) into LED position (%s, %s)" % (xpos, ypos, led_xpos, led_ypos))

                wall_points_to_draw = {
                    (led_xpos-1, led_ypos-1),
                    (led_xpos-1, led_ypos+1),
                    (led_xpos+1, led_ypos-1),
                    (led_xpos+1, led_ypos+1)
                }
                paths = point.paths
                if 'north' not in paths:
                    wall_points_to_draw.add((led_xpos, led_ypos-1))
                if 'south' not in paths:
                    wall_points_to_draw.add((led_xpos, led_ypos+1))
                if 'east' not in paths:
                    wall_points_to_draw.add((led_xpos+1, led_ypos))
                if 'west' not in paths:
                    wall_points_to_draw.add((led_xpos-1, led_ypos))

                self._draw_walls(wall_points_to_draw)
                self.draw_point_at(led_xpos, led_ypos, color)
        self.np.show()

    def draw_maze(self, *args, **kwargs):
        super().draw_maze(*args, **kwargs)
        self.draw_maze_leds()
        return True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = RPiMaze(app, 'mazegame.ui')
    sys.exit(app.exec_())
