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
import gtk
import threading

import audiowaveform
import buttonevent
import clipeffectseditor
import compositeeditor
import compositormodes
import gui
import editevent
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
import monitorevent
import resync #debug
import updater
import useraction

# ------------------------------------- keyboard events
def key_down(widget, event):
    """
    Global key press listener.
    """
    # Handle ESCAPE
    if event.keyval == gtk.keysyms.Escape:
        if audiowaveform.waveform_thread != None:
            audiowaveform.waveform_thread.abort_rendering()
            return True
        else:
            if editorstate.current_is_move_mode() == False:
                editevent.set_default_edit_mode()

    # If timeline widgets are in focus timeline keyevents are available
    if _timeline_has_focus():
        was_handled = _handle_tline_key_event(event)
        if was_handled:
            # Stop widget focus from travelling if arrow key pressed for next frame
            # by stopping signal
            gui.editor_window.window.emit_stop_by_name("key_press_event")
        return was_handled

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
    if event.keyval == gtk.keysyms.Delete:
        return _handle_delete()

    #debug
    if event.keyval == gtk.keysyms.F12:
        current_sequence().print_all()
        return True

    #debug
    if event.keyval == gtk.keysyms.F11:
        print "haloo"
        resync.calculate_and_set_child_clip_sync_states()
        updater.repaint_tline()
        return True

    # Key event was not handled here.
    return False
    
def _timeline_has_focus():
    if(gui.tline_canvas.widget.is_focus()
       or gui.tline_column.widget.is_focus()
       or (gui.pos_bar.widget.is_focus() and timeline_visible())
       or gui.tline_scale.widget.is_focus()):
        return True

    return False
    
def _handle_tline_key_event(event):
    """
    This is called when timeline widgets have focus and key is pressed.
    Returns True for handled key presses to stop those
    keyevents from going forward.
    """
    # PLUS
    if event.keyval == gtk.keysyms.plus:
        updater.zoom_in()
        return True

    # MINUS
    if event.keyval == gtk.keysyms.minus:
        updater.zoom_out()
        return True
    
    # I
    if event.keyval == gtk.keysyms.i:
        updater.set_mode_button_active(editorstate.INSERT_MOVE)
        return True

    # T
    if event.keyval == gtk.keysyms.t:
        updater.set_mode_button_active(editorstate.ONE_ROLL_TRIM)
        return True

    # SPACE
    if event.keyval == gtk.keysyms.space:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        else:
            monitorevent.play_pressed()
        return True
            
    # Key bindings for MOVE MODES
    if editorstate.current_is_move_mode():

        # UP ARROW, next cut
        if event.keyval == gtk.keysyms.Up:
            tline_frame = PLAYER().tracktor_producer.frame()
            frame = current_sequence().find_next_cut_frame(tline_frame)
            if frame != -1:
                PLAYER().seek_frame(frame)
                return True
        
        # DOWN ARROW, prev cut
        if event.keyval == gtk.keysyms.Down:
            tline_frame = PLAYER().tracktor_producer.frame()
            frame = current_sequence().find_prev_cut_frame(tline_frame)
            if frame != -1:
                PLAYER().seek_frame(frame)
                return True
            
        # LEFT ARROW, prev frame
        if event.keyval == gtk.keysyms.Left:
            PLAYER().seek_delta(-1)
            return True

        # RIGHT ARROW, next frame
        if event.keyval == gtk.keysyms.Right:
            PLAYER().seek_delta(1)
            return True
        
        # DELETE
        if event.keyval == gtk.keysyms.Delete:
            # Clip selection and compositor selection are mutually exclusive, 
            # so max one one these will actually delete something
            buttonevent.splice_out_button_pressed()
            compositormodes.delete_current_selection()

        # X 
        if event.keyval == gtk.keysyms.x:
            buttonevent.cut_pressed()
            return True

    return False

def _handle_clip_key_event(event):
    # Key bindings for MOVE MODES
    if editorstate.current_is_move_mode():                  
        # LEFT ARROW, prev frame
        if event.keyval == gtk.keysyms.Left:
            PLAYER().seek_delta(-1)
            return 

        # RIGHT ARROW, next frame
        if event.keyval == gtk.keysyms.Right:
            PLAYER().seek_delta(1)
            return 
                 
        # SPACE
        if event.keyval == gtk.keysyms.space:
            if PLAYER().is_playing():
                monitorevent.stop_pressed()
            else:
                monitorevent.play_pressed()

def _handle_delete():
    # Delete media file
    if gui.media_list_view.get_focus_child() != None:
        if gui.media_list_view.text_rend_1.get_property("editing") == True:
            return False
        useraction.delete_media_files()
        return True

    # Delete bin
    if gui.bin_list_view.get_focus_child() != None:
        if gui.bin_list_view.text_rend_1.get_property("editing") == True:
            return False
        useraction.delete_selected_bin()
        return True

    # Delete sequence
    if gui.sequence_list_view.get_focus_child() != None:
        if gui.sequence_list_view.text_rend_1.get_property("editing") == True:
            return False
        useraction.delete_selected_sequence()
        return True

    # Delete effect
    if gui.effect_stack_list_view.get_focus_child() != None:
        clipeffectseditor.delete_effect_pressed()
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
        
def _get_focus_keyframe_editor(keyframe_editor_widgets):
    if keyframe_editor_widgets == None:
        return None
    for kfeditor in keyframe_editor_widgets:
        if kfeditor.get_focus_child() != None:
            print "jou"
            print kfeditor
            return kfeditor
    
    print "nou"
    return None
