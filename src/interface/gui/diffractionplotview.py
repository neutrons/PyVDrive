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
        MultiMode = 2

        def __init__(self):
            """ Init
            """
            return

    class GroupedPeaksInfo(object):
        """ Simple class to contain the information of peaks belonged to
        the same group.
        Peaks in the group will share the same range.
        """
        def __init__(self, left_boundary_id, left_x, right_boundary_id, right_x):
            """ Init
            """
            # check
            assert isinstance(left_boundary_id, int)
            assert isinstance(left_x, float)
            assert isinstance(right_boundary_id, int)
            assert isinstance(right_x, float)

            #
            self._leftID = left_boundary_id
            self._rightID = right_boundary_id

            self._leftX = left_x
            self._rightX = right_x

            self._peakIDPosList = list()  # a list of 2-tuple as peak position and indicator ID

            return

        @property
        def left_boundary(self):
            """
            """
            return self._leftX

        @left_boundary.setter
        def left_boundary(self, x):
            """
            """
            assert isinstance(x, float)
            self._leftX = x

            return

        @property
        def left_boundary_id(self):
            """ Indicator ID of the left boundary
            :return:
            """
            return self._leftID

        @property
        def right_boundary_id(self):
            """ Indicator ID of the right boundary
            :return:
            """
            return self._rightID

        @property
        def right_boundary(self):
            """
            """
            return self._rightX

        @right_boundary.setter
        def right_boundary(self, x):
            """
            """
            assert isinstance(x, float)
            assert x > self._leftX
            self._rightX = x
            return

        def add_peak(self, indicator_id, peak_pos):
            """
            Add a peak
            :param indicator_id:
            :param peak_pos:
            :return:
            """
            # check
            assert isinstance(indicator_id, int)
            assert isinstance(peak_pos, float)

            # add to peak list
            self._peakIDPosList.append((peak_pos, indicator_id))

            return

        def delete_peak(self, peak_id):
            """
            Delete a peak by its indicator ID
            :param peak_id:
            :return: boolean whether peak indicator is found and deleted
            """
            # check
            assert isinstance(peak_id, int)

            # remove
            found_peak = False
            for i_peak in xrange(len(self._peakIDPosList)):
                p_id = self._peakIDPosList[i_peak][1]
                if p_id == peak_id:
                    found_peak = True
                    self._peakIDPosList.pop(i_peak)
                    break

            return found_peak

        def get_peaks(self):
            """ Get all the peaks' tuple
            :return: a list of 2-tuples (peak position and peak ID)
            """
            self._peakIDPosList.sort()

            return self._peakIDPosList[:]

        def update_peak_position(self, peak_id, center_position):
            """ Update peak position
            :param peak_id:
            :param center_position:
            :return:
            """
            # check
            assert isinstance(peak_id, int)
            assert isinstance(center_position, float)

            found_peak = False
            for i_peak in xrange(len(self._peakIDPosList)):
                p_id = self._peakIDPosList[i_peak][1]
                if p_id == peak_id:
                    self._peakIDPosList[i_peak] = (center_position, peak_id)
                    found_peak = True
                    break
            # END-FOR

            return found_peak

    class CursorPositionMap(object):
        """
        A lookup table to map the cursor's position to its shape and peak or boundary that it is
        belonged to
        """
        def __init__(self, resolution=0.00001):
            """
            Initialization
            Note: range of boundary should be close to 2 twice of bin size
            :param resolution:
            :return:
            """
            # check
            assert isinstance(resolution, float)
            assert resolution > 0.

            # vector of X of region boundaries, x0, x1, x2, x3, where (x0, x1) is for group 1's left boundary
            self._vecX = list()
            # vector of peak/boundary' indicator IDs corresponding to vecX
            self._vecID = list()
            # vector of indicator types including left boundary (0), peak (1) and right boundary (2)
            self._vecType = list()

            self._resolution = resolution

            return

        def add_item(self, range_left, range_right, indicator_id, item_type):
            """
            Add an item
            :param range_left:
            :param range_right:
            :param indicator_id:
            :param item_type:
            :return:
            """
            # check
            assert isinstance(range_left, float)
            assert isinstance(range_right, float)
            assert range_left < range_right
            assert isinstance(indicator_id, int), 'Indicator ID %s must be an integer,' \
                                                  'but not %s.' % (str(indicator_id),
                                                                   str(type(indicator_id)))
            assert isinstance(item_type, int)
            assert 0 <= item_type <= 2, 'Indicator type %s must be 0, 1, or 2' % str(item_type)

            # find the spot to insert
            index = bisect.bisect_right(self._vecX, range_left)

            # determine whether to insert the left boundary
            if index == len(self._vecX):
                # appending mode
                self._vecX.extend([range_left, range_right])
                self._vecID.extend([-1, indicator_id])
                self._vecType.extend([-1, item_type])
            else:
                # insertion mode
                # insert left boundary information
                # check requirement of the left boundary and set the minimum distance to the right boundary of left item
                assert range_left > self._vecX[index] - self._resolution, 'Left boundary of region range is too left'
                range_left = max(range_left, self._vecX[index] + self._resolution)
                self._vecX.insert(index, range_left)
                self._vecID.insert(index, -1)
                self._vecType.insert(index, -1)
                index += 1
                # insert right boundary
                # check
                assert self._vecID[index] == 1, 'the right side must be a start of new region'

                # check requirement of the right boundary and set the maximum distance to the left boundary o
                # right item
                assert range_right < self._vecX[index] + self._resolution
                range_right = min(range_right, self._vecX[index] - self._resolution)

                # right boundary does not overlap with left boundary of next
                self._vecX.insert(index, range_right)
                self._vecID.insert(index, indicator_id)
                self._vecType.insert(index, item_type)
            # END-IF

            return

        def get_information(self, cursor_x):
            """ Get information, including indicator ID and indicator Type
            :param cursor_x: x position
            :return: 2-tuple as ID and type
            """
            # check
            assert isinstance(cursor_x, float)

            # locate index by bisect
            x_index = bisect.bisect_right(self._vecX, cursor_x)

            if x_index == 0 or x_index >= len(self._vecX):
                # out of boundary
                return -1, -1

            return self._vecID[x_index], self._vecType[x_index]

        def update_item_position(self, indicator_id, new_left_x, new_right_x):
            """
            Update the peak or boundary position
            :param indicator_id:
            :param new_left_x:
            :param new_right_x:
            :return: 2-tuple as (updated successful, error message).  0: over left boundary; 1: over right boundary
            """
            # check some status
            num_x = len(self._vecX)
            assert num_x == len(self._vecID)

            # locate position in list by indicator ID
            map_index = -1
            for index in xrange(num_x):
                if self._vecID == indicator_id:
                    map_index = index
                    break
            # END-FOR
            assert map_index >= 0, 'Indicator ID %d cannot be found' % indicator_id
            assert map_index > 0, 'It is logically wrong to find it at index 0.'
            if self._vecID[map_index-1] != -1:
                # shared boundary situation: it is not allowed!
                raise RuntimeError('It is not allowed to shared boundary of peak/group boundary')

            # update the right boundary position
            # check whether new region boundary is valid
            if map_index != num_x - 1 and new_right_x >= self._vecX[map_index+1] - self._resolution:
                # over the boundary of the right indicator
                return False, 1
            if map_index >= 2 and new_left_x < self._vecX[map_index-2] + self._resolution:
                # over the boundary of the left indicator
                return False, 2

            # update!
            self._vecX[map_index] = new_right_x
            self._vecX[map_index-1] = new_left_x

            return True, 0

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
        self._pickedPeakList = list()

        # default peak width
        self._defaultPeakWidth = 0.03

        # Interaction with the canvas
        self._myCanvas.mpl_connect('button_press_event', self.on_mouse_press_event)
        self._myCanvas.mpl_connect('button_release_event', self.on_mouse_release_event)
        self._myCanvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

        # mouse position
        self._mouseX = 0
        self._mouseY = 0
        self._mouseRelativeResolution = 0.005  # 0.5 percent of the image
        self._mousePressed = 0  # integer: 0 for no pressed, 1 for left button, 3 for right button

        # cursor type
        self._cursorType = 0
        self._cursorRestored = False

        #self._vecX = list()
        #self._vecPeakID = list()

        #self._vecPeakVicinityX = list()
        #self._vecBoundaryID = list()
        #self._vecPeakVicinityPID = list()

        self._boundaryRightEdge = -0.
        self._boundaryLeftEdge = -0.

        # indicator of the current selected peak (center)
        # self._currPeakIndicator = -1

        # flag to reconstruct the peak list maps including ... and ...
        self._reconstructMaps = False
        min_data_resolution = 0.003  # For Vulcan
        self._cursorPositionMap = DiffractionPlotView.CursorPositionMap(min_data_resolution)

        self._currIndicatorID = -1
        self._currIndicatorType = -1

        return

    def _add_peaks_group(self, peak_center, center_id, left_id, right_id):
        """
        Add grouped-peaks to current
        :param peak_center:
        :param center_id:
        :param left_id:
        :param right_id:
        :return:
        """
        # create an instance of GroupedPeaksInfo
        left_x = self.get_indicator_position(left_id)[0]
        right_x = self.get_indicator_position(right_id)[0]
        grouped_peak = DiffractionPlotView.GroupedPeaksInfo(left_id, left_x, right_id, right_x)

        if peak_center is not None:
            grouped_peak.add_peak(center_id, peak_center)

        # add to _inPickPeakList
        self._inPickPeakList.append(grouped_peak)

        # re-establish the look up table for peaks and grouped peak ranges
        self._construct_vicinity_map([-1])

        return

    def _close_to_canvas_edge(self, x, y):
        """ Check whether the cursor (x, y) is very close to the edge of the canvas
        :param x:
        :param y:
        :return:
        """
        assert isinstance(x, float), 'x is not a float but a %s.' % str(type(x))
        assert isinstance(y, float), 'y is not a float but a %s.' % str(type(y))

        xmin, xmax = self.getXLimit()
        if abs(x-xmin) <= 2*self._mouseRelativeResolution or abs(x-xmax) <= 2*self._mouseRelativeResolution:
            # close to left or right boundary
            return True

        ymin, ymax = self.getYLimit()
        if abs(y-ymin) <= 2*self._mouseRelativeResolution or abs(y-ymax) <= 2*self._mouseRelativeResolution:
            # close to top or bottom boundary
            return True

        return False

    def _construct_vicinity_map(self, new_group_index_list):
        """
        Create a set of mapping vectors to check whether the mouse cursor is in between 2 peaks,
        in the vicinity of a peaks boundary or in the vicinity of peak center.
        peak range for cursor
        :param new_group_index_list:
        :return:
        """
        # check
        assert self._cursorPositionMap is not None
        assert isinstance(new_group_index_list, list)

        # work
        for i_group in new_group_index_list:
            new_group = self._inPickPeakList[i_group]

            # left boundary of group
            left_bound_center = new_group.left_boundary
            left_bound_id = new_group.left_boundary_id
            left_range = 0.005  # FIXME - smart?
            self._cursorPositionMap.add_item(left_bound_center-left_range,
                                             left_bound_center+left_range,
                                             left_bound_id, 0)

            # peaks
            peak_info_list = new_group.get_peaks()
            for p_info in peak_info_list:
                peak_pos, peak_id = p_info
                peak_range = 0.005
                self._cursorPositionMap.add_item(peak_pos - peak_range,
                                                 peak_pos + peak_range,
                                                 peak_id, 1)
            # END-FOR

            # right boundary
            right_bound_center = new_group.right_boundary
            right_bound_id = new_group.right_boundary_id
            right_range = 0.005
            self._cursorPositionMap.add_item(right_bound_center - right_range,
                                             right_bound_center + right_range,
                                             right_bound_id, 2)
        # END-FOR

        return

    def _get_peak_tuple(self, center_id):
        """

        :param center_id:
        :return: peak_tuple (center position, center ID, left boundary ID, right boundary ID)
        """
        for peak_tup in self._inPickPeakList:
            if peak_tup[1] == center_id:
                return peak_tup

        for peak_tup in self._pickedPeakList:
            if peak_tup[1] == center_id:
                return peak_tup

        return None

    def add_peak(self, peak_pos, peak_width, in_pick):
        """ Add a peak's indicators (center, left and right boundaries)
        Requirements:
            Peak position must be given in current range
        Guarantees:
            A dashed line is drawn vertically across the figure as an indicator
        :param peak_pos:
        :param peak_width:
        :param in_pick:
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
        if in_pick is True:
            self._add_peaks_group(peak_center, peak_id, left_id, right_id)
        else:
            self._add_non_editable_peak(peak_center, peak_id, left_id, right_id)

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
        :return: 2-float tuple as (peak center, width)
        """
        assert isinstance(index, int), 'Peak index must be a integer but not %s.' % str(type(index))
        assert 0 <= index < len(self._inPickPeakList)

        peak_tuple = self._inPickPeakList[index]

        peak_center = peak_tuple[0]
        left_bound_x = self.get_indicator_position(peak_tuple[2])[0]

        return peak_center, abs(peak_center - left_bound_x)

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

    def on_mouse_motion(self, event):
        """
        :param event:
        :return:
        """
        # Check current cursor position. Return if it is out of canvas
        if event.xdata is None or event.ydata is None:
            # restore cursor if it is necessary
            if self._cursorRestored is False:
                self._cursorRestored = True
                QtGui.QApplication.restoreOverrideCursor()
                self._cursorType = 0
            return

        # Calculate current absolute resolution and determine whether the movement
        # is smaller than resolution
        x_min, x_max = self.getXLimit()
        resolution_x = (x_max - x_min) * self._mouseRelativeResolution
        y_min, y_max = self.getYLimit()
        resolution_y = (y_max - y_min) * self._mouseRelativeResolution

        abs_move_x = abs(event.xdata - self._mouseX)
        abs_move_y = abs(event.ydata - self._mouseY)
        if abs_move_x < resolution_x and abs_move_y < resolution_y:
            # movement is too small to require operation
            return

        # No operation if NOT in peak picking mode
        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.NormalMode:
            return

        # check zoom mode
        if self._myToolBar.get_mode() != 0 and self._inZoomMode is False:
            # just transit to the zoom mode
            self._inZoomMode = True
            # useless: self._myCanvas.setWindowTitle('Zoom mode! Unable to add peak!')

        elif self._myToolBar.get_mode() == 0 and self._inZoomMode is True:
            # just transit out of the zoom mode
            self._inZoomMode = False
            # self._myCanvas.setWindowTitle('Add peak!')

        else:
            pass
            # print 'No operation'

        # No operation in zooming mode
        if self._inZoomMode is True:
            # in zoom mode. no response is required
            return

        elif self._mousePressed == 1:
            # left mouse button is pressed and move
            print '[DB-BAT] Current peak index = ', self._currIndicatorID
            self._move_selected_peak(event.xdata)

        elif len(self._inPickPeakList) > 0:
            # get position information for peak and boundary vicinity
            indicator_id, indicator_type = self._cursorPositionMap.get_information(event.xdata)

            self._currIndicatorID = indicator_id

            if indicator_type == self._currIndicatorType:
                # no change
                pass

            elif indicator_type == 0 or indicator_type == 2:
                # left or right boundary
                new_cursor = QtCore.Qt.SplitHCursor
                QtGui.QApplication.setOverrideCursor(new_cursor)
                self._cursorType = 2

            elif indicator_type == 1:
                # peak
                self._cursorType = 1
                new_cursor = QtCore.Qt.DragMoveCursor
                QtGui.QApplication.setOverrideCursor(new_cursor)

            else:
                # in the middle of nowhere
                self._cursorType = 0
                QtGui.QApplication.restoreOverrideCursor()
            # END-IF-ELSE
        # END-IF-ELSE

        # update mouse position
        self._mouseX = event.xdata
        self._mouseY = event.ydata

        return

    def _move_selected_peak(self, new_x):
        """ Event handling while mouse's left button is pressed and moved
        Method is going to check the curse (i.e., the region that the mouse in)
        In this case, neither cursor's type nor selected peak can be changed
        :param new_x:
        :return:
        """
        # check whether current peak index is updated
        assert self._currPeakIndicator >= 0, 'Peak indicator\'s indicator %d cannot be negative.' \
                                         '' % self._currPeakIndicator

        # check the cursor type
        if self._cursorType == 0:
            # in between 2 peaks. no peak is selected. pointed arrow
            print 'arrow cursor, between 2 peaks, no operation.'
            pass

        elif self._cursorType == 1:
            # select a peak's center, then move the whole peak (center and boundary)
            peak_tuple = self._get_peak_tuple(center_id=self._currPeakIndicator)
            # peak_tuple = self._inPickPeakList[self._currPeakIndicator]
            peak_indicator_id = peak_tuple[1]
            left_indicator_id = peak_tuple[2]
            right_indicator_id = peak_tuple[3]

            # move
            d_x = new_x - self._mouseX
            new_center = peak_tuple[0] + d_x

            self.move_indicator(peak_indicator_id, d_x, 0)
            self.move_indicator(left_indicator_id, d_x, 0)
            self.move_indicator(right_indicator_id, d_x, 0)

            peak_tuple[0] = new_center
            # self._inPickPeakList[self._currPeakIndicator] =
            #   (new_center, peak_tuple[1], peak_tuple[2], peak_tuple[3])

            self._reconstructMaps = True

        elif self._cursorType == 2:
            # select a peak's boundary, then widen or narrow the peak's boundary
            peak_tuple = self._get_peak_tuple(self._currPeakIndicator)
            # peak_tuple = self._inPickPeakList[self._currPeakIndicator]
            peak_pos, peak_id, left_id, right_id = peak_tuple
            if self._boundaryRightEdge < peak_pos:
                # left boundary
                # prev_bound_x = self.get_indicator_position(left_id)[0]
                d_x = self._mouseX - new_x

            elif self._boundaryLeftEdge > peak_pos:
                # right boundary
                # prev_bound_x =
                d_x = new_x - self._mouseX
            else:
                err_msg = 'Left boundary  = %f, Right boundary = %f, Peak position = %f. ' \
                          'Situation of mouse cursor is not defined!' % (self._boundaryLeftEdge,
                                                                         self._boundaryRightEdge,
                                                                         peak_pos)
                raise RuntimeError(err_msg)

            # change the peak boundaries
            self.move_indicator(left_id, -d_x, 0)
            self.move_indicator(right_id, d_x, 0)

            self._reconstructMaps = True

        # END-IF-ELSE

        return

    def on_mouse_press_event(self, event):
        """

        :return:
        """
        # Update the mouse pressed up the status
        if event.button == 1:
            self._mousePressed = 1
        elif event.button == 3:
            self._mousePressed = 3

        # Check current cursor position. Return if it is out of canvas
        if event.xdata is None or event.ydata is None:
            return

        # Get data
        x = event.xdata
        # y = event.ydata
        button = event.button

        # if mode is 2, it means that the zoom button is pressed and shouldn't do anything at all!
        # print '[DB-BAT] Tool bar mode = ', self._myToolBar.get_mode()

        print '[DB] Cursor shape: ', self._myCanvas.cursor().shape(), ' at ', event.xdata, event.ydata
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
                pass
            elif button == 3:
                # right button
                self._respond_right_button(x)
        else:
            # unrecognized
            raise RuntimeError('Peak selection mode %s is not supported!' % str(self._myPeakSelectionMode))

        return

    def _respond_left_button(self, x):
        """
        Add peak if the cursor is not within boundaries of any peak
        :param x:
        :return:
        """
        # check
        assert x is not None, 'X cannot be None, i.e., out of canvas'

        # take no operation if the cursor is within range of any peak
        if self._currIndicatorID >= 0:
            return

        # add a peak
        peak_id = self.add_vertical_indicator(x, 'red')
        left_id = self.add_vertical_indicator(x - self._defaultPeakWidth, 'orange')
        right_id = self.add_vertical_indicator(x + self._defaultPeakWidth, 'blue')

        self._add_peaks_group(x, peak_id, left_id, right_id)

        return

    def _respond_right_button(self, x):
        """

        :param x:
        :return:
        """
        # FIXME/TODO/ Clean after development is finished
        """ Disabled due to no use!
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
        """

        return

    def on_mouse_release_event(self, event):
        """

        :param event:
        :return:
        """
        # set the mouse pressed status back
        self._mousePressed = 0

        # Check current cursor position. Return if it is out of canvas
        if event.xdata is None or event.ydata is None:
            return

        if event.button == 1:
            # left button
            self._respond_left_button(event.xdata)

        # reconstruct the query map
        if self._reconstructMaps is True:
            self._construct_peak_range_map()
            self._construct_vicinity_map()

        return

    def set_peak_selection_mode(self, single_mode, multi_mode):
        """
        Set peak-selection mode
        :param single_mode:
        :param multi_mode:
        :return:
        """
        # check
        assert not (single_mode and multi_mode), 'Ambiguous selection mode'

        if single_mode is True:
            self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.QuickMode
        elif multi_mode is True:
            self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.MultiMode
        else:
            self._myPeakSelectionMode = DiffractionPlotView.PeakAdditionMode.NormalMode

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
        self.add_arrow(0.5, 5000, )

        # Check requirements
        # assert len(self._vecX) > 1
        # assert self._vecX[0] <= left_x < right_x <= self._vecX[-1]

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

    def remove_all_in_pick_peaks(self):
        """ Remove all peaks' indicators
        :return:
        """
        # Remove all indicators
        for indicator_tup in self._inPickPeakList:
            indicator_key = indicator_tup[1]
            left_key = indicator_tup[2]
            right_key = indicator_tup[3]
            self.remove_indicator(indicator_key)
            self.remove_indicator(left_key)
            self.remove_indicator(right_key)

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
