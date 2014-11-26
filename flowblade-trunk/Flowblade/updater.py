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
Module contains GUI update routines.
"""

import pygtk
pygtk.require('2.0');
import gtk


import appconsts
import clipeffectseditor
import compositeeditor
import gui
import editorstate
from editorstate import current_sequence
from editorstate import MONITOR_MEDIA_FILE
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import timeline_visible
import editorpersistance
import monitorevent
import utils
import respaths
import tlinewidgets

page_size = 99.0 # gtk.Adjustment.get_page_size() wasn't there
                 # (wft?) so use this to have page size

# Scale constants
PIX_PER_FRAME_MAX = 20.0
PIX_PER_FRAME_MIN = 0.001
SCALE_MULTIPLIER = 0.66

# Trim edit loop playback
TRIM_EDIT_PRE_ROLL = 25
TRIM_EDIT_POST_ROLL = 20

# Current limit for full view scale
pix_per_frame_full_view = 0.2 

# Icons
IMG_PATH = None
play_icon = None
play_loop_icon = None
next_icon = None
next_trim_icon = None
prev_icon = None
prev_trim_icon = None
stop_icon = None
stop_trim_icon = None

# Callback func to set default editmode, set from outside of the module.
set_clip_edit_mode_callback = None

# Timeline position is saved when clip is displayed
saved_timeline_pos = -1

last_clicked_media_row = -1

# This needs to blocked for first and last window state events
player_refresh_enabled = False


#  This needs to be blocked when timeline is displayed as result 
# of Append/Inset... from monitor to get correct results
save_monitor_frame = False

# ---------------------------------- init
def load_icons():
    """
    These icons are switched when changing between trim and move modes
    """
    global play_icon, play_loop_icon,  next_icon, next_trim_icon, \
    prev_icon, prev_trim_icon, stop_icon, stop_trim_icon
     
    play_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "play_2_s.png")
    play_loop_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "play_loop.png")
    next_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "next_frame_s.png")
    next_trim_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "next_frame_trim.png")
    prev_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "prev_frame_s.png")
    prev_trim_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "prev_frame_trim.png")
    stop_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "stop_s.png")
    stop_trim_icon = gtk.image_new_from_file(respaths.IMAGE_PATH  + "stop_loop.png")


# --------------------------------- player
def refresh_player():
    # First event is initial window displayed event.
    # Last closing event needs to be blocked by setting this flag
    # before calling window hide
    global player_refresh_enabled
    if not player_refresh_enabled:
        player_refresh_enabled = True
        return
    # Refreshing while rendering overwrites file on disk and loses 
    # previous rendered data. 
    if PLAYER().is_rendering:
        return

    PLAYER().refresh()

# --------------------------------- window 
def window_resized():
    # This can get async called from window "size-allocate" signal 
    # during project load before project.c_seq has been build
    if not(hasattr(editorstate.project, "c_seq")):
        return
    if editorstate.project.c_seq == None:
        return

    # Resize track heights so that all tracks are displayed
    current_sequence().resize_tracks_to_fit(gui.tline_canvas.widget.allocation)
    
    # Place clips in the middle of timeline canvas after window resize
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)

    gui.tline_column.init_listeners() # hit areas for track swicthes need to be recalculated
    repaint_tline()

# --------------------------------- timeline
# --- REPAINT
def repaint_tline():
    """
    Repaints timeline canvas and scale
    """
    gui.tline_canvas.widget.queue_draw()
    gui.tline_scale.widget.queue_draw()

# --- SCROLL AND LENGTH EVENTS
def update_tline_scrollbar():
    """
    Sets timeline scrollwidget bar size and position
    """
    # Calculate page size
    # page_size / 100.0 == scroll bar size / scroll track width
    update_pix_per_frame_full_view()
    global page_size
    if tlinewidgets.pix_per_frame < pix_per_frame_full_view:
        page_size = 100.0
    else:
        page_size = (float(pix_per_frame_full_view) / \
                    tlinewidgets.pix_per_frame) * 100.0
                    
    # Get position, this might get called before GUI initiated 
    try:
        old_adjustment = gui.tline_scroll.get_adjustment()
        pos = old_adjustment.get_value()
    except Exception:
        pos = 0.0

    # Create and set adjustment
    adjustment = gtk.Adjustment(pos, 0.0, 100.0, 
                                1.0, 10.0, page_size)
    adjustment.connect("value-changed", tline_scrolled)
    try: # when testing this might get called before gui is build
        gui.tline_scroll.set_adjustment(adjustment)
    except Exception:
        pass 

def tline_scrolled(adjustment):
    """
    Callback from timeline scroller widget
    """
    if page_size != 100.0:
        tlinewidgets.pos = ((adjustment.get_value() / 100.0) * 
                           current_sequence().get_length())
    else:
        tlinewidgets.pos = 0
    repaint_tline()
    
def center_tline_to_current_frame():
    """
    Sets scroll widget adjustment to place current frame in the middle of display.
    """
    pos = tlinewidgets.get_pos_for_tline_centered_to_current_frame()
    gui.tline_scroll.get_adjustment().set_value((float(pos) / float(current_sequence().get_length())) * 100.0)

def init_tline_scale():
    """
    Calculates and sets first scale quaranteed to display full view 
    when starting from PIX_PER_FRAME_MAX with SCALE_MULTIPLIER steps.
    """
    pix_per_frame = PIX_PER_FRAME_MAX
    while pix_per_frame > pix_per_frame_full_view:
        pix_per_frame *= SCALE_MULTIPLIER
        
    tlinewidgets.pix_per_frame = pix_per_frame

def update_pix_per_frame_full_view():
    """
    Sets the value of pix_per_frame_full_view 
    Called at sequence init to display full sequence.
    """
    global pix_per_frame_full_view
    length = current_sequence().get_length() + 5 # +5 is just selected end pad so that end of movie is visible
    x, y, w, h = gui.tline_canvas.widget.allocation
    pix_per_frame_full_view = float(w) / length

def set_info_icon(info_icon_id):
    if info_icon_id == None:
        widget = gtk.Label()
    else:
        widget = gtk.image_new_from_stock(info_icon_id, gtk.ICON_SIZE_MENU)
    
    gui.tline_info.remove(gui.tline_info.info_contents)
    gui.tline_info.add(widget)
    gui.tline_info.info_contents = widget
    widget.show()

# --- ZOOM
def zoom_in():
    """
    Zooms in in the timeline view.
    """
    tlinewidgets.pix_per_frame *= 1.0 / SCALE_MULTIPLIER
    if tlinewidgets.pix_per_frame > PIX_PER_FRAME_MAX:
        tlinewidgets.pix_per_frame = PIX_PER_FRAME_MAX

    repaint_tline()
    update_tline_scrollbar()
    center_tline_to_current_frame()
    
def zoom_out():
    """
    Zooms out in the timeline view.
    """
    tlinewidgets.pix_per_frame *= SCALE_MULTIPLIER
    if tlinewidgets.pix_per_frame < PIX_PER_FRAME_MIN:
        tlinewidgets.pix_per_frame = PIX_PER_FRAME_MIN
    repaint_tline()
    update_tline_scrollbar()
    center_tline_to_current_frame()

def zoom_max():
    tlinewidgets.pix_per_frame = PIX_PER_FRAME_MAX
    repaint_tline()
    update_tline_scrollbar()
    center_tline_to_current_frame()

def zoom_project_length():
    tlinewidgets.pos = 0
    update_pix_per_frame_full_view()
    init_tline_scale()
    repaint_tline()
    update_tline_scrollbar()

def mouse_scroll_zoom(event):
    if event.state & gtk.gdk.CONTROL_MASK:
        adj = gui.tline_scroll.get_adjustment()
        incr = adj.get_step_increment()
        if event.direction == gtk.gdk.SCROLL_UP:
            adj.set_value(adj.get_value() + incr)
        else:
            adj.set_value(adj.get_value() - incr)
    else:
        if event.direction == gtk.gdk.SCROLL_UP:
            zoom_in()
        else:
            zoom_out()

def maybe_autocenter():
    if timeline_visible():
        if editorpersistance.prefs.auto_center_on_play_stop == True:
            center_tline_to_current_frame()


# ----------------------------------------- monitor
def display_clip_in_monitor(clip_monitor_currently_active=False):
    """
    Sets mltplayer producer to be video file clip and updates GUI.
    """
    if MONITOR_MEDIA_FILE() == None:
        gui.editor_window.clip_editor_b.set_active(False)
        return

    global save_monitor_frame
    save_monitor_frame = True

    # Opening clip exits trim modes
    if not editorstate.current_is_move_mode():
        set_clip_edit_mode_callback()

    gui.clip_editor_b.set_sensitive(True)
    editorstate._timeline_displayed = False

    # Save timeline pos if so directed.
    if clip_monitor_currently_active == False:
        global saved_timeline_pos
        saved_timeline_pos = PLAYER().current_frame()
        editorstate.tline_shadow_frame = saved_timeline_pos

    # If we're already displaying monitor clip we stop consumer 
    # to supress timeline flashing between monitor clips
    if clip_monitor_currently_active == False:
        editorstate.PLAYER().consumer.stop()

    # Clear old clip
    current_sequence().clear_hidden_track()
    
    # Create and display clip on hidden track
    if MONITOR_MEDIA_FILE().type == appconsts.PATTERN_PRODUCER or MONITOR_MEDIA_FILE().type == appconsts.IMAGE_SEQUENCE:
        # pattern producer or image sequence
        clip_producer = current_sequence().display_monitor_clip(None, MONITOR_MEDIA_FILE())
    else:
        # File producers
        clip_producer = current_sequence().display_monitor_clip(MONITOR_MEDIA_FILE().path)

    # Timeline flash does not happen if we start consumer after monitor clip is 
    # already on sequence
    if clip_monitor_currently_active == False:
        editorstate.PLAYER().consumer.start()
        
    # IMAGE_SEQUENCE files always returns 15000 for get_length from mlt so we have to monkeypatch that method to get correct results
    if MONITOR_MEDIA_FILE().type == appconsts.IMAGE_SEQUENCE:
        clip_producer.get_length = lambda : MONITOR_MEDIA_FILE().length
    
    clip_producer.mark_in = MONITOR_MEDIA_FILE().mark_in
    clip_producer.mark_out = MONITOR_MEDIA_FILE().mark_out
    
    # Give IMAGE and PATTERN_PRODUCER media types default mark in and mark out if not already set.
    # This makes them reasonably short and trimmable in both directions.
    if clip_producer.media_type == appconsts.IMAGE or clip_producer.media_type == appconsts.PATTERN_PRODUCER:
        if  clip_producer.mark_in == -1 and clip_producer.mark_out == -1:
            center_frame = clip_producer.get_length() / 2
            default_length_half = 75
            mark_in = center_frame - default_length_half
            mark_out = center_frame + default_length_half - 1
            clip_producer.mark_in = mark_in
            clip_producer.mark_out = mark_out
            MONITOR_MEDIA_FILE().mark_in = mark_in
            MONITOR_MEDIA_FILE().mark_out = mark_out

    display_monitor_clip_name()

    # Display frame, marks and pos
    gui.pos_bar.update_display_from_producer(clip_producer)

    if MONITOR_MEDIA_FILE().type == appconsts.IMAGE or \
        MONITOR_MEDIA_FILE().type == appconsts.PATTERN_PRODUCER:
        PLAYER().seek_frame(0)
    else:
        if editorpersistance.prefs.remember_monitor_clip_frame: 
            PLAYER().seek_frame(MONITOR_MEDIA_FILE().current_frame)
        else:
            PLAYER().seek_frame(0)
                    
    display_marks_tc()
    
    gui.pos_bar.widget.grab_focus()
    gui.media_list_view.widget.queue_draw()
    
    if editorpersistance.prefs.auto_play_in_clip_monitor == True:
        PLAYER().start_playback()
    
    repaint_tline()

def display_monitor_clip_name():
    # Display clip name
    if  MONITOR_MEDIA_FILE().mark_in != -1 and MONITOR_MEDIA_FILE().mark_out != -1:
        clip_length = utils.get_tc_string(MONITOR_MEDIA_FILE().mark_out - MONITOR_MEDIA_FILE().mark_in + 1) #+1 out incl.
        range_text = " / ][ " + str(clip_length)
    else:
        range_text = ""

    gui.editor_window.monitor_source.set_text(MONITOR_MEDIA_FILE().name + range_text)

def display_sequence_in_monitor():
    """
    Sets mltplayer producer to be current sequence
    tractor and updates GUI.
    """
    if PLAYER() == None: # this method gets called too early when initializing, hack fix.
        return
    
    # If this gets called without user having pressed 'Timeline' button we'll 
    # programmatically press it to recall this method to have the correct button down.
    if gui.sequence_editor_b.get_active() == False:
        gui.sequence_editor_b.set_active(True)
        return
        
    editorstate._timeline_displayed = True

    # Clear hidden track that has been displaying monitor clip
    current_sequence().clear_hidden_track()

    # Reset timeline pos
    global saved_timeline_pos
    if saved_timeline_pos != -1:
        PLAYER().seek_frame(saved_timeline_pos)
    saved_timeline_pos = -1

    # Display sequence name
    name = editorstate.current_sequence().name
    profile_desc = editorstate.current_sequence().profile.description()
    if editorpersistance.prefs.show_sequence_profile:
        gui.editor_window.monitor_source.set_text(name + " / " + profile_desc)
    else:
        gui.editor_window.monitor_source.set_text(name)
    
    # Display marks and pos 
    gui.pos_bar.update_display_from_producer(PLAYER().producer)
    display_marks_tc()

    repaint_tline()

def switch_monitor_display():
    monitorevent.stop_pressed()
    if editorstate.MONITOR_MEDIA_FILE() == None:
        return
    if editorstate._timeline_displayed == True:
        gui.editor_window.clip_editor_b.set_active(True)
    else:
        gui.editor_window.sequence_editor_b.set_active(True)

def display_tline_cut_frame(track, index):
    """
    Displays sequence frame at cut
    """
    if not timeline_visible():
        display_sequence_in_monitor()

    if index < 0:
        index = 0
    if index > (len(track.clips) - 1):
        index = len(track.clips) - 1
    
    clip_start_frame = track.clip_start(index)
    PLAYER().seek_frame(clip_start_frame)

def media_file_row_double_clicked(treeview, tree_path, col):
    gui.tline_canvas.widget.grab_focus()
    row = max(tree_path)
    media_file_id = editorstate.current_bin().file_ids[row]
    media_file = PROJECT().media_files[media_file_id]
    set_and_display_monitor_media_file(media_file)

def set_and_display_monitor_media_file(media_file):
    """
    Displays media_file in clip monitor when new media file 
    selected for display by double clicking or drag'n'drop
    """
    editorstate._monitor_media_file = media_file
    
    # If we're already displaying clip monitor, then already button is down we call display_clip_in_monitor(..)
    # directly, but dont save position because we're not displaying now.
    #
    # If we're displaying sequence we do programmatical click on "Clip" button 
    # to display clip via it's signal listener. 
    if gui.editor_window.clip_editor_b.get_active() == True:
        display_clip_in_monitor(clip_monitor_currently_active = True)
    else:
        gui.editor_window.clip_editor_b.set_active(True)

# --------------------------------------- frame displayes
def update_frame_displayers(frame):
    """
    Display frame position in position bar and time code display.
    """
    # Update position bar with normalized pos
    if timeline_visible():
        producer_length = PLAYER().producer.get_length()
    else:
        producer_length = gui.pos_bar.producer.get_length()
        if save_monitor_frame:
            MONITOR_MEDIA_FILE().current_frame = frame

    norm_pos = frame / float(producer_length) 
    gui.pos_bar.set_normalized_pos(norm_pos)

    gui.tline_scale.widget.queue_draw()
    gui.tline_canvas.widget.queue_draw()
    gui.big_tc.widget.queue_draw()
    clipeffectseditor.display_kfeditors_tline_frame(frame)
    compositeeditor.display_kfeditors_tline_frame(frame)

def update_kf_editor():
    clipeffectseditor.update_kfeditors_positions()

# ----------------------------------------- marks
def display_marks_tc():
    if not timeline_visible():
        display_monitor_clip_name()

# ----------------------------------------------- clip editors
def clip_removed_during_edit(clip):
    clipeffectseditor.clip_removed_during_edit(clip)
    
def clear_clip_from_editors(clip):
    if clipeffectseditor.clip == clip:
        clipeffectseditor.clear_clip()

def open_clip_in_effects_editor(data):
    clip, track, item_id, x = data
    frame = tlinewidgets.get_frame(x)
    index = current_sequence().get_clip_index(track, frame)

    clipeffectseditor.set_clip(clip, track, index)
    
# ----------------------------------------- edit modes
def set_trim_mode_gui():
    """
    Called when user selects trim mode
    """
    display_sequence_in_monitor()

def set_move_mode_gui():
    """
    Called when user selects move mode
    """
    display_sequence_in_monitor()

def set_transition_render_edit_menu_items_sensitive(range_start, range_end):
    if not editorstate.current_is_move_mode():
        return

    ui = gui.editor_window.uimanager
    render_transition = ui.get_widget('/MenuBar/EditMenu/AddTransition')
    render_fade = ui.get_widget('/MenuBar/EditMenu/AddFade')
    if range_start == -1:
        render_transition.set_sensitive(False)
        render_fade.set_sensitive(False)
    elif range_start == range_end:
        render_transition.set_sensitive(False)
        render_fade.set_sensitive(True)
    elif range_start == range_end - 1:
        render_transition.set_sensitive(True)
        render_fade.set_sensitive(False)
    else:
        render_transition.set_sensitive(False)
        render_fade.set_sensitive(False)

# ------------------------------------------------ notebook
def switch_notebook_panel(index):
    gui.middle_notebook.set_current_page(index)


