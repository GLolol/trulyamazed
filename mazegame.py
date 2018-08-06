#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###
# Copyright (c) 2016, 2018 James Lu <james@overdrivenetworks.com>

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
import random
import json
import traceback
import os.path

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import *

from lib.mazemaker import debug_print
from mazegui import MazeGUI
from lib.characters import *
from lib.util import *
from config import *

class MazeGame(MazeGUI):
    """
    Subclass of the GUI maze app with custom controls.
    """

    def __init__(self, app, uifile):
        # Define variables.
        self.fuel_timer = None
        self.player = None
        self.sprites = []
        self.started = False
        self.fuel = None
        self.starting_fuel = None
        self.levels = []

        super().__init__(app, uifile)
        self.reset_state()

    def _sync_level_state(self):
        """Syncs level settings with the configuration fields."""
        # Update the level settings: darkness, number of fuel packs, number of enemies, etc.
        # If no level is being loaded, fetch these values from our UI. But, also update the UI
        # elements if any values change due to level loading.

        self.use_darkness = self.leveldata.get('darkness', self.ui.enable_darkness.isChecked())
        self.use_fuel = self.leveldata.get('use_fuel', self.ui.enable_fuel.isChecked())
        self.ui.enable_darkness.setChecked(self.use_darkness)
        self.ui.enable_fuel.setChecked(self.use_fuel)

        caption = self.leveldata.get("caption", welcome_caption)
        self.ui.caption.setText(caption)

        # Update static start / finish settings, but only if it has changed.

        self.static_start = self.leveldata.get('static_start', self.static_start)
        self.static_finish = self.leveldata.get('static_finish', self.static_finish)

        # Clear the sprites list.
        self.sprites.clear()
        self.checkpoints_hit = 0

    def _get_unused_points(self):
        """Returns all points that aren't the start or finish."""
        allowed_points = self.maze.all_items()
        allowed_points.remove(self.mg.start)
        allowed_points.remove(self.mg.finish)
        return allowed_points

    def _get_unused_endpoints(self):
        """Returns all end points that aren't the start or finish."""
        unused_endpoints = list(self.mg.end_points)
        try:
            unused_endpoints.remove(self.mg.start)
        except ValueError:
            pass

        try:
            unused_endpoints.remove(self.mg.finish)
        except ValueError:
            pass

        return unused_endpoints

    def make_maze(self, reset_state=False):
        """
        Generates the maze.
        """
        self._sync_level_state()

        if reset_state:
            # Reset the score, but only if we've been told to do
            # so.
            debug_print("make_maze: resetting state")
            self.reset_state()

        super().make_maze()

        if self.player:
            # Reset the player's position, if one exists.
            self.player.reset_coords()
            # Focus the display, so arrow keys instantly work.
            self.display.setFocus()

            # Re-add the player into the sprites list.
            self.sprites.append(self.player)

        self._make_fuel_packs()
        self._make_enemies()
        self._make_checkpoints()

    def _make_fuel_packs(self):
        # Fuel packs count cannot be greater than the amount of tiles in the maze
        # (excluding start and finish points)!
        self.fuelpacks_count = self.leveldata.get('fuel_packs', self.ui.fuelpacks_spinbox.value())
        available_points = self._get_unused_points()
        self.fuelpacks_count = min(len(available_points), self.fuelpacks_count)
        self.ui.fuelpacks_spinbox.setValue(self.fuelpacks_count)

        for point in random.sample(available_points, self.fuelpacks_count):
            debug_print('Spawning fuel pack at (%s, %s)' % (point.x, point.y))
            fp = FuelPack(self, point.x, point.y)
            self.sprites.append(fp)

    def _make_enemies(self):
        available_points = self._get_unused_points()
        self.enemy_count = self.leveldata.get('enemies', self.ui.enemies_spinbox.value())
        self.enemy_count = min(len(available_points), self.enemy_count)
        self.ui.enemies_spinbox.setValue(self.enemy_count)

        for point in random.sample(available_points, self.enemy_count):
            fp = Enemy(self, point.x, point.y)
            self.sprites.append(fp)

    def _make_checkpoints(self):
        # For checkpoints, choose random dead ends on the maze.
        # Don't allow checkpoints to spawn on the start or finish, however.
        valid_endpoints = self._get_unused_endpoints()

        self.checkpoint_count = self.leveldata.get('checkpoints', self.ui.checkpoints_spinbox.value())
        debug_print("_make_checkpoints: Found %s endpoints, wanted %s" % (len(valid_endpoints), self.checkpoint_count))
        self.checkpoint_count = min(len(valid_endpoints), self.checkpoint_count)
        self.ui.checkpoints_spinbox.setValue(self.checkpoint_count)

        for point in random.sample(valid_endpoints, self.checkpoint_count):
            fp = Checkpoint(self, point.x, point.y)
            self.sprites.append(fp)

    def draw_maze(self, painter, width, height):
        retcode = super().draw_maze(painter, width, height)

        if retcode:
            for character in self.sprites:
                #debug_print("Drawing character %s" % character)
                character.draw(painter)
        return retcode

    def reset_state(self, level=0):
        """
        Resets the game state (fuel, game over setting, levels list, etc.).
        """
        self.update_fuel(0, reset=True)
        self.is_game_over = False

        self.current_level = level
        self.update_current_level()

    def update_current_level(self):
        """Updates the current level display."""
        level = self.current_level+1
        text = "Current level: %s" % level

        self.ui.current_level_text.setText(text)

    def setup_elements(self):
        """
        Initializes the game by generating a maze and binding widgets to their
        corresponding functions.
        """
        # Explicitly call make_maze() with reset_state set to True. For some reason,
        # the implicit reset_state=True doesn't work when binding widgets.
        def generatebutton():
            self.clear_settings()
            self.make_maze(reset_state=True)
        self.ui.generate_button.clicked.connect(generatebutton)
        self.make_maze()

        # Export levels button
        self.ui.export_levels_button.clicked.connect(self.export_settings)
        # Load levels button
        self.ui.load_levels_button.clicked.connect(self.load_settings)
        # Clear levels button
        self.ui.clear_levels_button.clicked.connect(self.clear_settings)
        # Load progress button
        self.ui.load_progress_button.clicked.connect(self.load_savefile)
        # Save progress button
        self.ui.save_progress_button.clicked.connect(self.export_savefile)

        # Initialize our character class, and bind it to the maze game so that
        # it is drawn whenever requested.
        self.player = PlayerCharacter(self)
        self.player.bind()
        self.sprites.append(self.player)

        # Start a threaded loop to decrease the fuel count gradually,
        # if darkness is enabled.
        def decrease_fuel_loop():
            if self.has_quit.is_set():
                return

            if self.use_fuel and not self.is_game_over:
                self.update_fuel(-1)

        if self.fuel_timer is None:
            # Only spawn this thread ONCE.
            self.fuel_timer = QTimer()
            self.fuel_timer.timeout.connect(decrease_fuel_loop)
            self.fuel_timer.start(100)

        self.ui.show()

    def update_fuel(self, amount, reset=False):
        """
        Updates the fuel count by the given amount, fuel being essentially the player
        needs to survive. If the replace option is enabled, the amount number is ignored
        and the fuel count reset to its original value.
        """

        if reset:
            self.starting_fuel = self.leveldata.get('starting_fuel',
                self.ui.starting_fuel_spinbox.value())
            fuel = self.fuel = amount or self.starting_fuel
            self.ui.starting_fuel_spinbox.setValue(self.starting_fuel)
            debug_print("Resetting self.fuel to %s, self.starting_fuel to %s" % (fuel,
                        self.starting_fuel))
            self.ui.fuel_remaining.setValue(fuel)
            self.ui.fuel_remaining.setMaximum(self.starting_fuel)
            return

        if self.fuel is None:
            return  # Fuel count not initialized yet, ignore.
        elif (self.fuel + amount) > self.starting_fuel:
            # Don't allow the fuel count to go over the maximum (this
            # breaks the progress bar widget)
            self.fuel = self.starting_fuel

        self.fuel += amount
        if self.fuel < 0:
            # If the fuel remaining becomes negative, the player loses the game.
            self.game_over()
            return

        self.ui.fuel_remaining.setValue(self.fuel)
        self.ui.fuel_remaining.update()

    def game_over(self, win=False):
        """Ends the game."""

        if win:
            caption = self.leveldata.get('win_caption', 'You win! Your score: %s')
        else:
            caption = self.leveldata.get('death_caption',
                'GAME OVER, press Generate to replay or Load level settings to reload a level pack.\n'
                'Your score: %s')

        # Calculate the player's score based on the amount of levels completed,
        # adding the fuel remaining to it.
        self.score = self.current_level*100 + (self.fuel // 2)
        self.score = max(0, self.score)
        try:
            # Try to substitute the score into the caption, but fail silently if there
            # is no field for it.
            caption %= self.score
        except TypeError:
            pass

        self.ui.caption.setText(caption)
        self.is_game_over = True
        self.ui.fuel_remaining.update()

    def clear_settings(self):
        # Clear loaded level.
        self.leveldata = {}
        self.levels = []
        self.reset_state()

    def load_settings(self):
        """Loads maze generator settings from file."""

        filepicker = QFileDialog()
        filepicker.setWindowTitle('Load settings')
        # Only show .json files in the dialog
        filepicker.setDefaultSuffix('json')
        filepicker.setNameFilter("Maze Generator Config files (*.json)")

        # Set the default folder to presets/
        presets_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'presets')
        filepicker.setDirectory(presets_folder)

        filepicker.exec_()

        # Fetch the filename from the dialog.
        files = filepicker.selectedFiles()

        if not files:
            # The user hit cancel or failed to get a valid filename. Abort.
            return

        filename = files[0]

        # Reset the level count to 0 (first level).
        self.reset_state(level=0)

        try:
            with open(filename) as f:
                # Open the file and load as JSON.
                self.levels = json.load(f)
                debug_print('Loaded levels: %s' % self.levels)
                self.leveldata = self.levels[0]
        except:
            # Print the exact error to the console.
            traceback.print_exc()
            QMessageBox.critical(self.ui, "Error", "Failed to load given level.")
            return

        # Clear select_tile state to prevent conflicts.
        self.select_tile('clear')

        # Reset the fuel count to the one the level data defines.
        self.update_fuel(0, reset=True)

        # Draw the maze with the settings from the first level.
        self.make_maze()

    def fetch_level_data(self):
        """Generates level data using the current editor settings."""
        return [{'static_start': self.static_start,
        'static_finish': self.static_finish,
        'darkness': self.use_darkness,
        'fuel_packs': self.fuelpacks_count,
        'width': self.mazewidth,
        'height': self.mazeheight,
        'enemies': self.enemy_count,
        'use_fuel': self.use_fuel,
        'min_difficulty': self.min_difficulty,
        'gunshot_fuel': self.ui.gunshot_fuel_spinbox.value(),
        'enemy_move_delay': self.ui.move_delay_spinbox.value(),
        'fuel_pack_amount': self.ui.fuel_pack_amount_spinbox.value(),
        'starting_fuel': self.starting_fuel,
        'finish_bonus': self.ui.finish_bonus_spinbox.value(),
         # XXX perhaps make this configurable?
        'caption': '',
        'checkpoints': self.checkpoint_count}]

    def export_settings(self):
        """Exports the current maze generator settings to file."""
        self.make_maze(reset_state=True)

        filepicker = QFileDialog()
        filepicker.setWindowTitle('Export settings')

        # Only show .json files in the dialog
        filepicker.setDefaultSuffix('json')

        # Set this file picker to be a Save file dialog instead of an Open file dialog.
        filepicker.setAcceptMode(QFileDialog.AcceptSave)

        filepicker.setNameFilter("Maze Generator Config files (*.json)")
        presets_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'presets')
        filepicker.setDirectory(presets_folder)
        filepicker.exec_()

        # Fetch the filename from the dialog.
        files = filepicker.selectedFiles()

        if not files:
            # The user hit cancel or failed to get a valid filename. Abort.
            return

        filename = files[0]

        # Put all the level options as a dict, and export as JSON.
        leveldata = self.levels or self.fetch_level_data()

        try:
            with open(filename, 'w') as f:
                json.dump(leveldata, f, sort_keys=True)
        except OSError:
            traceback.print_exc()
            QMessageBox.critical(self.ui, "Error", "Failed to export given level.")
            return

    def load_savefile(self):
        """Loads a game progress save from file."""
        filepicker = QFileDialog()
        filepicker.setWindowTitle('Load save file')
        # Only show .tasave files in the dialog
        filepicker.setDefaultSuffix('tasave')
        filepicker.setNameFilter("TrulyAmazed save files (*.tasave)")
        saves_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'saves')
        filepicker.setDirectory(saves_folder)

        filepicker.exec_()

        # Fetch the filename from the dialog.
        files = filepicker.selectedFiles()

        if not files:
            # The user hit cancel or failed to get a valid filename. Abort.
            return

        # Clear select_tile state to prevent conflicts.
        self.select_tile('clear')

        filename = files[0]
        try:
            with open(filename) as f:
                # Open the file and load as JSON.
                savedata = json.load(f)
                debug_print('Loaded save data: %s' % savedata)

                # Populate the level data from the save file.
                self.levels = savedata['levels']
                try:
                    self.leveldata = self.levels[savedata['current_level']]
                except IndexError:  # We reached the last level, use that.
                    self.leveldata = self.levels[-1]

                # Reset the level count and the fuel.
                self.reset_state(savedata['current_level'])
                self.update_fuel(savedata['fuel'], reset=True)
                self.make_maze(reset_state=False)
        except:
            # Print the exact error to the console.
            traceback.print_exc()
            QMessageBox.critical(self.ui, "Error", "Failed to load save file.")
            return

    def export_savefile(self):
        """Saves the current game progress to file."""
        if self.is_game_over:
            QMessageBox.critical(self.ui, "Error", "Nothing to save if you're dead!")
            return

        filepicker = QFileDialog()
        filepicker.setWindowTitle('Export save file')

        # Only show .tasave files in the dialog
        filepicker.setDefaultSuffix('tasave')

        # Set this file picker to be a Save file dialog instead of an Open file dialog.
        filepicker.setAcceptMode(QFileDialog.AcceptSave)

        filepicker.setNameFilter("TrulyAmazed save files (*.tasave)")
        saves_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'saves')
        filepicker.setDirectory(saves_folder)
        filepicker.exec_()

        # Fetch the filename from the dialog.
        files = filepicker.selectedFiles()

        if not files:
            # The user hit cancel or failed to get a valid filename. Abort.
            return

        filename = files[0]

        # Put all the level options as a dict, and export as JSON.
        savedata = {'levels': self.levels or self.fetch_level_data(), 'current_level': self.current_level, 'fuel': self.fuel}

        try:
            with open(filename, 'w') as f:
                json.dump(savedata, f, sort_keys=True)
        except OSError:
            traceback.print_exc()
            QMessageBox.critical(self.ui, "Error", "Failed to export save file.")
            return

if __name__ == '__main__':
    # Start the application by initializing a QApplication instance.
    app = QApplication(sys.argv)

    # Initialize the GUI instance.
    gui = MazeGame(app, 'mazegame.ui')

    # Handle quits properly, exiting using the GUI app's exit code.
    sys.exit(app.exec_())
