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

from gi.repository import Gtk

import appconsts
import dialogs
import dialogutils
import editorpersistance
import gui
import guiutils
import mltprofiles
# Jan-2017 - SvdB - To get the number of CPU cores
import multiprocessing

PREFERENCES_WIDTH = 730
PREFERENCES_HEIGHT = 440
PREFERENCES_LEFT = 410

select_thumbnail_dir_callback = None # app.py sets at start up
select_render_clips_dir_callback = None # app.py sets at start up

def preferences_dialog():


    dialog = Gtk.Dialog(_("Editor Preferences"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT,
                    _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))

    gen_opts_panel, gen_opts_widgets = _general_options_panel(_thumbs_select_clicked, _renders_select_clicked)
    edit_prefs_panel, edit_prefs_widgets = _edit_prefs_panel()
    view_pres_panel, view_pref_widgets = _view_prefs_panel()
    # Jan-2017 - SvdB
    performance_panel, performance_widgets = _performance_panel()

    notebook = Gtk.Notebook()
    notebook.set_size_request(PREFERENCES_WIDTH, PREFERENCES_HEIGHT)
    notebook.append_page(gen_opts_panel, Gtk.Label(label=_("General")))
    notebook.append_page(edit_prefs_panel, Gtk.Label(label=_("Editing")))
    notebook.append_page(view_pres_panel, Gtk.Label(label=_("View")))
    notebook.append_page(performance_panel, Gtk.Label(label=_("Performance")))
    guiutils.set_margins(notebook, 4, 24, 6, 0)

    dialog.connect('response', _preferences_dialog_callback, (gen_opts_widgets, edit_prefs_widgets, view_pref_widgets, performance_widgets))
    dialog.vbox.pack_start(notebook, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    # Jul-2016 - SvdB - The next line is to get rid of the message "GtkDialog mapped without a transient parent. This is discouraged."
    dialog.set_transient_for(gui.editor_window.window)
    dialog.show_all()

def _thumbs_select_clicked(widget):
    dialogs.select_thumbnail_dir(select_thumbnail_dir_callback, gui.editor_window.window, editorpersistance.prefs.thumbnail_folder, False)

def _renders_select_clicked(widget):
    dialogs.select_rendred_clips_dir(select_render_clips_dir_callback, gui.editor_window.window, editorpersistance.prefs.render_folder)

def _preferences_dialog_callback(dialog, response_id, all_widgets):
    if response_id == Gtk.ResponseType.ACCEPT:
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
    open_in_last_opened_check = Gtk.CheckButton()
    open_in_last_opened_check.set_active(prefs.open_in_last_opended_media_dir)

    open_in_last_rendered_check = Gtk.CheckButton()
    open_in_last_rendered_check.set_active(prefs.remember_last_render_dir)

    default_profile_combo = Gtk.ComboBoxText()
    profiles = mltprofiles.get_profiles()
    for profile in profiles:
        default_profile_combo.append_text(profile[0])
    default_profile_combo.set_active(mltprofiles.get_default_profile_index())

    spin_adj = Gtk.Adjustment(prefs.undos_max, editorpersistance.UNDO_STACK_MIN, editorpersistance.UNDO_STACK_MAX, 1)
    undo_max_spin = Gtk.SpinButton.new_with_range(editorpersistance.UNDO_STACK_MIN, editorpersistance.UNDO_STACK_MAX, 1)
    undo_max_spin.set_adjustment(spin_adj)
    undo_max_spin.set_numeric(True)

    folder_select = Gtk.Button(_("Select Folder")) # thumbnails
    folder_select.connect("clicked" , folder_select_clicked_cb)

    render_folder_select = Gtk.Button(_("Select Folder"))
    render_folder_select.connect("clicked" , render_folder_select_clicked_cb)

    autosave_combo = Gtk.ComboBoxText()
    AUTO_SAVE_OPTS = ((-1, _("No Autosave")),(1, _("1 min")),(2, _("2 min")),(5, _("5 min")))

    for i in range(0, len(AUTO_SAVE_OPTS)):
        time, desc = AUTO_SAVE_OPTS[i]
        autosave_combo.append_text(desc)
    autosave_combo.set_active(prefs.auto_save_delay_value_index)

    load_order_combo  = Gtk.ComboBoxText()
    load_order_combo.append_text(_("Absolute paths first, relative second"))
    load_order_combo.append_text(_("Relative paths first, absolute second"))
    load_order_combo.append_text(_("Absolute paths only"))
    load_order_combo.set_active(prefs.media_load_order)

    # Layout
    row1 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Default Profile:")), default_profile_combo, PREFERENCES_LEFT))
    row2 = _row(guiutils.get_checkbox_row_box(open_in_last_opened_check, Gtk.Label(label=_("Remember last media directory"))))
    row3 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Undo stack size:")), undo_max_spin, PREFERENCES_LEFT))
    row4 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Thumbnail folder:")), folder_select, PREFERENCES_LEFT))
    row5 = _row(guiutils.get_checkbox_row_box(open_in_last_rendered_check, Gtk.Label(label=_("Remember last render directory"))))
    row6 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Autosave for crash recovery every:")), autosave_combo, PREFERENCES_LEFT))
    row8 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Rendered Clips folder:")), render_folder_select, PREFERENCES_LEFT))
    row9 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Media look-up order on load:")), load_order_combo, PREFERENCES_LEFT))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    return vbox, (default_profile_combo, open_in_last_opened_check, open_in_last_rendered_check, undo_max_spin, load_order_combo)

def _edit_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    auto_play_in_clip_monitor = Gtk.CheckButton()
    auto_play_in_clip_monitor.set_active(prefs.auto_play_in_clip_monitor)

    auto_center_on_stop = Gtk.CheckButton()
    auto_center_on_stop.set_active(prefs.auto_center_on_play_stop)

    spin_adj = Gtk.Adjustment(prefs.default_grfx_length, 1, 15000, 1)
    gfx_length_spin = Gtk.SpinButton()
    gfx_length_spin.set_adjustment(spin_adj)
    gfx_length_spin.set_numeric(True)

    trim_exit_on_empty = Gtk.CheckButton()
    trim_exit_on_empty.set_active(prefs.empty_click_exits_trims)

    quick_enter_trim = Gtk.CheckButton()
    quick_enter_trim.set_active(prefs.quick_enter_trims)

    remember_clip_frame = Gtk.CheckButton()
    remember_clip_frame.set_active(prefs.remember_monitor_clip_frame)

    overwrite_clip_drop = Gtk.ComboBoxText()
    active = 0
    if prefs.overwrite_clip_drop == False:
        active = 1
    overwrite_clip_drop.append_text(_("Overwrite blanks"))
    overwrite_clip_drop.append_text(_("Always insert"))
    overwrite_clip_drop.set_active(active)

    cover_delete = Gtk.CheckButton()
    cover_delete.set_active(prefs.trans_cover_delete)
    
    # Jul-2016 - SvdB - For play_pause button
    play_pause_button = Gtk.CheckButton()
    # The following test is to make sure play_pause can be used for the initial value. If not found, then leave uninitialized
    if hasattr(prefs, 'play_pause'):
        play_pause_button.set_active(prefs.play_pause)    
    
    active = 0
    if prefs.mouse_scroll_action_is_zoom == False:
        active = 1
    mouse_scroll_action = Gtk.ComboBoxText()
    mouse_scroll_action.append_text(_("Zoom, Control to Scroll Horizontal"))
    mouse_scroll_action.append_text(_("Scroll Horizontal, Control to Zoom"))
    mouse_scroll_action.set_active(active)

    hide_file_ext_button = Gtk.CheckButton()
    if hasattr(prefs, 'hide_file_ext'):
        hide_file_ext_button.set_active(prefs.hide_file_ext)

    # Layout
    row1 = _row(guiutils.get_checkbox_row_box(auto_play_in_clip_monitor, Gtk.Label(label=_("Autoplay new Clips in Clip Monitor"))))
    row2 = _row(guiutils.get_checkbox_row_box(auto_center_on_stop, Gtk.Label(label=_("Center Current Frame on Playback Stop"))))
    row4 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Graphics default length:")), gfx_length_spin, PREFERENCES_LEFT))
    row5 = _row(guiutils.get_checkbox_row_box(trim_exit_on_empty, Gtk.Label(label=_("Trim Modes exit on empty click"))))
    row6 = _row(guiutils.get_checkbox_row_box(quick_enter_trim, Gtk.Label(label=_("Quick enter Trim Modes"))))
    row7 = _row(guiutils.get_checkbox_row_box(remember_clip_frame, Gtk.Label(label=_("Remember Monitor Clip Frame"))))
    row8 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Media drag'n'drop action on non-V1 tracks")), overwrite_clip_drop, PREFERENCES_LEFT))
    row9 = _row(guiutils.get_checkbox_row_box(cover_delete, Gtk.Label(label=_("Cover Transition/Fade clips on delete if possible"))))
    # Jul-2016 - SvdB - For play_pause button
    row10 = _row(guiutils.get_checkbox_row_box(play_pause_button, Gtk.Label(label=_("Enable single Play/Pause button"))))
    row11 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Mouse Middle Button Scroll Action")), mouse_scroll_action, PREFERENCES_LEFT))
    row12 = _row(guiutils.get_checkbox_row_box(hide_file_ext_button, Gtk.Label(label=_("Hide file extensions when importing Clips"))))
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    # Jul-2016 - SvdB - For play_pause button
    vbox.pack_start(row10, False, False, 0)
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(row12, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    # Jul-2016 - SvdB - Added play_pause_button
    return vbox, (auto_play_in_clip_monitor, auto_center_on_stop, gfx_length_spin,
                  trim_exit_on_empty, quick_enter_trim, remember_clip_frame, overwrite_clip_drop, cover_delete,
                  play_pause_button, mouse_scroll_action, hide_file_ext_button)

def _view_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    force_english_check = Gtk.CheckButton()
    force_english_check.set_active(prefs.use_english_always)

    display_splash_check = Gtk.CheckButton()
    display_splash_check.set_active(prefs.display_splash_screen)

    buttons_combo = Gtk.ComboBoxText()
    buttons_combo.append_text(_("Glass"))
    buttons_combo.append_text(_("Simple"))
    if prefs.buttons_style == editorpersistance.GLASS_STYLE:
        buttons_combo.set_active(0)
    else:
        buttons_combo.set_active(1)

    dark_combo = Gtk.ComboBoxText()
    dark_combo.append_text(_("Light Theme"))
    dark_combo.append_text(_("Dark Theme"))
    if prefs.dark_theme == True:
        dark_combo.set_active(1)
    else:
        dark_combo.set_active(0)

    theme_combo = Gtk.ComboBoxText()
    for theme in gui._THEME_COLORS:
        theme_combo.append_text(theme[4])
    theme_combo.set_active(prefs.theme_fallback_colors)

    audio_levels_combo = Gtk.ComboBoxText()
    audio_levels_combo.append_text(_("Display All Levels"))
    audio_levels_combo.append_text(_("Display Levels On Request"))
    if prefs.display_all_audio_levels == True:
        audio_levels_combo.set_active(0)
    else:
        audio_levels_combo.set_active(1)

    window_mode_combo = Gtk.ComboBoxText()
    window_mode_combo.append_text(_("Single Window"))
    window_mode_combo.append_text(_("Two Windows"))
    if prefs.global_layout == appconsts.SINGLE_WINDOW:
        window_mode_combo.set_active(0)
    else:
        window_mode_combo.set_active(1)
        
    # Layout
    row00 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Application window mode:")), window_mode_combo, PREFERENCES_LEFT))
    row0 =  _row(guiutils.get_checkbox_row_box(force_english_check, Gtk.Label(label=_("Use English texts on localized OS"))))
    row1 =  _row(guiutils.get_checkbox_row_box(display_splash_check, Gtk.Label(label=_("Display splash screen"))))
    row2 =  _row(guiutils.get_two_column_box(Gtk.Label(label=_("Buttons style:")), buttons_combo, PREFERENCES_LEFT))
    row3 =  _row(guiutils.get_two_column_box(Gtk.Label(label=_("Theme request, icons and colors:")), dark_combo, PREFERENCES_LEFT))
    row4 =  _row(guiutils.get_two_column_box(Gtk.Label(label=_("Theme detection fail fallback colors:")), theme_combo, PREFERENCES_LEFT))
    row5 =  _row(guiutils.get_two_column_box(Gtk.Label(label=_("Default audio levels display:")), audio_levels_combo, PREFERENCES_LEFT))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row00, False, False, 0)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    return vbox, (force_english_check, display_splash_check, buttons_combo, dark_combo, theme_combo, audio_levels_combo, window_mode_combo)

def _performance_panel():
    # Jan-2017 - SvdB
    # Add a panel for performance settings. The first setting is allowing multiple threads to render
    # the files. This is used for the real_time parameter to mlt in renderconsumer.py.
    # The effect depends on the computer running the program.
    # Max. number of threads is set to number of CPU cores. Default is 1.
    # Allow Frame Dropping should help getting real time output on low performance computers.
    prefs = editorpersistance.prefs

    # Widgets
    spin_adj = Gtk.Adjustment(prefs.perf_render_threads, 1, multiprocessing.cpu_count(), 1)
    perf_render_threads = Gtk.SpinButton()
    perf_render_threads.set_adjustment(spin_adj)
    perf_render_threads.set_numeric(True)

    perf_drop_frames = Gtk.CheckButton()
    perf_drop_frames.set_active(prefs.perf_drop_frames)

    # Tooltips
    perf_render_threads.set_tooltip_text(_("Between 1 and the number of CPU Cores"))
    perf_drop_frames.set_tooltip_text(_("Allow Frame Dropping for real-time rendering, when needed"))

    # Layout
    row1 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Render Threads:")), perf_render_threads, PREFERENCES_LEFT))
    row2 = _row(guiutils.get_checkbox_row_box(perf_drop_frames, Gtk.Label(label=_("Allow Frame Dropping"))))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    return vbox, (perf_render_threads, perf_drop_frames)

def _row(row_cont):
    row_cont.set_size_request(10, 26)
    return row_cont
