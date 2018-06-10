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
Module handles keyevents.
"""

from gi.repository import Gdk

import audiowaveform
import clipeffectseditor
import compositeeditor
import compositormodes
import glassbuttons
import gui
import editorpersistance
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
import keyframeeditor
import medialog
import menuactions
import modesetting
import monitorevent
# Apr-2017 - SvdB
import shortcuts
import re
import tlineaction
import tlinewidgets
import trimmodes
import updater
import projectaction
import workflow



# ------------------------------------- keyboard events
def key_down(widget, event):
    """
    Global key press listener.
    """
    # Handle ESCAPE
    if event.keyval == Gdk.KEY_Escape:
        if audiowaveform.waveform_thread != None:
            audiowaveform.waveform_thread.abort_rendering()
            return True
        elif editorstate.current_is_move_mode() == False:
            modesetting.set_default_edit_mode()
            return True
        elif gui.big_tc.get_visible_child_name() == "BigTCEntry":
            gui.big_tc.set_visible_child_name("BigTCDisplay")
            return True

    # Compositor editors keyevents
    was_handled = _handle_geometry_editor_keys(event)
    if was_handled:
        # Stop widget focus from travelling if arrow key pressed
        gui.editor_window.window.emit_stop_by_name("key_press_event")
        return True

    was_handled = _handle_effects_editor_keys(event)
    if was_handled:
        # Stop widget focus from travelling if arrow key pressed
        gui.editor_window.window.emit_stop_by_name("key_press_event")
        return True
    
    # If timeline widgets are in focus timeline keyevents are available
    if _timeline_has_focus():
        was_handled = _handle_tline_key_event(event)
        if was_handled:
            # Stop widget focus from travelling if arrow key pressed for next frame
            # by stopping signal
            gui.editor_window.window.emit_stop_by_name("key_press_event")
        return was_handled

    # Insert shortcut keys need more focus then timeline shortcuts.
    # these may already have been handled in timeline focus events
    was_handled = _handle_extended_tline_focus_events(event)
    if was_handled:
        # Stop event handling here
        return True

    # Pressing timeline button obivously leaves user expecting
    # to have focus in timeline
    """
    TODO: this needs something
    if gui.sequence_editor_b.has_focus():
        _handle_tline_key_event(event)
        # Stop event handling here
        return True
    """
    
    # Clip button or posbar focus with clip displayed leaves playback keyshortcuts available
    """
    if (gui.clip_editor_b.has_focus()
        TODO: this needs something
        or (gui.pos_bar.widget.is_focus() and (not timeline_visible()))):
        _handle_clip_key_event(event)
        # Stop event handling here
        return True
    """
    if gui.monitor_switch.widget.has_focus() and timeline_visible():
        _handle_tline_key_event(event)
        return True

    if gui.monitor_switch.widget.has_focus() and (not timeline_visible()):
        _handle_clip_key_event(event)
        return True
        
    if gui.pos_bar.widget.is_focus() and (not timeline_visible()):
        _handle_clip_key_event(event)
        return True
        
    #  Handle non-timeline delete 
    if event.keyval == Gdk.KEY_Delete:
        return _handle_delete()

    # Home
    if event.keyval == Gdk.KEY_Home:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        PLAYER().seek_frame(0)
        _move_to_beginning()
        return True

    # End
    if event.keyval == Gdk.KEY_End:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        PLAYER().seek_end()
        _move_to_end()
        return True

    # Select all with CTRL + A in media panel
    if event.keyval == Gdk.KEY_a:
        if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            if gui.media_list_view.widget.has_focus() or gui.media_list_view.widget.get_focus_child() != None:
                gui.media_list_view.select_all()
                return True
        
    if event.keyval == Gdk.KEY_F11:
        menuactions.toggle_fullscreen()
        return True

    #debug
    if event.keyval == Gdk.KEY_F12:
        if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            pass
        return True

    # Key event was not handled here.
    return False
    
def _timeline_has_focus():
    if(gui.tline_canvas.widget.has_focus()
       or gui.tline_column.widget.has_focus()
       or gui.editor_window.tool_selector.widget.has_focus()
       or (gui.pos_bar.widget.has_focus() and timeline_visible())
       or gui.tline_scale.widget.has_focus()
       or glassbuttons.focus_group_has_focus(glassbuttons.DEFAULT_FOCUS_GROUP)):
        return True
        
    return False
    
def _handle_tline_key_event(event):
    """
    This is called when timeline widgets have focus and key is pressed.
    Returns True for handled key presses to stop those
    keyevents from going forward.
    """

    tool_was_selected = workflow.tline_tool_keyboard_selected(event)
    if tool_was_selected == True:
        return True
    
    action = _get_shortcut_action(event)
    prefs = editorpersistance.prefs

    if action == 'mark_in':
        monitorevent.mark_in_pressed()
        return True
    if action == 'to_mark_in':
        monitorevent.to_mark_in_pressed()
        return True
    if action == 'zoom_out':
        updater.zoom_out()
    if action == 'zoom_in':
        updater.zoom_in()
    if action == 'mark_out':
        monitorevent.mark_out_pressed()
        return True
    if action == 'to_mark_out':
        monitorevent.to_mark_out_pressed()
        return True
    if action == 'play_pause':
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        else:
            monitorevent.play_pressed()
        return True
    if action == 'switch_monitor':
        updater.switch_monitor_display()
        return True
    if action == 'add_marker':
        tlineaction.add_marker()
        return True    
    if action == 'cut':
        tlineaction.cut_pressed()
        return True
    if action == 'sequence_split':
        tlineaction.sequence_split_pressed()
        return True
    if action == 'log_range':
        medialog.log_range_clicked()
        return True
    """
    THis may need rethinking
    if action == 'toggle_ripple':
        gui.editor_window.toggle_trim_ripple_mode()
        return True
    """
    
    # Key bindings for keyboard trimming
    if editorstate.current_is_active_trim_mode() == True:
        if action == 'prev_frame':
            trimmodes.left_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
            return True
        elif action == 'next_frame':
            trimmodes.right_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
            return True
        elif action == 'enter_edit':
            trimmodes.enter_pressed()
            return True

    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if action == 'next_cut':
            if editorstate.timeline_visible():
                tline_frame = PLAYER().tracktor_producer.frame()
                frame = current_sequence().find_next_cut_frame(tline_frame)
                if frame != -1:
                    PLAYER().seek_frame(frame)
                    if editorpersistance.prefs.center_on_arrow_move == True:
                        updater.center_tline_to_current_frame()
                    return True
            else:
                monitorevent.up_arrow_seek_on_monitor_clip()
        if action == 'prev_cut':
            if editorstate.timeline_visible():
                tline_frame = PLAYER().tracktor_producer.frame()
                frame = current_sequence().find_prev_cut_frame(tline_frame)
                if frame != -1:
                    PLAYER().seek_frame(frame)
                    if editorpersistance.prefs.center_on_arrow_move == True:
                        updater.center_tline_to_current_frame()
                    return True
            else:
                 monitorevent.down_arrow_seek_on_monitor_clip()
                 return True
        # Apr-2017 - SvdB - Add different speeds for different modifiers
        # Allow user to select what speed belongs to what modifier, knowing that a combo of mods
        # will MULTIPLY all speeds
        # Available: SHIFT_MASK LOCK_MASK CONTROL_MASK
        if action == 'prev_frame' or action == 'next_frame':
            if action == 'prev_frame':
                seek_amount = -1
            else:
                seek_amount = 1
                
            if (event.get_state() & Gdk.ModifierType.SHIFT_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_shift
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_ctrl
            if (event.get_state() & Gdk.ModifierType.LOCK_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_caps
            PLAYER().seek_delta(seek_amount)
            return True
        if action == '3_point_overwrite':
            tlineaction.three_point_overwrite_pressed()
            return True
        if action == 'insert':
            if not (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                tlineaction.insert_button_pressed()
                return True
        if action == 'append':
            tlineaction.append_button_pressed()
            return True
        if action == 'slower':
            monitorevent.j_pressed()
            return True
        if action == 'stop':
            monitorevent.k_pressed()
            return True
        if action == 'faster':
            monitorevent.l_pressed()
            return True
        if action == 'log_range':
            medialog.log_range_clicked()
            return True
        if action == 'resync':
            tlineaction.resync_button_pressed()
            return True
        if action == 'delete':
            # Clip selection and compositor selection are mutually exclusive, 
            # so max one one these will actually delete something
            tlineaction.splice_out_button_pressed()
            compositormodes.delete_current_selection()
        if action == 'to_start':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            PLAYER().seek_frame(0)
            _move_to_beginning()
            return True
        if action == 'to_end':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            PLAYER().seek_end()
            _move_to_end()
            return True
    else:
        if action == 'to_start':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            gui.editor_window.set_default_edit_tool()
            PLAYER().seek_frame(0)
            _move_to_beginning()
            return True
        if action == 'to_end':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            gui.editor_window.set_default_edit_tool()
            PLAYER().seek_end()
            _move_to_end()
            return True

    return False

def _handle_extended_tline_focus_events(event):
    # This function was added to fix to a bug long time ago but the rationale for "extended_tline_focus_events" has been forgotten, but probably still exists
    # Apr-2017 - SvdB - For keyboard shortcuts
    action = _get_shortcut_action(event)

    # We're dropping monitor window in 2 window mode as part of timeline focus
    #    TODO:        gui.sequence_editor_b.has_focus() or
    #        gui.clip_editor_b.has_focus()):
    if not(_timeline_has_focus() or gui.monitor_switch.widget.has_focus() or
            gui.pos_bar.widget.has_focus()):
        return False

    if action == '3_point_overwrite':
        tlineaction.three_point_overwrite_pressed()
        return True
    if action == 'insert':
        tlineaction.insert_button_pressed()
        return True
    if action == 'append':
        tlineaction.append_button_pressed()
        return True
    if action == 'slower':
        monitorevent.j_pressed()
        return True
    if action == 'stop':
        monitorevent.k_pressed()
        return True
    if action == 'faster':
        monitorevent.l_pressed()
        return True
    if action == 'log_range':
        medialog.log_range_clicked()
        return True
    if action == 'switch_monitor':
        updater.switch_monitor_display()
        return True
    
    tool_was_selected = workflow.tline_tool_keyboard_selected(event)
    if tool_was_selected == True:
        return True

    return False
        
# Apr-2017 - SvdB
def _get_shortcut_action(event):
    # Get the name of the key pressed
    key_name = Gdk.keyval_name(event.keyval).lower()
    # Check if this key is in the dictionary.
    state = event.get_state()
    # Now we have a key and a key state we need to check if it is a shortcut.
    # If it IS a shortcut we need to determine what action to take
    if key_name in shortcuts._keyboard_actions:
        # Now get the associated dictionary
        _secondary_dict = shortcuts._keyboard_actions[key_name]
        # In order to check for all available combinations of Ctrl+Alt etc (CTRL+ALT should be the same as ALT_CTRL)
        # we do a SORT on the string. So both CTRL+ALT and ALT+CTRL will become +ACLLRTT and can be easily compared
        modifier = ""
        if state & Gdk.ModifierType.CONTROL_MASK:
            modifier = "CTRL"
        if state & Gdk.ModifierType.MOD1_MASK:
            if modifier != "":
                modifier = modifier + "+"
            modifier = modifier + "ALT"
        if state & Gdk.ModifierType.SHIFT_MASK:
            if modifier != "":
                modifier = modifier + "+"
            modifier = modifier + "SHIFT"
        # CapsLock is used as an equivalent to SHIFT, here
        if state & Gdk.ModifierType.LOCK_MASK:
            if modifier != "":
                modifier = modifier + "+"
            modifier = modifier + "SHIFT"
        # Set to None if no modifier found
        if modifier == "":
            modifier = 'None'
        try:
            action = _secondary_dict[''.join(sorted(re.sub('[\s]','',modifier.lower())))]
        except:
            try:
                action = _secondary_dict[''.join(sorted(re.sub('[\s]','','Any'.lower())))]
            except:
                action = 'None'
        return action
    # We didn't find an action, so return nothing 
    return 'None'

def _handle_clip_key_event(event):
    # Key bindings for MOVE MODES
    if editorstate.current_is_move_mode():
        action = _get_shortcut_action(event)
        # Apr-2017 - SvdB - Add different speeds for different modifiers
        # Allow user to select what speed belongs to what modifier, knowing that a combo of mods
        # will MULTIPLY all speeds
        # Available: SHIFT_MASK LOCK_MASK CONTROL_MASK
        
        prefs = editorpersistance.prefs
        if action == 'prev_frame' or action == 'next_frame':
            if action == 'prev_frame':
                seek_amount = -1
            else:
                seek_amount = 1
            if (event.get_state() & Gdk.ModifierType.SHIFT_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_shift
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_ctrl
            if (event.get_state() & Gdk.ModifierType.LOCK_MASK):
                seek_amount = seek_amount * prefs.ffwd_rev_caps
            PLAYER().seek_delta(seek_amount)
            return True

        if action == 'next_cut':
            if editorstate.timeline_visible():
                tline_frame = PLAYER().tracktor_producer.frame()
                frame = current_sequence().find_next_cut_frame(tline_frame)
                if frame != -1:
                    PLAYER().seek_frame(frame)
                    if editorpersistance.prefs.center_on_arrow_move == True:
                        updater.center_tline_to_current_frame()
                    return True
            else:
                 monitorevent.up_arrow_seek_on_monitor_clip()
                 return True
        if action == 'prev_cut':
            if editorstate.timeline_visible():
                tline_frame = PLAYER().tracktor_producer.frame()
                frame = current_sequence().find_prev_cut_frame(tline_frame)
                if frame != -1:
                    PLAYER().seek_frame(frame)
                    if editorpersistance.prefs.center_on_arrow_move == True:
                        updater.center_tline_to_current_frame()  
                    return True
            else:
                 monitorevent.down_arrow_seek_on_monitor_clip()
                 return True
        if action == 'play_pause':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            else:
                monitorevent.play_pressed()
        if action == 'mark_in':
            monitorevent.mark_in_pressed()
            return True
        if action == 'to_mark_in':
            monitorevent.to_mark_in_pressed()
            return True
        if action == 'mark_out':
            monitorevent.mark_out_pressed()
            return True
        if action == 'to_mark_out':
            monitorevent.to_mark_out_pressed()
            return True

def _handle_delete():
    # Delete media file
    if gui.media_list_view.widget.get_focus_child() != None:
        projectaction.delete_media_files()
        return True

    # Delete bin
    if gui.bin_list_view.get_focus_child() != None:
        if gui.bin_list_view.text_rend_1.get_property("editing") == True:
            return False
        projectaction.delete_selected_bin()
        return True

    # Delete sequence
    if gui.sequence_list_view.get_focus_child() != None:
        if gui.sequence_list_view.text_rend_1.get_property("editing") == True:
            return False
        projectaction.delete_selected_sequence()
        return True

    # Delete effect
    if gui.effect_stack_list_view.get_focus_child() != None:
        clipeffectseditor.delete_effect_pressed()
        return True

    # Delete media log event
    if gui.editor_window.media_log_events_list_view.get_focus_child() != None:
        medialog.delete_selected()
        return True

    focus_editor = _get_focus_keyframe_editor(compositeeditor.keyframe_editor_widgets)
    if focus_editor != None:
        focus_editor.delete_pressed()
        return True

    focus_editor = _get_focus_keyframe_editor(clipeffectseditor.keyframe_editor_widgets)
    if focus_editor != None:
        focus_editor.delete_pressed()
        return True

    return False

def _handle_geometry_editor_keys(event):
    if compositeeditor.keyframe_editor_widgets != None:
        for kfeditor in compositeeditor.keyframe_editor_widgets:
            if kfeditor.get_focus_child() != None:
                if kfeditor.__class__ == keyframeeditor.GeometryEditor or \
                kfeditor.__class__ == keyframeeditor.RotatingGeometryEditor:
                    # Apr-2017 - SvdB - For keyboard shortcuts. I have NOT changed the arrow keys for
                    # the kfeditor action. That didn't seem appropriate
                    action = _get_shortcut_action(event)
                    if ((event.keyval == Gdk.KEY_Left) 
                        or (event.keyval == Gdk.KEY_Right)
                        or (event.keyval == Gdk.KEY_Up)
                        or (event.keyval == Gdk.KEY_Down)):
                        kfeditor.arrow_edit(event.keyval, (event.get_state() & Gdk.ModifierType.CONTROL_MASK))
                        return True
                    if event.keyval == Gdk.KEY_plus:
                        pass # not impl
                    if action == 'play_pause':
                        if PLAYER().is_playing():
                            monitorevent.stop_pressed()
                        else:
                            monitorevent.play_pressed()
                        return True
    return False

def _handle_effects_editor_keys(event):
    action = _get_shortcut_action(event)
    focus_editor = _get_focus_keyframe_editor(clipeffectseditor.keyframe_editor_widgets)
    if focus_editor != None:
      if action == 'play_pause':
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            else:
                monitorevent.play_pressed()
            return True

    return False

def _get_focus_keyframe_editor(keyframe_editor_widgets):
    if keyframe_editor_widgets == None:
        return None
    for kfeditor in keyframe_editor_widgets:
        if kfeditor.get_focus_child() != None:
           return kfeditor
    return None

def _move_to_beginning():
    tlinewidgets.pos = 0
    updater.repaint_tline()
    updater.update_tline_scrollbar()
    
def _move_to_end():
    updater.repaint_tline()
    updater.update_tline_scrollbar()

