import bisect
import numpy
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5.QtWidgets import QApplication, QMenu, QAction, QMainWindow
    from PyQt5 import QtCore
    from PyQt5.QtGui import QCursor
except ImportError:
    from PyQt4.QtGui import QApplication, QMenu, QAction, QCursor, QMainWindow
    from PyQt4 import QtCore

from pyvdrive.interface.gui import mplgraphicsview
from pyvdrive.interface.gui import peaksmanager
from pyvdrive.core import datatypeutility

__author__ = 'wzz'

# define constants
RESOLUTION = 0.005


class FunctionMode(object):
    """ Function mode of the diffraction view
    """
    PeakSelectionMode = 0
    VanadiumProcessingMode = 1

    @staticmethod
    def is_valid_mode(mode):
        """
        Check whether a mode is value
        :param mode:
        :return:
        """
        return 0 <= mode <= 1


class PeakAdditionState(object):
    """ Enumerate for peak adding mode
    """
    NonEdit = -1
    NormalMode = 0
    QuickMode = 1
    MultiMode = 2
    AutoMode = 3  # this is single peak add mode

    @staticmethod
    def is_valid_mode(mode):
        """
        Check whether a mode is value
        :param mode:
        :return:
        """
        return -1 <= mode <= 3


class DiffractionPlotView(mplgraphicsview.MplGraphicsView):
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
        # Base class constructor
        mplgraphicsview.MplGraphicsView.__init__(self, parent)

        # parent
        self._parentWindow = None

        # Mode: default to peak selection
        self._functionMode = FunctionMode.PeakSelectionMode

        # Bragg diffraction pattern
        self._lastPlotID = None  # plot ID for the diffraction pattern plotted last
        self._highlightsPlotIDList = list()

        # Define the class variable
        # Peak selection mode: not-in-edit
        self._myPeakSelectionMode = PeakAdditionState.NonEdit
        # Canvas moving mode
        self._inZoomMode = False
        # peak process status

        # Peaks-group manager
        self._myPeakGroupManager = peaksmanager.GroupedPeaksManager()
        # single peaks collection used in auto-peak-finding mode
        self._mySinglePeakDict = dict()
        # peak information dictionary. value is a 2-tuple including its color and group ID
        self._myPeakInfoDict = dict()

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

        self._mouseButtonBeingPressed = 0  # integer: 0 for no pressed, 1 for left button, 3 for right button
        self._pressedX = 0      # position x as mouse is pressed
        self._pressedY = 0      # position y as mouse is pressed

        # cursor type
        self._cursorType = 0
        self._cursorRestored = False

        self._currIndicatorID = -1
        self._currIndicatorType = -1
        self._currGroupID = -1

        # automatic peak selection
        self._addedLeftBoundary = True  # flag to add a single boundary line as the left boundary

        # peak indicator management
        self._highlightPeakID = -1  # Peak ID (indicator ID) of the current highlighted peak by mouse moving
        self._shownPeakIDList = list()  # list of indicator IDs for peaks show on canvas

        # menu
        self._menu = None

    def add_item(self, pos_x):
        """ Add item, which may be peak, peak group or peak group with 1 peak depending on the
        position X.
        :param pos_x:
        :return: boolean if successfully added
        """
        if self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            # auto (quick) pick up mode. just add the peak without the peak boundary
            self.add_single_peak(peak_pos=pos_x)

        elif self._myPeakSelectionMode == PeakAdditionState.NormalMode:
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

        elif self._myPeakSelectionMode == PeakAdditionState.MultiMode:
            # multi-peak-indication mode:
            group_id = self._myPeakGroupManager.get_group_id(pos_x)

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

    def add_vanadium_peaks(self, peak_pos_list):
        """ Add vanadium peaks indicators
        :param peak_pos_list:
        :return:
        """
        datatypeutility.check_list('Peak positions', peak_pos_list)
        peak_pos_list = sorted(peak_pos_list)

        indicator_id_list = list()
        for peak_pos in peak_pos_list:
            peak_indicator_id = self.add_vertical_indicator(peak_pos, color='red')
            indicator_id_list.append(peak_indicator_id)

        return indicator_id_list

    def add_peak_group(self, left_boundary, right_boundary):
        """
        add a peak group with left and right boundary
        :param left_boundary:
        :param right_boundary:
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

    def add_single_peak(self, peak_pos):
        """
        Add a single peak without group
        :param peak_pos:
        :return:
        """
        # check
        assert isinstance(peak_pos, float), 'peak position %s must be a float number but not %s.' \
                                            '' % (str(peak_pos), type(peak_pos))

        # add peak
        peak_id = self.add_vertical_indicator(peak_pos, color='blue')

        # record
        self._mySinglePeakDict[peak_id] = peak_pos

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
            for i_group in range(len(self._inEditGroupList)):
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

        for peak_tup in self._shownPeakIDList:
            if peak_tup[1] == center_id:
                return peak_tup

        return None

    def clear_highlight_data(self):
        """
        Clear the highlighted data
        :return:
        """
        # remove lines from canvas
        for hl_line_id in self._highlightsPlotIDList:
            self.remove_line(hl_line_id)

        self._highlightsPlotIDList = list()

        return

    # NOTE: Removed because it is not used
    # def clear_peak_by_id(self, peak_id):
    #     """
    #     Remove peak-tuple from the current in-pick-up peaks
    #     Requirement: peak ID is a valid integer
    #     Guarantees: the indicators for peak, left boundary and right boundary are removed from canvas.
    #                 the peak tuple is removed from self._inPickList
    #     :param peak_id: integer
    #     :return: None
    #     """
    #     # check
    #     assert isinstance(peak_id, int), 'Input peak/indicator ID must be an integer but not %s.' \
    #                                      '' % str(type(peak_id))
    #
    #     # find peak tuple
    #     remove_peak_index = -1
    #     for i_peak in self._inEditGroupList:
    #         if self._inEditGroupList[1] == peak_id:
    #             remove_peak_index = i_peak
    #             break
    #
    #     # check whether it is found
    #     assert remove_peak_index >= 0, 'Peak/indicator ID %d does not exist on canvas.' % peak_id
    #
    #     # remove peak from inPickPeakList
    #     remove_peak_tuple = self._inEditGroupList.pop(remove_peak_index)
    #     print '[INFO] Peak {0} is removed.'.format(remove_peak_tuple)
    #
    #     # remove from canvas
    #     for indicator_index in xrange(1, 4):
    #         self.remove_peak_indicator(remove_peak_index[indicator_index])
    #
    #     return

    def adjust_indiators(self, indicator_list, x_range=None, y_range=None):

        # TODO - TONIGHT 1 - Code quality

        if y_range:
            lower_y, upper_y = y_range
            new_vec_y = numpy.array([lower_y, upper_y])
        else:
            new_vec_y = None

        for indicator_id in indicator_list:
            self.update_indicator(indicator_id, y_range=new_vec_y)

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
        # FIXME/TODO/NOW - Need a better way to manage group/group-ID
        if status:
            # add all the indicators
            self._add_group_to_canvas(group_id)

        else:
            # remove all the indicators of this group
            self._remove_group_from_canvas(group_id)
            # self._inEditGroupList.remove(group_id) : items are group but not group ID

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

        # This is a brute force searching algorithm.  It won't be efficient if there are many peaks
        # But as the number of peaks won't exceed 100s, there is no urgent need to improve the performance
        for peak_tup in self._inEditGroupList:
            if peak_tup[1] == indicator_id:
                return peak_tup

        return None

    def get_ungrouped_peaks(self):
        """
        Get ungrouped peaks that are selected automatically
        :return: a sorted list of tuples. each tuple contains peak position and peak ID
        """
        tuple_list = list()
        for peak_id in self._mySinglePeakDict.keys():
            peak_pos = self._mySinglePeakDict[peak_id]
            tuple_list.append((peak_pos, peak_id))

        return tuple_list

    def highlight_data(self, left_x, right_x, color):
        """
        Requirements:
            Left_x and right_x are within data range;
            Data is loaded on canvas
        Guarantees:
            Diffraction pattern between left_x and right_x is plot with different color
        :param left_x:
        :param right_x:
        :param color:
        :return:
        """
        # issue 44... check inputs

        #
        vec_x, vec_y = self.canvas().get_data(self._lastPlotID)

        left_index = bisect.bisect_right(vec_x, left_x)
        right_index = bisect.bisect_right(vec_x, right_x)
        # if right_index == len(vec_x):
        #     right_index -= 1

        line_id = self.add_plot_1d(vec_x[left_index:right_index], vec_y[left_index:right_index], color=color,
                                   marker=None, line_width=2)

        self._highlightsPlotIDList.append(line_id)

        return

    def highlight_peak_nearby(self, curr_position):
        """
        check mouse cursor is near enough to a selected peak. if it is then highlight that peak.
        if there is not any, then de-highlight all
        :param curr_position:
        :return:
        """
        # check
        assert isinstance(curr_position, float), 'mouse cursor position must be a float number but not ' \
                                                 'of type %s' % curr_position.__class__.__name__

        # return if there is no peak
        if len(self._mySinglePeakDict) == 0:
            return

        # sort the peaks with position
        peak_tup_list = list()
        if self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            # automatic mode: collect the peaks from peak tuple list
            for peak_id in self._mySinglePeakDict.keys():
                peak_pos = self._mySinglePeakDict[peak_id]
                peak_tup_list.append((peak_pos, peak_id))
            # END-FOR
            peak_tup_list.sort()

        else:
            # power mode. collect the peak from peak group list
            # FIXME/NOW/ISSUE 45 or late: need a better data structure for it
            g_id_list = self._myPeakGroupManager.get_group_ids()
            for g_id in g_id_list:
                # group = self._myPeakGroupManager.get_group(g_id)
                raise NotImplementedError('ASAP for get_group()')
        # END-IF

        # find the nearby peak
        index = bisect.bisect_left(peak_tup_list, (curr_position, -1))
        index = max(0, index)

        # use the dynamic resolution
        resolution = curr_position * 0.01
        peak_id = -1
        if index == 0:
            # left to the left most peak. it must be the left most peak or not any peak
            peak0_pos = peak_tup_list[index][0]
            if abs(curr_position - peak0_pos) <= resolution:
                peak_id = peak_tup_list[index][1]
        elif index == len(peak_tup_list):
            # right to the rightmost peak. it must be the right most peak or not amy peak
            peak_right_pos = peak_tup_list[index-1][0]
            if abs(curr_position - peak_right_pos) <= resolution:
                peak_id = peak_tup_list[index-1][1]
        else:
            # in the middle
            peak_left_pos = peak_tup_list[index-1][0]
            peak_right_pos = peak_tup_list[index][0]

            if abs(peak_right_pos - curr_position) <= resolution:
                peak_id = peak_tup_list[index][1]
            elif abs(peak_left_pos - curr_position) <= resolution:
                peak_id = peak_tup_list[index-1][1]

        # END-IF

        # highlight or de-highlight the peak indicator by updating its color
        # if the mouse is moving around a peak, then highlight it red
        # if the mouse is moving far from a peak, which is previously highlighted, then color it to blue
        if peak_id == self._highlightPeakID:
            # no change
            pass

        elif peak_id == -1:
            # move away from a peak: clean the original line
            # note: self._highlightPeakID >= 0 must be TRUE according to case 1
            self.update_indicator(self._highlightPeakID, 'blue')
            self._highlightPeakID = -1

        else:
            # move around a peak
            self.update_indicator(peak_id, 'red')
            # de-highlight the previously highlighted peak
            if self._highlightPeakID >= 0:
                self.update_indicator(self._highlightPeakID, 'blue')
            self._highlightPeakID = peak_id
        # END-IF-ELSE

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

    def on_mouse_motion(self, event):
        """
        No operation under any of these situations
        1. in zoom mode
        2. in non-editing (non-peak-selection) mode
        3. mouse cursor is out of canvas
        4. movement from 'last position' is too small
        :param event:
        :return:
        """
        # No operation if NOT in peak picking mode
        if self._myPeakSelectionMode == PeakAdditionState.NonEdit:
            return

        # Check current cursor position. Return if it is out of canvas
        if event.xdata is None or event.ydata is None:
            # restore cursor if it is necessary
            # if self._cursorRestored is False:
            self._cursorRestored = True
            QApplication.restoreOverrideCursor()
            self._cursorType = 0
            return

        # check zoom mode
        if self._myToolBar.get_mode() != 0 and self._inZoomMode is False:
            # just transit to the zoom mode and then
            self._inZoomMode = True
            self.setWindowTitle('Zoom mode! Unable to add peak!')
            # useless: self._myCanvas.setWindowTitle('Zoom mode! Unable to add peak!')

        elif self._myToolBar.get_mode() == 0 and self._inZoomMode is True:
            # just transit out of the zoom mode
            self._inZoomMode = False
            # self._myCanvas.setWindowTitle('Add peak!')

        if self._inZoomMode is True:
            # in zoom mode. no response is required
            return

        # Calculate current absolute resolution and determine whether the movement
        #   is smaller than resolution
        x_min, x_max = self.getXLimit()
        resolution_x = (x_max - x_min) * self._mouseRelativeResolution
        y_min, y_max = self.getYLimit()
        resolution_y = (y_max - y_min) * self._mouseRelativeResolution

        abs_move_x = abs(event.xdata - self._mouseX)
        abs_move_y = abs(event.ydata - self._mouseY)
        if abs_move_x < resolution_x and abs_move_y < resolution_y:
            # movement is too small to require operation
            return

        # Now it is the time to process
        if self._mouseButtonBeingPressed == 0:
            # mouse button is not pressed.
            self.highlight_peak_nearby(event.xdata)

        elif self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            # auto peak selection mode does not support any peak moving so far
            pass

        elif self._mouseButtonBeingPressed == 1:
            # left mouse button is pressed and move
            # so move the peak, boundaries or group
            if self._myPeakSelectionMode == PeakAdditionState.QuickMode:
                # quick mode: move 2 boundaries or whole group
                self._move_peak_and_boundaries(event.xdata)

            elif self._myPeakSelectionMode == PeakAdditionState.MultiMode:
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
                QApplication.setOverrideCursor(new_cursor)
                self._cursorType = 2

            elif indicator_type == 1:
                # peak
                self._cursorType = 1
                new_cursor = QtCore.Qt.DragMoveCursor
                QApplication.setOverrideCursor(new_cursor)

            else:
                # in the middle of nowhere
                self._cursorType = 0
                new_cursor = QtCore.Qt.ArrowCursor
                QApplication.setOverrideCursor(new_cursor)
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
                print('[DB...] group: ', curr_group.get_id(), 'can move left = ', can_move_left,)
                print('; can move right = ', can_move_right)
                print(self._myPeakGroupManager.pretty())

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
                print('[DB....Warning] Group %d cannot be moved.' % curr_group.get_id())

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
            print('[DB] No indicator is selected. Nothing to move!')
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

            print('[DB] Move (left/right %d) boundary from %f to %f' % (self._currIndicatorType,
                                                                        self._mouseX, new_x),)
            print('Left boundary ID = %d, Right boundary ID = %d' % (curr_group.left_boundary_id,
                                                                     curr_group.right_boundary_id))

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
                print('[DB...] Boundary (left=%s) cannot be moved.' % str(movable))

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
                print('[DB...] Peak (indicator %d in group %d) cannot moved by %f.' % (self._currIndicatorID,
                                                                                       self._currGroupID,
                                                                                       delta_x))

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
            self._mouseButtonBeingPressed = 1
        elif event.button == 3:
            self._mouseButtonBeingPressed = 3

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
        # as menu is popped out, the mouse state on the canvas must be reset to 0
        self._mouseButtonBeingPressed = 0

        # no operation if event is outside of canvas
        if event.xdata is None or event.ydata is None:
            return
        else:
            # set up the eventX for the menu actions, which won't have access to event.xdata
            self._eventX = event.xdata

        # no operation required for the non-edit mode
        if self._myPeakSelectionMode == PeakAdditionState.NonEdit:
            # no action on non-edit mode
            pass

        elif self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            # automatic mode to support actions including delete, add boundaries, undo boundaries
            #  and reset group
            self._menu = QMenu(self)

            # add actions to delete peak
            if self._highlightPeakID >= 0:
                action_del_peak = QAction('Delete Peak', self)
                action_del_peak.triggered.connect(self.menu_delete_peak_in_pick)
                self._menu.addAction(action_del_peak)

            # NOTE: The following 3 actions are disabled as they are rarely used and confusing
            # # add actions to add group boundaries
            # if self._addedLeftBoundary:
            #     # next boundary to add must be a right boundary
            #     action_add_right_bound = QtGui.QAction('Add right boundary', self)
            #     action_add_right_bound.triggered.connect(self.menu_add_right_group_boundary)
            #     self._menu.addAction(action_add_right_bound)
            # else:
            #     # next boundary to add must be a left boundary
            #     action_add_left_bound = QtGui.QAction('Add left boundary', self)
            #     action_add_left_bound.triggered.connect(self.menu_add_left_group_boundary)
            #     self._menu.addAction(action_add_left_bound)

            # # add action to undo work to add boundary
            # action_cancel = QtGui.QAction('Cancel boundary', self)
            # action_cancel.triggered.connect(self.menu_undo_boundary)
            # self._menu.addAction(action_cancel)

            # # add action to reset all the grouping effort
            # action_reset = QtGui.QAction('Reset grouping', self)
            # action_reset.triggered.connect(self.menu_reset_grouping)
            # self._menu.addAction(action_reset)

            # pop
            self._menu.popup(QCursor.pos())

        else:
            # power mode
            # create a menu in the edit mode
            self._menu = QMenu(self)

            self._eventX = event.xdata

            # optionally add option to delete peak
            if self._myPeakSelectionMode == PeakAdditionState.MultiMode:
                action2 = QAction('Delete Peak', self)
                action2.triggered.connect(self.menu_delete_peak_in_pick)
                self._menu.addAction(action2)

            # add item to delete peak group
            action1 = QAction('Delete Group', self)
            action1.triggered.connect(self.menu_delete_group_in_pick)
            self._menu.addAction(action1)

            action3 = QAction('Show Info', self)
            action3.triggered.connect(self.menu_show_info)
            self._menu.addAction(action3)

            # add other required actions
            self._menu.popup(QCursor.pos())
        # END-IF-ELSE

        return

    def on_mouse_release_event(self, event):
        """

        :param event:
        :return:
        """
        # set the mouse pressed status back
        if self._mouseButtonBeingPressed != 0:
            self._mouseButtonBeingPressed = 0
        else:
            print('[DB] Mouse is not pressed but released.')

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

    def set_peak_selection_mode(self, peak_selection_mode):
        """
        Set peak-selection mode
        :param peak_selection_mode:
        :return:
        """
        # check inputs
        assert isinstance(peak_selection_mode, int), 'Input peak selection mode must be an integer but not ' \
                                                     '%s' % peak_selection_mode.__class__.__name__
        assert PeakAdditionState.is_valid_mode(peak_selection_mode), 'Mode %d is not valid.' % peak_selection_mode

        self._myPeakSelectionMode = peak_selection_mode

        return

    def menu_delete_group_in_pick(self):
        """ Delete the peak group (in-pick mode) where the cursor is
        :return:
        """
        # check
        assert self._eventX is not None

        # find out the current position
        curr_group_id = self._currGroupID

        # delete group on canvas
        removed = self.remove_group(curr_group_id)
        assert removed

        # delete group from peak group manager
        removed = self._myPeakGroupManager.delete_group(curr_group_id)
        assert removed, 'Unable to delete group %d from group manager.' % curr_group_id

        return

    def menu_delete_peak_in_pick(self):
        """
        Delete a peak from canvas
        :return:
        """
        # check
        assert self._eventX is not None

        # delete peak in 2 different type
        if self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            # automatic peak selection
            curr_peak_id = self._highlightPeakID
            # reset highlight
            self._highlightPeakID = -1
            # remove
            # TO-TEST: corrected #65
            removed = self.remove_peak_indicator(self._currGroupID, curr_peak_id)
            assert removed

        elif self._myPeakSelectionMode == PeakAdditionState.QuickMode \
                or self._myPeakSelectionMode == PeakAdditionState.MultiMode:
            # manual peak selection
            # find out the current position
            curr_group_id = self._currGroupID
            curr_peak_id = self._currIndicatorID
            curr_item_type = self._currIndicatorType
            print('[DB....Delete Peak] About to delete group %d peak %d type %d==2.' % (curr_group_id,
                                                                                        curr_peak_id,
                                                                                        curr_item_type))
            assert curr_item_type == 1, \
                'Current item type must be equal 1 for peak but not %d.' % curr_item_type

            # remove peak
            # TO-TEST: corrected #65
            removed = self.remove_peak_indicator(self._currGroupID, curr_peak_id)
            if not removed:
                raise RuntimeError('Unable to remove peak (indicator) for peak with ID {0}'.format(curr_peak_id))
            # delete peak from peak group manager
            removed = self._myPeakGroupManager.delete_peak(curr_group_id, curr_peak_id)
            if not removed:
                raise RuntimeError('Unable to remove peak with ID {0} from peak group {1}.'
                                   ''.format(curr_peak_id, curr_group_id))

        else:
            # unsupported situation
            raise RuntimeError('Impossible to happen!')

        return

    """
    menu_reset_grouping
    """

    def menu_add_left_group_boundary(self):
        """
        add left boundary
        :return:
        """
        # check
        assert self._eventX is not None, 'Event dataX must be specified.'

        # add a boundary
        self.add_group_boundary(self._eventX, left=True)

        return

    def menu_add_right_group_boundary(self):
        """
        add right boundary
        :return:
        """
        # check
        assert self._eventX is not None, 'Event dataX must be specified.'

        # add a boundary
        self.add_group_boundary(self._eventX, left=False)

        return

    def menu_show_info(self):
        """

        :return:
        """
        item_id, item_type, group_id = self._myPeakGroupManager.in_vicinity(self._eventX, 0.005)
        print('[DB] Current Item = %d of type %d in Group %d.' % (item_id, item_type, group_id))

        return

    def plot_diffraction_pattern(self, vec_x, vec_y, title=None, key=None):
        """
        Plot a diffraction pattern on canvas
        :param vec_x: 1d array or list for X
        :param vec_y: 1d array or list for Y
        :param title:
        :param key:
        :return:
        """
        # check
        if len(vec_x) != len(vec_y):
            raise RuntimeError('vector of x and y have different size!')

        # Plot
        if title is None:
            title = ''

        pattern_key = self.add_plot_1d(vec_x, vec_y, label=title, color='black', marker='.',
                                       x_label='dSpacing')
        if self.get_x_limit()[1] > 50:
            # reset x range
            self.setXYLimit(xmin=0, xmax=5.)

        # Record the data for future usage
        if key is not None:
            self._myPatternDict[key] = (vec_x, vec_y, pattern_key)

        print('[DB...BAT] Plot {} to have pattern key {}'.format(title, pattern_key))
        self._lastPlotID = pattern_key

        return

    def plot_peak_indicator(self, peak_pos):
        """ Add a peak's indicator, i.e., center only
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
        assert peak_pos > 0., 'Peak position {0} must be positive.'.format(peak_pos)
        assert left_x <= peak_pos <= right_x, 'Specified peak position %f is out of canvas range ' \
                                              '(%f, %f)' % (peak_pos, left_x, right_x)

        # Add indicator
        indicator_id = self.add_vertical_indicator(peak_pos, 'red')

        # Add peak to data structure for managing
        self._shownPeakIDList.append(indicator_id)

        return

    def remove_all_in_pick_peaks(self):
        """ Remove all peaks' indicators
        Note: this method is not used (as caller is disabled for further review')
        :return:
        """
        # Remove all indicators
        for peak_group in self._inEditGroupList:
            assert isinstance(peak_group, DiffractionPlotView.GroupedPeaksInfo), 'Peak group has a wrong type'

            # remove left boundary
            left_id = peak_group.left_boundary_id
            self.remove_indicator(left_id)
            # if left_id in self._mySinglePeakDict:
            #     del self._mySinglePeakDict[left_id]

            right_id = peak_group.right_boundary_id
            self.remove_indicator(right_id)
            # if right_id in self._mySinglePeakDict:
            #     del self._mySinglePeakDict[right_id]

            for peak_tuple in peak_group.get_peaks():
                peak_ind_id = peak_tuple[1]
                self.remove_indicator(peak_ind_id)
                # if peak_ind_id in self._mySinglePeakDict:
                #     del self._mySinglePeakDict[peak_ind_id]

        # Clear the indicator position-key list
        self._inEditGroupList = list()

        raise NotImplementedError('Enable: remove_all_in_pick_peaks')

    def remove_peak_indicator(self, peak_group_id, peak_indicator_index):
        """ Remove a peak indicator
        Purpose:
            Remove a peak indicator according to a given position value
        Requirements:
            Peak index should be a valid value
        Guarantees:
            The indicator is removed from the canvas
        :param peak_group_id:
        :param peak_indicator_index:
        :return:
        """
        # check
        assert isinstance(peak_indicator_index, int), 'Peak indicator index {0} must be an integer but not a {1}.' \
                                                      ''.format(peak_indicator_index, type(peak_indicator_index))

        # find and remove indicator from peak group manager
        if self._myPeakSelectionMode == PeakAdditionState.AutoMode:
            removable = True
            # remove it from controller
            del self._mySinglePeakDict[peak_indicator_index]
        else:
            # remove peak by ID for PeakAdditionState
            removable = self._myPeakGroupManager.delete_peak(group_id=peak_group_id,
                                                             peak_id=peak_indicator_index)

        # remove indicator on the canvas
        if removable:
            self.remove_indicator(peak_indicator_index)

        return True

    def remove_vanadium_peaks(self, peak_indicator_list):
        """
        Remove vanadium peaks indicators
        :param peak_indicator_list:
        :return:
        """
        datatypeutility.check_list('Vanadium peak indicators', peak_indicator_list)

        for peak_index in range(len(peak_indicator_list)):
            peak_indicator = peak_indicator_list[peak_index]
            self.remove_indicator(peak_indicator)
            peak_indicator_list[peak_index] = None
        # END-FOR

        return

    def remove_show_only_peaks(self):
        """ Removed all the peaks' indicators that is for shown only
        :return:
        """
        # remove indicators from canvas
        for peak_indicator_id in self._shownPeakIDList:
            self.remove_indicator(peak_indicator_id)
            self._shownPeakIDList.remove(peak_indicator_id)

        # clear the inPickPeakList
        assert len(self._inEditGroupList) == 0, 'It is supposed that there is no peak group in edit mode.'

        return

    def reset_peak_picker_mode(self, remove_diffraction_data=True):
        """ Reset the canvas and peaks managers and single peak lines in peak picker mode
        :return:
        """
        # reset peak indicator for selected peaks
        self.clear_highlight_data()
        self.reset_selected_peaks()

        # remove the plotted diffraction pattern
        if self._lastPlotID:
            print('[DB...BAT] reset() --> remove {}'.format(self._lastPlotID))
            self.remove_line(self._lastPlotID)
            self._lastPlotID = None

        self._myPeakGroupManager.reset()
        self._highlightsPlotIDList = list()

        # FIXME TODO - ASAP - shall not use clear_all_lines.
        # FIXME ...  cont.    but cannot find out the cause for the original diffraciton line not be removed
        if remove_diffraction_data:
            self.clear_all_lines()

        return

    def reset_selected_peaks(self):
        """
        reset selected peaks
        :return:
        """
        # all grouped peaks
        self._myPeakGroupManager.reset()

        # all single peaks
        peak_indicator_index_list = self._mySinglePeakDict.keys()
        for peak_indicator_index in peak_indicator_index_list:
            del self._mySinglePeakDict[peak_indicator_index]
            self.remove_indicator(peak_indicator_index)
        # END-FOR

        return

    def set_parent_window(self, parent_window):
        """
        Set a parent window (QMainWindow)
        :param parent_window:
        :return:
        """
        assert isinstance(parent_window, QMainWindow), \
            'Parent window must be a QMainWindow instance, but not an instance of %s.' \
            '' % parent_window.__class__.__name__

        self._parentWindow = parent_window

        return

    def sort_n_add_peaks(self, peak_info_list):
        """ Sort and add peaks including
        use case 1: it is called by find_peaks() in automatic peak finding mode.
        Requirements:
         1. peak info list: list of peak information tuple (centre, height, width, HKL)
        Guarantees (goal):
         1. peaks will be sorted by positions;
         x peaks will be added to peak table without group and peak range (for fitting);
           -- this will be done in its main application!
         3. peaks will be plotted to canvas
        :param peak_info_list:
        :return:
        """
        # check requirements
        assert self._myPeakSelectionMode != PeakAdditionState.NonEdit, 'Peak selection mode cannot be ' \
                                                                       'in NonEdit mode.'
        datatypeutility.check_list('Peaks information', peak_info_list)

        if len(peak_info_list) == 0:
            # return for an empty peak list
            return

        # order the peaks in reverse order
        peak_info_list.sort(reverse=True)

        # plot all the peaks
        for peak_info in peak_info_list:
            # get value
            peak_center = peak_info[0]

            if self._myPeakSelectionMode == PeakAdditionState.AutoMode:
                # auto mode. peak only
                print('[DB...BAT] Add single peak @ {}'.format(peak_center))
                self.add_single_peak(peak_pos=peak_center)
            else:
                # power mode: peak and boundary
                peak_width = peak_info[2]
                print('[DB...BAT] Add grouped peaks @ {}'.format(peak_center))
                # add peak group indicator
                group_id = self.add_peak_group(peak_center - 2*peak_width, peak_center + 2*peak_width)
                self.add_peak(peak_center, group_id=group_id)
            # END-IF-ELSE

    def switch_mode(self, target_mode):
        """
        switch function mode
        :param target_mode:
        :return:
        """
        print(f'[WARNING] {target_mode} is not used')
        # reset current canvas
        self.reset()

        return
