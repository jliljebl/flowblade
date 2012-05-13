

import gtk

from editorstate import PLAYER
import vieweditor
import vieweditorlayer

_titler = None

def show_titler():
    global _titler
    _titler = Titler()

class Titler(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title("Titler")
        
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile)
        edit_layer = vieweditorlayer.SimpleRectEditLayer(self.view_editor)
        self.view_editor.edit_layers.append(edit_layer)
        self.view_editor.active_layer = edit_layer

        self.add(self.view_editor)
        self.show_all()

    def show_current_frame(self):
        rgbdata = PLAYER().seek_and_get_rgb_frame(PLAYER().current_frame())
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.view_editor.set_scale_and_update(0.75)
        self.view_editor.edit_area.queue_draw()
