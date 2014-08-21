import itertools
import os
import stat
import sys


class TransparentLineReader:
    """
    Very simple class that facilitates reading from an already opened
    file (e.g. stdin) or a filename or a named pipe
    without the caller needing to know which it is

    TODO: Handle IO errors more gracefully
    """
    def __init__(self, filename):
        self.do_close = True
        self.fd = None
        self.handle = None
        self.open = True

        if isinstance(filename, file):
            self.handle = filename
            self.do_close = False  # Don't close something if it wasn't opened by us
        elif stat.S_ISFIFO(os.stat(filename).st_mode):
            self.fd = os.open(filename, os.O_RDONLY)
            self.handle = os.fdopen(self.fd, 'r')
        else:
            self.handle = open(filename, 'r')

    def __iter__(self):
        return self

    def next(self):
        line = self.handle.readline()
        if line == "":
            self.close()
            raise StopIteration
        else:
            return line

    def close(self):
        if self.do_close and self.open:
            self.handle.close()
        self.open = False


def map_csv_to_cycle(arg, f, sep=','):
    """
    Map the supplied argument to a cycle, by splitting by sep and
    applying the function f
    """
    values = arg.split(sep)
    try:
        values = map(f, values)
    except ValueError as e:
        print >> sys.stderr, e
        return False
    return itertools.cycle(values)