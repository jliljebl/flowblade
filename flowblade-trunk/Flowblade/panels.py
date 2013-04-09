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

import gtk
import os
import pango

import appconsts
import guicomponents
import guiutils
import clipeffectseditor
import compositeeditor
import editorstate
import editorpersistance
import mltfilters
import mltprofiles
import mlttransitions
import render
import renderconsumer
import respaths
import utils


HALF_ROW_WIDTH = 160 # Size of half row when using two column row components created here
EFFECT_PANEL_WIDTH_PAD = 20 # This is subtracted from notebook width to get some component widths
PREFERENCES_LEFT = 290 # label column of preferences panel
PROFILE_MANAGER_LEFT = 265 # label column of profile manager panel
FFMPEG_VIEW_SIZE = (200, 210) # Text edit area size for render opts, width 200 seems to be ignored in current layout
TC_LABEL_WIDTH = 80 # in, out and length timecodes in monitor area top row 
COMPOSITOR_PANEL_LEFT_WIDTH = 160

MEDIA_PANEL_MIN_ROWS = 2
MEDIA_PANEL_MAX_ROWS = 8
MEDIA_PANEL_DEFAULT_ROWS = 2


def get_media_files_panel(media_list_view, add_cb, del_cb, col_changed_cb):
    # Create buttons and connect signals
    add_media_b = gtk.Button(_("Add"))
    del_media_b = gtk.Button(_("Delete"))    
    add_media_b.connect("clicked", add_cb, None)
    del_media_b.connect("clicked", del_cb, None)
    add_media_b.set_tooltip_text(_("Add Media File to Bin"))
    del_media_b.set_tooltip_text(_("Delete Media File from Bin"))

    columns_img = gtk.image_new_from_file(respaths.IMAGE_PATH + "columns.png")
        
    adj = gtk.Adjustment(value=editorpersistance.prefs.media_columns, lower=MEDIA_PANEL_MIN_ROWS, upper=MEDIA_PANEL_MAX_ROWS, step_incr=1)
    spin = gtk.SpinButton(adj)
    spin.connect("changed", col_changed_cb)

    buttons_box = gtk.HBox(False,1)
    buttons_box.pack_start(add_media_b, True, True, 0)
    buttons_box.pack_start(del_media_b, True, True, 0)
    buttons_box.pack_start(guiutils.get_pad_label(4, 4), False, False, 0)
    buttons_box.pack_start(columns_img, False, False, 0)
    buttons_box.pack_start(spin, False, False, 0)
    
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

    return get_named_frame(_("Sequences"), panel)

"""
def get_profile_info_panel(profile):
    hbox = guicomponents.get_profile_info_box(profile, True)
    return get_named_frame(_("Profile"), hbox)
"""

def get_profile_info_panel(profile):
    desc_label = gtk.Label(profile.description())
    info = guicomponents.get_profile_info_small_box(profile)
    panel = gtk.VBox()
    panel.pack_start(guiutils.get_left_justified_box([desc_label]), False, True, 0)
    panel.pack_start(info, False, True, 0)
    return get_named_frame(_("Profile"), panel)
    
def get_media_log_events_panel(events_list_view):
    auto_log_mode_combo = gtk.combo_box_new_text()
    auto_log_mode_combo.append_text(_("All Events"))
    auto_log_mode_combo.append_text(_("Insert Events"))
    auto_log_mode_combo.append_text(_("Range Events"))
    auto_log_mode_combo.set_active(0)
    delete_b = gtk.Button(_("Delete"))  
    row1 =  gtk.HBox()
    row1.pack_start(auto_log_mode_combo, False, True, 0)
    row1.pack_start(gtk.Label(), True, True, 0)
    row1.pack_start(delete_b, False, True, 0)

    logging_type_combo = gtk.combo_box_new_text()
    logging_type_combo.append_text(_("Auto Log All"))
    logging_type_combo.append_text(_("Auto Log Inserts"))
    logging_type_combo.append_text(_("Auto Log Ranges"))
    logging_type_combo.append_text(_("Manual Logging"))
    logging_type_combo.set_active(0)
    log_insert = gtk.Button(_("Log Insert"))
    log_range = gtk.Button(_("Log Range"))
    row2 =  gtk.HBox()
    row2.pack_start(logging_type_combo, False, True, 0)
    row2.pack_start(gtk.Label(), True, True, 0)
    row2.pack_start(log_insert, False, True, 0)
    row2.pack_start(log_range, False, True, 0)

    panel = gtk.VBox()
    panel.pack_start(row1, False, True, 0)
    panel.pack_start(events_list_view, True, True, 0)
    panel.pack_start(row2, False, True, 0)
    panel.set_size_request(400, 200)

    return get_named_frame(_("Media Log"), panel, 0, 0, 0)

def get_project_name_panel(project_name):
    name_row = get_left_justified_box([gtk.Label(project_name)])
    return get_named_frame(_("Name"), name_row)

def get_render_panel_left(editor_window, add_audio_panel):
    try:
        render.create_widgets()
    except IndexError:
        print "No rendering options found"
        return None
        
    out_folder_row = get_two_column_box(gtk.Label(_("Folder:")),
                              render.widgets.out_folder, 60)
    name_box = gtk.HBox(False, 8)
    name_box.pack_start(render.widgets.movie_name, True, True, 0)
    name_box.pack_start(render.widgets.extension_label, False, False, 0)    
    movie_name_row = get_two_column_box(gtk.Label(_("Name:")), name_box, 60)

    options_vbox = gtk.VBox(False, 2)
    options_vbox.pack_start(out_folder_row, False, False, 0)
    options_vbox.pack_start(movie_name_row, False, False, 0)

    file_opts_panel = get_named_frame(_("File"), options_vbox)
    
    quality_row = get_two_column_box(render.widgets.quality_label,
                                     render.widgets.quality_cb, 
                                     80)

    render_type_vbox = gtk.VBox(False, 2)
    render_type_vbox.pack_start(get_two_column_box(render.widgets.type_label,
                                                   render.widgets.type_combo,
                                                   80), 
                                False, False, 0)
    render_type_vbox.pack_start(get_two_column_box(render.widgets.presets_label,
                                                   render.widgets.preset_encodings_cb,
                                                   80),
                                False, False, 0)
    render_type_panel = get_named_frame(_("Render Type"), render_type_vbox)

    use_project_profile_row = gtk.HBox()
    use_project_profile_row.pack_start(render.widgets.use_project_label,  False, False, 0)
    use_project_profile_row.pack_start(render.widgets.use_project_profile_check,  False, False, 0)
    use_project_profile_row.pack_start(gtk.Label(), True, True, 0)

    profile_vbox = gtk.VBox(False, 2)
    profile_vbox.pack_start(use_project_profile_row, False, False, 0)
    profile_vbox.pack_start(render.widgets.out_profile_combo, False, False, 0)
    profile_vbox.pack_start(render.widgets.out_profile_info_box, False, False, 0)
    profile_panel = get_named_frame(_("Render Profile"), profile_vbox)

    if add_audio_panel:
        audio_panel = gtk.HBox()
        audio_panel.pack_start(render.widgets.audio_label, False, False, 0)
        audio_panel.pack_start(render.widgets.audio_desc, True, True, 0)
    
    encoding_vbox = gtk.VBox(False, 2)
    encoding_vbox.pack_start(render.widgets.encodings_cb, False, False, 0)
    encoding_vbox.pack_start(quality_row, False, False, 0)

    if add_audio_panel:
        encoding_vbox.pack_start(guiutils.get_pad_label(10, 2), False, False, 0)
        encoding_vbox.pack_start(audio_panel, False, False, 0)
    encoding_panel = get_named_frame(_("Encoding Format"), encoding_vbox)

    render_panel = gtk.VBox()
    render_panel.pack_start(file_opts_panel, False, False, 0)
    render_panel.pack_start(render_type_panel, False, False, 0)
    render_panel.pack_start(profile_panel, False, False, 0)
    render_panel.pack_start(encoding_panel, False, False, 0)
    render_panel.pack_start(gtk.Label(), True, True, 0)
    return render_panel

def get_render_panel_right(render_clicked_cb, normal_height):
    use_opts_row = gtk.HBox()
    use_opts_row.pack_start(render.widgets.use_args_label,  False, False, 0)
    use_opts_row.pack_start(render.widgets.use_opts_check,  False, False, 0)
    use_opts_row.pack_start(gtk.Label(), True, True, 0)
    use_opts_row.pack_start(render.widgets.opts_load_button,  False, False, 0)
    use_opts_row.pack_start(render.widgets.opts_save_button,  False, False, 0)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(render.widgets.opts_view)
    if normal_height:
        sw.set_size_request(*FFMPEG_VIEW_SIZE)
    else:
        w, h = FFMPEG_VIEW_SIZE
        h = h - 30
        sw.set_size_request(w, h)
        
    scroll_frame = gtk.Frame()
    scroll_frame.add(sw)
    
    opts_buttons_row = gtk.HBox(False)
    opts_buttons_row.pack_start(render.widgets.load_selection_button, False, False, 0)
    opts_buttons_row.pack_start(gtk.Label(), True, True, 0)

    opts_vbox = gtk.VBox(False, 2)
    opts_vbox.pack_start(use_opts_row , False, False, 0)
    opts_vbox.pack_start(scroll_frame, True, True, 0)
    opts_vbox.pack_start(opts_buttons_row, False, False, 0)
    opts_panel = get_named_frame(_("Render Args"), opts_vbox)

    bin_row = gtk.HBox()
    bin_row.pack_start(guiutils.get_pad_label(10, 8),  False, False, 0)
    bin_row.pack_start(gtk.Label(_("Open File in Bin:")),  False, False, 0)
    bin_row.pack_start(guiutils.get_pad_label(10, 2),  False, False, 0)
    bin_row.pack_start(render.widgets.open_in_bin,  False, False, 0)
    bin_row.pack_start(gtk.Label(), True, True, 0)

    range_row = gtk.HBox()
    range_row.pack_start(guiutils.get_pad_label(10, 8),  False, False, 0)
    range_row.pack_start(gtk.Label(_("Render Range:")),  False, False, 0)
    range_row.pack_start(guiutils.get_pad_label(10, 2),  False, False, 0)
    range_row.pack_start(render.widgets.range_cb,  True, True, 0)

    buttons_panel = gtk.HBox()
    buttons_panel.pack_start(guiutils.get_pad_label(10, 8), False, False, 0)
    buttons_panel.pack_start(render.widgets.reset_button, False, False, 0)
    buttons_panel.pack_start(gtk.Label(), True, True, 0)
    buttons_panel.pack_start(render.widgets.render_button, False, False, 0)

    render.widgets.render_button.connect("clicked", 
                                         render_clicked_cb, 
                                         None)

    render_panel = gtk.VBox()
    render_panel.pack_start(opts_panel, True, True, 0)
    render_panel.pack_start(guiutils.get_pad_label(10, 22), False, False, 0)
    render_panel.pack_start(bin_row, False, False, 0)
    render_panel.pack_start(range_row, False, False, 0)
    render_panel.pack_start(guiutils.get_pad_label(10, 12), False, False, 0)
    render_panel.pack_start(buttons_panel, False, False, 0)

    return render_panel

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
                                     _(" still be available,\nthis only affects thumnails that are created for new media.\n") + 
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
    
def get_render_progress_panel():
    status_box = gtk.HBox(False, 2)
    status_box.pack_start(render.widgets.status_label,False, False, 0)
    status_box.pack_start(gtk.Label(), True, True, 0)
    
    remaining_box = gtk.HBox(False, 2)
    remaining_box.pack_start(render.widgets.remaining_time_label,False, False, 0)
    remaining_box.pack_start(gtk.Label(), True, True, 0)

    passed_box = gtk.HBox(False, 2)
    passed_box.pack_start(render.widgets.passed_time_label,False, False, 0)
    passed_box.pack_start(gtk.Label(), True, True, 0)

    est_box = gtk.HBox(False, 2)
    est_box.pack_start(render.widgets.estimation_label,False, False, 0)
    est_box.pack_start(gtk.Label(), True, True, 0)

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(remaining_box, False, False, 0)
    progress_vbox.pack_start(passed_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(render.widgets.progress_bar, False, False, 0)
    progress_vbox.pack_start(est_box, False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)
    return alignment

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

def _group_selection_changed(group_combo, filters_list_view):
    group_name, filters_array = mltfilters.groups[group_combo.get_active()]
    filters_list_view.fill_data_model(filters_array)
    filters_list_view.treeview.get_selection().select_path("0")

def get_compositor_clip_panel():
    compositeeditor.create_widgets()
    
    compositor_vbox = gtk.VBox(False, 2)
    compositor_vbox.pack_start(compositeeditor.widgets.compositor_info, False, False, 0)
    compositor_vbox.pack_start(gtk.Label(), True, True, 0)
    compositor_vbox.pack_start(compositeeditor.widgets.reset_b, False, False, 0)
    compositor_vbox.pack_start(compositeeditor.widgets.delete_b, False, False, 0)
    compositor_vbox.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    compositor_vbox.set_size_request(COMPOSITOR_PANEL_LEFT_WIDTH, 200)

    compositeeditor.set_enabled(False)
    
    return compositor_vbox
                                    
def get_timecode_panel(editor_window):
    editor_window.tc = guicomponents.MonitorTCDisplay()
    editor_window.monitor_source = gtk.Label("sequence1")
    editor_window.monitor_source.set_ellipsize(pango.ELLIPSIZE_END)
    editor_window.mark_in_entry = gtk.Label()
    editor_window.mark_in_entry.set_text("--:--:--:--")
    editor_window.mark_in_entry.set_size_request(TC_LABEL_WIDTH, 20)
    editor_window.mark_out_entry = gtk.Label()
    editor_window.mark_out_entry.set_text("--:--:--:--")
    editor_window.mark_out_entry.set_size_request(TC_LABEL_WIDTH, 20)
    editor_window.length_entry = gtk.Label()
    editor_window.length_entry.set_text("--:--:--:--")
    editor_window.length_entry.set_size_request(TC_LABEL_WIDTH, 20)

    
    row = gtk.HBox(False, 1)
    #row.pack_start(guicomponents.get_monitor_view_select_combo(), False, False, 0)
    row.pack_start(editor_window.tc.widget, False, False, 0)
    row.pack_start(guiutils.get_pad_label(20, 20), False, False, 0)
    #row.pack_start(editor_window.monitor_source, True, True, 0)
    row.pack_start(gtk.Label(), False, False, 0)
    in_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "mark_in_label.png") 
    row.pack_start(in_icon, False, False, 0)
    row.pack_start(editor_window.mark_in_entry, False, False, 0)
    out_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "mark_out_label.png") 
    row.pack_start(out_icon, False, False, 0)
    row.pack_start(editor_window.mark_out_entry, False, False, 0)
    lengtht_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "marks_length_label.png") 
    row.pack_start(lengtht_icon, False, False, 0)
    row.pack_start(editor_window.length_entry, False, False, 0)

    return row

def get_clip_effects_editor_panel(group_combo_box, effects_list_view):
    """
    Use components created at clipeffectseditor.py.
    """
    clipeffectseditor.create_widgets()
    
    stack_buttons_box = gtk.HBox(True,1)
    stack_buttons_box.pack_start(clipeffectseditor.widgets.add_effect_b)
    stack_buttons_box.pack_start(clipeffectseditor.widgets.del_effect_b)
    
    effect_stack = clipeffectseditor.widgets.effect_stack_view    

    for group in mltfilters.groups:
        group_name, filters_array = group
        group_combo_box.append_text(group_name)
    group_combo_box.set_active(0)    

    # Same callback function works for filter select window too
    group_combo_box.connect("changed", 
                            lambda w,e: _group_selection_changed(w,effects_list_view), 
                            None)

    clipeffectseditor.widgets.group_combo = group_combo_box
    clipeffectseditor.widgets.effect_list_view = effects_list_view
    clipeffectseditor.set_enabled(False)
    
    combo_row = gtk.HBox(False, 2)
    combo_row.pack_start(group_combo_box, True, True, 0)
    combo_row.pack_start(guiutils.get_pad_label(8, 2), False, False, 0)
    combo_row.pack_start(clipeffectseditor.widgets.exit_button, False, False, 0)
   
    group_name, filters_array = mltfilters.groups[0]
    effects_list_view.fill_data_model(filters_array)
    effects_list_view.treeview.get_selection().select_path("0")
    
    effects_vbox = gtk.VBox(False, 2)
    effects_vbox.pack_start(clipeffectseditor.widgets.clip_info, False, False, 0)
    effects_vbox.pack_start(guiutils.get_pad_label(2, 2), False, False, 0)
    effects_vbox.pack_start(combo_row, False, False, 0)
    effects_vbox.pack_start(effects_list_view, True, True, 0)
    effects_vbox.pack_start(stack_buttons_box, False, False, 0)
    effects_vbox.pack_start(effect_stack, True, True, 0)

    clipeffectseditor.widgets.group_combo.set_tooltip_text(_("Select Filter Group"))
    clipeffectseditor.widgets.effect_list_view.set_tooltip_text(_("Current group Filters"))

    return effects_vbox
    
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

def get_color_clip_panel():
    name_entry = gtk.Entry()
    name_entry.set_text(_("Color Clip"))   

    color_button = gtk.ColorButton()

    cb_hbox = gtk.HBox(False, 0)
    cb_hbox.pack_start(color_button, False, False, 4)
    cb_hbox.pack_start(gtk.Label(), True, True, 0)

    row1 = get_two_column_box(gtk.Label(_("Clip Name")), name_entry)
    row2 = get_two_column_box(gtk.Label(_("Select Color")), cb_hbox)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (name_entry, color_button)

def get_general_options_panel(folder_select_clicked_cb, render_folder_select_clicked_cb):
    prefs = editorpersistance.prefs

    # Widgets
    open_in_last_opened_check = gtk.CheckButton()
    open_in_last_opened_check.set_active(prefs.open_in_last_opended_media_dir)
    
    default_profile_combo = gtk.combo_box_new_text()
    profiles = mltprofiles.get_profiles()
    for profile in profiles:
        default_profile_combo.append_text(profile[0])
    default_profile_combo.set_active( mltprofiles.get_default_profile_index())

    spin_adj = gtk.Adjustment(prefs.undos_max, editorpersistance.UNDO_STACK_MIN, editorpersistance.UNDO_STACK_MAX, 1)
    undo_max_spin = gtk.SpinButton(spin_adj)
    undo_max_spin.set_numeric(True)

    folder_select = gtk.Button(_("Select Folder")) # thumbnails
    folder_select.connect("clicked" , folder_select_clicked_cb)

    render_folder_select = gtk.Button(_("Select Folder"))
    render_folder_select.connect("clicked" , render_folder_select_clicked_cb)

    display_splash_check = gtk.CheckButton()
    display_splash_check.set_active(prefs.display_splash_screen)

    autosave_combo = gtk.combo_box_new_text()
    for i in range(0, len(editorpersistance.prefs.AUTO_SAVE_OPTS)):
        time, desc = editorpersistance.prefs.AUTO_SAVE_OPTS[i]
        autosave_combo.append_text(desc)
    autosave_combo.set_active(prefs.auto_save_delay_value_index)

    # Layout
    row1 = get_two_column_box(gtk.Label(_("Default Profile")), default_profile_combo, PREFERENCES_LEFT)
    row2 = get_two_column_box(gtk.Label(_("Remember last media directory")), open_in_last_opened_check, PREFERENCES_LEFT)
    row3 = get_two_column_box(gtk.Label(_("Undo stack size")), undo_max_spin, PREFERENCES_LEFT)
    row4 = get_two_column_box(gtk.Label(_("Thumbnail folder")), folder_select, PREFERENCES_LEFT)
    row5 = get_two_column_box(gtk.Label(_("Display splash screen")), display_splash_check, PREFERENCES_LEFT)
    row6 = get_two_column_box(gtk.Label(_("Autosave for crash recovery every")), autosave_combo, PREFERENCES_LEFT)
    row8 = get_two_column_box(gtk.Label(_("Rendered Clips folder")), render_folder_select, PREFERENCES_LEFT)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (default_profile_combo, open_in_last_opened_check, undo_max_spin, display_splash_check)

def get_edit_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    auto_play_in_clip_monitor = gtk.CheckButton()
    auto_play_in_clip_monitor.set_active(prefs.auto_play_in_clip_monitor)

    auto_center_on_stop = gtk.CheckButton()
    auto_center_on_stop.set_active(prefs.auto_center_on_play_stop)

    auto_move_on_edit = gtk.CheckButton()
    auto_move_on_edit.set_active(prefs.auto_move_after_edit)

    spin_adj = gtk.Adjustment(prefs.default_grfx_length, 1, 15000, 1)
    gfx_length_spin = gtk.SpinButton(spin_adj)
    gfx_length_spin.set_numeric(True)
    
    # Layout
    row1 = get_two_column_box(gtk.Label(_("Autoplay new Clips in Clip Monitor")), auto_play_in_clip_monitor, PREFERENCES_LEFT)
    row2 = get_two_column_box(gtk.Label(_("Center Current Frame on Playback Stop")), auto_center_on_stop, PREFERENCES_LEFT)
    row3 = get_two_column_box(gtk.Label(_("Move Current Frame to Clip start after edit")), auto_move_on_edit, PREFERENCES_LEFT)
    row4 = get_two_column_box(gtk.Label(_("Graphics default length")), gfx_length_spin, PREFERENCES_LEFT)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    #vbox.pack_start(row3, False, False, 0) feature disabled
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (auto_play_in_clip_monitor, auto_center_on_stop, auto_move_on_edit, gfx_length_spin)

def get_file_properties_panel(data):
    media_file, img, size, length, vcodec, acodec, channels, frequency = data
    
    row0 = get_two_column_box(get_bold_label(_("Name:")), gtk.Label(media_file.name))
    row00 = get_two_column_box(get_bold_label(_("Path:")), gtk.Label(media_file.path))
    row1 = get_two_column_box(get_bold_label(_("Image Size:")), gtk.Label(size))
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
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    return vbox    
    
def get_clip_properties_panel(data):
    length, size, path = data
    
    row1 = get_two_column_box(get_bold_label(_("Clip Length:")), gtk.Label(length))
    row2 = get_two_column_box(get_bold_label(_("Image Size:")), gtk.Label(size))
    row3 = get_two_column_box(get_bold_label(_("Media Path:")), gtk.Label(path))

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
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

def get_create_profiles_panel(load_values_clicked, save_profile_clicked, user_profiles_list):
    default_profile_index = mltprofiles.get_default_profile_index()
    default_profile = mltprofiles.get_default_profile()

    load_profile_button = gtk.Button(_("Load values"))

    load_profile_combo = gtk.combo_box_new_text()
    profiles = mltprofiles.get_profiles()
    for profile in profiles:
        load_profile_combo.append_text(profile[0])
    load_profile_combo.set_active(default_profile_index)  

    description = gtk.Entry()
    description.set_text("User Created Profile")

    f_rate_num = gtk.Entry()
    f_rate_num.set_text(str(25))
    f_rate_dem = gtk.Entry()
    f_rate_dem.set_text(str(1))

    width = gtk.Entry()
    width.set_text(str(720))

    height = gtk.Entry()
    height.set_text(str(576))
    
    s_rate_num = gtk.Entry()
    s_rate_num.set_text(str(15))
    s_rate_dem = gtk.Entry()
    s_rate_dem.set_text(str(16))
    
    d_rate_num = gtk.Entry()
    d_rate_num.set_text(str(4))
    d_rate_dem = gtk.Entry()
    d_rate_dem.set_text(str(3))

    progressive = gtk.CheckButton()
    progressive.set_active(False)

    save_button = gtk.Button(_("Save New Profile"))

    widgets = (load_profile_combo, description, f_rate_num, f_rate_dem, width, height, s_rate_num,
                s_rate_dem, d_rate_num, d_rate_dem, progressive)
    fill_new_profile_panel_widgets(default_profile, widgets)

    # callbacks
    load_profile_button.connect("clicked",lambda w,e: load_values_clicked(widgets), None)
    save_button.connect("clicked",lambda w,e: save_profile_clicked(widgets, user_profiles_list), None)

    # build panel
    profile_row = gtk.HBox(False,0)
    profile_row.pack_start(load_profile_combo, False, False, 0)
    profile_row.pack_start(gtk.Label(), True, True, 0)
    profile_row.pack_start(load_profile_button, False, False, 0)

    row0 = get_two_column_box(gtk.Label(_("Description.:")), description, PROFILE_MANAGER_LEFT)
    row1 = get_two_column_box(gtk.Label(_("Frame rate num.:")), f_rate_num, PROFILE_MANAGER_LEFT)
    row2 = get_two_column_box(gtk.Label(_("Frame rate den.:")), f_rate_dem, PROFILE_MANAGER_LEFT)
    row3 = get_two_column_box(gtk.Label(_("Width:")), width, PROFILE_MANAGER_LEFT)
    row4 = get_two_column_box(gtk.Label(_("Height:")), height, PROFILE_MANAGER_LEFT)
    row5 = get_two_column_box(gtk.Label(_("Sample aspect num.:")), s_rate_num, PROFILE_MANAGER_LEFT)
    row6 = get_two_column_box(gtk.Label(_("Sample aspect den.:")), s_rate_dem, PROFILE_MANAGER_LEFT)
    row7 = get_two_column_box(gtk.Label(_("Display aspect num.:")), d_rate_num, PROFILE_MANAGER_LEFT)
    row8 = get_two_column_box(gtk.Label(_("Display aspect den.:")), d_rate_dem, PROFILE_MANAGER_LEFT)
    row9 = get_two_column_box(gtk.Label(_("Progressive:")), progressive, PROFILE_MANAGER_LEFT)

    save_row = gtk.HBox(False,0)
    save_row.pack_start(gtk.Label(), True, True, 0)
    save_row.pack_start(save_button, False, False, 0)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(profile_row, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    vbox.pack_start(save_row, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)

    return vbox

def fill_new_profile_panel_widgets(profile, widgets):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets
    description.set_text(_("User ") + profile.description())
    f_rate_num.set_text(str(25))
    f_rate_dem.set_text(str(1))
    width.set_text(str(profile.width()))
    height.set_text(str(profile.height()))
    s_rate_num.set_text(str(profile.sample_aspect_num()))
    s_rate_dem.set_text(str(profile.sample_aspect_den()))
    d_rate_num.set_text(str(profile.display_aspect_num()))
    d_rate_dem.set_text(str(profile.display_aspect_den()))
    progressive.set_active(profile.progressive())


def get_manage_profiles_panel(delete_user_profiles, hide_selected, unhide_selected):
    # User 
    user_profiles_list = guicomponents.ProfileListView()
    user_profiles_list.fill_data_model(mltprofiles.get_user_profiles())    
    delete_selected_button = gtk.Button(_("Delete Selected"))
    
    user_vbox = gtk.VBox(False, 2)
    user_vbox.pack_start(user_profiles_list, True, True, 0)
    user_vbox.pack_start(guiutils.get_right_justified_box([delete_selected_button]), False, False, 0)

    # Factory
    all_profiles_list = guicomponents.ProfileListView(_("Visible").encode('utf-8'))
    all_profiles_list.fill_data_model(mltprofiles.get_factory_profiles())    
    hide_selected_button = gtk.Button(_("Hide Selected"))
    
    hidden_profiles_list = guicomponents.ProfileListView(_("Hidden").encode('utf-8'))
    hidden_profiles_list.fill_data_model(mltprofiles.get_hidden_profiles())   
    unhide_selected_button = gtk.Button(_("Unhide Selected"))
    
    stop_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "bothways.png")
    
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 28
    hide_selected_button.set_size_request(BUTTON_WIDTH, BUTTON_HEIGHT)
    unhide_selected_button.set_size_request(BUTTON_WIDTH, BUTTON_HEIGHT)
    
    # callbacks
    hide_selected_button.connect("clicked",lambda w,e: hide_selected(all_profiles_list, hidden_profiles_list), None)
    unhide_selected_button.connect("clicked",lambda w,e: unhide_selected(all_profiles_list, hidden_profiles_list), None)    
    delete_selected_button.connect("clicked",lambda w,e: delete_user_profiles(user_profiles_list), None)

    top_hbox = gtk.HBox(True, 2)
    top_hbox.pack_start(all_profiles_list, True, True, 0)
    top_hbox.pack_start(hidden_profiles_list, True, True, 0)
    
    bottom_hbox = gtk.HBox(False, 2)
    bottom_hbox.pack_start(hide_selected_button, False, False, 0)
    bottom_hbox.pack_start(gtk.Label(), True, True, 0)
    bottom_hbox.pack_start(stop_icon, False, False, 0)
    bottom_hbox.pack_start(gtk.Label(), True, True, 0)
    bottom_hbox.pack_start(unhide_selected_button, False, False, 0)

    factory_vbox = gtk.VBox(False, 2)
    factory_vbox.pack_start(top_hbox, True, True, 0)
    factory_vbox.pack_start(bottom_hbox, False, False, 0)

    # Build all
    vbox = gtk.VBox(True, 2)
    vbox.pack_start(get_named_frame(_("User Profiles"), user_vbox), True, True, 0)
    vbox.pack_start(get_named_frame(_("Factory Profiles"), factory_vbox), True, True, 0)
    
    return (vbox, user_profiles_list)

def get_project_info_panel():
    name_panel = get_project_name_panel(editorstate.project.name)
    profile_info = get_profile_info_panel(editorstate.project.profile)
    events_panel = get_project_events_panel()
    
    project_info_vbox = gtk.VBox()
    project_info_vbox.pack_start(name_panel, False, True, 0)
    project_info_vbox.pack_start(profile_info, False, True, 0)
    project_info_vbox.pack_start(events_panel, False, True, 0)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 24, 12, 12)
    align.add(project_info_vbox)
    
    return align

def get_project_events_panel():
    events_list = guicomponents.ProjectEventListView()
    events_list.set_size_request(550, 300)
    events_list.fill_data_model()
    return guiutils.get_named_frame(_("Project Events"), events_list)
    
def get_transition_panel(trans_data):
    type_combo_box = gtk.combo_box_new_text()
    
    rendered_transitions = [("Dissolve","luma")]
    for transition in rendered_transitions:
        name, t_service_name = transition
        type_combo_box.append_text(name)

    type_combo_box.set_active(0)    
    type_row = get_two_column_box(gtk.Label("Type:"), 
                                 type_combo_box)
                                 
    pos_combo_box = gtk.combo_box_new_text()

    # Index values correspond to constants in cliprenderer.py
    pos_combo_box.append_text("Centered on cut")
    pos_combo_box.append_text("Starting at Cut")
    pos_combo_box.append_text("Ending at Cut")
    pos_combo_box.set_active(0)    
    pos_row = get_two_column_box(gtk.Label("Position:"), 
                                 pos_combo_box)
    
    length_entry = gtk.Entry()
    length_entry.set_text(str(30))    
    length_row = get_two_column_box(gtk.Label("Length:"), 
                                    length_entry)
                                    
    filler = gtk.Label()
    filler.set_size_request(10,10)

    out_clip_label = gtk.Label("From Clip Handle:")
    out_clip_value = gtk.Label(trans_data["from_handle"])
    
    in_clip_label = gtk.Label("To Clip Handle:")
    in_clip_value = gtk.Label(trans_data["to_handle"])


    out_handle_row = get_two_column_box(out_clip_label, 
                                        out_clip_value)
    in_handle_row = get_two_column_box(in_clip_label, 
                                       in_clip_value)

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
    #edit_vbox.pack_start(pos_row, False, False, 0)
    edit_vbox.pack_start(length_row, False, False, 0)

    data_vbox = gtk.VBox(False, 2)
    data_vbox.pack_start(out_handle_row, False, False, 0)
    data_vbox.pack_start(in_handle_row, False, False, 0)
    
    enconding_vbox = gtk.VBox(False, 2)
    enconding_vbox.pack_start(encodings_cb, False, False, 0)
    enconding_vbox.pack_start(quality_cb, False, False, 0)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(get_named_frame("Transition Options",  edit_vbox))
    vbox.pack_start(get_named_frame("Clips info",  data_vbox))
    vbox.pack_start(get_named_frame("Encoding",  enconding_vbox))

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 24, 12, 12)
    alignment.add(vbox)
    return (alignment, type_combo_box, length_entry, encodings_cb, quality_cb)

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




    
# -------------------------------------------------- guiutils
def get_bold_label(text):
    return guiutils.bold_label(text)

def get_left_justified_box(widgets):
    return guiutils.get_left_justified_box(widgets)

def get_two_column_box(widget1, widget2, left_width=HALF_ROW_WIDTH):
    return guiutils.get_two_column_box(widget1, widget2, left_width)
