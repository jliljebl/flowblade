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
Module contains the main editor window object and timeline cursor handling.
"""

from gi.repository import Gtk, GLib


import appconsts
import appactions
import audiomonitoring
import audiosync
import batchrendering
import callbackbridge
import clipeffectseditor
import clipmenuaction
import compositeeditor
import containerclip
import copypaste
import dialogs
import dialogutils
import dnd
import editevent
import editorlayout
import editorpersistance
import editorstate
from editorstate import APP
import exporting
import glassbuttons
import gmic
import gui
import guicomponents
import guiutils
import gtkbuilder
import jobs
import medialinker
import medialog
import mediaplugin
import menuactions
import menubar
import middlebar
import mltplayer
import modesetting
import monitorevent
import monitorwidget
import mutabletooltips
import respaths
import render
import rendergui
import panels
import patternproducer
from positionbar import PositionBar
import preferenceswindow
import projectaction
import projectaddmediafolder
import projectdatavaultgui
import projectinfogui
import proxyediting
import proxytranscodemanager
import scripttool
import shortcuts
import shortcutsdialog
import singletracktransition
import syncsplitevent
import titler
import tlineaction
import tlinecursors
import tlinewidgets
import tlineypage
import trackaction
import updater
import undo
import workflow

# GUI min size params, these have probably no effect on layout.
MEDIA_MANAGER_WIDTH = 110 # This in paned container on small screens, has no effect on whole window layout. 
MONITOR_AREA_WIDTH = appconsts.MONITOR_AREA_WIDTH

DARK_BG_COLOR = (0.223, 0.247, 0.247, 1.0)


class EditorWindow:

    def __init__(self):

        self.tline_cursor_manager = tlinecursors.TLineCursorManager()

        # Create window(s)
        self.window = Gtk.ApplicationWindow(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
        self.window.set_border_width(0)

        self.window2 = None
        if editorpersistance.prefs.global_layout != appconsts.SINGLE_WINDOW:
            self.window2 = Gtk.Window(Gtk.WindowType.TOPLEVEL)
            self.window2.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
            self.window2.set_border_width(5)
            self.window2.connect("delete-event", lambda w, e:callbackbridge.app_shutdown())

        # To ask confirmation for shutdown
        self.window.connect("delete-event", lambda w, e:callbackbridge.app_shutdown())

        # Player consumer has to be stopped and started when window resized
        if mltplayer.get_sdl_consumer_version() == mltplayer.SDL_1: # Delete when everyone is on mlt 7.30 or moving to Gtk4.
            self.window.connect("window-state-event", lambda w, e:updater.refresh_player(e))

        self.audio_master_meter = None

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
        self.app_v_paned = gtkbuilder.VPaned()
        self.app_v_paned.pack1(self.top_row_hbox, resize=False, shrink=False)
        self.app_v_paned.pack2(self.tline_pane, resize=True, shrink=False)

        # self.app_h_box is used to implement position PANEL_PLACEMENT_LEFT_COLUMN.
        self.app_h_box = Gtk.HBox(False, 0)
        self.app_h_box.pack_start(self.left_column_frame, False, False, 0)
        self.app_h_box.pack_start(self.app_v_paned, True, True, 0)
        self.app_h_box.pack_start(self.right_column_frame, False, False, 0)
        
        # Menu box
        self.menubar.set_margin_bottom(4)
        self.menubar.set_name("lighter-bg-widget")

        menubar_box = Gtk.HBox(False, 0)
        if editorstate.screen_size_small_width() == False:
            menubar_box.pack_start(guiutils.get_right_justified_box([self.menubar]), False, False, 0)
            menubar_box.pack_start(Gtk.Label(), True, True, 0)
        else:
            menubar_box.pack_start(self.menubar, False, False, 0)

        project_info_box = Gtk.HBox(False, 0)
        project_info_box.pack_start(Gtk.Label(), True, True, 0)
        monitor_desc_panel = projectinfogui.get_top_level_project_info_panel()
        self.monitor_desc_label = projectinfogui.widgets.monitor_desc_label
        project_info_box.pack_start(monitor_desc_panel, False, False, 0)
        project_info_box.pack_start(Gtk.Label(), True, True, 0)

        layout_widgets = [self.tools_buttons.widget, guiutils.pad_label(24,2), self.fullscreen_press.widget, guiutils.pad_label(6,2), self.layout_press.widget]
        layout_controls_box = guiutils.get_right_justified_box(layout_widgets)
        layout_controls_box.set_margin_right(6)

        if editorstate.SCREEN_WIDTH > 1550:
            menu_vbox = Gtk.HBox(True, 0)
        else:
            menu_vbox = Gtk.HBox(False, 0) # small screens can't fit 3 equal sized panels here

        menu_vbox.pack_start(menubar_box, True, True, 0)

        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            if editorstate.screen_size_small_width() == False:
                menu_vbox.pack_start(project_info_box, True, True, 0)
            else:
                menu_vbox.pack_start(guiutils.pad_label(24, 2), False, False, 0)
                menu_vbox.pack_start(project_info_box, False, False, 0)
                menu_vbox.pack_start(guiutils.pad_label(40, 2), False, False, 0)
            menu_vbox.pack_start(layout_controls_box, True, True, 0)
        else:
            menu_vbox.pack_start(project_info_box, True, True, 0)
            menu_vbox.pack_start(layout_controls_box, True, True, 0)
            tline_info_box = self._get_monitor_info_box()
            self.top_row_window_2 = tline_info_box #Gtk.HBox(False, 0)
            
        # Pane
        pane = Gtk.VBox(False, 1)
        pane.pack_start(menu_vbox, False, True, 0)
        pane.pack_start(self.app_h_box, True, True, 0)
        return pane

    def _init_gui_components(self):        
        # Disable G'Mic container clip menu items if not available.
        if gmic.gmic_available() == False:
            self.ui.get_widget('/MenuBar/ProjectMenu/ContainerClipsMenu/CreateGMicContainerItem').set_sensitive(False)
            
        # Media panel
        self.bin_list_view = guicomponents.BinTreeView(
                                        projectaction.bin_selection_changed,
                                        projectaction.bin_name_edited,
                                        projectaction.bins_panel_popup_requested,
                                        projectaction.media_panel_to_front)
        dnd.connect_bin_tree_view(self.bin_list_view.treeview, projectaction.move_files_to_bin)
        self.bin_list_view.set_property("can-focus",  True)


        self.bins_panel = panels.get_bins_tree_panel(self.bin_list_view, projectaction.bin_hambuger_pressed)
        self.bins_panel.set_size_request(MEDIA_MANAGER_WIDTH, 10) # this component is always expanded, so 10 for minimum size ok

        self.media_list_view = guicomponents.MediaPanel(projectaction.media_file_popover_mouse_right_pressed,
                                                        projectaction.media_panel_double_click,
                                                        projectaction.media_panel_popup_requested)
        view = Gtk.Viewport()
        view.add(self.media_list_view.widget)

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
                                    projectaction.media_filtering_select_pressed)

        self.media_panel = media_panel
        self.media_panel.set_name("darker-bg-widget")
        self.bin_info = bin_info

        # Smallest screens always get bins in same panel as media, others get top level project panel if selected
        if editorlayout.top_level_project_panel() == True:
            self.mm_paned = Gtk.HBox()
            self.mm_paned.add(media_panel)

        else:
            self.mm_paned = gtkbuilder.HPaned()
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

        gui.apply_widget_css_class(self.effects_panel, "dark-bg", "dark-bg-class.css")

        # Effects select panel
        effect_select_panel, effect_select_list_view, effect_select_combo_box = panels.get_effect_selection_panel(clipeffectseditor.effect_select_row_double_clicked)
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
        gui.apply_widget_css_class(multi_empty_vbox, "dark-bg", "dark-bg-class.css")
        
        # Multi edit panel
        self.edit_multi = guicomponents.EditMultiStack()
        self.edit_multi.add_named(multi_empty_vbox, appconsts.EDIT_MULTI_EMPTY)
        self.edit_multi.add_named(self.effects_panel, appconsts.EDIT_MULTI_FILTERS)
        self.edit_multi.add_named(compositors_panel, appconsts.EDIT_MULTI_COMPOSITORS)
        self.edit_multi.add_named(mediaplugins_panel, appconsts.EDIT_MULTI_PLUGINS)
        self.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_EMPTY)
        gui.apply_widget_css_class(self.edit_multi.widget, "dark-bg", "dark-bg-class.css")
        # Render panel
        try:
            render.create_widgets()
            render_panel_left = rendergui.get_render_panel_left(render.widgets,
                                                                lambda w,e: projectaction.do_rendering(),
                                                                lambda w,e: projectaction.add_to_render_queue(),
                                                                lambda w,e: preferenceswindow.preferences_dialog(True))
        except IndexError:
            print("No rendering options found")
            render_panel_left = None

        # 'None' here means that no possible rendering options were available
        # and creating panel failed. Inform user of this and hide render GUI
        if render_panel_left == None:
            render_panel_info = Gtk.VBox(False, 5)
            render_panel_info.pack_start(Gtk.Label(label="Rendering disabled."), False, False, 0)
            render_panel_info.pack_start(Gtk.Label(label="No available rendering options found."), False, False, 0)
            render_panel_info.pack_start(Gtk.Label(label="See Help->Environment->Render Options for details."), False, False, 0)
            render_panel_info.pack_start(Gtk.Label(label="Install codecs to make rendering available."), False, False, 0)
            render_panel_info.pack_start(Gtk.Label(label=" "), True, True, 0)
            self.render_panel = render_panel_info
        else: # all is good, create render panel.
            if editorstate.screen_size_large_width() == False:
                render_hbox = Gtk.HBox(False, 5)
                render_hbox.pack_start(render_panel_left, True, True, 0)
                render_panel_right = rendergui.get_render_panel_right(render.widgets,
                                                                      lambda w,e: projectaction.do_rendering(),
                                                                      lambda w,e: projectaction.add_to_render_queue())
                render_hbox.pack_start(render_panel_right, True, True, 0)
                
                self.render_panel = guiutils.set_margins(render_hbox, 2, 6, 8, 6)
            else:
                self.render_panel = guiutils.set_margins(render_panel_left, 2, 6, 8, 6)

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
        seq_panel = panels.get_sequences_panel(self.sequence_list_view, projectaction.sequences_hamburger_pressed)

        # Jobs panel
        jobs.create_jobs_list_view()
        jobs_panel = jobs.get_jobs_panel()
        jobs_hbox = Gtk.HBox()
        jobs_hbox.pack_start(jobs_panel, True, True, 0)
        self.jobs_pane = guiutils.set_margins(jobs_hbox, 6, 6, 6, 6)

        # Project panel
        if editorlayout.top_level_project_panel() == True:
            # Project info
            top_project_vbox = Gtk.VBox()
            top_project_vbox.pack_start(self.bins_panel, True, True, 0)
            top_project_vbox.pack_start(seq_panel, True, True, 0)

            self.top_project_panel = guiutils.set_margins(top_project_vbox, 0, 0, 0, 0)
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

        # Middlebar
        # Fullscreen and layout buttons are created here but adda to middlebar in middlebar.py
        fullscreen_icon = guiutils.get_cairo_image("fullscreen")
        fullscreen_exit_icon = guiutils.get_cairo_image("fullscreen_exit")
        self.fullscreen_press = guicomponents.PressLaunch(menuactions.toggle_fullscreen, fullscreen_icon, 20, 12)
        self.fullscreen_press.widget.set_margin_top(1)
        self.fullscreen_press.widget.set_tooltip_text(_("Fullscreen - F11"))
        # Used in menuactions.toggle_fullscreen to switch image
        self.fullscreen_press.fullscreen_icon = fullscreen_icon
        self.fullscreen_press.fullscreen_exit_icon = fullscreen_exit_icon

        icon_2 = guiutils.get_cairo_image("layout")
        self.layout_press = guicomponents.PressLaunchPopover(editorlayout.show_layout_press_menu, icon_2, 24, 12)
        self.layout_press.widget.set_margin_top(1)
        self.layout_press.widget.set_tooltip_text(_("Layouts"))
        
        self.edit_buttons_row = self._get_edit_buttons_row()

        self.edit_buttons_frame = Gtk.Frame()
        self.edit_buttons_frame.add(self.edit_buttons_row)
        guiutils.set_margins(self.edit_buttons_frame, 1, 0, 0, 0)

        # Position bar and decorative frame for it
        self.pos_bar = PositionBar()
        pos_bar_frame = Gtk.HBox()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_margin_top(2)
        pos_bar_frame.set_margin_bottom(4)
        pos_bar_frame.set_margin_start(4)
        pos_bar_frame.set_margin_end(4)

        # Play buttons row
        self._create_monitor_buttons()
        self._create_monitor_row_widgets()

        self.player_buttons = glassbuttons.PlayerButtonsCompact()
        tooltip_runner = glassbuttons.TooltipRunner(self.player_buttons, None)
        mutabletooltips.add_widget(mutabletooltips.PLAYER_BUTTONS, self.player_buttons, tooltip_runner)
        if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
            self.player_buttons.no_decorations = True

        self.view_mode_select = guicomponents.get_monitor_view_select_launcher(tlineaction.view_mode_menu_lauched)
        self.view_mode_select.widget.set_margin_end(10)
        self.trim_view_select = guicomponents.get_trim_view_select_launcher(monitorevent.trim_view_menu_launched)
        self.playback_settings = guicomponents.get_playback_settings_launcher(monitorevent.playback_settings_menu_launched)
        self.playback_settings.widget.set_margin_right(12) 
        self.playback_settings.widget.set_tooltip_markup(_("Playback Settings"))

        callbacks = [monitorevent.mark_in_pressed,
                     monitorevent.mark_out_pressed,
                     monitorevent.marks_clear_pressed,
                     monitorevent.to_mark_in_pressed,
                     monitorevent.to_mark_out_pressed]
        markbuttons = glassbuttons.MarkButtons(callbacks)
        markbuttons.widget.set_margin_right(12)
        tooltip_runner = glassbuttons.TooltipRunner(markbuttons, None)
        mutabletooltips.add_widget(mutabletooltips.MARK_BUTTONS, markbuttons, tooltip_runner)
        
        player_buttons_row = Gtk.HBox(False, 0)
        player_buttons_row.pack_start(self.monitor_switch.widget, False, False, 0)
        player_buttons_row.pack_start(self.playback_settings.widget, False, False, 0)
        player_buttons_row.pack_start(self.monitor_tc_info.scaling, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(self.player_buttons.widget, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(markbuttons.widget, False, False, 0)
        player_buttons_row.pack_start(self.trim_view_select.widget, False, False, 0)
        player_buttons_row.pack_start(self.view_mode_select.widget, False, False, 0)
        player_buttons_row.set_margin_top(7)
        player_buttons_row.set_margin_bottom(6)
        player_buttons_row.set_margin_left(12)
        player_buttons_row.set_margin_right(12)

        # This is used in updater.py
        player_buttons_row.set_name("player-bar")

        self.player_buttons_row = player_buttons_row
        
        tc_player_row = Gtk.HBox(False, 0)
        tc_player_row.pack_start(self.big_TC, False, False, 0)
        tc_player_row.pack_start(player_buttons_row, True, True, 0)

        # pos bar row
        sw_pos_hbox = Gtk.HBox(False, 1)
        sw_pos_hbox.pack_start(pos_bar_frame, True, True, 0)
        
        # Video display
        monitor_widget = monitorwidget.MonitorWidget()
        self.tline_display = monitor_widget.get_monitor()
        self.monitor_widget = monitor_widget

        dnd.connect_video_monitor(self.tline_display)

        # Top info row
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            monitor_info_box = self._get_monitor_info_box()

        # Monitor
        monitor_vbox = Gtk.VBox(False, 0)
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            monitor_vbox.pack_start(monitor_info_box, False, True, 0)
        monitor_vbox.pack_start(monitor_widget.widget, True, True, 0)
        monitor_vbox.pack_start(tc_player_row, False, True, 0)
        monitor_vbox.pack_start(sw_pos_hbox, False, True, 0)
        monitor_align = guiutils.set_margins(monitor_vbox, 0, 0, 0, 0)

        self.monitor_frame = Gtk.Frame()
        self.monitor_frame.add(monitor_align)
        self.monitor_frame.set_size_request(MONITOR_AREA_WIDTH, appconsts.TOP_ROW_HEIGHT)

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

        size_x = tlinewidgets.COLUMN_WIDTH - 22 - 22 - 22 - 22
        size_y = tlinewidgets.SCALE_HEIGHT

        info_h.set_size_request(size_x, size_y)

        marker_surface =  guiutils.get_cairo_image("marker")
        markers_launcher =  guicomponents.PressLaunchPopover(tlineaction.marker_menu_lauch_pressed, marker_surface, 22, 22)
        markers_launcher.widget.set_tooltip_markup(_("Timeline Markers"))

        tracks_launcher_surface = guiutils.get_cairo_image("track_menu_launch")
        tracks_launcher = guicomponents.PressLaunchPopover(trackaction.all_tracks_menu_launch_pressed, tracks_launcher_surface, 22, 22)
        tracks_launcher.widget.set_tooltip_markup(_("Tracks"))
        
        levels_launcher_surface = guiutils.get_cairo_image("audio_levels_menu_launch")
        levels_launcher = guicomponents.PressLaunchPopover(trackaction.tline_properties_menu_launch_pressed, levels_launcher_surface, 22, 22)
        levels_launcher.widget.set_tooltip_markup(_("Timeline Properties"))
        
        sync_launcher_surface = guiutils.get_cairo_image("sync_menu_launch")
        sync_launcher = guicomponents.PressLaunchPopover(syncsplitevent.sync_menu_launch_pressed, sync_launcher_surface, 22, 22)
        sync_launcher.widget.set_tooltip_markup(_("Syncing"))
        
        # Timeline top row
        tline_hbox_1 = Gtk.HBox()
        tline_hbox_1.pack_start(info_h, False, False, 0)
        tline_hbox_1.pack_start(sync_launcher.widget, False, False, 0)
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
            self.tline_cursor_manager.tline_cursor_leave,
            self.tline_cursor_manager.tline_cursor_enter)

        dnd.connect_tline(self.tline_canvas.widget, editevent.tline_effect_drop,
                          editevent.tline_media_drop)

        # Y Scroll
        self.tline_y_page = tlinewidgets.TimeLineYPage(tlineypage.page_up, tlineypage.page_down)

        # Create tool dock if needed
        if editorpersistance.prefs.tools_selection != appconsts.TOOL_SELECTOR_IS_MENU:
            self.tool_dock = workflow.get_tline_tool_dock()
        else:
            self.tool_dock = None

        # Timeline middle row
        tline_hbox_2 = Gtk.HBox()
        tline_hbox_2.pack_start(self.tline_column.widget, False, False, 0)
        tline_hbox_2.pack_start(self.tline_canvas.widget, True, True, 0)
        tline_hbox_2.pack_start(self.tline_y_page.widget, False, False, 0)
        
        self.tline_hbox_2 = tline_hbox_2

        # Comp mode selector

        tds = guiutils.get_cairo_image("top_down")
        tdds = guiutils.get_cairo_image("top_down_auto")
        sas = guiutils.get_cairo_image("standard_auto")
        fta = guiutils.get_cairo_image("full_track_auto")
        surfaces = [tds, tdds, sas, fta]
        comp_mode_launcher = guicomponents.ImageMenuLaunchPopover(projectaction.compositing_mode_menu_launched, surfaces, 22, 20)
        comp_mode_launcher.surface_x = 0
        comp_mode_launcher.surface_y = 4
        comp_mode_launcher.widget.set_tooltip_markup(_("Current Sequence Compositing Mode"))
        self.comp_mode_launcher = comp_mode_launcher

        # Bottom row filler
        self.left_corner = guicomponents.TimeLineLeftBottom(comp_mode_launcher, None)
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
        self.notebook_frame = guiutils.get_panel_etched_frame(self.notebook)
        guiutils.set_margins(self.notebook_frame, 0, 0, 0, 1)
            
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
        if editorpersistance.prefs.audio_master_position_is_top_row == False:
            self.tline_pane.pack_end(self._get_audio_master_meter(), False, False, 0)

        # -------------- appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT, by default this has filter select panel.
        self.bottom_right_panel, widget_is_notebook  = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_BOTTOM_ROW_RIGHT)
        if self.bottom_right_panel != None:
            self.bottom_right_frame = guiutils.get_panel_etched_frame(self.bottom_right_panel)
            guiutils.set_margins(self.bottom_right_frame, 0, 0, 0, 1)

        else:
            self.bottom_right_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position.
        self.tline_pane.pack_start(self.bottom_right_frame, False, False, 0) # self.tline_pane was already created in self._init_tline().


        # ---------------------------------------------------------------- LEFT  COLUMN
        self.left_column_panel, widget_is_notebook = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_LEFT_COLUMN)
        if self.left_column_panel != None:
            self.left_column_frame = guiutils.get_panel_etched_frame(self.left_column_panel)
            guiutils.set_margins(self.left_column_frame, 0, 0, 0, 1)

        else:
            self.left_column_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position.

        # ---------------------------------------------------------------- RIGHT COLUMN
        self.right_column_panel, widget_is_notebook = editorlayout.create_position_widget(self, appconsts.PANEL_PLACEMENT_RIGHT_COLUMN)
        if self.right_column_panel != None:
            self.right_column_frame = guiutils.get_panel_etched_frame(self.right_column_panel)
            guiutils.set_margins(self.right_column_frame, 0, 0, 0, 1)

        else:
            self.right_column_frame = guiutils.get_empty_panel_etched_frame() # to be filled later if panels are added into this position.
            
        # Top row paned
        self.top_paned = gtkbuilder.HPaned()
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
        if editorpersistance.prefs.audio_master_position_is_top_row == True:
            self.top_row_hbox.pack_end(self._get_audio_master_meter(), False, False, 0)

        editorlayout.apply_tabs_positions()
        
    def _init_app_menu(self, ui):
        self.menubar = menubar.get_menu()

    def init_compositing_mode_menu(self):
        try:
            appactions.update_compositing_mode_action_state()
        except:
            pass

    def change_compositing_mode_from_menu(self, action, variant):
        if variant.get_string() == "fulltrackauto":
            projectaction.change_current_sequence_compositing_mode(w, appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK)
        else:
            projectaction.change_current_sequence_compositing_mode(w, appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE)

    def fill_recents_menu_widget(self, callback):
        menubar.fill_recents_menu_widget(projectaction.open_recent_project)
        
    def change_windows_preference(self, action, value):
        action.set_state(value)

        if value.get_string() == "singlewindow":
            new_window_layout = appconsts.SINGLE_WINDOW
        else:
            new_window_layout = appconsts.TWO_WINDOWS
                                
        editorpersistance.prefs.global_layout = new_window_layout
        editorpersistance.save()

        primary_txt = _("Global Window Mode changed")
        secondary_txt = _("Application restart required for the new layout choice to take effect.")

        dialogutils.info_message(primary_txt, secondary_txt, self.window)

    # --------------------------------------------------------------- LAYOUT CHANGES
    # These methods are called from app menu and they show and hide panels or
    # move them around. When layout is created or startup we make sure that there is enough information  to
    # do the changes, e.g. some caontainer either exist are are set to None etc. 

    def show_tools_dock_change_from_menu(self, action, variant):
        if variant.get_string() == "middlebar":
            self._do_show_tools_middlebar()
        else:
            self._do_show_tools_dock()
 
    def _show_tools_middlebar(self, widget):
        if widget.get_active() == False:
            return
        
        self._do_show_tools_middlebar()
    
    def _do_show_tools_middlebar(self):
        editorpersistance.prefs.tools_selection = appconsts.TOOL_SELECTOR_IS_MENU
        editorpersistance.save()

        if self.tool_dock != None:
            self.tline_box.remove(self.tool_dock)

        middlebar.re_create_tool_selector(self)
        middlebar.redo_layout(self)
        workflow.select_default_tool()

        try:
             appactions.update_tools_view_action_state()
        except:
            pass # This gets called too early on startup when placing widgets but is needed at runtime.

    def set_audiomaster_position(self, action, value):
        action.set_state(value)

        if value.get_string() == "toprow":
            new_value = True
        else:
            new_value = False
        
        if new_value == editorpersistance.prefs.audio_master_position_is_top_row:
            return
            
        editorpersistance.prefs.audio_master_position_is_top_row = new_value
        editorpersistance.save()

        if new_value == True:
            self.tline_pane.remove(self._get_audio_master_meter())
            self.top_row_hbox.pack_end(self._get_audio_master_meter(), False, False, 0)
        else:
            self.top_row_hbox.remove(self._get_audio_master_meter())
            self.tline_pane.pack_end(self._get_audio_master_meter(), False, False, 0)

    def _get_audio_master_meter(self):
        if self.audio_master_meter == None:
            self. audio_master_meter = audiomonitoring.get_master_meter()
        
        return self.audio_master_meter

    def _show_tools_dock(self, widget):
        if widget.get_active() == False:
            return

        self._do_show_tools_dock()

    def _do_show_tools_dock(self):
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

        try:
             appactions.update_tools_view_action_state()
        except:
            pass # This gets called too early on startup when placing widgets but is needed at runtime.

    def update_tool_dock(self):
        self.tline_box.remove(self.tool_dock)

        self.tool_dock = workflow.get_tline_tool_dock()
        self.tool_dock.show_all()

        self.tline_box.pack_start(self.tool_dock, False, False, 0)

    def set_middlebar_visible(self, visible):
        if visible == False:
            self.edit_buttons_frame.remove(self.edit_buttons_row)
            self._do_show_tools_dock()
            gui.tline_scale.widget.set_margin_top(4)
            self.tline_hbox_1.set_margin_top(4)
        else:
            middlebar.re_create_tool_selector(self)
            middlebar.redo_layout(self)
            self.edit_buttons_frame.add(self.edit_buttons_row)
            self.edit_buttons_frame.show()
            self.edit_buttons_row.show()
            self._do_show_tools_middlebar()
            gui.tline_scale.widget.set_margin_top(0)
            self.tline_hbox_1.set_margin_top(0)

    def enable_save(self):
        appactions.set_save_action_sensitive(True)

    def set_save_action_sensitive(self, sensitive):
        appactions.set_save_action_sensitive(sensitive)

    def set_undo_sensitive(self, sensitive):
        appactions.set_undo_sensitive(False)

    def set_redo_sensitive(self, sensitive):
        appactions.set_redo_sensitive(False)
        
    # ----------------------------------------------------------- GUI components monitor, middlebar.
    def _create_monitor_buttons(self):
        self.monitor_switch = guicomponents.MonitorSwitch(self._monitor_switch_handler)
        self.monitor_switch.widget.set_margin_top(1)
        self.monitor_switch.widget.set_margin_right(4)

    def _create_monitor_row_widgets(self):
        self.monitor_tc_info = guicomponents.MonitorMarksTCInfo()

    def _monitor_switch_handler(self, action):
        if action == appconsts.MONITOR_TLINE_BUTTON_PRESSED:
            updater.display_sequence_in_monitor()

        if action == appconsts.MONITOR_CLIP_BUTTON_PRESSED:
            updater.display_clip_in_monitor()

    def connect_player(self, mltplayer):

        pressed_callback_funcs = [monitorevent.prev_pressed,
                                  monitorevent.play_stop_pressed,
                                  monitorevent.next_pressed]

        self.player_buttons.set_callbacks(pressed_callback_funcs)

        # Monitor position bar
        self.pos_bar.set_listener(mltplayer.seek_position_normalized)
        #gui.monitor_waveform_display.set_listener(mltplayer.seek_position_normalized)
        
    def _get_edit_buttons_row(self):
        tools_pixbufs = tlinecursors.get_tools_pixbuffs()

        middlebar.create_edit_buttons_row_buttons(self, tools_pixbufs)

        buttons_row = Gtk.HBox(False, 1)
        middlebar.fill_with_TC_LEFT_pattern(buttons_row, self)

        offset = 2
        buttons_row.set_margin_top(offset)
        buttons_row.set_margin_start(offset)
        buttons_row.set_margin_end(offset)

        return buttons_row

    def _get_monitor_info_box(self):
        tline_info_box = Gtk.HBox(False, 0)
        tline_info_box.pack_start(self.monitor_tc_info.monitor_source, False, False, 0)
        tline_info_box.pack_start(self.monitor_tc_info.monitor_tc, False, False, 0)
        #tline_info_box.pack_start(self.monitor_tc_info.scaling, False, False, 0)
        tline_info_box.pack_start(Gtk.Label(), True, True, 0)
        tline_info_box.pack_start(self.monitor_tc_info.widget, False, False, 0)
        guiutils.set_margins(tline_info_box, 0, 0, 4, 2)
    
        return tline_info_box
        
    def _add_tool_tips(self):
        self.big_TC.set_tooltip_text(_("Timeline current frame timecode"))

        self.view_mode_select.widget.set_tooltip_text(_("Select view mode: Video / Vectorscope/ RGBParade"))
        self.trim_view_select.widget.set_tooltip_text(_("Set trim view and match frames"))

        self.pos_bar.widget.set_tooltip_text(_("Sequence / Media current position"))

    def top_paned_resized(self, w, req):
        pass

    def get_middlebar_required_width(self):
        return middlebar.get_required_width()

# testing
def _apply_test_dimensions(window, test_index, scale):
    dims = [(1920, 1200), (2048, 1152), (2048, 1536), (2560, 1440), (2560, 1600), (3440, 1440), (3840, 2160)]
    w, h = dims[test_index]
    print("unscaled", w, h)
    w = int(w/scale)
    h = int(h/scale)
    print("scaled", w, h)
    window.set_size_request(w, h)

def _this_is_not_used():
    print("THIS WAS USED!!!!!")

