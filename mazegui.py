#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Graphical Maze generator app, written using PyQt5.
"""

import sys
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import *

from lib.mazemaker import MazeGenerator
from lib.util import *

class MazeGUI(QMainWindow):
    """
    Graphical Maze generator app, written using PyQt5.
    """

    def __init__(self, app, uifile):
        # Call the init function of the parent class (in this case, Qt's Window
        # class).
        super().__init__()

        # Use a thread-safe Event object to keep track of whether we've quit.
        self.has_quit = threading.Event()
        self.app = app

        # Initialize some variables. self.generated sets tells whether we've
        # generated a maze yet (draw won't do anything unless this is set).
        self.generated = False

        # These variables define point selections and static start/finish points.
        self.selected_point = (None, None)
        self.select_type = ''
        self.static_finish = None
        self.static_start = None

        # If this is True, the program will stop drawing and produce an error.
        self.draw_failed = False

        # Define sprites (characters, etc.) that applications using the MazeGUI
        # backend can use.
        self.sprites = []

        # Defines whether darkness should be enabled in the maze
        self.use_darkness = False

        # Default level data is empty.
        self.leveldata = {}

        # The actual GUI layout is made using a program called Qt Designer,
        # which lets you design graphical interfaces and save them as XML-format
        # .ui files. All this does is tell PyQt to load the UI file and display
        # its contents as the main window.
        self.ui = loadUi(uifile, self)
        self.ui.show()
        self.display = self.ui.display

        # Set up the Quit and About actions in the program menu.
        self.ui.actionQuit.triggered.connect(self.closeEvent)
        self.ui.actionAbout.triggered.connect(self.show_about)

        self.display.paintEvent = self.paintEvent

        # Lambda functions wrap around select_tile() so it's called with arguments
        debug_print("Connecting set static start/finish buttons")
        self.ui.set_static_start.clicked.connect(lambda: self.select_tile(type='start'))
        self.ui.set_static_finish.clicked.connect(lambda: self.select_tile(type='finish'))

        # These function overrides are for the static start/finish selecting part.
        # First step: enable mouse tracking, meaning an event is sent for
        # each mouse movement, and not just for clicks.
        self.display.setMouseTracking(True)

        self.display.mouseMoveEvent = self.mouseMoveEvent
        self.display.mousePressEvent = self.mousePressEvent

        self.setup_elements()

    def paintEvent(self, event):
        # In order to draw lines, shapes, etc. on a canvas, we use the QPainter
        # class.
        # QPainter() will only draw on widgets if called from the paintEvent()
        # function attached to it, so we must assign one for it here.
        # paintEvent() is automatically called for by Qt whenever the object
        # is moved, resized, etc.
        if not self.generated:
            return  # Don't do anything if no maze has been generated

        painter = QPainter()
        painter.begin(self.display)

        draw_result = self.draw_maze(painter, self.display.width(), self.display.height())
        if not draw_result:
            # draw_maze() returns False if something went wrong. We should display an error
            # if this happens, usually because the maze size requested was too big to draw
            # in our preview window.

            # Note: only show this error box ONCE! (check if self.draw_failed is set)
            # Otherwise, we will have a nasty recursive loop, since this function is
            # called every single time an UI element updates.
            debug_print("Hit paintEvent: draw_failed = %s" % self.draw_failed)
            if not self.draw_failed:
                QMessageBox.warning(self.ui, "Error", "Could not draw maze with the given size, as there is not enough space in the window! Try increasing the window size, or using image export instead.")

            self.draw_failed = True

        # Draw all our characters if defined. Do this in reversed order so that the earliest
        # created sprites get drawn on top.
        for character in self.sprites:
            #debug_print("Drawing character %s" % character)
            character.draw(painter)
        painter.end()

    # Override the mouseMoveEvent function in our display object
    # to track the mouse positions.
    def mouseMoveEvent(self, event):
        if not self.select_type:
            # No selection process is going on.
            return

        mouseposition = event.pos()
        debug_print(mouseposition)

        # Get the X and Y coordinates of the mouse, relative to the widget.
        xpos = mouseposition.x()
        ypos = mouseposition.y()

        # Find the X and Y positions of the mouse relative to the grid by
        # diving these by the tile width and height.
        xpos -= self.tile_width // 2
        ypos -= self.tile_height // 2
        xgridpos = int(xpos / self.tile_width)
        ygridpos = int(ypos / self.tile_height)
        debug_print(xgridpos, ygridpos)
        debug_print("self.select_type is %s" % self.select_type)

        for point in self.maze.all_items():
            # Mark all points in the maze as not selected.
            point.is_selected = False

        try:
            # Then, set the point that the mouse is hovering over
            # as selected.
            mazepoint = self.maze.get(xgridpos, ygridpos)
            self.selected_point = (xgridpos, ygridpos)
            mazepoint.is_selected = True
        except IndexError:
            return
        else:
            self.display.update()

    # Ditto with the mouse pressed event: when the display is pressed after
    # a point is chosen, make that the selected point and disable the
    # tile selection overlay.
    def mousePressEvent(self, event):
        if not (self.selected_point and self.select_type and self.generated):
            # No valid point was selected, or the selection overlay isn't enabled.
            return

        if self.select_type == 'start':
            if self.static_finish and self.selected_point == self.static_finish:
                # Error if the start point we're trying to set is the same as the static
                # finish.
                QMessageBox.critical(self.ui, "Setting point failed",
                                     "Cannot set the start and finish point to be the same point.")
                return

            self.static_start = self.selected_point
            debug_print("Set self.static_start to (%s, %s)" % self.selected_point)

            # Change the button text to "Clear fixed start point" instead of setting.
            self.set_static_start.setText("Clear fixed start point")

        elif self.select_type == 'finish':
            if self.static_start and self.selected_point == self.static_start:
                # Error if the finish point we're trying to set is the same as the static
                # start.
                QMessageBox.critical(self.ui, "Setting point failed",
                                     "Cannot set the start and finish point to be the same point.")
                return

            debug_print("Set self.static_finish to (%s, %s)" % self.selected_point)
            self.static_finish = self.selected_point

            self.set_static_finish.setText("Clear fixed finish point")

        # Disable any further selections until one of the "select tile" buttons are pressed.
        # Also unset the selected point so the red overlay goes away.
        self.select_type = ''
        self.maze.get(*self.selected_point).is_selected = False

        self.display.update()

    def closeEvent(self, event):
        """Quits the program cleanly by killing all threads."""
        self.has_quit.set()
        self.app.quit()

    def setup_elements(self):
        """Sets up extra elements specific to this window."""
        # Attach button widgets to their various functions.
        self.ui.save_image_button.clicked.connect(self.save_to_image)
        self.ui.generate_button.clicked.connect(self.make_maze)

    def show_about(self):
        """Shows the about window of the application."""
        about_window = loadUi('about.ui', QDialog())
        about_window.exec()

    def make_maze(self):
        """Generates a maze, overwriting any previously generated ones."""
        # Get the maze width and height from either the level data,
        # or the two spinbox (number input) elements.
        self.mazewidth = self.leveldata.get('width', self.ui.width_spinbox.value())
        self.ui.width_spinbox.setValue(self.mazewidth)
        self.mazeheight = self.leveldata.get('height', self.ui.height_spinbox.value())
        self.ui.height_spinbox.setValue(self.mazeheight)

        # Initialize the maze generator from the mazemaker.py module, and tell
        # it to get to work!
        self.mg = MazeGenerator(self.mazewidth, self.mazeheight)

        # Generate the maze! Static start and static finish are empty (nil) values
        # if not set, and will be ignored if so.
        debug_print("Calling make_maze() with start_point=%s, end_point=%s" % (self.static_start, self.static_finish))
        debug_print("Calling make_maze() with start_point=%s, end_point=%s" % (self.static_start, self.static_finish))

        try:
            self.maze = self.mg.generate(start_point=self.static_start, end_point=self.static_finish)
        except ValueError:
            # The maze we got wasn't random enough to get a path from the start to
            # finish. Regenerate the maze.
            self.make_maze()
        else:
            if self.mg.start.x == self.mg.finish.x and self.mg.start.y == self.mg.finish.y:
                # The start point and finish point landed on the same point.
                # This is also not random enough, so we should regenerate.
                self.make_maze()

            # "Difficulty" is determined by the distance between the start and finish points.
            # Level presets can choose a minimum difficulty, so the game is more balanced against
            # spawning the start and finish points too close.
            # This is ignored if the value is zero. The maximum allowed value is the smaller of the maze's width and height.
            self.ui.min_difficulty_spinbox.setMaximum(min(self.mazewidth, self.mazeheight))
            self.min_difficulty = self.leveldata.get('min_difficulty', self.ui.min_difficulty_spinbox.value())
            if self.min_difficulty:
                if self.static_finish or self.static_start:
                     QMessageBox.warning(self.ui, "Incompatible options selected", "Minimum difficulty cannot be tweaked in conjunction with static start/finish points. This setting will be ignored.")
                elif self.mg.distance(self.mg.start, self.mg.finish) < self.min_difficulty:
                    # Not difficult enough; regenerate the maze.
                    self.make_maze()

            self.generated = True

        # Poke the display to update itself
        self.display.update()

    def draw_maze(self, painter, width, height):
        """
        Draws a graphical representation of the currently stored maze, using
        the painter object, picture height, and picture width given.
        This returns True if successful, or False if an error occurred.
        """
        painter.setRenderHint(QPainter.Antialiasing)
        # Automatically find the best tile size for each piece of our maze by
        # finding the size of the display, and dividing that by the size of our
        # maze plus 1. There needs to be one grid tile more than the maze size,
        # in order to fit the boundaries of the maze in.
        self.tile_width = round_down_to_even(width / (self.mazewidth + 1))
        self.tile_height = round_down_to_even(height / (self.mazeheight + 1))

        if self.tile_width == 0 or self.tile_height == 0:
            # Oh no, our window size is too small for the maze! We can't draw
            # anything meaningful because our tile size is ZERO!
            return False

        if self.ui.force_square_tiles.isChecked():
            # If Force Square Tiles is set, set the tile height and width to the
            # smaller of the two. This makes sure that the maze fits on the display.
            self.tile_height = self.tile_width = min(self.tile_width, self.tile_height)

        #debug_print("Got tile size to be %s by %s" % (self.tile_width, self.tile_height))

        xpos = self.tile_width
        ypos = self.tile_height

        # Iterate over every point in the maze.
        for row in self.maze:
            for point in row:
                # The lines around each grid point in the maze is drawn relative to the
                # centre of that point. The distances between the lines and the centre of
                # the point we're on (xoffset and yoffset) are equal to half the tile width
                # or height.
                paths = point.paths
                xoffset = self.tile_width / 2
                yoffset = self.tile_height / 2

                def fill_tile():
                    # Fills in the tile with the specified colour.
                    painter.drawRect(xpos-xoffset, ypos-yoffset, self.tile_width, self.tile_height)

                painter.setPen(Qt.NoPen)
                if point.is_finish:
                    # Finish point is light blue.
                    #debug_print("Colouring point %s blue" % point)
                    painter.setBrush(QColor('#99BCFF'))
                elif point.is_start:
                    # Start point colour is light green.
                    painter.setBrush(QColor('#99FF99'))
                    #debug_print("Colouring point %s green" % point)
                else:
                    # Normal tile with no visible fill.
                    painter.setBrush(Qt.white)

                fill_tile()

                # Darkness mode is enabled. Every tile 1 or more away
                # from the player is covered in black at a certain opacity:
                # This will only work if there is a player in the game.
                if self.use_darkness and self.player:
                    # Fetch the flashlight radius, which defaults to half of
                    # the either the maze height or width, whichever is smaller.
                    flashlight_radius = self.leveldata.get('flashlight_radius') or \
                        min(self.mazewidth, self.mazeheight)//2+1
                    player_point = self.maze.get(self.player.x, self.player.y)
                    point_distance = self.mg.distance(player_point, point)

                    fill_color = QColor(0)  # Darkened tiles are black
                    # Derive the amount that the darkness should change with
                    # each point from the player by dividing 255 (the max.
                    # opacity value) by the flashlight radius.
                    # Then, multiply this amount by the point distance and
                    # to find the final opacity value.
                    flashlight_step = 255 // flashlight_radius
                    darkness_opacity = min(250, point_distance*flashlight_step)

                    #print('distance: %s, darkness_opacity: %s, f step: %s' % (point_distance, darkness_opacity, flashlight_step))
                    fill_color.setAlpha(darkness_opacity)

                    painter.setBrush(fill_color)
                    fill_tile()

                if point.is_selected:
                    # If the point is being selected (when choosing static start/finish tiles), fill
                    # it with dark red. Note: only do this after drawing darkness.
                    fill_color = QColor('#AA0000')
                    # Make this slightly transparent so finishes and other special points are visible.
                    fill_color.setAlpha(200)
                    painter.setBrush(fill_color)
                    fill_tile()

                # Pen class is used to draw outlines
                pen = QPen()

                # Set the pen size to an EVEN value, to prevent off-by-one drawing
                pensize = round_down_to_even(min(self.tile_width, self.tile_height) // 24)
                # Minimum pen size is 2
                pen.setWidth(max(2, pensize))

                # Set whether pen scales with the painter object
                pen.setCosmetic(True)

                pen.setColor(Qt.black)
                painter.setPen(pen)

                # Draw the walls around each tile in order to form the actual maze. This is
                # done using lines relative to the center of each tile (the xpos and ypos),
                # where the x and y offsets are half the tile width and height, respectively.
                # FIXME: there are some off by ones in drawing southeast corners that I'm not
                # quite sure how to fix...
                if 'north' not in paths:
                    painter.drawLine(xpos-xoffset, ypos-yoffset, xpos+xoffset-pensize//2, ypos-yoffset)
                if 'south' not in paths:
                    painter.drawLine(xpos-xoffset, ypos+yoffset, xpos+xoffset, ypos+yoffset)
                if 'east' not in paths:
                    painter.drawLine(xpos+xoffset, ypos-yoffset, xpos+xoffset, ypos+yoffset)
                if 'west' not in paths:
                    painter.drawLine(xpos-xoffset, ypos-yoffset, xpos-xoffset, ypos+yoffset)

                # After each point is drawn, add the tile width  to the x position
                # to move on to the next point.
                xpos += self.tile_width

            # At the end of each row, reset the x position to the beginning, and add the
            # tile height to the y position.
            xpos = self.tile_width
            ypos += self.tile_height

        return True

    def select_tile(self, type):
        """
        Turns on tile-selection mode for the given type. Type can be one of 'start', 'finish', or
        'clear'.
        """
        debug_print('select_tile called')
        if not self.generated:
            # If we haven't generated a maze yet, there are no tiles to select!
            QMessageBox.critical(self.ui, "Error", "Run Generate first before selecting tiles!")
            return

        if self.leveldata and type != 'clear':
            QMessageBox.critical(self.ui, "Error", "Cannot mix tile selection with loaded levels!")
            return

        if self.static_start and type == 'start':
            # If a point was already selected, we want the buttons to clear the
            # fixed start / finish tile.
            try:
                self.maze.get(*self.static_start).is_start = False
            except:
                # If this errors, just ignore it.
                pass
            self.static_start = None

            # After the static point is cleared, the button should read
            # "Set static start" instead of "Clear static start".
            debug_print('select_tile: resetting "Set fixed start point" text')
            self.set_static_start.setText("Set fixed start point")

        elif self.static_finish and type == 'finish':
            # Ditto above; make the button clear static finishes if one was already set.
            try:
                self.maze.get(*self.static_finish).is_finish = False
            except:
                pass
            self.static_finish = None
            debug_print('select_tile: resetting "Set fixed finish point" text')
            self.set_static_finish.setText("Set fixed finish point")

        elif type == 'clear':
            self.set_static_start.setText("Set fixed start point")
            self.set_static_finish.setText("Set fixed finish point")
            self.select_type = None
        else:
            # Set the type of selection to the type given (start or finish).
            # The mouseMoveEvent and mousePressEvent handlers in the main
            # display will then be activated when the user moves the mouse
            # over the display.
            debug_print('select_tile: updating select_type to %s' % type)
            self.select_type = type

    def save_to_image(self):
        """Runs the process for saving generated mazes to image."""
        if not self.generated:
            # If we haven't generated a maze yet, then there's nothing that can be saved as an image... Error accordingly.
            QMessageBox.critical(self.ui, "Error", "Run Generate first before exporting as image!")
            return

        # Create an instance of QFileDialog, a file chooser screen
        filepicker = QFileDialog()

        # Show a list of supported file extensions. The default export format will be set
        # to .PNG if not given, but other image formats can be picked too.
        # setNameFilter() only needs to be given a specially formatted string
        # "<name of type> (*.extension1 *.extension2)" in order to process which extensions
        # we should show. Afterwards, the image writer is smart enough to tell which format
        # type to write to simply by looking at the file extension.
        filepicker.setDefaultSuffix('png')
        filepicker.setNameFilter("Image files (*.bmp *.jpg *.jpeg *.png *.ppm *.xbm *.xpm)")

        # Set a relevant window title
        filepicker.setWindowTitle('Save as image')

        # Set this file picker to be a Save file dialog instead of an Open file dialog.
        filepicker.setAcceptMode(QFileDialog.AcceptSave)

        # Now, run the file picker dialog. exec_() makes the dialog modal, so the
        # application stops doing everything else until it is closed.
        filepicker.exec_()

        # Fetch the filename from the dialog.
        files = filepicker.selectedFiles()

        if not files:
            # The user hit cancel or failed to get a valid filename. Abort.
            return

        filename = files[0]

        width = self.ui.image_tile_size.value() * (self.mazewidth + 1)
        height = self.ui.image_tile_size.value() * (self.mazeheight + 1)

        # Create an empty image object. Simple RGB should do for colours.
        # TODO: configurable image size
        image = QImage(width, height, QImage.Format_RGB32)

        # Default image background is black, so we'd be drawing black lines on a black
        # background without this...
        image.fill(Qt.white)

        # Create another lovely QPainter instance. Instead of drawing on a widget using paintEvent,
        # this time we're drawing on an image instance (QImage).
        painter = QPainter()
        painter.begin(image)
        self.draw_maze(painter, width, height)
        painter.end()

        if not image.save(filename):
            # QImage().save() returns True if successful, and False if something went wrong.
            # In this app, a likely source of error is if someone put an invalid file extension,
            # or one that the image writer doesn't understand, as the export filename.
            QMessageBox.critical(self.ui, "Image export failed", "Image export failed. Check to make sure the file name given corresponds to a supported image format!")
            return

if __name__ == '__main__':
    # Start the application by initializing a QApplication instance.
    app = QApplication(sys.argv)

    # Initialize the GUI instance.
    gui = MazeGUI(app, 'mazegui.ui')

    # Handle quits properly, exiting using the GUI app's exit code.
    sys.exit(app.exec_())
