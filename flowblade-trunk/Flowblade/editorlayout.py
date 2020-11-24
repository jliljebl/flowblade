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
import gui


# Transforms when adding panels.
# 0 -> 1    The pre-created Gtk.Frame is filled with added panel.
# 1 -> 2    The pre-created Gtk.Frame is removed from layout box and panel is removed from it
#           New notebook id created and both panels are added into it.
# 2 -> N    Panel is added into existing notebook.

# Transforms when removing panels.
# N -> 2    Panel is removed from notebook.
# 2 -> 1    Notebook is removed from pre-created Gtk.Frame, panel is removed from noteboook
#           and added to pre-created Gtk.Frame.
# 1 -> 0    Panel is removed from the pre-created Gtk.Frame.

# Pre-created Gtk.Frames exist all through app life-cycle, notebooks are dynamically created
# as needed. 

# The exception for these transforms here is top row default notebook 
# that is forced to always exit with at least two panels displayed.
# This makes easier to add and remove top row panels.

DEFAULT_PANEL_POSITIONS = { \
    appconsts.PANEL_MEDIA: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTER_SELECT: appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, # This is the only different default position.
    appconsts.PANEL_RANGE_LOG: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_FILTERS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_COMPOSITORS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_JOBS: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_RENDERING: appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,
    appconsts.PANEL_PROJECT: appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT,
    appconsts.PANEL_PROJECT_SMALL_SCREEN: None, # default values are for large screen single window layout, these are modified on startup if needed.
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: None # default values are for large screen single window layout, these are modified on startup if needed.
}

AVAILABLE_PANEL_POSITIONS_OPTIONS = { \
    appconsts.PANEL_MEDIA: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_FILTERS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT,  appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_LEFT_COLUMN, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT],
    appconsts.PANEL_COMPOSITORS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_RANGE_LOG: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_RENDERING: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_JOBS: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_PROJECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT],
    appconsts.PANEL_PROJECT_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN: [appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT],
    appconsts.PANEL_FILTER_SELECT: [appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, appconsts.PANEL_PLACEMENT_NOT_VISIBLE]
}

PANEL_ORDER_IN_NOTEBOOKS = [appconsts.PANEL_MEDIA, appconsts.PANEL_FILTER_SELECT, appconsts.PANEL_RANGE_LOG, 
                            appconsts.PANEL_FILTERS, appconsts.PANEL_COMPOSITORS,
                            appconsts.PANEL_JOBS, appconsts.PANEL_RENDERING,
                            appconsts.PANEL_PROJECT, appconsts.PANEL_PROJECT_SMALL_SCREEN,
                            appconsts.PANEL_MEDIA_AND_BINS_SMALL_SCREEN]

# Saved data struct holding panel positions information.
_panel_positions = None

# Gtk.Notebooks that may or may not exist to containe 2-N panel is layou position
_position_notebooks = {}

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
    global _panel_positions, _positions_names, _panels_names, _position_notebooks
    _panel_positions = editorpersistance.prefs.panel_positions

    _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
    editorpersistance.prefs.panel_positions = _panel_positions
    editorpersistance.save()
        
    if _panel_positions == None:
        _panel_positions = copy.deepcopy(DEFAULT_PANEL_POSITIONS)
        editorpersistance.prefs.panel_positions = _panel_positions
        editorpersistance.save()

    # Translations need to be initialized after modules have been loaded.
    _positions_names = { \
        appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT: _("Top Row Default Notebook"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT: _("Top Row Right"),
        appconsts.PANEL_PLACEMENT_LEFT_COLUMN: _("Left Column"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT:  _("Bottom Row Left"),
        appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT:_("Bottom Row Right"),
        appconsts.PANEL_PLACEMENT_NOT_VISIBLE:_("Not Visible"),
        appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT:_("Top Row Project Panel Default"),
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
        # These are inveriably not equal because the way we handle radiomenuitem events.
        if insert_widget_ordinal < page_ordinal:
            return i

    return notebook.get_n_pages()


# ----------------------------------------------------------- PANELS PLACEMENT
def create_position_widget(editor_window, position):
    # This method creates and returns the widget that is put into the frame 
    # holding panel/s in given position.
    # If no panels go into position, None is returned.
    # If 1 panel in position, then that panel itself is the widget.
    # If 2-N panels in position, then a notebook containing panels in position is the widget.
    # We also return flag whether the returned widget is notebook.
    panels = _get_position_panels(position)
    panel_widgets = _get_panels_widgets_dict(editor_window)
    
    global _position_notebooks
    if len(panels) == 0:
        return (None, False) 
    elif len(panels) == 1:
        _position_notebooks[position] = None
        return (panel_widgets[panels[0]], False)
    else:
        notebook = _create_notebook(position, editor_window)
        _position_notebooks[position] = notebook
        return (notebook, True)

def _create_notebook(position, editor_window):
    notebook = Gtk.Notebook()
    panels = _get_position_panels(position)
    panel_widgets = _get_panels_widgets_dict(editor_window)
    
    for panel in panels:
        widget = panel_widgets[panel]
        label = Gtk.Label(label=_panels_names[panel])
        notebook.append_page(widget, label)
    
    return notebook
    
# ---------------------------------------------------------- APP MENU
def get_panel_positions_menu_item():
    panel_positions_menu_item = Gtk.MenuItem(_("Panel Placement"))
    panel_positions_menu = Gtk.Menu()
    panel_positions_menu_item.set_submenu(panel_positions_menu)

    # Project Panel
    project_panel_menu_item = Gtk.MenuItem(_("Project Panel"))
    panel_positions_menu.append(project_panel_menu_item)

    project_panel_menu = _get_position_selection_menu(appconsts.PANEL_PROJECT)
    project_panel_menu_item.set_submenu(project_panel_menu)
    
    # Media Panel
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
    filter_panel_menu_item = Gtk.MenuItem(_("Filter Panel"))
    panel_positions_menu.append(filter_panel_menu_item)

    filter_panel_menu =  _get_position_selection_menu(appconsts.PANEL_FILTERS)
    filter_panel_menu_item.set_submenu(filter_panel_menu)

    # Compositors Panel
    compositors_panel_menu_item = Gtk.MenuItem(_("Compositors Panel"))
    panel_positions_menu.append(compositors_panel_menu_item)

    compositors_panel_menu =  _get_position_selection_menu(appconsts.PANEL_COMPOSITORS)
    compositors_panel_menu_item.set_submenu(compositors_panel_menu)

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
        #pos_option = available_positions[i]
        print(panel_id, available_positions[i])
        menu_item.connect("activate", _change_panel_position, panel_id, available_positions[i])
        #menu_item.option_index = i
    
    return positions_menu
    
    
# ----------------------------------------------- CHANGING POSITIONS
def _change_panel_position(widget, panel_id, pos_option):
    print(_panel_positions)
    print(panel_id, pos_option)
    if widget.get_active() == False:
        print("not active label", widget.get_label())
        return
    
    print("ACTIVE label", widget.get_label())
    #group_index = widget.get_group().index(widget)

    #print(panel_id, pos_option)
    # Remove panel if it currently has position in layout.
    if _panel_positions[panel_id] != appconsts.PANEL_PLACEMENT_NOT_VISIBLE:
        print("remove")
        _remove_panel(panel_id)
    else:
        print("in appconsts.PANEL_PLACEMENT_NOT_VISIBLE, NO REMOVE")
    # Add panel if new position is part of layout.
    if pos_option != appconsts.PANEL_PLACEMENT_NOT_VISIBLE:
        print("add")
        _add_panel(panel_id, pos_option)
    else:
        print("else")
        _panel_positions[panel_id] = pos_option
             
    gui.editor_window.window.show_all()
    
def _remove_panel(panel_id):
    current_position = _panel_positions[panel_id]
    panel_widgets = _get_panels_widgets_dict(gui.editor_window)
    panel_widget = panel_widgets[panel_id]
    notebook = _position_notebooks[current_position]
    
    if notebook != None:
        print("1")
        notebook.remove(panel_widget)

        if len(notebook.get_children()) == 1:
            print("2")
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
    
    """
    if position == appconsts.PANEL_PLACEMENT_LEFT_COLUMN:
        # These are Gtk.Box widgets
        position_frame.pack_start(panel_widget, False, False, 0)
    else:
        # These are gtk.Frames
        position_frame.add(panel_widget)
    """

"""        
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
    
"""
def _show_media_panel_top_row_notebook(self, widget):
    if widget.get_active() == False:
        return

    self.app_h_box.remove(self.mm_paned_frame)

    self.mm_paned_frame.remove(self.mm_paned)
    self.mm_paned_frame = None

    media_label = Gtk.Label(label=_("Media"))
    self.notebook.insert_page(self.mm_paned, media_label, 0)

    self.window.show_all()
    
    editorpersistance.prefs.placement_media_panel = appconsts.PANEL_PLACEMENT_TOP_ROW_NOTEBOOK
    editorpersistance.save()

def _show_media_panel_left_column(self, widget):
    if widget.get_active() == False:
        return
        
    self.notebook.remove(self.mm_paned)

    self.mm_paned_frame = guiutils.get_panel_etched_frame(self.mm_paned)
    self.mm_paned_frame = guiutils.set_margins(self.mm_paned_frame, 0, 0, 1, 0)

    self.app_h_box.pack_start(self.mm_paned_frame , False, False, 0)
    self.window.show_all()

    editorpersistance.prefs.placement_media_panel = appconsts.PANEL_PLACEMENT_LEFT_COLUMN
    editorpersistance.save()
"""
