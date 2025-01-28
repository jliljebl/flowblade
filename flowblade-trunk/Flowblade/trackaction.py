"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

"""
This module handles track actions; mute, change active state, size change.
"""

from gi.repository import GLib

import appconsts
import audiomonitoring
import gui
import guipopover
import editorstate
import editorpersistance
from editorstate import get_track
from editorstate import current_sequence
from editorstate import PROJECT
from editorstate import PLAYER
import movemodes
import projectaction
import snapping
import syncsplitevent
import tlinewidgets
import updater


_menu_track_index = None
        
# --------------------------------------- menu events
def _track_menu_item_activated(widget, action, data):
    track, item_id, selection_data = data
    handler = POPUP_HANDLERS[item_id]
    if selection_data == None:
        handler(track)
    else:
        handler(track, selection_data)

def _track_menu_height_activated(action, variant):
    if variant.get_string() == "highheight":
        set_track_high_height(_menu_track_index)
    elif variant.get_string() == "normalheight":
        set_track_normal_height(_menu_track_index)
    else:
        set_track_small_height(_menu_track_index)
        
    action.set_state(variant)
    editorpersistance.save()
    guipopover._tracks_column_popover.hide()
    
def lock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.LOCKED
    updater.repaint_tline()

def unlock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.FREE
    updater.repaint_tline()


def set_track_sync(track_index):
    child_track = get_track(track_index)
    syncsplitevent.set_track_clips_sync(child_track)

def reset_treack_sync(track_index):
    child_track = get_track(track_index)
    parent_track = child_track.parent_track
    syncsplitevent.do_set_track_clips_sync(child_track, parent_track)

def clear_track_sync(track_index):
    track = get_track(track_index)
    if len(track.clips) == 0:
        return

    syncsplitevent.clear_track_clips_sync(track)

def resync_track(track_index):
    track = get_track(track_index)
    if len(track.clips) == 0:
        return

    syncsplitevent.resync_selected_track(track)

def toggle_track_output():
    if movemodes.selected_track == -1:
        return
    
    track = current_sequence().tracks[movemodes.selected_track]
    
    if movemodes.selected_track >= current_sequence().first_video_index:
        # Video tracks
        if track.mute_state != appconsts.TRACK_MUTE_ALL:
            new_mute_state = appconsts.TRACK_MUTE_ALL
        else:
            new_mute_state = appconsts.TRACK_MUTE_NOTHING
    else:
        # Audio tracks
        if track.mute_state == appconsts.TRACK_MUTE_ALL:
            new_mute_state = appconsts.TRACK_MUTE_VIDEO
        else:
            new_mute_state = appconsts.TRACK_MUTE_ALL

    # Update track mute state
    current_sequence().set_track_mute_state(movemodes.selected_track, new_mute_state)
    
    audiomonitoring.update_mute_states()
    gui.tline_column.widget.queue_draw()
            
def set_track_high_height(track_index, is_retry=False):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_HIGH

    # Check that new height tracks can be displayed and cancel if not.
    new_h = current_sequence().get_tracks_height()
    allocation = gui.tline_canvas.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height

    if new_h > h and is_retry == False:
        current_paned_pos = gui.editor_window.app_v_paned.get_position()
        new_paned_pos = current_paned_pos - (new_h - h) - 5
        gui.editor_window.app_v_paned.set_position(new_paned_pos)
        GLib.timeout_add(200, lambda: set_track_high_height(track_index, True))
        return False
    
    allocation = gui.tline_canvas.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height
    
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.get_allocation())
    gui.tline_column.init_listeners()
    updater.repaint_tline()

    return False

def set_track_normal_height(track_index, is_retry=False, is_auto_expand=False):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_NORMAL

    # Check that new height tracks can be displayed and cancel if not.
    new_h = current_sequence().get_tracks_height()
    allocation = gui.tline_canvas.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height

    if new_h > h and is_retry == False:
        current_paned_pos = gui.editor_window.app_v_paned.get_position()
        new_paned_pos = current_paned_pos - (new_h - h) - 5
        gui.editor_window.app_v_paned.set_position(new_paned_pos)
        GLib.timeout_add(200, lambda: set_track_normal_height(track_index, True, is_auto_expand))
        return False
    
    allocation = gui.tline_canvas.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height

    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.get_allocation())
    gui.tline_column.init_listeners()
    updater.repaint_tline()

    return False

def set_track_small_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_SMALL
    if editorstate.SCREEN_HEIGHT < 863:
        track.height = appconsts.TRACK_HEIGHT_SMALLEST
    
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.get_allocation())
    gui.tline_column.init_listeners()
    updater.repaint_tline()

def maybe_do_auto_expand(tracks_clips_count_before_exit):
    initial_drop_track_index = current_sequence().get_inital_drop_target_track(tracks_clips_count_before_exit)
    if initial_drop_track_index == None or editorpersistance.prefs.auto_expand_tracks == False:
        return

    if current_sequence().tracks[initial_drop_track_index].height == appconsts.TRACK_HEIGHT_SMALL:
        GLib.timeout_add(50, lambda: _do_auto_expand(initial_drop_track_index))

def _do_auto_expand(initial_drop_track_index):
    set_track_normal_height(initial_drop_track_index, is_retry=False, is_auto_expand=True)
    
def mute_track(track, new_mute_state):
    # NOTE: THIS IS A SAVED EDIT OF SEQUENCE, BUT IT IS NOT AN UNDOABLE EDIT.
    current_sequence().set_track_mute_state(track, new_mute_state)
    gui.tline_column.widget.queue_draw()
    
def all_tracks_menu_launch_pressed(launcher, widget, event):
    guipopover.all_tracks_menu_show(launcher, widget, _all_tracks_item_activated)

def _all_tracks_item_activated(action, variant, msg):
    if msg == "addvideo":
        projectaction.add_video_track()
        return

    if msg == "addaudio":
        projectaction.add_audio_track()
        return
        
    if msg == "deletevideo":
        projectaction.delete_video_track()
        return
        
    if msg == "deleteaudio":
        projectaction.delete_audio_track()
        return
    
    if msg == "resetheights":
        current_sequence().minimize_tracks_height()
        current_sequence().tracks[current_sequence().first_video_index].height = appconsts.TRACK_HEIGHT_NORMAL
        _tracks_resize_update()

    if msg == "min":
        current_sequence().minimize_tracks_height()
        _tracks_resize_update()
    
    if msg == "max":
        current_sequence().maximize_tracks_height(gui.tline_canvas.widget.get_allocation())
        _tracks_resize_update()
    
    if msg == "maxvideo":
        current_sequence().maximize_video_tracks_height(gui.tline_canvas.widget.get_allocation())
        _tracks_resize_update()

    if msg == "maxaudio":
        current_sequence().maximize_audio_tracks_height(gui.tline_canvas.widget.get_allocation())
        _tracks_resize_update()

    if msg == "allactive":
        _activate_all_tracks()

    if msg == "topactiveonly":
        _activate_only_current_top_active()
    
    if msg == "shrink":
        new_state = not(action.get_state().get_boolean())
        _tline_vertical_shrink_changed(new_state)
        action.set_state(GLib.Variant.new_boolean(new_state))
            
    if msg == "autoexpand_on_drop":
        new_state = not(action.get_state().get_boolean())
        editorpersistance.prefs.auto_expand_tracks = new_state
        editorpersistance.save()
        action.set_state(GLib.Variant.new_boolean(new_state))
        
def _tracks_resize_update():
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.get_allocation())
    gui.tline_column.init_listeners()
    updater.repaint_tline()
    gui.tline_column.widget.queue_draw()

def _tline_vertical_shrink_changed(do_shrink):
    PROJECT().project_properties[appconsts.P_PROP_TLINE_SHRINK_VERTICAL] = do_shrink
    updater.set_timeline_height()

def _activate_all_tracks():
    for i in range(0, len(current_sequence().tracks) - 1):
        current_sequence().tracks[i].active = True

    gui.tline_column.widget.queue_draw()
    
def _activate_only_current_top_active():
    for i in range(0, len(current_sequence().tracks) - 1):
        if i == current_sequence().get_first_active_track().id:
            current_sequence().tracks[i].active = True
        else:
            current_sequence().tracks[i].active = False

    gui.tline_column.widget.queue_draw()
    
def tline_properties_menu_launch_pressed(launcher, widget, event):
    guipopover.tline_properties_menu_show(launcher, widget, _tline_properties_item_activated, _tline_mouse_zoom_selected)

def _tline_properties_item_activated(action, event, msg):
    new_state = not(action.get_state().get_boolean())
    
    if msg == "all":
        editorstate.display_all_audio_levels = new_state
        updater.repaint_tline()
    elif msg == "snapping":
        snapping.snapping_on = new_state
    elif msg == "scrubbing":
        editorpersistance.prefs.audio_scrubbing = new_state
        editorpersistance.save()
        PLAYER().set_scrubbing(new_state)
    else: # media thumbnails
        editorstate.display_clip_media_thumbnails = new_state
        updater.repaint_tline()

    action.set_state(GLib.Variant.new_boolean(new_state))

def _tline_mouse_zoom_selected(action, variant):
    if variant.get_string() == "zoomtoplayhead":
        editorpersistance.prefs.zoom_to_playhead = True
    else:
        editorpersistance.prefs.zoom_to_playhead = False

    action.set_state(variant)
    editorpersistance.save()
    guipopover._tline_properties_popover.hide()
    
# ------------------------------------------------------------- mouse events
def track_active_switch_pressed(data):
    track = get_track(data.track) # data.track is index, not object

    # Flip active state
    if data.event.button == 1:
        track.active = (track.active == False)
        if current_sequence().all_tracks_off() == True:
            track.active = True
        gui.tline_column.widget.queue_draw()
    elif data.event.button == 3:
        global _menu_track_index # popover + gio.actions just wont allow easily packing track to go, so we're going global
        _menu_track_index = data.track
        guipopover.tracks_popover_menu_show(data.track, gui.tline_column.widget, \
                                            data.event.x, data.event.y, \
                                            _track_menu_item_activated,
                                            _track_menu_height_activated)

def track_double_click(track_id):
    track = get_track(track_id) # data.track is index, not object
    if track.height == appconsts.TRACK_HEIGHT_HIGH:
        set_track_small_height(track_id)
    elif track.height == appconsts.TRACK_HEIGHT_NORMAL:
        set_track_high_height(track_id)
    elif track.height == appconsts.TRACK_HEIGHT_SMALL:
        set_track_normal_height(track_id)
    
def track_center_pressed(data):
    if data.event.button == 1:
        # handle possible mute icon presses
        press_x = data.event.x
        press_y = data.event.y
        track = tlinewidgets.get_track(press_y)
        if track == None:
            return
        y_off = press_y - tlinewidgets._get_track_y(track.id)
        ICON_WIDTH = 14
        ICON_HEIGHT = 10

        X_CORR_OFF = 4 # icon edge not on image left edge
        if press_x > tlinewidgets.COLUMN_LEFT_PAD + X_CORR_OFF and press_x < tlinewidgets.COLUMN_LEFT_PAD + ICON_WIDTH + X_CORR_OFF:
            # Mute icon x area hit
            ix, iy = tlinewidgets.MUTE_ICON_POS
            if track.height == appconsts.TRACK_HEIGHT_HIGH:
                ix, iy = tlinewidgets.MUTE_ICON_POS_HIGH
            elif track.height == appconsts.TRACK_HEIGHT_NORMAL: 
                ix, iy = tlinewidgets.MUTE_ICON_POS_NORMAL

            if track.id >= current_sequence().first_video_index:
                # Video tracks
                # Test mute switches
                if y_off > iy and y_off < iy + ICON_HEIGHT:
                    # Video mute icon hit
                    if track.mute_state == appconsts.TRACK_MUTE_NOTHING:
                        new_mute_state = appconsts.TRACK_MUTE_VIDEO
                    elif track.mute_state == appconsts.TRACK_MUTE_VIDEO:
                        new_mute_state = appconsts.TRACK_MUTE_NOTHING
                    elif track.mute_state == appconsts.TRACK_MUTE_AUDIO:
                        new_mute_state = appconsts.TRACK_MUTE_ALL
                    elif track.mute_state == appconsts.TRACK_MUTE_ALL:
                        new_mute_state = appconsts.TRACK_MUTE_AUDIO
                elif y_off > iy + ICON_HEIGHT and y_off < iy + ICON_HEIGHT * 2:
                    # Audio mute icon hit
                    if track.mute_state == appconsts.TRACK_MUTE_NOTHING:
                        new_mute_state = appconsts.TRACK_MUTE_AUDIO
                    elif track.mute_state == appconsts.TRACK_MUTE_VIDEO:
                        new_mute_state = appconsts.TRACK_MUTE_ALL
                    elif track.mute_state == appconsts.TRACK_MUTE_AUDIO:
                        new_mute_state = appconsts.TRACK_MUTE_NOTHING
                    elif track.mute_state == appconsts.TRACK_MUTE_ALL:
                        new_mute_state = appconsts.TRACK_MUTE_VIDEO
                else:
                    return
            else:
                # Audio tracks
                # Test mute switches
                iy = iy + 6 # Mute icon is lower on audio tracks
                if y_off > iy and y_off < iy + ICON_HEIGHT:
                    if track.mute_state == appconsts.TRACK_MUTE_VIDEO:
                        new_mute_state = appconsts.TRACK_MUTE_ALL
                    else:
                        new_mute_state = appconsts.TRACK_MUTE_VIDEO
                else:
                    return 
            # Update track mute state
            current_sequence().set_track_mute_state(track.id, new_mute_state)
            
            audiomonitoring.update_mute_states()
            gui.tline_column.widget.queue_draw()
    
    if data.event.button == 3:
        global _menu_track_index # popover + gio.actions just wont allow easily packing track to go, so we're going global
        _menu_track_index = data.track
        guipopover.tracks_popover_menu_show(data.track, gui.tline_column.widget, \
                                            data.event.x, data.event.y, \
                                            _track_menu_item_activated,
                                            _track_menu_height_activated)

POPUP_HANDLERS = {"lock":lock_track,
                  "unlock":unlock_track,
                  "mute_track":mute_track,
                  "clearsync":clear_track_sync,
                  "resync":resync_track,
                  "setsync":set_track_sync,
                  "ressetsync":reset_treack_sync}
