__author__ = 'wzz'

from PyQt4 import QtGui, QtCore
import mplgraphicsview


class DiffractionPlotView(mplgraphicsview.MplGraphicsView):
    """
    Class ... extends ...
    for specific needs of the graphics view for interactive plotting of diffraction patten,
    including peak and background
    """
    class PeakAdditionMode:
        """ Enumerate for peak adding mode
        """
        NormalMode = 0
        QuickMode = 1

        def __init__(self):
            """ Init
            """
            return

    def __init__(self, parent):
        """
        Purpose
        :return:
        """
        # Base class constructor
        mplgraphicsview.MplGraphicsView.__init__(self, parent)

        # Define the class variable
        # Peak selection mode
        self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.NormalMode
        # peak process status

        # List of current peaks (in QuickMode);
        # each element should be a tuple as
        # (peak center position, indicator ID (center), indicator ID (left boundary), indicator ID (right boundary))
        self._currentPeakList = list()

        # default peak width
        self._defaultPeakWidth = 0.03

        # Interaction with the canvas
        self._myCanvas.mpl_connect('button_press_event', self.on_mouse_press_event)
        self._myCanvas.mpl_connect('button_release_event', self.on_mouse_release_event)
        self._myCanvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

        return

    def set_quick_add_mode(self, mode):
        """

        :param mode:
        :return:
        """
        # TODO/NOW - Doc
        if mode is True:
            self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.QuickMode
        else:
            self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.NormalMode

        return

    def on_mouse_motion(self, event):
        """
        :param event:
        :return:
        """
        """
        if pressed:
            cursor1 = QtGui.QCursor(QtCore.Qt.CrossCursor)
            cursor2 = QtGui.QCursor(QtCore.Qt.SplitHCursor)
            QtGui.QApplication.setOverrideCursor(cursor2)
        """

        return

    def on_mouse_press_event(self, event):
        """

        :return:
        """
        # Get data
        x = event.xdata
        # y = event.ydata
        button = event.button

        # if mode is 2, it means that the zoom button is pressed and shouldn't do anything at all!
        # print '[DB-BAT] Tool bar mode = ', self._myToolBar.get_mode()
        if self._myToolBar.get_mode() != 0:
            return

        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.NormalMode:
            print '[DB-BAT] Peak selection-Normal Mode: No operation.'
            pass
        elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.QuickMode:
            # operation
            if button == 1:
                # left button
                self._respond_left_button(x)
            elif button == 3:
                # right button
                self._reponse_right_button(x)
        else:
            # unrecognized
            raise RuntimeError('Peak selection mode %s is not supported!' % str(self._myPeakSelectionMode))

        return

    def _respond_left_button(self, x):
        """

        :param x:
        :return:
        """
        peak_id = self.add_vertical_indicator(x, 'red')
        left_id = self.add_vertical_indicator(x - self._defaultPeakWidth, 'orange')
        right_id = self.add_vertical_indicator(x + self._defaultPeakWidth, 'blue')

        return

    def on_mouse_release_event(self, event):
        """

        :param event:
        :return:
        """
        print 'Released @ ', event.x, event.y

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
        assert isinstance(peak_pos, float), 'Input peak position must be a float'
        assert peak_pos > 0.
        assert left_x <= peak_pos <= right_x, 'Specified peak position %f is out of canvas range ' \
                                              '(%f, %f)' % (peak_pos, left_x, right_x)

        # Add indicator
        indicator_key = self.add_vertical_indicator(peak_pos, 'red')

        # Update peak indicator list
        self._currentPeakList.append((peak_pos, indicator_key))

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
        assert 0 <= indicator_index < len(self._currentPeakList), \
            'Indicator index %d is out of index range [0, %d).' % (indicator_index, len(self._currentPeakList))

        # Get indicator key
        indicator_key = self._currentPeakList[indicator_index][1]

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
        if len(self._currentPeakList) == 1:
            return self._currentPeakList[0][1]

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
        pattern_key = self.add_plot_1d(vec_x, vec_y, color='blue', marker='.')

        return

    def remove_all_peak_indicators(self):
        """ Remove all peaks' indicators
        :return:
        """
        # Remove all indicators
        for indicator_tup in self._currentPeakList:
            indicator_key = indicator_tup[1]
            self.remove_indicator(indicator_key)

        # Clear the indicator position-key list
        self._currentPeakList = list()

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
        self._currentPeakList.pop(i)  #((peak_pos, indicator_key))


        return
