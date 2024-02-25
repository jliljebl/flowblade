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

    print("Changed lines for ", replace_string, line_count)


def _append_line_after(starts_string, sub_string, append_line):
    files_changed_count = 0
   
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

            changed = False
            for line in lines:
                new_lines.append(line)
                if line.startswith(starts_string) and changed == False:
                    if sub_string in line:
                        new_lines.append(append_line + "\n")
                        changed = True

            if changed == True:
                files_changed_count += 1
                with open(file_path, "w") as f:
                    f.writelines(new_lines)  
   
    print("Files changed with added line: " + append_line + " " + str(files_changed_count))


_substring_replace(' Gtk.VBox', ' gtkbox.VBox')
_substring_replace(' Gtk.HBox', ' gtkbox.HBox')

_append_line_after("from gi.repository import", "Gtk", "import gtkbox")

_substring_replace("gi.require_version('Gtk', '3.0')","gi.require_version('Gtk', '4.0')")


_substring_replace('class RenderQueueView(Gtk.VBox):', 'class RenderQueueView(Gtk.Box):')



