

import NatronEngine

import os

# This run by Natron after render is started

#print "In Natron Render Modify"

user_natron_dir = os.getenv("HOME") + "/.flowblade/natron/"
instance_id_path = user_natron_dir + "LATEST_RENDER_INSTANCE_ID"
instance_id_file = open(instance_id_path, "r")
instance_id = instance_id_file.read()
instance_id_file.close()

exec_data_file_path = user_natron_dir + "mod_data_" + str(instance_id)
exec_data_file = open(exec_data_file_path, "r")
exec_code = exec_data_file.read()
exec_data_file.close()

#print exec_code

exec exec_code 

#print "exec done"
#solidNode = app.getNode("Solid2")
#colorParam = solidNode.getParam("color")
#colorParam.set(0.9, 0.9, 0.1, 1.0)

