__author__ = 'wzz'

import bisect

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
        # Canvas moving mode
        self._inZoomMode = False
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

        # mouse position
        self._mouseX = 0
        self._mouseY = 0
        self._mouseResolution = 0.01
        self._cursorType = 0

        self._vecX = list()
        self._vecY = list()

        return

    def _add_peak(self, peak_center, center_id, left_id, right_id):
        """
        Add a peak to list
        :param peak_center:
        :param center_id:
        :param left_id:
        :param right_id:
        :return:
        """
        self._currentPeakList.append([peak_center, center_id, left_id, right_id])

        # [DB] FIXME/TODO/Delete me ASAP
        for p in self._currentPeakList:
            print p

        self._construct_peak_range_map()
        self._construct_vicity_map()

        return

    def _construct_peak_range_map(self):
        """ Construct a 2-vector-tuple to check peak range quickly
        :return:
        """
        # clear the 2-tuple
        self._vecX = list()
        self._vecY = list()

        # sort all peaks
        self._currentPeakList.sort()

        # create vectors
        num_peaks = len(self._currentPeakList)
        for i_peak in xrange(num_peaks):
            # get peak parameters
            peak_center, center_id, left_id, right_id = self._currentPeakList[i_peak]
            # get boundaries
            left_x = self.get_indicator_position(left_id)[0]
            right_x = self.get_indicator_position(right_id)[1]
            assert left_x < peak_center < right_x
            # add to vector
            self._vecX.extend([left_x, right_x])
            self._vecY.extend([-1, center_id])

        return

    def clear_peak_by_position(self, peak_pos):
        """

        :param peak_pos:
        :return:
        """

        return False

    def clear_peak_by_id(self, peak_id):
        """

        :param peak_id:
        :return:
        """

        return False

    def get_number_of_peaks(self):
        """

        :return:
        """
        # TODO/NOW/DOC

        return len(self._currentPeakList)

    def get_peak(self, index):
        """ Get peak by the simple index from 0 to (num peaks - 1)
        :param index:
        :return:
        """
        # TODO/NOW/ - check

        #

        return

    def get_peak_by_indicator(self, indicator_id):
        """ Get peak by indicator ID
        :param indicator_id:
        :return:
        """
        # FIXME - This is a brute force searching algorithm.  It won't be efficient if there are many peaks
        # TODO/NOW - Doc!
        for peak_tup in self._currentPeakList:
            if peak_tup[1] == indicator_id:
                return peak_tup

        return None

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
        # Check movement
        x_min, x_max = self.getXLimit()
        resolution_x = (x_max - x_min) * self._mouseResolution
        y_min, y_max = self.getYLimit()
        resolution_y = (y_max - y_min) * self._mouseResolution
        if abs(event.x - self._mouseX) < resolution_x and abs(event.y - self._mouseY) < resolution_y:
            # movement is small
            return

        # No operation if NOT in peak picking mode
        if self._myPeakSelectionMode != DiffractionPlotView.PeakAdditionMode.QuickMode:
            return

        # check zoom mode
        if self._myToolBar.get_mode() != 0 and self._inZoomMode is False:
            self._inZoomMode = True
            print 'Try to set main window title 1'
            self._myCanvas.setWindowTitle('Zoom mode! Unable to add peak!')
        elif self._myToolBar.get_mode() == 0 and self._inZoomMode is True:
            self._inZoomMode = False
            print 'Try to set main window title 1'
            self._myCanvas.setWindowTitle('Add peak!')
        else:
            pass
            # print 'No operation'

        # No operation in zooming mode
        if self._inZoomMode is True:
            return

        # change cursor
        if self._inZoomMode is False:
            if self._cursorType == 0:
                new_cursor = QtCore.Qt.SplitHCursor
                self._cursorType = 1
            elif self._cursorType == 1:
                new_cursor = QtCore.Qt.CrossCursor
                self._cursorType = 2
            elif self._cursorType == 2:
                new_cursor = QtCore.Qt.ArrowCursor
                self._cursorType = 0
            QtGui.QApplication.setOverrideCursor(new_cursor)

        QtCore.Qt.DragMoveCursor


        """
        if pressed:
            cursor1 = QtGui.QCursor(QtCore.Qt.CrossCursor)
            cursor2 = QtGui.QCursor(QtCore.Qt.SplitHCursor)
            QtGui.QApplication.setOverrideCursor(cursor2)
        """

        self._mouseX = event.x
        self._mouseY = event.y

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

        print '[DB] Cursor shape: ', self._myCanvas.cursor().shape()
        # NOTE: regular cursor = 0
        #       cross cursor   = 2
        #

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
                print 'HERE!'
                self._respond_right_button(x)
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

        self._add_peak(x, peak_id, left_id, right_id)

        return

    def _respond_right_button(self, x):
        """

        :param x:
        :return:
        """
        # FIXME/TODO/ Clean after development is finished
        print self._vecX
        print self._vecY

        range_index = bisect.bisect_left(self._vecX, x)
        if range_index == len(self._vecX):
            print '[DB-BAT] Out of range rightmost'
        elif self._vecY[range_index] < 0:
            print '[DB-BAT] Out of range'
        else:
            peak_center_index = self._vecY[range_index]
            print '[DB-BAT] Peak center index is ', peak_center_index, 'peak position is ', \
                self.get_indicator_position(peak_center_index)

        return

    def on_mouse_release_event(self, event):
        """

        :param event:
        :return:
        """
        x = event.x
        y = event.y
        button = event.button

        print 'Released @ ', x, y, 'by button', button

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
