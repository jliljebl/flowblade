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

import pygtk
pygtk.require('2.0');
import gtk

import gui
import guicomponents
import guiutils
import editorpersistance
import mlttransitions
import renderconsumer
import respaths
import utils


HALF_ROW_WIDTH = 160 # Size of half row when using two column row components created here
EFFECT_PANEL_WIDTH_PAD = 20 # This is subtracted from notebgtk.Calendar ook width to get some component widths
TC_LABEL_WIDTH = 80 # in, out and length timecodes in monitor area top row 

MEDIA_PANEL_MIN_ROWS = 2
MEDIA_PANEL_MAX_ROWS = 8
MEDIA_PANEL_DEFAULT_ROWS = 2


def get_media_files_panel(media_list_view, add_cb, del_cb, col_changed_cb, proxy_cb, filtering_cb):
    # Create buttons and connect signals
    add_media_b = gtk.Button(_("Add"))
    del_media_b = gtk.Button(_("Delete"))    
    add_media_b.connect("clicked", add_cb, None)
    del_media_b.connect("clicked", del_cb, None)
    add_media_b.set_tooltip_text(_("Add Media File to Bin"))
    del_media_b.set_tooltip_text(_("Delete Media File from Bin"))

    proxy_b = gtk.Button()
    proxy_b.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "proxy_button.png"))
    proxy_b.connect("clicked", proxy_cb, None)
    proxy_b.set_tooltip_text(_("Render Proxy Files For Selected Media"))
    gui.proxy_button = proxy_b

    columns_img = gtk.image_new_from_file(respaths.IMAGE_PATH + "columns.png")
        
    adj = gtk.Adjustment(value=editorpersistance.prefs.media_columns, lower=MEDIA_PANEL_MIN_ROWS, upper=MEDIA_PANEL_MAX_ROWS, step_incr=1)
    spin = gtk.SpinButton(adj)
    spin.set_numeric(True)
    spin.set_size_request(40, 30)
    spin.connect("changed", col_changed_cb)

    all_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_all_files.png")
    audio_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_audio_files.png")
    graphics_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_graphics_files.png")
    video_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_video_files.png")
    imgseq_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_imgseq_files.png")
    pattern_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "show_pattern_producers.png")

    files_filter_launcher = guicomponents.ImageMenuLaunch(filtering_cb, [all_pixbuf, video_pixbuf, audio_pixbuf, graphics_pixbuf, imgseq_pixbuf, pattern_pixbuf], 20, 22)
    files_filter_launcher.pixbuf_x  = 3
    files_filter_launcher.pixbuf_y  = 9
    gui.media_view_filter_selector = files_filter_launcher

    buttons_box = gtk.HBox(False,1)
    buttons_box.pack_start(add_media_b, True, True, 0)
    buttons_box.pack_start(del_media_b, True, True, 0)
    buttons_box.pack_start(proxy_b, False, False, 0)
    buttons_box.pack_start(guiutils.get_pad_label(4, 4), False, False, 0)
    buttons_box.pack_start(columns_img, False, False, 0)
    buttons_box.pack_start(spin, False, False, 0)
    buttons_box.pack_start(files_filter_launcher.widget, False, False, 0)
    
    panel = gtk.VBox()
    panel.pack_start(buttons_box, False, True, 0)
    panel.pack_start(media_list_view, True, True, 0)
    
    out_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    out_align.set_padding(4, 4, 0, 4)
    out_align.add(panel)
    
    return out_align

def get_bins_panel(bin_list_view, add_cb, delete_cb):
    # Create buttons and connect signals
    add_b = gtk.Button(_("Add"))
    del_b = gtk.Button(_("Delete"))
    add_b.connect("clicked", add_cb, None)
    del_b.connect("clicked", delete_cb, None)
    add_b.set_tooltip_text(_("Add Bin to Project"))
    del_b.set_tooltip_text(_("Delete Bin from Project"))
    buttons_box = gtk.HBox(True,1)
    buttons_box.pack_start(add_b)
    buttons_box.pack_start(del_b)
    
    panel = gtk.VBox()
    panel.pack_start(buttons_box, False, True, 0)
    panel.pack_start(bin_list_view, True, True, 0)

    return get_named_frame(_("Bins"), panel, 0, 0, 0)

def get_sequences_panel(sequence_list_view, edit_seq_cb, add_seq_cb, del_seq_cb):
    # Create buttons and connect signals
    add_b = gtk.Button(_("Add"))
    del_b = gtk.Button(_("Delete"))
    edit_b = gtk.Button(_("Edit"))
    add_b.set_tooltip_text(_("Add new Sequence to Project"))
    del_b.set_tooltip_text(_("Delete Sequence from Project"))
    edit_b.set_tooltip_text(_("Start editing Sequence"))
    edit_b.connect("clicked", edit_seq_cb, None)
    add_b.connect("clicked", add_seq_cb, None)
    del_b.connect("clicked", del_seq_cb, None)

    buttons_box = gtk.HBox(True,1)
    buttons_box.pack_start(edit_b)
    buttons_box.pack_start(add_b)
    buttons_box.pack_start(del_b)
    
    panel = gtk.VBox()
    panel.pack_start(buttons_box, False, True, 0)
    panel.pack_start(sequence_list_view, True, True, 0)

    return get_named_frame(_("Sequences"), panel, 4)

"""
def get_profile_info_panel(profile):
    desc_label = gtk.Label(profile.description())
    info = guicomponents.get_profile_info_small_box(profile)
    panel = gtk.VBox()
    panel.pack_start(guiutils.get_left_justified_box([desc_label]), False, True, 0)
    panel.pack_start(info, False, True, 0)
    return get_named_frame(_("Profile"), panel, 4)
"""
"""
def get_project_name_panel(project_name):
    name_row = get_left_justified_box([gtk.Label(project_name)])
    return get_named_frame(_("Name"), name_row, 4)
"""

def get_thumbnail_select_panel(current_folder_path):    
    texts_panel = get_two_text_panel(_("Select folder for new thumbnails."), 
                                     _("Old thumbnails in this or other projects will") + 
                                     _(" still be available,\nthis only affects thumnails that are created for new media.\n") + 
                                     _("\nSetting your home folder as thumbnails folder is not allowed."))

    out_folder = gtk.FileChooserButton("Select Folder")
    out_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    if current_folder_path != None:
        out_folder.set_current_folder(current_folder_path)
    
    out_folder_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    out_folder_align.set_padding(12, 24, 12, 12)
    out_folder_align.add(out_folder)
    
    panel = gtk.VBox()
    panel.pack_start(texts_panel, False, False, 0)
    panel.pack_start(out_folder_align, False, False, 0)
    
    return (panel, out_folder)

def get_render_folder_select_panel(current_folder_path):    
    texts_panel = get_two_text_panel(_("Select folder for rendered clips."), 
                                     _("Old rendered clips in this or other projects will") + 
                                     _(" still be available,\nthis only affects rendered files that are created from now on.\n") + 
                                     _("\nSetting your home folder as folder for rendered clips is not allowed."))
        
    out_folder = gtk.FileChooserButton("Select Folder")
    out_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    if current_folder_path != None:
        out_folder.set_current_folder(current_folder_path)

    out_folder_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    out_folder_align.set_padding(12, 24, 12, 12)
    out_folder_align.add(out_folder)
    
    panel = gtk.VBox()
    panel.pack_start(texts_panel, False, False, 0)
    panel.pack_start(out_folder_align, False, False, 0)
    
    return (panel, out_folder)

def _set_sensive_widgets(sensitive, list):
    for widget in list:
        widget.set_sensitive(sensitive)

def get_motion_render_progress_panel(file_name, progress_bar):
    status_box = gtk.HBox(False, 2)
    status_box.pack_start(gtk.Label(file_name),False, False, 0)
    status_box.pack_start(gtk.Label(), True, True, 0)

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(progress_bar, False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)
    return alignment
    
def get_named_frame(name, widget, left_padding=12, right_padding=6, right_out_padding=4):
    """
    Gnome style named panel
    """
    if name != None:
        label = guiutils.bold_label(name)
        label.set_justify(gtk.JUSTIFY_LEFT)
        
        label_box = gtk.HBox()
        label_box.pack_start(label, False, False, 0)
        label_box.pack_start(gtk.Label(), True, True, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(right_padding, 0, left_padding, 0)
    alignment.add(widget)
    
    frame = gtk.VBox()
    if name != None:
        frame.pack_start(label_box, False, False, 0)
    frame.pack_start(alignment, True, True, 0)
    
    out_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    out_align.set_padding(4, 4, 0, right_out_padding)
    out_align.add(frame)
    
    return out_align

def get_two_text_panel(primary_txt, secondary_txt):
    p_label = guiutils.bold_label(primary_txt)
    s_label = gtk.Label(secondary_txt)
    texts_pad = gtk.Label()
    texts_pad.set_size_request(12,12)

    pbox = gtk.HBox(False, 1)
    pbox.pack_start(p_label, False, False, 0)
    pbox.pack_start(gtk.Label(), True, True, 0)

    sbox = gtk.HBox(False, 1)
    sbox.pack_start(s_label, False, False, 0)
    sbox.pack_start(gtk.Label(), True, True, 0)
    
    text_box = gtk.VBox(False, 0)
    text_box.pack_start(pbox, False, False, 0)
    text_box.pack_start(texts_pad, False, False, 0)
    text_box.pack_start(sbox, False, False, 0)
    text_box.pack_start(gtk.Label(), True, True, 0)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(text_box)
    
    return align

def get_file_properties_panel(data):
    media_file, img, size, length, vcodec, acodec, channels, frequency, fps = data
    
    row0 = get_two_column_box(get_bold_label(_("Name:")), gtk.Label(media_file.name))
    row00 = get_two_column_box(get_bold_label(_("Path:")), gtk.Label(media_file.path))
    row1 = get_two_column_box(get_bold_label(_("Image Size:")), gtk.Label(size))
    row111 = get_two_column_box(get_bold_label(_("Frames Per Second:")), gtk.Label(fps))
    row11 = get_two_column_box(get_bold_label(_("Playtime:")), gtk.Label(length))
    row2 = get_two_column_box(get_bold_label(_("Video Codec:")), gtk.Label(vcodec))
    row3 = get_two_column_box(get_bold_label(_("Audio Codec:")), gtk.Label(acodec))
    row4 = get_two_column_box(get_bold_label(_("Audio Channels:")), gtk.Label(channels))
    row5 = get_two_column_box(get_bold_label(_("Audio Sample Rate:")), gtk.Label(frequency))
    
    vbox = gtk.VBox(False, 2)
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
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    return vbox
    
def get_clip_properties_panel(data):
    length, size, path, vcodec, acodec = data
    
    row1 = get_two_column_box(get_bold_label(_("Clip Length:")), gtk.Label(length))
    row2 = get_two_column_box(get_bold_label(_("Image Size:")), gtk.Label(size))
    row3 = get_two_column_box(get_bold_label(_("Media Path:")), gtk.Label(path))
    row4 = get_two_column_box(get_bold_label(_("Video Codec:")), gtk.Label(vcodec))
    row5 = get_two_column_box(get_bold_label(_("Audio Codec:")), gtk.Label(acodec))
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    return vbox   

def get_add_compositor_panel(current_sequence, data):
    clip, track, compositor_index, clip_index = data
    track_combo = gtk.combo_box_new_text()
    
    default_track_index = -1
    for i in range(current_sequence.first_video_index, track.id):
        add_track = current_sequence.tracks[i]
        text = "Track " + utils.get_track_name(add_track, current_sequence)
        track_combo.append_text(text)
        default_track_index += 1
    track_combo.set_active(default_track_index)
    track_combo.set_size_request(HALF_ROW_WIDTH, 30)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(get_two_column_box(gtk.Label(_("Composite clip on:")), track_combo), False, False, 0)
    return (vbox, track_combo)

def get_transition_panel(trans_data):
    type_combo_box = gtk.combo_box_new_text()
    name, t_service_id = mlttransitions.rendered_transitions[0]
    type_combo_box.append_text(name)
    name, t_service_id = mlttransitions.rendered_transitions[1]
    type_combo_box.append_text(name)
    name, t_service_id = mlttransitions.rendered_transitions[2]
    type_combo_box.append_text(name)
    type_combo_box.set_active(0)

    type_row = get_two_column_box(gtk.Label(_("Type:")), 
                                 type_combo_box)

    wipe_luma_combo_box = gtk.combo_box_new_text()
    keys = mlttransitions.wipe_lumas.keys()
    keys.sort()
    for k in keys:
        wipe_luma_combo_box.append_text(k)
    wipe_luma_combo_box.set_active(0)
    wipe_label = gtk.Label(_("Wipe Pattern:"))
    wipe_row = get_two_column_box(wipe_label, 
                                 wipe_luma_combo_box)

    color_button = gtk.ColorButton(gtk.gdk.Color(0.0, 0.0, 0.0))
    color_button_box = guiutils.get_left_justified_box([color_button])
    color_label = gtk.Label(_("Dip Color:"))
    color_row = get_two_column_box(color_label, color_button_box)

    wipe_luma_combo_box.set_sensitive(False)
    color_button.set_sensitive(False)
    wipe_label.set_sensitive(False)
    color_label.set_sensitive(False)

    transition_type_widgets = (type_combo_box, wipe_luma_combo_box, color_button, wipe_label, color_label)
    type_combo_box.connect("changed", 
                              lambda w,e: _transition_type_changed(transition_type_widgets), 
                              None)
                              
    length_entry = gtk.Entry()
    length_entry.set_text(str(30))    
    length_row = get_two_column_box(gtk.Label(_("Length:")), 
                                    length_entry)

    filler = gtk.Label()
    filler.set_size_request(10,10)

    out_clip_label = gtk.Label(_("From Clip Handle:"))
    out_clip_value = gtk.Label(trans_data["from_handle"])
    
    in_clip_label = gtk.Label(_("To Clip Handle:"))
    in_clip_value = gtk.Label(trans_data["to_handle"])
    
    max_label = gtk.Label(_("Max. Transition Length:"))
    max_value = gtk.Label(trans_data["max_length"])

    out_handle_row = get_two_column_box(out_clip_label, 
                                        out_clip_value)
    in_handle_row = get_two_column_box(in_clip_label, 
                                       in_clip_value)
    max_row = get_two_column_box(max_label, 
                                 max_value)

    # Encoding widgets
    encodings_cb = gtk.combo_box_new_text()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = gtk.combo_box_new_text()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets)
    
    # Build panel
    edit_vbox = gtk.VBox(False, 2)
    edit_vbox.pack_start(type_row, False, False, 0)
    edit_vbox.pack_start(length_row, False, False, 0)
    edit_vbox.pack_start(wipe_row, False, False, 0)
    edit_vbox.pack_start(color_row, False, False, 0)

    data_vbox = gtk.VBox(False, 2)
    data_vbox.pack_start(out_handle_row, False, False, 0)
    data_vbox.pack_start(in_handle_row, False, False, 0)
    data_vbox.pack_start(max_row, False, False, 0)
    
    enconding_vbox = gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Transition Options"),  edit_vbox))
    vbox.pack_start(get_named_frame(_("Clips info"),  data_vbox))
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox))

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 24, 12, 12)
    alignment.add(vbox)
    return (alignment, type_combo_box, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, color_button)

def get_fade_panel(fade_data):
    type_combo_box = gtk.combo_box_new_text()    
    type_combo_box.append_text(_("Fade In"))
    type_combo_box.append_text(_("Fade Out"))
    type_combo_box.set_active(0)

    type_row = get_two_column_box(gtk.Label(_("Type:")), 
                                 type_combo_box)

    color_button = gtk.ColorButton(gtk.gdk.Color(0.0, 0.0, 0.0))
    color_button_box = guiutils.get_left_justified_box([color_button])
    color_label = gtk.Label(_("Color:"))
    color_row = get_two_column_box(color_label, color_button_box)
                              
    length_entry = gtk.Entry()
    length_entry.set_text(str(30))    
    length_row = get_two_column_box(gtk.Label(_("Length:")), 
                                    length_entry)

    # Encoding widgets
    encodings_cb = gtk.combo_box_new_text()
    for encoding in renderconsumer.encoding_options:
        encodings_cb.append_text(encoding.name)
    encodings_cb.set_active(0)

    quality_cb = gtk.combo_box_new_text()
    transition_widgets = (encodings_cb, quality_cb)
    encodings_cb.connect("changed", 
                              lambda w,e: _transition_encoding_changed(transition_widgets), 
                              None)
    _fill_transition_quality_combo_box(transition_widgets)
    
    # Build panel
    edit_vbox = gtk.VBox(False, 2)
    edit_vbox.pack_start(type_row, False, False, 0)
    edit_vbox.pack_start(length_row, False, False, 0)
    edit_vbox.pack_start(color_row, False, False, 0)

    enconding_vbox = gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame(_("Transition Options"),  edit_vbox))
    vbox.pack_start(get_named_frame(_("Encoding"),  enconding_vbox))

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 24, 12, 12)
    alignment.add(vbox)
    return (alignment, type_combo_box, length_entry, encodings_cb, quality_cb, color_button)
    
def _transition_encoding_changed(widgets):
    _fill_transition_quality_combo_box(widgets)
 
def _fill_transition_quality_combo_box(widgets):
    encodings_cb, quality_cb = widgets
    enc_index = encodings_cb.get_active()
    encoding = renderconsumer.encoding_options[enc_index]

    quality_cb.get_model().clear()
    for quality_option in encoding.quality_options:
        quality_cb.append_text(quality_option.name)

    if encoding.quality_default_index != None:
        quality_cb.set_active(encoding.quality_default_index)
    else:
        quality_cb.set_active(0)

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
