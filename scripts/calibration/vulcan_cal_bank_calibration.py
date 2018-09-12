# Generate VULCAN's calibration from an already binned workspace in a NeXus file
import os
import sys
import math
import numpy
import lib_cross_correlation as ccl

# sys.path.insert(1, '/SNS/users/wzz/Mantid_Project/vulcan-build/bin/')




def plot_difc_diff(idf_difc_vec, cal_difc_vec, start_index, mask_ws):
    """

    :param mask:
    :return:
    """
    # TODO - 20180911 - how to remove elements in numpy array
    # difference between IDF and calibrated DIFC
    difc_diff_vec = idf_difc_vec - cal_difc_vec



    return


# TODO - 20180911 - move to lib and it is for 3 banks... rename!
def analyze_result():
    """
    get a cost array for plotting in MantidPlot???!
    """
    # WEST
    calculate_model('cc_vulcan_diamond_west', 1755, 'offset_vulcan_diamond_west_FitResult')
    # plot cost list
    cost_list, west_bad = evaluate_cc_quality('cc_vulcan_diamond_west', 'offset_vulcan_diamond_west_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='West_Cost')
    
    
    # East
    # plot cost list
    cost_list, east_bad = evaluate_cc_quality('cc_vulcan_diamond_east', 'offset_vulcan_diamond_east_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    print (cost_array)
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='East_Cost')
    
    # HIGH ANGLE
    calculate_model('cc_vulcan_diamond_high_angle', 12200, 'offset_vulcan_diamond_high_angle_FitResult')
    # plot cost list
    cost_list, high_angle_bad = evaluate_cc_quality('cc_vulcan_diamond_high_angle', 'offset_vulcan_diamond_high_angle_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='HighAngle_Cost')


# Default diamond runs
Diamond_Runs = {'2017-06-01': '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
                              'VULCAN_150178_HighResolution_Diamond.nxs',
                '2018-08-01': '/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180910/'
                              'raw_dspace_hitogram.nxs'}


def parse_inputs(arg_list):
    """

    :param arg_list:
    :return:
    """
    arg_dict = dict()

    for arg_i in arg_list:
        print ('arg: {}'.format(arg_i))
        items = arg_i.split('=')
        arg_name = str(items[0]).strip()
        arg_str = str(items[1]).strip()

        if arg_name == '--diamond':
            arg_dict['diamond_file'] = arg_str
        else:
            print ('Error: Unknown argument {}'.format(arg_name))
    # END-FOR

    return arg_dict


def main(argv):
    """
    main argument
    :param argv:
    :return:
    """
    if False:
        # TODO FIXME - This is a debugging solution
        dates = sorted(Diamond_Runs.keys())
        nxs_file_name = Diamond_Runs[dates[-1]]

    input_arg_dict = parse_inputs(argv[1:])

    # decide to load or not and thus group workspace
    nxs_file_name = input_arg_dict['diamond_file']
    diamond_ws_name, group_ws_name = ccl.initialize_calibration(nxs_file_name, False)

    # do cross correlation: 2 fit
    ccl.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')

    # check the difference between DIFCs
    check_correct_difcs(ws_name='vulcan_diamond')

    # save calibration file
    for num_banks in [3, 7, 27]:
        export_diff_cal_h5(ref_ws_name='vulcan_diamond', offset_ws=xx, mask_ws=yy, num_groups=num_banks)

    # save difc file
    if 'difc' in input_arg_dict:
        ccl.export_difc(offset_ws=xx, file_name=input_arg_dict['difc'])

    # plot_difc_diff(mask=mask_ws)


if __name__ == '__main__':
    # main
    main(sys.argv)


