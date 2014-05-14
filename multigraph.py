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

        self.num_plots_x = num_plots_x
        self.num_plots_y = num_plots_y

    def get_parser(self):
        parser = super(MultiGraph, self).get_parser()
        parser.add_argument('--multigraph-specific')
        return parser

    def format_axes(self, axes, cli_args):
        """
        Apply formatting to the axes by iterating over our axes""
        """
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
            fig.text(0.5, self.gs_bottom, cli_args.x_label, ha='center', va='center')

        if y_label:
            self.gs_left += 0.02
            fig.text(self.gs_left, 0.5, cli_args.y_label,
                     ha='center', va='center', rotation='vertical')

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
