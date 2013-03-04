
"""
Module handles initializing and changing window contents acoording to user preferences.
"""

import gtk

import appconsts
import audiomonitoring
import buttonevent
import editevent
import editorpersistance
import editorstate
import glassbuttons
import gui
import guicomponents
import guiutils
import respaths
import titler
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
    
    
    if editorstate.SCREEN_WIDTH > 1678:
        layout_menu_item = gtk.MenuItem("Window Layout")
        layout_menu =  gtk.Menu()
        default = gtk.RadioMenuItem(None, "Default")

        default.connect("activate", lambda w: _show_default_layout(w))
        layout_menu.append(default)

        widescreen = gtk.RadioMenuItem(default, "Widescreen")
        widescreen.connect("activate", lambda w: _show_widescreen_layout(w))
        layout_menu.append(widescreen)

        if editorpersistance.prefs.default_layout == True:
            default.set_active(True)
        else:
            widescreen.set_active(True)
        layout_menu_item.set_submenu(layout_menu)
        menu.append(layout_menu_item)

    mb_menu_item = gtk.MenuItem("Middlebar Layout")
    mb_menu =  gtk.Menu()
    tc_left = gtk.RadioMenuItem(None, "TC Left")
    tc_left.set_active(True)
    tc_left.connect("activate", lambda w: _show_buttons_TC_LEFT_layout(w))
    mb_menu.append(tc_left)

    tc_middle = gtk.RadioMenuItem(tc_left, "TC Center")
    tc_middle.connect("activate", lambda w: _show_buttons_TC_MIDDLE_layout(w))
    mb_menu.append(tc_middle)

    if editorpersistance.prefs.midbar_tc_left == True:
        tc_left.set_active(True)
    else:
        tc_middle.set_active(True)

    mb_menu_item.set_submenu(mb_menu)
    menu.append(mb_menu_item)

    tabs_menu_item = gtk.MenuItem("Tabs Position")
    tabs_menu =  gtk.Menu()
    tabs_up = gtk.RadioMenuItem(None, "Up")
    tabs_up.connect("activate", lambda w: _show_tabs_up(w))
    tabs_menu.append(tabs_up)
    
    tabs_down = gtk.RadioMenuItem(tabs_up, "Down")
    tabs_down.connect("activate", lambda w: _show_tabs_down(w))

    if editorpersistance.prefs.tabs_on_top == True:
        tabs_up.set_active(True)
    else:
        tabs_down.set_active(True)

    tabs_menu.append(tabs_down)
    tabs_menu_item.set_submenu(tabs_menu)
    menu.append(tabs_menu_item)

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
    w.window.show_all()

    editorpersistance.prefs.midbar_tc_left = False
    editorpersistance.save()

def create_edit_buttons_row_buttons(editor_window):
    IMG_PATH = respaths.IMAGE_PATH
    
    editor_window.big_TC = guicomponents.BigTCDisplay()

    editor_window.zoom_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_in.png"), updater.zoom_in)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_out.png"), updater.zoom_out)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_length.png"), updater.zoom_project_length)

    editor_window.edit_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "splice_out.png"), buttonevent.splice_out_button_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "cut.png"), buttonevent.cut_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "lift.png"), buttonevent.lift_button_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "resync.png"), buttonevent.resync_button_pressed)

    editor_window.monitor_insert_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "overwrite_range.png"), buttonevent.range_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "overwrite_clip.png"), buttonevent.three_point_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "insert_clip.png"), buttonevent.insert_button_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "append_clip.png"), buttonevent.append_button_pressed)
    
    editor_window.mode_buttons_group = glassbuttons.GlassButtonsToggleGroup(46, 23, 2, 4, 5)
    editor_window.mode_buttons_group.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "over_move.png"), editor_window.handle_over_move_mode_button_press)
    editor_window.mode_buttons_group.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "insert_move.png"), editor_window.handle_insert_move_mode_button_press)
    editor_window.mode_buttons_group.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "one_roll_trim.png"), editor_window.handle_one_roll_mode_button_press)
    editor_window.mode_buttons_group.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "two_roll_trim.png"), editor_window.handle_two_roll_mode_button_press)
    editor_window.mode_buttons_group.set_pressed_button(1)

    editor_window.undo_redo = glassbuttons.GlassButtonsGroup(46, 23, 2, 2, 7)
    editor_window.undo_redo.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "undo.png"), editevent.do_undo)
    editor_window.undo_redo.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "redo.png"), editevent.do_redo)

    editor_window.tools_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 14, 7)
    editor_window.tools_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "open_mixer.png"), audiomonitoring.show_audio_monitor)
    editor_window.tools_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "open_titler.png"), titler.show_titler)
    
def fill_with_TC_LEFT_pattern(buttons_row, window):
    global w
    w = window
    buttons_row.pack_start(w.big_TC.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, 30), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(_get_mode_buttons_panel(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
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
    left_panel.pack_start(guiutils.get_pad_label(10, 30), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    left_panel.pack_start(_get_zoom_buttons_panel(), False, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        left_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        left_panel.pack_start(_get_tools_buttons(), False, True, 0)
        left_panel.pack_start(guiutils.get_pad_label(50, 10), False, True, 10) # to left and right panel same size for centering
    else:
        left_panel.pack_start(guiutils.get_pad_label(60, 10), False, True, 10) # to left and right panel same size for centering
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
    return w.mode_buttons_group.widget

def _get_zoom_buttons_panel():    
    return w.zoom_buttons.widget

def _get_undo_buttons_panel():
    return w.undo_redo.widget

def _get_edit_buttons_panel():
    return w.edit_buttons.widget

def _get_monitor_insert_buttons():
    return w.monitor_insert_buttons.widget

def _get_tools_buttons():
    return w.tools_buttons.widget

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
