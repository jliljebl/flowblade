
"""
Module handles initializing and changing window contents acoording to user preferences.
"""

import gtk

import appconsts
import buttonevent
import editevent
import editorpersistance
import gui
import guicomponents
import guiutils
import respaths
import updater

# editor window object
# This needs to be set here because gui.py module ref is not available at init time
w = None

BUTTON_HEIGHT = 28 # middle edit buttons row
BUTTON_WIDTH = 48 # middle edit buttons row

def init_view_menu(menu_item):
    """
    Fills menu item with menuitems to open recent projects.
    """
    menu = menu_item.get_submenu()
    
    default = gtk.RadioMenuItem(None, "Default")

    default.connect("activate", lambda w: _show_default_layout(w))
    menu.append(default)

    widescreen = gtk.RadioMenuItem(default, "Widescreen")
    widescreen.connect("activate", lambda w: _show_widescreen_layout(w))
    menu.append(widescreen)

    if editorpersistance.prefs.default_layout == True:
        default.set_active(True)
    else:
        widescreen.set_active(True)

    sep = gtk.SeparatorMenuItem()
    menu.append(sep)
    
    tc_left = gtk.RadioMenuItem(None, "Middle bar TC Left")
    tc_left.set_active(True)
    tc_left.connect("activate", lambda w: _show_buttons_TC_LEFT_layout(w))
    menu.append(tc_left)

    tc_middle = gtk.RadioMenuItem(tc_left, "Middle bar TC Center")
    tc_middle.connect("activate", lambda w: _show_buttons_TC_MIDDLE_layout(w))
    menu.append(tc_middle)

    if editorpersistance.prefs.midbar_tc_left == True:
        tc_left.set_active(True)
    else:
        tc_middle.set_active(True)

    sep = gtk.SeparatorMenuItem()
    menu.append(sep)

    tabs_up = gtk.RadioMenuItem(None, "Tabs Up")
    tabs_up.connect("activate", lambda w: _show_tabs_up(w))
    menu.append(tabs_up)
    
    tabs_down = gtk.RadioMenuItem(tabs_up, "Tabs Down")
    tabs_down.connect("activate", lambda w: _show_tabs_down(w))

    if editorpersistance.prefs.tabs_on_top == True:
        tabs_up.set_active(True)
    else:
        tabs_down.set_active(True)

    menu.append(tabs_down)

def init_gui_to_prefs(window):
    global w
    w = window

    if editorpersistance.prefs.tabs_on_top == True:
        w.notebook.set_tab_pos(gtk.POS_TOP)
        w.right_notebook.set_tab_pos(gtk.POS_TOP)
    else:
        w.notebook.set_tab_pos(gtk.POS_BOTTOM)
        w.right_notebook.set_tab_pos(gtk.POS_BOTTOM)

    if editorpersistance.prefs.default_layout == False:
        _execute_widescreen_layout(window)

def _show_default_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return # this may get called on start up before refs are available 
    if widget.get_active() == False: # setting radiobutton active called listener on all of groups items
        return
    if editorpersistance.prefs.default_layout == True:
        return
    
    w.right_notebook.remove_page(0)
    w.notebook.insert_page(w.effects_panel, gtk.Label(_("Filters")), 1)
    w.right_notebook.remove_page(0)
    w.notebook.insert_page(w.compositors_panel,  gtk.Label(_("Compositors")), 2)

    w.top_row_hbox.remove(w.right_notebook)
    w.notebook.set_size_request(appconsts.NOTEBOOK_WIDTH, appconsts.TOP_ROW_HEIGHT)
    w.top_row_hbox.resize_children()

    w.window.show_all()

    editorpersistance.prefs.default_layout = True
    editorpersistance.save()

def _show_widescreen_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return # this may get called on start up before refs are available
    if widget.get_active() == False:
        return
    if editorpersistance.prefs.default_layout == False:
        return
    _execute_widescreen_layout(w)
    
def _execute_widescreen_layout(window):
    window.notebook.remove_page(1)
    window.right_notebook.append_page(w.effects_panel, gtk.Label(_("Filters")))    
    window.notebook.remove_page(1)
    window.right_notebook.append_page(w.compositors_panel,  gtk.Label(_("Compositors")))

    window.top_row_hbox.pack_start(w.right_notebook, False, False, 0)

    window.notebook.set_size_request(appconsts.NOTEBOOK_WIDTH_WIDESCREEN, appconsts.TOP_ROW_HEIGHT)
    window.right_notebook.set_size_request(appconsts.NOTEBOOK_WIDTH_WIDESCREEN, appconsts.TOP_ROW_HEIGHT)
    
    window.window.show_all()

    editorpersistance.prefs.default_layout = False
    editorpersistance.save()
    
def _show_buttons_TC_LEFT_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    create_edit_buttons_row_buttons(w)
    fill_with_TC_LEFT_pattern(w.edit_buttons_row, w)
    connect_edit_buttons(w)
    w.window.show_all()

    editorpersistance.prefs.midbar_tc_left = True
    editorpersistance.save()
    
def _show_buttons_TC_MIDDLE_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    create_edit_buttons_row_buttons(w)
    fill_with_TC_MIDDLE_pattern(w.edit_buttons_row, w)
    connect_edit_buttons(w)
    w.window.show_all()

    editorpersistance.prefs.midbar_tc_left = False
    editorpersistance.save()

def create_edit_buttons_row_buttons(editor_window):
    IMG_PATH = respaths.IMAGE_PATH
    
    # Create TC Display
    editor_window.big_TC = guicomponents.BigTCDisplay()

    # Zoom buttnos
    editor_window.zoom_in_b = gtk.Button()
    zoomin_icon = gtk.image_new_from_file(IMG_PATH + "zoom_in.png")
    _b(editor_window.zoom_in_b, zoomin_icon)

    editor_window.zoom_out_b = gtk.Button()
    zoomout_icon = gtk.image_new_from_file(IMG_PATH + "zoom_out.png")
    _b(editor_window.zoom_out_b, zoomout_icon)

    editor_window.zoom_length_b = gtk.Button()
    zoom_length_icon = gtk.image_new_from_file(IMG_PATH + "zoom_length.png")
    _b(editor_window.zoom_length_b, zoom_length_icon)

    # Edit action buttons
    editor_window.splice_out_b = gtk.Button()
    splice_out_icon = gtk.image_new_from_file(IMG_PATH + "splice_out.png")
    _b(editor_window.splice_out_b, splice_out_icon)

    editor_window.cut_b = gtk.Button()
    cut_move_icon = gtk.image_new_from_file(IMG_PATH + "cut.png") 
    _b(editor_window.cut_b, cut_move_icon)

    editor_window.lift_b = gtk.Button()
    lift_icon = gtk.image_new_from_file(IMG_PATH + "lift.png") 
    _b(editor_window.lift_b, lift_icon)

    editor_window.resync_b = gtk.Button()
    resync_icon = gtk.image_new_from_file(IMG_PATH + "resync.png") 
    _b(editor_window.resync_b, resync_icon)

    # Monitor insert buttons
    editor_window.overwrite_range_b = gtk.Button()
    overwrite_r_clip_icon = gtk.image_new_from_file(IMG_PATH + "overwrite_range.png")
    _b(editor_window.overwrite_range_b, overwrite_r_clip_icon)
    
    editor_window.overwrite_b = gtk.Button()
    overwrite_clip_icon = gtk.image_new_from_file(IMG_PATH + "overwrite_clip.png")
    _b(editor_window.overwrite_b, overwrite_clip_icon)

    editor_window.insert_b = gtk.Button()
    insert_clip_icon = gtk.image_new_from_file(IMG_PATH + "insert_clip.png")
    _b(editor_window.insert_b, insert_clip_icon)

    editor_window.append_b = gtk.Button()
    append_clip_icon = gtk.image_new_from_file(IMG_PATH + "append_clip.png")
    _b(editor_window.append_b, append_clip_icon)
    
    # Mode buttons
    editor_window.insert_move_b = gtk.RadioButton()
    editor_window.insert_move_b.set_mode(False)
    insert_move_icon = gtk.image_new_from_file(IMG_PATH + "insert_move.png")
    _b(editor_window.insert_move_b, insert_move_icon)
    editor_window._set_mode_button_colors(editor_window.insert_move_b)

    editor_window.one_roll_trim_b = gtk.RadioButton(editor_window.insert_move_b)
    editor_window.one_roll_trim_b.set_mode(False)
    one_roll_icon = gtk.image_new_from_file(IMG_PATH + "one_roll_trim.png")
    _b(editor_window.one_roll_trim_b, one_roll_icon)
    editor_window._set_mode_button_colors(editor_window.one_roll_trim_b)

    editor_window.overwrite_move_b = gtk.RadioButton(editor_window.insert_move_b)
    editor_window.overwrite_move_b.set_mode(False)
    over_move_icon = gtk.image_new_from_file(IMG_PATH + "over_move.png")
    _b(editor_window.overwrite_move_b, over_move_icon)
    editor_window._set_mode_button_colors(editor_window.overwrite_move_b)
    
    editor_window.tworoll_trim_b = gtk.RadioButton(editor_window.insert_move_b)
    editor_window.tworoll_trim_b.set_mode(False)
    two_roll_icon = gtk.image_new_from_file(IMG_PATH + "two_roll_trim.png")
    _b(editor_window.tworoll_trim_b, two_roll_icon)
    editor_window._set_mode_button_colors(editor_window.tworoll_trim_b)
    
    # Undo / Redo buttons
    editor_window.undo_b = gtk.Button()
    undo_icon = gtk.image_new_from_file(IMG_PATH + "undo.png")
    _b(editor_window.undo_b, undo_icon)

    editor_window.redo_b = gtk.Button()
    redo_icon = gtk.image_new_from_file(IMG_PATH + "redo.png")
    _b(editor_window.redo_b, redo_icon)

def connect_edit_buttons(editor_window):
    editor_window.zoom_in_b.connect("clicked", lambda w,e: updater.zoom_in(), None)
    editor_window.zoom_out_b.connect("clicked", lambda w,e: updater.zoom_out(), None)
    editor_window.zoom_length_b.connect("clicked", lambda w,e: updater.zoom_project_length(), None)

    editor_window.insert_move_b.connect("clicked", lambda w,e: editor_window._handle_mode_button_press(w), None)        
    editor_window.one_roll_trim_b.connect("clicked", lambda w,e: editor_window._handle_mode_button_press(w), None)        
    editor_window.tworoll_trim_b.connect("clicked", lambda w,e: editor_window._handle_mode_button_press(w), None)
    editor_window.overwrite_move_b.connect("clicked", lambda w,e: editor_window._handle_mode_button_press(w), None)   

    editor_window.cut_b.connect("clicked", lambda w,e: buttonevent.cut_pressed(), None)
    editor_window.splice_out_b.connect("clicked", lambda w,e: buttonevent.splice_out_button_pressed(), None)
    editor_window.lift_b.connect("clicked", lambda w,e: buttonevent.lift_button_pressed(), None)
    editor_window.resync_b.connect("clicked", lambda w,e:buttonevent.resync_button_pressed(), None)

    editor_window.insert_b.connect("clicked", lambda w,e: buttonevent.insert_button_pressed(), None)
    editor_window.overwrite_b.connect("clicked", lambda w,e: buttonevent.three_point_overwrite_pressed(), None)
    editor_window.overwrite_range_b.connect("clicked", lambda w,e: buttonevent.range_overwrite_pressed(), None)
    editor_window.append_b.connect("clicked", lambda w,e: buttonevent.append_button_pressed(), None)

    editor_window.undo_b.connect("clicked", lambda w,e: editevent.do_undo(), None)
    editor_window.redo_b.connect("clicked", lambda w,e: editevent.do_redo(), None)
    
def fill_with_TC_LEFT_pattern(buttons_row, window):
    global w
    w = window
    buttons_row.pack_start(w.big_TC.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, 10), False, True, 0)
    buttons_row.pack_start(_get_mode_buttons_panel(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_undo_buttons_panel(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_zoom_buttons_panel(), False, True, 10)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_edit_buttons_panel(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_monitor_insert_buttons(), False, True, 0)

def fill_with_TC_MIDDLE_pattern(buttons_row, window):
    global w
    w = window
    left_panel = gtk.HBox(False, 0)    
    left_panel.pack_start(_get_undo_buttons_panel(), False, True, 0)
    left_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    left_panel.pack_start(_get_zoom_buttons_panel(), False, True, 0)
    left_panel.pack_start(guiutils.get_pad_label(117, 10), False, True, 10) # to left and right panel same size for centering
    left_panel.pack_start(gtk.Label(), True, True, 0)

    middle_panel = gtk.HBox(False, 0) 
    middle_panel.pack_start(w.big_TC.widget, False, True, 0)
    middle_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    middle_panel.pack_start(_get_mode_buttons_panel(), False, True, 0)
    
    right_panel = gtk.HBox(False, 0) 
    right_panel.pack_start(gtk.Label(), True, True, 0)
    right_panel.pack_start(_get_edit_buttons_panel(), False, True, 0)
    right_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    right_panel.pack_start(_get_monitor_insert_buttons(), False, True, 0)

    buttons_row.pack_start(left_panel, True, True, 0)
    buttons_row.pack_start(middle_panel, False, False, 0)
    buttons_row.pack_start(right_panel, True, True, 0)

def _get_mode_buttons_panel():
    mode_buttons = _get_buttons_panel(4, 38)
    mode_buttons.set_size_request(195, 24)
    mode_buttons.pack_start(w.overwrite_move_b, False, True, 0)
    mode_buttons.pack_start(w.insert_move_b, False, True, 0)
    mode_buttons.pack_start(w.one_roll_trim_b, False, True, 0)
    mode_buttons.pack_start(w.tworoll_trim_b, False, True, 0)

    return mode_buttons

def _get_zoom_buttons_panel():    
    zoom_buttons = _get_buttons_panel(3)
    zoom_buttons.pack_start(w.zoom_in_b, False, True, 0)
    zoom_buttons.pack_start(w.zoom_out_b, False, True, 0)
    zoom_buttons.pack_start(w.zoom_length_b, False, True, 0)
    
    return zoom_buttons

def _get_undo_buttons_panel():
    undo_buttons = _get_buttons_panel(2)
    undo_buttons.pack_start(w.undo_b, False, True, 0)
    undo_buttons.pack_start(w.redo_b, False, True, 0)

    return undo_buttons

def _get_edit_buttons_panel():
    edit_buttons = _get_buttons_panel(4)
    edit_buttons.pack_start(w.lift_b, False, True, 0)
    edit_buttons.pack_start(w.splice_out_b, False, True, 0)
    edit_buttons.pack_start(w.cut_b, False, True, 0)
    edit_buttons.pack_start(w.resync_b, False, True, 0)
    
    return edit_buttons

def _get_monitor_insert_buttons():
    monitor_input_buttons = _get_buttons_panel(4)
    monitor_input_buttons.pack_start(w.overwrite_range_b, False, True, 0)
    monitor_input_buttons.pack_start(w.overwrite_b, False, True, 0)
    monitor_input_buttons.pack_start(w.insert_b, False, True, 0)
    monitor_input_buttons.pack_start(w.append_b, False, True, 0)

    return monitor_input_buttons

def _show_tabs_up(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return
    w.notebook.set_tab_pos(gtk.POS_TOP)
    w.right_notebook.set_tab_pos(gtk.POS_TOP)
    editorpersistance.prefs.tabs_on_top = True
    editorpersistance.save()

def _show_tabs_down(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return
    w.notebook.set_tab_pos(gtk.POS_BOTTOM)
    w.right_notebook.set_tab_pos(gtk.POS_BOTTOM)
    editorpersistance.prefs.tabs_on_top = False
    editorpersistance.save()

def _get_buttons_panel(btns_count, btn_width=BUTTON_WIDTH):
    panel = gtk.HBox(True, 0)
    panel.set_size_request(btns_count * btn_width, BUTTON_HEIGHT)
    return panel

def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(gtk.RELIEF_NONE)

def _clear_container(cont):
    children = cont.get_children()
    for child in children:
        cont.remove(child)
