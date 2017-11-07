"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2017 Janne Liljeblad and contributors.

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

"""
Atomic file write support.
"""

import os
import md5

MAX_CREATE_FILE_ATTEMPTS = 10

class AtomicFileWriteError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class AtomicFileWriter(object):
    """
    Context manager for writing files atomically.

    Usage:

        with AtomicFileWriter("/path/to/file") as afw:
            f = afw.get_file()

            # do stuff with writable file object
            f.write("hello world\n")

    Behind the scenes, a temp file will be created in /path/to/, and when
    the context manager block goes out of scope, the temp file will be
    atomically renamed to /path/to/file.

    Because of the atomic nature of this write, /path/to/file will either
    contain the complete contents of the written file, or retain its
    previous state.
    """

    def __init__(self, file_path, mode=None):
        """
        AtomicFileWriter constructor.

        Accepts a file path to write to (eventually)
        """

        # absolute path to the temp file used for writing
        self.tmp_file_path = None

        if mode is None:
            self.mode = "w"
        elif (mode == "w") or (mode == "wb"):
            self.mode = mode
        else:
            raise ValueError("AtomicFileWriter only accepts 'w' or 'wb' as valid modes")

        # absolute path to the file that the caller eventually wants to write
        self.dest_file_path = os.path.abspath(file_path)

        # absolute path to the directory containing the files
        self.dir_path = os.path.dirname(file_path)

        # destination base filename (without the parent path)
        self.basename = os.path.basename(file_path)

        # temp file object
        self.file_obj = None

    def __enter__(self):
        """
        Context manager starting point.

        Creates a temp file, and returns a reference to this instance.
        """

        # try several times to create a new temp file
        for i in range(MAX_CREATE_FILE_ATTEMPTS):
            # pick a temp filename that we hope is unique
            maybe_tmp_file_path = self.__get_random_filename(self.basename)

            try:
                # create the temp file, with a guarantee that it didn't exist before
                # this returns a numeric file descriptor
                # the mode of 666 is passed in because it will be filtered by the user's umask
                fd = os.open(maybe_tmp_file_path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o666)

                # if we didn't get an OSError by now, turn the numeric
                # file descriptor into a Python file object
                self.file_obj = os.fdopen(fd, "w")

                # remember the temp file path
                self.tmp_file_path = maybe_tmp_file_path

                # we created a file, stop trying
                break

            except OSError:
                pass

        # if we were unable to create a temp file, raise an error
        if not self.tmp_file_path:
            raise AtomicFileWriteError("could not open '%s' for writing" % (self.dest_file_path,))

        # return a reference to this instance so it can be used as a context manager
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """
        Context manager cleanup.

        Flushes and closes the temp file (if necessary),
        and atomically renames it into place.
        """

        # if we caught an exception from inside the context manager block,
        # then remove the temp file and let the exception bubble up
        if exception_type:
            try:
                # close the temp file if necessary
                if not self.file_obj.closed:
                    self.file_obj.close()

                # remove the temp file
                os.unlink(self.tmp_file_path)

            except:
                print "Error cleaning up temp file: " + self.tmp_file_path

            # let the original exception that was passed into this method bubble up
            return False

        # if the caller didn't already close the file
        if not self.file_obj.closed:
            # flush the file buffer to disk
            self.file_obj.flush()

            # close the file
            self.file_obj.close()

        # rename the temp file into the final destination
        os.rename(self.tmp_file_path, self.dest_file_path)

    def get_file(self):
        """
        Get a reference to the writable temp file object.

        This returns a regular Python file object.
        """

        return self.file_obj

    def __get_random_filename(self, basepath):
        """
        Create a candidate temp filename, without touching the filesystem.
        """

        uuid_str = md5.new(str(os.urandom(32))).hexdigest()
        return ".tmp-" + uuid_str + "-" + basepath

