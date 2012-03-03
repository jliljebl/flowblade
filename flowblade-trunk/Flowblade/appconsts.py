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

# Autosave options
AUTO_SAVE_OPTS = ((-1, "No Autosave"),(2, "2 min"),(5, "5 min"),(10, "10 min"),(20,"20 min"))

# Number of tracks in new project
VTRACK_OPTS = ((3, "3"),(4, "4"),(5, "5"))
ATRACK_OPTS = ((2, "2"),(3, "3"),(4, "4"))

# Display heights for tracks.
TRACK_HEIGHT_NORMAL = 50 # track height in canvas and column
TRACK_HEIGHT_SMALL = 25 # track height in canvas and column

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
