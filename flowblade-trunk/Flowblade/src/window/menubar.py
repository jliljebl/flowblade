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
import medialinker
import menuactions
import middlebar
import projectaction
import projectaddmediafolder
import projectdatavaultgui
import proxytranscodemanager
import scripttool
import singletracktransition
import titler
import updater


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
                <submenu>
                  <attribute name="label">""" + _("Monitor Playback Interpolation") + """</attribute>
                </submenu>
            </section>
            <section>
                <item>
                  <attribute name="label">""" + _("Zoom In") + """</attribute>
                  <attribute name="action">app.zoomin</attribute>
                </item>
                <item>
                  <attribute name="label">""" + _("Zoom out") + """</attribute>
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

    _create_action("undoaction", lambda w, a:undo.do_undo_and_repaint())
    _create_action("redoaction", lambda w, a:undo.do_undo_and_repaint())
              
    _create_action("copyaction", lambda w, a: copypaste.copy_action())
    _create_action("pasteaction", lambda w, a: copypaste.paste_action())
    _create_action("pastefiltersaction", lambda w, a: tlineaction.do_timeline_filters_paste())
    _create_action("cutaction", lambda w, a: copypaste.cut_action())
    _create_action("appendfrommonitor", lambda w, a: tlineaction.append_button_pressed())
    _create_action("insertfrommonitor", lambda w, a: tlineaction.insert_button_pressed())
    _create_action("threepointoverwrite", lambda w, a: tlineaction.three_point_overwrite_pressed())
    _create_action("rangeoverwrite", lambda w, a: tlineaction.range_overwrite_pressed())
    _create_action("cutatplayhead", lambda w, a: tlineaction.cut_pressed())
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
    _create_action("showkeyboardshortcuts", lambda w, a: menuactions.profiles_manager())
    _create_action("showpreferences", lambda w, a: preferenceswindow.preferences_dialog())

    _create_action("fullscreen", lambda w, a: menuactions.toggle_fullscreen())
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:    
        default_value = "singlewindow"
    else:
        default_value = "twowindows"
    _create_stateful_action("windowmode", "s", default_value,  lambda a, v: gui.editor_window.change_windows_preference(a, v))
    _create_action("showmiddlebarconfig", lambda w, a: middlebar.show_middlebar_conf_dialog())

    if editorpersistance.prefs.audio_master_position_is_top_row == True:
        default_value = "toprow"
    else:
        default_value = "bottomrow"
    _create_stateful_action("audiomasterposition", "s", default_value,  lambda a, v: gui.editor_window.set_audiomaster_position(a, v))
        
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

def _create_stateful_action(name, typestr, default_value, callback):
    action = Gio.SimpleAction.new_stateful( name,
                                            GLib.VariantType.new(typestr),
                                            GLib.Variant(typestr, default_value))

    action.connect("change-state", callback)
    APP().add_action(action)

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
                                
                                # Audio master meter
                                # Tool Selection Widget
                                audiomaster_menu_item = Gtk.MenuItem(_("Audoi Master Level Meter"))
                                audiomaster_menu = Gtk.Menu()
                                audiomaster_top = Gtk.RadioMenuItem()
                                audiomaster_top.set_label( _("Top Row"))
                                audiomaster_menu.append(audiomaster_top)
                                audiomaster_bottom = Gtk.RadioMenuItem.new_with_label([audiomaster_top], _("Bottom Row"))

                                if editorpersistance.prefs.audio_master_position_is_top_row == True:
                                    audiomaster_top.set_active(True)
                                else:
                                    audiomaster_bottom.set_active(True)
                                audiomaster_top.connect("activate", lambda w: self._set_audiomaster_position(True))
                                audiomaster_bottom.connect("activate", lambda w: self._set_audiomaster_position(False))

                                audiomaster_menu.append(audiomaster_bottom)
                                audiomaster_menu_item.set_submenu(audiomaster_menu)
                                menu.append(audiomaster_menu_item)
                                
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
"""
        
        

