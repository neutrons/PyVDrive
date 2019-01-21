#!/bin/python
# It is to evaluate the calibration result
import sys
import os
from mantid.simpleapi import Load, LoadDiffCal, SaveNexusProcessed
from mantid.api import AnalysisDataService as mtd

import lib_cross_correlation as lib





def analysize_mask():
    """
    """
    # TODO - 20180910 - Implement!

    # 1. Load original event workspace

    # 2. For each bank, sort the masked workspace from highest ban


def align_detectors():

    AlignDetectors(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                   CalibrationWorkspace='vulcan_cal')

def diffraction_focus():

    DiffractionFocussing(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                         GroupingWorkspace='vulcan_group')

    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')

    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_3bank')

    EditInstrumentGeometry(Workspace='vulcan_diamond_3bank', PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2',
                           Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3',
                           InstrumentName='vulcan_3bank')


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
    # TODO - NIGHT - Merge to vulcan_cal_instrument_calibration
    raise NotImplementedError('This will be moved to ')

    if len(argv) == 1:
        print ('Help: {} --help'.format(argv[0]))
        sys.exit(0)

    # help
    if '--help' in argv:
        print_help(script_name=argv[0])
        sys.exit(1)

    # parse input arguments
    input_arg_dict = parse_inputs(argv[1:])

    # load event data
    if 'event_nexus' in input_arg_dict:
        event_ws = load_raw_nexus(file_name=input_arg_dict['event_nexus'], ipts=None, run_number=None)
    else:
        ipts_number = input_arg_dict['ipts']
        run_number = input_arg_dict['run']
        event_ws = lib.load_raw_nexus(file_name=None, ipts=ipts_number, run_number=run_number)
    # END-IF

    # load calibration file
    calib_ws, mask_ws, group_ws = lib.load_calibration_file(ref_ws_name=event_ws, 
                                                            calib_file_name=input_arg_dict['calib_file'],
                                                            calib_ws_base_name='vulcan')

    # analyze the masking
    # zero_count_mask_ws, low_count_mask_ws, regular_count_mask_ws =\
    #     analysize_mask(event_ws, mask_ws, output_dir=os.getcwd())

    # export the
    focus_ws_name = lib.align_focus_event_ws(event_ws_name=str(event_ws), calib_ws_name=calib_ws,
            group_ws_name=group_ws)
    if 'output' in input_arg_dict:
        SaveNexusProcessed(InputWorkspace=focus_ws_name, Filename=input_arg_dict['output'],
                           Title='{} calibrated by {}'.format(str(event_ws), input_arg_dict['calib_file']))

    from matplotlib import pyplot as plt

    focus_ws = mtd[focus_ws_name]

    for bank_id in range(3):
        vec_x = focus_ws.readX(bank_id)
        vec_y = focus_ws.readY(bank_id)
        plt.plot(vec_x[:len(vec_y)], vec_y, label='bank {}'.format(bank_id+1))
    plt.legend()
    plt.show()

if __name__ == '__main__':
    main(sys.argv)
