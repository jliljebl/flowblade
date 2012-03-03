#!/usr/bin/env python
import os, sys

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
