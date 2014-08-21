#!/usr/bin/env python2

import itertools
import sys

import scipy.stats

import cligraph
import utils


class Linegraph(cligraph.CLIGraph):

    def __init__(self, **kwargs):
        super(Linegraph, self).__init__(**kwargs)
        self.axes_twin = None

    def check_args(self, cli_args, inputs):
        super(Linegraph, self).check_args(cli_args, inputs)

        self.x_col = cli_args.x_column - 1
        self.y_cols = utils.get_columns_from_string(cli_args.y_column)

        self.colours = itertools.cycle(cli_args.colours)
        self.axes_associations = utils.map_csv_to_cycle(cli_args.axes, int)

        return bool(self.y_cols) and self.axes_associations

    def get_parser(self):
        parser = super(Linegraph, self).get_parser()

        # Inputs
        parser.add_argument("-x", "--x-column", help="Column for x values. (1-based indexing). \
            Default = 1", type=int, default=1)
        parser.add_argument("-y", "--y-column", help="Column for y values. (1-based indexing). \
            Unix cut format for multiple columns. Default = 2", default="2")

        parser.add_argument('-c', '--colours', default='rgbcymk')
        parser.add_argument('-a', '--axes', help="Comma separated 1 and 2, to associate inputs \
            with different y-axes", default='1')
        return parser

    def input_started_hook(self, axes, cli_args, inp, inp_index):
        self.x_data = []
        self.y_data = []
        for _ in self.y_cols:
            self.y_data.append([])

    def input_ended_hook(self, axes, cli_args, inp, inp_index):

        for data in self.y_data:
            axis_to_use = axes
            association = self.axes_associations.next()
            if association == 2:
                if self.axes_twin is None:
                    self.axes_twin = axes.twinx()
                axis_to_use = self.axes_twin
            axis_to_use.errorbar(self.x_data, data, c=self.colours.next())

    def process_input_by_fields(self, axes, cli_args, inp, inp_index, fields):
        """
        Do something with the inputs to create a scatter graph
        """
        self.x_data.append(float(fields[self.x_col]))
        for index, column in enumerate(self.y_cols):
            self.y_data[index].append(float(fields[column]))

if __name__ == '__main__':
    l = Linegraph(grid_default_on=True)
    l.graphify()