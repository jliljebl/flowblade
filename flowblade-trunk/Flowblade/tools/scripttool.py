"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2021 Janne Liljeblad.

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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import GObject, GLib
from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GdkX11
from gi.repository import Pango

import cairo
import locale
import mlt
import os
import re
import shutil
import subprocess
import sys
import time
import webbrowser

import appconsts
import atomicfile
import cairoarea
import dialogutils
import editorstate
import editorpersistance
import fluxity
import gui
import guicomponents
import guiutils
import glassbuttons
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import positionbar
import processutils
import respaths
import renderconsumer
import toolguicomponents
import toolsencoding
import translations
import threading
import userfolders
import utils

import gmicplayer

MONITOR_WIDTH = 500
MONITOR_HEIGHT = 300 # initial value, this gets changed when material is loaded
CLIP_FRAMES_DIR = "/clip_frames"
RENDER_FRAMES_DIR = "/render_frames"
PREVIEW_FILE = "preview.png"
NO_PREVIEW_FILE = "fallback_thumb.png"

MLT_PLAYER_MONITOR = "mlt_player_monitor" # This one used to play clips
CAIRO_DRAW_MONITOR = "cairo_draw_monitor"  # This one used to show single frames

_session_id = None

_window = None

_player = None
_effect_renderer = None

_script_length = fluxity.DEFAULT_LENGTH

_current_profile_name = None
_current_profile_index = None # We necesserily would not need this too.

_current_path = None
#_current_preview_surface = None
_current_dimensions = None
_current_fps = None

_render_data = None # toolsencoding.ToolsRenderData object

_encoding_panel = None

# GTK3 requires this to be created outside of callback
_hamburger_menu = Gtk.Menu()

#-------------------------------------------------- launch and inits
def launch_scripttool(launch_data=None):
    gui.save_current_colors()

    # no args yet
    args = ["profile_name:" + editorstate.PROJECT().profile.description()]

    #if launch_data != None:
    #    clip, track = launch_data # from guicomponwnts._get_tool_integration_menu_item()
    #    args = ("path:" + str(clip.path), "clip_in:" + str(clip.clip_in), "clip_out:" + str(clip.clip_out))
        
    print("Launch scripttool...")
    FLOG = open(userfolders.get_cache_dir() + "log_scripttool", 'w')
    if args == None:
        subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladescripttool"], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    else:
        subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladescripttool", args[0]], stdin=FLOG, stdout=FLOG, stderr=FLOG)

def _get_arg_value(args, key_str):
    for arg in sys.argv:
        parts = arg.split(":")
        if len(parts) > 1:
            if parts[0] == key_str:
                return parts[1]
    
    return None
        
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

    # Write stdout to log file
    userfolders.init()
    sys.stdout = open(userfolders.get_cache_dir() + "log_scripttool", 'w')

    # Init script tool session dirs
    if os.path.exists(get_session_folder()):
        shutil.rmtree(get_session_folder())
        
    os.mkdir(get_session_folder())

    _init_frames_dirs()

    # Load editor prefs and apply themes
    editorpersistance.load()
            
    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Load preset gmic scripts
    #gmicscript.load_preset_scripts_xml()

    # Init gtk threads
    Gdk.threads_init()
    Gdk.threads_enter()

    # Set monitor sizes
    scr_w = Gdk.Screen.width()
    scr_h = Gdk.Screen.height()
    editorstate.SCREEN_WIDTH = scr_w
    editorstate.SCREEN_HEIGHT = scr_h
    if editorstate.screen_size_large_height() == True and editorstate.screen_size_small_width() == False:
        global MONITOR_WIDTH, MONITOR_HEIGHT
        MONITOR_WIDTH = 650
        MONITOR_HEIGHT = 400 # initial value, this gets changed when material is loaded

    # Themes
    if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
        respaths.apply_dark_theme()
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME \
            or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_GRAY \
            or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
            gui.apply_gtk_css(editorpersistance.prefs.theme)

    repo = mlt.Factory().init()
    processutils.prepare_mlt_repo(repo)
    
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

    # Get launch profile and init player and display GUI params for it. 
    global _current_profile_name
    _current_profile_name = _get_arg_value(sys.argv, "profile_name")
    _init_player_and_profile_data(_current_profile_name)

    # Show window.
    global _window
    _window = ScriptToolWindow()
    _window.pos_bar.set_dark_bg_color()
    _window.update_marks_display()

    os.putenv('SDL_WINDOWID', str(_window.monitor.get_window().get_xid()))
    Gdk.flush()

    _init_playback()
    update_length(_script_length)

    print(_current_profile_name)

    Gtk.main()
    Gdk.threads_leave()

# ------------------------------------------------- folders init
def _init_frames_dirs():
    os.mkdir(get_clip_frames_dir())
    os.mkdir(get_render_frames_dir())
    
# ----------------------------------------------------------- MLT player playback
def _init_player_and_profile_data(profile_name):
    gmicplayer.set_current_profile_for_profile_name(profile_name)
    new_profile = mltprofiles.get_profile(profile_name)

    global _current_dimensions, _current_fps, _current_profile_index
    _current_dimensions = (new_profile.width(), new_profile.height(), 1.0)
    _current_fps = float(new_profile.frame_rate_num())/float(new_profile.frame_rate_den())
    _current_profile_index = mltprofiles.get_profile_index_for_profile(new_profile)

    global _player, _current_path
    _current_path = respaths.FLUXITY_EMPTY_BG_RES_PATH
    _player = gmicplayer.GmicPlayer(_current_path)

def _init_playback():
    _window.set_fps()
    _window.pos_bar.update_display_from_producer(_player.producer)
    _window.set_monitor_sizes()

    _player.create_sdl_consumer()
    _player.connect_and_start()

def get_playback_tractor(length, range_frame_res_str=None, in_frame=-1, out_frame=-1):
    # Create tractor and tracks
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist()
    multitrack.connect(track0, 0)

    bg_path = respaths.FLUXITY_EMPTY_BG_RES_PATH
    profile = mltprofiles.get_profile(_current_profile_name)
        
    if range_frame_res_str == None:
        bg_clip = mlt.Producer(profile, str(bg_path))
        track0.insert(bg_clip, 0, 0, length - 1)
    else:
        indx = 0
        if in_frame > 0:
            bg_clip1 = mlt.Producer(profile, str(bg_path))
            track0.insert(bg_clip1, indx, 0, in_frame - 1)
            indx += 1
    
        range_producer = mlt.Producer(profile, range_frame_res_str)
        track0.insert(range_producer, indx, in_frame, out_frame)
        indx += 1
        
        if out_frame < length - 1:
            bg_clip2 = mlt.Producer(profile, str(bg_path))
            track0.insert(bg_clip2, indx, out_frame, length - 1)
        
    return tractor
    
#----------------------------------------------- session folders and files
def get_session_folder():
    return userfolders.get_cache_dir() + appconsts.SCRIP_TOOL_DIR + "/session_" + str(_session_id)

def get_clip_frames_dir():
    return get_session_folder() + CLIP_FRAMES_DIR

def get_render_frames_dir():
    return get_session_folder() + RENDER_FRAMES_DIR
    
def get_current_frame_file():
    return get_clip_frames_dir() + "/frame" + str(_player.current_frame()) + ".png"

def get_preview_file():
    return get_session_folder() + "/" + PREVIEW_FILE


    
"""
#-------------------------------------------------- script setting and save/load
#def script_menu_lauched(launcher, event):
#    gmicscript.show_menu(event, script_menu_item_selected)

def script_menu_item_selected(item, script):
    if _window.action_select.get_active() == False:
        _window.script_view.get_buffer().set_text(script.script)
    else:
        buf = _window.script_view.get_buffer()
        buf.insert(buf.get_end_iter(), " " + script.script)
    _window.preset_label.set_text(script.name)
"""

def save_script_dialog(callback):
    dialog = Gtk.FileChooserDialog(_("Save Script As"), None, 
                                   Gtk.FileChooserAction.SAVE, 
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name("flowblade_script")
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def _save_script_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        file_path = dialog.get_filenames()[0]
        buf = _window.script_view.get_buffer()
        script_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        with atomicfile.AtomicFileWriter(file_path, "w") as afw:
            script_file = afw.get_file()
            script_file.write(script_text)
        dialog.destroy()
    else:
        dialog.destroy()

def load_script_dialog(callback):
    dialog = Gtk.FileChooserDialog(_("Load Script"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def _load_script_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filename = dialog.get_filenames()[0]
        args_file = open(filename)
        args_text = args_file.read()
        _window.script_view.get_buffer().set_text(args_text)
        dialog.destroy()
    else:
        dialog.destroy()



    
#-------------------------------------------------- menu
def _hamburger_menu_callback(widget, msg):
    if msg == "load_script":
        load_script_dialog(_load_script_dialog_callback)
    elif msg == "save_script":
        save_script_dialog(_save_script_dialog_callback)
    elif msg == "render_preview":
        render_preview()
    elif msg == "close":
        _shutdown()
    elif msg == "docs":
        webbrowser.open(url="http://gmic.eu/", new=0, autoraise=True)

def _get_menu_item(text, callback, data, sensitive=True):
    item = Gtk.MenuItem.new_with_label(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item

def _add_separetor(menu):
    sep = Gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)

#-------------------------------------------------- player buttons
def prev_pressed(delta=-1):
    _player.seek_delta(delta)
    update_frame_displayers()
        
def next_pressed(delta=1):
    _player.seek_delta(delta)
    update_frame_displayers()

def start_pressed():
    _player.seek_frame(0)
    update_frame_displayers()
        
def end_pressed():
    _player.seek_delta(_player.get_active_length() - 1)
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
    _window.update_render_status_info()

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

def update_length(new_length):
    global _script_length
    _script_length = new_length

    new_playback_producer = get_playback_tractor(_script_length)
    _player.set_producer(new_playback_producer)

    _window.update_marks_display()
    _window.pos_bar.update_display_from_producer(_player.producer)

#-------------------------------------------------- render and preview
def render_output():
    global _effect_renderer
    _effect_renderer = FluxityPluginRenderer()
    _effect_renderer.start()

def abort_render():
    _effect_renderer.abort_render()

def render_preview_frame():
    buf = _window.script_view.get_buffer()
    script = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
    _profile_file_path = mltprofiles.get_profile_file_path(_current_profile_name)

    profile = mltprofiles.get_profile(_current_profile_name)
    global _current_dimensions
    _current_dimensions = (profile.width(), profile.height(), 1.0)
    frame = _player.current_frame()
    
    _window.out_view.get_buffer().set_text("Rendering...")

    fctx = fluxity.render_preview_frame(script, frame, get_session_folder(), _profile_file_path)
    _window.pos_bar.preview_range = None # frame or black for fail, no range anyway
        
    if fctx.error == None:
        fctx.priv_context.frame_surface.write_to_png(respaths.FLUXITY_PREVIEW_IMG_PATH,)
        new_playback_producer = get_playback_tractor(_script_length, respaths.FLUXITY_PREVIEW_IMG_PATH, 0, _script_length)
        _player.set_producer(new_playback_producer)
        _player.seek_frame(frame)

        _window.monitors_switcher.set_visible_child_name(MLT_PLAYER_MONITOR)

        _window.monitors_switcher.queue_draw()
        _window.preview_monitor.queue_draw()
        _window.pos_bar.widget.queue_draw()
        _window.out_view.get_buffer().set_text("Preview rendered for frame " + str(frame))
        _window.media_info.set_markup("<small>" + _("Preview for frame: ") + str(frame) + "</small>")
    else:
        #global _current_preview_surface
        #_current_preview_surface = None
        _window.monitors_switcher.set_visible_child_name(CAIRO_DRAW_MONITOR)
        _window.out_view.get_buffer().set_text(fctx.error)
        _window.media_info.set_markup("<small>" + _("No Preview") +"</small>")
        #_current_preview_surface = None
        _window.monitors_switcher.queue_draw()
        _window.preview_monitor.queue_draw()
        
def render_range():
    buf = _window.script_view.get_buffer()
    script = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
    profile_file_path = mltprofiles.get_profile_file_path(_current_profile_name)

    profile = mltprofiles.get_profile(_current_profile_name)
    global _current_dimensions
    _current_dimensions = (profile.width(), profile.height(), 1.0)

    _window.out_view.get_buffer().set_text("Rendering...")

    range_renderer = FluxityRangeRenderer(script, get_render_frames_dir(), profile_file_path)
    range_renderer.start()

def _encode_settings_clicked():
    toolsencoding.create_widgets(_current_profile_index)
        
    global _encoding_panel
    _encoding_panel = toolsencoding.get_encoding_panel(_render_data)

    if _render_data == None and toolsencoding.widgets.file_panel.movie_name.get_text() == "movie":
        toolsencoding.widgets.file_panel.movie_name.set_text("plugin_clip")

    align = dialogutils.get_default_alignment(_encoding_panel)
    
    dialog = Gtk.Dialog(_("Video Encoding Settings"),
                        _window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Set Encoding"), Gtk.ResponseType.ACCEPT))
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
class ScriptToolWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowbladetoolicon.png")
        self.set_icon(app_icon)
        hamburger_launcher_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger.png")
        self.hamburger_launcher = guicomponents.PressLaunch(self.hamburger_launch_pressed, hamburger_launcher_surface)
        
        # ---------------------------------------------------------------------- TOP ROW
        # ---------------------------------------------------------------------- TOP ROW
        # ---------------------------------------------------------------------- TOP ROW
        self.load_button = Gtk.Button(_("Load Clip"))
        self.load_button.connect("clicked", lambda w: open_clip_dialog())

        self.media_info = Gtk.Label()
        self.media_info.set_markup("<small>" + _("No Preview") + "</small>")

        top_row = Gtk.HBox(False, 2)
        top_row.pack_start(self.hamburger_launcher.widget, False, False, 0)
        top_row.pack_start(guiutils.get_pad_label(6, 2), False, False, 0)
        top_row.pack_start(Gtk.Label(), True, True, 0)
        top_row.pack_start(self.media_info, False, False, 0)
        top_row.set_margin_bottom(4)

        # -------------------------------------------------------------------- RIGHT SIDE: MONITOR, CONTROLS, ENCODING
        # -------------------------------------------------------------------- RIGHT SIDE: MONITOR, CONTROLS, ENCODING 
        # -------------------------------------------------------------------- RIGHT SIDE: MONITOR, CONTROLS, ENCODING 
        black_box = Gtk.EventBox()
        black_box.add(Gtk.Label())
        bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
        black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
        self.monitor = black_box  # This could be any GTK+ widget (that is not "windowless"), only its XWindow draw rect 
                                  # is used to position and scale SDL overlay that actually displays video.
        self.monitor.set_size_request(MONITOR_WIDTH, MONITOR_HEIGHT)

        self.preview_monitor = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_preview)

        self.monitors_switcher = Gtk.Stack()    
        self.monitors_switcher.add_named(self.monitor, MLT_PLAYER_MONITOR)
        self.monitors_switcher.add_named(self.preview_monitor, CAIRO_DRAW_MONITOR)
        self.monitors_switcher.set_visible_child_name(CAIRO_DRAW_MONITOR)

        # Control row
        self.tc_display = guicomponents.MonitorTCDisplay(56)
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)
        self.tc_display.use_internal_fps = True
        self.tc_display.display_tc = False
        
        self.pos_bar = positionbar.PositionBar(False)
        self.pos_bar.set_listener(self.position_listener)
        pos_bar_frame = Gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pos_bar_frame.set_margin_top(10)
        pos_bar_frame.set_margin_bottom(9)
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
        self.preview_range_button = Gtk.Button(_("Preview Range"))
        self.preview_range_button.connect("clicked", lambda w: render_range())
        self.preview_range_button.set_sensitive(False)
            
        control_top = Gtk.HBox(False, 2)
        control_top.pack_start(self.tc_display.widget, False, False, 0)
        control_top.pack_start(pos_bar_frame, True, True, 0)
        control_top.pack_start(guiutils.pad_label(2, 2), False, False, 0)
        control_top.pack_start(self.preview_button, False, False, 0)
        control_top.pack_start(self.preview_range_button, False, False, 0)

        control_bottom = Gtk.HBox(False, 2)
        control_bottom.pack_start(Gtk.Label(), True, True, 0)
        control_bottom.pack_start(self.control_buttons.widget, False, False, 0)
        control_bottom.pack_start(Gtk.Label(), True, True, 0)
        
        control_panel = Gtk.VBox(False, 2)
        control_panel.pack_start(control_top, False, False, 0)
        control_panel.pack_start(control_bottom, True, True, 0)

        preview_panel = Gtk.VBox(False, 2)
        preview_panel.pack_start(self.monitors_switcher, True, True, 0)
        preview_panel.pack_start(control_panel, False, False, 0)
        preview_panel.set_margin_bottom(8)

        # Render panel
        self.mark_in_label = guiutils.bold_label(_("Mark In:"))
        self.mark_out_label = guiutils.bold_label(_("Mark Out:"))
        self.length_label = guiutils.bold_label(_("Length:"))

        self.mark_in_info = Gtk.Label("")
        self.mark_out_info = Gtk.Label("")
        self.length_info = Gtk.Label("")

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

        self.encode_check_label = Gtk.Label(_("Encode Video"))
        self.encode_check = Gtk.CheckButton()
        self.encode_check.set_active(False)
        self.encode_check.connect("toggled", lambda w:self.update_encode_sensitive())

        self.encode_settings_button = Gtk.Button(_("Encoding settings"))
        self.encode_settings_button.connect("clicked", lambda w:_encode_settings_clicked())
        self.encode_desc = Gtk.Label()
        self.encode_desc.set_markup("<small>" + _("not set")  + "</small>")
        self.encode_desc.set_ellipsize(Pango.EllipsizeMode.END)
        self.encode_desc.set_max_width_chars(32)

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

        self.status_no_render = _("Set Frames Folder for valid render")
         
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
        self.stop_button.connect("clicked", lambda w:abort_render())
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

        exit_b = guiutils.get_sized_button(_("Close"), 150, 32)
        exit_b.connect("clicked", lambda w:_shutdown())
        self.close_button = exit_b
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)

        preview_render_vbox = Gtk.VBox(False, 2)
        preview_render_vbox.pack_start(preview_panel, True, True, 0)
        preview_render_vbox.pack_start(render_vbox, False, False, 0)
        preview_render_vbox.pack_start(editor_buttons_row, False, False, 0)
        preview_render_vbox.set_margin_left(4)

        # --------------------------------------------------- LEFT SIDE: SCRIPTING
        # --------------------------------------------------- LEFT SIDE: SCRIPTING
        # --------------------------------------------------- LEFT SIDE: SCRIPTING    
        self.script_view = Gtk.TextView()
        self.script_view.set_sensitive(True)
        self.script_view.set_editable(True)
        self.script_view.set_pixels_above_lines(2)
        self.script_view.set_left_margin(2)
        self.script_view.set_monospace(True)
        self.script_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        
        script_sw = Gtk.ScrolledWindow()
        script_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        script_sw.add(self.script_view)
        script_sw.set_size_request(MONITOR_WIDTH - 100, 225)
        script_sw.set_margin_bottom(4)

        self.out_view = Gtk.TextView()
        self.out_view.set_sensitive(False)
        self.out_view.set_pixels_above_lines(2)
        self.out_view.set_left_margin(2)
        self.out_view.set_monospace(True)
        self.out_view.set_wrap_mode(Gtk.WrapMode.WORD)
        fd = Pango.FontDescription.from_string("Sans 8")
        self.out_view.override_font(fd)

        out_sw = Gtk.ScrolledWindow()
        out_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        out_sw.add(self.out_view)
        out_sw.set_size_request(MONITOR_WIDTH - 150, 200)
        out_sw.set_margin_top(4)

        script_vbox = Gtk.Paned.new(Gtk.Orientation.VERTICAL) 
        script_vbox.pack1(script_sw, True, False)
        script_vbox.pack2(out_sw, False, False)
        script_vbox.set_margin_right(4)
        

        # ------------------------------------------------------------ BUILD WINDOW
        # ------------------------------------------------------------ BUILD WINDOW
        # ------------------------------------------------------------ BUILD WINDOW
        main_hbox = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL) #Gtk.HBox(False, 2)
        main_hbox.pack1(script_vbox, True, False)
        main_hbox.pack2(preview_render_vbox, False, False)

        # Build window
        pane = Gtk.VBox(False, 2)
        pane.pack_start(top_row, False, False, 0)
        pane.pack_start(main_hbox, True, True, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        self.script_view.get_buffer().set_text(fluxity.DEFAULT_SCRIPT)

        self.update_encode_sensitive()

        self.connect("key-press-event", _global_key_down_listener)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Flowblade Media Plugin Editor"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_active_state(True)

    def update_marks_display(self):

        if _player.producer.mark_in  == -1:
            self.mark_in_info.set_text("-")
        else:
            self.mark_in_info.set_text(str(_player.producer.mark_in))
        
        if _player.producer.mark_out == -1:
            self.mark_out_info.set_text("-")
        else:
            self.mark_out_info.set_text(str(_player.producer.mark_out))

        if _player.producer.mark_in  == -1 or _player.producer.mark_out == -1:
            self.preview_range_button.set_sensitive(False)
        else:
            self.preview_range_button.set_sensitive(True)
            
        self.length_info.set_text(str(_script_length) + " " + _("frames"))

        self.mark_in_info.queue_draw()
        self.mark_out_info.queue_draw()
        self.length_info.queue_draw()

    def update_render_status_info(self):
        if _player == None:# this gets called too on startup to set text before player is ready
            self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>")
            self.render_button.set_sensitive(False)
            return
        
        if  self.out_folder.get_filename() == None:
            self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>")
            self.render_button.set_sensitive(False)
        else:
            start =  _player.producer.mark_in
            end = _player.producer.mark_out
            if start == -1:
                start = 0
            if end == -1:
                end = _player.get_active_length()
            length = end - start
            video_info = _(" no video file")
            if self.encode_check.get_active() == True:
                video_info = _(" render video file")
            info_str = str(length) + _(" frame(s),") + video_info
            self.render_status_info.set_markup("<small>" + info_str + "</small>")
            self.render_button.set_sensitive(True)
            
    def folder_selection_changed(self, chooser):
        self.update_render_status_info()

    def hamburger_launch_pressed(self, widget, event):
        menu = _hamburger_menu
        guiutils.remove_children(menu)
        
        menu.add(_get_menu_item(_("Load Script") + "...", _hamburger_menu_callback, "load_script" ))
        menu.add(_get_menu_item(_("Save Script") + "...", _hamburger_menu_callback, "save_script" ))
        _add_separetor(menu)
        menu.add(_get_menu_item(_("Render Frame Preview") + "...", _hamburger_menu_callback, "render_preview" ))
        menu.add(_get_menu_item(_("Render Range Preview") + "...", _hamburger_menu_callback, "render_range_preview" ))
        _add_separetor(menu)
        menu.add(_get_menu_item(_("G'Mic Webpage"), _hamburger_menu_callback, "docs" ))
        _add_separetor(menu)
        menu.add(_get_menu_item(_("Close"), _hamburger_menu_callback, "close" ))
        
        menu.popup(None, None, None, None, event.button, event.time)

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
        """
        if _current_preview_surface != None:
            width, height, pixel_aspect = _current_dimensions
            scale = float(MONITOR_WIDTH) / float(width)
            cr.scale(scale * pixel_aspect, scale)
            cr.set_source_surface(_current_preview_surface, 0, 0)
            cr.paint()
        else:
        """
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
        self.update_render_status_info()

    def update_encode_desc(self):
        if _render_data == None:
            desc_str = "not set" 
        else:
            args_vals = toolsencoding.get_args_vals_list_for_render_data(_render_data)
            desc_str = toolsencoding.get_encoding_desc(args_vals) + ", " + _render_data.file_name + _render_data.file_extension

        self.encode_desc.set_markup("<small>" + desc_str + "</small>")
        self.encode_desc.set_ellipsize(Pango.EllipsizeMode.END)

    def set_widgets_sensitive(self, value):
        self.monitor.set_sensitive(value)
        self.preview_monitor.set_sensitive(value)
        self.tc_display.widget.set_sensitive(value)
        self.pos_bar.widget.set_sensitive(value)      
        self.control_buttons.set_sensitive(value)
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
        self.stop_button.set_sensitive(False)
        self.render_button.set_sensitive(value)
        self.preview_button.set_sensitive(value)
        self.mark_in_label.set_sensitive(value)
        self.mark_out_label.set_sensitive(value)
        self.length_label.set_sensitive(value)
        self.out_label.set_sensitive(value)
        self.media_info.set_sensitive(value)
 
        self.update_encode_sensitive()


#------------------------------------------------- global key listener
def _global_key_down_listener(widget, event):

    # Script view and frame name entry need their own key presses
    if _window.frame_name.has_focus() or _window.script_view.has_focus():
        return False
        
    # LEFT ARROW, prev frame
    if event.keyval == Gdk.KEY_Left:
        if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            prev_pressed(-10)
        else:
            prev_pressed()

    # RIGHT ARROW, next frame
    if event.keyval == Gdk.KEY_Right:
        if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            next_pressed(10)
        else:
            next_pressed()

    # DOWN ARROW, start
    if event.keyval == Gdk.KEY_Down:
        start_pressed()
        
    # UP ARROW, end
    if event.keyval == Gdk.KEY_Up:
        end_pressed()
    
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
class FluxityRangeRenderer(threading.Thread):

    def __init__(self, script, render_folder, profile_file_path):
        threading.Thread.__init__(self)
        self.script = script
        self.render_folder = render_folder
        self.profile_file_path = profile_file_path

    def run(self):
        #start_time = time.time()
    
        Gdk.threads_enter()
        _window.out_view.get_buffer().set_text("Rendering...")
        Gdk.threads_leave()
            
        # GUI quarantees valid range here.
        in_frame = _player.producer.mark_in
        out_frame = _player.producer.mark_out
        
        fctx = fluxity.render_frame_sequence(self.script, in_frame, out_frame, self.render_folder, self.profile_file_path, self.frame_write_update)

        Gdk.threads_enter()
        
        if fctx.error == None:
            frame_file = fctx.priv_context.first_rendered_frame_path
            resource_name_str = utils.get_img_seq_resource_name(frame_file, True)
            range_resourse_mlt_path = get_render_frames_dir() + "/" + resource_name_str
            new_playback_producer = get_playback_tractor(_script_length, range_resourse_mlt_path, in_frame, out_frame)
            _player.set_producer(new_playback_producer)
            _player.seek_frame(in_frame)
            _window.pos_bar.preview_range = (in_frame, out_frame)

            _window.monitors_switcher.set_visible_child_name(MLT_PLAYER_MONITOR)
            _window.monitors_switcher.queue_draw()
            _window.preview_monitor.queue_draw()
            _window.pos_bar.widget.queue_draw()
            _window.out_view.get_buffer().set_text("success:\n" + "rendered some frames!")
            _window.media_info.set_markup("<small>" + _("Range preview for frame range ") + str(in_frame) + " - " + str(out_frame)  +"</small>")
        else:
            _window.out_view.get_buffer().set_text(fctx.error)
            _window.media_info.set_markup("<small>" + _("No Preview") +"</small>")
            _window.pos_bar.preview_range = None
            #global _current_preview_surface
            #_current_preview_surface = None
            _window.monitors_switcher.set_visible_child_name(CAIRO_DRAW_MONITOR)
            _window.monitors_switcher.queue_draw()
            _window.preview_monitor.queue_draw()

        Gdk.threads_leave()

    def frame_write_update(self, frame):
        Gdk.threads_enter()
        _window.media_info.set_markup("<small>" + _("Rendered frame ") + str(frame) + "</small>")
        Gdk.threads_leave()


class FluxityPluginRenderer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        #sys.stdout = open(userfolders.get_cache_dir() + "log_scripttool_render", 'w')
        #so = se = open(userfolders.get_cache_dir() + "log_scripttool_render", 'w', buffering=1)
        #sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
        #os.dup2(so.fileno(), sys.stdout.fileno())
    
        self.render_player = None        
        self.abort = False

        # Refuse to render into user home folder
        out_folder = _window.out_folder.get_filenames()[0] + "/"
        if out_folder == (os.path.expanduser("~") + "/"):
            return
            
        start_time = time.time()
        
        Gdk.threads_enter()
        _window.render_status_info.set_markup("")
        _window.set_widgets_sensitive(False)
        _window.render_percentage.set_sensitive(True)
        _window.render_status_info.set_sensitive(True)
        _window.render_progress_bar.set_sensitive(True)
        _window.stop_button.set_sensitive(True)
        _window.render_button.set_sensitive(False)
        _window.close_button.set_sensitive(False)
        _window.encode_settings_button.set_sensitive(False)
        _window.encode_desc.set_sensitive(False)
        _window.hamburger_launcher.widget.set_sensitive(False)
        _window.load_button.set_sensitive(False)
        Gdk.threads_leave()
        
        # Get render data.
        in_frame =  _player.producer.mark_in
        out_frame = _player.producer.mark_out
        if in_frame == -1:
            in_frame = 0
        if out_frame == -1:
            out_frame = _player.get_active_length()
        length = out_frame - in_frame
        self.length = out_frame - in_frame
        self.mark_in = in_frame
        self.mark_out = out_frame
        
        frame_name = _window.frame_name.get_text()

        buf = _window.script_view.get_buffer()
        script_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        profile_file_path = mltprofiles.get_profile_file_path(_current_profile_name)
    
        # Render frames
        fctx = fluxity.render_frame_sequence(script_text, in_frame, out_frame, out_folder, profile_file_path, self.frames_update)

        # Set GUI state and exit on error.
        if fctx.error != None:
            Gdk.threads_enter()
            _window.out_view.get_buffer().set_text(fctx.error)
            _window.media_info.set_markup("<small>" + _("No Preview") +"</small>")
            #_current_preview_surface = None
            _window.monitors_switcher.queue_draw()
            _window.preview_monitor.queue_draw()
            self.set_render_stopped_gui_state()
            Gdk.threads_leave()
            
            return
                    
        # Render video
        if _window.encode_check.get_active() == True:
            # Render consumer
            args_vals_list = toolsencoding.get_args_vals_list_for_render_data(_render_data)
            profile = mltprofiles.get_profile_for_index(_current_profile_index) 
            file_path = _render_data.render_dir + "/" +  _render_data.file_name  + _render_data.file_extension
            consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)

            # Render producer
            frame_file = fctx.priv_context.first_rendered_frame_path
            resource_name_str = utils.get_img_seq_resource_name(frame_file, True)
            range_resourse_mlt_path = out_folder + resource_name_str
            producer = mlt.Producer(profile, str(range_resourse_mlt_path))

            self.render_player = renderconsumer.FileRenderPlayer("", producer, consumer, in_frame, out_frame - 1)
            self.render_player.wait_for_producer_end_stop = False
            self.render_player.consumer_pos_stop_add = 1
            self.do_consumer_position_wait = False
            self.render_player.start()

            while self.render_player.stopped == False:
                if self.abort == True:
                    Gdk.threads_enter()
                    _window.render_percentage.set_markup("<small>" + _("Render stopped!") + "</small>")
                    _window.render_progress_bar.set_fraction(0.0)
                    Gdk.threads_leave()
                    return
                
                fraction = self.render_player.get_render_fraction()
                update_info = _("Rendering video, ") + str(int(fraction * 100)) + _("% done")
                
                print(fraction, self.render_player.producer.frame(), self.render_player.stop_frame, self.render_player.producer.get_speed(), self.render_player.consumer.is_stopped())
                
                Gdk.threads_enter()
                _window.render_percentage.set_markup("<small>" + update_info + "</small>")
                _window.render_progress_bar.set_fraction(fraction)
                Gdk.threads_leave()
                
                time.sleep(0.3)

        Gdk.threads_enter()
        _window.render_percentage.set_markup("<small>" + _("Render complete!") + "</small>")
        self.set_render_stopped_gui_state()
        Gdk.threads_leave()
        
    def frames_update(self, frame):
        if frame - self.mark_in < 0:
            frame = self.length # hack fix, producer suddenly changes the frame it thinks it is in
        else:
            frame = frame - self.mark_in # producer returns original clip frames
        
        update_info = _("Writing clip frame: ") + str(frame) + "/" +  str(self.length)

        Gdk.threads_enter()
        _window.render_percentage.set_markup("<small>" + update_info + "</small>")
        _window.render_progress_bar.set_fraction(float(frame + 1)/float(self.length))
        Gdk.threads_leave()

    def abort_render(self):
        self.abort = True

        if self.script_renderer != None:
             self.script_renderer.abort_rendering()

        self.shutdown()
                         
        _window.render_percentage.set_markup("<small>" + _("Render stopped!") + "</small>")
        self.set_render_stopped_gui_state()

    def set_render_stopped_gui_state(self):
        _window.render_progress_bar.set_fraction(0.0)
        _window.update_render_status_info()
        _window.stop_button.set_sensitive(False)
        _window.set_widgets_sensitive(True)
        _window.close_button.set_sensitive(True)
        _window.hamburger_launcher.widget.set_sensitive(True)
        _window.load_button.set_sensitive(True)
        if _window.encode_check.get_active() == True:
            _window.encode_settings_button.set_sensitive(True)
            _window.encode_desc.set_sensitive(True)

    def shutdown(self):
        if self.frames_range_writer != None:
            self.frames_range_writer.shutdown()
        
        if self.render_player != None:
            self.render_player.shutdown()        





