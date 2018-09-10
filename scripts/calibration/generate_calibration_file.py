# Generate VULCAN's calibration
import os
import sys
sys.path.insert(1, '/SNS/users/wzz/Mantid_Project/vulcan-build/bin/')
import math
import cross_correlation_lib as ccl

# TODO - 20180910 - 


def main(argv):
    """
    main argument
    :param argv:
    :return:
    """
    # get input
    if argv[0].count('-h') == 1:
        print ('Generate cross correlation from input diamond file in dSpacing with resolution -0.0003')
        sys.exit(0)
    else:
        # user specified
        nxs_file_name = argv[0]

    # decide to load or not and thus group workspace
    diamond_ws_name, group_ws_name = ccl.initialize_calibration(nxs_file_name, False)

    # do cross correlation: 2 fit
    ccl.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')

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

    # save calibration file
    SaveDiffCal(blabla)

    # plot_difc_diff(mask=mask_ws)


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


def correct_difc_to_default(idf_difc_vec, cal_difc_vec, cal_table, row_shift, difc_tol, difc_col_index, mask_ws):
    """

    :param idf_difc_vec:
    :param cal_difc_vec:
    :param cal_table:
    :param row_shift:
    :param difc_tol:
    :param difc_col_index:
    :param mask_ws:
    :return:
    """
    difc_diff_vec = idf_difc_vec - cal_difc_vec
    num_corrected = 0
    for index in range(len(difc_diff_vec)):
        if abs(difc_diff_vec[index]) > difc_tol:
            cal_table.setCell(index+row_shift, difc_col_index, idf_difc_vec[index])
            if mask_ws.readY(index+row_shift)[0] < 0.5:
                mask_sig = 'No Mask'
                num_corrected += 1
            else:
                mask_sig = 'Masked'
            print ('{0}: ws-index = {1}, diff = {2}, {3}'
                   ''.format(index, index+row_shift, difc_diff_vec[index], mask_sig))
    # END-FOR
    print ('Number of corrected DIFC = {0}'.format(num_corrected))

    return


def plot_difc_diff(mask=None):
    return



def analysize_mask():
    """
    """
    # TODO - 20180910 - Implement!
    
    # 1. Load original event workspace

    # 2. For each bank, sort the masked workspace from highest ban


def analyze_result():
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


if __name__ == '__main__':
    # main
    if len(sys.argv) == 1:
        # default
        working_dir = '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
        diamond_file_name = os.path.join(working_dir, 'VULCAN_150178_HighResolution_Diamond.nxs')
        argv = [diamond_file_name]
    else:
        argv = sys.argv[1:]

    main(argv)





