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
import editorstate

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
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTERS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_COMPOSITORS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: None, # default values are for large screen single window layout, these are modified on startup if needed.
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None, # default values are for large screen single window layout, these are modified on startup if needed.
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, # This is the only different default position.
}

AVAILABLE_PANEL_POSITIONS_OPTIONS = { \
    appconsts.PANEL_MEDIA: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN],
    appconsts.PANEL_FILTERS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_COMPOSITORS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_RANGE_LOG: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_RENDERING: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_JOBS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_PROJECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_PROJECT_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_FILTER_SELECT: [appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT]
}


# Saved data struct holding panel positions information.
_panel_positions = None

# Index of noteboo
#_panel_notebook_indexes = {}

# Dicts for translations.
_positions_names = {}
_panels_names = {}


def top_level_project_panel():
    if editorpersistance.prefs.top_row_layout == appconsts.ALWAYS_TWO_PANELS:
        return False
    if editorpersistance.prefs.top_level_project_panel == True and editorstate.SCREEN_WIDTH > 1440 and editorstate.SCREEN_HEIGHT > 898:
        return True

    return False
    
# ----------------------------------------------------------- INIT
def init_layout_data():
    global _panel_positions, _positions_names, _panels_names
    _panel_positions = editorpersistance.prefs.panel_positions

    _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
    editorpersistance.prefs.panel_positions = _panel_positions
    editorpersistance.save()
        
    if _panel_positions == None:
        _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
        editorpersistance.prefs.panel_positions = _panel_positions
        editorpersistance.save()

    # Translations need to be inited after all modules havfe been loaded
    _positions_names = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: _("Top Row Notebook"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: _("Top Row Right Notebook"),
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: _("Left Column"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT:  _("Bottom Row Left"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT:_("Bottom Row Right"),
    }
    
    _panels_names = { \
        appconsts.PANEL_MEDIA: _("Media"),
        appconsts.PANEL_FILTERS: _("Filters"),
        appconsts.PANEL_COMPOSITORS: _("Compositors"),
        appconsts.PANEL_RANGE_LOG: _("Range Log"),
        appconsts.PANEL_RENDERING: _("Render"),
        appconsts.PANEL_JOBS: _("Jobs"),
        appconsts.PANEL_PROJECT: _("Project"),
        appconsts.PANEL_PROJECT_SMALL_SCREEN: "tba",
        appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: "tba",
        appconsts.PANEL_FILTER_SELECT: _("Filter Select")
    }

# ---------------------------------------------------------- DATA METHODS
def _get_panel_position(panel):
    return _panel_positions[panel]

def _get_position_panels(position):
    panels = []
    for panel, panel_position in _panel_positions.items():
        if position == panel_position:
            panels.append(panel)

    return panels

def _get_panels_widgets_dict(editor_window):
    _panels_widgets = { \
        appconsts.PANEL_MEDIA: editor_window.mm_paned,
        appconsts.PANEL_FILTERS: editor_window.effects_panel,
        appconsts.PANEL_COMPOSITORS: editor_window.compositors_panel,
        appconsts.PANEL_RANGE_LOG: editor_window.media_log_panel,
        appconsts.PANEL_RENDERING: editor_window.render_panel,
        appconsts.PANEL_JOBS: editor_window.jobs_pane,
        appconsts.PANEL_PROJECT: editor_window.top_project_panel,
        appconsts.PANEL_FILTER_SELECT: editor_window.effect_select_panel
    }
    # appconsts.PANEL_PROJECT_SMALL_SCREEN, appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN
    # not available currently

    return _panels_widgets
        
# ----------------------------------------------------------- PANELS PLACEMENT
def create_position_container(editor_window, position):
    panels = _get_position_panels(position)
    panel_widgets = _get_panels_widgets_dict(editor_window)
    if len(panels) == 0:
        return None 
    elif len(panels) == 1:
        print("returning panel it self")
        return panel_widgets[panels[0]] # Just oanel, no notebook, we have only one panel in this position
    else:
        notebook = Gtk.Notebook()

        for panel in panels:
            widget = panel_widgets[panel]
            label = Gtk.Label(label=_panels_names[panel])
            print(_panels_names[panel])
            notebook.append_page(widget, label)
        print("returning notebook")
        return notebook
            
        """
        # For multiple panels we are making notebook
 = Gtk.Notebook()
self.notebook.set_size_request(appconsts.NOTEBOOK_WIDTH, appconsts.TOP_ROW_HEIGHT)
media_label = Gtk.Label(label=_("Media"))

# Here we put media panel in notebook if that is the current user pref.
if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
    self.notebook.append_page(self.mm_paned, media_label)
#    if editorpersistance.prefs.placement_media_panel == appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT:
#        self.notebook.append_page(self.mm_paned, media_label)
self.notebook.append_page(self.media_log_panel, Gtk.Label(label=_("Range Log")))
self.notebook.append_page(self.effects_panel, Gtk.Label(label=_("Filters")))
self.notebook.append_page(self.compositors_panel, Gtk.Label(label=_("Compositors")))
if top_level_project_panel() == False:
    self.notebook.append_page(self.project_panel, Gtk.Label(label=_("Project")))

self.notebook.append_page(self.jobs_pane, Gtk.Label(label=_("Jobs")))
self.notebook.append_page(self.render_panel, Gtk.Label(label=_("Render")))
    """
    
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
    
    