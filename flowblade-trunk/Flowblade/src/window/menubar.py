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

from gi.repository import Gtk, Gio, GLib

import copy

import appconsts
import audiomonitoring
import batchrendering
import callbackbridge
import containerclip
import editorlayout
import editorpersistance
from editorstate import APP
import exporting
import gmic
import gui
import keygtkactions
import shortcuts
import medialinker
import menuactions
import middlebar
import projectaction
import projectaddmediafolder
import projectdatavaultgui
import proxytranscodemanager
import scripttool
import shortcutsdialog
import singletracktransition
import tlineaction
import titler
import undo
import updater
import workflow

_tline_widgets = None 
_tline_actions = None
 

_recent_menu = None
_panel_positions_menu = None
_tabs_menu = None


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
              <attribute name="label">""" + _("Undo") + """</attribute>
              <attribute name="action">app.undoaction</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Redo") + """</attribute>
              <attribute name="action">app.redoaction</attribute>
            </item>
          </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Cut") + """</attribute>
                  <attribute name="action">app.cutaction</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Copy") + """</attribute>
                  <attribute name="action">app.copyaction</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Paste") + """</attribute>
                  <attribute name="action">app.pasteaction</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Paste Filters / Properties") + """</attribute>
                  <attribute name="action">app.pastefiltersaction</attribute>
                </item>
            </section>
            <section>
            <submenu>
             <attribute name="label">""" + _("Add From Monitor") + """</attribute>
                <section>
                <item>
                  <attribute name="label">""" + _("Append") + """</attribute>
                  <attribute name="action">app.appendfrommonitor</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Insert") + """</attribute>
                  <attribute name="action">app.insertfrommonitor</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Three Point Overwrite") + """</attribute>
                  <attribute name="action">app.threepointoverwrite</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Range Overwrite") + """</attribute>
                  <attribute name="action">app.rangeoverwrite</attribute>
                </item>
                </section>
            </submenu>
            </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Cut Clip At Playhead") + """</attribute>
                  <attribute name="action">app.cutatplayhead</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Lift") + """</attribute>
                  <attribute name="action">app.liftaction</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Splice Out") + """</attribute>
                  <attribute name="action">app.spliceaction</attribute>
                </item>
            </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Resync Track") + """</attribute>
                  <attribute name="action">app.resynctrack</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Sync All Compositors") + """</attribute>
                  <attribute name="action">app.syncallcompositors</attribute>
                </item>
            </section>
            <section> 
                <item>
                  <attribute name="label">""" + _("All Filters Off") + """</attribute>
                  <attribute name="action">app.allfiltersoff</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("All Filters On") + """</attribute>
                  <attribute name="action">app.allfilterson</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Clear Filters") + """</attribute>
                  <attribute name="action">app.clearfilters</attribute>
                </item>
            </section>
            <section> 
                <item>
                  <attribute name="label">""" + _("Add Single Track Transition") + """</attribute>
                  <attribute name="action">app.addtransition</attribute>
                </item>
            </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Data Store Manager") + """</attribute>
                  <attribute name="action">app.showdatastore</attribute>
                </item>
            </section>
            <section> 
                <item>
                  <attribute name="label">""" + _("Profiles Manager") + """</attribute>
                  <attribute name="action">app.showprofilesmanager</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Keyboard Shortcuts") + """</attribute>
                  <attribute name="action">app.showkeyboardshortcuts</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Preferences") + """</attribute>
                  <attribute name="action">app.showpreferences</attribute>
                </item>
            </section>
        </submenu>
        <submenu id="filemenu">
          <attribute name="label">""" + _("View") + """</attribute>
            <section>
                <item>
                    <attribute name="label">""" + _("Fullscreen") + """</attribute>
                    <attribute name="action">app.fullscreen</attribute>
                </item>
            </section>
            <section>
                <submenu>
                  <attribute name="label">""" + _("Window Mode") + """</attribute>
                      <section>
                      <item>
                        <attribute name="label">""" + _("Single Window") + """</attribute>
                        <attribute name="action">app.windowmode</attribute>
                        <attribute name="target">singlewindow</attribute>
                      </item>
                      <item>
                        <attribute name="label">""" + _("Two Windows") + """</attribute>
                        <attribute name="action">app.windowmode</attribute>
                        <attribute name="target">twowindows</attribute>
                      </item>
                      </section>
                </submenu>
                <submenu id="panelpositionsmenu">
                  <attribute name="label">""" + _("Panel Placement") + """</attribute>
                </submenu>
                <submenu id="tabsmenu">
                  <attribute name="label">""" + _("Tabs Positions") + """</attribute>
                </submenu>
                <item>
                  <attribute name="label">""" + _("Middlebar Configuration...") + """</attribute>
                  <attribute name="action">app.showmiddlebarconfig</attribute>
                </item>
                <submenu>
                  <attribute name="label">""" + _("Edit Tool Selection Widget") + """</attribute>
                   <section>
                   <item>
                     <attribute name="label">""" + _("Middlebar Menu") + """</attribute>
                     <attribute name="action">app.tooldockpos</attribute>
                     <attribute name="target">middlebar</attribute>
                   </item>
                   <item>
                     <attribute name="label">""" + _("Dock") + """</attribute>
                     <attribute name="action">app.tooldockpos</attribute>
                     <attribute name="target">dock</attribute>
                   </item>
                   </section>
                </submenu>
                <submenu>
                  <attribute name="label">""" + _("Audio Master Level Meter") + """</attribute>
                      <section>
                      <item>
                        <attribute name="label">""" + _("Top Row") + """</attribute>
                        <attribute name="action">app.audiomasterposition</attribute>
                        <attribute name="target">toprow</attribute>
                      </item>
                      <item>
                        <attribute name="label">""" + _("Bottom Row") + """</attribute>
                        <attribute name="action">app.audiomasterposition</attribute>
                        <attribute name="target">bottomrow</attribute>
                      </item>
                      </section>
                </submenu>
            </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Zoom In") + """</attribute>
                  <attribute name="action">app.zoomin</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Zoom Out") + """</attribute>
                  <attribute name="action">app.zoomout</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Zoom Fit") + """</attribute>
                  <attribute name="action">app.zoomfit</attribute>
                </item>
            </section>
        </submenu>      
        <submenu>
          <attribute name="label">""" + _("Project") + """</attribute>
          <section>
            <item>
              <attribute name="label">""" + _("Add Video, Audio or Image...") + """</attribute>
              <attribute name="action">app.addmedia</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Add Image Sequence...") + """</attribute>
              <attribute name="action">app.addimgseq</attribute>
            </item>
            </section>
            <section>
            <item>
            <attribute name="label">""" + _("Add Generator...") + """</attribute>
            <attribute name="action">app.addgenerator</attribute>
            </item>
            <item>
              <attribute name="label">""" + _("Add Title...") + """</attribute>
              <attribute name="action">app.addtitle</attribute>
            </item>
            <item>
                <attribute name="label">""" + _("Add Color Clip...") + """</attribute>
                <attribute name="action">app.addcolorclip</attribute>
            </item>
            </section>
            <section>
                <submenu>
                  <attribute name="label">""" + _("Create Container Clip") + """</attribute>
                    <section>
                        <item>
                        <attribute name="label">""" + _("From Selected Clips") + """</attribute>
                        <attribute name="action">app.fromselected</attribute>
                        </item>
                        <item>
                        <attribute name="label">""" + _("From Box Selection") + """</attribute>
                        <attribute name="action">app.frombox</attribute>
                        </item>
                        <item>
                        <attribute name="label">""" + _("From Timeline Range") + """</attribute>
                        <attribute name="action">app.fromtimeline</attribute>
                        </item>
                        <item>
                        <attribute name="label">""" + _("From Current Sequence") + """</attribute>
                        <attribute name="action">app.fromcurrentsequence</attribute>
                        </item>
                        </section>
                        <section>
                        <item>
                        <attribute name="label">""" + _("From G'Mic Script") + """</attribute>
                        <attribute name="action">app.fromgmic</attribute>
                        </item>
                    </section>
                </submenu>
                <item>
                <attribute name="label">""" + _("Add Sequence Link Container Clip...") + """</attribute>
                <attribute name="action">app.addsequencelink</attribute>
                </item>
            </section>
            <section>
            <item>
              <attribute name="label">""" + _("Add Media From Folder...") + """</attribute>
              <attribute name="action">app.addfromfolder</attribute>
            </item>
            <item>
            <attribute name="label">""" + _("Import Media From Project...") + """</attribute>
            <attribute name="action">app.importfromproject</attribute>
            </item>
            <item>
            <attribute name="label">""" + _("Load Generator Script...") + """</attribute>
            <attribute name="action">app.loadgeneratorscript</attribute>
            </item>
            </section>
            <section>
            <submenu>
              <attribute name="label">""" + _("Bins") + """</attribute>
                <section>
                    <item>
                        <attribute name="label">""" + _("Add Bin") + """</attribute>
                        <attribute name="action">app.addbinmainmenu</attribute>
                    </item>
                    <item>
                        <attribute name="label">""" + _("'Delete Selected Bin") + """</attribute>
                        <attribute name="action">app.deletebinmainmenu</attribute>
                    </item>
                </section>
                </submenu>
            </section>
            <section>
                <item>
                <attribute name="label">""" + _("Log Marked Clip Range") + """</attribute>
                <attribute name="action">app.logcliprange</attribute>
                </item>
            </section>
            <section>
                <item>
                <attribute name="label">""" + _("Recreate Media Icons...") + """</attribute>
                <attribute name="action">app.recreateicons</attribute>
                </item>
                <item>
                <attribute name="label">""" + _("Remove Unused Media...") + """</attribute>
                <attribute name="action">appremoveunusedmedia.</attribute>
                </item>
            </section>
            <section>
                <item>
                <attribute name="label">""" + _("Change Project Profile...") + """</attribute>
                <attribute name="action">app.changeprofile</attribute>
                </item>
            </section>
            <section>
                <item>
                <attribute name="label">""" + _("Project Data") + """</attribute>
                <attribute name="action">app.projectinfoanddata</attribute>
                </item>
            </section>
            <section>
            <item>
            <attribute name="label">""" + _("Proxy Manager") + """</attribute>
            <attribute name="action">app.proxymanager</attribute>
            </item>
            <item>
            <attribute name="label">""" + _("Transcode Manager") + """</attribute>
            <attribute name="action">app.transcodemanager</attribute>
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
          <section>
          <item>
            <attribute name="label">""" + _("Compositors Free Move") + """</attribute>
            <attribute name="action">app.compositing.compmode</attribute>
            <attribute name="target">topdown</attribute>
          </item>
          <item>
            <attribute name="label">""" + _("Standard Full Track") + """</attribute>
            <attribute name="action">app.compositing.compmode</attribute>
            <attribute name="target">fulltrackauto</attribute>
          </item>
          </section>
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
    
    global _recent_menu
    _recent_menu = builder.get_object("recentmenu")
    
    global _panel_positions_menu
    _panel_positions_menu = builder.get_object("panelpositionsmenu")
    
    global _tabs_menu
    _tabs_menu = builder.get_object("tabsmenu")
    
    # Create menubar widget
    menubar = Gtk.MenuBar.new_from_model(menu_model)
        
    return menubar

def create_actions():
    
    root = shortcuts.get_root()
    print(shortcuts.get_shortcut_kb_str(root, "resync_selected", True))
    
    _create_action("new", lambda w, a:projectaction.new_project(), shortcuts.get_shortcut_kb_str(root, "new_project", True))
    _create_action("open", lambda w, a:projectaction.load_project(), shortcuts.get_shortcut_kb_str(root, "open_project", True))
    _create_action("save", lambda w, a:projectaction.save_project(), shortcuts.get_shortcut_kb_str(root, "save_project", True))
    _create_action("saveas", lambda w, a:projectaction.save_project_as())
    _create_action("exportxml", lambda w, a:exporting.MELT_XML_export())
    _create_action("exportedl", lambda w, a:exporting.EDL_export())
    _create_action("exportcurrentframe", lambda w, a:exporting.screenshot_export())
    _create_action("exportardour", lambda w, a:exporting.ardour_export())
    _create_action("close", lambda w, a:projectaction.close_project())
    _create_action("quit", lambda w, a:callbackbridge.app_shutdown(), shortcuts.get_shortcut_kb_str(root, "quit", True))

    _create_action("undoaction", lambda w, a: undo.do_undo_and_repaint(), shortcuts.get_shortcut_kb_str(root, "undo", True))
    _create_action("redoaction", lambda w, a: undo.do_redo_and_repaint(), shortcuts.get_shortcut_kb_str(root, "redo", True))
    _create_action("cutaction", lambda w, a: copypaste.cut_action(), shortcuts.get_shortcut_kb_str(root, "cutaction", True))
    _create_action("copyaction", lambda w, a: copypaste.copy_action())
    _create_action("pasteaction", lambda w, a: copypaste.paste_action())
    _create_action("pastefiltersaction", lambda w, a: tlineaction.do_timeline_filters_paste())
    _create_action("appendfrommonitor", lambda w, a: tlineaction.append_button_pressed())
    _create_action("insertfrommonitor", lambda w, a: tlineaction.insert_button_pressed())
    _create_action("threepointoverwrite", lambda w, a: tlineaction.three_point_overwrite_pressed())
    _create_action("rangeoverwrite", lambda w, a: tlineaction.range_overwrite_pressed())
    _create_action("cutatplayhead", lambda w, a: tlineaction.cut_pressed(), shortcuts.get_shortcut_kb_str(root, "cut", True))
    _create_action("liftaction", lambda w, a: tlineaction.lift_button_pressed())
    _create_action("spliceaction", lambda w, a: tlineaction.splice_out_button_pressed())
    _create_action("resynctrack", lambda w, a: tlineaction.resync_button_pressed())
    _create_action("syncallcompositors", lambda w, a: tlineaction.sync_all_compositors())
    _create_action("allfiltersoff", lambda w, a: tlineaction.all_filters_off())
    _create_action("allfilterson", lambda w, a: tlineaction.all_filters_on())
    _create_action("clearfilters", lambda w, a: clipmenuaction.clear_filters())
    _create_action("addtransition", lambda w, a: singletracktransition.add_transition_menu_item_selected())
    _create_action("showdatastore", lambda w, a: projectdatavaultgui.show_project_data_manager_window())
    _create_action("showprofilesmanager", lambda w, a: menuactions.profiles_manager())
    _create_action("showkeyboardshortcuts", lambda w, a: shortcutsdialog.keyboard_shortcuts_dialog(gui.editor_window.window, workflow.get_tline_tool_working_set, menuactions.keyboard_shortcuts_callback, menuactions.change_single_shortcut, menuactions.keyboard_shortcuts_menu_item_selected_callback))
    _create_action("showpreferences", lambda w, a: preferenceswindow.preferences_dialog())

    _create_action("fullscreen", lambda w, a: menuactions.toggle_fullscreen(), "F11")
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:    
        default_value = "singlewindow"
    else:
        default_value = "twowindows"
    _create_stateful_action("windowmode", "s", default_value, lambda a, v: gui.editor_window.change_windows_preference(a, v))
    _create_action("showmiddlebarconfig", lambda w, a: middlebar.show_middlebar_conf_dialog())
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
        default_value = "middlebar"
    else:
        default_value = "dock"
    _create_stateful_action("tooldockpos", "s", default_value, lambda a, v: gui.editor_window.show_tools_dock_change_from_menu(a, v))
    if editorpersistance.prefs.audio_master_position_is_top_row == True:
        default_value = "toprow"
    else:
        default_value = "bottomrow"
    _create_stateful_action("audiomasterposition", "s", default_value, lambda a, v: gui.editor_window.set_audiomaster_position(a, v))
    _create_action("zoomin", lambda w, a: updater.zoom_in())
    _create_action("zoomout", lambda w, a: updater.zoom_out())
    _create_action("zoomfit", lambda w, a: updater.zoom_project_length())

    _create_action("addmedia", lambda w, a:  projectaction.add_media_files())
    _create_action("addimgseq", lambda w, a: projectaction.add_image_sequence())
    _create_action("addgenerator", lambda w, a: mediaplugin.show_add_media_plugin_window())
    _create_action("addtitle", lambda w, a:  titler.show_titler())
    _create_action("addcolorclip", lambda w, a: patternproducer.create_color_clip())
    _create_action("fromselected", lambda w, a: projectaction.create_selection_compound_clip())
    _create_action("frombox", lambda w, a: projectaction.create_box_compound_clip())
    _create_action("fromtimeline", lambda w, a: projectaction.create_range_compound_clip())
    _create_action("fromcurrentsequence", lambda w, a: projectaction.create_sequence_compound_clip())
    _create_action("fromgmic", lambda w, a: containerclip.create_gmic_media_item())
    _create_action("addsequencelink", lambda w, a: projectaction.create_sequence_link_container())
    _create_action("addfromfolder", lambda w, a: projectaddmediafolder.show_add_media_folder_dialog())
    _create_action("importfromproject", lambda w, a: projectaction.import_project_media())
    _create_action("loadgeneratorscript", lambda w, a: containerclip.create_fluxity_media_item())
    _create_action("addbinmainmenu", lambda w, a: projectaction.add_new_bin())
    _create_action("deletebinmainmenu", lambda w, a: projectaction.delete_selected_bin())
    _create_action("logcliprange", lambda w, a: medialog.log_range_clicked())
    _create_action("recreateicons", lambda w, a: menuactions.recreate_media_file_icons())
    _create_action("removeunusedmedia", lambda w, a: projectaction.remove_unused_media())
    _create_action("changeprofile", lambda w, a: projectaction.change_project_profile())
    _create_action("projectinfoanddata", lambda w, a: projectdatavaultgui.show_current_project_data_store_info_window())
    _create_action("proxymanager", lambda w, a: proxytranscodemanager.show_proxy_manager_dialog())
    _create_action("transcodemanager", lambda w, a: proxytranscodemanager.show_transcode_manager_dialog())

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
    _create_stateful_action("compositing.compmode", "s", "fulltrackauto", lambda a, v: projectaction.change_current_sequence_compositing_mode_from_corner_menu(a, v))

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

    # Create data for timeline actions enbled/disabled handling.
    global _tline_widgets, _tline_actions
    _tline_widgets = keygtkactions.get_widgets_list(keygtkactions.TLINE_MONITOR_ALL)
    _tline_action_ids = ["cutatplayhead"]
    _tline_actions = _get_actions(_tline_action_ids)

    # Connect all widgets in main window to send info on focus changes.
    all_widgets = get_all_widgets(gui.editor_window.window)
    for w in all_widgets:
        _connect_for_focus_notifications(w)
 
def _create_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    APP().add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])

def _create_win_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    gui.editor_window.window.add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])
    action.set_enabled(True)

def _create_stateful_action(name, typestr, default_value, callback):
    action = Gio.SimpleAction.new_stateful( name,
                                            GLib.VariantType.new(typestr),
                                            GLib.Variant(typestr, default_value))

    action.connect("change-state", callback)
    APP().add_action(action)

# --------------------------------------------- View menu updates
def fill_recents_menu_widget(callback):
    """
    Fills menu item with menuitems to open recent projects.
    """
    global _recent_menu
    _recent_menu.remove_all()

    # Add new menu items
    recent_proj_names = editorpersistance.get_recent_projects()
    if len(recent_proj_names) != 0:
        for i in range (0, len(recent_proj_names)):
            proj_name = recent_proj_names[i]
            _recent_menu.append(proj_name, "app.openrecent." + str(i))
            action = Gio.SimpleAction.new("openrecent." + str(i), None)
            action.connect("activate", callback, copy.deepcopy(i))
            APP().add_action(action)
    else:
        _recent_menu.append (_("Empty"), None)

def fill_panel_positions_menu():
    global _panel_positions_menu, _tabs_menu

    # Panel positions.
    if editorlayout.panel_positioning_available() == True:
        editorlayout.get_panel_positions_menu_item(_panel_positions_menu)
        editorlayout.get_tabs_menu_item(_tabs_menu)
    else:
        print("Panel positioning feature not available, too small screen.")

def update_compositing_mode_action_state():
    action = APP().lookup_action("compositing.compmode")
    
    if editorstate.editorstate.get_compositing_mode() == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:  
        new_variant = GLib.Variant.new_string("fulltrackauto")
    else:
        new_variant = GLib.Variant.new_string("topdown")

    action.set_state(new_variant)

def enable_save():
    action = APP().lookup_action("save")
    action.set_enabled(True)

def set_save_action_sensitive(sensitive):
    action = APP().lookup_action("save")
    action.set_enabled(sensitive)

def set_undo_sensitive(sensitive):
    action = APP().lookup_action("undoaction")
    action.set_enabled(sensitive)
    
def set_redo_sensitive(sensitive):
    action = APP().lookup_action("redoaction")
    action.set_enabled(sensitive)

# ---------------------------------- action focus handling
def get_all_widgets(container):
    widgets = []
    if isinstance(container, Gtk.Container):
        for child in container.get_children():
            widgets.append(child)
            widgets.extend(get_all_widgets(child))
            
    return widgets


def _connect_for_focus_notifications(widget):
    widget.connect("notify::has-focus", _handle_state_change)

def _get_actions(action_ids):
    action_list = []
    for aid in action_ids:
        action_list.append(APP().lookup_action(aid))
    return action_list

def _handle_state_change(w, param_spec):
    #focused = bool(Gtk.StateFlags.FOCUSED & flags)
    widget = gui.editor_window.window.get_focus()
    #print("---------------------------------------------")
    #print(w)
    #print(widget)
    #print(w.has_focus(), w==widget)
    if widget in _tline_widgets:
        print("tlinewidget has focus")
        _set_tline_actions_enabled(True)
    else:
        print("NON tlinewidget has focus")
        _set_tline_actions_enabled(False)

def _set_tline_actions_enabled(enabled):
    for action in _tline_actions:
        action.set_enabled(enabled)
   