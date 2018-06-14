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
from gi.repository import Pango

import app
import appconsts
import audiomonitoring
import audiosync
import batchrendering
import boxmove
import clipeffectseditor
import clipmenuaction
import compositeeditor
import dialogs
import dialogutils
import diskcachemanagement
import dnd
import editevent
import editorpersistance
import editorstate
import exporting
import glassbuttons
import gmic
import gui
import guicomponents
import guiutils
import medialinker
import medialog
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
import projectinfogui
import proxyediting
import titler
import tlineaction
import tlinewidgets
import trackaction
import toolnatron
import updater
import undo
import workflow

# GUI size params
MEDIA_MANAGER_WIDTH = 110
MONITOR_AREA_WIDTH = 600 # defines app min width with NOTEBOOK_WIDTH 400 for small

IMG_PATH = None

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

def top_level_project_panel():
    if editorpersistance.prefs.top_level_project_panel == True and editorstate.screen_size_small_width() == False and editorstate.screen_size_large_height() == True:
        return True
    
    return False


class EditorWindow:

    def __init__(self):
        global IMG_PATH
        IMG_PATH = respaths.IMAGE_PATH 

        # Read cursors
        global INSERTMOVE_CURSOR, OVERWRITE_CURSOR, TWOROLL_CURSOR, ONEROLL_CURSOR, \
        ONEROLL_NO_EDIT_CURSOR, TWOROLL_NO_EDIT_CURSOR, SLIDE_CURSOR, SLIDE_NO_EDIT_CURSOR, \
        MULTIMOVE_CURSOR, MULTIMOVE_NO_EDIT_CURSOR, ONEROLL_RIPPLE_CURSOR, ONEROLL_TOOL, \
        OVERWRITE_BOX_CURSOR, OVERWRITE_TOOL, CUT_CURSOR, KF_TOOL_CURSOR
        
        INSERTMOVE_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "insertmove_cursor.png")
        OVERWRITE_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "overwrite_cursor.png")
        OVERWRITE_BOX_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "overwrite_cursor_box.png")
        TWOROLL_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "tworoll_cursor.png")
        ONEROLL_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "oneroll_cursor.png")
        SLIDE_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "slide_cursor.png")
        ONEROLL_NO_EDIT_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "oneroll_noedit_cursor.png")
        TWOROLL_NO_EDIT_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "tworoll_noedit_cursor.png")
        SLIDE_NO_EDIT_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "slide_noedit_cursor.png")
        MULTIMOVE_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "multimove_cursor.png")
        MULTIMOVE_NO_EDIT_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "multimove_cursor.png")
        ONEROLL_RIPPLE_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "oneroll_cursor_ripple.png")
        ONEROLL_TOOL = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "oneroll_tool.png")
        OVERWRITE_TOOL = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "overwrite_tool.png")
        CUT_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "cut_cursor.png")
        KF_TOOL_CURSOR = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kftool_cursor.png")

        # Context cursors 
        self.context_cursors = {appconsts.POINTER_CONTEXT_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 3, 7),
                                appconsts.POINTER_CONTEXT_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 14, 7),
                                appconsts.POINTER_CONTEXT_TRIM_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_TRIM_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_right.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_BOX_SIDEWAYS:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_MOVE:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 9, 9)}

        # Window
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
            ('Close', None, _('_Close'), None, None, lambda a:projectaction.close_project()),
            ('Quit', None, _('_Quit'), '<control>Q', None, lambda a:app.shutdown()),
            ('EditMenu', None, _('_Edit')),
            ('Undo', None, _('_Undo'), '<control>Z', None, undo.do_undo_and_repaint),
            ('Redo', None, _('_Redo'), '<control>Y', None, undo.do_redo_and_repaint),
            ('Copy', None, _('Copy'), '<control>C', None, lambda a:tlineaction.do_timeline_objects_copy()),
            ('Paste', None, _('Paste'), '<control>V', None, lambda a:tlineaction.do_timeline_objects_paste()),
            ('PasteFilters', None, _('Paste Filters'), '<control><alt>V', None, lambda a:tlineaction.do_timeline_filters_paste()),
            ('AddFromMonitor', None, _('Add Monitor Clip')),
            ('AppendClip', None, _('Append'), None, None, lambda a:tlineaction.append_button_pressed()),
            ('InsertClip', None, _('Insert'), None, None, lambda a:tlineaction.insert_button_pressed()),
            ('ThreepointOverWriteClip', None, _('Three Point Overwrite'), None, None, lambda a:tlineaction.three_point_overwrite_pressed()),
            ('RangeOverWriteClip', None, _('Range Overwrite'), None, None, lambda a:tlineaction.range_overwrite_pressed()),
            ('CutClip', None, _('Cut Clip'), None, None, lambda a:tlineaction.cut_pressed()),
            ('SequenceSplit', None, _('Split to new Sequence at Playhead Position'), None, None, lambda a:tlineaction.sequence_split_pressed()),
            ('DeleteClip', None, _('Lift'), None, None, lambda a:tlineaction.lift_button_pressed()),
            ('SpliceOutClip', None, _('Splice Out'), None, None, lambda a:tlineaction.splice_out_button_pressed()),
            ('ResyncSelected', None, _('Resync'), None, None, lambda a:tlineaction.resync_button_pressed()),
            ('SetSyncParent', None, _('Set Sync Parent'), None, None, lambda a:_this_is_not_used()),
            ('AddTransition', None, _('Add Single Track Transition'), None, None, lambda a:tlineaction.add_transition_menu_item_selected()),
            ('AddFade', None, _('Add Single Track Fade'), None, None, lambda a:tlineaction.add_fade_menu_item_selected()),
            ('ClearFilters', None, _('Clear Filters'), None, None, lambda a:clipmenuaction.clear_filters()),
            ('Timeline', None, _('Timeline')),
            ('FiltersOff', None, _('All Filters Off'), None, None, lambda a:tlineaction.all_filters_off()),
            ('FiltersOn', None, _('All Filters On'), None, None, lambda a:tlineaction.all_filters_on()),
            ('SyncCompositors', None, _('Sync All Compositors'), None, None, lambda a:tlineaction.sync_all_compositors()),
            ('CompositorsFadesDefaults', None, _('Set Compositor Auto Fades...'), None, None, lambda a:tlineaction.set_compositors_fades_defaults()),
            ('ChangeSequenceTracks', None, _('Change Sequence Tracks Count...'), None, None, lambda a:projectaction.change_sequence_track_count()),
            ('Watermark', None, _('Watermark...'), None, None, lambda a:menuactions.edit_watermark()),
            ('DiskCacheManager', None, _('Disk Cache Manager'), None, None, lambda a:diskcachemanagement.show_disk_management_dialog()),
            ('ProfilesManager', None, _('Profiles Manager'), None, None, lambda a:menuactions.profiles_manager()),
            ('Preferences', None, _('Preferences'), None, None, lambda a:preferenceswindow.preferences_dialog()),
            ('ViewMenu', None, _('View')),
            ('FullScreen', None, _('Fullscreen'), 'F11', None, lambda a:menuactions.toggle_fullscreen()),
            ('ProjectMenu', None, _('Project')),
            ('AddMediaClip', None, _('Add Media Clip...'), None, None, lambda a: projectaction.add_media_files()),
            ('AddImageSequence', None, _('Add Image Sequence...'), None, None, lambda a:projectaction.add_image_sequence()),
            ('CreateColorClip', None, _('Create Color Clip...'), None, None, lambda a:patternproducer.create_color_clip()),
            ('PatternProducersMenu', None, _('Create Pattern Producer')),
            ('CreateNoiseClip', None, _('Noise'), None, None, lambda a:patternproducer.create_noise_clip()),
            ('CreateBarsClip', None, _('EBU Bars'), None, None, lambda a:patternproducer.create_bars_clip()),
            ('CreateIsingClip', None, _('Ising'), None, None, lambda a:patternproducer.create_icing_clip()),
            ('CreateColorPulseClip', None, _('Color Pulse'), None, None, lambda a:patternproducer.create_color_pulse_clip()),
            ('CreateCountClip', None, _('Count'), None, None, lambda a:patternproducer.create_count_clip()),
            ('CompoundClipsMenu', None, _('Create Compound Clip')),
            ('CreateSelectionCompound', None, _('From Selected Clips'), None, None, lambda a:projectaction.create_selection_compound_clip()),
            ('CreateSequenceCompound', None, _('From Current Sequence'), None, None, lambda a:projectaction.create_sequence_compound_clip()),
            ('AudioSyncCompoundClip', None, _('Audio Sync Merge Clip From 2 Media Items '), None, None, lambda a:audiosync.create_audio_sync_compound_clip()),
            ('ImportProjectMedia', None, _('Import Media From Project...'), None, None, lambda a:projectaction.import_project_media()),
            ('CombineSequences', None, _('Import Another Sequence Into This Sequence...'), None, None, lambda a:projectaction.combine_sequences()),
            ('LogClipRange', None, _('Log Marked Clip Range'), '<control>L', None, lambda a:medialog.log_range_clicked()),
            ('RecreateMediaIcons', None, _('Recreate Media Icons...'), None, None, lambda a:menuactions.recreate_media_file_icons()),
            ('RemoveUnusedMedia', None, _('Remove Unused Media...'), None, None, lambda a:projectaction.remove_unused_media()),
            ('JackAudio', None, _("JACK Audio..."), None, None, lambda a: menuactions.jack_output_managing()),
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
            ('NatronAnimations', None, _("Natron Animations"),None, None, lambda a:toolnatron.launch_natron_animations_tool()),
            ('MediaLink', None, _('Media Relinker'), None, None, lambda a:medialinker.display_linker()),
            ('HelpMenu', None, _('_Help')),
            ('QuickReference', None, _('Contents'), None, None, lambda a:menuactions.quick_reference()),
            ('Environment', None, _('Runtime Environment'), None, None, lambda a:menuactions.environment()),
            ('KeyboardShortcuts', None, _('Keyboard Shortcuts'), None, None, lambda a:dialogs.keyboard_shortcuts_dialog(self.window, menuactions.keyboard_shortcuts_callback)),
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
                    <menuitem action='SyncCompositors'/>
                    <menuitem action='ClearFilters'/>
                    <separator/>
                    <menu action='Timeline'>
                        <menuitem action='FiltersOff'/>
                        <menuitem action='FiltersOn'/>
                    </menu>
                    <separator/>
                    <menuitem action='AddTransition'/>
                    <menuitem action='AddFade'/>
                    <separator/>
                    <menuitem action='ChangeSequenceTracks'/>
                    <menuitem action='Watermark'/>
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
                    <separator/>
                    <menuitem action='CreateColorClip'/>
                    <menu action='PatternProducersMenu'>
                        <menuitem action='CreateNoiseClip'/>
                        <menuitem action='CreateColorPulseClip'/>
                        <menuitem action='CreateIsingClip'/> 
                        <menuitem action='CreateBarsClip'/>    
                    </menu>
                    <menu action='CompoundClipsMenu'>
                        <menuitem action='CreateSelectionCompound'/>
                        <menuitem action='CreateSequenceCompound'/>
                        <menuitem action='AudioSyncCompoundClip'/>
                    </menu>
                    <separator/>
                    <menuitem action='ImportProjectMedia'/>
                    <menuitem action='CombineSequences'/>
                    <separator/>
                    <menuitem action='LogClipRange'/>
                    <separator/>
                    <menuitem action='SequenceSplit'/>
                    <separator/>
                    <menuitem action='RecreateMediaIcons'/>
                    <menuitem action='RemoveUnusedMedia'/>
                    <separator/>
                    <menuitem action='ChangeProfile'/>
                    <separator/>
                    <menuitem action='ProxyManager'/>
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
                    <menuitem action='NatronAnimations'/>
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
        
        # Create UIManager and add accelators to window
        ui = Gtk.UIManager()
        ui.insert_action_group(action_group, 0)
        ui.add_ui_from_string(menu_string)
        accel_group = ui.get_accel_group()
        self.window.add_accel_group(accel_group)

        # Get menu bar
        self.menubar = ui.get_widget('/MenuBar')
        
        # Set reference to UI manager and acclegroup
        self.uimanager = ui
        self.accel_group = accel_group

        # Add recent projects to menu
        editorpersistance.fill_recents_menu_widget(ui.get_widget('/MenuBar/FileMenu/OpenRecent'), projectaction.open_recent_project)

        # Disable audio mixer if not available
        if editorstate.audio_monitoring_available == False:
            ui.get_widget('/MenuBar/ToolsMenu/AudioMix').set_sensitive(False)

        # Media panel
        self.bin_list_view = guicomponents.BinTreeView(
                                        projectaction.bin_selection_changed, 
                                        projectaction.bin_name_edited,
                                        projectaction.bins_panel_popup_requested)
        dnd.connect_bin_tree_view(self.bin_list_view.treeview, projectaction.move_files_to_bin)
        self.bin_list_view.set_property("can-focus",  True)
        

        self.bins_panel = panels.get_bins_tree_panel(self.bin_list_view)
        self.bins_panel.set_size_request(MEDIA_MANAGER_WIDTH, 10) # this component is always expanded, so 10 for minimum size ok

        self.media_list_view = guicomponents.MediaPanel(projectaction.media_file_menu_item_selected,
                                                        updater.set_and_display_monitor_media_file,
                                                        projectaction.media_panel_popup_requested)
    
    
        view = Gtk.Viewport()
        view.add(self.media_list_view.widget)
        view.set_shadow_type(Gtk.ShadowType.NONE)
    
        self.media_scroll_window = Gtk.ScrolledWindow()
        self.media_scroll_window.add(view)
        self.media_scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.media_scroll_window.set_size_request(guicomponents.MEDIA_OBJECT_WIDGET_WIDTH * 2 + 70, guicomponents.MEDIA_OBJECT_WIDGET_HEIGHT)
        self.media_scroll_window.show_all()

        media_panel = panels.get_media_files_panel(
                                self.media_scroll_window,
                                lambda w,e: projectaction.add_media_files(), 
                                lambda w,e: projectaction.delete_media_files(),
                                projectaction.columns_count_launch_pressed,
                                projectaction.hamburger_pressed,  # lambda w,e: proxyediting.create_proxy_files_pressed(),
                                projectaction.media_filtering_select_pressed)
        guiutils.set_margins(media_panel, 6, 6, 4, 6)
        self.media_panel = media_panel

        # Smallest screens always get bins in same panel as media, others get top level project panel if selected
        if top_level_project_panel() == True:
            self.mm_paned = Gtk.HBox()
            self.mm_paned.add(media_panel)
        else:
            self.mm_paned = Gtk.HPaned()
            self.mm_paned.pack1(self.bins_panel, resize=True, shrink=True)
            self.mm_paned.pack2(media_panel, resize=True, shrink=False)
        #self.mm_paned.set_position(10)

        mm_panel = guiutils.set_margins(self.mm_paned, 0, 0, 0, 0)
        
        # Effects panel
        self.effect_select_list_view = guicomponents.FilterListView()
        self.effect_select_combo_box = Gtk.ComboBoxText()
        self.effect_select_list_view.treeview.connect("row-activated", clipeffectseditor.effect_select_row_double_clicked)
        dnd.connect_effects_select_tree_view(self.effect_select_list_view.treeview)



        clip_editor_panel, info_row = clipeffectseditor.get_clip_effects_editor_panel(
                                        self.effect_select_combo_box,
                                        self.effect_select_list_view)

        clipeffectseditor.widgets.effect_stack_view.treeview.connect("button-press-event",
                                              clipeffectseditor.filter_stack_button_press)
                                              
        effects_editor_panel = guiutils.set_margins(clipeffectseditor.widgets.value_edit_frame, 0, 0, 8, 0)
        
        effects_hbox = Gtk.HBox()
        effects_hbox.set_border_width(0)
        effects_hbox.pack_start(clip_editor_panel, False, False, 0)
        effects_hbox.pack_start(effects_editor_panel, True, True, 0)

        effects_vbox = Gtk.VBox()
        effects_vbox.pack_start(effects_hbox, True, True, 0)
        effects_vbox.pack_start(info_row, False, False, 0)
        
        self.effects_panel = guiutils.set_margins(effects_vbox, 8, 0, 7, 2)
        
        # Compositors panel
        action_row = compositeeditor.get_compositor_clip_panel()
        compositor_editor_panel = guiutils.set_margins(compositeeditor.widgets.value_edit_frame, 0, 0, 4, 0)

        compositors_hbox = Gtk.HBox()
        #compositors_hbox.set_border_width(5)
        compositors_hbox.pack_start(compositor_editor_panel, True, True, 0)

        compositors_vbox = Gtk.VBox()
        compositors_vbox.pack_start(compositors_hbox, True, True, 0)
        compositors_vbox.pack_start(action_row, False, False, 0)
        
        self.compositors_panel = guiutils.set_margins(compositors_vbox, 2, 2, 2, 2) 

        # Render panel
        try:
            render.create_widgets()
            render_panel_left = rendergui.get_render_panel_left(render.widgets)
        except IndexError:
            print "No rendering options found"
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
            if editorstate.screen_size_small_width() == False:
                render_hbox = Gtk.HBox(True, 5)
            else:
                render_hbox = Gtk.HBox(False, 5)             
            render_hbox.pack_start(render_panel_left, True, True, 0)
            render_hbox.pack_start(render_panel_right, True, True, 0)

        render_panel = guiutils.set_margins(render_hbox, 2, 6, 8, 6)

        # Range Log panel
        media_log_events_list_view = medialog.get_media_log_list_view()   
        events_panel = medialog.get_media_log_events_panel(media_log_events_list_view)

        media_log_vbox = Gtk.HBox()
        media_log_vbox.pack_start(events_panel, True, True, 0)
        
        media_log_panel = guiutils.set_margins(media_log_vbox, 6, 6, 6, 6)
        self.media_log_events_list_view = media_log_events_list_view

        # Project Panel / Pop Level Project pane
        # Sequence list
        self.sequence_list_view = guicomponents.SequenceListView(   projectaction.sequence_name_edited,
                                                                    projectaction.sequence_panel_popup_requested)
        seq_panel = panels.get_sequences_panel(
                             self.sequence_list_view,
                             lambda w,e: projectaction.change_edit_sequence(),
                             lambda w,e: projectaction.add_new_sequence(), 
                             lambda w,e: projectaction.delete_selected_sequence())

        if top_level_project_panel() == True:
            # Project info
            project_info_panel = projectinfogui.get_top_level_project_info_panel()
            PANEL_WIDTH = 10
            PANEL_HEIGHT = 150
            top_project_vbox = Gtk.VBox()
            top_project_vbox.pack_start(project_info_panel, False, False, 0)
            top_project_vbox.pack_start(self.bins_panel, True, True, 0)
            top_project_vbox.pack_start(seq_panel, True, True, 0)
            
            top_project_vbox.set_size_request(PANEL_WIDTH, PANEL_HEIGHT)
            top_project_panel = guiutils.set_margins(top_project_vbox, 0, 2, 6, 2)
        else:

            # Notebook project panel for smallest screens
            # Project info
            project_info_panel = projectinfogui.get_project_info_panel()
            
            # Project vbox and panel
            project_vbox = Gtk.VBox()
            project_vbox.pack_start(project_info_panel, False, True, 0)
            project_vbox.pack_start(seq_panel, True, True, 0)
            project_panel = guiutils.set_margins(project_vbox, 0, 2, 6, 2)
        
        # Notebook
        self.notebook = Gtk.Notebook()
        self.notebook.set_size_request(appconsts.NOTEBOOK_WIDTH, appconsts.TOP_ROW_HEIGHT)
        media_label = Gtk.Label(label=_("Media"))
        media_label.no_dark_bg = True
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            self.notebook.append_page(mm_panel, media_label)
        self.notebook.append_page(media_log_panel, Gtk.Label(label=_("Range Log")))
        self.notebook.append_page(self.effects_panel, Gtk.Label(label=_("Filters")))
        self.notebook.append_page(self.compositors_panel, Gtk.Label(label=_("Compositors")))
        if top_level_project_panel() == False:
            self.notebook.append_page(project_panel, Gtk.Label(label=_("Project")))
        self.notebook.append_page(render_panel, Gtk.Label(label=_("Render")))
        self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)

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
        self.player_buttons.widget.set_tooltip_text(_("Prev Frame - Arrow Left\nNext Frame - Arrow Right\nPlay - Space\nStop - Space\nMark In - I\nMark Out - O\nClear Marks\nTo Mark In\nTo Mark Out"))
        if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
            self.player_buttons.no_decorations = True

        self.view_mode_select = guicomponents.get_monitor_view_select_combo(lambda w, e: tlineaction.view_mode_menu_lauched(w, e))
        self.trim_view_select = guicomponents.get_trim_view_select_combo(lambda w, e: monitorevent.trim_view_menu_launched(w, e))
        
        player_buttons_row = Gtk.HBox(False, 0)
        player_buttons_row.pack_start(self.monitor_switch.widget, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(self.player_buttons.widget, False, False, 0)
        player_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        player_buttons_row.pack_start(self.trim_view_select.widget, False, False, 0)
        player_buttons_row.pack_start(self.view_mode_select.widget, False, False, 0)
        player_buttons_row.set_margin_bottom(2)

        # Switch / pos bar row
        sw_pos_hbox = Gtk.HBox(False, 1)
        sw_pos_hbox.pack_start(pos_bar_frame, True, True, 0)
        sw_pos_hbox.set_margin_top(4)
        sw_pos_hbox.set_margin_left(2)
        
        # Video display
        monitor_widget = monitorwidget.MonitorWidget()
        self.tline_display = monitor_widget.get_monitor()
        self.monitor_widget = monitor_widget

        dnd.connect_video_monitor(self.tline_display)

        # Monitor
        monitor_vbox = Gtk.VBox(False, 1)
        monitor_vbox.pack_start(monitor_widget.widget, True, True, 0)
        monitor_vbox.pack_start(sw_pos_hbox, False, True, 0)
        monitor_vbox.pack_start(player_buttons_row, False, True, 0)

        monitor_align = guiutils.set_margins(monitor_vbox, 3, 0, 3, 3)

        monitor_frame = Gtk.Frame()
        monitor_frame.add(monitor_align)
        monitor_frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        monitor_frame.set_size_request(MONITOR_AREA_WIDTH, appconsts.TOP_ROW_HEIGHT)

        # Notebook panel
        notebook_vbox = Gtk.VBox(False, 1)
        notebook_vbox.no_dark_bg = True
        notebook_vbox.pack_start(self.notebook, True, True, 0)

        # Top row paned
        self.top_paned = Gtk.HPaned()
        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            self.top_paned.pack1(notebook_vbox, resize=False, shrink=False)
            self.top_paned.pack2(monitor_frame, resize=True, shrink=False)
        else:
            self.top_paned.pack1(mm_panel, resize=False, shrink=False)
            self.top_paned.pack2(notebook_vbox, resize=True, shrink=False)

        # Top row
        self.top_row_hbox = Gtk.HBox(False, 0)
        if top_level_project_panel() == True:
            self.top_row_hbox.pack_start(top_project_panel, False, False, 0)
        self.top_row_hbox.pack_start(self.top_paned, True, True, 0)
        self._update_top_row()

        # Edit buttons rows
        self.edit_buttons_row = self._get_edit_buttons_row()
        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            self.edit_buttons_frame = Gtk.Frame()
            self.edit_buttons_frame.add(self.edit_buttons_row)
            self.edit_buttons_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        else:
            self.edit_buttons_frame  = self.edit_buttons_row

        # Timeline scale
        self.tline_scale = tlinewidgets.TimeLineFrameScale(modesetting.set_default_edit_mode,  
                                                           updater.mouse_scroll_zoom)

        self.tline_info = Gtk.HBox()
        info_contents = Gtk.Label()
        self.tline_info.add(info_contents)
        self.tline_info.info_contents = info_contents # this switched and saved as member of its container
        info_h = Gtk.HBox()
        info_h.pack_start(self.tline_info, False, False, 0)
        info_h.pack_start(Gtk.Label(), True, True, 0)
        info_h.set_size_request(tlinewidgets.COLUMN_WIDTH - 22 - 22 - 22,# - 22, # room for 3 menu launch buttons 
                                      tlinewidgets.SCALE_HEIGHT)

        marker_surface =  cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "marker.png")
        markers_launcher = guicomponents.get_markers_menu_launcher(tlineaction.marker_menu_lauch_pressed, marker_surface)

        tracks_launcher_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "track_menu_launch.png")
        tracks_launcher = guicomponents.PressLaunch(trackaction.all_tracks_menu_launch_pressed, tracks_launcher_surface)

        levels_launcher_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "audio_levels_menu_launch.png")
        levels_launcher = guicomponents.PressLaunch(trackaction.audio_levels_menu_launch_pressed, levels_launcher_surface)
        
        # Timeline top row
        tline_hbox_1 = Gtk.HBox()
        tline_hbox_1.pack_start(info_h, False, False, 0)
        tline_hbox_1.pack_start(levels_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(tracks_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(markers_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(self.tline_scale.widget, True, True, 0)

        # Timeline column
        self.tline_column = tlinewidgets.TimeLineColumn(
                            trackaction.track_active_switch_pressed,
                            trackaction.track_center_pressed)

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

        # Timeline middle row
        tline_hbox_2 = Gtk.HBox()
        tline_hbox_2.pack_start(self.tline_column.widget, False, False, 0)
        tline_hbox_2.pack_start(self.tline_canvas.widget, True, True, 0)
        
        # Bottom row filler
        self.left_corner = guicomponents.TimeLineLeftBottom()
        self.left_corner.widget.set_size_request(tlinewidgets.COLUMN_WIDTH, 20)

        # Timeline scroller
        self.tline_scroller = tlinewidgets.TimeLineScroller(updater.tline_scrolled)
        
        # Timeline bottom row
        tline_hbox_3 = Gtk.HBox()
        tline_hbox_3.pack_start(self.left_corner.widget, False, False, 0)
        tline_hbox_3.pack_start(self.tline_scroller, True, True, 0)
        
        # Timeline hbox 
        tline_vbox = Gtk.VBox()
        tline_vbox.pack_start(tline_hbox_1, False, False, 0)
        tline_vbox.pack_start(tline_hbox_2, True, True, 0)
        tline_vbox.pack_start(tline_hbox_3, False, False, 0)
        
        # Timeline box 
        self.tline_box = Gtk.HBox()
        self.tline_box.pack_start(tline_vbox, True, True, 0)

        # Timeline pane
        tline_pane = Gtk.VBox(False, 1)
        tline_pane.pack_start(self.edit_buttons_frame, False, True, 0)
        tline_pane.pack_start(self.tline_box, True, True, 0)
        #tline_pane.override_background_color(Gtk.StateFlags.NORMAL, gui.get_bg_color())
        self.tline_pane = tline_pane
    
        # VPaned top row / timeline
        self.app_v_paned = Gtk.VPaned()
        self.app_v_paned.pack1(self.top_row_hbox, resize=False, shrink=False)
        self.app_v_paned.pack2(tline_pane, resize=True, shrink=False)
        self.app_v_paned.no_dark_bg = True


        # Menu box
        # menubar size 348, 28 if w want to center someting her with set_size_request
        self.menubar.set_margin_bottom(4)
        menu_vbox = Gtk.HBox(False, 0)
        menu_vbox.pack_start(guiutils.get_right_justified_box([self.menubar]), False, False, 0)
        menu_vbox.pack_start(Gtk.Label(), True, True, 0)
        menu_vbox.pack_start(self.monitor_source, False, False, 0)
        menu_vbox.pack_start(guiutils.pad_label(24, 10), False, False, 0)
        menu_vbox.pack_start(self.info1, False, False, 0)
        #menu_vbox.pack_start(guiutils.pad_label(32, 10), False, False, 0)
        
        # Pane
        pane = Gtk.VBox(False, 1)
        pane.pack_start(menu_vbox, False, True, 0)
        pane.pack_start(self.app_v_paned, True, True, 0)
        
        # Tooltips
        self._add_tool_tips()

        # GUI preferences
        self._init_gui_to_prefs()

        # Viewmenu initial state
        self._init_view_menu(ui.get_widget('/MenuBar/ViewMenu'))
        
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
            pane2.pack_start(monitor_frame, True, True, 0)
            
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
        
        if top_level_project_panel() == False:
            self.mm_paned.set_position(bin_w)
            
        self.top_paned.set_position(editorpersistance.prefs.top_paned_position)
        self.app_v_paned.set_position(editorpersistance.prefs.app_v_paned_position)

    def _init_view_menu(self, menu_item):
        menu = menu_item.get_submenu()

        # Full Screen -tem is already in menu, we need separator here
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        windows_menu_item = Gtk.MenuItem(_("Window Mode").encode('utf-8'))
        windows_menu =  Gtk.Menu()
        one_window = Gtk.RadioMenuItem()
        one_window.set_label( _("Single Window").encode('utf-8'))

        windows_menu.append(one_window)
        
        two_windows = Gtk.RadioMenuItem.new_with_label([one_window], _("Two Windows").encode('utf-8'))

        if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
            one_window.set_active(True)
        else:
            two_windows.set_active(True)

        one_window.connect("activate", lambda w: self._change_windows_preference(w, appconsts.SINGLE_WINDOW))
        two_windows.connect("activate", lambda w: self._change_windows_preference(w, appconsts.TWO_WINDOWS))
        
        windows_menu.append(two_windows)
        windows_menu_item.set_submenu(windows_menu)
        menu.append(windows_menu_item)
        
        mb_menu_item = Gtk.MenuItem(_("Middlebar Layout").encode('utf-8'))
        mb_menu = Gtk.Menu()
        tc_left = Gtk.RadioMenuItem()
        tc_left.set_label(_("Timecode Left").encode('utf-8'))
        #tc_left.set_active(appconsts)
        tc_left.connect("activate", lambda w: middlebar._show_buttons_TC_LEFT_layout(w))
        mb_menu.append(tc_left)

        tc_middle = Gtk.RadioMenuItem.new_with_label([tc_left], _("Timecode Center").encode('utf-8'))
        tc_middle.connect("activate", lambda w: middlebar._show_buttons_TC_MIDDLE_layout(w))
        mb_menu.append(tc_middle)

        components_centered = Gtk.RadioMenuItem.new_with_label([tc_left], _("Components Centered").encode('utf-8'))
        components_centered.connect("activate", lambda w: middlebar._show_buttons_COMPONETS_CENTERED_layout(w))
        mb_menu.append(components_centered)

        if editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_COMPONENTS_CENTERED:
            components_centered.set_active(True)
        elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_LEFT:
            tc_left.set_active(True)
        else:
            tc_middle.set_active(True)

        mb_menu_item.set_submenu(mb_menu)
        menu.append(mb_menu_item)

        tabs_menu_item = Gtk.MenuItem(_("Tabs Position").encode('utf-8'))
        tabs_menu =  Gtk.Menu()
        tabs_up = Gtk.RadioMenuItem()
        tabs_up.set_label( _("Up").encode('utf-8'))
        tabs_up.connect("activate", lambda w: self._show_tabs_up(w))
        tabs_menu.append(tabs_up)
        
        tabs_down = Gtk.RadioMenuItem.new_with_label([tabs_up], _("Down").encode('utf-8'))
        tabs_down.connect("activate", lambda w: self._show_tabs_down(w))

        if editorpersistance.prefs.tabs_on_top == True:
            tabs_up.set_active(True)
        else:
            tabs_down.set_active(True)

        tabs_menu.append(tabs_down)
        tabs_menu_item.set_submenu(tabs_menu)
        menu.append(tabs_menu_item)

        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        """
        show_monitor_info_item = Gtk.CheckMenuItem(_("Show Monitor Sequence Profile").encode('utf-8'))
        show_monitor_info_item.set_active(editorpersistance.prefs.show_sequence_profile)
        show_monitor_info_item.connect("toggled", lambda w: middlebar._show_monitor_info_toggled(w))
        menu.append(show_monitor_info_item)
        """
        
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)

        interp_menu_item = Gtk.MenuItem(_("Monitor Playback Interpolation").encode('utf-8'))
        interp_menu = Gtk.Menu()
        
        interp_nearest = Gtk.RadioMenuItem()
        interp_nearest.set_label(_("Nearest Neighbour (fast)").encode('utf-8'))
        interp_nearest.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("nearest"))
        interp_menu.append(interp_nearest)
        
        interp_bilinear = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Bilinear (good)").encode('utf-8'))
        interp_bilinear.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("bilinear"))
        interp_menu.append(interp_bilinear)

        interp_bicubic = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Bicubic (better)").encode('utf-8'))
        interp_bicubic.set_active(True)
        interp_bicubic.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("bicubic"))
        interp_menu.append(interp_bicubic)

        interp_hyper = Gtk.RadioMenuItem.new_with_label([interp_nearest], _("Hyper/Lanczos (best)").encode('utf-8'))
        interp_hyper.connect("activate", lambda w: monitorevent.set_monitor_playback_interpolation("hyper"))
        interp_menu.append(interp_hyper)

        interp_menu_item.set_submenu(interp_menu)
        menu.append(interp_menu_item)

        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)        
        
        zoom_in_menu_item = Gtk.MenuItem(_("Zoom In").encode('utf-8'))
        zoom_in_menu_item.connect("activate", lambda w: updater.zoom_in())
        menu.append(zoom_in_menu_item)
        zoom_out_menu_item = Gtk.MenuItem(_("Zoom Out").encode('utf-8'))
        zoom_out_menu_item.connect("activate", lambda w: updater.zoom_out())
        menu.append(zoom_out_menu_item)
        zoom_fit_menu_item = Gtk.MenuItem(_("Zoom Fit").encode('utf-8'))
        zoom_fit_menu_item.connect("activate", lambda w: updater.zoom_project_length())
        menu.append(zoom_fit_menu_item)
                
    def _init_gui_to_prefs(self):
        if editorpersistance.prefs.tabs_on_top == True:
            self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        else:
            self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)

    def _change_windows_preference(self, widget, new_window_layout):
        if widget.get_active() == False:
            return

        editorpersistance.prefs.global_layout = new_window_layout
        editorpersistance.save()
        
        primary_txt = _("Global Window Mode changed")
        secondary_txt = _("Application restart required for the new layout choice to take effect.")
        
        dialogutils.info_message(primary_txt, secondary_txt, self.window)
        
    def _show_tabs_up(self, widget):
        if widget.get_active() == False:
            return
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        editorpersistance.prefs.tabs_on_top = True
        editorpersistance.save()

    def _show_tabs_down(self, widget):
        if widget.get_active() == False:
            return
        self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)
        editorpersistance.prefs.tabs_on_top = False
        editorpersistance.save()

    def _show_vu_meter(self, widget):
        editorpersistance.prefs.show_vu_meter = widget.get_active()
        editorpersistance.save()
        
        self._update_top_row(True)

    def _update_top_row(self, show_all=False):
        self.top_row_hbox.pack_end(audiomonitoring.get_master_meter(), False, False, 0)


        if show_all:
            self.window.show_all()
        
    def _create_monitor_buttons(self):
        self.monitor_switch = guicomponents.MonitorSwitch(self._monitor_switch_handler)
        
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
                         TWOROLL_CURSOR, SLIDE_CURSOR, MULTIMOVE_CURSOR, OVERWRITE_BOX_CURSOR, CUT_CURSOR, KF_TOOL_CURSOR]
        middlebar.create_edit_buttons_row_buttons(self, tools_pixbufs)
    
        buttons_row = Gtk.HBox(False, 1)
        if editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_COMPONENTS_CENTERED:
            middlebar.fill_with_COMPONETS_CENTERED_pattern(buttons_row, self)
        elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_LEFT:
            middlebar.fill_with_TC_LEFT_pattern(buttons_row, self)
        else:
            middlebar.fill_with_TC_MIDDLE_pattern(buttons_row, self)

        buttons_row.set_margin_top(2)
        buttons_row.set_margin_left(2)
        buttons_row.set_margin_right(2)

        return buttons_row

    def _add_tool_tips(self):
        self.big_TC.set_tooltip_text(_("Timeline current frame timecode"))

        self.view_mode_select.widget.set_tooltip_text(_("Select view mode: Video/Vectorscope/RGBParade"))
        
        self.tc.widget.set_tooltip_text(_("Monitor Sequence/Media current frame timecode"))
        self.monitor_source.set_tooltip_text(_("Current Monitor Sequence/Media name"))
    
        self.pos_bar.widget.set_tooltip_text(_("Monitor Sequence/Media current position"))
        
        #self.sequence_editor_b.set_tooltip_text(_("Display Current Sequence on Timeline"))
        #self.clip_editor_b.set_tooltip_text(_("Display Monitor Clip"))

    def set_default_edit_tool(self):
        # First active tool is the default tool. So we need to always have atleast one tool available.
        self.change_tool(editorpersistance.prefs.active_tools[0])

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
        else:
            # We should not hit this
            print "editorwindow.change_tool() else: hit!"
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

    def toggle_trim_ripple_mode(self):
        editorstate.trim_mode_ripple = (editorstate.trim_mode_ripple == False)
        modesetting.stop_looping()
        editorstate.edit_mode = editorstate.ONE_ROLL_TRIM_NO_EDIT
        tlinewidgets.set_edit_mode(None, None)
        self.set_tool_selector_to_mode()
        self.set_tline_cursor(editorstate.EDIT_MODE())
        updater.set_trim_mode_gui()
    
    def toggle_overwrite_box_mode(self):
        editorstate.overwrite_mode_box = (editorstate.overwrite_mode_box == False)
        boxmove.clear_data()
        self.set_tool_selector_to_mode()
        self.set_tline_cursor(editorstate.EDIT_MODE())

    def mode_selector_pressed(self, selector, event):
        workflow.get_tline_tool_popup_menu(selector, event, self.tool_selector_item_activated)
    
    def tool_selector_item_activated(self, selector, tool):
        if tool == appconsts.TLINE_TOOL_INSERT:
            self.handle_insert_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_OVERWRITE:
            self.handle_over_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_TRIM:
            self.handle_one_roll_mode_button_press()
        if tool == appconsts.TLINE_TOOL_RIPPLE_TRIM:
            self.handle_one_roll_ripple_mode_button_press()
        """
            if editorstate.edit_mode != editorstate.ONE_ROLL_TRIM and editorstate.edit_mode != editorstate.ONE_ROLL_TRIM_NO_EDIT:
                self.handle_one_roll_mode_button_press()
            else:
                self.toggle_trim_ripple_mode()
        """
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
            
        self.set_cursor_to_mode()
        self.set_tool_selector_to_mode()
        
    def set_cursor_to_mode(self):
        if editorstate.cursor_on_tline == True:
            self.set_tline_cursor(editorstate.EDIT_MODE())
        else:
            gdk_window = gui.tline_display.get_parent_window();
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
                cursor = self.get_own_cursor(display, OVERWRITE_BOX_CURSOR, 6, 15)
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
            cursor = self.get_own_cursor(display, KF_TOOL_CURSOR, 1, 8)
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
        print self.app_v_paned.get_position()
        print self.top_paned.get_position()
        print self.mm_paned.get_position()

    def _create_monitor_row_widgets(self):
        if editorstate.screen_size_small_height() == True:
            font_desc = "sans bold 8"
        else:
            font_desc = "sans bold 9"

        self.tc = guicomponents.MonitorTCDisplay()
        self.monitor_source = Gtk.Label(label="sequence1")
        self.monitor_source.set_ellipsize(Pango.EllipsizeMode.END)
        self.monitor_source.modify_font(Pango.FontDescription(font_desc))
        self.monitor_source.set_sensitive(False)
        self.info1 = Gtk.Label(label="--:--:--:--")
        self.info1.set_ellipsize(Pango.EllipsizeMode.END)
        self.info1.modify_font(Pango.FontDescription(font_desc))
        self.info1.set_sensitive(False)
        
def _this_is_not_used():
    print "THIS WAS USED!!!!!"

