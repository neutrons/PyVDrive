__author__ = 'wzz'

import bisect
import operator

from PyQt4 import QtGui, QtCore
import mplgraphicsview

import peaksmanager

# define constants
RESOLUTION = 0.005


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

        # Peaks-group manager
        self._myPeakGroupManager = peaksmanager.GroupedPeaksManager()

        # List of current peak groups in editing mode
        self._inEditGroupList = list()

        # default peak width
        self._defaultPeakWidth = 0.03

        # Interaction with the canvas
        self._myCanvas.mpl_connect('button_press_event', self.on_mouse_press_event)
        self._myCanvas.mpl_connect('button_release_event', self.on_mouse_release_event)
        self._myCanvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

        # mouse position
        self._mouseX = 0
        self._mouseY = 0
        self._mouseRelativeResolution = RESOLUTION  # 0.5% of the image

        self._mousePressed = 0  # integer: 0 for no pressed, 1 for left button, 3 for right button
        self._pressedX = 0      # position x as mouse is pressed
        self._pressedY = 0      # position y as mouse is pressed

        # cursor type
        self._cursorType = 0
        self._cursorRestored = False

        self._currIndicatorID = -1
        self._currIndicatorType = -1
        self._currGroupID = -1

        """
        self._boundaryRightEdge = -0.
        self._boundaryLeftEdge = -0.

        # flag to reconstruct the peak list maps including ... and ...
        min_data_resolution = 0.003  # For Vulcan
        """

        return

    def add_item(self, pos_x):
        """ Add item, which may be peak, peak group or peak group with 1 peak depending on the
        position X.
        :param pos_x:
        :return: boolean if successfully added
        """
        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.QuickMode:
            # quick mode: add peak and peak range
            # propose new peak group and peak's positions
            new_peak_center = pos_x
            new_left_bound = pos_x - self._defaultPeakWidth
            new_right_bound = pos_x + self._defaultPeakWidth

            # quit if it is not allowed to add a peak group
            if self._myPeakGroupManager.can_add_group(new_left_bound, new_right_bound) is False:
                return False

            # add a peak group
            grp_id = self.add_peak_group(new_left_bound, new_right_bound)
            assert grp_id is not None

            # add a peak
            self.add_peak(new_peak_center, grp_id)

        elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.MultiMode:
            # multi-peak-indication mode:
            group_id = self._myPeakGroupManager.get_group_id(pos_x)
            print '[DB] Group-ID = %d vs. current Group ID %s' % (group_id, self._currGroupID)

            if group_id < 0:
                # unable to add a peak, then possibly to add a group
                left_limit, right_limit = self._myPeakGroupManager.get_boundaries(pos_x, self.getXLimit())
                assert left_limit < pos_x < right_limit

                # left and right boundary
                left_boundary = max(pos_x - self._defaultPeakWidth, (left_limit + pos_x) * 0.5)
                right_boundary = min((pos_x + right_limit) * 0.5, pos_x + self._defaultPeakWidth)

                # add peak group
                grp_id = self.add_peak_group(left_boundary, right_boundary)

            else:
                # it is a proper place to add a peak
                self.add_peak(pos_x, group_id)

        else:
            # other mode without any operation
            pass

        return True

    def add_peak(self, peak_pos, group_id=None):
        """
        Add peak as edit mode.
        This is the only 'peak adding' method supported by diffractionplotview
        Requirements:
          - peak group must be aded to DiffractionPlotView before
        :param peak_pos:
        :param group_id:
        :return:
        """
        if group_id is None:
            group_id = self._myPeakGroupManager.get_group_id(peak_pos)
        else:
            assert isinstance(group_id, int)
        assert self._myPeakGroupManager.has_group(group_id)

        assert group_id is not None

        # add peak on canvas as its position is inside a group
        peak_id = self.add_vertical_indicator(peak_pos, color='red')

        self._myPeakGroupManager.add_peak(group_id, peak_pos, peak_id)

        return peak_id

    def add_peak_group(self, left_boundary, right_boundary):
        """
        Add grouped-peaks to current
        :param peak_center:
        :param center_id:
        :param left_id:
        :param right_id:
        :return:
        """
        # check whether it is able to add a peak group
        if self._myPeakGroupManager.can_add_group(left_boundary, right_boundary) is False:
            return None

        # add indicator on the canvas
        left_bound_id = self.add_vertical_indicator(left_boundary, 'blue', style='-', line_width=2)
        right_bound_id = self.add_vertical_indicator(right_boundary, 'green', style='-', line_width=2)

        # create a peak group
        new_group = peaksmanager.GroupedPeaksInfo(left_bound_id, left_boundary,
                                                  right_bound_id, right_boundary)
        new_grp_id = self._myPeakGroupManager.get_new_group_id()
        new_group.set_id(new_grp_id)
        new_group.set_edit_mode(True)

        # add group to group manager
        self._myPeakGroupManager.add_group(new_group)

        # add group to in-edit group list
        self._inEditGroupList.append(new_group)

        return new_grp_id

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

    def _get_peak_group(self, pos_x):
        """ Locate the in-pick peaks group
        :param pos_x:
        :return: 3-tuple.  peak group, indicator ID and indicator Type
        """
        # locate whether it is in within range of any indicator
        indicator_id, indicator_type = self._cursorPositionMap.get_information(pos_x)

        peak_group = None
        if indicator_type == 0:
            # left boundary. search inPickList by ID
            for p_grp in self._inEditGroupList:
                if p_grp.left_boundary_id == indicator_id:
                    peak_group = p_grp
                    break
        elif indicator_type == 2:
            # right boundary. search inPickList by ID
            for p_grp in self._inEditGroupList:
                if p_grp.right_boundary_id == indicator_id:
                    peak_group = p_grp
                    break
        else:
            # a peak or just within left and right boundary of a peak
            for p_grp in self._inEditGroupList:
                if p_grp.left_boundary <= pos_x <= p_grp.right_boundary:
                    peak_group = p_grp
        # END-IF-ELSE

        # rule out the case that peak group is not found if it is within indicator range
        if peak_group is None and indicator_id >= 0:

            err_msg = 'It is logically wrong that at X = %.5f, group is not found but ' % pos_x
            err_msg += 'its has a valid indicator ID %d and a valid indicator type %d.\n' % (
                indicator_id, indicator_type
            )
            err_msg += 'There are %d peaks group:\n' % len(self._inEditGroupList)
            for i_group in xrange(len(self._inEditGroupList)):
                err_msg += '%s\n' % str(self._inEditGroupList[i_group])
            raise RuntimeError(err_msg)

        return peak_group, indicator_id, indicator_type

    def _get_peak_tuple(self, center_id):
        """

        :param center_id:
        :return: peak_tuple (center position, center ID, left boundary ID, right boundary ID)
        """
        for peak_tup in self._inEditGroupList:
            if peak_tup[1] == center_id:
                return peak_tup

        for peak_tup in self._pickedPeakList:
            if peak_tup[1] == center_id:
                return peak_tup

        return None

    def plot_peak_indicator(self, peak_pos):
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

        # Add peak to data structure for mananging
        self._pickedPeakList.append(indicator_key)

        return


    def clear_peak_by_position(self, peak_pos):
        """
        Purpose: clear a peak by given its position
        :param peak_pos:
        :return:
        """
        # check
        assert isinstance(peak_pos, float) and peak_pos > 0

        # find peak with position
        self._myPeakGroupManager.get_peak_by_position(peak_pos)

        # remove
        self._myPeakGroupManager.delete_peak(group_id, peak_id)

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
        for i_peak in self._inEditGroupList:
            if self._inEditGroupList[1] == peak_id:
                remove_peak_index = i_peak
                break

        # check whether it is found
        assert remove_peak_index >= 0, 'Peak/indicator ID %d does not exist on canvas.' % peak_id

        # remove peak from inPickPeakList
        remove_peak_tuple = self._inEditGroupList.pop(remove_peak_index)

        # remove from canvas
        for indicator_index in xrange(1, 4):
            self.remove_peak_indicator(remove_peak_index[indicator_index])

        return

    def edit_group(self, group_id, status):
        """
        Enable or disable a group to be in edit mode according to the group ID
        :param group_id:
        :param status:
        :return:
        """
        # check
        assert isinstance(group_id, int)
        assert self._myPeakGroupManager.has_group(group_id), \
            'Peak group manager has no group with ID %d, candidates are %s.' % (
                group_id, self._myPeakGroupManager.get_group_ids())
        assert isinstance(status, bool)

        # enter/enable or leave/disable edit mode
        if status:
            # add all the indicators
            self._add_group_to_canvas(group_id)

        else:
            # remove all the indicators of this group
            self._remove_group_from_canvas(group_id)

        return

    def _add_group_to_canvas(self, group_id):
        """ (private)
        For an existing PeakGroup, plot all of its boundaries and peaks to the canvas
        and set the indicator ID to the peak group
        :param group_id:
        :return:
        """
        # get group
        pk_group = self._myPeakGroupManager.get_group(group_id)
        assert isinstance(pk_group, peaksmanager.GroupedPeaksInfo)

        # get all the indicators' position from peak group and add to canvas
        left_bound_id = self.add_vertical_indicator(x=pk_group.left_boundary, color='blue',
                                                    style='-', line_width=2)
        right_bound_id = self.add_vertical_indicator(x=pk_group.right_boundary, color='green',
                                                     style='-', line_width=2)
        peak_id_list = list()
        for peak_tup in pk_group.get_peaks():
            peak_pos = peak_tup[0]
            peak_id = self.add_vertical_indicator(x=peak_pos, color='red',
                                                  style='--', line_width=1)
            peak_id_list.append(peak_id)
        # END-FOR (peak_tup)

        # set to group
        self._myPeakGroupManager.group_enter_edit_mode(group_id, left_bound_id, right_bound_id, peak_id_list)

        return

    def _remove_group_from_canvas(self, group_id):
        """ (private)
        Remove all the indicators belonged to peaks group from canvas and thus the corresponding PeaksGroup
        :param group_id:
        :return:
        """
        # get the group
        pk_group = self._myPeakGroupManager.get_group(group_id)
        assert isinstance(pk_group, peaksmanager.GroupedPeaksInfo)

        # get all the indicator IDs from peak group and remove from canvas
        self.remove_indicator(pk_group.left_boundary_id)
        self.remove_indicator(pk_group.right_boundary_id)
        for peak_tup in pk_group.get_peaks():
            peak_id = peak_tup[1]
            print '[DB...BAT] Remove ID %d' % peak_id
            self.remove_indicator(peak_id)

        # remove the indicator IDs from PeaksGroup by setting to -1
        self._myPeakGroupManager.group_leave_edit_mode(group_id)

        return

    def get_number_peaks_groups(self):
        """
        Get number of peak groups that are of in-pick mode on the canvas
        :return:
        """
        return len(self._myPeakGroupManager.get_group_ids())

    def get_peaks_group(self, index):
        """ Get peak by the simple index from 0 to (num peaks - 1)
        Requirements: index is valid for list self._inPickPeakList
        Guarantees: peak-tuple is returned
        :param index:
        :return: peak group
        """
        # get group index
        group_id_list = self._myPeakGroupManager.get_group_ids()
        assert 0 <= index < len(group_id_list), 'Group sequence index %d is out of bound.' % index
        group_id = group_id_list[index]

        peak_group = self._myPeakGroupManager.get_group(group_id)

        """
        assert isinstance(index, int), 'Peak index must be a integer but not %s.' % str(type(index))
        assert 0 <= index < len(self._inEditGroupList)

        peak_group = self._myPeakGroupManager.get_group_id()

        peak_group = self._inEditGroupList[index]
        assert isinstance(peak_group, peaksmanager.GroupedPeaksInfo)
        """

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
        for peak_tup in self._inEditGroupList:
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
            # so move the peak, boundaries or group
            if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.QuickMode:
                # quick mode: move 2 boundaries or whole group
                self._move_peak_and_boundaries(event.xdata)

            elif self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.MultiMode:
                # multi-peak mode: move a boundary or a peak
                self._move_peak_group_multi_mode(event.xdata)

        elif len(self._inEditGroupList) > 0:
            # get position information for peak and boundary vicinity
            indicator_id, indicator_type, group_id = self._myPeakGroupManager.in_vicinity(event.xdata,
                                                                                          item_range=0.005)

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

            # update to class variables if it is not in hold mode
            self._currIndicatorID = indicator_id
            self._currIndicatorType = indicator_type
            self._currGroupID = group_id
        # END-IF-ELSE

        # update mouse position
        self._mouseX = event.xdata
        self._mouseY = event.ydata

        return

    def _move_peak_and_boundaries(self, new_x):
        """ Move peak and/or boundaries if
        Requirements:
        1. self._currGroupID is set up correctly!

        (1) mode is in single peak selection; AND
        (2) there is one and only 1 peak in the peak group
        :param new_x:
        :return:
        """
        if self._currIndicatorID < 0:
            # cursor is not in vicinity of any peak or boundary. return with out any operation
            return

        if self._myPeakGroupManager.has_group(self._currGroupID):
            # get current group
            curr_group = self._myPeakGroupManager.get_group(self._currGroupID)
            curr_group_id = curr_group.get_id()
        else:
            # does not exist. unsupported situation
            err_msg = 'Current peak group ID %s does not exist.  Cursor at X = %.5f, ID = %d, Type = %d' % (
                str(self._currGroupID),
                new_x, self._currIndicatorID, self._currIndicatorType)
            raise RuntimeError(err_msg)

        # absolute displacement
        delta_x = new_x - self._mouseX

        if self._currIndicatorType == 0 or self._currIndicatorType == 2:
            # cursor is in vicinity of either left boundary or right boundary
            # select a peak's boundary, then widen or narrow the peak's boundary
            assert self._cursorType == 2, 'Cursor type %d must be 2!' % self._cursorType

            # calculate displacement
            if self._currIndicatorType == 0:
                delta_x_left = delta_x
                delta_x_right = -delta_x_left
            else:
                delta_x_right = delta_x
                delta_x_left = -delta_x_right

            # check whether it is allowed to move left and move right
            left_bound_id = curr_group.left_boundary_id
            can_move_left = self._myPeakGroupManager.can_move_item(item_id=left_bound_id,
                                                                   delta_x=delta_x_left,
                                                                   limit=self.getXLimit())
            can_move_right = self._myPeakGroupManager.can_move_item(item_id=curr_group.right_boundary_id,
                                                                    delta_x=delta_x_right,
                                                                    limit=self.getXLimit())

            # move indicators if allowed
            if can_move_left and can_move_right:
                # allowed to move both boundaries, move the indicators on canvas
                self.move_indicator(curr_group.left_boundary_id, delta_x_left, 0.)
                self.move_indicator(curr_group.right_boundary_id, delta_x_right, 0.)

                # update the peak group manager
                self._myPeakGroupManager.move_left_boundary(group_id=curr_group_id,
                                                            displacement=delta_x_left,
                                                            check=False)
                self._myPeakGroupManager.move_right_boundary(group_id=curr_group_id,
                                                             displacement=delta_x_right,
                                                             check=False)
            else:
                # unable to move
                print '[DB...] group: ', curr_group.get_id(), 'can move left = ', can_move_left,
                print '; can move right = ', can_move_right
                print self._myPeakGroupManager.pretty()

        elif self._currIndicatorType == 1:
            # cursor is in the vicinity of a peak. so the peaks-group will be moved
            assert self._cursorType == 1, 'Cursor type (now %d) must be 2!' % self._cursorType
            assert curr_group.get_number_peaks() == 1, 'There must be one peak in the peaks group.'

            # check whether group can be moved and update the peaks-group information
            movable = self._myPeakGroupManager.move_group(group_id=curr_group_id,
                                                          displacement=delta_x,
                                                          limit_x=self.getXLimit(),
                                                          check=True)

            if movable:
                # move the indicators if it is allowed to move
                # get peak ID and move peak
                peak_id = curr_group.get_peaks()[0][1]
                self.move_indicator(peak_id, delta_x, 0.)

                # move the boundary
                self.move_indicator(curr_group.left_boundary_id, delta_x, 0.)
                self.move_indicator(curr_group.right_boundary_id, delta_x, 0.)
            else:
                print '[DB....Warning] Group %d cannot be moved.' % curr_group.get_id()

        else:
            # non-supported
            err_msg = 'Cursor type %d is not supported in peak group moving mode.' % self._currIndicatorType
            raise RuntimeError(err_msg)

        return

    def _move_peak_group_multi_mode(self, new_x):
        """ Event handling while mouse's left button is pressed and moved as it is in
        multi-peak selection mode.
        Method is going to check the curse (i.e., the region that the mouse in)
        In this case, neither cursor's type nor selected peak can be changed
        :param new_x:
        :return:
        """
        # check whether the cursor is on any
        if self._currIndicatorID < 0:
            # not within any indicator range.
            print '[DB] No indicator is selected. Nothing to move!'
            assert self._cursorType == 0, 'arrow cursor, between 2 peaks, no operation.'
            return

        # check status
        assert self._myPeakGroupManager.has_group(self._currGroupID), \
            'Current peak group (ID: %s) does not exist.' % str(self._currGroupID)
        curr_group = self._myPeakGroupManager.get_group(self._currGroupID)
        # calculate displacement: current mouse position to previous mouse position
        delta_x = new_x - self._mouseX

        if self._currIndicatorType == 0 or self._currIndicatorType == 2:
            # left boundary or right boundary
            # select a peak's boundary, then move that
            # check
            assert self._cursorType == 2, 'Cursor type %d must be 2!' % self._cursorType

            print '[DB] Move (left/right %d) boundary from %f to %f' % (self._currIndicatorType,
                                                                        self._mouseX, new_x),
            print 'Left boundary ID = %d, Right boundary ID = %d' % (
                curr_group.left_boundary_id, curr_group.right_boundary_id)

            move_left_boundary = False
            if self._currIndicatorType == 0:
                # move left boundary
                # delta_x = new_x - curr_group.left_boundary
                move_left_boundary = True
            else:
                # move right boundary
                # delta_x = new_x - curr_group.right_boundary
                pass

            # check whether move is allowed
            movable = self._myPeakGroupManager.can_move_item(curr_group.left_boundary_id, delta_x,
                                                             self.getXLimit())

            if movable and move_left_boundary:
                # move left boundary of the group
                # move indicator on canvas
                self.move_indicator(curr_group.left_boundary_id, delta_x, 0.)
                # update peak group manager
                self._myPeakGroupManager.move_left_boundary(self._currGroupID, delta_x, False)
            elif movable and not move_left_boundary:
                # move right boundary of the group
                # move indicator on canvas
                self.move_indicator(curr_group.right_boundary_id, delta_x, 0.)
                # update peak group manager
                self._myPeakGroupManager.move_right_boundary(self._currGroupID, delta_x, False)
            else:
                print '[DB...] Boundary (left=%s) cannot be moved.' % str(movable)

        elif self._currIndicatorType == 1:
            # select a peak's center, then move the peak
            assert self._cursorType == 1, 'Cursor type should be 1 as drag/move'

            # check whether the peak can be moved by specified displacement
            peak_movable = self._myPeakGroupManager.can_move_item(self._currIndicatorID, delta_x,
                                                                  self.getXLimit())

            if peak_movable:
                # move the peak
                # move the peak's indicator on canvas
                self.move_indicator(self._currIndicatorID, delta_x, 0.)

                # update the peak group manager
                self._myPeakGroupManager.move_peak(group_id=self._currGroupID, peak_id=self._currIndicatorID,
                                                   delta_x=delta_x, check=False, limit=self.getXLimit())

            else:
                print '[DB...] Peak (indicator %d in group %d) cannot moved by %f.' % (self._currIndicatorID,
                                                                                       self._currGroupID,
                                                                                       delta_x)

        else:
            # unsupported case
            err_msg = 'Cursor type %d is not supported.' % self._currIndicatorType
            raise RuntimeError(err_msg)
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

        self._pressedX = event.xdata
        self._pressedY = event.ydata

        # Check current cursor position. Return if it is out of canvas
        if self._pressedX is None or self._pressedY is None:
            return

        # return if tool bar is in some process mode such as zoom
        if self._myToolBar.get_mode() != 0:
            return

        # get vicinity/cursor map information

        # record current selected group
        info_tup = self._myPeakGroupManager.in_vicinity(event.xdata, item_range=0.005)
        self._currIndicatorID = info_tup[0]
        self._currIndicatorType = info_tup[1]
        self._currGroupID = info_tup[2]

        # respond according to mouse button pressed
        if event.button == 1:
            # no operation for left button pressed
            pass
        elif event.button == 3:
            self._pop_menu(event)

        return

    def _pop_menu(self, event):
        """
        Pop up the menu to (mostly) to remove the peak or peak group
        :param event:
        :return:
        """
        # no operation required for the non-edit mode
        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.NormalMode:
            return

        # no operation if event is outside of canvas
        if event.xdata is None or event.ydata is None:
            return

        # create a menu in the edit mode
        self.menu = QtGui.QMenu(self)

        self._eventX = event.xdata

        # optionally add option to delete peak
        if self._myPeakSelectionMode == DiffractionPlotView.PeakAdditionMode.MultiMode:
            action2 = QtGui.QAction('Delete Peak', self)
            action2.triggered.connect(self.menu_delete_peak_in_pick)
            self.menu.addAction(action2)

        # add item to delete peak group
        action1 = QtGui.QAction('Delete Group', self)
        action1.triggered.connect(self.menu_delete_group_in_pick)
        self.menu.addAction(action1)

        action3 = QtGui.QAction('Show Info', self)
        action3.triggered.connect(self.menu_show_info)
        self.menu.addAction(action3)

        # add other required actions
        self.menu.popup(QtGui.QCursor.pos())

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
            # add an item if and only if the mouse is not moved
            min_x, max_x = self.getXLimit()
            if abs(self._pressedX - event.xdata) < 0.5 * (max_x - min_x) * self._mouseRelativeResolution:
                self.add_item(event.xdata)

        elif event.button == 3:
            # right button: do nothing
            pass
        # END-IF-ELSE (button)

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
        self.add_peak_group(cursor_x, peak_id, left_id, right_id)

        return

    def _add_peak_to_group(self, cursor_x):
        """
        Add a peak to an existing peak group if cursor_x is in the range
        :param cursor_x:
        :return:
        """
        # sort list
        self._inEditGroupList.sort(key=operator.attrgetter('left_boundary'))
        w_buf = ''
        for grp in self._inEditGroupList:
            w_buf += '%f < ' % grp.left_boundary
        print '[DB-Check] Is peak group ordered? ', w_buf

        # FIXME - this is a brute force search.  but easy to code
        # find out the peak group where it should be belonged to
        peak_added = False
        for index in xrange(len(self._inEditGroupList)):
            p_group = self._inEditGroupList[index]
            if p_group.left_boundary <= cursor_x <= p_group.right_boundary:
                # check whether it is OK to add
                left_in_vicinity = self._cursorPositionMap.in_vicinity(cursor_x - RESOLUTION)
                right_in_vicinity = self._cursorPositionMap.in_vicinity(cursor_x + RESOLUTION)
                allow_to_add = not left_in_vicinity and not right_in_vicinity
                if allow_to_add is False:
                    raise RuntimeError('Unable to add new peak due to its range overlaps other peak/boundary'
                                       'in this peak group.')
                # create a peak as an indicator and save the indicator (peak) ID
                peak_id = self.add_vertical_indicator(cursor_x, 'red')
                # update to cursor map
                self._cursorPositionMap.add_item(cursor_x - RESOLUTION, cursor_x + RESOLUTION,
                                                 peak_id, 1)
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
        assert 0 <= indicator_index < len(self._inEditGroupList), \
            'Indicator index %d is out of index range [0, %d).' % (indicator_index, len(self._inEditGroupList))

        # Get indicator key
        indicator_key = self._inEditGroupList[indicator_index][1]

        # Re-plot
        self.highlight_indictor(indicator_key)

        return

    def menu_delete_group_in_pick(self):
        """ Delete the peak group (in-pick mode) where the cursor is
        :return:
        """
        # check
        assert self._eventX is not None

        # find out the current position
        curr_group_id = self._currGroupID

        print '[DB....Delete Group] About to delete group %d.' % curr_group_id

        # delete group on canvas
        removed = self.remove_group(curr_group_id)
        assert removed

        # delete group from peak group manager
        removed = self._myPeakGroupManager.delete_group(curr_group_id)
        assert removed, 'Unable to delete group %d from group manager.' % curr_group_id

        print '[DB....Result]\n', self._myPeakGroupManager.pretty()

        return

    def menu_delete_peak_in_pick(self):
        """
        Delete a peak from canvas
        :return:
        """
        # check
        assert self._eventX is not None

        # find out the current position
        curr_group_id = self._currGroupID
        curr_item_id = self._currIndicatorID
        curr_item_type = self._currIndicatorType

        print '[DB....Delete Peak] About to delete group %d peak %d type %d==2.' % (curr_group_id,
                                                                                    curr_item_id,
                                                                                    curr_item_type)
        assert curr_item_type == 1, \
            'Current item type must be equal 1 for peak but not %d.' % curr_item_type


        # delete peak on canvas
        removed = self.remove_peak_indicator(curr_item_id)
        assert removed

        # delete peak from peak group manager
        removed = self._myPeakGroupManager.delete_peak(curr_group_id, curr_item_id)

        return

    def menu_show_info(self):
        """

        :return:
        """
        item_id, item_type, group_id = self._myPeakGroupManager.in_vicinity(self._eventX, 0.005)
        print '[DB] Current Item = %d of type %d in Group %d.' % (item_id, item_type, group_id)

        return

    def plot_diffraction_pattern(self, vec_x, vec_y, key=None):
        """
        Plot a diffraction pattern on canvas
        :param vec_x: 1d array or list for X
        :param vec_y: 1d array or list for Y
        :return:
        """
        # check
        assert len(vec_x) == len(vec_y), 'vector of x and y have different size!'

        # Plot
        pattern_key = self.add_plot_1d(vec_x, vec_y, color='black', marker='.')

        # Record the data for future usage
        if key is not None:
            self._myPatternDict[key] = (vec_x, vec_y, pattern_key)

        return

    def remove_all_in_pick_peaks(self):
        """ Remove all peaks' indicators
        :return:
        """
        # Remove all indicators
        for peak_group in self._inEditGroupList:
            assert isinstance(peak_group, DiffractionPlotView.GroupedPeaksInfo)

            left_id = peak_group.left_boundary_id
            self.remove_indicator(left_id)
            right_id = peak_group.right_boundary_id
            self.remove_indicator(right_id)

            for peak_tuple in peak_group.get_peaks():
                peak_ind_id = peak_tuple[1]
                self.remove_indicator(peak_ind_id)

        # Clear the indicator position-key list
        self._inEditGroupList = list()

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
        # check
        assert isinstance(peak_indicator_index, int)

        # find and remove indicator from peak group manager
        removable = self._myPeakGroupManager.delete_peak(peak_indicator_index)

        # remove indicator on the canvas
        if removable:
            self.remove_indicator(peak_indicator_index)

        return True

    def remove_picked_peaks_indicators(self):
        """ Removed all the being-picked peaks' indicators stored in _pickedPeaksList
        :return:
        """
        # remove indicators from canvas
        for peak_indicator_id in self._pickedPeakList:
            self.remove_indicator(peak_indicator_id)

        # clear the inPickPeakList
        self._inEditGroupList = list()

        return

    def reset(self):
        """ Reset the canvas and peaks managers
        :return:
        """
        self.clear_all_lines()
        self._myPeakGroupManager.reset()

        return

    def sort_n_add_peaks(self, peak_info_list, edit_mode=True, plot=True):
        """ Sort and add peaks to edit mode
        Requirements:
         1. peak info list: list of peak information tuple (centre, height, width, HKL)
        Guarantees:
         1. peaks will be sorted and grouped by considering overlapping range
        :param peak_info_list:
        :param plot:
        :return:
        """
        # check requirements

        # order the peaks in reverse order

        # create list of peak index with peak boundary

        # merge the peaks with overlapped boundaries

        # add peak groups and peak

        # plot

        return

