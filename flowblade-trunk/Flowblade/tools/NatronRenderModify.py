

import NatronEngine

import os

# This is run by Natron after render is started
user_natron_dir = os.getenv("HOME") + "/.flowblade/natron/"
instance_id_path = user_natron_dir + "LATEST_RENDER_INSTANCE_ID"
instance_id_file = open(instance_id_path, "r")
instance_id = instance_id_file.read()
instance_id_file.close()

exec_data_file_path = user_natron_dir + "/session_" + instance_id  + "/mod_data"
exec_data_file = open(exec_data_file_path, "r")
exec_code = exec_data_file.read()
exec_data_file.close()

exec exec_code 
