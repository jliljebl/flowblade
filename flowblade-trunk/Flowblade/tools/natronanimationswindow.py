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


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import GObject, GLib
from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GdkX11
from gi.repository import Pango

import cairo
import locale
import md5
import mlt
import os
import pickle
import shutil
import subprocess
import sys
import threading
import time
import webbrowser

import appconsts
import atomicfile
import cairoarea
import editorstate
import editorpersistance
import gui
import guicomponents
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import natronanimations
import positionbar
import propertyedit
import propertyeditorbuilder
import renderconsumer
import respaths
import toolguicomponents
import translations
import utils


# draw params
EDIT_PANEL_WIDTH = 500
EDIT_PANEL_HEIGHT = 250

MONITOR_WIDTH = 700
MONITOR_HEIGHT = 400

# Indexes here correspond to "NatronParamFormatChoice" Param values
NATRON_DEFAULT_RENDER_FORMAT = 6
NATRON_RENDER_FORMATS = [   "PC_Video 640x480 (PC_Video)",
                            "NTSC 720x486 0.91 (NTSC)",
                            "PAL 720x576 1.09 (PAL)",
                            "NTSC_16:9 720x486 1.21 (NTSC_16:9)",
                            "PAL_16:9 720x576 1.46 (PAL_16:9)",
                            "HD_720 1280x720 (HD_720)",
                            "HD 1920x1080 (HD)",
                            "UHD_4K 3840x2160 (UHD_4K)",
                            "1K_Super_35(full-ap) 1024x778 (1K_Super_35(full-ap))",
                            "1K_Cinemascope 914x778 2.00 (1K_Cinemascope)",
                            "2K_Super_35(full-ap) 2048x1556 (2K_Super_35(full-ap))",
                            "2K_Cinemascope 1828x1556 2.00 (2K_Cinemascope)",
                            "2K_DCP 2048x1080 (2K_DCP)",
                            "4K_Super_35(full-ap) 4096x3112 (4K_Super_35(full-ap))",
                            "4K_Cinemascope 3656x3112 2.00 (4K_Cinemascope)",
                            "4K_DCP 4096x2160 (4K_DCP)",
                            "square_256 256x256 (square_256)",
                            "square_512 512x512 (square_512)",
                            "square_1K 1024x1024 (square_1K)",
                            "square_2K 2048x2048 (square_2K)" ]
        
# module global data
_animation_instance = None
_window = None
_animations_menu = Gtk.Menu()
_hamburger_menu = Gtk.Menu()
_current_preview_surface = None
_profile = None
_session_id = None

# ------------------------------------------ launch, close
def _shutdown():

    global _window
    
    _window.set_visible(False)
    _window.destroy()
    _window = None

    # Delete session folder
    shutil.rmtree(get_session_folder())
    
# ------------------------------------------ process main
def main(root_path, force_launch=False):

    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    global _session_id
    _session_id = md5.new(os.urandom(16)).hexdigest()

    # Set paths.
    respaths.set_paths(root_path)

    # Init session folders
    if os.path.exists(get_session_folder()):
        shutil.rmtree(get_session_folder())
        
    os.mkdir(get_session_folder())

    # Load editor prefs and list of recent projects
    editorpersistance.load()


    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Load aniamtions data
    natronanimations.load_animations_projects_xml()

    # Init gtk threads
    Gdk.threads_init()
    Gdk.threads_enter()

    # Set monitor sizes
    """
    scr_w = Gdk.Screen.width()
    scr_h = Gdk.Screen.height()
    editorstate.SCREEN_WIDTH = scr_w
    editorstate.SCREEN_HEIGHT = scr_h
    if editorstate.screen_size_large_height() == True and editorstate.screen_size_small_width() == False:
        global MONITOR_WIDTH, MONITOR_HEIGHT
        MONITOR_WIDTH = 650
        MONITOR_HEIGHT = 400 # initial value, this gets changed when material is loaded
    """
    
    # Request dark theme if so desired
    if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME:
            gui.apply_gtk_css()

    # We need mlt fpr profiles handling
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
    
    # Set launch profile
    profile_name = sys.argv[1].replace("_", " ") # we had underscores put in to pass as single arg
    print profile_name
    global _profile
    _profile = mltprofiles.get_profile(profile_name)
    
    global _animation_instance
    _animation_instance = natronanimations.get_default_animation_instance(_profile)
        
    global _window
    _window = NatronAnimatationsToolWindow()
    _window.pos_bar.set_dark_bg_color()

    Gtk.main()
    Gdk.threads_leave()


#----------------------------------------------- session folders and files
def get_session_folder():
    return utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/session_" + str(_session_id)
    
"""
def get_clip_frames_dir():
    return get_session_folder() + CLIP_FRAMES_DIR

def get_render_frames_dir():
    return get_session_folder() + RENDER_FRAMES_DIR
    
def get_current_frame_file():
    return get_clip_frames_dir() + "/frame" + str(_player.current_frame()) + ".png"

def get_preview_file():
    return get_session_folder() + "/" + PREVIEW_FILE
"""

# ----------------------------------------------------- tool window
class NatronAnimatationsToolWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowbladetoolicon.png")
        self.set_icon(app_icon)

        #---- LEFT PANEL
        hamburger_launcher_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger.png")
        self.hamburger_launcher = guicomponents.PressLaunch(_hamburger_launch_pressed, hamburger_launcher_surface)
        guiutils.set_margins(self.hamburger_launcher.widget, 0, 8, 0, 8)

        # Animation selector menu launcher row
        self.animation_label = Gtk.Label(_animation_instance.info.name)
        self.present_event_box = Gtk.EventBox()
        self.present_event_box.add(self.animation_label)
        self.present_event_box.connect("button-press-event", animations_menu_launched)
        self.script_menu = toolguicomponents.PressLaunch(animations_menu_launched)

        selector_row = Gtk.HBox(False, 2)
        selector_row.pack_start(self.hamburger_launcher.widget, False, False, 0)
        selector_row.pack_start(self.present_event_box, False, False, 0)
        selector_row.pack_start(self.script_menu.widget, False, False, 0)
        selector_row.set_margin_top(2)
        # Edit area
        self.value_edit_frame = Gtk.Frame()
        self.value_edit_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.value_edit_frame.set_size_request(EDIT_PANEL_WIDTH+ 10, EDIT_PANEL_HEIGHT + 10)
        self.value_edit_box = None
        
        
        #---- RIGHT PANEL
        self.preview_info = Gtk.Label()
        self.preview_info.set_markup("<small>" + _("no preview") + "</small>" )
        preview_info_row = Gtk.HBox()
        preview_info_row.pack_start(self.preview_info, False, False, 0)
        preview_info_row.pack_start(Gtk.Label(), True, True, 0)
        preview_info_row.set_margin_top(6)
        preview_info_row.set_margin_bottom(8)
        preview_info_row.set_size_request(200, 10)
        
        # Monitor 
        self.preview_monitor = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_preview)

        # Position control panel
        self.pos_bar = positionbar.PositionBar(False)
        self.pos_bar.set_listener(self.position_listener)
        pos_bar_frame = Gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pos_bar_frame.set_margin_top(5)
        pos_bar_frame.set_margin_bottom(4)
        pos_bar_frame.set_margin_left(6)
        pos_bar_frame.set_margin_right(2)
                
        self.preview_button = Gtk.Button(_("Preview Frame"))
        self.preview_button.connect("clicked", lambda w: render_preview_frame())
                            
        control_panel = Gtk.HBox(False, 2)
        control_panel.pack_start(pos_bar_frame, True, True, 0)
        control_panel.pack_start(guiutils.pad_label(2, 2), False, False, 0)
        control_panel.pack_start(self.preview_button, False, False, 0)
        
        # Range setting
        in_label = Gtk.Label(_("Start:"))
        self.range_in = Gtk.SpinButton.new_with_range(1, 249, 1)
        out_label = Gtk.Label(_("End:"))
        self.range_out = Gtk.SpinButton.new_with_range(2, 250, 1)
        self.range_in.set_value(1)
        self.range_out.set_value(250)
        self.range_in.connect("value-changed", self.range_changed)
        self.range_out.connect("value-changed", self.range_changed)
        pos_label = Gtk.Label(_("Frame:"))
        self.pos_info = Gtk.Label(_("1"))

        range_row = Gtk.HBox(False, 2)
        range_row.pack_start(in_label, False, False, 0)
        range_row.pack_start(self.range_in, False, False, 0)
        range_row.pack_start(Gtk.Label(), True, True, 0)
        range_row.pack_start(pos_label, False, False, 0)
        range_row.pack_start(self.pos_info, False, False, 0)
        range_row.pack_start(Gtk.Label(), True, True, 0)
        range_row.pack_start(out_label, False, False, 0)
        range_row.pack_start(self.range_out, False, False, 0)
        range_row.set_margin_bottom(24)
        range_row.set_margin_left(5)

        # Render panel
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

        format_label = Gtk.Label(_("Natron Render Format:"))
        self.format_selector = Gtk.ComboBoxText() # filled later when current sequence known
        for format_desc in NATRON_RENDER_FORMATS:
            self.format_selector.append_text(format_desc)
        self.format_selector.set_active(NATRON_DEFAULT_RENDER_FORMAT)

        format_select_row = Gtk.HBox(False, 2)
        format_select_row.pack_start(format_label, False, False, 0)
        format_select_row.pack_start(guiutils.pad_label(12, 2), False, False, 0)
        format_select_row.pack_start(self.format_selector, False, False, 0)
        format_select_row.set_margin_top(24)

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
        #self.stop_button.connect("clicked", lambda w:abort_render())
        self.render_button = guiutils.get_sized_button(_("Render"), 100, 32)
        self.render_button.connect("clicked", lambda w:render_output())

        render_row = Gtk.HBox(False, 2)
        render_row.pack_start(self.render_progress_bar, True, True, 0)
        render_row.pack_start(guiutils.pad_label(12, 2), False, False, 0)
        render_row.pack_start(self.stop_button, False, False, 0)
        render_row.pack_start(self.render_button, False, False, 0)

        render_vbox = Gtk.VBox(False, 2)
        render_vbox.pack_start(encode_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(out_folder_row, False, False, 0)
        render_vbox.pack_start(format_select_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(render_status_row, False, False, 0)
        render_vbox.pack_start(render_row, False, False, 0)
        render_vbox.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        render_vbox.set_margin_left(8)

        # Bottomrow
        self.load_anim = Gtk.Button(_("Load Animation"))
        self.load_anim.connect("clicked", lambda w:load_script_dialog(_load_script_dialog_callback))
        self.save_anim = Gtk.Button(_("Save Animation"))
        self.save_anim.connect("clicked", lambda w:save_script_dialog(_save_script_dialog_callback))

        exit_b = guiutils.get_sized_button(_("Close"), 150, 32)
        exit_b.connect("clicked", lambda w:_shutdown())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(self.load_anim, False, False, 0)
        editor_buttons_row.pack_start(self.save_anim, False, False, 0)
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)
        
        # Build window
        left_panel = Gtk.VBox(False, 2)
        left_panel.pack_start(selector_row, False, False, 0)
        left_panel.pack_start(self.value_edit_frame, True, True, 0)

        right_panel = Gtk.VBox(False, 0)
        right_panel.pack_start(preview_info_row, False, False, 0)
        right_panel.pack_start(self.preview_monitor, False, False, 0)
        right_panel.pack_start(control_panel, False, False, 0)
        right_panel.pack_start(range_row, False, False, 0)
        right_panel.pack_start(render_vbox, True, True, 0)
    
        right_panel.set_margin_left(4)
        
        sides_pane = Gtk.HBox(False, 2)
        sides_pane.pack_start(left_panel, False, False, 0)
        sides_pane.pack_start(right_panel, False, False, 0)

        pane = Gtk.VBox(False, 2)
        pane.pack_start(sides_pane, False, False, 0)
        pane.pack_start(editor_buttons_row, False, False, 0)
        
        align = guiutils.set_margins(pane, 2, 12, 12, 12)

        # Connect global key listener
        #self.connect("key-press-event", _global_key_down_listener)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Natron Animations"))
        self.set_position(Gtk.WindowPosition.CENTER)
        #self.set_widgets_sensitive(False)
        self.show_all()
        self.set_resizable(False)
        #self.set_active_state(False)

        self.update_render_status_info()
        self.change_animation()

    def change_animation(self):

        # ---------------- PROPERTY EDITING
        # We are using existing property edit code to create value editors.
        # We will need present a lot of dummy data and monkeypatch objects to make that 
        # pipeline do our bidding for natron animations value editing.
        clip = None
        filter_index = -1
        track = None
        clip_index = -1

        editable_properties = propertyedit.get_filter_editable_properties(clip, _animation_instance, filter_index, 
                                   track, clip_index, compositor_filter=False)
        
        self.editable_properties = editable_properties

        edit_panel = Gtk.VBox(False, 2)
        edit_panel.set_size_request(EDIT_PANEL_WIDTH, EDIT_PANEL_HEIGHT)
        guiutils.set_margins(edit_panel, 4, 4, 4, 4)

        if len(editable_properties) > 0:
            # Create editor row for each editable property
            for ep in editable_properties:

                # We are not interfacing with mlt objects or clip's filter arrays
                # and we need make functions accessing those no-ops.
                # We are only interested in saving value as string and then later interpreting
                # it somehow to use as input when modifying natron project.
                self.modify_editable_properties(ep)
                
                editor_row = propertyeditorbuilder.get_editor_row(ep)
                if editor_row == None:
                    continue

                # Set keyframe editor widget to be updated for frame changes if such is created 
                try:
                    editor_type = ep.args[propertyeditorbuilder.EDITOR]
                except KeyError:
                    editor_type = propertyeditorbuilder.SLIDER # this is the default value

                edit_panel.pack_start(editor_row, False, False, 0)
                if not hasattr(editor_row, "no_separator"):
                    edit_panel.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
        
        edit_panel.pack_start(Gtk.Label(), True, True, 0)
        edit_panel.show_all()
    
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.add_with_viewport(edit_panel)
        scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_window.show_all()

        if self.value_edit_box != None:
            self.value_edit_frame.remove(self.value_edit_box)
        self.value_edit_frame.add(scroll_window)

        self.value_edit_box = scroll_window
    
        # ---------------- GUI UPDATES
        global _current_preview_surface
        _current_preview_surface = None
        
        self.animation_label.set_text(_animation_instance.info.name)
        self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>")
        self.pos_bar.update_display_from_producer(_animation_instance) # duck typing as mlt.Producer for pos bar, need data methods are in NatronAnimationInstance
        self.range_in.set_value(_animation_instance.range_in)
        self.range_out.set_value(_animation_instance.range_out)
        _animation_instance.current_frame = _animation_instance.range_in
        self.set_position(_animation_instance.range_in)
        self.preview_monitor.queue_draw()

    def position_listener(self, normalized_pos, length):
        new_pos = int(normalized_pos * (length - 1)) + _animation_instance.range_in # -1 to compensate that Natron animations start from frame 1, not frame 0, and we need to keep doing the same here
        self.set_position(new_pos)
        self.pos_bar.widget.queue_draw()
        
    def set_position(self, new_pos):
        _animation_instance.current_frame = new_pos
        self.pos_info.set_text(str(_animation_instance.current_frame))

    def range_changed(self, widget):
        if widget == self.range_in:
            _animation_instance.range_in = int(widget.get_value())
        else:
            _animation_instance.range_out = int(widget.get_value())
            
        if _animation_instance.range_in > _animation_instance.range_out:
            _animation_instance.range_out = _animation_instance.range_in + 1
            self.range_out.set_value(_animation_instance.range_out) 

        self.pos_bar.update_display_from_producer(_animation_instance)
        
        if _animation_instance.current_frame < _animation_instance.range_in:
            _animation_instance.current_frame = _animation_instance.range_in
        
        norm_pos = float(_animation_instance.current_frame - _animation_instance.range_in) / float(_animation_instance.get_length())
        self.pos_bar.set_normalized_pos(norm_pos)
        
        self.set_position(_animation_instance.current_frame)
            
    def folder_selection_changed(self, chooser):
        self.update_render_status_info()

    def update_encode_sensitive(self):
        pass

    def _encode_settings_clicked(self):
        pass
 
    def update_render_status_info(self):

        
        if self.out_folder.get_filename() == None:
            self.render_status_info.set_markup("<small>" + self.status_no_render  + "</small>")
            self.render_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
        else:
            length = 250
            video_info = _(" no video file")
            if self.encode_check.get_active() == True:
                video_info = _(" render video file")
            info_str = str(length) + _(" frame(s),") + video_info
            self.render_status_info.set_markup("<small>" + info_str +  "</small>")
            self.render_button.set_sensitive(True)
            self.stop_button.set_sensitive(True)

    def modify_editable_properties(self, ep):
        # We are not interfacing with mlt objects or clip's filter arrays
        # and we need make functions accessing those no-ops.
        # We are only interested in saving value as string and then later interpreting
        # it somehow to use as input when modifying natron project
        ep.write_mlt_property_str_value = self._no_op
        ep.write_filter_object_property = self._no_op
 
    def get_render_frame(self):
        folder = self.out_folder.get_filename()
        frame = self.frame_name.get_text() + "####.png"
        return folder + "/" + frame
        
    def _no_op(self, str_value):
        pass
 
    def _draw_preview(self, event, cr, allocation):
        x, y, w, h = allocation

        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()
            
        if _current_preview_surface != None:
            sw = _current_preview_surface.get_width()
            sh = _current_preview_surface.get_height()
            s_aspect = float(sw) / float(sh)
            monitor_aspect = float(w) / float(h)
            
            if s_aspect > monitor_aspect: # letterbox
                scale = float(w) / float(sw)
                mx = 0
                my = h / 2.0 - (scale * sh) / 2.0
            else: # pillarbox
                scale = float(h) / float(sh)
                mx =  w / 2.0 - (scale * sw) / 2.0
                my = 0

            cr.scale(scale, scale)  # uhh... pixel aspect ratios ?
            cr.set_source_surface(_current_preview_surface, mx, my)
            cr.paint()



#-------------------------------------------------- GUI actions
def animations_menu_launched(launcher, event):
    show_menu(event, animations_menu_item_selected)

def animations_menu_item_selected(item, animation):
    #_window.preset_label.set_text(animation.name)
    
    global _animation_instance
    _animation_instance = animation.get_instance(_profile)

    _window.change_animation()

def show_menu(event, callback):
    # Remove current items
    items = _animations_menu.get_children()
    for item in items:
        _animations_menu.remove(item)

    animations_groups = natronanimations.get_animations_groups()
    for a_group in animations_groups:
        group_name, group = a_group
        group_item = Gtk.MenuItem(group_name)
        #group_item.connect("activate", callback, i)
        _animations_menu.append(group_item)
        sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_menu)

        for natron_animation in group:
            natron_animation_item = Gtk.MenuItem(natron_animation.name)
            sub_menu.append(natron_animation_item)
            natron_animation_item.connect("activate", callback, natron_animation)

    _animations_menu.show_all()
    _animations_menu.popup(None, None, None, None, event.button, event.time)

def _hamburger_launch_pressed(widget, event):
    menu = _hamburger_menu
    guiutils.remove_children(menu)
    
    menu.add(_get_menu_item(_("Load Animation") + "...", _hamburger_menu_callback, "load" ))
    menu.add(_get_menu_item(_("Save Animation") + "...", _hamburger_menu_callback, "save" ))
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Natron Webpage"), _hamburger_menu_callback, "web" ))
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Close"), _hamburger_menu_callback, "close" ))
    
    menu.popup(None, None, None, None, event.button, event.time)

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
    
def _hamburger_menu_callback(widget, msg):
    if msg == "load":
        _load_script_dialog(_load_animation_dialog_callback)
    elif msg == "save":     
        _save_animation_dialog(_save_animation_dialog_callback)
    elif msg == "close":
        _shutdown()
    elif msg == "web":
        webbrowser.open(url="https://natron.fr/", new=0, autoraise=True)



def _save_animation_dialog(callback):
    dialog = Gtk.FileChooserDialog(_("Save Natron Animation Values As"), None, 
                                   Gtk.FileChooserAction.SAVE, 
                                   (_("Cancel").encode('utf-8'), Gtk.ResponseType.CANCEL,
                                   _("Save").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name("animation")
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def _save_animation_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        file_path = dialog.get_filenames()[0]
        # Write out file.
        with atomicfile.AtomicFileWriter(file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(_animation_instance, write_file)
        dialog.destroy()
    else:
        dialog.destroy()

def _load_script_dialog(callback):
    dialog = Gtk.FileChooserDialog(_("Load Animation Data"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel").encode('utf-8'), Gtk.ResponseType.CANCEL,
                                    _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()
    
def _load_animation_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filename = dialog.get_filenames()[0]
        # Load project object
        f = open(filename)
        load_instance = pickle.load(f)
        global _animation_instance
        _animation_instance = load_instance
        _window.change_animation()
        dialog.destroy()
    else:
        dialog.destroy()


# ------------------------------------------------ rendering
def render_output():
    # Write data used to modyfy rendered notron animation
    _animation_instance.write_out_modify_data(_window.editable_properties, _session_id, _window.format_selector.get_active())
    _window.render_percentage.set_markup("<small>" + _("Render starting...") + "</small>")

    launch_thread = NatronRenderLaunchThread()
    launch_thread.start()

    global _progress_updater
    _progress_updater = ProgressUpdaterThread()
    _progress_updater.start()

def render_preview_frame():
    global _progress_updater
    _progress_updater = None

    _animation_instance.write_out_modify_data(_window.editable_properties, _session_id, _window.format_selector.get_active())
    
    launch_thread = NatronRenderLaunchThread(True)
    launch_thread.start()
    

#------------------------------------------------- render threads
class NatronRenderLaunchThread(threading.Thread):

    def __init__(self, is_preview=False):
        threading.Thread.__init__(self)
        self.is_preview = is_preview

    def run(self):
        start_time = time.time()
        
        b_switch = "-b"
        w_switch = "-w"
        writer = "Write1"
        if self.is_preview == False:
            range_str = _animation_instance.get_frame_range_str()
            render_frame = _window.get_render_frame()
        else:
            range_str = str(_animation_instance.frame())
            render_frame = utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/session_" + _session_id + "/preview####.png"
            print render_frame
            Gdk.threads_enter()
            _window.preview_info.set_markup("<small>" + _("Rendering preview for frame ") + range_str + "..." + "</small>") 
            Gdk.threads_leave()
                    
        l_switch = "-l"
        param_mod_script = respaths.ROOT_PATH + "/tools/NatronRenderModify.py"
        natron_project = _animation_instance.get_project_file_path()
        
        render_command = "NatronRenderer " + b_switch  + " " +  w_switch + " " + writer + " " + \
                         range_str  + " " +  render_frame + " " +  l_switch + " " +  param_mod_script + " " +  natron_project


        print "Starting Natron render, command: ", render_command

        FLOG = open(utils.get_hidden_user_dir_path() + "log_natron_render", 'w')
        p = subprocess.Popen(render_command, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)
        p.wait()
        FLOG.close()

        if _progress_updater != None:
            _progress_updater.stop_thread()

        # Render complete GUI updates
        Gdk.threads_enter()
        
        if self.is_preview == False:
            _window.render_percentage.set_markup("<small>" + _("Render complete.") + "</small>")
        else:
            render_time = time.time() - start_time
            time_str = "{0:.2f}".format(round(render_time,2))
            _window.preview_info.set_markup("<small>" + _("Preview for frame: ") + range_str + \
                _(", render time: ") + time_str +  "</small>" )

            global _current_preview_surface
            preview_frame_path = utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/session_" + _session_id + "/preview" + str(_animation_instance.frame()).zfill(4) +  ".png"
            _current_preview_surface = cairo.ImageSurface.create_from_png(preview_frame_path)
            _window.preview_monitor.queue_draw()
            
        Gdk.threads_leave()
        
        print "Natron render done."


class ProgressUpdaterThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.running = True
        self.length = _animation_instance.get_length()

        # This is a mucho hacky, see if we can get some events somehow
        render_ongoing = False # the method we're using needs 
        while self.running == True:
            try:
                count = self.file_lines() - 7
                if count > 0:
                    if count < 8: # if we get more then 8 frames before first update were f...cked
                        render_ongoing = True
                    
                    if render_ongoing == True:
                        update_info = _("Writing clip frame: ") + str(count) + "/" +  str(self.length)

                        Gdk.threads_enter()
                        _window.render_percentage.set_markup("<small>" + update_info + "</small>")
                        _window.render_progress_bar.set_fraction(float(count + 1)/float(self.length))
                        Gdk.threads_leave()
                
                time.sleep(0.3)
            except:
                pass
                #print "Except"
        print "ProgressUpdaterThread stpped"

    def file_lines(self):
        with open(utils.get_hidden_user_dir_path() + "log_natron_render", "r") as f:
            for i, l in enumerate(f):
                pass
        return i + 1
    
    def stop_thread(self):
        self.running = False
        global _progress_updater
        _progress_updater = None # disconnect this
