###
# Copyright (c) 2015-2016 James Lu <glolol@overdrivenetworks.com>

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

"""Grid system using nested lists (version 2)."""

from __future__ import print_function
import itertools
import sys

if sys.version_info[0] >= 3:
    raw_input = input
    xrange = range

class GridItemFilledError(ValueError):
    # Raised when a grid point we requested is already filled.
    pass

class Grid():
    """Grid system using nested lists."""
    def __init__(self, width=3, height=3):
        """
        Initialize the grid: a list of lists. The first (big) list is equal
        to the amount of columns in the game. It includes a series of
        sublists, each representing a row in the grid. Each item in the
        sublist represents a space on the grid.

        A 3 by 3 grid would look like, internally:
           [['', '', ''], ['', '', ''], ['', '', '']]
        In this implementation, the origin point (0, 0) is the top left. The
        coordinates for a 3 by 3 grid would thus be the following.
           [[(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)],
            [(0, 2), (1, 2), (2, 2)]]

        We need to use list comprehensions instead of simply multiplying a list by
        the width/height, so that each grid point has a distinct reference.
        Otherwise, setting one point in the grid will cause other ones to be
        changed too.
        """
        self.grid = [['' for _ in xrange(width)] for _ in xrange(height)]
        self.width = width
        self.height = height

        # Store the length of the largest item that's ever been added to the
        # grid, so that grid cells are formatted with the right widths.
        # 3 is a good default since it gives the grid ample space to start,
        # but it will grow if bigger strings are stored.
        self.largestlength = 20

    def _get_coordinate(self, x, y):
        """
        Fetches coordinate using Cartesian grid system.
        """
        return self.grid[y][x]

    def get(self, x, y, allowOverflow=False):
        """Returns the contents of the grid item at (x, y)."""
        if (not allowOverflow) and (x < 0 or y < 0):
            raise IndexError("Grid coordinate is negative.")
        return self._get_coordinate(x, y)

    def _set_coordinate(self, x, y, obj):
        """
        Sets a coordinate value using Cartesian grid system.
        """
        self.grid[y][x] = obj

    def set(self, x, y, obj, allowOverflow=False, allowOverwrite=False):
        """Sets the contents of the grid item at (x, y)."""
        if (not allowOverflow) and (x < 0 or y < 0):
            raise IndexError("Grid coordinate is negative.")
        if (not allowOverwrite) and self._get_coordinate(x, y):
            raise GridItemFilledError("Coordinates requested have already been filled.")

        objectlength = len(obj)
        # If the length of the object is greater than the largest length we've
        # seen so far, update the length. This is used for grid formatting
        # purposes, so that each cell has the right width.
        if objectlength > self.largestlength:
            self.largestlength = objectlength

        self._set_coordinate(x, y, obj)

    def show(self):
        """
        Prints the current grid to screen.

        For unused squares, show the number of the coordinate instead.
        This way, a blank 3 by 3 grid gets shown as:
        |---|---|---|
        | 1 | 2 | 3 |
        |---|---|---|
        | 4 | 5 | 6 |
        |---|---|---|
        | 7 | 8 | 9 |
        |---|---|---|, instead of each item being empty.
        """
        # Print the top bar with the right cell width:
        #    |---|---|---|
        print('|%s' % ('-' * self.largestlength) * self.width + '|')
        # To get the numbers of each grid point, first enumerate every rows'
        # data with their position in the grid:
        #    [(0, <contents of row 1>), (1, <contents of row 2>), (2, <contents of row 3), ...]
        for rowpos, row in enumerate(self.grid, 0):
            # In the same way, enumerate the column index and the data of each
            # grid point in the row:
            #    [(0, <contents of point (0, 0)>),
            #     (1, <contents of point (1, 0)>),
            #     (2, <contents of point (2, 0)>), ...]
            for colpos, char in enumerate(row, 1):
                print('|', end='')
                place = str(rowpos * self.width + colpos)

                # Note:
                # This can be uncommented so that the grid defaults to showing
                # the internal grid position, instead of the numeric position.
                #place = "(%s, %s)" % (colpos-1, rowpos)

                # Make each grid item N characters long, centring it and padding it with spaces.
                # N is always the LARGEST object length we've seen so far, so that the cell
                # has the right width.
                output = char or place
                output = output.center(self.largestlength, ' ')

                print(output, end='')
            print('|')
            print('|%s' % ('-' * self.largestlength) * self.width + '|')
            # Print the dividing bar with the right cell width between every row:
            #    |---|---|---|

    def __iter__(self):
        # This overrides list(Grid()), so that it returns meaningful results instead of an error.
        for item in self.grid:
            yield item

    def __repr__(self):
        # This overrides str(Grid()), so that it gives meaningful results instead of something like <Grid instance at 0x12345678>
        return repr(self.grid)

    def all_items(self):
        """Returns all the items in the grid, reduced into one list."""
        return list(itertools.chain.from_iterable(self.grid))

if __name__ == '__main__':
    print("This module provides no command line functions.")
