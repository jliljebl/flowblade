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
import editorpersistance
import mltprofiles
import panels
import projectdata
import respaths

# Gui consts
PREFERENCES_WIDTH = 550
PREFERENCES_HEIGHT = 300

PROFILES_WIDTH = 480
PROFILES_HEIGHT = 520

def new_project_dialog(callback):
    default_profile_index = editorpersistance.prefs.default_profile_index
    default_profile = mltprofiles.get_profile_for_index(default_profile_index)

    dialog = gtk.Dialog(_("New Project"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                        
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

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 12, 12)
    alignment.add(profiles_frame)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, out_profile_combo)
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
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.add_pattern("*" + projectdata.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_project_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Project As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT), None)
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

def save_ffmpep_optsdialog(callback, opts_extension):
    dialog = gtk.FileChooserDialog(_("Save Render Args As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT), None)
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
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), None)
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
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

    panel = panels.get_render_progress_panel()
    
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
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
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
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
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
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

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

def color_clip_dialog(callback):
    dialog = gtk.Dialog(_("Create Color Clip"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    _("Create").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    alignment, selection_widgets = panels.get_color_clip_panel()
    dialog.connect('response', callback, selection_widgets)
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.show_all()

def preferences_dialog(callback, thumbs_clicked_callback):
    dialog = gtk.Dialog(_("Editor Preferences"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
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
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                        
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
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                        
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
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
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
