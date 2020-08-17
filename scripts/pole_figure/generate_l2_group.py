# Generate L2 group
# This is a script that is supposed to be used in MantidPlot environment
"""
# FACTS
Bank 1: L2 in (2.00000155478, 2.04122819734)
Bank 2: L2 in (2.0000015625, 2.04122818421)
Bank 3: L2 in (2.00000155478, 2.04122819734)
Bank 4: L2 in (2.00000155478, 2.04122819734)
Bank 5: L2 in (2.0000015625, 2.04122818421)
Bank 6: L2 in (2.00000155478, 2.04122819734)
Bank 7: L2 in (2.00000164242, 2.04567857167)
"""


def create_l2_group(vulcan_ws, bank_range_dict, bank_id, l2_resolution, group_ws, start_group_number):
    """  create L2 group for 1 banks
    :param vulcan_ws:
    :param bank_range_dict:
    :param bank_id:
    :param l2_resolution_dict:
    :param group_ws:
    :param start_group_number:
    :return:
    """
    sample_pos = vulcan_ws.getInstrument().getSample().getPos()
    l2_list = list()
    start_iws, stop_iws = bank_range_dict[bank_id]
    for iws in range(start_iws, stop_iws):
        det_pos_i = vulcan_ws.getDetector(iws).getPos()
        l2_i = sample_pos.distance(det_pos_i)
        l2_list.append((l2_i, iws))
    # END-FOR

    l2_list.sort()
    print('Bank {0}: L2 in ({1}, {2}).  Resolution = {3}'.format(
        bank_id, l2_list[0][0], l2_list[-1][0], l2_resolution))

    l2_min = l2_list[0][0]
    l2_max = l2_list[-1][0]
    # Now set up the group work space
    max_grp_number = start_group_number
    for l2_i, iws_i in l2_list:
        # determine group ID
        group_i = int((l2_i - l2_min) / l2_resolution) + start_group_number
        group_ws.dataY(iws_i)[0] = group_i
        if group_i > max_grp_number:
            max_grp_number = group_i

    return group_ws, max_grp_number


def create_7_banks_info():
    """
    7 bank workspace index range: [lower, upper)
    :return:
    """
    # constants
    ninety_degree_panel_size = 3234/3

    bank_range_dict = dict()
    for bank_id in range(1, 7):
        bank_range_dict[bank_id] = (
            bank_id-1) * ninety_degree_panel_size, bank_id * ninety_degree_panel_size

    bank_range_dict[7] = 6468, 24900

    return bank_range_dict


def scan_l2_range(vulcan_ws, bank_range_dict):
    """
    get idea about the L2 range for each bank
    :param vulcan_ws:
    :param bank_range_dict:
    :return:
    """
    sample_pos = vulcan_ws.getInstrument().getSample().getPos()
    for bank_id in sorted(bank_range_dict.keys()):
        l2_list = list()
        start_iws, stop_iws = bank_range_dict[bank_id]
        for iws in range(start_iws, stop_iws):
            det_pos_i = vulcan_ws.getDetector(iws).getPos()
            l2_i = sample_pos.distance(det_pos_i)
            l2_list.append(l2_i)
        # END-FOR

        l2_list.sort()
        print('Bank {0}: L2 in ({1}, {2})'.format(
            bank_id, l2_list[0], l2_list[-1]))

    return


# Main:
workspace = mtd['ws']
group_ws = mtd['vulcan_group']

bank_spec_range_dict = create_7_banks_info()

# create for 1 bank as a test
start_group_number = 1
for bank_id in range(1, 8):
    group_ws, stop_group_number = create_l2_group(workspace, bank_spec_range_dict,
                                                  bank_id, 0.004, group_ws, start_group_number)
    print('Bank {0} range from group {1} to {2}'.format(
        bank_id, start_group_number, stop_group_number))
    start_group_number = stop_group_number + 1
