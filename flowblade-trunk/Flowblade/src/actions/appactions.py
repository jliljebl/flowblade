"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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

from gi.repository import Gtk, Gio, GLib

import copy

import appconsts
import audiomonitoring
import batchrendering
import callbackbridge
import containerclip
import copypaste
import editorlayout
import editorpersistance
import editorstate
from editorstate import APP
import exporting
import gmic
import gui
import keygtkactions
import shortcuts
import medialinker
import medialog
import mediaplugin
import menuactions
import monitorevent
import middlebar
import patternproducer
import preferenceswindow
import projectaction
import projectaddmediafolder
import projectdatavaultgui
import proxytranscodemanager
import scripttool
import shortcutsdialog
import singletracktransition
import tlineaction
import titler
import undo
import updater
import workflow


_tline_widgets = None 
_tline_actions = None


def create_actions():
    root = shortcuts.get_root()

    _create_action("new", lambda w, a:projectaction.new_project(), shortcuts.get_shortcut_kb_str(root, "new_project", True))
    _create_action("open", lambda w, a:projectaction.load_project(), shortcuts.get_shortcut_kb_str(root, "open_project", True))
    _create_action("save", lambda w, a:projectaction.save_project(), shortcuts.get_shortcut_kb_str(root, "save_project", True))
    _create_action("saveas", lambda w, a:projectaction.save_project_as())
    _create_action("exportxml", lambda w, a:exporting.MELT_XML_export())
    _create_action("exportedl", lambda w, a:exporting.EDL_export())
    _create_action("exportcurrentframe", lambda w, a:exporting.screenshot_export())
    _create_action("exportardour", lambda w, a:exporting.ardour_export())
    _create_action("close", lambda w, a:projectaction.close_project())
    _create_action("quit", lambda w, a:callbackbridge.app_shutdown(), shortcuts.get_shortcut_kb_str(root, "quit", True))

    _create_action("undoaction", lambda w, a: undo.do_undo_and_repaint(), shortcuts.get_shortcut_kb_str(root, "undo", True))
    _create_action("redoaction", lambda w, a: undo.do_redo_and_repaint(), shortcuts.get_shortcut_kb_str(root, "redo", True))
    _create_action("cutaction", lambda w, a: copypaste.cut_action(), shortcuts.get_shortcut_kb_str(root, "cutaction", True))
    _create_action("copyaction", lambda w, a: copypaste.copy_action(), shortcuts.get_shortcut_kb_str(root, "copyaction", True))
    _create_action("pasteaction", lambda w, a: copypaste.paste_action(), shortcuts.get_shortcut_kb_str(root, "pasteaction", True))
    _create_action("pastefiltersaction", lambda w, a: tlineaction.do_timeline_filters_paste(), shortcuts.get_shortcut_kb_str(root, "pastefiltersaction", True))
    _create_action("appendfrommonitor", lambda w, a: tlineaction.append_button_pressed(), shortcuts.get_shortcut_kb_str(root, "append", True))
    _create_action("insertfrommonitor", lambda w, a: tlineaction.insert_button_pressed(), shortcuts.get_shortcut_kb_str(root, "insert", True))
    _create_action("threepointoverwrite", lambda w, a: tlineaction.three_point_overwrite_pressed(), shortcuts.get_shortcut_kb_str(root, "3_point_overwrite", True))  
    _create_action("rangeoverwrite", lambda w, a: tlineaction.range_overwrite_pressed(), shortcuts.get_shortcut_kb_str(root, "overwrite_range", True)) 
    _create_action("cutatplayhead", lambda w, a: tlineaction.cut_pressed(), shortcuts.get_shortcut_kb_str(root, "cut", True))
    _create_action("liftaction", lambda w, a: tlineaction.lift_button_pressed(), shortcuts.get_shortcut_kb_str(root, "lift", True))
    _create_action("spliceaction", lambda w, a: tlineaction.splice_out_button_pressed())
    _create_action("resynctrack", lambda w, a: tlineaction.resync_button_pressed(), shortcuts.get_shortcut_kb_str(root, "resync", True))
    _create_action("syncallcompositors", lambda w, a: tlineaction.sync_all_compositors(), shortcuts.get_shortcut_kb_str(root, "sync_all", True))
    _create_action("allfiltersoff", lambda w, a: tlineaction.all_filters_off())
    _create_action("allfilterson", lambda w, a: tlineaction.all_filters_on())
    _create_action("clearfilters", lambda w, a: clipmenuaction.clear_filters(), shortcuts.get_shortcut_kb_str(root, "clear_filters", True)) 
    _create_action("addtransition", lambda w, a: singletracktransition.add_transition_menu_item_selected(), shortcuts.get_shortcut_kb_str(root, "add_dissolve", True)) 
    _create_action("showdatastore", lambda w, a: projectdatavaultgui.show_project_data_manager_window())
    _create_action("showprofilesmanager", lambda w, a: menuactions.profiles_manager())
    _create_action("showkeyboardshortcuts", lambda w, a: shortcutsdialog.keyboard_shortcuts_dialog(gui.editor_window.window, workflow.get_tline_tool_working_set, menuactions.keyboard_shortcuts_callback, menuactions.change_single_shortcut, menuactions.keyboard_shortcuts_menu_item_selected_callback))
    _create_action("showpreferences", lambda w, a: preferenceswindow.preferences_dialog())


    _create_action("fullscreen", lambda w, a: menuactions.toggle_fullscreen(), "F11")
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:    
        default_value = "singlewindow"
    else:
        default_value = "twowindows"
    _create_stateful_action("windowmode", "s", default_value, lambda a, v: gui.editor_window.change_windows_preference(a, v))
    _create_action("showmiddlebarconfig", lambda w, a: middlebar.show_middlebar_conf_dialog())
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
        default_value = "middlebar"
    else:
        default_value = "dock"
    _create_stateful_action("tooldockpos", "s", default_value, lambda a, v: gui.editor_window.show_tools_dock_change_from_menu(a, v))
    if editorpersistance.prefs.audio_master_position_is_top_row == True:
        default_value = "toprow"
    else:
        default_value = "bottomrow"
    _create_stateful_action("audiomasterposition", "s", default_value, lambda a, v: gui.editor_window.set_audiomaster_position(a, v))
    default_value = editorpersistance.prefs.default_playback_interpolation
    _create_stateful_action("playback.interpolation", "s", default_value, lambda a, v: monitorevent.playback_menu_item_activated(a, v))
    _create_action("zoomin", lambda w, a: updater.zoom_in(), shortcuts.get_shortcut_kb_str(root, "zoom_in", True))
    _create_action("zoomout", lambda w, a: updater.zoom_out(), shortcuts.get_shortcut_kb_str(root, "zoom_out", True))
    _create_action("zoomfit", lambda w, a: updater.zoom_project_length())

    _create_action("addmedia", lambda w, a:  projectaction.add_media_files(), shortcuts.get_shortcut_kb_str(root, "add_media", True))
    _create_action("addimgseq", lambda w, a: projectaction.add_image_sequence())
    _create_action("addgenerator", lambda w, a: mediaplugin.show_add_media_plugin_window())
    _create_action("addtitle", lambda w, a:  titler.show_titler())
    _create_action("addcolorclip", lambda w, a: patternproducer.create_color_clip())
    _create_action("fromselected", lambda w, a: projectaction.create_selection_compound_clip())
    _create_action("frombox", lambda w, a: projectaction.create_box_compound_clip())
    _create_action("fromtimeline", lambda w, a: projectaction.create_range_compound_clip())
    _create_action("fromcurrentsequence", lambda w, a: projectaction.create_sequence_compound_clip())
    _create_action("fromgmic", lambda w, a: containerclip.create_gmic_media_item())
    _create_action("addsequencelink", lambda w, a: projectaction.create_sequence_link_container())
    _create_action("addfromfolder", lambda w, a: projectaddmediafolder.show_add_media_folder_dialog())
    _create_action("importfromproject", lambda w, a: projectaction.import_project_media())
    _create_action("loadgeneratorscript", lambda w, a: containerclip.create_fluxity_media_item())
    _create_action("addbinmainmenu", lambda w, a: projectaction.add_new_bin())
    _create_action("deletebinmainmenu", lambda w, a: projectaction.delete_selected_bin())
    _create_action("logcliprange", lambda w, a: medialog.log_range_clicked(), shortcuts.get_shortcut_kb_str(root, "log_range", True))  
    _create_action("recreateicons", lambda w, a: menuactions.recreate_media_file_icons())
    _create_action("removeunusedmedia", lambda w, a: projectaction.remove_unused_media())
    _create_action("changeprofile", lambda w, a: projectaction.change_project_profile())
    _create_action("projectinfoanddata", lambda w, a: projectaction.show_project_info())
    _create_action("proxymanager", lambda w, a: proxytranscodemanager.show_proxy_manager_dialog())
    _create_action("transcodemanager", lambda w, a: proxytranscodemanager.show_transcode_manager_dialog())

    _create_action("addnewsequence", lambda w, a: projectaction.add_new_sequence())  
    _create_action("editselectedsequence", lambda w, a: projectaction.change_edit_sequence())  
    _create_action("deleteselectedsequence", lambda w, a: projectaction.delete_selected_sequence())  
    _create_action("importsequence", lambda w, a: projectaction.combine_sequences())  
    _create_action("splitsequence", lambda w, a: tlineaction.sequence_split_pressed())  
    _create_action("duplicatesequence", lambda w, a: projectaction.duplicate_sequence())  
    _create_action("addvideotrack", lambda w, a: projectaction.add_video_track())  
    _create_action("addaudiotrack", lambda w, a: projectaction.add_audio_track())  
    _create_action("deletevideotrack", lambda w, a: projectaction.delete_video_track())  
    _create_action("deleteaudiotrack", lambda w, a: projectaction.delete_audio_track())  
    _create_action("changesequencetrackcount", lambda w, a: projectaction.change_sequence_track_count())  
    _create_action("addwatermark", lambda w, a: menuactions.edit_watermark())  
    _create_stateful_action("compositing.compmode", "s", "fulltrackauto", lambda a, v: projectaction.change_current_sequence_compositing_mode_from_corner_menu(a, v))

    _create_action("showtitler", lambda w, a: titler.show_titler())  
    _create_action("showaudiomixer", lambda w, a: audiomonitoring.show_audio_monitor())  
    _create_action("showgmic", lambda w, a: gmic.launch_gmic())  
    _create_action("showgeneratoreditor", lambda w, a: scripttool.launch_scripttool())  
    _create_action("showrelinker", lambda w, a: medialinker.display_linker())  

    _create_action("addtobatch", lambda w, a: projectaction.add_to_render_queue())
    _create_action("showbatch", lambda w, a: batchrendering.launch_batch_rendering())
    _create_action("rerendertransitions", lambda w, a: singletracktransition.rerender_all_rendered_transitions())
    _create_action("rendertimeline", lambda w, a: projectaction.do_rendering())

    _create_action("contents", lambda w, a:menuactions.quick_reference(), shortcuts.get_shortcut_kb_str(root, "help", True))
    _create_action("contentsweb", lambda w, a:menuactions.quick_reference_web())
    _create_action("runtime", lambda w, a:menuactions.environment())
    _create_action("about", lambda w, a:menuactions.about())

    _create_action("appendselected", lambda w, a: projectaction.append_selected_media_clips_into_timeline(), shortcuts.get_shortcut_kb_str(root, "append_from_bin", True)) # in a context menu 
    
    # Create data for timeline actions enbled/disabled handling.
    global _tline_widgets, _tline_actions
    _tline_widgets = keygtkactions.get_widgets_list(keygtkactions.TLINE_MONITOR_ALL)
    _tline_action_ids = ["cutatplayhead", "liftaction", "resynctrack", "syncallcompositors", \
                         "appendfrommonitor", "insertfrommonitor", "threepointoverwrite", \
                         "rangeoverwrite", "clearfilters", "addtransition", "zoomin", "zoomout"]
    _tline_actions = _get_actions(_tline_action_ids)

    # Connect all widgets in main window to send info on focus changes.
    all_widgets = get_all_widgets(gui.editor_window.window)
    for w in all_widgets:
        _connect_for_focus_notifications(w)
 
def _create_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    APP().add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])

def _create_win_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    gui.editor_window.window.add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])
    action.set_enabled(True)

def _create_stateful_action(name, typestr, default_value, callback):
    action = Gio.SimpleAction.new_stateful( name,
                                            GLib.VariantType.new(typestr),
                                            GLib.Variant(typestr, default_value))

    action.connect("change-state", callback)
    APP().add_action(action)

# -------------------------------------------- per project stateful action updates
def set_per_project_stateful_action_variants():
    action = APP().lookup_action("playback.interpolation")
    playback_value = GLib.Variant.new_string(editorstate.PROJECT().get_project_property(appconsts.P_PROP_PLAYBACK_INTERPOLATION))
    monitorevent.playback_menu_item_activated(action, playback_value)

    
# --------------------------------------------- View menu updates
def update_compositing_mode_action_state():
    action = APP().lookup_action("compositing.compmode")
    
    if editorstate.editorstate.get_compositing_mode() == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:  
        new_variant = GLib.Variant.new_string("fulltrackauto")
    else:
        new_variant = GLib.Variant.new_string("topdown")

    action.set_state(new_variant)

def enable_save():
    action = APP().lookup_action("save")
    action.set_enabled(True)

def set_save_action_sensitive(sensitive):
    action = APP().lookup_action("save")
    action.set_enabled(sensitive)

def set_undo_sensitive(sensitive):
    action = APP().lookup_action("undoaction")
    action.set_enabled(sensitive)
    
def set_redo_sensitive(sensitive):
    action = APP().lookup_action("redoaction")
    action.set_enabled(sensitive)

# ---------------------------------- action focus handling
def get_all_widgets(container):
    widgets = []
    if isinstance(container, Gtk.Container):
        for child in container.get_children():
            widgets.append(child)
            widgets.extend(get_all_widgets(child))
            
    return widgets

def _connect_for_focus_notifications(widget):
    widget.connect("notify::has-focus", _handle_state_change)

def _get_actions(action_ids):
    action_list = []
    for aid in action_ids:
        action_list.append(APP().lookup_action(aid))
    return action_list

def _handle_state_change(w, param_spec):
    widget = gui.editor_window.window.get_focus()
    if widget in _tline_widgets:
        _set_tline_actions_enabled(True)
        if editorstate.current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE:
            _set_action_enabled("syncallcompositors", False)
    else:
        #print("NON tlinewidget has focus")
        _set_tline_actions_enabled(False)

def _set_tline_actions_enabled(enabled):
    for action in _tline_actions:
        action.set_enabled(enabled)
  
def _set_action_enabled(action_id, enabled):
    action = APP().lookup_action(action_id)
    action.set_enabled(enabled)
