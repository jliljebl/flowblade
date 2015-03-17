"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles track actions; mute, active state, size change.
"""

import appconsts
import dialogutils
import gui
import guicomponents
import editorstate
from editorstate import get_track
from editorstate import current_sequence
import tlinewidgets
import updater

# --------------------------------------- menu events
def _track_menu_item_activated(widget, data):
    track, item_id, selection_data = data
    handler = POPUP_HANDLERS[item_id]
    if selection_data == None:
        handler(track)
    else:
        handler(track, selection_data)
        
def lock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.LOCKED
    updater.repaint_tline()

def unlock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.FREE
    updater.repaint_tline()

def set_track_normal_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_NORMAL
    
    # Check that new height tracks can be displayed and cancel if not.
    new_h = current_sequence().get_tracks_height()
    x, y, w, h = gui.tline_canvas.widget.allocation
    if new_h > h:
        track.height = appconsts.TRACK_HEIGHT_SMALL
        dialogutils.warning_message(_("Not enough vertical space on Timeline to expand track"), 
                                _("Maximize or resize application window to get more\nspace for tracks if possible."),
                                gui.editor_window.window,
                                True)
        return

    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)
    gui.tline_column.init_listeners()
    updater.repaint_tline()

def set_track_small_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_SMALL
    if editorstate.SCREEN_HEIGHT < 863:
        track.height = appconsts.TRACK_HEIGHT_SMALLEST
    
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)
    gui.tline_column.init_listeners()
    updater.repaint_tline()
    
def mute_track(track, new_mute_state):
    # NOTE: THIS IS A SAVED EDIT OF SEQUENCE, BUT IS NOT AN UNDOABLE EDIT
    current_sequence().set_track_mute_state(track.id, new_mute_state)
    gui.tline_column.widget.queue_draw()
    
def all_tracks_menu_launch_pressed(widget, event):
    guicomponents.get_all_tracks_popup_menu(event, _all_tracks_item_activated)

def _all_tracks_item_activated(widget, msg):
    if msg == "min":
        current_sequence().minimize_tracks_height()
        _tracks_resize_update()
    
    if msg == "max":
        current_sequence().maximize_tracks_height(gui.tline_canvas.widget.allocation)
        _tracks_resize_update()
    
    if msg == "maxvideo":
        current_sequence().maximize_video_tracks_height(gui.tline_canvas.widget.allocation)
        _tracks_resize_update()

    if msg == "maxaudio":
        current_sequence().maximize_audio_tracks_height(gui.tline_canvas.widget.allocation)
        _tracks_resize_update()

def _tracks_resize_update():
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)
    gui.tline_column.init_listeners()
    updater.repaint_tline()
    gui.tline_column.widget.queue_draw()

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
        guicomponents.display_tracks_popup_menu(data.event, data.track, \
                                                _track_menu_item_activated)

def track_center_pressed(data):
    if data.event.button == 1:
        # handle possible mute icon presses
        press_x = data.event.x
        press_y = data.event.y
        track = tlinewidgets.get_track(press_y)
        if track == None:
            return
        y_off = press_y - tlinewidgets._get_track_y(track.id)
        ICON_WIDTH = 12
        if press_x > tlinewidgets.COLUMN_LEFT_PAD and press_x < tlinewidgets.COLUMN_LEFT_PAD + ICON_WIDTH:
            # Mute icon x area hit
            ix, iy = tlinewidgets.MUTE_ICON_POS
            if track.height > appconsts.TRACK_HEIGHT_SMALL:
                ix, iy = tlinewidgets.MUTE_ICON_POS_NORMAL
            ICON_HEIGHT = 10
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
            gui.tline_column.widget.queue_draw()
    
    if data.event.button == 3:
        guicomponents.display_tracks_popup_menu(data.event, data.track, \
                                                _track_menu_item_activated)

POPUP_HANDLERS = {"lock":lock_track,
                  "unlock":unlock_track,
                  "normal_height":set_track_normal_height,
                  "small_height":set_track_small_height,
                  "mute_track":mute_track}
