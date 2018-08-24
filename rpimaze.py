#!/usr/bin/env python3
import sys
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
#from PyQt5.QtCore import *

GPIO_PIN = 10
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
INTENSITY = 20
SHOW_DUMMY_VALUES = False

try:
    from neopixel import Adafruit_NeoPixel, Color
except ImportError:
    print("neopixel NOT FOUND - using dummy placeholder library instead.")
    class Dummy_NeoPixel:
        def __init__(self, npixels, *args, **kwargs):
            self._npixels = npixels
            self._led_data = [None for _ in range(npixels)]

        def begin(self):
            pass

        def show(self):
            if SHOW_DUMMY_VALUES:
                for idx, color in enumerate(self._led_data):
                    print("Pixel #%s: %s" % (idx, color))

        def setPixelColorRGB(self, target, *color):
            self._led_data[target] = Color(*color)
            print("Setting pixel %s to %s" % (target, str(color)))

    # From rpi_ws281x library
    def Color(red, green, blue, white=0):
        """Convert the provided red, green, blue color to a 24-bit color value.
        Each color component should be a value 0-255 where 0 is the lowest intensity
        and 255 is the highest intensity.
        """
        return (white << 24) | (red << 16) | (green << 8) | blue

    Adafruit_NeoPixel = Dummy_NeoPixel

from mazegame import MazeGame
from lib import grid

class RPiMaze(MazeGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up NeoPixel
        self.np = Adafruit_NeoPixel(NUM_PIXELS, GPIO_PIN, brightness=INTENSITY)
        self.np.begin()

        # Chain our SerpentineGrid instance directly into the NeoPixel data.
        self.led_grid = grid.SerpentineGrid(grid.SerpentinePattern.TOP_RIGHT, data=self.np._led_data,
                                            width=MATRIX_WIDTH, height=MATRIX_HEIGHT)

    @staticmethod
    def hexcolor_to_rgb(colorstr):
        # https://stackoverflow.com/a/29643643 TODO: abstract this out some more
        color = tuple(int(colorstr.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        print("%s: %s" % (colorstr, str(color)))
        return color

    def draw_point_at(self, x, y, color):
        real_color = Color(color[1], color[2], color[0])
        try:
            self.led_grid.set(x, y, real_color, allowOverwrite=True)
        except IndexError:
            pass

    def _draw_walls(self, wall_points_to_draw):
        for point in wall_points_to_draw:
            #print("Drawing LED point %s, %s as a wall" % (point[0], point[1]))
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
                    color = self.hexcolor_to_rgb(self.FINISH_COLOR)
                elif point.is_start:
                    color = self.hexcolor_to_rgb(self.START_COLOR)
                else:
                    # Empty tile
                    color = (0, 0, 0)

                for sprite in self.sprites:
                    if sprite.x == xpos and sprite.y == ypos:
                        color = self.hexcolor_to_rgb(sprite.color)
                        print("Setting color to %s for sprite %s at %s, %s" % (color, sprite, xpos, ypos))

                if point.is_selected:
                    color = self.hexcolor_to_rgb(self.SELECTED_COLOR)

                led_xpos = xpos * 2
                led_ypos = ypos * 2
                #print("Translating player position (%s, %s) into LED position (%s, %s)" % (xpos, ypos, led_xpos, led_ypos))

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
        self.led_grid.show()

    def draw_maze(self, *args, **kwargs):
        super().draw_maze(*args, **kwargs)
        self.draw_maze_leds()
        return True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = RPiMaze(app, 'mazegame.ui')
    sys.exit(app.exec_())
