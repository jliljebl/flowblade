"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import appconsts

"""
Module for project data objects used my multiple modules and objects here are part of save files.

NOTE: IMPORTANT!!! We can't rename or remove anything here without BREAKING USER SAVE FILES!!!!!

NOTE: Do not use any external modules other then appconsts.
"""


INGEST_ENCODING = "ingenc"
INGEST_RELATIONS = "ingtransrel"
INGEST_ACTION = "ingaction"

INGEST_ENCODING_NOT_SET = -1
INGETS_ACTION_NOTHING = 0
INGETS_ACTION_COPY = 1
INGETS_ACTION_TRANSCODE = 2


class ProjectProxyEditingData:
    
    def __init__(self):
        self.proxy_mode = appconsts.USE_ORIGINAL_MEDIA
        self.create_rules = None # not impl.
        self.encoding = 0 # default is first found encoding
        self.size = 1 # default is half project size


class IngestTranscodeData:
    
    def __init__(self):
        self.data = {}
        self.data[INGEST_ENCODING] = 0
        self.data[INGEST_RELATIONS] = {}
        self.data[INGEST_ACTION] = 0

    def set_default_encoding(self, def_enc):
        self.data[INGEST_ENCODING] = def_enc
        
    def get_default_encoding(self):
        return self.data[INGEST_ENCODING]

    def set_default_encoding(self, def_enc):
        self.data[INGEST_ENCODING] = def_enc

    def get_action(self):
        return self.data[INGEST_ACTION]

    def set_action(self, action):
        self.data[INGEST_ACTION] = action
