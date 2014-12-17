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
import pygtk
pygtk.require('2.0');
import gtk


import appconsts
from editorstate import PROJECT
from editorstate import PLAYER
from editorstate import current_sequence
import extraeditors
import guiutils
import keyframeeditor
import mltfilters
import mlttransitions
import translations
import utils

EDITOR = "editor"

# editor types                                              editor component
SLIDER = "slider"                                           # gtk.HScale                              
BOOLEAN_CHECK_BOX = "booleancheckbox"                       # gtk.CheckButton
COMBO_BOX = "combobox"                                      # gtk.Combobox
KEYFRAME_EDITOR = "keyframe_editor"                         # keyfremeeditor.KeyFrameEditor that has all the key frames relative to MEDIA start
KEYFRAME_EDITOR_CLIP = "keyframe_editor_clip"               # keyfremeeditor.KeyFrameEditor that has all the key frames relative to CLIP start
KEYFRAME_EDITOR_RELEASE = "keyframe_editor_release"         # HACK, HACK. used to prevent property update crashes in slider keyfremeeditor.KeyFrameEditor
COLOR_SELECT = "color_select"                               # gtk.ColorButton
GEOMETRY_EDITOR = "geometry_editor"                         # keyfremeeditor.GeometryEditor
WIPE_SELECT = "wipe_select"                                 # gtk.Combobox with options from mlttransitions.wipe_lumas
COMBO_BOX_OPTIONS = "cbopts"                                # List of options for combo box editor displayed to user
LADSPA_SLIDER = "ladspa_slider"                             # gtk.HScale, does ladspa update for release changes(disconnect, reconnect)
CLIP_FRAME_SLIDER = "clip_frame_slider"                     # gtk.HScale, range 0 - clip length in frames
AFFINE_GEOM_4_SLIDER = "affine_filt_geom_slider"            # 4 rows of gtk.HScales to set the position and size
COLOR_CORRECTOR = "color_corrector"                         # 3 band color corrector color circle and Lift Gain Gamma sliders
CR_CURVES = "crcurves"                                      # Curves color editor with Catmull-Rom curve
COLOR_BOX = "colorbox"                                      # One band color editor with color box interface
COLOR_LGG = "colorlgg"                                      # Editor for ColorLGG filter
NO_EDITOR = "no_editor"                                     # No editor displayed for property

COMPOSITE_EDITOR_BUILDER = "composite_properties"           # Creates a single row editor for multiple properties of composite transition
REGION_EDITOR_BUILDER = "region_properties"                 # Creates a single row editor for multiple properties of region transition
ROTATION_GEOMETRY_EDITOR_BUILDER = "rotation_geometry_editor" # Creates a single editor for multiple geometry values

SCALE_DIGITS = "scale_digits"                               # Number of decimal digits displayed in a widget

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
    #print editable_properties
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
    label = gtk.Label(name + ":")

    label_box = gtk.HBox()
    label_box.pack_start(label, False, False, 0)
    label_box.pack_start(gtk.Label(), True, True, 0)
    label_box.set_size_request(appconsts.PROPERTY_NAME_WIDTH, appconsts.PROPERTY_ROW_HEIGHT)
    
    hbox = gtk.HBox(False, 2)
    hbox.pack_start(label_box, False, False, 4)
    hbox.pack_start(editor_widget, True, True, 0)
    return hbox
    
def _get_slider_row(editable_property, slider_name=None, compact=False):
    adjustment = editable_property.get_input_range_adjustment()
    adjustment.connect("value-changed", editable_property.adjustment_value_changed)

    hslider = gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)

    spin = gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    _set_digits(editable_property, hslider, spin)

    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name
    name = _p(name)
    
    hbox = gtk.HBox(False, 4)
    if compact:
        name_label = gtk.Label(name + ":")
        hbox.pack_start(name_label, False, False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    vbox = gtk.VBox(False)
    if compact:
        vbox.pack_start(hbox, False, False, 0)
    else:
        top_row = _get_two_column_editor_row(name, gtk.HBox())
        vbox.pack_start(top_row, True, True, 0)
        vbox.pack_start(hbox, False, False, 0)
    return vbox

def _get_ladspa_slider_row(editable_property, slider_name=None):
    adjustment = editable_property.get_input_range_adjustment()

    hslider = gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    hslider.connect("button-release-event", lambda w, e: _ladspa_slider_update(editable_property, adjustment))
    
    spin = gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)
    spin.connect("button-release-event", lambda w, e: _ladspa_slider_update(editable_property, adjustment))

    _set_digits(editable_property, hslider, spin)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)
    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name

    top_row = _get_two_column_editor_row(name, gtk.HBox())
    vbox = gtk.VBox(False)
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

    hslider = gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    hslider.connect("button-release-event", lambda w, e: _clip_frame_slider_update(editable_property, adjustment))
    
    spin = gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)
    spin.connect("button-release-event", lambda w, e: _clip_frame_slider_update(editable_property, adjustment))

    hslider.set_digits(0)
    spin.set_digits(0)

    hbox = gtk.HBox(False, 4)
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

    x_adj = gtk.Adjustment(float(pos_tokens[0]), float(-scr_width), float(scr_width), float(1))
    y_adj = gtk.Adjustment(float(pos_tokens[1]), float(-scr_height), float(scr_height), float(1))
    h_adj = gtk.Adjustment(float(size_tokens[1]), float(0), float(scr_height * 5), float(1))
    
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

    
    vbox = gtk.VBox(False, 4)
    vbox.pack_start(x_row, True, True, 0)
    vbox.pack_start(y_row, True, True, 0)
    vbox.pack_start(h_row, True, True, 0)
    
    return vbox

def _get_affine_slider(name, adjustment):
    hslider = gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    
    spin = gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hslider.set_digits(0)
    spin.set_digits(0)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    return (hslider, spin, _get_two_column_editor_row(name, hbox))
    
def _get_boolean_check_box_row(editable_property):
    check_button = gtk.CheckButton()
    check_button.set_active(editable_property.value == "1")
    check_button.connect("toggled", editable_property.boolean_button_toggled)
    
    hbox = gtk.HBox(False, 4)

    hbox.pack_start(check_button, False, False, 4)
    hbox.pack_start(gtk.Label(), True, True, 0)
    
    return _get_two_column_editor_row(editable_property.get_display_name(), hbox)

def _get_combo_box_row(editable_property):
    combo_box = gtk.combo_box_new_text()
            
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
    gdk_color = editable_property.get_value_as_gdk_color()
    color_button = gtk.ColorButton(gdk_color)
    color_button.connect("color-set", editable_property.color_selected)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(color_button, False, False, 4)
    hbox.pack_start(gtk.Label(), True, True, 0)
    
    return _get_two_column_editor_row(editable_property.get_display_name(), hbox)

def _get_wipe_selector(editable_property):
    """
    Returns GUI component for selecting wipe type.
    """
    # Preset luma
    combo_box = gtk.combo_box_new_text()
            
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
    use_preset_luma_combo = gtk.combo_box_new_text()
    use_preset_luma_combo.append_text(_("Preset Luma"))
    use_preset_luma_combo.append_text(_("User Luma"))
        
    dialog = gtk.FileChooserDialog(_("Select Luma File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.add_pattern("*.png")
    file_filter.add_pattern("*.pgm")
    file_filter.set_name(_("Wipe Luma files"))
    dialog.add_filter(file_filter)
        
    user_luma_select = gtk.FileChooserButton(dialog)
    user_luma_select.set_size_request(210, 28)
    
    user_luma_label = gtk.Label(_("Luma File:"))

    if k_index == -1:
        use_preset_luma_combo.set_active(1)
        combo_box.set_sensitive(False)
        combo_box.set_active(0)
        user_luma_select.set_filename(editable_property.value)
    else:
        use_preset_luma_combo.set_active(0)
        user_luma_select.set_sensitive(False)
        user_luma_label.set_sensitive(False)
    
    user_luma_row = gtk.HBox(False, 2)
    user_luma_row.pack_start(use_preset_luma_combo, False, False, 0)
    user_luma_row.pack_start(gtk.Label(), True, True, 0)
    user_luma_row.pack_start(user_luma_label, False, False, 2)
    user_luma_row.pack_start(user_luma_select, False, False, 0)

    editor_pane = gtk.VBox(False)
    editor_pane.pack_start(preset_luma_row, False, False, 4)
    editor_pane.pack_start(user_luma_row, False, False, 4)

    widgets = (combo_box, use_preset_luma_combo, user_luma_select, user_luma_label, keys)
    
    combo_box.connect("changed", editable_property.combo_selection_changed, keys)
    use_preset_luma_combo.connect("changed", _wipe_preset_combo_changed, editable_property, widgets)
    dialog.connect('response', _wipe_lumafile_dialog_response, editable_property, widgets)
    
    return editor_pane

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

def _create_composite_editor(clip, editable_properties):
    aligned = filter(lambda ep: ep.name == "aligned", editable_properties)[0]
    distort = filter(lambda ep: ep.name == "distort", editable_properties)[0]
    operator = filter(lambda ep: ep.name == "operator", editable_properties)[0]
    values = ["over","and","or","xor"]
    deinterlace = filter(lambda ep: ep.name == "deinterlace", editable_properties)[0]
    progressive = filter(lambda ep: ep.name == "progressive", editable_properties)[0]
    force_values = [_("Nothing"),_("Progressive"),_("Deinterlace"),_("Both")]

    combo_box = gtk.combo_box_new_text()
    for val in force_values:
        combo_box.append_text(val)
    selection = _get_force_combo_index(deinterlace, progressive)
    combo_box.set_active(selection)
    combo_box.connect("changed", _compositor_editor_force_combo_box_callback, (deinterlace, progressive))
    force_vbox = gtk.VBox(False, 4)
    force_vbox.pack_start(gtk.Label(_("Force")), True, True, 0)
    force_vbox.pack_start(combo_box, True, True, 0)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Align"), aligned), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Distort"), distort), False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
    hbox.pack_start(_get_combo_box_column(_("Alpha"), values, operator), False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
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
    # Build a custom object that duck types for TransitionEditableProperty to use in editor
    ep = utils.EmptyClass()
    # pack real properties to go
    ep.x = filter(lambda ep: ep.name == "x", editable_properties)[0]
    ep.y = filter(lambda ep: ep.name == "y", editable_properties)[0]
    ep.x_scale = filter(lambda ep: ep.name == "x scale", editable_properties)[0]
    ep.y_scale = filter(lambda ep: ep.name == "y scale", editable_properties)[0]
    ep.rotation = filter(lambda ep: ep.name == "rotation", editable_properties)[0]
    ep.opacity = filter(lambda ep: ep.name == "opacity", editable_properties)[0]
    # Screen width and height are needeed for frei0r conversions
    ep.profile_width = current_sequence().profile.width()
    ep.profile_height = current_sequence().profile.height()
    # duck type methods, using opacity is not meaningful, any property with clip member could do
    ep.get_clip_tline_pos = lambda : ep.opacity.clip.clip_in # clip is compositor, compositor in and out points staright in timeline frames
    ep.get_clip_length = lambda : ep.opacity.clip.clip_out - ep.opacity.clip.clip_in + 1
    ep.get_input_range_adjustment = lambda : gtk.Adjustment(float(100), float(0), float(100), float(1))
    ep.get_display_name = lambda : "Opacity"
    ep.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
    ep.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range
    ep.write_out_keyframes = lambda w_kf : keyframeeditor.rotating_ge_write_out_keyframes(ep, w_kf)
    # duck type members
    x_tokens = ep.x.value.split(";")
    y_tokens = ep.y.value.split(";")
    x_scale_tokens = ep.x_scale.value.split(";")
    y_scale_tokens = ep.y_scale.value.split(";")
    rotation_tokens = ep.rotation.value.split(";")
    opacity_tokens = ep.opacity.value.split(";")
    
    value = ""
    for i in range(0, len(x_tokens)): # these better match, same number of keyframes for all values, or this will not work
        frame, x = x_tokens[i].split("=")
        frame, y = y_tokens[i].split("=")
        frame, x_scale = x_scale_tokens[i].split("=")
        frame, y_scale = y_scale_tokens[i].split("=")
        frame, rotation = rotation_tokens[i].split("=")
        frame, opacity = opacity_tokens[i].split("=")
        
        frame_str = str(frame) + "=" + str(x) + ":" + str(y) + ":" + str(x_scale) + ":" + str(y_scale) + ":" + str(rotation) + ":" + str(opacity)
        value += frame_str + ";"

    ep.value = value.strip(";")

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

    combo_box = gtk.combo_box_new_text()
    for val in force_values:
        combo_box.append_text(val)
    selection = _get_force_combo_index(deinterlace, progressive)
    combo_box.set_active(selection)
    combo_box.connect("changed", _compositor_editor_force_combo_box_callback, (deinterlace, progressive))
    force_vbox = gtk.VBox(False, 4)
    force_vbox.pack_start(gtk.Label(_("Force")), True, True, 0)
    force_vbox.pack_start(combo_box, True, True, 0)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Align"), aligned), False, False, 0)
    hbox.pack_start(_get_boolean_check_box_button_column(_("Distort"), distort), False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
    hbox.pack_start(_get_combo_box_column(_("Alpha"), values, operator), False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
    hbox.pack_start(force_vbox, False, False, 0)
    hbox.pack_start(guiutils.get_pad_label(3, 5), False, False, 0)
    return hbox

def _create_color_grader(filt, editable_properties):
    color_grader = extraeditors.ColorGrader(editable_properties)

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.pack_start(color_grader.widget, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_crcurves_editor(filt, editable_properties):
    curves_editor = extraeditors.CatmullRomFilterEditor(editable_properties)

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(curves_editor.widget, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_colorbox_editor(filt, editable_properties):
    colorbox_editor = extraeditors.ColorBoxFilterEditor(editable_properties)
    
    vbox = gtk.VBox(False, 4)
    vbox.pack_start(colorbox_editor.widget, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.no_separator = True
    return vbox

def _create_color_lgg_editor(filt, editable_properties):
    color_lgg_editor = extraeditors.ColorLGGFilterEditor(editable_properties)
    vbox = gtk.VBox(False, 4)
    vbox.pack_start(color_lgg_editor.widget, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
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
    check_button = gtk.CheckButton()
    check_button.set_active(editable_property.value == "1")
    check_button.connect("toggled", editable_property.boolean_button_toggled)
    check_align = gtk.Alignment(0.5, 0.0)
    check_align.add(check_button)
    vbox = gtk.VBox(False, 0)
    vbox.pack_start(gtk.Label(name), True, True, 0)
    vbox.pack_start(check_align, True, True, 0)
    return vbox

def _get_combo_box_column(name, values, editable_property):
    combo_box = gtk.combo_box_new_text()
    for val in values:
        val = translations.get_combo_option(val)
        combo_box.append_text(val)
    
    # Set initial value
    selection = values.index(editable_property.value)
    combo_box.set_active(selection)    
    combo_box.connect("changed", editable_property.combo_selection_changed, values)

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(gtk.Label(name), True, True, 0)
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
    COLOR_SELECT: lambda ep: _get_color_selector(ep),
    WIPE_SELECT: lambda ep: _get_wipe_selector(ep),
    LADSPA_SLIDER: lambda ep: _get_ladspa_slider_row(ep),
    CLIP_FRAME_SLIDER: lambda ep: _get_clip_frame_slider(ep),
    NO_EDITOR: lambda ep: _get_no_editor(),
    COMPOSITE_EDITOR_BUILDER: lambda comp, editable_properties: _create_composite_editor(comp, editable_properties),
    REGION_EDITOR_BUILDER: lambda comp, editable_properties: _create_region_editor(comp, editable_properties),
    ROTATION_GEOMETRY_EDITOR_BUILDER: lambda comp, editable_properties: _create_rotion_geometry_editor(comp, editable_properties),
    COLOR_CORRECTOR: lambda filt, editable_properties: _create_color_grader(filt, editable_properties),
    CR_CURVES: lambda filt, editable_properties:_create_crcurves_editor(filt, editable_properties),
    COLOR_BOX: lambda filt, editable_properties:_create_colorbox_editor(filt, editable_properties),
    COLOR_LGG: lambda filt, editable_properties:_create_color_lgg_editor(filt, editable_properties)
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
