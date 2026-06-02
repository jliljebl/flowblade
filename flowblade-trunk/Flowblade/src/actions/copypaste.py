
"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2025 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
from gi.repository import Gdk, Gtk

import appconsts
import clipeffectseditor
import compositeeditor
import editorstate
import gui
import projectaction
import tlineaction


# ----------------------------------------------------------------------- COPY PASTE ACTION FORWARDING
def cut_action():
    if gui.timeline_has_focus() == False:
        # Try to cut text to clipboard because user pressed CTRL + X.
        if gui.media_list_view.widget.get_focus_child() != None:
            projectaction.cut_media_files()
            return True
                    
        # Try to extract text to clipboard because user pressed CTRL + C.
        copy_source = gui.editor_window.window.get_focus()
        try:
            display = Gdk.Display.get_default()
            cb = Gtk.Clipboard.get_default(display)
            copy_source.get_buffer().cut_clipboard(cb, True)
            return True
        except:# selected widget was not a Gtk.Editable that can provide text to clipboard.
            return False
    else:
        tlineaction.do_timeline_objects_copy(False)
        return True
        
def copy_action():
    if gui.timeline_has_focus() == False:
        filter_kf_editor = _get_focus_keyframe_editor(clipeffectseditor.keyframe_editor_widgets)
        geom_kf_editor = _get_focus_keyframe_editor(compositeeditor.keyframe_editor_widgets)
        if filter_kf_editor != None:
            value = filter_kf_editor.get_copy_kf_value()
            save_data = (appconsts.COPY_PASTE_KEYFRAME_EDITOR_KF_DATA, (value, filter_kf_editor))
            editorstate.set_copy_paste_objects(save_data) 
            return True
        elif geom_kf_editor != None:
            value = geom_kf_editor.get_copy_kf_value() 
            save_data = (appconsts.COPY_PASTE_GEOMETRY_EDITOR_KF_DATA, (value, geom_kf_editor))
            editorstate.set_copy_paste_objects(save_data)
            return True
        else:
            # Try to extract text to clipboard because user pressed CTRL + C.
            copy_source = gui.editor_window.window.get_focus()
            try:
                display = Gdk.Display.get_default()
                cb = Gtk.Clipboard.get_default (display)
                copy_source.get_buffer().copy_clipboard(cb)
                return True
            except:# selected widget was not a Gtk.Editable that can provide text to clipboard.
                return False
    else:
        tlineaction.do_timeline_objects_copy()
        return True

def paste_action():
    if gui.timeline_has_focus() == False:
        copy_paste_object = editorstate.get_copy_paste_objects()
        if copy_paste_object == None:
            _attempt_default_paste()
            return False
        data_type, paste_data = editorstate.get_copy_paste_objects()
        if data_type == appconsts.COPY_PASTE_KEYFRAME_EDITOR_KF_DATA:
            value, kf_editor = paste_data
            kf_editor.paste_kf_value(value)
            return True
        
        elif data_type == appconsts.COPY_PASTE_GEOMETRY_EDITOR_KF_DATA:
            value, geom_editor = paste_data
            geom_editor.paste_kf_value(value)
            return True
        elif data_type == appconsts.CUT_PASTE_MEDIA_ITEMS:
            projectaction.paste_media_files()
            return True
        
        return False
    else:
        tlineaction.do_timeline_objects_paste()
        _attempt_default_paste()
        return True

def _attempt_default_paste():
    # Try to extract text to clipboard because user pressed CTRL + C.
    paste_target = gui.editor_window.window.get_focus()
    try:
        display = Gdk.Display.get_default()
        clipboard = Gtk.Clipboard.get_default(display)
        paste_target.get_buffer().paste_clipboard(clipboard, None, True)
        return True
    except:# selected widget cannot be pasted into
        return False

def _get_focus_keyframe_editor(keyframe_editor_widgets):
    if keyframe_editor_widgets == None:
        return None
    for kfeditor in keyframe_editor_widgets:
        if kfeditor.get_focus_child() != None:
           return kfeditor
    return None
    
