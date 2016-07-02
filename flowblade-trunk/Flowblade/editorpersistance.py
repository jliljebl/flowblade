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


from gi.repository import Gtk

import os
import pickle

import appconsts
import mltprofiles
import utils

PREFS_DOC = "prefs"
RECENT_DOC = "recent"

MAX_RECENT_PROJS = 15
UNDO_STACK_DEFAULT = 30
UNDO_STACK_MIN = 10
UNDO_STACK_MAX = 100

GLASS_STYLE = 0
SIMPLE_STYLE = 1

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

    # Remove non-existing projects from recents list
    remove_list = []
    for proj_path in recent_projects.projects:
        if os.path.isfile(proj_path) == False:
            remove_list.append(proj_path)

    if len(remove_list) > 0:
        for proj_path in remove_list:
            recent_projects.projects.remove(proj_path)
        write_file = file(recents_file_path, "wb")
        pickle.dump(recent_projects, write_file)
        
    # Versions of program may have different prefs objects and 
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
    Called when project is saved.
    """
    if len(recent_projects.projects) == MAX_RECENT_PROJS:
        recent_projects.projects.pop(-1)
        
    # Reject autosaves.
    autosave_dir = utils.get_hidden_user_dir_path() + appconsts.AUTOSAVE_DIR
    file_save_dir = os.path.dirname(path) + "/"        
    if file_save_dir == autosave_dir:
        return

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
            proj_name = proj_name.replace("_","__") # to display names with underscored correctly
            new_item = Gtk.MenuItem(proj_name)
            new_item.connect("activate", callback, i)
            menu.append(new_item)
            new_item.show()
    # ...or a single non-sensitive Empty item 
    else:
        new_item = Gtk.MenuItem(_("Empty"))
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
    gen_opts_widgets, edit_prefs_widgets, view_prefs_widgets = widgets_tuples_tuple

    default_profile_combo, open_in_last_opened_check, open_in_last_rendered_check, undo_max_spin, load_order_combo = gen_opts_widgets
    
    # Jul-2016 - SvdB - Added play_pause_button
    auto_play_in_clip_monitor_check, auto_center_check, grfx_insert_length_spin, \
    trim_exit_click, trim_quick_enter, remember_clip_frame, overwrite_clip_drop, cover_delete, play_pause_button = edit_prefs_widgets
    
    use_english, disp_splash, buttons_style, dark_theme, theme_combo, audio_levels_combo = view_prefs_widgets

    global prefs
    prefs.open_in_last_opended_media_dir = open_in_last_opened_check.get_active()
    prefs.remember_last_render_dir = open_in_last_rendered_check.get_active()
    prefs.default_profile_name = mltprofiles.get_profile_name_for_index(default_profile_combo.get_active())
    prefs.undos_max = undo_max_spin.get_adjustment().get_value()
    prefs.media_load_order = load_order_combo.get_active()

    prefs.auto_play_in_clip_monitor = auto_play_in_clip_monitor_check.get_active()
    prefs.auto_center_on_play_stop = auto_center_check.get_active()
    prefs.default_grfx_length = int(grfx_insert_length_spin.get_adjustment().get_value())
    prefs.empty_click_exits_trims = trim_exit_click.get_active()
    prefs.quick_enter_trims = trim_quick_enter.get_active()
    prefs.remember_monitor_clip_frame = remember_clip_frame.get_active()
    prefs.overwrite_clip_drop = (overwrite_clip_drop.get_active() == 0)
    prefs.trans_cover_delete = cover_delete.get_active()
    # Jul-2016 - SvdB - For play/pause button
    prefs.play_pause = play_pause_button.get_active()
    
    prefs.use_english_always = use_english.get_active()
    prefs.display_splash_screen = disp_splash.get_active()
    prefs.buttons_style = buttons_style.get_active() # styles enum values and widget indexes correspond
    prefs.dark_theme = (dark_theme.get_active() == 1)
    prefs.theme_fallback_colors = theme_combo.get_active() 
    prefs.display_all_audio_levels = (audio_levels_combo.get_active() == 0)

def get_graphics_default_in_out_length():
    in_fr = int(15000/2) - int(prefs.default_grfx_length/2)
    out_fr = in_fr + int(prefs.default_grfx_length) - 1 # -1, out inclusive
    return (in_fr, out_fr, prefs.default_grfx_length)

def create_thumbs_folder_if_needed(user_dir):
    if prefs.thumbnail_folder == None:
        thumbs_folder = user_dir + appconsts.THUMBNAILS_DIR
        if not os.path.exists(thumbs_folder + "/"):
            os.mkdir(thumbs_folder + "/")
        prefs.thumbnail_folder = thumbs_folder

def create_rendered_clips_folder_if_needed(user_dir):
    if prefs.render_folder == None:
        render_folder = user_dir + appconsts.RENDERED_CLIPS_DIR
        if not os.path.exists(render_folder + "/"):
            os.mkdir(render_folder + "/")
        prefs.render_folder = render_folder


class EditorPreferences:
    """
    Class holds data of persistant user preferences for editor.
    """

    def __init__(self):
        self.open_in_last_opended_media_dir = True
        self.last_opened_media_dir = None
        self.img_length = 2000
        self.auto_save_delay_value_index = 1 # value is index of AUTO_SAVE_OPTS in preferenceswindow._general_options_panel()
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
        self.AUTO_SAVE_OPTS = None # not used, these are cerated and translated else where
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
        self.buttons_style = GLASS_STYLE
        self.dark_theme = False
        self.remember_last_render_dir = True
        self.empty_click_exits_trims = True
        self.quick_enter_trims = True
        self.show_vu_meter = True
        self.remember_monitor_clip_frame = True
        self.jack_start_up_op = appconsts.JACK_ON_START_UP_NO # not used
        self.jack_frequency = 48000 # not used 
        self.jack_output_type = appconsts.JACK_OUT_AUDIO # not used
        self.media_load_order = appconsts.LOAD_ABSOLUTE_FIRST
        self.use_english_always = False
        self.theme_fallback_colors = 0 # index oc gui._THEME_COLORS
        self.display_all_audio_levels = True
        self.overwrite_clip_drop = True
        self.trans_cover_delete = True
        # Jul-2016 - SvdB - For play/pause button
        self.play_pause = True

