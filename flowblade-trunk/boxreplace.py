#!/usr/bin/env python3

import fnmatch
import glob
import os
import sys



# Get launch script dir
launch_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
src_dir = launch_dir + "/Flowblade"

def _first_non_whitespace_index(s):
    return len(s) - len(s.lstrip())

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


def _line_end_replace(sub_string, replace_string):
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
                    replace_index = line.find(sub_string)
                    replaced_line = line[0:replace_index] + replace_string + "\n"
                    line_count += 1
                    changed_files.append(file_path)
                    line = replaced_line
                    changed = True

                new_lines.append(line)
            
            if changed == True:
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  

    print("Changed line/s ends into: ", replace_string, line_count)
    
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

def _comment_out_with_substring(sub_string, show_files=False):
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
                if sub_string in line:
                    non_white_index = _first_non_whitespace_index(line)
                    if non_white_index == -1:
                        fix_line = "#" + line
                    else:
                        fix_line = line[:non_white_index] + "#" + line[non_white_index:]
                    line = fix_line
                    changed = True
                new_lines.append(line)
            
            if changed == True:
                changed_files.append(file_path)
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  

    print("Commented out files count for string: ", sub_string, len(changed_files))
    if show_files == True:
        print(changed_files)

def _file_line_replace(target_filename, line_number, sub_string, replace_string):
    line_count = 0
    changed_files = []
    for root, dirnames, filenames in os.walk(src_dir):
        for filename in filenames:

            if filename.endswith(".py") == False:
                continue
            print(filename)
            if filename != target_filename:
                continue
            
            print("ATTEMPTING file", filename)
            file_path = os.path.join(root, filename)
            
            lines = None
            new_lines = []
            changed = False

            with open(file_path, "rt") as f:
                lines = f.readlines()

            for i in range(0, len(lines)):
                line = lines[i]
                if i > line_number - 2 and i < line_number + 2: # line numbers move around a bit.
                    print("line", i)
                    replaced_line = line.replace(sub_string, replace_string)
                    print(line, replaced_line)
                    if line != replaced_line:
                        print("line change", replaced_line)
                        line_count += 1
                        changed_files.append(file_path)
                        line = replaced_line
                        changed = True

                new_lines.append(line)
            
            if changed == True:
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  
    if len(changed_files) == 1:
        print("Changed line ", str(line_number) ," in file ", target_filename, "into: ", replace_string)
    else:
        print("ERROR: ", target_filename, line_number, sub_string, replace_string)

_substring_replace(' Gtk.VBox', ' gtkbox.VBox')
_substring_replace(' Gtk.HBox', ' gtkbox.HBox')

_insert_line_after("from gi.repository import", "Gtk", "import gtkbox")

_substring_replace("gi.require_version('Gtk', '3.0')","gi.require_version('Gtk', '4.0')")


_substring_replace('class RenderQueueView(Gtk.VBox):', 'class RenderQueueView(Gtk.Box):')
_insert_line_after('class RenderQueueView(Gtk.Box):', 'Gtk.Box', '        gtkbox.build_vertical(self)', 5, True)

_substring_replace('class ProfileInfoBox(Gtk.VBox):', 'class ProfileInfoBox(Gtk.Box):')
_insert_line_after('class ProfileInfoBox(Gtk.Box):', 'Gtk.Box', '        gtkbox.build_vertical(self)', 5, True)

_substring_replace('class PositionNumericalEntries(Gtk.HBox):', 'class PositionNumericalEntries(Gtk.Box):')
_insert_line_after('class PositionNumericalEntries(Gtk.Box):', 'Gtk.Box', '        gtkbox.build_horizontal(self)', 5, True)

_substring_replace('class ScaleSelector(Gtk.VBox):', 'class ScaleSelector(Gtk.Box):')
_insert_line_after('class ScaleSelector(Gtk.Box):', 'Gtk.Box', '        gtkbox.build_vertical(self)', 5, True)

vboxes = ["class ImageTextTextListView(Gtk.VBox):", "class TextTextListView(Gtk.VBox):",
"class MultiTextColumnListView(Gtk.VBox):", "class MultiTextColumnListView(Gtk.VBox):",
"class BinTreeView(Gtk.VBox):","class ImageTextImageListView(Gtk.VBox):",
"class FilterSwitchListView(Gtk.VBox):","class TextListView(Gtk.VBox):",
"class JobsQueueView(Gtk.VBox):","class AbstractKeyFrameEditor(Gtk.VBox):",
"class RotoMaskKeyFrameEditor(Gtk.VBox):","class MediaRelinkListView(Gtk.VBox):",
"class MediaLogListView(Gtk.VBox):","class ProjectEventListView(Gtk.VBox):",
"class PreviewPanel(Gtk.VBox):","class TextLayerListView(Gtk.VBox):"]

for vbox in vboxes:
    fixed_box = vbox.replace("VBox", "Box")
    _substring_replace(vbox, fixed_box)
    _insert_line_after(fixed_box, 'Gtk.Box', '        gtkbox.build_vertical(self)', 8, True)

hboxes = ["class ClipInfoPanel(Gtk.HBox):","class CompositorInfoPanel(Gtk.HBox):",
"class PluginInfoPanel(Gtk.HBox):", "class BinInfoPanel(Gtk.HBox):",
"class ClipEditorButtonsRow(Gtk.HBox):", "class GeometryEditorButtonsRow(Gtk.HBox):",
"class FadeLengthEditor(Gtk.HBox):",
"class AbstractSimpleEditor(Gtk.HBox):"]

for hbox in hboxes: 
    fixed_box = hbox.replace("HBox", "Box")
    _substring_replace(hbox, fixed_box)
    _insert_line_after(fixed_box, 'Gtk.Box', '        gtkbox.build_horizontal(self)', 8, True)

_substring_replace("class TimeLineScroller(Gtk.HScrollbar):", "class TimeLineScroller(Gtk.Scrollbar):")
_insert_line_after('class TimeLineScroller(Gtk.Scrollbar):', 'Gtk.Scrollbar', '        self.set_orientation (Gtk.Orientation.HORIZONTAL)', 10, True)

_comment_out_with_substring("show_all", False)
_comment_out_with_substring("dnd.", False)
_comment_out_with_substring("add_events", False)

_substring_replace(".add(", ".set_child(")

_comment_out_with_substring("override_font", False)
_comment_out_with_substring("modify_font", False)

_line_end_replace("Gtk.FileChooserButton", "gtkbox.get_file_chooser_button()")

_file_line_replace("rendergui.py", 566, "self.set_child(Gtk.Label())", "self.append(Gtk.Label())")

_substring_replace("self.args_popover = Gtk.Popover.new(self.args_edit_launch.widget)", "self.args_popover = Gtk.Popover.new()")
_insert_line_after("        self.args_popover", "self.args_popover", "        self.args_popover.set_default_widget(self.args_edit_launch.widget)", 0, False)


