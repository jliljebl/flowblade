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
from gi.repository import Pango, PangoCairo, Gtk

import cairo
import math

import appconsts
import cairoarea
import clipeffectseditor
import dialogutils
import edit
from editorstate import current_sequence
from editorstate import PLAYER
import gui
import guiutils
import mltfilters
import propertyedit
import propertyparse
import respaths
import tlinewidgets
import updater

# Icons
HAMBURGER_ICON = None
ACTIVE_KF_ICON = None
NON_ACTIVE_KF_ICON = None

# Draw params
EDIT_AREA_HEIGHT = 200
END_PAD = 8
TOP_PAD = 23
HEIGHT_PAD_PIXELS_TOTAL = 44
OUT_OF_RANGE_ICON_PAD = 27
OUT_OF_RANGE_KF_ICON_HALF = 6
OUT_OF_RANGE_NUMBER_X_START = 7
OUT_OF_RANGE_NUMBER_X_END_PAD = 14

KF_ICON_Y_PAD = -6
KF_TEXT_PAD = -6
KF_LOWER_OFF = 11

# Kf edit params
KF_HIT_WIDTH = 8
KF_DRAG_THRESHOLD = 3

# Colors
FRAME_SCALE_LINES = (0.4, 0.4, 0.6) #(0.07, 0.07, 0.32)
FRAME_SCALE_LINES_BRIGHT = (0.2, 0.2, 0.6)
TEXT_COLOR = (0.6, 0.6, 0.6) 
CURVE_COLOR = (0.97, 0.97, 0.30, 1)#(0.71, 0.13, 0.64, 1.0) # (0.19, 0.69, 0.15, 1) #
OVERLAY_BG = (0.0, 0.0, 0.0, 0.8)
VALUE_AREA_COLOR = (0.27, 0.27, 0.62, 0.85)
SOURCE_TRIANGLE_COLOR = (0.19, 0.32, 0.57)
SOURCE_TRIANGLE_OUTLINE_COLOR = (0.9, 0.9, 0.9)
SCALE_LINES_TEXT_COLOR = (0.9, 0.9, 0.9)
CLIP_OUTLINE_COLOR = (0.7, 0.7, 0.5, 0.22)
AUDIO_LEVELS_COLOR = (0.4, 0.4, 0.68, 0.20)

# Edit types
VOLUME_KF_EDIT = 0
BRIGHTNESS_KF_EDIT = 1
PARAM_KF_EDIT = 2

# Editor states
KF_DRAG = 0
POSITION_DRAG = 1
KF_DRAG_DISABLED = 2 # Not used currently
KF_DRAG_FRAME_ZERO_KF = 3

DRAG_MIN_Y = 4 # to make strt value slightly macnetic, makes easier to move position without changing value

hamburger_menu = Gtk.Menu()
oor_before_menu = Gtk.Menu()
oor_after_menu = Gtk.Menu()
value_snapping_menu = Gtk.Menu()
params_menu =  Gtk.Menu()
 
edit_data = None
enter_mode = None
_kf_editor = None

_playhead_follow_kf = True

_snapping = 1

# -------------------------------------------------- init
def load_icons():
    global HAMBURGER_ICON, ACTIVE_KF_ICON, NON_ACTIVE_KF_ICON

    HAMBURGER_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger.png")
    ACTIVE_KF_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kf_active.png")
    NON_ACTIVE_KF_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kf_not_active_tool.png")    

def init_tool_for_clip(clip, track, edit_type=VOLUME_KF_EDIT, param_data=None):
    # These can produce data for same objects we choose not to commit to updating
    # clipeffectseditor/kftool with events from each other.
    clipeffectseditor.clear_clip()
    
    clip_index = track.clips.index(clip)

    # Save data needed to do the keyframe edits.
    global edit_data #, pressed_on_selected, drag_disabled
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":clip_index,
                 "clip_start_in_timeline":track.clip_start(clip_index),
                 "clip":clip,
                 "track":track,
                 "initializing":True}

    if edit_type == PARAM_KF_EDIT:
        pass # We are not trying to decide based on track what to edit
    else:
        # Always brightness keyframes for media types that contain no audio.
        if edit_data["clip"].media_type != appconsts.VIDEO and edit_data["clip"].media_type != appconsts.AUDIO:
            edit_type = BRIGHTNESS_KF_EDIT
        
        # Volume keyframes on audio track for video and audio
        if track.type == appconsts.AUDIO and not(edit_data["clip"].media_type != appconsts.VIDEO and edit_data["clip"].media_type != appconsts.AUDIO):
            edit_type = VOLUME_KF_EDIT

    global _kf_editor
        
    # Init for edit type
    if edit_type == VOLUME_KF_EDIT:
        ep = _get_volume_editable_property(clip, track, clip_index)
        if ep == None:
            filter_info = mltfilters.get_volume_filters_info()
            data = {"clip":clip, 
                    "filter_info":filter_info,
                    "filter_edit_done_func":_filter_create_dummy_func}
            action = edit.add_multipart_filter_action(data)
            action.do_edit()
            ep = _get_volume_editable_property(clip, track, clip_index)

        edit_data["editable_property"] = ep

        _kf_editor = TLineKeyFrameEditor(ep, True, VOLUME_KF_EDIT)
        
    elif edit_type == BRIGHTNESS_KF_EDIT:
        ep = _get_brightness_editable_property(clip, track, clip_index)
        if ep == None:

            filter_info = mltfilters.get_brightness_filter_info()
            data = {"clip":clip, 
                    "filter_info":filter_info,
                    "filter_edit_done_func":_filter_create_dummy_func}
            action = edit.add_filter_action(data)
            action.do_edit()
            ep = _get_brightness_editable_property(clip, track, clip_index)
            
        edit_data["editable_property"] = ep

        _kf_editor = TLineKeyFrameEditor(ep, True, BRIGHTNESS_KF_EDIT)
        
    else: #  edit_type == PARAM_KF_EDIT 
        property_name, filter_object, filter_index, disp_name = param_data
        ep = _get_param_editable_property(property_name, clip, track, clip_index, filter_object, filter_index)

        # create kf in frame 0 if value PROP_INT or PROP_FLOAT and kf expression
        eq_index = ep.value.find("=")
        if eq_index == -1:
            new_value = "0=" + ep.value
            ep.value = new_value
            ep.write_filter_object_property(new_value)

        # Turn into keyframe property
        ep = ep.get_as_KeyFrameHCSFilterProperty()
        
        edit_data["editable_property"] = ep

        filter_param_name = filter_object.info.name + ":" + disp_name

        _kf_editor = TLineKeyFrameEditor(ep, True, PARAM_KF_EDIT, filter_param_name)

    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()

def update_clip_frame(tline_frame):
    if _kf_editor != None and edit_data != None and edit_data["initializing"] != True:
        clip_frame = tline_frame - edit_data["clip_start_in_timeline"] + edit_data["clip"].clip_in
        _kf_editor.set_and_display_clip_frame(clip_frame)

def _get_volume_editable_property(clip, track, clip_index):
    return _get_multipart_keyframe_ep_from_service(clip, track, clip_index, "volume")

def _get_brightness_editable_property(clip, track, clip_index):
    for i in range(0, len(clip.filters)):
        filter_object = clip.filters[i]
        if filter_object.info.mlt_service_id == "brightness":
            editable_properties = propertyedit.get_filter_editable_properties(
                                                           clip, 
                                                           filter_object,
                                                           i,
                                                           track,
                                                           clip_index)
            for ep in editable_properties:          
                try:
                    if ep.name == "level":
                        return ep
                except:
                    pass
                    
    return None

def _get_param_editable_property(property_name, clip, track, clip_index, filter_object, filter_index):
    editable_properties = propertyedit.get_filter_editable_properties(
                                                   clip, 
                                                   filter_object,
                                                   filter_index,
                                                   track,
                                                   clip_index)
    for ep in editable_properties:          
        try:
            if ep.name == property_name:
                return ep
        except:
            pass
                    
    return None
    
def _get_multipart_keyframe_ep_from_service(clip, track, clip_index, mlt_service_id):
    for i in range(0, len(clip.filters)):
        filter_object = clip.filters[i]
        if filter_object.info.mlt_service_id == mlt_service_id:
            editable_properties = propertyedit.get_filter_editable_properties(
                                                           clip, 
                                                           filter_object,
                                                           i,
                                                           track,
                                                           clip_index)
            for ep in editable_properties:
                try:
                    if ep.args["exptype"] == "multipart_keyframe":
                        return ep
                except:
                    pass
                    
    return None


def exit_tool():
    set_no_clip_edit_data()
    global enter_mode
    if enter_mode != None:
        gui.editor_window.kf_tool_exit_to_mode(enter_mode)
        enter_mode = None
    updater.repaint_tline()
        
def _filter_create_dummy_func(obj1, obj2):
    pass

# ---------------------------------------------- mouse events
def mouse_press(event, frame):

    x = event.x
    y = event.y

    # If we have clip being edited and its edit area is hit, we do not need to init data.
    # If editor open we disregard track locking until it is closed.
    if _kf_editor != None and _kf_editor.overlay_area_hit(x, y):
        _handle_edit_mouse_press(event)
        return

    # Get pressed track
    track = tlinewidgets.get_track(y)  

    # Selecting empty clears selection
    if track == None or track.id == 0 or track.id == len(current_sequence().tracks) - 1:
        exit_tool()
        return    

    # No edits for locked tracks
    if dialogutils.track_lock_check_and_user_info(track):
        set_no_clip_edit_data()
        return
        
    # Attempt to init kf tool editing on some clip
    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty clears selection
    if clip_index == -1:
        exit_tool()
        return

    clip = track.clips[clip_index]

    init_tool_for_clip(clip, track)

def _handle_edit_mouse_press(event):
    _kf_editor.press_event(event)
        
def mouse_move(x, y, frame, state):
    if _kf_editor != None and edit_data != None and edit_data["initializing"] != True:
        _kf_editor.motion_notify_event(x, y, state)

def mouse_release(x, y, frame, state):
    if _kf_editor != None and edit_data != None and edit_data["initializing"] != True:
        _kf_editor.release_event(x, y)
        
    if edit_data != None: 
        edit_data["initializing"] = False

# -------------------------------------------- edit 
def delete_active_keyframe():
    if _kf_editor != None and edit_data != None and edit_data["initializing"] != True:
        _kf_editor.delete_active_keyframe()

def _clip_is_being_edited():
    if edit_data == None:
        return False
    if edit_data["clip_index"] == -1:
        return False
    
    return True

def set_no_clip_edit_data():
    # set edit data to reflect that no clip is being edited currently.
    global edit_data, _kf_editor
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":-1,
                 "track":None,
                 "mouse_start_x":-1,
                 "mouse_start_y":-1}
    _kf_editor = None

    tlinewidgets.set_edit_mode_data(edit_data)

# ----------------------------------------------------------------------- draw callback from tlinewidgets.py
def _tline_overlay(cr):
    if _clip_is_being_edited() == False:
        return
        
    track = edit_data["track"]
    cx_start = tlinewidgets._get_frame_x(edit_data["clip_start_in_timeline"])
    clip = track.clips[edit_data["clip_index"]]
    cx_end = tlinewidgets._get_frame_x(track.clip_start(edit_data["clip_index"]) + clip.clip_out - clip.clip_in + 1)  # +1 because out inclusive
    
    # Get y position for clip's track
    ty_bottom = tlinewidgets._get_track_y(1) + current_sequence().tracks[1].height
    ty_top = tlinewidgets._get_track_y(len(current_sequence().tracks) - 2) - 6 # -6 is hand correction, no idea why the math isn't getting correct pos top most track
    ty_top_bottom_edge = ty_top + EDIT_AREA_HEIGHT
    off_step = float(ty_bottom - ty_top_bottom_edge) / float(len(current_sequence().tracks) - 2)
    ty_off = off_step * float(track.id - 1)
    ty = ty_bottom - ty_off
    cy_start = ty - EDIT_AREA_HEIGHT

    # Set draw params and draw
    _kf_editor.set_allocation(cx_start, cy_start, cx_end - cx_start, EDIT_AREA_HEIGHT)
    _kf_editor.source_track_center = tlinewidgets._get_track_y(track.id) + current_sequence().tracks[track.id].height / 2.0
    _kf_editor.draw(cr)


# ----------------------------------------------------- editor object
class TLineKeyFrameEditor:

    def __init__(self, editable_property, use_clip_in, edit_type, filter_param_name=None):
        
        self.clip_length = editable_property.get_clip_length() - 1
        self.edit_type = edit_type
        # Some filters start keyframes from *MEDIA* frame 0
        # Some filters or compositors start keyframes from *CLIP* frame 0
        # Filters starting from *MEDIA* 0 need offset 
        # to clip start added to all values.
        self.use_clip_in = use_clip_in
        if self.use_clip_in == True:
            self.clip_in = editable_property.clip.clip_in
        else:
            self.clip_in = 0
        self.current_clip_frame = self.clip_in

        self.clip_tline_pos = editable_property.get_clip_tline_pos()
        
        self.keyframes = [(0, 0.0)]
        self.active_kf_index = 0

        self.frame_scale = tlinewidgets.KFToolFrameScale(FRAME_SCALE_LINES)
        
        self.source_track_center = 0 # set externally

        self.edit_value = None
        self.mouse_x = -1
        self.mouse_y = -1
        
        self.media_frame_txt = _("Media Frame: ")
        self.volume_kfs_text = _("Volume Keyframes")
        self.brightness_kfs_text = _("Brightness Keyframes")
        self.filter_param_name_txt = filter_param_name
        
        self.current_mouse_action = None
        self.drag_min = -1
        self.drag_max = -1

        # Init keyframes
        self.keyframe_parser = propertyparse.single_value_keyframes_string_to_kf_array
        editable_property.value.strip('"')
        self.set_keyframes(editable_property.value, editable_property.get_in_value)     

        self._set_pos_to_active_kf()

    # ---------------------------------------------------- data in
    def set_keyframes(self, keyframes_str, out_to_in_func):
        self.keyframes = self.keyframe_parser(keyframes_str, out_to_in_func)

    def set_allocation(self, x, y, w, h):
        self.allocation = (x, y, w, h)

    # ------------------------------------------------------ tline seek
    def clip_editor_frame_changed(self, clip_frame):
        self.seek_tline_frame(clip_frame)

    def seek_tline_frame(self, clip_frame):
        PLAYER().seek_frame(self.clip_tline_pos + clip_frame - self.clip_in)
    
    # ------------------------------------------------------ value write out
    def update_property_value(self):
        edit_data["editable_property"].write_out_keyframes(self.keyframes)

    # ------------------------------------------------------- debug
    def print_keyframes(self):
        print "clip edit keyframes:"
        for i in range(0, len(self.keyframes)):
            print self.keyframes[i]
            
    # ----------------------------------------------------------------- Draw
    def draw(self, cr):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = self.allocation
  
        # Draw bg
        cr.set_source_rgba(*OVERLAY_BG)
        cr.rectangle(x, y, w, h)
        cr.fill()

        self._draw_edit_area_borders(cr)

        # Top row
        cr.set_source_surface(HAMBURGER_ICON, x + 4.5, y + 4)
        cr.paint()

        # Draw clip out line
        clip = edit_data["clip"]
        track = edit_data["track"]

        pix_per_frame = tlinewidgets.pix_per_frame
        pos = tlinewidgets.pos
        
        clip_start_in_tline = edit_data["clip_start_in_timeline"]
        clip_start_frame = clip_start_in_tline - pos
    
        clip_in = clip.clip_in
        clip_out = clip.clip_out
        clip_length = clip_out - clip_in + 1 # +1 because in and out both inclusive
        scale_length = clip_length * pix_per_frame
        scale_in = clip_start_frame * pix_per_frame
        
        clip_outline_y = tlinewidgets._get_track_y(track.id)
         
        self.create_round_rect_path(cr, scale_in,
                                     clip_outline_y, scale_length, 
                                     track.height)
        cr.set_source_rgba(*CLIP_OUTLINE_COLOR)
        cr.set_line_width(2.0)
        cr.fill()
            
        # Frame scale and value lines
        self.frame_scale.draw(cr, edit_data["clip_start_in_timeline"], self.clip_length, self._get_upper_y(), self._get_lower_y())
        self._draw_value_lines(cr, x, w)

        kf_positions = self.get_clip_kfs_and_positions()

        # Draw value curves, area fill and audio levels,they need to be clipped into edit area
        cr.save()

        ex, ey, ew, eh = self._get_edit_area_rect()
        
        # Maybe draw audio levels
        if self.edit_type == VOLUME_KF_EDIT and clip.is_blanck_clip == False and clip.waveform_data != None:

            cr.set_source_rgba(*AUDIO_LEVELS_COLOR)
        
            y_pad = TOP_PAD
            bar_height = eh
            
            # Draw all frames only if pixels per frame > 2, otherwise
            # draw only every other or fewer frames
            draw_pix_per_frame = tlinewidgets.pix_per_frame
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

            # Get media frame 0 position in screen pixels
            media_start_pos_pix = scale_in - clip_in * pix_per_frame
            mid_y = y + y_pad + eh / 2.0
            
            # Draw level bar for each frame in draw range
            for f in range(draw_first, draw_last, step):
                try:
                    xf = media_start_pos_pix + f * pix_per_frame
                    hf = bar_height * clip.waveform_data[f] * 0.5
                    if h < 1:
                        h = 1
                    cr.rectangle(xf, mid_y - hf, draw_pix_per_frame, hf * 2.0)
                except:
                    # This is just dirty fix a when 23.98 fps does not work
                    break

            cr.fill()

        # Draw value curve and area fill
        cr.set_source_rgba(*CURVE_COLOR)
        cr.set_line_width(3.0)

        cr.rectangle(ex, ey, ew, eh)
        cr.clip() 
        for i in range(0, len(kf_positions)):
            kf, frame, kf_index, kf_pos_x, kf_pos_y = kf_positions[i]
            # this trying to get rid of some draw artifacts by limiting x positions
            if kf_pos_x < -10000:
                kf_pos_x = -10000
            if kf_pos_x > 10000:
                kf_pos_x = 10000
            if i == 0:
                cr.move_to(kf_pos_x, kf_pos_y)
            else:
                cr.line_to(kf_pos_x, kf_pos_y)
        # If last kf before clip end, continue value curve to end
        kf, frame, kf_index, kf_pos_x, kf_pos_y = kf_positions[-1]
        if kf_pos_x < ex + ew:
            cr.move_to(kf_pos_x, kf_pos_y)
            cr.line_to(ex + ew, kf_pos_y)
        else:
            cr.line_to(ex + ew, kf_pos_y)
    
        cr.stroke()
        
        cr.restore()

        # Draw keyframes
        for i in range(0, len(kf_positions)):
            kf, frame, kf_index, kf_pos_x, kf_pos_y = kf_positions[i]

            if frame < self.clip_in:
                continue
            if frame > self.clip_in + self.clip_length:
                continue  
                
            if kf_index == self.active_kf_index:
                icon = ACTIVE_KF_ICON
            else:
                icon = NON_ACTIVE_KF_ICON

            cr.set_source_surface(icon, kf_pos_x - 6, kf_pos_y - 6) # -6 to get kf bitmap center on calculated pixel
            cr.paint()

        # Draw out-of-range kf icons and kf counts
        if w > 55: # dont draw on too small editors
            before_kfs = len(self.get_out_of_range_before_kfs())
            after_kfs = len(self.get_out_of_range_after_kfs())
            
            kfy = self._get_lower_y() + KF_LOWER_OFF
            if before_kfs > 0:
                cr.set_source_surface(NON_ACTIVE_KF_ICON, x + OUT_OF_RANGE_ICON_PAD - OUT_OF_RANGE_KF_ICON_HALF * 2, kfy + KF_ICON_Y_PAD)
                cr.paint()
                self._draw_text(cr, str(before_kfs), x + OUT_OF_RANGE_NUMBER_X_START, kfy + KF_TEXT_PAD)
            if after_kfs > 0:
                cr.set_source_surface(NON_ACTIVE_KF_ICON, x + w - OUT_OF_RANGE_ICON_PAD, kfy + KF_ICON_Y_PAD)
                cr.paint()
                self._draw_text(cr, str(after_kfs), x + w - OUT_OF_RANGE_NUMBER_X_END_PAD, kfy + KF_TEXT_PAD)
        
        # Draw source triangle
        cr.set_line_width(2.0)
        cr.move_to(x - 8, self.source_track_center - 8)
        cr.line_to(x + 1, self.source_track_center)
        cr.line_to(x - 8, self.source_track_center + 8)
        cr.close_path()
        cr.set_source_rgb(*SOURCE_TRIANGLE_COLOR)
        cr.fill_preserve()
        cr.set_source_rgb(*SOURCE_TRIANGLE_OUTLINE_COLOR)
        cr.stroke()

        cr.move_to(x + w + 8, self.source_track_center - 8)
        cr.line_to(x + w - 1, self.source_track_center)
        cr.line_to(x + w + 8, self.source_track_center + 8)
        cr.close_path()
        cr.set_source_rgb(*SOURCE_TRIANGLE_COLOR)
        cr.set_source_rgb(*SOURCE_TRIANGLE_COLOR)
        cr.fill_preserve()
        cr.set_source_rgb(*SOURCE_TRIANGLE_OUTLINE_COLOR)
        cr.stroke()
        
        # Draw frame pointer
        try:
            panel_pos = self._get_panel_pos()
        except ZeroDivisionError: # math fails for 1 frame clip
            panel_pos = END_PAD
        cr.set_line_width(1.0)
        cr.set_source_rgb(*FRAME_SCALE_LINES_BRIGHT)
        cr.move_to(panel_pos, ey - 8)
        cr.line_to(panel_pos, ey + eh + 8)
        cr.stroke()

        # Draw title
        if w > 55: # dont draw on too small editors
            if self.edit_type == VOLUME_KF_EDIT:
                text = edit_data["editable_property"].clip.name + " - " + self.volume_kfs_text
            elif self.edit_type == BRIGHTNESS_KF_EDIT:
                text = edit_data["editable_property"].clip.name + " - " + self.brightness_kfs_text
            else: # PARAM_KF_EDIT
                text = edit_data["editable_property"].clip.name + " - " + self.filter_param_name_txt
            self._draw_text(cr, text, -1, y + 4, True, x, w)
            self._draw_text(cr, self.media_frame_txt + str(self.current_clip_frame), -1, kfy - 8, True, x, w)

        # Value texts
        self._draw_value_texts(cr, x, w)
     
        # Value value info
        if self.edit_value != None:
            self._draw_value_text_box(cr, self.mouse_x,self.mouse_y, str(self.edit_value))
    
    def _draw_edit_area_borders(self, cr):
        x, y, w, h = self._get_edit_area_rect()
        cr.set_source_rgb(*FRAME_SCALE_LINES)
        cr.rectangle(x, y, w, h)
        cr.stroke()

    def _draw_value_lines(self, cr, x, w):
        # Audio hard coded value lines
        active_width = w - 2 * END_PAD
        xs = x + END_PAD
        xe = xs + active_width

        if self.edit_type == VOLUME_KF_EDIT:
            # 0
            y = self._get_panel_y_for_value(0.0)
            cr.set_line_width(1.0)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
            # 50
            y = self._get_panel_y_for_value(50)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
            # 100
            y = self._get_panel_y_for_value(100)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
        elif self.edit_type == BRIGHTNESS_KF_EDIT:
            # 0
            y = self._get_panel_y_for_value(0.0)
            cr.set_line_width(1.0)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()

            # 50
            y = self._get_panel_y_for_value(50)
            cr.set_line_width(1.0)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
            # 100
            y = self._get_panel_y_for_value(100) 
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
        else:
            editable_property = edit_data["editable_property"] 
            adjustment = editable_property.get_input_range_adjustment()
            lower = adjustment.get_lower()
            upper = adjustment.get_upper()
            half = (upper - lower) / 2 + lower
            
            # Min
            y = self._get_panel_y_for_value(lower)
            cr.set_line_width(1.0)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()

            # Half
            y = self._get_panel_y_for_value(half)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()
            
            # Max
            y = self._get_panel_y_for_value(upper)
            cr.set_source_rgb(*FRAME_SCALE_LINES)
            cr.move_to(xs, y)
            cr.line_to(xe, y)
            cr.stroke()

    def _draw_value_texts(self, cr, x, w):
        # Audio hard coded value lines
        TEXT_X_OFF = 4
        TEXT_X_OFF_END = -28
        TEXT_Y_OFF = 4
        
        active_width = w - 2 * END_PAD
        xs = x + END_PAD
        xe = xs + active_width

        cr.select_font_face ("sans-serif",
                              cairo.FONT_SLANT_NORMAL,
                              cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        cr.set_source_rgb(*SCALE_LINES_TEXT_COLOR)
            
        if self.edit_type == VOLUME_KF_EDIT:
            # 0
            y = self._get_panel_y_for_value(0.0)
            
            text = "0"
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 16, y - TEXT_Y_OFF)
            cr.show_text(text)

            # 50
            y = self._get_panel_y_for_value(50)

            text = "50"
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF + 8)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 6, y - TEXT_Y_OFF + 8)
            cr.show_text(text)
            
            # 100
            y = self._get_panel_y_for_value(100)
            
            text = "100"
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF + 17)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END, y - TEXT_Y_OFF + 17)
            cr.show_text(text)
            
        elif self.edit_type == BRIGHTNESS_KF_EDIT:
            # 0
            y = self._get_panel_y_for_value(0.0)
            text = "0"
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 16, y - TEXT_Y_OFF)
            cr.show_text(text)

            # 50
            y = self._get_panel_y_for_value(50)
            
            text = "50"
            cr.move_to(xs + TEXT_X_OFF, y + 4)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 6, y + 4)
            cr.show_text(text)
            
            # 100
            y = self._get_panel_y_for_value(100) 
            
            text = "100"
            cr.move_to(xs + TEXT_X_OFF, y + 13)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END, y + 13)
            cr.show_text(text)
        else:

            editable_property = edit_data["editable_property"] 
            adjustment = editable_property.get_input_range_adjustment()
            lower = adjustment.get_lower()
            upper = adjustment.get_upper()
            half = (upper - lower) / 2 + lower
            
            # Min
            y = self._get_panel_y_for_value(lower)
            
            text = str(lower)
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 16, y - TEXT_Y_OFF)
            cr.show_text(text)

            # Half
            y = self._get_panel_y_for_value(half)

            text = str(half)
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF + 8)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END + 6, y - TEXT_Y_OFF + 8)
            cr.show_text(text)
            
            # Max
            y = self._get_panel_y_for_value(upper)
            
            text = str(upper)
            cr.move_to(xs + TEXT_X_OFF, y - TEXT_Y_OFF + 17)
            cr.show_text(text)
            cr.move_to(xe + TEXT_X_OFF_END, y - TEXT_Y_OFF + 17)
            cr.show_text(text)
            
    def _draw_text(self, cr, txt, x, y, centered=False, tline_x=-1, w=-1):
        layout = PangoCairo.create_layout(cr)
        layout.set_text(txt, -1)
        desc = Pango.FontDescription("Sans 8")
        layout.set_font_description(desc)
        lw, lh = layout.get_pixel_size()
            
        if centered == True:
            x = w/2 - lw/2 + tline_x

        if lw > w:
            return

        cr.move_to(x, y)
        cr.set_source_rgb(*TEXT_COLOR)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)

    def _draw_value_text_box(self, cr, x, y, text):
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

    def create_round_rect_path(self, cr, x, y, width, height, radius=4.0):
        degrees = math.pi / 180.0

        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()
        
    # ----------------------------------------------------------- mouse events
    def press_event(self, event):
        """
        Mouse button callback
        """
        # Check if menu icons hit
        if self._oor_start_kf_hit(event.x, event.y) == True:
            self._show_oor_before_menu(gui.tline_canvas.widget, event)
            return

        if self._oor_end_kf_hit(event.x, event.y) == True:
            self._show_oor_after_menu(gui.tline_canvas.widget, event)
            return

        if self._hamburger_hit(event.x, event.y) == True:
            self._show_hamburger_menu(gui.tline_canvas.widget, event)
            return

        lx = self._legalize_x(event.x)
        ly = self._legalize_y(event.y)

        self.value_drag_on = False
        self.mouse_start_y = ly

        self.mouse_x = lx
        self.mouse_y = ly

        if event.button == 3: # right mouse
            self.current_mouse_action = POSITION_DRAG
            
            self.drag_min = self.clip_in
            self.drag_max = self.clip_in + self.clip_length
            frame = self._get_drag_frame(lx)
            self.current_clip_frame = frame
            self.clip_editor_frame_changed(self.current_clip_frame)
            
            updater.repaint_tline()
            return
            
        hit_kf = self._key_frame_hit(lx, ly)

        if hit_kf == None: # nothing was hit, add new keyframe and set it active
            frame =  self._get_frame_for_panel_pos(lx)
            value = round(self._get_value_for_panel_y(ly))
            self.add_keyframe(frame, value)
            hit_kf = self.active_kf_index 
        else: # some keyframe was pressed
            self.active_kf_index = hit_kf
            
        frame, value = self.keyframes[hit_kf]
        self.edit_value = round(value)
        self.current_clip_frame = frame
        if hit_kf == 0:
            self.current_mouse_action = KF_DRAG_FRAME_ZERO_KF
        else:
            self.current_mouse_action = KF_DRAG
            
            prev_frame, val = self.keyframes[hit_kf - 1]
            self.drag_min = prev_frame  + 1
            try:
                next_frame, val = self.keyframes[hit_kf + 1]
                self.drag_max = next_frame - 1
            except:
                self.drag_max = self.clip_in + self.clip_length
                
        updater.repaint_tline()

    def motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        lx = self._legalize_x(x)
        ly = self._legalize_y(y)

        if abs(self.mouse_start_y - ly) > DRAG_MIN_Y:
            self.value_drag_on = True

        self.mouse_x = lx
        self.mouse_y = ly
        
        if self.current_mouse_action == POSITION_DRAG:
            frame = self._get_drag_frame(lx)
            self.current_clip_frame = frame
            self.clip_editor_frame_changed(self.current_clip_frame)
            updater.repaint_tline()
        elif self.current_mouse_action == KF_DRAG or self.current_mouse_action == KF_DRAG_FRAME_ZERO_KF:
            frame = self._get_drag_frame(lx)
            if self.current_mouse_action == KF_DRAG_FRAME_ZERO_KF:
                frame = 0
            if self.value_drag_on == True:
                value = round(self._get_value_for_panel_y(ly))
                if _snapping == 2:
                    value = round(value / 2) * 2
                elif  _snapping == 5:
                    value = round(value / 5.0) * 5
                self.edit_value = value
                self.set_active_kf_frame_and_value(frame, value)
            else:
                self.set_active_kf_frame_and_value(frame, self.edit_value)
            if _playhead_follow_kf == True:
                self.current_clip_frame = frame
                self.clip_editor_frame_changed(self.current_clip_frame)

        updater.repaint_tline()
        
    def release_event(self, x,y):
        """
        Mouse release callback.
        """
        lx = self._legalize_x(x)
        ly = self._legalize_y(y)

        if abs(self.mouse_start_y - ly) < DRAG_MIN_Y:
            value_drag_on = True
            
        self.mouse_x = lx
        self.mouse_y = ly

        if self.current_mouse_action == POSITION_DRAG:
            frame = self._get_drag_frame(lx)
            self.current_clip_frame = frame
            self.clip_editor_frame_changed(self.current_clip_frame)
            updater.repaint_tline()
        elif self.current_mouse_action == KF_DRAG or self.current_mouse_action == KF_DRAG_FRAME_ZERO_KF:
            frame = self._get_drag_frame(lx)
            if self.current_mouse_action == KF_DRAG_FRAME_ZERO_KF:
                frame = 0
            if self.value_drag_on == True:
                value = round(self._get_value_for_panel_y(ly))
                if _snapping == 2:
                    value = round(value / 2) * 2
                elif  _snapping == 5:
                    value = round(value / 5) * 5
                self.set_active_kf_frame_and_value(frame, value)
                self.hack_fix_for_zero_one_keyframe_problem()
            else:
                self.set_active_kf_frame_and_value(frame, self.edit_value)
                self.hack_fix_for_zero_one_keyframe_problem()

            if _playhead_follow_kf == True:
                self.current_clip_frame = frame
                self.clip_editor_frame_changed(self.current_clip_frame)
            self.update_property_value()

        self.edit_value = None
        
        updater.repaint_tline()
        self.current_mouse_action = None
        
    # --------------------------------------------------------------- keyframes funcs
    def get_clip_kfs_and_positions(self):
        kf_positions = []
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]

            try:
                kf_pos_x = self._get_panel_pos_for_frame(frame)
            except ZeroDivisionError: # math fails for 1 frame clip
                kf_pos_x = END_PAD
                
            kf_pos_y = self._get_panel_y_for_value(value)
            
            kf_positions.append((self.keyframes[i], frame, i, kf_pos_x, kf_pos_y))

        return kf_positions

    def get_out_of_range_before_kfs(self):
        # returns Keyframes before current clip start
        kfs = []
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]
            if frame < self.clip_in:
                kfs.append(self.keyframes[i])
        return kfs

    def get_out_of_range_after_kfs(self):
        # returns Keyframes before current clip start
        kfs = []
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]
            if frame > self.clip_in + self.clip_length:
                kfs.append(self.keyframes[i])
        return kfs
                
    def add_keyframe(self, frame, value):
        kf_index_on_frame = self.frame_has_keyframe(frame)
        if kf_index_on_frame != -1:
            # Trying add on top of existing keyframe makes it active
            self.active_kf_index = kf_index_on_frame
            return

        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value = self.keyframes[i]
            if kf_frame > frame:
                #prev_frame, prev_value = self.keyframes[i - 1]
                self.keyframes.insert(i, (frame, value))
                self.active_kf_index = i
                return

        self.keyframes.append((frame, value))
        self.active_kf_index = len(self.keyframes) - 1

    def delete_active_keyframe(self):
        if self.active_kf_index == 0:
            # keyframe frame 0 cannot be removed
            return
        self.keyframes.pop(self.active_kf_index)
        self.active_kf_index -= 1
        if self.active_kf_index < 0:
            self.active_kf_index = 0
        self._set_pos_to_active_kf()
        self.update_property_value()
        
        updater.repaint_tline()

    def set_and_display_clip_frame(self, clip_frame):
        self.current_clip_frame = clip_frame
        self._force_current_in_frame_range()
                
    def _set_pos_to_active_kf(self):
        frame, value = self.keyframes[self.active_kf_index]
        self.current_clip_frame = frame
        self._force_current_in_frame_range()
            
    def frame_has_keyframe(self, frame):
        """
        Returns index of keyframe if frame has keyframe or -1 if it doesn't.
        """
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value = self.keyframes[i]
            if frame == kf_frame:
                return i

        return -1
    
    def get_active_kf_frame(self):
        frame, val = self.keyframes[self.active_kf_index]
        return frame

    def get_active_kf_value(self):
        frame, val = self.keyframes[self.active_kf_index]
        return val
    
    def set_active_kf_value(self, new_value):
        frame, val = self.keyframes.pop(self.active_kf_index)
        self.keyframes.insert(self.active_kf_index,(frame, new_value))

    def active_kf_pos_entered(self, frame):
        if self.active_kf_index == 0:
            return
        
        prev_frame, val = self.keyframes[self.active_kf_index - 1]
        prev_frame += 1
        try:
            next_frame, val = self.keyframes[self.active_kf_index + 1]
            next_frame -= 1
        except:
            next_frame = self.clip_length - 1
        
        frame = max(frame, prev_frame)
        frame = min(frame, next_frame)

        self.set_active_kf_frame(frame)
        self.current_clip_frame = frame    
        
    def set_active_kf_frame(self, new_frame):
        frame, val = self.keyframes.pop(self.active_kf_index)
        self.keyframes.insert(self.active_kf_index,(new_frame, val))

    def set_active_kf_frame_and_value(self, new_frame, new_value):
        frame, val = self.keyframes.pop(self.active_kf_index)
        self.keyframes.insert(self.active_kf_index,(new_frame, new_value))

    def hack_fix_for_zero_one_keyframe_problem(self):
        # This is a quick, ugly fix for bug where having volume keyframes in frames 0 and 1 mutes the whole clip.
        # Look to fix underlying problem.
        try:
            kf1, val1 = self.keyframes[0]
            kf2, val2 = self.keyframes[1]
            if kf1 == 0 and kf2 == 1 and self.edit_type == VOLUME_KF_EDIT:
                self.keyframes.pop(1)
        except:
            pass

    # ------------------------------------------------- coordinates spaces
    def _get_edit_area_rect(self):
        x, y, w, h = self.allocation
        active_width = w - 2 * END_PAD
        ly = self._get_lower_y()
        uy = self._get_upper_y()
        return (x + END_PAD, uy, active_width - 1, ly - uy)
    
    def _get_panel_pos(self):
        return self._get_panel_pos_for_frame(self.current_clip_frame) 

    def _get_panel_pos_for_frame(self, clip_frame):
        x, y, width, h = self.allocation
        active_width = width - 2 * END_PAD
        disp_frame = clip_frame - self.clip_in 
        return x + END_PAD + int((float(disp_frame) / float(self.clip_length)) * 
                             float(active_width))

    def _get_frame_for_panel_pos(self, panel_x):
        rx, ry, rw, rh = self._get_edit_area_rect()
        clip_panel_x = panel_x - rx
        norm_pos = float(clip_panel_x) / float(rw)
        return int(norm_pos * self.clip_length) + self.clip_in

    def _get_value_for_panel_y(self, panel_y):
        rx, ry, rw, rh = self._get_edit_area_rect()
        editable_property = edit_data["editable_property"] 
        adjustment = editable_property.get_input_range_adjustment()
        lower = adjustment.get_lower()
        upper = adjustment.get_upper()
        value_range = upper - lower
        pos_fract = (ry + rh - panel_y) / rh
        return pos_fract * value_range + lower
        
    def _get_panel_y_for_value(self, value):
        editable_property = edit_data["editable_property"] 
        adjustment = editable_property.get_input_range_adjustment()
        lower = adjustment.get_lower()
        upper = adjustment.get_upper()
        value_range = upper - lower
        value_fract = (value - lower) / value_range
        return self._get_lower_y() - (self._get_lower_y() - self._get_upper_y()) * value_fract

    def _get_lower_y(self):
        x, y, w, h = self.allocation
        return y + TOP_PAD + h - HEIGHT_PAD_PIXELS_TOTAL

    def _get_upper_y(self):
        x, y, w, h = self.allocation
        return  y + TOP_PAD

    def _legalize_x(self, x):
        """
        Get x in pixel range between end pads.
        """
        rx, ry, rw, rh = self._get_edit_area_rect()
        if x < rx:
            return rx
        elif x > rx + rw:
            return rx + rw
        else:
            return x
    
    def _legalize_y(self, y):
        rx, ry, rw, rh = self._get_edit_area_rect()
        if y < ry:
            return ry
        elif y > ry + rh:
            return ry + rh
        else:
            return y

    # ------------------------------------------------- frames
    def _force_current_in_frame_range(self):
        if self.current_clip_frame < self.clip_in:
            self.current_clip_frame = self.clip_in
        if self.current_clip_frame > self.clip_in + self.clip_length:
            self.current_clip_frame = self.clip_in + self.clip_length
        
    def _get_drag_frame(self, panel_x):
        """
        Get x in range available for current drag.
        """
        frame = self._get_frame_for_panel_pos(panel_x)
        if frame < self.drag_min:
            frame = self.drag_min
        if frame > self.drag_max:
            frame = self.drag_max
        return frame
    
    # ----------------------------------------------------- hit testing
    def _key_frame_hit(self, x, y):
        for i in range(0, len(self.keyframes)):
            frame, val = self.keyframes[i]
            frame_x = self._get_panel_pos_for_frame(frame)
            value_y = self._get_panel_y_for_value(val)
            if((abs(x - frame_x) < KF_HIT_WIDTH)
                and (abs(y - value_y) < KF_HIT_WIDTH)):
                return i
            
        return None

    def _area_hit(self, tx, ty, x, y, w, h):
        if ty >= y and ty <= y + h: # 12 icon size
            if tx >= x and tx <= x + w:
                return True
            
        return False
        
    def _oor_start_kf_hit(self, x, y):
        rx, ry, rw, rh = self.allocation
        kfy = self._get_lower_y() + KF_LOWER_OFF
        area_y = kfy + KF_ICON_Y_PAD
        area_x = rx + OUT_OF_RANGE_ICON_PAD - OUT_OF_RANGE_KF_ICON_HALF * 2
        return self._area_hit(x, y, area_x, area_y, 12, 12)

    def _oor_end_kf_hit(self, x, y):
        rx, ry, rw, rh = self.allocation
        kfy = self._get_lower_y() + KF_LOWER_OFF
        area_x = rx + rw - OUT_OF_RANGE_ICON_PAD
        area_y = kfy + KF_ICON_Y_PAD
        return self._area_hit(x, y, area_x, area_y, 12, 12)

    def _hamburger_hit(self, x, y):
        rx, ry, rw, rh = self.allocation
        return self._area_hit(x, y, rx + 4.5, ry + 4, 12, 12)
        

    def overlay_area_hit(self, tx, ty):
        x, y, w, h = self.allocation
        if tx >= x and tx <= x + w:
            if ty >= y and ty <= y + h:
                return True
        
        return False

    # ------------------------------------------------------------ menus
    def _show_oor_before_menu(self, widget, event):
        menu = oor_before_menu
        self._build_oor_before_menu(menu)
        menu.popup(None, None, None, None, event.button, event.time)

    def _build_oor_before_menu(self, menu):
        guiutils.remove_children(menu)
        before_kfs = len(self.get_out_of_range_before_kfs())

        if before_kfs == 0 or (before_kfs == 1 and len(self.keyframes) == 1):
            item = self._get_menu_item(_("No Edit Actions currently available"), self._oor_menu_item_activated, "noop" )
            item.set_sensitive(False)
            menu.add(item)

        if before_kfs > 1:
            menu.add(self._get_menu_item(_("Delete all but first Keyframe before Clip Range"), self._oor_menu_item_activated, "delete_all_before" ))
            sep = Gtk.SeparatorMenuItem()
            sep.show()
            menu.add(sep)

        if len(self.keyframes) > 1 and before_kfs > 0:
            menu.add(self._get_menu_item(_("Set Keyframe at Frame 0 to value of next Keyframe"), self._oor_menu_item_activated, "zero_next" ))

    def _show_oor_after_menu(self, widget, event):
        menu = oor_before_menu
        self._build_oor_after_menu(menu)
        menu.popup(None, None, None, None, event.button, event.time)

    def _build_oor_after_menu(self, menu):
        guiutils.remove_children(menu)
        after_kfs = len(self.get_out_of_range_after_kfs())

        if after_kfs == 0:
            item = self._get_menu_item(_("No Edit Actions currently available"), self._oor_menu_item_activated, "noop" )
            item.set_sensitive(False)
            menu.add(item)
            return

        if self.edit_type == BRIGHTNESS_KF_EDIT:
            menu.add(self._get_menu_item(_("Delete all Keyframes after Clip Range"), self._oor_menu_item_activated, "delete_all_after" ))
        elif self.edit_type == VOLUME_KF_EDIT:
            if after_kfs > 1:
                menu.add(self._get_menu_item(_("Delete all but last Keyframe after Clip Range"), self._oor_menu_item_activated, "delete_all_but_last_after" ))
            else:
                item = self._get_menu_item(_("No Edit Actions currently available"), self._oor_menu_item_activated, "noop" )
                item.set_sensitive(False)
                menu.add(item)

    def _show_hamburger_menu(self, widget, event):
        menu = hamburger_menu
        guiutils.remove_children(menu)

        if edit_data["track"].type == appconsts.VIDEO:
            if edit_data["clip"].media_type == appconsts.VIDEO:
                edit_volume = self._get_menu_item(_("Edit Volume Keyframes"), self._oor_menu_item_activated, "edit_volume" )
                if self.edit_type == VOLUME_KF_EDIT:
                    edit_volume.set_sensitive(False)
                menu.add(edit_volume)

                edit_brightness = self._get_menu_item(_("Edit Brightness Keyframes"), self._oor_menu_item_activated, "edit_brightness" )
                if self.edit_type == BRIGHTNESS_KF_EDIT:
                    edit_brightness.set_sensitive(False)
                menu.add(edit_brightness)

            editable_params_exist = False
            params_menu_item = Gtk.MenuItem(_("Edit Other Filter Parameters"))
            params_menu = Gtk.Menu()
            guiutils.remove_children(params_menu)
            for i in range(0, len(edit_data["clip"].filters)):
                filt = edit_data["clip"].filters[i]
                for prop in filt.properties:
                    p_name, p_val, p_type = prop
                    args_str = filt.info.property_args[p_name]

                    args_dict = propertyparse.args_string_to_args_dict(args_str)
                    try:
                        editor = args_dict["editor"]
                    except:
                        editor = "slider"
                        
                    try:
                        disp_name = args_dict["displayname"]
                    except:
                        disp_name = p_name

                    try:
                        range_in = args_dict["range_in"]
                    except:
                        range_in = None

                    if (editor == "slider" or editor == "keyframe_editor") and range_in != None:
                        param_data = (p_name, filt, i, disp_name)
                        editable_params_exist = True
                        item_text = filt.info.name  + ": " +  disp_name
                        param_item = self._get_menu_item(item_text, self._param_edit_item_activated, param_data)
                        params_menu.add(param_item)
                        
            if editable_params_exist == False:
                params_menu_item.set_sensitive(False)
            params_menu_item.set_submenu(params_menu)
            params_menu_item.show_all()
            menu.add(params_menu_item)
        
            sep = Gtk.SeparatorMenuItem()
            sep.show()
            menu.add(sep)

        leading_menu_item = Gtk.MenuItem(_("Leading Keyframes"))
        leading_menu = Gtk.Menu()
        self._build_oor_before_menu(leading_menu)
        leading_menu_item.set_submenu(leading_menu)
        leading_menu_item.show_all()
        menu.add(leading_menu_item)
        
        trailing_menu_item = Gtk.MenuItem(_("Trailing Keyframes"))
        trailing_menu = Gtk.Menu()
        self._build_oor_after_menu(trailing_menu)
        trailing_menu_item.set_submenu(trailing_menu)
        trailing_menu_item.show_all()
        menu.add(trailing_menu_item)
        
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.add(sep)
        
        playhead_follow_item = Gtk.CheckMenuItem()
        playhead_follow_item.set_label(_("Playhead Follows Dragged Keyframe"))
        playhead_follow_item.set_active(_playhead_follow_kf)
        playhead_follow_item.connect("activate", self._oor_menu_item_activated, "playhead_follows")
        playhead_follow_item.show()
        menu.add(playhead_follow_item)

        value_snapping_item = Gtk.MenuItem(_("Value Snapping"))
        value_snapping_menu = Gtk.Menu()
        guiutils.remove_children(value_snapping_menu)

        first_item = Gtk.RadioMenuItem()
        first_item.set_label("1")
        if _snapping == 1:
            first_item.set_active(True)
        first_item.show()
        value_snapping_menu.append(first_item)
        first_item.connect("activate", self._oor_menu_item_activated, "1")

        radio_item = Gtk.RadioMenuItem.new_with_label([first_item], "2")
        if _snapping == 2:
            radio_item.set_active(True)
        radio_item.connect("activate", self._oor_menu_item_activated, "2")
        value_snapping_menu.append(radio_item)
        radio_item.show()

        radio_item = Gtk.RadioMenuItem.new_with_label([first_item], "5")
        if _snapping == 5:
            radio_item.set_active(True)
        radio_item.connect("activate", self._oor_menu_item_activated, "5")
        value_snapping_menu.append(radio_item)
        radio_item.show()

        value_snapping_item.set_submenu(value_snapping_menu)
        value_snapping_item.show_all()
        menu.add(value_snapping_item)
        
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.add(sep)
        
        menu.add(self._get_menu_item(_("Exit Edit"), self._oor_menu_item_activated, "exit" ))
        
        menu.popup(None, None, None, None, event.button, event.time)

    def _oor_menu_item_activated(self, widget, data):
        global _snapping
        
        if data == "delete_all_before":
            keep_doing = True
            while keep_doing:
                try:
                    frame, value = self.keyframes[1]
                    if frame < self.clip_in:
                        self.keyframes.pop(1)
                    else:
                        keep_doing = False 
                except:
                    keep_doing = False
        
        elif data == "delete_all_but_last_after":
        
            keep_doing = True
            index = 1
            while keep_doing:
                try:
                    frame, value = self.keyframes[index]
                    if frame > self.clip_in + self.clip_length and index < (len(self.keyframes) - 1):
                        self.keyframes.pop(index)
                    else:
                        index += 1
                except:
                    keep_doing = False
                    
        elif data == "zero_next":
            frame_zero, frame_zero_value = self.keyframes[0]
            frame, value = self.keyframes[1]
            self.keyframes.pop(0)
            self.keyframes.insert(0, (frame_zero, value))
            self.update_property_value()
        elif data == "delete_all_after":
            delete_done = False
            for i in range(0, len(self.keyframes)):
                frame, value = self.keyframes[i]
                if frame > self.clip_in + self.clip_length:
                    self.keyframes.pop(i)
                    popped = True
                    while popped:
                        try:
                            self.keyframes.pop(i)
                        except:
                            popped = False
                    delete_done = True
                if delete_done:
                    break
        elif data == "edit_brightness":
            init_tool_for_clip(edit_data["clip"] , edit_data["track"], BRIGHTNESS_KF_EDIT)
        elif data == "edit_volume":
            init_tool_for_clip(edit_data["clip"] , edit_data["track"], VOLUME_KF_EDIT)
        elif data == "exit":
            set_no_clip_edit_data()
        elif data == "playhead_follows":
            global _playhead_follow_kf
            _playhead_follow_kf = widget.get_active()
        elif data == "1":
            _snapping = 1
        elif data == "2":
            _snapping = 2
        elif data == "5":
            _snapping = 5

        updater.repaint_tline()

    def _param_edit_item_activated(self,  widget, data):
        init_tool_for_clip(edit_data["clip"],  edit_data["track"], PARAM_KF_EDIT, data)

    def _get_menu_item(self, text, callback, data):
        item = Gtk.MenuItem(text)
        item.connect("activate", callback, data)
        item.show()
        return item


