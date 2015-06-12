#!/usr/bin/env python2

from __future__ import division
import itertools
import math
import sys

import numpy
import scipy.stats

import cligraph
import utils

"""
TODO:
- Auto-detect number of bins
- Fixed width or variable width bins
- Stacked bins, overlapped bins or bins next to each other
- Change which side of bin is open (default: bins are half-open, closed on left, except final bin
  which is closed both sides)
"""


class Histogram(cligraph.CLIGraph):

    def __init__(self, **kwargs):
        super(Histogram, self).__init__(**kwargs)
        self.data = []
        self.data_params = []

    def check_args(self, cli_args, inputs):
        super(Histogram, self).check_args(cli_args, inputs)

        self.fields = utils.get_columns_from_string(cli_args.field)
        self.colours = itertools.cycle(cli_args.colours.split(','))
        self.markers = itertools.cycle(cli_args.markers)

        self.alphas = utils.map_csv_to_cycle(cli_args.alpha, float)
        self.histtypes = itertools.cycle(cli_args.hist_type.split(','))

        if cli_args.legends:
            self.legends = itertools.cycle(cli_args.legends)
        else:
            self.legends = itertools.cycle([None])

        # Should we store all data and render only after reading everything?
        self.store = False
        if cli_args.unify_bins:
            self.store = True

        # Set bin defaults if none given
        if not cli_args.bins and not cli_args.bin_size:
            cli_args.bins = 10

        return bool(self.fields) and bool(self.alphas)

    def get_parser(self):
        parser = super(Histogram, self).get_parser()

        # Inputs
        parser.add_argument('-f', '--field', help='Column to read values from. (1-based indexing). \
            Unix cut format for multiple columns. Default = 1', default='1')

        # Histogram setup
        parser.add_argument('--normed', help='Normalise frequency?', action="store_true",
                            default=False)
        parser.add_argument("--cumulative", help="Cumulative Frequency? Default=0",
                            action="store_true", default=False)
        parser.add_argument("--logscale", help="Use a logarithmic y-axs", action="store_true",
                            default=False)
        parser.add_argument("--legends", nargs="+", help="Dataset legends", default=None)

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-b', '--bins', help='Number of bins. If not given and bin-size not \
            given, this will default to 10', type=int)
        group.add_argument('-z', '--bin-size', help='Size of each bin', type=float)
        parser.add_argument('-u', '--unify-bins', action="store_true", default=False,
                            help='Unify bin sizes across different input sources')

        parser.add_argument('--disable-bin-offset', help="By default, bins are offset by half their\
                            width to help bins straddle integer values for example",
                            action="store_true", default=False)

        # Visual
        parser.add_argument('-c', '--colours', default='r,g,b,c,y,m,k')
        parser.add_argument('-m', '--markers', default=' ')
        parser.add_argument('-a', '--alpha', default='0.5')
        parser.add_argument('-y', '--hist-type', default='bar')

        return parser

    def input_started_hook(self, axes, cli_args, inp, inp_index):
        """
        Setup data structures
        """
        if not self.store:
            self.data = []
            self.data_params = []

        for _ in self.fields:
            self.data.append([])
            self.data_params.append({'min': float('inf'), 'max': float('-inf')})

    def input_ended_hook(self, axes, cli_args, inp, inp_index):
        """
        Draw histogram at end of input unless we have to store data (e.g. for bin calculation)
        """
        if self.store:
            return

        self.__draw_histogram(axes, cli_args)

    def process_input_by_fields(self, axes, cli_args, inp, inp_index, fields):
        """
        Store value for each dataset
        """
        for index, column in enumerate(self.fields):
            value = float(fields[column])
            if self.store:
                index = inp_index * len(self.fields) + index

            # Store min/max values for bin work
            self.data_params[index]['min'] = min(value, self.data_params[index]['min'])
            self.data_params[index]['max'] = max(value, self.data_params[index]['max'])
            self.data[index].append(float(fields[column]))

    def process_input(self, axes, cli_args, inputs):
        """
        If we are doing bin-size auto detection and require consist bin size
        across different inputs, we will have to read all data first before
        we can process
        """

        super(Histogram, self).process_input(axes, cli_args, inputs)

        if self.store:
            self.__draw_histogram(axes, cli_args)

    def apply_lables_and_titles(self, fig, axes, cli_args):
        """
        Add legend if we have them
        TODO: This can probably by done more generally, just have to be careful about
        plots with multiple axes.
        """
        super(Histogram, self).apply_lables_and_titles(fig, axes, cli_args)
        if cli_args.legends:
            axes.legend()

    def __draw_histogram(self, axes, cli_args):
        """
        Plot histograms for all datasets in current data
        """

        for index, dataset in enumerate(self.data):
            bins = self.__get_bins(cli_args, index)
            axes.hist(dataset, bins, facecolor=self.colours.next(), alpha=self.alphas.next(),
                      normed=cli_args.normed, cumulative=cli_args.cumulative,
                      log=cli_args.logscale, label=self.legends.next(), hatch=self.markers.next(),
                      histtype=self.histtypes.next())

    def __get_bins(self, cli_args, index):
        """
        Get the bin histogram parameter for the data at the given index. Use the supplied
        number of bins if given. Otherwise, calculate based on the supplied bin width.
        """

        # Short-circuit if we are given number of bins and not using equal bins
        if cli_args.bins and not self.store:
            return cli_args.bins

        # Get the minimum and maximum values either for this dataset or for all datasets
        # if we are post-processing
        min_val = self.data_params[index]['min']
        max_val = self.data_params[index]['max']
        if self.store:
            min_val = min([self.data_params[i]['min'] for i in range(0, len(self.data_params))])
            max_val = max([self.data_params[i]['max'] for i in range(0, len(self.data_params))])

        # For a fixed number of bins, do a linear fit. Otherwise, use a range with bin size
        if cli_args.bins:
            # Fit one extra value to include right edge (same as normal histogram behaviour)
            return numpy.linspace(min_val, max_val, cli_args.bins + 1)

        # Compute bins. Do not use range as values may be floats.
        # Lowest bin should be the largest multiple of bin_size that is <= min_val
        # Highest bin should be smallest multiple of bin_size that is >= max_val

        bins = []
        i = math.floor(min_val / cli_args.bin_size) * cli_args.bin_size

        # By default, bits are offset by half their width from the lowest value rather
        # than by their full width
        if not cli_args.disable_bin_offset:
            i -= cli_args.bin_size / 2
        else:
            i -= cli_args.bin_size

        while i <= max_val:
            bins.append(i)
            i += cli_args.bin_size
        bins.append(i)  # Add final bin

        # Combine offscreen bins for faster renders
        if cli_args.min_x and cli_args.min_x > min_val:
            first_onscreen = max([index for index, b in enumerate(bins) if b <= cli_args.min_x])
            # Include the first bin so that this captures everything offscren
            if first_onscreen >= 2:
                bins = [bins[0]] + bins[first_onscreen:]
        if cli_args.max_x and cli_args.max_x < max_val:
            last_onscreen = min([index for index, b in enumerate(bins) if b > cli_args.max_x])
            if last_onscreen < len(bins) - 1:
                bins = bins[:last_onscreen] + [bins[-1]]

        return bins


if __name__ == '__main__':
    hist = Histogram(grid_default_on=True)
    hist.graphify()
