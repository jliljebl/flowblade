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

AVAILABLE_PANEL_POSITIONS_OPTIONS = { \
    appconsts.PANEL_MEDIA: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN],
    appconsts.PANEL_FILTERS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_COMPOSITORS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_RANGE_LOG: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_RENDERING: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_JOBS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_PROJECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_PROJECT_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_FILTER_SELECT: [appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT]
}


# Saved data struct holding panel positions information.
_panel_positions = None

# Dict for translations
_positions_names = {}

# ----------------------------------------------------------- INIT
def init_layout_data():
    global _panel_positions, _positions_names
    _panel_positions = editorpersistance.prefs.panel_positions
    
    if _panel_positions == None:
        _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
        editorpersistance.prefs.panel_positions = _panel_positions
        editorpersistance.save()

    _positions_names = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: _("Top Row Notebook"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: _("Top Row Right Notebook"),
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: _("Left Column"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT:  _("Bottom Row Left"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT:_("Bottom Row Right"),
    }

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
    
    media_panel_menu = _get_position_selection_menu(appconsts.PANEL_MEDIA)
    media_panel_menu_item.set_submenu(media_panel_menu)
    
    # Panel positions - Filter Panel
    filter_panel_menu_item = Gtk.MenuItem(_("Filter Panel"))
    panel_positions_menu.append(filter_panel_menu_item)

    filter_panel_menu =  _get_position_selection_menu(appconsts.PANEL_FILTERS)
    filter_panel_menu_item.set_submenu(filter_panel_menu)
    
    return panel_positions_menu_item

def _get_position_selection_menu(panel):
    current_position = _get_panel_position(panel)
    available_positions = AVAILABLE_PANEL_POSITIONS_OPTIONS[panel]
    
    positions_menu  = Gtk.Menu()
    
    first_item = None
    menu_items = []
    for pos_option in available_positions:
        if first_item == None:
            menu_item = Gtk.RadioMenuItem()
            menu_item.set_label(_positions_names[pos_option])
            positions_menu.append(menu_item)
            first_item = menu_item
            menu_items.append(menu_item)
        else:
            menu_item = Gtk.RadioMenuItem.new_with_label([first_item], _positions_names[pos_option])
            positions_menu.append(menu_item)
            menu_items.append(menu_item)
                
    selected_index = available_positions.index(current_position)
    menu_items[selected_index].set_active(True)
    
    for menu_item in menu_items:
        pass
        #menu_item.connect("activate", lambda w: self._show_media_panel_top_row_notebook(w))
    
    return positions_menu
    
    