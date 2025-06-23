## Migrating from GTK 3.x to GTK 4

Migraation doc was moved, most links below not working, new place: [Migrating from GTK 3.x to GTK 4](https://docs.gtk.org/gtk4/migrating-3to4.html)

### Done

| Item                                                                                                                            | status                        |
| ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| [Stop using GdkScreen](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.4)                                   | **DONE**                      |
| [Enable diagnostic warnings](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.4)                | **DONE**, all indicated fixed |
| [Stop using `gtk_main()` and related APIs](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.16) | **DONE**                      |
| [Stop using GtkShadowType and GtkRelief properties](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.37)     | **DONE**                      |
| [Don’t use -gtk-icon-effect in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.42)                | **DONE**                      |
| [Stop using non-RGBA visuals](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.10)              | **DONE**                      |
| [Adapt to GtkWindow API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.25)                        | **DONE**                      |
| [GtkMenu, GtkMenuBar and GtkMenuItem are gone](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.74)          | **DONE** for popovers.        |
| Gtk.CheckButton does not inherit signal "clicked"                                                                               | **DONE**                      |

### Showstopper

| Item                                                                                                              | status                                     |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| [gtk_widget_get_surface has been removed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.70) | Breaks MLT SDL(any version) video display. |

### Changes that can be done running GTK 3.x

| Item                                                                                                                                                                  | status                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [Stop using GtkWidget event signals](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.14)                                             | **DONE**, exept for "button-press-event" and "button-release-event" which don't have the required class backported. |
| [GtkBox  - use orientatin parameter,  padding, fill and expand child properties](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.11) | Use indirection objects and builder func.                                                                           |
| Stop using GtkButton’s image-related API                                                                                                                              | **DONE** Using indirection builder func                                                                             |
| [Stop using GtkFileChooserButton](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.85)                                                             | **DONE**                                                                                                            |
| Gtk.Widget.modify_font deprecated                                                                                                                                     | 4 instances, use CSS instead.                                                                                       |
| [Stop using GtkEventBox](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.22)                                                                      | **DONE** easy ones, needs more work port time.                                                                      |

### Changes that need to be done at the time of the switch

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | status                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Set a proper application ID](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.15)                                                                                                                                                                                                                                                                                                                                                           | Affects D-Bus, this will be worked on last.                                                                                                                                                                                                                                                                                                    |
| [Adapt to GdkEvent API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.10) - [Adapt to event controller API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.19)                                                                                                                                                                                                                                                    | Mainly instances of **event.x** and **event.y** These will be real easy to scriptconvert at post time.                                                                                                                                                                                                                                         |
| [Adapt to GdkKeymap API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.13) - [Adapt to changes in keyboard modifier handling](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.14) - [Use the new apis for keyboard shortcuts](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.21)                                                                                                                      | Current assesment is that  this does not need to be addressed.                                                                                                                                                                                                                                                                                 |
| [Adapt to GtkStack, GtkAssistant and GtkNotebook API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.27)                                                                                                                                                                                                                                                                                                                                        | Current assesment is that  this does not need to be addressed.                                                                                                                                                                                                                                                                                 |
| [Adapt to button class hierarchy changes](https://docs.gtk.org/gtk4/migrating-3to4.html#adapt-to-button-class-hierarchy-changes)                                                                                                                                                                                                                                                                                                                                             | Heeds to be done port time, required API was not back ported.                                                                                                                                                                                                                                                                                  |
| [Adapt to GtkScrolledWindow API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.29)                                                                                                                                                                                                                                                                                                                                                             | With scrollbar we hit need to set orientation, other issues likely.                                                                                                                                                                                                                                                                            |
| [Adapt to GtkBin removal](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.30) - [Adapt to GtkContainer removal](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.31)  - [Switch to GtkWidget’s children APIs](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.40)                                                                                                                                                 | In test these were successfully handled with mostly scripted conversion, and most are not back ported, so this needs to be done port time with script.                                                                                                                                                                                         |
| [Adapt to GtkStyleContext API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.35)                                                                                                                                                                                                                                                                                                                                                               | Single instance, need use function **add_provider_for_display (display, provider, priority)**                                                                                                                                                                                                                                                  |
| [Adapt to GtkWidget’s size request changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.38)                                                                                                                                                                                                                                                                                                                                                          | **get_preferred_width()** 9 instances, Gtk4 has  **GtkWidgetClass::measure()**                                                                                                                                                                                                                                                                 |
| [Adapt to GtkWidget’s size allocation changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.39)                                                                                                                                                                                                                                                                                                                                                       | "size-allocate" signal 3 instances, The ::size-allocate signal has been removed, since it is easy to misuse. If you need to learn about sizing changes of custom drawing widgets, use the “resize” or “resize” signals. If you want to track the size of toplevel windows, use property notification for “default-width” and “default-height”. |
| [Widgets are now visible by default](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.47)                                                                                                                                                                                                                                                                                                                                                                 | show() is no-op on init now, hide() may need to be added somewhere,  show_all() 171 instances can be easily removed with scripts.                                                                                                                                                                                                              |
| [Stop using GtkWidget::draw](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.53)                                                                                                                                                                                                                                                                                                                                                                         | cairoarea.py, **gtk_drawing_area_set_draw_func()**.                                                                                                                                                                                                                                                                                            |
| [Window content observation has changed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.54)                                                                                                                                                                                                                                                                                                                                                             | e.g. timeline draw updates after resizes.                                                                                                                                                                                                                                                                                                      |
| [Monitor handling has changed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.55)                                                                                                                                                                                                                                                                                                                                                                       | Instead of a monitor number, GdkMonitor is used, see e.g. utilsgtk.py                                                                                                                                                                                                                                                                          |
| [Adapt to monitor API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.56)                                                                                                                                                                                                                                                                                                                                                                       | n_monitors is not in Gtk 4                                                                                                                                                                                                                                                                                                                     |
| [Adapt to cursor API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.57)                                                                                                                                                                                                                                                                                                                                                                        | **set_cursor()** many instances, we need to apply changes to tline canvas widget only.                                                                                                                                                                                                                                                         |
| [Switch to the new Drag-and-Drop api](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.78)                                                                                                                                                                                                                                                                                                                                                                | Yes, APIs different.                                                                                                                                                                                                                                                                                                                           |
| [Update to GtkFileChooser API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.80)                                                                                                                                                                                                                                                                                                                                                               | Very likely not needed or only a minor issue.                                                                                                                                                                                                                                                                                                  |
| [Stop using blocking dialog functions](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.81)                                                                                                                                                                                                                                                                                                                                                               | **DONE**                                                                                                                                                                                                                                                                                                                                       |
| [Do not use widget style properties](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.6) [Don’t use -gtk-gradient in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.41) [Don’t use -gtk-outline-…-radius in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.44) [Stop using GtkContainer::border-width](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.32) | These will worked on last, initial port with Adwaita.                                                                                                                                                                                                                                                                                          |
| [GtkMenu, GtkMenuBar and GtkMenuItem are gone](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.74)                                                                                                                                                                                                                                                                                                                                                       | Popovers **Done**, App menu needs to be done in GTK4.                                                                                                                                                                                                                                                                                          |

### Conversion test commits

Can't get xid for widgets in Gtk4 anymore GdkSurface, GtkSearchEntry
step - comment out more uimanger and initing compositing mode menu
step - get_children()[0] -> get_first_child()
step - comment out uimanager via gui
step - comment out "key-press-event"
step - comment out uimanager
step - more Window pos, size commentouts
step - comment out Window.resize()
step - comment out calling _init_view_menu
step - comment out self.menubar lines
step - VPaned -> Paned, Add VPaned indection layer method
Add pack1 and pack2 methods to build Paned objects
step - HPaned to Paned via builder method, Add HPaned indirection layer method
step - Box.pack_end -> Box.pack_start
step - Add Box.clear_children() method to be able to remove Box.get_children() calls
step - comment out override_background_color
step - comment out using non-fixed workflow._tools_menu
step - comment out focus-out-event
step - comment out modify_bg
step - Gdk.Color -> Gdk.RGBA
step - Update EventBox indirection code to handle set_child
step - EventBox replace code, Add EventBox conversion indirection layer code
step - comment out set_image() for buttons
step - comment out "clicked" 
step, handfix remove size attrs from new_from_icon_name creator funcs
step, Gtk.IconSize.BUTTON -> NORMAL
step, fix Gtk.Popover.new() with argument
File-line replace for ProjectInfoBox
step, add dummy set_current_folder for FileChooserButton
step, add dummy set_action for FileChooserButton
step, FileChooserButton replace
NOTE: ----------------- set_child -> append multiple for Boxes that don't use pack start (handfix Box.add -> Box.append)
step, comment out modify_font
step, comment out override_font
step, replace add -> set_child
step comment out draw signal
step, comment out add events  (cairo draw)
step, comment out dnd.*
step, comment out show_all
step, Add_pack_start lambda to VBoxes
step, Add pack_start lambda to HBoxes
step, scrolled window add -> set_child
step, comment out "button-press-event"
step, comment out UIManager
step, comment out "window-state-event"
step, comment out set_border_width
step, comment out set_icon_from_file
step, Delete window types from main app
step, comment out splashscreen WindowType
step, comment out n_monitors, more
step, comment out n_monitors
step, comment out theme
step, box
Step, box
step, comment out Gtk.Menu
Step, box, hscrollbar
Step, extending boxes replace
step, profileinfobox
Stex, fix renderqueueview vbox
Step, update gtkbox, work on extending box classes
Step, comment out Gtk.TargetEntrys
Step, gtk4, launchscript
boxreplace with funcs

### Conversion script last output

Changed line/s into:   gtkbox.VBox 242
Changed line/s into:   gtkbox.HBox 293
Files changed with added line: import gtkbox 65
Changed line/s into:  gi.require_version('Gtk', '4.0') 15
Changed line/s into:  class RenderQueueView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['batchrendering.py']
Changed line/s into:  class ProfileInfoBox(Gtk.Box): 2
Files changed with added line:         gtkbox.build_vertical(self) 2
['rendergui.py', 'toolsencoding.py']
Changed line/s into:  class PositionNumericalEntries(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['keyframeeditor.py']
Changed line/s into:  class ScaleSelector(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['vieweditor.py']
Changed line/s into:  class ImageTextTextListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class TextTextListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class MultiTextColumnListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class MultiTextColumnListView(Gtk.Box): 0
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class BinTreeView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class ImageTextImageListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class FilterSwitchListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class TextListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['guicomponents.py']
Changed line/s into:  class JobsQueueView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['jobs.py']
Changed line/s into:  class AbstractKeyFrameEditor(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['keyframeeditor.py']
Changed line/s into:  class RotoMaskKeyFrameEditor(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['keyframeeditor.py']
Changed line/s into:  class MediaRelinkListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['medialinker.py']
Changed line/s into:  class MediaLogListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['medialog.py']
Changed line/s into:  class ProjectEventListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['projectinfogui.py']
Changed line/s into:  class PreviewPanel(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['simpleeditors.py']
Changed line/s into:  class TextLayerListView(Gtk.Box): 1
Files changed with added line:         gtkbox.build_vertical(self) 1
['titler.py']
Changed line/s into:  class ClipInfoPanel(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['guicomponents.py']
Changed line/s into:  class CompositorInfoPanel(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['guicomponents.py']
Changed line/s into:  class PluginInfoPanel(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['guicomponents.py']
Changed line/s into:  class BinInfoPanel(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['guicomponents.py']
Changed line/s into:  class ClipEditorButtonsRow(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['keyframeeditor.py']
Changed line/s into:  class GeometryEditorButtonsRow(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['keyframeeditor.py']
Changed line/s into:  class FadeLengthEditor(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['propertyeditorbuilder.py']
Changed line/s into:  class AbstractSimpleEditor(Gtk.Box): 1
Files changed with added line:         gtkbox.build_horizontal(self) 1
['simpleeditors.py']
Changed line/s into:  class TimeLineScroller(Gtk.Scrollbar): 1
Files changed with added line:         self.set_orientation (Gtk.Orientation.HORIZONTAL) 1
['tlinewidgets.py']
Commented out files count for string:  show_all 40
Commented out files count for string:  dnd. 7
Commented out files count for string:  add_events 3
Changed line/s into:  .set_child( 139
Commented out files count for string:  override_font 3
Commented out files count for string:  modify_font 4
Changed line/s ends into:  gtkbox.get_file_chooser_button() 22
Changed line  566  in file  rendergui.py into:  self.append(Gtk.Label())
Changed line/s into:  self.args_popover = Gtk.Popover.new() 1
Files changed with added line:         self.args_popover.set_default_widget(self.args_edit_launch.widget) 1
Changed line/s into:  Gtk.IconSize.NORMAL 0
Commented out files count for string:  connect("clicked" 22
Commented out files count for string:  set_image 11
Changed line/s into:   gtkbox.EventBox 14
Changed line/s into:   Gdk.RGBA 3
Commented out files count for string:  modify_bg 3
Commented out files count for string:  connect("focus-out-event" 1
Commented out files count for string:  .connect_launched_menu(workflow._tools_menu) 1
Commented out files count for string:  override_background_color 2
Changed line/s into:  pack_start 3
Changed line/s into:   gtkbox.HPaned 2
Changed line/s into:   gtkbox.VPaned 1
Commented out files count for string:  self.menubar 1
Commented out files count for string:  self._init_view_menu 1
Commented out files count for string:  self.window.resize 1
Commented out files count for string:  self.window.set_position 2
Commented out files count for string:  self.window2.resize 1
Commented out files count for string:  editor_window.uimanager.get_widget 4
Commented out files count for string:  key-press-event 6
Commented out files count for string:  gui.editor_window.uimanager 4
Changed line/s into:  get_first_child() 3
Commented out files count for string:  self.uimanager 1
Commented out files count for string:  gui.editor_window.init_compositing_mode_menu() 2

### Errors

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/compositormodes.py", line 26, in <module>
    import edit
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/edit.py", line 40, in <module>
    import movemodes
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/movemodes.py", line 29, in <module>
    import boxmove
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/boxmove.py", line 31, in <module>
    import tlinewidgets
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/tlinewidgets.py", line 3047, in <module>
    class TimeLineScroller(Gtk.HScrollbar):
                           ^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'HScrollbar'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/workflow.py", line 69, in <module>
    _tools_menu = Gtk.Menu()
                  ^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'Menu'

Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 252, in on_activate
    gui.apply_theme(editorpersistance.prefs.theme)
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/gui.py", line 230, in apply_theme
    apply_gtk_css()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/gui.py", line 235, in apply_gtk_css
    screen = display.get_default_screen()

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 263, in on_activate
    scr_w, scr_h = _set_screen_size_data()
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 929, in _set_screen_size_data
    monitor_data = utilsgtk.get_display_monitors_size_data()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/utilsgtk.py", line 69, in get_display_monitors_size_data
    num_monitors = display.get_n_monitors() # Get number of monitors.
                   ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'X11Display' object has no attribute 'get_n_monitors'. Did you mean: 'get_monitors'?
janne@bash~/codes/flowblade/flowblade/flowblade-trunk$ 

Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 263, in on_activate
    scr_w, scr_h = _set_screen_size_data()
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 934, in _set_screen_size_data
    num_monitors = display.get_n_monitors() # Get number of monitors.

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 304, in on_activate
    show_splash_screen()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 885, in show_splash_screen
    splash_screen = Gtk.Window(Gtk.WindowType.TOPLEVEL)
                               ^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'WindowType'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 119, in __init__
    self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
                                  ^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'WindowType'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 120, in __init__
    self.window.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Window' object has no attribute 'set_icon_from_file'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 131, in __init__
    self.window.connect("delete-event", lambda w, e:app.shutdown())
TypeError: <Gtk.Window object at 0x7f60341c22c0 (GtkWindow at 0x416ebc0)>: unknown signal name: delete-event
GPU test results {'NVENC H.264 High Profile / .mp4': -11, 'NVENC HEVC / .mp4': -11, 'NVENC HEVC HDR / .mp4': -11, 'VAAPI H.264 / .mp4': -11}

Player initialized with profile:  HD 1080p 30 fps
Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 121, in __init__
    self.window.set_border_width(5)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 137, in __init__
    self.ui = Gtk.UIManager()
              ^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'UIManager'

Player initialized with profile:  HD 1080p 30 fps
Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 318, in _init_gui_components
    self.bin_list_view = guicomponents.BinTreeView(
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 359, in __init__
    self.treeview.connect('button-press-event', self._button_press_event)
TypeError: <Gtk.TreeView object at 0x7f00efbe3000 (GtkTreeView at 0x404acb0)>: unknown signal name: button-press-event

Player initialized with profile:  HD 1080p 30 fps
Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 318, in _init_gui_components
    self.bin_list_view = guicomponents.BinTreeView(
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 392, in __init__
    self.scroll.add(self.treeview)
    ^^^^^^^^^^^^^^^
AttributeError: 'ScrolledWindow' object has no attribute 'add'

show_all() !!!!!!!!!!!!!!!!!!! jäi välistä 

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 318, in _init_gui_components
    self.bin_list_view = guicomponents.BinTreeView(
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 393, in __init__
    self.pack_start(self.scroll, True, True, 0)
    ^^^^^^^^^^^^^^^
AttributeError: 'BinTreeView' object has no attribute 'pack_start'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 322, in _init_gui_components
    dnd.connect_bin_tree_view(self.bin_list_view.treeview, projectaction.move_files_to_bin)
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/dnd.py", line 105, in connect_bin_tree_view
    treeview.enable_model_drag_dest([MEDIA_FILES_DND_TARGET],

_panel
    hamburger = guicomponents.HamburgerPressLaunch(callback)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 2665, in __init__
    self.widget = cairoarea.CairoDrawableArea2( self.x_size_pref,
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/cairoarea.py", line 38, in __init__
    self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    ^^^^^^^^^^^^^^^
AttributeError: 'CairoDrawableArea2' object has no attribute 'add_events'

self._init_gui_components()

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 326, in _init_gui_components
    self.bins_panel = panels.get_bins_tree_panel(self.bin_list_view, projectaction.bin_hambuger_pressed)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/panels.py", line 104, in get_bins_tree_panel
    hamburger = guicomponents.HamburgerPressLaunch(callback)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 2665, in __init__
    self.widget = cairoarea.CairoDrawableArea2( self.x_size_pref,
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/cairoarea.py", line 52, in __init__
    self.connect('draw', self._draw_event)

self._init_gui_components()

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 341, in _init_gui_components
    media_panel, bin_info = panels.get_media_files_panel(
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/panels.py", line 72, in get_media_files_panel
    files_filter_launcher = guicomponents.ImageMenuLaunchPopover(filtering_cb, [all_pixbuf, video_pixbuf, audio_pixbuf, graphics_pixbuf, imgseq_pixbuf, pattern_pixbuf, unused_pixbuf], 24*size_adj, 22*size_adj)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/panels.py", line 78, in get_media_files_panel
    bin_info = guicomponents.BinInfoPanel()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 1055, in __init__
    self.bin_name.override_font(Pango.FontDescription(font_desc))
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Label' object has no attribute 'override_font'

bin_info = guicomponents.BinInfoPanel()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 1061, in __init__
    self.items.modify_font(Pango.FontDescription(font_desc))
    ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Label' object has no attribute 'modify_font'

self._init_gui_components()

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 333, in _init_gui_components
    view.add(self.media_list_view.widget)
    ^^^^^^^^
AttributeError: 'Viewport' object has no attribute 'add'

  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'FileChooserButton'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/render.py", line 185, in create_widgets
    widgets.file_panel = rendergui.RenderFilePanel()
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/rendergui.py", line 689, in __init__
    self.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Button' object has no attribute 'set_action'. Did you mean: 'query_action'?

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/render.py", line 185, in create_widgets
    widgets.file_panel = rendergui.RenderFilePanel()
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/rendergui.py", line 690, in __init__
    self.out_folder.set_current_folder(os.path.expanduser("~") + "/")
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Button' object has no attribute 'set_current_folder'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/rendergui.py", line 566, in __init__
    self.set_child(Gtk.Label()) # This is removed when we have data to fill this
    ^^^^^^^^^^^^^^
AttributeError: 'ProfileInfoBox' object has no attribute 'set_child'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/rendergui.py", line 1016, in __init__
    self.args_popover = Gtk.Popover.new(self.args_edit_launch.widget)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Gtk.Popover.new() takes exactly 0 arguments (1 given)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guiutils.py", line 411, in get_render_button
    Gtk.IconSize.BUTTON)
    ^^^^^^^^^^^^^^^^^^^
AttributeError: type object 'IconSize' has no attribute 'BUTTON'

render_icon = Gtk.Image.new_from_icon_name( "media-record", 
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TypeError: Gtk.Image.new_from_icon_name() takes exactly 1 argument (2 given)

star_check.connect("clicked", lambda w:media_log_filtering_changed())

TypeError: <Gtk.CheckButton object at 0x7903fb2641c0 (GtkCheckButton at 0x30ce5d0)>: unknown signal name: clicked

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 463, in _init_gui_components
    events_panel = medialog.get_media_log_events_panel(media_log_events_list_view)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/medialog.py", line 689, in get_media_log_events_panel
    star_button.set_image(guiutils.get_image("star"))
    ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Button' object has no attribute 'set_image'. Did you mean: 'set_name'?

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 509, in _init_gui_components
    pos_bar_frame.set_child(self.pos_bar.widget)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/monitorwidget.py", line 112, in __init__
    black_box = Gtk.EventBox()
                ^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'EventBox'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 555, in _init_gui_components
    monitor_widget = monitorwidget.MonitorWidget()
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/monitorwidget.py", line 113, in __init__
    black_box.set_child(Gtk.Label())

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/monitorwidget.py", line 114, in __init__
    bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
               ^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gdk' object has no attribute 'Color'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 141, in __init__
    self._init_gui_components()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 555, in _init_gui_components
    monitor_widget = monitorwidget.MonitorWidget()
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/monitorwidget.py", line 115, in __init__
    black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
    ^^^^^^^^^^^^^^^^^^^
AttributeError: 'Box' object has no attribute 'modify_bg'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/middlebar.py", line 186, in create_edit_buttons_row_buttons
    _create_buttons(editor_window)
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/middlebar.py", line 211, in _create_buttons
    editor_window.tool_selector = create_tool_selector(editor_window)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/middlebar.py", line 300, in create_tool_selector
    tool_selector.connect_launched_menu(workflow._tools_menu)
                                        ^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'workflow' has no attribute '_tools_menu'

Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 144, in __init__
    self._init_tline()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 588, in _init_tline
    self.tline_info.set_child(info_contents)
    ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Box' object has no attribute 'set_child'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 2250, in __init__
    self.update_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 2253, in update_gui
    for child in self.widget.get_children():
                 ^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Box' object has no attribute 'get_children'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 144, in __init__
    self._init_tline()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 695, in _init_tline
    self.tline_box.pack_end(tline_vbox_frame, True, True, 0)
    ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Box' object has no attribute 'pack_end'

  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'HPaned'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 147, in __init__
    self._init_panels_and_frames()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 775, in _init_panels_and_frames
    self.top_paned.pack1(self.notebook_frame , resize=True, shrink=False)
    ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Paned' object has no attribute 'pack1'. Did you mean: 'pick'?

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 211, in _get_app_pane
    self.app_v_paned = Gtk.VPaned()
                       ^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/overrides/__init__.py", line 32, in __getattr__
    return getattr(self._introspection_module, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/gi/module.py", line 126, in __getattr__
    raise AttributeError("%r object has no attribute %r" % (
AttributeError: 'gi.repository.Gtk' object has no attribute 'VPaned'

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 221, in _get_app_pane
    self.menubar.set_margin_bottom(4)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 168, in __init__
    self.window.resize(w, h)
    ^^^^^^^^^^^^^^^^^^
AttributeError: 'Window' object has no attribute 'resize'. Did you mean: 'realize'?

<class 'gi.repository.Gtk.Box'>
Traceback (most recent call last):
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 538, in create_gui
    editor_window = editorwindow.EditorWindow()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/editorwindow.py", line 169, in __init__
    self.window.set_position(Gtk.WindowPosition.CENTER)

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 350, in on_activate
    create_gui()
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 552, in create_gui
    gui.editor_window.window.connect("key-press-event", keyevents.key_down)
TypeError: <Gtk.Window object at 0x7cec397b7d00 (GtkWindow at 0x33da690)>: unknown signal name: key-press-event

  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/app.py", line 572, in launch_player
    editorstate.player.set_sdl_xwindow(gui.tline_display)
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/mltplayer.py", line 88, in set_sdl_xwindow
    os.putenv('SDL_WINDOWID', str(widget.get_window().get_xid()))
                                  ^^^^^^^^^^^^^^^^^
AttributeError: 'Box' object has no attribute 'get_window'. Did you mean: 'get_width'?  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/middlebar.py", line 186, in create_edit_buttons_row_buttons
    _create_buttons(editor_window)
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/middlebar.py", line 198, in _create_buttons
    tc_entry = guicomponents.BigTCEntry()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/janne/codes/flowblade/flowblade/flowblade-trunk/Flowblade/guicomponents.py", line 1921, in __init__
    self.widget.connect("focus-out-event", self._focus_lost)
