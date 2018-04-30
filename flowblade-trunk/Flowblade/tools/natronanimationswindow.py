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

import threading
import subprocess

import guicomponents
import guiutils
import natronanimations
import propertyedit
import propertyeditorbuilder
import respaths
import toolguicomponents
import utils

_animation_instance = None
_window = None
_animations_menu = Gtk.Menu()

def launch_tool_window():
    global _window
    _window = NatronAnimatationsToolWindow()

class NatronAnimatationsToolWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        #self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowbladetoolicon.png")
        self.set_icon(app_icon)

        # Animation selector menu launcher
        self.animation_label = Gtk.Label(natronanimations.get_default_animation_instance().info.name)
        self.present_event_box = Gtk.EventBox()
        self.present_event_box.add(self.animation_label)
        self.present_event_box.connect("button-press-event", animations_menu_launched)
        self.script_menu = toolguicomponents.PressLaunch(animations_menu_launched)

        selector_row = Gtk.HBox(False, 2)
        selector_row.pack_start(self.present_event_box, False, False, 0)
        selector_row.pack_start(self.script_menu.widget, False, False, 0)
        
        self.edit_panel = Gtk.VBox(False, 2)
        self.edit_panel.pack_start(Gtk.Label("Hello, Natron"), False, False, 0)

        # Build window
        left_panel = Gtk.VBox(False, 2)
        left_panel.pack_start(selector_row, False, False, 0)
        #left_panel.pack_start(self.script_menu.widget, False, False, 0)
        left_panel.pack_start(self.edit_panel, False, False, 0)
        
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
        render_vbox.pack_start(encode_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(out_folder_row, False, False, 0)
        render_vbox.pack_start(Gtk.Label(), True, True, 0)
        render_vbox.pack_start(render_status_row, False, False, 0)
        render_vbox.pack_start(render_row, False, False, 0)
        render_vbox.pack_start(guiutils.pad_label(24, 24), False, False, 0)

        # Build window
        pane = Gtk.HBox(False, 2)
        pane.pack_start(left_panel, False, False, 0)
        pane.pack_start(render_vbox, False, False, 0)
        
        align = guiutils.set_margins(pane, 12, 12, 12, 12)



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

        # We are using existing property edit code to create value editors.
        # We will need present a lot of dummy data and monkeypatch objects to make that 
        # pipeline do our bidding for natron animations value editing.
        clip = None
        filter_index = -1
        track = None
        clip_index = -1
        
        global _animation_instance
        _animation_instance = natronanimations.get_default_animation_instance() # This duck types for mltfilters.FilterObject
        
        editable_properties = propertyedit.get_filter_editable_properties(clip, _animation_instance, filter_index, 
                                   track, clip_index, compositor_filter=False)
        
        self.editable_properties = editable_properties
        
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

                self.edit_panel.pack_start(editor_row, False, False, 0)
                if not hasattr(editor_row, "no_separator"):
                    self.edit_panel.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
        
        self.edit_panel.show_all()
        
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
 
#-------------------------------------------------- script setting and save/load
def animations_menu_launched(launcher, event):
    show_menu(event, animations_menu_item_selected)

def animations_menu_item_selected(item, animation):

    _window.preset_label.set_text(script.name)
    
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
    
# ------------------------------------------------ rendering
def render_output():
    # Write data used to modyfy rendered notron animation
    _animation_instance.write_out_modify_data(_window.editable_properties)
    
    launch_thread = NatronRenderLaunchThread()
    launch_thread.start()

#------------------------------------------------- render threads
class NatronRenderLaunchThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        b_switch = "-b"
        w_switch = "-w"
        writer = "Write1"
        range_str = _animation_instance.get_frame_range()
        render_frame = _window.get_render_frame() #/home/janne/test/natrontestout/frame###.png
        l_switch = "-l"
        param_mod_script = respaths.ROOT_PATH + "/tools/NatronRenderModify.py"
        natron_project = _animation_instance.get_project_file_path()

        print "NatronRenderer ", b_switch, w_switch , writer, range_str, render_frame, l_switch, param_mod_script, natron_project
        
        #NatronRenderer -b -w Write1 /home/janne/test/natrontestout/frame###.png -l /home/janne/test/natron/NatronRenderParams.py /home/janne/test/flowbladetext.ntp
        render_command = "NatronRenderer " + b_switch  + " " +  w_switch + " " + writer + " " + \
                         range_str  + " " +  render_frame + " " +  l_switch + " " +  param_mod_script + " " +  natron_project

        
 
 
        print "Starting Natron render, command:", render_command
        
        
        FLOG = open(utils.get_hidden_user_dir_path() + "log_natron_render", 'w')
        p = subprocess.Popen(render_command, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)
        p.wait()
        FLOG.close()

        print "Natron render done."
    
