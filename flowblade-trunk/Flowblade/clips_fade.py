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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module handles button actions events from buttons in the middle bar.

Add buttons for use mouse easily.
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject
from gi.repository import Gst

import os

import appconsts
import clipeffectseditor
import dialogutils
import edit
import editorpersistance
from editorstate import get_track
from editorstate import PLAYER
from editorstate import timeline_visible
import gui
import kftoolmode
import mltfilters
import movemodes
import updater

# Edit types
VOLUME_KF_EDIT = kftoolmode.VOLUME_KF_EDIT # 0
BRIGHTNESS_KF_EDIT = kftoolmode.BRIGHTNESS_KF_EDIT # 1
PARAM_KF_EDIT = kftoolmode.PARAM_KF_EDIT # 2
VIDEO = appconsts.VIDEO # 0
AUDIO = appconsts.AUDIO # 2
IMAGE = appconsts.IMAGE # 3


def clip_accept():
    if not timeline_visible():
        updater.display_sequence_in_monitor()

    track_index = movemodes.selected_track
    print("ct 77 track_index ", track_index)

    # Get track
    track = get_track(movemodes.selected_track)
    print ("cp 81 track", track_index, track)

    # Get index and clip
    tline_frame = PLAYER().current_frame()
    if editorpersistance.prefs.trans_cover_delete == True:
        # Get pressed clip index
        clip_index = movemodes.selected_range_in
        print("cp 88 ", clip_index)
        if clip_index == -1: # No selected clip
            print("cp 90 ", "No selected clip")
            title = "Warning"
            message = "First select a clip \n"
            Alert(title, message, "service-logout.oga")
            return None# Frame is after last clip in track
        if movemodes.selected_range_out == movemodes.selected_range_in: # one clip
            clip = track.clips[clip_index]
            # don't fade blanck clips or headplay out of clip
            if clip.is_blanck_clip:
                print("cp 99 ", "blanck")
                title = "Warning"
                message = "Blank selected : select a clip \n"
                Alert(title, message, "service-logout.oga")
                return None
            if hasattr(clip, "rendered_type"):
                print("cp 99 ", "render")
                title = "Warning"
                message = "Render selected : select a clip without render \n"
                Alert(title, message, "service-logout.oga")
                return None
        clip_start = track.clip_start(clip_index)
        clip_end = clip_start + (clip.clip_out + 1 - clip.clip_in) # frames are inclusive
        print("\ncp 93", clip_start, tline_frame, clip_end, clip.clip_in, clip.get_length(), clip.clip_out + 1)
        if tline_frame <= clip_start or tline_frame >= clip_end:
            title = "Warning"
            message = "Put the playhead inside the clip \n"
            Alert(title, message, "service-logout.oga")
            return None
        else:
            print("cp 114 ", clip.media_type, clip.filters)
            return clip, track, tline_frame, clip_start, clip_index, track_index

def fade_in():
    print("Fade in")
    c_a = clip_accept()
    if c_a is not None:
        clip, track, tline_frame, clip_start, clip_index, track_index = c_a
        if clip.media_type == appconsts.VIDEO:
            print("ct 120 video")
            create_keyframe_fadein(clip, track, tline_frame, clip_start, edit_type=BRIGHTNESS_KF_EDIT, param_data=None)
            create_keyframe_fadein(clip, track, tline_frame, clip_start, edit_type=VOLUME_KF_EDIT, param_data=None)
        elif clip.media_type == appconsts.AUDIO:
            print("ct 124 audio")
            create_keyframe_fadein(clip, track, tline_frame, clip_start, edit_type=VOLUME_KF_EDIT, param_data=None)
        elif clip.media_type == appconsts.IMAGE:
            print("ct 127 image", appconsts.IMAGE)
            create_keyframe_fadein(clip, track, tline_frame, clip_start, edit_type=BRIGHTNESS_KF_EDIT, param_data=None)
        else:
            return

def create_keyframe_fadein(clip, track, tline_frame, clip_start, edit_type=VOLUME_KF_EDIT, param_data=None):
    # Adapted from kftoolmode.init_tool_for_clip()
    # These can produce data for same objects we choose not to commit to updating
    # clipeffectseditor/kftool with events from each other.
    clipeffectseditor.clear_clip()

    clip_index = track.clips.index(clip)
    clip_end = clip_start + (clip.clip_out + 1 - clip.clip_in) # frames are inclusive
    # Save data needed to do the keyframe edits.
    global edit_data #, pressed_on_selected, drag_disabled
    edit_data = {#"draw_function":_tline_overlay,
                 "clip_index":clip_index,
                 "clip_start_in_timeline":track.clip_start(clip_index),
                 "clip":clip,
                 "track":track,
                 "initializing":True}
    print("ct 149 edit type", edit_type, clip_end - clip_start)
    if edit_type == PARAM_KF_EDIT:
        pass # We are not trying to decide based on track what to edit
    print("ct 164 ", edit_type)
    global kf_editor

    # Init for edit type
    if edit_type == VOLUME_KF_EDIT:
        ep = kftoolmode._get_volume_editable_property(clip, track, clip_index)
        if ep == None:
            filter_info = mltfilters.get_volume_filters_info()
            data = {"clip":clip,
                    "filter_info":filter_info,
                    "filter_edit_done_func":kftoolmode._filter_create_dummy_func}
            action = edit.add_multipart_filter_action(data)
            action.do_edit()
            ep = kftoolmode._get_volume_editable_property(clip, track, clip_index)

        edit_data["editable_property"] = ep
        print("cp 180 v ed epname", edit_data, " -----", ep.name)
        kf_editor = kftoolmode.TLineKeyFrameEditor(ep, True, VOLUME_KF_EDIT)

    elif edit_type == BRIGHTNESS_KF_EDIT:
        ep = kftoolmode._get_brightness_editable_property(clip, track, clip_index)
        if ep == None:
            print("ct 186 ep None")
            filter_info = mltfilters.get_brightness_filter_info()
            data = {"clip":clip,
                    "filter_info":filter_info,
                    "filter_edit_done_func":kftoolmode._filter_create_dummy_func}
            action = edit.add_filter_action(data)
            action.do_edit()
            ep =kftoolmode._get_brightness_editable_property(clip, track, clip_index)

        edit_data["editable_property"] = ep
        print("ct 196 b ed epname", edit_data, " -----", ep.name, " +++ ", clip.filters)
        kf_editor = kftoolmode.TLineKeyFrameEditor(ep, True, BRIGHTNESS_KF_EDIT)

    else: #  edit_type == PARAM_KF_EDIT
        return

    print("ct 186 kf ed ", kf_editor.keyframes)
    # Clean disturbing keyframes and add a last keyframe if it doesn't exist
    while test_keyframe_after_pos(kf_editor.keyframes, clip.clip_out + 1): # Images have keyframe at 7350 or more
        kf_editor.keyframes.pop(len(kf_editor.keyframes) - 1)
        edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
        print("ct 191 kf ed fin ", kf_editor.keyframes)
    if len(kf_editor.keyframes) == 1: # Sometimes (?), there is no end keyframe : so we add it
        kf_editor.add_keyframe(clip.clip_out + 1, kf_editor.keyframes[0][1])
    print("ct 194 kf ed ", kf_editor.keyframes)

    keyframe_fade = tline_frame - clip_start + clip.clip_in
    print("ct 197 kff ", keyframe_fade, kf_editor.keyframes)
    # kft  value of the keyframe to use : previous or next
    kft = keyframe_fadein_choice(kf_editor.keyframes, keyframe_fade, clip.clip_in)
    print("ct 200 kft  ", kft)
    kf_editor.add_keyframe(keyframe_fade, kft)
    print("ct 202 kf ed ", kf_editor.keyframes)
    while test_keyframe_before_pos(kf_editor.keyframes, keyframe_fade):
        kf_editor.keyframes.pop(1)
        edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
        print("ct 206 kf ed fin ", kf_editor.keyframes)
    frame, val = kf_editor.keyframes.pop(0)
    kf_editor.keyframes.insert(0,(frame, 0.0))
    if clip.clip_in > 0: # the first visible keyframe is at clip_in and the keyframe 0 is hidden
        kf_editor.keyframes.insert(1,(clip.clip_in, 0.0))
    print("cf 211 kf ed fin ", kf_editor.keyframes)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    kf_editor.keyframes = three_consecutive_keyframes(kf_editor.keyframes)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 215 kf ed fin nett ", kf_editor.keyframes)
    verif(clip_start, 50)

def test_keyframe_before_pos(keyframes_list, keyframe_fade):

    for i in range(1, len(keyframes_list)): # keyframe 0 not deleted
        print("cf 220 kli ", keyframes_list[i], keyframe_fade)
        if keyframe_fade > keyframes_list[i][0]:
           return i
        if keyframe_fade == keyframes_list[i][0]:
            pass
    print("cf 225 ", keyframes_list)
    return 0

def keyframe_fadein_choice(keyframes_list, keyframe_fade, clip_in):
    """ Fadein exists and keyframe_fade is between 0 and the end of the fade.
    """
    print("cf 231 kli ", keyframes_list, len(keyframes_list))
    if keyframes_list[0][1] == 0.0: # Fade in exists, use next keyframe value
        if clip_in > 0:
            val = keyframes_list[2][1]
        else:
            val = keyframes_list[1][1]
    else:
        val = keyframes_list[0][1] # No fade, use first keyframe value
    return val

def three_consecutive_keyframes(keyframes_list):
    """ If three consecutive keyframes have the same value, the second is removed.
    """
    for i in range(0, len(keyframes_list)): # keyframe 0 not deleted
        print("cf 237 kli ", i, keyframes_list[i])
        if i + 2 < len(keyframes_list):
            print("cf 239 kli ", i, keyframes_list[i], keyframes_list[i + 1][1], keyframes_list[i + 2][1])
            if keyframes_list[i][1] == keyframes_list[i + 1][1] and  keyframes_list[i][1] == keyframes_list[i + 2][1]:
               del keyframes_list[i + 1]
               three_consecutive_keyframes(keyframes_list)
        else:
            break
    return keyframes_list

def fade_out():
    print("Fade out")
    c_a = clip_accept()
    if c_a is not None:
        clip, track, tline_frame, clip_start, clip_index, track_index = c_a
        if clip.media_type == appconsts.VIDEO:
            print("cf 252 video")
            create_keyframe_fadeout(clip, track, tline_frame, clip_start, edit_type=BRIGHTNESS_KF_EDIT, param_data=None)
            create_keyframe_fadeout(clip, track, tline_frame, clip_start, edit_type=VOLUME_KF_EDIT, param_data=None)
        elif clip.media_type == appconsts.AUDIO:
            print("cf 256 audio")
            create_keyframe_fadeout(clip, track, tline_frame, clip_start, edit_type=VOLUME_KF_EDIT, param_data=None)
        elif clip.media_type == appconsts.IMAGE:
            print("cf 259 image")
            create_keyframe_fadeout(clip, track, tline_frame, clip_start,edit_type=BRIGHTNESS_KF_EDIT, param_data=None)
        else:
            return

def create_keyframe_fadeout(clip, track, tline_frame, clip_start,  edit_type=VOLUME_KF_EDIT, param_data=None):
    # Adapted from kftoolmode.init_tool_for_clip()
    # These can produce data for same objects we choose not to commit to updating
    # clipeffectseditor/kftool with events from each other.
    clipeffectseditor.clear_clip()
    print("cf 269 ed typ", edit_type)
    clip_index = track.clips.index(clip)
    clip_end = clip_start + clip.clip_out + 1 # frames are inclusive
    keyframe_end = clip.clip_out + 1
    keyframe_fade = tline_frame - clip_start + clip.clip_in
    print("cf 275 kff 0 ", keyframe_fade, keyframe_end)
    print("cf 275 kff ", clip_start, tline_frame, clip_end, clip.get_length(), clip.clip_out + 1)
    # Save data needed to do the keyframe edits.
    global edit_data #, pressed_on_selected, drag_disabled
    edit_data = {#"draw_function":_tline_overlay,
                 "clip_index":clip_index,
                 "clip_start_in_timeline":track.clip_start(clip_index),
                 "clip":clip,
                 "track":track,
                 "initializing":True}

    if edit_type == PARAM_KF_EDIT:
        pass # We are not trying to decide based on track what to edit

    global kf_editor

    # Init for edit type
    if edit_type == VOLUME_KF_EDIT:
        ep = kftoolmode._get_volume_editable_property(clip, track, clip_index)
        if ep == None:
            filter_info = mltfilters.get_volume_filters_info()
            data = {"clip":clip,
                    "filter_info":filter_info,
                    "filter_edit_done_func":kftoolmode._filter_create_dummy_func}
            action = edit.add_multipart_filter_action(data)
            action.do_edit()
            ep = kftoolmode._get_volume_editable_property(clip, track, clip_index)
        print("cf 301 ep", ep)
        edit_data["editable_property"] = ep
        print("cf 303 ", edit_data)
        kf_editor = kftoolmode.TLineKeyFrameEditor(ep, True, VOLUME_KF_EDIT)
        print("cf 305 kf ed ", kf_editor.keyframes)
        print("kff vol", keyframe_fade)

    elif edit_type == BRIGHTNESS_KF_EDIT:
        ep = kftoolmode._get_brightness_editable_property(clip, track, clip_index)
        if ep == None:

            filter_info = mltfilters.get_brightness_filter_info()
            data = {"clip":clip,
                    "filter_info":filter_info,
                    "filter_edit_done_func":kftoolmode._filter_create_dummy_func}
            action = edit.add_filter_action(data)
            action.do_edit()
            ep =kftoolmode._get_brightness_editable_property(clip, track, clip_index)

        edit_data["editable_property"] = ep
        print("cf 321 ", edit_data)
        kf_editor = kftoolmode.TLineKeyFrameEditor(ep, True, BRIGHTNESS_KF_EDIT)
        print("cf 323 kf ed ", kf_editor.keyframes)
        print("kff br", keyframe_fade)

    else: #  edit_type == PARAM_KF_EDIT
        return

#    # Create end keyframe if it does not exist ; the value is set to 0.0
    kfe = kf_editor.frame_has_keyframe(keyframe_end)
    if kfe == -1:
        kf_editor.add_keyframe(keyframe_end, 0.0)
        edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    else:
        kf_editor.keyframes[kfe] = (keyframe_end, 0.0)
#        frame, val = kf_editor.keyframes.pop(kfe)
#        kf_editor.keyframes.insert(kfe,(frame, 0.0))
        edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 340 kf ed ", kf_editor.keyframes)

    # Add the fade keyframe
    kf_editor.add_keyframe(keyframe_fade, 100.0)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 345 ", kf_editor.keyframes)
    # Remove the keyframes after the end keyframe
    kf_editor.keyframes = remove_keyframe_after_pos(kf_editor.keyframes, keyframe_end)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 349 ", kf_editor.keyframes)
#    # Remove the keyframes between the fade keyframe and the end keyframe
    kf_editor.keyframes = remove_keyframe_after_kff(kf_editor.keyframes, keyframe_fade)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 353 ", kf_editor.keyframes)
    # Choice the keyframe to set the value of the start of the fade out
    kf_editor.keyframes = value_keyframe_fadeout_choice(kf_editor.keyframes, keyframe_fade)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 357 kf ed fin ", kf_editor.keyframes)
    #  Remove the keyframe if the previous and the next have the same value
    kf_editor.keyframes = three_consecutive_keyframes(kf_editor.keyframes)
    edit_data["editable_property"].write_out_keyframes(kf_editor.keyframes)
    print("cf 361 kf ed clean ", kf_editor.keyframes)
    verif(tline_frame, 50)


def test_keyframe_after_pos(keyframes_list, pos):
    for i in range(len(keyframes_list) - 2, 0, -1):
        print("cf 363 kli ", i, keyframes_list[i], pos)
        if pos < keyframes_list[i][0]:
           return i
        if pos == keyframes_list[i][0]:
            pass
    print("cf 368 ", keyframes_list)
    return 0

def value_keyframe_fadeout_choice(keyframes_list, keyframe_fade):
    """ Keyframes are between the start of the fade and the end of the clip.
    """
    for i in range(0, len(keyframes_list) - 1):
        if keyframes_list[i][0] == keyframe_fade:
            index = i
            if index == len(keyframes_list) - 2:
                keyframes_list[index] = (keyframes_list[index][0], keyframes_list[index - 1][1])
            else:
                keyframes_list[index] = (keyframes_list[index][0], keyframes_list[index + 1][1])
    return keyframes_list

def remove_keyframe_after_pos(keyframes_list, pos):
    for i in range(0, len(keyframes_list)):
        print("cf 399 kli ", i, keyframes_list[i], pos)
        if keyframes_list[i][0] > pos:
            print("cf 400 kli ", i, keyframes_list[i], keyframes_list)
            del keyframes_list[i]
            remove_keyframe_after_pos(keyframes_list, pos)
    print("cf 403 ", keyframes_list)
    return keyframes_list

def remove_keyframe_after_kff(keyframes_list, pos):
    for i in range(0, len(keyframes_list) - 1):
        print("cf 408 kli ", i, keyframes_list[i], pos)
        if keyframes_list[i][0] > pos:
           del keyframes_list[i]
    print("cf 411 ", keyframes_list)
    return keyframes_list

def verif(frame, delta):
    frame_verif = frame - delta
    if frame_verif < 0:
        frame_verif = 0

    PLAYER().seek_frame(int(frame_verif))
    PLAYER().start_playback()


# ---------------#########################################################
# Alert

class Alert(GObject.Object):
    """Show a window with title and message ; emit a sound if a sound file parameter exists.

    The prepath of this file is setted for Ubuntu 19.10
    prepath = "/usr/share/sounds/freedesktop/stereo/"
    """

    def __init__(self, title, message, file_sound=""):
        GObject.Object.__init__(self)
        Gst.init(None)

        self.file_sound = file_sound
        self.alert(title, message)

    def alert(self, title, message):
        """Window."""
        primary_txt = _(title)
        secondary_txt = _(message)
        parent_window = gui.editor_window.window
        dialogutils.info_message(primary_txt, secondary_txt, parent_window)
        self.sound(self.file_sound)

    def on_clicked_ok(self, widget):
        print("clicked")
        self.win.destroy()

    def sound(self, file):
        import sys
#        if sys.platform.startswith("win32"): # Non tested
#            import winsound
#            winsound.PlaySound("xxxxxxxx.wav", winsound.SND_FILENAME)
#    #            winsound.MessageBeep()
        if sys.platform.startswith("linux"):
            prepath = "/usr/share/sounds/freedesktop/stereo/" # Ubuntu
            file_sound = os.path.join(prepath, file)
            if os.path.isfile(file_sound):
#                print("ct 637 ", file_sound)
                sound_alert = Gst.ElementFactory.make("playbin", "player")
                sound_alert.set_property('uri', 'file://' + file_sound)
                sound_alert.set_state(Gst.State.PLAYING)

# End of Alert
# ---------------#########################################################
