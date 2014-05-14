#!/usr/bin/env python2

import argparse
import matplotlib
import matplotlib.gridspec as gridspec
import sys

import utils


class CLIGraph(object):

    def __init__(self, **kwargs):
        self.min_inputs = kwargs.get('min_inputs', 0)
        self.max_inputs = kwargs.get('max_inputs', 1)
        self.num_plots_x = kwargs.get('num_plots_x', 1)
        self.num_plots_y = kwargs.get('num_plots_y', 1)

        # Is there a better way to do this? Subclasses may also want this kind of
        # functionality and it could rapidly get unweidly.
        self.arg_defaults = {}
        self.arg_defaults['grid'] = kwargs.get('grid_default_on', False)
        self.gs_bottom = self.gs_left = 0
        self.gs_top = self.gs_right = 1

    def get_parser(self):
        """
        Return an ArgumentParser. Chilrdren should override this method
        and call super() before adding their own options
        """
        parser = argparse.ArgumentParser()

        # Figure Options
        parser.add_argument("-t", "--title", help="Image title", default="")
        parser.add_argument("--x-label", help="Label on the x axis", default="")
        parser.add_argument("--y-label", help="Label on the y axis", default="")

        self.add_variable_option(parser, 'grid', self.arg_defaults['grid'], 'the grid')
        # Output Options
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

    def add_variable_option(self, parser, name, enabled, help_text):
        """
        Add a toggle option to the argument parser where the initial state is
        determined by 'enabled'. If enabled, an option to turn off the option is
        provided instead with a --no- prefix. Underscores in option names are
        translated to dashes
        """
        option_name = name.replace('_', '-')
        if enabled:
            parser.add_argument('--no-' + option_name, help='Disable ' + help_text,
                                action='store_false', dest=name)
        else:
            parser.add_argument('--' + option_name, help="Enable " + help_text,
                                action='store_true')

    def check_args(self, cli_args, inputs):
        """
        Check the arguments make sense
        """
        if not self.min_inputs <= len(inputs) <= self.max_inputs:
            print >> sys.stderr, 'The expected number of inputs is between %d and %d' % (
                self.min_inputs, self.max_inputs)
            return False

        if cli_args.quiet and not cli_args.save:
            print >> sys.stderr, 'Running in quiet mode and no save desination was provided!'
            return False

        return True

    def graphify(self, cli_args, inputs):
        """
        Step through the process of graph creation. Children not requiring large modifications
        can simply override the appropriate methods
        """
        if not self.check_args(cli_args, inputs):
            return

        fig = self.create_figure(cli_args)
        axes = self.create_axes(fig, cli_args)
        self.process_input(axes, cli_args, inputs)
        self.format_graph(fig, axes, cli_args)
        self.finalise(fig, cli_args)

    def format_graph(self, fig, axes, cli_args):
        """
        Apply formatting steps, titles, lables, legends etc
        """
        self.apply_lables_and_titles(fig, axes, cli_args)
        self.format_axes(axes, cli_args)

    def format_axes(self, axes, cli_args):
        """
        Apply formatting to the axes""
        """
        if cli_args.grid:
            axes.grid()

    def create_figure(self, cli_args):
        """
        Create the figure object, setting figure size, dpi etc.
        """
        if cli_args.quiet:
            matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        self.plt = plt
        fig = plt.figure(figsize=(cli_args.fig_x * cli_args.fig_scale,
                                  cli_args.fig_y * cli_args.fig_scale))

        return fig

    def create_axes(self, fig, cli_args):
        """
        Create the axes for this graph. Although this baseclass creates
        a single subplot, grid_spec is still used for the custom tight_layout
        """

        self.grid_spec = gridspec.GridSpec(1, 1)
        axes = [fig.add_subplot(sp) for sp in self.grid_spec]
        axes = axes[0]

        return axes

    def process_input(self, axes, cli_args, inputs):
        """
        Do something with the inputs
        """
        pass

    def apply_lables_and_titles(self, fig, axes, cli_args):
        """
        Set graph titles and labels. With multiple plots, grid_spec dimensions are adjusted
        to make space
        """
        title, x_label, y_label = map(lambda s: s.decode('string_escape'), [
                                      cli_args.title, cli_args.x_label, cli_args.y_label])

        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        axes.set_title(title)

    def finalise(self, fig, cli_args):
        """
        Set final graph attributes then show and or save
        """
        self.grid_spec.tight_layout(
            fig, rect=[self.gs_left, self.gs_bottom, self.gs_right, self.gs_top])
        if cli_args.save is not None:
            for format in cli_args.save_formats.split(','):
                self.plt.savefig(cli_args.save + '.' + format)

        if not cli_args.quiet:
            self.plt.show()
