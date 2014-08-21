#!/usr/bin/env python2

import itertools
import sys

import scipy.stats

import cligraph
import utils


class Scatter(cligraph.CLIGraph):

    def __init__(self, **kwargs):
        super(Scatter, self).__init__(**kwargs)
        self.onclick_data = []

    def onclick(self, event):
        print event.ind
        data = self.onclick_data[event.ind[0]]
        print "Data:", data

    def check_args(self, cli_args, inputs):
        super(Scatter, self).check_args(cli_args, inputs)
        self.colours = itertools.cycle(cli_args.colours)
        self.markers = itertools.cycle(cli_args.markers)

        self.x_col = cli_args.x_column - 1
        self.y_col = cli_args.y_column - 1
        self.annotate_col = None if not cli_args.annotate_column else cli_args.annotate_column - 1
        self.onclick_col = None
        if cli_args.onclick_column:
            if len(inputs) > 1:
                print >> sys.stderr, "Onclick is currently only supported for single datasets."
                return False
            cli_args.onclick_column - 1

        # If we don't legend labels, make it a cycle of 'None'
        if not cli_args.legend:
            self.legends = itertools.cycle([None])
        else:
            self.legends = utils.map_csv_to_cycle(cli_args.legend, None)

        self.point_sizes = utils.map_csv_to_cycle(cli_args.point_size, int)
        self.alphas = utils.map_csv_to_cycle(cli_args.alpha, float)
        return (self.point_sizes and self.alphas)

    def get_parser(self):
        parser = super(Scatter, self).get_parser()

        # Inputs
        parser.add_argument("-x", "--x-column", help="Column for x values. (1-based indexing). \
            Default = 1", type=int, default=1)
        parser.add_argument("-y", "--y-column", help="Column for y values. (1-based indexing). \
            Default = 2", type=int, default=2)
        parser.add_argument("--annotate-column", help="Column for annotations. (1-based indexing)",
                            type=int, default=None)
        parser.add_argument("--onclick-column", help="Column for onclick data. (1-based indexing)",
                            type=int, default=None)

        # Figure display options
        # Maybe some of these things could be handled generically; though
        # it may not be clear what a (e.g.) colour refers to for a given graph type
        parser.add_argument('-c', '--colours', default='rgbcymk')
        parser.add_argument('-m', '--markers', default='o')
        parser.add_argument('-p', '--point-size', default='20')
        parser.add_argument('-a', '--alpha', default='1')
        parser.add_argument('-l', '--legend', default=None)

        parser.add_argument('--stats', action="store_true", default=False)
        parser.add_argument('--stats-title', action="store_true", default=False)
        return parser

    def input_started_hook(self, axes, cli_args, inp, inp_index):
        self.x_data = []
        self.y_data = []
        self.annotate_data = []

    def input_ended_hook(self, axes, cli_args, inp, inp_index):
        scatter = axes.scatter(
            self.x_data, self.y_data, c=self.colours.next(), marker=self.markers.next(),
            s=self.point_sizes.next(), alpha=self.alphas.next(), label=self.legends.next(),
            picker=True)

        if cli_args.stats or cli_args.stats_title:
            stats_id = scatter.get_label()
            if not stats_id:
                stats_id = str(inp_index)
            self.calc_and_show_stats(stats_id)

        if self.annotate_col:
            for i, annotation in enumerate(self.annotate_data):
                axes.annotate(annotation, (self.x_data[i], self.y_data[i]))

    def calc_and_show_stats(self, stats_id):
        spearmanr, spearmanp = scipy.stats.spearmanr(self.x_data, self.y_data)
        pearsonr, pearsonp = scipy.stats.pearsonr(self.x_data, self.y_data)

        if self.num_inputs > 1:
            print "Dataset:", stats_id
        print "Spearman Correlation:", (spearmanr, spearmanp)
        print "Pearson Correlation :", (pearsonr, pearsonp)

        if cli_args.stats_title:
            if len(cli_args.title) > 0:
                cli_args.title += '\n'

            if self.num_inputs == 1:
                stats_id = ""
            else:
                stats_id += ". "

            cli_args. title += '%sSpearman: (%.2f, %.2g); Pearson: (%.2f, %.2g)' % (
                stats_id, spearmanr, spearmanp, pearsonr, pearsonp)

    def process_input_by_fields(self, axes, cli_args, inp, inp_index, fields):
        """
        Do something with the inputs to create a scatter graph
        """
        self.x_data.append(float(fields[self.x_col]))
        self.y_data.append(float(fields[self.y_col]))
        if self.annotate_col:
            self.annotate_data.append(fields[self.annotate_col])
        if self.onclick_col:
            self.onclick_data.append(fields[self.onclick_col])

    def apply_lables_and_titles(self, fig, axes, cli_args):
        super(Scatter, self).apply_lables_and_titles(fig, axes, cli_args)

        # Legends could probably be handled generically.
        if cli_args.legend:
            axes.legend(scatterpoints=1)

        if cli_args.onclick_column is not None:
            fig.canvas.mpl_connect('pick_event', lambda e: self.onclick(e))


if __name__ == '__main__':

    s = Scatter(grid_default_on=True)
    s.graphify()