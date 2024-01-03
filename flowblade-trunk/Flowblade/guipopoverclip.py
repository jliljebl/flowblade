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

import copy

import appconsts
import guipopover
from editorstate import current_sequence
import mltfilters
import toolsintegration
import translations
import utils

_clip_popover = None
_clip_menu = None
_audio_submenu = None 
_markers_submenu = None
_markers_submenu_static_items = None
_reload_section = None
_edit_actions_menu = None

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
    global _clip_popover, _clip_menu, _audio_submenu, _markers_submenu, \
    _markers_submenu_static_items, _reload_section, _edit_actions_menu

    if _clip_menu == None:
        _clip_menu = guipopover.menu_clear_or_create(_clip_menu)
        
        monitor_section = Gio.Menu.new()
        add_menu_action(monitor_section, _("Open in Clip Monitor"), "clipmenu.openinmonitor",  (clip, track, "open_in_clip_monitor", x), callback)
        _clip_menu.append_section(None, monitor_section)

        audio_section = Gio.Menu.new()
        _audio_submenu = Gio.Menu.new()
        _fill_audio_menu(_audio_submenu, clip, track, x, callback)
        audio_section.append_submenu(_("Audio Edit"), _audio_submenu)
        _clip_menu.append_section(None, audio_section)

        clip_data_section = Gio.Menu.new()

        properties_submenu = _get_properties_submenu(clip, track, x, callback)
        clip_data_section.append_submenu(_("Properties"), properties_submenu)

        _markers_submenu = Gio.Menu.new()
        _markers_submenu_static_items = Gio.Menu.new()
        _fill_markers_menu(_markers_submenu, _markers_submenu_static_items, clip, track, x, callback)
        markers_section_all = Gio.Menu.new()
        markers_section_all.append_section(None, _markers_submenu)
        markers_section_all.append_section(None, _markers_submenu_static_items)
        clip_data_section.append_submenu(_("Markers"), markers_section_all)

        add_menu_action(clip_data_section, _("Clip Info"), "clipmenu.openinmonitor.clipinfo",  (clip, track, "clip_info", x), callback)
        _clip_menu.append_section(None, clip_data_section)

        _reload_section = Gio.Menu.new()
        _fill_reload_section(_reload_section, clip, track, x, callback)
        _clip_menu.append_section(None, _reload_section)

        edit_section = Gio.Menu.new()
        select_menu = Gio.Menu.new()
        _fill_select_menu(select_menu, clip, track, x, callback)
        edit_section.append_submenu(_("Select"), select_menu)
        _edit_actions_menu = Gio.Menu.new()
        _fill_edit_actions_menu(_edit_actions_menu, clip, track, x, callback)
        edit_section.append_submenu(_("Edit"), _edit_actions_menu)
        tools_submenu = Gio.Menu.new()
        _fill_tool_integration_menu(tools_submenu, clip, track, x, callback)
        edit_section.append_submenu(_("Export To Tool"), tools_submenu)
        _clip_menu.append_section(None, edit_section)

        filters_section = Gio.Menu.new()
        add_filter_menu = Gio.Menu.new()
        _fill_filters_menus(add_filter_menu, clip, track, x, callback, "add_filter", "clipmenu.addfilter.")
        filters_section.append_submenu(_("Add Filter"), add_filter_menu)
        clone_sub_menu = Gio.Menu.new()
        _fill_clone_filters_menu(clone_sub_menu, clip, track, x, callback, False)
        filters_section.append_submenu(_("Clone Filter"), clone_sub_menu)
        add_menu_action(filters_section, _("Clear Filters"), "clipmenu.clearfilters",  (clip, track, "clear_filters", x), callback)
        _clip_menu.append_section(None, filters_section)

        edit_filters_section = Gio.Menu.new()
        add_menu_action(edit_filters_section, _("Edit Filters"), "clipmenu.openineditor",  (clip, track, "open_in_editor", x), callback)
        _clip_menu.append_section(None, edit_filters_section)

    else: # Menu items with possible state changes need to recreated.
        guipopover.menu_clear_or_create(_audio_submenu)
        _fill_audio_menu(_audio_submenu, clip, track, x, callback)

        guipopover.menu_clear_or_create(_markers_submenu)
        guipopover.menu_clear_or_create(_markers_submenu_static_items)
        _fill_markers_menu(_markers_submenu, _markers_submenu_static_items, clip, track, x, callback)

        guipopover.menu_clear_or_create(_reload_section)
        _fill_reload_section(_reload_section, clip, track, x, callback)

        guipopover.menu_clear_or_create(_edit_actions_menu)
        _fill_edit_actions_menu(_edit_actions_menu, clip, track, x, callback)
 
    rect = guipopover.create_rect(x, y)
    _clip_popover = guipopover.new_mouse_popover(widget, _clip_menu, rect, Gtk.PositionType.TOP)

def _fill_audio_menu(audio_submenu, clip, track, x, callback):
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
    add_menu_action(audio_submenu, _("Select Clip to Audio Sync With..."), "clipmenu.setaudiosyncclip",  (clip, track, "set_audio_sync_clip", x), callback, active)
        
    active = not(clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Unmute"), "clipmenu.unmuteclip",  (clip, track, "mute_clip", (False)), callback, active)

    active = (clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Mute Audio"), "clipmenu.muteclip",  (clip, track, "mute_clip", (True)), callback, active)

def _get_properties_submenu(clip, track, x, callback):

    properties_submenu = Gio.Menu.new()

    add_menu_action(properties_submenu, _("Rename Clip"), "clipmenu.rename",  (clip, track, "rename_clip", x), callback)
    
    color_submenu = Gio.Menu.new()
    add_menu_action(color_submenu, _("Default"), "clipmenu.colordefault",  (clip, track, "clip_color", "default"), callback)
    add_menu_action(color_submenu, _("Red"), "clipmenu.colorred",  (clip, track, "clip_color", "red"), callback)
    add_menu_action(color_submenu, _("Green"), "clipmenu.colorgreen",  (clip, track, "clip_color", "green"), callback)
    add_menu_action(color_submenu, _("Blue"), "clipmenu.colorblue",  (clip, track, "clip_color", "blue"), callback)
    add_menu_action(color_submenu, _("Orange"), "clipmenu.colororange",  (clip, track, "clip_color", "orange"), callback)
    add_menu_action(color_submenu, _("Brown"), "clipmenu.colorbrown",  (clip, track, "clip_color", "brown"), callback)
    add_menu_action(color_submenu, _("Olive"), "clipmenu.colorolive",  (clip, track, "clip_color", "olive"), callback)
    properties_submenu.append_submenu(_("Clip Color"), color_submenu)

    return properties_submenu

def _fill_markers_menu(markers_submenu, markers_submenu_static_items, clip, track, x, callback):
    markers_exist = len(clip.markers) != 0
    if markers_exist:
        for i in range(0, len(clip.markers)):
            marker = clip.markers[i]
            name, frame = marker
            item_str = utils.get_tc_string(frame) + " " + name
            add_menu_action(markers_submenu, item_str, "clipmenu.markeritems." + str(i),  (clip, track, "go_to_clip_marker", str(i)), callback)
    else:
            add_menu_action(markers_submenu, _("No Clip Markers"), "clipmenu.markeritems.nomarkers",  None, callback, False)

    add_menu_action(markers_submenu_static_items, _("Add Clip Marker At Playhead Position"), "clipmenu.markeritems.addclipmarker",  (clip, track, "add_clip_marker", None), callback)
    add_menu_action(markers_submenu_static_items, _("Delete Clip Marker At Playhead Position"), "clipmenu.markeritems.deleteclipmarker",  (clip, track, "delete_clip_marker", None), callback)
    add_menu_action(markers_submenu_static_items, _("Delete All Clip Markers"), "clipmenu.markeritems.deleteall",  (clip, track, "deleteall_clip_markers", None), callback)


def _fill_reload_section(reload_section, clip, track, x, callback):
    if clip.media_type != appconsts.PATTERN_PRODUCER and clip.container_data == None:
        add_menu_action(reload_section, _("Reload Media From Disk"), "clipmenu.reload",  (clip, track, "reload_media", x), callback)
    else:
        add_menu_action(reload_section, _("Reload Media From Disk"), "clipmenu.reload",  (clip, track, "reload_media", x), callback, False)

def _fill_edit_actions_menu(edit_actions_menu, clip, track, x, callback):
    kf_section = Gio.Menu.new()
    if (clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER) == False:
        add_menu_action(edit_actions_menu, _("Volume Keyframes"), "clipmenu.volumekfs",  (clip, track, "volumekf", x), callback)
    if track.type == appconsts.VIDEO:
        add_menu_action(edit_actions_menu,_("Brightness Keyframes"), "clipmenu.brightkfs",  (clip, track, "brightnesskf", x), callback)
    edit_actions_menu.append_section(None, kf_section)

    del_section = Gio.Menu.new()
    add_menu_action(del_section,_("Delete"), "clipmenu.delete",  (clip, track, "delete", x), callback)
    add_menu_action(del_section,_("Lift"), "clipmenu.delete",  (clip, track, "lift", x), callback)
    edit_actions_menu.append_section(None, del_section)

    if track.id != current_sequence().first_video_index:
        sync_section = Gio.Menu.new()
        if clip.sync_data != None:
            add_menu_action(sync_section,_("Resync"), "clipmenu.resync",  (clip, track, "resync", x), callback)
            add_menu_action(sync_section,_("Clear Sync Relation"), "clipmenu.clearsyncrel",  (clip, track, "clear_sync_rel", x), callback)
        else:
            add_menu_action(sync_section,_("Select Sync Parent Clip..."), "clipmenu.setmaster",  (clip, track, "set_master", x), callback)
        edit_actions_menu.append_section(None, sync_section)

    length_section = Gio.Menu.new()
    add_menu_action(length_section, _("Set Clip Length..."), "clipmenu.length",  (clip, track, "length", x), callback)
    add_menu_action(length_section, _("Stretch Over Next Blank"), "clipmenu.stretchnext",  (clip, track, "stretch_next", x), callback)
    add_menu_action(length_section,_("Stretch Over Prev Blank"), "clipmenu.stretchprev",  (clip, track, "stretch_prev", x), callback)
    edit_actions_menu.append_section(None, length_section)

def _fill_tool_integration_menu(tools_sub_menu, clip, track, x, callback):
    export_tools = toolsintegration.get_export_integrators()
    i = 0
    for integrator in export_tools:
        if integrator.supports_clip_media(clip) == False:
            active = False
        else:
            active = True
        add_menu_action(tools_sub_menu, copy.copy(integrator.tool_name), "clipmenu." + str(i),  (clip, track),  integrator.export_callback, active)
        i += 1

def _fill_select_menu(select_menu, clip, track, x, callback):
    add_menu_action(select_menu, _("All Clips After"), "clipmenu.selectallafter",  (clip, track, "select_all_after", None), callback)
    add_menu_action(select_menu, _("All Clips Before"), "clipmenu.selectallbefore",  (clip, track, "select_all_before", None), callback)

def _fill_filters_menus(sub_menu, clip, track, x, callback, item_id, action_id):
    j = 0
    for group in mltfilters.groups:
        group_name, filters_array = group
        
        group_menu = Gio.Menu.new()
        sub_menu.append_submenu(group_name, group_menu)
        i = 0
        for filter_info in filters_array:
            add_menu_action(group_menu, translations.get_filter_name(filter_info.name), action_id + str(j) + "." + str(i),  (clip, track, item_id, (x, filter_info)), callback)
            i += 1
        j += 1

def _fill_clone_filters_menu(clone_sub_menu, clip, track, x, callback, is_multi=False):
    add_menu_action(clone_sub_menu, _("From Next Clip"), "clipmenu.clonefromnext", (clip, track, "clone_filters_from_next", is_multi), callback)
    add_menu_action(clone_sub_menu, _("From Previous Clip"), "clipmenu.clonefromprev", (clip, track, "clone_filters_from_prev", is_multi), callback)

    
"""
def _get_edit_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Edit"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)
        
    if (clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER) == False:
        vol_item = _get_menu_item(_("Volume Keyframes"), callback, (clip, track, "volumekf", event.x))
        sub_menu.append(vol_item)

    if track.type == appconsts.VIDEO:
        bright_item = _get_menu_item(_("Brightness Keyframes"), callback, (clip, track, "brightnesskf", event.x))
        sub_menu.append(bright_item)

    _add_separetor(sub_menu)
    
    del_item = _get_menu_item(_("Delete"), callback, (clip, track, "delete", event.x))
    sub_menu.append(del_item)

    lift_item = _get_menu_item(_("Lift"), callback, (clip, track, "lift", event.x))
    sub_menu.append(lift_item)

    if track.id != current_sequence().first_video_index:
        _add_separetor(sub_menu)
        if clip.sync_data != None:
            sub_menu.add(_get_menu_item(_("Resync"), callback, (clip, track, "resync", event.x)))
            sub_menu.add(_get_menu_item(_("Clear Sync Relation"), callback, (clip, track, "clear_sync_rel", event.x)))
        else:
            sub_menu.add(_get_menu_item(_("Select Sync Parent Clip..."), callback, (clip, track, "set_master", event.x)))

    _add_separetor(sub_menu)
    
    length_item = _get_menu_item(_("Set Clip Length..."), callback, (clip, track, "length", event.x))
    sub_menu.append(length_item)

    stretch_next_item = _get_menu_item(_("Stretch Over Next Blank"), callback, (clip, track, "stretch_next", event.x))
    sub_menu.append(stretch_next_item)

    stretch_prev_item = _get_menu_item(_("Stretch Over Prev Blank"), callback, (clip, track, "stretch_prev", event.x))
    sub_menu.append(stretch_prev_item)

    if track.type == appconsts.VIDEO:
        _add_separetor(sub_menu)
        sub_menu.add(_get_tool_integration_menu_item(event, clip, track, callback))

    menu_item.show()
    return menu_item


def _get_clip_markers_menu_item(event, clip, track, callback):
    markers_menu_item = Gtk.MenuItem(_("Markers"))
    markers_menu =  Gtk.Menu()
    markers_exist = len(clip.markers) != 0

    if markers_exist:
        for i in range(0, len(clip.markers)):
            marker = clip.markers[i]
            name, frame = marker
            item_str = utils.get_tc_string(frame) + " " + name
            markers_menu.add(_get_menu_item(item_str, callback, (clip, track, "go_to_clip_marker", str(i))))
        _add_separetor(markers_menu)
    else:
        no_markers_item = _get_menu_item(_("No Clip Markers"), callback, "dummy", False)
        markers_menu.add(no_markers_item)
        _add_separetor(markers_menu)
        
    markers_menu.add(_get_menu_item(_("Add Clip Marker At Playhead Position"), callback, (clip, track, "add_clip_marker", None)))
    del_item = _get_menu_item(_("Delete Clip Marker At Playhead Position"), callback, (clip, track, "delete_clip_marker", None), markers_exist==True)
    markers_menu.add(del_item)
    del_all_item = _get_menu_item(_("Delete All Clip Markers"), callback, (clip, track, "deleteall_clip_markers", None), markers_exist==True)
    markers_menu.add(del_all_item)
    markers_menu_item.set_submenu(markers_menu)
    markers_menu_item.show_all()
    return markers_menu_item
    
def _get_clip_properties_menu_item(event, clip, track, callback):
    properties_menu_item = Gtk.MenuItem(_("Properties"))
    properties_menu = Gtk.Menu()
    properties_menu.add(_get_menu_item(_("Rename Clip"), callback,\
                      (clip, track, "rename_clip", event.x)))
    properties_menu.add(_get_color_menu_item(clip, track, callback))
    properties_menu_item.set_submenu(properties_menu)
    properties_menu_item.show_all()
    return properties_menu_item

def _get_color_menu_item(clip, track, callback):
    color_menu_item = Gtk.MenuItem(_("Clip Color"))
    color_menu =  Gtk.Menu()
    color_menu.add(_get_menu_item(_("Default"), callback, (clip, track, "clip_color", "default")))
    color_menu.add(_get_menu_item(_("Red"), callback, (clip, track, "clip_color", "red")))
    color_menu.add(_get_menu_item(_("Green"), callback, (clip, track, "clip_color", "green")))
    color_menu.add(_get_menu_item(_("Blue"), callback, (clip, track, "clip_color", "blue")))
    color_menu.add(_get_menu_item(_("Orange"), callback, (clip, track, "clip_color", "orange")))
    color_menu.add(_get_menu_item(_("Brown"), callback, (clip, track, "clip_color", "brown")))
    color_menu.add(_get_menu_item(_("Olive"), callback, (clip, track, "clip_color", "olive")))
    color_menu_item.set_submenu(color_menu)
    color_menu_item.show_all()
    return color_menu_item
"""
