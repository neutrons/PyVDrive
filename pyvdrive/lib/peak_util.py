# This module contains algorithms to process peaks
import numpy  # type: ignore


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


def calculate_peak_integral_intensity(vec_d, vec_y, left_x_index, right_x_index, bkgd_a, bkgd_b):
    """
    calculate a peak's integral intensity by removing a linear background
    A = int f(x) dx = sum f(x) dx
    :param vec_d:
    :param vec_y:
    :param left_x_index:
    :param right_x_index: not included
    :param bkgd_a:
    :param bkgd_b:
    :return:
    """
    # check input:
    assert isinstance(vec_d, numpy.ndarray), 'Vector of D must be a numpy array'
    assert isinstance(vec_y, numpy.ndarray), 'Vector of Y must be a numpy array'
    if len(vec_d) - len(vec_y) > 1 or len(vec_d) - len(vec_y) < 0:
        raise RuntimeError('Vector of D and vector of Y have different size.')
    if left_x_index >= right_x_index:
        raise RuntimeError('Left X index cannot be equal or larger than right X index')
    if left_x_index < 0:
        raise RuntimeError('Left X index cannot be negative')
    if right_x_index > len(vec_d):
        raise RuntimeError('Right X index cannot be over limit of vector of D')

    # use numpy vector to solve the issue
    sub_d = vec_d[left_x_index:right_x_index]
    delta_d = vec_d[left_x_index:right_x_index] - vec_d[left_x_index-1:right_x_index-1]

    sub_y = vec_y[left_x_index:right_x_index]

    # remove background
    # sub_b = numpy.ndarray(shape=sub_y.shape, dtype='double')
    sub_b = sub_d * bkgd_a + bkgd_b

    peak_integral = numpy.sum((sub_y - sub_b) * delta_d)

    # print '[DB...BAT] Integrated Peak Intensity = {0}'.format(peak_integral)

    return peak_integral


def calculate_peak_average_d_space(vec_d, vec_y, left_x_index, right_x_index, bkgd_a, bkgd_b):
    """
    mu = 1/A int x f(x) dx = 1/A sum x * f(x) * delta(x)
    :param vec_d:
    :param vec_y:
    :param left_x_index:
    :param right_x_index:
    :param bkgd_a:
    :param bkgd_b:
    :return: 2-tuple: peak intensity, average d space
    """
    # check input:
    assert isinstance(vec_d, numpy.ndarray), 'Vector of D must be a numpy array'
    assert isinstance(vec_y, numpy.ndarray), 'Vector of Y must be a numpy array'
    if len(vec_d) - len(vec_y) > 1 or len(vec_d) - len(vec_y) < 0:
        raise RuntimeError('Vector of D and vector of Y have different size.')
    if left_x_index >= right_x_index:
        raise RuntimeError('Left X index cannot be equal or larger than right X index')
    if left_x_index < 0:
        raise RuntimeError('Left X index cannot be negative')
    if right_x_index >= len(vec_d):
        raise RuntimeError('Right X index cannot be over limit of vector of D')

    peak_integral = calculate_peak_integral_intensity(vec_d, vec_y, left_x_index, right_x_index,
                                                      bkgd_a, bkgd_b)

    sub_d = vec_d[left_x_index:right_x_index]
    sub_y = vec_y[left_x_index:right_x_index]
    vec_back = sub_d * bkgd_a + bkgd_b
    vec_dx = vec_d[left_x_index:right_x_index] - vec_d[left_x_index-1:right_x_index-1]

    mu = numpy.sum(sub_d * (sub_y - vec_back) * vec_dx) / peak_integral

    # print '[DB...BAT] Peak average d = {0}'.format(mu)

    return peak_integral, mu


def calculate_peak_variance(vec_d, vec_y, left_x_index, right_x_index, bkgd_a, bkgd_b):
    """
    var = int (x-mu)**2 f(x) dx = sum (x-mu)**2 * f(x) * dx
    :param vec_d:
    :param vec_y:
    :param left_x_index:
    :param right_x_index:
    :param bkgd_a:
    :param bkgd_b:
    :return: 3-tuple: peak integral, average d-space, variance
    """
    # check input:
    assert isinstance(vec_d, numpy.ndarray), 'Vector of D must be a numpy array'
    assert isinstance(vec_y, numpy.ndarray), 'Vector of Y must be a numpy array'
    if len(vec_d) - len(vec_y) > 1 or len(vec_d) - len(vec_y) < 0:
        raise RuntimeError('Vector of D and vector of Y have different size.')
    if left_x_index >= right_x_index:
        raise ValueError('Left X index cannot be equal or larger than right X index')
    if left_x_index < 0:
        raise ValueError('Left X index cannot be negative')
    if right_x_index >= len(vec_d):
        raise ValueError('Right X index cannot be over limit of vector of D')

    # calculate peak integral and average d-spacing
    peak_integral, average_d_space = calculate_peak_average_d_space(vec_d, vec_y, left_x_index, right_x_index,
                                                                    bkgd_a, bkgd_b)

    # get sub vector for calculation
    sub_d = vec_d[left_x_index:right_x_index]
    sub_y = vec_y[left_x_index:right_x_index]
    vec_dx = vec_d[left_x_index:right_x_index] - vec_d[left_x_index-1:right_x_index-1]

    # calculate variance
    variance = numpy.sum(numpy.power(sub_d - average_d_space, 2) * sub_y * vec_dx)

    return peak_integral, average_d_space, variance


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


def estimate_background(vec_d, vec_y, min_x_index, max_x_index):
    """Estimate background

    by assuming that the left and right boundaries have enough distance to peak
    :param vec_d:
    :param vec_y:
    :param min_x_index:
    :param max_x_index:
    :return:
    """
    # check inputs' types
    assert isinstance(vec_d, numpy.ndarray), 'Vector of dSpacing must be numpy.ndarray'
    assert isinstance(vec_y, numpy.ndarray), 'Vector of Y must be numpy.ndarray'

    # form the vector to fit with linear background
    list_x = list()
    list_y = list()
    for index in range(-1, 2):
        x_index = min_x_index + index
        if x_index > 0:
            list_x.append(vec_d[x_index])
            list_y.append(vec_y[x_index])
    # END-FOR
    for index in range(-1, 2):
        x_index = max_x_index + index
        if x_index < len(vec_d)-1:
            list_x.append(vec_d[x_index])
            list_y.append(vec_y[x_index])
    # END-FOR

    d_fit_vec = numpy.array(list_x)
    y_fit_vec = numpy.array(list_y)

    # fit for linear background, i.e, order = 1
    vec_bkgd = numpy.polyfit(d_fit_vec, y_fit_vec, 1)
    bkgd_a = vec_bkgd[0]
    bkgd_b = vec_bkgd[1]

    return bkgd_a, bkgd_b
