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

from editorstate import APP
import projectaction

def get_menu():

    MENU_XML = """
    <interface>
      <menu id="menubar">
        <submenu>
          <attribute name="label">File</attribute>
          <section>
            <item>
              <attribute name="label">New...</attribute>
              <attribute name="action">app.new</attribute>
            </item>
            <item>
              <attribute name="label">Open...</attribute>
              <attribute name="action">app.open</attribute>
            </item>
            <item>
              <attribute name="label">Quit</attribute>
              <attribute name="action">app.quit</attribute>
            </item>
          </section>
        </submenu>

        <submenu>
          <attribute name="label">Edit</attribute>
          <section>
            <item>
              <attribute name="label">Copy</attribute>
              <attribute name="action">app.copy</attribute>
            </item>
            <item>
              <attribute name="label">Paste</attribute>
              <attribute name="action">app.paste</attribute>
            </item>
          </section>
        </submenu>
      </menu>
    </interface>
    """

    builder = Gtk.Builder.new_from_string(MENU_XML, -1)
    menu_model = builder.get_object("menubar")

    # Create menubar widget
    menubar = Gtk.MenuBar.new_from_model(menu_model)
        
    return menubar

def create_actions():
    _create_action("new", lambda w, a:projectaction.new_project(), "<Ctrl>N")
    _create_action("open",  lambda w, a:projectaction.load_project(), "<Ctrl>O")

def _create_action(name, callback, accel=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    APP().add_action(action)
    if accel != None:
        APP().set_accels_for_action("app." + name, [accel])
