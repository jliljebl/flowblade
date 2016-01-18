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

from gi.repository import GObject, GLib
from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GdkX11
from gi.repository import Pango

import cairo
import locale
import mlt
import numpy as np
import os
import re
import shutil
import subprocess
import sys
import time

import appconsts
import cairoarea
import dialogutils
import editorstate
import editorpersistance
import gui
import guicomponents
import guiutils
import glassbuttons
import mlt
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import positionbar
import render
import respaths
import renderconsumer
import toolsencoding
import translations
import threading
import utils

import gmicplayer
import gmicscript

MONITOR_WIDTH = 500
MONITOR_HEIGHT = 300 # initial value, this gets changed when material is loaded
CLIP_FRAMES_DIR = "/clip_frames"
RENDER_FRAMES_DIR = "/render_frames"
PREVIEW_FILE = "preview.png"
NO_PREVIEW_FILE = "fallback_thumb.png"

_session_id = None

_window = None

_player = None
_preview_render = None
_frame_writer = None
_effect_renderer = None

_current_path = None
_current_preview_surface = None
_current_dimensions = None
_current_fps = None
_current_profile_index = None
_render_data = None
    
_encoding_panel = None

#-------------------------------------------------- launch and inits
def launch_gmic():
    print "Launch gmic..."
    gui.save_current_colors()
    
    FLOG = open(utils.get_hidden_user_dir_path() + "log_gmic", 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladegmic"], stdin=FLOG, stdout=FLOG, stderr=FLOG)


def main(root_path, force_launch=False):
       
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
    
    
    global _session_id
    _session_id = int(time.time() * 1000) # good enough

    # Set paths.
    respaths.set_paths(root_path)

    # Init gmic tool session dirs
    if os.path.exists(get_session_folder()):
        shutil.rmtree(get_session_folder())
        
    os.mkdir(get_session_folder())
    
    init_frames_dirs()
    
    # Load editor prefs and list of recent projects
    editorpersistance.load()
    if editorpersistance.prefs.dark_theme == True:
        respaths.apply_dark_theme()

    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Load preset gmic scripts
    gmicscript.load_preset_scripts_xml()
    
    # Init gtk threads
    Gdk.threads_init()
    Gdk.threads_enter()

    # Request dark them if so desired
    if editorpersistance.prefs.dark_theme == True:
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)

    repo = mlt.Factory().init()

    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()

    gui.load_current_colors()
    
    global _window
    _window = GmicWindow()
    _window.pos_bar.set_dark_bg_color()

    os.putenv('SDL_WINDOWID', str(_window.monitor.get_window().get_xid()))
    Gdk.flush()
        
    Gtk.main()
    Gdk.threads_leave()

def init_frames_dirs():
    os.mkdir(get_clip_frames_dir())
    os.mkdir(get_render_frames_dir())

#----------------------------------------------- session folders and files
def get_session_folder():
    return utils.get_hidden_user_dir_path() + appconsts.GMIC_DIR + "/session_" + str(_session_id)

def get_clip_frames_dir():
    return get_session_folder() + CLIP_FRAMES_DIR

def get_render_frames_dir():
    return get_session_folder() + RENDER_FRAMES_DIR
    
def get_current_frame_file():
    return get_clip_frames_dir() + "/frame" + str(_player.current_frame()) + ".png"

def get_preview_file():
    return get_session_folder() + "/" + PREVIEW_FILE
    
# --------------------------------------------- load clip
def open_clip_dialog():
    
    file_select = Gtk.FileChooserDialog(_("Select Image Media"), _window, Gtk.FileChooserAction.OPEN,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    file_select.set_default_response(Gtk.ResponseType.CANCEL)
    file_select.set_select_multiple(False)

    media_filter = utils.get_video_source_file_filter()
    all_filter = Gtk.FileFilter()
    file_select.add_filter(media_filter)

    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True) 
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_select.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
    
    file_select.connect('response', _open_files_dialog_cb)

    file_select.set_modal(True)
    file_select.show()

def _open_files_dialog_cb(file_select, response_id):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != Gtk.ResponseType.OK:
        return
    if len(filenames) == 0:
        return

    # Only accept video files
    if utils.get_file_type(filenames[0]) != "video":
        return
    
    global _current_path
    _current_path = filenames[0]

    new_profile_index = gmicplayer.set_current_profile(_current_path)
    new_profile = mltprofiles.get_profile_for_index(new_profile_index)

    global _current_dimensions, _current_fps, _current_profile_index
    _current_dimensions = (new_profile.width(), new_profile.height(), 1.0)
    _current_fps = float(new_profile.frame_rate_num())/float(new_profile.frame_rate_den())
    _current_profile_index = new_profile_index

    global _player, _frame_writer
    _player = gmicplayer.GmicPlayer(_current_path)
    _frame_writer = gmicplayer.PreviewFrameWriter(_current_path)

    _window.set_fps()
    _window.init_for_new_clip(_current_path, new_profile.description())
    _window.set_monitor_sizes()
    _window.set_widgets_sensitive(True)
    _player.create_sdl_consumer()
    _player.connect_and_start()

#-------------------------------------------------- script setting
def script_menu_lauched(launcher, event):
    gmicscript.show_menu(event, script_menu_item_selected)

def script_menu_item_selected(item, script):
    if _window.action_select.get_active() == 0:
        _window.script_view.get_buffer().set_text(script.script)
    else:
        buf = _window.script_view.get_buffer()
        buf.insert(buf.get_end_iter(), " " + script.script)
    _window.preset_label.set_text(script.name)
    
#-------------------------------------------------- player buttons
def prev_pressed():
    _player.seek_delta(-1)
    update_frame_displayers()
        
def next_pressed():
    _player.seek_delta(1)
    update_frame_displayers()

def mark_in_pressed():
    _player.producer.mark_in = _player.current_frame()
    if _player.producer.mark_in > _player.producer.mark_out:
        _player.producer.mark_out = -1

    _window.update_marks_display()
    _window.pos_bar.update_display_from_producer(_player.producer)
    _window.update_render_status_info()

def mark_out_pressed():
    _player.producer.mark_out = _player.current_frame()
    if _player.producer.mark_out < _player.producer.mark_in:
        _player.producer.mark_in = -1

    _window.update_marks_display()
    _window.pos_bar.update_display_from_producer(_player.producer)
    _window.update_render_status_info()
    
def marks_clear_pressed():
    _player.producer.mark_in = -1
    _player.producer.mark_out = -1

    _window.update_marks_display()
    _window.pos_bar.update_display_from_producer(_player.producer)
        
def to_mark_in_pressed():
    if _player.producer.mark_in != -1:
        _player.seek_frame(_player.producer.mark_in)
    update_frame_displayers()
    
def to_mark_out_pressed():
    if _player.producer.mark_out != -1:
        _player.seek_frame(_player.producer.mark_out)
    update_frame_displayers()

def update_frame_displayers():
    frame = _player.current_frame()
    _window.tc_display.set_frame(frame)
    _window.pos_bar.update_display_from_producer(_player.producer)

#-------------------------------------------------- render and preview
def render_output():
    global _effect_renderer
    _effect_renderer = GmicEffectRendererer()
    _effect_renderer.start()

def render_preview_frame():
    _frame_writer.write_frame(get_clip_frames_dir() + "/", _player.current_frame())
    render_current_frame_preview()
    _window.preview_monitor.queue_draw()
    
def render_current_frame_preview():
    global _preview_render
    _preview_render = GmicPreviewRendererer()
    _preview_render.start()

def _encode_settings_clicked():
    toolsencoding.create_widgets(_current_profile_index, True)
        
    global _encoding_panel
    _encoding_panel = toolsencoding.get_gmic_render_panel()

    align = dialogutils.get_default_alignment(_encoding_panel)
    
    dialog = Gtk.Dialog("Video Encoding Settings",
                        _window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT,
                         _("Set Encoding").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_resizable(False)

    dialog.connect('response', _encode_settings_callback)
    dialog.show_all()

def _encode_settings_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        global _render_data
        _render_data = toolsencoding.get_render_data_for_current_selections()
        _window.update_encode_desc()
    
    dialog.destroy()
        
        
#-------------------------------------------------- shutdown
def _shutdown():
    # Stop all possibly running threads and consumers
    if _player != None:
        _player.shutdown()
    if _effect_renderer != None:
        _effect_renderer.shutdown()

    # Delete session folder
    shutil.rmtree(get_session_folder())
    
    # Exit gtk main loop.
    Gtk.main_quit()


#------------------------------------------------- window
class GmicWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowblademedialinker.png")
        self.set_icon(app_icon)

        # Load media row
        load_button = Gtk.Button(_("Load Clip"))
        load_button.connect("clicked",
                            lambda w: self.load_button_clicked())
        self.media_info = Gtk.Label()
        self.media_info.set_markup("<small>no clip loaded</small>")#"<small>" + "video_clip.mpg, 1920x1080,  25.0fps" + "</small>" )
        load_row = Gtk.HBox(False, 2)
        load_row.pack_start(load_button, False, False, 0)
        load_row.pack_start(guiutils.get_pad_label(6, 2), False, False, 0)
        load_row.pack_start(self.media_info, False, False, 0)
        load_row.pack_start(Gtk.Label(), True, True, 0)
        load_row.set_margin_bottom(4)

        # Clip monitor
        black_box = Gtk.EventBox()
        black_box.add(Gtk.Label())
        bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
        black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
        self.monitor = black_box  # This could be any GTK+ widget (that is not "windowless"), only its XWindow draw rect 
                                  # is used to position and scale SDL overlay that actually displays video.
        self.monitor.set_size_request(MONITOR_WIDTH, MONITOR_HEIGHT)

        left_vbox = Gtk.VBox(False, 0)
        left_vbox.pack_start(load_row, False, False, 0)
        left_vbox.pack_start(self.monitor, True, True, 0)

        self.preview_info = Gtk.Label()
        self.preview_info.set_markup("<small>" + _("no preview") + "</small>" )
        preview_info_row = Gtk.HBox()
        preview_info_row.pack_start(self.preview_info, False, False, 0)
        preview_info_row.pack_start(Gtk.Label(), True, True, 0)
        preview_info_row.set_margin_top(6)
        preview_info_row.set_margin_bottom(8)

        self.preview_monitor = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_preview)

        self.no_preview_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + NO_PREVIEW_FILE)

        right_vbox = Gtk.VBox(False, 2)
        right_vbox.pack_start(preview_info_row, False, False, 0)
        right_vbox.pack_start(self.preview_monitor, True, True, 0)

        # Monitors panel
        monitors_panel = Gtk.HBox(False, 2)
        monitors_panel.pack_start(left_vbox, False, False, 0)
        monitors_panel.pack_start(Gtk.Label(), True, True, 0)
        monitors_panel.pack_start(right_vbox, False, False, 0)

        # Control row
        self.tc_display = guicomponents.MonitorTCDisplay()
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)
        self.tc_display.use_internal_fps = True
        
        self.pos_bar = positionbar.PositionBar(False)
        self.pos_bar.set_listener(self.position_listener)
        pos_bar_frame = Gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pos_bar_frame.set_margin_top(5)
        pos_bar_frame.set_margin_bottom(4)
        pos_bar_frame.set_margin_left(6)
        pos_bar_frame.set_margin_right(2)
        
        self.control_buttons = glassbuttons.GmicButtons()
        pressed_callback_funcs = [prev_pressed,
                                  next_pressed,
                                  mark_in_pressed,
                                  mark_out_pressed,
                                  marks_clear_pressed,
                                  to_mark_in_pressed,
                                  to_mark_out_pressed]
        self.control_buttons.set_callbacks(pressed_callback_funcs)
        
        self.preview_button = Gtk.Button(_("Preview"))
        self.preview_button.connect("clicked", lambda w: render_preview_frame())
                            
        control_panel = Gtk.HBox(False, 2)
        control_panel.pack_start(self.tc_display.widget, False, False, 0)
        control_panel.pack_start(pos_bar_frame, True, True, 0)
        control_panel.pack_start(self.control_buttons.widget, False, False, 0)
        control_panel.pack_start(guiutils.pad_label(2, 2), False, False, 0)
        control_panel.pack_start(self.preview_button, False, False, 0)

        preview_panel = Gtk.VBox(False, 2)
        preview_panel.pack_start(monitors_panel, False, False, 0)
        preview_panel.pack_start(control_panel, False, False, 0)
        preview_panel.set_margin_bottom(8)

        # Script area
        self.preset_label = Gtk.Label()
        self.present_event_box = Gtk.EventBox()
        self.present_event_box.add(self.preset_label)
        self.present_event_box.connect("button-press-event",  script_menu_lauched)

        self.script_menu = PressLaunch(script_menu_lauched)
        self.action_select = Gtk.ComboBoxText()
        self.action_select.append_text(_("Replace Script"))
        self.action_select.append_text(_("Add to Script"))
        self.action_select.set_active(0)
        
        preset_row = Gtk.HBox(False, 2)
        preset_row.pack_start(self.present_event_box, False, False, 0)
        preset_row.pack_start(self.script_menu.widget, False, False, 0)
        preset_row.pack_start(guiutils.pad_label(6, 12), False, False, 0)
        preset_row.pack_start(Gtk.Label(), True, True, 0)
        preset_row.pack_start(self.action_select, False, False, 0)
        
        self.script_view = Gtk.TextView()
        self.script_view.set_sensitive(False)
        self.script_view.set_pixels_above_lines(2)
        self.script_view.set_left_margin(2)
        self.script_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        
        script_sw = Gtk.ScrolledWindow()
        script_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        script_sw.add(self.script_view)
        script_sw.set_size_request(MONITOR_WIDTH - 100, 125)

        self.out_view = Gtk.TextView()
        self.out_view.set_sensitive(False)
        self.out_view.set_pixels_above_lines(2)
        self.out_view.set_left_margin(2)
        self.out_view.set_wrap_mode(Gtk.WrapMode.WORD)
        fd = Pango.FontDescription.from_string("Sans 8")
        self.out_view.override_font(fd)

        out_sw = Gtk.ScrolledWindow()
        out_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        out_sw.add(self.out_view)
        out_sw.set_size_request(MONITOR_WIDTH - 150, 100)
        
        script_vbox = Gtk.VBox(False, 2)
        script_vbox.pack_start(preset_row, False, False, 0)
        script_vbox.pack_start(script_sw, True, True, 0)
        script_vbox.pack_start(out_sw, True, True, 0)

        # Render panel
        self.mark_in_label = guiutils.bold_label("Mark In:")
        self.mark_out_label = guiutils.bold_label("Mark Out:")
        self.length_label = guiutils.bold_label("Length:")
        
        self.mark_in_info = Gtk.Label("-")
        self.mark_out_info = Gtk.Label("-")
        self.length_info = Gtk.Label("-")

        in_row = guiutils.get_two_column_box(self.mark_in_label, self.mark_in_info, 150)
        out_row = guiutils.get_two_column_box(self.mark_out_label, self.mark_out_info, 150)
        length_row = guiutils.get_two_column_box(self.length_label, self.length_info, 150)
        
        marks_row = Gtk.VBox(False, 2)
        marks_row.pack_start(in_row, True, True, 0)
        marks_row.pack_start(out_row, True, True, 0)
        marks_row.pack_start(length_row, True, True, 0)

        self.out_folder = Gtk.FileChooserButton(_("Select Folder"))
        self.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.out_folder.connect("selection-changed", self.folder_selection_changed) 
        self.out_label = Gtk.Label(label=_("Frames Folder:"))
        
        self.frame_name = Gtk.Entry()
        self.frame_name.set_text("frame")
        self.extension_label = Gtk.Label()
        self.extension_label.set_markup("<small>XXXX.png</small>")

        out_folder_row = guiutils.get_left_justified_box([self.out_label, guiutils.pad_label(12, 2), \
                            self.out_folder, guiutils.pad_label(24, 2), self.frame_name, \
                            guiutils.pad_label(2, 2), self.extension_label])

        self.encode_check_label = Gtk.Label("Encode Video")
        self.encode_check = Gtk.CheckButton()
        self.encode_check.set_active(False)
        self.encode_check.connect("toggled", lambda w:self.update_encode_sensitive())
        
        self.encode_settings_button = Gtk.Button(_("Encoding settings"))
        self.encode_settings_button.connect("clicked", lambda w:_encode_settings_clicked())
        self.encode_desc = Gtk.Label()
        self.encode_desc.set_markup("<small>"+ "mpeg2video, 3000k" + "</small>")
        
        encode_row = Gtk.HBox(False, 2)
        encode_row.pack_start(self.encode_check, False, False, 0)
        encode_row.pack_start(self.encode_check_label, False, False, 0)
        encode_row.pack_start(guiutils.pad_label(48, 12), False, False, 0)
        encode_row.pack_start(self.encode_settings_button, False, False, 0)
        encode_row.pack_start(guiutils.pad_label(6, 12), False, False, 0)
        encode_row.pack_start(self.encode_desc, False, False, 0)
        encode_row.pack_start(Gtk.Label(), True, True, 0)
        encode_row.set_margin_bottom(6)

        self.render_percentage = Gtk.Label("")
        
        self.status_no_render = _("Set Mark In, Mark Out and Frames Folder for valid render")
         
        self.render_status_info = Gtk.Label()
        self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>") 

        render_status_row = Gtk.HBox(False, 2)
        render_status_row.pack_start(self.render_percentage, False, False, 0)
        render_status_row.pack_start(Gtk.Label(), True, True, 0)
        render_status_row.pack_start(self.render_status_info, False, False, 0)

        render_status_row.set_margin_bottom(6)

        self.render_progress_bar = Gtk.ProgressBar()
        self.render_progress_bar.set_valign(Gtk.Align.CENTER)

        self.stop_button = guiutils.get_sized_button(_("Stop"), 100, 32)
        self.render_button = guiutils.get_sized_button(_("Render"), 100, 32)
        self.render_button.connect("clicked", lambda w:render_output())

        render_row = Gtk.HBox(False, 2)
        render_row.pack_start(self.render_progress_bar, True, True, 0)
        render_row.pack_start(guiutils.pad_label(12, 2), False, False, 0)
        render_row.pack_start(self.stop_button, False, False, 0)
        render_row.pack_start(self.render_button, False, False, 0)

        render_vbox = Gtk.VBox(False, 2)
        render_vbox.pack_start(marks_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(encode_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(out_folder_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(render_status_row, False, False, 0)
        render_vbox.pack_start(render_row, False, False, 0)
        render_vbox.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        
        # Script work panel
        script_work_panel = Gtk.HBox(False, 2)
        script_work_panel.pack_start(script_vbox, False, False, 0)
        script_work_panel.pack_start(guiutils.pad_label(12, 2), False, False, 0)
        script_work_panel.pack_start(render_vbox, True, True, 0)

        self.load_script = Gtk.Button(_("Load Script"))
        #load_layers.connect("clicked", lambda w:self._load_layers_pressed())
        self.save_script = Gtk.Button(_("Save Script"))
        #save_layers.connect("clicked", lambda w:self._save_layers_pressed())

        info_b = guiutils.get_sized_button(_("Info"), 150, 32)
        exit_b = guiutils.get_sized_button(_("Close"), 150, 32)
        exit_b.connect("clicked", lambda w:_shutdown())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(self.load_script, False, False, 0)
        editor_buttons_row.pack_start(self.save_script, False, False, 0)
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(info_b, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(96, 2), False, False, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)

        # Build window
        pane = Gtk.VBox(False, 2)
        pane.pack_start(preview_panel, False, False, 0)
        pane.pack_start(script_work_panel, False, False, 0)
        pane.pack_start(editor_buttons_row, False, False, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        script = gmicscript.get_default_script()
        self.script_view.get_buffer().set_text(script.script)
        self.preset_label.set_text(script.name)

        self.update_encode_sensitive()

        # Connect global key listener
        self.connect("key-press-event", _global_key_down_listener)

        # Set pane and show window
        self.add(align)
        self.set_title(_("G'MIC Effects"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_widgets_sensitive(False)
        self.show_all()
        self.set_resizable(False)
        self.set_active_state(False)

    def init_for_new_clip(self, clip_path, profile_name):
        self.clip_path = clip_path
        self.set_active_state(True)
        self.pos_bar.update_display_from_producer(_player.producer)
        self.media_info.set_markup("<small>" + os.path.basename(clip_path) + ", " + profile_name + "</small>")

    def update_marks_display(self):
        if _player.producer.mark_in == -1:
            self.mark_in_info.set_text("-")
        else:
            self.mark_in_info.set_text(utils.get_tc_string_with_fps(_player.producer.mark_in, _current_fps))
        
        if  _player.producer.mark_out == -1:
            self.mark_out_info.set_text("-")
        else:
            self.mark_out_info.set_text(utils.get_tc_string_with_fps(_player.producer.mark_out + 1, _current_fps))

        if _player.producer.mark_in == -1 or  _player.producer.mark_out == -1:
            self.length_info.set_text("-")
        else:
            self.length_info.set_text(str(_player.producer.mark_out - _player.producer.mark_in + 1) + " " + _("frames"))

        self.mark_in_info.queue_draw()
        self.mark_out_info.queue_draw()
        self.length_info.queue_draw()

    def update_render_status_info(self):
        if  _player.producer.mark_in == -1 or _player.producer.mark_out == -1 \
            or self.out_folder.get_filename() == None:
            self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>")
        else:
            length = _player.producer.mark_out - _player.producer.mark_in + 1
            info_str = str(length) + _(" frame(s),") + _(" no video file")
            self.render_status_info.set_markup("<small>" + info_str +  "</small>")

    def folder_selection_changed(self, chooser):
        self.update_render_status_info()
 
    def load_button_clicked(self):
        open_clip_dialog()

    def set_active_state(self, active):
        self.monitor.set_sensitive(active)
        self.pos_bar.widget.set_sensitive(active)

    def set_fps(self):
        self.tc_display.fps = _current_fps
        
    def position_listener(self, normalized_pos, length):
        frame = int(normalized_pos * length)
        self.tc_display.set_frame(frame)
        _player.seek_frame(frame)
        self.pos_bar.widget.queue_draw()

    def _draw_preview(self, event, cr, allocation):
        x, y, w, h = allocation

        if _current_preview_surface != None:
            width, height, pixel_aspect = _current_dimensions
            scale = float(MONITOR_WIDTH) / float(width)
            cr.scale(scale * pixel_aspect, scale)
            cr.set_source_surface(_current_preview_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(0, 0, w, h)
            cr.fill()
    
    def set_monitor_sizes(self):
        w, h, pixel_aspect = _current_dimensions
        new_height = MONITOR_WIDTH * (float(h)/float(w)) * pixel_aspect
        self.monitor.set_size_request(MONITOR_WIDTH, new_height)
        self.preview_monitor.set_size_request(MONITOR_WIDTH, new_height)

    def update_encode_sensitive(self):
        value = self.encode_check.get_active()
        self.encode_settings_button.set_sensitive(value)
        self.encode_desc.set_sensitive(value)

    def update_encode_desc(self):
        if _render_data == None:
            desc_str =  "mpeg2video, 3000k" 
        else:
            args_vals = toolsencoding.get_args_vals_list_for_render_data(_render_data)
            desc_str = toolsencoding.get_encoding_desc(args_vals)

        self.encode_desc.set_markup("<small>" + desc_str + "</small>")
        
    def set_widgets_sensitive(self, value):
        self.monitor.set_sensitive(value)
        self.preview_info.set_sensitive(value)
        self.preview_monitor.set_sensitive(value)
        self.tc_display.widget.set_sensitive(value)
        self.pos_bar.widget.set_sensitive(value)      
        self.control_buttons.set_sensitive(value)
        self.preset_label.set_sensitive(value)
        self.action_select.set_sensitive(value)
        self.script_view.set_sensitive(value) 
        self.out_view.set_sensitive(value)       
        self.mark_in_info.set_sensitive(value)
        self.mark_out_info.set_sensitive(value)
        self.length_info.set_sensitive(value)
        self.out_folder.set_sensitive(value)
        self.encode_check_label.set_sensitive(value)
        self.encode_check.set_sensitive(value)
        self.encode_settings_button.set_sensitive(value)
        self.encode_desc.set_sensitive(value)
        self.frame_name.set_sensitive(value)
        self.extension_label.set_sensitive(value)       
        self.render_percentage.set_sensitive(value)
        self.render_status_info.set_sensitive(value)
        self.render_progress_bar.set_sensitive(value)
        self.stop_button.set_sensitive(value)
        self.render_button.set_sensitive(value)
        self.preview_button.set_sensitive(value)
        self.load_script.set_sensitive(value)
        self.save_script.set_sensitive(value)
        self.mark_in_label.set_sensitive(value)
        self.mark_out_label.set_sensitive(value)
        self.length_label.set_sensitive(value)
        self.out_label.set_sensitive(value)
        self.media_info.set_sensitive(value)
        self.present_event_box.set_sensitive(value)
        self.script_menu.set_sensitive(value)
 
        self.update_encode_sensitive()


class PressLaunch:
    def __init__(self, callback, w=22, h=22):
        self.widget = cairoarea.CairoDrawableArea2( w, 
                                                    h, 
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.callback = callback
        self.sensitive = True

    def set_sensitive(self, value):
        self.sensitive = value
        
    def _draw(self, event, cr, allocation):      
        cr.move_to(7, 13)
        cr.line_to(12, 18)
        cr.line_to(17, 13)
        cr.close_path()
        if editorpersistance.prefs.dark_theme == False:
            cr.set_source_rgb(0, 0, 0)
        else:
            cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()
        
    def _press_event(self, event):
        if self.sensitive == False:
           return 

        self.callback(self.widget, event)

#------------------------------------------------- global key listener
def _global_key_down_listener(widget, event):

    # Script view and frame name entry need their own key presses
    if _window.frame_name.has_focus() or _window.script_view.has_focus():
        return False
        
    # LEFT ARROW, prev frame
    if event.keyval == Gdk.KEY_Left:
        prev_pressed()

    # RIGHT ARROW, next frame
    if event.keyval == Gdk.KEY_Right:
        next_pressed()

    # I
    if event.keyval == Gdk.KEY_i:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            to_mark_in_pressed()
        else:
            mark_in_pressed()

    if event.keyval == Gdk.KEY_I:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            to_mark_in_pressed()
        else:
            mark_in_pressed()

    # O
    if event.keyval == Gdk.KEY_o:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            to_mark_out_pressed()
        else:
            mark_out_pressed()

    if event.keyval == Gdk.KEY_O:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            to_mark_out_pressed()
        else:
            mark_out_pressed()
        
    return True

#------------------------------------------------- render threads
class GmicPreviewRendererer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        start_time = time.time()
            
        # For the case the render fails
        shutil.copyfile(get_current_frame_file(), get_preview_file())
        
        Gdk.threads_enter()
        _window.preview_info.set_markup("<small>" + _("Rendering preview...") + "</small>" )
        buf = _window.script_view.get_buffer()
        view_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        Gdk.threads_leave()
        
        script_str = "gmic " + get_current_frame_file() + " " + view_text + " -output " +  get_preview_file()

        print "Render preview:", script_str
        
        FLOG = open(utils.get_hidden_user_dir_path() + "log_gmic_preview", 'w')
        p = subprocess.Popen(script_str, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)
        p.wait()
        FLOG.close()
     
        # read log
        f = open(utils.get_hidden_user_dir_path() + "log_gmic_preview", 'r')
        out = f.read()
        f.close()

        global _current_preview_surface
        _current_preview_surface = cairo.ImageSurface.create_from_png(get_preview_file())

        Gdk.threads_enter()
        if p.returncode != 0:
           _window.out_view.override_color((Gtk.StateFlags.NORMAL and Gtk.StateFlags.ACTIVE), Gdk.RGBA(red=1.0, green=0.0, blue=0.0))
        else:
            _window.out_view.override_color((Gtk.StateFlags.NORMAL and Gtk.StateFlags.ACTIVE), None)
            
        _window.out_view.get_buffer().set_text(out + "Return code:" + str(p.returncode))

        render_time = time.time() - start_time
        time_str = "{0:.2f}".format(round(render_time,2))
        _window.preview_info.set_markup("<small>" + _("Preview for frame: ") + \
            utils.get_tc_string_with_fps(_player.current_frame(), _current_fps) + ", render time: " + time_str +  "</small>" )
            
        _window.preview_monitor.queue_draw()
        Gdk.threads_leave()


class GmicEffectRendererer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.abort = False
        
        # Refuse to render into user home folder
        out_folder = _window.out_folder.get_filenames()[0] + "/"
        if out_folder == (os.path.expanduser("~") + "/"):
            print "home folder"
            return
            
        start_time = time.time()
        
        Gdk.threads_enter()
        _window.render_status_info.set_markup("")
        Gdk.threads_leave()
            
        # Delete old preview frames
        folder = get_render_frames_dir()
        for frame_file in os.listdir(folder):
            file_path = os.path.join(folder, frame_file)
            os.remove(file_path)
        
        # Render clipm frames for range
        mark_in = _player.producer.mark_in
        mark_out = _player.producer.mark_out
        self.length = mark_out - mark_in + 1
        self.mark_in = mark_in
        self.mark_out = mark_out
        
        frame_name = _window.frame_name.get_text()
        
        # jotain controllii frame_namelle

        self.frames_range_writer = gmicplayer.FramesRangeWriter(_current_path, self.frames_update)
        self.frames_range_writer.write_frames(get_render_frames_dir() + "/", frame_name, mark_in, mark_out)
        
        # Render effect for frames
        # Get user script 
        Gdk.threads_enter()
        buf = _window.script_view.get_buffer()
        user_script = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        _window.render_percentage.set_text(_("Waiting for frames write to complete..."))
        Gdk.threads_leave()

        while len(os.listdir(folder)) != self.length:
            time.sleep(0.5)
            
        clip_frames = os.listdir(folder)

        frame_count = 1
        for clip_frame in clip_frames:
            if self.abort == True:
                return
            
            update_info = "Rending frame: " + str(frame_count) + "/" +  str(self.length)

            Gdk.threads_enter()
            _window.render_percentage.set_markup("<small>" + update_info + "</small>")
            _window.render_progress_bar.set_fraction(float(frame_count)/float(self.length))
            Gdk.threads_leave()
 
            file_numbers_list = re.findall(r'\d+', clip_frame)
            filled_number_str = str(file_numbers_list[0]).zfill(3)

            clip_frame_path = os.path.join(folder, clip_frame)
            rendered_file_path = out_folder + frame_name + "_" + filled_number_str + ".png"
            
            script_str = "gmic " + clip_frame_path + " " + user_script + " -output " +  rendered_file_path

            if frame_count == 1: # first frame displays shell output and does error checking
                FLOG = open(utils.get_hidden_user_dir_path() + "log_gmic_preview", 'w')
                p = subprocess.Popen(script_str, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)
                p.wait()
                FLOG.close()
                
                # read log
                f = open(utils.get_hidden_user_dir_path() + "log_gmic_preview", 'r')
                out = f.read()
                f.close()
                
                Gdk.threads_enter()
                _window.out_view.get_buffer().set_text(out + "Return code:" + str(p.returncode))
                if p.returncode != 0:
                    _window.out_view.override_color((Gtk.StateFlags.NORMAL and Gtk.StateFlags.ACTIVE), Gdk.RGBA(red=1.0, green=0.0, blue=0.0))
                    _window.render_percentage.set_text(_("Render error!"))
                    Gdk.threads_leave()
                    return
                else:
                    _window.out_view.override_color((Gtk.StateFlags.NORMAL and Gtk.StateFlags.ACTIVE), None)
                    Gdk.threads_leave()
            else:
                FLOG = open(utils.get_hidden_user_dir_path() + "log_gmic_preview", 'w')
                p = subprocess.Popen(script_str, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)
                p.wait()
                FLOG.close()

            frame_count = frame_count + 1

        # Render video
        if _window.encode_check.get_active() == True:
            # Render consumer
            args_vals_list = toolsencoding.get_args_vals_list_for_render_data(_render_data)
            profile = mltprofiles.get_profile_for_index(_current_profile_index) 
            file_path = _render_data.render_dir + "/" +  _render_data.file_name
            
            print file_path
            
            consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)
            
            # Render producer
            frame_file = out_folder + frame_name + "_0000.png"
            if editorstate.mlt_version_is_equal_or_greater("0.8.5"):
                resource_name_str = utils.get_img_seq_resource_name(frame_file, True)
            else:
                resource_name_str = utils.get_img_seq_resource_name(frame_file, False)
            resource_path = out_folder + "/" + resource_name_str
            producer = mlt.Producer(profile, str(resource_path))


            print resource_path

            render_player = renderconsumer.FileRenderPlayer("", producer, consumer, 0, len(clip_frames) - 1)
            render_player.start()

            while render_player.stopped == False:

                fraction = render_player.get_render_fraction()
                update_info = "Rendering video, " + str(int(fraction * 100)) + "% done"
                
                Gdk.threads_enter()
                _window.render_percentage.set_markup("<small>" + update_info + "</small>")
                _window.render_progress_bar.set_fraction(fraction)
                Gdk.threads_leave()
                
                time.sleep(0.3)

        Gdk.threads_enter()
        _window.render_percentage.set_markup("<small>" + _("Render complete!") + "</small>")
        _window.update_render_status_info()
        Gdk.threads_leave()
        
    def frames_update(self, frame):
        
        if frame - self.mark_in < 0:
            frame = self.length # hack fix, producer suddenly changes the frame i thinks it is in
        else:
            frame = frame - self.mark_in # producer returns original clip frames
        
        update_info = "Writing clip frame: " + str(frame) + "/" +  str(self.length)

        Gdk.threads_enter()
        _window.render_percentage.set_markup("<small>" + update_info + "</small>")
        _window.render_progress_bar.set_fraction(float(frame + 1)/float(self.length))
        Gdk.threads_leave()

    def shutdown(self):
        self.frames_range_writer.shutdown()
        self.abort = True


        
