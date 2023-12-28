"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

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
from gi.repository import Gio, Gtk, GLib, Gdk

import appconsts
import guipopover
from editorstate import current_sequence
import utils

_clip_popover = None
_clip_menu = None
 

# -------------------------------------------------- menuitems builder fuctions
def add_menu_action(menu, label, item_id, data, callback, active=True, app=None):
    return guipopover.add_menu_action(menu, label, item_id, data, callback, active, app)

def add_menu_action_check(menu, label, item_id, checked_state, msg_str, callback):
    return guipopover.add_menu_action_check(menu, label, item_id, checked_state, msg_str, callback)

def add_menu_action_radio(menu, label, item_id, target_variant):
    return guipopover.add_menu_action_radio(menu, label, item_id, target_variant)

def add_menu_action_all_items_radio(menu, items_data, item_id, selected_index, callback):
    return guipopover.add_menu_action_all_items_radio(menu, items_data, item_id, selected_index, callback)

# -------------------------------------------------- clip menus
def clip_popover_menu_show(widget, x, y, clip, track, callback):
    global _clip_popover, _clip_menu

    _clip_menu = guipopover.menu_clear_or_create(_clip_menu)
    
    monitor_section = Gio.Menu.new()
    add_menu_action(monitor_section, _("Open in Clip Monitor"), "clipmenu.openinmonitor",  (clip, track, "open_in_clip_monitor", x), callback)
    _clip_menu.append_section(None, monitor_section)

    audio_section = _get_audio_menu_section(clip, track, x, callback)
    _clip_menu.append_section(None, audio_section)
    
    rect = guipopover.create_rect(x, y)
    _clip_popover = guipopover.new_mouse_popover(widget, _clip_menu, rect)


def _get_audio_menu_section(clip, track, x, callback):
    audio_section = Gio.Menu.new()
    audio_submenu = Gio.Menu.new()

    if track.type == appconsts.VIDEO:
        active = True
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        add_menu_action(audio_submenu, _("Split Audio"), "clipmenu.splitaudio",  (clip, track, "split_audio", x), callback, active)

        active = (track.id == current_sequence().first_video_index)
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        add_menu_action(audio_submenu, _("Split Audio Synched"), "clipmenu.splitaudiosynched",  (clip, track, "split_audio_synched", x), callback, active)

    active = True
    if utils.is_mlt_xml_file(clip.path) == True:
        active = False
    if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
        active = False
    add_menu_action(audio_submenu, _("Select Clip to Audio Sync With..."), "clipmenu.set_audiosyncclip",  (clip, track, "set_audio_sync_clip", x), callback, active)
        
    active = not(clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Unmute"), "clipmenu.unmuteclip",  (clip, track, "mute_clip", (False)), callback, active)

    active = (clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Mute Audio"), "clipmenu.muteclip",  (clip, track, "mute_clip", (True)), callback, active)

    audio_section.append_submenu(_("Audio"), audio_submenu)
    return audio_section


    