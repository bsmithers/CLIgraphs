#!/usr/bin/env python2

import collections
import itertools

import cligraph
import utils


class Barchart(cligraph.CLIGraph):

    def __init__(self, **kwargs):
        self.categories = []
        self.category_to_index = {}
        self.data = collections.defaultdict(lambda: collections.defaultdict(int))
        self.errors = collections.defaultdict(lambda: collections.defaultdict(int))
        super(Barchart, self).__init__(**kwargs)

    def check_args(self, cli_args, inputs):
        super(Barchart, self).check_args(cli_args, inputs)

        self.fields = utils.get_columns_from_string(cli_args.field)
        self.error_fields = utils.get_columns_from_string(cli_args.error_field)
        if self.error_fields and len(self.fields) != len(self.error_fields):
            print >> sys.stderr, "# error columns must match # of data columns"
            return False
        self.total_datasets = len(inputs) * len(self.fields)
        self.colours = itertools.cycle(cli_args.colours.split(','))
        self.error_colours = itertools.cycle([None] if not cli_args.e_colours else cli_args.e_colours.split(','))
        self.alphas = utils.map_csv_to_cycle(cli_args.alpha, float)
        self.markers = itertools.cycle(cli_args.markers)

        if cli_args.legends:
            self.legends = itertools.cycle(cli_args.legends)
        else:
            self.legends = itertools.cycle([None])

        return bool(self.fields) and bool(self.alphas)

    def get_parser(self):
        parser = super(Barchart, self).get_parser()

        # Inputs
        parser.add_argument('-f', '--field', help='Column to read values from. (1-based indexing). \
            Unix cut format for multiple columns. Default = 1', default='2')
        parser.add_argument('-e', '--error-field', help='Column to read error bars from. (1-based \
            indexing). Unix cut format for multiple columns. Default = None', default=None)
        parser.add_argument('-d', '--cat-field', help='Column to read category from. (1-based \
            indexing). Default = 1', default=1, type=int)

        # Barchart setup
        parser.add_argument("--logscale", help="Use a logarithmic y-axs", action="store_true",
                            default=False)
        parser.add_argument("--legends", nargs="+", help="Dataset legends", default=None)

        parser.add_argument('--fig-legend', action="store_true", default=False)
        parser.add_argument('--fig-legend-loc', default="lower left")
        parser.add_argument('--fig-legend-ncol', type=int, default=1)


        # Visual
        parser.add_argument('--legend-fontsize', default=None, type=int)
        parser.add_argument('--tick-fontsize', default=None, type=int)

        parser.add_argument('-c', '--colours', default='r,g,b,c,y,m,k')
        parser.add_argument('--e-colours', default=None)
        parser.add_argument('-a', '--alpha', default='0.5')
        parser.add_argument('-m', '--markers', default=' ')
        parser.add_argument("--width", help="Overall width of each category", type=float,
                            default=0.8)


        return parser

    def process_input_by_fields(self, axes, cli_args, inp, inp_index, fields):
        """
        Store value for each dataset
        """

        # Track cateogies. Any dataset missing a category will get a zero value later
        category_index = len(self.categories)
        category = fields[cli_args.cat_field - 1]  # -1 because argument is 1-based
        if category in self.category_to_index:
            category_index = self.category_to_index[category]
        else:
            self.category_to_index[category] = category_index
            self.categories.append(category)

        # Add data for each field
        for index, column in enumerate(self.fields):
            value = float(fields[column])
            index = inp_index * len(self.fields) + index

            # Store min/max values for bin work
            self.data[index][category_index] = value

        for index, column in enumerate(self.error_fields):
            value = float(fields[column])
            index = inp_index * len(self.fields) + index

            # Store min/max values for bin work
            self.errors[index][category_index] = value


    def process_input(self, axes, cli_args, inputs):
        super(Barchart, self).process_input(axes, cli_args, inputs)
        self.__draw_barchart(axes, cli_args)

    def apply_lables_and_titles(self, fig, axes, cli_args):
        """
        Add legend if we have them
        """
        super(Barchart, self).apply_lables_and_titles(fig, axes, cli_args)
        if cli_args.legends:
            if not cli_args.fig_legend:
                axes.legend()
            else:
                handles, labels = axes.get_legend_handles_labels()
                self.plt.figlegend(handles, labels, cli_args.fig_legend_loc, ncol=cli_args.fig_legend_ncol, fancybox=True, fontsize=cli_args.legend_fontsize)

                # For now, we will hack on the spacing, but this may be a better solution long term
                # http://stackoverflow.com/a/10154763
                self.gs_bottom = 0.05
                


    def format_axes(self, axes, cli_args):
        super(Barchart, self).format_axes(axes, cli_args)
        axes.set_xticks([ i + 0.5 for i in range(0, len(self.categories))])
        axes.set_xticklabels(self.categories, fontsize=cli_args.tick_fontsize)
        axes.set_xlim(0, len(self.categories))

        if cli_args.tick_fontsize:
            map(lambda t : t.label.set_fontsize(cli_args.tick_fontsize), axes.yaxis.get_major_ticks())

    def __draw_barchart(self, axes, cli_args):
        """
        Plot barcharts for all dataset
        """

        bar_width = cli_args.width / self.total_datasets

        for i in range(0, self.total_datasets):
            left_pad = (1 - cli_args.width) / 2
            # X values should be adjusted for bar width
            #x_vals = [i + bar_width * x for x in range(0, len(self.categories))]
            x_vals = [left_pad + x + i * bar_width for x in range(0, len(self.categories))]
            y_vals = [self.data[i][self.category_to_index[c]] for c in self.categories]

            y_errors = None
            if self.error_fields:
                y_errors = [self.errors[i][self.category_to_index[c]] for c in self.categories]

            axes.bar(x_vals, y_vals, bar_width, facecolor=self.colours.next(), yerr=y_errors,
                     alpha=self.alphas.next(), log=cli_args.logscale, label=self.legends.next(),
                     hatch=self.markers.next(), ecolor=self.error_colours.next())


if __name__ == '__main__':
    graph = Barchart()
    graph.graphify()
