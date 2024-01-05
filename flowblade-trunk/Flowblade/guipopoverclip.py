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
_tools_submenu = None
_edit_bottom_section = None
_compositor_section = None
_title_section = None
_generator_section = None

_audio_clip_popover = None
_audio_clip_menu = None
_sync_section = None
_audio_mute_menu = None 
_audio_markers_submenu = None
_audio_markers_submenu_static_items = None


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
def clip_popover_menu_show(widget, clip, track, x, y, callback):
    global _clip_popover, _clip_menu, _audio_submenu, _markers_submenu, \
    _markers_submenu_static_items, _reload_section, _edit_actions_menu, \
    _tools_submenu, _title_section, _compositor_section, _generator_section

    if _clip_menu == None:
        _clip_menu = guipopover.menu_clear_or_create(_clip_menu)
        
        monitor_section = Gio.Menu.new()
        add_menu_action(monitor_section, _("Open in Clip Monitor"), "clipmenu.openinmonitor", ("open_in_clip_monitor", None), callback)
        _clip_menu.append_section(None, monitor_section)

        audio_section = Gio.Menu.new()
        _audio_submenu = Gio.Menu.new()
        _fill_audio_menu(_audio_submenu, clip, track, callback)
        audio_section.append_submenu(_("Audio Edit"), _audio_submenu)
        _clip_menu.append_section(None, audio_section)

        _generator_section = Gio.Menu.new()
        _fill_generator_section(_generator_section, clip, callback)
        _clip_menu.append_section(None, _generator_section)
        
        clip_data_section = Gio.Menu.new()
        properties_submenu = _get_properties_submenu(callback)
        clip_data_section.append_submenu(_("Properties"), properties_submenu)
        _markers_submenu = Gio.Menu.new()
        _markers_submenu_static_items = Gio.Menu.new()
        _fill_markers_menu(_markers_submenu, _markers_submenu_static_items, clip, callback)
        markers_section_all = Gio.Menu.new()
        markers_section_all.append_section(None, _markers_submenu)
        markers_section_all.append_section(None, _markers_submenu_static_items)
        clip_data_section.append_submenu(_("Markers"), markers_section_all)
        add_menu_action(clip_data_section, _("Clip Info"), "clipmenu.openinmonitor.clipinfo",  ("clip_info", None), callback)
        _clip_menu.append_section(None, clip_data_section)

        _compositor_section = Gio.Menu.new()
        _fill_compositors_section(_compositor_section, clip, track, callback)
        _clip_menu.append_section(None, _compositor_section)
        
        _reload_section = Gio.Menu.new()
        _fill_reload_section(_reload_section, clip, callback)
        _clip_menu.append_section(None, _reload_section)

        edit_section = Gio.Menu.new()
        select_menu = Gio.Menu.new()
        _fill_select_menu(select_menu, callback)
        edit_section.append_submenu(_("Select"), select_menu)
        _edit_actions_menu = Gio.Menu.new()
        _fill_edit_actions_menu(_edit_actions_menu, clip, track, callback)
        edit_section.append_submenu(_("Edit"), _edit_actions_menu)
        _tools_submenu = Gio.Menu.new()
        _fill_tool_integration_menu(_tools_submenu, clip, callback)
        edit_section.append_submenu(_("Export To Tool"), _tools_submenu)
        _clip_menu.append_section(None, edit_section)

        filters_section = Gio.Menu.new()
        add_filter_menu = Gio.Menu.new()
        _fill_filters_menus(add_filter_menu, callback, "add_filter", "clipmenu.addfilter.")
        filters_section.append_submenu(_("Add Filter"), add_filter_menu)
        clone_sub_menu = Gio.Menu.new()
        _fill_clone_filters_menu(clone_sub_menu, callback, False, False)
        filters_section.append_submenu(_("Clone Filter"), clone_sub_menu)
        add_menu_action(filters_section, _("Clear Filters"), "clipmenu.clearfilters",  ("clear_filters", None), callback)
        _clip_menu.append_section(None, filters_section)

        _title_section = Gio.Menu.new()
        _fill_title_section(_title_section, clip, callback)
        _clip_menu.append_section(None, _title_section)

        edit_bottom_section = Gio.Menu.new()
        add_menu_action(edit_bottom_section, _("Edit Filters"), "clipmenu.openineditor",  ("open_in_editor", None), callback)
        _clip_menu.append_section(None, edit_bottom_section)

    else: # Menu items with possible state changes need to recreated.
        guipopover.menu_clear_or_create(_audio_submenu)
        _fill_audio_menu(_audio_submenu, clip, track,  callback)

        guipopover.menu_clear_or_create(_markers_submenu)
        guipopover.menu_clear_or_create(_markers_submenu_static_items)
        _fill_markers_menu(_markers_submenu, _markers_submenu_static_items, clip, callback)

        guipopover.menu_clear_or_create(_compositor_section)
        _fill_compositors_section(_compositor_section, clip, track, callback)
        
        guipopover.menu_clear_or_create(_reload_section)
        _fill_reload_section(_reload_section, clip, callback)

        guipopover.menu_clear_or_create(_edit_actions_menu)
        _fill_edit_actions_menu(_edit_actions_menu, clip, track, callback)

        guipopover.menu_clear_or_create(_tools_submenu)
        _fill_tool_integration_menu(_tools_submenu, clip, callback)
        
        guipopover.menu_clear_or_create(_title_section)
        _fill_title_section(_title_section, clip, callback)

        guipopover.menu_clear_or_create(_generator_section)
        _fill_generator_section(_generator_section, clip, callback)

    rect = guipopover.create_rect(x, y)
    _clip_popover = guipopover.new_mouse_popover(widget, _clip_menu, rect, Gtk.PositionType.TOP)


def audio_clip_popover_menu_show(widget, clip, track, x, y, callback):
    global _audio_clip_popover, _audio_clip_menu, _sync_section, _audio_mute_menu, \
    _audio_markers_submenu, _audio_markers_submenu_static_items

    if _audio_clip_menu == None:
        _audio_clip_menu = guipopover.menu_clear_or_create(_audio_clip_menu)
        
        monitor_section = Gio.Menu.new()
        add_menu_action(monitor_section, _("Open in Clip Monitor"), "audioclipmenu.openinmonitor", ("open_in_clip_monitor", None), callback)
        _audio_clip_menu.append_section(None, monitor_section)

        _sync_section = Gio.Menu.new()
        _fill_audio_clip_sync_section(_sync_section, clip, callback)
        _audio_clip_menu.append_section(None, _sync_section)

        mute_section = Gio.Menu.new()
        _audio_mute_menu = Gio.Menu.new()
        _fill_audio_mute_menu(_audio_mute_menu, clip, callback)
        mute_section.append_submenu(_("Mute"), _audio_mute_menu)
        _audio_clip_menu.append_section(None, mute_section)

        clip_data_section = Gio.Menu.new()
        properties_submenu = _get_properties_submenu(callback, True)
        clip_data_section.append_submenu(_("Properties"), properties_submenu)
        _audio_markers_submenu = Gio.Menu.new()
        _audio_markers_submenu_static_items = Gio.Menu.new()
        _fill_markers_menu(_audio_markers_submenu, _audio_markers_submenu_static_items, clip, callback, True)
        markers_section_all = Gio.Menu.new()
        markers_section_all.append_section(None, _audio_markers_submenu)
        markers_section_all.append_section(None, _audio_markers_submenu_static_items)
        clip_data_section.append_submenu(_("Markers"), markers_section_all)
        _audio_clip_menu.append_section(None, clip_data_section)
        
        edit_section = Gio.Menu.new()
        select_menu = Gio.Menu.new()
        _fill_select_menu(select_menu, callback, True)
        edit_section.append_submenu(_("Select"), select_menu)
        edit_actions_menu = Gio.Menu.new()
        _fill_audio_edit_actions_menu(edit_actions_menu, callback)
        edit_section.append_submenu(_("Edit"), edit_actions_menu)
        _audio_clip_menu.append_section(None, edit_section)

        filters_section = Gio.Menu.new()
        audio_filters_menu = Gio.Menu.new()
        _fill_audio_filters_add_menu_item(audio_filters_menu, callback)
        filters_section.append_submenu(_("Add Filter"), audio_filters_menu)
        clone_sub_menu = Gio.Menu.new()
        _fill_clone_filters_menu(clone_sub_menu, callback, False, True)
        filters_section.append_submenu(_("Clone Filter"), clone_sub_menu)
        add_menu_action(filters_section, _("Clear Filters"), "audioclipmenu.clearfilters",  ("clear_filters", None), callback)
        _audio_clip_menu.append_section(None, filters_section)

        edit_bottom_section = Gio.Menu.new()
        add_menu_action(edit_bottom_section, _("Edit Filters"), "audioclipmenu.openineditor",  ("open_in_editor", None), callback)
        _audio_clip_menu.append_section(None, edit_bottom_section)
        
    else:
        guipopover.menu_clear_or_create(_sync_section)
        _fill_audio_clip_sync_section(_sync_section, clip, callback)

        guipopover.menu_clear_or_create(_audio_mute_menu)
        _fill_audio_mute_menu(_audio_mute_menu, clip, callback)

        guipopover.menu_clear_or_create(_audio_markers_submenu)
        guipopover.menu_clear_or_create(_audio_markers_submenu_static_items)
        _fill_markers_menu(_audio_markers_submenu, _audio_markers_submenu_static_items, clip, callback, True)
        
    rect = guipopover.create_rect(x, y)
    _audio_clip_popover = guipopover.new_mouse_popover(widget, _audio_clip_menu, rect, Gtk.PositionType.TOP)

def _fill_audio_menu(audio_submenu, clip, track, callback):
    if track.type == appconsts.VIDEO:
        active = True
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        add_menu_action(audio_submenu, _("Split Audio"), "clipmenu.splitaudio",  ("split_audio", None), callback, active)

        active = (track.id == current_sequence().first_video_index)
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        add_menu_action(audio_submenu, _("Split Audio Synched"), "clipmenu.splitaudiosynched", ("split_audio_synched", None), callback, active)

    active = True
    if utils.is_mlt_xml_file(clip.path) == True:
        active = False
    if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
        active = False
    add_menu_action(audio_submenu, _("Select Clip to Audio Sync With..."), "clipmenu.setaudiosyncclip", ("set_audio_sync_clip", None), callback, active)
        
    active = not(clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Unmute"), "clipmenu.unmuteclip", ("mute_clip", False), callback, active)

    active = (clip.mute_filter==None)
    add_menu_action(audio_submenu, _("Mute Audio"), "clipmenu.muteclip", ("mute_clip", True), callback, active)

def _get_properties_submenu(callback, is_audio_properties=False):
    if is_audio_properties == True:
        pre_id = "audio"
    else:
        pre_id = ""

    properties_submenu = Gio.Menu.new()

    add_menu_action(properties_submenu, _("Rename Clip"), pre_id + "clipmenu.rename", ("rename_clip", None), callback)
    
    color_submenu = Gio.Menu.new()
    add_menu_action(color_submenu, _("Default"), pre_id + "clipmenu.colordefault", ("clip_color", "default"), callback)
    add_menu_action(color_submenu, _("Red"), pre_id + "clipmenu.colorred", ("clip_color", "red"), callback)
    add_menu_action(color_submenu, _("Green"), pre_id + "clipmenu.colorgreen", ("clip_color", "green"), callback)
    add_menu_action(color_submenu, _("Blue"), pre_id + "clipmenu.colorblue", ("clip_color", "blue"), callback)
    add_menu_action(color_submenu, _("Orange"), pre_id + "clipmenu.colororange", ("clip_color", "orange"), callback)
    add_menu_action(color_submenu, _("Brown"), pre_id + "clipmenu.colorbrown",  ("clip_color", "brown"), callback)
    add_menu_action(color_submenu, _("Olive"), pre_id + "clipmenu.colorolive",  ("clip_color", "olive"), callback)
    properties_submenu.append_submenu(_("Clip Color"), color_submenu)

    return properties_submenu

def _fill_markers_menu(markers_submenu, markers_submenu_static_items, clip, callback, is_audio_markers=False):
    if is_audio_markers == True:
        pre_id = "audio"
    else:
        pre_id = ""
        
    markers_exist = len(clip.markers) != 0
    if markers_exist:
        for i in range(0, len(clip.markers)):
            marker = clip.markers[i]
            name, frame = marker
            item_str = utils.get_tc_string(frame) + " " + name
            add_menu_action(markers_submenu, item_str, pre_id + "clipmenu.markeritems." + str(i),  ("go_to_clip_marker", str(i)), callback)
    else:
            add_menu_action(markers_submenu, _("No Clip Markers"), pre_id + "clipmenu.markeritems.nomarkers",  (None, None), callback, False)

    add_menu_action(markers_submenu_static_items, _("Add Clip Marker At Playhead Position"), pre_id + "clipmenu.markeritems.addclipmarker",  ("add_clip_marker", None), callback)
    add_menu_action(markers_submenu_static_items, _("Delete Clip Marker At Playhead Position"), pre_id + "clipmenu.markeritems.deleteclipmarker",  ("delete_clip_marker", None), callback)
    add_menu_action(markers_submenu_static_items, _("Delete All Clip Markers"), pre_id + "clipmenu.markeritems.deleteall",  ("deleteall_clip_markers", None), callback)

def _fill_reload_section(reload_section, clip, callback):
    if clip.media_type != appconsts.PATTERN_PRODUCER and clip.container_data == None:
        add_menu_action(reload_section, _("Reload Media From Disk"), "clipmenu.reload",  ("reload_media", None), callback)
    else:
        add_menu_action(reload_section, _("Reload Media From Disk"), "clipmenu.reload",  ("reload_media", None), callback, False)

def _fill_edit_actions_menu(edit_actions_menu, clip, track, callback):
    kf_section = Gio.Menu.new()
    if (clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER) == False:
        add_menu_action(edit_actions_menu, _("Volume Keyframes"), "clipmenu.volumekfs",  ("volumekf", None), callback)
    if track.type == appconsts.VIDEO:
        add_menu_action(edit_actions_menu,_("Brightness Keyframes"), "clipmenu.brightkfs",  ("brightnesskf", None), callback)
    edit_actions_menu.append_section(None, kf_section)

    del_section = Gio.Menu.new()
    add_menu_action(del_section,_("Delete"), "clipmenu.delete",  ("delete", None), callback)
    add_menu_action(del_section,_("Lift"), "clipmenu.delete",  ("lift", None), callback)
    edit_actions_menu.append_section(None, del_section)

    if track.id != current_sequence().first_video_index:
        sync_section = Gio.Menu.new()
        if clip.sync_data != None:
            add_menu_action(sync_section,_("Resync"), "clipmenu.resync",  ("resync", None), callback)
            add_menu_action(sync_section,_("Clear Sync Relation"), "clipmenu.clearsyncrel",  ("clear_sync_rel", None), callback)
        else:
            add_menu_action(sync_section,_("Select Sync Parent Clip..."), "clipmenu.setmaster",  ("set_master", None), callback)
        edit_actions_menu.append_section(None, sync_section)

    length_section = Gio.Menu.new()
    add_menu_action(length_section, _("Set Clip Length..."), "clipmenu.length",  ("length", None), callback)
    add_menu_action(length_section, _("Stretch Over Next Blank"), "clipmenu.stretchnext",  ("stretch_next", None), callback)
    add_menu_action(length_section,_("Stretch Over Prev Blank"), "clipmenu.stretchprev",  ("stretch_prev", None), callback)
    edit_actions_menu.append_section(None, length_section)

def _fill_tool_integration_menu(tools_sub_menu, clip, callback):
    export_tools = toolsintegration.get_export_integrators()
    i = 0
    for integrator in export_tools:
        if integrator.supports_clip_media(clip) == False:
            active = False
        else:
            active = True
        add_menu_action(tools_sub_menu, copy.copy(integrator.tool_name), "clipmenu." + str(i), (None, None),  integrator.export_callback, active)
        i += 1

def _fill_select_menu(select_menu, callback, is_audio_select=False):
    if is_audio_select == True:
        pre_id = "audio"
    else:
        pre_id = ""
    add_menu_action(select_menu, _("All Clips After"), pre_id + "clipmenu.selectallafter",  ("select_all_after", None), callback)
    add_menu_action(select_menu, _("All Clips Before"), pre_id + "clipmenu.selectallbefore",  ("select_all_before", None), callback)

def _fill_filters_menus(sub_menu, callback, item_id, action_id):
    j = 0
    for group in mltfilters.groups:
        group_name, filters_array = group
        
        group_menu = Gio.Menu.new()
        sub_menu.append_submenu(group_name, group_menu)
        i = 0
        for filter_info in filters_array:
            add_menu_action(group_menu, translations.get_filter_name(filter_info.name), action_id + str(j) + "." + str(i), (item_id, filter_info), callback)
            i += 1
        j += 1

def _fill_clone_filters_menu(clone_sub_menu, callback, is_multi=False, is_audio=False):
    if is_audio == True:
        preid = "audio"
    else:
        preid = ""
    add_menu_action(clone_sub_menu, _("From Next Clip"), preid + "clipmenu.clonefromnext", ("clone_filters_from_next", is_multi), callback)
    add_menu_action(clone_sub_menu, _("From Previous Clip"), preid + "clipmenu.clonefromprev", ("clone_filters_from_prev", is_multi), callback)

def _fill_compositors_section(compositor_section, clip, track, callback):
    if track.id <= current_sequence().first_video_index or current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        active = False
    else:
        active = True
    add_menu_action(compositor_section, _("Add Compositor..."), "clipmenu.addcompositor",  ("add_compositor", None), callback, active)
    
    if len(current_sequence().get_clip_compositors(clip)) == 0 or current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        active = False
    else:
        active = True
    add_menu_action(compositor_section, _("Delete Compositor"), "clipmenu.deletecompositors",  ("delete_compositors", None), callback, active)

def _fill_title_section(title_section, clip, callback):
    #if current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
    active = (clip.titler_data != None)
    add_menu_action(title_section, _("Edit Title"), "clipmenu.edittitle",  ("edit_title", None), callback, active)
    
def _fill_generator_section(generator_section, clip, callback):
    active = (clip.container_data != None)
    genactive = active
    if clip.container_data != None and clip.container_data.container_type != appconsts.CONTAINER_CLIP_FLUXITY:
        genactive = False
    add_menu_action(generator_section, _("Edit Generator Properties..."), "clipmenu.ccedit",  ("cc_edit_program", None), callback, genactive)
    add_menu_action(generator_section, _("Create Cloned Generator..."), "clipmenu.ccclonegen",  ("cc_clone_generator", None), callback, genactive)
    add_menu_action(generator_section, _("Generator/Container Render Actions"), "clipmenu.ccclonegen",  ("cc_clone_generator", None), callback, active)

def _fill_audio_clip_sync_section(sync_section, clip, callback):
    is_synched = (clip.sync_data != None)
    add_menu_action(sync_section, _("Resync"), "audioclipmenu.resync", ("resync", None), callback, is_synched)
    add_menu_action(sync_section, _("Clear Sync Relation"), "audioclipmenu.clearsyncrel", ("clear_sync_rel", None), callback, is_synched)
    add_menu_action(sync_section, _("Select Sync Parent Clip..."), "audioclipmenu.setmaster", ("set_master", None), callback, (not is_synched))

def _fill_audio_mute_menu(audio_mute_menu, clip, callback):
    active = not(clip.mute_filter==None)
    add_menu_action(audio_mute_menu, _("Unmute"), "audioclipmenu.unmuteclip", ("mute_clip", False), callback, active)

    active = (clip.mute_filter==None)
    add_menu_action(audio_mute_menu, _("Mute Audio"), "audioclipmenu.muteclip", ("mute_clip", True), callback, active)

def _fill_audio_edit_actions_menu(edit_actions_menu, callback):
    kf_section = Gio.Menu.new()
    add_menu_action(edit_actions_menu, _("Volume Keyframes"), "audioclipmenu.volumekfs",  ("volumekf", None), callback)
    edit_actions_menu.append_section(None, kf_section)

    del_section = Gio.Menu.new()
    add_menu_action(del_section,_("Delete"), "audioclipmenu.delete",  ("delete", None), callback)
    add_menu_action(del_section,_("Lift"), "audioclipmenu.delete",  ("lift", None), callback)
    edit_actions_menu.append_section(None, del_section)

    length_section = Gio.Menu.new()
    add_menu_action(length_section, _("Set Clip Length..."), "audioclipmenu.length",  ("length", None), callback)
    add_menu_action(length_section, _("Stretch Over Next Blank"), "audioclipmenu.stretchnext",  ("stretch_next", None), callback)
    add_menu_action(length_section,_("Stretch Over Prev Blank"), "audioclipmenu.stretchprev",  ("stretch_prev", None), callback)
    edit_actions_menu.append_section(None, length_section)

def _fill_audio_filters_add_menu_item(audio_filters_menu, callback):
    audio_groups = mltfilters.get_audio_filters_groups()
    j = 0
    for group in audio_groups:
        if group == None:
            continue
        group_name, filters_array = group
        
        group_menu = Gio.Menu.new()
        audio_filters_menu.append_submenu(group_name, group_menu)
        i = 0
        for filter_info in filters_array:
            add_menu_action(group_menu, translations.get_filter_name(filter_info.name), "audioclipmenu.addfilter." + str(j) + "." + str(i), ("add_filter", filter_info), callback)
            i += 1
        j += 1

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
