__author__ = 'wzz'

import operator
import bisect

TINY = 1.0E-9


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

    def _check_vector_x(self):
        """ Check whether all items/elements in self._vecX are in ascending order
        :return: True if all elements in self._vecX are n ascending order
        """
        # special case for empty vector or 1-element vector
        if len(self._vecX) <= 1:
            return True

        # check
        vec_size = len(self._vecX)
        for index in xrange(1, vec_size):
            if self._vecX[index-1] >= self._vecX[index]:
                # previous element is not smaller than the current element
                return False

        return True

    def _remove_items(self, index_list):
        """ Remove items by their indexes
        Requirements: the input is a list of integers
        :param index_list:
        :return:
        """
        # check
        assert isinstance(index_list, list), 'Input index_list must be a list but not %s.' % str(type(index_list))

        # sort index_list
        index_list.sort(reverse=True)

        # pop items from back to frond
        for index in index_list:
            self._vecX.pop(index)
            self._vecID.pop(index)
            self._vecType.pop(index)
            self._vecGroupID.pop(index)
        # END-FOR

        return

    def _update_map_item_pos(self, indicator_id, new_pos, check):
        """
        Update the position of an indicator in the dynamic item-map (cursor map)
        Requirements: indicator_id is an existing indicator (integer) and new_pos is still in between its neighbors

        :exception: if the check is turned on and the mono-increment of vecX is destroyed
        :exception: if the indicator is not found

        :param indicator_id:
        :param new_pos:
        :param check: flag to check whether this update is allowed. Check should be turned off during mass move
        :return:
        """
        # check
        assert isinstance(indicator_id, int), 'Indicator ID must be an integer but not %s.' % str(type(indicator_id))
        assert isinstance(new_pos, float), 'New position must be a float but not %s.' % str(type(indicator_id))

        # search entry for this indicator by brute force
        updated = False
        for index in xrange(len(self._vecID)):
            if indicator_id == self._vecID[index]:
                # find the item in the list with desired indicator ID
                if check:
                    # check whether new position meets requirement
                    if index > 0 and new_pos <= self._vecX[index-1]:
                        raise RuntimeError('Indicator %d at index %d has new position %f smaller than X[%d] = %f.' % (
                            indicator_id, index, new_pos, index-1, self._vecX[index-1]
                        ))
                    elif index < len(self._vecX) - 1 and new_pos >= self._vecX[index+1]:
                        raise RuntimeError('Indicator %d at index %d has new position %f larger than X[%d] = %f.' % (
                            indicator_id, index, new_pos, index+1, self._vecX[index+1]
                        ))
                # END-IF

                # set new position to right X
                self._vecX[index] = new_pos
                updated = True
            # END-IF
        # END-FOR

        assert updated is True, 'Indicator %d does not exist.' % indicator_id

        return True

    def add_group(self, new_group):
        """ Add a new group
        :param new_group:
        :return:
        """
        assert isinstance(new_group, GroupedPeaksInfo)

        if self.can_add_group(new_group.left_boundary, new_group.right_boundary) is False:
            # unable to add new group
            raise RuntimeError('Unable to add group!')

        # add new group by getting ID, add group to both list and dictionary, and sort
        group_id = new_group.get_id()

        self._myGroupList.append(new_group)
        self._myGroupDict[group_id] = new_group

        self._groupSorted = False
        self.sort_group()

        # update the dynamic cursor map by adding boundaries and peaks in the group
        self._add_item(new_group.left_boundary, new_group.left_boundary_id, group_id, 0)
        peak_list = new_group.get_peaks()
        for peak_i in peak_list:
            self._add_item(peak_i[0], peak_i[1], group_id, 1)
        self._add_item(new_group.right_boundary, new_group.right_boundary_id, group_id, 2)

        # debug output
        print '[DB] Group list information:\n%s' % self.pretty()

        return

    def add_peak(self, group_id, peak_pos, peak_id):
        """ Add a peak to a peak group and update the dynamic cursor map
        :param group_id:
        :param peak_pos:
        :param peak_id: peak indicator ID
        :return:
        """
        #
        assert group_id in self._myGroupDict
        assert isinstance(peak_pos, float), 'Peak position must be a float but not a %s.' % str(type(peak_pos))
        assert isinstance(peak_id, int), 'Peak indicator ID must be an integer but not a %s.' % str(type(peak_id))

        # add peak to the group
        self._myGroupDict[group_id].add_peak(indicator_id=peak_id, peak_pos=peak_pos)

        # add to dynamic map
        self._add_item(position=peak_pos, indicator=peak_id, group_id=group_id, item_type=1)

        # debug output
        print '[DB] Group list information:\n%s' % self.pretty()

        return

    def can_add_group(self, left_boundary, right_boundary):
        """ check whether a peak (noted by its left and right boundaries) among a list of group
        Guarantees: It is defined for not being able to add a peak-group if
        (1) either left boundary or right boundary is inside a peak group
        (2) left boundary and right boundary are in different neighbor hood.
        :param left_boundary:
        :param right_boundary:
        :return: boolean
        """
        # check
        assert isinstance(left_boundary, float), 'Left boundary should be a float.'
        assert isinstance(right_boundary, float), 'Right boundary should be a float.'
        assert left_boundary < right_boundary, 'Left boundary %f should be smaller than right boundary %f' \
                                               '.' % (left_boundary, right_boundary)

        # always true for an empty vecX
        if len(self._vecX) == 0:
            return True

        # find the position
        left_bound_index = bisect.bisect_right(self._vecX, left_boundary)
        right_bound_index = bisect.bisect_right(self._vecX, right_boundary)

        print '[DB... Try to add group] New group region: ', left_boundary, ', ', right_boundary,
        print '; Boundary index = ', left_bound_index, ', ', right_bound_index
        print self.pretty()

        # indexes of left boundary and right boundary should be same because there must not be any indicator
        # between these 2 boundaries
        if left_bound_index != right_bound_index:
            return False

        # the group ID of the boundaries' neighbors must be different, such that these two boundaries
        # won't be inside any peak group
        if right_bound_index == 0:
            # left to left end of the scale
            ret_value = True
        elif left_bound_index == len(self._vecX):
            # right to right end of the scale
            ret_value = True
        else:
            # in the middle: they must be between 2 different groups
            ret_value = self._vecGroupID[left_bound_index-1] != self._vecGroupID[right_bound_index+1]

        return ret_value

    def can_move_item(self, item_id, delta_x, limit):
        """
        Check whether an item can be moved by not cross its neighbors
        :param item_id:
        :param delta_x:
        :param limit:
        :return:
        """
        # check
        assert isinstance(item_id, int) and item_id >= 0
        assert isinstance(delta_x, float)
        assert isinstance(limit, tuple) or isinstance(limit, list)
        assert len(limit) == 2

        # locate item by search for item_id in the vecID
        index = None
        for id_index in xrange(len(self._vecID)):
            if self._vecID[id_index] == item_id:
                index = id_index
        # END-FOR (id_index)
        assert index is not None, 'Indicator ID %d does not exist in group map %s.' % (item_id, self.pretty())

        # check with its neighbor
        if delta_x < 0:
            # tending to move to the left
            if index == 0:
                # already leftmost, check limit
                ret_value = self._vecX[index] + delta_x > limit[0]
            else:
                # compare with the left neighbor
                ret_value = self._vecX[index] + delta_x > self._vecX[index-1]
        else:
            # tending to move to the right
            if index == len(self._vecX) - 1:
                # already rightmost, check limit
                right_wall = limit[1]
            else:
                # compare with right neighbor
                right_wall = self._vecX[index+1]
            ret_value = self._vecX[index] + delta_x < right_wall

        return ret_value

    def delete_group(self, group_id):
        """
        Delete a group and remove all of its entries in the dynamic map
        :param group_id:
        :return:
        """
        # check
        assert group_id in self._myGroupDict

        # pop group from list
        group = None
        for i_group in self._myGroupList:
            group = self._myGroupList[i_group]
            if group.get_id() == group_id:
                group = self._myGroupList.pop(i_group)
        # END-FOR
        assert group is not None

        # delete group from dictionary
        del self._myGroupDict[group_id]

        # remove from the maps
        index_remove_list = list()
        for index in xrange(len(self._vecGroupID)):
            if self._vecGroupID[index] == group_id:
                index_remove_list.append(index)
        # END-IF
        self._remove_items(index_remove_list)

        return

    def delete_peak(self, group_id, peak_id):
        """ Delete a peak from a PeaksGroup and from the cursor map as well
        :param group_id:
        :param peak_id:
        :return: boolean. True if peak ID exists in group
        """
        # check
        assert isinstance(group_id, int)
        if group_id not in self._myGroupDict:
            return False

        assert isinstance(peak_id, int)
        group = self._myGroupDict[group_id]
        if group.has_peak(peak_id) is False:
            return False

        # remove peak from PeaksGroup
        peak_pos = group.get_peak_pos(peak_id)
        group.delete_peak(peak_id)

        # update the dynamic cursor map
        index_xp = bisect.bisect_right(self._vecX, peak_pos)
        if index_xp == 0:
            # peak cannot be at the begin of the items list
            index_xp = 1
        elif index_xp == len(self._vecX):
            # peak cannot be at the end of the items list
            index_xp = len(self._vecX) - 1
        else:
            # find out the nearest one
            if peak_pos - self._vecX[index_xp-1] < self._vecX[index_xp] - peak_pos:
                index_xp -= index_xp
        # END-IF-ELSE

        self._remove_items([index_xp])

        return True

    def get_boundaries(self, x, x_limit):
        """
        Find out the left and right boundary of a potential peak-group
        :param x:
        :param x_limit:
        :return:
        """
        assert len(x_limit) == 2
        assert x_limit[0] < x_limit[1]

        # in case emtpy
        if len(self._vecX) == 0:
            return x_limit[0], x_limit[1]

        # find index of x
        index_x = bisect.bisect_right(self._vecX, x)
        if index_x == 0:
            # left to everything
            left_bound = x_limit[0]
            right_bound = self._vecX[0]

        elif index_x == len(self._vecX):
            # right to everything
            left_bound  = self._vecX[-1]
            right_bound = x_limit[1]

        else:
            # in the middle
            left_bound = self._vecX[index_x-1]
            right_bound = self._vecX[index_x]

        # END-IF-ELSE
        # check
        assert left_bound < right_bound

        return left_bound, right_bound

    def get_group(self, group_id):
        """
        Get the reference to a group by its group ID
        :param group_id:
        :return:
        """
        return self._myGroupDict[group_id]

    def get_group_id(self, x):
        """
        Find out a position (x) inside any group
        :param x:
        :return:
        """
        assert isinstance(x, float)

        # find nearest index for x
        index_x = bisect.bisect_right(self._vecX, x)

        if index_x == 0 or index_x == len(self._vecX):
            # x is left to everything or right to everything
            group_id = -1
        else:
            # x is in between 2 items, check whether their group ID are same or not
            group_id = self._vecGroupID[index_x]
            if group_id != self._vecGroupID[index_x-1]:
                group_id = -1

        return group_id

    def get_new_group_id(self):
        """
        Get the next NEW group ID for uniqueness
        :return:
        """
        new_id = self._nextGroupID
        self._nextGroupID += 1

        return new_id

    def has_group(self, group_id):
        """
        Check whether the group manager has a group with a specified ID
        :param group_id:
        :return:
        """
        assert isinstance(group_id, int), 'Group ID must be an integer but not %s.' % str(type(group_id))

        return group_id in self._myGroupDict

    def in_vicinity(self, x, item_range):
        """ Get the information of a position X in the item/cursor map
        :param x:
        :param item_range: range of an item to claim that the cursor is in its vicinity region
        :return: 3-tuple as (item indicator ID, item type,  group ID)
        """
        assert isinstance(x, float)
        assert isinstance(item_range, float) and item_range > 0

        free_zone = -1, -1, -1

        # rule out the situation that is empty
        if len(self._vecX) == 0:
            return free_zone

        index = bisect.bisect_right(self._vecX, x)

        ret_index = None
        if index == 0:
            if self._vecX[0] - x < item_range:
                # before X[0] and within resolution range
                ret_index = 0
        elif index == len(self._vecX):
            if x - self._vecX[-1] < item_range:
                # after X[-1] and within resolution range
                ret_index = len(self._vecX) - 1
        elif x - self._vecX[index-1] < item_range:
            # x is within resolution range to its left
            ret_index = index - 1
        elif self._vecX[index] - x < item_range:
            # x is within resolution range to its right
            ret_index = index

        # set up return
        if ret_index is None:
            return free_zone

        return self._vecID[ret_index], self._vecType[ret_index], self._vecGroupID[ret_index]

    def can_move_left(self, item_pos, delta_x, x_left_limit):
        """

        :return:
        """
        assert delta_x < 0

        index_left = bisect.bisect_right(self._vecX, item_pos-TINY)
        if index_left == 0:
            # there is nothing to the group's left. free to go!
            left_wall = x_left_limit
            left_group = -2
        else:
            left_wall = self._vecX[index_left-1]
            left_group = self._vecGroupID[index_left-1]

        # return False if the left bound is hit
        if item_pos + delta_x <= left_wall:
            # form error message
            msg = 'Item position = %.9f, Left wall index = %d\n' % (item_pos, index_left-1)
            msg += 'Group information: \n%s\n' % self.pretty()
            msg += '[DB] Unable to move left boundary to left as Left wall @ %f of group %d is hit' % (left_wall,
                                                                                                       left_group)
            print msg
            return False

        return True

    def can_move_right(self, item_pos, delta_x, x_right_limit):
        """

        :param item_pos:
        :param delta_x:
        :param x_right_limit:
        :return:
        """
        assert delta_x > 0

        # check right wall
        index_right = bisect.bisect_right(self._vecX, item_pos+TINY)
        if index_right == len(self._vecX):
            # to the very right of anything
            right_wall = x_right_limit
            right_group = -2
        else:
            # something to its right
            right_wall = self._vecX[index_right]
            right_group = self._vecGroupID[index_right]

        # return False if the right bound is hit
        if item_pos + delta_x >= right_wall:
            print '[DB] Unable to move group to right as right wall @ %f of group %d is hit.' % (right_wall,
                                                                                                 right_group)
            return False

        return True

    def move_group(self, group_id, displacement, limit_x, check):
        """ Move a group to a same direction
        :param group_id:
        :param displacement:
        :param limit_x:
        :param check: check validity
        :return: boolean.  False if it is not allowed to move
        """
        # check
        assert isinstance(limit_x, tuple) or isinstance(limit_x, list)
        assert len(limit_x) == 2

        # find the left boundary and right boundary of the group to be moved
        group_2_move = self.get_group(group_id)

        # check whether it is allowed to move that far
        if check:
            if displacement < 0:
                # can move left?
                can_move = self.can_move_left(group_2_move.left_boundary, displacement, limit_x[0])
            else:
                # can move right?
                can_move = self.can_move_right(group_2_move.right_boundary, displacement, limit_x[1])
            if can_move is False:
                return False
        # END-IF

        # move the group by update positions of boundaries and peaks
        group_2_move.left_boundary += displacement
        group_2_move.right_boundary += displacement
        group_2_move.shift_peaks_position(peak_id=None, shift=displacement, check=False)

        # update the map
        self._update_map_item_pos(indicator_id=group_2_move.left_boundary_id,
                                  new_pos=group_2_move.left_boundary,
                                  check=False)
        self._update_map_item_pos(indicator_id=group_2_move.right_boundary_id,
                                  new_pos=group_2_move.right_boundary,
                                  check=False)
        for peak_info in group_2_move.get_peaks():
            peak_pos, peak_id = peak_info
            print '[DB...] Peak position = ', peak_pos, 'of type ', type(peak_pos)
            print '[DB...] Peak Id       = ', peak_id, 'of type', type(peak_id)
            self._update_map_item_pos(indicator_id=peak_id,
                                      new_pos=peak_pos,
                                      check=False)

        # check integrity
        if self._check_vector_x() is False:
            raise RuntimeError('Impossible to have vecX out of order.')

        return True

    def move_left_boundary(self, group_id, displacement, check):
        """
        Move the left boundary of a peak group and update the cursor map
        :param group_id:
        :param displacement: delta x
        :param check:
        :return:
        """
        # check arguments
        assert isinstance(group_id, int)
        assert isinstance(displacement, float)
        assert isinstance(check, bool)

        # get group
        assert group_id in self._myGroupDict
        peak_group = self._myGroupDict[group_id]
        left_bound_id = peak_group.left_boundary_id

        # check whether moving is allowed
        if check and not self.can_move_item(left_bound_id, displacement, (0, 1000000)):
            return False

        # update peak group
        peak_group.left_boundary += displacement

        # update the cursor map
        self._update_map_item_pos(indicator_id=left_bound_id,
                                  new_pos=peak_group.left_boundary,
                                  check=check)

        return True

    def move_right_boundary(self, group_id, displacement, check):
        """
        Move the right boundary of a peak group and update the cursor map
        :param group_id:
        :param displacement: delta x
        :param check:
        :return:
        """
        # check argument
        assert isinstance(group_id, int)
        assert isinstance(displacement, float)
        assert isinstance(check, bool)

        # get group
        assert group_id in self._myGroupDict
        peak_group = self._myGroupDict[group_id]
        right_bound_id = peak_group.right_boundary_id

        # check whether moving is allowed
        if check and not self.can_move_item(right_bound_id, displacement, (0, 1000000)):
            return False

        # update peak group
        peak_group.right_boundary += displacement

        # update the cursor map
        self._update_map_item_pos(indicator_id=right_bound_id,
                                  new_pos=peak_group.right_boundary,
                                  check=check)

        return True

    def move_peak(self, group_id, peak_id, delta_x, check):
        """

        :param group_id:
        :param peak_id:
        :param delta_x:
        :param check:
        :return:
        """
        # TODO/NOW - Doc and check
        # assert ...

        # get group
        curr_group = self._myGroupDict[group_id]

        # check
        if check:
            # TODO/NOW
            raise NotImplementedError('Implement ASAP')

        # update peak position inside group
        is_displacement = True
        updated = curr_group.update_peak_position(peak_id, delta_x, is_displacement)
        assert updated

        # update the dynamic cursor map
        self._update_map_item_pos(indicator_id=peak_id, new_pos=curr_group.get_peak_pos(peak_id),
                                  check=False)

        return True

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

        w_buf += '%-10s\t%-5s\t%-5s\t%-5s\n' % ('X', 'ID', 'Type', 'Group')
        number = len(self._vecX)
        for index in xrange(number):
            w_buf += '%.9f\t%-4d\t%-4d\t%-4d\n' % (self._vecX[index], self._vecID[index],
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

    def get_peak_pos(self, peak_id):
        """

        :param peak_id:
        :return:
        """
        # TODO/NOW - Doc & check
        # assert ...

        # get peak
        for peak_tup in self._peakPosIDList:
            peak_pos_i, peak_id_i = peak_tup
            if peak_id == peak_id_i:
                return peak_pos_i

        return None
    
    def get_peaks(self):
        """ Get all the peaks' tuple
        :return: a list of 2-tuples (peak position and peak ID)
        """
        self._peakPosIDList.sort()
        print '[DB...] get_peaks: return...', self._peakPosIDList
    
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

        return

    def shift_peaks_position(self, peak_id, shift, check):
        """
        Shift one peak or all peaks' position
        :param peak_id: None or integer
        :param shift:
        :param check:
        :return:
        """
        # check
        assert peak_id is None or isinstance(peak_id, int)
        assert isinstance(shift, float)
        assert check is False, 'It is not supported for check is True'

        num_peaks = len(self._peakPosIDList)
        for i_peak in xrange(num_peaks):
            peak_pos_i, peak_id_i = self._peakPosIDList[i_peak]
            if peak_id is None or peak_id == peak_id_i:
                assert isinstance(peak_pos_i+shift, float)
                assert isinstance(peak_id_i, int), \
                    'Peak ID %s must be an integer but not a %s.' % (str(peak_id_i), str(type(peak_id_i)))
                self._peakPosIDList[i_peak] = (peak_pos_i+shift, peak_id_i)

        return

    def update_peak_position(self, peak_id, x, is_displacement):
        """ Update peak position
        :param peak_id:
        :param x: ... ...
        :return:
        """
        # TODO/NOW - doc!
        # check
        assert isinstance(peak_id, int)
        assert isinstance(x, float)
    
        found_peak = False
        for i_peak in xrange(len(self._peakPosIDList)):
            p_id = self._peakPosIDList[i_peak][1]
            if p_id == peak_id:
                # peak is found

                # calculate peak's new position
                if is_displacement:
                    # x is delta x
                    new_peak_pos = self._peakPosIDList[i_peak][0] + x
                else:
                    # x is new peak position
                    new_peak_pos = x

                print '[DB.... update peak %d position] peak ID = %d new position is %f.' % (
                    i_peak, p_id, new_peak_pos)

                self._peakPosIDList[i_peak] = (new_peak_pos, peak_id)
                found_peak = True
                break
        # END-FOR
    
        return found_peak

