__author__ = 'wzz'

import gui.mplgraphicsview


class DiffractionPlotView(gui.mplgraphicsview.MplGraphicsView):
    """
    Class ... extends ...
    for specific needs of the graphics view for interactive plotting of diffraction patten,
    including peak and background
    """
    def __init__(self, parent):
        """
        Purpose
        :return:
        """
        gui.mplgraphicsview.MplGraphicsView.__init__(self, parent)

        # Define the class variable
        # list of tuple as (peak position, indicator key)
        self._peakIndicatorList = list()

        return

    def add_peak_indicator(self, peak_pos):
        """
        Purpose:
            Indicate the position of a peak on the figure
        Requirements:
            Peak position must be given in current range
        Guarantees:
            A dashed line is drawn vertically across the figure as an indicator
        :param peak_pos:
        :return:
        """
        # Check
        left_x, right_x = self.getXLimit()
        assert left_x <= peak_pos <= right_x, 'Specified peak position %f is out of canvas range ' \
                                              '(%f, %f)' % (peak_pos, left_x, right_x)

        # Add indicator
        indicator_key = self.add_vertical_indicator(peak_pos, 'red')

        # Update peak indicator list
        self._peakIndicatorList.append((peak_pos, indicator_key))

        return

    def clear_highlights(self):
        """
        Purpose:
            Clear all highlighted data
        Requirements:
            None
        Guarantees:
            All plots to highlight are removed
        :return:
        """
        # Get key/index for highlighted plots
        num_highlighted = len(self._myHighlightsList)
        for i_line in xrange(num_highlighted):
            h_key = self._myHighlighsList[i_line]
            self.remove_line(h_key)

        return

    def highlight_peak(self, left_x, right_x):
        """
        Purpose:
            Highlight a peak
        Requirements:
            Left_x and right_x are within data range;
            Data is loaded on canvas
        Guarantees:
            Diffraction pattern between left_x and right_x is plot with different color
        :param left_x:
        :param right_x:
        :return:
        """
        # Check requirements
        assert len(self._vecX) > 1
        assert self._vecX[0] <= left_x < right_x <= self._vecX[-1]

        # Get the sub data set of

        return

    def highlight_peak_indicator(self, indicator_index):
        """
        Purpose:
            Highlight a peak's indicator
        Requirements:
            Indicator index is valid
        Guarantees:
            The indicator (line) is replotted with a thicker line
        :param indicator_index:
        :return:
        """
        # Check requirements
        assert 0 <= indicator_index < len(self._peakIndicatorList), \
            'Indicator index %d is out of index range [0, %d).' % (indicator_index, len(self._peakIndicatorList))

        # Get indicator key
        indicator_key = self._peakIndicatorList[indicator_index][1]

        # Re-plot
        self.highlight_indictor(indicator_key)

        return

    def get_peak_indicator_by_position(self, peak_pos):
        """
        Purpose:
            Locate the peak indicator that is nearest to the peak position
        Requirements:
            1. peak position is within data range;
            2. at least there is one peak indicator;
        Guarantees:
            The key (or index) of the peak indicator will be returned
        :param peak_pos:
        :return:
        """
        # Check requirement

        # Return if there is only one peak
        if len(self._peakIndicatorList) == 1:
            return self._peakIndicatorList[0][1]

        # Use binary search to locate the nearest peak indicator to peak position.
        # TODO/NOW - Complete it!

        return

    def plot_diffraction_pattern(self, vec_x, vec_y):
        """
        TODO/NOW/ Doc
        :return:
        """
        # Record the data for future usage... ...

        # Plot
        pattern_key = self.add_plot_1d(vec_x, vec_y)

        return

    def remove_peak_indicator(self, peak_indicator_index):
        """ Remove a peak indicator
        Purpose:
            Remove a peak indicator according to a given position value
        Requirements:
            Peak index should be a valid value
        Guarantees:
            The indicator is removed from the canvas
        :param peak_indicator_index:
        :return:
        """
        self.remove_indicator(peak_indicator_index)

        # remove the tuple from list
        self._peakIndicatorList.pop(i) #((peak_pos, indicator_key))


        return
