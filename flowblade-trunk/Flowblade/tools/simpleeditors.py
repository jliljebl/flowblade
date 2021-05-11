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
Module for creating simple editors for e.g. container clips program data.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import GObject
import cairo
import copy
import time

import cairoarea
import editorstate
import dialogutils
import gui
import guiutils
import positionbar
import respaths

# NOTE: These need to correspond exacty with fluxity.FluxityContext.<editor> values because we do not want to import anything into fluxity.py.    
SIMPLE_EDITOR_STRING = 0
SIMPLE_EDITOR_VALUE = 1
SIMPLE_EDITOR_FLOAT = 2
SIMPLE_EDITOR_INT = 3
SIMPLE_EDITOR_COLOR = 4
SIMPLE_EDITOR_FILE_PATH = 5
SIMPLE_EDITOR_OPTIONS = 6
SIMPLE_EDITOR_CHECK_BOX = 7
SIMPLE_EDITOR_FLOAT_RANGE = 8
SIMPLE_EDITOR_INT_RANGE = 9

NO_PREVIEW_FILE = "fallback_thumb.png"

# Gtk.Adjustments require some bounds.
MIN_VAL = -pow(2, 63) 
MAX_VAL = pow(2, 63)

SIMPLE_EDITOR_LEFT_WIDTH = 150
MONITOR_WIDTH = 600
MONITOR_HEIGHT = 360

# -------------------------------------------------------------------- Blender container clip program values edit
def show_blender_container_clip_program_editor(callback, clip, container_action, program_info_json):
    editor_window = BlenderProgramEditorWindow(callback, clip, container_action, program_info_json)


class BlenderProgramEditorWindow(Gtk.Window):
    def __init__(self, callback, clip, container_action, program_info_json):
        
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e: self.cancel())
        
        self.callback = callback
        self.clip = clip
        self.container_action = container_action
        self.orig_program_info_json = copy.deepcopy(program_info_json) # We need to sabvre this for 'Cancel'because doing a preview updates edited values
                                                                       # in containeractions.BlenderContainerActions.render_blender_preview().
         
        self.preview_frame = -1 # -1 used as flag that no preview renders ongoing and new one can be started
         
        # Create panels for objects
        editors = []
        blender_objects = program_info_json["objects"]
        materials = program_info_json["materials"]
        curves = program_info_json["curves"]
        
        self.editors = editors
        
        objs_panel = _get_panel_and_create_editors(blender_objects, _("Objects"), editors)
        materials_panel = _get_panel_and_create_editors(materials, _("Materials"), editors)
        curves_panel = _get_panel_and_create_editors(curves, _("Curves"), editors)
        
        pane = Gtk.VBox(False, 2)
        if objs_panel != None:
            pane.pack_start(objs_panel, False, False, 0)
        if materials_panel != None:
            pane.pack_start(materials_panel, False, False, 0)
        if curves_panel != None:
            pane.pack_start(curves_panel, False, False, 0)
        
        # Put in scrollpane if too many editors for screensize.
        n_editors = len(editors)
        add_scroll = False
        if editorstate.screen_size_small_height() == True and n_editors > 4:
            add_scroll = True
            h = 500
        elif editorstate.screen_size_small_height() == True and editorstate.screen_size_large_height() == False and n_editors > 5:
            add_scroll = True
            h = 600
        elif editorstate.screen_size_large_height() == True and n_editors > 6:
            add_scroll = True
            h = 700
            
        if add_scroll == True:
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sw.add(pane)
            sw.set_size_request(400, h)

        if add_scroll == True:
            editors_panel = sw
        else:
            editors_panel = pane

        cancel_b = guiutils.get_sized_button(_("Cancel"), 150, 32)
        cancel_b.connect("clicked", lambda w: self.cancel())
        save_b = guiutils.get_sized_button(_("Save Changes"), 150, 32)
        save_b.connect("clicked", lambda w: self.save())
        
        buttons_box = Gtk.HBox(False, 2)
        buttons_box.pack_start(Gtk.Label(), True, True, 0)
        buttons_box.pack_start(cancel_b, False, False, 0)
        buttons_box.pack_start(save_b, False, False, 0)

        self.preview_panel = PreviewPanel(self, clip)
        
        preview_box = Gtk.VBox(False, 2)
        preview_box.pack_start(self.preview_panel, True, True, 0)
        preview_box.pack_start(guiutils.pad_label(2, 24), False, False, 0)
        preview_box.pack_start(buttons_box, False, False, 0)

        main_box = Gtk.HBox(False, 2)
        main_box.pack_start(guiutils.get_named_frame(_("Editors"), editors_panel), False, False, 0)
        main_box.pack_start(guiutils.get_named_frame(_("Preview"), preview_box), False, False, 0)

        alignment = guiutils.set_margins(main_box, 8,8,8,8) #dialogutils.get_default_alignment(main_box)

        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(_("Blender Project Edit - ") + self.container_action.container_data.get_program_name() + ".blend")
        self.set_resizable(False)

        self.add(alignment)
        self.show_all()

    def render_preview_frame(self):
        if self.preview_frame != -1:
            return # There already is preview render ongoing.
        self.start_time = time.monotonic()

        self.preview_panel.preview_info.set_markup("<small>Rendering preview...</small>")
        self.preview_frame = int(self.preview_panel.frame_select.get_value() + self.clip.clip_in)
        self.container_action.render_blender_preview(self, self.editors, self.preview_frame)

    def get_preview_file(self):
        filled_number_str = str(self.preview_frame).zfill(4)
        preview_file = self.container_action.get_preview_media_dir() + "/frame" + filled_number_str + ".png"

        return preview_file

    def preview_render_complete(self):
        self.preview_panel.preview_surface = cairo.ImageSurface.create_from_png(self.get_preview_file())
        self.preview_frame = -1
        
        render_time = time.monotonic() - self.start_time
        time_str = "{0:.2f}".format(round(render_time,2))
        frame_str = str(int(self.preview_panel.frame_select.get_value()))
        self.preview_panel.preview_info.set_markup("<small>" + _("Preview for frame: ") +  frame_str + _(", render time: ") + time_str +  "</small>")
        self.preview_panel.preview_monitor.queue_draw()

    def cancel(self):
        self.callback(False, self, self.editors, self.orig_program_info_json)

    def save(self):
        self.callback(True, self, self.editors, None)

def _get_panel_and_create_editors(objects, pane_title, editors):
    panels = []
    for obj in objects:
        # object is [name, type, editors_list] see blenderprojectinit.py
        editors_data_list = obj[2]
        editors_panel = Gtk.VBox(True, 2)
        for editor_data in editors_data_list:
            prop_path, label_text, tooltip, editor_type, value = editor_data
            editor_type = int(editor_type)
            editor = _get_editor(editor_type, (obj[0], prop_path), label_text, value, tooltip)
            editor.blender_editor_data = editor_data # We need this the later to apply the changes.
            editors.append(editor)
            
            editors_panel.pack_start(editor, False, False, 0)

        if len(editors_data_list) > 0:
            if len(obj[1]) > 0:
                panel_text = obj[0] + " - " + obj[1]
            else:
                panel_text = obj[0] 
            panel = guiutils.get_named_frame(panel_text, editors_panel)
            panels.append(panel)
    
    pane = Gtk.VBox(False, 2)
    for panel in panels:
        pane.pack_start(panel, False, False, 0)
    
    if len(panels) == 0:
        return None
        
    return guiutils.get_named_frame(pane_title, pane)
     
def get_simple_editor_selector(active_index, callback): # used in containerprogramedit.py to create editor for blender programs

    editor_select = Gtk.ComboBoxText()
    editor_select.append_text(_("String")) # these corespond values above
    editor_select.append_text(_("Value"))
    editor_select.append_text(_("Float"))
    editor_select.append_text(_("Int"))
    editor_select.append_text(_("Color"))
    editor_select.set_active(active_index)
    if callback != None:
        editor_select.connect("changed", callback)
    
    return editor_select



# -------------------------------------------------------------------- Media Plugin timeline clip editor
def show_fluxity_container_clip_program_editor(callback, clip, container_action, script_data_object):
    editor_window = FluxityScriptEditorWindow(callback, clip, container_action, script_data_object)

class FluxityScriptEditorWindow(Gtk.Window):
    def __init__(self, callback, clip, container_action, script_data_object):
        
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e: self.cancel())
        
        self.callback = callback
        self.clip = clip
        self.container_action = container_action
        self.script_data_object = copy.deepcopy(script_data_object)
         
        self.preview_frame = -1 # -1 used as flag that no preview renders ongoing and new one can be started
         
        # Create panels for objects
        self.editor_widgets = []
        editors_list = self.script_data_object["editors_list"]

        for editor_data in editors_list:
            name, type, value = editor_data
            editor_type = int(type)
            self.editor_widgets.append(_get_editor(editor_type, name, name, value, ""))

        editors_v_panel = Gtk.VBox(True, 2)
        for w in self.editor_widgets:        
            editors_v_panel.pack_start(w, False, False, 0)

        pane = Gtk.VBox(False, 2)
        if len(self.editor_widgets) != 0:
            pane.pack_start(editors_v_panel, False, False, 0)
        else:
            pane.pack_start(Gtk.Label(_("No Editors for this script")), False, False, 0)
            
        # Put in scrollpane if too many editors for screensize.
        n_editors = len(self.editor_widgets )
        add_scroll = False
        if editorstate.screen_size_small_height() == True and n_editors > 4:
            add_scroll = True
            h = 500
        elif editorstate.screen_size_small_height() == True and editorstate.screen_size_large_height() == False and n_editors > 5:
            add_scroll = True
            h = 600
        elif editorstate.screen_size_large_height() == True and n_editors > 6:
            add_scroll = True
            h = 700
            
        if add_scroll == True:
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sw.add(pane)
            sw.set_size_request(400, h)

        if add_scroll == True:
            editors_panel = sw
        else:
            editors_panel = pane

        cancel_b = guiutils.get_sized_button(_("Cancel"), 150, 32)
        cancel_b.connect("clicked", lambda w: self.cancel())
        save_b = guiutils.get_sized_button(_("Save Changes"), 150, 32)
        save_b.connect("clicked", lambda w: self.save())
        
        buttons_box = Gtk.HBox(False, 2)
        buttons_box.pack_start(Gtk.Label(), True, True, 0)
        buttons_box.pack_start(cancel_b, False, False, 0)
        buttons_box.pack_start(save_b, False, False, 0)

        self.preview_panel = PreviewPanel(self, clip)
        
        preview_box = Gtk.VBox(False, 2)
        preview_box.pack_start(self.preview_panel, True, True, 0)
        preview_box.pack_start(guiutils.pad_label(2, 24), False, False, 0)
        preview_box.pack_start(buttons_box, False, False, 0)

        main_box = Gtk.HBox(False, 2)
        main_box.pack_start(guiutils.get_named_frame(_("Editors"), editors_panel), False, False, 0)
        main_box.pack_start(guiutils.get_named_frame(_("Preview"), preview_box), False, False, 0)

        alignment = guiutils.set_margins(main_box, 8,8,8,8) #dialogutils.get_default_alignment(main_box)

        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(_("Media Plugin Values Edit - ") + self.container_action.container_data.get_program_name())
        self.set_resizable(False)

        self.add(alignment)
        self.show_all()

    def render_preview_frame(self):
        if self.preview_frame != -1:
            return # There already is preview render ongoing.
        self.start_time = time.monotonic()

        self.preview_panel.preview_info.set_markup("<small>Rendering preview...</small>")
        self.preview_frame = int(self.preview_panel.frame_select.get_value() + self.clip.clip_in)
        self.container_action.render_fluxity_preview(self, self.editor_widgets, self.preview_frame)

    def get_preview_file(self):
        preview_file = self.container_action.get_preview_media_dir() + "/preview.png"

        return preview_file

    def preview_render_complete(self):
        self.preview_panel.preview_surface = cairo.ImageSurface.create_from_png(self.get_preview_file())
        self.preview_frame = -1
        
        render_time = time.monotonic() - self.start_time
        time_str = "{0:.2f}".format(round(render_time,2))
        frame_str = str(int(self.preview_panel.frame_select.get_value()))
        self.preview_panel.preview_info.set_markup("<small>" + _("Preview for frame: ") +  frame_str + _(", render time: ") + time_str +  "</small>")
        self.preview_panel.preview_monitor.queue_draw()

    def preview_render_complete_error(self, error_msg):
        self.preview_panel.preview_surface = None
        self.preview_frame = -1
        
        self.preview_panel.preview_info.set_markup("<small>" + _("Error in Preview for frame: ") +  error_msg +  "</small>")
        self.preview_panel.preview_monitor.queue_draw()
        
    def cancel(self):
        self.callback(False, self, self.editor_widgets, self.orig_program_info_json)

    def save(self):
        self.callback(True, self, self.editor_widgets, None)

# -------------------------------------------------------------------- Media Plugin add editors
def create_add_media_plugin_editors(script_data_object):
    global SIMPLE_EDITOR_LEFT_WIDTH
    SIMPLE_EDITOR_LEFT_WIDTH = 200
    
    editors_object = AddMediaPluginEditors(script_data_object)
    return editors_object

class AddMediaPluginEditors:
    def __init__(self, script_data_object):
        self.script_data_object = copy.deepcopy(script_data_object)
         
        self.preview_frame = -1 # -1 used as flag that no preview renders ongoing and new one can be started
         
        # Create panels for objects
        self.editor_widgets = []
        editors_list = self.script_data_object["editors_list"]

        for editor_data in editors_list:
            name, type, value = editor_data
            editor_type = int(type)
            self.editor_widgets.append(_get_editor(editor_type, name, name, value, ""))

        editors_v_panel = Gtk.VBox(True, 2)
        for w in self.editor_widgets:        
            editors_v_panel.pack_start(w, False, False, 0)

        pane = Gtk.VBox(False, 2)
        if len(self.editor_widgets) != 0:
            pane.pack_start(editors_v_panel, False, False, 0)
        else:
            pane.pack_start(Gtk.Label(_("No Editors for this script")), False, False, 0)
            
        # Put in scrollpane if too many editors for screensize.
        n_editors = len(self.editor_widgets )
        add_scroll = False
        if editorstate.screen_size_small_height() == True and n_editors > 4:
            add_scroll = True
        elif editorstate.screen_size_small_height() == True and editorstate.screen_size_large_height() == False and n_editors > 5:
            add_scroll = True
        elif editorstate.screen_size_large_height() == True and n_editors > 6:
            add_scroll = True

        if add_scroll == True:
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sw.add(pane)

        if add_scroll == True:
            editors_panel = sw
        else:
            editors_panel = pane

        self.editors_panel = editors_panel

def get_editors_data_as_editors_list(editor_widgets):
    new_editors_list = [] # This is the editors list in format created in
                          # fluxity.FluxityContext.get_script_data()
    for editor in editor_widgets:
        value = editor.get_value()
        if editor.editor_type == SIMPLE_EDITOR_COLOR:
            value = editor.get_value_as_color_tuple()
        new_editor = [editor.id_data, editor.editor_type, value]
        new_editors_list.append(new_editor)
    
    return new_editors_list
        


# ----------------------------------------------------------------------- editors
def _get_editor(editor_type, id_data, label_text, value, tooltip):
    if editor_type == SIMPLE_EDITOR_STRING:
        editor = TextEditor(id_data, label_text, value, tooltip)
        editor.return_quoted_string = True
        editor.editor_type = SIMPLE_EDITOR_STRING
        return editor
    elif editor_type == SIMPLE_EDITOR_VALUE:
        editor = TextEditor(id_data, label_text, value, tooltip)
        editor.editor_type = SIMPLE_EDITOR_VALUE
        return editor
    elif editor_type == SIMPLE_EDITOR_FLOAT:
        return FloatEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_INT:
        return IntEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_COLOR:
        return ColorEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_FILE_PATH:
        return FilePathEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_OPTIONS:
        return OptionsEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_CHECK_BOX:
        return CheckboxEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_FLOAT_RANGE:
        return FloatEditorRange(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_INT_RANGE:
        return IntEditorRange(id_data, label_text, value, tooltip)

        
class AbstractSimpleEditor(Gtk.HBox):
    
    def __init__(self, id_data, tooltip):
        GObject.GObject.__init__(self)
        self.id_data = id_data # the data needed to target edited values on correct object.
        self.tooltip = tooltip
        self.editor_type = -1
        
    def build_editor(self, label_text, widget):
        widget.set_tooltip_text (self.tooltip)
        left_box = guiutils.get_left_justified_box([Gtk.Label(label=label_text)])
        left_box.set_size_request(SIMPLE_EDITOR_LEFT_WIDTH, guiutils.TWO_COLUMN_BOX_HEIGHT)
        self.pack_start(left_box, False, True, 0)
        self.pack_start(widget, True, True, 0)


class TextEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        
        self.return_quoted_string = False # This is set elsewhere if needed
        
        # If input value has quotes we need to strip them before editing
        # and put back when value is asked for.
        if value[0:1] == '"':
            value = value[1:len(value) - 1]

        self.entry = Gtk.Entry()
        self.entry.set_text(value)
        
        self.build_editor(label_text, self.entry)
        #self.editor_type is set in _get_editor() above.

    def get_value(self):
        value = self.entry.get_text()
        if self.return_quoted_string == True:
            return '"' + self.entry.get_text()  + '"'
        else:
            return self.value


class FloatEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        self.spinbutton = Gtk.SpinButton.new_with_range(MIN_VAL, MAX_VAL, 0.1)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(2)
        self.spinbutton.set_value(float(value))
        
        self.build_editor(label_text, self.spinbutton)
        self.editor_type = SIMPLE_EDITOR_FLOAT

    def get_value(self):
        return self.spinbutton.get_value()
            

class IntEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        self.spinbutton = Gtk.SpinButton.new_with_range(MIN_VAL, MAX_VAL, 1.0)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(0)
        self.spinbutton.set_value(int(value))
        
        self.build_editor(label_text, self.spinbutton)
        self.editor_type = SIMPLE_EDITOR_INT
        
    def get_value(self):
        return self.spinbutton.get_value_as_int()


class ColorEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        try:
            # This works for blender program input data.
            # Values may have parenthesis around 
            if value[0:1] == '(':
                value = value[1:len(value) - 1]

            if value[len(value) - 1:len(value)] == ')':
                value = value[0:len(value) - 1]
            
            value = value.replace(", ", ",") # input value can easily have some extra spaces, even better if we had some generic solution here
            four_float_tuple = tuple(map(float, value.split(',')))
        except:
            # This works for Media Plugins script input data.
            four_float_tuple = value

        rgba = Gdk.RGBA(*four_float_tuple)

        self.colorbutton = Gtk.ColorButton.new_with_rgba(rgba)
        
        self.build_editor(label_text, self.colorbutton)
        self.editor_type = SIMPLE_EDITOR_COLOR
        
    def get_value(self):
        # Blender projects use this output
        value = self.colorbutton.get_rgba().to_string()
        value = value[4:len(value)]
        value = value[0:len(value) - 1]

        color_list = list(map(float, value.split(',')))
        out_value = ""
        for color_val in color_list:
            color_val_str = str(float(color_val) / 255.0)
            out_value += color_val_str
            out_value += ","
            
        out_value += "1.0"

        return out_value
    
    def get_value_as_color_tuple(self):
        color = self.colorbutton.get_rgba()
        return (color.red, color.green, color.blue, 1.0)
        
class CheckboxEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        self.checkbox = Gtk.CheckButton.new()
        self.checkbox.set_active(bool(value))
        
        self.build_editor(label_text, self.checkbox)

    def get_value(self):
        return self.checkbox.get_active()

class OptionsEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        
        active_index, options = value
        self.combo = Gtk.ComboBoxText.new()
        for opt in options:
            self.combo.append_text(opt)
        self.combo.set_active(active_index)
        
        self.build_editor(label_text, self.combo)

    def get_value(self):
        return self.combo.get_active()

class FilePathEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        self.file_choose = Gtk.FileChooserButton.new("", Gtk.FileChooserAction.OPEN)
        
        self.build_editor(label_text, self.file_choose)

    def get_value(self):
        return self.file_choose.get_filename()

class FloatEditorRange(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        default_val, min_val, max_val = value
        self.spinbutton = Gtk.SpinButton.new_with_range(float(min_val), float(max_val), 0.1)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(2)
        self.spinbutton.set_value(float(default_val))
        
        self.build_editor(label_text, self.spinbutton)
        self.editor_type = SIMPLE_EDITOR_FLOAT

    def get_value(self):
        return self.spinbutton.get_value()

class IntEditorRange(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        default_val, min_val, max_val = value
        self.spinbutton = Gtk.SpinButton.new_with_range(min_val, max_val, 1.0)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(0)
        self.spinbutton.set_value(int(default_val))
        
        self.build_editor(label_text, self.spinbutton)
        self.editor_type = SIMPLE_EDITOR_INT
        
    def get_value(self):
        return self.spinbutton.get_value_as_int()

# ------------------------------------------------------------------- preview
class PreviewPanel(Gtk.VBox):

    def __init__(self, parent, clip, length=-1):
        GObject.GObject.__init__(self)

        self.frame = 0
        self.parent = parent
        self.preview_surface = None # gets set by parent on preview completion
        
        self.preview_info = Gtk.Label()
        self.preview_info.set_markup("<small>" + _("no preview") + "</small>" )
        preview_info_row = Gtk.HBox()
        preview_info_row.pack_start(self.preview_info, False, False, 0)
        preview_info_row.pack_start(Gtk.Label(), True, True, 0)
        preview_info_row.set_margin_top(6)
        preview_info_row.set_margin_bottom(8)

        self.preview_monitor = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_preview)

        self.no_preview_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + NO_PREVIEW_FILE)

        # Control row
        self.frame_display = Gtk.Label(_("Clip Frame"))
        self.frame_display.set_margin_right(2)
        
        if length == -1:
            length = clip.clip_out - clip.clip_in
        
        self.frame_select = Gtk.SpinButton.new_with_range (0, length, 1)
        self.frame_select.set_value(0)
        
        self.preview_button = Gtk.Button(_("Preview"))
        self.preview_button.connect("clicked", lambda w: parent.render_preview_frame())
                            
        control_panel = Gtk.HBox(False, 2)
        control_panel.pack_start(self.frame_display, False, False, 0)
        control_panel.pack_start(self.frame_select, False, False, 0)
        control_panel.pack_start(Gtk.Label(), True, True, 0)
        control_panel.pack_start(self.preview_button, False, False, 0)

        self.pack_start(preview_info_row, False, False, 0)
        self.pack_start(self.preview_monitor, False, False, 0)
        self.pack_start(guiutils.pad_label(4,4), False, False, 0)
        self.pack_start(control_panel, False, False, 0)
        self.pack_start(Gtk.Label(), True, True, 0)

    def _draw_preview(self, event, cr, allocation):
        x, y, w, h = allocation

        if self.preview_surface != None:
            sw = self.preview_surface.get_width ()
            sh = self.preview_surface.get_height ()
            scale = float(w) / float(sw)
            cr.scale(scale, scale) # pixel aspect ratio not used in computation, correct image only for square pixel formats.
            cr.set_source_surface(self.preview_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(0, 0, w, h)
            cr.fill()
