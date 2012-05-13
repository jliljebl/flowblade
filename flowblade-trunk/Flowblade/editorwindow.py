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
Module contains main editor window object.
"""
import cairo
import gtk
import pango
import pygtk

import app
import buttonevent
from cairoarea import CairoDrawableArea
import clipeffectseditor
import compositeeditor
import dnd
import editevent
import editorpersistance
import editorstate
import gui
import guicomponents
import mltplayer
import monitorevent
import movemodes
import render
import respaths
import panels
from positionbar import PositionBar
import syncsplitevent
import test
import tlinewidgets
import useraction
import updater
import utils
import vieweditor

# GUI size params
TOP_ROW_HEIGHT = 500 # defines app min height with tlinewidgets.HEIGHT
NOTEBOOK_WIDTH = 600 # defines app min width with MONITOR_AREA_WIDTH
NOTE_BOOK_LEFT_COLUMN = 300
MEDIA_MANAGER_WIDTH = 250

MONITOR_AREA_WIDTH = 600 # defines app min width with NOTEBOOK_WIDTH 400 for small

BUTTON_HEIGHT = 34 # middle edit buttons row
BUTTON_WIDTH = 48 # middle edit buttons row

BINS_HEIGHT = 250
EFFECT_STACK_VIEW_HEIGHT = 160
EFFECT_VALUE_EDITOR_HEIGHT = 200
EFFECT_SELECT_EDITOR_HEIGHT = 140

IMG_PATH = None

def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(gtk.RELIEF_NONE)

def _toggle_image_switch(widget, icons):
    not_pressed, pressed = icons
    if widget.get_active() == True:
        widget.set_image(pressed)
    else:
        widget.set_image(not_pressed)


class EditorWindow:

    def __init__(self):
        global IMG_PATH
        IMG_PATH = respaths.IMAGE_PATH 
        
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
        self.window.set_border_width(5)

        # To ask confirmation for shutdown 
        self.window.connect("delete-event", lambda w, e:app.shutdown())

        # Player consumer has to be stopped and started when window resized
        self.window.connect("window-state-event", lambda w, e:updater.refresh_player())

        # Build menubar
        # Menubar build resources
        menu_actions = [
            ('FileMenu', None, _('_File')),
            ('New', None, _('_New...'), '<control>N', None, lambda a:useraction.new_project()),
            ('Open', None, _('_Open...'), '<control>O', None, lambda a:useraction.load_project()),
            ('OpenRecent', None, _('Open Recent')),
            ('Save', None, _('_Save'), '<control>S', None, lambda a:useraction.save_project()),
            ('Save As', None, _('_Save As...'), None, None, lambda a:useraction.save_project_as()),
            ('Close', None, _('_Close'), None, None, lambda a:useraction.close_project()),
            ('Quit', None, _('_Quit'), '<control>Q', None, lambda a:app.shutdown()),
            ('EditMenu', None, _('_Edit')),
            ('Undo', None, _('_Undo'), '<control>Z', None, editevent.do_undo),
            ('Redo', None, _('_Redo'), '<control>Y', None, editevent.do_redo),
            ('CreateColorClip', None, _('Create Color Clip...'), None, None, lambda a:editevent.create_color_clip()),
            ('ClearFilters', None, _('Clear Filters From Selected'), None, None, lambda a:editevent.clear_filters()),
            ('ConsolidateSelectedBlanks', None, _('Consolidate Selected Blanks'), None, None, lambda a:editevent.consolidate_selected_blanks()),
            ('ConsolidateAllBlanks', None, _('Consolidate All Blanks'), None, None, lambda a:editevent.consolidate_all_blanks()),
            ('RecreateMediaIcons', None, _('Recreate Media Icons...'), None, None, lambda a:useraction.recreate_media_file_icons()),
            ('ProfilesManager', None, _('Profiles Manager'), None, None, lambda a:useraction.profiles_manager()),
            ('Preferences', None, _('Preferences'), None, None, lambda a:useraction.display_preferences()),
            ('HelpMenu', None, _('_Help')),
            ('QuickReference', None, _('Contents'), None, None, lambda a:useraction.quick_reference()),
            ('About', None, _('About'), None, None, lambda a:useraction.about())
            ]
    
        menu_string = """<ui>
            <menubar name='MenuBar'>
                <menu action='FileMenu'>
                    <menuitem action='New'/>
                    <menuitem action='Open'/>
                    <menu action='OpenRecent'/>
                    <menuitem action='Save'/>
                    <menuitem action='Save As'/>
                    <separator/>
                    <menuitem action='Close'/>
                    <menuitem action='Quit'/>
                </menu>
                <menu action='EditMenu'>
                    <menuitem action='Undo'/>
                    <menuitem action='Redo'/>
                    <separator/>
                    <menuitem action='ClearFilters'/>     
                    <separator/>
                    <menuitem action='ConsolidateSelectedBlanks'/>
                    <menuitem action='ConsolidateAllBlanks'/>
                    <separator/>
                    <menuitem action='CreateColorClip'/>
                    <separator/>
                    <menuitem action='RecreateMediaIcons'/>
                    <menuitem action='ProfilesManager'/>
                    <menuitem action='Preferences'/>
                </menu>
                <menu action='HelpMenu'>
                    <menuitem action='QuickReference'/>
                    <separator/>
                    <menuitem action='About'/>
                </menu>
          </menubar>
        </ui>"""
                    
        action_group = gtk.ActionGroup('WindowActions')
        action_group.add_actions(menu_actions, user_data=None)
        ui = gtk.UIManager()
        ui.insert_action_group(action_group, 0)
        ui.add_ui_from_string(menu_string)
        accel_group = ui.get_accel_group()
        self.window.add_accel_group(accel_group)
        self.menubar = ui.get_widget('/MenuBar')
        self.uimanager = ui

        # Add recent projects to menu
        editorpersistance.fill_recents_menu_widget(ui.get_widget('/MenuBar/FileMenu/OpenRecent'), useraction.open_recent_project)
        
        # Menu box
        menu_vbox = gtk.VBox(False, 0)
        menu_vbox.pack_start(self.menubar, False, True, 0)

        # Media manager
        self.bin_list_view = guicomponents.BinListView(
                                        useraction.bin_selection_changed, 
                                        useraction.bin_name_edited)
        dnd.connect_bin_tree_view(self.bin_list_view.treeview, useraction.move_files_to_bin)
        self.bin_list_view.set_property("can-focus",  True)
        bins_panel = panels.get_bins_panel(self.bin_list_view,
                                           lambda w,e: useraction.add_new_bin(),
                                           lambda w,e: useraction.delete_selected_bin())
        bins_panel.set_size_request(MEDIA_MANAGER_WIDTH, BINS_HEIGHT)

        self.media_list_view = guicomponents.MediaListView(
                                          updater.media_file_row_double_clicked,
                                          useraction.media_file_name_edited)                                          
        self.media_list_view.treeview.connect("button-press-event",
                                              useraction.media_list_button_press)
        dnd.connect_media_files_tree_view(self.media_list_view.treeview)
        media_panel = panels.get_media_files_panel(
                                self.media_list_view,
                                lambda w,e: useraction.add_media_files(), 
                                lambda w,e: useraction.delete_media_files())
        
        mm_vbox = gtk.HBox()
        mm_vbox.set_border_width(5)
        mm_vbox.pack_start(bins_panel, False, False, 0)
        mm_vbox.pack_start(media_panel, True, True, 0)
        
        mm_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        mm_panel.set_padding(0, 0, 4, 0)
        mm_panel.add(mm_vbox)

        # Effects
        self.effect_select_list_view = guicomponents.FilterListView()
        self.effect_select_combo_box = gtk.combo_box_new_text()
        self.effect_select_list_view.treeview.connect("row-activated", useraction.effect_select_row_double_clicked)
        dnd.connect_effects_select_tree_view(self.effect_select_list_view.treeview)

        clip_editor_panel = panels.get_clip_effects_editor_panel(
                                    self.effect_select_combo_box,
                                    self.effect_select_list_view)

        clipeffectseditor.widgets.effect_stack_view.treeview.connect("button-press-event",
                                              useraction.filter_stack_button_press)
                                              
        effects_editor_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        effects_editor_panel.set_padding(4, 4, 4, 4)
        effects_editor_panel.add(clipeffectseditor.widgets.value_edit_frame)
        
        effects_hbox = gtk.HBox()
        effects_hbox.set_border_width(5)
        effects_hbox.pack_start(clip_editor_panel, False, False, 0)
        effects_hbox.pack_start(effects_editor_panel, True, True, 0)

        effects_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        effects_panel.set_padding(0, 0, 4, 0)
        effects_panel.add(effects_hbox)
        
        # Compositors
        compositor_clip_panel = panels.get_compositor_clip_panel()

        compositor_editor_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        compositor_editor_panel.set_padding(4, 4, 4, 4)
        compositor_editor_panel.add(compositeeditor.widgets.value_edit_frame)

        compositors_hbox = gtk.HBox()
        compositors_hbox.set_border_width(5)
        compositors_hbox.pack_start(compositor_clip_panel, False, False, 0)
        compositors_hbox.pack_start(compositor_editor_panel, True, True, 0)

        compositors_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        compositors_panel.set_padding(0, 0, 4, 0)
        compositors_panel.add(compositors_hbox)

        # Project buttons
        self.open_project_b = gtk.Button(_("Open"))
        self.new_project_b = gtk.Button(_("New"))
    
        self.open_project_b.connect("clicked", lambda e: useraction.load_project())
        self.new_project_b.connect("clicked", lambda e: useraction.new_project())

        project_buttons_box = gtk.HBox(True,1)
        project_buttons_box.pack_start(self.open_project_b)
        project_buttons_box.pack_start(self.new_project_b)

        # Project
        name_panel = panels.get_project_name_panel(editorstate.project.name)

        profile_info = panels.get_profile_info_panel(editorstate.project.profile)
        
        self.project_info_vbox = gtk.VBox()
        self.project_info_vbox.pack_start(name_panel, False, True, 0)
        self.project_info_vbox.pack_start(profile_info, False, True, 0)
        
        # Sequence list
        self.sequence_list_view = guicomponents.SequenceListView(
                                        useraction.sequence_name_edited)
        seq_panel = panels.get_sequences_panel(
                             self.sequence_list_view,
                             lambda w,e: useraction.change_edit_sequence(),
                             lambda w,e: useraction.add_new_sequence(), 
                             lambda w,e: useraction.delete_selected_sequence())

        # Project vbox and panel
        project_vbox = gtk.VBox()
        project_vbox.pack_start(project_buttons_box, False, True, 0)
        project_vbox.pack_start(self.project_info_vbox, False, True, 0)
        project_vbox.pack_start(seq_panel, True, True, 0)
    
        project_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        project_panel.set_padding(6, 6, 12, 6)
        project_panel.add(project_vbox)

        # Render
        normal_height = True
        if TOP_ROW_HEIGHT < 500: # small screens have no space to display this
            normal_height = False

        render_panel_left = panels.get_render_panel_left(
                                self,
                                lambda w,e: useraction.open_additional_render_options_dialog(),
                                True)

        render_panel_right = panels.get_render_panel_right(lambda w,e: useraction.render_timeline(), normal_height)
        render.widgets.opts_info_button.connect("clicked", lambda w: useraction.ffmpeg_opts_help())

        render_hbox = gtk.HBox(True, 5)
        render_hbox.pack_start(render_panel_left, True, True, 0)
        render_hbox.pack_start(render_panel_right, True, True, 0)

        render_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        render_panel.set_padding(6, 12, 12, 12)
        render_panel.add(render_hbox)

        # Notebook
        self.notebook = gtk.Notebook()
        self.notebook.set_size_request(NOTEBOOK_WIDTH, TOP_ROW_HEIGHT)
        self.notebook.append_page(mm_panel, gtk.Label(_("Media")))
        self.notebook.append_page(effects_panel, gtk.Label(_("Filters")))
        self.notebook.append_page(compositors_panel, gtk.Label(_("Compositors")))
        self.notebook.append_page(project_panel, gtk.Label(_("Project")))
        self.notebook.append_page(render_panel, gtk.Label(_("Render")))

        # Timecode panel
        tc_panel = panels.get_timecode_panel(self)
   
        # Video display
        self.tline_display = gtk.DrawingArea() 
        dnd.connect_video_monitor(self.tline_display)

        # Position bar and decorative frame  for it
        self.pos_bar = PositionBar()
        pos_bar_frame = gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        # Positionbar vbox
        pos_bar_vbox = gtk.VBox(False, 1)
        filler1 = gtk.Label()
        filler1.set_size_request(5, 2)
        pos_bar_vbox.pack_start(filler1, False, True, 0)
        pos_bar_vbox.pack_start(pos_bar_frame, False, True, 0)

        playback_buttons = self._get_player_buttons()

        # Creates monitor switch buttons
        self._create_monitor_buttons()

        # Switch button box
        switch_hbox = gtk.HBox(True, 1)
        switch_hbox.pack_start(self.sequence_editor_b, False, False, 0)
        switch_hbox.pack_start(self.clip_editor_b, False, False, 0)

        # Switch button box V, for centered buttons
        switch_vbox = gtk.VBox(False, 1)
        filler333 = gtk.Label()
        filler333.set_size_request(5, 2)
        switch_vbox.pack_start(filler333, False, True, 0)
        switch_vbox.pack_start(switch_hbox, False, True, 0)

        # Switch / pos bar row
        sw_pos_hbox = gtk.HBox(False, 1)
        sw_pos_hbox.pack_start(switch_vbox, False, True, 0)
        sw_pos_hbox.pack_start(pos_bar_vbox, True, True, 0)
        
        # Monitor
        monitor_vbox = gtk.VBox(False, 1)
        monitor_vbox.pack_start(tc_panel, False, True, 0)
        monitor_vbox.pack_start(self.tline_display, True, True, 0)
        monitor_vbox.pack_start(sw_pos_hbox, False, True, 0)
        monitor_vbox.pack_start(playback_buttons, False, True, 0)
        
        monitor_align = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=1.0, yscale=1.0) 
        monitor_align.add(monitor_vbox)
        monitor_align.set_padding(3, 0, 3, 3)
        
        monitor_frame = gtk.Frame()
        monitor_frame.add(monitor_align)
        monitor_frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        monitor_frame.set_size_request(MONITOR_AREA_WIDTH, TOP_ROW_HEIGHT)

        # Top row 
        top_paned = gtk.HPaned()
        top_paned.pack1(self.notebook, resize=True, shrink=False)
        top_paned.pack2(monitor_frame, resize=False, shrink=False)

        top_row_hbox = gtk.HBox(False, 0)
        filler4 = gtk.Label()
        filler4.set_size_request(5, 5)
        top_row_hbox.pack_start(top_paned, True, True, 0)
        
        # Edit buttons rows
        edit_buttons_row = self._get_edit_buttons_row()

        # Timeline scale
        self.tline_scale = tlinewidgets.TimeLineFrameScale(editevent.insert_move_mode_pressed,  
                                                           updater.mouse_scroll_zoom)
        scale_frame = gtk.Frame()
        
        # Timecode display
        self.tline_info = gtk.HBox()
        info_contents = gtk.Label()
        self.tline_info.add(info_contents)
        self.tline_info.info_contents = info_contents # this switched and sacved as member of its container
        info_h = gtk.HBox()
        info_h.pack_start(self.tline_info, False, False, 0)
        info_h.pack_start(gtk.Label(), True, True, 0)
        info_h.set_size_request(tlinewidgets.COLUMN_WIDTH, 
                                      tlinewidgets.SCALE_HEIGHT)
                                       
        # Timeline top row
        tline_hbox_1 = gtk.HBox()
        tline_hbox_1.pack_start(info_h, False, False, 0)
        tline_hbox_1.pack_start(self.tline_scale.widget, True, True, 0)
        
        # Timeline column
        self.tline_column = tlinewidgets.TimeLineColumn(
                            editevent.track_active_switch_pressed,
                            editevent.track_mute_switch_pressed,
                            editevent.track_center_pressed)
                            
        # Timeline editpanel
        self.tline_canvas = tlinewidgets.TimeLineCanvas(
            editevent.tline_canvas_mouse_pressed,
            editevent.tline_canvas_mouse_moved,
            editevent.tline_canvas_mouse_released,
            editevent.tline_canvas_double_click,
            updater.mouse_scroll_zoom)
            
        dnd.connect_tline(self.tline_canvas.widget, editevent.tline_effect_drop,  
                          editevent.tline_media_drop)

        # Timeline middle row
        tline_hbox_2 = gtk.HBox()
        tline_hbox_2.pack_start(self.tline_column.widget, False, False, 0)
        tline_hbox_2.pack_start(self.tline_canvas.widget, True, True, 0)
        
        # Bottom row filler
        left_corner = gtk.Label()
        #font_desc = pango.FontDescription("normal 9")
        left_corner.set_size_request(tlinewidgets.COLUMN_WIDTH, 20)
        #left_corner.modify_font(font_desc)
        # Timeline scroller
        self.tline_scroller = tlinewidgets.TimeLineScroller(
                                                updater.tline_scrolled)
        
        # Timeline bottom row
        tline_hbox_3 = gtk.HBox()
        tline_hbox_3.pack_start(left_corner, False, False, 0)
        tline_hbox_3.pack_start(self.tline_scroller, True, True, 0)
        
        # Timeline hbox 
        tline_vbox = gtk.VBox()
        tline_vbox.pack_start(tline_hbox_1, False, False, 0)
        tline_vbox.pack_start(tline_hbox_2, True, True, 0)
        tline_vbox.pack_start(tline_hbox_3, False, False, 0)
        
        # Timeline box 
        self.tline_box = gtk.HBox()
        self.tline_box.pack_start(tline_vbox, True, True, 0)

        # Timeline pane
        filler_rp2 = gtk.Label()
        filler_rp2.set_size_request(5, 4)
        tline_pane = gtk.VBox(False, 1)
        tline_pane.pack_start(edit_buttons_row, False, True, 0)
        tline_pane.pack_start(filler_rp2, False, True, 0)
        tline_pane.pack_start(self.tline_box, True, True, 0)

        # VPaned top row / timeline
        app_v_paned = gtk.VPaned()
        app_v_paned.pack1(top_row_hbox, resize=False, shrink=False)
        app_v_paned.pack2(tline_pane, resize=True, shrink=False)

        # Pane
        pane = gtk.VBox(False, 1)
        pane.pack_start(menu_vbox, False, True, 0)
        pane.pack_start(app_v_paned, True, True, 0)
        
        # Tooltips
        self._add_tool_tips()

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade")
        self.window.set_position(gtk.WIN_POS_CENTER)  
        self.window.show_all()
                
    def _create_monitor_buttons(self):
        # Monitor switch buttons
        self.sequence_editor_b = gtk.RadioButton(None, _("Timeline"))
        self.sequence_editor_b.set_mode(False)
        self.sequence_editor_b.connect("clicked", 
                        lambda w,e: self._monitor_switch_handler(w), 
                        None)
        self.sequence_editor_b.set_size_request(100, 25)

        self.clip_editor_b = gtk.RadioButton(self.sequence_editor_b,_("Clip"))
        self.clip_editor_b.set_mode(False)
        self.clip_editor_b.connect("clicked",
                        lambda w,e: self._monitor_switch_handler(w),
                        None)
        self.clip_editor_b.set_size_request(100, 25)
    
    def _monitor_switch_handler(self, widget):
        # We get two "clicked" events per toggle, send through only the one
        # from activated button
        if ((self.sequence_editor_b.get_active() == True) 
            and (widget == self.sequence_editor_b)):
            updater.display_sequence_in_monitor() 

        if ((self.clip_editor_b.get_active() == True) 
            and (widget == self.clip_editor_b)):
            updater.display_clip_in_monitor()
    
    def _get_player_buttons(self):
        # Icons
        rew_icon = gtk.image_new_from_file(IMG_PATH + "backward_s.png")
        ff_icon = gtk.image_new_from_file(IMG_PATH + "forward_s.png")
        play_icon = gtk.image_new_from_file(IMG_PATH + "play_2_s.png")
        stop_icon = gtk.image_new_from_file(IMG_PATH + "stop_s.png")
        next_icon = gtk.image_new_from_file(IMG_PATH + "next_frame_s.png")
        prev_icon = gtk.image_new_from_file(IMG_PATH + "prev_frame_s.png")
        mark_in_icon = gtk.image_new_from_file(IMG_PATH + "mark_in_s.png")
        mark_out_icon = gtk.image_new_from_file(IMG_PATH + "mark_out_s.png")
        marks_clear_icon = gtk.image_new_from_file(IMG_PATH + "marks_clear_s.png") 
        to_mark_in_icon = gtk.image_new_from_file(IMG_PATH + "to_mark_in_s.png")        
        to_mark_out_icon = gtk.image_new_from_file(IMG_PATH + "to_mark_out_s.png") 
        
        # Create buttons
        self.rew_b = gtk.Button()
        self.rew_b.set_relief(gtk.RELIEF_NONE)
        _b(self.rew_b, rew_icon)
        
        self.ff_b = gtk.Button()
        self.ff_b.set_relief(gtk.RELIEF_NONE)
        _b(self.ff_b, ff_icon)
        
        self.next_b = gtk.Button()
        self.next_b.set_relief(gtk.RELIEF_NONE)
        _b(self.next_b, next_icon)
        
        self.prev_b = gtk.Button()
        self.prev_b.set_relief(gtk.RELIEF_NONE)
        _b(self.prev_b, prev_icon)
        
        self.play_b = gtk.Button()
        self.play_b.set_relief(gtk.RELIEF_NONE)
        _b(self.play_b, play_icon)
        
        self.stop_b = gtk.Button()
        self.stop_b.set_relief(gtk.RELIEF_NONE)
        _b(self.stop_b, stop_icon)

        self.mark_in_b = gtk.Button()
        self.mark_in_b.set_relief(gtk.RELIEF_NONE)
        _b(self.mark_in_b, mark_in_icon)

        self.mark_out_b = gtk.Button()
        self.mark_out_b.set_relief(gtk.RELIEF_NONE)
        _b(self.mark_out_b, mark_out_icon)

        self.marks_clear_b = gtk.Button()
        self.marks_clear_b.set_relief(gtk.RELIEF_NONE)
        _b(self.marks_clear_b, marks_clear_icon)

        self.to_mark_in_b = gtk.Button()
        self.to_mark_in_b.set_relief(gtk.RELIEF_NONE)
        _b(self.to_mark_in_b, to_mark_in_icon)

        self.to_mark_out_b = gtk.Button()
        self.to_mark_out_b.set_relief(gtk.RELIEF_NONE)
        _b(self.to_mark_out_b, to_mark_out_icon)

        self.view_mode_select = guicomponents.get_monitor_view_select_combo()

        start_pad = gtk.Label()
        start_pad.set_size_request(30, 23)
        rewind_group = gtk.HBox(True, 1)
        rewind_group.set_size_request(50, 23)
        one_frame_group = gtk.HBox(True, 1)
        one_frame_group.set_size_request(50, 23)
        play_group = gtk.HBox(True, 1)
        play_group.set_size_request(50, 23)
        in_out_group = gtk.HBox(True, 1)
        in_out_group.set_size_request(50, 23)
        to_marks_group = gtk.HBox(True, 1)
        to_marks_group.set_size_request(50, 23)
        end_pad = gtk.Label()
        end_pad.set_size_request(0, 23)

        # Create and return buttons panel
        player_buttons = gtk.HBox(False, 1)
        player_buttons.pack_start(start_pad, False, True, 0)
        rewind_group.pack_start(self.rew_b, False, True, 0)
        rewind_group.pack_start(self.ff_b, False, True, 0)
        player_buttons.pack_start(rewind_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        one_frame_group.pack_start(self.prev_b, False, True, 0)
        one_frame_group.pack_start(self.next_b, False, True, 0)
        player_buttons.pack_start(one_frame_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        play_group.pack_start(self.play_b, False, True, 0)
        play_group.pack_start(self.stop_b, False, True, 0)
        player_buttons.pack_start(play_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        in_out_group.pack_start(self.mark_in_b, False, True, 0)
        in_out_group.pack_start(self.mark_out_b, False, True, 0)
        player_buttons.pack_start(in_out_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        to_marks_group.pack_start(self.to_mark_in_b, False, True, 0)
        to_marks_group.pack_start(self.to_mark_out_b, False, True, 0)
        player_buttons.pack_start(to_marks_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        player_buttons.pack_start(self.marks_clear_b, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        player_buttons.pack_start(self.view_mode_select,  False, True, 0)
        player_buttons.pack_start(end_pad, False, True, 0)

        return player_buttons
        
    def connect_player(self, mltplayer):
        # Buttons
        self.play_b.connect("clicked", lambda w,e: monitorevent.play_pressed(), None)
        self.stop_b.connect("clicked", lambda w,e: monitorevent.stop_pressed(), None)
        self.prev_b.connect("clicked", lambda w,e: monitorevent.prev_pressed(), None)
        self.next_b.connect("clicked", lambda w,e: monitorevent.next_pressed(), None)

        self.ff_b.connect("pressed", lambda w,e: monitorevent.ff_pressed(), None)
        self.ff_b.connect("released", lambda w,e: monitorevent.ff_released(), None)
        self.rew_b.connect("pressed", lambda w,e: monitorevent.rew_pressed(), None)
        self.rew_b.connect("released", lambda w,e: monitorevent.rew_released(), None)

        self.mark_in_b.connect("clicked", lambda w,e: monitorevent.mark_in_pressed(), None)
        self.mark_out_b.connect("clicked", lambda w,e: monitorevent.mark_out_pressed(), None)
        self.marks_clear_b.connect("clicked", lambda w,e: monitorevent.marks_clear_pressed(), None)
        self.to_mark_in_b.connect("clicked", lambda w,e: monitorevent.to_mark_in_pressed(), None)
        self.to_mark_out_b.connect("clicked", lambda w,e: monitorevent.to_mark_out_pressed(), None)

        self.view_mode_select.connect("changed", lambda w, e: buttonevent.view_mode_changed(w), None)

        # Monitor position bar
        self.pos_bar.set_listener(mltplayer.seek_position_normalized)

    def _get_edit_buttons_row(self):
        # Create TC Display
        self.big_TC = guicomponents.BigTCDisplay()
        
        # Create buttons
        # Zoom buttnos
        self.zoom_in_b = gtk.Button()
        zoomin_icon = gtk.image_new_from_file(IMG_PATH + "zoom_in.png")
        _b(self.zoom_in_b, zoomin_icon)

        self.zoom_out_b = gtk.Button()
        zoomout_icon = gtk.image_new_from_file(IMG_PATH + "zoom_out.png")
        _b(self.zoom_out_b, zoomout_icon)

        self.zoom_length_b = gtk.Button()
        zoom_length_icon = gtk.image_new_from_file(IMG_PATH + "zoom_length.png")
        _b(self.zoom_length_b, zoom_length_icon)

        # Edit action buttons
        self.splice_out_b = gtk.Button()
        splice_out_icon = gtk.image_new_from_file(IMG_PATH + "splice_out.png")
        _b(self.splice_out_b, splice_out_icon)

        self.cut_b = gtk.Button()
        cut_move_icon = gtk.image_new_from_file(IMG_PATH + "cut.png") 
        _b(self.cut_b, cut_move_icon)

        self.lift_b = gtk.Button()
        lift_icon = gtk.image_new_from_file(IMG_PATH + "lift.png") 
        _b(self.lift_b, lift_icon)

        self.resync_b = gtk.Button()
        resync_icon = gtk.image_new_from_file(IMG_PATH + "resync.png") 
        _b(self.resync_b, resync_icon)

        # Monitor insert buttons
        self.overwrite_range_b = gtk.Button()
        overwrite_r_clip_icon = gtk.image_new_from_file(IMG_PATH + "overwrite_range.png")
        _b(self.overwrite_range_b, overwrite_r_clip_icon)
        
        self.overwrite_b = gtk.Button()
        overwrite_clip_icon = gtk.image_new_from_file(IMG_PATH + "overwrite_clip.png")
        _b(self.overwrite_b, overwrite_clip_icon)

        self.insert_b = gtk.Button()
        insert_clip_icon = gtk.image_new_from_file(IMG_PATH + "insert_clip.png")
        _b(self.insert_b, insert_clip_icon)

        self.append_b = gtk.Button()
        append_clip_icon = gtk.image_new_from_file(IMG_PATH + "append_clip.png")
        _b(self.append_b, append_clip_icon)
        
        # Mode buttons
        self.insert_move_b = gtk.RadioButton()
        self.insert_move_b.set_mode(False)
        insert_move_icon = gtk.image_new_from_file(IMG_PATH + "insert_move.png")
        _b(self.insert_move_b, insert_move_icon)

        self.one_roll_trim_b = gtk.RadioButton(self.insert_move_b)
        self.one_roll_trim_b.set_mode(False)
        one_roll_icon = gtk.image_new_from_file(IMG_PATH + "one_roll_trim.png")
        _b(self.one_roll_trim_b, one_roll_icon)
    
        self.overwrite_move_b = gtk.RadioButton(self.insert_move_b)
        self.overwrite_move_b.set_mode(False)
        over_move_icon = gtk.image_new_from_file(IMG_PATH + "over_move.png")
        _b(self.overwrite_move_b, over_move_icon)

        self.tworoll_trim_b = gtk.RadioButton(self.insert_move_b)
        self.tworoll_trim_b.set_mode(False)
        two_roll_icon = gtk.image_new_from_file(IMG_PATH + "two_roll_trim.png")
        _b(self.tworoll_trim_b, two_roll_icon)

        # Undo / Redo buttons
        self.undo_b = gtk.Button()
        undo_icon = gtk.image_new_from_file(IMG_PATH + "undo.png")
        _b(self.undo_b, undo_icon)

        self.redo_b = gtk.Button()
        redo_icon = gtk.image_new_from_file(IMG_PATH + "redo.png")
        _b(self.redo_b, redo_icon)

        # Mode buttons panel
        mode_buttons = self._get_buttons_panel(4, 38)
        mode_buttons.set_size_request(195, 22)
        mode_buttons.pack_start(self.overwrite_move_b, False, True, 0)
        mode_buttons.pack_start(self.insert_move_b, False, True, 0)
        mode_buttons.pack_start(self.one_roll_trim_b, False, True, 0)
        mode_buttons.pack_start(self.tworoll_trim_b, False, True, 0)

        # Zoom buttons panel
        zoom_buttons = self._get_buttons_panel(3)
        zoom_buttons.pack_start(self.zoom_in_b, False, True, 0)
        zoom_buttons.pack_start(self.zoom_out_b, False, True, 0)
        zoom_buttons.pack_start(self.zoom_length_b, False, True, 0)

        # Unro/Redo buttons panel
        undo_buttons = self._get_buttons_panel(2)
        undo_buttons.pack_start(self.undo_b, False, True, 0)
        undo_buttons.pack_start(self.redo_b, False, True, 0)

        # Edit buttons panel
        edit_buttons = self._get_buttons_panel(4)
        edit_buttons.pack_start(self.lift_b, False, True, 0)
        edit_buttons.pack_start(self.splice_out_b, False, True, 0)
        edit_buttons.pack_start(self.cut_b, False, True, 0)
        edit_buttons.pack_start(self.resync_b, False, True, 0)

        # Monitor source panel
        monitor_input_buttons =  self._get_buttons_panel(4)
        monitor_input_buttons.pack_start(self.overwrite_range_b, False, True, 0)
        monitor_input_buttons.pack_start(self.overwrite_b, False, True, 0)
        monitor_input_buttons.pack_start(self.insert_b, False, True, 0)
        monitor_input_buttons.pack_start(self.append_b, False, True, 0)

        tc_pad = gtk.Label()
        tc_pad.set_size_request(7, 10)

        # Row
        buttons_row = gtk.HBox(False, 1)
        buttons_row.pack_start(self.big_TC.widget, False, True, 0)
        buttons_row.pack_start(tc_pad, False, True, 0)
        buttons_row.pack_start(mode_buttons, False, True, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(undo_buttons, False, True, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(zoom_buttons, False, True, 10)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(edit_buttons, False, True, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(monitor_input_buttons, False, True, 0)

        # Connect signals
        self.zoom_in_b.connect("clicked", lambda w,e: updater.zoom_in(), None)
        self.zoom_out_b.connect("clicked", lambda w,e: updater.zoom_out(), None)
        self.zoom_length_b.connect("clicked", lambda w,e: updater.zoom_project_length(), None)

        self.insert_move_b.connect("clicked", lambda w,e: self._handle_mode_button_press(w), None)        
        self.one_roll_trim_b.connect("clicked", lambda w,e: self._handle_mode_button_press(w), None)        
        self.tworoll_trim_b.connect("clicked", lambda w,e: self._handle_mode_button_press(w), None)
        self.overwrite_move_b.connect("clicked", lambda w,e: self._handle_mode_button_press(w), None)   

        self.cut_b.connect("clicked", lambda w,e: buttonevent.cut_pressed(), None)
        self.splice_out_b.connect("clicked", lambda w,e: buttonevent.splice_out_button_pressed(), None)
        self.lift_b.connect("clicked", lambda w,e: buttonevent.lift_button_pressed(), None)
        self.resync_b.connect("clicked", lambda w,e:buttonevent.resync_button_pressed(), None)

        self.insert_b.connect("clicked", lambda w,e: buttonevent.insert_button_pressed(), None)
        self.overwrite_b.connect("clicked", lambda w,e: buttonevent.three_point_overwrite_pressed(), None)
        self.overwrite_range_b.connect("clicked", lambda w,e: buttonevent.range_overwrite_pressed(), None)
        self.append_b.connect("clicked", lambda w,e: buttonevent.append_button_pressed(), None)

        self.undo_b.connect("clicked", lambda w,e: editevent.do_undo(), None)
        self.redo_b.connect("clicked", lambda w,e: editevent.do_redo(), None)

        return buttons_row

    def _add_tool_tips(self):
        self.big_TC.widget.set_tooltip_text(_("Timeline current frame timecode"))
        
        self.zoom_in_b.set_tooltip_text(_("Zoom In"))
        self.zoom_out_b.set_tooltip_text(_("Zoom Out"))
        self.zoom_length_b.set_tooltip_text(_("Zoom to Sequence length"))

        self.insert_move_b.set_tooltip_text(_("Insert Move"))      
        self.one_roll_trim_b.set_tooltip_text(_("One Roll Trim"))           
        self.tworoll_trim_b.set_tooltip_text(_("Two Roll Trim"))    
        self.overwrite_move_b.set_tooltip_text(_("Overwrite Move"))    

        self.cut_b.set_tooltip_text(_("Cut"))    
        self.splice_out_b.set_tooltip_text(_("Splice Out Clip"))    
        self.lift_b.set_tooltip_text(_("Lift Clip"))    
        self.resync_b.set_tooltip_text(_("Resync Selected Clips"))    

        self.insert_b.set_tooltip_text(_("Insert Monitor Clip Range"))    
        self.overwrite_b.set_tooltip_text(_("Overwrite Selected Clips with Monitor Clip Range"))    
        self.overwrite_range_b.set_tooltip_text(_("Overwrite Mark In/Mark Out Range with Monitor Clip Range"))    
        self.append_b.set_tooltip_text(_("Append Monitor Clip Range"))    

        self.undo_b.set_tooltip_text(_("Undo"))    
        self.redo_b.set_tooltip_text(_("Redo"))

        self.play_b.set_tooltip_text(_("Play"))
        self.stop_b.set_tooltip_text(_("Stop"))
        self.prev_b.set_tooltip_text(_("Previous frame"))
        self.next_b.set_tooltip_text(_("Next frame"))

        self.ff_b.set_tooltip_text(_("Fast Forward"))
        self.rew_b.set_tooltip_text(_("Rewind"))

        self.mark_in_b.set_tooltip_text(_("Set Mark In"))
        self.mark_out_b.set_tooltip_text(_("Set Mark Out"))
        self.marks_clear_b.set_tooltip_text(_("Clear Marks"))
        self.to_mark_in_b.set_tooltip_text(_("Go to Mark In"))
        self.to_mark_out_b.set_tooltip_text(_("Go to Mark Out"))

        self.view_mode_select.set_tooltip_text(_("Select view mode: Program Video/Vectorscope/RGBParade"))
        
        self.tc.widget.set_tooltip_text(_("Monitor program current frame timecode"))
        self.monitor_source.set_tooltip_text(_("Current Monitor program name"))
        self.mark_in_entry.set_tooltip_text(_("Monitor program Mark In timecode"))
        self.mark_out_entry.set_tooltip_text(_("Monitor program Mark Out timecode"))
        self.length_entry.set_tooltip_text(_("Monitor program selected range length"))
    
        self.pos_bar.widget.set_tooltip_text(_("Monitor program current position"))
        
        self.sequence_editor_b.set_tooltip_text(_("Display Current Sequence on Timeline"))
        self.clip_editor_b.set_tooltip_text(_("Display Monitor Clip"))

        self.open_project_b.set_tooltip_text(_("Open Project File"))
        self.new_project_b.set_tooltip_text(_("Open New Project"))

    def _handle_mode_button_press(self, widget):
        # We get two "clicked" events per mode toggle, send through only the one
        # from the activated button
        if ((self.insert_move_b.get_active() == True) 
            and (widget == self.insert_move_b)):
            editevent.insert_move_mode_pressed()

        if ((self.one_roll_trim_b.get_active() == True) 
            and (widget == self.one_roll_trim_b)):
            editevent.oneroll_trim_mode_pressed()
            
        if ((self.tworoll_trim_b.get_active() == True) 
            and (widget == self.tworoll_trim_b)):
            editevent.tworoll_trim_mode_pressed()

        if ((self.overwrite_move_b.get_active() == True) 
            and (widget == self.overwrite_move_b)):
            editevent.overwrite_move_mode_pressed()

    def _get_buttons_panel(self, btns_count, btn_width=BUTTON_WIDTH):
        # Mode buttons panel
        panel = gtk.HBox(True, 0)
        panel.set_size_request(btns_count * btn_width, BUTTON_HEIGHT)
        return panel
