import os
import sys
from mantid.simpleapi import LoadDiffCal, SaveDiffCal, CloneWorkspace
import argparse

# default calibration and instrument file names
INSTRUMENT_FILE= '/home/wzz/SNS-Home/Projects/VULCAN/nED_Calibration/high_resolution_2/' \
                 'VULCAN_Definition_2017-05-20.xml'
CALIBRATION_FILE = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5'

# Load an up-to-date VULCAN calibration file


def make_7_bank_group_workspace():
    """
    make 6 + 1 bank group workspace
    :return:
    """
    # Clone from original group workspace to modify
    new_group_ws = CloneWorkspace(InputWorkspace='vulcan_orig_group')

    # group 1-18 west and east bank
    num_det_per_bank = 6468 / 6

    for bank_id in range(6):
        start_det_id = num_det_per_bank * bank_id
        stop_det_id = num_det_per_bank * (bank_id + 1)

        # determine group ID
        group_id = bank_id + 1

        # set group ID
        for iws in range(start_det_id, stop_det_id):
            new_group_ws.dataY(iws)[0] = group_id
        # END-FOR (sub_bank_index)
    # END-FOR (bank_id)

    # high angle bank: bank 7
    group_id = 7
    high_angle_bank_start_det_id = 6468
    for ws_index in range(high_angle_bank_start_det_id, len(new_group_ws.getNumberHistograms())):
        new_group_ws.dataY(ws_index)[0] = group_id
    # END-FOR

    return new_group_ws.name()


def make_27_bank_group_workspace():
    """

    :return:
    """
    # Modify groups
    new_group_ws = CloneWorkspace(InputWorkspace='vulcan_orig_group')

    # group 1-18 west and east bank
    num_det_per_bank = 6468 / 6

    for bank_id in range(6):
        start_det_id = num_det_per_bank * bank_id
        stop_det_id = num_det_per_bank * (bank_id + 1)
        for sub_bank_index in range(3):
            sub_start_det_id = start_det_id + sub_bank_index * num_det_per_bank / 3
            if sub_bank_index < 2:
                sub_stop_det_id = sub_start_det_id + num_det_per_bank / 3
            else:
                sub_stop_det_id = stop_det_id
            group_id = bank_id * 3 + sub_bank_index + 1

            # dry run output
            print ('Bank {0}-{1}: {2:03d}   From {3:04d} to {4:04d}  '
                   'Number of detectors: {5}'.format(bank_id, sub_bank_index, group_id, sub_start_det_id,
                                                     sub_stop_det_id - 1, sub_stop_det_id - sub_start_det_id))

            # set group ID
            for iws in range(sub_start_det_id, sub_stop_det_id):
                new_group_ws.dataY(iws)[0] = group_id

        # END-FOR (sub_bank_index)
    # END-FOR (bank_id)

    # high angle bank

    # mask first 1/9 of the high angle detector
    for col in range(3):
        for row in range(3):
            group_id = col * 3 + row + 19
            print ('High angle bank group ID: {0}'.format(group_id))
            # 256 rows in a column.  split as 85, 85, 86
            if row < 2:
                num_sub_rows = 85
            else:
                num_sub_rows = 86
            for col_index in range(col * 24, (col + 1) * 24):
                for row_index in range(row * 85, row * 85 + num_sub_rows):
                    ws_index = 6468 + 256 * col_index + row_index
                    new_group_ws.dataY(ws_index)[0] = group_id
            # END-FOR
        # END-FOR
    # END-FOR

    return new_group_ws.name()


def main(argv):
    """
    main method to create VULCAN groups
    :param argv:
    :return:
    """
    # define arguments
    parser = argparse.ArgumentParser(description='Create VULCAN calibration file with various number of groups')
    parser.add_argument('banks', metavar='B', type=int, help='Number of banks in the calibration file')
    parser.add_argument('output', metavar='O', type=str, help='Name of output file')

    if len(argv) == 0:
        print ('No argument is given.  Try --help')
        return

    args = parser.parse_args()
    # print ('[DB] Input argument: {0}'.format(argparse))
    bank_number = args['banks']
    output_file_name = args['output']

    # load a reference/source calibration file
    if os.path.exists(INSTRUMENT_FILE) is False:
        print ('Instrument file {0} cannot be found.'.format(INSTRUMENT_FILE))
        exit(1)
    if not os.path.exists(CALIBRATION_FILE):
        print ('Calibration file {0} cannot be found.'.format(CALIBRATION_FILE))
    LoadDiffCal(
        InstrumentFilename=INSTRUMENT_FILE,
        Filename=CALIBRATION_FILE,
        WorkspaceName='vulcan_orig')

    # create banks
    if bank_number == 27:
        new_group_ws_name = make_27_bank_group_workspace()
    elif bank_number == 7:
        new_group_ws_name = make_27_bank_group_workspace()
    else:
        print ('{0}-bank grouping/calibration file is not supported.'.format(bank_number))
        exit(1)

    # Save calibration
    SaveDiffCal(CalibrationWorkspace='vulcan_orig_cal',
                GroupingWorkspace=new_group_ws_name,
                MaskWorkspace='vulcan_orig_mask',
                Filename=output_file_name)

    return


if __name__ == '__main__':
    main(sys.argv)