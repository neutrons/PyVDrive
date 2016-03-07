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
        self._inPickPeakList = list()

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
        self._mousePressed = 0 # integer: 0 for no pressed, 1 for left button, 3 for right button

        self._vecX = list()
        self._vecPeakID = list()

        self._vecPeakVicinityX = list()
        self._vecBoundaryID = list()
        self._vecPeakVicinityPID = list()

        # flag to reconstruct the peak list maps including ... and ...
        self._reconstructMaps = False

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
        self._inPickPeakList.append([peak_center, center_id, left_id, right_id])

        # [DB] FIXME/TODO/Delete me ASAP
        for p in self._inPickPeakList:
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
        self._vecPeakID = list()

        # sort all peaks
        self._inPickPeakList.sort()

        # create vectors
        num_peaks = len(self._inPickPeakList)
        for i_peak in xrange(num_peaks):
            # get peak parameters
            peak_center, center_id, left_id, right_id = self._inPickPeakList[i_peak]
            # get boundaries
            left_x = self.get_indicator_position(left_id)[0]
            right_x = self.get_indicator_position(right_id)[1]
            assert left_x < peak_center < right_x
            # add to vector
            self._vecX.extend([left_x, right_x])
            self._vecPeakID.extend([-1, center_id])

        return

    def _construct_vicinity_map(self):
        """
        Create a set of mapping vectors to check whether the mouse cursor is in between 2 peaks,
        in the vicinity of a peaks boundary or in the vicinity of peak center.
        :return:
        """
        # reset all the list
        self._vecPeakVicinityX = list()
        self._vecBoundaryID = list()
        self._vecPeakVicinityPID = list()

        current_peak_list = self._inPickPeakList[:]
        current_peak_list.extend(self._pickedPeakList)

        for peak in current_peak_list:
            # consider to refactor it with section in method _construct_peak_range_map
            peak_center, center_id, left_id, right_id = peak
            # get boundaries
            left_x = self.get_indicator_position(left_id)[0]
            right_x = self.get_indicator_position(right_id)[1]
            assert left_x < peak_center < right_x

            # add to left boundary
            temp_x_left = left_x - (right_x - left_x) * 0.1  # use 10% dx
            temp_x_right = left_x + (right_x - left_x) * 0.5
            self._vecPeakVicinityX.extend([temp_x_left, temp_x_right])
            self._vecBoundaryID.extend([-1, center_id])
            self._vecPeakVicinityPID.extend([-1, -1])

            # add to peak
            temp_x_right = peak_center + (right_x - left_x) * 0.5
            self._vecPeakVicinityX.append(temp_x_right)
            self._vecBoundaryID.extend([-1])
            self._vecPeakVicinityPID.append(center_id)
            # add to right boundary
            temp_x_right = right_x + (right_x - left_x) * 0.1
            self._vecPeakVicinityX.append(temp_x_right)
            self._vecPeakVicinityPID.append(-1)
            self._vecBoundaryID.extend(center_id)
        # END-FOR

        return


    def clear_peak_by_position(self, peak_pos):
        """

        :param peak_pos:
        :return:
        """

        return False

    def clear_peak_by_id(self, peak_id):
        """
        Remove peak-tuple from the current in-pick-up peaks
        Requirement: peak ID is a valid integer
        Guarantees: the indicators for peak, left boundary and right boundary are removed from canvas.
                    the peak tuple is removed from self._inPickList
        :param peak_id: integer
        :return: None
        """
        # check
        assert isinstance(peak_id, int), 'Input peak/indicator ID must be an integer but not %s.' \
                                         '' % str(type(peak_id))

        # find peak tuple
        remove_peak_index = -1
        for i_peak in self._inPickPeakList:
            if self._inPickPeakList[1] == peak_id:
                remove_peak_index = i_peak
                break

        # check whether it is found
        assert remove_peak_index >= 0, 'Peak/indicator ID %d does not exist on canvas.' % peak_id

        # remove peak from inPickPeakList
        remove_peak_tuple = self._inPickPeakList.pop(remove_peak_index)

        # remove from canvas
        for indicator_index in xrange(1, 4):
            self.remove_peak_indicator(remove_peak_index[indicator_index])

        return

    def get_number_of_peaks(self):
        """
        Get number of peaks that are in pick up mode on the canvas
        :return:
        """
        return len(self._inPickPeakList)

    def get_peak(self, index):
        """ Get peak by the simple index from 0 to (num peaks - 1)
        Requirements: index is valid for list self._inPickPeakList
        Guarantees: peak-tuple is returned
        :param index:
        :return:
        """
        assert isinstance(index, int), 'Peak index must be a integer but not %s.' % str(type(index))
        assert 0 <= index < len(self._inPickPeakList)

        peak_tuple = self._inPickPeakList[index]

        return peak_tuple

    def get_peak_by_indicator(self, indicator_id):
        """ Get peak by peak's indicator ID (or canvas indicator ID)
        Requirements: indicator ID must exist
        Guarantees: the peak position and indicator IDs are returned as a tuple. If the indicator ID cannot be found
                    in _inPickPeakList, then it will be returned as None
        :param indicator_id:
        :return: None or 4-tuple as peak position, peak indictor ID, left boundary ID and right boundary ID
        """
        # check
        assert isinstance(indicator_id, int), 'Peak\'s indicator ID must be an integer but not %s.' \
                                              '' % str(type(indicator_id))

        # FIXME - This is a brute force searching algorithm.  It won't be efficient if there are many peaks
        for peak_tup in self._inPickPeakList:
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
            # in zoom mode. no response is required
            return
        elif self._mousePressed == 1:
            # left mouse button is pressed and move
            self._move_selected_peak(event.x)
        else:
            # get position information for peak and boundary vicinity
            x_index = bisect.bisect_right(self._inPickPeakList, event.x)
            # check peak vicinity
            peak_vicinity_index = self._vecPeakVicinityPID[x_index+1]
            # check peak boundary vicinity
            bound_peak_indicator = self._vecBoundaryID[x_index + 1]
            # check
            assert not (peak_vicinity_index >= 0 and bound_peak_indicator >= 0), \
                'Impossible to be in 2 regions simultaneous.'

            if peak_vicinity_index >= 0:
                # peak vicinity region
                cursor_type = 1
                new_cursor = QtCore.Qt.DragMoveCursor
            elif bound_peak_indicator >= 0:
                # boundary vicinity region
                cursor_type = 2
                new_cursor = QtCore.Qt.SplitHCursor
            else:
                # in the middle of nowhere (between peaks)
                cursor_type = 0
                new_cursor = QtCore.Qt.ArrowCursor

            if cursor_type != self._cursorType:
                self._cursorType = cursor_type
                QtGui.QApplication.setOverrideCursor(new_cursor)
            """
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
        # END-IF-ELSE

        self._mouseX = event.x
        self._mouseY = event.y

        return

    def _move_selected_peak(self, new_x):
        """ Event handling while mouse's left button is pressed and moved
        Method is going to check the curse (i.e., the region that the mouse in)
        In this case, neither cursor's type nor selected peak can be changed
        :param new_x:
        :return:
        """
        # check the cursor type
        if self._cursorType == 0:
            # in between 2 peaks. no peak is selected. pointed arrow
            print 'arrow cursor, between 2 peaks, no operation.'
            pass
        elif self._cursorType == 1:
            # select a peak's center, then move the whole peak (center and boundary)
            peak_tuple = self._inPickPeakList[self._currPeakIndex]
            peak_indicator_id = peak_tuple[1]
            left_indicator_id = peak_tuple[2]
            right_indicator_id = peak_tuple[3]

            # move
            d_x = new_x - self._prevX
            new_center = peak_tuple[0] + d_x

            self.move_indicator(peak_indicator_id, d_x, 0)
            self.move_indicator(left_indicator_id, d_x, 0)
            self.move_indicator(right_indicator_id, d_x, 0)

            self._inPickPeakList[self._currPeakIndex] = (new_center, peak_tuple[1], peak_tuple[2], peak_tuple[3])

            self._reconstructMaps = True

        elif self._cursorType == 2:
            # select a peak's boundary, then widen or narrow the peak's boundary
            peak_tuple = self._inPickPeakList[self._currPeakIndex]
            peak_pos, peak_id, left_id, right_id = peak_tuple[0]
            if self._boundaryRightEdge < peak_pos:
                # left boundary
                # prev_bound_x = self.get_indicator_position(left_id)[0]
                d_x = self._prevX - new_x

            elif self._boundaryLeftEdge > peak_pos:
                # right boundary
                # prev_bound_x =
                d_x = new_x - self._prevX
            else:
                raise RuntimeError('Situation of mouse cursor is not defined!')

            # change the peak boundaries
            self.move_indicator(left_id, d_x)
            self.move_indicator(right_id, d_x)

            self._reconstructMaps = True

        # END-IF-ELSE

        return

    def on_mouse_press_event(self, event):
        """

        :return:
        """
        # Get data
        x = event.xdata
        # y = event.ydata
        button = event.button

        # Set up the status
        if button == 1:
            self._mousePressed = 1
        elif button == 3:
            self._mousePressed = 3

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
        print self._vecPeakID

        range_index = bisect.bisect_left(self._vecX, x)
        if range_index == len(self._vecX):
            print '[DB-BAT] Out of range rightmost'
        elif self._vecPeakID[range_index] < 0:
            print '[DB-BAT] Out of range'
        else:
            peak_center_index = self._vecPeakID[range_index]
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

        # set the mouse pressed status back
        self._mousePressed = 0

        # reconstruct the query map
        if self._reconstructMaps is True:
            self._construct_peak_range_map()
            self._construct_vicinity_map()

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
        assert isinstance(peak_pos, float), 'Input peak position must be a float'
        assert peak_pos > 0.
        assert left_x <= peak_pos <= right_x, 'Specified peak position %f is out of canvas range ' \
                                              '(%f, %f)' % (peak_pos, left_x, right_x)

        # Add indicator
        indicator_key = self.add_vertical_indicator(peak_pos, 'red')

        # Update peak indicator list
        self._inPickPeakList.append((peak_pos, indicator_key))

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
        assert 0 <= indicator_index < len(self._inPickPeakList), \
            'Indicator index %d is out of index range [0, %d).' % (indicator_index, len(self._inPickPeakList))

        # Get indicator key
        indicator_key = self._inPickPeakList[indicator_index][1]

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
        if len(self._inPickPeakList) == 1:
            return self._inPickPeakList[0][1]

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
        for indicator_tup in self._inPickPeakList:
            indicator_key = indicator_tup[1]
            self.remove_indicator(indicator_key)

        # Clear the indicator position-key list
        self._inPickPeakList = list()

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
        self._inPickPeakList.pop(i)  #((peak_pos, indicator_key))


        return
