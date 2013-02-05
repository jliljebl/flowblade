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
Module contains GUI components for displayingand  editing clips in timeline.
Global display position and scale information is in this module.
"""
import cairo
import gtk
import math
import pango
import pangocairo
import time

import appconsts
from cairoarea import CairoDrawableArea
from editorstate import current_sequence
from editorstate import current_is_move_mode
from editorstate import timeline_visible
from editorstate import PLAYER
import respaths
import sequence
import utils
import updater

REF_LINE_Y = 250 # Y pos of tracks are relative to this. This is now recalculated on initilization so number here is irrelevent.

WIDTH = 430 # this has no effect if smaller then editorwindow.NOTEBOOK_WIDTH + editorwindow.MONITOR_AREA_WIDTH
HEIGHT = 260 # defines window min height with editorwindow.TOP_ROW_HEIGHT

# Timeline draw constants
# Other elements than black outline are not drawn if clip screen size
# in pixels is below certain thresholds
TEXT_MIN = 12 # if clip shorter, no text
EMBOSS_MIN = 8 # if clip shorter, no emboss
FILL_MIN = 1 # if clip shorter, no fill
TEXT_X = 6 # pos for clip text
TEXT_Y = 29 
TEXT_Y_SMALL = 17
WAVEFORM_PAD_LARGE = 3
WAVEFORM_PAD_SMALL = 1
MARK_PAD = 6
MARK_LINE_WIDTH = 4

# tracks column consts
COLUMN_WIDTH = 96 # column area width
SCALE_HEIGHT = 25
SCROLL_HEIGHT = 20
MUTE_SWITCH_WIDTH = 4 # as mute switch no longer exists this is now essentially left pad width 
ACTIVE_SWITCH_WIDTH = 18
COMPOSITOR_HEIGHT_OFF = 10
COMPOSITOR_HEIGHT = 20
COMPOSITOR_TEXT_X = 6
COMPOSITOR_TEXT_Y = 15
COMPOSITOR_TRACK_X_PAD = 4
COMPOSITOR_TRACK_ARROW_WIDTH = 6
COMPOSITOR_TRACK_ARROW_HEAD_WIDTH = 10
COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT = 5
ID_PAD_X = 29 # track id text pos
ID_PAD_Y = 16 # track id text pos
ID_PAD_Y_SMALL = 4 # track id text pos for small track
VIDEO_TRACK_V_ICON_POS = (5, 16)
VIDEO_TRACK_A_ICON_POS = (5, 25)
VIDEO_TRACK_V_ICON_POS_SMALL = (5, 3)
VIDEO_TRACK_A_ICON_POS_SMALL = (5, 12)
AUDIO_TRACK_ICON_POS = (5, 18)
AUDIO_TRACK_ICON_POS_SMALL = (5, 6)
MUTE_ICON_POS = (5, 4)
MUTE_ICON_POS_NORMAL = (5, 14)
LOCK_POS = (67, 2)
INSRT_ICON_POS = (81, 18)
INSRT_ICON_POS_SMALL = (81, 6)

# tracks column icons
FULL_LOCK_ICON = None
TRACK_BG_ICON = None
MUTE_VIDEO_ICON = None
MUTE_AUDIO_ICON = None
MUTE_AUDIO_A_ICON =  None
MUTE_ALL_ICON = None
TRACK_ALL_ON_V_ICON = None
TRACK_ALL_ON_A_ICON = None

# clip icons
FILTER_CLIP_ICON = None
COMPOSITOR_CLIP_ICON = None
VIEW_SIDE_ICON = None
INSERT_ARROW_ICON = None
AUDIO_MUTE_ICON = None
VIDEO_MUTE_ICON = None
ALL_MUTE_ICON = None
MARKER_ICON = None

# tc scale
TC_POINTER_HEAD = None

# tc frame scale consts
SCALE_LINE_Y = 4.5 # scale horizontal line pos
SMALL_TICK_Y = 18.5 # end for tick drawn in all scales 
BIG_TICK_Y = 12.5 # end for tick drawn in most zoomed in scales
TC_Y = 10 # TC text pos in scale
# Timeline scale is rendered with hardcoded steps for hardcoded 
# pix_per_frame ranges
DRAW_THRESHOLD_1 = 6 # if pix_per_frame below this, draw secs
DRAW_THRESHOLD_2 = 4
DRAW_THRESHOLD_3 = 2
DRAW_THRESHOLD_4 = 1
# Height of sync state stripe indicating if clip is in sync or not
SYNC_STRIPE_HEIGHT = 6
# number on lines and tc codes displayed with small pix_per_frame values
NUMBER_OF_LINES = 7
# Positions for 1-2 icons on clips.
ICON_SLOTS = [(14, 2),(28, 2),(42,2),(56,2)]

# Color creating utils methods
def get_multiplied_color(color, m):
    """
    Used to create lighter and darker hues of colors.
    """
    return (color[0] * m, color[1] * m, color[2] * m)

def get_multiplied_grad(pos, alpha, grad_color, m):
    """
    Used to create lighter and darker hues of gradient colors.
    """
    return (pos, grad_color[1] * m, grad_color[2] * m, grad_color[3] * m, alpha)

def get_multiplied_color_from_grad(grad_color, m):
    """
    Used to create lighter and darker hues of gradient colors.
    """
    return (grad_color[1] * m, grad_color[2] * m, grad_color[3] * m)
    
# Colors
GRAD_MULTIPLIER = 1.3
SELECTED_MULTIPLIER = 1.52

CLIP_COLOR = (0.62, 0.38, 0.7)
CLIP_COLOR_L = get_multiplied_color(CLIP_COLOR, GRAD_MULTIPLIER)
CLIP_COLOR_GRAD = (1, 0.62, 0.38, 0.7, 1)
CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, CLIP_COLOR_GRAD, GRAD_MULTIPLIER) 
CLIP_SELECTED_COLOR = get_multiplied_color_from_grad(CLIP_COLOR_GRAD, SELECTED_MULTIPLIER)

AUDIO_CLIP_COLOR_GRAD = (1, 0.79, 0.80, 0.18, 1)
AUDIO_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, AUDIO_CLIP_COLOR_GRAD, GRAD_MULTIPLIER + 0.5)
AUDIO_CLIP_SELECTED_COLOR = (0.96, 0.97, 0.53)

IMAGE_CLIP_SELECTED_COLOR = (0.45, 0.90, 0.93)
IMAGE_CLIP_COLOR_GRAD = (1, 0.33, 0.65, 0.69, 1)
IMAGE_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, IMAGE_CLIP_COLOR_GRAD, GRAD_MULTIPLIER) 

COMPOSITOR_CLIP = (0.3, 0.3, 0.3, 0.8)
COMPOSITOR_CLIP_SELECTED = (0.5, 0.5, 0.5, 0.8)

BLANK_CLIP_COLOR_GRAD = (1, 0.866, 1.0, 1.0, 1)
BLANK_CLIP_COLOR_GRAD_L = (0, 0.7, 0.96, 1.0, 1)

BLANK_CLIP_COLOR_SELECTED_GRAD = (1, 0.866, 0.8, 1.0, 1)
BLANK_CLIP_COLOR_SELECTED_GRAD_L = (0, 0.7, 0.7, 1.0, 1)

SYNC_OK_COLOR = (0.28, 0.65, 0.28)
SYNC_OFF_COLOR = (0.77, 0.20, 0.3)
SYNC_GONE_COLOR = (0.4, 0.4, 0.4)

MARK_COLOR = (0.1, 0.1, 0.1)

FRAME_SCALE_COLOR_GRAD = (1, 0.8, 0.8, 0.8, 1)
FRAME_SCALE_COLOR_GRAD_L = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, GRAD_MULTIPLIER) 

BG_COLOR = (0.6, 0.6, 0.65)

COLUMN_ACTIVE_COLOR = (0.36, 0.37, 0.37)
COLUMN_NOT_ACTIVE_COLOR = (0.65, 0.65, 0.65)

OVERLAY_COLOR = (0.9,0.9,0.9)
OVERLAY_SELECTION_COLOR = (0.9,0.9,0.0)
CLIP_OVERLAY_COLOR = (0.2, 0.2, 0.9, 0.5)
OWERWRITE_OVERLAY_COLOR = (0.9, 0.2, 0.2, 0.5)
INSERT_MODE_COLOR = (0.9,0.9,0.0)
OVERWRITE_MODE_COLOR = (0.9,0.0,0.0)

POINTER_TRIANGLE_COLOR = (0.6, 0.7, 0.8, 0.7)
SHADOW_POINTER_COLOR = (0.5, 0.5, 0.5)

BLANK_SELECTED = (0.68, 0.68, 0.74)

TRACK_GRAD_STOP1 = (1, 0.68, 0.68, 0.68, 1) #0.93, 0.93, 0.93, 1)
TRACK_GRAD_STOP2 = (0.5, 0.93, 0.93, 0.93, 1) # (0.5, 0.58, 0.58, 0.58, 1)
TRACK_GRAD_STOP3 = (0, 0.93, 0.93, 0.93, 1) #0.58, 0.58, 0.58, 1) #(0, 0.84, 0.84, 0.84, 1)

TRACK_GRAD_ORANGE_STOP1 = (1,  0.4, 0.4, 0.4, 1)
TRACK_GRAD_ORANGE_STOP2 = (1, 0.93, 0.62, 0.53, 1) #(0.5, 0.58, 0.34, 0.34, 1)
TRACK_GRAD_ORANGE_STOP3 = (0,  0.68, 0.68, 0.68, 1)

LIGHT_MULTILPLIER = 1.14
DARK_MULTIPLIER = 0.74

POINTER_COLOR = (1, 0.3, 0.3) # red frame pointer

# debug purposes
draw_blank_borders = True

# Draw state
pix_per_frame = 5.0 # Current draw scale. This set set elsewhere on init so value irrelevant.
pos = 0 # Current left most frame in timeline display

# ref to singleton TimeLineCanvas instance for mode setting and some position
# calculations.
canvas_widget = None

# Value used to display shadow frame when in clip edit mode 
shadow_frame = -1

def load_icons():
    global FULL_LOCK_ICON, FILTER_CLIP_ICON, VIEW_SIDE_ICON,\
    COMPOSITOR_CLIP_ICON, INSERT_ARROW_ICON, AUDIO_MUTE_ICON, MARKER_ICON, \
    VIDEO_MUTE_ICON, ALL_MUTE_ICON, TRACK_BG_ICON, MUTE_AUDIO_ICON, MUTE_VIDEO_ICON, MUTE_ALL_ICON, \
    TRACK_ALL_ON_V_ICON, TRACK_ALL_ON_A_ICON, MUTE_AUDIO_A_ICON, TC_POINTER_HEAD

    FULL_LOCK_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "full_lock.png")
    FILTER_CLIP_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "filter_clip_icon_sharp.png")
    COMPOSITOR_CLIP_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "compositor.png")
    VIEW_SIDE_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "view_side.png")
    INSERT_ARROW_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "insert_arrow.png")
    AUDIO_MUTE_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "clip_audio_mute.png")
    VIDEO_MUTE_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "clip_video_mute.png")
    ALL_MUTE_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "clip_all_mute.png")
    TRACK_BG_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "track_bg.png")
    MUTE_AUDIO_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "track_audio_mute.png")
    MUTE_VIDEO_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "track_video_mute.png")
    MUTE_ALL_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "track_all_mute.png")
    MARKER_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "marker.png")
    TRACK_ALL_ON_V_ICON = _load_pixbuf("track_all_on_V.png")
    TRACK_ALL_ON_A_ICON = _load_pixbuf("track_all_on_A.png")
    MUTE_AUDIO_A_ICON = _load_pixbuf("track_audio_mute_A.png") 
    TC_POINTER_HEAD = _load_pixbuf("tc_pointer_head.png") 

def _load_pixbuf(icon_file):
    return gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + icon_file)

def set_ref_line_y(allocation):
    """
    Sets value of REF_LINE_Y to such that tracks are vertically centered.
    """
    total_h = 0
    below_ref_h = 0
    for i in range(1, len(current_sequence().tracks) - 1):
        total_h += current_sequence().tracks[i].height
        if i < current_sequence().first_video_index:
            below_ref_h += current_sequence().tracks[i].height

    x, y, w, panel_height = allocation
    centerered_tracks_bottom_y = (panel_height / 2.0) + (total_h / 2.0)
    global REF_LINE_Y
    REF_LINE_Y = centerered_tracks_bottom_y - below_ref_h

def get_pos_for_tline_centered_to_current_frame():
    current_frame = PLAYER().current_frame()
    x, y, w, h = canvas_widget.widget.allocation
    frames_in_panel = w / pix_per_frame
    last_pos = current_sequence().get_length() - frames_in_panel

    # current in first half on first screen width of tline display
    if current_frame < (frames_in_panel / 2.0):
        return 0
    else:
        return current_frame - (frames_in_panel / 2)

def get_frame(panel_x):
    """
    Returns frame for panel x position
    """
    return int(pos + (panel_x / pix_per_frame))

def get_track(panel_y):
    """
    Returns track object for y or None
    """
    audio_add = 0
    for i in range(1, current_sequence().first_video_index):
        audio_add = audio_add + current_sequence().tracks[i].height

    bottom_line = REF_LINE_Y + audio_add
    if panel_y > bottom_line:
        return None
        
    tracks_height = bottom_line;
    for i in range(1, len(current_sequence().tracks)):
        tracks_height = tracks_height - current_sequence().tracks[i].height
        if tracks_height < panel_y:
            return current_sequence().tracks[i]
    
    return None

def get_clip_track_and_index_for_pos(x, y):
    # Returns tuple (clip, track, index)
    track = get_track(y)
    if track == None:
        return (None, None, -1)

    frame = get_frame(x)
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return (None, None, -1)
    
    return (track.clips[clip_index], track, clip_index)

def _get_track_y(track_index):
    """
    NOTE: NOT REALLY INTERNAL TO MODULE, HAS OUTSIDE USERS.
    Returns y pos in canvas for track index. y is top most pixel in track 
    """
    audio_add = 0
    for i in range(1, current_sequence().first_video_index):
        audio_add = audio_add + current_sequence().tracks[i].height

    bottom_line = REF_LINE_Y + audio_add
    tracks_height = 0;
    for i in range(1, track_index + 1):
        tracks_height = tracks_height + current_sequence().tracks[i].height
    
    return bottom_line - tracks_height
    
def _get_frame_x(frame):
    """
    NOTE: NOT REALLY INTERNAL TO MODULE, HAS OUTSIDE USERS.
    Returns x pos in canvas for timeline frame
    """
    disp_frame = frame - pos
    return disp_frame * pix_per_frame

def compositor_hit(frame, y, sorted_compositors):
    """
    Returns compositor hit with mouse press x,y or None if nothing hit.
    """
    track = get_track(y)
    track_top = _get_track_y(track.id)
    
    # Test if compositor hit on track top, so compositor hit on dest track side
    if y >= track_top and y < track_top + (COMPOSITOR_HEIGHT - COMPOSITOR_HEIGHT_OFF):
       return _comp_hit_on_below_track(frame, track, sorted_compositors)
       
    # Test if compositor hit on track bottom, so compositor hit on source track side      
    elif y >= (track_top + track.height - COMPOSITOR_HEIGHT_OFF) and y <=(track_top + track.height):
       return _comp_hit_on_source_track(frame, track, sorted_compositors)

    # Hit y is on he stripe where no compositors can be hit
    else:
        return None

def _comp_hit_on_below_track(frame, track, sorted_compositors):
    for comp in sorted_compositors:
        if comp.transition.b_track - 1 == track.id:
            if comp.clip_in <= frame and comp.clip_out >= frame:
                return comp
    return None

def _comp_hit_on_source_track(frame, track, sorted_compositors):
    for comp in sorted_compositors:
        if comp.transition.b_track == track.id:
            if comp.clip_in <= frame and comp.clip_out >= frame:
                return comp
    return None
    
# --------------------------------------- edit mode overlay draw handling
def set_edit_mode(data, draw_func):
    global canvas_widget
    canvas_widget.edit_mode_data = data
    canvas_widget.edit_mode_overlay_draw_func = draw_func
    
def set_edit_mode_data(data):
    global canvas_widget
    canvas_widget.edit_mode_data = data
        
def draw_insert_overlay(cr, data):
    """
    Overlay for insert move edit mode
    """
    # Only draw if were moving
    if data == None:
        return
    if data["move_on"] == False:
        return

    target_track = data["to_track_object"]
    y = _get_track_y(target_track.id)
    
    _draw_move_overlay(cr, data, y)
    
    insert_frame = data["insert_frame"]
    insert_frame_x = _get_frame_x(insert_frame)    
    _draw_mode_arrow(cr, insert_frame_x, y, INSERT_MODE_COLOR)

def draw_overwrite_overlay(cr, data):
    """
    Overlay for overwrite move edit mode
    """
    # Only draw if were moving
    if data == None:
        return
    if data["move_on"] == False:
        return
    
    target_track = data["to_track_object"]
    y = _get_track_y(target_track.id)
    
    track_height = target_track.height
    _draw_move_overlay(cr, data, y)
    
    start_x = _get_frame_x(data["over_in"])
    end_x = _get_frame_x(data["over_out"])
    _draw_overwrite_clips_overlay(cr, start_x, end_x, y, track_height)
    arrow_x = start_x + ((end_x - start_x)/2.0)
    _draw_mode_arrow(cr, arrow_x, y, OVERWRITE_MODE_COLOR)

def _draw_move_overlay(cr, data, y):
    # Get data
    press_frame = data["press_frame"]
    current_frame = data["current_frame"]
    first_clip_start = data["first_clip_start"]
    clip_lengths = data["clip_lengths"]
    track_height = data["to_track_object"].height

    # Get first frame for drawing shadow clips
    draw_start = first_clip_start + (current_frame - press_frame)
    clip_start_frame = draw_start - pos
        
    # Draw clips in draw range
    cr.set_line_width(2.0)
    cr.set_source_rgb(*OVERLAY_COLOR)
    for i in range(0, len(clip_lengths)):
        clip_length = clip_lengths[i]
        
        scale_length = clip_length * pix_per_frame
        scale_in = clip_start_frame * pix_per_frame
        cr.rectangle(scale_in, y + 1.5, scale_length, track_height - 2.5)
        cr.stroke()
        
        # Start frame for next clip
        clip_start_frame += clip_length

def draw_two_roll_overlay(cr, data):
    """
    Overlay for two roll trim edit mode
    """
    edit_frame = data["edit_frame"]
    frame_x = _get_frame_x(edit_frame)
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.move_to(frame_x, track_y - 3)
    cr.line_to(frame_x, track_y + track_height + 3)
    cr.stroke()
    
    selection_frame_x = _get_frame_x(data["selected_frame"])
    _draw_selected_frame(cr, selection_frame_x, track_y, track_height)
    
    _draw_two_arrows(cr, frame_x - 15, track_y + track_height - 13, 10)
    
    if data["to_side_being_edited"]:
        _draw_view_icon(cr, frame_x + 6, track_y + 1)
    else:
        _draw_view_icon(cr, frame_x - 18, track_y + 1)

    trim_limits = data["trim_limits"]
    clip_over_start_x = _get_frame_x(trim_limits["both_start"] - 1) # trim limits leave 1 frame non-trimmable
    clip_over_end_x = _get_frame_x(trim_limits["both_end"] + 1) # trim limits leave 1 frame non-trimmable  
    _draw_trim_clip_overlay(cr, clip_over_start_x, clip_over_end_x, track_y, track_height)

def draw_one_roll_overlay(cr, data):
    """
    Overlay for one roll trim edit mode
    """
    edit_frame = data["edit_frame"]
    frame_x = _get_frame_x(edit_frame)
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.move_to(frame_x, track_y - 3)
    cr.line_to(frame_x, track_y + track_height + 3)
    cr.stroke()
    
    selection_frame_x = _get_frame_x(data["selected_frame"])
    _draw_selected_frame(cr, selection_frame_x, track_y, track_height)
    
    trim_limits = data["trim_limits"]
    if data["to_side_being_edited"]:
        _draw_two_arrows(cr, frame_x, track_y + track_height - 13, 4)
        clip_over_end_x = _get_frame_x(trim_limits["both_end"] + 1) # trim limits leave 1 frame non-trimmable
        _draw_trim_clip_overlay(cr, selection_frame_x, clip_over_end_x, track_y, track_height)
    else:
        _draw_two_arrows(cr, frame_x - 27, track_y + track_height - 13, 4)
        clip_over_start_x = _get_frame_x(trim_limits["both_start"] - 1) # trim limits leave 1 frame non-trimmable 
        _draw_trim_clip_overlay(cr, clip_over_start_x, selection_frame_x, track_y, track_height)

def draw_compositor_move_overlay(cr, data):
    # Get data
    press_frame = data["press_frame"]
    current_frame = data["current_frame"]
    clip_in = data["clip_in"]
    clip_length = data["clip_length"]
    y = data["compositor_y"]
    compositor = data["compositor"]
    
    draw_start = clip_in + (current_frame - press_frame)
    clip_start_frame = draw_start - pos
    scale_length = clip_length * pix_per_frame
    scale_in = clip_start_frame * pix_per_frame

    target_track =  current_sequence().tracks[compositor.transition.a_track]
    target_y = _get_track_y(target_track.id) + target_track.height - COMPOSITOR_HEIGHT_OFF
            
    _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y)
            
    cr.set_line_width(2.0)
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.stroke()
    
def draw_compositor_trim(cr, data):
    clip_in = data["clip_in"]
    clip_out = data["clip_out"]
    y = data["compositor_y"]
    compositor = data["compositor"]

    clip_start_frame = clip_in - pos
    clip_length = clip_out - clip_in + 1
    scale_length = clip_length * pix_per_frame
    scale_in = clip_start_frame * pix_per_frame

    target_track =  current_sequence().tracks[compositor.transition.a_track]
    target_y = _get_track_y(target_track.id) + target_track.height - COMPOSITOR_HEIGHT_OFF
            
    _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y)
    
    cr.set_line_width(2.0)
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.stroke()
    
    if data["trim_is_clip_in"] == True:
        x = scale_in + 2
    else:
        x = scale_in + scale_length - 26
    _draw_two_arrows(cr, x, y + 4, 4)

def _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y):
    cr.move_to(scale_in + 0.5, y + 0.5)
    cr.line_to(scale_in + 0.5 + scale_length, y + 0.5)
    cr.line_to(scale_in + 0.5 + scale_length, y + 0.5 + COMPOSITOR_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + 2 * COMPOSITOR_TRACK_ARROW_WIDTH, y + 0.5 + COMPOSITOR_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + 2 * COMPOSITOR_TRACK_ARROW_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH + COMPOSITOR_TRACK_ARROW_HEAD_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH, target_y + 0.5)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
    cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD, y + 0.5 + COMPOSITOR_HEIGHT)
    cr.line_to(scale_in + 0.5, y + 0.5 + COMPOSITOR_HEIGHT)
    cr.close_path()
            
def _draw_two_arrows(cr, x, y, distance):
    """
    Draws two arrows indicating that user can drag in 
    both directions in trim mode
    """
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.move_to(x + 10, y)
    cr.line_to(x + 10, y + 10)
    cr.line_to(x, y + 5)
    cr.close_path()
    cr.fill()

    cr.move_to(x + 10 + distance, y)
    cr.line_to(x + 10 + distance, y + 10)
    cr.line_to(x + 20 + distance, y + 5)
    cr.close_path()
    cr.fill()

def _draw_selected_frame(cr, x, y, track_height):
    cr.set_source_rgb(*OVERLAY_SELECTION_COLOR)
    cr.move_to(x - 0.5, y - 3.5)
    cr.line_to(x - 0.5, y + track_height + 3.5)
    cr.stroke()

def _draw_mode_arrow(cr, x, y, color):
    cr.move_to(x - 3.5, y - 3.5)
    cr.line_to(x + 3.5, y - 3.5)
    cr.line_to(x + 3.5, y + 8.5)
    cr.line_to(x + 5.5, y + 8.5)
    cr.line_to(x, y + 12.5)
    cr.line_to(x - 5.5, y + 8.5)
    cr.line_to(x - 3.5, y + 8.5)
    cr.close_path()
    cr.set_source_rgb(*color)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(2.0)
    cr.stroke()
    
def _draw_trim_clip_overlay(cr, start_x, end_x, y, track_height):
    cr.set_source_rgba(*CLIP_OVERLAY_COLOR)
    cr.rectangle(start_x, y, end_x - start_x, track_height)
    cr.fill()

def _draw_overwrite_clips_overlay(cr, start_x, end_x, y, track_height):
    cr.set_source_rgba(*OWERWRITE_OVERLAY_COLOR)
    cr.rectangle(start_x, y, end_x - start_x, track_height)
    cr.fill()

def _draw_view_icon(cr, x, y):
    cr.set_source_pixbuf(VIEW_SIDE_ICON, x, y)
    cr.paint()

# ------------------------------- WIDGETS
class TimeLineCanvas:
    """
    GUI component for editing clips
    """

    def __init__(self, press_listener, move_listener, release_listener, double_click_listener, mouse_scroll_listener):
        # Create widget and connect listeners
        self.widget = CairoDrawableArea(WIDTH, 
                                        HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = mouse_scroll_listener
    
        # Mouse events are passed on 
        self.press_listener = press_listener
        self.move_listener = move_listener
        self.release_listener = release_listener
        self.double_click_listener = double_click_listener

        # Edit mode
        self.edit_mode_data = None
        self.edit_mode_overlay_draw_func = draw_insert_overlay
        
        # Drag state
        self.drag_on = False
                
        # for edit mode setting
        global canvas_widget
        canvas_widget = self
        
    #---------------------------- MOUSE EVENTS
    def _press_event(self, event):
        """
        Mouse button callback
        """
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.double_click_listener(get_frame(event.x), event.x, event.y)
            return
         
        self.drag_on = True
        self.press_listener(event, get_frame(event.x))

    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        if not self.drag_on:
            return
        button = -1 
        if (state & gtk.gdk.BUTTON1_MASK):
            button = 1
        elif (state & gtk.gdk.BUTTON3_MASK):
            button = 3
        self.move_listener(x, y, get_frame(x), button, state)
        
    def _release_event(self, event):
        """
        Mouse release callback.
        """
        self.drag_on = False
        self.release_listener(event.x, event.y, get_frame(event.x), \
                              event.button, event.state)
    
    
    #----------------------------------------- DRAW
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(*BG_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()
    
        # Draw tracks
        for i in range(1, len(current_sequence().tracks) - 1): # black and hidden tracks are ignored
            self.draw_track(cr
                            ,current_sequence().tracks[i]
                            ,_get_track_y(i)
                            ,w)

        # Draw compositors
        self.draw_compositors(cr)
    
        # Draw frame pointer
        current_frame = PLAYER().tracktor_producer.frame()
        if timeline_visible():
            pointer_frame = current_frame
            cr.set_source_rgb(0, 0, 0)
        else:
            pointer_frame = shadow_frame
            cr.set_source_rgb(*SHADOW_POINTER_COLOR)
        disp_frame = pointer_frame - pos
        frame_x = math.floor(disp_frame * pix_per_frame) + 0.5
        cr.move_to(frame_x, 0)#y1)
        cr.line_to(frame_x, h)#y2)
        cr.stroke()

        # Draw edit mode overlay
        if self.edit_mode_overlay_draw_func != None:
            self.edit_mode_overlay_draw_func(cr,self.edit_mode_data)

    def draw_track(self, cr, track, y, width):
        """
        Draws visible clips in track.
        """
        # Get text pos for track height
        track_height = track.height
        if track_height == sequence.TRACK_HEIGHT_NORMAL:
            text_y = TEXT_Y
        else:
            text_y = TEXT_Y_SMALL

        # Get clip indexes for clips in first and last displayed frame.
        start = track.get_clip_index_at(int(pos))
        end = track.get_clip_index_at(int(pos + width / pix_per_frame))

        # Add 1 to end because range() last index exclusive 
        # MLT returns clips structure size + 1 if frame after last clip,
        # so in that case don't add anything.
        if len(track.clips) != end:
            end = end + 1
            
        # Get frame of clip.clip_in_in on timeline.
        clip_start_in_tline = track.clip_start(start)
        # Pos is the first drawn frame.
        # clip_start_frame is always less or equal to zero as this is
        # the first maybe partially displayed clip.
        clip_start_frame = clip_start_in_tline - pos

        # Draw clips in draw range
        for i in range(start, end):

            clip = track.clips[i]

            # Get clip frame values
            clip_in = clip.clip_in
            clip_out = clip.clip_out
            clip_length = clip_out - clip_in + 1 # +1 because in and out both inclusive
            scale_length = clip_length * pix_per_frame
            scale_in = clip_start_frame * pix_per_frame
            
            # Fill clip bg 
            if scale_length > FILL_MIN:
                # Select color
                if clip.is_blanck_clip:
                    if clip.selected:
                        grad = cairo.LinearGradient (0, y, 0, y + track_height)
                        grad.add_color_stop_rgba(*BLANK_CLIP_COLOR_SELECTED_GRAD)
                        grad.add_color_stop_rgba(*BLANK_CLIP_COLOR_SELECTED_GRAD_L)
                        cr.set_source(grad)
                    else:
                        grad = cairo.LinearGradient (0, y, 0, y + track_height)
                        grad.add_color_stop_rgba(*BLANK_CLIP_COLOR_GRAD)
                        grad.add_color_stop_rgba(*BLANK_CLIP_COLOR_GRAD_L)
                        cr.set_source(grad)
                elif track.type == sequence.VIDEO:
                    if clip.media_type == sequence.VIDEO:
                        if not clip.selected:
                            grad = cairo.LinearGradient (0, y, 0, y + track_height)
                            grad.add_color_stop_rgba(*CLIP_COLOR_GRAD)
                            grad.add_color_stop_rgba(*CLIP_COLOR_GRAD_L)
                            cr.set_source(grad)
                        else:
                            cr.set_source_rgb(*CLIP_SELECTED_COLOR)
                    else: # IMAGE type
                        if not clip.selected:
                            grad = cairo.LinearGradient (0, y, 0, y + track_height)
                            grad.add_color_stop_rgba(*IMAGE_CLIP_COLOR_GRAD)
                            grad.add_color_stop_rgba(*IMAGE_CLIP_COLOR_GRAD_L)
                            cr.set_source(grad)
                        else:
                            cr.set_source_rgb(*IMAGE_CLIP_SELECTED_COLOR)
                else:
                    if not clip.selected:
                        grad = cairo.LinearGradient (0, y, 0, y + track_height)
                        grad.add_color_stop_rgba(*AUDIO_CLIP_COLOR_GRAD)
                        grad.add_color_stop_rgba(*AUDIO_CLIP_COLOR_GRAD_L)
                        cr.set_source(grad)
                    else:
                        cr.set_source_rgb(*AUDIO_CLIP_SELECTED_COLOR)
                
                # Clip bg
                cr.rectangle(scale_in, y, scale_length, track_height)
                cr.fill()

            # Draw clip frame 
            cr.set_line_width(1.0)
            if scale_length > FILL_MIN:
                cr.set_source_rgb(0, 0, 0)
            else:    
                cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.rectangle(scale_in + 0.5,
                         y + 0.5, scale_length, 
                         track_height)
            cr.stroke()
        
            # No further drawing for blank clip 
            if clip.is_blanck_clip:
                clip_start_frame += clip_length
                continue

            # Emboss
            if scale_length > EMBOSS_MIN:
                # Corner points
                left = scale_in + 1.5
                up = y + 1.5
                right = left + scale_length - 2.0
                down = up + track_height - 2.0
                
                # Draw lines
                cr.set_source_rgb(0.75, 0.43, 0.79)
                cr.move_to(left, down)
                cr.line_to(left, up)
                cr.stroke()
                
                cr.move_to(left, up)
                cr.line_to(right, up)
                cr.stroke()
                
                cr.set_source_rgb(0.47, 0.28, 0.51)
                cr.move_to(right, up)
                cr.line_to(right, down)
                cr.stroke()
                
                cr.move_to(right, down)
                cr.line_to(left, down)
                cr.stroke()

            # Sync stripe
            if scale_length > FILL_MIN: 
                if clip.sync_data != None:
                    stripe_color = SYNC_OK_COLOR
                    if clip.sync_data.sync_state == appconsts.SYNC_CORRECT:
                        stripe_color = SYNC_OK_COLOR
                    elif clip.sync_data.sync_state == appconsts.SYNC_OFF:
                        stripe_color = SYNC_OFF_COLOR
                    else:
                        stripe_color = SYNC_GONE_COLOR
                    cr.rectangle(scale_in + 1, y + track_height - SYNC_STRIPE_HEIGHT, 
                                    scale_length - 2, SYNC_STRIPE_HEIGHT)
                    cr.set_source_rgb(*stripe_color)
                    cr.fill()

            # Draw audio waveform
            if clip.waveform_data != None and scale_length > FILL_MIN:
                if track.height == sequence.TRACK_HEIGHT_NORMAL:
                    y_pad = WAVEFORM_PAD_LARGE
                else:
                    y_pad = WAVEFORM_PAD_SMALL
                waveform_pix_count = len(clip.waveform_data)
                if clip.get_length() < waveform_pix_count:
                    waveform_pix_count = clip.get_length()
                for i in range(0, waveform_pix_count):
                    x = scale_in + i * pix_per_frame
                    cr.set_source_pixbuf(clip.waveform_data[i], x, y + y_pad)
                    cr.paint()

            # Draw text and filter, sync icons
            if scale_length > TEXT_MIN:
                # Text
                cr.set_source_rgb(0, 0, 0)
                cr.select_font_face ("sans-serif",
                                     cairo.FONT_SLANT_NORMAL,
                                     cairo.FONT_WEIGHT_NORMAL)

                cr.set_font_size(11)
                cr.move_to(scale_in + TEXT_X, y + text_y)
                cr.show_text(clip.name.upper())
                #cr.show_text(str(clip.id).upper())
                
                icon_slot = 0
                # Filter icon
                if len(clip.filters) > 0:
                    ix, iy = ICON_SLOTS[icon_slot]
                    cr.set_source_pixbuf(FILTER_CLIP_ICON, int(scale_in) + int(scale_length) - ix, y + iy)
                    cr.paint()
                    icon_slot = icon_slot + 1
                # Mute icon
                if clip.mute_filter != None:
                    icon = AUDIO_MUTE_ICON
                    ix, iy = ICON_SLOTS[icon_slot]
                    cr.set_source_pixbuf(icon, int(scale_in) + int(scale_length) - ix, y + iy)
                    cr.paint()
                    icon_slot = icon_slot + 1

            # Get next draw position
            clip_start_frame += clip_length
            
        # Fill rest of track with bg color, if needed
        scale_in = clip_start_frame  * pix_per_frame
        if scale_in < width:
            cr.rectangle(scale_in + 0.5, y + 1, width - scale_in, track_height - 2)
            cr.set_source_rgb(*BG_COLOR)  
            cr.fill()

    def draw_compositors(self, cr):
        compositors = current_sequence().get_compositors()
        for comp in compositors:
            # compositor clip and edge
            track = current_sequence().tracks[comp.transition.b_track]
            target_track =  current_sequence().tracks[comp.transition.a_track]
            
            y = _get_track_y(track.id) + track.height - COMPOSITOR_HEIGHT_OFF
            target_y = _get_track_y(target_track.id) + target_track.height - COMPOSITOR_HEIGHT_OFF

            scale_in = (comp.clip_in - pos) * pix_per_frame
            scale_length = (comp.clip_out - comp.clip_in + 1) * pix_per_frame # +1, out inclusive
            if comp.selected == False:
                color = COMPOSITOR_CLIP
            else:
                color = COMPOSITOR_CLIP_SELECTED
            cr.set_source_rgba(*color)

            _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y)
            """
            cr.move_to(scale_in + 0.5, y + 0.5)
            cr.line_to(scale_in + 0.5 + scale_length, y + 0.5)
            cr.line_to(scale_in + 0.5 + scale_length, y + 0.5 + COMPOSITOR_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + 2 * COMPOSITOR_TRACK_ARROW_WIDTH, y + 0.5 + COMPOSITOR_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + 2 * COMPOSITOR_TRACK_ARROW_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH + COMPOSITOR_TRACK_ARROW_HEAD_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH, target_y + 0.5)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD + COMPOSITOR_TRACK_ARROW_WIDTH - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD, target_y + 0.5 - COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT)
            cr.line_to(scale_in + 0.5 + COMPOSITOR_TRACK_X_PAD, y + 0.5 + COMPOSITOR_HEIGHT)
            cr.line_to(scale_in + 0.5, y + 0.5 + COMPOSITOR_HEIGHT)

            cr.close_path()
            """

            cr.fill_preserve()

            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1.0)
            cr.stroke()

            # text
            cr.save()

            cr.rectangle(scale_in + 0.5,
                         y + 0.5, scale_length, 
                         COMPOSITOR_HEIGHT)
            cr.clip()
            cr.new_path()
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face ("sans-serif",
                                 cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)

            cr.set_font_size(11)
            cr.move_to(scale_in + COMPOSITOR_TEXT_X, y + COMPOSITOR_TEXT_Y)
            cr.show_text(comp.name.upper())
            
            cr.restore()
        

class TimeLineColumn:
    """
    GUI component for displaying and editing track parameters.
    """

    def __init__(self, active_listener, mute_listener, center_listener):
        # Init widget
        self.widget = CairoDrawableArea(COLUMN_WIDTH, 
                                        HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        
        self.active_listener = active_listener
        self.mute_listener = mute_listener
        self.center_listener = center_listener
        self.init_listeners()

    # ------------------------------- MOUSE EVENTS
    def init_listeners(self):
        self.track_testers = []
        
        # Add track click testers
        # track zero is ignored black bg track
        for i in range(1, len(current_sequence().tracks) - 1): # black and hidden tracks are ignored
            start =  _get_track_y(i)
            end = start + current_sequence().tracks[i].height
            tester = ValueTester(start, end, self.track_hit)
            tester.data.track = i
            self.track_testers.append(tester)
        
        # Add switch click testers
        self.switch_testers = []

        # Active area tester
        center_width = COLUMN_WIDTH - MUTE_SWITCH_WIDTH - ACTIVE_SWITCH_WIDTH
        tester = ValueTester(MUTE_SWITCH_WIDTH + center_width, COLUMN_WIDTH, 
                             self.active_listener)
        self.switch_testers.append(tester)
        # Center area tester
        tester = ValueTester(MUTE_SWITCH_WIDTH, COLUMN_WIDTH - ACTIVE_SWITCH_WIDTH, 
                             self.center_listener)
        self.switch_testers.append(tester)

    def _press_event(self, event):
        """
        Mouse button callback
        """
        self.event = event
        for tester in self.track_testers:
            tester.data.x = event.x # pack x value to go
            tester.data.event = event
            tester.call_listener_if_hit(event.y)

    def track_hit(self, data):
        """
        Called when a track has been hit.
        Call appropriate switch press listener, mute or active switch
        """
        for tester in self.switch_testers:
            tester.data.track = data.track # pack track index to go
            tester.data.event = data.event
            tester.call_listener_if_hit(data.x)
    
    # --------------------------------------------- DRAW
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(*BG_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        # get insert track
        insert_track_index = current_sequence().get_first_active_track().id
        
        # Draw tracks
        for i in range(1, len(current_sequence().tracks) - 1):
            y = _get_track_y(i)
            is_insert_track = (insert_track_index==i)
            self.draw_track(cr, current_sequence().tracks[i], y, is_insert_track)
 
    def draw_track(self, cr, track, y, is_insert_track):
        # Draw center area
        center_width = COLUMN_WIDTH - MUTE_SWITCH_WIDTH - ACTIVE_SWITCH_WIDTH
        rect = (MUTE_SWITCH_WIDTH, y, center_width, track.height)
        grad = cairo.LinearGradient (MUTE_SWITCH_WIDTH, y, MUTE_SWITCH_WIDTH, y + track.height)
        self._add_gradient_color_stops(grad, track)
        cr.rectangle(*rect)
        cr.set_source(grad)
        cr.fill()
        self.draw_edge(cr, rect)
        
        # Draw active switch bg end edge
        rect = (MUTE_SWITCH_WIDTH + center_width -1, y, ACTIVE_SWITCH_WIDTH + 1, track.height)
        cr.rectangle(*rect)
        if track.active:
            grad = cairo.LinearGradient(MUTE_SWITCH_WIDTH + center_width, y,
                                        MUTE_SWITCH_WIDTH + center_width, y + track.height)
            self._add_gradient_color_stops(grad, track)
            cr.set_source(grad)
        else:
            cr.set_source_rgb(*COLUMN_NOT_ACTIVE_COLOR)
        cr.fill()
        self.draw_edge(cr, rect)

        # Draw type and index text
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        text = utils.get_track_name(track, current_sequence())        
        layout.set_text(text)
        desc = pango.FontDescription("Sans Bold 11")
        layout.set_font_description(desc)

        pango_context.set_source_rgb(0.0, 0.0, 0)
        if track.height == sequence.TRACK_HEIGHT_NORMAL:
            text_y = ID_PAD_Y
        else:
            text_y = ID_PAD_Y_SMALL
        pango_context.move_to(MUTE_SWITCH_WIDTH + ID_PAD_X, y + text_y)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)
        
        # Draw mute icon
        mute_icon = None
        if track.mute_state == appconsts.TRACK_MUTE_VIDEO and track.type == appconsts.VIDEO:
            mute_icon = MUTE_VIDEO_ICON
        elif track.mute_state == appconsts.TRACK_MUTE_AUDIO and track.type == appconsts.VIDEO:
            mute_icon = MUTE_AUDIO_ICON
        elif track.mute_state == appconsts.TRACK_MUTE_AUDIO and track.type == appconsts.AUDIO:
            mute_icon = MUTE_AUDIO_A_ICON
        elif track.mute_state == appconsts.TRACK_MUTE_ALL:
            mute_icon = MUTE_ALL_ICON
        elif track.type == appconsts.VIDEO:
            mute_icon = TRACK_ALL_ON_V_ICON
        else:
            mute_icon = TRACK_ALL_ON_A_ICON
            
        if mute_icon != None:
            ix, iy = MUTE_ICON_POS
            if track.height > sequence.TRACK_HEIGHT_SMALL:
                ix, iy = MUTE_ICON_POS_NORMAL
            cr.set_source_pixbuf(mute_icon, ix, y + iy)
            cr.paint()

        # Draw locked icon
        if track.edit_freedom == sequence.LOCKED:
            ix, iy = LOCK_POS
            cr.set_source_pixbuf(FULL_LOCK_ICON, ix, y + iy)
            cr.paint()
        
        # Draw insert arrow
        if is_insert_track == True:
            ix, iy = INSRT_ICON_POS
            if track.height == sequence.TRACK_HEIGHT_SMALL:
                ix, iy = INSRT_ICON_POS_SMALL
            cr.set_source_pixbuf(INSERT_ARROW_ICON, ix, y + iy)
            cr.paint()

    def _add_gradient_color_stops(self, grad, track):
        if track.id == current_sequence().first_video_index: 
            grad.add_color_stop_rgba(*TRACK_GRAD_ORANGE_STOP1)
            #grad.add_color_stop_rgba(*TRACK_GRAD_ORANGE_STOP2)
            grad.add_color_stop_rgba(*TRACK_GRAD_ORANGE_STOP3)
        else:
            grad.add_color_stop_rgba(*TRACK_GRAD_STOP1)
            #grad.add_color_stop_rgba(*TRACK_GRAD_STOP2)
            grad.add_color_stop_rgba(*TRACK_GRAD_STOP3)

    def draw_edge(self, cr, rect):
        cr.set_line_width(1.0)
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(rect[0] + 0.5, rect[1] + 0.5, rect[2] - 1, rect[3])
        cr.stroke()


class TimeLineFrameScale:
    """
    GUI component for displaying frame tme value scale.
    """

    def __init__(self, set_default_callback, mouse_scroll_listener):
        self.widget = CairoDrawableArea(WIDTH, 
                                        SCALE_HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = mouse_scroll_listener
        self.drag_on = False
        self.set_default_callback = set_default_callback

    def _press_event(self, event):
        if event.button == 1 or event.button == 3:
            if not timeline_visible():
                updater.display_sequence_in_monitor()
                return
            PLAYER().seek_frame(get_frame(event.x))
            self.drag_on = True

    def _motion_notify_event(self, x, y, state):
        if((state & gtk.gdk.BUTTON1_MASK)
           or(state & gtk.gdk.BUTTON3_MASK)):
            if self.drag_on:
                PLAYER().seek_frame(get_frame(x)) 
                
    def _release_event(self, event):
        if self.drag_on:
            PLAYER().seek_frame(get_frame(event.x)) 
        
        self.drag_on = False

    # --------------------------------------------- DRAW
    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation
        
        # Get sequence and frames per second value
        seq = current_sequence()
        fps = seq.profile.fps()
        
        # Draw white bg
        grad = cairo.LinearGradient (0, 0, 0, h)
        grad.add_color_stop_rgba(*FRAME_SCALE_COLOR_GRAD)
        grad.add_color_stop_rgba(*FRAME_SCALE_COLOR_GRAD_L)
        cr.set_source(grad)
        cr.rectangle(0,0,w,h)
        cr.fill()

        # Set line attr for frames lines
        cr.set_source_rgb(0,0,0)
        cr.set_line_width(1.0)
        
        big_tick_step = -1 # this isn't rendered most ranges, -1 is flag

        # Get displayed frame range
        view_start_frame = pos
        view_end_frame = int(pos + w / pix_per_frame)

        # Get draw steps for marks and tc texts
        if pix_per_frame > DRAW_THRESHOLD_1:
            small_tick_step = 1
            big_tick_step = fps / 2
            tc_draw_step = fps / 2
        elif pix_per_frame > DRAW_THRESHOLD_2:
            small_tick_step = fps
            tc_draw_step = fps
        elif pix_per_frame > DRAW_THRESHOLD_3:
            small_tick_step = fps * 2
            tc_draw_step = fps * 2
        elif pix_per_frame > DRAW_THRESHOLD_4:
            small_tick_step = fps * 3
            tc_draw_step = fps * 3
        else:
            view_length = view_end_frame - view_start_frame
            small_tick_step = int(view_length / NUMBER_OF_LINES)
            tc_draw_step = int(view_length / NUMBER_OF_LINES)

        # Draw small tick lines
        # Get draw range in steps from 0
        start = int(view_start_frame / small_tick_step)
        if start * small_tick_step == pos:
            start += 1 # don't draw line on first pixel of scale display
        # +1 to ensure coverage
        end = int(view_end_frame / small_tick_step) + 1 
        for i in range(start, end):
            x = math.floor(i * small_tick_step * pix_per_frame - pos * pix_per_frame) + 0.5 
            cr.move_to(x, SCALE_HEIGHT)
            cr.line_to(x, SMALL_TICK_Y)
        cr.stroke()
        
        # Draw big tick lines, if required
        if big_tick_step != -1:
            count = int(seq.get_length() / big_tick_step)
            for i in range(1, count):
                x = math.floor(math.floor(i * big_tick_step) * pix_per_frame \
                    - pos * pix_per_frame) + 0.5 
                cr.move_to(x, SCALE_HEIGHT)
                cr.line_to(x, BIG_TICK_Y)
                cr.stroke()

        # Draw tc
        cr.select_font_face ("sans-serif",
                              cairo.FONT_SLANT_NORMAL,
                              cairo.FONT_WEIGHT_NORMAL)

        cr.set_font_size(11)
        start = int(view_start_frame / tc_draw_step)
        # Get draw range in steps from 0
        if start == pos:
            start += 1 # don't draw line on first pixel of scale display
        # +1 to ensure coverage
        end = int(view_end_frame / tc_draw_step) + 1 
        for i in range(start, end):
            x = math.floor(i * tc_draw_step * pix_per_frame \
                - pos * pix_per_frame) + 0.5
            cr.move_to(x, TC_Y)
            text = utils.get_tc_string(i * tc_draw_step)
            cr.show_text(text);

        # Draw marks
        self.draw_mark_in(cr, h)
        self.draw_mark_out(cr, h)
        
        # Draw markers
        for i in range(0, len(seq.markers)):
            marker_name, marker_frame = seq.markers[i]
            x = math.floor(_get_frame_x(marker_frame))
            cr.set_source_pixbuf(MARKER_ICON, x - 4, 15)
            cr.paint()

        # Select draw colors and frame based on mode
        current_frame = PLAYER().tracktor_producer.frame()
        if timeline_visible():
            cr.set_source_rgb(0, 0, 0)
            line_color = (0, 0, 0)
            triangle_color = POINTER_TRIANGLE_COLOR
            triangle_stroke = (0, 0, 0)
        else:
            current_frame = shadow_frame
            line_color = (0.8, 0.8, 0.8)
            triangle_color = (0.8, 0.8, 0.8)
            triangle_stroke = (0.8, 0.8, 0.8)
            
        # Draw position pointer
        disp_frame = current_frame - pos
        frame_x = math.floor(disp_frame * pix_per_frame) + 0.5
        cr.set_source_rgb(*line_color)
        cr.move_to(frame_x, 0)
        cr.line_to(frame_x, h)
        cr.stroke()

        # Draw pos triangle
        cr.set_source_pixbuf(TC_POINTER_HEAD, frame_x - 7.5, 0)
        cr.paint()
        #TC_POINTER_HEAD
        
        """
        cr.move_to(frame_x - 6, 0.5)
        cr.line_to(frame_x + 6, 0.5)
        cr.line_to(frame_x, 8.5)
        cr.close_path()
        cr.set_source_rgba(*triangle_color)
        cr.fill_preserve()
        cr.set_source_rgb(*triangle_stroke)
        cr.set_line_width(2.0)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke()
        """

    def draw_mark_in(self, cr, h):
        """
        Draws mark in graphic if set.
        """
        mark_frame = current_sequence().tractor.mark_in
        if mark_frame < 0:
            return
             
        x = _get_frame_x(mark_frame)
        cr.set_source_rgb(*MARK_COLOR)
        cr.move_to (x, MARK_PAD)
        cr.line_to (x, h - MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, h - MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x - MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x - MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
        cr.line_to (x - 2 * MARK_LINE_WIDTH, MARK_PAD)
        cr.close_path();
        cr.fill()

    def draw_mark_out(self, cr, h):
        """
        Draws mark out graphic if set.
        """
        mark_frame = current_sequence().tractor.mark_out
        if mark_frame < 0:
            return
             
        x = _get_frame_x(mark_frame + 1)
        cr.set_source_rgb(*MARK_COLOR)
        cr.move_to (x, MARK_PAD)
        cr.line_to (x, h - MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, h - MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x + MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x + MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
        cr.line_to (x + 2 * MARK_LINE_WIDTH, MARK_PAD)
        cr.close_path();

        cr.fill()

class TimeLineColumnHead:
    """
    GUI component filler at timeline area top left.
    """

    def __init__(self):
        self.widget = CairoDrawableArea(COLUMN_WIDTH, 
                                        SCALE_HEIGHT, 
                                        self._draw)

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(0,0,0)
        cr.rectangle(0,0,w,h)
        cr.fill()
        cr.stroke()

# NOT USED CURRENTLY
class TimeLineLeftBottom:
    """
    GUI 
    """

    def __init__(self):
        self.widget = CairoDrawableArea(COLUMN_WIDTH, 
                                        SCROLL_HEIGHT, 
                                        self._draw)

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(0,0,0)
        cr.rectangle(0,0,w,h)
        cr.fill()
        cr.stroke()
        

class TimeLineScroller(gtk.HScrollbar):
    """
    Scrollbar for timeline.
    """
    def __init__(self, scroll_listener):
        gtk.HScrollbar.__init__(self)
        adjustment = gtk.Adjustment(0.0, 0.0, 100.0, 1.0, 10.0, 30.0)
        adjustment.connect("value-changed", scroll_listener)
        self.set_adjustment(adjustment)


class ValueTester:
    """
    Calls listener if test value in hit range.
    """
    def __init__(self, start, end, listener):
        self.start = start
        self.end = end
        self.listener = listener
        self.data = utils.EmptyClass()
        
    def call_listener_if_hit(self, value):
        if value >= self.start and value <= self.end:
            self.listener(self.data)
         

def draw_bitmap(cr, data):
    array, w, h = data
    struct.unpack("B", array[0])

    for x in range(0, w):
        for y in range(0, h):
            i = x + w * y
            cr.rectangle (x, y, 1, 1)
            val = max(struct.unpack("B", array[i]))
            cr.set_source_rgb(float(val)/255.0, float(val)/255.0, float(val)/255.0)
            cr.fill()

