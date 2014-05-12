#!/usr/bin/env python2

import argparse
import matplotlib
import sys

import utils

def get_parent_parser():
    """
    Return the base parser used to set standard image attributes 
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-q', '--quiet', help='Do not display a graph. When envoked with -q, the \
        agg backend will be used so no SCREEN is needed', action='store_true', default=False)
    parser.add_argument('-s', '--save', help='Save an image with this *basename*. Extension & \
        format are determined by --save-formats')
    parser.add_argument('--save-formats', default='png,pdf', 
        help='A comma separated list of formats to use with --save')
    parser.add_argument("--fig-x", help="x figure size (default=8)", type=int, default=8)
    parser.add_argument("--fig-y", help="y figure size (default=6)", type=int, default=6)
    parser.add_argument("--fig-scale", help="Scale factor for figure size (default=1)", 
        type=float, default=1)

    return parser

class CLIgraph(object):
    def __init__(self, cli_args, inputs, **kwargs):
        self.min_inputs = kwargs.get('min_inputs', 0)
        self.max_inputs = kwargs.get('max_inputs', 1)
        self.check_args(cli_args, inputs)

    def check_args(self, cli_args, inputs):
        """
        Check the arguments make sense
        """
        if not self.min_inputs <= len(inputs) <= self.max_inputs:
            print >> sys.stderr, 'The expected number of inputs is between %d and %d' % (self.min_inputs,
             self.max_inputs)
            return False

        if cli_args.quiet and not cli_args.save:
            print >> sys.stderr, 'Running in queit mode and no save desination was provided!'
            return False

        return True

    def graphify(self, cli_args, inputs):
        fig = self.create_graph(cli_args)
        self.process_input(fig, cli_args, inputs)
        self.finalise(fig, cli_args)

    def create_graph(self, cli_args):
        """
        Create the figure object, setting figure size, dpi etc. 
        """
        if cli_args.quiet:
            matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        self.plt = plt
        fig = plt.figure(figsize=(cli_args.fig_x * cli_args.fig_scale, cli_args.fig_y * cli_args.fig_scale))

        return fig

    def process_input(self, fig, cli_args, inputs):
        """
        Do something with the inputs
        """
        pass

    def finalise(self, fig, cli_args):
        """
        Set final graph attributes then show and or save
        """
        if cli_args.save is not None:
            for format in cli_args.save_formats.split(','):
                self.plt.savefig(cli_args.save + '.' + format)

        if not cli_args.quiet:
            self.plt.show() 

