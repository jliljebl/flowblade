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
import pygtk
pygtk.require('2.0');
import gtk

import math
import pango
import pangocairo

import appconsts
from cairoarea import CairoDrawableArea
import clipeffectseditor
import editorpersistance
from editorstate import current_sequence
from editorstate import timeline_visible
from editorstate import PLAYER
from editorstate import EDIT_MODE
from editorstate import current_proxy_media_paths
import editorstate
import respaths
import sequence
import trimmodes
import utils
import updater

M_PI = math.pi

REF_LINE_Y = 250 # Y pos of tracks are relative to this. This is recalculated on initilization, so value here is irrelevent.

WIDTH = 430 # this has no effect if smaller then editorwindow.NOTEBOOK_WIDTH + editorwindow.MONITOR_AREA_WIDTH
HEIGHT = 260 # defines window min height together with editorwindow.TOP_ROW_HEIGHT

# Timeline draw constants
# Other elements than black outline are not drawn if clip screen size
# in pixels is below certain thresholds
TEXT_MIN = 12 # if clip shorter, no text
EMBOSS_MIN = 8 # if clip shorter, no emboss
FILL_MIN = 1 # if clip shorter, no fill
TEXT_X = 6 # pos for clip text
TEXT_Y = 29 
TEXT_Y_SMALL = 17
WAVEFORM_PAD_LARGE = 9
WAVEFORM_PAD_SMALL = 4
MARK_PAD = 6
MARK_LINE_WIDTH = 4

# tracks column consts
COLUMN_WIDTH = 96 # column area width
SCALE_HEIGHT = 25
SCROLL_HEIGHT = 20
COLUMN_LEFT_PAD = 4 # as mute switch no longer exists this is now essentially left pad width 
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
SYNC_STRIPE_HEIGHT = 12
SYNC_SAW_WIDTH = 5
SYNC_SAW_HEIGHT = 5
# number on lines and tc codes displayed with small pix_per_frame values
NUMBER_OF_LINES = 7
# Positions for 1-2 icons on clips.
ICON_SLOTS = [(14, 2),(28, 2),(42,2),(56,2)]
# Line width for moving clip boxes
MOVE_CLIPS_LINE_WIDTH = 3.0

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

AUDIO_CLIP_COLOR_GRAD = (1, 0.23, 0.52, 0.23, 1)#(1, 0.79, 0.80, 0.18, 1)
AUDIO_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, AUDIO_CLIP_COLOR_GRAD, GRAD_MULTIPLIER + 0.5)
AUDIO_CLIP_SELECTED_COLOR = (0.53, 0.85, 0.53)

IMAGE_CLIP_SELECTED_COLOR = (0.45, 0.90, 0.93)
IMAGE_CLIP_COLOR_GRAD = (1, 0.33, 0.65, 0.69, 1)
IMAGE_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, IMAGE_CLIP_COLOR_GRAD, GRAD_MULTIPLIER) 

COMPOSITOR_CLIP = (0.3, 0.3, 0.3, 0.8)
COMPOSITOR_CLIP_SELECTED = (0.5, 0.5, 0.7, 0.8)

BLANK_CLIP_COLOR_GRAD = (1, 0.6, 0.6, 0.65, 1)
BLANK_CLIP_COLOR_GRAD_L = (0, 0.6, 0.6, 0.65, 1)

BLANK_CLIP_COLOR_SELECTED_GRAD = (1, 0.7, 0.7, 0.75, 1)
BLANK_CLIP_COLOR_SELECTED_GRAD_L = (0, 0.7, 0.7, 0.75, 1)

SINGLE_TRACK_TRANSITION_SELECTED = (0.8, 0.8, 1.0)

SYNC_OK_COLOR = (0.18, 0.55, 0.18)
SYNC_OFF_COLOR = (0.77, 0.20, 0.3)
SYNC_GONE_COLOR = (0.4, 0.4, 0.4)

PROXY_STRIP_COLOR = (0.40, 0.60, 0.82)

MARK_COLOR = (0.1, 0.1, 0.1)

FRAME_SCALE_COLOR_GRAD = (1, 0.8, 0.8, 0.8, 1)
FRAME_SCALE_COLOR_GRAD_L = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, GRAD_MULTIPLIER)

FRAME_SCALE_SELECTED_COLOR_GRAD = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, 0.92)
FRAME_SCALE_SELECTED_COLOR_GRAD_L = get_multiplied_grad(1, 1, FRAME_SCALE_SELECTED_COLOR_GRAD, GRAD_MULTIPLIER) 

DARK_FRAME_SCALE_SELECTED_COLOR_GRAD = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, 0.7)
DARK_FRAME_SCALE_SELECTED_COLOR_GRAD_L = get_multiplied_grad(1, 1, FRAME_SCALE_SELECTED_COLOR_GRAD, GRAD_MULTIPLIER * 0.8) 

FRAME_SCALE_LINES = (0, 0, 0)

BG_COLOR = (0.5, 0.5, 0.55)#(0.6, 0.6, 0.65)
TRACK_BG_COLOR = (0.25, 0.25, 0.27)#(0.6, 0.6, 0.65)

COLUMN_ACTIVE_COLOR = (0.36, 0.37, 0.37)
COLUMN_NOT_ACTIVE_COLOR = (0.65, 0.65, 0.65)

OVERLAY_COLOR = (0.9,0.9,0.9)
OVERLAY_SELECTION_COLOR = (0.9,0.9,0.0)
CLIP_OVERLAY_COLOR = (0.2, 0.2, 0.9, 0.5)
OVERWRITE_OVERLAY_COLOR = (0.2, 0.2, 0.2, 0.5)
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

POINTER_COLOR = (1, 0.3, 0.3) # red frame pointer for position bar

# ------------------------------------------------------------------ MODULE STATE
# debug purposes
draw_blank_borders = True

# Draw state
pix_per_frame = 5.0 # Current draw scale. This set set elsewhere on init so default value irrelevant.
pos = 0 # Current left most frame in timeline display

# ref to singleton TimeLineCanvas instance for mode setting and some position
# calculations.
canvas_widget = None

# Used to draw trim modes differently when moving from <X>_NO_EDIT mode to active edit
trim_mode_in_non_active_state = False

# Used ahen editing with SLIDE_TRIM mode to make user believe that the frame being displayed 
# is the view frame user selected while in reality user is displayed images from hidden track and the
# current frame is moving in opposite direction to users mouse movement
fake_current_frame = None

# Used to draw indicators that tell if more frames are available while trimming
trim_status = appconsts.ON_BETWEEN_FRAME

# ------------------------------------------------------------------- module functions
def load_icons():
    global FULL_LOCK_ICON, FILTER_CLIP_ICON, VIEW_SIDE_ICON,\
    COMPOSITOR_CLIP_ICON, INSERT_ARROW_ICON, AUDIO_MUTE_ICON, MARKER_ICON, \
    VIDEO_MUTE_ICON, ALL_MUTE_ICON, TRACK_BG_ICON, MUTE_AUDIO_ICON, MUTE_VIDEO_ICON, MUTE_ALL_ICON, \
    TRACK_ALL_ON_V_ICON, TRACK_ALL_ON_A_ICON, MUTE_AUDIO_A_ICON, TC_POINTER_HEAD, EDIT_INDICATOR

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
    MARKER_ICON = _load_pixbuf("marker.png")
    TRACK_ALL_ON_V_ICON = _load_pixbuf("track_all_on_V.png")
    TRACK_ALL_ON_A_ICON = _load_pixbuf("track_all_on_A.png")
    MUTE_AUDIO_A_ICON = _load_pixbuf("track_audio_mute_A.png") 
    TC_POINTER_HEAD = _load_pixbuf("tc_pointer_head.png")
    EDIT_INDICATOR = _load_pixbuf("clip_edited.png")

    if editorpersistance.prefs.dark_theme == True:
        global FRAME_SCALE_COLOR_GRAD, FRAME_SCALE_COLOR_GRAD_L, BG_COLOR, FRAME_SCALE_LINES
        FRAME_SCALE_COLOR_GRAD = (1, 0.3, 0.3, 0.3, 1)
        FRAME_SCALE_COLOR_GRAD_L = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, GRAD_MULTIPLIER)
        BG_COLOR = (0.44, 0.44, 0.46)
        FRAME_SCALE_LINES = (0.8, 0.8, 0.8)

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
    try:
        track_top = _get_track_y(track.id)
    except AttributeError: # we didn't press on a editable track
        return None
        
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
    # Only draw if were moving
    if data == None:
        return
    if data["move_on"] == False:
        return
    
    target_track = data["to_track_object"]
    y = _get_track_y(target_track.id)
    start_x = _get_frame_x(data["over_in"])
    end_x = _get_frame_x(data["over_out"])
    
    track_height = target_track.height
    _draw_overwrite_clips_overlay(cr, start_x, end_x, y, track_height)

    _draw_move_overlay(cr, data, y)

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
    cr.set_line_width(MOVE_CLIPS_LINE_WIDTH)
    cr.set_source_rgb(*OVERLAY_COLOR)
    for i in range(0, len(clip_lengths)):
        clip_length = clip_lengths[i]
        
        scale_length = clip_length * pix_per_frame
        scale_in = clip_start_frame * pix_per_frame
        cr.rectangle(scale_in, y + 1.5, scale_length, track_height - 2.5)
        cr.stroke()
        
        # Start frame for next clip
        clip_start_frame += clip_length

def draw_multi_overlay(cr, data):
    if data == None:
        return

    press_frame = data["press_frame"]
    current_frame = data["current_frame"]
    min_allowed_delta = - data["multi_data"].max_backwards
    first_moved_frame = data["first_moved_frame"]
    move_all = data["multi_data"].move_all_tracks

    delta = current_frame - press_frame
    if delta <= min_allowed_delta:
        delta = min_allowed_delta
        can_move_back = False
    else:
        can_move_back = True

    draw_y = _get_track_y(0) + 100
    cr.set_line_width(1.0)

    first_frame = first_moved_frame - pos
    first_x = first_frame * pix_per_frame

    draw_frame = first_moved_frame + delta - pos
    draw_x = draw_frame * pix_per_frame

    if move_all:
        cr.rectangle(first_x, 0, draw_x - first_x, draw_y)
        cr.set_source_rgba(0,0,0,0.2)
        cr.fill()
        cr.set_source_rgb(*OVERLAY_COLOR)
        cr.move_to(draw_x, 0)
        cr.line_to(draw_x, draw_y)
        cr.stroke()
    else:
        moved_track_index = data["multi_data"].pressed_track_id
        draw_y = _get_track_y(moved_track_index)
        h = current_sequence().tracks[moved_track_index].height
        cr.rectangle(first_x, draw_y, draw_x - first_x,  h)
        cr.set_source_rgba(0,0,0,0.2)
        cr.fill()
        cr.set_source_rgb(*OVERLAY_COLOR)
        cr.move_to(draw_x, draw_y - 5)
        cr.line_to(draw_x, draw_y + h + 10)
        cr.stroke()

    tracks = current_sequence().tracks
    track_moved = data["multi_data"].track_affected
    for i in range(1, len(tracks) - 1):
        if not track_moved[i - 1]:
            continue
        track = tracks[i]
        draw_y = _get_track_y(i) + track.height / 2
        cr.move_to(draw_x + 2, draw_y)
        cr.line_to(draw_x + 2, draw_y - 5)
        cr.line_to(draw_x + 7, draw_y)
        cr.line_to(draw_x + 2, draw_y + 5)
        cr.close_path()
        cr.fill()
        if can_move_back:
            cr.move_to(draw_x - 2, draw_y)
            cr.line_to(draw_x - 2, draw_y - 5)
            cr.line_to(draw_x - 7, draw_y)
            cr.line_to(draw_x - 2, draw_y + 5)
            cr.close_path()
            cr.fill()

def draw_two_roll_overlay(cr, data):
    edit_frame = data["edit_frame"]
    frame_x = _get_frame_x(edit_frame)
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.move_to(frame_x, track_y - 3)
    cr.line_to(frame_x, track_y + track_height + 3)
    cr.stroke()

    selection_frame_x = _get_frame_x(data["selected_frame"])

    cr.set_source_rgb(*OVERLAY_SELECTION_COLOR)
    cr.move_to(selection_frame_x - 0.5, track_y - 6.5)
    cr.line_to(selection_frame_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    if data["to_side_being_edited"]:
        _draw_view_icon(cr, frame_x + 6, track_y + 1)
    else:
        _draw_view_icon(cr, frame_x - 18, track_y + 1)

    trim_limits = data["trim_limits"]
    clip_over_start_x = _get_frame_x(trim_limits["both_start"] - 1) # trim limits leave 1 frame non-trimmable
    clip_over_end_x = _get_frame_x(trim_limits["both_end"] + 1) # trim limits leave 1 frame non-trimmable
    cr.set_line_width(2.0)  
    _draw_trim_clip_overlay(cr, clip_over_start_x, clip_over_end_x, track_y, track_height, False, (1,1,1,0.3))

    cr.set_line_width(1.0)
    cr.move_to(clip_over_start_x - 0.5, track_y - 6.5)
    cr.line_to(clip_over_start_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    cr.move_to(clip_over_end_x - 0.5, track_y - 6.5)
    cr.line_to(clip_over_end_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    if trim_status != appconsts.ON_BETWEEN_FRAME:
        if trim_status == appconsts.ON_FIRST_FRAME:
            _draw_end_triangles(cr, selection_frame_x, track_y, track_height, 6)
        else:
            _draw_end_triangles(cr, selection_frame_x, track_y, track_height, -6)

    radius = 5.0
    degrees = M_PI/ 180.0
    bit = 3
    if not trim_mode_in_non_active_state:
        cr.set_source_rgb(0.9, 0.9, 0.2)
    else:
        cr.set_source_rgb(0.2, 0.2, 0.2)
    cr.set_line_width(2.0)
    cr.move_to(selection_frame_x + radius + bit, track_y + track_height)
    cr.arc (selection_frame_x + radius, track_y + track_height - radius, radius, 90 * degrees, 180.0 * degrees) 
    cr.arc (selection_frame_x + radius, track_y + radius, radius,  180.0 * degrees, 270.0 * degrees)
    cr.line_to(selection_frame_x + radius + bit, track_y)
    cr.stroke()
    cr.move_to(selection_frame_x - radius - bit, track_y)
    cr.arc (selection_frame_x - radius, track_y + radius, radius,  -90.0 * degrees, 0.0 * degrees)
    cr.arc (selection_frame_x - radius, track_y + track_height - radius, radius, 0 * degrees, 90.0 * degrees)
    cr.line_to(selection_frame_x - radius - bit, track_y + track_height)
    cr.stroke()

def draw_one_roll_overlay(cr, data):
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    
    selection_frame_x = _get_frame_x(data["selected_frame"])

    trim_limits = data["trim_limits"]
    if data["to_side_being_edited"]:
        # Case: editing to-clip
        first = data["selected_frame"]
        last = trim_limits["both_end"] + 1 # +1, end is allowed trim area, we cant clip
        x = _get_frame_x(last)

    else:
        # Case: editing from-clip
        first = trim_limits["both_start"] - 1 # -1, start is allowed trim area, we cant clip
        last = data["selected_frame"]
        x = _get_frame_x(first)
        
    cr.set_line_width(1.0)
    cr.set_source_rgb(*OVERLAY_COLOR)
    cr.move_to(x, track_y - 6.5)
    cr.line_to(x, track_y + track_height + 6.5)
    cr.stroke()
        
    cr.set_line_width(2.0)
    _draw_trim_clip_overlay(cr, _get_frame_x(first), _get_frame_x(last), track_y, track_height, False, (1,1,1,0.3))
        
    cr.set_source_rgb(*OVERLAY_SELECTION_COLOR)
    cr.move_to(selection_frame_x - 0.5, track_y - 6.5)
    cr.line_to(selection_frame_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    if trim_status != appconsts.ON_BETWEEN_FRAME:
        if trim_status == appconsts.ON_FIRST_FRAME:
            _draw_end_triangles(cr, selection_frame_x, track_y, track_height, 6)
        else:
            _draw_end_triangles(cr, selection_frame_x, track_y, track_height, -6)

    radius = 5.0
    degrees = M_PI/ 180.0
    bit = 3
    if not trim_mode_in_non_active_state:
        cr.set_source_rgb(0.9, 0.9, 0.2)
    else:
        cr.set_source_rgb(0.2, 0.2, 0.2)
    cr.set_line_width(2.0)
    if data["to_side_being_edited"]:
        cr.move_to(selection_frame_x + radius + bit, track_y + track_height)
        cr.arc (selection_frame_x + radius, track_y + track_height - radius, radius, 90 * degrees, 180.0 * degrees) 
        cr.arc (selection_frame_x + radius, track_y + radius, radius,  180.0 * degrees, 270.0 * degrees)
        cr.line_to(selection_frame_x + radius + bit, track_y)
    else:
        cr.move_to(selection_frame_x - radius - bit, track_y)
        cr.arc (selection_frame_x - radius, track_y + radius, radius,  -90.0 * degrees, 0.0 * degrees)
        cr.arc (selection_frame_x - radius, track_y + track_height - radius, radius, 0 * degrees, 90.0 * degrees)
        cr.line_to(selection_frame_x - radius - bit, track_y + track_height)
    cr.stroke()

def draw_slide_overlay(cr, data):
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    trim_limits = data["trim_limits"]
    
    clip = data["clip"]
    clip_start_frame = trim_limits["clip_start"]
    clip_end_frame = clip_start_frame + clip.clip_out - clip.clip_in + 1 # +1 to draw after out frame
    clip_start_frame_x = _get_frame_x(clip_start_frame)
    clip_end_frame_x = _get_frame_x(clip_end_frame)

    cr.set_line_width(2.0)
    media_start = clip_start_frame - data["mouse_delta"] - clip.clip_in
    orig_media_start_frame_x = _get_frame_x(media_start)
    orig_media_end_frame_x = _get_frame_x(media_start + trim_limits["media_length"])
    _draw_trim_clip_overlay(cr, orig_media_start_frame_x, orig_media_end_frame_x, track_y, track_height, False, (0.65,0.65,0.65, 0.65))

    _draw_end_triangles(cr, orig_media_start_frame_x, track_y, track_height, 6)
    _draw_end_triangles(cr, orig_media_end_frame_x, track_y, track_height, -6)
          
    cr.set_line_width(2.0)
    cr.set_source_rgb(*OVERLAY_SELECTION_COLOR)
    orig_clip_start_frame_x = _get_frame_x(clip_start_frame - data["mouse_delta"])
    orig_clip_end_frame_x = _get_frame_x(clip_end_frame - data["mouse_delta"])
    _draw_trim_clip_overlay(cr, orig_clip_start_frame_x, orig_clip_end_frame_x, track_y, track_height, False, (1,1,1,0.3))
        
    cr.move_to(clip_start_frame_x - 0.5, track_y - 6.5)
    cr.line_to(clip_start_frame_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    cr.move_to(clip_end_frame_x - 0.5, track_y - 6.5)
    cr.line_to(clip_end_frame_x - 0.5, track_y + track_height + 6.5)
    cr.stroke()

    radius = 5.0
    degrees = M_PI/ 180.0
    bit = 3
    if not trim_mode_in_non_active_state:
        cr.set_source_rgb(0.9, 0.9, 0.2)
    else:
        cr.set_source_rgb(0.2, 0.2, 0.2)
    cr.set_line_width(2.0)
    cr.move_to(clip_start_frame_x - radius - bit, track_y)
    cr.arc (clip_start_frame_x - radius, track_y + radius, radius,  -90.0 * degrees, 0.0 * degrees)
    cr.arc (clip_start_frame_x - radius, track_y + track_height - radius, radius, 0 * degrees, 90.0 * degrees)
    cr.line_to(clip_start_frame_x - radius - bit, track_y + track_height)
    cr.move_to(clip_end_frame_x + radius + bit, track_y + track_height)
    cr.arc (clip_end_frame_x + radius, track_y + track_height - radius, radius, 90 * degrees, 180.0 * degrees) 
    cr.arc (clip_end_frame_x + radius, track_y + radius, radius,  180.0 * degrees, 270.0 * degrees)
    cr.line_to(clip_end_frame_x + radius + bit, track_y)
    cr.stroke()

    if data["start_frame_being_viewed"]:
        x = clip_start_frame_x + 4
    else:
        x = clip_end_frame_x - 16

    cr.set_source_pixbuf(VIEW_SIDE_ICON, x, track_y + 4)
    cr.paint()

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

    target_track = current_sequence().tracks[compositor.transition.a_track]
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
    both directions in a trim mode
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

def _draw_end_triangles(cr, x, y, h, direction):
    triangles = 4
    if h < appconsts.TRACK_HEIGHT_NORMAL:
        triangles = 2
    cr.set_source_rgb(1, 1, 1)
    for i in range(0, triangles):
        cr.move_to(x, y + 2.5)
        cr.line_to(x + direction, y + 7.0)
        cr.line_to(x, y + 11.5)
        cr.close_path()
        cr.fill()
        y = y + 12.0

def _draw_trim_clip_overlay(cr, start_x, end_x, y, track_height, draw_stroke, color=(1,1,1,1)):
    cr.set_source_rgba(*color)
    cr.rectangle(start_x, y, end_x - start_x, track_height)
    if draw_stroke:
        cr.stroke()
    else:
        cr.fill()

def _draw_overwrite_clips_overlay(cr, start_x, end_x, y, track_height):
    cr.set_source_rgba(*OVERWRITE_OVERLAY_COLOR)
    cr.rectangle(start_x, y, end_x - start_x, track_height)
    cr.fill()

def _draw_view_icon(cr, x, y):
    cr.set_source_pixbuf(VIEW_SIDE_ICON, x, y)
    cr.paint()

# ------------------------------- WIDGETS
class TimeLineCanvas:
    """
    GUI component for editing clips.
    """

    def __init__(self, press_listener, move_listener, release_listener, double_click_listener,
                    mouse_scroll_listener, leave_notify_listener, enter_notify_listener):
        # Create widget and connect listeners
        self.widget = CairoDrawableArea(WIDTH, 
                                        HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = mouse_scroll_listener
        #self.widget.set_events(self.widget.get_events() | gtk.gdk.POINTER_MOTION_MASK)

        # Mouse events are passed on 
        self.press_listener = press_listener
        self.move_listener = move_listener
        self.release_listener = release_listener
        self.double_click_listener = double_click_listener

        self.widget.leave_notify_func = leave_notify_listener
        self.widget.enter_notify_func = enter_notify_listener
        
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
            self.set_pointer_context(x, y)
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

    def set_pointer_context(self, x, y):
        frame = get_frame(x)
        hit_compositor = compositor_hit(frame, y, current_sequence().compositors)
        if hit_compositor != None:
            print "comp"
            return

        track = get_track(y)  
        if track == None:
            return    

        clip_index = current_sequence().get_clip_index(track, frame)
        if clip_index == -1:
            return

        clip_start_frame = track.clip_start(clip_index) - pos
        if abs(x - _get_frame_x(clip_start_frame)) < 5:
            print "clip start"
            return

        clip_end_frame = track.clip_start(clip_index + 1) - pos
        if abs(x - _get_frame_x(clip_end_frame)) < 5:
            print "clip end"
            return

    #----------------------------------------- DRAW
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(*BG_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # This can get called during loads by unwanted expose events
        if editorstate.project_is_loading == True:
            return

        # Init sync draw structures
        self.parent_positions = {}
        self.sync_children = []

        # Draw tracks
        for i in range(1, len(current_sequence().tracks) - 1): # black and hidden tracks are ignored
            self.draw_track(cr
                            ,current_sequence().tracks[i]
                            ,_get_track_y(i)
                            ,w)

        self.draw_compositors(cr)
        self.draw_sync_relations(cr)

        # Exit displaying from fake_current_pointer for SLIDE_TRIM mode if last displayed 
        # was from fake_pointer but this is not anymore
        global fake_current_frame
        if EDIT_MODE() != editorstate.SLIDE_TRIM and fake_current_frame != None:
            PLAYER().seek_frame(fake_current_frame)
            fake_current_frame = None
            
        # Draw frame pointer
        if EDIT_MODE() != editorstate.SLIDE_TRIM or PLAYER().looping():
            current_frame = PLAYER().tracktor_producer.frame()
        else:
            current_frame = fake_current_frame

        if timeline_visible():
            pointer_frame = current_frame
            cr.set_source_rgb(0, 0, 0)
        else:
            pointer_frame = editorstate.tline_shadow_frame
            cr.set_source_rgb(*SHADOW_POINTER_COLOR)
        disp_frame = pointer_frame - pos
        frame_x = math.floor(disp_frame * pix_per_frame) + 0.5
        cr.move_to(frame_x, 0)
        cr.line_to(frame_x, h)
        cr.set_line_width(1.0)
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

        # Get clip indexes for clips overlapping first and last displayed frame.
        start = track.get_clip_index_at(int(pos))
        end = track.get_clip_index_at(int(pos + width / pix_per_frame))

        width_frames = float(width) / pix_per_frame

        # Add 1 to end because range() last index exclusive 
        # MLT returns clips structure size + 1 if frame after last clip,
        # so in that case don't add anything.
        if len(track.clips) != end:
            end = end + 1
            
        # Get frame of clip.clip_in_in on timeline.
        clip_start_in_tline = track.clip_start(start)

        # Pos is the first drawn frame.
        # clip_start_frame starts always less or equal to zero as this is
        # the first maybe partially displayed clip.
        clip_start_frame = clip_start_in_tline - pos

        # Check if we need to collect positions for drawing sync relations 
        collect_positions = False
        if track.id == current_sequence().first_video_index:
            collect_positions = True

        proxy_paths = current_proxy_media_paths()

        # Draw clips in draw range
        for i in range(start, end):

            clip = track.clips[i]

            # Get clip frame values
            clip_in = clip.clip_in
            clip_out = clip.clip_out
            clip_length = clip_out - clip_in + 1 # +1 because in and out both inclusive
            scale_length = clip_length * pix_per_frame
            scale_in = clip_start_frame * pix_per_frame
            
            # Collect positions for drawing sync relations 
            if collect_positions:
                self.parent_positions[clip.id] = scale_in
            
            # Fill clip bg 
            if scale_length > FILL_MIN:
                # Select color
                clip_bg_col = None
                if clip.color != None:
                    cr.set_source_rgb(*clip.color)
                    clip_bg_col = clip.color
                elif clip.is_blanck_clip:
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
                            clip_bg_col = CLIP_COLOR_GRAD[1:4]
                            cr.set_source(grad)
                        else:
                            cr.set_source_rgb(*CLIP_SELECTED_COLOR)
                            clip_bg_col = CLIP_SELECTED_COLOR
                    else: # IMAGE type
                        if not clip.selected:
                            grad = cairo.LinearGradient (0, y, 0, y + track_height)
                            grad.add_color_stop_rgba(*IMAGE_CLIP_COLOR_GRAD)
                            grad.add_color_stop_rgba(*IMAGE_CLIP_COLOR_GRAD_L)
                            clip_bg_col = IMAGE_CLIP_COLOR_GRAD[1:4]
                            cr.set_source(grad)
                        else:
                            cr.set_source_rgb(*IMAGE_CLIP_SELECTED_COLOR)
                            clip_bg_col = IMAGE_CLIP_SELECTED_COLOR
                else:
                    if not clip.selected:
                        grad = cairo.LinearGradient (0, y, 0, y + track_height)
                        grad.add_color_stop_rgba(*AUDIO_CLIP_COLOR_GRAD)
                        grad.add_color_stop_rgba(*AUDIO_CLIP_COLOR_GRAD_L)
                        clip_bg_col = AUDIO_CLIP_COLOR_GRAD[1:4]
                        cr.set_source(grad)
                    else:
                        clip_bg_col = AUDIO_CLIP_SELECTED_COLOR
                        cr.set_source_rgb(*AUDIO_CLIP_SELECTED_COLOR)
                
                # Clip bg
                cr.rectangle(scale_in, y, scale_length, track_height)
                cr.fill()

            # Draw transition clip image 
            if ((scale_length > FILL_MIN) and hasattr(clip, "rendered_type")):
                if not clip.selected:
                    cr.set_source_rgb(1.0, 1.0, 1.0)
                else:
                    cr.set_source_rgb(*SINGLE_TRACK_TRANSITION_SELECTED)

                cr.rectangle(scale_in + 2.5,
                         y + 2.5, scale_length - 4.0, 
                         track_height - 4.0)
                cr.fill()

                right = scale_in + 2.5 + scale_length - 6.0
                right_half = scale_in + 2.5 + ((scale_length - 6.0) / 2.0)
                down = y + 2.5 + track_height - 6.0
                down_half = y + 2.5 + ((track_height - 6.0) / 2.0)
                cr.set_source_rgb(0, 0, 0)
                
                if clip.rendered_type == appconsts.RENDERED_DISSOLVE:
                    cr.move_to(right, y + 4.5)
                    cr.line_to(right, down)
                    cr.line_to(scale_in + 4.5, down)
                    cr.close_path()
                    cr.fill()
                elif clip.rendered_type == appconsts.RENDERED_WIPE:
                    cr.rectangle(scale_in + 2.0, y + 2.0, scale_length - 4.0, track_height - 4.0)
                    cr.fill()
                    if not clip.selected:
                        cr.set_source_rgb(1.0, 1.0, 1.0)
                    else:
                        cr.set_source_rgb(*SINGLE_TRACK_TRANSITION_SELECTED)
                    cr.move_to(right_half, y + 3.0 + 2.0)
                    cr.line_to(right - 2.0, down_half)
                    cr.line_to(right_half, down - 2.0)
                    cr.line_to(scale_in + 2.0 + 4.0, down_half)
                    cr.close_path()
                    cr.fill()
                elif clip.rendered_type == appconsts.RENDERED_COLOR_DIP:
                    cr.move_to(scale_in + 4.5, y + 4.5)
                    cr.line_to(right, y + 4.5)
                    cr.line_to(right_half, down)
                    cr.close_path()
                    cr.fill()       
                elif clip.rendered_type == appconsts.RENDERED_FADE_IN:
                    cr.move_to(scale_in + 4.5, y + 4.5)
                    cr.line_to(right, y + 4.5)
                    cr.line_to(scale_in + 4.5, down_half)
                    cr.close_path()
                    cr.fill()
                    cr.move_to(scale_in + 4.5, down_half)
                    cr.line_to(right, down)
                    cr.line_to(scale_in + 4.5, down)
                    cr.close_path()
                    cr.fill()
                else: # clip.rendered_type == appconsts.RENDERED_FADE_OUT:
                    cr.move_to(scale_in + 4.5, y + 4.5)
                    cr.line_to(right, y + 4.5)
                    cr.line_to(right, down_half)
                    cr.close_path()
                    cr.fill()
                    cr.move_to(right, down_half)
                    cr.line_to(right, down)
                    cr.line_to(scale_in + 4.5, down)
                    cr.close_path()
                    cr.fill()

            # Draw sync stripe
            if scale_length > FILL_MIN: 
                if clip.sync_data != None:
                    stripe_color = SYNC_OK_COLOR
                    if clip.sync_data.sync_state == appconsts.SYNC_CORRECT:
                        stripe_color = SYNC_OK_COLOR
                    elif clip.sync_data.sync_state == appconsts.SYNC_OFF:
                        stripe_color = SYNC_OFF_COLOR
                    else:
                        stripe_color = SYNC_GONE_COLOR

                    dx = scale_in + 1
                    dy = y + track_height - SYNC_STRIPE_HEIGHT
                    saw_points = []
                    saw_points.append((dx, dy))
                    saw_delta = SYNC_SAW_HEIGHT
                    for i in range(0, int((scale_length - 2) / SYNC_SAW_WIDTH) + 1):
                        dx += SYNC_SAW_WIDTH
                        dy += saw_delta
                        saw_points.append((dx, dy))
                        saw_delta = -(saw_delta)

                    px = scale_in + 1 + scale_length - 2
                    py = y + track_height
                    cr.move_to(px, py)
                    for p in reversed(saw_points):
                        cr.line_to(*p)
                    cr.line_to(scale_in + 1, y + track_height)
                    cr.close_path()

                    cr.set_source_rgb(*stripe_color)
                    cr.fill_preserve()
                    cr.set_source_rgb(0.3, 0.3, 0.3)
                    cr.stroke()
                    
                    if clip.sync_data.sync_state != appconsts.SYNC_CORRECT:
                        cr.set_source_rgb(1, 1, 1)
                        cr.select_font_face ("sans-serif",
                                             cairo.FONT_SLANT_NORMAL,
                                             cairo.FONT_WEIGHT_NORMAL)
                        cr.set_font_size(9)
                        cr.move_to(scale_in + TEXT_X, y + track_height - 2)
                        try: # This is needed for backwards compability
                             # Projects saved before adding this feature do not have sync_diff attribute
                            cr.show_text(str(clip.sync_diff))
                        except:
                            clip.sync_diff = "n/a"
                            cr.show_text(str(clip.sync_diff))

            # Draw proxy indicator
            if scale_length > FILL_MIN:
                if (not clip.is_blanck_clip) and proxy_paths.get(clip.path) != None:
                    cr.set_source_rgb(*PROXY_STRIP_COLOR)
                    cr.rectangle(scale_in, y, scale_length, 8)
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
        
            # No further drawing for blank clips
            if clip.is_blanck_clip:
                clip_start_frame += clip_length
                continue

            # Save sync children data
            if clip.sync_data != None:
                self.sync_children.append((clip, track, scale_in))

            # Draw audio level data
            if clip.waveform_data != None and scale_length > FILL_MIN:
                r, g, b = clip_bg_col
                cr.set_source_rgb(r * 0.7, g * 0.7, b * 0.7)

                # Get level bar height and position for track height
                if track.height == sequence.TRACK_HEIGHT_NORMAL:
                    y_pad = WAVEFORM_PAD_LARGE
                    bar_height = 40.0
                else:
                    y_pad = WAVEFORM_PAD_SMALL
                    bar_height = 20.0
                
                # Draw all frames only if pixels per frame > 2, otherwise
                # draw only every other or fewer frames
                draw_pix_per_frame = pix_per_frame
                if draw_pix_per_frame < 2:
                    draw_pix_per_frame = 2
                    step = int(2 / pix_per_frame)
                    if step < 1:
                        step = 1
                else:
                    step = 1

                # Draw only frames in display
                draw_first = clip_in
                draw_last = clip_out + 1
                if clip_start_frame < 0:
                    draw_first = int(draw_first - clip_start_frame)
                if draw_first + width_frames < draw_last:
                    draw_last = int(draw_first + width_frames) + 1

                # Get media frame 0 position in screen pixels
                media_start_pos_pix = scale_in - clip_in * pix_per_frame
                
                # Draw level bar for each frame in draw range
                for i in range(draw_first, draw_last, step):
                    x = media_start_pos_pix + i * pix_per_frame
                    h = bar_height * clip.waveform_data[i]
                    if h < 1:
                        h = 1
                    cr.rectangle(x, y + y_pad + (bar_height - h), draw_pix_per_frame, h)

                cr.fill()

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

            # Draw text and filter, sync icons
            if scale_length > TEXT_MIN:
                if not hasattr(clip, "rendered_type"):
                    # Text
                    cr.set_source_rgb(0, 0, 0)
                    cr.select_font_face ("sans-serif",
                                         cairo.FONT_SLANT_NORMAL,
                                         cairo.FONT_WEIGHT_NORMAL)
                    cr.set_font_size(11)
                    cr.move_to(scale_in + TEXT_X, y + text_y)
                    cr.show_text(clip.name.upper())
                
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

                if clip == clipeffectseditor.clip:
                    icon = EDIT_INDICATOR
                    ix =  int(scale_in) + int(scale_length) / 2 - 7
                    iy = y + int(track_height) / 2 - 7
                    cr.set_source_pixbuf(icon, ix, iy)
                    cr.paint()
                    
            # Draw sync offset value
            if scale_length > FILL_MIN: 
                if clip.sync_data != None:
                    if clip.sync_data.sync_state != appconsts.SYNC_CORRECT:
                        cr.set_source_rgb(1, 1, 1)
                        cr.select_font_face ("sans-serif",
                                             cairo.FONT_SLANT_NORMAL,
                                             cairo.FONT_WEIGHT_NORMAL)
                        cr.set_font_size(9)
                        cr.move_to(scale_in + TEXT_X, y + track_height - 2)
                        cr.show_text(str(clip.sync_diff))
                        
            # Get next draw position
            clip_start_frame += clip_length

        # Fill rest of track with bg color if needed
        scale_in = clip_start_frame  * pix_per_frame
        if scale_in < width:
            cr.rectangle(scale_in + 0.5, y, width - scale_in, track_height)
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

    def draw_sync_relations(self, cr):
        parent_y = _get_track_y(current_sequence().first_video_index)
        radius = 4
        small_radius = 2
        pad = 6
        degrees = M_PI / 180.0
        for child_data in self.sync_children:
            child_clip, track, child_x = child_data
            child_y = _get_track_y(track.id)
            try:
                parent_x = self.parent_positions[child_clip.sync_data.master_clip.id]
            except KeyError: # parent clip not in tline view, don't draw - think about another solution
                continue
                
            cr.set_line_width(2.0)
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.move_to(child_x + pad, child_y + pad)
            cr.line_to(parent_x + pad, parent_y + pad)
            cr.stroke()
            
            cr.move_to(child_x + pad, child_y + pad)
            cr.arc (child_x + pad, child_y + pad, radius, 0.0 * degrees, 360.0 * degrees)
            cr.fill()
            
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.move_to(child_x + pad, child_y + pad)
            cr.arc (child_x + pad, child_y + pad, small_radius, 0.0 * degrees, 360.0 * degrees)
            cr.fill()

            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.move_to(parent_x + pad, parent_y + pad)
            cr.arc(parent_x + pad, parent_y + pad, radius,  0.0 * degrees, 360.0 * degrees)
            cr.fill()

            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.move_to(parent_x + pad, parent_y + pad)
            cr.arc(parent_x + pad, parent_y + pad, small_radius,  0.0 * degrees, 360.0 * degrees)
            cr.fill()


class TimeLineColumn:
    """
    GUI component for displaying and editing track parameters.
    """

    def __init__(self, active_listener, center_listener):
        # Init widget
        self.widget = CairoDrawableArea(COLUMN_WIDTH, 
                                        HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        
        self.active_listener = active_listener
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
        center_width = COLUMN_WIDTH - COLUMN_LEFT_PAD - ACTIVE_SWITCH_WIDTH
        tester = ValueTester(COLUMN_LEFT_PAD + center_width, COLUMN_WIDTH, 
                             self.active_listener)
        self.switch_testers.append(tester)

        # Center area tester
        tester = ValueTester(COLUMN_LEFT_PAD, COLUMN_WIDTH - ACTIVE_SWITCH_WIDTH, 
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
        center_width = COLUMN_WIDTH - COLUMN_LEFT_PAD - ACTIVE_SWITCH_WIDTH
        rect = (COLUMN_LEFT_PAD, y, center_width, track.height)
        grad = cairo.LinearGradient (COLUMN_LEFT_PAD, y, COLUMN_LEFT_PAD, y + track.height)
        self._add_gradient_color_stops(grad, track)
        cr.rectangle(*rect)
        cr.set_source(grad)
        cr.fill()
        self.draw_edge(cr, rect)
        
        # Draw active switch bg end edge
        rect = (COLUMN_LEFT_PAD + center_width - 1, y, ACTIVE_SWITCH_WIDTH + 1, track.height)
        cr.rectangle(*rect)
        if track.active:
            grad = cairo.LinearGradient(COLUMN_LEFT_PAD + center_width, y,
                                        COLUMN_LEFT_PAD + center_width, y + track.height)
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
        pango_context.move_to(COLUMN_LEFT_PAD + ID_PAD_X, y + text_y)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)
        
        # Draw mute icon
        mute_icon = None
        if track.mute_state == appconsts.TRACK_MUTE_VIDEO and track.type == appconsts.VIDEO:
            mute_icon = MUTE_VIDEO_ICON
        elif track.mute_state == appconsts.TRACK_MUTE_AUDIO and track.type == appconsts.VIDEO:
            mute_icon = MUTE_AUDIO_ICON
        elif track.mute_state == appconsts.TRACK_MUTE_ALL and track.type == appconsts.AUDIO:
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
            grad.add_color_stop_rgba(*TRACK_GRAD_ORANGE_STOP3)
        else:
            grad.add_color_stop_rgba(*TRACK_GRAD_STOP1)
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

        if editorpersistance.prefs.dark_theme == True:
            global FRAME_SCALE_SELECTED_COLOR_GRAD, FRAME_SCALE_SELECTED_COLOR_GRAD_L 
            FRAME_SCALE_SELECTED_COLOR_GRAD = DARK_FRAME_SCALE_SELECTED_COLOR_GRAD
            FRAME_SCALE_SELECTED_COLOR_GRAD_L = DARK_FRAME_SCALE_SELECTED_COLOR_GRAD_L

    def _press_event(self, event):
        if event.button == 1 or event.button == 3:
            if not timeline_visible():
                updater.display_sequence_in_monitor()
                return
            trimmodes.set_no_edit_trim_mode()
            frame = current_sequence().get_seq_range_frame(get_frame(event.x))
            PLAYER().seek_frame(frame)
            self.drag_on = True

    def _motion_notify_event(self, x, y, state):
        if((state & gtk.gdk.BUTTON1_MASK)
           or(state & gtk.gdk.BUTTON3_MASK)):
            if self.drag_on:
                frame = current_sequence().get_seq_range_frame(get_frame(x))
                PLAYER().seek_frame(frame) 
                
    def _release_event(self, event):
        if self.drag_on:
            frame = current_sequence().get_seq_range_frame(get_frame(event.x))
            PLAYER().seek_frame(frame) 
        
        self.drag_on = False

    # --------------------------------------------- DRAW
    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw grad bg
        grad = cairo.LinearGradient (0, 0, 0, h)
        grad.add_color_stop_rgba(*FRAME_SCALE_COLOR_GRAD)
        grad.add_color_stop_rgba(*FRAME_SCALE_COLOR_GRAD_L)
        cr.set_source(grad)
        cr.rectangle(0,0,w,h)
        cr.fill()

        # This can get called during loads by unwanted expose events
        if editorstate.project_is_loading == True:
            return

        # Get sequence and frames per second value
        seq = current_sequence()
        fps = seq.profile.fps()
        
        # Selected range
        if seq.tractor.mark_in != -1 and seq.tractor.mark_out != -1:
            in_x = (seq.tractor.mark_in - pos) * pix_per_frame
            out_x = (seq.tractor.mark_out + 1 - pos) * pix_per_frame
            grad = cairo.LinearGradient (0, 0, 0, h)
            grad.add_color_stop_rgba(*FRAME_SCALE_SELECTED_COLOR_GRAD)
            cr.set_source(grad)
            cr.rectangle(in_x,0,out_x-in_x,h)
            cr.fill()
            
        # Set line attr for frames lines
        cr.set_source_rgb(*FRAME_SCALE_LINES)
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
        if EDIT_MODE() != editorstate.SLIDE_TRIM or PLAYER().looping():
            current_frame = PLAYER().tracktor_producer.frame()
        else:
            current_frame = fake_current_frame

        if timeline_visible():
            cr.set_source_rgb(0, 0, 0)
            line_color = (0, 0, 0)
        else:
            current_frame = editorstate.tline_shadow_frame
            line_color = (0.8, 0.8, 0.8)

        disp_frame = current_frame - pos
        frame_x = math.floor(disp_frame * pix_per_frame) + 0.5
        cr.set_source_rgb(*line_color)
        cr.move_to(frame_x, 0)
        cr.line_to(frame_x, h)
        cr.stroke()

        # Draw pos triangle
        cr.set_source_pixbuf(TC_POINTER_HEAD, frame_x - 7.5, 0)
        cr.paint()

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
