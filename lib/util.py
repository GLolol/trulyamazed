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

"""Miscellaneous utilities for TrulyAmazed."""

# Quick and dirty sys.path hack to allow importing config.py
from sys import path
path.insert(0, '..')
from config import *

direction_opposites = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

def debug_print(*text):
    if verbose:
        print("DEBUG: ", end='')
        print(*text)

def opposite(direction):
    """Returns the opposite direction of the one given."""
    return direction_opposites[direction]

def round_down_to_even(num):
    """Rounds the given number down to the nearest even number."""
    return num // 2 * 2