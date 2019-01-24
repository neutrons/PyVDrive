#!/bin/python
# It is to evaluate the calibration result
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
                                                meta_data_only=False)   # max_time=300)

    # load calibration file
    base_cal_name = os.path.basename(input_arg_dict['calib_file'].split('.')[0])
    outputs, offset_ws = mantid_helper.load_calibration_file(calib_file_name=input_arg_dict['calib_file'],
                                                             output_name=base_cal_name,
                                                             ref_ws_name=event_ws_name)
    print ('[DB...BAT] Outputs: {}'.format(outputs))
    grouping_ws = outputs.OutputGroupingWorkspace
    calib_ws = outputs.OutputCalWorkspace
    mask_ws = outputs.OutputMaskWorkspace

    # export the
    from pyvdrive.lib import mantid_reduction

    # mask workspaces
    mantid_helper.mask_workspace(event_ws_name, mask_ws.name())

    message = mantid_reduction.align_and_focus_event_ws(event_ws_name=event_ws_name,
                                                        output_ws_name=event_ws_name,
                                                        binning_params='-0.001',
                                                        diff_cal_ws_name=str(calib_ws),
                                                        grouping_ws_name=str(grouping_ws),
                                                        reduction_params_dict=dict(),
                                                        convert_to_matrix=False)
    focus_ws_name = event_ws_name

    if 'output' in input_arg_dict:
        file_name = input_arg_dict['output']
    else:
        file_name = '{}_{}'.format(event_ws_name, base_cal_name)

    # output:
    # 2 sets of banks dspacing
    mantid_helper.mtd_convert_units(focus_ws_name, 'dSpacing')
    out_ws_name = mantid_helper.rebin(focus_ws_name, '0.3, -0.001, 5.0', output_ws_name=focus_ws_name+'temp',
                                      preserve=False)
    SaveNexusProcessed(InputWorkspace=out_ws_name, Filename=file_name + '_d_low.nxs',
                       Title='{} calibrated by {}'.format(event_nexus_name, input_arg_dict['calib_file']))
    out_ws_name = mantid_helper.rebin(focus_ws_name, '0.3, -0.0003, 5.0', output_ws_name=focus_ws_name+'temp',
                                      preserve=False)
    SaveNexusProcessed(InputWorkspace=out_ws_name, Filename=file_name + '_d_high.nxs',
                       Title='{} calibrated by {}'.format(event_nexus_name, input_arg_dict['calib_file']))

    # 2 sets of banks TOF
    mantid_helper.mtd_convert_units(focus_ws_name, 'TOF')
    out_ws_name = mantid_helper.rebin(focus_ws_name, '2000., -0.001, 70000', output_ws_name=focus_ws_name+'temp',
                                      preserve=False)
    SaveNexusProcessed(InputWorkspace=out_ws_name, Filename=file_name + '_tof_low.nxs',
                       Title='{} calibrated by {}'.format(event_nexus_name, input_arg_dict['calib_file']))
    out_ws_name = mantid_helper.rebin(focus_ws_name, '2000., -0.0003, 70000', output_ws_name=focus_ws_name+'temp',
                                      preserve=False)
    SaveNexusProcessed(InputWorkspace=out_ws_name, Filename=file_name + '_tof_high.nxs',
                       Title='{} calibrated by {}'.format(event_nexus_name, input_arg_dict['calib_file']))

    GeneratePythonScript(InputWorkspace=event_ws_name, Filename=file_name + '_focus.py')

    return


if __name__ == '__main__':
    main(sys.argv)
