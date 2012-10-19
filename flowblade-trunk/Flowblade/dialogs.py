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

import gtk
import pango

import guicomponents
import guiutils
import editorpersistance
import editorstate
import locale
import mltenv
import mltprofiles
import mltfilters
import mlttransitions
import panels
import projectdata
import render
import respaths

# Gui consts
PREFERENCES_WIDTH = 550
PREFERENCES_HEIGHT = 300

PROFILES_WIDTH = 480
PROFILES_HEIGHT = 520

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
                                               tracks_combo,
                                               250)
    tracks_vbox = gtk.VBox(False, 2)
    tracks_vbox.pack_start(tracks_select, False, False, 0)

    tracks_frame = panels.get_named_frame(_("Tracks"), tracks_vbox)

    vbox = gtk.VBox(False, 2)
    vbox.add(profiles_frame)
    vbox.add(tracks_frame)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(vbox)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, out_profile_combo, tracks_combo, tracks_combo_values_list)
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
    
def load_project_dialog(callback):    
    dialog = gtk.FileChooserDialog(_("Select Project File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.add_pattern("*" + projectdata.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def load_titler_data_dialog(callback):    
    dialog = gtk.FileChooserDialog(_("Select Titler Data File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
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
    file_filter.add_pattern("*" + projectdata.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def export_xml_dialog(callback, project_name):    
    dialog = gtk.FileChooserDialog(_("Export Project as XML to"), None, 
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

def save_titler_graphic_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Titler Graphic As"), None, 
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
    file_filter.add_pattern("*" + ".png")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()
    
def save_titler_data_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Titler Layers As"), None, 
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
    dialog.connect('response', callback)
    dialog.show()


def save_ffmpep_optsdialog(callback, opts_extension):
    dialog = gtk.FileChooserDialog(_("Save Render Args As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                   _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    dialog.set_current_name("untitled" + opts_extension)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.set_name(opts_extension + " files")
    file_filter.add_pattern("*" + opts_extension)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def load_ffmpep_optsdialog(callback, opts_extension):
    dialog = gtk.FileChooserDialog(_("Load Render Args File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.set_name(opts_extension + " files")
    file_filter.add_pattern("*" + opts_extension)
    dialog.add_filter(file_filter)
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

def render_progress_dialog(callback, parent_window):
    dialog = gtk.Dialog(_("Render Progress"),
                         parent_window,
                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                         (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT))

    panel = panels.get_render_progress_panel()
    
    dialog.vbox.pack_start(panel, True, True, 0)
    dialog.set_default_size(500, 125)
    panel.show_all()
    dialog.set_has_separator(False)
    dialog.connect('response', callback)
    dialog.show()
    return dialog
    
def motion_clip_render_progress_dialog(callback, file_name, progress_bar, parent_window):
    dialog = gtk.Dialog(_("Rendering Motion Clip"),
                         parent_window,
                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                         (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT))

    panel = panels.get_motion_render_progress_panel(file_name, progress_bar)
    
    dialog.vbox.pack_start(panel, True, True, 0)
    dialog.set_default_size(500, 125)
    panel.show_all()
    dialog.set_has_separator(False)
    dialog.connect('response', callback)
    dialog.show()
    return dialog

def exit_confirm_dialog(callback, msg, parent_window, project_name):
    title = _("Save project '") + project_name + _("' before exiting?")
    content = panels.get_warning_message_dialog_panel(title, msg, False, gtk.STOCK_QUIT)
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
    content = panels.get_warning_message_dialog_panel(title, msg, False, gtk.STOCK_QUIT)
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
    
def info_message(primary_txt, secondary_txt, parent_window):
    warning_message(primary_txt, secondary_txt, parent_window, is_info=True)

def warning_message(primary_txt, secondary_txt, parent_window, is_info=False):
    warning_message_with_callback(primary_txt, secondary_txt, parent_window, is_info,_dialog_destroy)

def warning_message_with_callback(primary_txt, secondary_txt, parent_window, is_info, callback):
    content = panels.get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info)
    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    dialog.vbox.pack_start(content, True, True, 0)
    dialog.set_has_separator(False)
    dialog.set_resizable(False)
    dialog.connect('response', callback)
    dialog.show_all()
    
def warning_confirmation(callback, primary_txt, secondary_txt, parent_window, data=None):
    content = panels.get_warning_message_dialog_panel(primary_txt, secondary_txt)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)
    
    dialog = gtk.Dialog("",
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                         _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    dialog.vbox.pack_start(align, True, True, 0)
    dialog.set_has_separator(False)
    dialog.set_resizable(False)
    if data == None:
        dialog.connect('response', callback)
    else:
        dialog.connect('response', callback, data)
    dialog.show_all()

def about_dialog(parent_window):
    dialog = gtk.Dialog(_("About"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    filler3 = gtk.Label()
    img = gtk.image_new_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
    flow_label = gtk.Label("Flowblade Movie Editor")
    filler0 = gtk.Label()
    ver_label = gtk.Label("0.6.0")
    filler1 = gtk.Label()
    janne_label = gtk.Label("Copyright 2012 Janne Liljeblad")
    licence_label = gtk.Label("Licensed under GPL 3")
    filler2 = gtk.Label()

    flow_label.modify_font(pango.FontDescription("sans bold 14"))

    filler0.set_size_request(30, 4)
    filler1.set_size_request(30, 22)
    filler3.set_size_request(30, 12)

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(filler3, False, False, 0)
    vbox.pack_start(img, False, False, 0)
    vbox.pack_start(filler0, False, False, 0)
    vbox.pack_start(flow_label, False, False, 0)
    vbox.pack_start(ver_label, False, False, 0)
    vbox.pack_start(filler1, False, False, 0)
    vbox.pack_start(janne_label, False, False, 0)
    #vbox.pack_start(licence_label, False, False, 0)
    vbox.pack_start(filler2, True, True, 0)
   
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(vbox)
    alignment.set_size_request(450, 370)

    up_label = gtk.Label("Upstream:")
    up_projs = gtk.Label("MLT")
    up_projs2 = gtk.Label("FFMpeg, LADSPA, Sox, Cairo, Gnome, Linux")
    tools_label = gtk.Label("Tools:")
    tools_list = gtk.Label("Genie, Inkscape, Gimp, ack-grep")
    vegas_label2 = gtk.Label("Image 'The Blade' in splash Creative Commons BY-NC-ND by"  )  
    vegas_button = gtk.LinkButton("http://www.flickr.com/people/vegas/", "Marcus Vegas")
    vegas_label3 = gtk.Label("Derivative use by permission.")

    vegas_hbox = gtk.HBox(False, 4)
    vegas_hbox.pack_start(gtk.Label(), True, True, 0)
    vegas_hbox.pack_start(vegas_label2, False, False, 0)
    vegas_hbox.pack_start(vegas_button, False, False, 0)
    vegas_hbox.pack_start(gtk.Label(), True, True, 0)

    filler11 = gtk.Label()
    filler12 = gtk.Label()
    filler13 = gtk.Label()
    filler14 = gtk.Label()
    
    filler11.set_size_request(30, 22)
    filler12.set_size_request(30, 22)
    filler13.set_size_request(30, 22)
    filler14.set_size_request(30, 12)
    
    up_label.modify_font(pango.FontDescription("sans bold 12"))
    tools_label.modify_font(pango.FontDescription("sans bold 12"))
    vegas_label2.modify_font(pango.FontDescription("serif light 7"))
    vegas_label3.modify_font(pango.FontDescription("serif light 7"))
    
    vbox2 = gtk.VBox(False, 4)
    vbox2.pack_start(filler14, False, False, 0)
    vbox2.pack_start(up_label, False, False, 0)
    vbox2.pack_start(up_projs, False, False, 0)
    vbox2.pack_start(up_projs2, False, False, 0)
    vbox2.pack_start(filler11, False, False, 0)
    vbox2.pack_start(tools_label, False, False, 0)
    vbox2.pack_start(tools_list, False, False, 0)
    vbox2.pack_start(filler12, False, False, 0)
    vbox2.pack_start(gtk.Label(), True, True, 0)
    vbox2.pack_start(vegas_hbox, False, False, 0)
    vbox2.pack_start(vegas_label3, False, False, 0)

    alignment2 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment2.set_padding(6, 24, 12, 12)
    alignment2.add(vbox2)
    alignment2.set_size_request(450, 370)

    license_view = guicomponents.get_gpl3_scroll_widget((450, 370))

    alignment3 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment3.set_padding(6, 24, 12, 12)
    alignment3.add(license_view)
    alignment3.set_size_request(450, 370)
    
    notebook = gtk.Notebook()
    notebook.set_size_request(450 + 10, 370 + 10)
    notebook.append_page(alignment, gtk.Label(_("Application")))
    notebook.append_page(alignment2, gtk.Label(_("Thanks")))
    notebook.append_page(alignment3, gtk.Label(_("License")))
    
    dialog.vbox.pack_start(notebook, True, True, 0)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def environment_dialog(parent_window):
    dialog = gtk.Dialog(_("Runtime Environment"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    r1 = guiutils.get_left_justified_box([gtk.Label(_("MLT version: ")), gtk.Label(str(editorstate.mlt_version))])
    r2 = guiutils.get_left_justified_box([gtk.Label(_("GTK version: ")), gtk.Label(str(editorstate.gtk_version))])
    lc, encoding = locale.getdefaultlocale()
    r3 = guiutils.get_left_justified_box([gtk.Label(_("Locale: ")), gtk.Label(str(lc))])
    r3 = guiutils.get_left_justified_box([gtk.Label(_("App root: ")), gtk.Label(str(respaths.ROOT_PATH))])

    vbox = gtk.VBox(False, 4)
    vbox.pack_start(r1, False, False, 0)
    vbox.pack_start(r2, False, False, 0)
    vbox.pack_start(r3, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)

    filters = sorted(mltenv.services)
    filters_sw = _get_items_in_scroll_window(filters, 12, 300, 200)

    transitions = sorted(mltenv.transitions)
    transitions_sw = _get_items_in_scroll_window(transitions, 12, 300, 200)

    v_codecs = sorted(mltenv.vcodecs)
    v_codecs_sw = _get_items_in_scroll_window(v_codecs, 12, 300, 200)

    a_codecs = sorted(mltenv.acodecs)
    a_codecs_sw = _get_items_in_scroll_window(a_codecs, 12, 300, 200)

    formats = sorted(mltenv.formats)
    formats_sw = _get_items_in_scroll_window(formats, 12, 300, 200)
    
    enc_ops = render.encoding_options + render.not_supported_encoding_options
    enc_msgs = []
    for e_opt in enc_ops:
        if e_opt.supported:
            msg = e_opt.name + _(" available.")
        else:
            msg = e_opt.name + _(" not available, ") + e_opt.err_msg + _(" missing.")
        enc_msgs.append(msg)
    enc_opt_sw = _get_items_in_scroll_window(enc_msgs, 100, 300, 200) # 100 == we want all of these to be in one column

    missing_mlt_services = []
    for f in mltfilters.not_found_filters:
        msg = "mlt.Filter " + f.mlt_service_id + _(" for filter ") + f.name + _(" not found.")
        missing_mlt_services.append(msg)
    for t in mlttransitions.not_found_transitions:
        msg = "mlt.Transition " + t.mlt_service_id + _(" for transition ") + t.name + _(" not found.")
    missing_services_sw = _get_items_in_scroll_window(missing_mlt_services, 100, 300, 200) # 100 == we want all of these to be in one column
    
    l_pane = gtk.VBox(False, 4)
    l_pane.pack_start(guiutils.get_named_frame(_("General"), vbox), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Filters"), filters_sw), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Transitions"), transitions_sw), False, False, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("Missing MLT Services"), missing_services_sw), False, False, 0)
    l_pane.pack_start(gtk.Label(), True, True, 0)

    r_pane = gtk.VBox(False, 4)
    r_pane.pack_start(guiutils.get_named_frame(_("Video Codecs"), v_codecs_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Audio Codecs"), a_codecs_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Formats"), formats_sw), False, False, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Render Options"), enc_opt_sw), False, False, 0)
    r_pane.pack_start(gtk.Label(), True, True, 0)

    pane = gtk.HBox(False, 4)
    pane.pack_start(l_pane, False, False, 0)
    pane.pack_start(r_pane, False, False, 0)
    
    a = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    a.set_padding(6, 24, 12, 12)
    a.add(pane)
    
    dialog.vbox.pack_start(a, True, True, 0)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

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

def color_clip_dialog(callback):
    dialog = gtk.Dialog(_("Create Color Clip"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("Create").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    alignment, selection_widgets = panels.get_color_clip_panel()
    dialog.connect('response', callback, selection_widgets)
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()

def preferences_dialog(callback, thumbs_clicked_callback):
    dialog = gtk.Dialog(_("Editor Preferences"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    
    gen_opts_panel, gen_opts_widgets = panels.get_general_options_panel(thumbs_clicked_callback)
    edit_prefs_panel, edit_prefs_widgets = panels.get_edit_prefs_panel()

    notebook = gtk.Notebook()
    notebook.set_size_request(PREFERENCES_WIDTH, PREFERENCES_HEIGHT)

    notebook.append_page(gen_opts_panel, gtk.Label(_("General")))
    notebook.append_page(edit_prefs_panel, gtk.Label(_("Editing")))
    
    dialog.connect('response', callback, (gen_opts_widgets, edit_prefs_widgets))
    dialog.vbox.pack_start(notebook, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()

def file_properties_dialog(data):
    dialog = gtk.Dialog(_("File Properties"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    panel = panels.get_file_properties_panel(data)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(panel)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def clip_properties_dialog(data):
    dialog = gtk.Dialog(_("Clip Properties"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
                        
    panel = panels.get_clip_properties_panel(data)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(panel)
    
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
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(panel)

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

def get_load_dialog():
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

def get_media_load_progress_dialog():
    dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
    dialog.set_title(_("Loading Media Files"))

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
    
def get_recreate_icons_progress_dialog():
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

def profiles_manager_dialog(callbacks):
    dialog = gtk.Dialog(_("Profiles Manager"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))
    
    load_values_clicked, save_profile_clicked, delete_user_profiles_clicked, hide_profiles_clicked, unhide_profiles_clicked = callbacks
    


    panel2, user_profiles_view = panels.get_manage_profiles_panel(delete_user_profiles_clicked, hide_profiles_clicked, unhide_profiles_clicked)
    alignment2 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment2.set_padding(12, 12, 12, 12)
    alignment2.add(panel2)

    panel1 = panels.get_create_profiles_panel(load_values_clicked, save_profile_clicked, user_profiles_view)
    alignment1 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment1.set_padding(12, 12, 12, 12)
    alignment1.add(panel1)

    notebook = gtk.Notebook()
    notebook.set_size_request(PROFILES_WIDTH, PROFILES_HEIGHT)

    notebook.append_page(alignment1, gtk.Label(_("Create New Profile")))
    notebook.append_page(alignment2, gtk.Label(_("Manage Profiles")))

    dialog.connect('response', _dialog_destroy)
    
    dialog.vbox.pack_start(notebook, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()
    return dialog

def autosave_recovery_dialog(callback, parent_window):
    title = _("Open last autosave?")
    msg1 = _("It seems that Flowblade exited abnormally last time.\n\n")
    msg3 = _("It is NOT possible to open this autosaved version later.")
    msg = msg1 + msg3
    content = panels.get_warning_message_dialog_panel(title, msg)
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

def no_monitor_clip_info(parent_window):
    primary_txt = _("No Clip loaded into Monitor")
    secondary_txt = _("Can't do the requested edit because there is no Clip in Monitor.")
    info_message(primary_txt, secondary_txt, parent_window)

def monitor_clip_too_short(parent_window):
    primary_txt = _("Defined range in Monitor Clip is too short")
    secondary_txt = _("Can't do the requested edit because Mark In -> Mark Out Range or Clip is too short.")
    info_message(primary_txt, secondary_txt, parent_window)

def get_tracks_count_change_dialog(callback):
    default_profile_index = mltprofiles.get_default_profile_index()
    default_profile = mltprofiles.get_default_profile()

    dialog = gtk.Dialog(_("Change Sequence Tracks Count"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                        _("Change Tracks"), gtk.RESPONSE_ACCEPT))

    tracks_combo, tracks_combo_values_list = guicomponents.get_track_counts_combo_and_values_list()
    tracks_select = panels.get_two_column_box(gtk.Label(_("New Number of Tracks:")),
                                               tracks_combo,
                                               250)
    info_text = _("Please note:\n") + \
                _("* It is recommended that you save Project before completing this operation\n") + \
                _("* There is no Undo for this operation\n") + \
                _("* Current Undo Stack will be destroyed\n") + \
                _("* All Clips and Compositors on deleted Tracks will be permanently destroyed")
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


def get_new_sequence_dialog(callback, default_name):
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

def not_valid_producer_dialog(file_path, parent_window):
    primary_txt = _("Can't open non-valid media")
    secondary_txt = _("File: ") + file_path + _("\nis not a valid media file.")
    warning_message(primary_txt, secondary_txt, parent_window, is_info=True)
    
