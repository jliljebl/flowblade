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

import os
import pickle

import appconsts
import atomicfile
import mltprofiles
import userfolders
import utils # this needs to also go to not load Gtk for background rendering process

PREFS_DOC = "prefs"
RECENT_DOC = "recent"

MAX_RECENT_PROJS = 15
UNDO_STACK_DEFAULT = 30
UNDO_STACK_MIN = 10
UNDO_STACK_MAX = 100

GLASS_STYLE = 0
SIMPLE_STYLE = 1
NO_DECORATIONS = 2

prefs = None
recent_projects = None

def load():
    """
    If docs fail to load, new ones are created and saved.
    """
    prefs_file_path = userfolders.get_config_dir() + PREFS_DOC
    recents_file_path = userfolders.get_config_dir() + RECENT_DOC

    global prefs, recent_projects

    try:
        prefs = utils.unpickle(prefs_file_path)
    except:
        prefs = EditorPreferences()
        with atomicfile.AtomicFileWriter(prefs_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(prefs, write_file)

    # Override deprecated preferences to default values.
    prefs.delta_overlay = True
    prefs.auto_play_in_clip_monitor = False
    prefs.empty_click_exits_trims = True
    prefs.quick_enter_trims = True
    prefs.remember_monitor_clip_frame = True

    try:
        recent_projects = utils.unpickle(recents_file_path)
    except:
        recent_projects = utils.EmptyClass()
        recent_projects.projects = []
        with atomicfile.AtomicFileWriter(recents_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(recent_projects, write_file)

    # Remove non-existing projects from recents list
    remove_list = []
    for proj_path in recent_projects.projects:
        if os.path.isfile(proj_path) == False:
            remove_list.append(proj_path)

    if len(remove_list) > 0:
        for proj_path in remove_list:
            recent_projects.projects.remove(proj_path)
        with atomicfile.AtomicFileWriter(recents_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(recent_projects, write_file)

    # Versions of program may have different prefs objects and
    # we may need to to update prefs on disk if user has e.g.
    # installed later version of Flowblade.
    current_prefs = EditorPreferences()

    if len(prefs.__dict__) != len(current_prefs.__dict__):
        current_prefs.__dict__.update(prefs.__dict__)
        prefs = current_prefs
        with atomicfile.AtomicFileWriter(prefs_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(prefs, write_file)
        print("prefs updated to new version, new param count:", len(prefs.__dict__))

def save():
    """
    Write out prefs and recent_projects files
    """
    prefs_file_path = userfolders.get_config_dir()+ PREFS_DOC
    recents_file_path = userfolders.get_config_dir() + RECENT_DOC

    with atomicfile.AtomicFileWriter(prefs_file_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(prefs, write_file)

    with atomicfile.AtomicFileWriter(recents_file_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(recent_projects, write_file)

def add_recent_project_path(path):
    """
    Called when project is saved.
    """
    if len(recent_projects.projects) == MAX_RECENT_PROJS:
        recent_projects.projects.pop(-1)

    # Reject autosaves.
    autosave_dir = userfolders.get_cache_dir() + appconsts.AUTOSAVE_DIR
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

def remove_non_existing_recent_projects():
    # Remove non-existing projects from recents list
    recents_file_path = userfolders.get_config_dir() + RECENT_DOC
    remove_list = []
    for proj_path in recent_projects.projects:
        if os.path.isfile(proj_path) == False:
            remove_list.append(proj_path)

    if len(remove_list) > 0:
        for proj_path in remove_list:
            recent_projects.projects.remove(proj_path)
        with atomicfile.AtomicFileWriter(recents_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(recent_projects, write_file)

def get_recent_projects():
    """
    Returns list of names of recent projects.
    """
    proj_list = []
    for proj_path in recent_projects.projects:
        proj_list.append(os.path.basename(proj_path))

    return proj_list

def update_prefs_from_widgets(widgets_tuples_tuple):
    # Aug-2019 - SvdB - BB - Replace double_track_hights by double_track_hights
    # Unpack widgets
    # Toolbar preferences panel for free elements and order
    gen_opts_widgets, edit_prefs_widgets, playback_prefs_widgets, view_prefs_widgets, performance_widgets = widgets_tuples_tuple
    # End of Toolbar preferences panel for free elements and order

    # Aug-2019 - SvdB - AS - added autosave_combo
    default_profile_combo, open_in_last_opened_check, open_in_last_rendered_check, undo_max_spin, load_order_combo, \
        autosave_combo, render_folder_select, disk_cache_warning_combo = gen_opts_widgets

    # Jul-2016 - SvdB - Added play_pause_button
    # Apr-2017 - SvdB - Added ffwd / rev values
    gfx_length_spin, cover_delete, mouse_scroll_action, hide_file_ext_button, \
    hor_scroll_dir, effects_editor_clip_load, auto_render_plugins = edit_prefs_widgets

    auto_center_check, play_pause_button, timeline_start_end_button, auto_center_on_updown, \
    ffwd_rev_shift_spin, ffwd_rev_ctrl_spin, ffwd_rev_caps_spin, follow_move_range, loop_clips = playback_prefs_widgets
    
    force_language_combo, disp_splash, buttons_style, theme, theme_fallback_combo, audio_levels_combo, \
    window_mode_combo, full_names, double_track_hights, top_row_layout, layout_monitor, colorized_icons = view_prefs_widgets

    # Jan-2017 - SvdB
    perf_render_threads, perf_drop_frames = performance_widgets

    global prefs
    prefs.open_in_last_opended_media_dir = open_in_last_opened_check.get_active()
    prefs.remember_last_render_dir = open_in_last_rendered_check.get_active()
    prefs.default_profile_name = mltprofiles.get_profile_name_for_index(default_profile_combo.get_active())
    prefs.undos_max = undo_max_spin.get_adjustment().get_value()
    prefs.media_load_order = load_order_combo.get_active()

    prefs.auto_center_on_play_stop = auto_center_check.get_active()
    prefs.default_grfx_length = int(gfx_length_spin.get_adjustment().get_value())
    prefs.trans_cover_delete = cover_delete.get_active()

    # Jul-2016 - SvdB - For play/pause button
    prefs.play_pause = play_pause_button.get_active()
# ------------------------------ timeline_start_end_button
    prefs.timeline_start_end = timeline_start_end_button.get_active()
# -------------------------------End of timeline_start_end_button
    prefs.hide_file_ext = hide_file_ext_button.get_active()
    prefs.mouse_scroll_action_is_zoom = (mouse_scroll_action.get_active() == 0)
    prefs.scroll_horizontal_dir_up_forward = (hor_scroll_dir.get_active() == 0)
    prefs.single_click_effects_editor_load = (effects_editor_clip_load.get_active() == 1)
    # Apr-2017 - SvdB - ffwd / rev values
    prefs.ffwd_rev_shift = int(ffwd_rev_shift_spin.get_adjustment().get_value())
    prefs.ffwd_rev_ctrl = int(ffwd_rev_ctrl_spin.get_adjustment().get_value())
    prefs.ffwd_rev_caps = int(ffwd_rev_caps_spin.get_adjustment().get_value())
    prefs.loop_clips = loop_clips.get_active()

    prefs.use_english_always = False # DEPRECATED, "force_language" used instead
    prefs.force_language = force_language_combo.lang_codes[force_language_combo.get_active()]
    prefs.display_splash_screen = disp_splash.get_active()
    prefs.buttons_style = buttons_style.get_active() # styles enum values and widget indexes correspond

    prefs.theme_fallback_colors = theme_fallback_combo.get_active()
    prefs.display_all_audio_levels = (audio_levels_combo.get_active() == 0)
    prefs.global_layout = window_mode_combo.get_active() + 1 # +1 'cause values are 1 and 2
    # Jan-2017 - SvdB
    prefs.perf_render_threads = int(perf_render_threads.get_adjustment().get_value())
    prefs.perf_drop_frames = perf_drop_frames.get_active()
    # Feb-2017 - SvdB - for full file names
    prefs.show_full_file_names = full_names.get_active()
    prefs.center_on_arrow_move = auto_center_on_updown.get_active()
    prefs.double_track_hights = (double_track_hights.get_active() == 1)
    prefs.playback_follow_move_tline_range = follow_move_range.get_active()
    if theme.get_active() == 1: # The displayed options indices do not correspond with theme const values.
        prefs.theme = appconsts.FLOWBLADE_THEME_GRAY
    elif theme.get_active() == 0: # The displayed options indices do not correspond with theme const values.
        prefs.theme = appconsts.FLOWBLADE_THEME_NEUTRAL
    else:    
        prefs.theme = theme.get_active() - 2
    prefs.top_row_layout = top_row_layout.get_active()
    # Aug-2019 - SvdB - AS
    prefs.auto_save_delay_value_index = autosave_combo.get_active()
    prefs.layout_display_index = layout_monitor.get_active()
    if len(render_folder_select.get_filenames()) != 0:
        prefs.default_render_directory = render_folder_select.get_filename()
    prefs.disk_space_warning = disk_cache_warning_combo.get_active()

    # --------------------------------- Colorized icons
    prefs.colorized_icons = colorized_icons.get_active()
    prefs.auto_render_media_plugins = auto_render_plugins.get_active()

def get_graphics_default_in_out_length():
    in_fr = int(15000/2) - int(prefs.default_grfx_length/2)
    out_fr = in_fr + int(prefs.default_grfx_length) - 1 # -1, out inclusive
    return (in_fr, out_fr, prefs.default_grfx_length)


class EditorPreferences:
    """
    Class holds data of persistant user preferences for editor.
    """

    def __init__(self):

        # Every preference needs to have its default value set in this constructor

        self.open_in_last_opended_media_dir = True
        self.last_opened_media_dir = None
        self.img_length = 2000
        self.auto_save_delay_value_index = 1 # value is index of AUTO_SAVE_OPTS in preferenceswindow._general_options_panel()
        self.undos_max = UNDO_STACK_DEFAULT
        self.default_profile_name = 10 # index of default profile
        self.auto_play_in_clip_monitor = False  # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.auto_center_on_play_stop = True
        self.thumbnail_folder = None # DEPRECATED, this is set by XDG variables now.
        self.hidden_profile_names = []
        self.display_splash_screen = True
        self.auto_move_after_edit = False
        self.default_grfx_length = 250 # value is in frames
        self.track_configuration = 0 # DEPRECATED
        self.AUTO_SAVE_OPTS = None # not used, these are created and translated else where
        self.tabs_on_top = False # DEPRECATED, we have positions_tabs now that we possibly have possibly multiple notebooks 
        self.midbar_tc_left = True
        self.default_layout = True # DEPRECATED, NOT USED ANYMORE
        self.exit_allocation = (0, 0)
        self.media_columns = 3
        self.app_v_paned_position = 500 # Paned get/set position value
        self.top_paned_position = 600 # Paned get/set position value
        self.mm_paned_position = 260 # Paned get/set position value
        self.render_folder = None  # DEPRECATED, this set by XDG variables now
        self.show_sequence_profile = True
        self.buttons_style = NO_DECORATIONS
        self.dark_theme = False # DEPRECATED, "theme" used instead
        self.remember_last_render_dir = True
        self.empty_click_exits_trims = True # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.quick_enter_trims = True # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.show_vu_meter = True  # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.remember_monitor_clip_frame = True # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.jack_start_up_op = appconsts.JACK_ON_START_UP_NO # not used
        self.jack_frequency = 48000 # not used
        self.jack_output_type = appconsts.JACK_OUT_AUDIO # not used
        self.media_load_order = appconsts.LOAD_ABSOLUTE_FIRST
        self.use_english_always = False # DEPRECATED, "force_language" used instead
        self.theme_fallback_colors = 4 # index of gui._THEME_COLORS
        self.display_all_audio_levels = True
        self.overwrite_clip_drop = True # DEPRECATED, "dnd_action" used instead
        self.trans_cover_delete = True
        # Jul-2016 - SvdB - For play/pause button
        self.play_pause = False
        # ------------------------------ timeline_start_end_button
        self.timeline_start_end = False
        # ------------------------------End of timeline_start_end_button
        self.midbar_layout = appconsts.MIDBAR_TC_LEFT
        self.global_layout = appconsts.SINGLE_WINDOW
        self.trim_view_default = appconsts.TRIM_VIEW_OFF
        self.trim_view_message_shown = False
        self.exit_allocation_window_2 = (0, 0, 0, 0)
        self.mouse_scroll_action_is_zoom = True
        self.hide_file_ext = False
        # Jan-2017 - SvdB
        self.perf_render_threads = 1
        self.perf_drop_frames = False
        # Feb-2017 - SvdB - for full file names
        self.show_full_file_names = False
        self.center_on_arrow_move = True
        # Apr-2017 - SvdB - Using these values we maintain the original hardcoded speed
        self.ffwd_rev_shift = 1
        self.ffwd_rev_ctrl = 10
        self.ffwd_rev_caps = 1
        self.shortcuts = "flowblade.xml"
        self.double_track_hights = False
        self.delta_overlay = True # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.show_alpha_info_message = True
        self.playback_follow_move_tline_range = True
        self.active_tools = [1, 2, 3, 4, 5, 6, 7]
        self.top_level_project_panel = True # DEPRECATED, NOT USER SETTABLE ANYMORE
        self.theme = appconsts.FLOWBLADE_THEME_NEUTRAL
        self.dnd_action = appconsts.DND_OVERWRITE_NON_V1
        self.top_row_layout = appconsts.THREE_PANELS_IF_POSSIBLE # DEPRECATED, we have new window layout data.
        self.box_for_empty_press_in_overwrite_tool = False
        self.scroll_horizontal_dir_up_forward = True
        self.kf_edit_init_affects_playhead = False # DEPRECATED, this feature is now removed, kf editor inits no longer have effect on playhead
        self.show_tool_tooltips = True
        self.workflow_dialog_last_version_shown = "0.0.1"
        self.loop_clips = False
        self.audio_scrubbing = False
        self.force_language = "None"
        self.default_compositing_mode = appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK
        self.single_click_effects_editor_load = False
        self.layout_display_index = 0 # 0 == full area - 1,2... monitor number
        self.default_render_directory = appconsts.USER_HOME_DIR
        self.tline_render_encoding = 0 # index of available proxy encodings, timeline rendering uses same encodings.
        self.tline_render_size = appconsts.PROXY_SIZE_FULL
        self.open_jobs_panel_on_add = True
        self.render_jobs_sequentially = True
        self.disk_space_warning = 1 #  [off, 500MB,1GB, 2GB], see preferenceswindow.py
        # Toolbar preferences panel for free elements and order
        self.groups_tools =  [  appconsts.WORKFLOW_LAUNCH, appconsts.TOOL_SELECT, appconsts.BUTTON_GROUP_ZOOM, \
                                appconsts.BUTTON_GROUP_UNDO, appconsts.BUTTON_GROUP_TOOLS, appconsts.BUTTON_GROUP_EDIT, \
                                appconsts.BUTTON_GROUP_DELETE ,  appconsts.BUTTON_GROUP_SYNC_SPLIT, \
                                appconsts.BUTTON_GROUP_MONITOR_ADD, appconsts.BIG_TIME_CODE] # DEPRECATED, we are now using 'layout_buttons'
        self.cbutton  = [True, True, True, True, True, True, True, True, True, True] # Toolbar objects active state
        self.colorized_icons = False
        self.tools_selection = appconsts.TOOL_SELECTOR_IS_MENU
        self.panel_positions = None
        self.force_small_midbar = False # DEPRECATED, after tools moved to topbar we can always support w >=1280 screens and do not care about smaller ones.
        self.positions_tabs = None
        self.midbar_layout_buttons = None
        self.auto_expand_tracks = True
        self.quick_effects = None
        self.auto_render_media_plugins = True
        