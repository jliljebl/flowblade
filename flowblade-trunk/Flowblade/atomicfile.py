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

Can also be run as a stand-alone script to do ad-hoc testing of the
AtomicFileWriter class.
"""

import hashlib
import os
import sys

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

        with AtomicFileWriter("/path/to/file", "w") as afw:
            f = afw.get_file()

            # do stuff with writable file object
            f.write("hello world\n")

    Behind the scenes, a temp file will be created in /path/to/, and when
    the context manager block goes out of scope, the temp file will be
    atomically renamed to /path/to/file.

    POSIX guarantees that rename() is an atomic operation, so on any
    reasonable UNIX filesystem, the file will either show up in the
    destination path with all of its contents, or it won't show up at all.
    Additionally, if a file was already in the destination path, it will
    not be corrupted. Either it will be cleanly overwritten, or it will
    be preserved in its former state without modification.
    """

    def __init__(self, file_path, mode, debug=False):
        """
        AtomicFileWriter constructor.

        Accepts a file path to write to (eventually), and a file write
        mode (either "w" or "wb" for text or binary, respectively).

        Also accepts an optional debug boolean argument, which will
        print out messages for testing and troubleshooting.
        """

        # validate file path
        if file_path is None:
            raise ValueError("file_path can not be None")

        # validate mode
        if mode in ("w", "wb"):
            self.mode = mode
        else:
            raise ValueError("AtomicFileWriter only accepts 'w' or 'wb' as valid modes")

        # absolute path to the temp file used for writing
        self.tmp_file_path = None

        # absolute path to the file that the caller eventually wants to write
        self.dest_file_path = os.path.abspath(file_path)

        # absolute path to the directory containing the files
        self.dir_path = os.path.dirname(self.dest_file_path)

        # destination base filename (without the parent path)
        self.basename = os.path.basename(self.dest_file_path)

        # temp file object
        self.file_obj = None

        # debugging mode
        self.debug = debug

    def __enter__(self):
        """
        Context manager starting point.

        Creates a temp file, and returns a reference to this instance.
        """

        # try several times to create a new temp file
        for i in range(MAX_CREATE_FILE_ATTEMPTS):
            # pick a temp filename that we hope is unique
            maybe_tmp_filename = self.__get_random_filename(self.basename)

            # add the candidate temp filename to the directory where the destination
            # file will be written. since the temp and final destination file are
            # in the same directory, rename() will never cross filesystems.
            maybe_tmp_file_path = os.path.join(self.dir_path, maybe_tmp_filename)

            try:
                # create the temp file, with a guarantee that it didn't exist before
                # this returns a numeric file descriptor
                # the mode of 666 is passed in because it will be filtered by the user's umask
                fd = os.open(maybe_tmp_file_path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o666)

                # if we didn't get an OSError by now, turn the numeric
                # file descriptor into a Python file object
                self.file_obj = os.fdopen(fd, self.mode)

                # remember the temp file path
                self.tmp_file_path = maybe_tmp_file_path

                if self.debug:
                    print("Created temp file: '%s'" % (self.tmp_file_path))

                # we created a file, stop trying
                break

            except OSError:
                pass

        # if we were unable to create a temp file, raise an error
        #
        # the destination file path is reported in this error instead of the temp file path,
        # and although this is slightly innacurate from this low-level context, it will be
        # a less surprising error message for a user of the program who really intends to
        # write the destination file eventually, and not some temp file
        if not self.tmp_file_path:
            raise AtomicFileWriteError("Could not open '%s' for writing" % (self.dest_file_path))

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
                print("Error cleaning up temp file: " + self.tmp_file_path)

            # let the original exception that was passed into this method bubble up
            return False

        # if the caller didn't already close the file
        if not self.file_obj.closed:
            # flush the file buffer to disk
            self.file_obj.flush()

            # close the file
            self.file_obj.close()

        try:
            # rename the temp file into the final destination
            os.rename(self.tmp_file_path, self.dest_file_path)

            if self.debug:
                print("Renamed temp file: '%s' to '%s'" % (self.tmp_file_path, self.dest_file_path))

        except:
            print("Error renaming temp file '%s' to '%s'" % (self.tmp_file_path, self.dest_file_path))

            # if the rename didn't work, try to clean up the temp file
            try:
                os.unlink(self.tmp_file_path)

                if self.debug:
                    print("Removed temp file: '%s'" % (self.tmp_file_path))
            except:
                print("Error removing temp file '%s' after rename to '%s' failed" % \
                      (self.tmp_file_path, self.dest_file_path))

            # let the os.rename() failure exception bubble up
            raise

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

        uuid_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
        return ".tmp-" + uuid_str + "-" + basepath

# command-line mode for testing
def main():
    if 2 != len(sys.argv):
        sys.stderr.write("usage: python3 atomicfile.py [file_path_to_write]\n")
        sys.exit(1)

    dest_file = sys.argv[1]

    with AtomicFileWriter(dest_file, "w", True) as afw:
        f = afw.get_file()
        f.write("test file written by atomicfile.AtomicFileWriter\n")

    sys.exit(0)

if __name__ == "__main__":
    main()

