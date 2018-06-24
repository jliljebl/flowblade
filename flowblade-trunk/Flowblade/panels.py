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
Module has methods that build panels from widgets. Created panels
are used to build gui at callsites.
"""
import cairo

from gi.repository import Gtk, Gdk

import appconsts
import gui
import guicomponents
import guiutils
import editorstate
import mlttransitions
import renderconsumer
import respaths
import utils

HALF_ROW_WIDTH = 160 # Size of half row when using two column row components created here
EFFECT_PANEL_WIDTH_PAD = 20 # This is subtracted from notebGtk.Calendar ook width to get some component widths
TC_LABEL_WIDTH = 80 # in, out and length timecodes in monitor area top row 

MEDIA_PANEL_MIN_ROWS = 2
MEDIA_PANEL_MAX_ROWS = 8
MEDIA_PANEL_DEFAULT_ROWS = 2


def get_media_files_panel(media_list_view, add_cb, del_cb, col_changed_cb, hamburger_launch_pressed, filtering_cb):
    # Create buttons and connect signals
    add_media_b = Gtk.Button(_("Add"))
    del_media_b = Gtk.Button(_("Delete"))    
    add_media_b.connect("clicked", add_cb, None)
    del_media_b.connect("clicked", del_cb, None)
    add_media_b.set_tooltip_text(_("Add Media File to Bin"))
    del_media_b.set_tooltip_text(_("Delete Media File from Bin"))

    hamburger_launcher = guicomponents.HamburgerPressLaunch(hamburger_launch_pressed)
    guiutils.set_margins(hamburger_launcher.widget, 2, 0, 4, 12)

    columns_img = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "columns.png")
    columns_launcher = guicomponents.PressLaunch(col_changed_cb, columns_img, w=22, h=22)
    columns_launcher.surface_y = 6
    #guiutils.set_margins(columns_launcher.widget, 0, 4, 0, 0)    
    
    all_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_all_files.png")
    audio_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_audio_files.png")
    graphics_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_graphics_files.png")
    video_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_video_files.png")
    imgseq_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_imgseq_files.png")
    pattern_pixbuf = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "show_pattern_producers.png")

    files_filter_launcher = guicomponents.ImageMenuLaunch(filtering_cb, [all_pixbuf, video_pixbuf, audio_pixbuf, graphics_pixbuf, imgseq_pixbuf, pattern_pixbuf], 24, 22)
    files_filter_launcher.surface_x  = 3
    files_filter_launcher.surface_y  = 4
    gui.media_view_filter_selector = files_filter_launcher
    #guiutils.set_margins(files_filter_launcher.widget, 0, 4, 0, 0)
    
    buttons_box = Gtk.HBox(False,1)
    buttons_box.pack_start(hamburger_launcher.widget, False, False, 0)
    buttons_box.pack_start(guiutils.get_pad_label(4, 4), False, False, 0)
    buttons_box.pack_start(columns_launcher.widget, False, False, 0)
    buttons_box.pack_start(files_filter_launcher.widget, False, False, 0)
    buttons_box.pack_start(Gtk.Label(), True, True, 0)

    panel = Gtk.VBox()
    panel.pack_start(media_list_view, True, True, 0)
    panel.pack_start(buttons_box, False, True, 0)

    
    return panel

def get_bins_panel(bin_list_view, add_cb, delete_cb):
    # Create buttons and connect signals
    add_b = Gtk.Button(_("Add"))
    del_b = Gtk.Button(_("Delete"))
    add_b.connect("clicked", add_cb, None)
    del_b.connect("clicked", delete_cb, None)
    add_b.set_tooltip_text(_("Add Bin to Project"))
    del_b.set_tooltip_text(_("Delete Bin from Project"))
    buttons_box = Gtk.HBox(True,1)
    buttons_box.pack_start(add_b, True, True, 0)
    buttons_box.pack_start(del_b, True, True, 0)
    
    panel = Gtk.VBox()
    panel.pack_start(buttons_box, False, True, 0)
    panel.pack_start(bin_list_view, True, True, 0)

    return get_named_frame(_("Bins"), panel, 0, 0, 0)

def get_bins_tree_panel(bin_list_view):   
    panel = Gtk.VBox()
    panel.pack_start(bin_list_view, True, True, 0)

    return get_named_frame(_("Bins"), panel, 0, 0, 0)
    
def get_sequences_panel(sequence_list_view, edit_seq_cb, add_seq_cb, del_seq_cb):
    # Create buttons and connect signals
    add_b = Gtk.Button(_("Add"))
    del_b = Gtk.Button(_("Delete"))
    edit_b = Gtk.Button(_("Edit"))
    add_b.set_tooltip_text(_("Add new Sequence to Project"))
    del_b.set_tooltip_text(_("Delete Sequence from Project"))
    edit_b.set_tooltip_text(_("Start editing Sequence"))
    edit_b.connect("clicked", edit_seq_cb, None)
    add_b.connect("clicked", add_seq_cb, None)
    del_b.connect("clicked", del_seq_cb, None)

    buttons_box = Gtk.HBox(True,1)
    buttons_box.pack_start(edit_b, True, True, 0)
    buttons_box.pack_start(add_b, True, True, 0)
    buttons_box.pack_start(del_b, True, True, 0)
    
    panel = Gtk.VBox()
    #panel.pack_start(buttons_box, False, True, 0)
    panel.pack_start(sequence_list_view, True, True, 0)

    return get_named_frame(_("Sequences"), panel, 0)

def get_thumbnail_select_panel(current_folder_path):    
    texts_panel = get_two_text_panel(_("Select folder for new thumbnails."), 
                                     _("Old thumbnails in this or other projects will") + 
                                     _(" still be available,\nthis only affects thumnails that are created for new media.\n") + 
                                     _("\nSetting your home folder as thumbnails folder is not allowed."))

    out_folder = Gtk.FileChooserButton("Select Folder")
    out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    if current_folder_path != None:
        out_folder.set_current_folder(current_folder_path)
    
    out_folder_align = guiutils.set_margins(out_folder, 12, 24, 12, 12)

    panel = Gtk.VBox()
    panel.pack_start(texts_panel, False, False, 0)
    panel.pack_start(out_folder_align, False, False, 0)
    
    return (panel, out_folder)

def get_render_folder_select_panel(current_folder_path):    
    texts_panel = get_two_text_panel(_("Select folder for rendered clips."), 
                                     _("Old rendered clips in this or other projects will") + 
                                     _(" still be available,\nthis only affects rendered files that are created from now on.\n") + 
                                     _("\nSetting your home folder as folder for rendered clips is not allowed."))
        
    out_folder = Gtk.FileChooserButton("Select Folder")
    out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    if current_folder_path != None:
        out_folder.set_current_folder(current_folder_path)

    out_folder_align = guiutils.set_margins(out_folder, 12, 24, 12, 12)
    
    panel = Gtk.VBox()
    panel.pack_start(texts_panel, False, False, 0)
    panel.pack_start(out_folder_align, False, False, 0)
    
    return (panel, out_folder)

def _set_sensive_widgets(sensitive, list):
    for widget in list:
        widget.set_sensitive(sensitive)
"""
def get_motion_render_progress_panel(file_name, progress_bar):
    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(Gtk.Label(label=file_name),False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(progress_bar, False, False, 0)
    print "ee"
    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    return alignment
"""

def get_named_frame(name, widget, left_padding=12, right_padding=6, right_out_padding=4):
    """
    Gnome style named panel
    """
    if name != None:
        label = guiutils.bold_label(name)
        label.set_justify(Gtk.Justification.LEFT)
        
        label_box = Gtk.HBox()
        label_box.pack_start(label, False, False, 0)
        label_box.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(widget, right_padding, 0, left_padding, 0)

    frame = Gtk.VBox()
    if name != None:
        frame.pack_start(label_box, False, False, 0)
    frame.pack_start(widget, True, True, 0)

    guiutils.set_margins(frame, 4, 4, 0, right_out_padding)
    
    return frame

def get_two_text_panel(primary_txt, secondary_txt):
    p_label = guiutils.bold_label(primary_txt)
    s_label = Gtk.Label(label=secondary_txt)
    texts_pad = Gtk.Label()
    texts_pad.set_size_request(12,12)

    pbox = Gtk.HBox(False, 1)
    pbox.pack_start(p_label, False, False, 0)
    pbox.pack_start(Gtk.Label(), True, True, 0)

    sbox = Gtk.HBox(False, 1)
    sbox.pack_start(s_label, False, False, 0)
    sbox.pack_start(Gtk.Label(), True, True, 0)
    
    text_box = Gtk.VBox(False, 0)
    text_box.pack_start(pbox, False, False, 0)
    text_box.pack_start(texts_pad, False, False, 0)
    text_box.pack_start(sbox, False, False, 0)
    text_box.pack_start(Gtk.Label(), True, True, 0)

    align = guiutils.set_margins(text_box, 12, 0, 12, 12)
    
    return align

def get_file_properties_panel(data):
    media_file, img, size, length, vcodec, acodec, channels, frequency, fps, match_profile_name, matches_current_profile = data
    
    row0 = get_two_column_box(get_bold_label(_("Name:")), Gtk.Label(label=media_file.name))
    row00 = get_two_column_box(get_bold_label(_("Path:")), Gtk.Label(label=media_file.path))
    row1 = get_two_column_box(get_bold_label(_("Image Size:")), Gtk.Label(label=size))
    row111 = get_two_column_box(get_bold_label(_("Frames Per Second:")), Gtk.Label(label=fps))
    row11 = get_two_column_box(get_bold_label(_("Playtime:")), Gtk.Label(label=length))
    row2 = get_two_column_box(get_bold_label(_("Video Codec:")), Gtk.Label(label=vcodec))
    row3 = get_two_column_box(get_bold_label(_("Audio Codec:")), Gtk.Label(label=acodec))
    row4 = get_two_column_box(get_bold_label(_("Audio Channels:")), Gtk.Label(label=channels))
    row5 = get_two_column_box(get_bold_label(_("Audio Sample Rate:")), Gtk.Label(label=frequency))
    row6 = get_two_column_box(get_bold_label(_("Best Profile:")), Gtk.Label(label=match_profile_name))
    row7 = get_two_column_box(get_bold_label(_("Matches Project Profile:")), Gtk.Label(label=matches_current_profile))
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(img, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(12, 16), False, False, 0)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(row00, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row111, False, False, 0)
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    
    return vbox
    
def get_clip_properties_panel(data):
    mark_in, mark_out, length, size, path, vcodec, acodec = data

    row0 = get_two_column_box(get_bold_label(_("Mark In:")), Gtk.Label(label=mark_in))
    row00 = get_two_column_box(get_bold_label(_("Mark Out:")), Gtk.Label(label=mark_out))
    row1 = get_two_column_box(get_bold_label(_("Clip Length:")), Gtk.Label(label=length))
    row2 = get_two_column_box(get_bold_label(_("Image Size:")), Gtk.Label(label=size))
    row3 = get_two_column_box(get_bold_label(_("Media Path:")), Gtk.Label(label=path))
    row4 = get_two_column_box(get_bold_label(_("Video Codec:")), Gtk.Label(label=vcodec))
    row5 = get_two_column_box(get_bold_label(_("Audio Codec:")), Gtk.Label(label=acodec))
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(row00, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    
    return vbox   

def get_add_compositor_panel(current_sequence, data):
    clip, track, compositor_index, clip_index = data
    track_combo = Gtk.ComboBoxText()
    
    default_track_index = -1
    for i in range(current_sequence.first_video_index, track.id):
        add_track = current_sequence.tracks[i]
        text = "Track " + utils.get_track_name(add_track, current_sequence)
        track_combo.append_text(text)
        default_track_index += 1
    track_combo.set_active(default_track_index)
    track_combo.set_size_request(HALF_ROW_WIDTH, 30)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_two_column_box(Gtk.Label(label=_("Composite clip on:")), track_combo), False, False, 0)
    return (vbox, track_combo)

def get_transition_panel(trans_data):
    type_combo_box = Gtk.ComboBoxText()
    name, t_service_id = mlttransitions.rendered_transitions[0]
    type_combo_box.append_text(name)
    name, t_service_id = mlttransitions.rendered_transitions[1]
    type_combo_box.append_text(name)
    name, t_service_id = mlttransitions.rendered_transitions[2]
    type_combo_box.append_text(name)
    type_combo_box.set_active(0)

    type_row = get_two_column_box(Gtk.Label(label=_("Type:")), 
                                 type_combo_box)

    wipe_luma_combo_box = Gtk.ComboBoxText()
    keys = mlttransitions.wipe_lumas.keys()
    keys.sort()
    for k in keys:
        wipe_luma_combo_box.append_text(k)
    wipe_luma_combo_box.set_active(0)
    wipe_label = Gtk.Label(label=_("Wipe Pattern:"))
    wipe_row = get_two_column_box(wipe_label, 
                                 wipe_luma_combo_box)

    color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(0,0,0,1))
    color_button_box = guiutils.get_left_justified_box([color_button])
    color_label = Gtk.Label(label=_("Dip Color:"))
    color_row = get_two_column_box(color_label, color_button_box)

    wipe_luma_combo_box.set_sensitive(False)
    color_button.set_sensitive(False)
    wipe_label.set_sensitive(False)
    color_label.set_sensitive(False)

    transition_type_widgets = (type_combo_box, wipe_luma_combo_box, color_button, wipe_label, color_label)
    type_combo_box.connect("changed", 
                              lambda w,e: _transition_type_changed(transition_type_widgets), 
                              None)
                              
    length_entry = Gtk.Entry()
    trans_length = 30
    if editorstate.transition_length > 0: # use last invocation length if available
        trans_length = editorstate.transition_length
    length_entry.set_text(str(trans_length))    
    length_row = get_two_column_box(Gtk.Label(label=_("Length:")), 
                                    length_entry)

    filler = Gtk.Label()
    filler.set_size_request(10,10)

    out_clip_label = Gtk.Label(label=_("First Clip Out Handle:"))
    out_clip_value = Gtk.Label(label=str(trans_data["from_handle"]) + _(" frame(s)"))
    
    in_clip_label = Gtk.Label(label=_("Second Clip In Handle:"))
    in_clip_value = Gtk.Label(label=str(trans_data["to_handle"]) + _(" frame(s)"))
    
    out_handle_row = get_two_column_box(out_clip_label, 
                                        out_clip_value)
    in_handle_row = get_two_column_box(in_clip_label, 
                                       in_clip_value)

    # Encoding widgets
    encodings_cb = Gtk.ComboBoxText()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = Gtk.ComboBoxText()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets, 10)
    
    _set_saved_encoding(transition_widgets)
    
    # Build panel
    edit_vbox = Gtk.VBox(False, 2)
    edit_vbox.pack_start(type_row, False, False, 0)
    edit_vbox.pack_start(length_row, False, False, 0)
    edit_vbox.pack_start(wipe_row, False, False, 0)
    edit_vbox.pack_start(color_row, False, False, 0)

    data_vbox = Gtk.VBox(False, 2)
    data_vbox.pack_start(out_handle_row, False, False, 0)
    data_vbox.pack_start(in_handle_row, False, False, 0)
    
    enconding_vbox = Gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Transition Options"),  edit_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Media Overlap info"),  data_vbox), True, True, 0)

    alignment = guiutils.set_margins(vbox, 12, 24, 12, 12)

    return (alignment, type_combo_box, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, color_button)

def get_transition_re_render_panel(trans_data):
    transition_length = trans_data["clip"] .clip_out - trans_data["clip"].clip_in + 1 # +1 out inclusive
    transition_length_label = Gtk.Label(label=_("Length:"))
    transition_length_value = Gtk.Label(label=str(transition_length))
    transition_length_row = get_two_column_box(transition_length_label, transition_length_value)

    # Encoding widgets
    encodings_cb = Gtk.ComboBoxText()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = Gtk.ComboBoxText()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets, 10)
    
    _set_saved_encoding(transition_widgets)

    transition_vbox = Gtk.VBox(False, 2)
    transition_vbox.pack_start(transition_length_row, False, False, 0)
   
    enconding_vbox = Gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Transition"),  transition_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox), True, True, 0)

    alignment = guiutils.set_margins(vbox, 12, 24, 12, 12)
    alignment.set_size_request(450, 200)
    
    return (alignment, encodings_cb, quality_cb)

def get_fade_re_render_panel(trans_data):
    fade_length = trans_data["clip"] .clip_out - trans_data["clip"].clip_in + 1 # +1 out inclusive
    fade_length_label = Gtk.Label(label=_("Length:"))
    fade_length_value = Gtk.Label(label=str(fade_length))
    fade_length_row = get_two_column_box(fade_length_label, fade_length_value)

    # Encoding widgets
    encodings_cb = Gtk.ComboBoxText()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = Gtk.ComboBoxText()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets, 10)
    
    _set_saved_encoding(transition_widgets)

    fade_vbox = Gtk.VBox(False, 2)
    fade_vbox.pack_start(fade_length_row, False, False, 0)
   
    enconding_vbox = Gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Fade"),  fade_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox), True, True, 0)

    alignment = guiutils.set_margins(vbox, 12, 24, 12, 12)
    alignment.set_size_request(450, 200)
    
    return (alignment, encodings_cb, quality_cb)

def get_re_render_all_panel(rerender_list, unrenderable):
    rerendercount_label = Gtk.Label(label=_("Transitions / Fades to be rerendered:"))
    rerendercount_value = Gtk.Label(label=str(len(rerender_list)))
    rerendercount_row = get_two_column_box(rerendercount_label, rerendercount_value)
    
    if unrenderable > 0:
        unrenderable_info = _("There are ") + str(unrenderable) + _(" Transitions / Fades that cannot be rerendered, either because they are\ncreated with Flowblade version <=1.14 or the source clips are no longer on timeline.")
        unrenderable_info_label = Gtk.Label(unrenderable_info)
        
    info_vbox = Gtk.VBox(False, 2)
    info_vbox.pack_start(rerendercount_row, False, False, 0)
    if unrenderable > 0:
        info_vbox.pack_start(guiutils.pad_label(12,12), False, False, 0)
        info_vbox.pack_start(unrenderable_info_label, False, False, 0)
    
    # Encoding widgets
    encodings_cb = Gtk.ComboBoxText()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = Gtk.ComboBoxText()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets, 10)
    
    _set_saved_encoding(transition_widgets)
   
    enconding_vbox = Gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Info"),  info_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox), True, True, 0)

    alignment = guiutils.set_margins(vbox, 12, 24, 12, 12)
    alignment.set_size_request(450, 120)
    
    return (alignment, encodings_cb, quality_cb)
    
def get_fade_panel(fade_data):
    type_combo_box = Gtk.ComboBoxText()    
    type_combo_box.append_text(_("Fade In"))
    type_combo_box.append_text(_("Fade Out"))
    type_combo_box.set_active(0)

    type_row = get_two_column_box(Gtk.Label(label=_("Type:")), 
                                 type_combo_box)
        
    color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(0,0,0,1))
    color_button_box = guiutils.get_left_justified_box([color_button])
    color_label = Gtk.Label(label=_("Color:"))
    color_row = get_two_column_box(color_label, color_button_box)
                              
    length_entry = Gtk.Entry()
    fade_length = 30
    if editorstate.fade_length > 0: # use last invocation length if available
        fade_length = editorstate.fade_length
    length_entry.set_text(str(fade_length))    
    length_row = get_two_column_box(Gtk.Label(label=_("Length:")), 
                                    length_entry)

    # Encoding widgets
    encodings_cb = Gtk.ComboBoxText()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = Gtk.ComboBoxText()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)

    _fill_transition_quality_combo_box(transition_widgets, 10)
    _set_saved_encoding(transition_widgets)
    
    
    # Build panel
    edit_vbox = Gtk.VBox(False, 2)
    edit_vbox.pack_start(type_row, False, False, 0)
    edit_vbox.pack_start(length_row, False, False, 0)
    edit_vbox.pack_start(color_row, False, False, 0)

    enconding_vbox = Gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Transition Options"),  edit_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox), True, True, 0)

    alignment = guiutils.set_margins(vbox, 12, 24, 12, 12)
    
    return (alignment, type_combo_box, length_entry, encodings_cb, quality_cb, color_button)
    
def _transition_encoding_changed(widgets):
    _fill_transition_quality_combo_box(widgets)
 
def _fill_transition_quality_combo_box(widgets, quality_index=-1):
    encodings_cb, quality_cb = widgets
    enc_index = encodings_cb.get_active()
    encoding = renderconsumer.encoding_options[enc_index]

    quality_cb.get_model().clear()
    for quality_option in encoding.quality_options:
        quality_cb.append_text(quality_option.name)

    if quality_index == -1:
        if encoding.quality_default_index != None:
            quality_cb.set_active(encoding.quality_default_index)
        else:
            quality_cb.set_active(0)
    else:
            quality_cb.set_active(quality_index)
            
def _set_saved_encoding(transition_widgets):
    saved_encoding = editorstate.PROJECT().get_project_property(appconsts.P_PROP_TRANSITION_ENCODING)
    if saved_encoding != None:
        encodings_cb, quality_cb = transition_widgets
        enc_index, quality_index = saved_encoding
        encodings_cb.set_active(enc_index)
        quality_cb.set_active(quality_index)
    
def _transition_type_changed(transition_type_widgets):
    type_combo_box, wipe_luma_combo_box, color_button, wipe_label, color_label = transition_type_widgets
    if type_combo_box.get_active() == 0:
        wipe_luma_combo_box.set_sensitive(False)
        color_button.set_sensitive(False)
        wipe_label.set_sensitive(False)
        color_label.set_sensitive(False)
    elif type_combo_box.get_active() == 1:
        wipe_luma_combo_box.set_sensitive(True)
        color_button.set_sensitive(False)
        wipe_label.set_sensitive(True)
        color_label.set_sensitive(False)
    else:
        wipe_luma_combo_box.set_sensitive(False)
        color_button.set_sensitive(True)
        wipe_label.set_sensitive(False)
        color_label.set_sensitive(True)
    
# -------------------------------------------------- guiutils
def get_bold_label(text):
    return guiutils.bold_label(text)

def get_left_justified_box(widgets):
    return guiutils.get_left_justified_box(widgets)

def get_two_column_box(widget1, widget2, left_width=HALF_ROW_WIDTH):
    return guiutils.get_two_column_box(widget1, widget2, left_width)
