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

import editorlayout
import editorpersistance
from editorstate import APP


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
                <submenu>
                    <attribute name="label">""" + _("Playback Interpolation") + """</attribute>
                      <section>
                      <item>
                        <attribute name="label">""" + _("Nearest Neighbour") + """</attribute>
                        <attribute name="action">app.playback.interpolation</attribute>
                        <attribute name="target">nearest</attribute>
                      </item>
                      <item>
                        <attribute name="label">""" + _("Bilinear") + """</attribute>
                        <attribute name="action">app.playback.interpolation</attribute>
                        <attribute name="target">bilinear</attribute>
                      </item>
                      <item>
                        <attribute name="label">""" + _("Bicubic") + """</attribute>
                        <attribute name="action">app.playback.interpolation</attribute>
                        <attribute name="target">bicubic</attribute>
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
                        <attribute name="label">""" + _("Delete Selected Bin") + """</attribute>
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
