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
import translations
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
_effects_popover = None
_effects_menu = None
_plugin_popover = None
_plugin_menu = None
_compositor_hamburger_popover = None
_compositor_hamburger_menu = None
_range_log_popover = None
_range_log_menu = None
_sorting_section = None
_sorting_submenu = None
_move_section = None
_move_submenu = None
_tracks_column_popover = None
_tracks_column_menu = None
_media_linker_popover = None
_media_linker_menu = None
_log_event_popover = None
_log_event_menu = None
_filter_mask_popover = None
_filter_mask_menu = None
_filter_add_popover = None
_filter_add_menu = None
_kb_shortcuts_popover = None
_kb_shortcuts_menu = None
_render_args_popove = None
_render_args_menu = None
_kf_popover = None
_kf_menu = None
    
# -------------------------------------------------- menuitems builder fuctions
def add_menu_action(menu, label, item_id, data, callback, active=True, app=None):
    if active == True:
        menu.append(label, "app." + item_id) 
    else:
        menu.append(label, "noaction") 
    action = Gio.SimpleAction(name=item_id)
    action.connect("activate", callback, data)
    if app == None:
        APP().add_action(action)
    else:
        app.add_action(action)

    return action

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

def tline_properties_menu_show(launcher, widget, callback, mouse_zoom_callback):
    global _tline_properties_popover, _tline_properties_menu

    _tline_properties_menu = menu_clear_or_create(_tline_properties_menu)

    display_section = Gio.Menu.new()
    add_menu_action_check(display_section, _("Display Clip Media Thumbnails"), "midbar.tlineproperties.thumb", editorstate.display_clip_media_thumbnails, "thumbs", callback)
    add_menu_action_check(display_section, _("Display Audio Levels"), "midbar.tlineproperties.all", editorstate.display_all_audio_levels, "all", callback)
    _tline_properties_menu.append_section(None, display_section)

    zoom_section = Gio.Menu.new()
    items_data =[(_("Mouse Zoom To Playhead"), "zoomtoplayhead"), (_("Mouse Zoom To Cursor"), "zoomtomouse")]
    if editorpersistance.prefs.zoom_to_playhead == True:
        active_index = 0
    else:
        active_index = 1
    add_menu_action_all_items_radio(zoom_section, items_data, "midbar.tlineproperties.mousezoom", active_index, mouse_zoom_callback)
    _tline_properties_menu.append_section(None, zoom_section)

    snapping_section = Gio.Menu.new()
    add_menu_action_check(snapping_section, _("Snapping On"), "midbar.tlineproperties.snapping", snapping.snapping_on, "snapping", callback)
    _tline_properties_menu.append_section(None, snapping_section)
    
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

    add_delete_section = Gio.Menu.new()
    add_menu_action(add_delete_section, _("Add Video Track"), "midbar.all.addvideo", "addvideo" , callback)
    add_menu_action(add_delete_section, _("Add Audio Track"), "midbar.all.addaudio", "addaudio" , callback)
    add_menu_action(add_delete_section, _("Delete Video Track"), "midbar.all.deletevideo", "deletevideo" , callback)
    add_menu_action(add_delete_section, _("Delete Audio Track"), "midbar.all.deleteaudio", "deleteaudio" , callback)
    _all_tracks_menu.append_section(None, add_delete_section)

    maximize_section = Gio.Menu.new()
    add_menu_action(maximize_section, _("Maximize Tracks"), "midbar.all.alltracks", "max" , callback)
    add_menu_action(maximize_section, _("Maximize Video Tracks"), "midbar.all.videotracks", "maxvideo" , callback)
    add_menu_action(maximize_section, _("Maximize Audio Tracks"), "midbar.all.audiotracks", "maxaudio" , callback)
    add_menu_action(maximize_section, _("Minimize Tracks"), "midbar.all.minimize", "min" , callback)
    add_menu_action(maximize_section, _("Reset Track Heights"), "midbar.all.minimize", "resetheights" , callback)
    _all_tracks_menu.append_section(None, maximize_section)


    
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

    section2 = Gio.Menu.new()
    add_menu_action(section2, _("Add Generator..."), "mediapanel.addgenerator", "add generator", callback)
    add_menu_action(section2, _("Add Color Clip..."), "mediapanel.addcolorclip", "add color clip", callback)
    _media_panel_menu.append_section(None, section2)
    
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
    items_data = [( _("100%"), "3"), ( _("80%"), "4"), ( _("50%"), "5"), ( _("20%"), "6")]
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
                (_("Pattern Producers"), "5"), (_("Unused Files"), "6")]
                
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
            add_menu_action(icon_section, _("Replace Media In Project"), "mediapanel.mediafile.replace", ("Replace", media_file), callback)
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

def effects_editor_hamburger_popover_show(launcher, widget, callback):
    global _effects_popover, _effects_menu

    _effects_menu = menu_clear_or_create(_effects_menu)

    toggle_section = Gio.Menu.new()
    add_menu_action(toggle_section, _("Toggle All Effects On/Off"), "effectseditor.toggle", "toggle", callback)
    _effects_menu.append_section(None, toggle_section)

    expand_section = Gio.Menu.new()
    add_menu_action(expand_section, _("Expand All"), "effectseditor.expanded", "expanded", callback)
    add_menu_action(expand_section, _("Unexpand All"), "effectseditor.unexpanded", "unexpanded", callback)
    _effects_menu.append_section(None, expand_section)

    save_section = Gio.Menu.new()
    add_menu_action(save_section, _("Save Effect Stack"), "effectseditor.savestack", "save_stack", callback)
    add_menu_action(save_section, _("Load Effect Stack"), "effectseditor.loadstack", "load_stack", callback)
    _effects_menu.append_section(None, save_section)

    fade_section = Gio.Menu.new()
    add_menu_action(fade_section, _("Set Fade Buttons Default Fade Length..."), "effectseditor.fadelength", "fade_length", callback)
    _effects_menu.append_section(None, fade_section)

    close_section = Gio.Menu.new()
    add_menu_action(close_section, _("Close Editor"), "effectseditor.close", "close", callback)
    _effects_menu.append_section(None, close_section)

    _effects_popover = new_popover(widget, _effects_menu, launcher)

def plugin_editor_hamburger_popover_show(launcher, widget, callback):
    global _plugin_popover, _plugin_menu

    _plugin_menu = menu_clear_or_create(_plugin_menu)

    save_section = Gio.Menu.new()
    add_menu_action(save_section, _("Save and Apply Plugin Properties"), "mediaplugineditor.save", "save_properties", callback)
    add_menu_action(save_section, _("Load and Apply Plugin Properties"), "mediaplugineditor.load", "load_properties", callback)
    _plugin_menu.append_section(None, save_section)

    close_section = Gio.Menu.new()
    add_menu_action(close_section, _("Close Editor"), "mediaplugineditor.close", "close", callback)
    _plugin_menu.append_section(None, close_section)
    
    _plugin_popover = new_popover(widget, _plugin_menu, launcher)

def compositor_editor_hamburger_menu_show(launcher, widget, callback):
    global _compositor_hamburger_popover, _compositor_hamburger_menu

    _compositor_hamburger_menu = menu_clear_or_create(_compositor_hamburger_menu)

    save_section = Gio.Menu.new()
    add_menu_action(save_section, _("Save Compositor Values"), "compositoreditor.save", "save", callback)
    add_menu_action(save_section, _("Load Compositor Values"), "compositoreditor.load", "load", callback)
    add_menu_action(save_section, _("Reset Compositor Values"), "compositoreditor.reset", "reset", callback)
    _compositor_hamburger_menu.append_section(None, save_section)


    delete_section = Gio.Menu.new()
    add_menu_action(delete_section, _("Delete Compositor"), "compositoreditor.delete", "delete", callback)
    _compositor_hamburger_menu.append_section(None, delete_section)

    fade_section = Gio.Menu.new()
    add_menu_action(fade_section, _("Set Fade Buttons Default Fade Length..."), "compositoreditor.fade", "fade_length", callback)
    _compositor_hamburger_menu.append_section(None, fade_section)

    close_section = Gio.Menu.new()
    add_menu_action(close_section,_("Close Editor"), "compositoreditor.close", "close", callback)
    _compositor_hamburger_menu.append_section(None, close_section)

    _compositor_hamburger_popover = new_popover(widget, _compositor_hamburger_menu, launcher)


def  range_log_hamburger_menu_show(launcher, widget, unsensitive_for_all_view, sorting_order,\
                                   use_comments_for_name, media_log_groups, callback,\
                                   sorting_callback, use_comments_toggled):

    global _range_log_popover,  _range_log_menu

    _range_log_menu = menu_clear_or_create(_range_log_menu)

    new_section = Gio.Menu.new()
    add_menu_action(new_section, _("New Group..."), "rangelog.new", "new", callback)
    add_menu_action(new_section, _("New Group From Selected..."), "rangelog.newfromselected", "newfromselected", callback)
    _range_log_menu.append_section(None, new_section)

    rename_section = Gio.Menu.new()
    add_menu_action(rename_section, _("Rename Current Group..."),  "rangelog.rename", "rename", callback,  not(unsensitive_for_all_view))
    _range_log_menu.append_section(None, rename_section)

    if len(media_log_groups) > 0:
        global _move_section, _move_submenu
        _move_section = menu_clear_or_create(_move_section)
        _move_submenu = menu_clear_or_create(_move_submenu)
    
        index = 0
        items_data = []
        for group in media_log_groups:
            name, items = group
            add_menu_action(_move_submenu, name, "rangelog.move." + str(index), str(index), callback)
            index = index + 1

        _move_section.append_submenu(_("Move Selected Items To Group"), _move_submenu)
        _range_log_menu.append_section(None, _move_section)

    delete_section = Gio.Menu.new()
    add_menu_action(delete_section,_("Delete Current Group"),  "rangelog.delete", "delete", callback, not(unsensitive_for_all_view))
    _range_log_menu.append_section(None, delete_section)

    comments_section =  Gio.Menu.new()
    add_menu_action_check(comments_section, _("Use Comments as Clip Names"), "rangelog.usecomments", use_comments_for_name, "usecomments", use_comments_toggled)
    _range_log_menu.append_section(None, comments_section)

    global _sorting_section, _sorting_submenu
    _sorting_section = menu_clear_or_create(_sorting_section)
    _sorting_submenu = menu_clear_or_create(_sorting_submenu)
    items_data = [( _("Time"), "time"), ( _("File Name"), "name"), ( _("Comment"), "comment")]
    if sorting_order == appconsts.TIME_SORT:
        active_index = 0
    elif sorting_order == appconsts.NAME_SORT:
        active_index = 1
    else:# "comment"
        active_index = 2
    add_menu_action_all_items_radio(_sorting_submenu, items_data, "rangelog.sorting", active_index, sorting_callback)
    _sorting_section.append_submenu(_("Sort by"), _sorting_submenu)
    _range_log_menu.append_section(None, _sorting_section)
    
    _range_log_popover = new_popover(widget, _range_log_menu, launcher)

def tracks_popover_menu_show(track, widget, x, y, callback, callback_height):
    
    track_obj = current_sequence().tracks[track]
    
    global _tracks_column_popover, _tracks_column_menu
    _tracks_column_menu = menu_clear_or_create(_tracks_column_menu)
    
    lock_section = Gio.Menu.new()
    if track_obj.edit_freedom != appconsts.FREE:
        add_menu_action(lock_section, _("Lock Track"), "trackcolumn.lock", (track,"lock", None), callback, False)
        add_menu_action(lock_section, _("Unlock Track"), "trackcolumn.unlock", (track,"unlock", None), callback)
    else:
        add_menu_action(lock_section, _("Lock Track"), "trackcolumn.lock", (track, "lock", None), callback)
        add_menu_action(lock_section, _("Unlock Track"), "trackcolumn.unlock", (track,"unlock", None), callback, False)
    _tracks_column_menu.append_section(None, lock_section)

    height_section = Gio.Menu.new()
    items_data =[(_("High Height"), "highheight"), (_("Large Height"), "normalheight"), (_("Normal Height"), "smallheight")]
    if track_obj.height == appconsts.TRACK_HEIGHT_HIGH:
        active_index = 0
    elif track_obj.height == appconsts.TRACK_HEIGHT_NORMAL:
        active_index = 1
    else:
        active_index = 2
    add_menu_action_all_items_radio(height_section, items_data, "trackcolumn.height", active_index, callback_height)
    _tracks_column_menu.append_section(None, height_section)

    mute_section = Gio.Menu.new()
    # _state_different(track_obj, state) as last param sets 
    # menu item active if track not in given state
    if track_obj.type == appconsts.VIDEO:
        state = appconsts.TRACK_MUTE_NOTHING
        add_menu_action(mute_section, _("Unmute"), "trackcolumn.unmute", (track, "mute_track", state), callback, _state_different(track_obj, state)) 
    else:
        state = appconsts.TRACK_MUTE_VIDEO
        add_menu_action(mute_section, _("Unmute"), "trackcolumn.unmute", (track, "mute_track", state), callback, _state_different(track_obj, state))

    if track_obj.type == appconsts.VIDEO:
        state = appconsts.TRACK_MUTE_VIDEO
        add_menu_action(mute_section, _("Mute Video"), "trackcolumn.mutevideo", (track, "mute_track", state), callback, _state_different(track_obj, state))

    if track_obj.type == appconsts.VIDEO:
        state = appconsts.TRACK_MUTE_AUDIO
        add_menu_action(mute_section, _("Mute Audio"), "trackcolumn.muteaudio", (track, "mute_track", state), callback, _state_different(track_obj, state))
    else:
        state = appconsts.TRACK_MUTE_ALL
        add_menu_action(mute_section, _("Mute Audio"), "trackcolumn.muteaudio", (track, "mute_track", state), callback, _state_different(track_obj, state))

    if track_obj.type == appconsts.VIDEO:
        state = appconsts.TRACK_MUTE_ALL
        add_menu_action(mute_section, _("Mute All"), "trackcolumn.muteall", (track, "mute_track", state), callback, _state_different(track_obj, state))

    _tracks_column_menu.append_section(None, mute_section)

    rect = create_rect(x, y)
    
    _tracks_column_popover = Gtk.Popover.new_from_model(widget, _tracks_column_menu)
    _tracks_column_popover.set_pointing_to(rect) 
    _tracks_column_popover.show()

def _state_different(mutable, state):
    if mutable.mute_state == state:
        return False
    else:
        return True

def media_linker_popover_show(app, row, widget, x, y, callback):

    global _media_linker_popover, _media_linker_menu
    _media_linker_menu = menu_clear_or_create(_media_linker_menu)

    file_section = Gio.Menu.new()
    add_menu_action(file_section, _("Set File Relink Path"), "medialink.relink", ("set relink", row), callback, True, app)
    add_menu_action(file_section, _("Delete File Relink Path"), "medialink.delete", ("delete relink", row), callback, True, app)
    add_menu_action(file_section, _("Create Placeholder File"), "medialink.placeholder", ("create placeholder", row), callback, True, app)
    _media_linker_menu.append_section(None, file_section)

    show_section = Gio.Menu.new()
    add_menu_action(show_section, _("Show Full Paths"), "medialink.showfull", ("show path", row), callback, True, app)
    _media_linker_menu.append_section(None, show_section)

    rect = create_rect(x, y + 24)
    
    _media_linker_popover = Gtk.Popover.new_from_model(widget, _media_linker_menu)
    _media_linker_popover.set_pointing_to(rect) 
    _media_linker_popover.show()

def media_log_event_popover_show(row, widget, x, y, callback):
    global _log_event_popover, _log_event_menu
    _log_event_menu = menu_clear_or_create(_log_event_menu)

    main_section = Gio.Menu.new()
    add_menu_action(main_section, _("Display In Clip Monitor"), "logevent.display", ("display", row, widget), callback)
    add_menu_action(main_section, _("Render Slow/Fast Motion File"), "logevent.renderslowmo", ("renderslowmo", row, widget), callback)
    add_menu_action(main_section, _("Toggle Star"), "logevent.toggle", ("toggle", row, widget), callback)
    add_menu_action(main_section, _("Delete"), "logevent.delete", ("delete", row, widget), callback)
    _log_event_menu.append_section(None, main_section)

    rect = create_rect(x, y + 24) # +24 because there seems to be bug if column titles preset.

    _log_event_popover = Gtk.Popover.new_from_model(widget, _log_event_menu)
    _log_event_popover.set_pointing_to(rect) 
    _log_event_popover.show()

def _add_filter_mask_submenu_items(sub_menu, filter_index, filter_names, filter_msgs, data_bool, callback):
    for f_name, f_msg in zip(filter_names, filter_msgs):
        #sub_menu.add(_get_menu_item("\u21c9" + " " + f_name, callback, (False, f_msg, filter_index)))
        
        label = "\u21c9" + " " + f_name
        item_id = f_name.lower().replace(" ", "_") + str(data_bool)
        data = (data_bool, f_msg, filter_index)
        add_menu_action(sub_menu, label, item_id, data, callback)
        
def filter_mask_popover_show(launcher, widget, callback, filter_names, filter_msgs, filter_index):
    global _filter_mask_popover, _filter_mask_menu
    _filter_mask_menu = menu_clear_or_create(_filter_mask_menu)

    main_section = Gio.Menu.new()
    add_selected_sub_menu = Gio.Menu.new()
    main_section.append_submenu(_("Add Filter Mask on Selected Filter"), add_selected_sub_menu)
    _add_filter_mask_submenu_items(add_selected_sub_menu, filter_index, filter_names, filter_msgs, False, callback)

    add_selected_sub_menu = Gio.Menu.new()
    main_section.append_submenu(_("Add Filter Mask on All Filters"), add_selected_sub_menu)
    _add_filter_mask_submenu_items(add_selected_sub_menu, filter_index, filter_names, filter_msgs, True, callback)

    _filter_mask_menu.append_section(None, main_section)
    _filter_mask_popover = new_popover(widget, _filter_mask_menu, launcher)

def filter_add_popover_show(launcher, widget, clip, track, x, mltfiltersgroups, callback):

    global _filter_add_popover, _filter_add_menu
    _filter_add_menu = menu_clear_or_create(_filter_add_menu)

    item_id = "add_filter"
    for group in mltfiltersgroups:
        group_name, filters_array = group

        # "Blend" group only when in compositing_mode COMPOSITING_MODE_STANDARD_FULL_TRACK.
        if filters_array[0].mlt_service_id == "cairoblend_mode" and current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
            continue
            
        sub_menu = Gio.Menu.new()
        _filter_add_menu.append_submenu(group_name, sub_menu)

        for filter_info in filters_array:
            filter_name = translations.get_filter_name(filter_info.name)
            item_id = filter_name.lower().replace(" ", "_")
            sub_menu.append(filter_name, "app." + item_id)         
    
            data = (clip, track, item_id, (x, filter_info))
                
            action = Gio.SimpleAction(name=item_id)
            action.connect("activate", callback, data)
            APP().add_action(action)
    
    _filter_add_popover = Gtk.Popover.new_from_model(widget, _filter_add_menu)
    launcher.connect_launched_menu(_filter_add_popover)
    _filter_add_popover.show()

def kb_shortcuts_popover_show(launcher, widget, data, callback):
    global _kb_shortcuts_popover, _kb_shortcuts_menu

    _kb_shortcuts_menu = menu_clear_or_create(_kb_shortcuts_menu)
    
    shortcuts_combo, dialog = data

    if shortcuts_combo.get_active() < 2:
        delete_active = False
    else:
        delete_active = True

    main_section = Gio.Menu.new()
    add_menu_action(main_section, _("Add Custom Shortcuts Group"), "kbdialog.addgroup", ("add", data), callback)
    add_menu_action(main_section, _("Delete Active Custom Shortcuts Group"), "kbdialog.deletegroup", ("delete", data), callback)
    _kb_shortcuts_menu.append_section(None, main_section)

    _kb_shortcuts_popover = new_popover(widget, _kb_shortcuts_menu, launcher)

def render_args_popover_show(launcher, widget, callback):
    global _render_args_popover, _render_args_menu

    _render_args_menu = menu_clear_or_create(_render_args_menu)

    main_section = Gio.Menu.new()
    add_menu_action(main_section, _("Load Render Args from a text file"), "renderargs.loadfromfile", "load_from_file", callback)
    add_menu_action(main_section, _("Save Render Args into a text file"), "renderargs.savetofile", "save_to_from_file", callback)
    add_menu_action(main_section, _("Load Render Args from Current Encoding"), "renderargs.loadselection", "load_from_selection", callback)
    _render_args_menu.append_section(None, main_section)

    reset_section = Gio.Menu.new()
    add_menu_action(reset_section,_("Reset all Render Options to Defaults"), "renderargs.reset", "reset_all", callback)
    _render_args_menu.append_section(None, reset_section)
    
    _render_args_popover = new_popover(widget, _render_args_menu, launcher)
