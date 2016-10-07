# This module contains algorithms to process peaks


HALF_PEAK_FIT_RANGE_FACTOR = 3.


def calculate_vulcan_resolution(d):
    """
    calculate the resolution (i.e., peak's FWHM) of VULCAN.
    :param d:
    :return:
    """
    fwhm = d * 0.0003

    return fwhm

def group_peaks(peak_tuple_list):
    """
    put a series of peaks into peak group for GSAS refinement
    :param peak_tuple_list: a list of tuples. each tuple contain a float (peak position) and a integer (peak ID)
    :return: a dictionary. key is group ID. value is a list of peak ID
    """
    # check validity
    assert isinstance(peak_tuple_list, list), 'Input peak-tuple list must be a list but not %s.' \
                                              '' % peak_tuple_list.__class__.__name__

    # sort to reverse
    peak_tuple_list.sort(reverse=True)

    # starting group ID
    group_id = 1
    peak_group = {group_id:list()}

    # group peaks from the high-d
    right_peak_left_bound = None
    for index, peak_tuple in enumerate(peak_tuple_list):
        # unpack tuple
        assert isinstance(peak_tuple, tuple)
        peak_pos, peak_id = peak_tuple
        peak_fwhm = calculate_vulcan_resolution(peak_pos)

        # check whether current peak can overlap to the right peak
        if index == 0:
            # right most peak: just add the group 0
            pass
        elif peak_pos + HALF_PEAK_FIT_RANGE_FACTOR * peak_fwhm < right_peak_left_bound:
            # current peak and right peak do not overlap. start a new group
            group_id += 1
            peak_group[group_id] = list()
        else:
            # current peak and right peak overlap. do nothing but add
            pass

        # add peak to peak group
        peak_group[group_id].append(peak_id)

        # calculate the right boundary
        right_peak_left_bound = peak_pos - HALF_PEAK_FIT_RANGE_FACTOR * peak_fwhm
    # END-FOR

    return peak_group
