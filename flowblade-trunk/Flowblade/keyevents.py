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

from gi.repository import Gtk
from gi.repository import Gdk

import audiowaveform
import clipeffectseditor
import compositeeditor
import compositormodes
import glassbuttons
import gui
import editevent
import editorpersistance
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
import keyframeeditor
import medialog
import menuactions
import monitorevent
import mltrefhold
import tlineaction
import tlinewidgets
import trimmodes
import updater
import projectaction

import audiowaveformrenderer


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
        else:
            if editorstate.current_is_move_mode() == False:
                editevent.set_default_edit_mode()
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
    if gui.sequence_editor_b.has_focus():
        _handle_tline_key_event(event)
        # Stop event handling here
        return True

    # Clip button or posbar focus with clip displayed leaves playback keyshortcuts available
    if (gui.clip_editor_b.has_focus() 
        or (gui.pos_bar.widget.is_focus() and (not timeline_visible()))):
        _handle_clip_key_event(event)
        # Stop event handling here
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
    if(gui.tline_canvas.widget.is_focus()
       or gui.tline_column.widget.is_focus()
       or gui.editor_window.modes_selector.widget.is_focus()
       or (gui.pos_bar.widget.is_focus() and timeline_visible())
       or gui.tline_scale.widget.is_focus()
       or glassbuttons.focus_group_has_focus(glassbuttons.DEFAULT_FOCUS_GROUP)):
        return True
    
    return False
    
def _handle_tline_key_event(event):
    """
    This is called when timeline widgets have focus and key is pressed.
    Returns True for handled key presses to stop those
    keyevents from going forward.
    """
    # I
    if event.keyval == Gdk.KEY_i:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            monitorevent.to_mark_in_pressed()
            return True
        monitorevent.mark_in_pressed()
        return True
    if event.keyval == Gdk.KEY_I:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            monitorevent.to_mark_in_pressed()
            return True
        monitorevent.to_mark_in_pressed()
        return True

    # Minus
    if event.keyval == Gdk.KEY_minus:
        updater.zoom_out()
    
    # Plus
    if event.keyval == Gdk.KEY_equal:
        updater.zoom_in()

    # O
    if event.keyval == Gdk.KEY_o:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            monitorevent.to_mark_out_pressed()
            return True
        monitorevent.mark_out_pressed()
        return True
    if event.keyval == Gdk.KEY_O:
        if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
            monitorevent.to_mark_out_pressed()
            return True
        monitorevent.to_mark_out_pressed()
        return True

    # SPACE
    if event.keyval == Gdk.KEY_space:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        else:
            monitorevent.play_pressed()
        return True
    
    # TAB
    if event.keyval == Gdk.KEY_Tab:
        updater.switch_monitor_display()
        return True

    # M
    if event.keyval == Gdk.KEY_m:
        tlineaction.add_marker()
        return True

    # Number edit mode changes
    if event.keyval == Gdk.KEY_1:
        gui.editor_window.handle_insert_move_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_2:
        gui.editor_window.handle_over_move_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_3:
        gui.editor_window.handle_one_roll_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_4:
        gui.editor_window.handle_two_roll_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_5:
        gui.editor_window.handle_slide_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_6:
        gui.editor_window.handle_multi_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_7:
        gui.editor_window.handle_box_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
        
    # X
    if event.keyval == Gdk.KEY_x:
        tlineaction.cut_pressed()
        return True

    # G
    if event.keyval == Gdk.KEY_g:
        medialog.log_range_clicked()
        return True

    # R
    if event.keyval == Gdk.KEY_r:
        gui.editor_window.toggle_trim_ripple_mode()
        return True

    # Key bindings for keyboard trimming
    if editorstate.current_is_active_trim_mode() == True:
        # LEFT ARROW, prev frame
        if event.keyval == Gdk.KEY_Left:
            trimmodes.left_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
            return True

        # RIGHT ARROW, next frame
        if event.keyval == Gdk.KEY_Right:
            trimmodes.right_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
            return True

        if event.keyval == Gdk.KEY_Return:
            trimmodes.enter_pressed()
            return True

    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
         # UP ARROW, next cut
        if event.keyval == Gdk.KEY_Up:
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
        
        # DOWN ARROW, prev cut
        if event.keyval == Gdk.KEY_Down:
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
            
        # LEFT ARROW, prev frame
        if event.keyval == Gdk.KEY_Left:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                PLAYER().seek_delta(-10)
            else:
                PLAYER().seek_delta(-1)
            return True

        # RIGHT ARROW, next frame
        if event.keyval == Gdk.KEY_Right:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                PLAYER().seek_delta(10)
            else:
                PLAYER().seek_delta(1)
            return True
            
        # T
        if event.keyval == Gdk.KEY_t:
            tlineaction.three_point_overwrite_pressed()
            return True

        # Y
        if event.keyval == Gdk.KEY_y:
            if not (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                tlineaction.insert_button_pressed()
                return True

        # U
        if event.keyval == Gdk.KEY_u:
            tlineaction.append_button_pressed()
            return True

        # J
        if event.keyval == Gdk.KEY_j:
            monitorevent.j_pressed()
            return True

        # K
        if event.keyval == Gdk.KEY_k:
            monitorevent.k_pressed()
            return True

        # L
        if event.keyval == Gdk.KEY_l:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                medialog.log_range_clicked()
            else:
                monitorevent.l_pressed()
            return True

        # S
        if event.keyval == Gdk.KEY_s:
            tlineaction.resync_button_pressed()
            return True
            
        # DELETE
        if event.keyval == Gdk.KEY_Delete:
            # Clip selection and compositor selection are mutually exclusive, 
            # so max one one these will actually delete something
            tlineaction.splice_out_button_pressed()
            compositormodes.delete_current_selection()
        
        # HOME
        if event.keyval == Gdk.KEY_Home:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            PLAYER().seek_frame(0)
            _move_to_beginning()
            return True

        # END
        if event.keyval == Gdk.KEY_End:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            PLAYER().seek_end()
            _move_to_end()
            return True
    else:
        # HOME
        if event.keyval == Gdk.KEY_Home:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            gui.editor_window.handle_insert_move_mode_button_press()
            gui.editor_window.set_mode_selector_to_mode()
            PLAYER().seek_frame(0)
            _move_to_beginning()
            return True

        # END
        if event.keyval == Gdk.KEY_End:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            gui.editor_window.handle_insert_move_mode_button_press()
            gui.editor_window.set_mode_selector_to_mode()
            PLAYER().seek_end()
            _move_to_end()
            return True

    return False


def _handle_extended_tline_focus_events(event):
    # This was added to fix to a bug long time ago but the rationale for "extended_tline_focus_events" has been forgotten, but probably still exists
    if not(_timeline_has_focus() or
            gui.pos_bar.widget.is_focus() or
            gui.sequence_editor_b.has_focus() or
            gui.clip_editor_b.has_focus()):
        return False

    # T
    if event.keyval == Gdk.KEY_t:
        tlineaction.three_point_overwrite_pressed()
        return True

    # Y
    if event.keyval == Gdk.KEY_y:
        if not (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            tlineaction.insert_button_pressed()
            return True

    # U
    if event.keyval == Gdk.KEY_u:
        tlineaction.append_button_pressed()
        return True

    # J
    if event.keyval == Gdk.KEY_j:
        monitorevent.j_pressed()
        return True

    # K
    if event.keyval == Gdk.KEY_k:
        monitorevent.k_pressed()
        return True

    # L
    if event.keyval == Gdk.KEY_l:
        if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            medialog.log_range_clicked()
        else:
            monitorevent.l_pressed()
        return True

    # TAB
    if event.keyval == Gdk.KEY_Tab:
        updater.switch_monitor_display()
        return True

    # G
    if event.keyval == Gdk.KEY_g:
        medialog.log_range_clicked()
        return True
        
    # Number edit mode changes
    if event.keyval == Gdk.KEY_1:
        gui.editor_window.handle_insert_move_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_2:
        gui.editor_window.handle_over_move_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_3:
        gui.editor_window.handle_one_roll_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_4:
        gui.editor_window.handle_two_roll_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_5:
        gui.editor_window.handle_slide_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_6:
        gui.editor_window.handle_multi_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True
    if event.keyval == Gdk.KEY_7:
        gui.editor_window.handle_box_mode_button_press()
        gui.editor_window.set_mode_selector_to_mode()
        return True

    return False
        
def _handle_clip_key_event(event):
    # Key bindings for MOVE MODES
    if editorstate.current_is_move_mode():                  
        # LEFT ARROW, prev frame
        if event.keyval == Gdk.KEY_Left:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                PLAYER().seek_delta(-10)
            else:
                PLAYER().seek_delta(-1)
            return True

        # RIGHT ARROW, next frame
        if event.keyval == Gdk.KEY_Right:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                PLAYER().seek_delta(10)
            else:
                PLAYER().seek_delta(1)
            return True

         # UP ARROW
        if event.keyval == Gdk.KEY_Up:
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
        
         # DOWN ARROW, prev cut
        if event.keyval == Gdk.KEY_Down:
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

        # SPACE
        if event.keyval == Gdk.KEY_space:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            else:
                monitorevent.play_pressed()

        # I
        if event.keyval == Gdk.KEY_i:
            if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
                monitorevent.to_mark_in_pressed()
                return True
            monitorevent.mark_in_pressed()
            return True
        if event.keyval == Gdk.KEY_I:
            if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
                monitorevent.to_mark_in_pressed()
                return True
            monitorevent.to_mark_in_pressed()
            return True

        # O
        if event.keyval == Gdk.KEY_o:
            if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
                monitorevent.to_mark_out_pressed()
                return True
            monitorevent.mark_out_pressed()
            return True
        if event.keyval == Gdk.KEY_O:
            if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
                monitorevent.to_mark_out_pressed()
                return True
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
                    if ((event.keyval == Gdk.KEY_Left) 
                        or (event.keyval == Gdk.KEY_Right)
                        or (event.keyval == Gdk.KEY_Up)
                        or (event.keyval == Gdk.KEY_Down)):
                        kfeditor.arrow_edit(event.keyval, (event.get_state() & Gdk.ModifierType.CONTROL_MASK))
                        return True
                    if event.keyval == Gdk.KEY_plus:
                        pass # not impl
                    if event.keyval == Gdk.KEY_space:
                        if PLAYER().is_playing():
                            monitorevent.stop_pressed()
                        else:
                            monitorevent.play_pressed()
                        return True
    return False

def _handle_effects_editor_keys(event):
    focus_editor = _get_focus_keyframe_editor(clipeffectseditor.keyframe_editor_widgets)
    if focus_editor != None:
      if event.keyval == Gdk.KEY_space:
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

