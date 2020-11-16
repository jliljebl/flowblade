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
from gi.repository import Gtk

import copy

import appconsts
import editorpersistance

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

# Saved data struct holding panel positions information.
_panel_positions = None


# ----------------------------------------------------------- INIT
def init_layout_data():
    global _panel_positions
    _panel_positions = editorpersistance.prefs.panel_positions
    
    if _panel_positions == None:
        _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
        editorpersistance.prefs.panel_positions = _panel_positions
        editorpersistance.save()

# ---------------------------------------------------------- DATA METHODS
def _get_panel_position(panel):
    return _panel_positions[panel]


# ---------------------------------------------------------- APP MENU
def get_panel_positions_menu_item():
    panel_positions_menu_item = Gtk.MenuItem(_("Panel Placement"))
    panel_positions_menu = Gtk.Menu()
    panel_positions_menu_item.set_submenu(panel_positions_menu)
    
    # Panel positions - Media Panel
    media_panel_menu_item = Gtk.MenuItem(_("Media Panel"))
    panel_positions_menu.append(media_panel_menu_item)
    
    media_panel_menu = Gtk.Menu()
    media_panel_menu_item.set_submenu(media_panel_menu)
    
    media_panel_top = Gtk.RadioMenuItem()
    media_panel_top.set_label( _("Top Row Notebook"))
    media_panel_menu.append(media_panel_top)

    media_panel_left_column = Gtk.RadioMenuItem.new_with_label([media_panel_top], _("Left Column"))

    if _get_panel_position(appconsts.PANEL_MEDIA) == appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT:
        media_panel_top.set_active(True)
    else:
        media_panel_left_column.set_active(True)

    media_panel_top.set_active(True)
    media_panel_top.connect("activate", lambda w: self._show_media_panel_top_row_notebook(w))
    media_panel_left_column.connect("activate", lambda w: self._show_media_panel_left_column(w))
    media_panel_menu.append(media_panel_left_column)

    # Panel positions - Filter Panel
    filter_panel_menu_item = Gtk.MenuItem(_("Filter Panel"))
    panel_positions_menu.append(filter_panel_menu_item)

    filter_panel_menu = Gtk.Menu()
    filter_panel_menu_item.set_submenu(filter_panel_menu)
    
    filter_panel_top = Gtk.RadioMenuItem()
    filter_panel_top.set_label( _("Top Row Notebook"))
    filter_panel_menu.append(filter_panel_top)

    filter_panel_bottom_right = Gtk.RadioMenuItem.new_with_label([filter_panel_top], _("Bottom Row Right"))

    if _get_panel_position(appconsts.PANEL_FILTERS) == appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT:
        filter_panel_top.set_active(True)
    else:
        filter_panel_bottom_right.set_active(True)

    filter_panel_top.set_active(True)
    #media_panel_top.connect("activate", lambda w: self._show_tabs_up(w))
    #tabs_down.connect("activate", lambda w: self._show_tabs_down(w))
    filter_panel_menu.append(filter_panel_bottom_right)

    return panel_positions_menu_item