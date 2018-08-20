#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Generates mazes using a depth-first search algorithm.
"""

from . import grid
from lib.util import *
import random

directions = ("north", "west", "south", "east")

class MazeGridPoint():
    """
    Class representing a single point of the maze.
    """

    def __init__(self, x, y, paths):
        # Determines which directions of the grid point should
        # NOT have walls blocking movement.
        self.paths = set(paths)

        self.x = x
        self.y = y

        self.is_finish = False
        self.is_start = False
        self.is_selected = False

    def __repr__(self):
        #return '%s' % ','.join(self.paths)
        return 'MazeGridPoint(%s, %s)' % (self.x, self.y)

    def __len__(self):
        return len(self.__repr__())

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def center(self, *args, **kwargs):
        return self.__repr__().center(*args, **kwargs)

class MazeGenerator():
    """Depth-first search maze generator."""

    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height

        # Keep track of which points are dead ends (end points).
        # This will help in randomly generating a finish later on.
        self.end_points = set()

    def _unvisited_directions_for(self, point):
        """
        Returns the directions of all unvisited maze points adjacent to the
        point given.
        """
        # Convert the list of directions into a set for error-free removal
        unvisited = set(directions)

        x, y = point
        #debug_print("Checking for unvisited directions for (%s, %s)" % (x, y))

        if x == 0:
            # If the x value is at the left-hand border of the grid,
            # going left will not be possible.
            unvisited.discard('west')

        elif x == self.grid.width-1:
            # Similarly, if the x value is at the right-hand border of the
            # grid, you won't be able to move right.
            unvisited.discard('east')

        if y == 0:
            # Y value is at the top of the grid, so disallow moving upwards any
            # further.
            unvisited.discard('north')

        elif y == self.grid.height-1:
            # Y value is at the bottom of the grid; disallow moving downwards.
            unvisited.discard('south')

        for direc in unvisited.copy():
            # After any border conditions are checked, we should eliminate all
            # directions where the point there has already been visited.
            neighbour_point = self._advance(point, direc)
            if self.grid.get(*neighbour_point):
                # Python note: using *listname as a function argument automatically expands
                # that list's contents and passes them to the function as arguments.
                # This is identical in this case to: self.grid.get(neighbour_point[0], neighbour_point[1])
                unvisited.remove(direc)

        # Finally, convert the directions set back into a list(), so
        # random.choice() can use it.
        return list(unvisited)

    def _advance(self, point, direction):
        """
        Returns the coordinate one away in the direction given, from the
        point given.
        """
        direction = direction.lower()
        x, y = point

        if direction == 'east':
            return (x+1, y)
        elif direction == 'west':
            return (x-1, y)
        elif direction == 'north':
            return (x, y-1)
        elif direction == 'south':
            return (x, y+1)
        else:
            raise ValueError("Unknown direction given.")

    def _generate(self, start_point=None):
        # Initialize an instance of the Grid class.
        self.grid = grid.Grid(self.width, self.height)

        # The first "current point" is the start point. This will change
        # as the generator moves from point to point.
        current_point = start_point
        x, y = current_point
        debug_print("current point is (%s, %s)" % (x, y))

        # Keep track of which points we've visited. When we reach a point
        # that no longer has any valid directions to go in, we return to
        # the point last visited before that.
        stack = [current_point]

        # Create the maze grid point instance for the starting point:
        # it will have no paths open by default, but more will be
        # added in the loop below.
        mazepoint = MazeGridPoint(x, y, [])
        self.grid.set(x, y, mazepoint)

        while stack:
            # While there are empty spaces beside a grid point, randomly
            # choose an unvisited adjacent grid point to advance to.
            try:
                valid_directions = self._unvisited_directions_for(current_point)
                direction = random.choice(valid_directions)
            except IndexError:
                # If there are no valid directions to go in (i.e. a dead end)
                # we should move back to the last point in the stack.
                self.end_points.add(new_mazepoint)

                new_point = stack.pop()
            else:
                # Before moving, make sure there is no wall between the current
                # point and the next point. In other words, add a path between
                # the last path and the current one.
                mazepoint = self.grid.get(x, y)
                mazepoint.paths.add(direction)

                # Get the new point by advancing 1 in the direction we chose.
                new_point = self._advance(current_point, direction)
                newx, newy = new_point

                # Add this new point to the stack: the list of points that we've
                # visited in the current path.
                stack.append(new_point)

                # Now, create a MazeGridPoint instance to represent the new point
                # we picked. The argument to MazeGridPoint() defines which sides
                # of the point should have a wall around it.

                # Make sure the direction we came to this point FROM is open.
                # This will be the opposite direction of the one we're advancing
                # in. For example, if we're moving upwards from point 1 to point 2,
                # the NORTH border of point 1 and the SOUTH border of point 2
                # should be open.
                new_mazepoint = MazeGridPoint(newx, newy, [opposite(direction)])
                self.grid.set(newx, newy, new_mazepoint)

            current_point = new_point
            x, y = current_point

    def generate(self, start_point=None, end_point=None):
        """
        Generates the maze, with optional fixed start and end points.
        """

        # Start point defaults to the top left of the maze.
        self.static_start = start_point  # Set static_start if exists
        start_point = start_point or (0, 0)

        if start_point[0] >= self.width or start_point[1] >= self.height:
            # Start point coordinates are outside our boundaries (likely
            # due to setting a static point and then making the maze
            # smaller. If this happens, just ignore that setting.
            # TODO: make this more intelligent.
            self.static_start = start_point = (0, 0)

        self._generate(start_point)

        self.static_finish = end_point  # Set static_finish if exists

        # Randomly choose two dead ends from the maze, unless a static start
        # or finish is being used.
        while True:
            try:
                self.start, self.finish = random.sample(self.end_points, 2)
                if self.start == self.finish:
                    raise ValueError("Start and finish at the same point")
            except (IndexError, ValueError):
                debug_print("Maze was not random enough, regenerating!")
                self._generate(start_point)
            else:
                break

        debug_print("List of end points: %s" % self.end_points)
        debug_print("Choosing %s and %s as our start and finish points" % (self.start, self.finish))

        # Static start or finish points will override the random picking.
        try:
            if self.static_start:
                self.start = self.grid.get(*self.static_start)
                debug_print("Setting start point to (%s, %s) via static start" % (self.static_start[0], self.static_start[1]))
        except IndexError:
            # Unless they're outside the boundaries of the maze... For now, it'll just
            # ignore the mismatched setting. TODO: make this more intelligent
            pass

        try:
            if self.static_finish:
                self.finish = self.grid.get(*self.static_finish)
                debug_print("Setting finish point to (%s, %s) via static finish" % (self.static_finish[0], self.static_finish[1]))
        except IndexError:
            pass

        # Set the is_finish or is_start values of the point to True. That's it!
        self.finish.is_finish = True
        self.start.is_start = True

        return self.grid

    def distance(self, point1, point2):
        """
        Returns the sum of the vertical and horizontal distances between the
        two points given.
        """
        x_distance = abs(point1.x - point2.x)
        y_distance = abs(point1.y - point2.y)
        return x_distance + y_distance

if __name__ == '__main__':
    print("This module provides no command line functions.")
