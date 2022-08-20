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
Application module.

Handles application initialization, shutdown, opening projects, autosave and changing
sequences.
"""

try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass
    
import gi

from gi.repository import GObject
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk

import locale
try:
    import mlt7 as mlt
except:
    import mlt7 as mlt
import hashlib
import os
import sys
import time

import appconsts
import audiomonitoring
import audiowaveform
import audiowaveformrenderer
import clipeffectseditor
import clipmenuaction
import compositeeditor
import containerclip
import containeractions
import dialogs
import dialogutils
import dnd
import diskcachemanagement
import edit
import editevent
import editorlayout
import editorpersistance
import editorstate
import editorwindow
import gmic
import gui
import guicomponents
import jobs
import keyevents
import keyframeeditor
import keyframeeditcanvas
import kftoolmode
import medialog
import mediaplugin
import mltenv
import mltfilters
import mltplayer
import mltprofiles
import mlttransitions
import modesetting
import movemodes
import multitrimmode
import persistance
import positionbar
import preferenceswindow
import processutils
import projectaction
import projectdata
import projectinfogui
import propertyeditorbuilder
import proxyediting
import render
import renderconsumer
import respaths
import resync
import rotomask
import sequence
import shortcuts
import shortcutsquickeffects
import snapping
import threading
import titler
import tlinerender
import tlinewidgets
import toolsintegration
import trimmodes
import translations
import undo
import updater
import userfolders
import utils
import workflow


AUTOSAVE_DIR = appconsts.AUTOSAVE_DIR
AUTOSAVE_FILE = "autosave/autosave"
instance_autosave_id_str = None
PID_FILE = "flowbladepidfile"
BATCH_DIR = "batchrender/"
autosave_timeout_id = -1
recovery_dialog_id = -1
disk_cache_timeout_id = -1
sdl2_timeout_id = -1
loaded_autosave_file = None

splash_screen = None
splash_timeout_id = -1
exit_timeout_id = -1
window_resize_id = -1
window_state_id = -1
resize_timeout_id = -1

_log_file = None

assoc_file_path = None
assoc_timeout_id = None

def main(root_path):
    """
    Called at application start.
    Initializes application with a default project.
    """
    # DEBUG: Direct output to log file if log file set.
    if _log_file != None:
        log_print_output_to_file()

    set_quiet_if_requested()

    print("Application version: " + editorstate.appversion)

    # Print OS, Python version and GTK+ version.
    try:
        os_release_file = open("/etc/os-release","r")
        os_text = os_release_file.read()
        s_index = os_text.find("PRETTY_NAME=")
        e_index = os_text.find("\n", s_index)
        print("OS: " + os_text[s_index + 13:e_index - 1])
    except:
        pass

    print("Python", sys.version)

    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    print("GTK+ version:", gtk_version)
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Create user folders if needed and determine if we're using xdg or dotfile user folders.
    userfolders.init()
    
    # Flatpak still needs to use standard home XDG cache folder for Blender.
    # Flatpak only uses XDG cache folder for Blender and we are keeping this around if we ever
    # succeed in getting Blender going for Flatpak.
    if editorstate.app_running_from == editorstate.RUNNING_FROM_FLATPAK:
        userfolders.init_user_cache_for_flatpak()

    # Set paths.
    respaths.set_paths(root_path)

    # Load editor prefs and list of recent projects.
    editorpersistance.load()
    if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
        respaths.apply_dark_theme()
    if editorpersistance.prefs.display_all_audio_levels == False:
        editorstate.display_all_audio_levels = False

    editorpersistance.save()

    # Init translations module with translations data.
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Keyboard shortcuts
    shortcuts.update_custom_shortcuts()
    shortcuts.load_shortcut_files()
    shortcuts.load_shortcuts()
    shortcutsquickeffects.load_shortcuts()
    
    # The test for len != 4 is to make sure that if we change the number of values below the prefs are reset to the correct list
    # So when we add or remove a value, make sure we also change the len test
    # Only use positive numbers.
    if( not editorpersistance.prefs.AUTO_SAVE_OPTS or len(editorpersistance.prefs.AUTO_SAVE_OPTS) != 4):
        print("Initializing Auto Save Options")
        editorpersistance.prefs.AUTO_SAVE_OPTS = ((0, _("No Autosave")),(1, _("1 min")),(2, _("2 min")),(5, _("5 min")))

    # We need respaths and translations data available so we need to do init in a function.
    workflow.init_data()

    # Init gtk threads
    Gdk.threads_init()
    Gdk.threads_enter()

    # Handle userfolders init error and quit.
    if userfolders.get_init_error() != None:
        _xdg_error_exit(userfolders.get_init_error())
        return

    # After moving to Python 3 we need at least MLT 6.18.
    if editorstate.mlt_version_is_greater_correct("6.17.99") == False:
        _too_low_mlt_version_exit()
        return

    # Apply custom themes.
    if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME \
        or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_GRAY \
        or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
        success = gui.apply_gtk_css(editorpersistance.prefs.theme)
        if not success:
            print("Applying custom theme failed.")
            editorpersistance.prefs.theme = appconsts.LIGHT_THEME
            editorpersistance.save()

    try:
        if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
            Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
    except:
        print("SETTING DARK THEME PREFERENCE FAILED, SYSTEM DARK THEME NOT AVAILABLE!")

    # Load drag'n'drop images.
    dnd.init()

    # Save screen size data and modify rendering based on screen size/s and number of monitors. 
    scr_w, scr_h = _set_screen_size_data()
    _set_draw_params()

    # Refuse to run on too small screen.
    if scr_w < 1151 or scr_h < 767:
        _too_small_screen_exit()
        return

    # Splash screen
    if editorpersistance.prefs.display_splash_screen == True: 
        show_splash_screen()

    # Init MLT framework
    repo = mlt.Factory().init()
    processutils.prepare_mlt_repo(repo)

    # Set numeric locale to use "." as radix, MLT initializes this to OS locale and this causes bugs.
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Check for codecs and formats on the system.
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)
    
    # Replace some services if better replacements available.
    mltfilters.replace_services(mltenv.services)

    # Create list of available mlt profiles.
    mltprofiles.load_profile_list()

    # If we have crashed we could have large amount of disk space wasted unless we delete all files here.
    tlinerender.app_launch_clean_up()

    # Save assoc file path if found in arguments.
    global assoc_file_path
    assoc_file_path = get_assoc_file_path()
        
    # There is always a project open, so at startup we create a default project.
    # Set default project as the project being edited.
    editorstate.project = projectdata.get_default_project()
    check_crash = True

    # Audiomonitoring being available needs to be known before GUI creation.
    audiomonitoring.init(editorstate.project.profile)

    # Set trim view mode to current default value.
    editorstate.show_trim_view = editorpersistance.prefs.trim_view_default

    # Check for tools and init tools integration.
    gmic.test_availablity()
    containerclip.test_blender_availebility()
    toolsintegration.init()

    # Media Plugins
    mediaplugin.init()

    # Create player object.
    create_player()

    # Create main window and make widgeta available from gui.py.
    create_gui()

    # Inits widgets with project data.
    init_project_gui()

    # Inits widgets with current sequence data.
    init_sequence_gui()

    # Launch player now that data and gui exist.
    launch_player()

    # Editor and modules need some more initializing.
    init_editor_state()

    # Tracks need to be re-centered if window is resized.
    # Connect listener for this now that the tline panel size allocation is sure to be available.
    global window_resize_id, window_state_id
    window_resize_id = gui.editor_window.window.connect("size-allocate", lambda w, e:updater.window_resized())
    window_state_id = gui.editor_window.window.connect("window-state-event", lambda w, e:updater.window_resized())

    # Get existing autosave files
    autosave_files = get_autosave_files()

    # Show splash
    if ((editorpersistance.prefs.display_splash_screen == True) and len(autosave_files) == 0) and not editorstate.runtime_version_greater_then_test_version(editorpersistance.prefs.workflow_dialog_last_version_shown, editorstate.appversion):
        global splash_timeout_id
        splash_timeout_id = GLib.timeout_add(2600, destroy_splash_screen)
        splash_screen.show_all()

    appconsts.SAVEFILE_VERSION = projectdata.SAVEFILE_VERSION # THIS IS A QUESTIONABLE IDEA TO SIMPLIFY IMPORTS, NOT DRY. WHEN DOING TOOLS THAT RUN IN ANOTHER PROCESSES AND SAVE PROJECTS, THIS LINE NEEDS TO BE THERE ALSO.

    # Every running instance has unique autosave file which is deleted at exit
    set_instance_autosave_id()

    # Existance of autosave file hints that program was exited abnormally.
    if check_crash == True and len(autosave_files) > 0:
        if len(autosave_files) == 1:
            GObject.timeout_add(10, autosave_recovery_dialog)
        else:
            GObject.timeout_add(10, autosaves_many_recovery_dialog)
    else:
        tlinerender.init_session()
        start_autosave()

    projectaction.clear_changed_since_last_save_flags()
    
    # We prefer to monkeypatch some callbacks into some modules, usually to
    # maintain a simpler and/or non-circular import structure.
    monkeypatch_callbacks()

    # File in assoc_file_path is opened after very short delay.
    if not(check_crash == True and len(autosave_files) > 0):
        if assoc_file_path != None:
            print("Launch assoc file:", assoc_file_path)
            global assoc_timeout_id
            assoc_timeout_id = GObject.timeout_add(10, open_assoc_file)
        
    # SDL 2 consumer needs to created after Gtk.main() has run enough for window to be visible
    #if editorstate.get_sdl_version() == editorstate.SDL_2: # needs more state consideration still
    #    print "SDL2 timeout launch"
    #    global sdl2_timeout_id
    #    sdl2_timeout_id = GObject.timeout_add(1500, create_sdl_2_consumer)
    
    # In PositionNumericalEntries we are using Gtk.Entry objects in a way that works for us nicely, but is somehow "error" for Gtk, so we just kill this.
    Gtk.Settings.get_default().set_property("gtk-error-bell", False)
    
    # Show first run workflow info dialog if not shown for this version of application.
    if editorstate.runtime_version_greater_then_test_version(editorpersistance.prefs.workflow_dialog_last_version_shown, editorstate.appversion):
        GObject.timeout_add(500, show_worflow_info_dialog)

    # Copy to XDG.
    if userfolders.data_copy_needed():
        GObject.timeout_add(500, show_user_folders_copy_dialog)
    else:
        print("No user folders actions needed.")

    global disk_cache_timeout_id
    disk_cache_timeout_id = GObject.timeout_add(2500, check_disk_cache_size)

    # Launch gtk+ main loop
    Gtk.main()

    Gdk.threads_leave()

# ----------------------------------- callback setting
def monkeypatch_callbacks():

    # We need to do this on app start-up or
    # we'll get circular imports with projectaction->mltplayer->render->projectaction
    render.open_media_file_callback = projectaction.open_rendered_file
    jobs.open_media_file_callback = projectaction.open_rendered_file

    # Set callback for undo/redo ops, batcherrender app does not need this 
    undo.set_post_undo_redo_callback(modesetting.set_post_undo_redo_edit_mode)
    undo.repaint_tline = updater.repaint_tline

    # Drag'n'drop callbacks
    dnd.display_monitor_media_file = updater.set_and_display_monitor_media_file
    dnd.range_log_items_tline_drop = editevent.tline_range_item_drop
    dnd.range_log_items_log_drop = medialog.clips_drop
    dnd.open_dropped_files = projectaction.open_file_names

    # Media log
    medialog.do_multiple_clip_insert_func = editevent.do_multiple_clip_insert

    editevent.display_clip_menu_pop_up = clipmenuaction.display_clip_menu
    editevent.compositor_menu_item_activated = clipmenuaction._compositor_menu_item_activated
    
    # Positionbar in gmic.py does not need trimmodes.py dependency and is avoided
    positionbar.trimmodes_set_no_edit_trim_mode = trimmodes.set_no_edit_trim_mode

    # Snapping is done in a separate module but needs some tlinewidgets state info
    snapping._get_frame_for_x_func = tlinewidgets.get_frame
    snapping._get_x_for_frame_func = tlinewidgets._get_frame_x

    # Callback to reinit to change slider <-> kf editor
    propertyeditorbuilder.re_init_editors_for_slider_type_change_func = clipeffectseditor.refresh_clip

    propertyeditorbuilder.show_rotomask_func = rotomask.show_rotomask
    
    multitrimmode.set_default_mode_func = modesetting.set_default_edit_mode
    
    keyframeeditor._get_current_edited_compositor = compositeeditor.get_compositor

    # Not callbacks but tlinerender needs this data and we do this instead of copypaste.
    tlinerender._get_frame_for_x_func = tlinewidgets.get_frame
    tlinerender._get_x_for_frame_func = tlinewidgets._get_frame_x
    tlinerender._get_last_tline_view_frame_func = tlinewidgets.get_last_tline_view_frame

    guicomponents.select_clip_func = movemodes.select_clip
    #keyframeeditor.add_fade_out_func = compositeeditor._add_fade_out_pressed.
    
    containeractions.set_plugin_to_be_edited_func = mediaplugin.set_plugin_to_be_edited
    
    # These provide clues for possible further refactoring.

# ---------------------------------- SDL2 consumer
#def create_sdl_2_consumer():
#    GObject.source_remove(disk_cache_timeout_id)
#    print "Creating SDL2 consumer..."
#    editorstate.PLAYER().create_sdl2_video_consumer()

# ---------------------------------- program, sequence and project init
def get_assoc_file_path():
    """
    Check if were opening app with file association launch from Gnome
    """
    arg_str = ""
    for arg in sys.argv:
        ext_index = arg.find(".flb")
        if ext_index != -1:
            arg_str = arg
    
    if len(arg_str) == 0:
        return None
    else:
        return arg_str

def open_assoc_file():
    GLib.source_remove(assoc_timeout_id)
    projectaction.actually_load_project(assoc_file_path, block_recent_files=False)

def set_quiet_if_requested():
    for arg in sys.argv:
        if arg == "--quiet":
            global _log_file
            _log_file = "/dev/null"
            log_print_output_to_file()
            
def create_gui():
    """
    Called at app start to create gui objects and handles for them.
    """
    tlinewidgets.load_icons_and_set_colors()
    kftoolmode.load_icons()

    updater.set_clip_edit_mode_callback = modesetting.set_clip_monitor_edit_mode
    updater.load_icons()

    # Make layout data available
    editorlayout.init_layout_data()

    # Create window and all child components
    editor_window = editorwindow.EditorWindow()
    
    # Make references to various gui components available via gui module
    gui.capture_references(editor_window)

    # Unused frames take 3 pixels so hide those.
    editorlayout.set_positions_frames_visibility()
        
    # All widgets are now realized and references captured so can find out theme colors
    gui.set_theme_colors()
    tlinewidgets.set_dark_bg_color()
    gui.pos_bar.set_dark_bg_color()
    
    # Connect window global key listener
    gui.editor_window.window.connect("key-press-event", keyevents.key_down)
    if editorpersistance.prefs.global_layout != appconsts.SINGLE_WINDOW:
        gui.editor_window.window2.connect("key-press-event", keyevents.key_down)

    # Give undo a reference to uimanager for menuitem state changes
    undo.set_menu_items(gui.editor_window.uimanager)
    
    updater.display_sequence_in_monitor()

def create_player():
    """
    Creates mlt player object
    """
    # Create player and make available from editorstate module.
    editorstate.player = mltplayer.Player(editorstate.project.profile)
    editorstate.player.set_tracktor_producer(editorstate.current_sequence().tractor)

def launch_player():
    # Create SDL output consumer
    editorstate.player.set_sdl_xwindow(gui.tline_display)
    editorstate.player.create_sdl_consumer()

    # Display current sequence tractor
    updater.display_sequence_in_monitor()
    
    # Connect buttons to player methods
    gui.editor_window.connect_player(editorstate.player)
    
    # Start player.
    editorstate.player.connect_and_start()

def init_project_gui():
    """
    Called after project load to initialize interface
    """
    # Display media files in "Media" tab 
    gui.media_list_view.fill_data_model()
    try: # Fails if current bin is empty
        selection = gui.media_list_view.treeview.get_selection()
        selection.select_path("0")
    except Exception:
        pass

    # Display bins in "Media" tab 
    gui.bin_list_view.fill_data_model()
    selection = gui.bin_list_view.treeview.get_selection()
    selection.select_path("0")
    gui.editor_window.bin_info.display_bin_info()

    # Display sequences in "Project" tab
    gui.sequence_list_view.fill_data_model()
    selection = gui.sequence_list_view.treeview.get_selection()
    selected_index = editorstate.project.sequences.index(editorstate.current_sequence())
    selection.select_path(str(selected_index))
  
    # Display logged ranges in "Range Log" tab
    medialog.update_group_select_for_load()
    medialog.update_media_log_view()

    render.set_default_values_for_widgets(True)
    gui.tline_left_corner.update_gui()
    projectinfogui.update_project_info()

    titler.reset_titler()
    
    # Set render folder selector to last render if prefs require 
    folder_path = editorstate.PROJECT().get_last_render_folder()
    if folder_path != None and editorpersistance.prefs.remember_last_render_dir == True:
        gui.render_out_folder.set_current_folder(folder_path)

def init_sequence_gui():
    """
    Called after project load or changing current sequence 
    to initialize interface.
    """
    # Set correct compositing mode menu item selected
    gui.editor_window.init_compositing_mode_menu()
    gui.editor_window.init_timeline_rendering_menu()
    gui.editor_window.tline_render_mode_launcher.set_pixbuf(editorstate.tline_render_mode) 
    gui.comp_mode_launcher.set_pixbuf(editorstate.get_compositing_mode())

    # Set initial timeline scale draw params
    editorstate.current_sequence().update_length()
    
    # Handle timeline rendering GUI and data
    tlinerender.init_for_sequence()
    gui.editor_window.hide_tline_render_strip()
    if editorstate.get_tline_rendering_mode() != appconsts.TLINE_RENDERING_OFF: 
        gui.editor_window.show_tline_render_strip()
        
    updater.update_pix_per_frame_full_view()
    updater.init_tline_scale()
    updater.repaint_tline()

def init_editor_state():
    """
    Called after project load or changing current sequence 
    to initialize editor state.
    """
    render.fill_out_profile_widgets()

    gui.media_view_filter_selector.set_pixbuf(editorstate.media_view_filter)

    gui.editor_window.window.set_title(editorstate.project.name + " - Flowblade")
    gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(False)
    gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Undo").set_sensitive(False)
    gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Redo").set_sensitive(False)

    # Center tracks vertical display and init some listeners to
    # new value and repaint tracks column.
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.get_allocation())
    gui.tline_column.init_listeners()
    gui.tline_column.widget.queue_draw()

    # Clear editors 
    clipeffectseditor.clear_clip()
    compositeeditor.clear_compositor()

    # Show first pages on notebooks
    gui.editor_window.notebook.set_current_page(0)

    # Clear clip selection.
    movemodes.clear_selection_values()

    # Set initial edit mode
    modesetting.set_default_edit_mode()
    
    # Create array needed to update compositors after all edits
    editorstate.current_sequence().restack_compositors()

    proxyediting.set_menu_to_proxy_state()

    undo.clear_undos()

    # Enable edit action GUI updates
    edit.do_gui_update = True

def new_project(profile_index, v_tracks, a_tracks):
    sequence.VIDEO_TRACKS_COUNT = v_tracks
    sequence.AUDIO_TRACKS_COUNT = a_tracks
    profile = mltprofiles.get_profile_for_index(profile_index)
    new_project = projectdata.Project(profile)
    open_project(new_project)

def open_project(new_project):
    stop_autosave()
    gui.editor_window.window.handler_block(window_resize_id)
    gui.editor_window.window.handler_block(window_state_id)

    audiomonitoring.close_audio_monitor()
    audiowaveformrenderer.clear_cache()
    audiowaveform.frames_cache = {}

    editorstate.project = new_project
    editorstate.media_view_filter = appconsts.SHOW_ALL_FILES
    editorstate.tline_render_mode = appconsts.TLINE_RENDERING_OFF
    
    # Inits widgets with project data
    init_project_gui()
    
    # Inits widgets with current sequence data
    init_sequence_gui()

    # Set and display current sequence tractor
    display_current_sequence()
    
    # Editor and modules need some more initializing
    init_editor_state()
    
    # For save time message on close
    projectaction.save_time = None
    
    # Delete autosave file after it has been loaded
    global loaded_autosave_file
    if loaded_autosave_file != None:
        print("Deleting", loaded_autosave_file)
        os.remove(loaded_autosave_file)
        loaded_autosave_file = None

    editorstate.update_current_proxy_paths()
    editorstate.fade_length = -1
    editorstate.transition_length = -1
    editorstate.clear_trim_clip_cache()
    audiomonitoring.init_for_project_load()

    tlinerender.init_session()
    start_autosave()

    if new_project.update_media_lengths_on_load == True:
        projectaction.update_media_lengths()

    gui.editor_window.set_default_edit_tool()
    editorstate.trim_mode_ripple = False

    updater.set_timeline_height()

    gui.editor_window.window.handler_unblock(window_resize_id)
    gui.editor_window.window.handler_unblock(window_state_id)

    global resize_timeout_id
    resize_timeout_id = GLib.timeout_add(500, _do_window_resized_update)

    projectaction.clear_changed_since_last_save_flags()

    # Set scrubbing
    editorstate.player.set_scrubbing(editorpersistance.prefs.audio_scrubbing)
    
def _do_window_resized_update():
    GLib.source_remove(resize_timeout_id)
    updater.window_resized()
    
def change_current_sequence(index):
    edit.do_gui_update = False  # This should not be necessary but we are doing this signal intention that GUI updates are disabled
    
    stop_autosave()
    editorstate.project.c_seq = editorstate.project.sequences[index]

    editorstate.tline_render_mode = appconsts.TLINE_RENDERING_OFF

    # Inits widgets with current sequence data
    init_sequence_gui()
    
    # update resync data
    resync.sequence_changed(editorstate.project.c_seq)

    # Set and display current sequence tractor
    display_current_sequence()
    
    # Editor and modules needs to do some initializing
    init_editor_state()

    # Display current sequence selected in gui.
    gui.sequence_list_view.fill_data_model()
    selection = gui.sequence_list_view.treeview.get_selection()
    selected_index = editorstate.project.sequences.index(editorstate.current_sequence())
    selection.select_path(str(selected_index))

    audiomonitoring.recreate_master_meter_filter_for_new_sequence()
    
    start_autosave()

    updater.set_timeline_height()

def display_current_sequence():
    # Get shorter alias.
    player = editorstate.player

    player.consumer.stop()
    player.init_for_profile(editorstate.project.profile)
    player.create_sdl_consumer()
    player.set_tracktor_producer(editorstate.current_sequence().tractor)
    player.connect_and_start()
    updater.display_sequence_in_monitor()
    player.seek_frame(0)
    updater.repaint_tline()

# ------------------------------------------------- autosave
def autosave_recovery_dialog():
    dialogs.autosave_recovery_dialog(autosave_dialog_callback, gui.editor_window.window)
    return False

def autosave_dialog_callback(dialog, response):
    dialog.destroy()
    autosave_file = userfolders.get_cache_dir() + AUTOSAVE_DIR + get_autosave_files()[0]
    if response == Gtk.ResponseType.OK:
        global loaded_autosave_file
        loaded_autosave_file = autosave_file
        projectaction.actually_load_project(autosave_file, True, False, True)
    else:
        tlinerender.init_session()  # didn't do this in main and not going to do app-open_project
        os.remove(autosave_file)
        start_autosave()

def autosaves_many_recovery_dialog():
    autosaves_file_names = get_autosave_files()
    now = time.time()
    autosaves = []
    for a_file_name in autosaves_file_names:
        autosave_path = userfolders.get_cache_dir() + AUTOSAVE_DIR + a_file_name
        autosave_object = utils.EmptyClass()
        autosave_object.age = now - os.stat(autosave_path).st_mtime
        autosave_object.path = autosave_path
        autosaves.append(autosave_object)
    autosaves = sorted(autosaves, key=lambda autosave_object: autosave_object.age)

    dialogs.autosaves_many_recovery_dialog(autosaves_many_dialog_callback, autosaves, gui.editor_window.window)
    return False

def autosaves_many_dialog_callback(dialog, response, autosaves_view, autosaves):
    if response == Gtk.ResponseType.OK:
        autosave_file = autosaves[autosaves_view.get_selected_indexes_list()[0]].path # Single selection, 1 quaranteed to exist
        print("autosave_file", autosave_file)
        global loaded_autosave_file
        loaded_autosave_file = autosave_file
        dialog.destroy()
        projectaction.actually_load_project(autosave_file, True, False, True)
    else:
        dialog.destroy()
        tlinerender.init_session()
        start_autosave()

def set_instance_autosave_id():
    global instance_autosave_id_str
    instance_autosave_id_str = "_" + hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    
def get_instance_autosave_file():
    return AUTOSAVE_FILE + instance_autosave_id_str

def start_autosave():
    global autosave_timeout_id

    # Aug-2019 - SvdB - AS - Made changes to use the value stored in prefs, with Default=1 minute, rather than hardcoding
    try:
        time_min, desc = editorpersistance.prefs.AUTO_SAVE_OPTS[editorpersistance.prefs.auto_save_delay_value_index]
    except:
        time_min = 1

    autosave_delay_millis = time_min * 60 * 1000

    # Aug-2019 - SvdB - AS - put in code to stop or not start autosave depending on user selection
    if autosave_delay_millis > 0:
        print("Autosave started...")
        autosave_timeout_id = GObject.timeout_add(autosave_delay_millis, do_autosave)
        autosave_file = userfolders.get_cache_dir() + get_instance_autosave_file()
        persistance.save_project(editorstate.PROJECT(), autosave_file)
    else:
        print("Autosave disabled...")
        stop_autosave()

def get_autosave_files():
    autosave_dir = userfolders.get_cache_dir() + AUTOSAVE_DIR
    return os.listdir(autosave_dir)

def stop_autosave():
    global autosave_timeout_id
    if autosave_timeout_id == -1:
        return
    GLib.source_remove(autosave_timeout_id)
    autosave_timeout_id = -1

def do_autosave():
    autosave_file = userfolders.get_cache_dir() + get_instance_autosave_file()
    persistance.save_project(editorstate.PROJECT(), autosave_file)
    return True

# ------------------------------------------------- splash screen
def show_splash_screen():
    global splash_screen
    splash_screen = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    splash_screen.set_border_width(0)
    splash_screen.set_decorated(False)
    splash_screen.set_position(Gtk.WindowPosition.CENTER)
    img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "flowblade_splash_black_small.png")

    splash_screen.add(img)
    splash_screen.set_keep_above(True)
    splash_screen.set_size_request(498, 320) # Splash screen is working funny since Ubuntu 13.10

    splash_screen.set_resizable(False)

    while(Gtk.events_pending()):
        Gtk.main_iteration()

def destroy_splash_screen():
    splash_screen.destroy()
    GLib.source_remove(splash_timeout_id)

def show_worflow_info_dialog():
    editorpersistance.prefs.workflow_dialog_last_version_shown = editorstate.appversion
    editorpersistance.save()
    
    worflow_info_dialog = workflow.WorkflowDialog(open_project)
    return False

# ------------------------------------------------------- disk cache size check
def check_disk_cache_size():
    GLib.source_remove(disk_cache_timeout_id)
    diskcachemanagement.check_disk_cache_size()
    
# ------------------------------------------------------- userfolders dialogs
def show_user_folders_init_error_dialog(error_msg):
    # not done
    print(error_msg, " user folder XDG init error")
    return False

def show_user_folders_copy_dialog():
    dialog = dialogs.xdg_copy_dialog()
    copy_thread = userfolders.XDGCopyThread(dialog, _xdg_copy_completed_callback)
    copy_thread.start()
    return False

def _xdg_copy_completed_callback(dialog):
    Gdk.threads_enter()
    dialog.destroy()
    Gdk.threads_leave()

# ------------------------------------------------------- small and multiple screens
# We need a bit more stuff because having multiple monitors can mix up setting draw parameters.
def _set_screen_size_data():
    monitor_data = utils.get_display_monitors_size_data()
    monitor_data_index = editorpersistance.prefs.layout_display_index

    display = Gdk.Display.get_default()
    num_monitors = display.get_n_monitors() # Get number of monitors.

    if monitor_data_index == 0:
        scr_w = Gdk.Screen.width()
        scr_h = Gdk.Screen.height()
        print("Using Full Screen size for layout:", scr_w, "x", scr_h)
    elif monitor_data_index > len(monitor_data) - 1:
        print("Specified layout monitor not present.")
        scr_w = Gdk.Screen.width()
        scr_h = Gdk.Screen.height()
        print("Using Full Screen size for layout:", scr_w, "x", scr_h)
        editorpersistance.prefs.layout_display_index = 0
    else:

        scr_w, scr_h = monitor_data[monitor_data_index]
        if scr_w < 1151 or scr_h < 767:
            print("Selected layout monitor too small.")
            scr_w = Gdk.Screen.width()
            scr_h = Gdk.Screen.height()
            print("Using Full Screen size for layout:", scr_w, "x", scr_h)
            editorpersistance.prefs.layout_display_index = 0
        else:
            # Selected monitor data is available and monitor is usable as layout monitor.
            print("Using monitor " + str(monitor_data_index) + " for layout: " + str(scr_w) + " x " + str(scr_h))
    
    editorstate.SCREEN_WIDTH = scr_w
    editorstate.SCREEN_HEIGHT = scr_h
    
    print("Small height:", editorstate.screen_size_small_height())
    print("Small width:",  editorstate.screen_size_small_width())

    return (scr_w, scr_h)

# Adjust gui parameters for smaller screens.
def _set_draw_params():    

    if editorstate.screen_size_large_height() == True:
        keyframeeditcanvas.GEOMETRY_EDITOR_HEIGHT = 300

    if editorpersistance.prefs.double_track_hights == True:
        appconsts.TRACK_HEIGHT_HIGH = 150
        appconsts.TRACK_HEIGHT_NORMAL = 100 # track height in canvas and column
        appconsts.TRACK_HEIGHT_SMALL = 50 # track height in canvas and column
        appconsts.TLINE_HEIGHT = 520
        sequence.TRACK_HEIGHT_NORMAL = appconsts.TRACK_HEIGHT_NORMAL # track height in canvas and column
        sequence.TRACK_HEIGHT_SMALL = appconsts.TRACK_HEIGHT_SMALL # track height in canvas and column
        sequence.TRACK_HEIGHT_HIGH = appconsts.TRACK_HEIGHT_HIGH
        tlinewidgets.set_tracks_double_height_consts()

def _too_small_screen_exit():
    global exit_timeout_id
    exit_timeout_id = GObject.timeout_add(200, _show_too_small_info)
    # Launch gtk+ main loop
    Gtk.main()

def _show_too_small_info():
    GLib.source_remove(exit_timeout_id)
    primary_txt = _("Too small screen for this application.")
    scr_w = Gdk.Screen.width()
    scr_h = Gdk.Screen.height()
    secondary_txt = _("Minimum screen dimensions for this application are 1152 x 768.\n") + \
                    _("Your screen dimensions are ") + str(scr_w) + " x " + str(scr_h) + "."
    dialogutils.warning_message_with_callback(primary_txt, secondary_txt, None, False, _early_exit)

def _xdg_error_exit(error_str):
    global exit_timeout_id
    exit_timeout_id = GObject.timeout_add(200, _show_xdg_error_info, error_str)
    # Launch gtk+ main loop
    Gtk.main()

def _show_xdg_error_info(error_str):
    GLib.source_remove(exit_timeout_id)
    primary_txt = _("Cannot launch application because XDG folders init error.")
    secondary_txt = error_str + "."
    dialogutils.warning_message_with_callback(primary_txt, secondary_txt, None, False, _early_exit)

def _too_low_mlt_version_exit():
    global exit_timeout_id
    exit_timeout_id = GObject.timeout_add(200, _show_mlt_version_exit_info)
    # Launch gtk+ main loop
    Gtk.main()

def _show_mlt_version_exit_info():
    primary_txt = _("Flowblade version 2.6 (or later) requires MLT version 6.18 to run")
    secondary_txt = _("Your MLT version is: ") + editorstate.mlt_version + ".\n\n" + _("Install MLT 6.18 or higher to run Flowblade.")
    dialogutils.warning_message_with_callback(primary_txt, secondary_txt, None, False, _early_exit)

def _early_exit(dialog, response):
    dialog.destroy()
    # Exit gtk main loop.
    Gtk.main_quit() 

# ------------------------------------------------------- logging
def log_print_output_to_file():
    so = se = open(_log_file, 'w', buffering=1)

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

# ------------------------------------------------------ shutdown
def shutdown():
    if projectaction.was_edited_since_last_save() == False:
        _shutdown_dialog_callback(None, None, True)
        return True
    else:
        dialogs.exit_confirm_dialog(_shutdown_dialog_callback, get_save_time_msg(), gui.editor_window.window, editorstate.PROJECT().name)
        return True # Signal that event is handled, otherwise it'll destroy window anyway

def get_save_time_msg():
    return projectaction.get_save_time_msg()

def _shutdown_dialog_callback(dialog, response_id, no_dialog_shutdown=False):
    if no_dialog_shutdown == False:
        dialog.destroy()
        if response_id == Gtk.ResponseType.CLOSE:# "Don't Save"
            pass
        elif response_id ==  Gtk.ResponseType.YES:# "Save"
            if editorstate.PROJECT().last_save_path != None:
                persistance.save_project(editorstate.PROJECT(), editorstate.PROJECT().last_save_path)
            else:
                dialogutils.warning_message(_("Project has not been saved previously"), 
                                        _("Save project with File -> Save As before closing."),
                                        gui.editor_window.window)
                return
        else: # "Cancel"
            return
    else:
        print("Nothing changed since last save.")

    # --- APP SHUT DOWN --- #
    print("Exiting app...")
    # Sep-2018 - SvdB - Stop wave form threads
    for thread_termination in threading.enumerate():
        # We only terminate threads with a 'process', as these are launched
        # by the audiowaveformrenderer
        try:
            thread_termination.process.terminate()
        except:
            None

    # No more auto saving
    stop_autosave()

    tlinerender.delete_session()

    clipeffectseditor.shutdown_polling()
    compositeeditor.shutdown_polling()

    
    # Save window dimensions on exit
    alloc = gui.editor_window.window.get_allocation()
    x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height 
    editorpersistance.prefs.exit_allocation = (w, h)
    if gui.editor_window.window2 != None:
        alloc = gui.editor_window.window2.get_allocation()
        pos_x, pos_y = gui.editor_window.window2.get_position()
        editorpersistance.prefs.exit_allocation_window_2 = (alloc.width, alloc.height, pos_x, pos_y)       
    editorpersistance.prefs.app_v_paned_position = gui.editor_window.app_v_paned.get_position()
    editorpersistance.prefs.top_paned_position = gui.editor_window.top_paned.get_position()
    try: # This fails if preference for top row layout changed, we just ignore saving these values then.
        if editorlayout.top_level_project_panel() == True:
            editorpersistance.prefs.mm_paned_position = 200  # This is not used until user sets preference to not have top level project panel
        else:
            editorpersistance.prefs.mm_paned_position = gui.editor_window.mm_paned.get_position()
    except: 
        pass
    editorpersistance.save()

    # Block reconnecting consumer before setting window not visible
    updater.player_refresh_enabled = False
    gui.editor_window.window.set_visible(False)
    if gui.editor_window.window2 != None:
        gui.editor_window.window2.set_visible(False)

    # Close and destroy app when gtk finds time to do it after hiding window
    GLib.idle_add(_app_destroy)

def _app_destroy():
    # Close threads and stop mlt consumers
    editorstate.player.shutdown() # has ticker thread and player threads running
    audiomonitoring.close()
    # Wait threads to stop
    while((editorstate.player.ticker.exited == False) and
         (audiomonitoring._update_ticker.exited == False) and
         (audiowaveform.waveform_thread != None)):
        pass
    # Delete autosave file
    try:
        os.remove(userfolders.get_cache_dir() + get_instance_autosave_file())
    except:
        print("Delete autosave file FAILED!")

    do_gtk_main_quit = jobs.handle_shutdown(get_instance_autosave_file())
    
    # Exit gtk main loop if no jobs unfinished.
    if do_gtk_main_quit == True:
        Gtk.main_quit()
    else:
        # Jobs launches its own top level window to show progress on unfinished jobs renders
        # and does Gtk.main_quit() later when done.
        pass
