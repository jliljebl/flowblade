## Migrating from GTK 3.x to GTK 4

### Done

| Item                                                                                                                            | status                        |
| ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| [Stop using GdkScreen](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.4)                                   | **DONE**                      |
| [Enable diagnostic warnings](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.4)                | **DONE**, all indicated fixed |
| [Stop using `gtk_main()` and related APIs](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.16) | **DONE**                      |
| [Stop using GtkShadowType and GtkRelief properties](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.37)     | **DONE**                      |
| [Don’t use -gtk-icon-effect in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.42)                | **DONE**                      |

### Unknown

| Item                                                                                                                     | status                                  |
| ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| [Do not use widget style properties](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.6) | Probably big issue, needs more digging. |

### Changes that can be done running GTK 3.x

| Item                                                                                                                                                                          | status                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [Stop using non-RGBA visuals](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.10)                                                            | Gdk.Color -> Gdk.RGBA                                                          |
| [Stop using GtkWidget event signals](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.14)                                                     | BIG ISSUE                                                                      |
| [Stop using GtkBox use orientatin parameter,  padding, fill and expand child properties](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.11) | Use indirection objects and builder func.                                      |
| Stop using GtkButton’s image-related API                                                                                                                                      | Use indirection builder func,  set_image() 11 instances.                       |
| [Stop using GtkFileChooserButton](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.85)                                                                     | Use indirection builder func, 20 instances.                                    |
| Gtk.Widget.modify_font deprecated                                                                                                                                             | 4 instances, use CSS instead.                                                  |
| [Adapt to GtkWindow API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.25)                                                                      | set_keep_above() 4 instances, delete, Wayland won't support anyway             |
| [Stop using GtkEventBox](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.22)                                                                              | 14 instances, use indirection builder func                                     |
| [GtkMenu, GtkMenuBar and GtkMenuItem are gone](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.74)                                                        | Port to GtkPopoverMenu in GTK 3 almost done. App menu needs to be done in GTK4 |

### Changes that need to be done at the time of the switch

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | status                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| [Stop using direct access to GdkEvent structs](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.8)                                                                                                                                                                                                                                                                                                                                           | BIG ISSUE,                                                                                                                     |
| [Set a proper application ID](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.15)                                                                                                                                                                                                                                                                                                                                                           | Affects D-Bus                                                                                                                  |
| [Reduce the use of `gtk_widget_destroy()`](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.17)                                                                                                                                                                                                                                                                                                                                              | We're doing window.destroy(), maybe not needed                                                                                 |
| [Reduce the use of generic container APIs](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.18)                                                                                                                                                                                                                                                                                                                                              | See what can be done *before* port.                                                                                            |
| [Adapt to GdkEvent API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.10)                                                                                                                                                                                                                                                                                                                                                                      | Direct access to GdkEvent structs is no longer possible in GTK 4....have accessors that you will have to use.                  |
| [Adapt to GdkKeymap API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.13)                                                                                                                                                                                                                                                                                                                                                                     | no effect (?)                                                                                                                  |
| [Adapt to changes in keyboard modifier handling](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.14)                                                                                                                                                                                                                                                                                                                                                     | not needed, probably, we don't have Gdk.ModifierIntent                                                                         |
| [Adapt to event controller API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.19)                                                                                                                                                                                                                                                                                                                                                              | We nned to port to this API first                                                                                              |
| [Focus handling changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.20)                                                                                                                                                                                                                                                                                                                                                                             | "can-focus" 4 instances                                                                                                        |
| [Use the new apis for keyboard shortcuts](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.21)                                                                                                                                                                                                                                                                                                                                                            | no effect, maybe, but not quite clear                                                                                          |
| [Adapt to GtkStack, GtkAssistant and GtkNotebook API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.27)                                                                                                                                                                                                                                                                                                                                        | maybe? depends on details not super clear from description.                                                                    |
| [Adapt to button class hierarchy changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.28)                                                                                                                                                                                                                                                                                                                                                            | Gtk.RadioButton removed, 6 instances                                                                                           |
| [Adapt to GtkScrolledWindow API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.29)                                                                                                                                                                                                                                                                                                                                                             | likely yes                                                                                                                     |
| [Adapt to GtkBin removal](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.30)                                                                                                                                                                                                                                                                                                                                                                            | BIG ISSUE, needs to worked on case by case basis                                                                               |
| [Adapt to GtkContainer removal](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.31)                                                                                                                                                                                                                                                                                                                                                                      | BIG ISSUE, needs to worked on case by case basis                                                                               |
| [Adapt to GtkStyleContext API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.35)                                                                                                                                                                                                                                                                                                                                                               | Need use function **add_provider_for_display (display, provider, priority)**                                                   |
| [Adapt to GtkWidget’s size request changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.38)                                                                                                                                                                                                                                                                                                                                                          | get_preferred_width() 9 instances                                                                                              |
| [Adapt to GtkWidget’s size allocation changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.39)                                                                                                                                                                                                                                                                                                                                                       | "size-allocate" signal 3 instances                                                                                             |
| [Switch to GtkWidget’s children APIs](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.40)                                                                                                                                                                                                                                                                                                                                                                | same as "Adapt to GtkContainer removal" above                                                                                  |
| [Adapt to drawing model changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.45)                                                                                                                                                                                                                                                                                                                                                                     | cairoarea.py, gtk_drawing_area_set_draw_func() using maybe enough here, snapshot?, same as "Stop using GtkWidget::draw" below. |
| [Widgets are now visible by default](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.47)                                                                                                                                                                                                                                                                                                                                                                 | show() is no-op on init now, hide() may need to be added somewhere,  show_all() 171 instances need to be removed.              |
| [GtkWidget event signals are removed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.51)                                                                                                                                                                                                                                                                                                                                                                | BIG ISSUE, cairoarea.py needs to be first customer for fixing                                                                  |
| [Stop using GtkWidget::draw](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.53)                                                                                                                                                                                                                                                                                                                                                                         | cairoarea.py, gtk_drawing_area_set_draw_func() using maybe enough here, snapshot?                                              |
| [Window content observation has changed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.54)                                                                                                                                                                                                                                                                                                                                                             | YES, timeline draw updates                                                                                                     |
| [Monitor handling has changed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.55)                                                                                                                                                                                                                                                                                                                                                                       | Instead of a monitor number, GdkMonitor is used, see e.g. utilsgtk.py                                                          |
| [Adapt to monitor API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.56)                                                                                                                                                                                                                                                                                                                                                                       | n_monitors is not in Gtk 4                                                                                                     |
| [Adapt to cursor API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.57)                                                                                                                                                                                                                                                                                                                                                                        | set_cursor() many instances, we need to apply changes to tline canvas widget only                                              |
| [Adapt to icon size API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.58)                                                                                                                                                                                                                                                                                                                                                                     | Needed, some instances                                                                                                         |
| [gtk_widget_get_surface has been removed](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.70)                                                                                                                                                                                                                                                                                                                                                            | Breaks MLT SDL1 video display                                                                                                  |
| [Switch to the new Drag-and-Drop api](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.78)                                                                                                                                                                                                                                                                                                                                                                | dnd.py etc.                                                                                                                    |
| [Update to GtkFileChooser API changes](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.80)                                                                                                                                                                                                                                                                                                                                                               | ?? get_file (), get_filename (), get_filenames ()                                                                              |
| [Stop using blocking dialog functions](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.81)                                                                                                                                                                                                                                                                                                                                                               | 1 instance, batchrendering.py                                                                                                  |
| [Do not use widget style properties](https://developer-old.gnome.org/gtk4/stable/gtk-migrating-3-to-4.html#id-1.7.4.3.6) [Don’t use -gtk-gradient in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.41) [Don’t use -gtk-outline-…-radius in your CSS](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.44) [Stop using GtkContainer::border-width](https://developer-old.gnome.org/gtk4/stable/ch41s02.html#id-1.7.4.4.32) | These will worked on last, initial port with Adwaita.                                                                          |

### Conversion test commits

Can't get xid for widgets in Gtk4 anymore
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
