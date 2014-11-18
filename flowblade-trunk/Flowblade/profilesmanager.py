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
This module handles functionality presented in Profiles Manager window.
"""
import pygtk
pygtk.require('2.0');
import gtk

import os

import dialogutils
import editorpersistance
import gui
import guicomponents
import guiutils
import mltprofiles
import render
import respaths
import utils

PROFILES_WIDTH = 480
PROFILES_HEIGHT = 690
PROFILE_MANAGER_LEFT = 265 # label column of profile manager panel

def profiles_manager_dialog():
    dialog = gtk.Dialog(_("Profiles Manager"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))
    

    panel2, user_profiles_view = _get_user_profiles_panel()
    alignment2 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment2.set_padding(12, 14, 12, 6)
    alignment2.add(panel2)

    panel1 = _get_factory_profiles_panel(user_profiles_view)
    alignment1 = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment1.set_padding(12, 12, 12, 12)
    alignment1.add(panel1)

    pane = gtk.HBox(True, 2)
    pane.pack_start(alignment1, True, True, 0)
    pane.pack_start(alignment2, True, True, 0)
    pane.set_size_request(PROFILES_WIDTH * 2, PROFILES_HEIGHT)
    pane.show_all()
    dialog.connect('response', dialogutils.dialog_destroy)
    
    dialog.vbox.pack_start(pane, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()
    return dialog

def _get_user_profiles_panel():
    # User profiles view
    user_profiles_list = guicomponents.ProfileListView()
    user_profiles_list.fill_data_model(mltprofiles.get_user_profiles())    
    delete_selected_button = gtk.Button(_("Delete Selected"))
    
    user_vbox = gtk.VBox(False, 2)
    user_vbox.pack_start(user_profiles_list, True, True, 0)
    user_vbox.pack_start(guiutils.get_right_justified_box([delete_selected_button]), False, False, 0)

    # Create profile panel
    default_profile_index = mltprofiles.get_default_profile_index()
    default_profile = mltprofiles.get_default_profile()

    load_profile_button = gtk.Button(_("Load Profile Values"))

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
    _fill_new_profile_panel_widgets(default_profile, widgets)
    
    # build panel
    profile_row = gtk.HBox(False,0)
    profile_row.pack_start(load_profile_combo, False, False, 0)
    profile_row.pack_start(gtk.Label(), True, True, 0)
    profile_row.pack_start(load_profile_button, False, False, 0)

    row0 = guiutils.get_two_column_box(gtk.Label(_("Description.:")), description, PROFILE_MANAGER_LEFT)
    row1 = guiutils.get_two_column_box(gtk.Label(_("Frame rate num.:")), f_rate_num, PROFILE_MANAGER_LEFT)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Frame rate den.:")), f_rate_dem, PROFILE_MANAGER_LEFT)
    row3 = guiutils.get_two_column_box(gtk.Label(_("Width:")), width, PROFILE_MANAGER_LEFT)
    row4 = guiutils.get_two_column_box(gtk.Label(_("Height:")), height, PROFILE_MANAGER_LEFT)
    row5 = guiutils.get_two_column_box(gtk.Label(_("Sample aspect num.:")), s_rate_num, PROFILE_MANAGER_LEFT)
    row6 = guiutils.get_two_column_box(gtk.Label(_("Sample aspect den.:")), s_rate_dem, PROFILE_MANAGER_LEFT)
    row7 = guiutils.get_two_column_box(gtk.Label(_("Display aspect num.:")), d_rate_num, PROFILE_MANAGER_LEFT)
    row8 = guiutils.get_two_column_box(gtk.Label(_("Display aspect den.:")), d_rate_dem, PROFILE_MANAGER_LEFT)
    row9 = guiutils.get_two_column_box(gtk.Label(_("Progressive:")), progressive, PROFILE_MANAGER_LEFT)

    save_row = gtk.HBox(False,0)
    save_row.pack_start(gtk.Label(), True, True, 0)
    save_row.pack_start(save_button, False, False, 0)
    
    create_vbox = gtk.VBox(False, 2)
    create_vbox.pack_start(profile_row, False, False, 0)
    create_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    create_vbox.pack_start(row0, False, False, 0)
    create_vbox.pack_start(row1, False, False, 0)
    create_vbox.pack_start(row2, False, False, 0)
    create_vbox.pack_start(row3, False, False, 0)
    create_vbox.pack_start(row4, False, False, 0)
    create_vbox.pack_start(row5, False, False, 0)
    create_vbox.pack_start(row6, False, False, 0)
    create_vbox.pack_start(row7, False, False, 0)
    create_vbox.pack_start(row8, False, False, 0)
    create_vbox.pack_start(row9, False, False, 0)
    create_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    create_vbox.pack_start(save_row, False, False, 0)

    # callbacks
    load_profile_button.connect("clicked",lambda w,e: _load_values_clicked(widgets), None)
    save_button.connect("clicked",lambda w,e: _save_profile_clicked(widgets, user_profiles_list), None)
    delete_selected_button.connect("clicked",lambda w,e: _delete_user_profiles_clicked(user_profiles_list), None)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(guiutils.get_named_frame(_("Create User Profile"), create_vbox), False, False, 0)
    vbox.pack_start(guiutils.get_named_frame(_("User Profiles"), user_vbox), True, True, 0)

    return (vbox, user_profiles_list)


def _get_factory_profiles_panel(user_profiles_list):

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
    hide_selected_button.connect("clicked",lambda w,e: _hide_selected_clicked(all_profiles_list, hidden_profiles_list), None)
    unhide_selected_button.connect("clicked",lambda w,e: _unhide_selected_clicked(all_profiles_list, hidden_profiles_list), None)    

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

    vbox = gtk.VBox(True, 2)
    vbox.pack_start(guiutils.get_named_frame(_("Factory Profiles"), factory_vbox), True, True, 0)
    
    return vbox

def _fill_new_profile_panel_widgets(profile, widgets):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets
    description.set_text(_("User ") + profile.description())
    f_rate_num.set_text(str(profile.frame_rate_num()))
    f_rate_dem.set_text(str(profile.frame_rate_den()))
    width.set_text(str(profile.width()))
    height.set_text(str(profile.height()))
    s_rate_num.set_text(str(profile.sample_aspect_num()))
    s_rate_dem.set_text(str(profile.sample_aspect_den()))
    d_rate_num.set_text(str(profile.display_aspect_num()))
    d_rate_dem.set_text(str(profile.display_aspect_den()))
    progressive.set_active(profile.progressive())
    
def _load_values_clicked(widgets):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, \
    s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets
    
    profile = mltprofiles.get_profile_for_index(load_profile_combo.get_active())
    _fill_new_profile_panel_widgets(profile, widgets)

def _save_profile_clicked(widgets, user_profiles_view):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, \
    s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets

    profile_file_name = description.get_text().lower().replace(os.sep, "_").replace(" ","_")
    
    file_contents = "description=" + description.get_text() + "\n"
    file_contents += "frame_rate_num=" + f_rate_num.get_text() + "\n"
    file_contents += "frame_rate_den=" + f_rate_dem.get_text() + "\n"
    file_contents += "width=" + width.get_text() + "\n"
    file_contents += "height=" + height.get_text() + "\n"
    if progressive.get_active() == True:
        prog_val = "1"
    else:
        prog_val = "0"
    file_contents += "progressive=" + prog_val + "\n"
    file_contents += "sample_aspect_num=" + s_rate_num.get_text() + "\n"
    file_contents += "sample_aspect_den=" + s_rate_dem.get_text() + "\n"
    file_contents += "display_aspect_num=" + d_rate_num.get_text() + "\n"
    file_contents += "display_aspect_den=" + d_rate_dem.get_text() + "\n"

    profile_path = utils.get_hidden_user_dir_path() + mltprofiles.USER_PROFILES_DIR + profile_file_name

    if os.path.exists(profile_path):
        dialogutils.warning_message(_("Profile '") +  description.get_text() + _("' already exists!"), \
                                _("Delete profile and save again."),  gui.editor_window.window)
        return

    profile_file = open(profile_path, "w")
    profile_file.write(file_contents)
    profile_file.close()

    dialogutils.info_message(_("Profile '") +  description.get_text() + _("' saved."), \
                 _("You can now create a new project using the new profile."), gui.editor_window.window)
    
    mltprofiles.load_profile_list()
    render.reload_profiles()
    user_profiles_view.fill_data_model(mltprofiles.get_user_profiles())


def _delete_user_profiles_clicked(user_profiles_view):
    delete_indexes = user_profiles_view.get_selected_indexes_list()
    if len(delete_indexes) == 0:
        return

    primary_txt = _("Confirm user profile delete")
    secondary_txt = _("This operation cannot be undone.") 
    
    dialogutils.warning_confirmation(_profiles_delete_confirm_callback, primary_txt, \
                                 secondary_txt, gui.editor_window.window, \
                                (user_profiles_view, delete_indexes))

def _profiles_delete_confirm_callback(dialog, response_id, data):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return

    user_profiles_view, delete_indexes = data
    for i in delete_indexes:
        pname, profile = mltprofiles.get_user_profiles()[i]
        profile_file_name = pname.lower().replace(os.sep, "_").replace(" ","_")
        profile_path = utils.get_hidden_user_dir_path() + mltprofiles.USER_PROFILES_DIR + profile_file_name
        print profile_path
        try:
            os.remove(profile_path)
        except:
            # This really should not happen
            print "removed user profile already gone ???"

    mltprofiles.load_profile_list()
    user_profiles_view.fill_data_model(mltprofiles.get_user_profiles())
    dialog.destroy()

def _hide_selected_clicked(visible_view, hidden_view):
    visible_indexes = visible_view.get_selected_indexes_list()
    prof_names = []
    default_profile = mltprofiles.get_default_profile()
    for i in visible_indexes:
        pname, profile = mltprofiles.get_factory_profiles()[i]
        if profile == default_profile:
            dialogutils.warning_message("Can't hide default Profile", 
                                    "Profile '"+ profile.description() + "' is default profile and can't be hidden.", 
                                    None)
            return
        prof_names.append(pname)

    editorpersistance.prefs.hidden_profile_names += prof_names
    editorpersistance.save()

    mltprofiles.load_profile_list()
    visible_view.fill_data_model(mltprofiles.get_factory_profiles())
    hidden_view.fill_data_model(mltprofiles.get_hidden_profiles())

def _unhide_selected_clicked(visible_view, hidden_view):
    hidden_indexes = hidden_view.get_selected_indexes_list()
    prof_names = []
    for i in hidden_indexes:
        pname, profile = mltprofiles.get_hidden_profiles()[i]
        prof_names.append(pname)
    
    editorpersistance.prefs.hidden_profile_names = list(set(editorpersistance.prefs.hidden_profile_names) - set(prof_names))
    editorpersistance.save()
    
    mltprofiles.load_profile_list()
    visible_view.fill_data_model(mltprofiles.get_factory_profiles())
    hidden_view.fill_data_model(mltprofiles.get_hidden_profiles())
