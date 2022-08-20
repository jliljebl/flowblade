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

from gi.repository import Gtk
from gi.repository import Gdk

import app
import appconsts
import audiomonitoring
import audiosync
import batchrendering
import boxmove
import clipeffectseditor
import clipmenuaction
import compositeeditor
import containerclip
import dialogs
import dialogutils
import diskcachemanagement
import dnd
import editevent
import editorlayout
import editorpersistance
import editorstate
import exporting
import glassbuttons
import gmic
import gui
import guicomponents
import guiutils
import jobs
import keyevents
import medialinker
import medialog
import mediaplugin
import menuactions
import middlebar
import modesetting
import monitorevent
import monitorwidget
import respaths
import render
import rendergui
import panels
import patternproducer
from positionbar import PositionBar
import preferenceswindow
import projectaction
import projectaddmediafolder
import projectinfogui
import proxyediting
import scripttool
import shortcuts
import titler
import tlineaction
import tlinerender
import tlinewidgets
import trackaction
import updater
import undo
import workflow

# GUI min size params, these have probably no effect on layout.
MEDIA_MANAGER_WIDTH = 110 # This in paned container on small screens, has no effect on whole window layout. 
MONITOR_AREA_WIDTH = appconsts.MONITOR_AREA_WIDTH

DARK_BG_COLOR = (0.223, 0.247, 0.247, 1.0)

# Cursors
OVERWRITE_CURSOR = None
OVERWRITE_BOX_CURSOR = None
INSERTMOVE_CURSOR = None
ONEROLL_CURSOR = None
ONEROLL_NO_EDIT_CURSOR = None
TWOROLL_CURSOR = None
TWOROLL_NO_EDIT_CURSOR = None
SLIDE_CURSOR = None
SLIDE_NO_EDIT_CURSOR = None
MULTIMOVE_CURSOR = None
ONEROLL_RIPPLE_CURSOR = None
CUT_CURSOR = None
KF_TOOL_CURSOR = None
MULTI_TRIM_CURSOR = None

ONEROLL_TOOL = None
OVERWRITE_TOOL = None

def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(Gtk.ReliefStyle.NONE)

def _toggle_image_switch(widget, icons):
    not_pressed, pressed = icons
    if widget.get_active() == True:
        widget.set_image(pressed)
    else:
        widget.set_image(not_pressed)


class EditorWindow:

    def __init__(self):

        self._init_cursors()

        # Create window(s)
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
        self.window.set_border_width(5)

        self.window2 = None
        if editorpersistance.prefs.global_layout != appconsts.SINGLE_WINDOW:
            self.window2 = Gtk.Window(Gtk.WindowType.TOPLEVEL)
            self.window2.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
            self.window2.set_border_width(5)
            self.window2.connect("delete-event", lambda w, e:app.shutdown())

        # To ask confirmation for shutdown
        self.window.connect("delete-event", lambda w, e:app.shutdown())

        # Player consumer has to be stopped and started when window resized
        self.window.connect("window-state-event", lambda w, e:updater.refresh_player(e))

        # Init application main menu.
        self.ui = Gtk.UIManager()
        self._init_app_menu(self.ui)

        # Create all panels and gui components.
        self._init_gui_components()
        
        # Create timeline comnponents and panels.
        self._init_tline()

        # Init panels and frames needed to be able to move panels around.
        self._init_panels_and_frames()

        # Build layout and put it in a single pane.
        pane = self._get_app_pane()

        # Tooltips.
        self._add_tool_tips()

        # Set view menu initial state.
        self._init_view_menu(self.ui.get_widget('/MenuBar/ViewMenu'))

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade")

        # Maximize if it seems that we exited maximized, else set size
        w, h = editorpersistance.prefs.exit_allocation
        if w != 0: # non-existing prefs file causes w and h to be 0
            if (float(w) / editorstate.SCREEN_WIDTH > 0.95) and (float(h) / editorstate.SCREEN_HEIGHT > 0.95):
                self.window.maximize()
            else:
                self.window.resize(w, h)
                self.window.set_position(Gtk.WindowPosition.CENTER)
        else:
            self.window.set_position(Gtk.WindowPosition.CENTER)

        # Show window and all of its components
        self.window.show_all()

        # Show Monitor Window in two window mode
        if editorpersistance.prefs.global_layout != appconsts.SINGLE_WINDOW:
            pane2 = Gtk.VBox(False, 1)
            pane2.pack_start(self.top_row_window_2, False, False, 0)
            pane2.pack_start(self.monitor_frame, True, True, 0)

            # Set pane and show window
            self.window2.add(pane2)
            self.window2.set_title("Flowblade")

            # Maximize if it seems that we exited maximized, else set size
            w, h, x, y = editorpersistance.prefs.exit_allocation_window_2

            if w != 0: # non-existing prefs file causes w and h to be 0
                if (float(w) / editorstate.SCREEN_WIDTH > 0.95) and (float(h) / editorstate.SCREEN_HEIGHT > 0.95):
                    self.window2.maximize()
                else:
                    self.window2.resize(w, h)

            self.window2.move(x, y)
            self.window2.show_all()

        # Set paned positions
        bin_w = editorpersistance.prefs.mm_paned_position
        if bin_w < MEDIA_MANAGER_WIDTH + 2:
            bin_w = 0

        if editorlayout.top_level_project_panel() == False:
            self.mm_paned.set_position(bin_w)

        self.top_paned.set_position(editorpersistance.prefs.top_paned_position)
        self.app_v_paned.set_position(editorpersistance.prefs.app_v_paned_position)

    def _get_app_pane(self): 
        # VPaned top row / timeline
        self.app_v_paned = Gtk.VPaned()
        self.app_v_paned.pack1(self.top_row_hbox, resize=False, shrink=False)
        self.app_v_paned.pack2(self.tline_pane, resize=True, shrink=False)

        # self.app_h_box is used to implement position PANEL_PLACEMENT_LEFT_COLUMN.
        self.app_h_box = Gtk.HBox(False, 0)
        self.app_h_box.pack_start(self.left_column_frame, False, False, 0)
        self.app_h_box.pack_start(self.app_v_paned, True, True, 0)

        # Menu box
        self.menubar.set_margin_bottom(4)
        self.menubar.set_name("lighter-bg-widget")

        menubar_box =  Gtk.HBox(False, 0)
        if editorstate.screen_size_small_width() == False:
            menubar_box.pack_start(guiutils.get_right_justified_box([self.menubar]), False, False, 0)
            menubar_box.pack_start(Gtk.Label(), True, True, 0)
        else:
            menubar_box.pack_start(self.menubar, False, False, 0)

        monitor_source_box = Gtk.HBox(False, 0)
        monitor_source_box.pack_start(Gtk.Label(), True, True, 0)
        monitor_source_box.pack_start(self.monitor_tc_info.monitor_source, False, False, 0)
        monitor_source_box.pack_start(self.monitor_tc_info.monitor_tc, False, False, 0)
        monitor_source_box.pack_start(Gtk.Label(), True, True, 0)

        fullscreen_icon = guiutils.get_cairo_image("fullscreen")
        fullscreen_exit_icon = guiutils.get_cairo_image("fullscreen_exit")
        if editorpersistance.prefs.double_track_hights == False:
            self.fullscreen_press = guicomponents.PressLaunch(menuactions.toggle_fullscreen, fullscreen_icon, 20, 12)
        else:
            self.fullscreen_press = guicomponents.PressLaunch(menuactions.toggle_fullscreen, fullscreen_icon, 40, 24)
            self.fullscreen_press.surface_x = 12
            self.fullscreen_press.surface_y = 13

        self.fullscreen_press.widget.set_margin_top(1)
        self.fullscreen_press.widget.set_tooltip_text(_("Fullscreen - F11"))
        # Used in menuactions.toggle_fullscreen to switch image
        self.fullscreen_press.fullscreen_icon = fullscreen_icon
        self.fullscreen_press.fullscreen_exit_icon = fullscreen_exit_icon

        icon_2 = guiutils.get_cairo_image("layout")
        if editorpersistance.prefs.double_track_hights == False:
            layout_press = guicomponents.PressLaunch(editorlayout.show_layout_press_menu, icon_2, 24, 12)
        else:
            layout_press = guicomponents.PressLaunch(editorlayout.show_layout_press_menu, icon_2, 48, 24)
            layout_press.surface_y = 13
            
        layout_press.widget.set_margin_top(1)
        layout_press.widget.set_tooltip_text(_("Layouts"))
        layout_press.connect_launched_menu(editorlayout._top_bar_button_menu)
        
        tline_info_box = Gtk.HBox(False, 0)
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            tline_info_box.pack_start(self.tools_buttons.widget, False, False, 0)
            tline_info_box.pack_start(guiutils.pad_label(8,2), False, False, 0)
            tline_info_box.pack_start(self.fullscreen_press.widget, False, False, 0)
            if editorstate.SCREEN_WIDTH > 1678:
                tline_info_box.pack_start(guiutils.pad_label(6,2), False, False, 0)
                tline_info_box.pack_start(layout_press.widget, False, False, 0)

        tline_info_box.pack_start(Gtk.Label(), True, True, 0)
        tline_info_box.pack_start(self.monitor_tc_info.widget, False, False, 0)
        guiutils.set_margins(tline_info_box, 0, 0, 0, 10)
        
        if editorstate.screen_size_small_width() == False:
            menu_vbox = Gtk.HBox(True, 0)
        else:
            menu_vbox = Gtk.HBox(False, 0) # small screens can't fit 3 equal sized panels here

        menu_vbox.pack_start(menubar_box, True, True, 0)

        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            if editorstate.screen_size_small_width() == False:
                menu_vbox.pack_start(monitor_source_box, True, True, 0)
            else:
                menu_vbox.pack_start(guiutils.pad_label(24, 2), False, False, 0)
                menu_vbox.pack_start(monitor_source_box, False, False, 0)
                menu_vbox.pack_start(guiutils.pad_label(40, 2), False, False, 0)
            menu_vbox.pack_start(tline_info_box, True, True, 0)
            
            if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
                menu_vbox.override_background_color(Gtk.StateFlags.NORMAL, gui.get_mid_neutral_color())
        else:
            menubar_box.pack_start(self.tools_buttons.widget, False, False, 0)
            menubar_box.pack_start(guiutils.pad_label(8, 2), False, False, 0)
            menubar_box.pack_start(self.fullscreen_press.widget, False, False, 0)
            
            self.top_row_window_2 = Gtk.HBox(False, 0)
            self.top_row_window_2.pack_start(monitor_source_box, False, False, 0)
            self.top_row_window_2.pack_start(Gtk.Label(), True, True, 0)
            self.top_row_window_2.pack_start(tline_info_box, False, False, 0)

        # Pane
        pane = Gtk.VBox(False, 1)
        pane.pack_start(menu_vbox, False, True, 0)
        pane.pack_start(self.app_h_box, True, True, 0)
        return pane

    def _init_gui_components(self):        
        # Disable Blender and G'Mic container clip menu items if not available.
        if containerclip.blender_available() == False:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateBlenderContainerItem').set_sensitive(False)
        if gmic.gmic_available() == False:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateGMicContainerItem').set_sensitive(False)
            
        # Media panel
        self.bin_list_view = guicomponents.BinTreeView(
                                        projectaction.bin_selection_changed,
                                        projectaction.bin_name_edited,
                                        projectaction.bins_panel_popup_requested)
        dnd.connect_bin_tree_view(self.bin_list_view.treeview, projectaction.move_files_to_bin)
        self.bin_list_view.set_property("can-focus",  True)


        self.bins_panel = panels.get_bins_tree_panel(self.bin_list_view, projectaction.bin_hambuger_pressed, projectaction.bin_popup_menu)
        self.bins_panel.set_size_request(MEDIA_MANAGER_WIDTH, 10) # this component is always expanded, so 10 for minimum size ok

        self.media_list_view = guicomponents.MediaPanel(projectaction.media_file_menu_item_selected,
                                                        projectaction.media_panel_double_click,
                                                        projectaction.media_panel_popup_requested)
        view = Gtk.Viewport()
        view.add(self.media_list_view.widget)
        view.set_shadow_type(Gtk.ShadowType.NONE)

        self.media_scroll_window = Gtk.ScrolledWindow()
        self.media_scroll_window.add(view)
        self.media_scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.media_scroll_window.set_size_request(guicomponents.MEDIA_OBJECT_WIDGET_WIDTH * 2 + 15, guicomponents.MEDIA_OBJECT_WIDGET_HEIGHT)
        self.media_scroll_window.show_all()

        media_panel, bin_info = panels.get_media_files_panel(
                                    self.media_scroll_window,
                                    lambda w,e: projectaction.add_media_files(),
                                    lambda w,e: projectaction.delete_media_files(),
                                    projectaction.columns_count_launch_pressed,
                                    projectaction.hamburger_pressed,  # lambda w,e: proxyediting.create_proxy_files_pressed(),
                                    projectaction.media_filtering_select_pressed,
                                    projectaction.hamburger_popup_menu)

        self.media_panel = media_panel
        self.media_panel.set_name("darker-bg-widget")
        self.bin_info = bin_info

        # Smallest screens always get bins in same panel as media, others get top level project panel if selected
        if editorlayout.top_level_project_panel() == True:
            self.mm_paned = Gtk.HBox()
            self.mm_paned.add(media_panel)

        else:
            self.mm_paned = Gtk.HPaned()
            guiutils.set_margins(self.bins_panel, 6, 6, 8, 0)
            self.mm_paned.pack1(self.bins_panel, resize=True, shrink=True)
            self.mm_paned.pack2(media_panel, resize=True, shrink=False)

        # Effects edit panel
        info_row = clipeffectseditor.get_clip_effects_editor_info_row()    
        effects_editor_panel = guiutils.set_margins(clipeffectseditor.widgets.value_edit_frame, 4, 0, 4, 0)

        effects_vbox = Gtk.VBox()
        effects_vbox.pack_start(effects_editor_panel, True, True, 0)
        effects_vbox.pack_start(info_row, False, False, 0)

        if not(editorstate.SCREEN_HEIGHT < 1023):
            self.effects_panel = guiutils.set_margins(effects_vbox, 8, 0, 7, 2)
        else:
            self.effects_panel = effects_vbox

        # Effects select panel
        effect_select_panel, effect_select_list_view, effect_select_combo_box  = panels.get_effect_selection_panel(clipeffectseditor.effect_select_row_double_clicked)
        self.effect_select_panel = effect_select_panel
        self.effect_select_list_view = effect_select_list_view
        self.effect_select_combo_box = effect_select_combo_box
        dnd.connect_effects_select_tree_view(self.effect_select_list_view.treeview)

        # Compositors panel
        action_row = compositeeditor.get_compositor_clip_panel()
        compositor_editor_panel = guiutils.set_margins(compositeeditor.widgets.value_edit_frame, 0, 0, 4, 0)

        compositors_hbox = Gtk.HBox()
        compositors_hbox.pack_start(compositor_editor_panel, True, True, 0)

        compositors_vbox = Gtk.VBox()
        compositors_vbox.pack_start(compositors_hbox, True, True, 0)
        compositors_vbox.pack_start(action_row, False, False, 0)

        compositors_panel = guiutils.set_margins(compositors_vbox, 2, 2, 2, 2)

        # Media Plugins
        hamburger_row = mediaplugin.get_plugin_hamburger_row()
        buttons_row = guiutils.set_margins(mediaplugin.get_plugin_buttons_row(),4, 4, 4, 4)
        mediaplugins_editor_panel = guiutils.set_margins(mediaplugin.widgets.value_edit_frame, 0, 0, 8, 4)
        
        mediaplugins_hbox = Gtk.HBox()
        mediaplugins_hbox.pack_start(mediaplugins_editor_panel, True, True, 0)

        mediaplugins_vbox = Gtk.VBox()
        mediaplugins_vbox.pack_start(mediaplugins_hbox, True, True, 0)
        mediaplugins_vbox.pack_start(buttons_row, False, False, 0)
        mediaplugins_vbox.pack_start(hamburger_row, False, False, 0)

        mediaplugins_panel = guiutils.set_margins(mediaplugins_vbox, 2, 2, 2, 2)

        # Multi empty panel
        multi_empty_vbox = Gtk.VBox(False, 0)
        multi_empty_vbox.pack_start(Gtk.Label(), True, True, 0)
        no_target = Gtk.Label(label=_("No Edit Target."))
        no_target.set_sensitive(False)
        multi_empty_vbox.pack_start(no_target, False, False, 0)
        multi_empty_vbox.pack_start(Gtk.Label(), True, True, 0)
    
        # Multi edit panel
        self.edit_multi = guicomponents.EditMultiStack()
        self.edit_multi.add_named(multi_empty_vbox, appconsts.EDIT_MULTI_EMPTY)
        self.edit_multi.add_named(self.effects_panel, appconsts.EDIT_MULTI_FILTERS)
        self.edit_multi.add_named(compositors_panel, appconsts.EDIT_MULTI_COMPOSITORS)
        self.edit_multi.add_named(mediaplugins_panel, appconsts.EDIT_MULTI_PLUGINS)
        self.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_EMPTY)
        
        # Render panel
        try:
            render.create_widgets()
            render_panel_left = rendergui.get_render_panel_left(render.widgets)
        except IndexError:
            print("No rendering options found")
            render_panel_left = None

        # 'None' here means that no possible rendering options were available
        # and creating panel failed. Inform user of this and hide render GUI
        if render_panel_left == None:
            render_hbox = Gtk.VBox(False, 5)
            render_hbox.pack_start(Gtk.Label(label="Rendering disabled."), False, False, 0)
            render_hbox.pack_start(Gtk.Label(label="No available rendering options found."), False, False, 0)
            render_hbox.pack_start(Gtk.Label(label="See Help->Environment->Render Options for details."), False, False, 0)
            render_hbox.pack_start(Gtk.Label(label="Install codecs to make rendering available."), False, False, 0)
            render_hbox.pack_start(Gtk.Label(label=" "), True, True, 0)
        else: # all is good
            render_panel_right = rendergui.get_render_panel_right(render.widgets,
                                                                  lambda w,e: projectaction.do_rendering(),
                                                                  lambda w,e: projectaction.add_to_render_queue())
            render_hbox = Gtk.HBox(False, 5)
            render_hbox.pack_start(render_panel_left, True, True, 0)
            render_hbox.pack_start(render_panel_right, True, True, 0)

        self.render_panel = guiutils.set_margins(render_hbox, 2, 6, 8, 6)

        # Range Log panel
        media_log_events_list_view = medialog.get_media_log_list_view()
        events_panel = medialog.get_media_log_events_panel(media_log_events_list_view)

        media_log_vbox = Gtk.HBox()
        media_log_vbox.pack_start(events_panel, True, True, 0)

        self.media_log_panel = guiutils.set_margins(media_log_vbox, 6, 6, 6, 6)
        self.media_log_events_list_view = media_log_events_list_view

        # Sequence list
        self.sequence_list_view = guicomponents.SequenceListView(   projectaction.sequence_name_edited,
                                                                    projectaction.sequence_panel_popup_requested,
                                                                    projectaction.sequence_list_double_click_done)
        seq_panel = panels.get_sequences_panel(self.sequence_list_view, projectaction.sequences_hamburger_pressed, projectaction.sequence_popup_menu)

        # Jobs panel
        jobs.create_jobs_list_view()
        jobs_panel = jobs.get_jobs_panel()
        jobs_hbox = Gtk.HBox()
        jobs_hbox.pack_start(jobs_panel, True, True, 0)
        self.jobs_pane = guiutils.set_margins(jobs_hbox, 6, 6, 6, 6)

        # Project panel
        if editorlayout.top_level_project_panel() == True:
            # Project info
            project_info_panel = projectinfogui.get_top_level_project_info_panel()
            top_project_vbox = Gtk.VBox()
            top_project_vbox.pack_start(project_info_panel, False, False, 0)
            top_project_vbox.pack_start(self.bins_panel, True, True, 0)
            top_project_vbox.pack_start(seq_panel, True, True, 0)
            self.top_project_panel = guiutils.set_margins(top_project_vbox, 0, 0, 0, 4)
            self.project_panel = None
        else:
            # Notebook project panel for smallest screens
            # Project info
            project_info_panel = projectinfogui.get_project_info_panel()

            # Project vbox and panel
            project_vbox = Gtk.VBox()
            project_vbox.pack_start(project_info_panel, False, True, 0)
            project_vbox.pack_start(seq_panel, True, True, 0)
            self.project_panel = guiutils.set_margins(project_vbox, 0, 2, 6, 2)
            self.top_project_panel = None 
        
        # Position bar and decorative frame  for it
        self.pos_bar = PositionBar()
        pos_bar_frame = Gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pos_bar_frame.set_margin_top(4)
        pos_bar_frame.set_margin_bottom(4)
        pos_bar_frame.set_margin_left(6)

        # Play buttons row
        self._create_monitor_buttons()
        self._create_monitor_row_widgets()

        self.player_buttons = glassbuttons.PlayerButtons()
        if (editorpersistance.prefs.play_pause == True):
            if (editorpersistance.prefs.timeline_start_end is True):
            # ------------------------------ timeline_start_end_button
                tooltips = [_("Start - Home key"), _("End - End key"),_("Prev Frame - Arrow Left"), _("Next Frame - Arrow Right"), _("Play/Pause- Space"), _("Mark In - I"), _("Mark Out - O"), _("Clear Marks"), _("To Mark In"), _("To Mark Out")]
            else:
                tooltips = [_("Prev Frame - Arrow Left"), _("Next Frame - Arrow Right"), _("Play/Pause - Space"), _("Mark In - I"), _("Mark Out - O"), _("Clear Marks"), _("To Mark In"), _("To Mark Out")]
        else:
            if (editorpersistance.prefs.timeline_start_end is True):
                tooltips = [_("Start - Home key"), _("End - End key"),_("Prev Frame - Arrow Left"), _("Next Frame - Arrow Right"), _("Play - Space"), _("Stop - Space"), _("Mark In - I"), _("Mark Out - O"), _("Clear Marks"), _("To Mark In"), _("To Mark Out")]
            else:
                tooltips = [_("Prev Frame - Arrow Left"), _("Next Frame - Arrow Right"), _("Play - Space"), _("Stop - Space"), _("Mark In - I"), _("Mark Out - O"), _("Clear Marks"), _("To Mark In"), _("To Mark Out")]
            # ------------------------------End of timeline_start_end_button
        tooltip_runner = glassbuttons.TooltipRunner(self.player_buttons, tooltips)
        if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
            self.player_buttons.no_decorations = True

        self.view_mode_select = guicomponents.get_monitor_view_select_combo(lambda w, e: tlineaction.view_mode_menu_lauched(w, e))
        self.view_mode_select.set_pixbuf(0)
        self.view_mode_select.connect_launched_menu(guicomponents.monitor_menu)
        self.view_mode_select.widget.set_margin_right(10)
        self.trim_view_select = guicomponents.get_trim_view_select_combo(lambda w, e: monitorevent.trim_view_menu_launched(w, e))
        self.trim_view_select.connect_launched_menu(guicomponents.trim_view_menu)

        player_buttons_row = Gtk.HBox(False, 0)
        player_buttons_row.pack_start(self.monitor_switch.widget, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(self.player_buttons.widget, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(self.trim_view_select.widget, False, False, 0)
        player_buttons_row.pack_start(self.view_mode_select.widget, False, False, 0)
        self.player_buttons_row = player_buttons_row
        
        # Switch / pos bar row
        sw_pos_hbox = Gtk.HBox(False, 1)
        sw_pos_hbox.pack_start(pos_bar_frame, True, True, 0)
        
        # Video display
        monitor_widget = monitorwidget.MonitorWidget()
        self.tline_display = monitor_widget.get_monitor()
        self.monitor_widget = monitor_widget

        dnd.connect_video_monitor(self.tline_display)

        # Monitor
        monitor_vbox = Gtk.VBox(False, 0)
        monitor_vbox.pack_start(monitor_widget.widget, True, True, 0)
        monitor_vbox.pack_start(sw_pos_hbox, False, True, 0)
        monitor_vbox.pack_start(player_buttons_row, False, True, 0)
        monitor_align = guiutils.set_margins(monitor_vbox, 0, 0, 0, 0)

        self.monitor_frame = Gtk.Frame()
        self.monitor_frame.add(monitor_align)
        self.monitor_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        self.monitor_frame.set_size_request(MONITOR_AREA_WIDTH, appconsts.TOP_ROW_HEIGHT)
        
        # Middlebar
        self.edit_buttons_row = self._get_edit_buttons_row()

        self.edit_buttons_frame = Gtk.Frame()
        self.edit_buttons_frame.add(self.edit_buttons_row)
        self.edit_buttons_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        guiutils.set_margins(self.edit_buttons_frame, 1, 0, 0, 0)

        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_GRAY:
            self.edit_buttons_frame.override_background_color(Gtk.StateFlags.NORMAL, gui.get_light_gray_light_color())

        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
            self.edit_buttons_frame.override_background_color(Gtk.StateFlags.NORMAL, gui.get_mid_neutral_color())
            
    def _init_tline(self):
        self.tline_scale = tlinewidgets.TimeLineFrameScale(modesetting.set_default_edit_mode,
                                                           updater.mouse_scroll_zoom)

        self.tline_info = Gtk.HBox()
        info_contents = Gtk.Label()
        self.tline_info.add(info_contents)
        self.tline_info.info_contents = info_contents # this switched and saved as member of its container
        info_h = Gtk.HBox()
        info_h.pack_start(self.tline_info, False, False, 0)
        info_h.pack_start(Gtk.Label(), True, True, 0)
        # Aug-2019 - SvdB - BB - Height doesn't need to be doubled. 1.4x is nicer
        size_adj = 1
        size_x = tlinewidgets.COLUMN_WIDTH - 22 - 22 - 22
        size_y = tlinewidgets.SCALE_HEIGHT
        if editorpersistance.prefs.double_track_hights:
            size_adj = 1.4
            size_x = tlinewidgets.COLUMN_WIDTH - (66*size_adj)

        info_h.set_size_request(size_x, size_y)

        # Aug-2019 - SvdB - BB - add size_adj and width/height as parameter to be able to adjust it for double height
        marker_surface =  guiutils.get_cairo_image("marker")
        markers_launcher = guicomponents.get_markers_menu_launcher(tlineaction.marker_menu_lauch_pressed, marker_surface, 22*size_adj, 22*size_adj)
        markers_launcher.connect_launched_menu(guicomponents.markers_menu)
        
        tracks_launcher_surface = guiutils.get_cairo_image("track_menu_launch")
        tracks_launcher = guicomponents.PressLaunch(trackaction.all_tracks_menu_launch_pressed, tracks_launcher_surface, 22*size_adj, 22*size_adj)
        tracks_launcher.connect_launched_menu(guicomponents.tracks_menu)

        levels_launcher_surface = guiutils.get_cairo_image("audio_levels_menu_launch")
        levels_launcher = guicomponents.PressLaunch(trackaction.audio_levels_menu_launch_pressed, levels_launcher_surface, 22*size_adj, 22*size_adj)
        levels_launcher.connect_launched_menu(guicomponents.levels_menu)

        # Timeline top row
        tline_hbox_1 = Gtk.HBox()
        tline_hbox_1.pack_start(info_h, False, False, 0)
        tline_hbox_1.pack_start(levels_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(tracks_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(markers_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(self.tline_scale.widget, True, True, 0)

        self.tline_hbox_1 = tline_hbox_1

        # Timeline column
        self.tline_column = tlinewidgets.TimeLineColumn(
                            trackaction.track_active_switch_pressed,
                            trackaction.track_center_pressed,
                            trackaction.track_double_click)

        # Timeline editpanel
        self.tline_canvas = tlinewidgets.TimeLineCanvas(
            editevent.tline_canvas_mouse_pressed,
            editevent.tline_canvas_mouse_moved,
            editevent.tline_canvas_mouse_released,
            editevent.tline_canvas_double_click,
            updater.mouse_scroll_zoom,
            self.tline_cursor_leave,
            self.tline_cursor_enter)

        dnd.connect_tline(self.tline_canvas.widget, editevent.tline_effect_drop,
                          editevent.tline_media_drop)

        # Create tool dock if needed
        if editorpersistance.prefs.tools_selection != appconsts.TOOL_SELECTOR_IS_MENU:
            self.tool_dock = workflow.get_tline_tool_dock()
        else:
            self.tool_dock = None

        # Timeline middle row
        tline_hbox_2 = Gtk.HBox()
        tline_hbox_2.pack_start(self.tline_column.widget, False, False, 0)
        tline_hbox_2.pack_start(self.tline_canvas.widget, True, True, 0)
        
        self.tline_hbox_2 = tline_hbox_2
        
        # Timeline renderer row
        self.pad_box = Gtk.HBox()
        self.pad_box.set_size_request(tlinewidgets.COLUMN_WIDTH, tlinewidgets.STRIP_HEIGHT)
        self.tline_render_strip = tlinewidgets.TimeLineRenderingControlStrip()
        self.tline_renderer_hbox = Gtk.HBox()
        self.pad_box.show()
        self.tline_render_strip.widget.show()

        # Comp mode selector
        size_adj = 1
        tds = guiutils.get_cairo_image("top_down")
        tdds = guiutils.get_cairo_image("top_down_auto")
        sas = guiutils.get_cairo_image("standard_auto")
        fta = guiutils.get_cairo_image("full_track_auto")
        surfaces = [tds, tdds, sas, fta]
        comp_mode_launcher = guicomponents.ImageMenuLaunch(projectaction.compositing_mode_menu_launched, surfaces, 22*size_adj, 20)
        comp_mode_launcher.connect_launched_menu(projectaction.compositing_mode_menu)
        comp_mode_launcher.surface_x = 0
        comp_mode_launcher.surface_y = 4
        comp_mode_launcher.widget.set_tooltip_markup(_("Current Sequence Compositing Mode"))
        self.comp_mode_launcher = comp_mode_launcher

        # Tlinerender mode selector
        tro = guiutils.get_cairo_image("tline_render_off")
        tra = guiutils.get_cairo_image("tline_render_auto")
        trr = guiutils.get_cairo_image("tline_render_request")
        surfaces = [tro, tra, trr]
        tline_render_mode_launcher = guicomponents.ImageMenuLaunch(tlinerender.corner_mode_menu_launched, surfaces, 22*size_adj, 20)
        tline_render_mode_launcher.connect_launched_menu(tlinerender.tlinerender_mode_menu)
        tline_render_mode_launcher.surface_x = 0
        tline_render_mode_launcher.surface_y = 4
        tline_render_mode_launcher.widget.set_tooltip_markup(_("Timeline Rendering"))
        self.tline_render_mode_launcher = tline_render_mode_launcher

        # Bottom row filler
        self.left_corner = guicomponents.TimeLineLeftBottom(comp_mode_launcher, tline_render_mode_launcher)
        self.left_corner.widget.set_size_request(tlinewidgets.COLUMN_WIDTH, 20)

        # Timeline scroller
        self.tline_scroller = tlinewidgets.TimeLineScroller(updater.tline_scrolled)

        tline_hbox_3 = Gtk.HBox()
        tline_hbox_3.pack_start(self.left_corner.widget, False, False, 0)
        tline_hbox_3.pack_start(self.tline_scroller, True, True, 0)

        # Timeline vbox
        tline_vbox = Gtk.VBox()
        tline_vbox.pack_start(self.tline_hbox_1, False, False, 0)
        tline_vbox.pack_start(self.tline_hbox_2, True, True, 0)
        tline_vbox.pack_start(self.tline_renderer_hbox, False, False, 0)
        tline_vbox.pack_start(tline_hbox_3, False, False, 0)

        tline_vbox_frame = guiutils.get_panel_etched_frame(tline_vbox)
    
        # Timeline box
        self.tline_box = Gtk.HBox()
        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_LEFT_DOCK:
            self.tline_box.pack_start(self.tool_dock, False, False, 0)
        self.tline_box.pack_end(tline_vbox_frame, True, True, 0)

        # Timeline pane
        self.tline_vpane = Gtk.VBox(False, 1)
        self.tline_vpane.pack_start(self.edit_buttons_frame, False, True, 0)
        self.tline_vpane.pack_start(self.tline_box, True, True, 0)

    def _init_panels_and_frames(self):     
        # Create position panels and frames

        # ---------------------------------------------------------------- TOP ROW
        # -------------- appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT
        # -------------- This special case, it can only self.top_project_panel on None.
        top_project_panel, widget_is_notebook = editorlayout.create_position_widget(self, \
                        appconsts.PANEL_PLACEMENT_TOP_ROW_PROJECT_DEFAULT)
        if top_project_panel != None:
            self.top_project_panel_frame = guiutils.get_panel_etched_frame(top_project_panel)
            guiutils.set_margins(self.top_project_panel_frame, 0, 0, 0, 1)
        else:
            # top_project_panel_frame is an etched frame and we put a non-visible dummy box in.
            # For small screen sizes this frame never gets used.
            self.top_project_panel_frame = guiutils.get_empty_panel_etched_frame()
            
        # -------------- appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT a.k.a Notebook 
        # --------------'this is always noteboof never Gtk.Frame or empty '
        self.notebook, widget_is_notebook = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_TOP_ROW_DEFAULT)
        self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)
        self.notebook_frame = guiutils.get_panel_etched_frame(self.notebook)
        guiutils.set_margins(self.notebook_frame, 0, 0, 0, 1)
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_GRAY:
            self.notebook.override_background_color(Gtk.StateFlags.NORMAL, gui.get_light_gray_light_color())
            
        # -------------- appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT
        # -------------- By default this is empty.
        self.top_right_panel, widget_is_notebook  = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_TOP_ROW_RIGHT)
        if self.top_right_panel != None:
            # We have note or frame with 1-n panels in it.
            self.top_right_frame = guiutils.get_panel_etched_frame(self.top_right_panel)
            guiutils.set_margins(self.top_right_frame, 0, 0, 0, 1)
        else:
            # Position is empty.
            self.top_right_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position 


        # ---------------------------------------------------------------- BOTTOM ROW
        # Horizon box for bottom row GUI elements
        self.tline_pane = Gtk.HBox(False, 0)
                
        # -------------- appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT, by default this is empty
        self.bottom_left_panel, widget_is_notebook  = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_LEFT)
        if self.bottom_left_panel != None:
            self.bottom_left_frame = guiutils.get_panel_etched_frame(self.bottom_left_panel)
            guiutils.set_margins(self.bottom_left_frame, 0, 0, 0, 1)
        else:
            self.bottom_left_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position
        self.tline_pane.pack_start(self.bottom_left_frame, False, False, 0) # self.tline_pane was already created in self._init_tline()
            
        # Put timeline between left and right bottom row panels.
        self.tline_pane.pack_start(self.tline_vpane, True, True, 0)
        
        # -------------- appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, by default this has filter select panel.
        self.bottom_right_panel, widget_is_notebook  = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT)
        if self.bottom_right_panel != None:
            self.bottom_right_frame = guiutils.get_panel_etched_frame(self.bottom_right_panel)
            guiutils.set_margins(self.bottom_right_frame, 0, 0, 0, 1)

        else:
            self.bottom_right_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position.
        self.tline_pane.pack_start(self.bottom_right_frame, False, False, 0) # self.tline_pane was already created in self._init_tline().


        # ---------------------------------------------------------------- LEFT  COLUMN
        self.left_column_panel, widget_is_notebook  = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_LEFT_COLUMN)
        if self.left_column_panel != None:
            self.left_column_frame = guiutils.get_panel_etched_frame(self.left_column_panel)
            guiutils.set_margins(self.left_column_frame, 0, 0, 0, 1)

        else:
            self.left_column_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position.

        # Top row paned
        self.top_paned = Gtk.HPaned()
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            self.top_paned.pack1(self.notebook_frame , resize=True, shrink=False)
            self.top_paned.pack2(self.monitor_frame, resize=True, shrink=False)
        else:
            self.top_paned.pack1(self.mm_paned, resize=True, shrink=False)
            self.top_paned.pack2(self.notebook_frame, resize=True, shrink=False)

        # Top row
        self.top_row_hbox = Gtk.HBox(False, 0)
        self.top_row_hbox.pack_start(self.top_project_panel_frame, False, False, 0)
        self.top_row_hbox.pack_start(self.top_paned, True, True, 0)
        self.top_row_hbox.pack_end(self.top_right_frame, False, False, 0)
        self.top_row_hbox.pack_end(audiomonitoring.get_master_meter(), False, False, 0)

        editorlayout.apply_tabs_positions()
        
    def _init_cursors(self):
        # Read cursors
        global INSERTMOVE_CURSOR, OVERWRITE_CURSOR, TWOROLL_CURSOR, ONEROLL_CURSOR, \
        ONEROLL_NO_EDIT_CURSOR, TWOROLL_NO_EDIT_CURSOR, SLIDE_CURSOR, SLIDE_NO_EDIT_CURSOR, \
        MULTIMOVE_CURSOR, MULTIMOVE_NO_EDIT_CURSOR, ONEROLL_RIPPLE_CURSOR, ONEROLL_TOOL, \
        OVERWRITE_BOX_CURSOR, OVERWRITE_TOOL, CUT_CURSOR, KF_TOOL_CURSOR, MULTI_TRIM_CURSOR

        # Aug-2019 - SvdB - BB
        INSERTMOVE_CURSOR = guiutils.get_cairo_image("insertmove_cursor")
        OVERWRITE_CURSOR = guiutils.get_cairo_image("overwrite_cursor")
        OVERWRITE_BOX_CURSOR = guiutils.get_cairo_image("overwrite_cursor_box")
        TWOROLL_CURSOR = guiutils.get_cairo_image("tworoll_cursor")
        SLIDE_CURSOR = guiutils.get_cairo_image("slide_cursor")
        ONEROLL_CURSOR = guiutils.get_cairo_image("oneroll_cursor")
        ONEROLL_NO_EDIT_CURSOR = guiutils.get_cairo_image("oneroll_noedit_cursor")
        TWOROLL_NO_EDIT_CURSOR = guiutils.get_cairo_image("tworoll_noedit_cursor")
        SLIDE_NO_EDIT_CURSOR = guiutils.get_cairo_image("slide_noedit_cursor")
        MULTIMOVE_CURSOR = guiutils.get_cairo_image("multimove_cursor")
        MULTIMOVE_NO_EDIT_CURSOR = guiutils.get_cairo_image("multimove_cursor")
        ONEROLL_TOOL = guiutils.get_cairo_image("oneroll_tool")
        ONEROLL_RIPPLE_CURSOR = guiutils.get_cairo_image("oneroll_cursor_ripple")
        OVERWRITE_TOOL = guiutils.get_cairo_image("overwrite_tool")
        CUT_CURSOR = guiutils.get_cairo_image("cut_cursor")
        KF_TOOL_CURSOR = guiutils.get_cairo_image("kftool_cursor")
        MULTI_TRIM_CURSOR = guiutils.get_cairo_image("multitrim_cursor")

        # Context cursors
        self.context_cursors = {appconsts.POINTER_CONTEXT_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 3, 7),
                                appconsts.POINTER_CONTEXT_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 14, 7),
                                appconsts.POINTER_CONTEXT_TRIM_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_TRIM_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_right.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_BOX_SIDEWAYS:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_MOVE:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_MULTI_ROLL:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "tworoll_cursor.png"), 11, 9),
                                appconsts.POINTER_CONTEXT_MULTI_SLIP:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "slide_cursor.png"), 9, 9)}

    def _init_app_menu(self, ui):

        # Get customizable shortcuts that are displayed in menu
        root = shortcuts.get_root()
        resync_shortcut = shortcuts.get_shortcut_gtk_code(root, "resync")
        clear_filters_shortcut = shortcuts.get_shortcut_gtk_code(root, "clear_filters")
        sync_all_shortcut = shortcuts.get_shortcut_gtk_code(root, "sync_all")
        
        # Build menubar
        # Menubar build resources
        menu_actions = [
            ('FileMenu', None, _('_File')),
            ('New', None, _('_New...'), '<control>N', None, lambda a:projectaction.new_project()),
            ('Open', None, _('_Open...'), '<control>O', None, lambda a:projectaction.load_project()),
            ('OpenRecent', None, _('Open Recent')),
            ('Save', None, _('_Save'), '<control>S', None, lambda a:projectaction.save_project()),
            ('Save As', None, _('_Save As...'), None, None, lambda a:projectaction.save_project_as()),
            ('SaveSnapshot', None, _('Save Backup Snapshot...'), None, None, lambda a:projectaction.save_backup_snapshot()),
            ('ExportMenu', None, _('Export')),
            ('ExportMeltXML', None, _('MLT XML'), None, None, lambda a:exporting.MELT_XML_export()),
            ('ExportEDL', None, _('EDL'), None, None, lambda a:exporting.EDL_export()),
            ('ExportScreenshot', None, _('Current Frame'), None, None, lambda a:exporting.screenshot_export()),
            ('ExportToArdour', None, _('Current Sequence Audio As Ardour Session'), None, None, lambda a:exporting.ardour_export()),
            ('Close', None, _('_Close'), None, None, lambda a:projectaction.close_project()),
            ('Quit', None, _('_Quit'), '<control>Q', None, lambda a:app.shutdown()),
            ('EditMenu', None, _('_Edit')),
            ('Undo', None, _('_Undo'), '<control>Z', None, undo.do_undo_and_repaint),
            ('Redo', None, _('_Redo'), '<control>Y', None, undo.do_redo_and_repaint),
            ('Copy', None, _('Copy'), '<control>C', None, lambda a:keyevents.copy_action()),
            ('Paste', None, _('Paste'), '<control>V', None, lambda a:keyevents.paste_action()),
            ('PasteFilters', None, _('Paste Filters / Properties'), '<control><alt>V', None, lambda a:tlineaction.do_timeline_filters_paste()),
            ('AddFromMonitor', None, _('Add Monitor Clip')),
            ('AppendClip', None, _('Append'), None, None, lambda a:tlineaction.append_button_pressed()),
            ('InsertClip', None, _('Insert'), None, None, lambda a:tlineaction.insert_button_pressed()),
            ('ThreepointOverWriteClip', None, _('Three Point Overwrite'), None, None, lambda a:tlineaction.three_point_overwrite_pressed()),
            ('RangeOverWriteClip', None, _('Range Overwrite'), None, None, lambda a:tlineaction.range_overwrite_pressed()),
            ('CutClip', None, _('Cut Clip'), None, None, lambda a:tlineaction.cut_pressed()),
            ('SequenceSplit', None, _('Split to new Sequence at Playhead Position'), None, None, lambda a:tlineaction.sequence_split_pressed()),
            ('DeleteClip', None, _('Lift'), None, None, lambda a:tlineaction.lift_button_pressed()),
            ('SpliceOutClip', None, _('Splice Out'), None, None, lambda a:tlineaction.splice_out_button_pressed()),
            ('ResyncSelected', None, _('Resync'),  resync_shortcut, None, lambda a:tlineaction.resync_button_pressed()),
            ('SetSyncParent', None, _('Set Sync Parent'), None, None, lambda a:_this_is_not_used()),
            ('AddTransition', None, _('Add Single Track Transition'), None, None, lambda a:tlineaction.add_transition_menu_item_selected()),
            ('AddFade', None, _('Add Single Track Fade'), None, None, lambda a:tlineaction.add_fade_menu_item_selected()),
            ('ClearFilters', None, _('Clear Filters'), clear_filters_shortcut, None, lambda a:clipmenuaction.clear_filters()),
            ('Timeline', None, _('Timeline')),
            ('FiltersOff', None, _('All Filters Off'), None, None, lambda a:tlineaction.all_filters_off()),
            ('FiltersOn', None, _('All Filters On'), None, None, lambda a:tlineaction.all_filters_on()),
            ('SyncCompositors', None, _('Sync All Compositors'), sync_all_shortcut, None, lambda a:tlineaction.sync_all_compositors()),
            ('ChangeSequenceTracks', None, _('Change Sequence Tracks Count...'), None, None, lambda a:projectaction.change_sequence_track_count()),
            ('Watermark', None, _('Watermark...'), None, None, lambda a:menuactions.edit_watermark()),
            ('DiskCacheManager', None, _('Disk Cache Manager'), None, None, lambda a:diskcachemanagement.show_disk_management_dialog()),
            ('ProfilesManager', None, _('Profiles Manager'), None, None, lambda a:menuactions.profiles_manager()),
            ('Preferences', None, _('Preferences'), None, None, lambda a:preferenceswindow.preferences_dialog()),
            ('ViewMenu', None, _('View')),
            ('FullScreen', None, _('Fullscreen'), 'F11', None, lambda a:menuactions.toggle_fullscreen()),
            ('ProjectMenu', None, _('Project')),
            ('AddMediaClip', None, _('Add Video, Audio or Image...'), None, None, lambda a: projectaction.add_media_files()),
            ('AddMediaFolder', None, _('Add Media Folder...'), None, None, lambda a: projectaddmediafolder.show_add_media_folder_dialog()),
            ('AddImageSequence', None, _('Add Image Sequence...'), None, None, lambda a:projectaction.add_image_sequence()),
            ('CreateColorClip', None, _('Create Color Clip...'), None, None, lambda a:patternproducer.create_color_clip()),
            ('BinMenu', None, _('Bin')),
            ('AddBin', None, _('Add Bin'), None, None, lambda a:projectaction.add_new_bin()),
            ('DeleteBin', None, _('Delete Selected Bin'), None, None, lambda a:projectaction.delete_selected_bin()),
            ('SequenceMenu', None, _('Sequence')),
            ('AddSequence', None, _('Add New Sequence'), None, None, lambda a:projectaction.add_new_sequence()),
            ('EditSequence', None, _('Edit Selected Sequence'), None, None, lambda a:projectaction.change_edit_sequence()),
            ('DeleteSequence', None, _('Delete Selected Sequence'), None, None, lambda a:projectaction.delete_selected_sequence()),
            ('CompositingModeMenu', None, _('Compositing Mode')),
            ('TimelineRenderingMenu', None, _('Timeline Rendering')),
            ('AddMediaPlugin', None, _('Add Generator...'), None, None, lambda a:mediaplugin.show_add_media_plugin_window()),
            ('LoadMediaPluginScript', None, _('Load Media Plugin Script...'), None, None,lambda w: containerclip.create_fluxity_media_item()),
            ('CreateSelectionCompound', None, _('From Selected Clips'), None, None, lambda a:projectaction.create_selection_compound_clip()),
            ('CreateSequenceCompound', None, _('From Current Sequence'), None, None, lambda a:projectaction.create_sequence_compound_clip()),
            ('CreateSequenceFreezeCompound', None, _('From Current Sequence With Freeze Frame at Playhead Position'), None, None, lambda a:projectaction.create_sequence_freeze_frame_compound_clip()),
            ('AudioSyncCompoundClip', None, _('Audio Sync Merge Clip From 2 Media Items '), None, None, lambda a:audiosync.create_audio_sync_compound_clip()),
            ('ImportProjectMedia', None, _('Import Media From Project...'), None, None, lambda a:projectaction.import_project_media()),
            ('ContainerClipsMenu', None, _('Create Container Clip')),
            ('CreateGMicContainerItem', None, _("From G'Mic Script"), None, None, lambda a:containerclip.create_gmic_media_item()),
            ('CreateBlenderContainerItem', None, _("From Blender Project"), None, None, lambda a:containerclip.create_blender_media_item()),
            ('CombineSequences', None, _('Import Another Sequence Into This Sequence...'), None, None, lambda a:projectaction.combine_sequences()),
            ('LogClipRange', None, _('Log Marked Clip Range'), '<control>L', None, lambda a:medialog.log_range_clicked()),
            ('ViewProjectEvents', None, _('View Project Events...'), None, None, lambda a:projectaction.view_project_events()),
            ('RecreateMediaIcons', None, _('Recreate Media Icons...'), None, None, lambda a:menuactions.recreate_media_file_icons()),
            ('RemoveUnusedMedia', None, _('Remove Unused Media...'), None, None, lambda a:projectaction.remove_unused_media()),
            ('ChangeProfile', None, _("Change Project Profile..."), None, None, lambda a: projectaction.change_project_profile()),
            ('ProxyManager', None, _('Proxy Manager'), None, None, lambda a:proxyediting.show_proxy_manager_dialog()),
            ('ProjectInfo', None, _('Project Info'), None, None, lambda a:menuactions.show_project_info()),
            ('RenderMenu', None, _('Render')),
            ('AddToQueue', None, _('Add To Batch Render Queue...'), None, None, lambda a:projectaction.add_to_render_queue()),
            ('BatchRender', None, _('Batch Render Queue'), None, None, lambda a:batchrendering.launch_batch_rendering()),
            ('ReRenderTransitionsFades', None, _('Rerender All Rendered Transitions And Fades '), None, None, lambda a:tlineaction.rerender_all_rendered_transitions_and_fades()),
            ('Render', None, _('Render Timeline'), None, None, lambda a:projectaction.do_rendering()),
            ('ToolsMenu', None, _('Tools')),
            ('Titler', None, _('Titler'), None, None, lambda a:titler.show_titler()),
            ('AudioMix', None, _('Audio Mixer'), None, None, lambda a:audiomonitoring.show_audio_monitor()),
            ('GMIC', None, _("G'MIC Effects"), None, None, lambda a:gmic.launch_gmic()),
            ('Scripttool', None, _("Flowblade Media Plugin Editor"), None, None, lambda a:scripttool.launch_scripttool()),
            ('MediaLink', None, _('Media Relinker'), None, None, lambda a:medialinker.display_linker()),
            ('HelpMenu', None, _('_Help')),
            ('QuickReference', None, _('Contents'), None, None, lambda a:menuactions.quick_reference()),
            ('Environment', None, _('Runtime Environment'), None, None, lambda a:menuactions.environment()),
            ('KeyboardShortcuts', None, _('Keyboard Shortcuts'), None, None, lambda a:dialogs.keyboard_shortcuts_dialog(self.window, workflow.get_tline_tool_working_set, menuactions.keyboard_shortcuts_callback, keyevents.change_single_shortcut, menuactions.keyboard_shortcuts_menu_item_selected_callback)),
            ('About', None, _('About'), None, None, lambda a:menuactions.about()),
            ('TOOL_ACTION_KEY_1', None, None, '1', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_2', None, None, '2', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_3', None, None, '3', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_4', None, None, '4', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_5', None, None, '5', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_6', None, None, '6', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_7', None, None, '7', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_8', None, None, '8', None, lambda a:_this_is_not_used()),
            ('TOOL_ACTION_KEY_9', None, None, '9', None, lambda a:_this_is_not_used())
            ]

        menu_string = """<ui>
            <menubar name='MenuBar'>
                <menu action='FileMenu'>
                    <menuitem action='New'/>
                    <menuitem action='Open'/>
                    <menu action='OpenRecent'/>
                    <menuitem action='Save'/>
                    <menuitem action='Save As'/>
                    <menuitem action='SaveSnapshot'/>
                    <separator/>
                    <menu action='ExportMenu'>
                        <menuitem action='ExportMeltXML'/>
                        <menuitem action='ExportEDL'/>
                        <menuitem action='ExportScreenshot'/>
                        <menuitem action='ExportToArdour'/>
                    </menu>
                    <separator/>
                    <menuitem action='Close'/>
                    <menuitem action='Quit'/>
                </menu>
                <menu action='EditMenu'>
                    <menuitem action='Undo'/>
                    <menuitem action='Redo'/>
                    <separator/>
                    <menuitem action='Copy'/>
                    <menuitem action='Paste'/>
                    <menuitem action='PasteFilters'/>
                    <separator/>
                    <menu action='AddFromMonitor'>
                        <menuitem action='AppendClip'/>
                        <menuitem action='InsertClip'/>
                        <menuitem action='ThreepointOverWriteClip'/>
                        <menuitem action='RangeOverWriteClip'/>
                    </menu>
                    <separator/>
                    <menuitem action='CutClip'/>
                    <separator/>
                    <menuitem action='SpliceOutClip'/>
                    <menuitem action='DeleteClip'/>
                    <menuitem action='ResyncSelected'/>
                    <menuitem action='ClearFilters'/>
                    <separator/>
                    <menuitem action='SyncCompositors'/>
                    <menuitem action='FiltersOff'/>
                    <menuitem action='FiltersOn'/>
                    <separator/>
                    <menuitem action='AddTransition'/>
                    <menuitem action='AddFade'/>
                    <separator/>
                    <menuitem action='ProfilesManager'/>
                    <menuitem action='DiskCacheManager'/>
                    <menuitem action='KeyboardShortcuts'/>
                    <menuitem action='Preferences'/>
                </menu>
                <menu action='ViewMenu'>
                    <menuitem action='FullScreen'/>
                </menu>
                <menu action='ProjectMenu'>
                    <menuitem action='AddMediaClip'/>
                    <menuitem action='AddImageSequence'/>
                    <menuitem action='AddMediaPlugin'/>
                    <separator/>
                    <menuitem action='AddMediaFolder'/>
                    <separator/>
                    <menuitem action='CreateColorClip'/>
                    <menu action='ContainerClipsMenu'>
                        <menuitem action='CreateSelectionCompound'/>
                        <menuitem action='CreateSequenceCompound'/>
                        <menuitem action='AudioSyncCompoundClip'/>
                        <separator/>
                        <menuitem action='CreateGMicContainerItem'/>
                        <menuitem action='CreateBlenderContainerItem'/>
                    </menu>
                    <menuitem action='LoadMediaPluginScript'/>
                    <separator/>
                    <menu action='BinMenu'>
                        <menuitem action='AddBin'/>
                        <menuitem action='DeleteBin'/>
                    </menu>
                    <separator/>
                    <menuitem action='ImportProjectMedia'/>
                    <separator/>
                    <menuitem action='LogClipRange'/>
                    <separator/>
                    <menuitem action='ViewProjectEvents'/>
                    <menuitem action='RecreateMediaIcons'/>
                    <menuitem action='RemoveUnusedMedia'/>
                    <separator/>
                    <menuitem action='ChangeProfile'/>
                    <separator/>
                    <menuitem action='ProxyManager'/>
                </menu>
                <menu action='SequenceMenu'>
                    <menuitem action='AddSequence'/>
                    <menuitem action='EditSequence'/>
                    <menuitem action='DeleteSequence'/>
                    <separator/>
                    <menu action='CompositingModeMenu'/>
                    <separator/>
                    <menu action='TimelineRenderingMenu'/>
                    <separator/>
                    <menuitem action='CombineSequences'/>
                    <menuitem action='SequenceSplit'/>
                    <separator/>
                    <menuitem action='ChangeSequenceTracks'/>
                    <menuitem action='Watermark'/>
                </menu>
                <menu action='RenderMenu'>
                    <menuitem action='AddToQueue'/>
                    <menuitem action='BatchRender'/>
                    <separator/>
                    <menuitem action='ReRenderTransitionsFades'/>
                    <separator/>
                    <menuitem action='Render'/>
                </menu>
                <menu action='ToolsMenu'>
                    <menuitem action='AudioMix'/>
                    <separator/>
                    <menuitem action='Titler'/>
                    <menuitem action='GMIC'/>
                    <menuitem action='Scripttool'/>
                    <separator/>
                    <menuitem action='MediaLink'/>
                </menu>
                <menu action='HelpMenu'>
                    <menuitem action='QuickReference'/>
                    <menuitem action='Environment'/>
                    <separator/>
                    <menuitem action='About'/>
                </menu>
          </menubar>
        </ui>"""
        
        # Create global action group
        action_group = Gtk.ActionGroup('WindowActions')
        action_group.add_actions(menu_actions, user_data=None)

        # Use UIManager and add accelators to window.
        self.ui.insert_action_group(action_group, 0)
        self.ui.add_ui_from_string(menu_string)
        accel_group = self.ui.get_accel_group()
        self.window.add_accel_group(accel_group)

        # Get menu bar
        self.menubar = self.ui.get_widget('/MenuBar')
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
            self.menubar .override_background_color(Gtk.StateFlags.NORMAL, gui.get_mid_neutral_color())
        # Set reference to UI manager and acclegroup
        self.uimanager = ui
        self.accel_group = accel_group

        # Add recent projects to menu
        self.fill_recents_menu_widget(self.ui.get_widget('/MenuBar/FileMenu/OpenRecent'), projectaction.open_recent_project)
        
        # Disable audio mixer if not available
        if editorstate.audio_monitoring_available == False:
            self.ui.get_widget('/MenuBar/ToolsMenu/AudioMix').set_sensitive(False)

        # Hide Blender menu item for Flatpaks or if not available.
        if editorstate.app_running_from == editorstate.RUNNING_FROM_FLATPAK:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateBlenderContainerItem').set_visible(False)
        elif containerclip.blender_available() == False:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateBlenderContainerItem').set_sensitive(False)
        # Hide G'Mic if not available.
        if gmic.gmic_available() == False:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateGMicContainerItem').set_sensitive(False)

    def _init_view_menu(self, menu_item):
        menu = menu_item.get_submenu()

        # Full Screen -tem is already in menu, we need separator here
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        # Window Mode
        windows_menu_item = Gtk.MenuItem(_("Window Mode"))
        windows_menu = Gtk.Menu()
        one_window = Gtk.RadioMenuItem()
        one_window.set_label(_("Single Window"))

        windows_menu.append(one_window)

        two_windows = Gtk.RadioMenuItem.new_with_label([one_window], _("Two Windows"))

        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            one_window.set_active(True)
        else:
            two_windows.set_active(True)

        one_window.connect("activate", lambda w: self._change_windows_preference(w, appconsts.SINGLE_WINDOW))
        two_windows.connect("activate", lambda w: self._change_windows_preference(w, appconsts.TWO_WINDOWS))

        windows_menu.append(two_windows)
        windows_menu_item.set_submenu(windows_menu)
        menu.append(windows_menu_item)

        # Panel positions.
        if editorlayout.panel_positioning_available() == True:
            panel_positions_menu_item = editorlayout.get_panel_positions_menu_item()
            menu.append(panel_positions_menu_item)
            tabs_menu_item = editorlayout.get_tabs_menu_item()
            menu.append(tabs_menu_item)
        else:
            print("Panel positioning feature not available, too small screen.")

        # Middlebar Layout
        mb_menu_item = Gtk.MenuItem(_("Middlebar Configuration..."))
        mb_menu_item.connect("activate", lambda w: middlebar.show_middlebar_conf_dialog())
        menu.append(mb_menu_item)

        # Tool Selection Widget
        tool_selector_menu_item = Gtk.MenuItem(_("Edit Tool Selection Widget"))
        tool_selector_menu =  Gtk.Menu()
        tools_middlebar = Gtk.RadioMenuItem()
        tools_middlebar.set_label( _("Middlebar Menu"))

        tool_selector_menu.append(tools_middlebar)
        
        tools_dock = Gtk.RadioMenuItem.new_with_label([tools_middlebar], _("Dock"))

        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
            tools_middlebar.set_active(True)
        else:
            tools_dock.set_active(True)

        tools_middlebar.connect("activate", lambda w: self._show_tools_middlebar(w))
        tools_dock.connect("activate", lambda w: self._show_tools_dock(w))
        
        tool_selector_menu.append(tools_dock)
        tool_selector_menu_item.set_submenu(tool_selector_menu)
        menu.append(tool_selector_menu_item)
        
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        # Monitor Playback Interpolation
        interp_menu_item = Gtk.MenuItem(_("Monitor Playback Interpolation"))
        interp_menu = Gtk.Menu()

        interp_nearest = Gtk.RadioMenuItem()
        interp_nearest.set_label(_("Nearest Neighbour (fast)"))
        interp_nearest.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("nearest"))
        interp_menu.append(interp_nearest)

        interp_bilinear = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Bilinear (good)"))
        interp_bilinear.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("bilinear"))
        interp_menu.append(interp_bilinear)

        interp_bicubic = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Bicubic (better)"))
        interp_bicubic.set_active(True)
        interp_bicubic.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("bicubic"))
        interp_menu.append(interp_bicubic)

        interp_hyper = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Hyper/Lanczos (best)"))
        interp_hyper.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("hyper"))
        interp_menu.append(interp_hyper)

        interp_menu_item.set_submenu(interp_menu)
        menu.append(interp_menu_item)

        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        # Zoom
        zoom_in_menu_item = Gtk.MenuItem(_("Zoom In"))
        zoom_in_menu_item.connect("activate", lambda w: updater.zoom_in())
        menu.append(zoom_in_menu_item)
        zoom_out_menu_item = Gtk.MenuItem(_("Zoom Out"))
        zoom_out_menu_item.connect("activate", lambda w: updater.zoom_out())
        menu.append(zoom_out_menu_item)
        zoom_fit_menu_item = Gtk.MenuItem(_("Zoom Fit"))
        zoom_fit_menu_item.connect("activate", lambda w: updater.zoom_project_length())
        menu.append(zoom_fit_menu_item)

    def init_compositing_mode_menu(self):
        menu_item = self.uimanager.get_widget('/MenuBar/SequenceMenu/CompositingModeMenu')
        menu = menu_item.get_submenu()
        guiutils.remove_children(menu)

        comp_top_free = Gtk.RadioMenuItem()
        comp_top_free.set_label(_("Top Down Free Move"))
        comp_top_free.show()
        menu.append(comp_top_free)

        comp_standard_auto = Gtk.RadioMenuItem.new_with_label([comp_top_free],_("Auto Follow"))
        comp_standard_auto.show()
        menu.append(comp_standard_auto)

        comp_standard_full = Gtk.RadioMenuItem.new_with_label([comp_top_free],_("Standard Full Track"))
        comp_standard_full.show()
        menu.append(comp_standard_full)

        menu_items = [comp_top_free, comp_standard_auto, comp_standard_full]
        comp_mode = editorstate.get_compositing_mode()
        
        # We dropped compositing mode COMPOSITING_MODE_TOP_DOWN_AUTO_FOLLOW so compositing mode values no longer
        # correspond to menu indexes.
        comp_mode_to_menu_index = {0:0, 1:0, 2:1, 3:2}
        menu_index = comp_mode_to_menu_index[editorstate.get_compositing_mode()]
        menu_items[menu_index].set_active(True)

        comp_top_free.connect("toggled", lambda w: projectaction.change_current_sequence_compositing_mode(w, appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE))
        comp_standard_auto.connect("toggled", lambda w: projectaction.change_current_sequence_compositing_mode(w, appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW))
        comp_standard_full.connect("toggled", lambda w: projectaction.change_current_sequence_compositing_mode(w, appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK))

    def init_timeline_rendering_menu(self):
        menu_item = self.uimanager.get_widget('/MenuBar/SequenceMenu/TimelineRenderingMenu')
        menu = menu_item.get_submenu()
        guiutils.remove_children(menu)

        rendering_off = Gtk.RadioMenuItem()
        rendering_off.set_label(_("Off"))
        rendering_off.show()
        menu.append(rendering_off)

        rendering_auto = Gtk.RadioMenuItem.new_with_label([rendering_off],_("Render Auto"))
        rendering_auto.show()
        menu.append(rendering_auto)

        rendering_request = Gtk.RadioMenuItem.new_with_label([rendering_off],_("Render On Request"))
        rendering_request.show()
        menu.append(rendering_request)

        menu_items = [rendering_off, rendering_auto, rendering_request]
        menu_items[editorstate.get_tline_rendering_mode()].set_active(True)

        rendering_off.connect("toggled", lambda w: tlinerender.change_current_tline_rendering_mode(w, appconsts.TLINE_RENDERING_OFF))
        rendering_auto.connect("toggled", lambda w: tlinerender.change_current_tline_rendering_mode(w, appconsts.TLINE_RENDERING_AUTO))
        rendering_request.connect("toggled", lambda w: tlinerender.change_current_tline_rendering_mode(w, appconsts.TLINE_RENDERING_REQUEST))

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.append(sep)

        item = guiutils.get_menu_item(_("Settings..."), tlinerender.settings_dialog_launch, None)
        menu.append(item)

    def fill_recents_menu_widget(self, menu_item, callback):
        """
        Fills menu item with menuitems to open recent projects.
        """
        menu = menu_item.get_submenu()

        # Remove current items
        items = menu.get_children()
        for item in items:
            menu.remove(item)

        # Add new menu items
        recent_proj_names = editorpersistance.get_recent_projects()
        if len(recent_proj_names) != 0:
            for i in range (0, len(recent_proj_names)):
                proj_name = recent_proj_names[i]
                new_item = Gtk.MenuItem(proj_name)
                new_item.connect("activate", callback, i)
                menu.append(new_item)
                new_item.show()
        # ...or a single non-sensitive Empty item
        else:
            new_item = Gtk.MenuItem(_("Empty"))
            new_item.set_sensitive(False)
            menu.append(new_item)
            new_item.show()

    def hide_tline_render_strip(self):
        guiutils.remove_children(self.tline_renderer_hbox)

    def show_tline_render_strip(self):
        self.tline_renderer_hbox.pack_start(self.pad_box, False, False, 0)
        self.tline_renderer_hbox.pack_start(self.tline_render_strip.widget, True, True, 0)

    def _change_windows_preference(self, widget, new_window_layout):
        if widget.get_active() == False:
            return

        editorpersistance.prefs.global_layout = new_window_layout
        editorpersistance.save()

        primary_txt = _("Global Window Mode changed")
        secondary_txt = _("Application restart required for the new layout choice to take effect.")

        dialogutils.info_message(primary_txt, secondary_txt, self.window)

    # --------------------------------------------------------------- LAYOUT CHANGES
    # These methods are called from app menu and they show and hide panels or
    # move them around. When layout is created or startup we make sure that there is enough information  to
    # do the changes, e.g. some caontainer either exist are are set to None etc.  
    def _show_tools_middlebar(self, widget):
        if widget.get_active() == False:
            return
        editorpersistance.prefs.tools_selection = appconsts.TOOL_SELECTOR_IS_MENU
        editorpersistance.save()

        if self.tool_dock != None:
            self.tline_box.remove(self.tool_dock)

        middlebar.re_create_tool_selector(self)
        middlebar.redo_layout(self)
        workflow.select_default_tool()
        
    def _show_tools_dock(self, widget):
        if widget.get_active() == False:
            return

        editorpersistance.prefs.tools_selection = appconsts.TOOL_SELECTOR_IS_LEFT_DOCK
        editorpersistance.save()

        if self.tool_dock != None:
            self.tline_box.remove(self.tool_dock)

        self.tool_dock = workflow.get_tline_tool_dock()
        self.tool_dock.show_all()

        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_LEFT_DOCK:
            self.tline_box.pack_start(self.tool_dock, False, False, 0)

        middlebar.redo_layout(self)
        self.tool_selector = None
        workflow.select_default_tool()

    def update_tool_dock(self):
        self.tline_box.remove(self.tool_dock)

        self.tool_dock = workflow.get_tline_tool_dock()
        self.tool_dock.show_all()

        self.tline_box.pack_start(self.tool_dock, False, False, 0)

    # ----------------------------------------------------------- GUI components monitor, middlebar.
    def _create_monitor_buttons(self):
        self.monitor_switch = guicomponents.MonitorSwitch(self._monitor_switch_handler)

    def _create_monitor_row_widgets(self):
        self.monitor_tc_info = guicomponents.MonitorMarksTCInfo()
        guiutils.set_margins(self.monitor_tc_info.widget,5,0,0,0)

    def _monitor_switch_handler(self, action):
        if action == appconsts.MONITOR_TLINE_BUTTON_PRESSED:
            updater.display_sequence_in_monitor()

        if action == appconsts.MONITOR_CLIP_BUTTON_PRESSED:
            updater.display_clip_in_monitor()

    def connect_player(self, mltplayer):
        # Buttons
        # NOTE: ORDER OF CALLBACKS IS THE SAME AS ORDER OF BUTTONS FROM LEFT TO RIGHT
        # Jul-2016 - SvdB - For play/pause button
        if editorpersistance.prefs.play_pause == False:
            # ------------------------------timeline_start_end_button
            if (editorpersistance.prefs.timeline_start_end is True):
                pressed_callback_funcs = [monitorevent.start_pressed,  #  go to start
                                          monitorevent.end_pressed,   #  go to  end
                                          monitorevent.prev_pressed,
                                          monitorevent.next_pressed,
                                          monitorevent.play_pressed,
                                          monitorevent.stop_pressed,
                                          monitorevent.mark_in_pressed,
                                          monitorevent.mark_out_pressed,
                                          monitorevent.marks_clear_pressed,
                                          monitorevent.to_mark_in_pressed,
                                          monitorevent.to_mark_out_pressed]
            else:
                pressed_callback_funcs = [monitorevent.prev_pressed,
                                          monitorevent.next_pressed,
                                          monitorevent.play_pressed,
                                          monitorevent.stop_pressed,
                                          monitorevent.mark_in_pressed,
                                          monitorevent.mark_out_pressed,
                                          monitorevent.marks_clear_pressed,
                                          monitorevent.to_mark_in_pressed,
                                          monitorevent.to_mark_out_pressed]
        else:
            if (editorpersistance.prefs.timeline_start_end is True):
                pressed_callback_funcs = [monitorevent.start_pressed,  #  go to start
                                          monitorevent.end_pressed,   #  go to  end
                                          monitorevent.prev_pressed,
                                          monitorevent.next_pressed,
                                          monitorevent.play_pressed,
                                          monitorevent.mark_in_pressed,
                                          monitorevent.mark_out_pressed,
                                          monitorevent.marks_clear_pressed,
                                          monitorevent.to_mark_in_pressed,
                                          monitorevent.to_mark_out_pressed]
            else:
                pressed_callback_funcs = [monitorevent.prev_pressed,
                                          monitorevent.next_pressed,
                                          monitorevent.play_pressed,
                                          monitorevent.mark_in_pressed,
                                          monitorevent.mark_out_pressed,
                                          monitorevent.marks_clear_pressed,
                                          monitorevent.to_mark_in_pressed,
                                          monitorevent.to_mark_out_pressed]

        self.player_buttons.set_callbacks(pressed_callback_funcs)

        # Monitor position bar
        self.pos_bar.set_listener(mltplayer.seek_position_normalized)

    def _get_edit_buttons_row(self):
        tools_pixbufs = [INSERTMOVE_CURSOR, OVERWRITE_CURSOR, ONEROLL_CURSOR, ONEROLL_RIPPLE_CURSOR, \
                         TWOROLL_CURSOR, SLIDE_CURSOR, MULTIMOVE_CURSOR, OVERWRITE_BOX_CURSOR, CUT_CURSOR, KF_TOOL_CURSOR, MULTI_TRIM_CURSOR]
        middlebar.create_edit_buttons_row_buttons(self, tools_pixbufs)

        buttons_row = Gtk.HBox(False, 1)
        if editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_COMPONENTS_CENTERED:
            middlebar.fill_with_COMPONENTS_CENTERED_pattern(buttons_row, self)
        elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_LEFT:
            middlebar.fill_with_TC_LEFT_pattern(buttons_row, self)
        else:
            middlebar.fill_with_TC_MIDDLE_pattern(buttons_row, self)

        # Aug-2019 - SvdB - BB
        offset = 2
        if editorpersistance.prefs.double_track_hights:
           offset = 4
           buttons_row.set_margin_bottom(offset)

        buttons_row.set_margin_top(offset)
        buttons_row.set_margin_left(offset)
        buttons_row.set_margin_right(offset)

        return buttons_row

    def _add_tool_tips(self):
        self.big_TC.set_tooltip_text(_("Timeline current frame timecode"))

        self.view_mode_select.widget.set_tooltip_text(_("Select view mode: Video / Vectorscope/ RGBParade"))
        self.trim_view_select.widget.set_tooltip_text(_("Set trim view and match frames"))

        self.pos_bar.widget.set_tooltip_text(_("Sequence / Media current position"))

    # --------------------------------------------------------- EDIT TOOL AND CURSOR CHANGE HANDLING
    def set_default_edit_tool(self):
        # First active tool is the default tool. So we need to always have atleast one tool available.
        self.change_tool(editorpersistance.prefs.active_tools[0])
        # Update paths for tool selector and tool dock are unfortunately a bit different.
        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_LEFT_DOCK:
            workflow.set_default_tool_dock_item_selected()

    def kf_tool_exit_to_mode(self, mode): # Kf tool can be entered from popup menu and it exists to mode it was started in.
        tool_id = None
        if mode == editorstate.INSERT_MOVE:
            tool_id = appconsts.TLINE_TOOL_INSERT
        elif mode == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                tool_id = appconsts.TLINE_TOOL_OVERWRITE
            else:
                tool_id = appconsts.TLINE_TOOL_BOX
        elif mode == editorstate.ONE_ROLL_TRIM or mode == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False: # this was not touched on entering KF tool
                tool_id = appconsts.TLINE_TOOL_TRIM
            else:
                tool_id = appconsts.TLINE_TOOL_RIPPLE_TRIM
        elif mode == editorstate.TWO_ROLL_TRIM or mode == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            tool_id = appconsts.TLINE_TOOL_ROLL
        elif mode == editorstate.SLIDE_TRIM or mode == editorstate.SLIDE_TRIM_NO_EDIT:
            tool_id = appconsts.TLINE_TOOL_SLIP
        elif mode == editorstate.MULTI_MOVE:
            tool_id = appconsts.TLINE_TOOL_SPACER
        elif mode == editorstate.CUT:
            tool_id = appconsts.TLINE_TOOL_CUT
        elif mode == editorstate.KF_TOOL:
            tool_id = appconsts.TLINE_TOOL_KFTOOL
        elif mode == editorstate.MULTI_TRIM:
            tool_id = appconsts.TLINE_TOOL_MULTI_TRIM
        if tool_id != None:
            self.change_tool(tool_id)
        else:
            print("kf_tool_exit_to_mode(): NO TOOL_ID!") # This should not happen, but lets print info instead of crashing if we get here

    def change_tool(self, tool_id):
        if tool_id == appconsts.TLINE_TOOL_INSERT:
            self.handle_insert_move_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_OVERWRITE:
            self.handle_over_move_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_TRIM:
            self.handle_one_roll_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_ROLL:
            self.handle_two_roll_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_SLIP:
            self.handle_slide_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_SPACER:
            self.handle_multi_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_BOX:
            self.handle_box_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_RIPPLE_TRIM:
            self.handle_one_roll_ripple_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_CUT:
            self.handle_cut_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_KFTOOL:
            self.handle_kftool_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_MULTI_TRIM:
            self.handle_multitrim_mode_button_press()
        else:
            # We should not hit this
            print("editorwindow.change_tool() else: hit!")
            return

        gui.editor_window.set_tool_selector_to_mode()

    def handle_over_move_mode_button_press(self):
        modesetting.overwrite_move_mode_pressed()
        self.set_cursor_to_mode()

    def handle_box_mode_button_press(self):
        modesetting.box_mode_pressed()
        self.set_cursor_to_mode()

    def handle_insert_move_mode_button_press(self):
        modesetting.insert_move_mode_pressed()
        self.set_cursor_to_mode()

    def handle_one_roll_mode_button_press(self):
        editorstate.trim_mode_ripple = False
        modesetting.oneroll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_one_roll_ripple_mode_button_press(self):
        editorstate.trim_mode_ripple = True
        modesetting.oneroll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_two_roll_mode_button_press(self):
        modesetting.tworoll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_slide_mode_button_press(self):
        modesetting.slide_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_multi_mode_button_press(self):
        modesetting.multi_mode_pressed()
        self.set_cursor_to_mode()

    def handle_cut_mode_button_press(self):
        modesetting.cut_mode_pressed()
        self.set_cursor_to_mode()

    def handle_kftool_mode_button_press(self):
        modesetting.kftool_mode_pressed()
        self.set_cursor_to_mode()

    def handle_multitrim_mode_button_press(self):
        modesetting.multitrim_mode_pressed()
        self.set_cursor_to_mode()

    def toggle_trim_ripple_mode(self):
        editorstate.trim_mode_ripple = (editorstate.trim_mode_ripple == False)
        modesetting.stop_looping()
        editorstate.edit_mode = editorstate.ONE_ROLL_TRIM_NO_EDIT
        tlinewidgets.set_edit_mode(None, None)
        self.set_tool_selector_to_mode()
        self.set_tline_cursor(editorstate.EDIT_MODE())
        updater.set_trim_mode_gui()

    def mode_selector_pressed(self, selector, event):
        workflow.get_tline_tool_popup_menu(event, self.tool_selector_item_activated)

    def tool_selector_item_activated(self, selector, tool):
        if tool == appconsts.TLINE_TOOL_INSERT:
            self.handle_insert_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_OVERWRITE:
            self.handle_over_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_TRIM:
            self.handle_one_roll_mode_button_press()
        if tool == appconsts.TLINE_TOOL_RIPPLE_TRIM:
            self.handle_one_roll_ripple_mode_button_press()
        if tool == appconsts.TLINE_TOOL_ROLL:
            self.handle_two_roll_mode_button_press()
        if tool == appconsts.TLINE_TOOL_SLIP:
            self.handle_slide_mode_button_press()
        if tool == appconsts.TLINE_TOOL_SPACER:
            self.handle_multi_mode_button_press()
        if tool == appconsts.TLINE_TOOL_BOX:
            self.handle_box_mode_button_press()
        if tool == appconsts.TLINE_TOOL_CUT:
            self.handle_cut_mode_button_press()
        if tool == appconsts.TLINE_TOOL_KFTOOL:
            self.handle_kftool_mode_button_press()
        if tool == appconsts.TLINE_TOOL_MULTI_TRIM:
            self.handle_multitrim_mode_button_press()

        self.set_cursor_to_mode()
        self.set_tool_selector_to_mode()

    def set_cursor_to_mode(self):
        if editorstate.cursor_on_tline == True:
            self.set_tline_cursor(editorstate.EDIT_MODE())
        else:
            gdk_window = gui.tline_display.get_parent_window()
            gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))

    def get_own_cursor(self, display, surface, hotx, hoty):
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, surface.get_width(), surface.get_height())
        return Gdk.Cursor.new_from_pixbuf(display, pixbuf, hotx, hoty)

    def set_tline_cursor(self, mode):
        display = Gdk.Display.get_default()
        gdk_window = self.window.get_window()

        if mode == editorstate.INSERT_MOVE:
            cursor = self.get_own_cursor(display, INSERTMOVE_CURSOR, 0, 0)
        elif mode == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                cursor = self.get_own_cursor(display, OVERWRITE_CURSOR, 0, 0)
            else:
                if boxmove.entered_from_overwrite == False:
                    cursor = self.get_own_cursor(display, OVERWRITE_BOX_CURSOR, 6, 15)
                else:
                    cursor = self.get_own_cursor(display, OVERWRITE_CURSOR, 0, 0)
        elif mode == editorstate.TWO_ROLL_TRIM:
            cursor = self.get_own_cursor(display, TWOROLL_NO_EDIT_CURSOR, 11, 9)
        elif mode == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            cursor = self.get_own_cursor(display, TWOROLL_NO_EDIT_CURSOR, 11, 9)
        elif mode == editorstate.ONE_ROLL_TRIM:
            if editorstate.trim_mode_ripple == False:
                cursor = self.get_own_cursor(display, ONEROLL_NO_EDIT_CURSOR, 9, 9)
            else:
                cursor = self.get_own_cursor(display, ONEROLL_RIPPLE_CURSOR, 9, 9)
        elif mode == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False:
                cursor = self.get_own_cursor(display, ONEROLL_NO_EDIT_CURSOR, 9, 9)
            else:
                cursor = self.get_own_cursor(display, ONEROLL_RIPPLE_CURSOR, 9, 9)
        elif mode == editorstate.SLIDE_TRIM:
            cursor = self.get_own_cursor(display, SLIDE_NO_EDIT_CURSOR, 9, 9)
        elif mode == editorstate.SLIDE_TRIM_NO_EDIT:
            cursor = self.get_own_cursor(display, SLIDE_NO_EDIT_CURSOR, 9, 9)
        elif mode == editorstate.SELECT_PARENT_CLIP:
            cursor =  Gdk.Cursor.new(Gdk.CursorType.TCROSS)
        elif mode == editorstate.SELECT_TLINE_SYNC_CLIP:
            cursor =  Gdk.Cursor.new(Gdk.CursorType.TCROSS)
        elif mode == editorstate.MULTI_MOVE:
            cursor = self.get_own_cursor(display, MULTIMOVE_CURSOR, 4, 8)
        elif mode == editorstate.CLIP_END_DRAG:
            surface, px, py = self.context_cursors[tlinewidgets.pointer_context]
            cursor = self.get_own_cursor(display, surface, px, py)
        elif mode == editorstate.CUT:
            cursor = self.get_own_cursor(display, CUT_CURSOR, 1, 8)
        elif mode == editorstate.KF_TOOL:
            cursor = self.get_own_cursor(display, KF_TOOL_CURSOR, 1, 0)
        elif mode == editorstate.MULTI_TRIM:
            cursor = self.get_own_cursor(display, MULTI_TRIM_CURSOR, 1, 0)
        else:
            cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR)

        gdk_window.set_cursor(cursor)

    def set_tline_cursor_to_context(self, pointer_context):
        display = Gdk.Display.get_default()
        gdk_window = self.window.get_window()

        surface, px, py = self.context_cursors[pointer_context]
        cursor = self.get_own_cursor(display, surface, px, py)
        gdk_window.set_cursor(cursor)

    def set_tool_selector_to_mode(self):
        if self.tool_selector == None:
            return # We are using dock

        if editorstate.EDIT_MODE() == editorstate.INSERT_MOVE:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_INSERT)
        elif editorstate.EDIT_MODE() == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_OVERWRITE)
            else:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_BOX)
        elif editorstate.EDIT_MODE() == editorstate.ONE_ROLL_TRIM or editorstate.EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_TRIM)
            else:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_RIPPLE_TRIM)
        elif editorstate.EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_ROLL)
        elif editorstate.EDIT_MODE() == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_ROLL)
        elif editorstate.EDIT_MODE() == editorstate.SLIDE_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SLIP)
        elif editorstate.EDIT_MODE() == editorstate.SLIDE_TRIM_NO_EDIT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SLIP)
        elif editorstate.EDIT_MODE() == editorstate.MULTI_MOVE:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SPACER)
        elif editorstate.EDIT_MODE() == editorstate.CUT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_CUT)
        elif editorstate.EDIT_MODE() == editorstate.KF_TOOL:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_KFTOOL)
        elif editorstate.EDIT_MODE() == editorstate.MULTI_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_MULTI_TRIM)

    def tline_cursor_leave(self, event):
        cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR)
        gdk_window = self.window.get_window()
        gdk_window.set_cursor(cursor)

        if event.get_state() & Gdk.ModifierType.BUTTON1_MASK:
            if editorstate.current_is_move_mode():
                tlineaction.mouse_dragged_out(event)

    def tline_cursor_enter(self, event):
        editorstate.cursor_on_tline = True
        self.set_cursor_to_mode()

    def top_paned_resized(self, w, req):
        pass


def _this_is_not_used():
    print("THIS WAS USED!!!!!")

