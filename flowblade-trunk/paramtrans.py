#!/usr/bin/env python
import os, sys

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

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
#source_file_path = script_dir + "/Flowblade/res/filters/filters.xml"
source_file_path = script_dir + "/Flowblade/res/filters/compositors.xml"
output_file_path = script_dir + "/params_trans_output"

# Read source
source_file = open(source_file_path)
source_text = source_file.read()

# Go through lines and build output
lines = source_text.splitlines()
out_lines = []
d_name_len = len("displayname=")
name_len = len("name=")
for line in lines:
    if ((("property" in line) or ("multipartproperty" in line))
        and (not("no_editor" in line))):
        i = line.find("displayname=")
        
        if i != -1:
            start = i + d_name_len
        else:
            i = line.find("name=")
            start = i + name_len + 1
        e1 = line.find('"', start)
        e2 = line.find(' ', start)
        if e2 != -1 and (e2 < e1 ):
            end = e2
        else:
            end = e1
        param_name = line[start:end]
        param_name = param_name.replace("!", " ")
        out_line = '    param_names["' + param_name + '"] = _("' + param_name + '")\n'
        out_lines.append(out_line)
out_str = "".join(out_lines)

# Write out
out_file = open(output_file_path,"w")
out_file.write(out_str)
out_file.close()
