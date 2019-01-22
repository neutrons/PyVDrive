#!/bin/python
# It is to evaluate the calibration result
import sys
import os
from mantid.simpleapi import Load, LoadDiffCal, SaveNexusProcessed
from mantid.api import AnalysisDataService as mtd
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import lib_cross_correlation


# TODO - 20180910 - Implement!
def analysize_mask(event_ws, mask_ws, output_dir):
    """ analyze mask workspace
    """
    assert mask_ws.getNumberHistograms() == event_ws.getNumberHistograms(), 'blabla'

    for ws_index in range(mask_ws.getNumberHistograms()):
        if mask_ws.readY(ws_index)[0] < 0.1:
            continue

        # analyze masking information
        if event_ws.getSpectrum(ws_index).getNumberEvents() == 0:
            case_i = 1  # no event
        elif event_ws.getSpectrum:
            pass

    # 2. For each bank, sort the masked workspace from highest ban

    return None, None, None


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
        if items[0] == '--ipts':
            arg_dict['ipts'] = int(items[1])
        elif items[0] == '--run':
            arg_dict['run'] = int(items[1])
        elif items[0] == '--nexus':
            arg_dict['event_nexus'] = str(items[1])
        elif items[0] == '--calib':
            arg_dict['calib_file'] = str(items[1])
        elif items[0] == '--output':
            arg_dict['output'] = str(items[1])
        else:
            print ('Argument {} is not supported'.format(items[0]))
    # END-FOR

    return arg_dict


def print_help(script_name):
    """
    print out help information
    :return:
    """
    print ('Format: {} --ipts=xxx --run=xxx --nexus=blabla.nxs --calib=balbal.h5'.format(script_name))

    return


def main(argv):
    """
    main method
    :param argv:
    :return:
    """
    if len(argv) == 1:
        print ('Help: {} --help'.format(argv[0]))
        sys.exit(0)

    # help
    if '--help' in argv:
        print_help(script_name=argv[0])
        sys.exit(1)
    else:
        # parse input arguments
        input_arg_dict = parse_inputs(argv[1:])

    # load event data
    if 'event_nexus' in input_arg_dict:
        event_nexus_name = input_arg_dict['event_nexus']
    else:
        ipts_number = input_arg_dict['ipts']
        run_number = input_arg_dict['run']
        event_nexus_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)
    event_ws_name = os.path.basename(event_nexus_name).split('.')[0] + '_event'
    status, event_ws = mantid_helper.load_nexus(data_file_name=event_nexus_name,
                                                output_ws_name=event_ws_name,
                                                meta_data_only=False,
                                                max_time=300)

    # load calibration file
    base_cal_name = os.path.basename(input_arg_dict['calib_file'].split('.')[0])
    outputs = mantid_helper.load_calibration_file(calib_file_name=input_arg_dict['calib_file'],
                                                  output_name=base_cal_name,
                                                  ref_ws_name=event_ws_name)
    print ('[DB...BAT] Outputs: {}'.format(outputs))
    grouping_ws = outputs.OutputGroupingWorkspace
    calib_ws = outputs.OutputCalWorkspace
    mask_ws = outputs.OutputMaskWorkspace

    # analyze the masking
    zero_count_mask_ws, low_count_mask_ws, regular_count_mask_ws = analysize_mask(event_ws, mask_ws,
                                                                                  output_dir=os.getcwd())

    # export the
    from pyvdrive.lib import mantid_reduction
    focus_ws_name = mantid_reduction.align_and_focus_event_ws(event_ws_name=event_ws_name,
                                                              output_ws_name=event_ws_name,
                                                              binning_params='-0.001',
                                                              diff_cal_ws_name=calib_ws,
                                                              grouping_ws_name=grouping_ws,
                                                              reduction_params_dict=dict(),
                                                              convert_to_matrix=False)

    if 'output' in input_arg_dict:
        SaveNexusProcessed(InputWorkspace=focus_ws_name, Filename=input_arg_dict['output'],
                           Title='{} calibrated by {}'.format(str(event_ws), input_arg_dict['calib_file']))

    # from matplotlib import pyplot as plt
    #
    # focus_ws = mtd[focus_ws_name]
    #
    # for bank_id in range(3):
    #     vec_x = focus_ws.readX(bank_id)
    #     vec_y = focus_ws.readY(bank_id)
    #     plt.plot(vec_x[:len(vec_y)], vec_y, label='bank {}'.format(bank_id+1))
    # plt.legend()
    # plt.show()

    print ('WARNING!!! Event file is loaded for 300 seconds for test purpose')

if __name__ == '__main__':
    main(sys.argv)
