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
import math

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
from gi.repository import PangoCairo

import appconsts
import audiowaveformrenderer
import boxmove
import cairoarea
import clipeffectseditor
import compositormodes
import editorpersistance
from editorstate import current_sequence
from editorstate import timeline_visible
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import EDIT_MODE
from editorstate import current_proxy_media_paths
import editorstate
import gui
import respaths
import sequence
import snapping
import trimmodes
import utils
import updater

M_PI = math.pi

REF_LINE_Y = 250 # Y pos of tracks are relative to this. This is recalculated on initilization, so value here is irrelevent.

WIDTH = 430 # this has no effect if smaller then editorwindow.NOTEBOOK_WIDTH + editorwindow.MONITOR_AREA_WIDTH
HEIGHT = appconsts.TLINE_HEIGHT # defines window min height together with editorwindow.TOP_ROW_HEIGHT

# Timeline draw constants
# Other elements than black outline are not drawn if clip screen size
# in pixels is below certain thresholds
TEXT_MIN = 12 # if clip shorter, no text
EMBOSS_MIN = 8 # if clip shorter, no emboss
FILL_MIN = 1 # if clip shorter, no fill
TEXT_X = 6 # pos for clip text
TEXT_Y = 29 
TEXT_Y_SMALL = 17
WAVEFORM_PAD_LARGE = 27
WAVEFORM_PAD_SMALL = 8
WAVEFORM_HEIGHT_LARGE = 22.0
WAVEFORM_HEIGHT_SMALL = 17.0
MARK_PAD = 6
MARK_LINE_WIDTH = 4

# tracks column consts
COLUMN_WIDTH = 124 # column area width
SCALE_HEIGHT = 25
SCROLL_HEIGHT = 20
COLUMN_LEFT_PAD = 0 # as mute switch no longer exists this is now essentially left pad width 
ACTIVE_SWITCH_WIDTH = 18
COMPOSITOR_HEIGHT_OFF = 10
COMPOSITOR_HEIGHT = 20
COMPOSITOR_TEXT_X = 6
COMPOSITOR_TEXT_Y = 15
COMPOSITOR_TRACK_X_PAD = 4
COMPOSITOR_TRACK_ARROW_WIDTH = 6
COMPOSITOR_TRACK_ARROW_HEAD_WIDTH = 10
COMPOSITOR_TRACK_ARROW_HEAD_WIDTH_HEIGHT = 5
ID_PAD_X = 48 # track id text pos
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
LOCK_POS = (90, 5)
INSRT_ICON_POS = (108, 18)
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
CLIP_MARKER_ICON = None
LEVELS_RENDER_ICON = None
SNAP_ICON = None
KEYBOARD_ICON = None
CLOSE_MATCH_ICON = None

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

#CLIP_COLOR = (0.62, 0.38, 0.7) 0.18, 0.11 0.21
#CLIP_COLOR_L = get_multiplied_color(CLIP_COLOR, GRAD_MULTIPLIER)
CLIP_TEXT_COLOR = (0, 0, 0)
CLIP_TEXT_COLOR_OVERLAY = (0.78, 0.78, 0.78, 0.6)

CLIP_COLOR_GRAD = (1,  0.18, 0.11, 0.21, 1)  #(1, 0.62, 0.38, 0.7, 1) 
CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, CLIP_COLOR_GRAD, GRAD_MULTIPLIER) 
CLIP_SELECTED_COLOR = get_multiplied_color_from_grad(CLIP_COLOR_GRAD, SELECTED_MULTIPLIER)
CLIP_END_DRAG_OVERLAY_COLOR = (1,1,1,0.3)

AUDIO_CLIP_COLOR_GRAD = (1, 0.09, 0.21, 0.09, 1)#(1, 0.23, 0.52, 0.23, 1)#(1, 0.79, 0.80, 0.18, 1)
AUDIO_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, AUDIO_CLIP_COLOR_GRAD, GRAD_MULTIPLIER)
AUDIO_CLIP_SELECTED_COLOR = (0.53, 0.85, 0.53)

IMAGE_CLIP_SELECTED_COLOR = (0.45, 0.90, 0.93)
IMAGE_CLIP_COLOR_GRAD = (1, 0.1, 0.20, 0.21, 1) #(1, 0.33, 0.65, 0.69, 1)
IMAGE_CLIP_COLOR_GRAD_L = get_multiplied_grad(0, 1, IMAGE_CLIP_COLOR_GRAD, GRAD_MULTIPLIER) 

COMPOSITOR_CLIP = (0.12, 0.12, 0.22, 0.7)
COMPOSITOR_CLIP_AUTO_FOLLOW = (0.33, 0.05, 0.52, 0.65)
COMPOSITOR_CLIP_SELECTED = (0.5, 0.5, 0.7, 0.8)

BLANK_CLIP_COLOR_GRAD = (1, 0.6, 0.6, 0.65, 1)
BLANK_CLIP_COLOR_GRAD_L = (0, 0.6, 0.6, 0.65, 1)

BLANK_CLIP_COLOR_SELECTED_GRAD = (1, 0.80, 0.80, 0.80, 1)
BLANK_CLIP_COLOR_SELECTED_GRAD_L = (0, 0.80, 0.80, 0.80, 1)

SINGLE_TRACK_TRANSITION_SELECTED = (0.8, 0.8, 1.0)

SYNC_OK_COLOR = (0.18, 0.55, 0.18)
SYNC_OFF_COLOR = (0.77, 0.20, 0.3)
SYNC_GONE_COLOR = (0.4, 0.4, 0.4)

PROXY_STRIP_COLOR = (0.40, 0.60, 0.82)
PROXY_STRIP_COLOR_SELECTED = (0.52, 0.72, 0.96)

MARK_COLOR = (0.1, 0.1, 0.1)

FRAME_SCALE_COLOR_GRAD = (1, 0.8, 0.8, 0.8, 1)
FRAME_SCALE_COLOR_GRAD_L = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, GRAD_MULTIPLIER)

FRAME_SCALE_SELECTED_COLOR_GRAD = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, 0.92)
FRAME_SCALE_SELECTED_COLOR_GRAD_L = get_multiplied_grad(1, 1, FRAME_SCALE_SELECTED_COLOR_GRAD, GRAD_MULTIPLIER) 

DARK_FRAME_SCALE_SELECTED_COLOR_GRAD = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, 0.7)
DARK_FRAME_SCALE_SELECTED_COLOR_GRAD_L = get_multiplied_grad(1, 1, FRAME_SCALE_SELECTED_COLOR_GRAD, GRAD_MULTIPLIER * 0.8) 

ICON_SELECTED_OVERLAY_COLOR = (0.8, 0.8, 1.0, 0.3)

# Dash pattern used by Box tool
BOX_DASH_INK = 12.0
BOX_DASH_SKIP = 3.0
BOX_DASHES = [BOX_DASH_INK, BOX_DASH_SKIP, BOX_DASH_INK, BOX_DASH_SKIP]

FRAME_SCALE_LINES = (0, 0, 0)

BG_COLOR = (0.5, 0.5, 0.55)

#COLUMN_NOT_ACTIVE_COLOR = (0.65, 0.65, 0.65)
COLUMN_NOT_ACTIVE_COLOR = (0.32, 0.32, 0.34)

OVERLAY_COLOR = (0.9,0.9,0.9)
OVERLAY_SELECTION_COLOR = (0.9,0.9,0.0)
CLIP_OVERLAY_COLOR = (0.2, 0.2, 0.9, 0.5)
OVERWRITE_OVERLAY_COLOR = (0.2, 0.2, 0.2, 0.5)
INSERT_MODE_COLOR = (0.9,0.9,0.0)
OVERWRITE_MODE_COLOR = (0.9,0.0,0.0)
OVERLAY_TRIM_COLOR = (0.81, 0.82, 0.3)
BOX_BOUND_COLOR =(0.137, 0.80, 0.85)
TRIM_MAX_RED = (1.0,0.1,0.1)

POINTER_TRIANGLE_COLOR = (0.6, 0.7, 0.8, 0.7)
SHADOW_POINTER_COLOR = (0.5, 0.5, 0.5)

MATCH_FRAME_LINES_COLOR = (0.78, 0.31, 0.31)

BLANK_SELECTED = (0.68, 0.68, 0.74)

TRACK_NAME_COLOR = (0.0,0.0,0.0) # 
#TRACK_NAME_COLOR = (0.9,0.9,0.9)

TRACK_GRAD_STOP1 = (1, 0.5, 0.5, 0.55, 1) #0.93, 0.93, 0.93, 1)
TRACK_GRAD_STOP3 = (0, 0.5, 0.5, 0.55, 1) #0.58, 0.58, 0.58, 1) #(0, 0.84, 0.84, 0.84, 1)

"""
TRACK_GRAD_STOP1 = (1, 0.68, 0.68, 0.68, 1) #0.93, 0.93, 0.93, 1)
TRACK_GRAD_STOP3 = (0, 0.93, 0.93, 0.93, 1) #0.58, 0.58, 0.58, 1) 
"""

TRACK_GRAD_ORANGE_STOP1 = (1, 0.65, 0.65, 0.65, 1)
TRACK_GRAD_ORANGE_STOP3 = (0, 0.65, 0.65, 0.65, 1)

"""
TRACK_GRAD_STOP1 = (1,  0.12, 0.14, 0.2, 1)
TRACK_GRAD_STOP1 = (1,  0.12, 0.14, 0.2, 1)
"""
LIGHT_MULTILPLIER = 1.14
DARK_MULTIPLIER = 0.74

POINTER_COLOR = (1, 0.3, 0.3) # red frame pointer for position bar

# ------------------------------------------------------------------ MODULE STATE
# debug purposes
draw_blank_borders = True

# Draw state
pix_per_frame = 5.0 # Current draw scale. This set set elsewhere on init so default value irrelevant.
pos = 0 # Current left most frame in timeline display

# A context defining action taken when mouse press happens based on edit mode and mouse position.
# Cursor communicates current pointer contest to user.
pointer_context = appconsts.POINTER_CONTEXT_NONE
DRAG_SENSITIVITY_AREA_WIDTH_PIX = 10

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

# Dict for clip thumbnails path -> image
clip_thumbnails = {}

# Timeline match image
match_frame = -1
match_frame_track_index = -1
image_on_right = True 
match_frame_image = None
match_frame_width = 1
match_frame_height = 1


# ------------------------------------------------------------------- module functions
def load_icons():
    global FULL_LOCK_ICON, FILTER_CLIP_ICON, VIEW_SIDE_ICON,\
    COMPOSITOR_CLIP_ICON, INSERT_ARROW_ICON, AUDIO_MUTE_ICON, MARKER_ICON, \
    VIDEO_MUTE_ICON, ALL_MUTE_ICON, TRACK_BG_ICON, MUTE_AUDIO_ICON, MUTE_VIDEO_ICON, MUTE_ALL_ICON, \
    TRACK_ALL_ON_V_ICON, TRACK_ALL_ON_A_ICON, MUTE_AUDIO_A_ICON, TC_POINTER_HEAD, EDIT_INDICATOR, \
    LEVELS_RENDER_ICON, SNAP_ICON, KEYBOARD_ICON, CLOSE_MATCH_ICON, CLIP_MARKER_ICON

    FULL_LOCK_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "full_lock.png")
    FILTER_CLIP_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "filter_clip_icon_sharp.png")
    COMPOSITOR_CLIP_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "compositor.png")
    VIEW_SIDE_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "view_side.png")
    INSERT_ARROW_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "insert_arrow.png")
    AUDIO_MUTE_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH +"clip_audio_mute.png")
    VIDEO_MUTE_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH +"clip_video_mute.png")
    ALL_MUTE_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "clip_all_mute.png")
    TRACK_BG_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "track_bg.png")
    MUTE_AUDIO_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "track_audio_mute.png")
    MUTE_VIDEO_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "track_video_mute.png")
    MUTE_ALL_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "track_all_mute.png")
    LEVELS_RENDER_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "audio_levels_render.png")
    SNAP_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "snap_magnet.png")
    KEYBOARD_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "keyb_trim.png")
    CLOSE_MATCH_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "close_match.png")
    CLIP_MARKER_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "clip_marker.png")

    MARKER_ICON = _load_pixbuf("marker.png")
    TRACK_ALL_ON_V_ICON = _load_pixbuf("track_all_on_V.png")
    TRACK_ALL_ON_A_ICON = _load_pixbuf("track_all_on_A.png")
    MUTE_AUDIO_A_ICON = _load_pixbuf("track_audio_mute_A.png") 
    TC_POINTER_HEAD = _load_pixbuf("tc_pointer_head.png")
    EDIT_INDICATOR = _load_pixbuf("clip_edited.png")

    if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
        global FRAME_SCALE_COLOR_GRAD, FRAME_SCALE_COLOR_GRAD_L, BG_COLOR, FRAME_SCALE_LINES, TRACK_GRAD_STOP1, TRACK_GRAD_STOP3, TRACK_NAME_COLOR,  \
                TRACK_GRAD_ORANGE_STOP1, TRACK_GRAD_ORANGE_STOP3, BLANK_CLIP_COLOR_GRAD, BLANK_CLIP_COLOR_GRAD_L
        FRAME_SCALE_COLOR_GRAD = (1, 0.3, 0.3, 0.3, 1)
        FRAME_SCALE_COLOR_GRAD_L = get_multiplied_grad(0, 1, FRAME_SCALE_COLOR_GRAD, GRAD_MULTIPLIER)
        BG_COLOR = (0.44, 0.44, 0.46)

        FRAME_SCALE_LINES = (0.8, 0.8, 0.8)
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME:
            TRACK_GRAD_STOP1 = (1,  0.12, 0.14, 0.2, 1)
            TRACK_GRAD_STOP3 = (1,  0.12, 0.14, 0.2, 1)
            TRACK_GRAD_ORANGE_STOP1 = (1,  0.20, 0.22, 0.28, 1) # V1
            TRACK_GRAD_ORANGE_STOP3 = (1,  0.20, 0.22, 0.28, 1) # V1
            TRACK_NAME_COLOR = (0.68, 0.68, 0.68)
            TRACK_ALL_ON_V_ICON = _load_pixbuf("track_all_on_V_fb.png")
            TRACK_ALL_ON_A_ICON = _load_pixbuf("track_all_on_A_fb.png")
            MUTE_AUDIO_ICON = _load_pixbuf("track_audio_mute_fb.png")
            MUTE_VIDEO_ICON = _load_pixbuf("track_video_mute_fb.png")
            MUTE_ALL_ICON = _load_pixbuf("track_all_mute_fb.png")
            MUTE_AUDIO_A_ICON = _load_pixbuf("track_audio_mute_A_fb.png")
            INSERT_ARROW_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "insert_arrow_fb.png")
            BLANK_CLIP_COLOR_GRAD = (1, 0.12, 0.14, 0.2, 1)
            BLANK_CLIP_COLOR_GRAD_L = (0, 0.12, 0.14, 0.2, 1)
    else:
        global TRACK_GRAD_ORANGE_STOP1,TRACK_GRAD_ORANGE_STOP3,TRACK_GRAD_STOP1,TRACK_GRAD_STOP3
        TRACK_GRAD_ORANGE_STOP1 = (1,  0.4, 0.4, 0.4, 1) # V1
        TRACK_GRAD_ORANGE_STOP3 = (0,  0.68, 0.68, 0.68, 1) # V1

        TRACK_GRAD_STOP1 = (1, 0.68, 0.68, 0.68, 1) #0.93, 0.93, 0.93, 1)
        TRACK_GRAD_STOP3 = (0, 0.93, 0.93, 0.93, 1) #0.58, 0.58, 0.58, 1) 

def set_tracks_double_height_consts():
    global ID_PAD_Y, ID_PAD_Y_SMALL, VIDEO_TRACK_V_ICON_POS, VIDEO_TRACK_A_ICON_POS, VIDEO_TRACK_V_ICON_POS_SMALL, VIDEO_TRACK_A_ICON_POS_SMALL, \
    AUDIO_TRACK_ICON_POS, AUDIO_TRACK_ICON_POS_SMALL, MUTE_ICON_POS, MUTE_ICON_POS_NORMAL, LOCK_POS, INSRT_ICON_POS, INSRT_ICON_POS_SMALL, \
    WAVEFORM_PAD_LARGE, WAVEFORM_PAD_SMALL, HEIGHT
    
    HEIGHT = appconsts.TLINE_HEIGHT
    ID_PAD_Y = 41
    ID_PAD_Y_SMALL = 16
    VIDEO_TRACK_V_ICON_POS = (5, 41)
    VIDEO_TRACK_A_ICON_POS = (5, 50)
    VIDEO_TRACK_V_ICON_POS_SMALL = (5, 16)
    VIDEO_TRACK_A_ICON_POS_SMALL = (5, 25) 
    AUDIO_TRACK_ICON_POS = (5, 43)
    AUDIO_TRACK_ICON_POS_SMALL = (5, 18)
    MUTE_ICON_POS = (5, 14)
    MUTE_ICON_POS_NORMAL = (5, 39)
    LOCK_POS = (67, 2)
    INSRT_ICON_POS = (81, 43)
    INSRT_ICON_POS_SMALL =  (81, 18)
    WAVEFORM_PAD_LARGE = 77
    WAVEFORM_PAD_SMALL = 33

def set_dark_bg_color():
    if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
        return

    r, g, b, a = gui.unpack_gdk_color(gui.get_bg_color())

    global BG_COLOR
    BG_COLOR = get_multiplied_color((r, g, b), 1.25)

def set_match_frame(tline_match_frame, track_index, display_on_right):
    global match_frame, match_frame_track_index, image_on_right, match_frame_image
    match_frame = tline_match_frame
    match_frame_track_index = track_index
    image_on_right = display_on_right
    match_frame_image = None

def match_frame_close_hit(x, y):
    if match_frame == -1:
        return False
    
    if image_on_right == True:
        frame_adj = 0
        img_pos_adj = 0
    else:
        frame_adj = 1
        img_pos_adj = int(match_frame_width)
    
    scale_in = (match_frame + frame_adj - pos) * pix_per_frame

    test_x = scale_in - img_pos_adj + 4
    test_y = 24
    if (x >= test_x and  x <= test_x + 12) and (y >= test_y and  y <= test_y + 12):
        return True
    
    return False

def _load_pixbuf(icon_file):
    return cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + icon_file)

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

    x, y, w, panel_height = allocation.x, allocation.y, allocation.width, allocation.height
    centerered_tracks_bottom_y = (panel_height / 2.0) + (total_h / 2.0)
    global REF_LINE_Y
    REF_LINE_Y = centerered_tracks_bottom_y - below_ref_h

def get_pos_for_tline_centered_to_current_frame():
    current_frame = PLAYER().current_frame()
    allocation = canvas_widget.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height
    frames_in_panel = w / pix_per_frame

    # current in first half on first screen width of tline display
    if current_frame < (frames_in_panel / 2.0):
        return 0
    else:
        return current_frame - (frames_in_panel / 2)

def get_last_tline_view_frame():
    allocation = canvas_widget.widget.get_allocation()
    x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height
    frames_in_panel = w / pix_per_frame
    return int(pos + frames_in_panel)

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
    
    _draw_snap(cr, y)

def draw_overwrite_box_overlay(cr, data):
    # Only draw if were moving
    if data == None:
        return
    if data["action_on"] == False:
        return

    if data["box_selection_data"] == None: # mouse action selection
        x1, y1 = data["press_point"]
        x2, y2 = data["mouse_point"]

        cr.set_line_width(2.0)
        cr.set_source_rgb(*OVERLAY_COLOR)
        cr.move_to(x1, y1)
        cr.line_to(x1, y2)
        cr.line_to(x2, y2)
        cr.line_to(x2, y1)
        cr.close_path()
        cr.stroke()
    else: # mouse action move
        # Draw clips in draw range
        cr.set_line_width(MOVE_CLIPS_LINE_WIDTH)
        cr.set_source_rgb(*OVERLAY_COLOR)
        
        s_data = data["box_selection_data"]

        # Draw moved clips
        for i in range(0, len(s_data.track_selections)):
            track_selection = s_data.track_selections[i]
            y = _get_track_y(track_selection.track_id)
            clip_start_frame = track_selection.range_frame_in - pos + data["delta"]
            track_height = current_sequence().tracks[track_selection.track_id].height
            
            for i in range(0, len(track_selection.clip_lengths)):
                clip_length = track_selection.clip_lengths[i]
                if track_selection.clip_is_media[i] == True:
                    scale_length = clip_length * pix_per_frame
                    scale_in = clip_start_frame * pix_per_frame
                    cr.rectangle(scale_in, y + 1.5, scale_length, track_height - 2.0)
                    cr.stroke()
                clip_start_frame += clip_length
        
        # Draw moved compositors
        for comp in s_data.selected_compositors:
            comp_in = comp.clip_in - pos + data["delta"]
            comp_out = comp.clip_out - pos + data["delta"]
            track = current_sequence().tracks[comp.transition.b_track]
            y = _get_track_y(comp.transition.b_track) + track.height - COMPOSITOR_HEIGHT_OFF
            track_height = current_sequence().tracks[comp.transition.b_track].height
            scale_length = (comp_out - comp_in) * pix_per_frame
            scale_in = comp_in * pix_per_frame
            target_track = current_sequence().tracks[comp.transition.a_track]
            target_y = _get_track_y(target_track.id) + target_track.height - COMPOSITOR_HEIGHT_OFF
                
            _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y)
    
            cr.set_source_rgb(*BOX_BOUND_COLOR)
            cr.stroke()
                    
        # Draw bounding box
        cr.set_line_width(6.0)
        cr.set_source_rgb(*BOX_BOUND_COLOR)
        x = (s_data.topleft_frame  - pos + data["delta"]) * pix_per_frame
        w = s_data.width_frames * pix_per_frame
        y = _get_track_y(s_data.topleft_track)
        bottom_track = s_data.topleft_track - s_data.height_tracks + 1
        y2 = _get_track_y(bottom_track) + current_sequence().tracks[bottom_track].height
        cr.move_to(x, y)
        cr.line_to(x + w, y)
        cr.line_to(x + w, y2)
        cr.line_to(x, y2)
        cr.close_path()
        cr.set_dash(BOX_DASHES, 0) 
        cr.stroke()

        # Draw move arrows
        draw_x = x - 6
        draw_y = y + (y2 - y) / 2.0
        size = 9
        cr.set_source_rgb(*OVERLAY_COLOR)
        cr.move_to(draw_x, draw_y)
        cr.line_to(draw_x, draw_y - size)
        cr.line_to(draw_x - size, draw_y)
        cr.line_to(draw_x, draw_y + size)
        cr.close_path()
        cr.fill()

        draw_x = x + w + 6
        cr.move_to(draw_x, draw_y)
        cr.line_to(draw_x, draw_y - size)
        cr.line_to(draw_x + size, draw_y)
        cr.line_to(draw_x, draw_y + size)
        cr.close_path()
        cr.fill()

        if editorpersistance.prefs.delta_overlay == True:
            delta = data["delta"]       
            tc_str = utils.get_tc_string_short(abs(delta))
            tc_str = _get_signed_tc_str(tc_str, delta)
                
            _draw_text_info_box(cr, x, y - 12, tc_str)
        
def _draw_move_overlay(cr, data, y):
    # Get data
    press_frame = data["press_frame"]
    current_frame = data["current_frame"]
    first_clip_start = data["first_clip_start"]
    clip_lengths = data["clip_lengths"]
    track_height = data["to_track_object"].height

    # Get first frame for drawing shadow clips
    delta = current_frame - press_frame
    draw_start = first_clip_start + delta
    clip_start_frame = draw_start - pos
        
    # Draw clips in draw range
    cr.set_line_width(MOVE_CLIPS_LINE_WIDTH)
    cr.set_source_rgb(*OVERLAY_COLOR)
    for i in range(0, len(clip_lengths)):
        clip_length = clip_lengths[i]
        
        scale_length = clip_length * pix_per_frame
        scale_in = clip_start_frame * pix_per_frame
        cr.rectangle(scale_in, y + 1.5, scale_length, track_height - 2.0)
        cr.stroke()
        
        # Start frame for next clip
        clip_start_frame += clip_length

    if editorpersistance.prefs.delta_overlay == True:
        x = (draw_start - pos) * pix_per_frame
        
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, x, y - 12, tc_str)

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

    y = _get_track_y(current_sequence().first_video_index)

    if editorpersistance.prefs.delta_overlay == True:        
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, draw_x, y - 12, tc_str)
    
    _draw_snap(cr, y)
    
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

    if editorpersistance.prefs.delta_overlay == True:
        delta = data["selected_frame"] - data["edit_frame"]        
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, selection_frame_x + 3, track_y - 12, tc_str)

    _draw_kb_trim_indicator(cr, selection_frame_x, track_y)
    _draw_snap(cr, track_y)
    
def draw_one_roll_overlay(cr, data):
    track_height = current_sequence().tracks[data["track"]].height
    track_y = _get_track_y(data["track"])
    
    selection_frame_x = _get_frame_x(data["selected_frame"])

    trim_limits = data["trim_limits"]
    if data["to_side_being_edited"]:
        # Case: editing to-clip
        first = data["selected_frame"]
        last = trim_limits["both_end"] + 1
        if trim_limits["ripple_display_end"] != -1:
            last = trim_limits["ripple_display_end"]
        x = _get_frame_x(last)

    else:
        # Case: editing from-clip
        first = trim_limits["both_start"] - 1
        if trim_limits["ripple_display_start"] != -1:
            first = trim_limits["ripple_display_start"]
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

    if editorpersistance.prefs.delta_overlay == True:
        delta = data["selected_frame"] - data["edit_frame"]        
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, selection_frame_x + 3, track_y - 12, tc_str)

    _draw_kb_trim_indicator(cr, selection_frame_x, track_y)
    _draw_snap(cr, track_y)
    
def draw_one_roll_overlay_ripple(cr, data):
    # Trim overlay
    draw_one_roll_overlay(cr, data)
    
    # Blanks indicators
    ripple_data = data["ripple_data"]
    
    cr.set_line_width(2.0)
    cr.set_source_rgb(*OVERLAY_COLOR)
    
    for i in range(1, len(current_sequence().tracks) - 1):
        offset = ripple_data.track_blank_end_offset[i-1]
        if offset == None:
            continue
        
        delta = data["selected_frame"] - data["edit_frame"]
        if data["to_side_being_edited"]:
            indicator_frame = data["edit_frame"] - delta + offset
        else:
            indicator_frame = data["selected_frame"] + offset
        
        # Trimmed track needs different position
        if i == data["track"]:
            indicator_frame = data["edit_frame"] + delta + offset
            
        indicator_x = _get_frame_x(indicator_frame)
        
        track_height = current_sequence().tracks[i].height
        track_y = _get_track_y(i)

        # Max edit hint len on edit track
        if i == data["track"]:
            
            if data["to_side_being_edited"] == False:
                max_edit_frame = data["trim_limits"]["both_start"] 
            else:
                max_edit_frame = data["trim_limits"]["both_end"] 
        
            max_x = _get_frame_x(max_edit_frame)
        
            cr.save()
            cr.move_to(max_x, track_y)
            cr.line_to(max_x, track_y + track_height)
            cr.set_dash(BOX_DASHES, 0) 
            cr.stroke()
            cr.restore() # to get rid of dashes
            continue
            
        # Red indicators
        max_trim = False
        if delta == ripple_data.max_backwards:# and ripple_data.track_edit_ops[i-1] == appconsts.MULTI_TRIM_REMOVE:
            max_trim = True
        elif data["to_side_being_edited"] == False and delta == -ripple_data.max_backwards:
            max_trim = True
            
        if max_trim and i != data["track"]:
            cr.set_source_rgb(*TRIM_MAX_RED)

            cr.move_to(indicator_x, track_y)
            cr.line_to(indicator_x, track_y + track_height)
            cr.stroke()
     
            draw_y = track_y + track_height / 2

            cr.move_to(indicator_x + 2, draw_y)
            cr.line_to(indicator_x + 2, draw_y - 5)
            cr.line_to(indicator_x + 7, draw_y)
            cr.line_to(indicator_x + 2, draw_y + 5)
            cr.close_path()
            cr.fill()
            
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

    cr.set_source_surface(VIEW_SIDE_ICON, x, track_y + 4)
    cr.paint()

    _draw_kb_trim_indicator(cr, x, track_y)

    if editorpersistance.prefs.delta_overlay == True:
        delta = data["mouse_delta"]  
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, clip_start_frame_x + 3, track_y - 12, tc_str)
        
def draw_clip_end_drag_overlay(cr, data):
    if data["editing_clip_end"] == True:
        end = data["frame"]  - pos
        start = data["bound_start"]  - pos
    else:
        start = data["frame"]  - pos
        end = data["bound_end"]  - pos

    y = _get_track_y(data["track"].id)
    
    # Draw clips in draw range
    cr.set_line_width(MOVE_CLIPS_LINE_WIDTH)


    clip_length = end - start
    scale_length = clip_length * pix_per_frame
    scale_in = int(start * pix_per_frame) + 0.5
    track_height = data["track_height"]

    cr.rectangle(scale_in, int(y) + 1.5, int(scale_length), track_height - 2.0)
    cr.set_source_rgba(*CLIP_END_DRAG_OVERLAY_COLOR)
    cr.fill_preserve()
    cr.set_source_rgb(*OVERLAY_TRIM_COLOR)
    cr.stroke()

    if editorpersistance.prefs.delta_overlay == True:
        if data["editing_clip_end"] == True:
            x = scale_in + scale_length
            delta = data["frame"] - data["orig_out"]
        else:
            x = scale_in
            delta = data["frame"] - data["orig_in"]  - 1
            
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)

        _draw_text_info_box(cr, x - 3, y - 12, tc_str)
    
    _draw_snap(cr, y)
            
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

    if editorpersistance.prefs.delta_overlay == True:
        delta = current_frame - press_frame
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, scale_in, y - 12, tc_str)
    
    _draw_snap(cr, y)

def draw_cut_overlay(cr, data):
    pass

def draw_kftool_overlay(cr, data):
    draw_function = data["draw_function"]
    draw_function(cr, pos)
    
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
    cr.set_source_rgb(*OVERLAY_TRIM_COLOR)
    cr.stroke()
    
    if data["trim_is_clip_in"] == True:
        x = scale_in + 2
        delta = data["clip_in"] - data["orig_clip_in"]
        info_x = scale_in - 3
    else:
        x = scale_in + scale_length - 26
        delta = data["clip_out"] - data["orig_clip_out"]
        info_x = scale_in + + scale_length - 3

    _draw_two_arrows(cr, x, y + 4, 4)

    if editorpersistance.prefs.delta_overlay == True:
        tc_str = utils.get_tc_string_short(abs(delta))
        tc_str = _get_signed_tc_str(tc_str, delta)
            
        _draw_text_info_box(cr, info_x, y - 12, tc_str)

    _draw_snap(cr, y)
    
def _create_compositor_cairo_path(cr, scale_in, scale_length, y, target_y):
    scale_in = int(scale_in) + 0.5
    scale_length = int(scale_length)
    y = int(y) + 0.5
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
    cr.set_source_surface(VIEW_SIDE_ICON, x, y)
    cr.paint()

def _draw_snap(cr, y):
    if snapping.snap_active() == True:
        cr.set_source_surface(SNAP_ICON, int(snapping.get_snap_x()) - 6, int(y) - 14)
        cr.paint()

def _draw_kb_trim_indicator(cr, x, y):
    if trimmodes.submode == trimmodes.KEYB_EDIT_ON:
        cr.set_source_surface(KEYBOARD_ICON, int(x) - 9, int(y) - 16)
        cr.paint()

def _draw_text_info_box(cr, x, y, text):
    x = int(x)
    y = int(y)
    cr.set_source_rgb(1, 1, 1)
    cr.select_font_face ("sans-serif",
                     cairo.FONT_SLANT_NORMAL,
                     cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(13)

    x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(text)
    
    x1 = x - 3.5
    y1 = y + 4.5
    x2 = x + width + 5.5
    y2 = y - height - 4.5
    
    cr.move_to(x1, y1)
    cr.line_to(x1, y2)
    cr.line_to(x2, y2)
    cr.line_to(x2, y1)
    cr.close_path()
    cr.set_source_rgb(0.1, 0.1, 0.1)
    cr.fill_preserve()
    
    cr.set_line_width(1.0)
    cr.set_source_rgb(0.7, 0.7, 0.7)
    cr.stroke()
    
    cr.move_to(x, y)
    cr.set_source_rgb(0.8, 0.8, 0.8)
    cr.show_text(text) 

def _get_signed_tc_str(tc_str, delta):
    if delta < 0:
        tc_str = "-" + tc_str
    elif  delta > 0:
        tc_str = "+" + tc_str
    return tc_str

# ------------------------------- WIDGETS
class TimeLineCanvas:
    """
    GUI component for editing clips.
    """

    def __init__(self, press_listener, move_listener, release_listener, double_click_listener,
                    mouse_scroll_listener, leave_notify_listener, enter_notify_listener):
        # Create widget and connect listeners
        self.widget = cairoarea.CairoDrawableArea2( WIDTH, 
                                                    HEIGHT, 
                                                    self._draw)
        self.widget.add_pointer_motion_mask()
        
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = mouse_scroll_listener

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
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.double_click_listener(get_frame(event.x), event.x, event.y)
            return
         
        self.drag_on = True
        self.press_listener(event, get_frame(event.x))

    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        #if EDIT_MODE() == editorstate.CUT:
        #    cutmode.
        
        if (not self.drag_on) and editorstate.cursor_is_tline_sensitive == True:
            self.set_pointer_context(x, y)
            return

        button = -1 
        if (state & Gdk.ModifierType.BUTTON1_MASK):
            button = 1
        elif (state & Gdk.ModifierType.BUTTON3_MASK):
            button = 3
        
        track = get_track(y)
        x = snapping.get_snapped_x(x, track, self.edit_mode_data)
            
        self.move_listener(x, y, get_frame(x), button, state) # -> editevent.tline_canvas_mouse_pressed(...)
        
    def _release_event(self, event):
        """
        Mouse release callback.
        """
        self.drag_on = False
        
        track = get_track(event.y)
        x = snapping.get_snapped_x(event.x, track, self.edit_mode_data)
        snapping.mouse_edit_ended()
        
        self.release_listener(x, event.y, get_frame(x), \
                              event.button, event.get_state())

    def set_pointer_context(self, x, y):
        current_pointer_context = self.get_pointer_context(x, y)

        # If pointer_context changed then save it and change cursor.
        global pointer_context
        if pointer_context != current_pointer_context:
            pointer_context = current_pointer_context
            if pointer_context == appconsts.POINTER_CONTEXT_NONE:
                gui.editor_window.set_tline_cursor(EDIT_MODE())
            else:
                gui.editor_window.set_tline_cursor_to_context(pointer_context)
        
    def get_pointer_context(self, x, y):
        frame = get_frame(x)
        hit_compositor = compositor_hit(frame, y, current_sequence().compositors)
        if hit_compositor != None:
            if editorstate.auto_follow == False or (editorstate.auto_follow == True and hit_compositor.obey_autofollow == False):
                return compositormodes.get_pointer_context(hit_compositor, x)
            else:
                return appconsts.POINTER_CONTEXT_NONE

        track = get_track(y)
        if track == None:
            return appconsts.POINTER_CONTEXT_NONE

        clip_index = current_sequence().get_clip_index(track, frame)
        if clip_index == -1:
            # This gets none always afetr rack, which may not be what we want
            return appconsts.POINTER_CONTEXT_NONE

        clip_start_frame = track.clip_start(clip_index)
        clip_end_frame = track.clip_start(clip_index + 1)
        
        # INSERT, OVEWRITE
        if (EDIT_MODE() == editorstate.INSERT_MOVE or EDIT_MODE() == editorstate.OVERWRITE_MOVE) and editorstate.overwrite_mode_box == False:
            if abs(x - _get_frame_x(clip_start_frame)) < DRAG_SENSITIVITY_AREA_WIDTH_PIX:
                return appconsts.POINTER_CONTEXT_END_DRAG_LEFT
            if abs(x - _get_frame_x(clip_end_frame)) < DRAG_SENSITIVITY_AREA_WIDTH_PIX:
                return appconsts.POINTER_CONTEXT_END_DRAG_RIGHT
            
            return appconsts.POINTER_CONTEXT_NONE
        # TRIM
        elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM or EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if abs(frame - clip_start_frame) < abs(frame - clip_end_frame):
                return appconsts.POINTER_CONTEXT_TRIM_LEFT
            else:
                return appconsts.POINTER_CONTEXT_TRIM_RIGHT
        # BOX
        elif (EDIT_MODE() == editorstate.OVERWRITE_MOVE and editorstate.overwrite_mode_box == True and 
            boxmove.box_selection_data != None):
            if boxmove.box_selection_data.is_hit(x, y):
                return appconsts.POINTER_CONTEXT_BOX_SIDEWAYS
                
        return appconsts.POINTER_CONTEXT_NONE
            
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
        
        # Draw match frame
        self.draw_match_frame(cr)
            
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
        
        audiowaveformrenderer.launch_queued_renders()

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
        #print start, end
        width_frames = float(width) / pix_per_frame

        # Add 1 to end because range() last index exclusive 
        # MLT returns clips structure size + 1 if frame after last clip,
        # so in that case don't add anything.
        if len(track.clips) != end:
            end = end + 1
            
        # Get frame of clip.clip_in on timeline.
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

        global clip_thumbnails
                
        # Draw clips in draw range
        for i in range(start, end):
            #print "track :", track.id, "index:", i
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
                else:# Audio clip
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
                #cr.rectangle(scale_in, y, scale_length, track_height)
                self.create_round_rect_path(cr, scale_in, y, scale_length, track_height)
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

            # Draw video clip icon
            text_x_add = 0
            if scale_length > TEXT_MIN and editorstate.display_clip_media_thumbnails:
                if clip.is_blanck_clip == False and track.type == sequence.VIDEO and \
                    (clip.media_type == sequence.VIDEO or clip.media_type == sequence.IMAGE 
                        or clip.media_type == sequence.IMAGE_SEQUENCE):
                        
                    text_x_add = 115
                    cr.save()
                    try: # paint thumbnail
                        thumb_img = clip_thumbnails[clip.path]
                        cr.rectangle(scale_in + 4, y + 3.5, scale_length - 8, track_height - 6)
                        cr.clip()
                        cr.set_source_surface(thumb_img,scale_in, y - 20)
                        cr.paint()
                    except: # thumbnail not found  in dict, get it pait it
                        try:
                            media_file = PROJECT().get_media_file_for_path(clip.path)
                            thumb_img = media_file.icon
                            cr.rectangle(scale_in + 4, y + 3.5, scale_length - 8, track_height - 6)
                            cr.clip()
                            cr.set_source_surface(thumb_img, scale_in, y - 20)
                            cr.paint()
                            clip_thumbnails[clip.path] = thumb_img
                        except:
                            pass # This fails for rendered fades and transitions
                    
                    if clip.selected:
                        if scale_length - 8 < appconsts.THUMB_WIDTH:
                            ow = scale_length - 8 
                        else:
                            ow = appconsts.THUMB_WIDTH
                        cr.rectangle(scale_in + 4, y + 3.5, ow, track_height - 6)
                        cr.set_source_rgba(*ICON_SELECTED_OVERLAY_COLOR)
                        cr.fill()
                                                    
                    cr.restore()
                
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
                    if clip.selected:
                        cr.set_source_rgb(*PROXY_STRIP_COLOR_SELECTED)
                    else:
                        cr.set_source_rgb(*PROXY_STRIP_COLOR)

                    cr.rectangle(scale_in, y, scale_length, 8)
                    cr.fill()

            # Draw clip frame 
            cr.set_line_width(1.0)
            if scale_length > FILL_MIN:
                cr.set_source_rgb(0, 0, 0)
            else:    
                cr.set_source_rgb(0.3, 0.3, 0.3)
                
            self.create_round_rect_path(cr, scale_in,
                                         y, scale_length, 
                                         track_height)
            """
            cr.rectangle(scale_in + 0.5,
                         y + 0.5, scale_length, 
                         track_height)
            """
            cr.stroke()
        
            # No further drawing for blank clips
            if clip.is_blanck_clip:
                clip_start_frame += clip_length
                continue

            # Save sync children data
            if clip.sync_data != None:
                self.sync_children.append((clip, track, scale_in))

            # Draw audio level data, except for IMAGE_SEQUENCE clips
            # Init data rendering if data needed and not available
            if clip.waveform_data == None and editorstate.display_all_audio_levels == True and clip.media_type != appconsts.IMAGE_SEQUENCE and clip.media_type != appconsts.PATTERN_PRODUCER:
                 clip.waveform_data = audiowaveformrenderer.get_waveform_data(clip)
            # Draw data if available large enough scale
            if clip.waveform_data != None and scale_length > FILL_MIN:
                r, g, b = clip_bg_col
                #r, g, b =  (0.62, 0.38, 0.7)
                #cr.set_source_rgb(r * 0.9, g * 0.9, b * 0.9)
                cr.set_source_rgb(r * 1.9, g * 1.9, b * 1.9)
                
                cr.save()
                self.create_round_rect_path(cr, scale_in,
                                             y, scale_length - 1, 
                                             track_height)
                cr.clip()
                                         
                # Get level bar height and position for track height
                if track.height == sequence.TRACK_HEIGHT_NORMAL:
                    y_pad = WAVEFORM_PAD_LARGE
                    bar_height = WAVEFORM_HEIGHT_LARGE
                else:
                    y_pad = WAVEFORM_PAD_SMALL
                    bar_height = WAVEFORM_HEIGHT_SMALL
                
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
                for f in range(draw_first, draw_last, step):
                    try:
                        x = media_start_pos_pix + f * pix_per_frame
                        h = bar_height * clip.waveform_data[f]
                        if h < 1:
                            h = 1
                        cr.rectangle(x, y + y_pad + (bar_height - h), draw_pix_per_frame, h)
                    except:
                        # This is just dirty fix a when 23.98 fps does not work
                        break

                cr.fill()
                cr.restore()
    
            """
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
            """
            
            # Draw text and filter, sync icons
            if scale_length > TEXT_MIN:
                if not hasattr(clip, "rendered_type"):
                    # Text
                    cr.set_source_rgba(*CLIP_TEXT_COLOR_OVERLAY)
                    #cr.set_source_rgb(0, 0, 0)
                    cr.select_font_face ("sans-serif",
                                         cairo.FONT_SLANT_NORMAL,
                                         cairo.FONT_WEIGHT_BOLD)
                    cr.set_font_size(10)
                    cr.move_to(scale_in + TEXT_X + text_x_add, y + text_y)
                    cr.show_text(clip.name.upper())
                
                icon_slot = 0
                # Filter icon
                if len(clip.filters) > 0:
                    ix, iy = ICON_SLOTS[icon_slot]
                    cr.set_source_surface(FILTER_CLIP_ICON, int(scale_in) + int(scale_length) - ix, y + iy)
                    cr.paint()
                    icon_slot = icon_slot + 1
                # Mute icon
                if clip.mute_filter != None:
                    icon = AUDIO_MUTE_ICON
                    ix, iy = ICON_SLOTS[icon_slot]
                    cr.set_source_surface(icon, int(scale_in) + int(scale_length) - ix, y + iy)
                    cr.paint()
                    icon_slot = icon_slot + 1

                if clip == clipeffectseditor.clip:
                    icon = EDIT_INDICATOR
                    ix =  int(scale_in) + int(scale_length) / 2 - 7
                    iy = y + int(track_height) / 2 - 7
                    cr.set_source_surface(icon, ix, iy)
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

            if clip.waveform_data == None and editorstate.display_all_audio_levels == True and scale_length > FILL_MIN:
                if clip.media_type != appconsts.IMAGE_SEQUENCE and clip.media_type != appconsts.PATTERN_PRODUCER:
                    cr.set_source_surface(LEVELS_RENDER_ICON, int(scale_in) + 4, y + 8)
                    cr.paint()

            # Clip markers
            if len(clip.markers) > 0 and scale_length > TEXT_MIN:
                for marker in clip.markers:
                    name, clip_marker_frame = marker
                    marker_x = (clip_start_frame + clip_marker_frame - clip.clip_in) * pix_per_frame
                    cr.set_source_surface(CLIP_MARKER_ICON, int(marker_x) - 4, y)
                    cr.paint()
                    
                    
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
                if editorstate.auto_follow_active() == True and comp.obey_autofollow == True:
                    color = COMPOSITOR_CLIP_AUTO_FOLLOW
                else:
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

    def draw_match_frame(self, cr):
        if match_frame == -1:
            return
        
        global match_frame_image
        if match_frame_image == None:
            self.create_match_frame_image_surface()

        if image_on_right == True:
            dir_mult = 1
            frame_adj = 0
            img_pos_adj = 0
        else:
            dir_mult = -1
            frame_adj = 1
            img_pos_adj = int(match_frame_width)
        
        scale_in = (match_frame + frame_adj - pos) * pix_per_frame
                
        cr.set_source_surface(match_frame_image, scale_in - img_pos_adj, 20)
        cr.paint_with_alpha(0.7)
    
        cr.set_source_surface(CLOSE_MATCH_ICON, scale_in - img_pos_adj + 4, 24)
        cr.paint()
        
        cr.set_source_rgb(*MATCH_FRAME_LINES_COLOR)
        cr.set_line_width(2.0)
        cr.rectangle(int(scale_in) - img_pos_adj, 20, int(match_frame_width), int(match_frame_height))
        cr.stroke()

        cr.move_to(int(scale_in), 0, )
        cr.line_to(int(scale_in), int(match_frame_height) + 42)
        cr.stroke()

        start_y = _get_track_y(match_frame_track_index)
        end_y = _get_track_y(match_frame_track_index - 1)
        
        cr.move_to (int(scale_in) + 8 * dir_mult, start_y)
        cr.line_to (int(scale_in), start_y)
        cr.line_to (int(scale_in), end_y + 1)
        cr.line_to (int(scale_in) + 8 * dir_mult, end_y + 1)
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.set_line_width(4.0)
        cr.stroke()

    def create_round_rect_path(self, cr, x, y, width, height):
        radius = 4.0
        degrees = M_PI / 180.0

        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()

    def create_match_frame_image_surface(self):
        # Create non-scaled icon
        matchframe_path = utils.get_hidden_user_dir_path() + appconsts.MATCH_FRAME
        icon = cairo.ImageSurface.create_from_png(matchframe_path)

        # Create and return scaled icon
        allocation = canvas_widget.widget.get_allocation()
        x, y, w, h = allocation.x, allocation.y, allocation.width, allocation.height
        profile_screen_ratio = float(PROJECT().profile.width()) / float(PROJECT().profile.height())
        
        global match_frame_width, match_frame_height
        match_frame_height = h - 40
        match_frame_width = match_frame_height * profile_screen_ratio
    
        scaled_icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(match_frame_width), int(match_frame_height))
        cr = cairo.Context(scaled_icon)
        cr.scale(float(match_frame_width) / float(icon.get_width()), float(match_frame_height) / float(icon.get_height()))

        cr.set_source_surface(icon, 0, 0)
        cr.paint()
        
        global match_frame_image
        match_frame_image = scaled_icon



class TimeLineColumn:
    """
    GUI component for displaying and editing track parameters.
    """

    def __init__(self, active_listener, center_listener):
        # Init widget
        self.widget = cairoarea.CairoDrawableArea2( COLUMN_WIDTH, 
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
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME:
            stop, r,g,b, a = TRACK_GRAD_STOP1
            cr.set_source_rgb(r,g,b)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_line_width(1.0)
            cr.set_source_rgb(0, 0, 0)
            cr.rectangle(0.5, 0.5, w, h - 1)
            #cr.stroke()
        else:
            cr.set_source_rgb(*BG_COLOR)
            cr.rectangle(0, 0, w, h)
            cr.fill()

        # This can get called during loads by expose events.
        if editorstate.project_is_loading == True:
            return

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

        # Draw track name
        layout = PangoCairo.create_layout(cr)
        text = utils.get_track_name(track, current_sequence())
        desc = Pango.FontDescription("Sans Bold 10")
        layout.set_text(text, -1)
        layout.set_font_description(desc)

        cr.set_source_rgb(*TRACK_NAME_COLOR)
        if track.height == sequence.TRACK_HEIGHT_NORMAL:
            text_y = ID_PAD_Y
        else:
            text_y = ID_PAD_Y_SMALL
        cr.move_to(COLUMN_LEFT_PAD + ID_PAD_X, y + text_y)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)
        
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
            cr.set_source_surface(mute_icon, int(ix), int(y + iy))
            cr.paint()

        # Draw locked icon
        if track.edit_freedom == sequence.LOCKED:
            ix, iy = LOCK_POS
            if track.height == sequence.TRACK_HEIGHT_NORMAL:
                iy = ID_PAD_Y + 4
            else:
                iy = ID_PAD_Y_SMALL + 4
            cr.set_source_surface(FULL_LOCK_ICON, ix, int(y + iy))
            cr.paint()
        
        # Draw insert arrow
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME:
            stop, r,g,b, a = TRACK_GRAD_STOP1
            cr.set_source_rgb(r,g,b)
        if is_insert_track == True:
            ix, iy = INSRT_ICON_POS
            if track.height == sequence.TRACK_HEIGHT_SMALL:
                ix, iy = INSRT_ICON_POS_SMALL
            cr.set_source_surface(INSERT_ARROW_ICON, ix, y + iy)
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
        self.widget = cairoarea.CairoDrawableArea2( WIDTH, 
                                                    SCALE_HEIGHT, 
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = mouse_scroll_listener
        self.drag_on = False
        self.set_default_callback = set_default_callback

        if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
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
        if((state & Gdk.ModifierType.BUTTON1_MASK)
           or(state & Gdk.ModifierType.BUTTON3_MASK)):
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
        if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
            grad = self._get_dark_theme_grad(h)
        else:
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

        # Draw start indicator triangles
        if pos == 0:
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            start_y = 1
            tri_h = 8
            tri_h_half = tri_h / 2
            tri_w = 8
            for i in range(0, 3):
                cr.move_to (0, start_y + i * tri_h)
                cr.line_to (tri_w, start_y + i * tri_h + tri_h_half)
                cr.line_to (0, start_y + i * tri_h + tri_h)
                cr.close_path();
                cr.fill()

        # Set line attr for frames lines
        cr.set_source_rgb(*FRAME_SCALE_LINES)
        cr.set_line_width(1.0)
        
        big_tick_step = -1 # this isn't rendered most ranges, -1 is flag

        # Get displayed frame range
        view_start_frame = pos
        view_end_frame = int(pos + w / pix_per_frame)

        # Get draw steps for marks and tc texts
        if fps < 20:
            spacer_mult = 2 # for fps like 15 this looks bad with out some help
        else:
            spacer_mult = 1
            
        if pix_per_frame > DRAW_THRESHOLD_1:
            small_tick_step = 1
            big_tick_step = fps / 2
            tc_draw_step = (fps * spacer_mult)  / 2
        elif pix_per_frame > DRAW_THRESHOLD_2:
            small_tick_step = fps * spacer_mult
            tc_draw_step = fps * spacer_mult
        elif pix_per_frame > DRAW_THRESHOLD_3:
            small_tick_step = fps * 2 * spacer_mult
            tc_draw_step = fps * 2 * spacer_mult
        elif pix_per_frame > DRAW_THRESHOLD_4:
            small_tick_step = fps * 3 * spacer_mult
            tc_draw_step = fps * 3 * 2
        else:
            view_length = view_end_frame - view_start_frame
            small_tick_step = int(view_length / NUMBER_OF_LINES)
            tc_draw_step = int(view_length / NUMBER_OF_LINES)

        # Draw tc
        cr.select_font_face ("sans-serif",
                              cairo.FONT_SLANT_NORMAL,
                              cairo.FONT_WEIGHT_NORMAL)

        cr.set_font_size(11)
        
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
            if tc_draw_step == small_tick_step:
                cr.move_to(x, TC_Y)
                text = utils.get_tc_string(int(round(float(i) * float(tc_draw_step))))
                cr.show_text(text);
        cr.stroke()
        
        # 23.98 and 29.97 need this to get drawn on even seconds with big ticks and tcs
        if round(fps) != fps:
            to_seconds_fix_add = 1.0
        else:
            to_seconds_fix_add = 0.0
        
        # Draw big tick lines, if required
        if big_tick_step != -1:
            count = int(seq.get_length() / big_tick_step)
            for i in range(1, count):
                x = math.floor((math.floor(i * big_tick_step) + to_seconds_fix_add) * pix_per_frame \
                    - pos * pix_per_frame) + 0.5 
                cr.move_to(x, SCALE_HEIGHT)
                cr.line_to(x, BIG_TICK_Y)
                cr.stroke()

        if tc_draw_step != small_tick_step:
            start = int(view_start_frame / tc_draw_step)
            # Get draw range in steps from 0
            if start == pos:
                start += 1 # don't draw line on first pixel of scale display
            # +1 to ensure coverage
            end = int(view_end_frame / tc_draw_step) + 1 
            for i in range(start, end):
                x = math.floor((math.floor(i * tc_draw_step) + to_seconds_fix_add) * pix_per_frame \
                    - pos * pix_per_frame) + 0.5
                cr.move_to(x, TC_Y)
                text = utils.get_tc_string(int(math.floor((float(i) * tc_draw_step) + to_seconds_fix_add)))
                cr.show_text(text)
        
        # Draw marks
        self.draw_mark_in(cr, h)
        self.draw_mark_out(cr, h)
        
        # Draw markers
        for i in range(0, len(seq.markers)):
            marker_name, marker_frame = seq.markers[i]
            x = math.floor(_get_frame_x(marker_frame))
            cr.set_source_surface(MARKER_ICON, x - 4, 15)
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
        cr.set_source_surface(TC_POINTER_HEAD, frame_x - 7.5, 0)
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
        cr.line_to (x - 1 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x - MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x - MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x - 1 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
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
        cr.line_to (x + 1 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x + MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x + MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x + 1 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
        cr.line_to (x + 2 * MARK_LINE_WIDTH, MARK_PAD)
        cr.close_path();

        cr.fill()
   
    def _get_dark_theme_grad(self, h):
        r, g, b, a  = gui.get_bg_color()
           
        grad = cairo.LinearGradient (0, 0, 0, h)
        grad.add_color_stop_rgba(1, r, g, b, 1)
        grad.add_color_stop_rgba(0, r + 0.05, g + 0.05, b + 0.05, 1)
        
        return grad
        
class TimeLineScroller(Gtk.HScrollbar):
    """
    Scrollbar for timeline.
    """
    def __init__(self, scroll_listener):
        GObject.GObject.__init__(self)
        adjustment = Gtk.Adjustment(0.0, 0.0, 100.0, 1.0, 10.0, 30.0)
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
