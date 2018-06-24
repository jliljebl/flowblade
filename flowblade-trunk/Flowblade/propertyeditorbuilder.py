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
Module creates GUI editors for editable mlt properties.
"""

from gi.repository import Gtk, Gdk, GObject

import cairo

import appconsts
import cairoarea
from editorstate import PROJECT
from editorstate import PLAYER
import extraeditors
import guiutils
import keyframeeditor
import mltfilters
import mlttransitions
import propertyparse
import respaths
import translations
import updater
import utils

EDITOR = "editor"

# editor types and agrs                                     editor component or arg description
SLIDER = "slider"                                           # Gtk.HScale                              
BOOLEAN_CHECK_BOX = "booleancheckbox"                       # Gtk.CheckButton
COMBO_BOX = "combobox"                                      # Gtk.Combobox
KEYFRAME_EDITOR = "keyframe_editor"                         # keyfremeeditor.KeyFrameEditor that has all the key frames relative to MEDIA start
KEYFRAME_EDITOR_CLIP = "keyframe_editor_clip"               # keyfremeeditor.KeyFrameEditor that has all the key frames relative to CLIP start
KEYFRAME_EDITOR_RELEASE = "keyframe_editor_release"         # HACK, HACK. used to prevent property update crashes in slider keyfremeeditor.KeyFrameEditor
COLOR_SELECT = "color_select"                               # Gtk.ColorButton
GEOMETRY_EDITOR = "geometry_editor"                         # keyfremeeditor.GeometryEditor
WIPE_SELECT = "wipe_select"                                 # Gtk.Combobox with options from mlttransitions.wipe_lumas
COMBO_BOX_OPTIONS = "cbopts"                                # List of options for combo box editor displayed to user
LADSPA_SLIDER = "ladspa_slider"                             # Gtk.HScale, does ladspa update for release changes(disconnect, reconnect)
CLIP_FRAME_SLIDER = "clip_frame_slider"                     # Gtk.HScale, range 0 - clip length in frames
AFFINE_GEOM_4_SLIDER = "affine_filt_geom_slider"            # 3 rows of Gtk.HScales to set the position and size
AFFINE_GEOM_4_SLIDER_2 = "affine_filt_geom_slider_2"          # 4 rows of Gtk.HScales to set the position and size
COLOR_CORRECTOR = "color_corrector"                         # 3 band color corrector color circle and Lift Gain Gamma sliders
CR_CURVES = "crcurves"                                      # Curves color editor with Catmull-Rom curve
COLOR_BOX = "colorbox"                                      # One band color editor with color box interface
COLOR_LGG = "colorlgg"                                      # Editor for ColorLGG filter
FILE_SELECTOR = "file_select"                               # File selector button for selecting single files from
IMAGE_MEDIA_FILE_SELECTOR = "image_media_file_select"       # File selector button for selecting single files from
FILE_TYPES = "file_types"                                   # list of files types with "." chracters, like ".png.tga.bmp"
FADE_LENGTH = "fade_length"                                 # Autofade compositors fade length
TEXT_ENTRY = "text_entry"                                   # Text editor
NO_EDITOR = "no_editor"                                     # No editor displayed for property

COMPOSITE_EDITOR_BUILDER = "composite_properties"           # Creates a single row editor for multiple properties of composite transition
REGION_EDITOR_BUILDER = "region_properties"                 # Creates a single row editor for multiple properties of region transition
ROTATION_GEOMETRY_EDITOR_BUILDER = "rotation_geometry_editor" # Creates a single editor for multiple geometry values

SCALE_DIGITS = "scale_digits"                               # Number of decimal digits displayed in a widget

# We need to use globals to change slider -> kf editor and back because the data does not (can not) exist anywhere else. FilterObject.properties are just tuples and EditableProperty objects
# are created deterministically from those and FilterObject.info.property_args data. So we need to save data here on change request to make the change happen.
# This data needs to erased always after use.
changing_slider_to_kf_property_name = None
re_init_editors_for_slider_type_change_func = None # monkeypatched in

def _p(name):
    try:
        return translations.param_names[name]
    except KeyError:
        return name


def get_editor_row(editable_property):
    """
    Returns GUI component to edit provided editable property.
    """
    try:
        editor = editable_property.args[EDITOR]
    except KeyError:
        editor = SLIDER #default, if editor not specified
    
    create_func = EDITOR_ROW_CREATORS[editor]
    return create_func(editable_property)

def get_transition_extra_editor_rows(compositor, editable_properties):
    """
    Returns list of extraeditors GUI components.
    """
    extra_editors = compositor.transition.info.extra_editors
    rows = []
    for editor_name in extra_editors:
        try:
            create_func = EDITOR_ROW_CREATORS[editor_name]
            editor_row = create_func(compositor, editable_properties)
            rows.append(editor_row)
        except KeyError:
            print "get_transition_extra_editor_rows fail with:" + editor_name

    return rows

def get_filter_extra_editor_rows(filt, editable_properties):
    """
    Returns list of extraeditors GUI components.
    """
    extra_editors = filt.info.extra_editors
    rows = []
    for editor_name in extra_editors:
        try:
            create_func = EDITOR_ROW_CREATORS[editor_name]
            editor_row = create_func(filt, editable_properties)
            rows.append(editor_row)
        except KeyError:
            print "get_filter_extra_editor_rows fail with:" + editor_name

    return rows
    
# ------------------------------------------------- gui builders
def _get_two_column_editor_row(name, editor_widget):
    name = _p(name)
    label = Gtk.Label(label=name + ":")

    label_box = Gtk.HBox()
    label_box.pack_start(label, False, False, 0)
    label_box.pack_start(Gtk.Label(), True, True, 0)
    label_box.set_size_request(appconsts.PROPERTY_NAME_WIDTH, appconsts.PROPERTY_ROW_HEIGHT)
    
    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(label_box, False, False, 4)
    hbox.pack_start(editor_widget, True, True, 0)
    return hbox
    
def _get_slider_row(editable_property, slider_name=None, compact=False):
    slider_editor = SliderEditor(editable_property, slider_name=None, compact=False)
    
    # This has now already been used if existed and has to be deleted.
    global changing_slider_to_kf_property_name
    changing_slider_to_kf_property_name = None
    
    # We need to tag this somehow and add lambda to pass frame events so that this can be to set get frame events
    # in clipeffectseditor.py.
    if slider_editor.editor_type == KEYFRAME_EDITOR:
        slider_editor.vbox.is_kf_editor = True      
        slider_editor.vbox.display_tline_frame = lambda tline_frame:slider_editor.kfeditor.display_tline_frame(tline_frame)
        
    return slider_editor.vbox
    

class SliderEditor:
    def __init__(self, editable_property, slider_name=None, compact=False):

        self.vbox = Gtk.VBox(False)
        is_multi_kf = (editable_property.value.find(";") != -1)
        if changing_slider_to_kf_property_name == editable_property.name or is_multi_kf == True:
            eq_index = editable_property.value.find("=")
            
            # create kf in frame 0 if value PROP_INT or PROP_FLOAT
            if eq_index == -1:
                new_value = "0=" + editable_property.value
                editable_property.value = new_value
                editable_property.write_filter_object_property(new_value)
                            
            editable_property = editable_property.get_as_KeyFrameHCSFilterProperty()
            self.init_for_kf_editor(editable_property)
        else:
            self.init_for_slider(editable_property, slider_name, compact)
        
        self.editable_property = editable_property
        
    def init_for_slider(self, editable_property, slider_name=None, compact=False):
        self.editor_type = SLIDER
        
        adjustment = editable_property.get_input_range_adjustment()
        adjustment.connect("value-changed", editable_property.adjustment_value_changed)

        hslider = Gtk.HScale()
        hslider.set_adjustment(adjustment)
        hslider.set_draw_value(False)

        spin = Gtk.SpinButton()
        spin.set_numeric(True)
        spin.set_adjustment(adjustment)

        _set_digits(editable_property, hslider, spin)

        if slider_name == None:
            name = editable_property.get_display_name()
        else:
            name = slider_name
        name = _p(name)
        
        kfs_switcher = KeyframesToggler(self)
                
        hbox = Gtk.HBox(False, 4)
        if compact:
            name_label = Gtk.Label(label=name + ":")
            hbox.pack_start(name_label, False, False, 4)
        hbox.pack_start(hslider, True, True, 0)
        hbox.pack_start(spin, False, False, 4)
        hbox.pack_start(kfs_switcher.widget, False, False, 4)

        if compact:
            self.vbox.pack_start(hbox, False, False, 0)
        else:
            top_right_h = Gtk.HBox()
            top_right_h.pack_start(Gtk.Label(), True, True, 0)            
            top_row = _get_two_column_editor_row(name, top_right_h)
            
            self.vbox.pack_start(top_row, True, True, 0)
            self.vbox.pack_start(hbox, False, False, 0)

    def init_for_kf_editor(self, editable_property):
        self.editor_type = KEYFRAME_EDITOR
        
        kfs_switcher = KeyframesToggler(self)
        self.kfeditor = keyframeeditor.KeyFrameEditor(editable_property, True, kfs_switcher)
        self.vbox.pack_start(self.kfeditor, False, False, 0)

    def kfs_toggled(self):
        if self.editor_type == SLIDER: # slider -> kf editor
            global changing_slider_to_kf_property_name
            changing_slider_to_kf_property_name = self.editable_property.name
            re_init_editors_for_slider_type_change_func()
        else: # kf editor -> slider
            # Save value as single keyframe or PROP_INT or PROP_FLOAT and
            # drop all but first keyframe.
            # Going kf editor -> slider destroys all but first keyframe.
            first_kf_index = self.editable_property.value.find(";")
            if first_kf_index == -1:
                val = self.editable_property.value
            else:
                val = self.editable_property.value[0:first_kf_index]
            
            eq_index = self.editable_property.value.find("=")  + 1
            first_kf_val = val[eq_index:len(val)]
            
            #  We need to turn editable prperty value and type(original type) back to what it was before user selected to go kf editing
            if self.editable_property.prop_orig_type == appconsts.PROP_INT:
                self.editable_property.type = appconsts.PROP_INT 
                self.editable_property.write_filter_object_property(str(int(first_kf_val)))
                #self.editable_property.typ
            elif self.editable_property.prop_orig_type == appconsts.PROP_FLOAT:
                self.editable_property.type = appconsts.PROP_FLOAT 
                self.editable_property.write_filter_object_property(str(float(first_kf_val)))
            else:
                self.editable_property.write_filter_object_property("0=" + str(float(first_kf_val)))

            re_init_editors_for_slider_type_change_func()


class KeyframesToggler:
    def __init__(self, parent_editor):
        w=16
        h=22
        self.widget = cairoarea.CairoDrawableArea2( w,
                                                    h,
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.parent_editor = parent_editor
        if parent_editor.editor_type == KEYFRAME_EDITOR:
            self.surface  = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "slider_icon.png")
        else:
            self.surface  = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kf_active.png")

        self.surface_x  = 3
        self.surface_y  = 8

    def _draw(self, event, cr, allocation):
        cr.set_source_surface(self.surface, self.surface_x, self.surface_y)
        cr.paint()

    def _press_event(self, event):
        self.parent_editor.kfs_toggled()

def _get_ladspa_slider_row(editable_property, slider_name=None):
    adjustment = editable_property.get_input_range_adjustment()

    hslider = Gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    hslider.connect("button-release-event", lambda w, e: _ladspa_slider_update(editable_property, adjustment))
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)
    spin.connect("button-release-event", lambda w, e: _ladspa_slider_update(editable_property, adjustment))

    _set_digits(editable_property, hslider, spin)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)
    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name

    top_row = _get_two_column_editor_row(name, Gtk.HBox())
    vbox = Gtk.VBox(False)
    vbox.pack_start(top_row, True, True, 0)
    vbox.pack_start(hbox, False, False, 0)
    return vbox
    

def _get_clip_frame_slider(editable_property):
    # Exceptionally we set the edit range here,
    # as the edit range is the clip length and 
    # is obivously not known at program start.
    length = editable_property.get_clip_length() - 1
    editable_property.input_range = (0, length)
    editable_property.output_range = (0.0, length)
            
    adjustment = editable_property.get_input_range_adjustment()

    hslider = Gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    hslider.connect("button-release-event", lambda w, e: _clip_frame_slider_update(editable_property, adjustment))
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)
    spin.connect("button-release-event", lambda w, e: _clip_frame_slider_update(editable_property, adjustment))

    hslider.set_digits(0)
    spin.set_digits(0)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    name = editable_property.get_display_name()
    return _get_two_column_editor_row(name, hbox)

def _get_affine_filt_geom_sliders(ep):
    scr_width = PROJECT().profile.width()
    scr_height = PROJECT().profile.width()

    # "0=0,0:SCREENSIZE:100"
    frame_value = ep.value.split("=")
    tokens = frame_value[1].split(":")
    pos_tokens = tokens[0].split("/")
    size_tokens = tokens[1].split("x")

    x_adj = Gtk.Adjustment(float(pos_tokens[0]), float(-scr_width), float(scr_width), float(1))
    y_adj = Gtk.Adjustment(float(pos_tokens[1]), float(-scr_height), float(scr_height), float(1))
    h_adj = Gtk.Adjustment(float(size_tokens[1]), float(0), float(scr_height * 5), float(1))
    
    x_slider, x_spin, x_row =  _get_affine_slider("X", x_adj)
    y_slider, y_spin, y_row =  _get_affine_slider("Y", y_adj)
    h_slider, h_spin, h_row =  _get_affine_slider(_("Size/Height"), h_adj)

    all_sliders = (x_slider, y_slider, h_slider)

    x_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))
    x_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))
    y_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))
    y_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))
    h_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))
    h_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_width))

    
    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(x_row, True, True, 0)
    vbox.pack_start(y_row, True, True, 0)
    vbox.pack_start(h_row, True, True, 0)
    
    return vbox

def _get_affine_filt_geom_sliders_2(ep):
    scr_width = PROJECT().profile.width()
    scr_height = PROJECT().profile.height()

    # "0=0,0:SCREENSIZE:100"
    frame_value = ep.value.split("=")
    tokens = frame_value[1].split(":")
    pos_tokens = tokens[0].split("/")
    size_tokens = tokens[1].split("x")

    x_adj = Gtk.Adjustment(float(pos_tokens[0]), float(-scr_width), float(scr_width), float(1))
    y_adj = Gtk.Adjustment(float(pos_tokens[1]), float(-scr_height), float(scr_height), float(1))
    xs_adj = Gtk.Adjustment(float(size_tokens[0]), float(10), float(scr_width * 3), float(1))
    #ys_adj = Gtk.Adjustment(float(size_tokens[1]), float(10), float(scr_height * 3), float(1))

    x_slider, x_spin, x_row =  _get_affine_slider("X", x_adj)
    y_slider, y_spin, y_row =  _get_affine_slider("Y", y_adj)
    xs_slider, xs_spin, xs_row =  _get_affine_slider(_("Width"), xs_adj)
    #ys_slider, ys_spin, ys_row =  _get_affine_slider(_("Height"), ys_adj)

    all_sliders = (x_slider, y_slider, xs_slider)

    x_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    x_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    y_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    y_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    xs_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    xs_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders, scr_height))
    #ys_slider.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders))
    #ys_spin.get_adjustment().connect("value-changed", lambda w: ep.slider_values_changed(all_sliders))
    
    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(x_row, True, True, 0)
    vbox.pack_start(y_row, True, True, 0)
    vbox.pack_start(xs_row, True, True, 0)
    #vbox.pack_start(ys_row, True, True, 0)

    return vbox
    
def _get_affine_slider(name, adjustment):
    hslider = Gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hslider.set_digits(0)
    spin.set_digits(0)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    return (hslider, spin, _get_two_column_editor_row(name, hbox))


def _get_text_entry(editable_property):
    entry = Gtk.Entry.new()
    entry.set_text(editable_property.value)
    entry.connect("changed", lambda w: _entry_contentents_changed(w, editable_property))

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(entry, True, True, 0)
    #hbox.pack_start(Gtk.Label(), False, False, 4)


    return _get_two_column_editor_row(editable_property.get_display_name(), hbox)

def _entry_contentents_changed(entry, editable_property):
     editable_property.value = entry.get_text()
 
def _get_boolean_check_box_row(editable_property):
    check_button = Gtk.CheckButton()
    check_button.set_active(editable_property.value == "1")
    check_button.connect("toggled", editable_property.boolean_button_toggled)
    
    hbox = Gtk.HBox(False, 4)

    hbox.pack_start(check_button, False, False, 4)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    
    return _get_two_column_editor_row(editable_property.get_display_name(), hbox)

def _get_combo_box_row(editable_property):
    combo_box = Gtk.ComboBoxText()
            
    # Parse options and fill combo box
    opts_str = editable_property.args[COMBO_BOX_OPTIONS]
    values = []
    opts = opts_str.split(",")
    for option in opts:
        sides = option.split(":")   
        values.append(sides[1])
        opt = sides[0].replace("!"," ")# Spaces are separators in args
                                       # and are replaced with "!" charactes for names
        opt = translations.get_combo_option(opt)
        combo_box.append_text(opt) 

    # Set initial value
    selection = values.index(editable_property.value)
    combo_box.set_active(selection)
    
    combo_box.connect("changed", editable_property.combo_selection_changed, values)  

    return _get_two_column_editor_row(editable_property.get_display_name(), combo_box)

def _get_color_selector(editable_property):
    gdk_color = editable_property.get_value_rgba()
    color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(*gdk_color))
    color_button.connect("color-set", editable_property.color_selected)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(color_button, False, False, 4)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    
    return _get_two_column_editor_row(editable_property.get_display_name(), hbox)

def _get_wipe_selector(editable_property):
    """
    Returns GUI component for selecting wipe type.
    """
    # Preset luma
    combo_box = Gtk.ComboBoxText()
            
    # Get options
    keys = mlttransitions.wipe_lumas.keys()
    # translate here
    keys.sort()
    for k in keys:
        combo_box.append_text(k)
 
    # Set initial value
    k_index = -1
    tokens = editable_property.value.split("/")
    test_value = tokens[len(tokens) - 1]
    for k,v in mlttransitions.wipe_lumas.iteritems():
        if v == test_value:
            k_index = keys.index(k)
    
    combo_box.set_active(k_index)
    preset_luma_row = _get_two_column_editor_row(editable_property.get_display_name(), combo_box)
    
    # User luma
    use_preset_luma_combo = Gtk.ComboBoxText()
    use_preset_luma_combo.append_text(_("Preset Luma"))
    use_preset_luma_combo.append_text(_("User Luma"))
        
    dialog = Gtk.FileChooserDialog(_("Select Luma File"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel").encode('utf-8'), Gtk.ResponseType.CANCEL,
                                    _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.add_pattern("*.png")
    file_filter.add_pattern("*.pgm")
    file_filter.set_name(_("Wipe Luma files"))
    dialog.add_filter(file_filter)
        
    user_luma_select = Gtk.FileChooserButton(dialog)
    user_luma_select.set_size_request(210, 28)
    
    user_luma_label = Gtk.Label(label=_("Luma File:"))

    if k_index == -1:
        use_preset_luma_combo.set_active(1)
        combo_box.set_sensitive(False)
        combo_box.set_active(0)
        user_luma_select.set_filename(editable_property.value)
    else:
        use_preset_luma_combo.set_active(0)
        user_luma_select.set_sensitive(False)
        user_luma_label.set_sensitive(False)
    
    user_luma_row = Gtk.HBox(False, 2)
    user_luma_row.pack_start(use_preset_luma_combo, False, False, 0)
    user_luma_row.pack_start(Gtk.Label(), True, True, 0)
    user_luma_row.pack_start(user_luma_label, False, False, 2)
    user_luma_row.pack_start(user_luma_select, False, False, 0)

    editor_pane = Gtk.VBox(False)
    editor_pane.pack_start(preset_luma_row, False, False, 4)
    editor_pane.pack_start(user_luma_row, False, False, 4)

    widgets = (combo_box, use_preset_luma_combo, user_luma_select, user_luma_label, keys)
    
    combo_box.connect("changed", editable_property.combo_selection_changed, keys)
    use_preset_luma_combo.connect("changed", _wipe_preset_combo_changed, editable_property, widgets)
    dialog.connect('response', _wipe_lumafile_dialog_response, editable_property, widgets)
    
    return editor_pane

class FadeLengthEditor(Gtk.HBox):
    def __init__(self, editable_property):

        GObject.GObject.__init__(self)
        self.set_homogeneous(False)
        self.set_spacing(2)
        
        self.editable_property = editable_property
        length = self.editable_property.clip.clip_out - self.editable_property.clip.clip_in + 1
        
        name = editable_property.get_display_name()
        name = _p(name)
        name_label = Gtk.Label(label=name + ":")
        
        label_box = Gtk.HBox()
        label_box.pack_start(name_label, False, False, 0)
        label_box.pack_start(Gtk.Label(), True, True, 0)
        label_box.set_size_request(appconsts.PROPERTY_NAME_WIDTH, appconsts.PROPERTY_ROW_HEIGHT)
           
        self.spin = Gtk.SpinButton.new_with_range (1, 1000, 1)
        self.spin.set_numeric(True)
        self.spin.set_value(length)
        self.spin.connect("value-changed", self.spin_value_changed)

        self.pack_start(guiutils.pad_label(4,4), False, False, 0)
        self.pack_start(label_box, False, False, 0)
        self.pack_start(self.spin, False, False, 0)
        self.pack_start(Gtk.Label(), True, True, 0)
        
    def spin_value_changed(self, spin):
        if self.editable_property.clip.transition.info.name == "##auto_fade_in":
            self.editable_property.clip.set_length_from_in(int(spin.get_value()))
        else:
            self.editable_property.clip.set_length_from_out(int(spin.get_value()))

        updater.repaint_tline()
    
    def display_tline_frame(self, frame):
        pass # we don't seem to need this afte all, panel gets recreated after cpompositor length change
        
def _get_fade_length_editor(editable_property):
    return FadeLengthEditor(editable_property)

def _wipe_preset_combo_changed(widget, ep, widgets):
    combo_box, use_preset_luma_combo, user_luma_select, user_luma_label, keys = widgets
    if widget.get_active() == 1:
        combo_box.set_sensitive(False)
        user_luma_select.set_sensitive(True)
        user_luma_label.set_sensitive(True)
        file_name = user_luma_select.get_filename()
        if file_name != None:
            ep.write_value(file_name)
    else:
        user_luma_select.set_sensitive(False)
        user_luma_label.set_sensitive(False)
        combo_box.set_sensitive(True)
        ep.combo_selection_changed(combo_box, keys)

def _wipe_lumafile_dialog_response(dialog, response_id, ep, widgets):
    combo_box, use_preset_luma_combo, user_luma_select, user_luma_label, keys = widgets
    file_name = user_luma_select.get_filename()
    if file_name != None:
        ep.write_value(file_name)

def _get_file_select_editor(editable_property):
    """
    Returns GUI component for selecting file of determined type
    """
    dialog = Gtk.FileChooserDialog(_("Select File"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel").encode('utf-8'), Gtk.ResponseType.CANCEL,
                                    _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)

    file_types_args_list = editable_property.args[FILE_TYPES].split(".")
    file_types_args_list = file_types_args_list[1:len(file_types_args_list)]
    file_filter = Gtk.FileFilter()
    for file_type in file_types_args_list:
        file_filter.add_pattern("*." + file_type)
    file_filter.set_name("Accepted Files")
    
    dialog.add_filter(file_filter)
        
    file_select_button = Gtk.FileChooserButton.new_with_dialog(dialog)
    file_select_button.set_size_request(210, 28)
    
    file_select_label = Gtk.Label(editable_property.get_display_name())

    editor_row = Gtk.HBox(False, 2)
    editor_row.pack_start(file_select_label, False, False, 2)
    editor_row.pack_start(guiutils.get_pad_label(3, 5), False, False, 2)
    editor_row.pack_start(file_select_button, False, False, 0)

    dialog.connect('response', editable_property.dialog_response_callback)
    
    return editor_row
    
def _get_image_file_select_editor(editable_property):
    """
    Returns GUI component for selecting image producing file
    """
    dialog = Gtk.FileChooserDialog(_("Select Image Producing File"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel").encode('utf-8'), Gtk.ResponseType.CANCEL,
                                    _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)

    file_filter = utils.get_media_source_file_filter(False)    
    dialog.add_filter(file_filter)
        
    file_select_button = Gtk.FileChooserButton.new_with_dialog(dialog)
    file_select_button.set_size_request(210, 28)
    
    file_select_label = Gtk.Label(editable_property.get_display_name())

    editor_row = Gtk.HBox(False, 2)
    editor_row.pack_start(file_select_label, False, False, 2)
    editor_row.pack_start(guiutils.get_pad_label(3, 5), False, False, 2)
    editor_row.pack_start(file_select_button, False, False, 0)

    dialog.connect('response', editable_property.dialog_response_callback)
    
    return editor_row
    
def _create_composite_editor(clip, editable_properties):
    aligned = filter(lambda ep: ep.name == "aligned", editable_properties)[0]
    distort = filter(lambda ep: ep.name == "distort", editable_properties)[0]
    operator = filter(lambda ep: ep.name == "operator", editable_properties)[0]
    values = ["over","and","or","xor"]
    deinterlace = filter(lambda ep: ep.name == "deinterlace", editable_properties)[0]
    progressive = filter(lambda ep: ep.name == "progressive", editable_properties)[0]
    force_values = [_("Nothing"),_("Progressive"),_("Deinterlace"),_("Both")]

    combo_box = Gtk.ComboBoxText()
    for val in force_values:
        combo_box.append_text(val)
    selection = _get_force_combo_index(deinterlace, progressive)
    combo_box.set_active(selection)
    combo_box.connect("changed", _compositor_editor_force_combo_box_callback, (deinterlace, progressive))
    force_vbox = Gtk.VBox(False, 4)
    force_vbox.pack_start(Gtk.Label(label=_("Force")), True, True, 0)
    force_vbox.pack_start(combo_box, True, True, 0)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Align"), aligned), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Distort"), distort), False, False, 0)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    # THESE ARE DISABLED BECAUSE CHANGING APLHA MODE CAN MAKE PROJECTS UNOPENABLE IF AFFECTED 
    # COMPOSITOR IS ON THE FIRST FRAME
    #hbox.pack_start(_get_combo_box_column(_("Alpha"), values, operator), False, False, 0)
    #hbox.pack_start(Gtk.Label(), True, True, 0)
    hbox.pack_start(force_vbox, False, False, 0)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    return hbox

def _compositor_editor_force_combo_box_callback(combo_box, data):
    value = combo_box.get_active()
    deinterlace, progressive = data
    # these must correspond to hardcoded values ["Nothing","Progressive","Deinterlace","Both"] above
    if value == 0:
        deinterlace.write_value("0")
        progressive.write_value("0")
    elif value == 1:
        deinterlace.write_value("0")
        progressive.write_value("1")
    elif value == 2:
        deinterlace.write_value("1")
        progressive.write_value("0")
    else:
        deinterlace.write_value("1")
        progressive.write_value("1")

def _create_rotion_geometry_editor(clip, editable_properties):   
    ep = propertyparse.create_editable_property_for_affine_blend(clip, editable_properties)
    
    kf_edit = keyframeeditor.RotatingGeometryEditor(ep, False)
    return kf_edit

def _create_region_editor(clip, editable_properties):
    aligned = filter(lambda ep: ep.name == "composite.aligned", editable_properties)[0]
    distort = filter(lambda ep: ep.name == "composite.distort", editable_properties)[0]
    operator = filter(lambda ep: ep.name == "composite.operator", editable_properties)[0]
    values = ["over","and","or","xor"]
    deinterlace = filter(lambda ep: ep.name == "composite.deinterlace", editable_properties)[0]
    progressive = filter(lambda ep: ep.name == "composite.progressive", editable_properties)[0]
    force_values = [_("Nothing"),_("Progressive"),_("Deinterlace"),_("Both")]

    combo_box = Gtk.ComboBoxText()
    for val in force_values:
        combo_box.append_text(val)
    selection = _get_force_combo_index(deinterlace, progressive)
    combo_box.set_active(selection)
    combo_box.connect("changed", _compositor_editor_force_combo_box_callback, (deinterlace, progressive))
    force_vbox = Gtk.VBox(False, 4)
    force_vbox.pack_start(Gtk.Label(label=_("Force")), True, True, 0)
    force_vbox.pack_start(combo_box, True, True, 0)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Align"), aligned), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Distort"), distort), False, False, 0)
    # THESE ARE DISABLED BECAUSE CHANGING APLHA MODE CAN MAKE PROJECTS UNOPENABLE IF THE AFFECTED 
    # COMPOSITOR IS ON THE FIRST FRAME
    #hbox.pack_start(Gtk.Label(), True, True, 0)
    #hbox.pack_start(_get_combo_box_column(_("Alpha"), values, operator), False, False, 0)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    hbox.pack_start(force_vbox, False, False, 0)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    return hbox

def _create_color_grader(filt, editable_properties):
    color_grader = extraeditors.ColorGrader(editable_properties)

    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.pack_start(color_grader.widget, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_crcurves_editor(filt, editable_properties):
    curves_editor = extraeditors.CatmullRomFilterEditor(editable_properties)

    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(curves_editor.widget, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_colorbox_editor(filt, editable_properties):
    colorbox_editor = extraeditors.ColorBoxFilterEditor(editable_properties)
    
    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(colorbox_editor.widget, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_color_lgg_editor(filt, editable_properties):
    color_lgg_editor = extraeditors.ColorLGGFilterEditor(editable_properties)
    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(color_lgg_editor.widget, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _get_force_combo_index(deinterlace, progressive):
    # These correspond to hardcoded values ["Nothing","Progressive","Deinterlace","Both"] above
    if int(deinterlace.value) == 0:
        if int(progressive.value) == 0:
            return 0
        else:
            return 1
    else:
        if int(progressive.value) == 0:
            return 2
        else:
            return 3

def _get_keyframe_editor(editable_property):
    return keyframeeditor.KeyFrameEditor(editable_property)

def _get_keyframe_editor_clip(editable_property):
    return keyframeeditor.KeyFrameEditor(editable_property, False)
    
def _get_keyframe_editor_release(editable_property):
    editor = keyframeeditor.KeyFrameEditor(editable_property)
    editor.connect_to_update_on_release()
    return editor
    
def _get_geometry_editor(editable_property):
    return keyframeeditor.GeometryEditor(editable_property, False)

def _get_no_editor():
    return None

def _set_digits(editable_property, scale, spin):
    try:
        digits_str = editable_property.args[SCALE_DIGITS]
        digits = int(digits_str)
    except:
        return

    scale.set_digits(digits)
    spin.set_digits(digits)

# -------------------------------------------------------- gui utils funcs
def _get_boolean_check_box_button_column(name, editable_property):
    check_button = Gtk.CheckButton()
    check_button.set_active(editable_property.value == "1")
    check_button.connect("toggled", editable_property.boolean_button_toggled)
    vbox = Gtk.VBox(False, 0)
    vbox.pack_start(Gtk.Label(label=name), True, True, 0)
    vbox.pack_start(check_button, True, True, 0)
    return vbox

def _get_combo_box_column(name, values, editable_property):
    combo_box = Gtk.ComboBoxText()
    for val in values:
        val = translations.get_combo_option(val)
        combo_box.append_text(val)
    
    # Set initial value
    selection = values.index(editable_property.value)
    combo_box.set_active(selection)    
    combo_box.connect("changed", editable_property.combo_selection_changed, values)

    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(Gtk.Label(label=name), True, True, 0)
    vbox.pack_start(combo_box, True, True, 0)
    return vbox
    
# ------------------------------------ SPECIAL VALUE UPDATE METHODS
# LADSPA filters do not respond to MLT property updates and 
# need to be recreated to update output
def _ladspa_slider_update(editable_property, adjustment):
    # ...or segphault
    PLAYER().stop_playback()
    
    # Change property value
    editable_property.adjustment_value_changed(adjustment)
    
    # Update output by cloning and replacing filter
    ladspa_filter = editable_property._get_filter_object()
    filter_clone = mltfilters.clone_filter_object(ladspa_filter, PROJECT().profile)
    clip = editable_property.track.clips[editable_property.clip_index]

    mltfilters.detach_all_filters(clip)
    clip.filters.pop(editable_property.filter_index)
    clip.filters.insert(editable_property.filter_index, filter_clone)
    mltfilters.attach_all_filters(clip)

def _clip_frame_slider_update(editable_property, adjustment):
    PLAYER().stop_playback()
    editable_property.adjustment_value_changed(adjustment)

# editor types -> creator functions
EDITOR_ROW_CREATORS = { \
    SLIDER:lambda ep :_get_slider_row(ep),
    BOOLEAN_CHECK_BOX:lambda ep :_get_boolean_check_box_row(ep),
    COMBO_BOX:lambda ep :_get_combo_box_row(ep),
    KEYFRAME_EDITOR: lambda ep : _get_keyframe_editor(ep),
    KEYFRAME_EDITOR_CLIP: lambda ep : _get_keyframe_editor_clip(ep),
    KEYFRAME_EDITOR_RELEASE: lambda ep : _get_keyframe_editor_release(ep),
    GEOMETRY_EDITOR: lambda ep : _get_geometry_editor(ep),
    AFFINE_GEOM_4_SLIDER: lambda ep : _get_affine_filt_geom_sliders(ep),
    AFFINE_GEOM_4_SLIDER_2: lambda ep :_get_affine_filt_geom_sliders_2(ep),
    COLOR_SELECT: lambda ep: _get_color_selector(ep),
    WIPE_SELECT: lambda ep: _get_wipe_selector(ep),
    LADSPA_SLIDER: lambda ep: _get_ladspa_slider_row(ep),
    CLIP_FRAME_SLIDER: lambda ep: _get_clip_frame_slider(ep),
    FILE_SELECTOR: lambda ep: _get_file_select_editor(ep),
    IMAGE_MEDIA_FILE_SELECTOR: lambda ep: _get_image_file_select_editor(ep),
    FADE_LENGTH: lambda ep: _get_fade_length_editor(ep),
    NO_EDITOR: lambda ep: _get_no_editor(),
    COMPOSITE_EDITOR_BUILDER: lambda comp, editable_properties: _create_composite_editor(comp, editable_properties),
    REGION_EDITOR_BUILDER: lambda comp, editable_properties: _create_region_editor(comp, editable_properties),
    ROTATION_GEOMETRY_EDITOR_BUILDER: lambda comp, editable_properties: _create_rotion_geometry_editor(comp, editable_properties),
    COLOR_CORRECTOR: lambda filt, editable_properties: _create_color_grader(filt, editable_properties),
    CR_CURVES: lambda filt, editable_properties:_create_crcurves_editor(filt, editable_properties),
    COLOR_BOX: lambda filt, editable_properties:_create_colorbox_editor(filt, editable_properties),
    COLOR_LGG: lambda filt, editable_properties:_create_color_lgg_editor(filt, editable_properties),
    TEXT_ENTRY: lambda ep: _get_text_entry(ep),
    }

"""
    # example code for using slider editor with NON-MLT property
    #hue = filter(lambda ep: ep.name == "hue", editable_properties)[0]
    #hue_row = _get_slider_row(hue, None, True)
    #saturation = filter(lambda ep: ep.name == "saturation", editable_properties)[0]
    #saturation_row = _get_slider_row(saturation, None, True)
    #value = filter(lambda ep: ep.name == "value", editable_properties)[0]
    #value_row = _get_slider_row(value, None, True)
    #colorbox_editor = extraeditors.ColorBoxFilterEditor(editable_properties, [hue_row, saturation_row, value_row])
    #hue.adjustment_listener = colorbox_editor.hue_changed
    #saturation.adjustment_listener = colorbox_editor.saturation_changed
    #value.adjustment_listener = colorbox_editor.value_changed
"""
