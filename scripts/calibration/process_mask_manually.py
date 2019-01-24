#!/bin/python
# It is to process mask manually with .h5 calibration file
import sys
import os
from mantid.simpleapi import LoadDiffCal, SaveNexusProcessed, GeneratePythonScript
from mantid.api import AnalysisDataService as mtd
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import lib_cross_correlation


def parse_inputs(argv):
    """
    parse inputs
    :param argv:
    :return:
    """
    arg_dict = dict()

    # go through each term
    for sub_arg in argv:
        items = sub_arg.split('=')
        if items[0] == '--nexus':
            arg_dict['nexus'] = int(items[1])
        elif items[0] == '--h5':
            arg_dict['calib_file'] = str(items[1])
        elif items[0] == '--output':
            arg_dict['output'] = str(items[1])
        elif items[0] == '--mask':
            arg_dict['mask_file'] = str(items[1])
        else:
            print ('Argument {} is not supported'.format(items[0]))
    # END-FOR

    return arg_dict


def main(argv):
    """

    :param argv:
    :return:
    """

    print ('Example: --nexus=small_nexus_file  --h5=source.h5  --mask=mask_ws_indexes.txt  --output=target.h5')

    input_args = parse_inputs(argv)

    # Load mask
    mask_file_name = input_args['mask_file']
    masked_ws_indexes = parse_masked_ws_indexes[mask_file_name]

    # Load data for a reference workspace with instrument
    nexus_file_name = input_args['nexus']
    data_ws_name = os.path.basename(nexus_file_name).split('.')[0]
    mantid_helper.load_nexus(nexus_file_name, output_ws_name=data_ws_name, meta_data_only=False,
                             max_time=60)

    # load calibration
    cal_base_name = 'VULCAN'
    cal_file_name = input_args['calib_file']
    outputs, offset_ws_name = mantid_helper.load_calibration_file(calib_file_name=cal_file_name,
                                                                  output_name=cal_base_name,
                                                                  ref_ws_name=data_ws_name, load_cal=True)

    # mask workspace
    mask_ws_name = outputs.OutputMaskWorkspace

    from pyvdrive.lib import mantid_mask
    mantid_mask.mask_detectors(mask_ws_name, ws_index_list=masked_ws_indexes)

    return
