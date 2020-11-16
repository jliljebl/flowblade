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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This modules handles displaying and moving panels into different positions 
in application window.
"""
import appconsts

"""
# Panel placement options
appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT
appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT
appconsts.PANEL_PLACEMENT_LEFT_COLUMN
appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT
appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT

# Panels
appconsts.PANEL_MEDIA
appconsts.PANEL_FILTERS
appconsts.PANEL_COMPOSITORS
appconsts.PANEL_RANGE_LOG
appconsts.PANEL_RENDERING
appconsts.PANEL_JOBS
appconsts.PANEL_PROJECT
appconsts.PANEL_PROJECT_SMALL_SCREEN
appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN
appconsts.PANEL_FILTER_SELECT
"""

DEFAULT_PANEL_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTERS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_COMPOSITORS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, # This is the only different default position.
}


_panel_positions = None

def init_layout_data():
    global _panel_positions
    _panel_positions = editorpersistance.prefs.panel_positions
    