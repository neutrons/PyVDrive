__author__ = 'wzz'

import operator
import bisect


class GroupedPeaksManager(object):
    """ Manager for grouped peaks
    It will serve as the backbone data structure for both diffraction view for peak picking
    and table for picked peaks
    """
    def __init__(self):
        """
        Initialization
        :return:
        """
        # group
        self._myGroupList = list()  # group list and group dict
        self._myGroupDict = dict()  # contain same set of Group object. Dictionary use ID for
        self._groupSorted = True

        # key for group ID
        self._nextGroupID = 0

        # dynamic search map
        # vector of X of region boundaries, x0, x1, x2, x3, where (x0, x1) is for group 1's left boundary
        self._vecX = list()
        # vector of peak/boundary' indicator IDs corresponding to vecX
        self._vecID = list()
        # vector of peak/boundary's group IDs
        self._vecGroupID = list()
        # vector of indicator types including left boundary (0), peak (1) and right boundary (2)
        self._vecType = list()

        return

    def _add_item(self, position, indicator, group_id, item_type):
        """
        Add an item to search map
        Note: the integrity should not been considered in this method
        :param position:
        :param group_id:
        :param item_type: 0 (left boundary), 1 (peak), 2 (right boundary)
        :return:
        """
        # check
        assert isinstance(position, float)
        assert isinstance(group_id, int), 'Indicator ID %s must be an integer,' \
                                          'but not %s.' % (str(group_id), str(type(group_id)))
        assert isinstance(item_type, int)
        assert 0 <= item_type <= 2, 'Indicator type %s must be 0, 1, or 2' % str(item_type)

        # find the spot to insert
        index_x = bisect.bisect_right(self._vecX, position)

        # insert
        self._vecX.insert(index_x, position)
        self._vecID.insert(index_x, indicator)
        self._vecGroupID.insert(index_x, group_id)
        self._vecType.insert(index_x, item_type)

        return

    def _remove_items(self, index_list):
        """ Remove items
        :param index_list:
        :return:
        """

    def _update_item(self, indicator_id, new_pos):
        """

        :param indicator_id:
        :param new_pos:
        :return:
        """

    def add_group(self, new_group):
        """ Add a new group
        :param new_group:
        :return:
        """
        assert isinstance(new_group, GroupedPeaksInfo)

        if self.can_add_group(new_group.left_boundary, new_group.right_boundary) is False:
            # unable to add new group
            raise RuntimeError('Unable to add group!')

        # add new group
        group_id = new_group.get_id()

        self._myGroupList.append(new_group)
        self._myGroupDict[group_id] = new_group

        self._groupSorted = False
        self.sort_group()

        # update ...
        self._add_item(new_group.left_boundary, new_group.left_boundary_id, group_id, 0)
        peak_list = new_group.get_peaks()
        for peak_i in peak_list:
            self._add_item(peak_i[0], peak_i[1], group_id, 1)
        self._add_item(new_group.right_boundary, new_group.right_boundary_id, group_id, 2)

        # debug output
        print '[DB] Group list information:\n%s' % self.pretty()

        return

    def add_peak(self, group_id, peak_pos, peak_id):
        """

        :param group_id:
        :param peak_pos:
        :return:
        """
        assert group_id in self._myGroupDict

        self._myGroupDict[group_id].add_peak(indicator_id=peak_id, peak_pos=peak_pos)

        # add to dynamic map
        self._add_item(position=peak_pos, indicator=peak_id, group_id=group_id, item_type=1)

        # debug output
        print '[DB] Group list information:\n%s' % self.pretty()

        return

    def can_add_group(self, left_boundary, right_boundary):
        """

        :param left_boundary:
        :param right_boundary:
        :return:
        """
        return True

    def delete_group(self, group_id):
        """

        :param group_id:
        :return:
        """

    def get_group_id(self, peak_pos):
        """

        :param peak_pos:
        :return:
        """

        return -1

    def get_new_group_id(self):
        """

        :return:
        """
        new_id = self._nextGroupID
        self._nextGroupID += 1

        return new_id

    def in_vicinity(self, x, resolution):
        """
        :param x:
        :return:
        """
        assert isinstance(x, float)

        index = bisect.bisect_right(self._vecX, x)

        ret_index = None
        if index == 0:
            if self._vecX[0] - x < resolution:
                # before X[0] and within resolution range
                ret_index = 0
        elif index == len(self._vecX):
            if x - self._vecX[-1] < resolution:
                # after X[-1] and within resolution range
                ret_index = len(self._vecX) - 1
        elif x - self._vecX[index-1] < resolution:
            # x is within resolution range to its left
            ret_index = index - 1
        elif self._vecX[index] - x < resolution:
            # x is within resolution rnage to its right
            ret_index = index

        # set up return
        if ret_index is None:
            return -1, -1, -1

        return self._vecID[0], self._vecType[0], self._vecGroupID[0]

    @property
    def is_sorted(self):
        """ Whether group is sorted
        :return:
        """
        return self._groupSorted

    def pretty(self):
        """
        Print prettily
        :return:
        """
        w_buf = ''
        for p_g in self._myGroupList:
            w_buf += '%s\n' % str(p_g)

        w_buf += '%-5s\t%-5s\t%-5s\t%-5s\n' % ('X', 'ID', 'Type', 'Group')
        number = len(self._vecX)
        for index in xrange(number):
            w_buf += '%.5f\t%-4d\t%-4d\t%-4d\n' % (self._vecX[index], self._vecID[index],
                                                   self._vecType[index], self._vecGroupID[index])

        return w_buf

    def sort_group(self):
        """

        :return:
        """
        # ...
        if len(self._myGroupList) > 1:
            # ...
            self._myGroupList.sort(key=operator.attrgetter('left_boundary'))

        self._groupSorted = True

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

        # group ID
        self._groupID = -1
    
        #
        self._leftID = left_boundary_id
        self._rightID = right_boundary_id
    
        self._leftX = left_x
        self._rightX = right_x
    
        self._peakPosIDList = list()  # a list of 2-tuple as peak position and indicator ID
    
        return
    
    def __str__(self):
        """ Pretty print for Grouped PeaksInfo
        :return:
        """
        out_str = 'Group %d: ' % self._groupID
        out_str += '[Left boundary (%d): %.7f, ' % (self.left_boundary_id, self.left_boundary)
        for i_peak in xrange(len(self._peakPosIDList)):
            out_str += 'P_%d (%d): %.7f, ' % (i_peak, self._peakPosIDList[i_peak][1],
                                              self._peakPosIDList[i_peak][0])
        out_str += 'Right boundary (%d): %.7f]' % (self.right_boundary_id, self.right_boundary)
    
        return out_str
    
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
        self._peakPosIDList.append((peak_pos, indicator_id))
    
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
        for i_peak in xrange(len(self._peakPosIDList)):
            p_id = self._peakPosIDList[i_peak][1]
            if p_id == peak_id:
                found_peak = True
                self._peakPosIDList.pop(i_peak)
                break
    
        return found_peak

    def get_id(self):
        """

        :return:
        """
        return self._groupID
    
    def get_number_peaks(self):
        """ Get number of peaks in this peaks group
        :return:
        """
        return len(self._peakPosIDList)
    
    def get_peaks(self):
        """ Get all the peaks' tuple
        :return: a list of 2-tuples (peak position and peak ID)
        """
        self._peakPosIDList.sort()
    
        return self._peakPosIDList[:]

    def set_id(self, group_id):
        """

        :return:
        """
        self._groupID = group_id

    def set_edit_mode(self, mode):
        """

        :param mode:
        :return:
        """
        self._inEditMode = mode

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
        for i_peak in xrange(len(self._peakPosIDList)):
            p_id = self._peakPosIDList[i_peak][1]
            if p_id == peak_id:
                self._peakPosIDList[i_peak] = (center_position, peak_id)
                found_peak = True
                break
        # END-FOR
    
        return found_peak

