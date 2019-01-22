# This is the second round of cross-correlation in order to
# cross-correlate/align 3 already-focused banks (west, east and high angle) to the same peak positions
import sys
import os
import pyvdrive.lib.lib_cross_correlation as lib
from pyvdrive.lib import mantid_helper


# (hard coded) diamond peak position in d-Spacing
Diamond_Peaks_1 = 1.2614
peakpos2 = 1.2614
peakpos3 = 1.07577




def cross_instrument_calibration():
    """
    Main algorithm to do cross-correlation among different banks of VULCAN.
    This is the second round calibration using the data file
    1. calibrated by previous calibration file based on inner bank cross correlation
    2. diffraction focused
    For the instrument with west, east and high angle banks, the input file shall be a 3 bank
    :return:
    """
    CrossCorrelate(InputWorkspace='vulcan_diamond_3bank', OutputWorkspace='cc_vulcan_diamond_3bank', ReferenceSpectra=1, WorkspaceIndexMax=2, XMin=1.0649999999999999, XMax=1.083)
    GetDetectorOffsets(InputWorkspace='cc_vulcan_diamond_3bank', Step=0.00029999999999999997, DReference=1.0757699999999999, XMin=-20, XMax=20, OutputWorkspace='zz_test_3bank', FitEachPeakTwice=True, PeakFitResultTableWorkspace='ddd', OutputFitResult=True, MinimumPeakHeight=1)


def apply_second_cc(calib_ws_dict, difc_shift_dict):
    """
    apply the result from the second round cross correlation
    (apply the result of second round cross correlation)
    :param calib_ws_dict:
    :param difc_shift_dict:
    :return:
    """
    # offset_ws = mtd['vulcan_foc_cal_offsets']
    # shift_offset_ws  = CloneWorkspace(InputWorkspace=offset_ws, OutputWorkspace='offset_test')
    # for iws in range(0, 3234):
    #     shift_offset_ws.dataY(iws)[0] *= 1+1.0938E-4
    # for iws in range(6468, 24900):
    #     shift_offset_ws.dataY(iws)[0] *= 1 - 1.3423E-4

    offset_ws_name = str(calib_ws_dict['offset'])
    shifted_offset_name = offset_ws_name + '_cc'
    shift_offset_ws = CloneWorkspace(InputWorkspace=offset_ws_name, OutputWorkspace=shifted_offset_name)

    # west bank
    for iws in range(0, 3234):
        shift_offset_ws.dataY(iws)[0] *= 1 + difc_shift_dict['west']
    # high angle bank
    for iws in range(6468, 24900):
        shift_offset_ws.dataY(iws)[0] *= 1 - difc_shift_dict['high angle']

    calib_ws_dict['offset'] = shift_offset_ws

    return calib_ws_dict


def parse_inputs(arg_list):
    """
    parse input arguements
    :param arg_list:
    :return:
    """
    arg_dict = dict()

    # define default
    arg_dict['testmode'] = False

    # TODO - NIGHT - Add input to select banks to calibrate
    for arg_i in arg_list:
        items = arg_i.split('=')
        arg_name = items[0]
        if arg_name == '--focus':
            arg_dict['num_banks'] = int(items[1])
        elif arg_name == '--grouping':
            arg_dict['grouping'] = str(items[1])
        elif arg_name == '--input':
            arg_dict['input'] = str(items[1])
        elif arg_name == '--nexus':
            arg_dict['nexus'] = str(items[1])
        elif arg_name == '--output':
            arg_dict['output'] = str(items[1])
        elif arg_name == '--ref':
            arg_dict['ref_cal'] = str(items[1])
        elif arg_name == '--test':
            arg_dict['testmode'] = int(items[1]) == 1
        else:
            print ('Argument {} is not supported'.format(arg_name))
    # END-FOR

    return arg_dict


def main(argv):
    """
    main method
    :param argv:
    :return:
    """
    def prompt_message(input_arg):
        print ('Cross correlate upon calibrated and focus diamond data.')
        print ('> {} --nexus=xxx.nxs --input=zz.h5 --output=yyy --ref=zzz.nxs'.format(input_arg[0]))
        print ('> Or')
        print ('> {} --nexus=xxx.nxs --focus=3 --grouping=zz.nxs --output=yyy --ref=zzz.nxs'.format(input_arg[0]))
        print ('  --nexus: event nexus file name for diamond')
        print ('  --focus: integer for how many banks to focus to')
        print ('  --grouping: name of file saved from detectors grouping workspace.  --focus and --group are a pair')
        print ('  --input: an existing calibration file serving as the start.  --focus can be ignored')
        print ('  --output: output diff-cal file name in .h5 format')
        print ('  --ref: reference workspace with set of spectra')
        print ('  --test: only load the first 300 seconds for testing purpose')
        print ('\n{} will generate \n\t1. calibration files with 1-fit\n\t2. calibration files with 2-fit\n'
               '\t3. an ascii file with number of events per spectrum for further analysis')
        print ('\nLatest hint:\n')
        print ('--nexus=??? --focus=3 --grouping=/SNS/VULCAN/shared/CALIBRATION/vulcan_prex_3bank_group.xml')
        return
    # END

    if len(argv) < 2:
        prompt_message(argv)
        sys.exit(0)

    input_args = parse_inputs(argv[1:])

    # load data
    diamond_ws_name = os.path.basename(input_args['nexus']).split('.')[0] + '_diamond'
    if input_args['testmode']:
        mantid_helper.load_nexus(data_file_name=input_args['nexus'],
                                 output_ws_name=diamond_ws_name,
                                 meta_data_only=False,
                                 max_time=300)
        print ('[WARNING] Testing mode only have first 300 seconds data loaded!')
    else:
        mantid_helper.load_nexus(data_file_name=input_args['nexus'],
                                 output_ws_name=diamond_ws_name,
                                 meta_data_only=False)
    mantid_helper.mtd_convert_units(diamond_ws_name, 'dSpacing')

    # load grouping workspace
    if 'grouping' in input_args:
        raise RuntimeError('Mantid does not support 3-bank nED geometry yet')
        group_ws_name = input_args['grouping']
        group_ws_name = os.path.basename(grouping_file).split('.')[0]
        mantid_helper.load_grouping_file(grouping_file_name=grouping_file,
                                         grouping_ws_name=group_ws_name)
    elif 'ref_cal' in input_args:
        # using reference calibration file for grouping workspace
        ref_ws_name = os.path.basename(input_args['ref_cal']).split('.')[0]
        outputs = mantid_helper.load_calibration_file(input_args['ref_cal'], ref_ws_name, diamond_ws_name,
                                                      load_cal=False)
        group_ws = outputs.OutputGroupingWorkspace
        group_ws_name = group_ws.name()
        print (outputs)
    else:
        # not specified
        raise RuntimeError('No detector grouping is specified')

    # do cross correlation: 1 fit
    if input_args['num_banks'] == 3:
        results = lib.cross_correlate_vulcan_data_3banks(diamond_ws_name, group_ws_name, fit_time=1,
                                                         calib_flag={'west': False, 'east': False, 'high angle': True},
                                                         flag='1fit')
        offset_ws_dict, mask_ws_dict = results
        if ref_ws_name is None:
            # no reference offsetworkspace
            lib.merge_save_detector_calibration(ref_calib_ws=outputs.OutputCalWorkspace,
                                                ref_grouping_ws=group_ws_name, ref_mask_ws=outputs.OutputMaskWorkspace,
                                                offset_ws_dict=offset_ws_dict, mask_ws_dict=mask_ws_name,
                                                num_banks=3, output_ws_name='VULCAN_1ft', flag='1f')
        else:
            # with regular reference workspace
            lib.merge_save_mask_detector(ref_offset_ws=ref_ws_name, ref_calib_ws=outputs.OutputCalWorkspace,
                                         ref_grouping_ws=group_ws_name, ref_mask_ws=outputs.OutputMaskWorkspace,
                                         offset_ws_dict=offset_ws_dict, mask_ws_dict=mask_ws_name,
                                         num_banks=3, output_ws_name='VULCAN_1ft', flag='1f')


        # check the difference between DIFCs
        lib.check_correct_difcs_3banks(diamond_ws_name, difc_1ft_cal_name, mask_ws_name)

    # do cross correlation: 2 fit
    if input_args['num_banks'] == 3:
        results = lib.cross_correlate_vulcan_data_3banks(diamond_ws_name, group_ws_name, fit_time=2,
                                                         calib_flag={'west': False, 'east': False, 'high angle': True},
                                                         flag='2fit')
        difc_2fit_cal_name = results[2][0]
        mask_ws_name = results[2][1]

        # do cross correlation: 1 fit
        lib.check_correct_difcs_3banks(diamond_ws_name, difc_2fit_cal_name, mask_ws_name)

    # TODO - NIGHT - Implement instrument wise cross correlation after analysis is finished
    #
    # # cross correlation on the aligned and reduced data
    # # shift_dict = cross_instrument_calibration()
    # shift_dict = lib.instrument_wide_cross_correlation()
    #
    # # load the calibration file to be modified from
    # workspace_dict = lib.load_calibration_file(input_args['input'], input_args['ref'])
    #
    # # modify the calibration file
    # workspace_dict = apply_second_cc(workspace_dict, shift_dict)
    #
    # # save
    # lib.combine_save_calibration(workspace_dict)

    if input_args['testmode']:
        print ('[WARNING] Testing mode only have first 300 seconds data loaded!')

    return


if __name__ == '__main__':
    main(sys.argv)

