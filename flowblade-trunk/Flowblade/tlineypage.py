"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

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

"""
This module handles displaying timeline in paged view if all tracks 
cannot be displayed in single view.
"""

from editorstate import current_sequence
import gui
import tlinewidgets
import updater

_page = 0

def vertical_size_update(allocation):
    set_tlinewidgets_page_offset(allocation)

def page_up():
    global _page
    _page = _page + 1
    allocation = gui.tline_canvas.widget.get_allocation()
    set_tlinewidgets_page_offset(allocation)

def page_down():
    global _page
    _page = _page - 1
    allocation = gui.tline_canvas.widget.get_allocation()
    set_tlinewidgets_page_offset(allocation)

def set_tlinewidgets_page_offset(allocation):
    half_height = allocation.height // 2
    tlinewidgets.page_y_off = int(_page * half_height)
    tlinewidgets.set_ref_line_y(allocation)

    set_ypage_buttons_active(allocation)

    updater.repaint_tline()
    
def set_ypage_buttons_active(allocation):
    down_limit = tlinewidgets._get_track_y(1) + current_sequence().tracks[1].height
    up_limit = tlinewidgets._get_track_y(len(current_sequence().tracks) - 2)

    up_active = False
    if up_limit < 0:
        up_active = True

    down_active = False
    if down_limit > allocation.height:
        down_active = True

    gui.editor_window.tline_y_page.set_active_state(up_active, down_active)