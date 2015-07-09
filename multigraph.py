"""
An extension of a standard cligraph for plotting
graphs with subplots using gridspec
"""

import matplotlib
import matplotlib.gridspec as gridspec

from cligraph import CLIGraph


class MultiGraph(CLIGraph):

    def __init__(self, num_plots_x, num_plots_y, **kwargs):
        super(MultiGraph, self).__init__(**kwargs)

        self.arg_defaults['compress_ticks'] = kwargs.get('compress_ticks_default', True)
        self.arg_defaults['equalise_x'] = kwargs.get('equalise_x_default', True)
        self.arg_defaults['equalise_y'] = kwargs.get('equalise_y_default', True)

        self.num_plots_x = num_plots_x
        self.num_plots_y = num_plots_y

    def get_parser(self):
        parser = super(MultiGraph, self).get_parser()
        parser.add_argument('--h-pad', type=float, default=0.6,
                            help='Height padding between subplots')
        parser.add_argument('--w-pad', type=float, default=0.6,
                            help='Width padding between subplots')
        self.add_variable_option(parser, 'compress_ticks', self.arg_defaults['compress_ticks'],
                                 'axes tick compression, which shows tick lables only on the left \
                                 row and bottom column')
        self.add_variable_option(parser, 'equalise_x', self.arg_defaults['equalise_x'],
                                 'equalisation of x axes ranges across subplots')
        self.add_variable_option(parser, 'equalise_y', self.arg_defaults['equalise_y'],
                                 'equalisation of y axes ranges across subplots')

        return parser

    def format_axes(self, axes, cli_args):
        """
        Apply formatting to the axes by iterating over our axes""
        """

        if cli_args.compress_ticks:
            # Only display labels on bottom and left axes
            # note that we hide the tick labels rather than the ticks themselves
            # to make scanning across/down easier on the eye
            map(lambda ax: ax.label_outer(), axes)

        # Optionally set the range of the axes to be consistent across all subplots
        if cli_args.equalise_x:
            min_x = min([ax.get_xlim()[0] for ax in axes])
            max_x = max([ax.get_xlim()[1] for ax in axes])
            map(lambda ax: ax.set_xlim(min_x, max_x), axes)

        if cli_args.equalise_y:
            min_y = min([ax.get_ylim()[0] for ax in axes])
            max_y = max([ax.get_ylim()[1] for ax in axes])
            map(lambda ax: ax.set_ylim(min_y, max_y), axes)

        for ax in axes:
            super(MultiGraph, self).format_axes(ax, cli_args)

    def create_axes(self, fig, cli_args):
        """
        Create the axes for this graph using gridspec for subplots
        """

        self.grid_spec = gridspec.GridSpec(self.num_plots_x, self.num_plots_y)
        axes = [fig.add_subplot(sp) for sp in self.grid_spec]

        return axes

    def apply_lables_and_titles(self, fig, axes, cli_args):
        """
        Set graph titles and labels. With multiple plots, grid_spec dimensions are adjusted
        to make space
        """
        title, x_label, y_label = map(lambda s: s.decode('string_escape'), [
                                      cli_args.title, cli_args.x_label, cli_args.y_label])

        # For multiple axes, we make room and apply text(); this keeps things working
        # with tight layout
        if title:
            self.gs_top -= 0.02
            self.plt.suptitle(title)

        if x_label:
            # Ajust rather than set, children can then make space for other graphics
            self.gs_bottom += 0.02
            fig.text(0.5, self.gs_bottom, cli_args.x_label, ha='center', va='center', fontsize=cli_args.x_label_fontsize)

        if y_label:
            self.gs_left += 0.02
            fig.text(self.gs_left, 0.5, cli_args.y_label,
                     ha='center', va='center', rotation='vertical', fontsize=cli_args.y_label_fontsize)

    def finalise(self, fig, cli_args):
        """
        Set final graph attributes then show and or save
        """
        self.grid_spec.tight_layout(
            fig, h_pad=cli_args.h_pad, w_pad=cli_args.w_pad,
            rect=[self.gs_left, self.gs_bottom, self.gs_right, self.gs_top])
        if cli_args.save is not None:
            for format in cli_args.save_formats.split(','):
                self.plt.savefig(cli_args.save + '.' + format)

        if not cli_args.quiet:
            self.plt.show()
