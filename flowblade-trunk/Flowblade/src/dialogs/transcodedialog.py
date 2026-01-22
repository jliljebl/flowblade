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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""


from gi.repository import Gtk, GLib

import dialogutils
import editorstate
import guiutils
import ingest

def show_transcode_dialog(media_items):


    dialog = Gtk.Dialog(_("Transcode Media"), None,
                        None,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Transcode"), Gtk.ResponseType.ACCEPT))

    #info_label = guiutils.bold_label(_("Project Profile can only be changed by saving a version\nwith different profile."))
    """
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
    """

    vbox = guiutils.get_vbox([Gtk.Label()], False)

    alignment = dialogutils.get_default_alignment(vbox)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_resizable(False)
    dialog.connect('response', _resposnse_callback, media_items)
    
    dialog.show_all()

def _resposnse_callback(dialog, response_id, media_items):
    dialog.destroy()
    