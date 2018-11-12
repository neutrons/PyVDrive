# This is the second round of cross-correlation in order to
# cross-correlate/align 3 already-focused banks (west, east and high angle) to the same peak positions
import sys
import lib_cross_correlation as lib


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

    for arg_i in arg_list:
        items = arg_i.split('=')
        arg_name = items[0]
        if arg_name == '--focus':
            arg_dict['nexus'] = str(items[1])
        elif arg_name == '--output':
            arg_dict['output'] = str(items[1])
        elif arg_name == '--input':
            arg_dict['input'] = str(items[1])
        elif arg_name == '--ref':
            arg_dict['ref'] = str(items[1])
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
    if len(argv) < 2:
        print ('Cross correlate upon calibrated and focus diamond data.')
        print ('> {} --focus=xxx.nxs --input=zz.h --output=yyy --ref=zzz.nxs'.format(argv[0]))
        print ('  --focus: focused 3 bank diamond data in NeXus file format')
        print ('  --output: output diff-cal file name in .h5 format')
        print ('  --ref: reference workspace with set of spectra')
        sys.exit(0)

    input_args = parse_inputs(argv[1:])

    # load data
    lib.load_processed_nexus(input_args['nexus'], 'vulcan_diamond_3bank')

    # cross correlation on the aligned and reduced data
    shift_dict = cross_instrument_calibration()

    # load the calibration file to be modified from
    workspace_dict = lib.load_calibration_file(input_args['input'], input_args['ref'])

    # modify the calibration file
    workspace_dict = apply_second_cc(workspace_dict, shift_dict)

    # save
    lib.save_calibration(workspace_dict)

    return


if __name__ == '__main__':

    calib_file_name = '/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/vulcan_2fit.h5'
    
        
    


