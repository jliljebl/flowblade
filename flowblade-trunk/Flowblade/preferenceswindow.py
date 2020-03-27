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

import os

from gi.repository import Gtk

import appconsts
import dialogs
import dialogutils
import editorpersistance
import gui
import guiutils
import mltprofiles
import multiprocessing
import utils

PREFERENCES_WIDTH = 730
PREFERENCES_HEIGHT = 440
PREFERENCES_LEFT = 410

def preferences_dialog():


    dialog = Gtk.Dialog(_("Editor Preferences"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Cancel"), Gtk.ResponseType.REJECT,
                    _("OK"), Gtk.ResponseType.ACCEPT))

    gen_opts_panel, gen_opts_widgets = _general_options_panel()
    edit_prefs_panel, edit_prefs_widgets = _edit_prefs_panel()
    playback_prefs_panel, playback_prefs_widgets  = _playback_prefs_panel()
    view_pres_panel, view_pref_widgets = _view_prefs_panel()
    # Jan-2017 - SvdB
    performance_panel, performance_widgets = _performance_panel()
    # Apr-2017 - SvdB
    #shortcuts_panel, shortcuts_widgets = _shortcuts_panel()

    notebook = Gtk.Notebook()
    notebook.set_size_request(PREFERENCES_WIDTH, PREFERENCES_HEIGHT)
    notebook.append_page(gen_opts_panel, Gtk.Label(label=_("General")))
    notebook.append_page(edit_prefs_panel, Gtk.Label(label=_("Editing")))
    notebook.append_page(playback_prefs_panel, Gtk.Label(label=_("Playback")))
    notebook.append_page(view_pres_panel, Gtk.Label(label=_("View")))
    notebook.append_page(performance_panel, Gtk.Label(label=_("Performance")))
    guiutils.set_margins(notebook, 4, 24, 6, 0)

    dialog.connect('response', _preferences_dialog_callback, (gen_opts_widgets, edit_prefs_widgets, playback_prefs_widgets, view_pref_widgets, \
        performance_widgets))
    dialog.vbox.pack_start(notebook, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    # Jul-2016 - SvdB - The next line is to get rid of the message "GtkDialog mapped without a transient parent. This is discouraged."
    dialog.set_transient_for(gui.editor_window.window)
    dialog.show_all()

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

def _general_options_panel():
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
    spin_adj = Gtk.Adjustment(value=prefs.undos_max, lower=editorpersistance.UNDO_STACK_MIN, upper=editorpersistance.UNDO_STACK_MAX, step_incr=1)
    undo_max_spin = Gtk.SpinButton.new_with_range(editorpersistance.UNDO_STACK_MIN, editorpersistance.UNDO_STACK_MAX, 1)
    undo_max_spin.set_adjustment(spin_adj)
    undo_max_spin.set_numeric(True)

    autosave_combo = Gtk.ComboBoxText()
    # Aug-2019 - SvdB - AS - This is now initialized in app.main
    # Using editorpersistance.prefs.AUTO_SAVE_OPTS as source
    # AUTO_SAVE_OPTS = ((-1, _("No Autosave")),(1, _("1 min")),(2, _("2 min")),(5, _("5 min")))

    for i in range(0, len(editorpersistance.prefs.AUTO_SAVE_OPTS)):
        time, desc = editorpersistance.prefs.AUTO_SAVE_OPTS[i]
        autosave_combo.append_text(desc)
    autosave_combo.set_active(prefs.auto_save_delay_value_index)

    load_order_combo  = Gtk.ComboBoxText()
    load_order_combo.append_text(_("Absolute paths first, relative second"))
    load_order_combo.append_text(_("Relative paths first, absolute second"))
    load_order_combo.append_text(_("Absolute paths only"))
    load_order_combo.set_active(prefs.media_load_order)

    render_folder_select = Gtk.FileChooserButton.new (_("Select Default Render Folder"), Gtk.FileChooserAction.SELECT_FOLDER)
    if prefs.default_render_directory == None or prefs.default_render_directory == appconsts.USER_HOME_DIR \
        or (not os.path.exists(prefs.default_render_directory)) \
        or (not os.path.isdir(prefs.default_render_directory)):
        render_folder_select.set_current_folder_uri(os.path.expanduser("~") + "/")
    else:
        render_folder_select.set_current_folder_uri(prefs.default_render_directory)

    disk_cache_warning_combo  = Gtk.ComboBoxText()
    disk_cache_warning_combo.append_text(_("Off"))
    disk_cache_warning_combo.append_text(_("500 MB"))
    disk_cache_warning_combo.append_text(_("1 GB"))
    disk_cache_warning_combo.append_text(_("2 GB"))
    disk_cache_warning_combo.set_active(prefs.disk_space_warning)
    
    # Layout
    row1 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Default Profile:")), default_profile_combo, PREFERENCES_LEFT))
    row2 = _row(guiutils.get_checkbox_row_box(open_in_last_opened_check, Gtk.Label(label=_("Remember last media directory"))))
    row3 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Undo stack size:")), undo_max_spin, PREFERENCES_LEFT))
    row5 = _row(guiutils.get_checkbox_row_box(open_in_last_rendered_check, Gtk.Label(label=_("Remember last render directory"))))
    row6 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Autosave for crash recovery every:")), autosave_combo, PREFERENCES_LEFT))
    row9 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Media look-up order on load:")), load_order_combo, PREFERENCES_LEFT))
    row10 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Default render directory:")), render_folder_select, PREFERENCES_LEFT))
    row11 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Warning on Disk Cache Size:")), disk_cache_warning_combo, PREFERENCES_LEFT))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row10, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    # Aug-2019 - SvdB - AS - Added autosave_combo
    return vbox, ( default_profile_combo, open_in_last_opened_check, open_in_last_rendered_check,
                    undo_max_spin, load_order_combo, autosave_combo, render_folder_select, disk_cache_warning_combo)

def _edit_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    spin_adj = Gtk.Adjustment(value=prefs.default_grfx_length, lower=1, upper=15000, step_incr=1)
    gfx_length_spin = Gtk.SpinButton()
    gfx_length_spin.set_adjustment(spin_adj)
    gfx_length_spin.set_numeric(True)

    cover_delete = Gtk.CheckButton()
    cover_delete.set_active(prefs.trans_cover_delete)

    active = 0
    if prefs.mouse_scroll_action_is_zoom == False:
        active = 1
    mouse_scroll_action = Gtk.ComboBoxText()
    mouse_scroll_action.append_text(_("Zoom, Control to Scroll Horizontal"))
    mouse_scroll_action.append_text(_("Scroll Horizontal, Control to Zoom"))
    mouse_scroll_action.set_active(active)

    active = 0
    if prefs.scroll_horizontal_dir_up_forward == False:
        active = 1
    hor_scroll_dir = Gtk.ComboBoxText()
    hor_scroll_dir.append_text(_("Scroll Up Forward"))
    hor_scroll_dir.append_text(_("Scroll Down Forward"))
    hor_scroll_dir.set_active(active)

    active = 0
    if prefs.single_click_effects_editor_load == True:
        active = 1
    effects_editor_clip_load = Gtk.ComboBoxText()
    effects_editor_clip_load.append_text(_("On Double Click"))
    effects_editor_clip_load.append_text(_("On Single Click"))
    effects_editor_clip_load.set_active(active)

    hide_file_ext_button = Gtk.CheckButton()
    if hasattr(prefs, 'hide_file_ext'):
        hide_file_ext_button.set_active(prefs.hide_file_ext)

    # Layout
    row4 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Graphics default length:")), gfx_length_spin, PREFERENCES_LEFT))
    row9 = _row(guiutils.get_checkbox_row_box(cover_delete, Gtk.Label(label=_("Cover Transition/Fade clips on delete if possible"))))
    # Jul-2016 - SvdB - For play_pause button
    row11 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Mouse Middle Button Scroll Action:")), mouse_scroll_action, PREFERENCES_LEFT))
    row13 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Mouse Horizontal Scroll Direction:")), hor_scroll_dir, PREFERENCES_LEFT))
    row12 = _row(guiutils.get_checkbox_row_box(hide_file_ext_button, Gtk.Label(label=_("Hide file extensions when importing Clips"))))
    row15 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Open Clip in Effects Editor")), effects_editor_clip_load, PREFERENCES_LEFT))
    # Apr-2017 - SvdB - For Fast Forward / Reverse options

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(row11, False, False, 0)
    vbox.pack_start(row13, False, False, 0)
    vbox.pack_start(row12, False, False, 0)
    vbox.pack_start(row15, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    # Jul-2016 - SvdB - Added play_pause_button
    # Apr-2017 - SvdB - Added ffwd / rev values
    return vbox, (gfx_length_spin, cover_delete,
                  mouse_scroll_action, hide_file_ext_button, hor_scroll_dir,
                  effects_editor_clip_load)

def _playback_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    auto_center_on_stop = Gtk.CheckButton()
    auto_center_on_stop.set_active(prefs.auto_center_on_play_stop)

    # Jul-2016 - SvdB - For play_pause button
    play_pause_button = Gtk.CheckButton()
    # The following test is to make sure play_pause can be used for the initial value. If not found, then leave uninitialized
    if hasattr(prefs, 'play_pause'):
        play_pause_button.set_active(prefs.play_pause)

# ------------------------------ timeline_start_end_button
    timeline_start_end_button = Gtk.CheckButton()
    if hasattr(prefs, 'timeline_start_end'):
        timeline_start_end_button.set_active(prefs.timeline_start_end)
# ------------------------------ End of timeline_start_end_button

    auto_center_on_updown = Gtk.CheckButton()
    auto_center_on_updown.set_active(prefs.center_on_arrow_move)

    follow_move_range = Gtk.CheckButton()
    follow_move_range.set_active(prefs.playback_follow_move_tline_range)

    # Apr-2017 - SvdB - For FF/Rev speed options
    if hasattr(prefs, 'ffwd_rev_shift'):
        spin_adj = Gtk.Adjustment(value=prefs.ffwd_rev_shift, lower=1, upper=10, step_incr=1)
    else:
        spin_adj = Gtk.Adjustment(value=1, lower=1, upper=10, step_incr=1)
    ffwd_rev_shift_spin = Gtk.SpinButton()
    ffwd_rev_shift_spin.set_adjustment(spin_adj)
    ffwd_rev_shift_spin.set_numeric(True)

    if hasattr(prefs, 'ffwd_rev_ctrl'):
        spin_adj = Gtk.Adjustment(value=prefs.ffwd_rev_ctrl, lower=1, upper=10, step_incr=1)
    else:
        spin_adj = Gtk.Adjustment(value=10, lower=1, upper=10, step_incr=1)
    ffwd_rev_ctrl_spin = Gtk.SpinButton()
    ffwd_rev_ctrl_spin.set_adjustment(spin_adj)
    ffwd_rev_ctrl_spin.set_numeric(True)

    if hasattr(prefs, 'ffwd_rev_caps'):
        spin_adj = Gtk.Adjustment(value=prefs.ffwd_rev_caps, lower=1, upper=10, step_incr=1)
    else:
        spin_adj = Gtk.Adjustment(value=1, lower=1, upper=10, step_incr=1)
    ffwd_rev_caps_spin = Gtk.SpinButton()
    ffwd_rev_caps_spin.set_adjustment(spin_adj)
    ffwd_rev_caps_spin.set_numeric(True)

    loop_clips = Gtk.CheckButton()
    loop_clips.set_active(prefs.loop_clips)

    # Layout
    row2 = _row(guiutils.get_checkbox_row_box(auto_center_on_stop, Gtk.Label(label=_("Center Current Frame on Playback Stop"))))
    row13 = _row(guiutils.get_checkbox_row_box(auto_center_on_updown, Gtk.Label(label=_("Center Current Frame after Up/Down Arrow"))))
    # Jul-2016 - SvdB - For play_pause button
    row10 = _row(guiutils.get_checkbox_row_box(play_pause_button, Gtk.Label(label=_("Enable single Play/Pause button"))))
    # Apr-2017 - SvdB - For Fast Forward / Reverse options
# ------------------------------ timeline_start_end_button
    row11 = _row(guiutils.get_checkbox_row_box(timeline_start_end_button, Gtk.Label(label=_("Enable timeline at start or end  buttons"))))
# ------------------------------ End of timeline_start_end_button
    row14 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Fast Forward / Reverse Speed for Shift Key:")), ffwd_rev_shift_spin, PREFERENCES_LEFT))
    row14.set_tooltip_text(_("Speed of Forward / Reverse will be multiplied by this value if Shift Key is held (Only using KEYS).\n" \
        "Enabling multiple modifier keys will multiply the set values.\n" \
        "E.g. if Shift is set to " + str(prefs.ffwd_rev_shift) + " and Ctrl to " + str(prefs.ffwd_rev_ctrl) + \
        ", holding Shift + Ctrl will result in up to " + str(prefs.ffwd_rev_shift * prefs.ffwd_rev_ctrl) + "x speed.\n" \
        "(Effective maximum speed depends on underlying software and/or hardware limitations)"))
    row15 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Fast Forward / Reverse Speed for Control Key:")), ffwd_rev_ctrl_spin, PREFERENCES_LEFT))
    row15.set_tooltip_text(_("Speed of Forward / Reverse will be multiplied by this value if Ctrl Key is held (Only using KEYS)."))
    row16 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Fast Forward / Reverse Speed for Caps Lock Key:")), ffwd_rev_caps_spin, PREFERENCES_LEFT))
    row16.set_tooltip_text(_("Speed of Forward / Reverse will be multiplied by this value if Caps Lock is set (Only using KEYS)."))
    row17 = _row(guiutils.get_checkbox_row_box(follow_move_range, Gtk.Label(label=_("Move Timeline to follow Playback"))))
    row18 = _row(guiutils.get_checkbox_row_box(loop_clips, Gtk.Label(label=_("Loop Media Clips on Monitor"))))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row17, False, False, 0)
    vbox.pack_start(row18, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row13, False, False, 0)
    # Jul-2016 - SvdB - For play_pause button
    vbox.pack_start(row10, False, False, 0)
# ------------------------------ timeline_start_end_button
    vbox.pack_start(row11, False, False, 0)
# ------------------------------ End of timeline_start_end_button
    # Apr-2017 - SvdB - For ffwd / rev speed
    vbox.pack_start(row14, False, False, 0)
    vbox.pack_start(row15, False, False, 0)
    vbox.pack_start(row16, False, False, 0)

    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    # Jul-2016 - SvdB - Added play_pause_button
    # Apr-2017 - SvdB - Added ffwd / rev values
# ------------------------------ timeline_start_end_button
    return vbox, (auto_center_on_stop,
                  play_pause_button, timeline_start_end_button, auto_center_on_updown,
                  ffwd_rev_shift_spin, ffwd_rev_ctrl_spin, ffwd_rev_caps_spin, follow_move_range, loop_clips)
# ------------------------------ End of timeline_start_end_button
#    return vbox, (auto_center_on_stop,
#                  play_pause_button, auto_center_on_updown,
#                  ffwd_rev_shift_spin, ffwd_rev_ctrl_spin, ffwd_rev_caps_spin, follow_move_range, loop_clips)

def _view_prefs_panel():
    prefs = editorpersistance.prefs

    # Widgets
    force_english_check = Gtk.CheckButton()
    force_english_check.set_active(prefs.use_english_always)

    force_language_combo = Gtk.ComboBoxText()
    force_language_combo.append_text(_("None"))
    force_language_combo.append_text(_("English"))
    force_language_combo.append_text(_("Chinese, Simplified"))
    force_language_combo.append_text(_("Chinese, Traditional"))
    force_language_combo.append_text(_("Czech"))
    force_language_combo.append_text(_("French"))
    force_language_combo.append_text(_("German"))
    force_language_combo.append_text(_("Hungarian"))
    force_language_combo.append_text(_("Italian"))
    force_language_combo.append_text(_("Polish"))
    force_language_combo.append_text(_("Russian"))
    force_language_combo.append_text(_("Spanish"))
    force_language_combo.append_text(_("Ukranian"))
    # THIS NEEDS TO BE UPDATED WHEN LANGUAGES ARE ADDED!!!
    lang_list = ["None","English","zh_CN","zh_TW","cs","fr","de","hu","it","pl","ru","es","uk"]
    active_index = lang_list.index(prefs.force_language)
    force_language_combo.set_active(active_index)
    force_language_combo.lang_codes = lang_list

    display_splash_check = Gtk.CheckButton()
    display_splash_check.set_active(prefs.display_splash_screen)

    # Feb-2017 - SvdB - For full file names
    show_full_file_names = Gtk.CheckButton()
    show_full_file_names.set_active(prefs.show_full_file_names)

    buttons_combo = Gtk.ComboBoxText()
    buttons_combo.append_text(_("Glass"))
    buttons_combo.append_text(_("Simple"))
    buttons_combo.append_text(_("No Decorations"))
    buttons_combo.set_active( prefs.buttons_style )

    dark_combo = Gtk.ComboBoxText()
    dark_combo.append_text(_("Flowblade Theme"))
    dark_combo.append_text(_("Dark Theme"))
    dark_combo.append_text(_("Light Theme"))
    dark_combo.set_active(prefs.theme)


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

    tracks_combo = Gtk.ComboBoxText()
    tracks_combo.append_text(_("Normal - 50px, 25px"))
    tracks_combo.append_text(_("Double for HiDPI - 100px, 50px"))
    # Aug-2019 - SvdB - BB
    tracks_combo.set_active(prefs.double_track_hights)

    top_row_layout = Gtk.ComboBoxText()
    top_row_layout.append_text(_("3 panels if width (1450px+) available"))
    top_row_layout.append_text(_("2 panels always"))
    top_row_layout.set_active(prefs.top_row_layout)

    monitors_data = utils.get_display_monitors_size_data()
    layout_monitor = Gtk.ComboBoxText()
    combined_w, combined_h = monitors_data[0]
    layout_monitor.append_text(_("Full Display area: ") + str(combined_w) + " x " + str(combined_h))
    if len(monitors_data) >= 3:
        for monitor_index in range(1, len(monitors_data)):
            monitor_w, monitor_h = monitors_data[monitor_index]
            layout_monitor.append_text(_("Monitor ") + str(monitor_index) + ": " + str(monitor_w) + " x " + str(monitor_h))
    layout_monitor.set_active(prefs.layout_display_index)


    # Layout
    row00 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Application window mode:")), window_mode_combo, PREFERENCES_LEFT))
    #row0 = _row(guiutils.get_checkbox_row_box(force_english_check, Gtk.Label(label=_("Use English texts on localized OS"))))
    row9 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Force Language:")), force_language_combo, PREFERENCES_LEFT))
    row1 = _row(guiutils.get_checkbox_row_box(display_splash_check, Gtk.Label(label=_("Display splash screen"))))
    row2 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Buttons style:")), buttons_combo, PREFERENCES_LEFT))
    row3 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Theme request, icons and colors:")), dark_combo, PREFERENCES_LEFT))
    row4 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Theme detection fail fallback colors:")), theme_combo, PREFERENCES_LEFT))
    row5 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Default audio levels display:")), audio_levels_combo, PREFERENCES_LEFT))
    row7 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Tracks Heights:")), tracks_combo, PREFERENCES_LEFT))
    # Feb-2017 - SvdB - For full file names
    row6 =  _row(guiutils.get_checkbox_row_box(show_full_file_names, Gtk.Label(label=_("Show Full File names"))))
    row8 =  _row(guiutils.get_two_column_box(Gtk.Label(label=_("Top row layout:")), top_row_layout, PREFERENCES_LEFT))

    row10 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Do GUI layout based on:")), layout_monitor, PREFERENCES_LEFT))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row00, False, False, 0)
    vbox.pack_start(row10, False, False, 0)
    vbox.pack_start(row9, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    # Feb-2017 - SvdB - For full file names
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    # Feb-2017 - SvdB - Added code for full file names
    return vbox, (force_language_combo, display_splash_check, buttons_combo, dark_combo, theme_combo, audio_levels_combo,
                  window_mode_combo, show_full_file_names, tracks_combo, top_row_layout, layout_monitor)

def _performance_panel():
    # Jan-2017 - SvdB
    # Add a panel for performance settings. The first setting is allowing multiple threads to render
    # the files. This is used for the real_time parameter to mlt in renderconsumer.py.
    # The effect depends on the computer running the program.
    # Max. number of threads is set to number of CPU cores. Default is 1.
    # Allow Frame Dropping should help getting real time output on low performance computers.
    prefs = editorpersistance.prefs

    warning_icon = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DIALOG)
    warning_label = Gtk.Label(label=_("Changing these values may cause problems with playback and rendering.\nThe safe values are Render Threads:1, Allow Frame Dropping: No."))

    spin_adj = Gtk.Adjustment(value=prefs.perf_render_threads, lower=1, upper=multiprocessing.cpu_count(), step_incr=1)
    perf_render_threads = Gtk.SpinButton(adjustment=spin_adj)
    #perf_render_threads.set_adjustment(spin_adj)
    perf_render_threads.set_numeric(True)

    perf_drop_frames = Gtk.CheckButton()
    perf_drop_frames.set_active(prefs.perf_drop_frames)

    # Tooltips
    perf_render_threads.set_tooltip_text(_("Between 1 and the number of CPU Cores"))
    perf_drop_frames.set_tooltip_text(_("Allow Frame Dropping for real-time rendering, when needed"))

    # Layout
    row0 = _row(guiutils.get_left_justified_box([warning_icon, warning_label]))
    row1 = _row(guiutils.get_two_column_box(Gtk.Label(label=_("Render Threads:")), perf_render_threads, PREFERENCES_LEFT))
    row2 = _row(guiutils.get_checkbox_row_box(perf_drop_frames, Gtk.Label(label=_("Allow Frame Dropping"))))

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(guiutils.pad_label(12, 12), False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)

    guiutils.set_margins(vbox, 12, 0, 12, 12)

    return vbox, (perf_render_threads, perf_drop_frames)

def _row(row_cont):
    row_cont.set_size_request(10, 26)
    return row_cont
