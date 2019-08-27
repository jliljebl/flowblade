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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
import appconsts
import cairoarea
import editorpersistance

class PressLaunch:
    def __init__(self, callback, w=22, h=22):
        self.widget = cairoarea.CairoDrawableArea2( w, 
                                                    h, 
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.callback = callback
        self.sensitive = True

    def set_sensitive(self, value):
        self.sensitive = value
        
    def _draw(self, event, cr, allocation):      
        cr.move_to(7, 13)
        cr.line_to(12, 18)
        cr.line_to(17, 13)
        cr.close_path()
        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            cr.set_source_rgb(0, 0, 0)
        else:
            cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()
        
    def _press_event(self, event):
        if self.sensitive == False:
           return 

        self.callback(self.widget, event)
