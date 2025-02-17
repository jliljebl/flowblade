"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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

from gi.repository import Gtk, GLib

import locale
import os
from gi.repository import Pango

import appconsts
import dialogutils
import editorstate
import editorpersistance
import gui
import guicomponents
import guiutils
import gtkbuilder
import mltenv
import mltprofiles
import mltfilters
import mlttransitions
import panels
import projectdatavaultgui
import projectdatavault
import renderconsumer
import respaths
import utils
import utilsgtk


def new_project_dialog(callback):
    default_desc = mltprofiles.get_profile_name_for_index(mltprofiles.get_default_profile_index())
    default_profile = mltprofiles.get_default_profile()

    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)

    out_profile_combo = guicomponents.get_profiles_combo()
    out_profile_combo.set_selected(default_desc)
    out_profile_combo.widget.connect('changed', lambda w: _new_project_profile_changed(out_profile_combo, profile_info_box))
    profile_select = panels.get_two_column_box(Gtk.Label(label=_("Project profile:")),
                                               out_profile_combo.widget,
                                               250)
    profile_info_panel = guicomponents.get_profile_info_box(default_profile, False)
    profile_info_box = Gtk.VBox()
    profile_info_box.add(profile_info_panel)
    profiles_vbox = guiutils.get_vbox([profile_select,profile_info_box], False)
    profiles_frame = panels.get_named_frame(_("Profile"), profiles_vbox)
    profiles_frame.set_margin_end(18)
    
    tracks_select = guicomponents.TracksNumbersSelect(appconsts.INIT_V_TRACKS, appconsts.INIT_A_TRACKS)
    tracks_vbox = guiutils.get_vbox([tracks_select.widget], False)
    tracks_frame = panels.get_named_frame(_("Tracks"), tracks_vbox)
    tracks_frame.set_margin_end(18)

    vault_combo = projectdatavaultgui.get_vault_select_combo(projectdatavault.get_active_vault_index())
    add_vault_button = Gtk.Button(label=_("Create New Data Store"))
    add_vault_button.connect("clicked", lambda w: projectdatavaultgui.show_create_data_dialog(_create_data_store_callback, vault_combo))
    add_vault_button.set_margin_start(12)
    vault_row = Gtk.HBox(False, 8)
    vault_row.pack_start(vault_combo, True, True, 0)
    vault_row.pack_start(add_vault_button, False, False, 0)
    
    vault_vbox = guiutils.get_vbox([vault_row], False)
    vault_frame = panels.get_named_frame(_("Data Store"), vault_vbox)
    
    ok_button = Gtk.Button(label=_("Ok"))
    ok_button.connect("clicked", lambda w: callback(dialog, Gtk.ResponseType.ACCEPT, out_profile_combo, tracks_select, vault_combo))
    cancel_button = Gtk.Button(label=_("Cancel"))
    cancel_button.connect("clicked", lambda w: callback(dialog, Gtk.ResponseType.REJECT, out_profile_combo, tracks_select, vault_combo))
    dialog_buttons_box = dialogutils.get_ok_cancel_button_row(ok_button, cancel_button)
    dialog_buttons_box.set_margin_top(24)
        
    vbox = guiutils.get_vbox([profiles_frame, tracks_frame, vault_frame, dialog_buttons_box], False)
    guiutils.set_margins(vbox, 12, 12, 12, 12)

    dialog.set_transient_for(gui.editor_window.window)
    dialog.set_title(_("New Project"))
    dialog.set_resizable(False)
    dialog.add(vbox)
    dialog.set_position(Gtk.WindowPosition.CENTER)

    dialog.show_all()

def _new_project_profile_changed(out_profile_combo, profile_info_box):
    profile_name = out_profile_combo.get_selected()
    profile = mltprofiles.get_profile(profile_name)

    info_box_children = profile_info_box.get_children()
    for child in info_box_children:
        profile_info_box.remove(child)

    info_panel = guicomponents.get_profile_info_box(profile, True)
    profile_info_box.add(info_panel)
    profile_info_box.show_all()
    info_panel.show()

def _create_data_store_callback(dialog, response, widgets):
    if response != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # Get and verify vault data.
    data_folder_button, name_entry, vaults_combo = widgets
    dir_path = data_folder_button.get_filename()
    user_visible_name = name_entry.get_text() 
    dialog.destroy()
                    
    if not os.listdir(dir_path):
        pass
    else:
        primary_txt = _("Selected folder was not empty!")
        secondary_txt = _("Can't add non-empty folder as new Project Data Folder.")
        dialogutils.warning_message(primary_txt, secondary_txt, None)
        return

    if len(user_visible_name) == 0:
        user_visible_name = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())

    # Add new vault
    vaults_obj = projectdatavault.get_vaults_object()
    vaults_obj.add_user_vault(user_visible_name, dir_path)
    vaults_obj.save()

    projectdatavaultgui.fill_vaults_combo(vaults_combo, len(vaults_obj.user_vaults_data))

def change_profile_project_dialog(project, callback):
    project_name = project.name.rstrip(".flb")
    default_profile = mltprofiles.get_default_profile()

    dialog = Gtk.Dialog(_("Change Project Profile"), None,
                        None,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Save With Changed Profile"), Gtk.ResponseType.ACCEPT))

    info_label = guiutils.bold_label(_("Project Profile can only changed by saving a version\nwith different profile."))

    default_desc = mltprofiles.get_profile_name_for_index(mltprofiles.get_default_profile_index())
    default_profile = mltprofiles.get_default_profile()


    out_profile_combo = guicomponents.get_profiles_combo()
    out_profile_combo.set_selected(default_desc)
    
    profile_select = panels.get_two_column_box(Gtk.Label(label=_("Project profile:")),
                                               out_profile_combo.widget,
                                               250)

    profile_info_panel = guicomponents.get_profile_info_box(default_profile, False)
    profile_info_box = Gtk.VBox()
    profile_info_box.add(profile_info_panel)
    profiles_vbox = guiutils.get_vbox([profile_select,profile_info_box], False)
    profiles_frame = panels.get_named_frame(_("New Profile"), profiles_vbox)

    out_folder = gtkbuilder.get_file_chooser_button(_("Select Folder"))
    out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    out_folder.set_current_folder(os.path.expanduser("~") + "/")
    out_folder.set_local_only(True)
    out_folder_row = panels.get_two_column_box(Gtk.Label(label=_("Folder:")), out_folder,  250)

    project_name_entry = Gtk.Entry()
    project_name_entry.set_text(project_name + "_NEW_PROFILE.flb")

    name_box = Gtk.HBox(False, 8)
    name_box.pack_start(project_name_entry, True, True, 0)

    movie_name_row = panels.get_two_column_box(Gtk.Label(label=_("Project Name:")), name_box,  250)

    new_file_vbox = guiutils.get_vbox([out_folder_row, movie_name_row], False)

    new_file_frame = panels.get_named_frame(_("New Project File"), new_file_vbox)

    vbox = guiutils.get_vbox([info_label, guiutils.pad_label(2, 24), profiles_frame, new_file_frame], False)

    alignment = dialogutils.get_default_alignment(vbox)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.vbox.pack_start(alignment, True, True, 0)
    _default_behaviour(dialog)
    dialog.connect('response', callback, out_profile_combo, out_folder, project_name_entry)
    
    out_profile_combo.widget.connect('changed', lambda w: _new_project_profile_changed(out_profile_combo, profile_info_box))
    dialog.show_all()

def export_ardour_session_folder_select(sample_rate_combo, callback):
    dialog = Gtk.Dialog(_("Save Sequence Audio As Ardour Session"), None,
                        None,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Export"), Gtk.ResponseType.ACCEPT))

    # project folder
    project_folder = gtkbuilder.get_file_chooser_button(_("Select Ardour Session Folder"))
    project_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    project_folder.set_current_folder(os.path.expanduser("~") + "/")

    project_folder_label = Gtk.Label(label=_("Select Ardour Session Folder:"))

    project_folder_row = guiutils.get_two_column_box(project_folder_label, project_folder, 250)

    sample_rate_label = Gtk.Label(label=_("Sample Rate:"))
    sample_rate_row = panels.get_two_column_box(sample_rate_label, sample_rate_combo, 250)

    type_vbox = Gtk.VBox(False, 2)
    type_vbox.pack_start(project_folder_row, False, False, 0)
    type_vbox.pack_start(sample_rate_row, False, False, 0)

    vbox = Gtk.VBox(False, 2)
    vbox.add(type_vbox)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, project_folder, sample_rate_combo)
    dialog.show_all()
    
def load_project_dialog(callback, parent=None, title_text=None):
    if parent == None:
        parent = gui.editor_window.window

    if title_text == None:
       title_text = _("Select Project File")

    dialog = Gtk.FileChooserDialog(title_text, parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Flowblade Projects"))
    file_filter.add_pattern("*" + appconsts.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_project_as_dialog(callback, current_name, open_dir, parent=None):
    if parent == None:
        parent = gui.editor_window.window

    dialog = Gtk.FileChooserDialog(_("Save Project As"), parent,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name(current_name)
    dialog.set_do_overwrite_confirmation(True)
    if open_dir != None:
        dialog.set_current_folder(open_dir)

    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.add_pattern("*" + appconsts.PROJECT_FILE_EXTENSION)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_effects_compositors_values(callback, default_name, saving_effect=True, filter_object=None, saving_stack=False):
    parent = gui.editor_window.window

    if saving_effect == True:
        title = _("Save Effect Values Data")
    else:
        title = _("Save Compositor Values Data")
    
    if saving_stack == True:
        title = _("Save Effects Stack Values Data")

    dialog = Gtk.FileChooserDialog(title, parent,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name(default_name)
    dialog.set_do_overwrite_confirmation(True)

    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Stack/Effect/Compositor Values Data"))
    file_filter.add_pattern("*" + "data")
    dialog.add_filter(file_filter)
    if filter_object == None:
        dialog.connect('response', callback)
    else:
        dialog.connect('response', callback, filter_object)
    dialog.show()

def load_effects_compositors_values_dialog(callback, loading_effect=True, filter_object=None, loading_stack=False):
    parent = gui.editor_window.window

    if loading_effect == True:
        title_text = _("Load Effect Values Data")
    else:
        title_text = _("Load Compositor Values Data") 
    
    if loading_stack == True:
        title_text = _("Load Effects Stack Values Data")

    dialog = Gtk.FileChooserDialog(title_text, parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Effect/Compositor Values Data"))
    file_filter.add_pattern("*" + "data")
    dialog.add_filter(file_filter)
    if filter_object == None:
        dialog.connect('response', callback)
    else:
        dialog.connect('response', callback, filter_object)
    dialog.show()

def save_layout_data(callback, data):
    parent = gui.editor_window.window

    dialog = Gtk.FileChooserDialog( _("Save Layout"), parent,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name(_("flowblade_custom_layout.layout_data"))
    dialog.set_do_overwrite_confirmation(True)

    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Flowblade Layout Data"))
    file_filter.add_pattern("*" + "layout_data")
    dialog.add_filter(file_filter)
    
    dialog.connect('response', callback, data)
    dialog.show()
    
def load_layout_data(callback):
    parent = gui.editor_window.window
    dialog = Gtk.FileChooserDialog(_("Load Layout"), parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Flowblade Layout Data"))
    file_filter.add_pattern("*" + "layout_data")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_media_plugin_plugin_properties(callback, default_name, data):
    parent = gui.editor_window.window

    dialog = Gtk.FileChooserDialog( _("Save Generator Properties"), parent,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name(default_name)
    dialog.set_do_overwrite_confirmation(True)

    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Flowblade Generator Properties"))
    file_filter.add_pattern("*" + "mediaplugindata")
    dialog.add_filter(file_filter)
    
    dialog.connect('response', callback, data)
    dialog.show()

def load_media_plugin_plugin_properties(callback):
    parent = gui.editor_window.window
    dialog = Gtk.FileChooserDialog(_("Load Generator Properties"), parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(_("Flowblade Generator Properties"))
    file_filter.add_pattern("*" + "mediaplugindata")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def get_media_plugin_length(callback, data):
    dialog = Gtk.Dialog(_("Create Cloned Media Item"), gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Create"), Gtk.ResponseType.ACCEPT))

    clip, track, item_id, item_data = data
    LABEL_WIDTH = 200
    
    name_label = Gtk.Label(label=_("Name:"))
    name_entry = Gtk.Entry()
    name_entry.set_text(clip.name)

    length_label = Gtk.Label(label=_("Length in Frames:"))
    length_spin = Gtk.SpinButton.new_with_range(15, 10000, 1)
    length_spin.set_value(200)

    name_row = guiutils.get_two_column_box(name_label, name_entry, LABEL_WIDTH)
    
    frames_row  = guiutils.get_two_column_box(length_label, length_spin, LABEL_WIDTH)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(name_row, False, False, 0)
    vbox.pack_start(frames_row, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(24, 24), False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, data, length_spin, name_entry)
    dialog.show_all()



def export_xml_dialog(callback, project_name):
    _export_file_name_dialog(callback, project_name, _("Export Project as XML to"))

def _export_file_name_dialog(callback, project_name, dialog_title):
    dialog = Gtk.FileChooserDialog(dialog_title,  gui.editor_window.window,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Export"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    project_name = project_name.strip(".flb")
    dialog.set_current_name(project_name + ".xml")
    dialog.set_do_overwrite_confirmation(True)

    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def compound_clip_name_dialog(callback, default_name, dialog_title, data=None):
    
    dialog = Gtk.Dialog(dialog_title,  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Create"), Gtk.ResponseType.ACCEPT))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text(default_name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("Clip Name:")),
                                               name_entry,
                                               180)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(name_select, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    if data == None:
        dialog.connect('response', callback, name_entry)
    else:
        dialog.connect('response', callback, (data, name_entry))
    dialog.show_all()
    
def save_env_data_dialog(callback):
    dialog = Gtk.FileChooserDialog(_("Save Runtime Environment Data"),  gui.editor_window.window,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name("flowblade_runtime_environment_data")
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def save_cont_clip_edit_data(callback, default_name, edit_data):
    dialog = Gtk.FileChooserDialog(_("Save Container Clip Edit Data"),  gui.editor_window.window,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name(default_name)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback, edit_data)
    dialog.show()

def load_cont_clip_edit_data(callback):
    parent = gui.editor_window.window

    title_text = _("Load Container Clip Program Edit Data") 

    dialog = Gtk.FileChooserDialog(title_text, parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()
    
def rendered_clips_no_home_folder_dialog():
    dialogutils.warning_message(_("Can't make home folder render clips folder"),
                            _("Please create and select some other folder then \'") +
                            os.path.expanduser("~") + _("\' as render clips folder"),
                            gui.editor_window.window)

def exit_confirm_dialog(callback, msg, parent_window, project_name, data=None):
    title = _("Save project '") + project_name + _("' before exiting?")
    content = dialogutils.get_warning_message_dialog_panel(title, msg, False, "dialog-information")

    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Don't Save"), Gtk.ResponseType.CLOSE,
                        _("Cancel"), Gtk.ResponseType.CANCEL,
                        _("Save"), Gtk.ResponseType.YES))

    alignment = dialogutils.get_default_alignment(content)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    if data == None:
        dialog.connect('response', callback)
    else:
        dialog.connect('response', callback, data)
    dialog.show_all()

def close_confirm_dialog(callback, msg, parent_window, project_name):
    title = _("Save project '") + project_name + _("' before closing project?")
    content = dialogutils.get_warning_message_dialog_panel(title, msg, False, "dialog-information")
    align = dialogutils.get_default_alignment(content)

    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Don't Save"), Gtk.ResponseType.CLOSE,
                        _("Cancel"), Gtk.ResponseType.CANCEL,
                        _("Save"), Gtk.ResponseType.YES))

    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback)
    dialog.show_all()

def about_dialog(parent_window):
    dialog = Gtk.Dialog(_("About"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("OK"), Gtk.ResponseType.ACCEPT))

    # Application tab
    img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
    flow_label = Gtk.Label(label="Flowblade Movie Editor")
    ver_label = Gtk.Label(label="2.18.1")
    janne_label = Gtk.Label(label="Copyright 2024 Janne Liljeblad and contributors.")
    page_label = Gtk.Label(label=_("Project page:") + " " + "<a href=\"https://github.com/jliljebl/flowblade\">https://github.com/jliljebl/flowblade</a>")
    page_label.set_use_markup(True)
    flow_label.modify_font(Pango.FontDescription("sans bold 14"))
    janne_label.modify_font(Pango.FontDescription("sans 10"))
    page_label.modify_font(Pango.FontDescription("sans 10"))

    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox.pack_start(img, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(30, 4), False, False, 0)
    vbox.pack_start(flow_label, False, False, 0)
    vbox.pack_start(ver_label, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.pack_start(janne_label, False, False, 0)
    vbox.pack_start(page_label, False, False, 0)

    alignment =  dialogutils.get_default_alignment(vbox)
    alignment.set_size_request(450, 370)

    # Thanks tab
    up_label = Gtk.Label(label=_("Upstream:"))
    up_projs = Gtk.Label(label="MLT")
    up_projs2 = Gtk.Label(label="FFMpeg, Frei0r, LADSPA, Cairo, Gnome, Linux")
    tools_label = Gtk.Label(label=_("Tools:"))
    tools_list = Gtk.Label(label="Geany, Inkscape, Gimp, ack-grep")

    up_label.modify_font(Pango.FontDescription("sans bold 12"))
    tools_label.modify_font(Pango.FontDescription("sans bold 12"))

    vbox2 = Gtk.VBox(False, 4)
    vbox2.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox2.pack_start(up_label, False, False, 0)
    vbox2.pack_start(up_projs, False, False, 0)
    vbox2.pack_start(up_projs2, False, False, 0)
    vbox2.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox2.pack_start(tools_label, False, False, 0)
    vbox2.pack_start(tools_list, False, False, 0)
    vbox2.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox2.pack_start(Gtk.Label(), True, True, 0)

    alignment2 = dialogutils.get_default_alignment(vbox2)
    alignment2.set_size_request(450, 370)

    # Licence tab
    license_view = guicomponents.get_gpl3_scroll_widget((450, 370))
    alignment3 = dialogutils.get_default_alignment(license_view)
    alignment3.set_size_request(450, 370)

    # Developers tab
    lead_label = Gtk.Label(label=_("Lead Developer:"))
    lead_label.modify_font(Pango.FontDescription("sans bold 12"))
    lead_info = Gtk.Label(label="Janne Liljeblad")
    developers_label = Gtk.Label(_("Developers:"))
    developers_label.modify_font(Pango.FontDescription("sans bold 12"))

    devs_file = open(respaths.DEVELOPERS_DOC)
    devs_text = devs_file.read()
    devs_info = Gtk.Label(label=devs_text)

    contributos_label = Gtk.Label(label=_("Contributors:"))
    contributos_label.modify_font(Pango.FontDescription("sans bold 12"))
    
    contributors_file = open(respaths.CONTRIBUTORS_DOC)
    contributors_text = contributors_file.read()

    contributors_view = Gtk.TextView()
    contributors_view.set_editable(False)
    contributors_view.set_pixels_above_lines(2)
    contributors_view.set_left_margin(2)
    contributors_view.set_wrap_mode(Gtk.WrapMode.WORD)
    contributors_view.get_buffer().set_text(contributors_text)
    contributors_view.set_justification(2) # Centered
    guiutils.set_margins(contributors_view, 0, 0, 30, 30)
    
    vbox3 = Gtk.VBox(False, 4)
    vbox3.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox3.pack_start(lead_label, False, False, 0)
    vbox3.pack_start(lead_info, False, False, 0)
    vbox3.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox3.pack_start(developers_label, False, False, 0)
    vbox3.pack_start(guiutils.get_centered_box([devs_info]), False, False, 0)
    vbox3.pack_start(guiutils.get_pad_label(30, 22), False, False, 0)
    vbox3.pack_start(contributos_label, False, False, 0)
    vbox3.pack_start(contributors_view, False, False, 0)
    
    alignment5 = dialogutils.get_default_alignment(vbox3)
    alignment5.set_size_request(450, 370)

    # Translations tab
    translations_label = Gtk.Label(label=_("Translations by:"))
    translations_label.modify_font(Pango.FontDescription("sans bold 12"))
    translations_view = guicomponents.get_translations_scroll_widget((450, 370))

    vbox4 = Gtk.VBox(False, 4)
    vbox4.pack_start(guiutils.get_pad_label(30, 12), False, False, 0)
    vbox4.pack_start(translations_label, False, False, 0)
    vbox4.pack_start(translations_view, False, False, 0)

    alignment4 = dialogutils.get_default_alignment(vbox4)
    alignment4.set_size_request(450, 370)

    notebook = Gtk.Notebook()
    notebook.set_size_request(450 + 10, 370 + 10)
    notebook.append_page(alignment, Gtk.Label(label=_("Application")))
    notebook.append_page(alignment2, Gtk.Label(label=_("Thanks")))
    notebook.append_page(alignment3, Gtk.Label(label=_("License")))
    notebook.append_page(alignment5, Gtk.Label(label=_("Developers")))
    notebook.append_page(alignment4, Gtk.Label(label=_("Translations")))
    guiutils.set_margins(notebook, 6, 6, 6, 0)

    dialog.vbox.pack_start(notebook, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def environment_dialog(parent_window):
    dialog = Gtk.Dialog(_("Runtime Environment"),  gui.editor_window.window,
                        Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("OK"), Gtk.ResponseType.ACCEPT))

    COLUMN_WIDTH = 650

    r1 = guiutils.get_left_justified_box([Gtk.Label(label=_("MLT version: ")), Gtk.Label(label=str(editorstate.mlt_version))])
    try:
        major, minor, rev = editorstate.gtk_version
        gtk_ver = str(major) + "." + str(minor) + "." + str(rev)
    except:
        gtk_ver = str(editorstate.gtk_version)
    r2 = guiutils.get_left_justified_box([Gtk.Label(label=_("GTK version: ")), Gtk.Label(label=gtk_ver)])
    lc, encoding = locale.getdefaultlocale()
    r3 = guiutils.get_left_justified_box([Gtk.Label(label=_("Locale: ")), Gtk.Label(label=str(lc))])

    if editorstate.app_running_from == editorstate.RUNNING_FROM_INSTALLATION:
        run_type = _("INSTALLATION")
    elif editorstate.app_running_from == editorstate.RUNNING_FROM_FLATPAK:
        run_type = "FLATPAK"
    else:
        run_type = _("DEVELOPER VERSION")

    r4 = guiutils.get_left_justified_box([Gtk.Label(label=_("Running from: ")), Gtk.Label(label=run_type)])

    vbox = Gtk.VBox(False, 4)
    vbox.pack_start(r1, False, False, 0)
    vbox.pack_start(r2, False, False, 0)
    vbox.pack_start(r3, False, False, 0)
    vbox.pack_start(r4, False, False, 0)


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

    l_pane = Gtk.VBox(False, 4)
    l_pane.pack_start(guiutils.get_named_frame(_("General"), vbox), True, True, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Filters"), filters_sw), True, True, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("MLT Transitions"), transitions_sw), True, True, 0)
    l_pane.pack_start(guiutils.get_named_frame(_("Missing MLT Services"), missing_services_sw), True, True, 0)

    r_pane = Gtk.VBox(False, 4)
    r_pane.pack_start(guiutils.get_named_frame(_("Video Codecs"), v_codecs_sw), True, True, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Audio Codecs"), a_codecs_sw), True, True, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Formats"), formats_sw), True, True, 0)
    r_pane.pack_start(guiutils.get_named_frame(_("Render Options"), enc_opt_sw), True, True, 0)

    pane = Gtk.HBox(False, 4)
    pane.pack_start(l_pane, True, True, 0)
    pane.pack_start(guiutils.pad_label(5, 5), False, False, 0)
    pane.pack_start(r_pane, True, True, 0)

    a = dialogutils.get_default_alignment(pane)

    dialog.vbox.pack_start(a, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()
    dialog.set_resizable(True)

def _get_items_in_scroll_window(items, rows_count, w, h):
    row_widgets = []
    for i in items:
        row = guiutils.get_left_justified_box([Gtk.Label(label=i)])
        row_widgets.append(row)
    items_pane = _get_item_columns_panel(row_widgets, rows_count)

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.add(items_pane)
    sw.set_size_request(w, h)
    return sw

def _get_item_columns_panel(items, rows):
    hbox = Gtk.HBox(False, 4)
    n_item = 0
    col_items = 0
    vbox = Gtk.VBox()
    hbox.pack_start(vbox, False, False, 0)
    while n_item < len(items):
        item = items[n_item]
        vbox.pack_start(item, False, False, 0)
        n_item += 1
        col_items += 1
        if col_items > rows:
            vbox = Gtk.VBox()
            hbox.pack_start(vbox, False, False, 0)
            col_items = 0
    return hbox

def file_properties_dialog(data):
    dialog = Gtk.Dialog(_("File Properties"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        ( _("OK"), Gtk.ResponseType.ACCEPT))

    panel = panels.get_file_properties_panel(data)

    alignment = dialogutils.get_default_alignment(panel)
    guiutils.set_margins(dialog.vbox, 6, 6, 6, 6)
    dialog.vbox.pack_start(alignment, False, False, 0)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def clip_properties_dialog(data):
    dialog = Gtk.Dialog(_("Clip Properties"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        ( _("OK"), Gtk.ResponseType.ACCEPT))

    panel = panels.get_clip_properties_panel(data)
    alignment = dialogutils.get_default_alignment(panel)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()
   
def _dialog_destroy(dialog, response):
    dialog.destroy()

def _default_behaviour(dialog):
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_resizable(False)

def load_dialog():
    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    dialog.set_title(_("Loading project"))

    info_label = Gtk.Label(label="")
    info_label.set_ellipsize(Pango.EllipsizeMode.END)
    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(info_label, False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_bar = Gtk.ProgressBar()
    progress_bar.set_fraction(0.2)
    progress_bar.set_pulse_step(0.1)

    est_box = Gtk.HBox(False, 2)
    est_box.pack_start(Gtk.Label(label=""),False, False, 0)
    est_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.add(alignment)
    dialog.set_default_size(500, 70)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.show_all()

    # Make refs available for updates
    dialog.progress_bar = progress_bar
    dialog.info = info_label

    return dialog

def recreate_icons_progress_dialog():
    return _text_info_prograss_dialog(_("Recreating icons"))

def update_media_lengths_progress_dialog():
    return _text_info_prograss_dialog(_("Update media lengths data"))

def audio_sync_active_dialog():
    return _text_info_prograss_dialog(_("Comparing Audio Data..."))
    
def _text_info_prograss_dialog(title):
    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    dialog.set_title(title)

    info_label = Gtk.Label(label="")
    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(info_label, False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_bar = Gtk.ProgressBar()
    progress_bar.set_fraction(0.0)

    est_box = Gtk.HBox(False, 2)
    est_box.pack_start(Gtk.Label(label=""),False, False, 0)
    est_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(Gtk.WindowPosition.CENTER)
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
    align = guiutils.set_margins(content, 12, 12, 12, 12)

    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.CANCEL,
                        _("Force Delete"), Gtk.ResponseType.OK))

    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.CANCEL)
    dialog.connect('response', callback)

    dialog.show_all()

def autosave_recovery_dialog(callback, parent_window):
    title = _("Open last autosave?")
    msg1 = _("It seems that Flowblade exited abnormally last time.\n\n")
    msg2 = _("If there is another instance of Flowblade running,\nthis dialog has probably detected its autosave file.\n\n")
    msg3 = _("It is NOT possible to open this autosaved version later.")
    msg = msg1 + msg2 + msg3
    content = dialogutils.get_warning_message_dialog_panel(title, msg)
    align = dialogutils.get_default_alignment(content)

    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Continue with default 'untitled' project"), Gtk.ResponseType.CANCEL,
                        _("Open Autosaved Project"), Gtk.ResponseType.OK))

    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.vbox.set_margin_start(6)
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

    delete_all = Gtk.Button(label=_("Delete all autosaves"))
    delete_all.connect("clicked", lambda w : _autosaves_delete_all_clicked(autosaves, autosaves_view, dialog))
    delete_all_but_selected = Gtk.Button(label=_("Delete all but selected autosave"))
    delete_all_but_selected.connect("clicked", lambda w : _autosaves_delete_unselected(autosaves, autosaves_view))

    delete_buttons_vbox = Gtk.HBox()
    delete_buttons_vbox.pack_start(Gtk.Label(), True, True, 0)
    delete_buttons_vbox.pack_start(delete_all, False, False, 0)
    delete_buttons_vbox.pack_start(delete_all_but_selected, False, False, 0)
    delete_buttons_vbox.pack_start(Gtk.Label(), True, True, 0)

    pane = Gtk.VBox()
    pane.pack_start(info_panel, False, False, 0)
    pane.pack_start(delete_buttons_vbox, False, False, 0)
    pane.pack_start(guiutils.get_pad_label(12,12), False, False, 0)
    pane.pack_start(autosaves_view, False, False, 0)

    align = dialogutils.get_default_alignment(pane)

    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Continue with default 'untitled' project"), Gtk.ResponseType.CANCEL,
                        _("Open Selected Autosave"), Gtk.ResponseType.OK))

    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.vbox.set_margin_start(6)
    _default_behaviour(dialog)
    dialog.connect('response', response_callback, autosaves_view, autosaves)
    dialog.show_all()

def _autosaves_delete_all_clicked(autosaves, autosaves_view, dialog):
    for autosave in autosaves:
        os.remove(autosave.path)
    dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
    del autosaves[:]
    autosaves_view.fill_data_model(autosaves)

def _autosaves_delete_unselected(autosaves, autosaves_view):
    selected_autosave = autosaves.pop(autosaves_view.get_selected_indexes_list()[0])
    for autosave in autosaves:
        os.remove(autosave.path)
    del autosaves[:]
    autosaves.append(selected_autosave)
    autosaves_view.fill_data_model(autosaves)

def confirm_track_add_delete(is_add, is_video, v_tracks, a_tracks, callback):

    title = ""
    action = ""
    if is_add == True:
        if is_video == True:
            title = _("Confirm Adding Video Track")
            action = _("Add Video Track")
        else:
            title = _("Confirm Adding Audio Track")
            action = _("Add Audio Track")
    else:
        if is_video == True:
            title = _("Confirm Deleting Video Track")
            action = _("Delete Video Track")
        else:
            title = _("Confirm Deleting Audio Track")
            action = _("Delete Audio Track")

    dialog = Gtk.Dialog(title,  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        action, Gtk.ResponseType.ACCEPT))
                        
    info_text = _("<b>Please note:</b>\n") + \
                "    \u2022" + _(" There is no Undo for this operation\n") + \
                "    \u2022" + _(" Current Undo Stack will be destroyed\n")
    info_label = Gtk.Label(label=info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])

    pad = guiutils.get_pad_label(24, 12)

    tracks_vbox = Gtk.VBox(False, 2)
    tracks_vbox.pack_start(info_box, False, False, 0)
    #tracks_vbox.pack_start(pad, False, False, 0)

    alignment = dialogutils.get_alignment2(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, v_tracks, a_tracks)
    dialog.show_all()
    
def tracks_count_change_dialog(callback, v_tracks, a_tracks):
    dialog = Gtk.Dialog(_("Change Sequence Tracks Count"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Change Tracks"), Gtk.ResponseType.ACCEPT))

    tracks_select = guicomponents.TracksNumbersSelect(v_tracks, a_tracks)

    info_text = _("Please note:\n") + \
                "\u2022" + _(" When reducing the number of tracks the top Video track and/or bottom Audio track will be removed\n") + \
                "\u2022" + _(" There is no Undo for this operation\n") + \
                "\u2022" + _(" Current Undo Stack will be destroyed\n") + \
                "\u2022" + _(" All Clips and Compositors on deleted Tracks will be permanently destroyed")
    info_label = Gtk.Label(label=info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])

    pad = guiutils.get_pad_label(24, 24)

    tracks_vbox = Gtk.VBox(False, 2)
    tracks_vbox.pack_start(info_box, False, False, 0)
    tracks_vbox.pack_start(pad, False, False, 0)
    tracks_vbox.pack_start(tracks_select.widget, False, False, 0)

    alignment = dialogutils.get_alignment2(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, tracks_select)
    dialog.show_all()

def replace_media_dialog(media_file, callback):
    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    dialog.set_title(_("Replace Media Item in Project"))
    dialog.set_transient_for(gui.editor_window.window)

    info_text = _("Please note:\n\n") + \
                "\u2022" + _(" It is recommended that you save Project before completing this operation.\n") + \
                "\u2022" + _(" There is no Undo for this operation.\n") + \
                "\u2022" + _(" Current Undo Stack will be destroyed.\n") + \
                "\u2022" + _(" Replacing current media with shorter or othervise unsuitable media may result in\n   crashes or corrupted project data.")
    info_label = Gtk.Label(label=info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])

    path_row = guiutils.get_left_justified_box([Gtk.Label(label=media_file.path)])
    file_box = guiutils.get_named_frame(_("Media File To Replace"), path_row, 4)
    file_box.set_margin_top(24)

    replacement_path_label = Gtk.Label(label=("No Replacement Media Selected"))
    file_button = Gtk.Button(label=_("Select Replacement File"))
    file_button.selected_file = ""
    file_button.connect("clicked", lambda w: GLib.idle_add(_replace_button_clicked, w, dialog, replacement_path_label))

    select_row = guiutils.get_left_justified_box([file_button, replacement_path_label])
    select_box = guiutils.get_named_frame(_("Replacement Media"), select_row, 4)
    select_box.set_margin_top(24)


    cancel_b = guiutils.get_sized_button(_("Cancel"), 150, 32)
    cancel_b.connect("clicked", lambda w: dialogutils.dialog_destroy(dialog, None))
    replace_b = guiutils.get_sized_button(_("Replace Media"), 150, 32)
    replace_b.connect("clicked", lambda w: callback(dialog, media_file, file_button.selected_file))
    buttons_row = guiutils.get_right_justified_box([cancel_b, replace_b])
    
    pad = guiutils.get_pad_label(24, 24)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(info_box, False, False, 0)
    vbox.pack_start(file_box, False, False, 0)
    vbox.pack_start(select_box, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    vbox.pack_start(buttons_row, False, False, 0)

    guiutils.set_margins(vbox, 12, 12, 12, 12)

    dialog.add(vbox)
    #dialog.set_default_size(500, 70)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.show_all()
        
def _replace_button_clicked(button, parent, path_label):

    dialog = Gtk.FileChooserDialog( _("Select Replament Media"), parent,
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
                                    
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    ff = utilsgtk.get_media_source_file_filter()
    ff.set_name(_("Media Files"))
    dialog.add_filter(ff)
    
    data = (button, path_label)
    dialog.connect('response', _replacement_media_selected, data)
    dialog.show()

def _replacement_media_selected(dialog, response_id, data):
    res_path = dialog.get_filename()
    button, path_label = data
    if response_id == Gtk.ResponseType.ACCEPT and res_path != None:
        path_label.set_text(res_path)
        button.selected_file = res_path
    
    dialog.destroy()

def clip_length_change_dialog(callback, clip, track):
    dialog = Gtk.Dialog(_("Change Clip Length"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Ok"), Gtk.ResponseType.ACCEPT))
    
    length_changer = guicomponents.ClipLengthChanger(clip)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(length_changer.widget, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(24, 24), False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, clip, track, length_changer)
    dialog.show_all()


def new_sequence_dialog(callback, default_name):
    dialog = Gtk.Dialog(_("Create New Sequence"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Create Sequence"), Gtk.ResponseType.ACCEPT))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text(default_name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("Sequence Name:")),
                                               name_entry,
                                               250)

    tracks_select = guicomponents.TracksNumbersSelect(appconsts.INIT_V_TRACKS, appconsts.INIT_A_TRACKS)

    open_check = Gtk.CheckButton()
    open_check.set_active(True)
    open_label = Gtk.Label(label=_("Open For Editing:"))

    open_hbox = Gtk.HBox(False, 2)
    open_hbox.pack_start(Gtk.Label(), True, True, 0)
    open_hbox.pack_start(open_label, False, False, 0)
    open_hbox.pack_start(open_check, False, False, 0)

    tracks_vbox = Gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 2), False, False, 0)
    tracks_vbox.pack_start(tracks_select.widget, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)
    tracks_vbox.pack_start(open_hbox, False, False, 0)

    alignment = dialogutils.get_alignment2(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (name_entry, tracks_select, open_check))
    dialog.show_all()

def new_media_name_dialog(callback, media_file):
    dialog = Gtk.Dialog(_("Rename New Media Object"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Rename"), Gtk.ResponseType.ACCEPT))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text(media_file.name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("New Name:")),
                                               name_entry,
                                               180)

    tracks_vbox = Gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = dialogutils.get_alignment2(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    dialog.connect('response', callback, (name_entry, media_file))
    dialog.show_all()

def new_clip_name_dialog(callback, clip):
    dialog = Gtk.Dialog(_("Rename Clip"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Rename"), Gtk.ResponseType.ACCEPT))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text(clip.name)
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("New Name:")),
                                               name_entry,
                                               180)

    tracks_vbox = Gtk.VBox(False, 2)
    tracks_vbox.pack_start(name_select, False, False, 0)
    tracks_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = dialogutils.get_alignment2(tracks_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    dialog.connect('response', callback, (name_entry, clip))
    dialog.show_all()

def new_media_log_group_name_dialog(callback, next_index, add_selected):
    dialog = Gtk.Dialog(_("New Range Item Group"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Create"), Gtk.ResponseType.OK))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text(_("User Group ") + str(next_index))
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("New Group Name:")),
                                               name_entry,
                                               180)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(name_select, False, False, 0)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    dialog.connect('response', callback, (name_entry, add_selected))
    dialog.show_all()

def group_rename_dialog(callback, group_name):
    dialog, entry = dialogutils.get_single_line_text_input_dialog(30, 130,
                                                _("Rename Range Log Item Group"),
                                                _("Rename"),
                                                _("New Group Name:"),
                                                group_name)
    dialog.connect('response', callback, entry)
    dialog.show_all()

def not_valid_producer_dialog(err, parent_window):
    primary_txt = _("Can't open non-valid media")
    secondary_txt = err.value + "\n\n" + _("File: ") + err.file_path + _("\nis not a valid media file.")
    dialogutils.warning_message(primary_txt, secondary_txt, parent_window, is_info=True)

def marker_name_dialog(frame_str, callback, rename=False):
    if rename == False:
        title = _("New Marker")
        btn_text = _("Add Marker")
    else:
        title = _("Rename Marker")
        btn_text = _("Do Rename")
        
    dialog = Gtk.Dialog(title, gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (btn_text, Gtk.ResponseType.ACCEPT))

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text("")
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("Name for marker at ") + frame_str),
                                               name_entry,
                                               250)
    alignment = dialogutils.get_default_alignment(name_select)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    _default_behaviour(dialog)
    dialog.connect('response', callback, name_entry)
    dialog.show_all()

def clip_marker_name_dialog(clip_frame_str, tline_frame_str, callback, data):
    dialog = Gtk.Dialog(_("New Marker"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Add Marker"), Gtk.ResponseType.ACCEPT))

    tline_frame_info = guiutils.get_left_justified_box([Gtk.Label(label=_("Timeline position: ") + tline_frame_str),Gtk.Label()])

    name_entry = Gtk.Entry()
    name_entry.set_width_chars(30)
    name_entry.set_text("")
    name_entry.set_activates_default(True)

    name_select = panels.get_two_column_box(Gtk.Label(label=_("Name for clip marker at ") + clip_frame_str),
                                               name_entry,
                                               250)

    rows_vbox = Gtk.VBox(False, 2)
    rows_vbox.pack_start(tline_frame_info, False, False, 0)
    rows_vbox.pack_start(name_select, False, False, 0)
    #rows_vbox.pack_start(guiutils.get_pad_label(12, 2), False, False, 0)
    
    alignment = dialogutils.get_default_alignment(rows_vbox)
        
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    _default_behaviour(dialog)
    dialog.connect('response', callback, name_entry, data)
    dialog.show_all()

def alpha_info_msg(callback, filter_name):
    dialog = Gtk.Dialog(_("Alpha Filters Info"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Ok"), Gtk.ResponseType.ACCEPT))

    label_text = _("You are adding <b>Alpha Filter '") + filter_name + _("'</b> into a clip. Here is some info on how <b>Alpha Filters</b> work on Flowblade:")
    line_label = Gtk.Label(label=label_text)
    line_label.set_use_markup(True)
    row1 = guiutils.get_left_justified_box([line_label])

    label_text = _("This applies to all <b>Compositing Modes</b> other then <b>Standard Full Track</b>.")
    line_label = Gtk.Label(label=label_text)
    line_label.set_use_markup(True)
    row11 = guiutils.get_left_justified_box([line_label])
    guiutils.set_margins(row11, 12, 0, 0, 0)
    
    info_text = "\u2022" + _(" <b>Alpha Filters</b> work by modifying image's alpha channel.\n") + \
                "\u2022" + _(" To see the effect of <b>Alpha Filter</b> you need composite this clip on track below by adding a <b>Compositor like 'Blend'</b> into this clip.\n") + \
                "\u2022" + _(" <b>Alpha Filters</b> on clips on <b>Track V1</b> have no effect.")
    info_label = Gtk.Label(label=info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])

    dont_show_check = Gtk.CheckButton.new_with_label (_("Don't show this message again."))
    row2 = guiutils.get_left_justified_box([dont_show_check])

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(guiutils.pad_label(24, 12), False, False, 0)
    vbox.pack_start(info_box, False, False, 0)
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(guiutils.pad_label(24, 24), False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    
    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    _default_behaviour(dialog)
    dialog.connect('response', callback, dont_show_check)
    dialog.show_all()

def open_image_sequence_dialog(callback, parent_window):
    cancel_str = _("Cancel")
    ok_str = _("Ok")
    dialog = Gtk.Dialog(_("Add Image Sequence Clip"),
                        None,
                        None,
                        (cancel_str, Gtk.ResponseType.CANCEL,
                        ok_str, Gtk.ResponseType.YES))

    file_chooser = gtkbuilder.get_file_chooser_button(_("Select First Frame"))
    file_chooser.set_size_request(250, 25)
    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True)
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_chooser.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
    else:
        file_chooser.set_current_folder(os.path.expanduser("~") + "/")

    filt = utilsgtk.get_image_sequence_file_filter()
    file_chooser.add_filter(filt)
    row1 = guiutils.get_two_column_box(Gtk.Label(label=_("First frame:")), file_chooser, 220)

    adj = Gtk.Adjustment(value=1, lower=1, upper=250, step_increment=1)
    frames_per_image = Gtk.SpinButton(adjustment=adj, climb_rate=1.0, digits=0)
    row2 = guiutils.get_two_column_box(Gtk.Label(label=_("Frames per Source Image:")), frames_per_image, 220)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, (file_chooser, frames_per_image))
    dialog.show_all()


def export_edl_dialog(callback, parent_window, project_name):
    dialog = Gtk.FileChooserDialog(_("Export EDL"), parent_window,
                                   Gtk.FileChooserAction.SAVE,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Export"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    project_name = project_name.rstrip(".flb")
    dialog.set_current_name(project_name + ".edl")
    dialog.set_do_overwrite_confirmation(True)

    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def transition_re_render_dialog(callback, transition_data):
    dialog = Gtk.Dialog(_("Rerender Transition"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Rerender"), Gtk.ResponseType.ACCEPT))

    alignment, encodings_cb, quality_cb, encodings = panels.get_transition_re_render_panel(transition_data)
    widgets = (encodings_cb, quality_cb, encodings)
    dialog.connect('response', callback, widgets, transition_data)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.show_all()

def re_render_all_dialog(callback, rerender_list, unrenderable):
    dialog = Gtk.Dialog(_("Rerender All Transitions and Fades"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Rerender All"), Gtk.ResponseType.ACCEPT))

    alignment, encodings_cb, quality_cb, encodings = panels.get_re_render_all_panel(rerender_list, unrenderable)
    widgets = (encodings_cb, quality_cb, encodings)
    dialog.connect('response', callback, widgets, rerender_list)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.show_all()


def watermark_dialog(add_callback, remove_callback):
    dialog = Gtk.Dialog(_("Sequence Watermark"),  gui.editor_window.window,
                        Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Close"), Gtk.ResponseType.CLOSE))

    seq_label = guiutils.bold_label(_("Sequence:") + " ")
    seq_name = Gtk.Label(label=editorstate.current_sequence().name)


    file_path_label = guiutils.bold_label(_("Watermark:") + " ")

    add_button = Gtk.Button(label=_("Set Watermark File"))
    remove_button = Gtk.Button(label=_("Remove Watermark"))
    if editorstate.current_sequence().watermark_file_path == None:
        file_path_value_label = Gtk.Label(label=_("Not Set"))
        add_button.set_sensitive(True)
        remove_button.set_sensitive(False)
    else:
        file_path_value_label = Gtk.Label(label=editorstate.current_sequence().watermark_file_path)
        add_button.set_sensitive(False)
        remove_button.set_sensitive(True)

    row1 = guiutils.get_left_justified_box([seq_label, seq_name])
    row2 = guiutils.get_left_justified_box([file_path_label, file_path_value_label])
    row3 = guiutils.get_left_justified_box([Gtk.Label(), remove_button, guiutils.pad_label(8, 8), add_button])
    row3.set_size_request(470, 30)

    widgets = (add_button, remove_button, file_path_value_label)
    add_button.connect("clicked", add_callback, dialog, widgets)
    remove_button.connect("clicked", remove_callback, widgets)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(guiutils.pad_label(12, 8), False, False, 0)
    vbox.pack_start(row3, False, False, 0)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', _dialog_destroy)
    dialog.show_all()

def watermark_file_dialog(callback, parent, widgets):
    dialog = Gtk.FileChooserDialog(_("Select Watermark File"), None,
                                   Gtk.FileChooserAction.OPEN,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name("Accepted Watermark Files")
    file_filter.add_pattern("*" + ".png")
    file_filter.add_pattern("*" + ".jpeg")
    file_filter.add_pattern("*" + ".jpg")
    file_filter.add_pattern("*" + ".tga")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback, widgets)
    dialog.show()

def media_file_dialog(text, callback, multiple_select, data=None, parent=None, open_dir=None):
    if parent == None:
        parent = gui.editor_window.window

    file_select = Gtk.FileChooserDialog(text, parent, Gtk.FileChooserAction.OPEN,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    file_select.set_default_response(Gtk.ResponseType.CANCEL)
    file_select.set_select_multiple(multiple_select)

    media_filter = utilsgtk.get_media_source_file_filter()
    all_filter = Gtk.FileFilter()
    all_filter.set_name(_("All files"))
    all_filter.add_pattern("*.*")
    file_select.add_filter(media_filter)
    file_select.add_filter(all_filter)

    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True)
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_select.set_current_folder(editorpersistance.prefs.last_opened_media_dir)

    if open_dir != None:
        file_select.set_current_folder(open_dir)

    if data == None:
        file_select.connect('response', callback)
    else:
        file_select.connect('response', callback, data)

    file_select.set_modal(True)
    file_select.show()

def save_snaphot_progess(media_copy_txt, project_txt):
    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    dialog.set_title(_("Saving project snapshot"))

    dialog.media_copy_info = Gtk.Label(label=media_copy_txt)
    media_copy_row = guiutils.get_left_justified_box([dialog.media_copy_info])

    dialog.saving_project_info = Gtk.Label(label=project_txt)
    project_row = guiutils.get_left_justified_box([dialog.saving_project_info])

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(media_copy_row, False, False, 0)
    progress_vbox.pack_start(project_row, True, True, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.show_all()

    return dialog

def not_matching_media_info_dialog(project, media_file, callback):
    dialog = Gtk.Dialog(_("Loaded Media Profile Mismatch"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Keep Current Profile"), Gtk.ResponseType.REJECT,
                         _("Change To File Profile"), Gtk.ResponseType.ACCEPT))

    primary_txt = _("A video file was loaded that does not match the Project Profile!")
    secondary_txt = ""

    match_profile_index = mltprofiles.get_closest_matching_profile_index(media_file.info)
    match_profile_name =  mltprofiles.get_profile_name_for_index(match_profile_index)
    project_profile_name = project.profile.description()

    row1 = guiutils.get_two_column_box(guiutils.bold_label(_("File:")), Gtk.Label(label=media_file.name), 120)
    row2 = guiutils.get_two_column_box(guiutils.bold_label(_("File Profile:")), Gtk.Label(label=match_profile_name), 120)
    row3 = guiutils.get_two_column_box(guiutils.bold_label(_("Project Profile:")), Gtk.Label(label=project_profile_name), 120)
    row4 = guiutils.get_left_justified_box([Gtk.Label(label=_("Using a matching profile is recommended.\n\nThis message is only displayed on first media load for Project."))])

    text_panel = Gtk.VBox(False, 2)
    text_panel.pack_start(row1, False, False, 0)
    text_panel.pack_start(row2, False, False, 0)
    text_panel.pack_start(row3, False, False, 0)
    text_panel.pack_start(Gtk.Label(label=" "), False, False, 0)
    text_panel.pack_start(row4, False, False, 0)

    vbox = dialogutils.get_warning_message_dialog_panel(primary_txt, secondary_txt,
                                                        True, None, [text_panel])

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, media_file)
    dialog.show_all()
    
    
def combine_sequences_dialog(callback):
    
    if len(editorstate.PROJECT().sequences) < 2:
        primary_txt = _("Cannot import sequence!")
        secondary_txt = _("There are no other sequences in the Project.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return
    
    dialog = Gtk.Dialog(_("Import Sequence"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Import"), Gtk.ResponseType.ACCEPT))
    
    info_text = _("<b>Please note:</b>\n") + \
                "\u2022" + _(" It is recommended that you save Project before completing this operation\n") + \
                "\u2022" + _(" There is no Undo for this operation\n") + \
                "\u2022" + _(" Current Undo Stack will be destroyed\n")
    info_label = Gtk.Label(label=info_text)
    info_label.set_use_markup(True)
    info_box = guiutils.get_left_justified_box([info_label])
    
    action_select = Gtk.ComboBoxText()
    action_select.append_text(_("Append Sequence"))
    action_select.append_text(_("Insert Sequence at Playhead position"))
    action_select.set_active(0)

    seq_select = Gtk.ComboBoxText()
    selectable_seqs = []
    for seq in editorstate.PROJECT().sequences:
        if seq != editorstate.current_sequence():
            seq_select.append_text(seq.name)
            selectable_seqs.append(seq)
            
    seq_select.set_active(0)

    row1 = Gtk.HBox(False, 2)
    row1.pack_start(Gtk.Label(label=_("Action:")), False, False, 0)
    row1.pack_start(action_select, False, False, 0)
    row1.pack_start(guiutils.pad_label(12,2), False, False, 0)
    row1.pack_start(Gtk.Label(label=_("Import:")), False, False, 0)
    row1.pack_start(seq_select, False, False, 0)

    panel = Gtk.VBox(False, 2)
    panel.pack_start(info_box, False, False, 0)
    panel.pack_start(row1, False, False, 0)
    
    alignment = dialogutils.get_default_alignment(panel)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, action_select, seq_select, selectable_seqs)
    dialog.show_all()
    
def tline_audio_sync_dialog(callback, data):
    dialog = Gtk.Dialog(_("Timeline Audio Sync"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Do Audio Sync Move Edit"), Gtk.ResponseType.ACCEPT))
    
    label_text = _("<b>Audio Sync Offset</b> between clips media is ") + str(data.media_offset_frames) + _(" frames.")
    media_offsets_label = Gtk.Label(label=label_text)
    media_offsets_label.set_use_markup(True)
    label_text = _("<b>Timeline Media Offset</b> between clips is ") + str(data.clip_tline_media_offset) + _(" frames.")
    tline_offsets_label = Gtk.Label(label=label_text)
    tline_offsets_label.set_use_markup(True)
    
    action_label_text = _("To audio sync clips you need move action origin clip by ") + str(data.clip_tline_media_offset - data.media_offset_frames) + _(" frames.")
    action_label = Gtk.Label(label=action_label_text)
    
    panel_vbox = Gtk.VBox(False, 2)
    panel_vbox.pack_start(guiutils.get_left_justified_box([media_offsets_label]), False, False, 0)
    panel_vbox.pack_start(guiutils.get_left_justified_box([tline_offsets_label]), False, False, 0)

    panel_vbox.pack_start(guiutils.get_pad_label(24, 12), False, False, 0)
    panel_vbox.pack_start(guiutils.get_left_justified_box([action_label]), False, False, 0)
    panel_vbox.pack_start(guiutils.get_pad_label(24, 24), False, False, 0)

    alignment = dialogutils.get_alignment2(panel_vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, data)
    dialog.show_all()

def no_audio_dialog(track):
    dialogutils.warning_message(_("Can't put an audio clip on a video track."), 
                            _("Track ")+ utils.get_track_name(track, editorstate.current_sequence()) + _(" is a video track and can't display audio only material."),
                            gui.editor_window.window)


def confirm_compositing_mode_change(callback, new_compositing_mode):
    dialog = Gtk.Dialog(_("Confirm Compositing Mode Change"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Change Compositing Mode"), Gtk.ResponseType.ACCEPT))
    
    primary_txt = _("Changing Compositing Mode destroys current Compositors and undo stack")
    secondary_txt = _("This operation cannot be undone. Are you sure you wish to proceed?")
    warning_panel = dialogutils.get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info=False, alternative_icon=None, panels=None)

    alignment = dialogutils.get_alignment2(warning_panel)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, new_compositing_mode)
    dialog.show_all()

def set_fade_length_default_dialog(callback, current_value):
    dialog = Gtk.Dialog(_("Fades Default Lengths"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Set"), Gtk.ResponseType.ACCEPT))

    length_spin = Gtk.SpinButton.new_with_range(3, 200, 1)
    length_spin.set_value(current_value)
    
    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(Gtk.Label(label=_("Fade Buttons Fades Default Length:")), False, False, 0)
    hbox.pack_start(length_spin, False, False, 0)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(hbox, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(12, 2), False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, length_spin)
    dialog.show_all()
        
def show_no_plugins_in_monitor_dialog():
    primary_txt = _("No Monitor display available for Generators")
    secondary_txt = _("Generators with user mutable media are best handled on Timeline.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def refuse_to_empty_default_notebook_dialog():
    primary_txt = _("Cannot do the panel move!")
    secondary_txt = _("It is not possible to move the panel and make the top left notebook empty.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def active_jobs_info(active_jobs_count):
    primary_txt =  _("There are currenly ") + str(active_jobs_count) + _(" active job/s!")
    secondary_txt = _("Let active jobs complete or cancel them before closing the application.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def show_dead_compositors(number_of_dead_compositors):
    primary_txt = _("Unable to load some Compositors!")
    secondary_txt = _("MLT version 7 removed several services that were used to implement Compositors in Flowblade.\n\nYour Project had ") \
                    + str(number_of_dead_compositors) + _(" Compositor/s in it that cannot be loaded.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def no_timeline_ranges_dialog():
    primary_txt = _("Cannot log Ranges from Timelime!")
    secondary_txt = _("'Range Log' functionality is intented to log areas of interest\nin Media Items.\n\nTo save interesting positions or ranges on Timeline use\nthe 'Timeline Markers' functionality.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def add_compositor_dialog(compositors, callback):
    dialog = Gtk.Dialog(_("Add Compositor To Clip"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Add Compositor"), Gtk.ResponseType.ACCEPT))

    select_combo = Gtk.ComboBoxText()
    for comp in compositors:
        name, compositor_type = comp
        select_combo.append_text(name)
    select_combo.set_active(0)

    vbox = Gtk.VBox(False, 2)
    vbox.add(select_combo)

    alignment = dialogutils.get_default_alignment(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    _default_behaviour(dialog)
    dialog.connect('response', callback, compositors, select_combo)
    dialog.show_all()

def set_bin_grfx_default_length_dialog(bin, current_default_length, callback):
    title = _("Set Bin Graphics Default Length")
    accept_text = _("Set")
    
    label_text = _("Set graphics default length for {}:").format(bin.name)
    value_spin = Gtk.SpinButton.new_with_range(1, 15000, 1)
    value_spin.set_value(current_default_length)

    info_label = Gtk.Label(label=label_text)
    info_label.set_margin_right(4)

    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(info_label, False, False, 0)
    hbox.pack_start(value_spin, False, False, 0)

    panel = dialogutils.get_alignment2(hbox)

    dialogutils.panel_ok_cancel_dialog(title, panel, accept_text, callback, value_spin)


    