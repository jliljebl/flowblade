

import os
import sys


def get_modules_path():
    return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))