__author__ = 'wzz'

import bisect
import operator

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

        def pretty_print(self):
            """
            Print prettily
            :return:
            """
            w_buf = 'Pretty Print:\n'
            number = len(self._vecX)
            for index in xrange(number):
                w_buf += '%.5f\t%-4d\t%-2d\n' % (self._vecX[index], self._vecID[index], self._vecType[index])

            print w_buf

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
                assert range_right < self._vecX[index] - self._resolution, \
                    'New item\'s right side (%f) overlaps with left side (%f) of ' \
                    'next item (%d).' % (range_right, self._vecX[index] - self._resolution,
                                         index)
                self._vecX.insert(index, range_left)
                self._vecID.insert(index, -1)
                self._vecType.insert(index, -1)
                index += 1
                self._vecX.insert(index, range_right)
                self._vecID.insert(index,  indicator_id)
                self._vecType.insert(index, item_type)

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

        def inside_peak_group_range(self, cursor_x):
            """ Check whether the cursor is inside any peak group's range
            :param cursor_x:
            :return:
            """
            # check
            assert isinstance(cursor_x, float)

            # locate index in vecX with bisection
            x_index = bisect.bisect_right(self._vecX, cursor_x)

            print '[DB] X = ', cursor_x, 'index = ', x_index, 'size of vector of x = ', len(self._vecX)

            # check inside/outside peak group range
            if x_index == 0 or x_index >= len(self._vecX):
                # outside limit of vecX
                return False

            if x_index % 2 == 1:
                # index is odd because it is within some cursor range
                print '[DB] It is ODD to be in an indicator\'s range.'
                raise RuntimeError('No operation to the situation to be ON another indicator.')

            # if the right side of x is the left boundary of a group, then it must be outside
            # of any peak range
            assert self._vecType[x_index] == -1, 'start of a new indicator. must be -1.'
            if self._vecType[x_index+1] == 0:
                return False

            return True

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

        self._boundaryRightEdge = -0.
        self._boundaryLeftEdge = -0.

        # indicator of the current selected peak (center)
        self._currPeakGroup = None
        self._currIndicatorID = -1
        self._currIndicatorType = -1

        # flag to reconstruct the peak list maps including ... and ...
        self._reconstructMaps = False
        min_data_resolution = 0.003  # For Vulcan
        self._cursorPositionMap = DiffractionPlotView.CursorPositionMap(min_data_resolution)

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
        print '[DB] About to add peak @ ', peak_center, 'to ....'
        self._cursorPositionMap.pretty_print()

        # create an instance of GroupedPeaksInfo
        left_x = self.get_indicator_position(left_id)[0]
        right_x = self.get_indicator_position(right_id)[0]
        grouped_peak = DiffractionPlotView.GroupedPeaksInfo(left_id, left_x, right_id, right_x)

        if peak_center is not None and center_id is not None:
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

        # print as debug
        self._cursorPositionMap.pretty_print()

        return

    def _get_peak_group(self, pos_x):
        """ Locate the in-pick peaks group
        :param pos_x:
        :return: 3-tuple.  peak group, indicator ID and indicator Type
        """
        # locate whether it is in within range of any indicator
        indicator_id, indicator_type = self._cursorPositionMap.get_information(pos_x)

        peak_group = None
        if indicator_id == 0:
            # left boundary. search inPickList by ID
            for p_grp in self._inPickPeakList:
                if p_grp.left_boundary_id == indicator_id:
                    peak_group = p_grp
                    break
        elif indicator_id == 2:
            # right boundary. search inPickList by ID
            for p_grp in self._inPickPeakList:
                if p_grp.right_boundary_id == indicator_id:
                    peak_group = p_grp
                    break
        else:
            # a peak or just within left and right boundary of a peak
            for p_grp in self._inPickPeakList:
                if p_grp.left_boundary <= pos_x <= p_grp.right_boundary:
                    peak_group = p_grp
        # END-IF-ELSE

        # rule out the case that peak group is not found if it is within indicator range
        if peak_group is None and indicator_id >= 0:
            raise RuntimeError('It is logically wrong that peak group is not found!')

        return peak_group, indicator_id, indicator_type

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

    def get_number_peaks_groups(self):
        """
        Get number of peak groups that are of in-pick mode on the canvas
        :return:
        """
        print '[DB] _inPickPeakList: ', self._inPickPeakList

        return len(self._inPickPeakList)

    def get_peaks_group(self, index):
        """ Get peak by the simple index from 0 to (num peaks - 1)
        Requirements: index is valid for list self._inPickPeakList
        Guarantees: peak-tuple is returned
        :param index:
        :return: peak group
        """
        assert isinstance(index, int), 'Peak index must be a integer but not %s.' % str(type(index))
        assert 0 <= index < len(self._inPickPeakList)

        peak_group = self._inPickPeakList[index]
        assert isinstance(peak_group, DiffractionPlotView.GroupedPeaksInfo)

        return peak_group

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
            # if self._cursorRestored is False:
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
            self._move_about_peak_group(event.xdata)

        elif len(self._inPickPeakList) > 0:
            # get position information for peak and boundary vicinity
            indicator_id, indicator_type = self._cursorPositionMap.get_information(event.xdata)
            print '[DB] ID = ', indicator_id, 'Type = ', indicator_type, 'Current ID and Type',
            print self._currIndicatorID, self._currIndicatorType

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
                new_cursor = QtCore.Qt.ArrowCursor
                QtGui.QApplication.setOverrideCursor(new_cursor)
                # QtGui.QApplication.restoreOverrideCursor()
            # END-IF-ELSE

            self._currIndicatorType = indicator_type

        # END-IF-ELSE

        # update mouse position
        self._mouseX = event.xdata
        self._mouseY = event.ydata

        return

    def _move_about_peak_group(self, new_x):
        """ Event handling while mouse's left button is pressed and moved
        Method is going to check the curse (i.e., the region that the mouse in)
        In this case, neither cursor's type nor selected peak can be changed
        :param new_x:
        :return:
        """
        if self._currIndicatorID < 0:
            # not within any indicator range.
            print '[DB] No indicator is selected. Nothing to move!'
            assert self._cursorType == 0, 'arrow cursor, between 2 peaks, no operation.'

        elif self._currIndicatorType == 0 or self._currIndicatorType == 2:
            # left boundary or right boundary
            # select a peak's boundary, then widen or narrow the peak's boundary
            print 'Move boundary to %f' % new_x
            assert self._cursorType == 2

            # calculate displacement
            if self._currIndicatorType == 0:
                delta_x_left = new_x - self._currPeakGroup.left_boundary
                delta_x_right = -delta_x_left
            else:
                delta_x_right = new_x - self._currPeakGroup.right_boundary
                delta_x_left = -delta_x_right

            # move the indicators for 2 boundary
            self.move_indicator(self._currPeakGroup.left_boundary, delta_x_left, 0.)
            self.move_indicator(self._currPeakGroup.right_boundary, delta_x_right, 0.)

            # update to peak group
            self._currPeakGroup.left_boundary += delta_x_left
            self._currPeakGroup.right_boundary += delta_x_right

            # update
            self._reconstructMaps = True

        elif self._currIndicatorType == 1:
            # select a peak's center, then move the peak
            assert self._cursorType == 1, 'Cursor type should be 1 as drag/move'

            # check whether the movement exceeds the boundary of the peak group
            if new_x <= self._currPeakGroup.left_boundary or new_x >= self._currPeakGroup.right_boundary:
                return False

            # move (peak) indicator
            delta_x = new_x - self.get_indicator_position(self._currIndicatorID)[0]
            self.move_indicator(self._currIndicatorID, delta_x)

            # update the peak group
            self._currPeakGroup.update_peak_position(self._currIndicatorID, new_x)

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

        # return if tool bar is in some process mode such as zoom
        if self._myToolBar.get_mode() != 0:
            return

        # if mode is 2, it means that the zoom button is pressed and shouldn't do anything at all!
        # print '[DB-BAT] Tool bar mode = ', self._myToolBar.get_mode()
        # print '[DB] Cursor shape: ', self._myCanvas.cursor().shape(), ' at ', event.xdata, event.ydata
        # NOTE: regular cursor = 0
        #       cross cursor   = 2
        #

        # find out the current group, whether it is in range of any indicator
        self._currPeakGroup, self._currIndicatorID, self._currIndicatorID = self._get_peak_group(event.xdata)

        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.NormalMode:
            # mode 0
            # no operation for any button
            # print '[DB-BAT] Peak selection-Normal Mode: No operation.'
            pass
        elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.QuickMode:
            # mode 1
            # operation
            if event.button == 1:
                # no operation left button
                pass
            elif event.button == 3:
                # right button
                self._respond_right_button(event.xdata)
        elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.MultiMode:
            # mode 2
            # multi-peak selection mode
            pass
        else:
            # unrecognized
            raise RuntimeError('Peak selection mode %s is not supported!' % str(self._myPeakSelectionMode))

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
        if self._mousePressed != 0:
            self._mousePressed = 0
        else:
            print '[DB] Mouse is not pressed but released.'

        # skip the zoom or whatever mode
        if self._myToolBar.get_mode() != 0:
            return

        # Check current cursor position. Return if it is out of canvas
        if event.xdata is None or event.ydata is None:
            return

        if event.button == 1:
            # left button
            if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.QuickMode:
                # quick mode: add peak and peak range
                self._add_range_peak(event.xdata, add_peak=True)

            elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.MultiMode:
                # multi-peak-indication mode:
                if self._cursorPositionMap.inside_peak_group_range(event.xdata):
                    # add peak if cursor is inside any peak group range
                    self._add_peak_to_group(event.xdata)
                else:
                    # add range if cursor is outside any peak group range
                    self._add_range_peak(event.xdata, add_peak=False)
                # END-IF-ELSE (inside/outside peak group range)
            # END-IF-ELSE (mode)
        # END-IF-ELSE (button)

        # reconstruct the query map
        if self._reconstructMaps is True:
            self._construct_peak_range_map()
            self._construct_vicinity_map()

        return

    def _add_range_peak(self, cursor_x, add_peak):
        """
        Add peak range and a peak as an option.
        Requirements:
        1. if the cursor is not within boundaries of any peak
        :param cursor_x:
        :param add_peak
        :return:
        """
        # check
        assert cursor_x is not None, 'X cannot be None, i.e., out of canvas'

        # take no operation if the cursor is within range of any peak
        if self._currIndicatorID >= 0:
            return

        if add_peak is True:
            # add a peak
            peak_id = self.add_vertical_indicator(cursor_x, 'red')
        else:
            # no peak to add
            peak_id = None

        # add peak(s)' range
        left_id = self.add_vertical_indicator(cursor_x - self._defaultPeakWidth, 'orange')
        right_id = self.add_vertical_indicator(cursor_x + self._defaultPeakWidth, 'blue')

        # add peaks' group
        self._add_peaks_group(cursor_x, peak_id, left_id, right_id)

        return

    def _add_peak_to_group(self, cursor_x):
        """
        Add a peak to an existing peak group if cursor_x is in the range
        :param cursor_x:
        :return:
        """
        # sort list
        self._inPickPeakList.sort(key=operator.attrgetter('left_boundary'))
        w_buf = ''
        for grp in self._inPickPeakList:
            w_buf += '%f < ' % grp.left_boundary
        print '[DB Is peak group ordered? ', w_buf

        # FIXME - this is a brute force search.  but easy to code
        # find out the peak group where it should be belonged to
        peak_added = False
        for index in xrange(len(self._inPickPeakList)):
            p_group = self._inPickPeakList[index]
            if p_group.left_boundary <= cursor_x <= p_group.right_boundary:
                # create a peak as an indicator and save the indicator (peak) ID
                peak_id = self.add_vertical_indicator(cursor_x, 'red')
                p_group.add_peak(peak_id, cursor_x)
                peak_added = True
                break
            # END-IF
        # END-FOR

        if peak_added is False:
            raise RuntimeError('Unable to add peak @ %f to any peak group!' % cursor_x)

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
        for peak_group in self._inPickPeakList:
            assert isinstance(peak_group, DiffractionPlotView.GroupedPeaksInfo)

            left_id = peak_group.left_boundary_id
            self.remove_indicator(left_id)
            right_id = peak_group.right_boundary_id
            self.remove_indicator(right_id)

            for peak_tuple in peak_group.get_peaks():
                peak_ind_id = peak_tuple[1]
                self.remove_indicator(peak_ind_id)

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
