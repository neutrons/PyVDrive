# Generate VULCAN's calibration from an already binned workspace in a NeXus file
import os
import sys
import math
import numpy
import cross_correlation_lib as ccl

# sys.path.insert(1, '/SNS/users/wzz/Mantid_Project/vulcan-build/bin/')


# 
# TODO - 20180911 - move to lib and it is for 3 banks... rename!
def check_correct_difcs(ws_name):
    """
    check and correct DIFCs if necessary: it is for 3 banks
    :param ws_name:
    :return:
    """
    # west bank
    ws = mtd['vulcan_diamond']
    cal_table_ws = mtd['vulcan_diamond_2fit_cal']
    difc_col_index = 1
    # west_spec_vec = numpy.arange(0, 3234)
    west_idf_vec = numpy.ndarray(shape=(3234,), dtype='float')
    west_cal_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(0, 3234):
        west_idf_vec[irow] = calcualte_difc(ws, irow)
        west_cal_vec[irow] = cal_table_ws.cell(irow, difc_col_index)
    # CreateWorkspace(DataX=west_spec_vec, DataY=west_difc_vec, NSpec=1, OutputWorkspace='west_idf_difc')

    # east bank
    # east_spec_vec = numpy.arange(3234, 6468)
    east_idf_vec = numpy.ndarray(shape=(3234,), dtype='float')
    east_cal_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(3234, 6468):
        east_idf_vec[irow - 3234] = calcualte_difc(ws, irow)
        east_cal_vec[irow - 3234] = cal_table_ws.cell(irow, difc_col_index)
    # CreateWorkspace(DataX=east_spec_vec, DataY=east_difc_vec, NSpec=1, OutputWorkspace='east_idf_difc')

    # high angle bank
    # highangle_spec_vec = numpy.arange(6468, 24900)
    highangle_idf_vec = numpy.ndarray(shape=(24900 - 6468,), dtype='float')
    highangle_cal_vec = numpy.ndarray(shape=(24900 - 6468,), dtype='float')
    for irow in range(6468, 24900):
        highangle_idf_vec[irow - 6468] = calcualte_difc(ws, irow)
        highangle_cal_vec[irow - 6468] = cal_table_ws.cell(irow, difc_col_index)

    mask_ws = mtd['vulcan_diamond_2fit_mask']

    # do correction: west
    correct_difc_to_default(west_idf_vec, west_cal_vec, cal_table_ws, 0, 20, 1, mask_ws)
    correct_difc_to_default(east_idf_vec, east_cal_vec, cal_table_ws, 3234, 20, 1, mask_ws)
    correct_difc_to_default(west_idf_vec, west_cal_vec, cal_table_ws, 6468, 20, 1, mask_ws)

    return


# TODO - 20180911 - move to lib and merge with another save_calibration
def save_calibration(ref_ws_name):
    """

    :param ref_ws_name:
    :return:
    """
    # Load an existing 3-bank calibration file for grouping
    exist3bank = '/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180530/VULCAN_calibrate_2018_04_12.h5'
    LoadDiffCal(InputWorkspace=ref_ws_name,
                Filename=exist3bank,
            WorkspaceName='vulcan_old_3banks')
    
    SaveDiffCal(CalibrationWorkspace='',
                GroupingWorkspace='vulcan_exist_grouping',
                MaskWorkspace='')

    return


# TODO - 20180911 - move to lib
def calcualte_difc(ws, ws_index):
    # det_id = ws.getDetector(i).getID()
    det_pos = ws.getDetector(ws_index).getPos()
    source_pos = ws.getInstrument().getSource().getPos()
    sample_pos = ws.getInstrument().getSample().getPos()

    source_sample = sample_pos - source_pos
    det_sample = det_pos - sample_pos
    angle = det_sample.angle(source_sample)

    L1 = source_sample.norm()
    L2 = det_sample.norm()

    # theta = angle * 180/3.14
    # print theta

    difc = 252.816 * 2 * math.sin(angle * 0.5) * (L1 + L2)  # math.sqrt(L1+L2) #\sqrt{L1+L2}

    return difc


# TODO - 20180911 - move to lib
def correct_difc_to_default(idf_difc_vec, cal_difc_vec, cal_table, row_shift, difc_tol, difc_col_index, mask_ws):
    """ Compare the DIFC calculated from the IDF and calibration.
    If the difference is beyond tolerance, using the IDF-calculated DIFC instead and report verbally
    :param idf_difc_vec: DIFC calculated from the instrument geometry (engineered)
    :param cal_difc_vec: DIFC calculated from the calibration
    :param cal_table: calibration value table (TableWorkspace)
    :param row_shift: starting row number the first element in DIFC vector
    :param difc_tol: tolerance on the difference between calculated difc and calibrated difc
    :param difc_col_index: column index of the DIFC in the table workspace
    :param mask_ws: mask workspace
    :return:
    """
    # difference between IDF and calibrated DIFC
    difc_diff_vec = idf_difc_vec - cal_difc_vec

    # go over all the DIFCs
    num_corrected = 0
    message = ''
    for index in range(len(difc_diff_vec)):
        if abs(difc_diff_vec[index]) > difc_tol:
            cal_table.setCell(index+row_shift, difc_col_index, idf_difc_vec[index])
            if mask_ws.readY(index+row_shift)[0] < 0.5:
                mask_sig = 'No Mask'
                num_corrected += 1
            else:
                mask_sig = 'Masked'
            message += '{0}: ws-index = {1}, diff = {2}...  {3}\n' \
                       ''.format(index, index+row_shift, difc_diff_vec[index], mask_sig)
        # END-IF
    # END-FOR
    print (message)
    print ('Number of corrected DIFC = {0}'.format(num_corrected))

    return


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

def main(argv):
    """
    main argument
    :param argv:
    :return:
    """
    # get input
    # TODO - 2018911 - Parse -h/--help, --default, --nexus
    # if argv[0].count('-h') == 1:
    #     print ('Generate cross correlation from input diamond file in dSpacing with resolution -0.0003')
    #     sys.exit(0)
    # else:
    #     # user specified
    #     nxs_file_name = argv[0]

    if True:
        # TODO FIXME - This is a debugging solution
        dates = sorted(Diamond_Runs.keys())
        nxs_file_name = Diamond_Runs[dates[-1]]

    # decide to load or not and thus group workspace
    diamond_ws_name, group_ws_name = ccl.initialize_calibration(nxs_file_name, False)

    # do cross correlation: 2 fit
    ccl.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')

    # check the difference between DIFCs
    check_correct_difcs(ws_name='vulcan_diamond')


    # save calibration file
    save_calibration(ref_ws_name='vulcan_diamond')


    # plot_difc_diff(mask=mask_ws)


if __name__ == '__main__':
    # main
    main(sys.argv)


