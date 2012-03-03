"""
Module handles saving and loading data that is related to the editor and not any particular project.
"""
import gtk
import os
import pickle

import utils
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
        for i in range (0, len(recent_proj_names) - 1):
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
        auto_play_in_clip_monitor_check, auto_center_check = edit_prefs_widgets

        global prefs
        prefs.open_in_last_opended_media_dir = open_in_last_opened_check.get_active()
        prefs.display_splash_screen = disp_splash.get_active()        
        prefs.default_profile_index = default_profile_combo.get_active()
        prefs.undos_max = undo_max_spin.get_adjustment().get_value()

        prefs.auto_play_in_clip_monitor = auto_play_in_clip_monitor_check.get_active()
        prefs.auto_center_on_play_stop = auto_center_check.get_active()

class EditorPreferences:
    """
    Class holds data of persistant user preferences for editor.
    """
    
    def __init__(self):
        self.open_in_last_opended_media_dir = True
        self.last_opened_media_dir = None
        self.img_length = 2000
        self.auto_save_delay_value_index = 0 # value is index of appconsts.AUTO_SAVE_OPTS
        self.undos_max = UNDO_STACK_DEFAULT
        self.default_profile_index = 10 # value is index of mltprofiles._profile_list
        self.auto_play_in_clip_monitor = False
        self.auto_center_on_play_stop = False
        self.thumbnail_folder = None
        self.hidden_profile_names = []
        self.display_splash_screen = True
    
