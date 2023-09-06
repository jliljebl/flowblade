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

import gui
import tlinewidgets

_page = 0

def vertical_size_update(allocation):
    set_tlinewidgets_page_offset(allocation)

def page_up():
    global _page
    _page =_ page - 1
    allocation = gui.tline_canvas.widget.get_allocation()
    set_tlinewidgets_page_offset(allocation)

def page_down():
    global _page
    _page =_ page + 1
    allocation = gui.tline_canvas.widget.get_allocation()
    set_tlinewidgets_page_offset(allocation)

def set_tlinewidgets_page_offset(allocation):
    x, y, w, panel_height = allocation.x, allocation.y, allocation.width, allocation.height
    half_height = panel_height // 2
    tlinewidgets.page_y_off + int(_page * half_height)
