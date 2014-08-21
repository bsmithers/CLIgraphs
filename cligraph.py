#!/usr/bin/env python2

import argparse
import matplotlib
import matplotlib.gridspec as gridspec
import sys

import utils


class CLIGraph(object):

    def __init__(self, **kwargs):
        self.min_inputs = kwargs.get('min_inputs', 0)
        self.max_inputs = kwargs.get('max_inputs', -1)
        self.num_plots_x = kwargs.get('num_plots_x', 1)
        self.num_plots_y = kwargs.get('num_plots_y', 1)
        self.allow_stdin = kwargs.get('allow_stdin', True)

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
        parser.add_argument("--separator", help="Field separator for tsv-like input files. \
            String.split() compatible", default=None)
        parser.add_argument("-t", "--title", help="Image title", default="")
        parser.add_argument("--x-label", help="Label on the x axis", default="")
        parser.add_argument("--y-label", help="Label on the y axis", default="")

        parser.add_argument("--min-x", help="Minimum value on the x axis",
                            type=float, default=None)
        parser.add_argument("--max-x", help="Maximum value on the x axis",
                            type=float, default=None)
        parser.add_argument("--min-y", help="Minimum value on the y axis",
                            type=float, default=None)
        parser.add_argument("--max-y", help="Maximum value on the y axis",
                            type=float, default=None)
        parser.add_argument("--square", help="Force square axis limits",
                            action="store_true", default=False)

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
        if not self.min_inputs <= len(inputs) or (
                self.max_inputs > -1 and len(inputs) <= self.max_inputs):
            print >> sys.stderr, 'The expected number of inputs is between %d and %d' % (
                self.min_inputs, self.max_inputs)
            return False

        if cli_args.quiet and not cli_args.save:
            print >> sys.stderr, 'Running in quiet mode and no save desination was provided!'
            return False

        self.num_inputs = len(inputs)
        return True

    def graphify(self):
        """
        Step through the process of graph creation. Children not requiring large modifications
        can simply override the appropriate methods
        """
        cli_args, inputs = self.get_args_and_inputs(self.get_parser())

        if not self.check_args(cli_args, inputs):
            return

        fig = self.create_figure(cli_args)
        axes = self.create_axes(fig, cli_args)
        self.process_input(axes, cli_args, inputs)
        self.format_graph(fig, axes, cli_args)
        self.finalise(fig, cli_args)

    def get_args_and_inputs(self, parser):
        """
        Return the arguments and list of inputs to read from.
        List of inputs will be length 0 or more, including stdin if allowed
        All inputs are of type utils.TransparentLineReader
        """

        args, inputs = parser.parse_known_args()
        if self.allow_stdin and len(inputs) == 0:
            inputs = [sys.stdin]

        inputs = [utils.TransparentLineReader(i) for i in inputs]

        return args, inputs

    def format_graph(self, fig, axes, cli_args):
        """
        Apply formatting steps, titles, lables, legends etc
        """
        self.apply_lables_and_titles(fig, axes, cli_args)
        self.format_axes(axes, cli_args)

    def format_axes(self, axes, cli_args):
        """
        Apply formatting to the axes
        """
        if cli_args.grid:
            axes.grid()

        if cli_args.min_x is not None:
            axes.set_xlim(left=cli_args.min_x)
        if cli_args.max_x is not None:
            axes.set_xlim(right=cli_args.max_x)

        if cli_args.min_y is not None:
            axes.set_ylim(bottom=cli_args.min_y)
        if cli_args.max_y is not None:
            axes.set_ylim(top=cli_args.max_y)

        if cli_args.square:
            x_min, x_max = axes.get_xlim()
            y_min, y_max = axes.get_ylim()
            axes_min = min(x_min, y_min)
            axes_max = max(x_max, y_max)
            axes.set_xlim(left=axes_min, right=axes_max)
            axes.set_ylim(bottom=axes_min, top=axes_max)

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
        Do something with the inputs. By default, this loops through
        and calls process_single_input() on each input we have, then
        close the input
        """

        for index, inp in enumerate(inputs):
            self.input_started_hook(axes, cli_args, inp, index)
            self.process_single_input(axes, cli_args, inp, index)
            self.input_ended_hook(axes, cli_args, inp, index)
            inp.close()

    def input_started_hook(self, axes, cli_args, inp, index):
        pass

    def input_ended_hook(self, axes, cli_args, inp, index):
        pass

    def process_single_input(self, axes, cli_args, inp, inp_indx):
        """
        Process a single input(file). By default, read line by line and
        call process input by line
        """
        for line in inp:
            self.process_input_by_line(axes, cli_args, inp, inp_indx, line)

    def process_input_by_line(self, axes, cli_args, inp, inp_indx, line):
        """
        Process a line from an input(file). By default, split the line into
        fields (based on aseparator argument), then call process_input_by_fields
        """
        fields = line.strip().split(cli_args.separator)
        self.process_input_by_fields(axes, cli_args, inp, inp_indx, fields)

    def process_input_by_fields(self, axes, cli_args, inp, inp_indx, fields):
        """
        Handle inputs to the file where a record is a line split into fields
        For now, believe this to be the functionality required by most graphing
        scripts so we make this easy but allow customisation. This may change.
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
