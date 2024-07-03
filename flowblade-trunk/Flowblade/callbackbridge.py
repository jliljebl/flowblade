"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2024 Janne Liljeblad.

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

app_open_project = None
app_new_project = None
app_stop_autosave = None
app_start_autosave = None
app_change_current_sequence = None
app_shutdown = None

clipeffectseditor_refresh_clip = None
clipeffectseditor_update_kfeditors_sliders = None
clipeffectseditor_clip_is_being_edited = None
    
clipmenuaction_display_clip_menu = None
clipmenuaction_compositor_menu_item_activated = None
clipmenuaction_get_popover_clip_data = None
clipmenuaction_set_compositor_data = None

compositeeditor_get_compositor = None
 
editevent_tline_range_item_drop = None
editevent_do_multiple_clip_insert = None

medialog_clips_drop = None

mediaplugin_get_clip = None
mediaplugin_set_plugin_to_be_edited = None

modesetting_set_default_edit_mode = None

movemodes_select_clip = None
movemodes_select_from_box_selection = None

projectaction_open_rendered_file = None
projectaction_open_file_names = None

rotomask_show_rotomask = None

targetactions_get_handler_by_name = None
targetactions_move_player_position = None
targetactions_variable_speed_playback = None

trimmodes_set_no_edit_trim_mode = None

updater_set_and_display_monitor_media_file = None
pdater_display_sequence_in_monitor = None
updater_repaint_tline = None
