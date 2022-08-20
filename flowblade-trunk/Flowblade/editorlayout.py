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
from gi.repository import Gtk, GObject

import copy
import pickle

import appconsts
import atomicfile
import editorpersistance
import editorstate
import dialogs
import dialogutils
import gui
import guiutils
import utils

# Transforms when adding panels.
# 0 -> 1    The pre-created Gtk.Frame is filled with added panel.
# 1 -> 2    The pre-created Gtk.Frame is removed from layout box and panel is removed from it
#           New notebook is created and both panels are added into it.
# 2 -> N    Panel is added into existing notebook.

# Transforms when removing panels.
# N -> 2    Panel is removed from notebook.
# 2 -> 1    Notebook is removed from pre-created Gtk.Frame, panel is removed from notebook
#           and added to pre-created Gtk.Frame.
# 1 -> 0    Panel is removed from the pre-created Gtk.Frame.

# Pre-created Gtk.Frames exist all through app life-cycle, notebooks are dynamically created
# as needed.

# The exception for these transforms here is the top row default notebook 
# that is forced to always exits with at least two panels displayed.
# This makes easier to add and remove top row panels.

 # This is no longer default. Available as layout option 'Monitor Left'
DEFAULT_PANEL_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT,
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MULTI_EDIT: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None
}

MONITOR_CENTER_PANEL_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT,
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MULTI_EDIT: appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None
}

TOP_ROW_FOUR_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT,
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MULTI_EDIT: appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None
}

MEDIA_PANEL_LEFT_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_LEFT_COLUMN,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_NOT_VISIBLE,
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MULTI_EDIT: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None
}

AVAILABLE_PANEL_POSITIONS_OPTIONS = { \
    appconsts.PANEL_MEDIA: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_MULTI_EDIT: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,  appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_RANGE_LOG: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_RENDERING: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_JOBS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_PROJECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_PROJECT_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_FILTER_SELECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, appconsts.PANEL_PLACEMENT_NOT_VISIBLE]
}

PANEL_ORDER_IN_NOTEBOOKS = [appconsts.PANEL_MEDIA, appconsts.PANEL_FILTER_SELECT, appconsts.PANEL_RANGE_LOG, 
                            appconsts.PANEL_MULTI_EDIT, appconsts.PANEL_JOBS, appconsts.PANEL_PROJECT_SMALL_SCREEN, 
                            appconsts.PANEL_PROJECT, appconsts.PANEL_RENDERING,
                            appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN]

PANEL_MINIMUM_SIZES = { \
    appconsts.PANEL_MEDIA: (appconsts.PANEL_MEDIA_MINIMUM_SIZE, appconsts.TOP_ROW_HEIGHT), 
    appconsts.PANEL_FILTER_SELECT: None,
    appconsts.PANEL_RANGE_LOG: None,
    appconsts.PANEL_MULTI_EDIT: (appconsts.PANEL_MULTI_EDIT_MINIMUM_SIZE, appconsts.TOP_ROW_HEIGHT),
    appconsts.PANEL_JOBS: None,
    appconsts.PANEL_RENDERING: None,
    appconsts.PANEL_PROJECT: None,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: None,
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None
}

UP  = 0
DOWN = 1
DEFAULT_TABS_POSITIONS = { \
    appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: DOWN,
    appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: DOWN,
    appconsts.PANEL_PLACEMENT_LEFT_COLUMN: DOWN,
    appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT: UP,
    appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT: UP,
    appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT: DOWN
}

# Saved data struct holding panel positions information.
_panel_positions = None

# Gtk.Notebooks that may or may not exist to contain 2-N panel is layout position
_position_notebooks = {}

# Dicts for translations.
_positions_names = {}
_panels_names = {}

# Pop-up menu from top bar button.
_top_bar_button_menu = Gtk.Menu()

def top_level_project_panel():
    if editorpersistance.prefs.top_level_project_panel == True and editorstate.SCREEN_WIDTH > 1440 and editorstate.SCREEN_HEIGHT > 898:
        return True

    return False
    
# ----------------------------------------------------------- INIT
def init_layout_data():
    global _panel_positions, _positions_names, _panels_names, _position_notebooks
    _panel_positions = editorpersistance.prefs.panel_positions

    # Use default panels positions if nothing available yet or too small screen
    if panel_positioning_available() == False or _panel_positions == None:
        _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
        editorpersistance.prefs.panel_positions = _panel_positions
        editorpersistance.save()

    if editorpersistance.prefs.positions_tabs == None:
        editorpersistance.prefs.positions_tabs = DEFAULT_TABS_POSITIONS
        editorpersistance.save()

    # PANEL_COMPOSITORS was deprecated whenmoving to use multi edit panel.
    if appconsts.PANEL_COMPOSITORS in _panel_positions:
        _panel_positions.pop(appconsts.PANEL_COMPOSITORS)

    # Force media panel positioning to work with both one and two window modes 
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
        # When two windows -> single window put media panel in dewfault pos
        if _panel_positions[appconsts.PANEL_MEDIA] == appconsts.PANEL_PLACEMENT_TWO_WINDOWS_MEDIA_PANEL_POS:
            _panel_positions[appconsts.PANEL_MEDIA] = appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT
    else:
        # When two windows always force pos  PANEL_PLACEMENT_TWO_WINDOWS_MEDIA_PANEL_POS for media.
        _panel_positions[appconsts.PANEL_MEDIA] = appconsts.PANEL_PLACEMENT_TWO_WINDOWS_MEDIA_PANEL_POS

    # We are using different media panels for different screen sizes,
    # make sure that are using and displaying the right one here even screen size has changed.
    if top_level_project_panel() == True:
        if appconsts.PANEL_PROJECT_SMALL_SCREEN in _panel_positions:
            _panel_positions[appconsts.PANEL_PROJECT] = appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT
            del(_panel_positions[appconsts.PANEL_PROJECT_SMALL_SCREEN])
    else:
        if appconsts.PANEL_PROJECT in _panel_positions:
            _panel_positions[appconsts.PANEL_PROJECT_SMALL_SCREEN] = appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT
            del(_panel_positions[appconsts.PANEL_PROJECT])
            
    # Translations need to be initialized after modules have been loaded.
    _positions_names = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: _("Top Row Default Notebook"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: _("Top Row Right"),
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: _("Left Column"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT: _("Bottom Row Left"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT: _("Bottom Row Right"),
        appconsts.PANEL_PLACEMENT_NOT_VISIBLE: _("Not Visible"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT: _("Top Row Project Panel Default"),
    }
    
    _panels_names = { \
        appconsts.PANEL_MEDIA: _("Media"),
        appconsts.PANEL_MULTI_EDIT: _("Edit"),
        appconsts.PANEL_RANGE_LOG: _("Range Log"),
        appconsts.PANEL_RENDERING: _("Render"),
        appconsts.PANEL_JOBS: _("Jobs"),
        appconsts.PANEL_PROJECT: _("Project"),
        appconsts.PANEL_PROJECT_SMALL_SCREEN: _("Project"),
        appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: "tba",
        appconsts.PANEL_FILTER_SELECT: _("Filter Select")
    }
    
     # Values are possibly set to other then None as layout is being build
    _position_notebooks = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: None,
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: None,
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: None,
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT: None,
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT: None,
        appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT: None
    }

def show_panel(panel_id):
    # Iterate positions to find where panel is and bring it to front.
    for position in _positions_names:
        pos_panel_ids = _get_position_panels(position)
        if len(pos_panel_ids) == 0:
            continue
        if len(pos_panel_ids) == 1:
            continue
        
        panel_widget = _get_panels_widgets_dict(gui.editor_window)[panel_id]
        notebook = _position_notebooks[position]
        for i in range(0, notebook.get_n_pages()):
            notebook_page = notebook.get_nth_page(i)
            if notebook_page == panel_widget:
                notebook.set_current_page(i)
            
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
        appconsts.PANEL_MULTI_EDIT: editor_window.edit_multi.widget,
        appconsts.PANEL_RANGE_LOG: editor_window.media_log_panel,
        appconsts.PANEL_RENDERING: editor_window.render_panel,
        appconsts.PANEL_JOBS: editor_window.jobs_pane,
        appconsts.PANEL_PROJECT: editor_window.top_project_panel,
        appconsts.PANEL_FILTER_SELECT: editor_window.effect_select_panel,
        appconsts.PANEL_PROJECT_SMALL_SCREEN: editor_window.project_panel
    }
    # appconsts.PANEL_PROJECT_SMALL_SCREEN, appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN
    # not available currently

    return _panels_widgets

def _get_position_frames_dict():
    editor_window = gui.editor_window # This is always available at calltime.
    position_frames = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: editor_window.notebook_frame,
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: editor_window.top_right_frame,
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT: editor_window.bottom_left_frame,
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT: editor_window.bottom_right_frame,
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: editor_window.left_column_frame,
        appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT: editor_window.top_project_panel_frame
    }

    return position_frames

def _get_ordered_widgets_list():
    ordered_list = []
    panel_widgets = _get_panels_widgets_dict(gui.editor_window)
    for panel_id in PANEL_ORDER_IN_NOTEBOOKS:
        try:
            ordered_list.append(panel_widgets[panel_id])
        except:
            pass
    
    return ordered_list

def _get_insert_index(insert_widget, notebook):
    panels_list = _get_ordered_widgets_list()
    for i in range(0, notebook.get_n_pages()):
        page_widget = notebook.get_nth_page(i)
        page_ordinal = panels_list.index(page_widget)
        insert_widget_ordinal = panels_list.index(insert_widget)
        # These are never equal because of the way we handle radiomenuitem events.
        if insert_widget_ordinal < page_ordinal:
            return i

    return notebook.get_n_pages()

def _set_min_size(panel_id, widget):
    min_size = PANEL_MINIMUM_SIZES[panel_id]
    if min_size != None:
        widget.set_size_request(*min_size)

def panel_positioning_available():
    # This feature now available only for 1680x1050 and larger screens.
    # Maybe some reduced version later for smaller screens.
    if editorstate.SCREEN_WIDTH > 1678 and  editorstate.SCREEN_HEIGHT > 1048:
        return True
    
    return False

def set_positions_frames_visibility():
    # if frame has 0 panels in it, hide
    for position in _positions_names:
        if position == appconsts.PANEL_PLACEMENT_NOT_VISIBLE:
            continue # this not applicable here
        frame = _get_position_frames_dict()[position]
        panels = _get_position_panels(position)
        if len(panels) > 0:
            frame.show()
        else:
            frame.hide()
        
# ----------------------------------------------------------- PANELS PLACEMENT
def create_position_widget(editor_window, position):
    # This method creates and returns the widget that is put into the frame 
    # holding panel/s in given position.
    # If no panels go into position, None is returned.
    # If 1 panel in position, then that panel itself is the widget.
    # If 2-N panels in position, then a notebook containing panels in position is the widget.
    # We also return flag telling whether the returned widget is notebook.
    panels = _get_position_panels(position)
    panel_widgets = _get_panels_widgets_dict(editor_window)
    
    global _position_notebooks
    if len(panels) == 0:
        return (None, False) 
    elif len(panels) == 1:
        _position_notebooks[position] = None
        _set_min_size(panels[0], panel_widgets[panels[0]])
        return (panel_widgets[panels[0]], False)
    else:
        notebook = _create_notebook(position, editor_window)
        _position_notebooks[position] = notebook
        return (notebook, True)

def _create_notebook(position, editor_window):
    notebook = Gtk.Notebook()
    panels = _get_position_panels(position)
    panel_widgets = _get_panels_widgets_dict(editor_window)
    for panel_id in panels:
        widget = panel_widgets[panel_id]
        _set_min_size(panel_id, widget)
        label = Gtk.Label(label=_panels_names[panel_id])
        notebook.append_page(widget, label)
    
    try:
        tabs_positions = editorpersistance.prefs.positions_tabs
        tabs_pos = tabs_positions[position]
    except:
        editorpersistance.prefs.positions_tabs = DEFAULT_TABS_POSITIONS
        editorpersistance.save()
        tabs_positions = editorpersistance.prefs.positions_tabs
        tabs_pos = tabs_positions[position]
        
    if tabs_pos == UP:
        notebook.set_tab_pos(Gtk.PositionType.TOP)
    else:
        notebook.set_tab_pos(Gtk.PositionType.BOTTOM)
        
    return notebook
    
# ---------------------------------------------------------- APP MENU, TOP BAR BUTTON MENU
def get_panel_positions_menu_item():
    panel_positions_menu_item = Gtk.MenuItem(_("Panel Placement"))
    panel_positions_menu = Gtk.Menu()
    panel_positions_menu_item.set_submenu(panel_positions_menu)

    # Presets
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
        presets_menu_item = Gtk.MenuItem(_("Preset Layouts"))
        presets_menu = Gtk.Menu()
        presets_menu_item.set_submenu(presets_menu)
        _create_layout_presets_menu(presets_menu)
        panel_positions_menu.append(presets_menu_item)
        sep = Gtk.SeparatorMenuItem()
        panel_positions_menu.append(sep)
    
    # Project Panel
    project_panel_menu_item = Gtk.MenuItem(_("Project Panel"))
    panel_positions_menu.append(project_panel_menu_item)

    project_panel_menu = _get_position_selection_menu(appconsts.PANEL_PROJECT)
    project_panel_menu_item.set_submenu(project_panel_menu)
    
    # Media Panel - we're forcing a position for this on two window mode for the time being.
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
        media_panel_menu_item = Gtk.MenuItem(_("Media Panel"))
        panel_positions_menu.append(media_panel_menu_item)
        
        media_panel_menu = _get_position_selection_menu(appconsts.PANEL_MEDIA)
        media_panel_menu_item.set_submenu(media_panel_menu)

    # Range Log Panel
    range_log_panel_menu_item = Gtk.MenuItem(_("Range Log Panel"))
    panel_positions_menu.append(range_log_panel_menu_item)
    
    range_log_panel_menu = _get_position_selection_menu(appconsts.PANEL_RANGE_LOG)
    range_log_panel_menu_item.set_submenu(range_log_panel_menu)
    
    # Filter Panel
    filter_panel_menu_item = Gtk.MenuItem(_("Edit Panel"))
    panel_positions_menu.append(filter_panel_menu_item)

    filter_panel_menu =  _get_position_selection_menu(appconsts.PANEL_MULTI_EDIT)
    filter_panel_menu_item.set_submenu(filter_panel_menu)

    # Jobs
    jobs_panel_menu_item = Gtk.MenuItem(_("Jobs Panel"))
    panel_positions_menu.append(jobs_panel_menu_item)

    jobs_panel_menu =  _get_position_selection_menu(appconsts.PANEL_JOBS)
    jobs_panel_menu_item.set_submenu(jobs_panel_menu)

    # Render
    render_panel_menu_item = Gtk.MenuItem(_("Render Panel"))
    panel_positions_menu.append(render_panel_menu_item)

    render_panel_menu =  _get_position_selection_menu(appconsts.PANEL_RENDERING)
    render_panel_menu_item.set_submenu(render_panel_menu)
    
    # Filter Select Panel
    filter_select_panel_menu_item = Gtk.MenuItem(_("Filter Select Panel"))
    panel_positions_menu.append(filter_select_panel_menu_item)

    filter_select_panel_menu =  _get_position_selection_menu(appconsts.PANEL_FILTER_SELECT)
    filter_select_panel_menu_item.set_submenu(filter_select_panel_menu)
    
    return panel_positions_menu_item

def _get_position_selection_menu(panel_id):
    current_position = _get_panel_position(panel_id)
    available_positions = AVAILABLE_PANEL_POSITIONS_OPTIONS[panel_id]
    
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
    
    for i in range(0, len(available_positions)):
        menu_item = menu_items[i]
        menu_item.connect("activate", _change_panel_position, panel_id, available_positions[i])
    
    return positions_menu

def get_tabs_menu_item():
    tabs_menu_item = Gtk.MenuItem(_("Tabs Positions"))
    tabs_menu = Gtk.Menu()
    tabs_menu_item.set_submenu(tabs_menu)
    
    tabs_positions = editorpersistance.prefs.positions_tabs
    
    for position in tabs_positions:
        tabs_pos = tabs_positions[position]

        positions_tabs_pos_item = Gtk.MenuItem(_positions_names[position])
        tabs_menu.append(positions_tabs_pos_item)

        positions_menu = Gtk.Menu()
        positions_tabs_pos_item.set_submenu(positions_menu)

        up_item = Gtk.RadioMenuItem()
        up_item.set_label(_("Top"))
        positions_menu.append(up_item)

        down_item = Gtk.RadioMenuItem.new_with_label([up_item], _("Bottom"))
        positions_menu.append(down_item)

        if tabs_pos == UP:
            up_item.set_active(True)
        else:
            down_item.set_active(True)
        
        up_item.connect("activate", _change_tabs_pos, position, UP)
        down_item.connect("activate", _change_tabs_pos, position, DOWN)
        
    return tabs_menu_item

def show_layout_press_menu(widget, event):
    menu = _top_bar_button_menu
    guiutils.remove_children(menu)
    _create_layout_presets_menu(menu)
    #menu.connect("hide", _testing_hide)
    
    menu.popup(None, None, None, None, event.button, event.time)

#def _testing_hide(widget):
    #print("hide layout")

def _create_layout_presets_menu(menu):
    callback = _top_bar_menu_item_activated
    
    menu_item = guiutils.get_menu_item(_("Layout Monitor Left"), callback, "monitor_left")
    menu.add(menu_item)

    menu_item = guiutils.get_menu_item(_("Layout Monitor Center"), callback, "monitor_center")
    menu.add(menu_item)

    menu_item = guiutils.get_menu_item(_("Layout Top Row 4 Panels"), callback, "top_row_four")
    menu.add(menu_item)
    if editorstate.SCREEN_WIDTH < 1919:
        menu_item.set_sensitive(False)

    menu_item = guiutils.get_menu_item(_("Layout Media Panel Left Column"), callback, "media_panel_left")
    menu.add(menu_item)
    
    guiutils.add_separetor(menu)
    
    menu_item = guiutils.get_menu_item(_("Save Current Layout..."), callback, "save_layout")
    menu.add(menu_item)

    menu_item = guiutils.get_menu_item(_("Load Layout..."), callback, "load_layout")
    menu.add(menu_item)

    menu.show_all()

def _top_bar_menu_item_activated(widget, msg):
    if msg == "monitor_center":
        apply_layout(MONITOR_CENTER_PANEL_POSITIONS)
    elif msg == "monitor_left":
         apply_layout(DEFAULT_PANEL_POSITIONS)
    elif msg == "top_row_four":
         apply_layout(TOP_ROW_FOUR_POSITIONS)
    elif msg == "media_panel_left":
         apply_layout(MEDIA_PANEL_LEFT_POSITIONS)
    elif msg == "save_layout":
        data = (editorpersistance.prefs.panel_positions, editorpersistance.prefs.positions_tabs)
        dialogs.save_layout_data(_save_layout_callback, data)
    elif msg == "load_layout":
        dialogs.load_layout_data(_load_layout_callback)

def _save_layout_callback(dialog, response_id, data):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        with atomicfile.AtomicFileWriter(save_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(data, write_file)
            
    dialog.destroy()

def _load_layout_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        try:
            load_path = dialog.get_filenames()[0]
            layout_data = utils.unpickle(load_path)
            panel_positions, positions_tabs = layout_data
            apply_layout(panel_positions)
            editorpersistance.prefs.panel_positions = panel_positions
            editorpersistance.prefs.positions_tabs = positions_tabs
            editorpersistance.save()
            apply_tabs_positions()
        except Exception as e:
            apply_layout(DEFAULT_PANEL_POSITIONS)
            editorpersistance.save()
            dialogutils.info_message(_("Loading Layout Filed!"), "Exception message: " + str(e), gui.editor_window.window)
                    
    dialog.destroy()
    
# ----------------------------------------------- CHANGING POSITIONS
def _change_panel_position(widget, panel_id, pos_option):
    # We're again getting one event for activated item and one for the de-activated item.
    if widget != None and widget.get_active() == False:
        return

    # Remove panel if it currently has position in layout.
    if _panel_positions[panel_id] != appconsts.PANEL_PLACEMENT_NOT_VISIBLE:
        _remove_panel(panel_id)

    # Add panel if new position is part of layout.
    if pos_option != appconsts.PANEL_PLACEMENT_NOT_VISIBLE:
        _add_panel(panel_id, pos_option)
    else:
        _panel_positions[panel_id] = pos_option

    # Show layout immediately if this called to change single position,
    # applying layout changes multiple positions.
    if widget != None:
        gui.editor_window.window.show_all()
        set_positions_frames_visibility()
        GObject.timeout_add(100, _check_dimensions)
        
def _check_dimensions():
    top_row_min_width = get_top_row_minimum_width()
    bottom_row_min_width = get_bottom_row_minimum_width()

    if top_row_min_width > editorstate.SCREEN_WIDTH or bottom_row_min_width > editorstate.SCREEN_WIDTH:
        primary_txt = _("Custom layout does not fit on screen!") 
        
        info_text = _("Available screen dimensions: ") + str(editorstate.SCREEN_WIDTH) + " x " +  str(editorstate.SCREEN_HEIGHT) + "\n\n"
        if top_row_min_width > editorstate.SCREEN_WIDTH:
            info_text = info_text + _("Top row width:        ") + str(top_row_min_width) + "\n"
        if bottom_row_min_width > editorstate.SCREEN_WIDTH:
            info_text = info_text + _("Bottom row width:     ") + str(bottom_row_min_width) + "\n\n"
        
        info_text = info_text + _("Change panels positions or remove buttons from midbar\nto make layout fit on screen.")

        dialogutils.info_message(primary_txt, info_text, gui.editor_window.window)

    return  False

def get_top_row_minimum_width():
    player_buttons_w, h = gui.editor_window.player_buttons_row.get_preferred_width()
    top_default_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT].get_preferred_width()
    top_right_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT].get_preferred_width()
    left_column_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_LEFT_COLUMN].get_preferred_width() 
    top_left_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT].get_preferred_width() 
    combined = top_default_w + top_right_w + left_column_w + top_left_w + player_buttons_w
    return combined

def get_bottom_row_minimum_width():
    middle_bar_w, h = gui.editor_window.edit_buttons_row.get_preferred_width()
    bottom_left_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT].get_preferred_width()
    bottom_right_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT].get_preferred_width()
    left_column_w, h = _get_position_frames_dict()[appconsts.PANEL_PLACEMENT_LEFT_COLUMN].get_preferred_width() 
    combined = middle_bar_w + bottom_left_w + bottom_right_w + left_column_w
    return combined
    
def _remove_panel(panel_id):
    current_position = _panel_positions[panel_id]
    panel_widgets = _get_panels_widgets_dict(gui.editor_window)
    panel_widget = panel_widgets[panel_id]
    notebook = _position_notebooks[current_position]
    
    if notebook != None:
        notebook.remove(panel_widget)

        if len(notebook.get_children()) == 1:
            # 1 panel left in position, get rid of notebook and 
            # move remaining panel in frame
            position_frame = _get_position_frames_dict()[current_position]
            position_frame.remove(notebook)
            _position_notebooks[current_position] = None
            
            last_widget = notebook.get_children()[0]
            notebook.remove(last_widget)
            position_frame.add(last_widget)

    else:
        # Panel is in position frame as single panel
        position_frame = _get_position_frames_dict()[current_position]
        position_frame.remove(panel_widget)

def _add_panel(panel_id, position):
    panel_widgets = _get_panels_widgets_dict(gui.editor_window)
    panel_widget = panel_widgets[panel_id]
    notebook = _position_notebooks[position]
    
    if notebook != None:
        # Determine position in notebook.
        insert_index = _get_insert_index(panel_widget, notebook)
        label_str = _panels_names[panel_id]
        if insert_index < notebook.get_n_pages():
            notebook.insert_page(panel_widget, Gtk.Label(label=label_str), insert_index)
        else:
            notebook.append_page(panel_widget, Gtk.Label(label=label_str))
    else:
        position_frames = _get_position_frames_dict()
        position_frame = position_frames[position]
        if len(_get_position_panels(position)) == 0:
            # Panel is added into position hat has no panels currently.
            position_frame.add(panel_widget)
        else:
            # Panel is added into position that has one panel currently.
            # Remove current panel, create notebook, add two panels into it,
            # add it into layout and notebooks dict.
            position_frame.remove(position_frame.get_child())
            _panel_positions[panel_id] = position
            notebook = _create_notebook(position, gui.editor_window)
            position_frame.add(notebook)
            _position_notebooks[position] = notebook

    _panel_positions[panel_id] = position

def _change_tabs_pos(widget, position, direction):
    if widget.get_active() == False:
        return

    editorpersistance.prefs.positions_tabs[position] = direction
    editorpersistance.save()

    apply_tabs_positions()

def apply_tabs_positions():
    tabs_positions = editorpersistance.prefs.positions_tabs
    for position in tabs_positions:
        tabs_pos = tabs_positions[position]
        notebook = _position_notebooks[position]
        if notebook != None:
            if tabs_pos == UP:
                notebook.set_tab_pos(Gtk.PositionType.TOP)
            else:
                notebook.set_tab_pos(Gtk.PositionType.BOTTOM)

def apply_layout(layout_dict):
    for panel_id, layout_position in layout_dict.items():
        try:
            current_position = _panel_positions[panel_id]
            if current_position != layout_position:
                _change_panel_position(None, panel_id, layout_position)
        except KeyError:
            pass # Not all panels are part of current layout
            
    gui.editor_window.window.show_all()
    set_positions_frames_visibility()


