"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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

"""
Module handles Keyframe tool functionality
"""

import cairo

from editorstate import current_sequence
import respaths
import tlinewidgets
import updater

CLOSE_ICON = None
HAMBURGER_ICON = None

OVERLAY_BG = (0.0, 0.0, 0.0, 0.8)
OVERLAY_DRAW_COLOR = (0.0, 0.0, 0.0, 0.8)
EDIT_AREA_HEIGHT = 200

edit_data = None

# -------------------------------------------------- init
def load_icons():
    global CLOSE_ICON, HAMBURGER_ICON
    CLOSE_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "close_match.png")
    HAMBURGER_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger.png")


# ---------------------------------------------- mouse events
def mouse_press(event, frame):

    x = event.x
    y = event.y

    # If we have clip being edited and its edit area is hit, we do not need to init data.
    if _clip_is_being_edited() and _clip_edit_area_hit(x, y):
        return
    
    # Get pressed track
    track = tlinewidgets.get_track(y)  

    # Selecting empty clears selection
    if track == None:
        #clear_selected_clips()
        #pressed_on_selected = False
        _set_no_clip_edit_data()
        updater.repaint_tline()
        return    
    
    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty clears selection
    if clip_index == -1:
        #clear_selected_clips()
        #pressed_on_selected = False
        _set_no_clip_edit_data()
        updater.repaint_tline()
        return

    clip = track.clips[clip_index]
    
    # Save data needed to do the keyframe edits.
    global edit_data #, pressed_on_selected, drag_disabled
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":clip_index,
                 "clip":clip,
                 "track":track,
                 "mouse_start_x":x,
                 "mouse_start_y":y}


    # Init for volume editing if volume filter available
    for i in range(0, len(clip.filters)):
        filter_object = clip.filters[i]
        if filter_object.info.mlt_service_id == "volume":
            editable_properties = propertyedit.get_filter_editable_properties(
                                                           clip, 
                                                           filter_object,
                                                           i,
                                                           track,
                                                           clip_index)
            for ep in editable_properties:
                if ep.name == "gain":
                    _init_for_editable_property(ep)
            
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
        
def mouse_move(x, y, frame, state):
    pass
    
def mouse_release(x, y, frame, state):
    #global edit_data#, pressed_on_selected, drag_disabled
    #edit_data = None
    pass

# -------------------------------------------- edit 
def _clip_is_being_edited():
    if edit_data == None:
        return False
    if edit_data["clip_index"] == -1:
        return False
    
    return True

def _clip_edit_area_hit(x, y):
    return False

def _set_no_clip_edit_data():
    # set edit data to reflect that no clip is being edited currently.
    global edit_data 
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":-1,
                 "track":None,
                 "mouse_start_x":-1,
                 "mouse_start_y":-1}

    tlinewidgets.set_edit_mode_data(edit_data)


def _init_for_editable_property(editable_property):
    edit_data["editable_property"] = editable_property
    adjustment = editable_property.get_input_range_adjustment()
    edit_data["lower"] = adjustment.get_lower()
    edit_data["upper"] = adjustment.get_upper ()
    
    
# ----------------------------------------------------------------------- draw
def _tline_overlay(cr, pos):
    if _clip_is_being_edited() == False:
        return
        
    track = edit_data["track"]
    ty = tlinewidgets._get_track_y(track.id)
    cx_start = tlinewidgets._get_frame_x(track.clip_start(edit_data["clip_index"]))
    clip = track.clips[edit_data["clip_index"]]
    cx_end = tlinewidgets._get_frame_x(track.clip_start(edit_data["clip_index"]) + clip.clip_out - clip.clip_in + 1)  # +1 because out inclusive
    height = EDIT_AREA_HEIGHT
    cy_start = ty - height/2
    
    # Draw bg
    cr.set_source_rgba(*OVERLAY_BG)
    cr.rectangle(cx_start, cy_start, cx_end - cx_start, height)
    cr.fill()

    # Top row
    cr.set_source_surface(HAMBURGER_ICON, cx_start, cy_start)
    cr.paint()
    cr.set_source_surface(CLOSE_ICON, cx_start +  (cx_end - cx_start) - 14, cy_start + 2)
    cr.paint()

    try:
        ep = edit_data["editable_property"]
        _draw_edit_area_borders(cr, cx_start, cy_start, cx_end - cx_start, height)
    except:
        _draw_edit_area_borders(cr, cx_start, cy_start, cx_end - cx_start, height)

def _draw_edit_area_borders(cr, x, y, w, h):
    cr.set_source_rgba(1,1,1,1)
    cr.rectangle(x + 4, y + 18, w - 8, h - 24)
    cr.stroke()



