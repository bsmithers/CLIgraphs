#!/usr/bin/env python2

import argparse
import sys

import cligraph
import utils

class scatter(cligraph.CLIgraph):
    def __init__(self, cli_args, inputs):
        super(scatter, self).__init__(cli_args, inputs)

    def process_input(self, fig, cli_args, inputs):
        """
        Do something with the inputs to create a scatter graph
        """

        # Think about how we want to do some of the boilerplate for single
        # axes figures (most likely for these CLI graphs) whilst being able
        # to extend to multiple axes
        ax = fig.add_subplot(111)

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

        ax.scatter(x_data, y_data)
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[cligraph.get_parent_parser()])
    parser.add_argument('--scatter-specific')
    args, inputs = parser.parse_known_args()

    s = scatter(args, inputs)
    s.graphify(args, inputs)