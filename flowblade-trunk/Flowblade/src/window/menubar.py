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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

from gi.repository import Gtk, Gio

import copy

import audiomonitoring
import batchrendering
import callbackbridge
import editorpersistance
from editorstate import APP
import exporting
import gmic
import medialinker
import menuactions
import projectaction
import scripttool
import singletracktransition
import titler


global recent_menu

def get_menu():

    MENU_XML = """
    <interface>
      <menu id="menubar">
        <submenu id="filemenu">
          <attribute name="label">""" + _("File") + """</attribute>
          <section>
            <item>
              <attribute name="label">""" + _("New...") + """</attribute>
              <attribute name="action">app.new</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Open...") + """</attribute>
              <attribute name="action">app.open</attribute>
            </item>
            <submenu id="recentmenu">
                <attribute name="label">""" + _("Open Recent...") + """</attribute>
            </submenu>
          </section>
          <section>
            <item>
              <attribute name="label">""" + _("Save") + """</attribute>
              <attribute name="action">app.save</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Save As...") + """</attribute>
              <attribute name="action">app.saveas</attribute>
            </item>
          </section>
         <section>
            <submenu>
              <attribute name="label">""" + _("Export") + """</attribute>
                 <item>
                  <attribute name="label">""" + _("MLT XML") + """</attribute>
                  <attribute name="action">app.exportxml</attribute>
                 </item>
                  <item>
                    <attribute name="label">""" + _("EDL") + """</attribute>
                    <attribute name="action">app.exportedl</attribute>
                  </item>
                <item>
                  <attribute name="label">""" + _("Current Frame") + """</attribute>
                  <attribute name="action">app.exportcurrentframe</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Current Sequence Audio As Ardour Session") + """</attribute>
                  <attribute name="action">app.exportardour</attribute>
                </item>
            </submenu>
          </section>
          <section>
          <item>
            <attribute name="label">""" + _("Close") + """</attribute>
            <attribute name="action">app.close</attribute>
          </item>
            <item>
              <attribute name="label">""" + _("Quit") + """</attribute>
              <attribute name="action">app.quit</attribute>
            </item>
          </section>
        </submenu>
        <submenu>
          <attribute name="label">""" + _("Edit") + """</attribute>
          <section>
            <item>
              <attribute name="label">""" + _("Copy") + """</attribute>
              <attribute name="action">app.copy</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Paste") + """</attribute>
              <attribute name="action">app.paste</attribute>
            </item>
          </section>
        </submenu>
    <submenu>
      <attribute name="label">""" + _("Sequence") + """</attribute>
      <section>
        <item>
          <attribute name="label">""" + _("Add New Sequence") + """</attribute>
          <attribute name="action">app.addnewsequence</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Edit Selected Sequence") + """</attribute>
            <attribute name="action">app.editselectedsequence</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Delete Selected Sequence") + """</attribute>
            <attribute name="action">app.deleteselectedsequence</attribute>
        </item>
      </section>
      <section>
        <submenu>
            <attribute name="label">""" + _("Compositing Mode") + """</attribute>
        </submenu>
      </section>
      <section>
        <item>
            <attribute name="label">""" + _("Import Another Sequence Into This Sequence...") + """</attribute>
            <attribute name="action">app.importsequence</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Split to new Sequence at Playhead Position") + """</attribute>
            <attribute name="action">app.splitsequence</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Duplicate Sequence") + """</attribute>
            <attribute name="action">app.duplicatesequence</attribute>
        </item>
      </section>
      <section>
        <item>
            <attribute name="label">""" + _("Add Video Track") + """</attribute>
            <attribute name="action">app.addvideotrack</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Add Audio Track") + """</attribute>
            <attribute name="action">app.addaudiotrack</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Delete Video Track") + """</attribute>
            <attribute name="action">app.deletevideotrack</attribute>
        </item>
        <item>
            <attribute name="label">""" + _("Delete Audio Track") + """</attribute>
            <attribute name="action">app.deleteaudiotrack</attribute>
        </item>
      </section>
      <section>
        <item>
            <attribute name="label">""" + _("Change Sequence Tracks Count...") + """</attribute>
            <attribute name="action">app.changesequencetrackcount</attribute>
        </item>
      </section>
      <section>
        <item>
            <attribute name="label">""" + _("Watermark...") + """</attribute>
            <attribute name="action">app.addwatermark</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">""" + _("Tool") + """</attribute>
      <section>
        <item>
          <attribute name="label">""" + _("Titler") + """</attribute>
          <attribute name="action">app.showtitler</attribute>
        </item>
        </section>
        <section>
        <item>
          <attribute name="label">""" + _("Audio Mixer") + """</attribute>
          <attribute name="action">app.showaudiomixer</attribute>
        </item>
        </section>
        <section>
        <item>
          <attribute name="label">""" + _("G'MIC Effects") + """</attribute>
          <attribute name="action">app.showgmic</attribute>
        </item>

        <item>
          <attribute name="label">""" + _("Generator Script Editor") + """</attribute>
          <attribute name="action">app.showgeneratoreditor</attribute>
        </item>
        </section>
        <section>
        <item>
          <attribute name="label">""" + _("Media Relinker") + """</attribute>
          <attribute name="action">app.showrelinker</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">""" + _("Render") + """</attribute>
      <section>
        <item>
          <attribute name="label">""" + _("Add To Batch Render Queue...") + """</attribute>
          <attribute name="action">app.addtobatch</attribute>
        </item>
        <item>
          <attribute name="label">""" + _("Batch Render Queue") + """</attribute>
          <attribute name="action">app.showbatch</attribute>
        </item>
        </section>
        <section>
        <item>
          <attribute name="label">""" + _("Re-render All Rendered Transitions") + """</attribute>
          <attribute name="action">app.rerendertransitions</attribute>
        </item>
        </section>
        <section>
        <item>
          <attribute name="label">""" + _("Render Timeline") + """</attribute>
          <attribute name="action">app.rendertimeline</attribute>
        </item>
      </section>
    </submenu>
        <submenu>
          <attribute name="label">""" + _("Help") + """</attribute>
          <section>
            <item>
              <attribute name="label">""" + _("Contents") + """</attribute>
              <attribute name="action">app.contents</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Contents Web") + """</attribute>
              <attribute name="action">app.contentsweb</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Runtime Environment") + """</attribute>
              <attribute name="action">app.runtime</attribute>
            </item>
            </section>
            <section>
            <item>
              <attribute name="label">""" + _("About") + """</attribute>
              <attribute name="action">app.about</attribute>
            </item>
          </section>
        </submenu>
      </menu>
    </interface>
    """

    builder = Gtk.Builder.new_from_string(MENU_XML, -1)
    menu_model = builder.get_object("menubar")
    
    global recent_menu
    recent_menu = builder.get_object("recentmenu")

    # Create menubar widget
    menubar = Gtk.MenuBar.new_from_model(menu_model)
        
    return menubar

def create_actions():
    _create_action("new", lambda w, a:projectaction.new_project(), "<Ctrl>N")
    _create_action("open", lambda w, a:projectaction.load_project(), "<Ctrl>O")
    _create_action("save", lambda w, a:projectaction.save_project(), "<Ctrl>S")
    _create_action("saveas", lambda w, a:projectaction.save_project_as())
    _create_action("exportxml", lambda w, a:exporting.MELT_XML_export())
    _create_action("exportedl", lambda w, a:exporting.EDL_export())
    _create_action("exportcurrentframe", lambda w, a:exporting.screenshot_export())
    _create_action("exportardour", lambda w, a:exporting.ardour_export())
    _create_action("close", lambda w, a:projectaction.close_project())
    _create_action("quit", lambda w, a:callbackbridge.app_shutdown(), "<Ctrl>Q")

    _create_action("addnewsequence", lambda w, a: projectaction.add_new_sequence())  
    _create_action("editselectedsequence", lambda w, a: projectaction.change_edit_sequence())  
    _create_action("deleteselectedsequence", lambda w, a: projectaction.delete_selected_sequence())  
    _create_action("importsequence", lambda w, a: projectaction.combine_sequences())  
    _create_action("splitsequence", lambda w, a: tlineaction.sequence_split_pressed())  
    _create_action("duplicatesequence", lambda w, a: projectaction.duplicate_sequence())  
    _create_action("addvideotrack", lambda w, a: projectaction.add_video_track())  
    _create_action("addaudiotrack", lambda w, a: projectaction.add_audio_track())  
    _create_action("deletevideotrack", lambda w, a: projectaction.delete_video_track())  
    _create_action("deleteaudiotrack", lambda w, a: projectaction.delete_audio_track())  
    _create_action("changesequencetrackcount", lambda w, a: projectaction.change_sequence_track_count())  
    _create_action("addwatermark", lambda w, a: menuactions.edit_watermark())  
            
    _create_action("showtitler", lambda w, a: titler.show_titler())  
    _create_action("showaudiomixer", lambda w, a: audiomonitoring.show_audio_monitor())  
    _create_action("showgmic", lambda w, a: gmic.launch_gmic())  
    _create_action("showgeneratoreditor", lambda w, a: scripttool.launch_scripttool())  
    _create_action("showrelinker", lambda w, a: medialinker.display_linker())  

    _create_action("addtobatch", lambda w, a: projectaction.add_to_render_queue())
    _create_action("showbatch", lambda w, a: batchrendering.launch_batch_rendering())
    _create_action("rerendertransitions", lambda w, a: singletracktransition.rerender_all_rendered_transitions())
    _create_action("rendertimeline", lambda w, a: projectaction.do_rendering())

    _create_action("contents", lambda w, a:menuactions.quick_reference())
    _create_action("contentsweb", lambda w, a:menuactions.quick_reference_web())
    _create_action("runtime", lambda w, a:menuactions.environment())
    _create_action("about", lambda w, a:menuactions.about())

def _create_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    APP().add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])

def fill_recents_menu_widget(callback):
    """
    Fills menu item with menuitems to open recent projects.
    """
    global recent_menu
    recent_menu.remove_all()

    # Add new menu items
    recent_proj_names = editorpersistance.get_recent_projects()
    if len(recent_proj_names) != 0:
        for i in range (0, len(recent_proj_names)):
            proj_name = recent_proj_names[i]
            recent_menu.append(proj_name, "app.openrecent." + str(i))
            action = Gio.SimpleAction.new("openrecent." + str(i), None)
            action.connect("activate", callback,  copy.deepcopy(i))
            APP().add_action(action)
    else:
        recent_menu.append (_("Empty"), None)

"""

                            
        menu_actions = [
            ('FileMenu', None, _('_File')),
            ('New', None, _('_New...'), '<control>N', None, lambda a:projectaction.new_project()),
            ('Open', None, _('_Open...'), '<control>O', None, lambda a:projectaction.load_project()),
            ('OpenRecent', None, _('Open Recent')),
            ('Save', None, _('_Save'), '<control>S', None, lambda a:projectaction.save_project()),
            ('Save As', None, _('_Save As...'), None, None, lambda a:projectaction.save_project_as()),
            ('ExportMenu', None, _('Export')),
            ('ExportMeltXML', None, _('MLT XML'), None, None, lambda a:exporting.MELT_XML_export()),
            ('ExportEDL', None, _('EDL'), None, None, lambda a:exporting.EDL_export()),
            ('ExportScreenshot', None, _('Current Frame'), None, None, lambda a:exporting.screenshot_export()),
            ('ExportToArdour', None, _('Current Sequence Audio As Ardour Session'), None, None, lambda a:exporting.ardour_export()),
            ('Close', None, _('_Close'), None, None, lambda a:projectaction.close_project()),
            ('Quit', None, _('_Quit'), '<control>Q', None, lambda a:callbackbridge.app_shutdown()),
            ('EditMenu', None, _('_Edit')),
            ('Undo', None, _('_Undo'), '<control>Z', None, undo.do_undo_and_repaint),
            ('Redo', None, _('_Redo'), '<control>Y', None, undo.do_redo_and_repaint),
            ('Cut', None, _('Cut'), '<control>X', None, lambda a:copypaste.cut_action()),
            ('Copy', None, _('Copy'), '<control>C', None, lambda a:copypaste.copy_action()),
            ('Paste', None, _('Paste'), '<control>V', None, lambda a:copypaste.paste_action()),
            ('PasteFilters', None, _('Paste Filters / Properties'), '<control><alt>V', None, lambda a:tlineaction.do_timeline_filters_paste()),
            ('AddFromMonitor', None, _('Add Monitor Clip')),
            ('AppendClip', None, _('Append'), None, None, lambda a:tlineaction.append_button_pressed()),
            ('InsertClip', None, _('Insert'), None, None, lambda a:tlineaction.insert_button_pressed()),
            ('ThreepointOverWriteClip', None, _('Three Point Overwrite'), None, None, lambda a:tlineaction.three_point_overwrite_pressed()),
            ('RangeOverWriteClip', None, _('Range Overwrite'), None, None, lambda a:tlineaction.range_overwrite_pressed()),
            ('CutClip', None, _('Cut Clip At Playhead'), None, None, lambda a:tlineaction.cut_pressed()),
            ('SequenceSplit', None, _('Split to new Sequence at Playhead Position'), None, None, lambda a:tlineaction.sequence_split_pressed()),
            ('SequenceDuplicate', None, _('Duplicate Sequence'), None, None, lambda a:projectaction.duplicate_sequence()),
            ('DeleteClip', None, _('Lift'), None, None, lambda a:tlineaction.lift_button_pressed()),
            ('SpliceOutClip', None, _('Splice Out'), None, None, lambda a:tlineaction.splice_out_button_pressed()),
            ('ResyncSelected', None, _('Resync Track'),  None, None, lambda a:tlineaction.resync_button_pressed()),
            ('SetSyncParent', None, _('Set Sync Parent'), None, None, lambda a:_this_is_not_used()),
            ('AddTransition', None, _('Add Single Track Transition'), None, None, lambda a:singletracktransition.add_transition_menu_item_selected()),
            ('ClearFilters', None, _('Clear Filters'), None, None, lambda a:clipmenuaction.clear_filters()),
            ('Timeline', None, _('Timeline')),
            ('FiltersOff', None, _('All Filters Off'), None, None, lambda a:tlineaction.all_filters_off()),
            ('FiltersOn', None, _('All Filters On'), None, None, lambda a:tlineaction.all_filters_on()),
            ('SyncCompositors', None, _('Sync All Compositors'), None, None, lambda a:tlineaction.sync_all_compositors()),
            ('AddVideoTrack', None, _('Add Video Track'), None, None, lambda a:projectaction.add_video_track()),
            ('AddAudioTrack', None, _('Add Audio Track'), None, None, lambda a:projectaction.add_audio_track()),
            ('DeleteVideoTrack', None, _('Delete Video Track'), None, None, lambda a:projectaction.delete_video_track()),
            ('DeleteAudioTrack', None, _('Delete Audio Track'), None, None, lambda a:projectaction.delete_audio_track()),
            ('ChangeSequenceTracks', None, _('Change Sequence Tracks Count...'), None, None, lambda a:projectaction.change_sequence_track_count()),
            ('Watermark', None, _('Watermark...'), None, None, lambda a:menuactions.edit_watermark()),
            ('ProfilesManager', None, _('Profiles Manager'), None, None, lambda a:menuactions.profiles_manager()),
            ('Preferences', None, _('Preferences'), None, None, lambda a:preferenceswindow.preferences_dialog()),
            ('ViewMenu', None, _('View')),
            ('FullScreen', None, _('Fullscreen'), 'F11', None, lambda a:menuactions.toggle_fullscreen()),
            ('ProjectMenu', None, _('Project')),
            ('AddMediaClip', None, _('Add Video, Audio or Image...'), None, None, lambda a: projectaction.add_media_files()),
            ('AddMediaFolder', None, _('Add Media From Folder...'), None, None, lambda a: projectaddmediafolder.show_add_media_folder_dialog()),
            ('AddImageSequence', None, _('Add Image Sequence...'), None, None, lambda a:projectaction.add_image_sequence()),
            ('AddTitle', None, _('Add Title...'), None, None, lambda a: titler.show_titler()),
            ('CreateColorClip', None, _('Add Color Clip...'), None, None, lambda a:patternproducer.create_color_clip()),
            ('BinMenu', None, _('Bins')),
            ('AddBin', None, _('Add Bin'), None, None, lambda a:projectaction.add_new_bin()),
            ('DeleteBin', None, _('Delete Selected Bin'), None, None, lambda a:projectaction.delete_selected_bin()),
            ('SequenceMenu', None, _('Sequence')),
            ('AddSequence', None, _('Add New Sequence'), None, None, lambda a:projectaction.add_new_sequence()),
            ('EditSequence', None, _('Edit Selected Sequence'), None, None, lambda a:projectaction.change_edit_sequence()),
            ('DeleteSequence', None, _('Delete Selected Sequence'), None, None, lambda a:projectaction.delete_selected_sequence()),
            ('CompositingModeMenu', None, _('Compositing Mode')),
            ('TimelineRenderingMenu', None, _('Timeline Rendering')),
            ('AddMediaPlugin', None, _('Add Generator...'), None, None, lambda a:mediaplugin.show_add_media_plugin_window()),
            ('LoadMediaPluginScript', None, _('Load Generator Script...'), None, None,lambda w: containerclip.create_fluxity_media_item()),
            ('CreateSelectionCompound', None, _('From Selected Clips'), None, None, lambda a:projectaction.create_selection_compound_clip()),
            ('CreateBoxCompound', None, _('From Box Selection'), None, None, lambda a:projectaction.create_box_compound_clip()),
            ('CreateRangeCompound', None, _('From Timeline Range'), None, None, lambda a:projectaction.create_range_compound_clip()),
            ('CreateSequenceCompound', None, _('From Current Sequence'), None, None, lambda a:projectaction.create_sequence_compound_clip()),
            ('CreateSequenceLinkContainerItem', None, _("Add Sequence Link Container Clip..."), None, None, lambda a:projectaction.create_sequence_link_container()),
            ('CreateSequenceFreezeCompound', None, _('From Current Sequence With Freeze Frame at Playhead Position'), None, None, lambda a:projectaction.create_sequence_freeze_frame_compound_clip()),
            ('AudioSyncCompoundClip', None, _('Audio Sync Merge Clip From 2 Media Items '), None, None, lambda a:audiosync.create_audio_sync_compound_clip()),
            ('ImportProjectMedia', None, _('Import Media From Project...'), None, None, lambda a:projectaction.import_project_media()),
            ('ContainerClipsMenu', None, _('Create Container Clip')),
            ('CreateGMicContainerItem', None, _("From G'Mic Script"), None, None, lambda a:containerclip.create_gmic_media_item()),
            ('CombineSequences', None, _('Import Another Sequence Into This Sequence...'), None, None, lambda a:projectaction.combine_sequences()),
            ('LogClipRange', None, _('Log Marked Clip Range'), '<control>L', None, lambda a:medialog.log_range_clicked()),
            ('RecreateMediaIcons', None, _('Recreate Media Icons...'), None, None, lambda a:menuactions.recreate_media_file_icons()),
            ('ShowProjectInfo', None, _('Project Info and Data'), None, None, lambda a:projectaction.show_project_info()),
            ('RemoveUnusedMedia', None, _('Remove Unused Media...'), None, None, lambda a:projectaction.remove_unused_media()),
            ('ChangeProfile', None, _("Change Project Profile..."), None, None, lambda a: projectaction.change_project_profile()),
            ('ProxyManager', None, _('Proxy Manager'), None, None, lambda a:proxytranscodemanager.show_proxy_manager_dialog()),
            ('TranscodeManager', None, _('Transcode Manager'), None, None, lambda a:proxytranscodemanager.show_transcode_manager_dialog()),
            ('DataStoreManager', None, _('Data Store Manager'), None, None, lambda a:projectdatavaultgui.show_project_data_manager_window()),
            ('ProjectDataInfo', None, _('Project Data'), None, None, lambda a:projectdatavaultgui.show_current_project_data_store_info_window()),
            ('RenderMenu', None, _('Render')),
            ('AddToQueue', None, _('Add To Batch Render Queue...'), None, None, lambda a:projectaction.add_to_render_queue()),
            ('BatchRender', None, _('Batch Render Queue'), None, None, lambda a:batchrendering.launch_batch_rendering()),
            ('ReRenderTransitionsFades', None, _('Rerender All Rendered Transitions'), None, None, lambda a:singletracktransition.rerender_all_rendered_transitions()),
            ('Render', None, _('Render Timeline'), None, None, lambda a:projectaction.do_rendering()),
            ('ToolsMenu', None, _('Tools')),
            ('Titler', None, _('Titler'), None, None, lambda a:titler.show_titler()),
            ('AudioMix', None, _('Audio Mixer'), None, None, lambda a:audiomonitoring.show_audio_monitor()),
            ('GMIC', None, _("G'MIC Effects"), None, None, lambda a:gmic.launch_gmic()),
            ('Scripttool', None, _("Generator Script Editor"), None, None, lambda a:scripttool.launch_scripttool()),
            ('MediaLink', None, _('Media Relinker'), None, None, lambda a:medialinker.display_linker()),
            ('HelpMenu', None, _('_Help')),
            ('QuickReference', None, _('Contents'), None, None, lambda a:menuactions.quick_reference()),
            ('QuickReferenceWeb', None, _('Contents Web'), None, None, lambda a:menuactions.quick_reference_web()),
            ('Environment', None, _('Runtime Environment'), None, None, lambda a:menuactions.environment()),
            ('KeyboardShortcuts', None, _('Keyboard Shortcuts'), None, None, lambda a:shortcutsdialog.keyboard_shortcuts_dialog(self.window, workflow.get_tline_tool_working_set, menuactions.keyboard_shortcuts_callback, menuactions.change_single_shortcut, menuactions.keyboard_shortcuts_menu_item_selected_callback)),
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
            <ui>
                <menubar name='MenuBar'>
                    <menu action='FileMenu'>
                        <menuitem action='New'/>
                        <menuitem action='Open'/>
                        <menu action='OpenRecent'/>
                        <separator/>
                        <menuitem action='Save'/>
                        <menuitem action='Save As'/>
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
                        <menuitem action='Cut'/>
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
                        <menuitem action='SpliceOutClip'/>
                        <menuitem action='DeleteClip'/>
                        <separator/>
                        <menuitem action='SyncCompositors'/>
                        <menuitem action='ResyncSelected'/>
                        <separator/>
                        <menuitem action='FiltersOff'/>
                        <menuitem action='FiltersOn'/>
                        <menuitem action='ClearFilters'/>
                        <separator/>
                        <menuitem action='AddTransition'/>
                        <separator/>
                        <menuitem action='DataStoreManager'/>
                        <separator/>
                        <menuitem action='ProfilesManager'/>
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
                        <menuitem action='AddMediaPlugin'/>
                        <menuitem action='AddTitle'/>
                        <menuitem action='CreateColorClip'/>
                        <separator/>
                        <menu action='ContainerClipsMenu'>
                            <menuitem action='CreateSelectionCompound'/>
                            <menuitem action='CreateBoxCompound'/>
                            <menuitem action='CreateRangeCompound'/>
                            <menuitem action='CreateSequenceCompound'/>
                            <menuitem action='AudioSyncCompoundClip'/>
                            <separator/>
                            <menuitem action='CreateGMicContainerItem'/>
                        </menu>
                        <menuitem action='CreateSequenceLinkContainerItem'/>
                        <separator/>
                        <menuitem action='AddMediaFolder'/>
                        <menuitem action='ImportProjectMedia'/>
                        <menuitem action='LoadMediaPluginScript'/>
                        <separator/>
                        <menu action='BinMenu'>
                            <menuitem action='AddBin'/>
                            <menuitem action='DeleteBin'/>
                        </menu>
                        <separator/>
                        <menuitem action='LogClipRange'/>
                        <separator/>
                        <menuitem action='RecreateMediaIcons'/>
                        <menuitem action='RemoveUnusedMedia'/>
                        <separator/>
                        <menuitem action='ChangeProfile'/>
                        <separator/>
                        <menuitem action='ShowProjectInfo'/>
                        <separator/>
                        <menuitem action='ProxyManager'/>
                        <menuitem action='TranscodeManager'/>
                    </menu>
                    <menu action='SequenceMenu'>
                        <menuitem action='AddSequence'/>
                        <menuitem action='EditSequence'/>
                        <menuitem action='DeleteSequence'/>
                        <separator/>
                        <menu action='CompositingModeMenu'/>
                        <separator/>
                        <menuitem action='CombineSequences'/>
                        <menuitem action='SequenceSplit'/>
                        <menuitem action='SequenceDuplicate'/>
                        <separator/>
                        <menuitem action='AddVideoTrack'/>
                        <menuitem action='AddAudioTrack'/>
                        <menuitem action='DeleteVideoTrack'/>
                        <menuitem action='DeleteAudioTrack'/>
                        <separator/>
                        <menuitem action='ChangeSequenceTracks'/>
                        <separator/>
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
                        <menuitem action='QuickReferenceWeb'/>
                        <menuitem action='Environment'/>
                        <separator/>
                        <menuitem action='About'/>
                    </menu>
              </menubar>
            </ui>
"""
        