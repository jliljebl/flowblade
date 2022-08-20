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
import appconsts
import dialogutils
import gui
from editorstate import current_sequence
import propertyedit
import propertyparse

"""
This module handles adding fade-ins and fade-outs to compositors and filters.

Creating and managing keyframes is mostly handled by editor GUI components which cannot easily 
be used for adding fade-ins and fade outs, so this dedicated module is needed.

NOTE: This can all (maybe) be killed now and done more simply in keyframeeditor.py, original reasons for this existing
may not apply anymore.
"""

# Dissolve default fades group ("Dissolve", "Blend") keyframe property class names
_dissolve_property_klasses = ["OpacityInGeomKeyframeProperty", "KeyFrameHCSTransitionProperty"]

# -------------------------------------------------------------- module interface
def add_fade_in(compositor, fade_in_length):
    clip = _get_compositor_clip(compositor)
    keyframe_property, property_klass, keyframes = _get_kfproperty_klass_and_keyframes(compositor, clip)
    
    if fade_in_length > 0:
        if fade_in_length <= clip.clip_length():
            return _do_user_add_fade_in(keyframe_property, property_klass, keyframes, fade_in_length)
        else:
            _show_length_error_dialog()
            return None

def add_fade_out(compositor, fade_out_length):
    clip = _get_compositor_clip(compositor)
    keyframe_property, property_klass, keyframes = _get_kfproperty_klass_and_keyframes(compositor, clip)
    
    if fade_out_length > 0:
        if fade_out_length + 1 <= clip.clip_length():
            return _do_user_add_fade_out(keyframe_property, property_klass, keyframes, fade_out_length, clip)
        else:
            _show_length_error_dialog()
            return None

def add_filter_fade_in(clip, keyframe_property, keyframes, fade_in_length):   
    if fade_in_length > 0:
        if clip.clip_in + fade_in_length <= clip.clip_out:
            return _do_user_add_fade_in_filter(keyframe_property, keyframes, fade_in_length, clip.clip_in)
        else:
            _show_length_error_dialog()
            return None

def add_filter_fade_out(clip, keyframe_property, keyframes, fade_out_length):   
    if fade_out_length > 0:
        if clip.clip_in + fade_out_length <=  clip.clip_out:
            return _do_user_add_fade_out_filter(keyframe_property, keyframes, fade_out_length, clip)
        else:
            _show_length_error_dialog()
            return None

def set_auto_fade_in_keyframes(compositor):
    clip = _get_compositor_clip(compositor)
    keyframe_property, property_klass, keyframes = _get_kfproperty_klass_and_keyframes(compositor, clip)
    
    # Remove all key frames, there exists 2 or 1, 0 when created 1 always after that
    while len(keyframes) > 0: 
        keyframes.pop()
    
    # Set in fade in keyframes
    keyframes.append((0, 0))
    keyframes.append((compositor.get_length() - 1, 100))

    keyframe_property.write_out_keyframes(keyframes)

def set_auto_fade_out_keyframes(compositor):
    clip = _get_compositor_clip(compositor)
    keyframe_property, property_klass, keyframes = _get_kfproperty_klass_and_keyframes(compositor, clip)
    
    # Remove all key frames, there exists 2 or 1, 0 when created 1 always after that
    while len(keyframes) > 0: 
        keyframes.pop()
    
    # Set in fade in keyframes
    keyframes.append((0, 100))
    keyframes.append((compositor.get_length() - 1, 0))

    print("before write out keyframes")
    keyframe_property.write_out_keyframes(keyframes)
    print("after write out keyframes")
        
# ---------------------------------------------------------------------- module functions
def _get_kfproperty_klass_and_keyframes(compositor, clip):
    # We create a SECOND SET of EditableProperties from compositor properties.
    # These are not the same EditableProperties that are edited in GUI in "Compositor" panel.
    # This approach seems necessary because Affine Blend requires creating a new property.
    t_editable_properties = propertyedit.get_transition_editable_properties(compositor)

    # Find keyframe property, its class and create keyframes list
    if compositor.transition.info.mlt_service_id == "frei0r.cairoaffineblend": # Affine Blend
        # Because of frei0r's forced value 0.0-1.0 range "Affine Blend" is handled in a more complex way compared to other compositors
        keyframe_property = propertyparse.create_editable_property_for_affine_blend(clip, t_editable_properties)
        keyframes = propertyparse.rotating_geom_keyframes_value_string_to_geom_kf_array(keyframe_property.value, keyframe_property.get_in_value)
        property_klass = keyframe_property.__class__.__name__
        return (keyframe_property, property_klass, keyframes)
        
    else: # Dissolve, Blend, Picture-in-Picture, Region
        keyframe_property = None
        property_klass = None
        for ep in t_editable_properties:
            property_klass = ep.__class__.__name__
            if property_klass == "OpacityInGeomKeyframeProperty": # Dissolve
                keyframe_property = ep
                print("HERE  OpacityInGeomKeyframeProperty")
                keyframes = propertyparse.geom_keyframes_value_string_to_opacity_kf_array(keyframe_property.value, keyframe_property.get_in_value)
                break
            if property_klass == "KeyFrameHCSTransitionProperty" and compositor.transition.info.mlt_service_id != "affine": # Blend, and we exclude Transform
                keyframe_property = ep
                keyframes = propertyparse.single_value_keyframes_string_to_kf_array(keyframe_property.value, keyframe_property.get_in_value)
                break
            if property_klass == "KeyFrameGeometryOpacityProperty": # Picture-in-Picture, Region
                keyframe_property = ep
                keyframes = propertyparse.geom_keyframes_value_string_to_geom_kf_array(keyframe_property.value, keyframe_property.get_in_value)
                break

        if keyframe_property == None:
            return (None, None, None)

        return (keyframe_property, property_klass, keyframes)

def _get_compositor_clip(compositor):
    for i in range(current_sequence().first_video_index, len(current_sequence().tracks) - 1): # -1, there is a topmost hidden track 
        track = current_sequence().tracks[i] # b_track is source track where origin clip is
        for j in range(0, len(track.clips)):
            clip = track.clips[j]
            if clip.id == compositor.origin_clip_id:
                return clip
    
    return None

def _add_default_fade_in(keyframe_property, property_klass, keyframes, fade_in_length):
    if property_klass in _dissolve_property_klasses:
        frame, opacity, kf_type = keyframes.pop(0)
        keyframes.append((frame, 0, appconsts.KEYFRAME_LINEAR))
        keyframes.append((frame + fade_in_length, 100, appconsts.KEYFRAME_LINEAR))
        return keyframes
    else:
        # (0, [0, 0, 1280, 720], 100.0) or (0, [640.0, 360.0, 1.0, 1.0, 0.0], 100.0) e.g.
        frame, geom, opacity, kf_type = keyframes.pop(0)
        keyframes.append((frame, geom, 0, appconsts.KEYFRAME_LINEAR))
        keyframes.append((frame + fade_in_length, geom, 100, appconsts.KEYFRAME_LINEAR))
        return keyframes

def _add_default_fade_out(keyframe_property, property_klass, keyframes, fade_out_length, clip, kf_before_fade_out_index=0):
    if property_klass in _dissolve_property_klasses:
        keyframes.append((clip.clip_length() - fade_out_length - 1, 100, appconsts.KEYFRAME_LINEAR))
        keyframes.append((clip.clip_length() - 1, 0, appconsts.KEYFRAME_LINEAR))
        return keyframes
    else:
        # (0, [0, 0, 1280, 720], 100.0) or (0, [640.0, 360.0, 1.0, 1.0, 0.0], 100.0) e.g.
        frame, geom, opacity, kf_type = keyframes[kf_before_fade_out_index]
        keyframes.append((clip.clip_length() - fade_out_length - 1, geom, 100, appconsts.KEYFRAME_LINEAR))
        keyframes.append((clip.clip_length() - 1, geom, 0, appconsts.KEYFRAME_LINEAR))
        return keyframes

def _do_user_add_fade_in(keyframe_property, property_klass, keyframes, fade_in_length):
    
    # Get index of first keyframe after fade_in_length
    kf_after_fade_in_index = -1
    for i in range (0, len(keyframes)):
        kf = keyframes[i]
        if property_klass in _dissolve_property_klasses:
            frame, opacity, kf_type = kf
        else:
            frame, geom, opacity, kf_type = kf
        
        if frame > fade_in_length:
            kf_after_fade_in_index = i
            break

    # Case no keyframes after fade in length
    if kf_after_fade_in_index == -1:
        # Remove all but first keyframe
        for i in range(0, len(keyframes) - 1):
            keyframes.pop(1)
        # nOw this the same action as addin default keyframe on creation
        keyframes = _add_default_fade_in(keyframe_property, property_klass, keyframes, fade_in_length)
    # Case keyframes exists after fade in length
    else:
        # Remove keyframes in range 0 - kf_after_fade_in_index
        for i in range(0, kf_after_fade_in_index - 1):
            keyframes.pop(1)
        if property_klass in _dissolve_property_klasses:
            frame, opacity, kf_type = keyframes.pop(0)
            keyframes.insert(0, (frame, 0, appconsts.KEYFRAME_LINEAR))
            keyframes.insert(1,(frame + fade_in_length, 100, appconsts.KEYFRAME_LINEAR))
        else:
            # (0, [0, 0, 1280, 720], 100.0) or (0, [640.0, 360.0, 1.0, 1.0, 0.0], 100.0) e.g.
            frame, geom, opacity, kf_type = keyframes.pop(0)
            keyframes.insert(0, (frame, geom, 0, appconsts.KEYFRAME_LINEAR))
            keyframes.insert(1, (frame + fade_in_length, geom, 100, appconsts.KEYFRAME_LINEAR))

    # Because we created a SECOND SET of EditableProperties this only updates data structures (py and MLT)
    # but not EditableProperties wrappers that are edited in GUI in "Compositor" panel.
    keyframe_property.write_out_keyframes(keyframes)
    
    # We need to return updated keyframes to update GUI in "Compositor" panel.
    return keyframes

def _do_user_add_fade_out(keyframe_property, property_klass, keyframes, fade_out_length, clip):
    # Get index of first keyframe before fade out begins
    fade_out_frame = clip.clip_length() - fade_out_length
    kf_after_fade_out_index = -1
    for i in range (0, len(keyframes)):
        kf = keyframes[i]
        if property_klass in _dissolve_property_klasses:
            frame, opacity, kf_type = kf
        else:
            frame, geom, opacity, kf_type = kf
        
        if frame >= fade_out_frame:
            kf_after_fade_out_index = i
            break

    # Case no keyframes after fade out start
    if kf_after_fade_out_index == -1:
        keyframes = _add_default_fade_out(keyframe_property, property_klass, keyframes, fade_out_length, clip, 0)

    # Case keyframes exists after  fade out start
    else:
        # Remove keyframes in range 0 - kf_after_fade_in_index
        for i in range(kf_after_fade_out_index, len(keyframes)):
            keyframes.pop(-1) # pop last
            
        keyframes = _add_default_fade_out(keyframe_property, property_klass, keyframes, fade_out_length, clip, len(keyframes) - 1)

    # Because we created a SECOND SET of EditableProperties this only updates data structures (py and MLT)
    # but not EditableProperties wrappers that are edited in GUI in "Compositor" panel.
    keyframe_property.write_out_keyframes(keyframes)

    # We need to return updated keyframes to update GUI in "Compositor" panel.
    return keyframes

def _do_user_add_fade_in_filter(keyframe_property, keyframes, fade_in_length, clip_in):
    # Get index of first keyframe after fade_in_length
    kf_after_fade_in_index = -1
    for i in range (0, len(keyframes)):
        kf = keyframes[i]
        frame, opacity, kf_type = kf
        
        if frame > clip_in + fade_in_length:
            kf_after_fade_in_index = i
            break

    # Case no keyframes after fade in length
    if kf_after_fade_in_index == -1:
        # Remove all but first keyframe
        for i in range(0, len(keyframes) - 1):
            keyframes.pop(1)

        frame, opacity  = keyframes.pop(0)

        keyframes.append((clip_in, 0, appconsts.KEYFRAME_LINEAR))
        keyframes.append((clip_in + fade_in_length, 100, appconsts.KEYFRAME_LINEAR))
    # Case keyframes exists after fade in length
    else:
        # Remove keyframes in range 0 - kf_after_fade_in_index
        for i in range(0, kf_after_fade_in_index - 1):
            keyframes.pop(1)

        frame, opacity  = keyframes.pop(0)
        keyframes.insert(0, (clip_in, 0))
        keyframes.insert(1, (clip_in + fade_in_length, 100))

    # Because we created a SECOND SET of EditableProperties this only updates data structures (py and MLT)
    # but not EditableProperties wrappers that are edited in GUI in "Compositor" panel.
    keyframe_property.write_out_keyframes(keyframes)
    
    # We need to return updated keyframes to update GUI in "Compositor" panel.
    return keyframes

def _do_user_add_fade_out_filter(keyframe_property, keyframes, fade_out_length, clip):

    # Get index of first keyframe before fade out begins
    fade_out_frame = clip.clip_out - fade_out_length
    kf_after_fade_out_index = -1
    for i in range (0, len(keyframes)):
        kf = keyframes[i]
        frame, opacity, kf_type  = kf

        if frame >= fade_out_frame:
            kf_after_fade_out_index = i
            break

    # Case no keyframes after fade out start
    if kf_after_fade_out_index == -1:
        keyframes.append((clip.clip_out - fade_out_length - 1, 100, appconsts.KEYFRAME_LINEAR))
        keyframes.append((clip.clip_out - 1, 0, appconsts.KEYFRAME_LINEAR))

    # Case keyframes exists after  fade out start
    else:
        # Remove keyframes in range 0 - kf_after_fade_in_index
        for i in range(kf_after_fade_out_index, len(keyframes)):
            keyframes.pop(-1) # pop last
            
        keyframes.append((clip.clip_out - fade_out_length - 1, 100, appconsts.KEYFRAME_LINEAR))
        keyframes.append((clip.clip_out - 1, 0, appconsts.KEYFRAME_LINEAR))

    # Because we created a SECOND SET of EditableProperties this only updates data structures (py and MLT)
    # but not EditableProperties wrappers that are edited in GUI in "Compositor" panel.
    keyframe_property.write_out_keyframes(keyframes)

    # We need to return updated keyframes to update GUI in "Compositor" panel.
    return keyframes
    
def _show_length_error_dialog():
    parent_window = gui.editor_window.window
    primary_txt = _("Clip too short!")
    secondary_txt = _("The Clip is too short to add the requested fade.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)
    
def _show_defaults_length_error_dialog():
    parent_window = gui.editor_window.window
    primary_txt = _("Clip too short for Auto Fades!")
    secondary_txt = _("The Clip is too short to add the user set default fades on Compositor creation.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)
            
            
            
            
