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
from editorstate import APP
from editorstate import current_sequence
from editorstate import PROJECT
import editorpersistance
import editorstate
import gui
import snapping
import utils


_markers_popover = None
_markers_menu = None
_tline_properties_popover = None
_tline_properties_menu = None
_all_tracks_popover = None
_all_tracks_menu = None
_compositing_mode_popover = None
_compositing_mode_menu = None
_media_panel_popover = None
_media_panel_menu = None
_sequecne_panel_popover = None
_sequence_panel_menu = None
_layout_popover = None
_layout_menu = None
_trimview_popover = None
_trimview_menu = None
_monitorview_popover = None 
_monitorview_menu = None
_opacity_section = None
_opacity_submenu = None
_bins_panel_widget_popover = None
_bins_panel_widget_menu = None
_bins_panel_mouse_popover = None
_bins_panel_mouse_menu = None
_media_panel_hamburger_popover = None
_media_panel_hamburger_menu = None
_columns_popover = None
_columns_menu = None
_file_filter_popover = None
_file_filter_menu = None
_media_file_popover = None
_media_file_menu = None
_jobs_popover = None
_jobs_menu = None



# -------------------------------------------------- menuitems builder fuctions
def add_menu_action(menu, label, item_id, data, callback):
    menu.append(label, "app." + item_id) 
    
    action = Gio.SimpleAction(name=item_id)
    action.connect("activate", callback, data)
    APP().add_action(action)

def add_menu_action_check(menu, label, item_id, checked_state, msg_str, callback):
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=None, state=GLib.Variant.new_boolean(checked_state))
    action.connect("activate", callback, msg_str)
    APP().add_action(action)

    menu_item = Gio.MenuItem.new(label,  "app." + item_id)
    menu_item.set_action_and_target_value("app." + item_id, None)
    menu.append_item(menu_item)

def add_menu_action_radio(menu, label, item_id, target_variant):
    menu_item = Gio.MenuItem.new(label, "app." + item_id)
    menu_item.set_action_and_target_value("app." + item_id, target_variant)
    menu.append_item(menu_item)

def add_menu_action_all_items_radio(menu, items_data, item_id, selected_index, callback):

    variants = []
    for item_data in items_data: 
        label, variant_id = item_data
        target_variant = GLib.Variant.new_string(variant_id)
        menu_item = Gio.MenuItem.new(label, "app." + item_id)
        menu_item.set_action_and_target_value("app." + item_id, target_variant)
        menu.append_item(menu_item)
        variants.append(target_variant)

    # Create action and set state variant
    selected_variant = variants[selected_index]
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=GLib.VariantType.new("s"), state=selected_variant)
    action.connect("activate", callback)
    APP().add_action(action)

    
# --------------------------------------------------- helper functions
def menu_clear_or_create(menu):
    if menu != None:
        menu.remove_all()
    else:
        menu = Gio.Menu.new()
    
    return menu

def new_popover(widget, menu, launcher):
    popover = Gtk.Popover.new_from_model(widget, menu)
    launcher.connect_launched_menu(popover)
    popover.show()

    return popover

def new_mouse_popover(widget, menu, rect):
    popover = Gtk.Popover.new_from_model(widget, menu)
    popover.set_position(Gtk.PositionType(Gtk.PositionType.BOTTOM))
    popover.set_pointing_to(rect) 
    popover.show()
    
    return popover
    
def create_rect(x, y):
    rect = Gdk.Rectangle()
    rect.x = x
    rect.y = y
    rect.width = 2
    rect.height = 2
    
    return rect

# --------------------------------------------------- popover builder functions
def markers_menu_show(launcher, widget, callback):
    global _markers_popover, _markers_menu

    _markers_menu = menu_clear_or_create(_markers_menu)
    
    seq = current_sequence()
    markers_exist = len(seq.markers) != 0

    if markers_exist: 
        markers_section = Gio.Menu.new()
        for i in range(0, len(seq.markers)):
            marker = seq.markers[i]
            name, frame = marker
            item_str  = utils.get_tc_string(frame) + " " + name
                    
            add_menu_action(markers_section, item_str, "midbar.markers." + str(i), str(i), callback)

        _markers_menu.append_section(None, markers_section)

    actions_section = Gio.Menu.new()
    add_menu_action(actions_section, _("Add Marker"), "midbar.markers.addmarker", "add", callback)
    add_menu_action(actions_section, _("Delete Marker"), "midbar.markers.delete", "delete", callback)
    add_menu_action(actions_section, _("Delete All Markers"), "midbar.markers.deleteall", "deleteall", callback)
    add_menu_action(actions_section, _("Rename Marker"), "midbar.markers.rename", "rename", callback)
    _markers_menu.append_section(None, actions_section)

    _markers_popover = Gtk.Popover.new_from_model(widget, _markers_menu)
    launcher.connect_launched_menu(_markers_popover)
    _markers_popover.show()

def tline_properties_menu_show(launcher, widget, callback):
    global _tline_properties_popover, _tline_properties_menu

    _tline_properties_menu = menu_clear_or_create(_tline_properties_menu)

    display_section = Gio.Menu.new()
    add_menu_action_check(display_section, _("Display Clip Media Thumbnails"), "midbar.tlineproperties.thumb", editorstate.display_clip_media_thumbnails, "thumbs", callback)
    add_menu_action_check(display_section, _("Display Audio Levels"), "midbar.tlineproperties.all", editorstate.display_all_audio_levels, "all", callback)
    _tline_properties_menu.append_section(None, display_section)

    snapping_section = Gio.Menu.new()
    add_menu_action_check(snapping_section, _("Snapping On"), "midbar.tlineproperties.snapping", snapping.snapping_on, "snapping", callback)
    _tline_properties_menu.append_section(None, snapping_section)

    scrubbing_section = Gio.Menu.new()
    add_menu_action_check(scrubbing_section, _("Audio scrubbing"), "midbar.tlineproperties.scrubbing", editorpersistance.prefs.audio_scrubbing, "scrubbing", callback)
    _tline_properties_menu.append_section(None, scrubbing_section)

    _tline_properties_popover = Gtk.Popover.new_from_model(widget, _tline_properties_menu)
    launcher.connect_launched_menu(_tline_properties_popover)
    _tline_properties_popover.show()

def all_tracks_menu_show(launcher, widget, callback):
    global _all_tracks_popover, _all_tracks_menu

    _all_tracks_menu = menu_clear_or_create(_all_tracks_menu)

    maximize_section = Gio.Menu.new()
    add_menu_action(maximize_section, _("Maximize Tracks"), "midbar.all.alltracks", "max" , callback)
    add_menu_action(maximize_section, _("Maximize Video Tracks"), "midbar.all.videotracks", "maxvideo" , callback)
    add_menu_action(maximize_section, _("Maximize Audio Tracks"), "midbar.all.audiotracks", "maxaudio" , callback)
    _all_tracks_menu.append_section(None, maximize_section)

    minimize_section = Gio.Menu.new()
    add_menu_action(minimize_section, _("Minimize Tracks"), "midbar.all.minimize", "min" , callback)
    _all_tracks_menu.append_section(None, minimize_section)
    
    activate_section = Gio.Menu.new()
    add_menu_action(activate_section, _("Activate All Tracks"), "midbar.all.allactive", "allactive" , callback)
    add_menu_action(activate_section, _("Activate Only Current Top Active Track"), "midbar.all.topactiveonly", "topactiveonly" , callback)
    _all_tracks_menu.append_section(None, activate_section)

    expand_section = Gio.Menu.new()
    add_menu_action_check(expand_section, _("Expand Track on First Item Drop"), "midbar.tlineproperties.expand", editorpersistance.prefs.auto_expand_tracks, "autoexpand_on_drop", callback)
    add_menu_action_check(expand_section, _("Vertical Shrink Timeline"), "midbar.tlineproperties.shrink", PROJECT().get_project_property(appconsts.P_PROP_TLINE_SHRINK_VERTICAL), "shrink", callback)
    _all_tracks_menu.append_section(None, expand_section)

    _all_tracks_popover = Gtk.Popover.new_from_model(widget, _all_tracks_menu)
    launcher.connect_launched_menu(_all_tracks_popover)
    _all_tracks_popover.show()

def compositing_mode_menu_show(launcher, widget, callback):
    global _compositing_mode_popover, _compositing_mode_menu

    _compositing_mode_menu = menu_clear_or_create(_compositing_mode_menu)

    # Create menu, menuitems and variants 
    mode_section = Gio.Menu.new()
    item_id = "compositing.compmode"
    
    target_variant_topdown = GLib.Variant.new_string("topdown")
    add_menu_action_radio(mode_section, _("Compositors Free Move"), item_id, target_variant_topdown)
    target_variant_fulltrack = GLib.Variant.new_string("fulltrackauto")
    add_menu_action_radio(mode_section, _("Standard Full Track"), item_id, target_variant_fulltrack)

    # Create action and set state variant
    if current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        target_variant = target_variant_fulltrack
    else:
        target_variant = target_variant_topdown
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=GLib.VariantType.new("s"), state=target_variant)
    action.connect("activate", callback)
    APP().add_action(action)

    _compositing_mode_menu.append_section(None, mode_section)

    _compositing_mode_popover = Gtk.Popover.new_from_model(widget, _compositing_mode_menu)
    launcher.connect_launched_menu(_compositing_mode_popover)
    _compositing_mode_popover.show()

def media_panel_popover_show(widget, x, y, callback):
    global _media_panel_popover, _media_panel_menu

    _media_panel_menu = menu_clear_or_create(_media_panel_menu)

    section = Gio.Menu.new()
    add_menu_action(section, _("Add Video, Audio or Image..."), "mediapanel.addvideo",  "add media", callback)
    add_menu_action(section, _("Add Image Sequence..."), "mediapanel.addsequence", "add image sequence", callback)
    _media_panel_menu.append_section(None, section)
    
    rect = create_rect(x, y)

    _media_panel_popover = Gtk.Popover.new_from_model(widget, _media_panel_menu)
    _media_panel_popover.set_position(Gtk.PositionType(Gtk.PositionType.BOTTOM))
    _media_panel_popover.set_pointing_to(rect) 
    _media_panel_popover.show()

def sequence_panel_popover_show(widget, x, y, callback):
    global _sequecne_panel_popover, _sequence_panel_menu

    _sequence_panel_menu = menu_clear_or_create(_sequence_panel_menu)

    main_section = Gio.Menu.new()
    add_menu_action(main_section, _("Add New Sequence"), "sequencepanel.add", "add sequence", callback)
    add_menu_action(main_section, _("Edit Selected Sequence"), "sequencepanel.edit", "edit sequence", callback)
    add_menu_action(main_section, _("Delete Selected Sequence"), "sequencepanel.delete", "delete sequence", callback)
    _sequence_panel_menu.append_section(None, main_section)

    container_section = Gio.Menu.new()
    add_menu_action(container_section, _("Create Container Clip from Selected Sequence"), "sequencepanel.create", "compound clip", callback)
    _sequence_panel_menu.append_section(None, container_section)

    rect = create_rect(x, y)

    _sequecne_panel_popover = Gtk.Popover.new_from_model(widget, _sequence_panel_menu)
    _sequecne_panel_popover.set_position(Gtk.PositionType(Gtk.PositionType.BOTTOM))
    _sequecne_panel_popover.set_pointing_to(rect) 
    _sequecne_panel_popover.show()

def layout_menu_show(launcher, widget, callback):
    global _layout_popover, _layout_menu

    _layout_menu = menu_clear_or_create(_layout_menu)

    main_section = Gio.Menu.new()
    add_menu_action(main_section, _("Layout Monitor Left"), "layout.monitorleft",  "monitor_left", callback)
    add_menu_action(main_section, _("Layout Monitor Center"), "layout.monitorcenter",  "monitor_center", callback)
    if not(editorstate.SCREEN_WIDTH < 1919):
        add_menu_action(main_section, _("Layout Top Row 4 Panels"), "layout.fourpanels",  "top_row_four", callback)
    add_menu_action(main_section, _("Layout Media Panel Left Column"), "layout.medialeft",  "media_panel_left", callback)
    _layout_menu.append_section(None, main_section)

    save_section = Gio.Menu.new()
    add_menu_action(save_section, _("Save Current Layout..."), "layout.save",  "save_layout", callback)
    add_menu_action(save_section, _("Load Layout..."), "layout.load",  "load_layout", callback)
    _layout_menu.append_section(None, save_section)

    _layout_popover = new_popover(widget, _layout_menu, launcher)

def trim_view_popover_show(launcher, widget, callback):
    global _trimview_popover, _trimview_menu

    _trimview_menu = menu_clear_or_create(_trimview_menu)
    
    items_data =[(_("Trim View On"), "trimon"), (_("Trim View Single Side Edits Only"), "trimsingle"), \
                (_("Trim View Off"), "trimoff")]
    active_index = editorstate.show_trim_view
    
    radio_section = Gio.Menu.new()
    add_menu_action_all_items_radio(radio_section, items_data, "monitor.trimview", active_index, callback)
    _trimview_menu.append_section(None, radio_section)

    _trimview_popover = new_popover(widget, _trimview_menu, launcher)

def monitor_view_popupmenu_show(launcher, widget, callback, callback_opacity):
    global _monitorview_popover, _monitorview_menu, _opacity_section, _opacity_submenu

    _monitorview_menu = menu_clear_or_create(_monitorview_menu)
    
    items_data =[( _("Image"), "0"), (_("Vectorscope"), "1"), \
                ( _("RGB Parade"), "2")]
    active_index = editorstate.tline_view_mode
    
    view_section = Gio.Menu.new()
    add_menu_action_all_items_radio(view_section, items_data, "monitor.viewimage", active_index, callback)
    _monitorview_menu.append_section(None, view_section)

    # WE are getting gtk warning here, look to fix
    _opacity_section = menu_clear_or_create(_opacity_section)
    _opacity_submenu = menu_clear_or_create(_opacity_submenu)
    items_data = [( _("100%"), "3"), ( _("80%"), "4"), ( _("50%"), "5"), (_("20%"), "6")]
    active_index = current_sequence().get_mix_index()
    add_menu_action_all_items_radio(_opacity_submenu, items_data, "monitor.viewimageopcity", active_index, callback_opacity)
    _opacity_section.append_submenu(_("Overlay Opacity"), _opacity_submenu)
    _monitorview_menu.append_section(None, _opacity_section)
    
    _monitorview_popover = new_popover(widget, _monitorview_menu, launcher)

def bins_panel_widget_popover_show(launcher, widget, callback):
    global _bins_panel_widget_popover, _bins_panel_widget_menu

    if _bins_panel_widget_popover == None:
        _bins_panel_widget_menu = Gio.Menu.new()
        _build_bins_panel_menu(_bins_panel_widget_menu, callback)
        _bins_panel_widget_popover = new_popover(widget, _bins_panel_widget_menu, launcher)

    _bins_panel_widget_popover.show()

def bins_panel_mouse_popover_show(widget, x, y, callback):
    global _bins_panel_mouse_popover, _bins_panel_mouse_menu
    if _bins_panel_mouse_popover == None:
        _bins_panel_mouse_menu = Gio.Menu.new()
        _build_bins_panel_menu(_bins_panel_mouse_menu, callback)
        rect = create_rect(x, y)
        _bins_panel_mouse_popover = new_mouse_popover(widget, _bins_panel_mouse_menu, rect)
    else:
        _bins_panel_mouse_popover.show()
        
def _build_bins_panel_menu(menu, callback):
    
    add_section = Gio.Menu.new()
    add_menu_action(add_section, _("Add Bin"), "binspanel.add", "add bin", callback)
    add_menu_action(add_section, _("Delete Selected Bin"), "binspanel.edit", "delete bin", callback)
    menu.append_section(None, add_section)
    
    move_section = Gio.Menu.new()
    move_submenu = Gio.Menu.new()
    add_menu_action(move_submenu,_("Up"), "binspanel.up", "up bin", callback)
    add_menu_action(move_submenu,_("Down"), "binspanel.down", "down bin", callback)
    add_menu_action(move_submenu,_("First"), "binspanel.first", "first bin", callback)
    add_menu_action(move_submenu,_("Last"), "binspanel.last", "last bin", callback)

    move_section.append_submenu(_("Move Bin"), move_submenu)
    menu.append_section(None, move_section)
    
    return menu

# ----------------------------------- media files
def media_hamburger_popover_show(launcher, widget, callback):
    global _media_panel_hamburger_popover, _media_panel_hamburger_menu

    _media_panel_hamburger_menu = menu_clear_or_create(_media_panel_hamburger_menu)
    
    proxy_section = Gio.Menu.new()
    add_menu_action(proxy_section, _("Render Proxy Files For Selected Media"), "mediapanel.proxyrender", "render proxies", callback)
    add_menu_action(proxy_section, _("Render Proxy Files For All Media"), "mediapanel.proxyall", "render all proxies", callback)
    _media_panel_hamburger_menu.append_section(None, proxy_section)

    select_section = Gio.Menu.new()
    add_menu_action(select_section, _("Select All"), "mediapanel.selectall", "select all", callback)
    add_menu_action(select_section, _("Select None"), "mediapanel.selectnone",  "select none", callback)
    _media_panel_hamburger_menu.append_section(None, select_section)

    if len(PROJECT().bins) > 1:
        move_section = Gio.Menu.new()
        move_submenu = Gio.Menu.new()

        index = 0
        for media_bin in PROJECT().bins:
            if media_bin == PROJECT().c_bin:
                index = index + 1
                continue
            
            add_menu_action(move_submenu, str(media_bin.name), "mediapanel." + str(index), str(index), callback) 
            index = index + 1

        move_section.append_submenu(_("Move Selected Media To Bin"), move_submenu)
        _media_panel_hamburger_menu.append_section(None, move_section)

    append_section = Gio.Menu.new()
    add_menu_action(append_section, _("Append All Media to Timeline"), "mediapanel.appendall", "append all", callback)
    add_menu_action(append_section, _("Append Selected Media to Timeline"), "mediapanel.appendselected", "append selected", callback)
    _media_panel_hamburger_menu.append_section(None, append_section)

    _media_panel_hamburger_popover = new_popover(widget, _media_panel_hamburger_menu, launcher)

def columns_count_popupover_show(launcher, widget, callback):
    global _columns_popover, _columns_menu

    _columns_menu = menu_clear_or_create(_columns_menu)

    items_data =[(_("2 Columns"), "2"), (_("3 Columns"), "3"), \
                (_("4 Columns"), "4"), (_("5 Columns"), "5"), (_("6 Columns"), "6"), \
                (_("7 Columns"), "7")]
    active_index = gui.editor_window.media_list_view.columns - 2
    radio_section = Gio.Menu.new()
    add_menu_action_all_items_radio(radio_section, items_data, "mediapanel.columnview", active_index, callback)
    _columns_menu.append_section(None, radio_section)

    _columns_popover = new_popover(widget, _columns_menu, launcher)
    

def file_filter_popover_show(launcher, widget, callback):
    global _file_filter_popover, _file_filter_menu

    _file_filter_menu = menu_clear_or_create(_file_filter_menu)
    items_data =[( _("All Files"), "0"), (_("Video Files"), "1"), \
                ( _("Audio Files"), "2"), (_("Graphics Files"), "3"), ( _("Image Sequences"), "4"), \
                (_("Pattern Producers"), "6"), (_("Unused Files"), "7")]
                
    active_index = editorstate.media_view_filter
    radio_section = Gio.Menu.new()
    add_menu_action_all_items_radio(radio_section, items_data, "mediapanel.fileview", active_index, callback)
    _file_filter_menu.append_section(None, radio_section)

    _file_filter_popover = new_popover(widget, _file_filter_menu, launcher)

def media_file_popover_show(media_file, widget, x, y, callback):
    global _media_file_popover, _media_file_menu

    _media_file_menu = menu_clear_or_create(_media_file_menu)

    file_action_section = Gio.Menu.new()
    add_menu_action(file_action_section, _("Rename"), "mediapanel.mediafile.rename", ("Rename", media_file), callback)
    add_menu_action(file_action_section, _("Delete"), "mediapanel.mediafile.delete", ("Delete", media_file), callback)
    _media_file_menu.append_section(None, file_action_section)

    if hasattr(media_file, "container_data"): 
        if media_file.container_data == None:
            monitor_item_active = True
        else:
            monitor_item_active = False
    else:
            monitor_item_active = True

    if monitor_item_active == True:
        monitor_section = Gio.Menu.new()
        add_menu_action(monitor_section, _("Open in Clip Monitor"), "mediapanel.mediafile.clipmonitor", ("Open in Clip Monitor", media_file), callback)
        _media_file_menu.append_section(None, monitor_section)

    if media_file.type != appconsts.PATTERN_PRODUCER:
        properties_section = Gio.Menu.new()
        add_menu_action(properties_section, _("File Properties"), "mediapanel.mediafile.fileproperties", ("File Properties", media_file), callback)
        _media_file_menu.append_section(None, properties_section)

    if hasattr(media_file, "container_data") == True and media_file.container_data == None:
        if media_file.type != appconsts.PATTERN_PRODUCER and media_file.type != appconsts.AUDIO:
            icon_section = Gio.Menu.new()
            add_menu_action(icon_section, _("Recreate Icon"), "mediapanel.mediafile.icon", ("Recreate Icon", media_file), callback)
            _media_file_menu.append_section(None, icon_section)

    if media_file.type != appconsts.IMAGE and media_file.type != appconsts.AUDIO and media_file.type != appconsts.PATTERN_PRODUCER:
        render_section = Gio.Menu.new()
        if media_file.type != appconsts.IMAGE_SEQUENCE:
            add_menu_action(render_section, _("Render Slow/Fast Motion File"), "mediapanel.mediafile.slow", ("Render Slow/Fast Motion File", media_file), callback)
        if media_file.type != appconsts.IMAGE_SEQUENCE:
            add_menu_action(render_section, _("Render Reverse Motion File"), "mediapanel.mediafile.reverse", ("Render Reverse Motion File", media_file), callback)
        _media_file_menu.append_section(None, render_section)
            
    if media_file.type == appconsts.VIDEO or media_file.type == appconsts.IMAGE_SEQUENCE:
        proxy_section = Gio.Menu.new()
        add_menu_action(proxy_section, _("Render Proxy File"), "mediapanel.mediafile.proxy", ("Render Proxy File", media_file), callback)
        _media_file_menu.append_section(None, proxy_section)

    rect = create_rect(x, y)
    _media_file_popover = new_mouse_popover(widget, _media_file_menu, rect)


def jobs_menu_popover_show(launcher, widget, callback):
    global _jobs_popover, _jobs_menu

    _jobs_menu = menu_clear_or_create(_jobs_menu)

    cancel_section = Gio.Menu.new()
    add_menu_action(cancel_section, _("Cancel Selected Render"), "jobspanel.cancelselected", "cancel_selected", callback)
    add_menu_action(cancel_section, _("Cancel All Renders"), "jobspanel.cancelall",  "cancel_all", callback)
    _jobs_menu.append_section(None, cancel_section)

    options_section = Gio.Menu.new()
    add_menu_action_check(options_section, _("Show Jobs Panel on Adding New Job"), "jobspanel.showonadd", editorpersistance.prefs.open_jobs_panel_on_add, "open_on_add", callback)
    _jobs_menu.append_section(None, options_section)

    _jobs_popover = new_popover(widget, _jobs_menu, launcher)
