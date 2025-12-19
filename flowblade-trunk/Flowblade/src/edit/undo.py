"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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

"""
Module manages undo and redo stacks and executes edit actions from them
on user requests.
"""
import gi
from gi.repository import GLib

import copy
import time

import callbackbridge
import editorstate
import utils
import utilsgtk

PROPERTY_EDIT_COMMIT_DELAY_MILLIS = 500
PROPERTY_POLL_TICK_DELAY_MILLIS = 250 
_property_edit_poll_ticker = None
_first_action = None

set_post_undo_redo_edit_mode = None # This is set at startup to avoid circular imports.
repaint_tline = None

# Max stack size.
MAX_UNDOS = 35

# EditActions are placed in this stack after their do_edit()
# method has been called.
undo_stack = []

# Index is the stack pointer that tracks done undos and redos.
# The value of index is index of next undo + 1
# The value of index is index of next redo or == stack size if
# no redos.
index = 0

# Some menu items are set active/deactivate based on undo stack state.
save_item = None
undo_item = None 
redo_item = None


# dict edtable property -> editor, needed to update editors after undo/redo
_editor_for_property = {}


def clear_undos():
    global undo_stack, index
    undo_stack = []
    index = 0

def set_post_undo_redo_callback(undo_redo_callback):
    global set_post_undo_redo_edit_mode
    set_post_undo_redo_edit_mode = undo_redo_callback

def set_menu_items(uimanager):
    global save_item, undo_item, redo_item
    save_item = uimanager.get_widget("/MenuBar/FileMenu/Save")
    undo_item = uimanager.get_widget("/MenuBar/EditMenu/Undo")
    redo_item = uimanager.get_widget("/MenuBar/EditMenu/Redo")

def register_edit(undo_edit):
    """
    Adds a performed EditAction into undo stack
    """
    global index
    
    # New edit action clears all redos(== undos after index)
    if index != len(undo_stack) and (len(undo_stack) != 0):
        del undo_stack[index:]
 
    # Keep stack in size, if too big remove undo at 0
    if len(undo_stack) > MAX_UNDOS:
        del undo_stack[0]
        index = index - 1
        
    # Add to stack and grow index
    undo_stack.append(undo_edit)
    index = index + 1
    
    if editorstate.PROJECT().last_save_path != None:
        save_item.set_sensitive(True) # Disabled at load and save, first edit enables if project has been saved.
    undo_item.set_sensitive(True)
    redo_item.set_sensitive(False)



def do_undo_and_repaint(widget=None, data=None):
    do_undo()
    repaint_tline()
    
def do_redo_and_repaint(widget=None, data=None):
    do_redo()
    repaint_tline()
    
def do_undo():
    global index
    if index == 0:
        return
    
    # Empty stack, no undos
    if len(undo_stack) == 0:
        undo_item.set_sensitive(False)
        redo_item.set_sensitive(False)
        return

    # After undo we may change edit mode
    _set_post_edit_mode()
    
    # Move stack pointer down and do undo
    index = index - 1
    undo_edit = undo_stack[index]
    undo_edit.undo()
    
    if index == 0:
        undo_item.set_sensitive(False)
    
    redo_item.set_sensitive(True)
    
def do_redo():
    global index
        
    # If we are at the top of the stack, can't do redo
    if index == len(undo_stack):
        redo_item.set_sensitive(False)
        return
        
    # Empty stack, no redos
    if len(undo_stack) == 0:
        redo_item.set_sensitive(False)
        return

    # After redo we may change edit mode
    _set_post_edit_mode()

    # Do redo and move stack pointer up
    redo_edit = undo_stack[index]
    redo_edit.redo()
    index = index + 1

    if index == len(undo_stack):
        redo_item.set_sensitive(False)

    undo_item.set_sensitive(True)

def _set_post_edit_mode():
    if editorstate.edit_mode != editorstate.INSERT_MOVE:
        set_post_undo_redo_edit_mode()

def undo_redo_stress_test():
    global undo_stack, index
    times = 10
    delay = 0.100
    
    for r in range(0, times):
        while index > 0:
            print("undo:", index)
            do_undo()

            time.sleep(delay)
    
        while index < len(undo_stack):
            print("redo:", index)
            do_redo()

            time.sleep(delay)


# ------------------------------------------- PROPERT EDIT UNDO
def _property_edit_poll_event(property_edit_action):
    print("tick")
    global _property_edit_poll_ticker
    if _property_edit_poll_ticker == None:
        return
    
    current_time = round(time.time() * 1000)
    
    property_edit_action.maybe_commit_event(current_time)

def set_editor_for_property(editable_property, editor):
    global _editor_for_property
    _editor_for_property[editable_property] = editor

def get_editor_for_property(editable_property):
    global _editor_for_property
    return _editor_for_property[editable_property]
    

class ProperEditAction:
    
    def __init__(self, value_set_func, undo_val, edit_data):
        self.value_set_func = value_set_func
        self.undo_val = copy.deepcopy(undo_val)
        self.edit_data = edit_data
        self.redo_val = None
        self.creation_time = None 

    def edit_done(self, redo_val):
        self.redo_val = copy.deepcopy(redo_val)
        self.creation_time = round(time.time() * 1000)
                    
        global _property_edit_poll_ticker, _first_action
        if _property_edit_poll_ticker == None:
            _first_action = self
            _property_edit_poll_ticker = utilsgtk.GtkTicker(_property_edit_poll_event, PROPERTY_POLL_TICK_DELAY_MILLIS, self)
            _property_edit_poll_ticker.start_ticker()
        else:
            _property_edit_poll_ticker.data = self

    def maybe_commit_event(self, current_time):
        if current_time - self.creation_time < PROPERTY_EDIT_COMMIT_DELAY_MILLIS:
            return
        
        global _property_edit_poll_ticker, _first_action
        _property_edit_poll_ticker.destroy_ticker()
        _property_edit_poll_ticker = None
        
        self.undo_val = _first_action.undo_val 
        _first_action = None 

        register_edit(self)
    
    def undo(self):
        print("ProperEditAction.undo", self.undo_val)
        self.value_set_func(self.undo_val, self.edit_data)

    def redo(self):
        print("ProperEditAction.redo", self.redo_val)
        self.value_set_func(self.redo_val, self.edit_data)


# ------------------------------------------- LINKED SEQUENCE CYCLIC TESTING
WHITE = 0
GREY = 1
BLACK = 2

is_cyclic = False

class LinkNode:
    
    def __init__(self, seq):
        self.seq = seq
        self.targets = []
        self.color = WHITE

    def get_target_nodes(self, nodes):
        target_nodes = []
        for node in nodes:
            if node.seq.uid in self.targets:
                target_nodes.append(node)
        return target_nodes

def force_revert_if_cyclic_seq_links(project):
    test_thread = utils.LaunchThread(project, _run_seq_link_cyclic_test)
    test_thread.run()

def _run_seq_link_cyclic_test(project):
    global is_cyclic
    is_cyclic = False
    nodes = []
    
    for seq in project.sequences:
        node = LinkNode(seq)
        nodes.append(node)
        for track in seq.tracks:
            for clip in track.clips:
                if clip.link_seq_data == None:
                    continue
                else:
                    try:
                        node.targets.append(clip.link_seq_data)
                    except AttributeError:
                        # Is already a set.
                        node.targets.add(clip.link_seq_data)
                    node.targets = set(node.targets) 

    for node in nodes:
        _visitDFS(node, nodes)
        
    if is_cyclic == True:
        GLib.idle_add(_do_force_undo_with_pop)

def _visitDFS(node, nodes):
    global is_cyclic
    
    node.color = GREY

    target_nodes = node.get_target_nodes(nodes)

    for target_node in target_nodes:
        if target_node.color == GREY:
            is_cyclic = True
        if target_node.color == WHITE:
            _visitDFS(target_node, nodes)

    node.color = BLACK


def _do_force_undo_with_pop():
    global undo_stack, index
    
    # Revert edit 
    do_undo()
    
    # Delete edit action creating cyclic state.
    if index != len(undo_stack) and (len(undo_stack) != 0):
        del undo_stack[index:]

    callbackbridge.dialogs_show_cyclic_error()
