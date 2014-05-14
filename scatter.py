#!/usr/bin/env python2

import sys

import cligraph
import utils


class Scatter(cligraph.CLIGraph):

    def __init__(self, **kwargs):
        super(Scatter, self).__init__(**kwargs)

    def process_input(self, axes, cli_args, inputs):
        """
        Do something with the inputs to create a scatter graph
        """

        # Do we want to generalise this too? We can probably assume each graph
        # is reading tsv data.
        x_data = []
        y_data = []
        read_from = sys.stdin
        if len(inputs) > 0:
            read_from = inputs[0]
        for line in utils.TransparentLineReader(read_from):
            x, y = map(float, line.strip().split())
            x_data.append(x)
            y_data.append(y)

        axes.scatter(x_data, y_data)

    def get_parser(self):
        parser = super(Scatter, self).get_parser()
        parser.add_argument('--scatter-specific')
        return parser

if __name__ == '__main__':

    s = Scatter(grid_default_on=True)

    parser = s.get_parser()
    args, inputs = parser.parse_known_args()
    s.graphify(args, inputs)
