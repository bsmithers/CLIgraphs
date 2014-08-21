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


def get_columns_from_string(column_string):
    """
    Takes a unix cut-like format for columns, returning a list
    of integers suitable for indexing into a list of fields (i.e. 0-based)
    """
    columns = []
    if column_string is None:
        return columns

    list_pieces = column_string.strip().split(',')
    list_pieces = map(lambda x: x.strip(), list_pieces)

    try:
        for list_piece in list_pieces:
            range_pieces = list_piece.split('-')
            if len(range_pieces) > 2:
                print >>sys.stderr, "Malformated column range"
                sys.exit()

            if len(range_pieces) == 1:
                columns.append(int(range_pieces[0]))
            else:
                columns.extend(range(int(range_pieces[0]), int(range_pieces[1]) + 1))
    except ValueError as e:
        print >> sys.stderr, e
        return []

    return map(lambda c: c-1, columns)