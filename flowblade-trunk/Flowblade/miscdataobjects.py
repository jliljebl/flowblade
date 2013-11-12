

import appconsts



"""
Module for data objects used my multiple modules.

This module is used when import structure gets worse if
object is included in any of the modules that they are used in.
"""

class ProjectProxyEditingData:
    
    def __init__(self):
        self.proxy_mode = appconsts.USE_ORIGINAL_MEDIA
        self.create_rules = None # not impl.
        self.encoding = 0 # default is first found encoding
        self.size = 1 # default is half project size
