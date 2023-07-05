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
import guicomponents
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

# -------------------------------------------------- menuitems builder fuctions
def add_menu_action(menu, label, item_id, msg_str, callback):
    menu.append(label, "app." + item_id) 
    
    action = Gio.SimpleAction(name=item_id)
    action.connect("activate", callback, msg_str)
    APP().add_action(action)

def add_menu_action_check(menu, label, item_id, checked_state, msg_str, callback):
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=None, state=GLib.Variant.new_boolean(checked_state))
    action.connect("activate", callback, msg_str)
    APP().add_action(action)

    menu_item = Gio.MenuItem.new(label,  "app." + item_id)
    menu_item.set_action_and_target_value("app." + item_id, None)
    menu.append_item(menu_item)

def add_menu_action_radio(menu, label, item_id, target_variant):
    #target_variant = GLib.Variant.new_string(value_str)
    #action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=GLib.VariantType.new("s"), state=target_variant)
    #action.connect("activate", callback, msg_str)
    #APP().add_action(action)

    menu_item = Gio.MenuItem.new(label, "app." + item_id)
    menu_item.set_action_and_target_value("app." + item_id, target_variant)
    menu.append_item(menu_item)


# --------------------------------------------------- popover builder functions
def markers_menu_launcher(callback, pixbuf, w=22, h=22):
    launch = guicomponents.PressLaunchPopover(callback, pixbuf, w, h)
    return launch

def markers_menu_show(launcher, widget, callback):
    global _markers_popover, _markers_menu

    if _markers_menu != None:
        _markers_menu.remove_all()
    else:
        _markers_menu = Gio.Menu.new()
    
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

    if _tline_properties_menu != None:
        _tline_properties_menu.remove_all()
    else:
        _tline_properties_menu = Gio.Menu.new()

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

    if _all_tracks_menu != None:
        _all_tracks_menu.remove_all()
    else:
        _all_tracks_menu = Gio.Menu.new()

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

    if _compositing_mode_menu != None:
        _compositing_mode_menu.remove_all()
    else:
        _compositing_mode_menu = Gio.Menu.new()

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

    if _media_panel_menu != None:
        _media_panel_menu.remove_all()
    else:
        _media_panel_menu = Gio.Menu.new()

    section = Gio.Menu.new()
    add_menu_action(section, _("Add Video, Audio or Image..."), "mediapanel.addvideo",  "add media", callback)
    add_menu_action(section, _("Add Image Sequence..."), "mediapanel.addsequence", "add image sequence", callback)
    _media_panel_menu.append_section(None, section)
    
    rect = Gdk.Rectangle()
    rect.x = x
    rect.y = y
    rect.width = 2
    rect.height = 2
    
    _media_panel_popover = Gtk.Popover.new_from_model(widget, _media_panel_menu)
    _media_panel_popover.set_pointing_to(rect) 
    _media_panel_popover.show()

