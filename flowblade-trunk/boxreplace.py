#!/usr/bin/env python3

import fnmatch
import glob
import os
import sys



# Get launch script dir
launch_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
src_dir = launch_dir + "/Flowblade"


def _substring_replace(sub_string, replace_string):
    line_count = 0
    changed_files = []
    for root, dirnames, filenames in os.walk(src_dir):
        for filename in filenames:
            
            if filename.endswith(".py") == False:
                continue
            
            file_path = os.path.join(root, filename)
            
            lines = None
            new_lines = []
            changed = False

            with open(file_path, "rt") as f:
                lines = f.readlines()

            for line in lines:
                
                replaced_line = line.replace(sub_string, replace_string)
                if line != replaced_line:
                    line_count += 1
                    changed_files.append(file_path)
                    line = replaced_line
                    changed = True

                new_lines.append(line)
            
            if changed == True:
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  

    print("Changed line/s into: ", replace_string, line_count)


def _insert_line_after(starts_string, sub_string, append_line, lines_in_between=0, show_files=False):
    files_changed_count = 0

    changed_files = []
    for root, dirnames, filenames in os.walk(src_dir):
        for filename in filenames:
            insert_index = -99
            if filename.endswith(".py") == False:
                continue

            file_path = os.path.join(root, filename)
            
            lines = None
            new_lines = []
            changed = False

            with open(file_path, "rt") as f:
                lines = f.readlines()

            changed = False
            for line in lines:
                new_lines.append(line)
                if line.startswith(starts_string) and changed == False:
                    if sub_string in line:
                        if lines_in_between == 0:
                            new_lines.append(append_line + "\n")
                            changed = True
                        else:
                            insert_index = len(new_lines) + lines_in_between
                if len(new_lines) == insert_index:
                    new_lines.append(append_line + "\n")
                    changed = True
                    
            if changed == True:
                files_changed_count += 1
                changed_files.append(filename)
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  
   
    print("Files changed with added line: " + append_line + " " + str(files_changed_count))
    if show_files == True:
        print(changed_files)


_substring_replace(' Gtk.VBox', ' gtkbox.VBox')
_substring_replace(' Gtk.HBox', ' gtkbox.HBox')

_insert_line_after("from gi.repository import", "Gtk", "import gtkbox")

_substring_replace("gi.require_version('Gtk', '3.0')","gi.require_version('Gtk', '4.0')")


_substring_replace('class RenderQueueView(Gtk.VBox):', 'class RenderQueueView(Gtk.Box):')
_insert_line_after('class RenderQueueView(Gtk.Box):', 'Gtk.Box', '        gtkbox.set_default_vertical(self)', 5, True)

_substring_replace('class ProfileInfoBox(Gtk.VBox):', 'class ProfileInfoBox(Gtk.Box):')
_insert_line_after('class ProfileInfoBox(Gtk.Box):', 'Gtk.Box', '        gtkbox.set_default_vertical(self)', 5, True)

_substring_replace('class PositionNumericalEntries(Gtk.HBox):', 'class PositionNumericalEntries(Gtk.Hox):')
_insert_line_after('class PositionNumericalEntries(Gtk.Hox):', 'Gtk.Box', '        gtkbox.set_default_horizontal(self)', 5, True)


vboxes = ["class ImageTextTextListView(Gtk.VBox):", "class TextTextListView(Gtk.VBox):",
"class MultiTextColumnListView(Gtk.VBox):", "class MultiTextColumnListView(Gtk.VBox):",
"class BinTreeView(Gtk.VBox):","class ImageTextImageListView(Gtk.VBox):",
"class FilterSwitchListView(Gtk.VBox):","class TextListView(Gtk.VBox):",
"class JobsQueueView(Gtk.VBox):","class AbstractKeyFrameEditor(Gtk.VBox):",
"class RotoMaskKeyFrameEditor(Gtk.VBox):","class MediaRelinkListView(Gtk.VBox):",
"class MediaLogListView(Gtk.VBox):","class ProjectEventListView(Gtk.VBox):",
"class PreviewPanel(Gtk.VBox):","class TextLayerListView(Gtk.VBox):",
"class ScaleSelector(Gtk.VBox):"]

for vbox in vboxes:
    fixed_box = vbox.replace("VBox", "Box")
    _substring_replace(vbox, fixed_box)
    _insert_line_after(fixed_box, 'Gtk.Box', '        gtkbox.set_default_vertical(self)', 8, True)

hboxes = ["class ClipInfoPanel(Gtk.HBox):","class CompositorInfoPanel(Gtk.HBox):",
"class PluginInfoPanel(Gtk.HBox):", "class BinInfoPanel(Gtk.HBox):",
"class ClipEditorButtonsRow(Gtk.HBox):", "class GeometryEditorButtonsRow(Gtk.HBox):",
"class FadeLengthEditor(Gtk.HBox):",
"class AbstractSimpleEditor(Gtk.HBox):"]

for hbox in hboxes: 
    fixed_box = hbox.replace("HBox", "Box")
    _substring_replace(hbox, fixed_box)
    _insert_line_after(fixed_box, 'Gtk.Box', '        gtkbox.set_default_horizontal(self)', 8, True)


_substring_replace("class TimeLineScroller(Gtk.HScrollbar):", "class TimeLineScroller(Gtk.Scrollbar):")
_insert_line_after('class TimeLineScroller(Gtk.Scrollbar):', 'Gtk.Scrollbar', '        self.set_orientation (Gtk.Orientation.HORIZONTAL)', 10, True)

