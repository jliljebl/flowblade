#!/usr/bin/env python
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
Module for building and displaying pulsing progress dialog during loading
"""
import gtk
import threading

EXIT_NOW = "##%%&&EXIT&&%%##"

dialog = None
progress_bar = None
ticker = None
message_thread = None
msg_queue = None

class Ticker:
    """
    Calls function repeatedly with given delay between calls.
    This is exatly the same as the one in utils but that has imports so 
    duplicated here.
    """
    def __init__(self, action, delay):
        self.action = action
        self.delay = delay
        self.running = False
    
    def start_ticker(self):
        self.ev = threading.Event()
        self.thread = threading.Thread(target=self.runner,  
                                       args=(self.ev, 
                                       self.delay, 
                                       self.action))
        self.running = True
        self.thread.start()
    
    def stop_ticker(self):
        try:
            self.ev.set()
            self.running = False
        except Exception:
            pass # called when not running

    def runner(self, event, delay, action):
        while True:
            action()
            if not self.running:
                break
            if event.isSet():
                break
            event.wait(delay)
        

class MessageThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        more = True
        while(more == True):
            msg = msg_queue.get(True)
            print msg
            if msg == EXIT_NOW:
                more = False
        ticker.stop_ticker()
        while(ticker.stopped == False):
            pass
        
   
        
def show_window():
    gtk.gdk.threads_init()


    global dialog
    dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
    dialog.set_title("Loading project")


    status_box = gtk.HBox(False, 2)
    status_box.pack_start(gtk.Label(""),False, False, 0)
    status_box.pack_start(gtk.Label(), True, True, 0)


    global progress_bar
    progress_bar = gtk.ProgressBar()
    progress_bar.set_fraction(0.2)
    progress_bar.set_pulse_step(0.1)

    est_box = gtk.HBox(False, 2)
    est_box.pack_start(gtk.Label(""),False, False, 0)
    est_box.pack_start(gtk.Label(), True, True, 0)

    progress_vbox = gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(progress_vbox)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.show_all()

    
    global ticker
    ticker = Ticker(pulse_bar, 0.1)
    ticker.start_ticker()
    
    global message_thread
    message_thread = MessageThread()
    message_thread.start()

    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()

def pulse_bar():
    progress_bar.pulse()

def exit_window_process():
    global ticker
    ticker.stop_ticker()


def start_window_process(q):
    global msg_queue
    msg_queue = q
    show_window()

# Start up
if __name__ == "__main__":
    show_window()
