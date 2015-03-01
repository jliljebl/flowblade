"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2013 Janne Liljeblad.

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

import pygtk
pygtk.require('2.0');
import gtk


import dialogs
import dialogutils
import editorpersistance
import gui
import guiutils
import mltprofiles

PREFERENCES_WIDTH = 730
PREFERENCES_HEIGHT = 300
PREFERENCES_LEFT = 410

select_thumbnail_dir_callback = None # app.py sets at start up
select_render_clips_dir_callback = None # app.py sets at start up

def preferences_dialog():

    #global select_thumbnail_dir_callback, select_render_clips_dir_callback
    #select_thumbnail_dir_callback = select_thumbnail_cb
    #select_render_clips_dir_callback = select_render_clips_cb

    dialog = gtk.Dialog(_("Editor Preferences"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT))
    
    gen_opts_panel, gen_opts_widgets = _general_options_panel(_thumbs_select_clicked, _renders_select_clicked)
    edit_prefs_panel, edit_prefs_widgets = _edit_prefs_panel()
    view_pres_panel, view_pref_widgets = _view_prefs_panel()

    notebook = gtk.Notebook()
    notebook.set_size_request(PREFERENCES_WIDTH, PREFERENCES_HEIGHT)

    notebook.append_page(gen_opts_panel, gtk.Label(_("General")))
    notebook.append_page(edit_prefs_panel, gtk.Label(_("Editing")))
    notebook.append_page(view_pres_panel, gtk.Label(_("View")))

    dialog.connect('response', _preferences_dialog_callback, (gen_opts_widgets, edit_prefs_widgets, view_pref_widgets))
    dialog.vbox.pack_start(notebook, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()

def _thumbs_select_clicked(widget):
    dialogs.select_thumbnail_dir(select_thumbnail_dir_callback, gui.editor_window.window, editorpersistance.prefs.thumbnail_folder, False)

def _renders_select_clicked(widget):
    dialogs.select_rendred_clips_dir(select_render_clips_dir_callback, gui.editor_window.window, editorpersistance.prefs.render_folder)

def _preferences_dialog_callback(dialog, response_id, all_widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        editorpersistance.update_prefs_from_widgets(all_widgets)
        editorpersistance.save()
        dialog.destroy()
        primary_txt = _("Restart required for some setting changes to take effect.")
        secondary_txt = _("If requested change is not in effect, restart application.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    dialog.destroy()
    
def _general_options_panel(folder_select_clicked_cb, render_folder_select_clicked_cb):
    prefs = editorpersistance.prefs

    # Widgets
    open_in_last_opened_check = gtk.CheckButton()
    open_in_last_opened_check.set_active(prefs.open_in_last_opended_media_dir)

    open_in_last_rendered_check = gtk.CheckButton()
    open_in_last_rendered_check.set_active(prefs.remember_last_render_dir)

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

    autosave_combo = gtk.combo_box_new_text()
    for i in range(0, len(editorpersistance.prefs.AUTO_SAVE_OPTS)):
        time, desc = editorpersistance.prefs.AUTO_SAVE_OPTS[i]
        autosave_combo.append_text(desc)
    autosave_combo.set_active(prefs.auto_save_delay_value_index)

    load_order_combo  = gtk.combo_box_new_text()
    load_order_combo.append_text("Absolute paths first, relative second")
    load_order_combo.append_text("Relative paths first, absolute second")
    load_order_combo.append_text("Absolute paths only")
    load_order_combo.set_active(prefs.media_load_order)

    # Layout
    row1 = guiutils.get_two_column_box(gtk.Label(_("Default Profile:")), default_profile_combo, PREFERENCES_LEFT)
    row2 = guiutils.get_checkbox_row_box(open_in_last_opened_check, gtk.Label(_("Remember last media directory")))
    row3 = guiutils.get_two_column_box(gtk.Label(_("Undo stack size:")), undo_max_spin, PREFERENCES_LEFT)
    row4 = guiutils.get_two_column_box(gtk.Label(_("Thumbnail folder:")), folder_select, PREFERENCES_LEFT)
    row5 = guiutils.get_checkbox_row_box(open_in_last_rendered_check, gtk.Label(_("Remember last render directory")))
    row6 = guiutils.get_two_column_box(gtk.Label(_("Autosave for crash recovery every:")), autosave_combo, PREFERENCES_LEFT)
    row8 = guiutils.get_two_column_box(gtk.Label(_("Rendered Clips folder:")), render_folder_select, PREFERENCES_LEFT)
    row9 = guiutils.get_two_column_box(gtk.Label(_("Media look-up order on load:")), load_order_combo, PREFERENCES_LEFT)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (default_profile_combo, open_in_last_opened_check, open_in_last_rendered_check, undo_max_spin, load_order_combo)

def _edit_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    auto_play_in_clip_monitor = gtk.CheckButton()
    auto_play_in_clip_monitor.set_active(prefs.auto_play_in_clip_monitor)

    auto_center_on_stop = gtk.CheckButton()
    auto_center_on_stop.set_active(prefs.auto_center_on_play_stop)

    spin_adj = gtk.Adjustment(prefs.default_grfx_length, 1, 15000, 1)
    gfx_length_spin = gtk.SpinButton(spin_adj)
    gfx_length_spin.set_numeric(True)

    trim_exit_on_empty = gtk.CheckButton()
    trim_exit_on_empty.set_active(prefs.empty_click_exits_trims)

    quick_enter_trim = gtk.CheckButton()
    quick_enter_trim.set_active(prefs.quick_enter_trims)

    remember_clip_frame = gtk.CheckButton()
    remember_clip_frame.set_active(prefs.remember_monitor_clip_frame)

    # Layout
    row1 = guiutils.get_checkbox_row_box(auto_play_in_clip_monitor, gtk.Label(_("Autoplay new Clips in Clip Monitor")))
    row2 = guiutils.get_checkbox_row_box(auto_center_on_stop, gtk.Label(_("Center Current Frame on Playback Stop")))
    row4 = guiutils.get_two_column_box(gtk.Label(_("Graphics default length:")), gfx_length_spin, PREFERENCES_LEFT)
    row5 = guiutils.get_checkbox_row_box(trim_exit_on_empty, gtk.Label(_("Trim Modes exit on empty click")))
    row6 = guiutils.get_checkbox_row_box(quick_enter_trim, gtk.Label(_("Quick enter Trim Modes")))
    row7 = guiutils.get_checkbox_row_box(remember_clip_frame, gtk.Label(_("Remember Monitor Clip Frame")))
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (auto_play_in_clip_monitor, auto_center_on_stop, gfx_length_spin, trim_exit_on_empty, quick_enter_trim, remember_clip_frame)
    
def _view_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    display_splash_check = gtk.CheckButton()
    display_splash_check.set_active(prefs.display_splash_screen)

    buttons_combo = gtk.combo_box_new_text()
    buttons_combo.append_text(_("Glass"))
    buttons_combo.append_text(_("Simple"))
    if prefs.buttons_style == editorpersistance.GLASS_STYLE:
        buttons_combo.set_active(0)
    else:
        buttons_combo.set_active(1)

    dark_combo = gtk.combo_box_new_text()
    dark_combo.append_text(_("Light Theme"))
    dark_combo.append_text(_("Dark Theme"))
    if prefs.dark_theme == True:
        dark_combo.set_active(1)
    else:
        dark_combo.set_active(0)
        
    # Layout
    row1 = guiutils.get_checkbox_row_box(display_splash_check, gtk.Label(_("Display splash screen")))
    row2 = guiutils.get_two_column_box(gtk.Label(_("Buttons style:")), buttons_combo, PREFERENCES_LEFT)
    row3 = guiutils.get_two_column_box(gtk.Label(_("Icons and color optimized for:")), dark_combo, PREFERENCES_LEFT)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)

    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    return align, (display_splash_check, buttons_combo, dark_combo)
    
