# This module contains algorithms to process peaks


class PeakGroupCollection(object):
    """
    A simple version for PeakGroupManagement.
    It is assumed that each time that the user changes setting on peaks or peak group,
    a new PeakGroupCollection will be created
    """
    def __init__(self, starting_group_id):
        """
        Initialization
        :param starting_group_id:
        """
        self._groupPeakListDict = dict()   # key: group ID. value: a lit of 2-tuple (peak ID, peak position)
        self._groupBoundaryDict = dict()   # key: group ID. value: 2-tuple (left boundary, right boundary)

        self._nextGroupID = starting_group_id
        self._currentGroupID = None

        return

    def add_group(self, peak_tuple_list, left_boundary, right_boundary):
        """
        Add peak group
        :param peak_tuple_list:
        :param left_boundary:
        :param right_boundary:
        :return:
        """

        return

    def add_peak(self, peak_id, peak_pos, left_boundary, right_boundary):
        """

        :param peak_id:
        :param peak_pos:
        :param left_boundary:
        :param right_boundary:
        :return:
        """
        # append boundary
        self._groupPeakListDict[self._currentGroupID].append((peak_id, peak_pos))

        # left boundary
        if self._groupBoundaryDict[self._currentGroupID] is None:
            group_left = left_boundary
            group_right = right_boundary
        else:
            group_left, group_right = self._groupBoundaryDict[self._currentGroupID]
            if left_boundary < group_left:
                group_left = left_boundary
            if right_boundary > group_right:
                group_right = right_boundary
        # END-IF

        self._groupBoundaryDict[self._currentGroupID] = (group_left, group_right)

        return

    def get_fit_range(self, group_id):
        """

        :param group_id:
        :return:
        """
        return self._groupBoundaryDict[group_id]

    def get_group_ids(self):
        """

        :return:
        """
        return self._groupPeakListDict.keys()

    def get_peaks(self, group_id):
        """

        :param group_id:
        :return:
        """
        return self._groupPeakListDict[group_id][:]

    def new_group(self):
        """

        :return:
        """
        # get current group ID
        self._currentGroupID = self._nextGroupID
        self._nextGroupID += 1

        # new list
        self._groupBoundaryDict[self._currentGroupID] = None
        self._groupPeakListDict[self._currentGroupID] = list()

        return

    def verify(self):
        """

        :return:
        """

HALF_PEAK_FIT_RANGE_FACTOR = 6.


def calculate_vulcan_resolution(d, delta_d):
    """
    calculate the resolution (i.e., peak's FWHM) of VULCAN.
    :param d:
    :param delta_d:
    :return:
    """
    assert isinstance(delta_d, float) and delta_d > 0
    fwhm = delta_d * d

    return fwhm


def group_peaks_to_fit(peak_tuple_list, resolution, fit_range_factor):
    """
    put a series of peaks into peak group for GSAS refinement
    :param peak_tuple_list: a list of tuples. each tuple contain a float (peak position) and a integer (peak ID)
    :param resolution:
    :param fit_range_factor:
    :return: a dictionary. key is group ID. value is a list of peak ID
    """
    # check validity
    assert isinstance(peak_tuple_list, list), 'Input peak-tuple list must be a list but not %s.' \
                                              '' % peak_tuple_list.__class__.__name__
    assert isinstance(resolution, float), 'Resolution %s must be a float but not %s.' % (str(resolution),
                                                                                         type(resolution))
    assert isinstance(fit_range_factor, float) or isinstance(fit_range_factor, int), \
        'Fit range factor {0} must be a float or integer but not {1}.'.format(fit_range_factor,
                                                                              type(fit_range_factor))

    # sort to reverse
    peak_tuple_list.sort(reverse=True)

    # starting group ID
    # group_id = 1
    # peak_group = {group_id: list()}

    # peak group
    peak_group = PeakGroupCollection(starting_group_id=1)

    # group peaks from the high-d
    right_peak_left_bound = None
    for index, peak_tuple in enumerate(peak_tuple_list):
        # unpack tuple
        assert isinstance(peak_tuple, tuple)
        peak_pos, peak_id = peak_tuple
        peak_fwhm = calculate_vulcan_resolution(peak_pos, delta_d=resolution)
        peak_fit_range = fit_range_factor * peak_fwhm

        # check whether current peak can overlap to the right peak
        if index == 0:
            # right most peak: just add the group 0
            peak_group.new_group()
        elif peak_pos + peak_fit_range < right_peak_left_bound:
            # current peak and right peak do not overlap. start a new group
            peak_group.new_group()
            # group_id += 1
            # peak_group[group_id] = list()
        else:
            # current peak and right peak overlap. do nothing but add
            pass

        # add peak to peak group
        # peak_group[group_id].append(peak_id)
        peak_group.add_peak(peak_id, peak_pos, peak_pos-peak_fit_range, peak_pos+peak_fit_range)

        # calculate the right boundary
        right_peak_left_bound = peak_pos - peak_fit_range
    # END-FOR

    return peak_group
