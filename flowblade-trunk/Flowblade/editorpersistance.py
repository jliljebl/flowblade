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
Module handles saving and loading data that is related to the editor and not any particular project.
"""
import gtk
import os
import pickle

import utils
import mltprofiles
import respaths

PREFS_DOC = "prefs"
RECENT_DOC = "recent"

MAX_RECENT_PROJS = 15
UNDO_STACK_DEFAULT = 30
UNDO_STACK_MIN = 10
UNDO_STACK_MAX = 100

prefs = None
recent_projects = None

def load():
    """
    If docs fail to load, new ones are created and saved.
    """
    prefs_file_path = utils.get_hidden_user_dir_path() + PREFS_DOC
    recents_file_path = utils.get_hidden_user_dir_path() + RECENT_DOC

    global prefs, recent_projects
    try:
        f = open(prefs_file_path)
        prefs = pickle.load(f)
    except:
        prefs = EditorPreferences()
        write_file = file(prefs_file_path, "wb")
        pickle.dump(prefs, write_file)

    try:
        f = open(recents_file_path)
        recent_projects = pickle.load(f)
    except:
        recent_projects = utils.EmptyClass()
        recent_projects.projects = []
        write_file = file(recents_file_path, "wb")
        pickle.dump(recent_projects, write_file)

    # version of program may have different prefs objects and 
    # we may need to to update prefs on disk if user has e.g.
    # installed later version of Flowblade
    current_prefs = EditorPreferences()
    if len(prefs.__dict__) != len(current_prefs.__dict__):
        current_prefs.__dict__.update(prefs.__dict__)
        prefs = current_prefs
        write_file = file(prefs_file_path, "wb")
        pickle.dump(prefs, write_file)
        print "prefs updated to new version, new param count:", len(prefs.__dict__)

def save():
    """
    Write out prefs and recent_projects files 
    """
    prefs_file_path = utils.get_hidden_user_dir_path() + PREFS_DOC
    recents_file_path = utils.get_hidden_user_dir_path() + RECENT_DOC
    
    write_file = file(prefs_file_path, "wb")
    pickle.dump(prefs, write_file)

    write_file = file(recents_file_path, "wb")
    pickle.dump(recent_projects, write_file)

def add_recent_project_path(path):
    """
    Called when project saved.
    """
    if len(recent_projects.projects) == MAX_RECENT_PROJS:
        recent_projects.projects.pop(-1)
        
    try:
        index = recent_projects.projects.index(path)
        recent_projects.projects.pop(index)
    except:
        pass
    
    recent_projects.projects.insert(0, path)    
    save()
    
def fill_recents_menu_widget(menu_item, callback):
    """
    Fills menu item with menuitems to open recent projects.
    """
    menu = menu_item.get_submenu()

    # Remove current items
    items = menu.get_children()
    for item in items:
        menu.remove(item)
    
    # Add new menu items
    recent_proj_names = get_recent_projects()
    if len(recent_proj_names) != 0:
        for i in range (0, len(recent_proj_names)):
            proj_name = recent_proj_names[i]
            new_item = gtk.MenuItem(proj_name)
            new_item.connect("activate", callback, i)
            menu.append(new_item)
            new_item.show()
    # ...or a single non-sensitive Empty item 
    else:
        new_item = gtk.MenuItem(_("Empty"))
        new_item.set_sensitive(False)
        menu.append(new_item)
        new_item.show()

def get_recent_projects():
    """
    Returns list of names of recent projects.
    """
    proj_list = []
    for proj_path in recent_projects.projects:
        proj_list.append(os.path.basename(proj_path))
    
    return proj_list
        
def update_prefs_from_widgets(widgets_tuples_tuple):
    # Unpack widgets
    gen_opts_widgets, edit_prefs_widgets = widgets_tuples_tuple
    default_profile_combo, open_in_last_opened_check, undo_max_spin, disp_splash = gen_opts_widgets
    auto_play_in_clip_monitor_check, auto_center_check, auto_move_on_edit, grfx_insert_length_spin = edit_prefs_widgets

    global prefs
    prefs.open_in_last_opended_media_dir = open_in_last_opened_check.get_active()
    prefs.display_splash_screen = disp_splash.get_active()

    prefs.default_profile_name = mltprofiles.get_profile_name_for_index(default_profile_combo.get_active())
    prefs.undos_max = undo_max_spin.get_adjustment().get_value()

    prefs.auto_play_in_clip_monitor = auto_play_in_clip_monitor_check.get_active()
    prefs.auto_center_on_play_stop = auto_center_check.get_active()
    prefs.auto_move_after_edit = auto_move_on_edit.get_active()

    prefs.default_grfx_length = int(grfx_insert_length_spin.get_adjustment().get_value())

def get_graphics_default_in_out_length():
    in_fr = int(15000/2) - int(prefs.default_grfx_length/2)
    out_fr = in_fr + int(prefs.default_grfx_length) - 1 # -1, out inclusive
    return (in_fr, out_fr, prefs.default_grfx_length)
    

    
class EditorPreferences:
    """
    Class holds data of persistant user preferences for editor.
    """
    
    def __init__(self):
        self.open_in_last_opended_media_dir = True
        self.last_opened_media_dir = None
        self.img_length = 2000
        self.auto_save_delay_value_index = 1 # value is index of self.AUTO_SAVE_OPTS
        self.undos_max = UNDO_STACK_DEFAULT
        self.default_profile_name = 10 # index of default profile
        self.auto_play_in_clip_monitor = False
        self.auto_center_on_play_stop = False
        self.thumbnail_folder = None
        self.hidden_profile_names = []
        self.display_splash_screen = True
        self.auto_move_after_edit = False
        self.default_grfx_length = 250 # value is in frames
        self.track_configuration = 0 # this is index on list appconsts.TRACK_CONFIGURATIONS
        self.AUTO_SAVE_OPTS = ((-1, _("No Autosave")),(1, _("1 min")),(2, _("2 min")),(5, _("5 min")))
        self.tabs_on_top = False
        self.midbar_tc_left = True
        self.default_layout = True
        self.exit_allocation = (0, 0)
        self.media_columns = 2
        self.app_v_paned_position = 500 # Paned get/set position value
        self.top_paned_position = 600 # Paned get/set position value
        self.mm_paned_position = 260 # Paned get/set position value
        self.render_folder = None
        self.show_sequence_profile = True
