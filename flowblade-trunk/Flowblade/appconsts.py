"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module contains constant values that are used by multiple modules in the application. 
"""

# Media types for tracks or clips
UNKNOWN = 0
VIDEO = 1
AUDIO = 2
IMAGE = 3
RENDERED_VIDEO = 4 # not implemented
PATTERN_PRODUCER = 5
SYNC_AUDIO = 6
FILE_DOES_NOT_EXIST = 7

# Sync states of sync child clips
SYNC_CORRECT = 0
SYNC_OFF = 1
SYNC_PARENT_GONE = 2

# Allowed editing operations on a track
FREE = 0        # All edits allowed
SYNC_LOCKED = 1 # No insert, splice out or one roll trim.
                # Allowed edits do not change positions of later clips 
LOCKED = 2      # No edits allowed

# Property types of mlt filters and mlt transitions in filters.xml
# and compositors.xml
PROP_INT = 0
PROP_FLOAT = 1
PROP_EXPRESSION = 2

# Pattern producer types. Currently only 1 available.
COLOR_CLIP = 1

# Display heights for tracks.
TRACK_HEIGHT_NORMAL = 50 # track height in canvas and column
TRACK_HEIGHT_SMALL = 25 # track height in canvas and column
TRACK_HEIGHT_SMALLEST = 20 # track height in canvas and column

# Property editing gui consts
PROPERTY_ROW_HEIGHT = 22
PROPERTY_NAME_WIDTH = 90

# Clip mute options
MUTE_NOTHING = 0
MUTE_AUDIO = 1
MUTE_VIDEO = 2
MUTE_ALL = 3

# Track mute options
TRACK_MUTE_NOTHING = 0
TRACK_MUTE_VIDEO = 1
TRACK_MUTE_AUDIO = 2
TRACK_MUTE_ALL = 3

# XML Attribute and element names
NAME = "name"
ARGS = "args"
PROPERTY = "property"
MLT_SERVICE = "mlt_service"
EXTRA_EDITOR = "extraeditor"

# Available tracks configurations for flowblade
TRACK_CONFIGURATIONS = [(5,4),(4,3),(3,2),(2,1),(8,1),(1,8)]
