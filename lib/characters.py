###
# Copyright (c) 2016 James Lu <glolol@overdrivenetworks.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###

"""Sprites module for TrulyAmazed."""

import random

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .util import *

# All of these Qt.Key_XYZ values are pre-defined; see
# https://doc.qt.io/qt-5/qt.html#Key-enum for a list.
key_directions = {Qt.Key_Up: 'north', Qt.Key_Down: 'south',
                  Qt.Key_Right: 'east', Qt.Key_Left: 'west'}

class Sprite():
    """
    Generic sprite class.
    """

    def __init__(self, game, x=None, y=None, color='#654678'):
        # Character colour
        self.color = color

        # Store the MazeGame instance too for reference.
        self.game = game

        # Defines a list of types that the object CAN'T collide with.
        self.collision_blacklist = []

        self.reset_coords(x, y)

    def reset_coords(self, x=None, y=None):
        """
        Resets the sprite's coords to match the maze's
        start point.
        """
        # Stores the character's initial x and y positions, relative
        # to the grid, along with the grid boundaries. If not defined,
        # this will be equal to the maze's starting point.
        self.x = x
        self.y = y

        if self.x is None:
            self.x = self.game.mg.start.x
        if self.y is None:
            self.y = self.game.mg.start.y

        # Save the boundaries of the moving area too.
        self.max_x = self.game.mazewidth
        self.max_y = self.game.mazeheight

    def check_collision(self):
        """
        Checks collisions with other objects in game, and returns the amount of items
        collided with.
        """
        hit = 0
        for obj in self.game.sprites:
            if obj == self or obj.__class__ in self.collision_blacklist:
                # Don't allow objects to collide with themselves, or anything on
                # their collision blacklist.
                continue
            if obj.x == self.x and obj.y == self.y and hasattr(obj, 'hit'):
                debug_print("check_collision: Calling hit() on %s (%s, %s)" % (obj, self.x, self.y))
                # Call the hit() function defined in the other object,
                # but only if it is defined.
                obj.hit(self)
                hit += 1

        return hit

    def predraw(self):
        """
        Initializes variables for the drawing process, such as X and Y positions,
        to make drawing easier for subclasses.
        """
        # From https://doc.qt.io/qt-5/qrectf.html and
        # https://doc.qt.io/qt-5/qpainter.html#drawEllipse
        # To paint an ellipse in Qt, what we first have to do is initialize
        # a rectangle, which takes the first two arguments as the X and Y
        # coordinates of the rectangle's top left, and the last two arguments
        # as the rectangle's width and height. Here, this is based off the
        # character's grid position and the tile size.

        self.tilewidth = self.game.tile_width
        self.tileheight = self.game.tile_height

        # Initialize the x positions of the canvas on the left side,
        # center, and right side of the grid point we're on.
        self.xpos_left = self.x * self.tilewidth
        self.xpos_center = self.xpos_left + (3*self.tilewidth//4)
        self.xpos_right = self.xpos_left + self.tilewidth

        # Similarly, initialize the y positions on the top, center, and bottom
        # of the current grid point.
        self.ypos_top = self.y * self.tileheight
        self.ypos_center = self.ypos_top + (3*self.tileheight//4)
        self.ypos_bottom = self.ypos_top + self.tileheight

        self.tilewidth = self.game.tile_width

        # Draw characters half the width and height of the tile size, rounded
        # down to the nearest even number.
        self.charwidth = round_down_to_even(self.tilewidth//2)
        self.charheight = round_down_to_even(self.tileheight//2)

    def draw(self, painter):
        """
        Draws this character (an ellipse 1/2 of the tile size, rounded down to
        the nearest even number).
        """
        self.predraw()
        rect = QRectF(self.xpos_center, self.ypos_center, self.charwidth, self.charheight)

        # Set the right brush colour first
        painter.setBrush(QColor(self.color))

        painter.drawEllipse(rect)

    def hit(self, source):
        """
        This trigger activates when the object is touched. Subclasses must redefine this.
        """

        raise NotImplementedError

    def try_move(self, direc):
        """
        Tries to move the character 1 point in the given
        direction. key is the key code of the arrow key pressed.
        """

        if self.__class__ == PlayerCharacter and self.game.is_game_over:
            # We've lost; disallow movement.
            return False

        current_point = self.game.maze.get(self.x, self.y)
        debug_print("Trying to move from (%s, %s)" % (self.x, self.y))

        # This wall-checking code becomes a lot simpler now, though a bit
        # repetitive. Basically, check if the requested direction has a valid
        # path from the current point, and move successfully in that direction
        # only if this is True.
        self.facing = direc
        if direc in current_point.paths:
            if direc == 'north':
                # Move success, update the x or y coords of the character accordingly.
                self.y -= 1
            elif direc == 'south':
                self.y += 1
            elif direc == 'west':
                self.x -= 1
            elif direc == 'east':
                self.x += 1
            debug_print("Moved to (%s, %s)" % (self.x, self.y))
            self.game.display.update()
            return True
        return False

    def remove(self):
        """
        Removes the current object from the sprites object.
        """
        self.game.sprites.remove(self)
        self.game.display.update()

class PlayerCharacter(Sprite):
    """
    Character class that represents the player in the game.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facing = 'north'

    def check_win(self):
        """Checks whether we've won the game."""
        if self.game.checkpoints_hit < self.game.checkpoint_count:
            # User didn't hit all the checkpoints yet.
            return False
        if self.game.is_game_over:
            return False
        return (self.x == self.game.mg.finish.x and self.y == self.game.mg.finish.y)

    def shoot(self):
        """Shoots a laser in the current facing direction."""

        gunshot_fuel = self.game.leveldata.get("gunshot_fuel", self.game.ui.gunshot_fuel_spinbox.value())
        self.game.ui.gunshot_fuel_spinbox.setValue(gunshot_fuel)

        if self.game.fuel > gunshot_fuel:
            # Only allow shooting if we have enough fuel.
            self.game.update_fuel(-gunshot_fuel)
            self.game.sprites.append(Laser(self.game, self.facing, self.x, self.y))

    def bind(self):
        def keyPressEvent(event):
            """Handles key press events."""
            # Try to move in the direction given if an arrow key is pressed.
            direc = key_directions.get(event.key())

            if event.key() == Qt.Key_Space and not self.game.is_game_over:
                # Arrow keys to shoot.
                self.shoot()
                return
            elif QApplication.keyboardModifiers() == Qt.ShiftModifier:
                # Hold shift and arrow keys to move in place.
                if direc:
                    self.facing = direc
                return
            elif direc:
                self.try_move(direc)
                # Check for collisions with any objects.
                self.check_collision()

            # Then, check if we've won, and move to the next level if we have.
            if self.check_win():

                # Optionally, give the player a fuel bonus, if configured or defined by the level.
                bonus = self.game.leveldata.get('finish_bonus', self.game.ui.finish_bonus_spinbox.value())
                self.game.ui.finish_bonus_spinbox.setValue(bonus)

                debug_print("Adding finish bonus of %s" % bonus)
                self.game.update_fuel(bonus)

                self.game.current_level += 1
                self.game.update_current_level()

                # We reached the last stage. Finish the game and display score.
                if self.game.leveldata.get('winning_stage'):
                    self.game.game_over(win=True)
                    return
                elif self.game.levels:
                    # Level pack is loaded; try to find the next level definition.
                    try:
                        # If we run out of levels, just keep the settings of the last one.
                        self.game.leveldata = self.game.levels[self.game.current_level]
                    except IndexError:
                        pass

                # Generate the next level.
                debug_print('player.keyPressEvent: calling make_maze(reset_state=False)')
                self.game.make_maze()

            # Refresh the game display.
            self.game.display.update()

        self.game.ui.keyPressEvent = keyPressEvent

    def hit(self, source):
        pass

class FuelPack(Sprite):
    # Redefine the fuel pack as a different colour.
    def __init__(self, game, x=None, y=None, color='#FAE793'):
        super().__init__(game, x, y, color)

    def hit(self, source):
        """
        Method called to remove the fuel pack and take its contents.
        """
        # Amount of fuel in each fuel pack can be overridden by
        # levels, and defaults to the value in the config.
        amount = self.game.leveldata.get('fuel_pack_amount', self.game.ui.fuel_pack_amount_spinbox.value())
        self.game.ui.fuel_pack_amount_spinbox.setValue(amount)

        self.game.update_fuel(amount)

        # Delete the fuel pack from the objects list.
        self.remove()

class Laser(Sprite):
    def __init__(self, game, direc, x=None, y=None, color='#22FF22'):
        super().__init__(game, x, y, color)
        # Start a timer to track the laser's movement.
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.laser_loop)
        self.move_timer.start(100)
        self.facing = direc

        self.collision_blacklist = [self.__class__, PlayerCharacter]

    def laser_loop(self):
        """Tracks the laser's movement in a loop."""
        if self.game.has_quit.is_set() or self.game.is_game_over:
            # Game quit or user lost. Remove lasers.
            self.remove()
            return

        # Check if the object collides with anything. If so,
        # the laser is destroyed.
        if self.check_collision():
            debug_print("Laser removed at (%s, %s)" % (self.x, self.y))
            self.remove()
            return

        if not self.try_move(self.facing):
            # Try to move the laser. If this fails, the laser
            # is removed.
            self.remove()
            return

    def hit(self, source):
        pass

    def draw(self, painter):
        """
        Draws the laser as a laser beam.
        """
        self.predraw()
        if self.facing == 'north':
            rect = QRectF(self.xpos_center, self.ypos_top, self.charwidth, self.tileheight)
        elif self.facing == 'south':
            rect = QRectF(self.xpos_center, self.ypos_center, self.charwidth, self.tileheight)
        elif self.facing == 'east':
            rect = QRectF(self.xpos_center, self.ypos_center, self.tilewidth, self.charheight)
        elif self.facing == 'west':
            rect = QRectF(self.xpos_left, self.ypos_center, self.tilewidth, self.charheight)

        # Draw the laser beam slightly transparent.
        color = QColor(self.color)
        color.setAlphaF(0.7)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        painter.drawRect(rect)

class Enemy(Sprite):
    def __init__(self, game, x=None, y=None, color='#FE1111'):
        super().__init__(game, x, y, color)

        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.enemy_move_loop)
        move_delay = self.game.leveldata.get('enemy_move_delay', self.game.ui.move_delay_spinbox.value())

        if move_delay > 0:
            # If move delay is 0, disable movement for enemies entirely.
            self.game.ui.move_delay_spinbox.setValue(move_delay)
            self.move_timer.start(move_delay)
        self.direc = None

    def hit(self, source):
        """
        Method called when you hit an enemy.
        """
        if source.__class__ == PlayerCharacter:
            self.game.game_over()
        else:
            self.remove()

    def enemy_move_loop(self):
        """Tracks the laser's movement in a loop."""
        if self.game.has_quit.is_set() or self.game.is_game_over:
            return

        current_point = self.game.maze.get(self.x, self.y)
        # Enemies try to move in a straight line, turning around only if that fails
        # due to a wall in the way.
        if self.direc not in current_point.paths:
            # Direction to move in hasn't been initialized yet. Randomly choose
            # one.
            self.direc = random.choice(list(current_point.paths))

        if not self.try_move(self.direc):
            self.direc = random.choice(list(current_point.paths))

class Checkpoint(Sprite):
    def __init__(self, game, x=None, y=None, color='#FE55AA'):
        super().__init__(game, x, y, color)

    def hit(self, source):
        """
        Method called when the player hits a checkpoint.
        """
        if source.__class__ == PlayerCharacter:
            self.game.checkpoints_hit += 1
            self.remove()

    def draw(self, painter):
        """
        Draws this checkpoint (a small square).
        """
        self.predraw()
        rect = QRectF(self.xpos_center, self.ypos_center, self.charwidth, self.charheight)

        # Set the right brush colour first
        painter.setBrush(QColor(self.color))

        painter.drawRect(rect)