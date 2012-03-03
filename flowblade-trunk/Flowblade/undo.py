"""
Module manages undo and redo stacks and executes edit actions from them
on user requests.
"""
import editorstate
from editevent import set_default_edit_mode as default_edit_mode

# Max stack size
MAX_UNDOS = 35

# EditActions are placed in this stack after their do_edit()
# method has been called
undo_stack = []

# Index is the stack pointer that tracks done undos and redos.
# The value of index is index of next undo + 1
# The value of index is index of next redo or == stack size if
# no redos.
index = 0

# Some menu items are set active/deactive based on undo stack state
save_item = None
undo_item = None 
redo_item = None

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
    undo_stack.append(undo_edit);
    index = index + 1
    
    save_item.set_sensitive(True) # Disabled at load and save, first edit enables
    undo_item.set_sensitive(True)
    redo_item.set_sensitive(False)

def do_undo():
    global index
    
    if index == 0:
        return
    
    # Empty stack, no undos
    if len(undo_stack) == 0:
        undo_item.set_sensitive(False)
        redo_item.set_sensitive(False)
        return

    # After undo we're always in INSERT_MOVE mode
    _reset_default_editmode()
    
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

    # After redo we're always in INSERT_MOVE mode
    _reset_default_editmode()

    # Do redo and move stack pointer up
    redo_edit = undo_stack[index]
    redo_edit.redo()
    index = index + 1

    if index == len(undo_stack):
        redo_item.set_sensitive(False)

    undo_item.set_sensitive(True)

def _reset_default_editmode():
    if editorstate.edit_mode != editorstate.INSERT_MOVE:
        default_edit_mode()
