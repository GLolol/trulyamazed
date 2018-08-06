import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
#from PyQt5.QtCore import *

from neopixel import *

from mazegame import MazeGame


GPIO_PIN = 18
MATRIX_WIDTH = 15
MATRIX_HEIGHT = 15
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
INTENSITY = 12

class RPiMaze(MazeGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_leds()
    
    def init_leds(self):
        self.np = Adafruit_NeoPixel(NUM_PIXELS, GPIO_PIN, brightness=INTENSITY)
        self.np.begin()

    def draw_point_at(self, x, y, color):
        if y > (MATRIX_HEIGHT-1) or y < 0:
            return
        if x > (MATRIX_WIDTH-1) or x < 0:
            return
        
        target = 0
        # https://stackoverflow.com/questions/33059850/
        if y % 2 != 0:
            target = -x + MATRIX_WIDTH * (MATRIX_HEIGHT - y + 1);
        else:
            target = x - 1 + MATRIX_WIDTH * (MATRIX_HEIGHT - y);
        
        self.np.setPixelColorRGB(target, *color)
        

    def _draw_walls(self, wall_points_to_draw):
        for point in wall_points_to_draw:
            self.draw_point_at(point[0], point[1], (255, 255, 255))

    def draw_maze_leds(self):
        """
        Draws the maze on an LED strip.
        """
        for ypos, row in enumerate(self.maze):
            for xpos, point in enumerate(row):
                if point.is_finish:
                    color = (0, 0, 255)
                elif point.is_start:
                    color = (255, 255, 0)
                else:
                    # Empty tile
                    color = (0, 0, 0)

                if point.is_selected:
                    color = (130, 0, 250)
                
                led_xpos = xpos * 2
                led_ypos = ypos * 2
                
                wall_points_to_draw = [
                    (led_xpos-1, led_ypos-1),
                    (led_xpos-1, led_ypos+1),
                    (led_xpos+1, led_ypos-1),
                    (led_xpos+1, led_ypos+1)
                ]
                paths = point.paths
                if 'north' not in paths:
                    wall_points_to_draw.append((led_xpos, led_ypos-1))
                if 'south' not in paths:
                    wall_points_to_draw.append((led_xpos, led_ypos+1))
                if 'east' not in paths:
                    wall_points_to_draw.append((led_xpos+1, led_ypos))
                if 'west' not in paths:
                    wall_points_to_draw.append((led_xpos+1, led_ypos))
                
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
