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
Module builds dialog windows. User input is handled at 
callsites which provide callback methods for response signals.
"""
import pygtk
pygtk.require('2.0');
import gtk

import locale
import os
import pango

import appconsts
import dialogutils
import gui
import guicomponents
import guiutils
import editorstate
import editorpersistance
import mltenv
import mltprofiles
import mltfilters
import mlttransitions
import panels
import renderconsumer
import respaths
import utils


def new_project_dialog(callback):
    default_profile_index = mltprofiles.get_default_profile_index()
    default_profile = mltprofiles.get_default_profile()

    dialog = gtk.Dialog(_("New Project"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                         _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    out_profile_combo = gtk.combo_box_new_text()
    profiles = mltprofiles.get_profiles()
    for profile in profiles:
        out_profile_combo.append_text(profile[0])

    out_profile_combo.set_active(default_profile_index)    
    profile_select = panels.get_two_column_box(gtk.Label(_("Project profile:")),
                                               out_profile_combo,
                                               250)

    profile_info_panel = guicomponents.get_profile_info_box(default_profile, False)
    profile_info_box = gtk.VBox() 
    profile_info_box.add(profile_info_panel)
    profiles_vbox = gtk.VBox(False, 2)
    profiles_vbox.pack_start(profile_select, False, False, 0)
    profiles_vbox.pack_start(profile_info_box, False, False, 0)
    profiles_frame = panels.get_named_frame(_("Profile"), profiles_vbox)

    tracks_combo, tracks_combo_values_list = guicomponents.get_track_counts_combo_and_values_list()
    tracks_select = panels.get_two_column_box(gtk.Label(_("Number of tracks:")),
                                               tracks_combo, 250)
    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(tracks_select, False, False, 0)

    tracks_frame = panels.get_named_frame(_("Tracks"), tracks_vbox)
    
    """
    project_type_combo = gtk.combo_box_new_text()
    project_type_combo.append_text(_("Standard"))
    project_type_combo.append_text(_("Compact"))
    project_type_combo.set_active(0)

    
    type_select = panels.get_two_column_box(gtk.Label(_("Type:")),
                                               project_type_combo,
                                               250)

    project_folder = gtk.FileChooserButton(_("Select Compact Project Folder"))
    project_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    project_folder.set_current_folder(os.path.expanduser("~") + "/")
    project_folder.set_sensitive(False)
    
    project_folder_label = gtk.Label(_("Compact Project Folder:"))
    project_folder_label.set_sensitive(False)
    
    project_folder_row = guiutils.get_two_column_box(project_folder_label, project_folder, 250)

    compact_name_entry = gtk.Entry(30)
    compact_name_entry.set_width_chars(30)
    compact_name_entry.set_text(_("initial_save"))
    compact_name_entry.set_sensitive(False)
    
    compact_name_label = gtk.Label(_("Compact Project Initial Name:"))
    compact_name_label.set_sensitive(False)
    
    compact_name_entry_row = guiutils.get_two_column_box(compact_name_label, compact_name_entry, 250)
    
    project_type_combo.connect('changed', lambda w: _new_project_type_changed(w, 
                                                    project_folder,
                                                    project_folder_label,
                                                    compact_name_entry,
                                                    compact_name_label))

    type_vbox = gtk.VBox(False, 2)
    type_vbox.pack_start(type_select, False, False, 0)
    type_vbox.pack_start(project_folder_row, False, False, 0)
    type_vbox.pack_start(compact_name_entry_row, False, False, 0)

    type_frame = panels.get_named_frame(_("Project Type"), type_vbox)
    """
    vbox = gtk.VBox(False, 2)
    vbox.add(profiles_frame)
    vbox.add(tracks_frame)
    #vbox.add(type_frame)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, out_profile_combo, tracks_combo, 
                   tracks_combo_values_list)#, project_type_combo, 
                   #project_folder, compact_name_entry)
    out_profile_combo.connect('changed', lambda w: _new_project_profile_changed(w, profile_info_box))
    dialog.show_all()
    
def _new_project_profile_changed(combo_box, profile_info_box):
    profile = mltprofiles.get_profile_for_index(combo_box.get_active())
    
    info_box_children = profile_info_box.get_children()
    for child in info_box_children:
        profile_info_box.remove(child)
    
    info_panel = guicomponents.get_profile_info_box(profile, True)
    profile_info_box.add(info_panel)
    profile_info_box.show_all()
    info_panel.show()

def save_backup_snapshot(name, callback):
    dialog = gtk.Dialog(_("Save Project Backup Snapshot"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                         _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    project_folder = gtk.FileChooserButton(_("Select Snapshot Project Folder"))
    project_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    project_folder.set_current_folder(os.path.expanduser("~") + "/")
    
    project_folder_label = gtk.Label(_("Snapshot Folder:"))
    
    project_folder_row = guiutils.get_two_column_box(project_folder_label, project_folder, 250)

    compact_name_entry = gtk.Entry(30)
    compact_name_entry.set_width_chars(30)
    compact_name_entry.set_text(name)
    
    compact_name_label = gtk.Label(_("Project File Name:"))
    
    compact_name_entry_row = guiutils.get_two_column_box(compact_name_label, compact_name_entry, 250)
    
    type_vbox = gtk.VBox(False, 2)
    type_vbox.pack_start(project_folder_row, False, False, 0)
    type_vbox.pack_start(compact_name_entry_row, False, False, 0)

    #type_frame = panels.get_named_frame(_("Project Type"), type_vbox)
    
    vbox = gtk.VBox(False, 2)
    vbox.add(type_vbox)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, project_folder, compact_name_entry)
    dialog.show_all()

def load_project_dialog(callback):    
    dialog = gtk.FileChooserDialog(_("Select Project File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.set_name(_("Flowblade Projects"))
    file_filter.add_pattern("*" + appconsts.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_project_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Project As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    dialog.set_current_name(current_name)
    dialog.set_do_overwrite_confirmation(True)
    if open_dir != None:
        dialog.set_current_folder(open_dir)

    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.add_pattern("*" + appconsts.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def export_xml_dialog(callback, project_name):    
    _export_file_name_dialog(callback, project_name, _("Export Project as XML to"))

def _export_file_name_dialog(callback, project_name, dialog_title):  
    dialog = gtk.FileChooserDialog(dialog_title, None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                   _("Export").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    project_name = project_name.strip(".flb")
    dialog.set_current_name(project_name + ".xml")
    dialog.set_do_overwrite_confirmation(True)
    
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()
    
def save_env_data_dialog(callback):    
    dialog = gtk.FileChooserDialog(_("Save Runtime Environment Data"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                   _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    dialog.set_current_name("flowblade_runtime_environment_data")
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def select_thumbnail_dir(callback, parent_window, current_dir_path, retry_open_media):
    panel, file_select = panels.get_thumbnail_select_panel(current_dir_path)
    cancel_str = _("Cancel").encode('utf-8')
    ok_str = _("Ok").encode('utf-8')
    dialog = gtk.Dialog(_("Select Thumbnail Folder"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (cancel_str, gtk.RESPONSE_CANCEL,
                        ok_str, gtk.RESPONSE_YES))

    dialog.vbox.pack_start(panel, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (file_select, retry_open_media))
    dialog.show_all()

def select_rendred_clips_dir(callback, parent_window, current_dir_path, context_data=None):
    panel, file_select = panels.get_render_folder_select_panel(current_dir_path)
    cancel_str = _("Cancel").encode('utf-8')
    ok_str = _("Ok").encode('utf-8')
    dialog = gtk.Dialog(_("Select Thumbnail Folder"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (cancel_str, gtk.RESPONSE_CANCEL,
                        ok_str, gtk.RESPONSE_YES))

    dialog.vbox.pack_start(panel, True, True, 0)
    _default_behaviour(dialog)
    if context_data == None:
        dialog.connect('response', callback, file_select)
    else:
        dialog.connect('response', callback, file_select, context_data)
    dialog.show_all()

def rendered_clips_no_home_folder_dialog():
    dialogutils.warning_message(_("Can't make home folder render clips folder"), 
                            _("Please create and select some other folder then \'") + 
                            os.path.expanduser("~") + _("\' as render clips folder"), 
                            gui.editor_window.window)

def exit_confirm_dialog(callback, msg, parent_window, project_name):
    title = _("Save project '") + project_name + _("' before exiting?")
    content = dialogutils.get_warning_message_dialog_panel(title, msg, False, gtk.STOCK_QUIT)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)

    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Don't Save").encode('utf-8'), gtk.RESPONSE_CLOSE,
                        _("Cancel").encode('utf-8'), gtk.RESPONSE_CANCEL,
                        _("Save").encode('utf-8'), gtk.RESPONSE_YES))

    dialog.vbox.pack_start(align, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback)
    dialog.show_all()

def close_confirm_dialog(callback, msg, parent_window, project_name):
    title = _("Save project '") + project_name + _("' before closing project?")
    content = dialogutils.get_warning_message_dialog_panel(title, msg, False, gtk.STOCK_QUIT)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)

    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Don't Save").encode('utf-8'), gtk.RESPONSE_CLOSE,
                        _("Cancel").encode('utf-8'), gtk.RESPONSE_CANCEL,
                        _("Save").encode('utf-8'), gtk.RESPONSE_YES))

    dialog.vbox.pack_start(align, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback)
    dialog.show_all()

def about_dialog(parent_window):
    dialog = gtk.Dialog(_("About"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    img = gtk.image_new_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
    flow_label = gtk.Label("Flowblade Movie Editor")
    ver_label = gtk.Label("0.18.0")
    janne_label = gtk.Label("Copyright 2015 Janne Liljeblad")

    flow_label.modify_font(pango.FontDescription("sans bold 14"))

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox.pack_start(img, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(30, 4), False, False, 0)
    vbox.pack_start(flow_label, False, False, 0)
    vbox.pack_start(ver_label, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox.pack_start(janne_label, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
   
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(vbox)
    alignment.set_size_request(450, 370)

    up_label = gtk.Label("Upstream:")
    up_projs = gtk.Label("MLT")
    up_projs2 = gtk.Label("FFMpeg, Frei0r, LADSPA, Cairo, Gnome, Linux")
    tools_label = gtk.Label("Tools:")
    tools_list = gtk.Label("Geany, Inkscape, Gimp, ack-grep")
    
    up_label.modify_font(pango.FontDescription("sans bold 12"))
    tools_label.modify_font(pango.FontDescription("sans bold 12"))
    
    vbox2 = gtk.VBox(False, 4)
    vbox2.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox2.pack_start(up_label, False, False, 0)
    vbox2.pack_start(up_projs, False, False, 0)
    vbox2.pack_start(up_projs2, False, False, 0)
    vbox2.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox2.pack_start(tools_label, False, False, 0)
    vbox2.pack_start(tools_list, False, False, 0)
    vbox2.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox2.pack_start(gtk.Label(), True, True, 0)

    alignment2 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment2.set_padding(6, 24, 12, 12)
    alignment2.add(vbox2)
    alignment2.set_size_request(450, 370)

    license_view = guicomponents.get_gpl3_scroll_widget((450, 370))
    alignment3 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment3.set_padding(6, 24, 12, 12)
    alignment3.add(license_view)
    alignment3.set_size_request(450, 370)

    translations_view = guicomponents.get_translations_scroll_widget((450, 370))
    alignment4 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment4.set_padding(6, 24, 12, 12)
    alignment4.add(translations_view)
    alignment4.set_size_request(450, 370)
    
    notebook = gtk.Notebook()
    notebook.set_size_request(450 + 10, 370 + 10)
    notebook.append_page(alignment, gtk.Label(_("Application")))
    notebook.append_page(alignment2, gtk.Label(_("Thanks")))
    notebook.append_page(alignment3, gtk.Label(_("License")))
    notebook.append_page(alignment4, gtk.Label(_("Translations")))
    
    dialog.vbox.pack_start(notebook, True, True, 0)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def environment_dialog(parent_window, write_data_cb):
    dialog = gtk.Dialog(_("Runtime Environment"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    COLUMN_WIDTH = 450

    r1 = guiutils.get_left_justified_box([gtk.Label(_("MLT version: ")), gtk.Label(str(editorstate.mlt_version))])
    try:
        major, minor, rev = editorstate.gtk_version
        gtk_ver = str(major) + "." + str(minor) + "." + str(rev)
    except:
        gtk_ver = str(editorstate.gtk_version)
    r2 = guiutils.get_left_justified_box([gtk.Label(_("GTK version: ")), gtk.Label(gtk_ver)])
    lc, encoding = locale.getdefaultlocale()
    r3 = guiutils.get_left_justified_box([gtk.Label(_("Locale: ")), gtk.Label(str(lc))])

    if editorstate.app_running_from == editorstate.RUNNING_FROM_INSTALLATION:
        run_type = _("INSTALLATION")
    else:
        run_type = _("DEVELOPER VERSION")
        
    r4 = guiutils.get_left_justified_box([gtk.Label(_("Running from: ")), gtk.Label(run_type)])
    write_button = gtk.Button(_("Write Environment Data to File"))
    write_button.connect("clicked", lambda w,e: write_data_cb(), None)
    r5 = guiutils.get_left_justified_box([write_button])
    
    vbox = gtk.VBox(False, 4)
    vbox.pack_start(r1, False, False, 0)
    vbox.pack_start(r2, False, False, 0)
    vbox.pack_start(r3, False, False, 0)
    vbox.pack_start(r4, False, False, 0)
    vbox.pack_start(r5, False, False, 0)

    filters = sorted(mltenv.services)
    filters_sw = _get_items_in_scroll_window(filters, 7, COLUMN_WIDTH, 140)

    transitions = sorted(mltenv.transitions)
    transitions_sw = _get_items_in_scroll_window(transitions, 7, COLUMN_WIDTH, 140)

    v_codecs = sorted(mltenv.vcodecs)
    v_codecs_sw = _get_items_in_scroll_window(v_codecs, 6, COLUMN_WIDTH, 125)

    a_codecs = sorted(mltenv.acodecs)
    a_codecs_sw = _get_items_in_scroll_window(a_codecs, 6, COLUMN_WIDTH, 125)

    formats = sorted(mltenv.formats)
    formats_sw = _get_items_in_scroll_window(formats, 5, COLUMN_WIDTH, 105)
    
    enc_ops = renderconsumer.encoding_options + renderconsumer.not_supported_encoding_options
    enc_msgs = []
    for e_opt in enc_ops:
        if e_opt.supported:
            msg = e_opt.name + _(" AVAILABLE")
        else:
            msg = e_opt.name + _(" NOT AVAILABLE, ") + e_opt.err_msg + _(" MISSING")
        enc_msgs.append(msg)
    enc_opt_sw = _get_items_in_scroll_window(enc_msgs, 5, COLUMN_WIDTH, 115)

    missing_mlt_services = []
    for f in mltfilters.not_found_filters:
        msg = "mlt.Filter " + f.mlt_service_id + _(" FOR FILTER ") + f.name + _(" NOT FOUND")
        missing_mlt_services.append(msg)
    for t in mlttransitions.not_found_transitions:
        msg = "mlt.Transition " + t.mlt_service_id + _(" FOR TRANSITION ") + t.name + _(" NOT FOUND")
    missing_services_sw = _get_items_in_scroll_window(missing_mlt_services, 5, COLUMN_WIDTH, 60)
    
    l_pane = gtk.VBox(False, 4)
    l_pane.pack_start(guiutils.get_named_frame(_("General"), vbox), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Filters"), filters_sw), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Transitions"), transitions_sw), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("Missing MLT Services"), missing_services_sw), True, True, 0)

    r_pane = gtk.VBox(False, 4)
    r_pane.pack_start(guiutils.get_named_frame(_("Video Codecs"), v_codecs_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Audio Codecs"), a_codecs_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Formats"), formats_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Render Options"), enc_opt_sw), False, False, 0)

    pane = gtk.HBox(False, 4)
    pane.pack_start(l_pane, False, False, 0)
    pane.pack_start(guiutils.pad_label(5, 5), False, False, 0)
    pane.pack_start(r_pane, False, False, 0)
    
    a = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    a.set_padding(6, 24, 12, 12)
    a.add(pane)
    
    dialog.vbox.pack_start(a, True, True, 0)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()
    dialog.set_resizable(False)

def _get_items_in_scroll_window(items, rows_count, w, h):
    row_widgets = []
    for i in items:
        row = guiutils.get_left_justified_box([gtk.Label(i)])
        row_widgets.append(row)
    items_pane = _get_item_columns_panel(row_widgets, rows_count)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add_with_viewport(items_pane)
    sw.set_size_request(w, h)
    return sw
    
def _get_item_columns_panel(items, rows):
    hbox = gtk.HBox(False, 4)
    n_item = 0
    col_items = 0
    vbox = gtk.VBox()
    hbox.pack_start(vbox, False, False, 0)
    while n_item < len(items):
        item = items[n_item]
        vbox.pack_start(item, False, False, 0)
        n_item += 1
        col_items += 1
        if col_items > rows:
            vbox = gtk.VBox()
            hbox.pack_start(vbox, False, False, 0)
            col_items = 0
    return hbox

def file_properties_dialog(data):
    dialog = gtk.Dialog(_("File Properties"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    panel = panels.get_file_properties_panel(data)
    alignment = dialogutils.get_default_alignment(panel)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def clip_properties_dialog(data):
    dialog = gtk.Dialog(_("Clip Properties"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    panel = panels.get_clip_properties_panel(data)
    alignment = dialogutils.get_default_alignment(panel)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def add_compositor_dialog(current_sequence, callback, data):
    dialog = gtk.Dialog(_("Composite Target Track"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("Add Compositor").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    
    panel, track_combo = panels.get_add_compositor_panel(current_sequence, data)
    alignment = dialogutils.get_default_alignment(panel)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, data, track_combo)
    dialog.show_all()
    
def _dialog_destroy(dialog, response):
    dialog.destroy()

def _default_behaviour(dialog):
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_has_separator(False)
    dialog.set_resizable(False)

def load_dialog():
    dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
    dialog.set_title(_("Loading project"))

    info_label = gtk.Label("")
    status_box = gtk.HBox(False, 2)
    status_box.pack_start(info_label, False, False, 0)
    status_box.pack_start(gtk.Label(), True, True, 0)

    progress_bar = gtk.ProgressBar()
    progress_bar.set_fraction(0.2)
    progress_bar.set_pulse_step(0.1)

    est_box = gtk.HBox(False, 2)
    est_box.pack_start(gtk.Label(""),False, False, 0)
    est_box.pack_start(gtk.Label(), True, True, 0)

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.show_all()

    # Make refs available for updates
    dialog.progress_bar = progress_bar
    dialog.info = info_label

    return dialog

def recreate_icons_progress_dialog():
    dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
    dialog.set_title(_("Recreating icons"))

    info_label = gtk.Label("")
    status_box = gtk.HBox(False, 2)
    status_box.pack_start(info_label, False, False, 0)
    status_box.pack_start(gtk.Label(), True, True, 0)

    progress_bar = gtk.ProgressBar()
    progress_bar.set_fraction(0.0)

    est_box = gtk.HBox(False, 2)
    est_box.pack_start(gtk.Label(""),False, False, 0)
    est_box.pack_start(gtk.Label(), True, True, 0)

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.show_all()

    # Make refs available for updates
    dialog.progress_bar = progress_bar
    dialog.info = info_label

    return dialog

def proxy_delete_warning_dialog(parent_window, callback):
    title = _("Are you sure you want to delete these media files?")
    msg1 = _("One or more of the Media Files you are deleting from the project\neither <b>have proxy files or are proxy files.</b>\n\n")
    msg2 = _("Deleting these files could <b>prevent converting</b> between\nusing proxy files and using original media.\n\n")

    msg = msg1 + msg2 
    content = dialogutils.get_warning_message_dialog_panel(title, msg)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)

    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_CANCEL,
                        _("Force Delete").encode('utf-8'), gtk.RESPONSE_OK))

    dialog.vbox.pack_start(align, True, True, 0)
    _default_behaviour(dialog)
    dialog.set_default_response(gtk.RESPONSE_CANCEL)
    dialog.connect('response', callback)

    dialog.show_all()

def autosave_recovery_dialog(callback, parent_window):
    title = _("Open last autosave?")
    msg1 = _("It seems that Flowblade exited abnormally last time.\n\n")
    msg2 = _("If there is another instance of Flowblade running,\nthis dialog has probably detected its autosave file.\n\n")
    msg3 = _("It is NOT possible to open this autosaved version later.")
    msg = msg1 + msg2 + msg3
    content = dialogutils.get_warning_message_dialog_panel(title, msg)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)

    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Continue with default 'untitled' project").encode('utf-8'), gtk.RESPONSE_CANCEL,
                        _("Open Autosaved Project").encode('utf-8'), gtk.RESPONSE_OK))

    dialog.vbox.pack_start(align, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback)
    dialog.show_all()

def autosaves_many_recovery_dialog(response_callback, autosaves, parent_window):
    title = _("Open a autosave file?")
    msg1 = _("There are <b>multiple autosave files</b> from application crashes.\n\n")
    msg3 = _("If you just <b>experienced a crash, select the last created autosave</b> file\nto continue working.\n\n")
    msg4 = _("If you see this at application start without a recent crash,\nyou should probably delete all autosave files to stop seeing this dialog.")
    msg = msg1 + msg3 + msg4
    info_panel = dialogutils.get_warning_message_dialog_panel(title, msg)
    
    autosaves_view = guicomponents.AutoSavesListView()
    autosaves_view.set_size_request(300, 300)
    autosaves_view.fill_data_model(autosaves)

    delete_all = gtk.Button("Delete all autosaves")
    delete_all.connect("clicked", lambda w : _autosaves_delete_all_clicked(autosaves, autosaves_view, dialog))
    delete_all_but_selected = gtk.Button("Delete all but selected autosave")
    delete_all_but_selected.connect("clicked", lambda w : _autosaves_delete_unselected(autosaves, autosaves_view))

    delete_buttons_vbox = gtk.HBox()
    delete_buttons_vbox.pack_start(gtk.Label(), True, True, 0)
    delete_buttons_vbox.pack_start(delete_all, False, False, 0)
    delete_buttons_vbox.pack_start(delete_all_but_selected, False, False, 0)
    delete_buttons_vbox.pack_start(gtk.Label(), True, True, 0)

    pane = gtk.VBox()
    pane.pack_start(info_panel, False, False, 0)
    pane.pack_start(delete_buttons_vbox, False, False, 0)
    pane.pack_start(guiutils.get_pad_label(12,12), False, False, 0)
    pane.pack_start(autosaves_view, False, False, 0)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(pane)

    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Continue with default 'untitled' project").encode('utf-8'), gtk.RESPONSE_CANCEL,
                        _("Open Selected Autosave").encode('utf-8'), gtk.RESPONSE_OK))

    dialog.vbox.pack_start(align, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', response_callback, autosaves_view, autosaves)
    dialog.show_all()

def _autosaves_delete_all_clicked(autosaves, autosaves_view, dialog):
    for autosave in autosaves:
        os.remove(autosave.path)
    dialog.set_response_sensitive(gtk.RESPONSE_OK, False)
    del autosaves[:]
    autosaves_view.fill_data_model(autosaves)

def _autosaves_delete_unselected(autosaves, autosaves_view):
    selected_autosave = autosaves.pop(autosaves_view.get_selected_indexes_list()[0])
    for autosave in autosaves:
        os.remove(autosave.path)
    del autosaves[:]
    autosaves.append(selected_autosave)
    autosaves_view.fill_data_model(autosaves)

def tracks_count_change_dialog(callback):
    dialog = gtk.Dialog(_("Change Sequence Tracks Count"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Change Tracks").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    tracks_combo, tracks_combo_values_list = guicomponents.get_track_counts_combo_and_values_list()
    tracks_select = panels.get_two_column_box(gtk.Label(_("New Number of Tracks:")),
                                               tracks_combo,
                                               250)
    info_text = _("Please note:\n") + \
                u"\u2022" + _(" It is recommended that you save Project before completing this operation\n") + \
                u"\u2022" + _(" There is no Undo for this operation\n") + \
                u"\u2022" + _(" Current Undo Stack will be destroyed\n") + \
                u"\u2022" + _(" All Clips and Compositors on deleted Tracks will be permanently destroyed")
    info_label = gtk.Label(info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])

    pad = guiutils.get_pad_label(24, 24)
    
    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(info_box, False, False, 0)
    tracks_vbox.pack_start(pad, False, False, 0)
    tracks_vbox.pack_start(tracks_select, False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, tracks_combo)
    dialog.show_all()

def new_sequence_dialog(callback, default_name):
    dialog = gtk.Dialog(_("Create New Sequence"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Create Sequence").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    name_entry = gtk.Entry(30)
    name_entry.set_width_chars(30)
    name_entry.set_text(default_name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(gtk.Label(_("Sequence Name:")),
                                               name_entry,
                                               250)

    tracks_combo, tracks_combo_values_list = guicomponents.get_track_counts_combo_and_values_list()
    tracks_select = panels.get_two_column_box(gtk.Label(_("Number of Tracks:")),
                                               tracks_combo,
                                               250)

    open_check = gtk.CheckButton()
    open_check.set_active(True)
    open_label = gtk.Label(_("Open For Editing:"))

    open_hbox = gtk.HBox(False, 2)
    open_hbox.pack_start(gtk.Label(), True, True, 0)
    open_hbox.pack_start(open_label, False, False, 0)
    open_hbox.pack_start(open_check, False, False, 0)
    
    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(tracks_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)
    tracks_vbox.pack_start(open_hbox, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (name_entry, tracks_combo, open_check))
    dialog.show_all()

def new_media_name_dialog(callback, media_file):
    dialog = gtk.Dialog(_("Rename New Media Object"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Rename").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    name_entry = gtk.Entry(30)
    name_entry.set_width_chars(30)
    name_entry.set_text(media_file.name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(gtk.Label(_("New Name:")),
                                               name_entry,
                                               180)

    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.set_default_response(gtk.RESPONSE_ACCEPT)
    dialog.connect('response', callback, (name_entry, media_file))
    dialog.show_all()

def new_clip_name_dialog(callback, clip):
    dialog = gtk.Dialog(_("Rename Clip"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Rename").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    name_entry = gtk.Entry(30)
    name_entry.set_width_chars(30)
    name_entry.set_text(clip.name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(gtk.Label(_("New Name:")),
                                               name_entry,
                                               180)

    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.set_default_response(gtk.RESPONSE_ACCEPT)
    dialog.connect('response', callback, (name_entry, clip))
    dialog.show_all()

def new_media_log_group_name_dialog(callback, next_index, add_selected):
    dialog = gtk.Dialog(_("New Range Item Group"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Create").encode('utf-8'), gtk.RESPONSE_OK))

    name_entry = gtk.Entry(30)
    name_entry.set_width_chars(30)
    name_entry.set_text(_("User Group ") + str(next_index))
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(gtk.Label(_("New Group Name:")),
                                               name_entry,
                                               180)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(name_select, False, False, 0)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.set_default_response(gtk.RESPONSE_ACCEPT)
    dialog.connect('response', callback, (name_entry, add_selected))
    dialog.show_all()

def group_rename_dialog(callback, group_name):
    dialog, entry = dialogutils.get_single_line_text_input_dialog(30, 130,
                                                _("Rename Range Log Item Group"), 
                                                _("Rename").encode('utf-8'),
                                                _("New Group Name:"),
                                                group_name)
    dialog.connect('response', callback, entry)
    dialog.show_all()

def not_valid_producer_dialog(file_path, parent_window):
    primary_txt = _("Can't open non-valid media")
    secondary_txt = _("File: ") + file_path + _("\nis not a valid media file.")
    dialogutils.warning_message(primary_txt, secondary_txt, parent_window, is_info=True)

def marker_name_dialog(frame_str, callback):
    dialog = gtk.Dialog(_("New Marker"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Add Marker").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    name_entry = gtk.Entry(30)
    name_entry.set_width_chars(30)
    name_entry.set_text("")
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(gtk.Label(_("Name for marker at ") + frame_str),
                                               name_entry,
                                               250)
    alignment = dialogutils.get_default_alignment(name_select)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialog.set_default_response(gtk.RESPONSE_ACCEPT)
    _default_behaviour(dialog)
    dialog.connect('response', callback, name_entry)
    dialog.show_all()

def open_image_sequence_dialog(callback, parent_window):
    cancel_str = _("Cancel").encode('utf-8')
    ok_str = _("Ok").encode('utf-8')
    dialog = gtk.Dialog(_("Add Image Sequence Clip"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (cancel_str, gtk.RESPONSE_CANCEL,
                        ok_str, gtk.RESPONSE_YES))

    file_chooser = gtk.FileChooserButton(_("Select First Frame"))
    file_chooser.set_size_request(250, 25)
    filt = utils.get_image_sequence_file_filter()
    file_chooser.add_filter(filt)
    row1 = guiutils.get_two_column_box(gtk.Label(_("First frame:")), file_chooser, 220)

    adj = gtk.Adjustment(value=1, lower=1, upper=250, step_incr=1)
    frames_per_image = gtk.SpinButton(adjustment=adj, climb_rate=1.0, digits=0)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Frames per Source Image:")), frames_per_image, 220)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (file_chooser, frames_per_image))
    dialog.show_all()
    
def export_edl_dialog(callback, parent_window, project_name):
    cancel_str = _("Cancel").encode('utf-8')
    ok_str = _("Export To EDL").encode('utf-8')
    dialog = gtk.Dialog(_("Export EDL"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (cancel_str, gtk.RESPONSE_CANCEL,
                        ok_str, gtk.RESPONSE_YES))
    
    INPUT_LABELS_WITDH = 220
    project_name = project_name.strip(".flb")
    
    file_name = gtk.Entry()
    file_name.set_text(project_name)

    extension_label = gtk.Label(".edl")
    extension_label.set_size_request(35, 20)

    name_pack = gtk.HBox(False, 4)
    name_pack.pack_start(file_name, True, True, 0)
    name_pack.pack_start(extension_label, False, False, 0)

    name_row = guiutils.get_two_column_box(gtk.Label(_("Export file name:")), name_pack, INPUT_LABELS_WITDH)
 
    out_folder = gtk.FileChooserButton(_("Select target folder"))
    out_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    out_folder.set_current_folder(os.path.expanduser("~") + "/")
    
    folder_row = guiutils.get_two_column_box(gtk.Label(_("Export folder:")), out_folder, INPUT_LABELS_WITDH)

    file_frame = guiutils.get_named_frame_with_vbox(_("File"), [name_row, folder_row])

    seq = editorstate.current_sequence()
    track_select_combo = gtk.combo_box_new_text()
    for i in range(seq.first_video_index,  len(seq.tracks) - 1):
        track_select_combo.append_text(utils.get_track_name(seq.tracks[i], seq))
    track_select_combo.set_active(0)
    track_row = guiutils.get_two_column_box(gtk.Label(_("Exported video track:")), track_select_combo, INPUT_LABELS_WITDH)
    
    cascade_check = gtk.CheckButton()
    cascade_check.connect("toggled", _cascade_toggled, track_select_combo)
    
    cascade_row = guiutils.get_left_justified_box( [cascade_check, gtk.Label(_("Cascade video tracks"))])

    audio_track_select_combo = gtk.combo_box_new_text()
    for i in range(1,  seq.first_video_index):
        audio_track_select_combo.append_text(utils.get_track_name(seq.tracks[i], seq))
    audio_track_select_combo.set_active(seq.first_video_index - 2)
    audio_track_select_combo.set_sensitive(False)

    audio_track_row = guiutils.get_two_column_box(gtk.Label(_("Exported audio track:")), audio_track_select_combo, INPUT_LABELS_WITDH)

    op_combo = gtk.combo_box_new_text()
    op_combo.append_text(_("Audio From Video"))
    op_combo.append_text(_("Separate Audio Track"))
    op_combo.append_text(_("No Audio"))
    op_combo.set_active(0)
    op_combo.connect("changed", _audio_op_changed, audio_track_select_combo)
    op_row = guiutils.get_two_column_box(gtk.Label(_("Audio export:")), op_combo, INPUT_LABELS_WITDH)
    
    tracks_frame = guiutils.get_named_frame_with_vbox(_("Tracks"), [cascade_row, track_row, op_row, audio_track_row])

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(file_frame, False, False, 0)
    vbox.pack_start(tracks_frame, False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (file_name, out_folder, track_select_combo, cascade_check, op_combo, audio_track_select_combo))
    dialog.show_all()

def _cascade_toggled(check, track_select_combo):
    if check.get_active() == True:
        track_select_combo.set_sensitive(False)
    else:
        track_select_combo.set_sensitive(True)

def _audio_op_changed(combo, audio_track_select_combo):
    if combo.get_active() == 1:
        audio_track_select_combo.set_sensitive(True)
    else:
        audio_track_select_combo.set_sensitive(False)

def transition_edit_dialog(callback, transition_data):
    dialog = gtk.Dialog(_("Add Transition").encode('utf-8'), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Apply").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    alignment, type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, color_button = panels.get_transition_panel(transition_data)
    widgets = (type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, color_button)
    dialog.connect('response', callback, widgets, transition_data)
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()

def fade_edit_dialog(callback, transition_data):
    dialog = gtk.Dialog(_("Add Fade"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Apply").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    alignment, type_combo, length_entry, encodings_cb, quality_cb, color_button = panels.get_fade_panel(transition_data)
    widgets = (type_combo, length_entry, encodings_cb, quality_cb, color_button)
    dialog.connect('response', callback, widgets, transition_data)
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()

def keyboard_shortcuts_dialog(parent_window):    
    dialog = gtk.Dialog(_("Keyboard Shortcuts"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Close").encode('utf-8'), gtk.RESPONSE_CLOSE))
    
    general_vbox = gtk.VBox()
    general_vbox.pack_start(_get_kb_row(_("Control + N"), _("Create New Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + S"), _("Save Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Delete"), _("Delete Selected Item")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Escape"), _("Stop Rendering Audio Levels")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Q"), _("Quit")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Z"), _("Undo")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Y"), _("Redo")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + O"), _("Open Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("TAB"), _("Switch Monitor Source")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + L"), _("Log Marked Clip Range")), False, False, 0)
    general = guiutils.get_named_frame(_("General"), general_vbox)

    tline_vbox = gtk.VBox()
    tline_vbox.pack_start(_get_kb_row("I", _("Set Mark In")))
    tline_vbox.pack_start(_get_kb_row("O", _("Set Mark Out")))
    tline_vbox.pack_start(_get_kb_row("Alt + I", _("Go To Mark In")))
    tline_vbox.pack_start(_get_kb_row("Alt + O", _("Go To Mark Out")))
    tline_vbox.pack_start(_get_kb_row("X", _("Cut Clip")))
    tline_vbox.pack_start(_get_kb_row(_("Delete"),  _("Splice Out")))
    tline_vbox.pack_start(_get_kb_row("Y", _("Insert")))
    tline_vbox.pack_start(_get_kb_row("U", _("Append")))
    tline_vbox.pack_start(_get_kb_row("T", _("3 Point Overwrite Insert")))
    tline_vbox.pack_start(_get_kb_row("M", _("Add Mark")))
    tline_vbox.pack_start(_get_kb_row("Control + C", _("Copy Clips")))
    tline_vbox.pack_start(_get_kb_row("Control + V", _("Paste Clips")))
    tline_vbox.pack_start(_get_kb_row(_("G"), _("Log Marked Clip Range")), False, False, 0)
    tline = guiutils.get_named_frame(_("Timeline"), tline_vbox)

    play_vbox = gtk.VBox()
    play_vbox.pack_start(_get_kb_row(_("Space"), _("Start / Stop Playback")))
    play_vbox.pack_start(_get_kb_row("J", _("Backwards Faster")))
    play_vbox.pack_start(_get_kb_row("K", _("Stop")))
    play_vbox.pack_start(_get_kb_row("L", _("Forward Faster")))
    play_vbox.pack_start(_get_kb_row(_("Left Arrow "), _("Prev Frame")))
    play_vbox.pack_start(_get_kb_row(_("Right Arrow"), _("Next Frame")))
    play_vbox.pack_start(_get_kb_row(_("Up Arrow"), _("Next Edit/Mark")))
    play_vbox.pack_start(_get_kb_row(_("Down Arrow"), _("Prev Edit/Mark"))) 
    play_vbox.pack_start(_get_kb_row(_("Home"), _("Go To Start")))
    play_vbox.pack_start(_get_kb_row(_("Shift + I"), _("To Mark In")))
    play_vbox.pack_start(_get_kb_row(_("Shift + O"), _("To Mark Out")))
    play = guiutils.get_named_frame(_("Playback"), play_vbox)

    tools_vbox = gtk.VBox()
    tools_vbox.pack_start(_get_kb_row("1", _("Insert")))
    tools_vbox.pack_start(_get_kb_row("2", _("Overwrite")))
    tools_vbox.pack_start(_get_kb_row("3", _("Trim")))
    tools_vbox.pack_start(_get_kb_row("4", _("Roll")))
    tools_vbox.pack_start(_get_kb_row("5", _("Slip")))
    tools_vbox.pack_start(_get_kb_row("6", _("Spacer")))
    tools = guiutils.get_named_frame(_("Tools"), tools_vbox)

    geom_vbox = gtk.VBox()
    geom_vbox.pack_start(_get_kb_row(_("Left Arrow "), _("Move Source Video Left")))
    geom_vbox.pack_start(_get_kb_row(_("Right Arrow"), _("Move Source Video Right")))
    geom_vbox.pack_start(_get_kb_row(_("Up Arrow"), _("Move Source Video Up")))
    geom_vbox.pack_start(_get_kb_row(_("Down Arrow"), _("Move Source Video Down"))) 
    geom = guiutils.get_named_frame(_("Geometry Editor"), geom_vbox)
    
    panel = gtk.VBox()
    panel.pack_start(tools, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(tline, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(play, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(general, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(geom, False, False, 0)

    pad_panel = gtk.HBox()
    pad_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    pad_panel.pack_start(panel, True, False, 0)
    pad_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    sw.add_with_viewport(pad_panel)
    sw.set_size_request(420, 400)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(24, 24, 24, 24)
    alignment.add(sw)

    dialog.vbox.pack_start(alignment, True, True, 0)

    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def _get_kb_row(msg1, msg2):
    label1 = gtk.Label(msg1)
    label2 = gtk.Label(msg2)
    KB_SHORTCUT_ROW_WIDTH = 400
    KB_SHORTCUT_ROW_HEIGHT = 22
    row = guiutils.get_two_column_box(label1, label2, 170)
    row.set_size_request(KB_SHORTCUT_ROW_WIDTH, KB_SHORTCUT_ROW_HEIGHT)
    return row

def watermark_dialog(add_callback, remove_callback):
    dialog = gtk.Dialog(_("Sequence Watermark"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Close").encode('utf-8'), gtk.RESPONSE_CLOSE))

    seq_label = guiutils.bold_label(_("Sequence:") + " ")
    seq_name = gtk.Label(editorstate.current_sequence().name)

 
    file_path_label = guiutils.bold_label(_("Watermark:") + " ")

    add_button = gtk.Button(_("Set Watermark File"))
    remove_button = gtk.Button(_("Remove Watermark"))
    if editorstate.current_sequence().watermark_file_path == None:
        file_path_value_label = gtk.Label("Not Set")
        add_button.set_sensitive(True)
        remove_button.set_sensitive(False)
    else:
        file_path_value_label = gtk.Label(editorstate.current_sequence().watermark_file_path)
        add_button.set_sensitive(False)
        remove_button.set_sensitive(True)    

    row1 = guiutils.get_left_justified_box([seq_label, seq_name])
    row2 = guiutils.get_left_justified_box([file_path_label, file_path_value_label])
    row3 = guiutils.get_left_justified_box([gtk.Label(), remove_button, guiutils.pad_label(8, 8), add_button])
    row3.set_size_request(470, 30)

    widgets = (add_button, remove_button, file_path_value_label)
    add_button.connect("clicked", add_callback, widgets)
    remove_button.connect("clicked", remove_callback, widgets)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(guiutils.pad_label(12, 8), False, False, 0)
    vbox.pack_start(row3, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def watermark_file_dialog(callback, widgets):
    dialog = gtk.FileChooserDialog(_("Select Watermark File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.set_name("Accepted Watermark Files")
    file_filter.add_pattern("*" + ".png")
    file_filter.add_pattern("*" + ".jpeg")
    file_filter.add_pattern("*" + ".jpg")
    file_filter.add_pattern("*" + ".tga")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback, widgets)
    dialog.show()

def media_file_dialog(text, callback, multiple_select, data=None):
    file_select = gtk.FileChooserDialog(text, None, gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))

    file_select.set_default_response(gtk.RESPONSE_CANCEL)
    file_select.set_select_multiple(multiple_select)

    media_filter = utils.get_media_source_file_filter()
    all_filter = gtk.FileFilter()
    all_filter.set_name(_("All files"))
    all_filter.add_pattern("*.*")
    file_select.add_filter(media_filter)
    file_select.add_filter(all_filter)

    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True) 
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_select.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
    
    if data == None:
        file_select.connect('response', callback)
    else:
        file_select.connect('response', callback, data)

    file_select.set_modal(True)
    file_select.show()

def save_snaphot_progess(media_copy_txt, project_txt):
    dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
    dialog.set_title(_("Saving project snapshot"))
    
    dialog.media_copy_info = gtk.Label(media_copy_txt)
    media_copy_row = guiutils.get_left_justified_box([dialog.media_copy_info])

    dialog.saving_project_info = gtk.Label(project_txt)
    project_row = guiutils.get_left_justified_box([dialog.saving_project_info])

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(media_copy_row, False, False, 0)
    progress_vbox.pack_start(project_row, True, True, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.show_all()

    return dialog
    
