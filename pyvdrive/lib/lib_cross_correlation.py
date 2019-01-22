# script to do cross-correlation
import os
import math
from mantid.api import AnalysisDataService as mtd
from mantid.simpleapi import CrossCorrelate, GetDetectorOffsets, SaveCalFile, ConvertDiffCal, SaveDiffCal
from mantid.simpleapi import RenameWorkspace, Plus, CreateWorkspace, Load, CreateGroupingWorkspace
from mantid.simpleapi import CloneWorkspace, DeleteWorkspace, LoadDiffCal
from mantid.simpleapi import Load, LoadDiffCal, AlignDetectors, DiffractionFocussing, Rebin, EditInstrumentGeometry
from mantid.simpleapi import ConvertToMatrixWorkspace, CrossCorrelate, GetDetectorOffsets, GeneratePythonScript
import bisect
import numpy
import datetime
import datatypeutility
import mantid_helper


def analyze_outputs(cross_correlation_ws_dict, getdetoffset_result_ws_dict):
    """
    evaluate (by matching the fitted cross-correlation peaks to those calculated from
    CrossCorrelation) the peak fitting result from GetDetectorOffsets in order to create
    list of spectra to be masked.
    :param cross_correlation_ws_dict:
    :param getdetoffset_result_ws_dict:
    :return:
    """
    cost_ws_dict = dict()
    for bank_name in ['west', 'east', 'high angle']:
        cc_diamond_ws_name = cross_correlation_ws_dict[bank_name]
        fit_result_table_name = getdetoffset_result_ws_dict[bank_name]

        # create the workspaces
        cost_list = evaluate_cc_quality(cc_diamond_ws_name, fit_result_table_name)
        cost_array = numpy.array(cost_list).transpose()
        cost_ws_name_i = '{0}_cost'.format(bank_name)
        CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1,
                        OutputWorkspace=cost_ws_name_i)

        cost_ws_dict[bank_name] = cost_ws_name_i
    # END-FOR

    return cost_ws_dict


def apply_reference_calibration(calib_ws, ref_calib_ws, bank_name):
    """
    apply reference calibration to output
    :param calib_ws_name:
    :param ref_calib_ws:
    :param bank_name:
    :return:
    """
    if bank_name == 'west':
        row_range = range(0, 3234)
    elif bank_name == 'east':
        row_range = range(3234, 6468)
    elif bank_name == 'high angle':
        row_range = range(6468, 24900)
    else:
        raise RuntimeError('balbal {}'.format(bank_name))

    # apply
    if isinstance(calib_ws, str):
        calib_ws = mantid_helper.retrieve_workspace(calib_ws, True)
    if isinstance(ref_calib_ws, str):
        ref_calib_ws = mantid_helper.retrieve_workspace(ref_calib_ws, True)
    num_cols = calib_ws.columnCount()

    for row_index in row_range:
        for col_index in range(num_cols):
            calib_ws.setCell(row_index, col_index, ref_calib_ws.cell(row_index, col_index))

    return


def calculate_difc(ws, ws_index):
    """ Calculate DIFC of one spectrum
    :param ws:
    :param ws_index:
    :return:
    """
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


def check_correct_difcs_3banks(ws_name, cal_table_name, mask_ws_name):
    """
    check and correct DIFCs if necessary: it is for 3 banks
    :param ws_name:
    :param cal_table_name: name of Calibration workspace (a TableWorkspace)
    :return:
    """
    # west bank
    diamond_event_ws = mtd[ws_name]   # ['vulcan_diamond']
    cal_table_ws = mtd[cal_table_name]
    difc_col_index = 1
    # west_spec_vec = numpy.arange(0, 3234)
    west_idf_vec = numpy.ndarray(shape=(3234,), dtype='float')
    west_cal_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(0, 3234):
        west_idf_vec[irow] = calculate_difc(diamond_event_ws, irow)
        west_cal_vec[irow] = cal_table_ws.cell(irow, difc_col_index)
    # CreateWorkspace(DataX=west_spec_vec, DataY=west_difc_vec, NSpec=1, OutputWorkspace='west_idf_difc')

    # east bank
    # east_spec_vec = numpy.arange(3234, 6468)
    east_idf_vec = numpy.ndarray(shape=(3234,), dtype='float')
    east_cal_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(3234, 6468):
        east_idf_vec[irow - 3234] = calculate_difc(diamond_event_ws, irow)
        east_cal_vec[irow - 3234] = cal_table_ws.cell(irow, difc_col_index)

    # high angle bank
    # highangle_spec_vec = numpy.arange(6468, 24900)
    highangle_idf_vec = numpy.ndarray(shape=(24900 - 6468,), dtype='float')
    highangle_cal_vec = numpy.ndarray(shape=(24900 - 6468,), dtype='float')
    for irow in range(6468, 24900):
        highangle_idf_vec[irow - 6468] = calculate_difc(diamond_event_ws, irow)
        highangle_cal_vec[irow - 6468] = cal_table_ws.cell(irow, difc_col_index)

    mask_ws = mtd[mask_ws_name]

    # correct the unphysical (bad) calibrated DIFC to default DIF: west, east and high angle
    correct_difc_to_default(west_idf_vec, west_cal_vec, cal_table_ws, 0, 20, 1, mask_ws)
    correct_difc_to_default(east_idf_vec, east_cal_vec, cal_table_ws, 3234, 20, 1, mask_ws)
    correct_difc_to_default(highangle_idf_vec, highangle_idf_vec, cal_table_ws, 6468, 20, 1, mask_ws)

    return


def calculate_detector_2theta(workspace, ws_index):
    """ Calculate a detector's 2theta angle
    :param workspace:
    :param ws_index: where the detector is
    :return:
    """
    detpos = workspace.getDetector(ws_index).getPos()
    samplepos = workspace.getInstrument().getPos()
    sourcepos = workspace.getInstrument().getSource().getPos()
    q_out = detpos - samplepos
    q_in = samplepos - sourcepos

    twotheta = q_out.angle(q_in) / math.pi * 180

    return twotheta


def calculate_model(data_ws_name, ws_index, fit_param_table_name):
    """

    :param data_ws_name:
    :param ws_index:
    :param fit_param_table_name:
    :return:
    """
    #data_ws = AnalysisDataService.retrieve(data_ws_name)
    data_ws = mtd[data_ws_name]
    # param_table_ws = AnalysisDataService.retrieve(fit_param_table_name)
    param_table_ws = mtd[fit_param_table_name]

    for row_index in range(param_table_ws.rowCount()):

        ws_index_i = param_table_ws.cell(row_index, 0)
        if ws_index != ws_index_i:
            continue

        peak_pos = param_table_ws.cell(row_index, 1)
        peak_height = param_table_ws.cell(row_index, 3)
        peak_sigma = param_table_ws.cell(row_index, 2)
        bkgd_a0 = param_table_ws.cell(row_index, 4)
        bkgd_a1 = param_table_ws.cell(row_index, 5)

        peak_fwhm = peak_sigma * 2.355

        x_min = peak_pos - 0.5 * peak_fwhm
        x_max = peak_pos + 0.5 * peak_fwhm

        vec_x = data_ws.readX(ws_index)
        i_min = bisect.bisect(vec_x, x_min)
        i_max = bisect.bisect(vec_x, x_max)

        vec_x = vec_x[i_min:i_max]
        obs_y = data_ws.readY(ws_index)[i_min:i_max]
        model_y = peak_function(vec_x, peak_height, peak_pos, peak_sigma, bkgd_a0, bkgd_a1, 'guassian')
        cost = numpy.sqrt(numpy.sum((model_y - obs_y)**2))/len(obs_y)

        print ('Cost x = {0}'.format(cost))

        CreateWorkspace(vec_x, model_y, NSpec=1, OutputWorkspace='model_{0}'.format(ws_index))

    # END-FOR

    return


def find_reference_spectrum(diamond_event_ws):
    # find reference workspace (i.e., detector)

    # Find good peak for reference: strongest???
    ymax = 0
    for s in range(0, diamond_event_ws.getNumberHistograms()):
        y_s = diamond_event_ws.readY(s)
        midBin = int(diamond_event_ws.blocksize() / 2)
        if y_s[midBin] > ymax:
            reference_ws_index = s
            ymax = y_s[midBin]

    return reference_ws_index


def cc_calibrate(ws_name, peak_position, peak_min, peak_max, ws_index_range, reference_ws_index, cc_number, max_offset,
                 binning, index='', peak_fit_time=1):
    """
    cross correlation calibration on a specified subset of spectra in a diamond workspace
    :param ws_name:
    :param peak_position:
    :param peak_min:
    :param peak_max:
    :param ws_index_range:
    :param reference_ws_index:
    :param cc_number:
    :param max_offset:
    :param binning:
    :param index:
    :param peak_fit_time: number of peak fitting in GetDetectorOffsets
    :return: OffsetsWorkspace name, MaskWorkspace name
    """
    # get reference of input workspace
    diamond_event_ws = mantid_helper.retrieve_workspace(ws_name, True)

    datatypeutility.check_int_variable('Reference workspace index', reference_ws_index,
                                       (0, diamond_event_ws.getNumberHistograms()))

    # get reference detector position
    det_pos = diamond_event_ws.getDetector(reference_ws_index).getPos()
    twotheta = calculate_detector_2theta(diamond_event_ws, reference_ws_index)
    print ('[INFO] Reference spectra = {0}  @ {1}   2-theta = {2}'.format(reference_ws_index, det_pos, twotheta))

    # TODO - NIGHT - shall change from bank to bank
    Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params='0.5, -{}, 3.'.format(abs(binning)))

    # Cross correlate spectra using interval around peak at peakpos (d-Spacing)
    cc_ws_name = 'cc_' + ws_name + '_' + index
    CrossCorrelate(InputWorkspace=ws_name,
                   OutputWorkspace=cc_ws_name,
                   ReferenceSpectra=reference_ws_index,
                   WorkspaceIndexMin=ws_index_range[0], WorkspaceIndexMax=ws_index_range[1],
                   XMin=peak_min, XMax=peak_max)

    # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
    offset_ws_name = 'offset_' + ws_name + '_' + index
    mask_ws_name = 'mask_' + ws_name + '_' + index

    if peak_fit_time == 1:
        fit_twice = False
    else:
        fit_twice = True

    # TODO - THIS IS AN IMPORTANT PARAMETER TO SET THE MASK
    min_peak_height = 1.0

    print ('[DB...BAT] ref peak pos = {}, xrange = {}, {}'.format(peak_position, -cc_number, cc_number))
    try:
        GetDetectorOffsets(InputWorkspace=cc_ws_name,
                           OutputWorkspace=offset_ws_name,
                           MaskWorkspace=mask_ws_name,
                           Step=abs(binning),
                           DReference=peak_position,
                           XMin=-cc_number,
                           XMax=cc_number,
                           MaxOffset=max_offset,
                           FitEachPeakTwice=fit_twice,
                           PeakFunction='Gaussian',  # 'PseudoVoigt', # Gaussian
                           MinimumPeakHeight=min_peak_height,  # any peak is lower than 1 shall be masked!
                           PeakFitResultTableWorkspace=cc_ws_name + '_fit'
                           )
    except RuntimeError as run_err:
        # failed to do cross correlation
        return None, run_err

    # check result and remove interval result
    # TODO - FUTURE NEXT - consider whether the cross correlate workspace shall be removed or not
    if False and mtd.doesExist(ws_name + "cc" + index):
        mtd.remove(ws_name + "cc")

    return offset_ws_name, mask_ws_name


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
            cal_table.setCell(index + row_shift, difc_col_index, idf_difc_vec[index])
            if mask_ws.readY(index + row_shift)[0] < 0.5:
                mask_sig = 'No Mask'
                num_corrected += 1
            else:
                mask_sig = 'Masked'
            message += '{0}: ws-index = {1}, diff = {2}...  {3}\n' \
                       ''.format(index, index + row_shift, difc_diff_vec[index], mask_sig)
        # END-IF
    # END-FOR
    print (message)
    print ('Number of corrected DIFC = {0}'.format(num_corrected))

    return


# TODO - FUTURE - Convert this method to a more general form
def cross_correlate_vulcan_data_3banks(diamond_ws_name, group_ws_name, calib_flag, fit_time=1, flag='1fit'):
    """
    main entrance cross-correlation (for VULCAN west/east/high angle).
    Note: it only works for VULCAN dated from 2017.06.01 to 2019.10.01
    :param diamond_ws_name:
    :param group_ws_name:
    :param calib_flag: a 3-element dict of boolean as the flag whether there is need to calibrate this bank
    :param fit_time:
    :param flag:
    :return: 2-tuple: (difc calib, mask workspae, grouping workspace)

    """
    # peak position in d-Spacing
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

    offset_ws_dict = dict()
    mask_ws_dict = dict()

    # West bank
    if calib_flag['west']:
        ref_ws_index = 1613
        peak_width = 0.04  # modified from 0.005
        cc_number_west = 80
        west_offset, west_mask = cc_calibrate(diamond_ws_name, peakpos1, peakpos1 - peak_width, peakpos1 + peak_width,
                                              [0, 3234 - 1],
                                              ref_ws_index, cc_number_west, 1, -0.0003, 'west_{0}'.format(flag),
                                              peak_fit_time=fit_time)
        if west_offset is None:
            err_msg = west_mask
            print ('[ERROR] Unable to calibrate West Bank by cross correlation: {}'.format(err_msg))
        else:
            offset_ws_dict['west'] = west_offset
            mask_ws_dict['west'] = west_mask
    # END-IF

    # East bank
    if calib_flag['east']:
        ref_ws_index = 4847 - 7  # 4854 ends with an even right-shift spectrum
        peak_width = 0.04
        cc_number_east = 80
        east_offset, east_mask = cc_calibrate(diamond_ws_name, peakpos2, peakpos2 - peak_width, peakpos2 + peak_width,
                                              [3234, 6468 - 1],
                                              ref_ws_index, cc_number_east, 1, -0.0003, 'east_{0}'.format(flag),
                                              peak_fit_time=fit_time)
        if east_offset is None:
            err_msg = east_mask
            print ('[ERROR] Unable to calibrate West Bank by cross correlation: {}'.format(err_msg))
        else:
            offset_ws_dict['east'] = east_offset
            mask_ws_dict['east'] = east_mask
    # END-IF

    # High angle
    if calib_flag['high angle']:
        # High angle bank
        ref_ws_index = 15555
        peak_width = 0.01
        cc_number = 20
        ha_offset, ha_mask = cc_calibrate(diamond_ws_name, peakpos3, peakpos3 - peak_width, peakpos3 + peak_width,
                                          [6468, 24900 - 1],
                                          ref_ws_index, cc_number=cc_number, max_offset=1, binning=-0.0003,
                                          index='high_angle_{0}'.format(flag),
                                          peak_fit_time=fit_time)
        if ha_offset is None:
            err_msg = ha_mask
            print ('[ERROR] Unable to calibrate West Bank by cross correlation: {}'.format(err_msg))
        else:
            offset_ws_dict['high angle'] = ha_offset
            mask_ws_dict['high angle'] = ha_mask
    # END-IF

    if len(offset_ws_dict) == 0:
        raise RuntimeError('No bank is calibrated.  Either none of them is flagged Or all of them failed')

    return offset_ws_dict, mask_ws_dict


def merge_detector_calibration(ref_calib_ws, ref_mask_ws, ref_grouping_ws,
                               offset_ws_dict, mask_ws_dict,
                               num_banks, output_ws_name, flag):
    """ Note: only work for 3 banks
    :param ref_calib_ws:
    :param ref_mask_ws:
    :param ref_grouping_ws:
    :param offset_ws_dict:
    :param mask_ws_dict:
    :param num_banks:
    :param output_ws_name:
    :param flag:
    :return:
    """
    # get the starting offset workspace and mask workspace
    bank_name = offset_ws_dict.keys()[0]
    out_offset_ws = CloneWorkspace(InputWorkspace=offset_ws_dict[bank_name],
                                   OutputWorkspace=output_ws_name + '_offset')
    out_mask_ws = CloneWorkspace(InputWorkspace=mask_ws_dict[bank_name],
                                 OutputWorkspace=output_ws_name + '_mask')
    applied = {bank_name: True}
    print ('Offsets and Mask of {} is cloned for output'.format(bank_name))

    # merge
    for bank_name in offset_ws_dict.keys():
        # avoid duplicate operation
        if bank_name in applied:
            print ('[INFO] {} has been applied to output before merging'.format(bank_name))
            continue

        # merge
        merge_calibration(out_offset_ws, offset_ws_dict[bank_name],
                          out_mask_ws, mask_ws_dict[bank_name])
    # END-FOR

    # convert to diff calibratin table:  convert the offsets workspace to difc calibration workspace
    calib_ws_name = output_ws_name + '_cal'
    ConvertDiffCal(OffsetsWorkspace=out_offset_ws,
                   OutputWorkspace=calib_ws_name)

    # apply reference to
    for bank_name in ['west', 'east', 'high angle']:
        # skip calibrated banks
        if bank_name in offset_ws_dict.keys():
            continue

        print ('[INFO] Applying {}:{} to {}'.format(ref_calib_ws, bank_name, calib_ws_name))
        apply_reference_calibration(calib_ws_name, ref_calib_ws, bank_name)
    # END-FOR

    if len(offset_ws_dict.keys()) < num_banks:
        out_offset_ws = None

    return calib_ws_name, out_offset_ws, out_mask_ws


def merge_save_mask_detector(ref_offset_ws, ref_calib_ws, ref_mask_ws, ref_grouping_ws,
                             offset_ws_dict, mask_ws_dict,
                             num_banks, output_ws_name, flag):

    # get the starting offset workspace and mask workspace
    applied = dict()
    if num_banks == len(offset_ws_dict):
        out_offset_ws = CloneWorkspace(InputWorkspace=offset_ws_dict['west'],
                                       OutputWorkspace=output_ws_name + '_offset')
        out_mask_ws = CloneWorkspace(InputWorkspace=offset_ws_dict['west'],
                                     OutputWorkspace=output_ws_name + '_mask')
        applied['west'] = True
    else:
        out_offset_ws = CloneWorkspace(InputWorkspace=ref_offset_ws,
                                       OutputWorkspace=output_ws_name + '_offset')
        out_mask_ws = CloneWorkspace(InputWorkspace=ref_mask_ws,
                                     OutputWorkspace=output_ws_name + '_mask')
        applied['west'] = False

    # merge
    for bank_name in offset_ws_dict.keys():
        # avoid duplicate operation
        if bank_name in applied:
            print ('[INFO] {} has been applied to output before merging'.format(bank_name))
            continue

        # merge
        merge_calibration(out_offset_ws, offset_ws_dict[bank_name],
                          out_mask_ws, mask_ws_dict[bank_name])
    # END-FOR
    # offset_ws_name, mask_ws_name = merge_calibration(diamond_ws_name, out_offset_ws
    #                                                  [(west_offset, west_mask), (east_offset, east_mask),
    #                                                   (ha_offset, ha_mask)])
    # save
    time_now = datetime.datetime.now()
    file_base_name = 'VULCAN_Calibration_{}-{}-{}_{}-{}-{}_{}'.format(time_now.year, time_now.month, time_now.day,
                                                                   time_now.hour, time_now.minute,
                                                                   time_now.second, flag)
    calib_ws_name, dummy1, dummy2 = save_calibration(out_offset_ws, out_mask_ws, ref_grouping_ws, file_base_name)

    # # combine_save_calibration(diamond_ws_name + '_{0}'.format(flag),
    # #                          [(west_offset, west_mask), (east_offset, east_mask), (ha_offset, ha_mask)],
    # #                          group_ws_name, 'vulcan_{0}'.format(flag))
    #
    # offset_dict = {'west': west_offset_clone, 'east': east_offset, 'high angle': ha_offset}
    # mask_dict = {'west': west_mask_clone, 'east': east_mask, 'high angle': ha_mask}

    return calib_ws_name, out_offset_ws, out_mask_ws


def cross_correlate_vulcan_data_2bank(diamond_ws_name, group_ws_name, fit_time=1, flag='1fit'):
    """ main cross-correlation (for VULCAN west/east and high angle)
    :param diamond_ws_name:
    :param group_ws_name:
    :param fit_time:
    :param flag:
    :return:
    """
    # peak position in d-Spacing
    peakpos1 = 1.2614
    # peakpos2 = 1.2614
    peakpos3 = 1.07577

    # West and east bank
    ref_ws_index = 1613
    peak_width = 0.04  # modified from 0.005
    cc_number_west = 80
    westeast_offset, westeast_mask = cc_calibrate(diamond_ws_name, peakpos1, peakpos1 - peak_width,
                                                  peakpos1 + peak_width,
                                                  [0, 6468 - 1],
                                                  ref_ws_index, cc_number_west, 1, -0.0003, 'westeast_{0}'.format(flag),
                                                  peak_fit_time=fit_time)

    # # East bank
    # ref_ws_index = 4847 - 7    # 4854 ends with an even right-shift spectrum
    # peak_width = 0.04
    # cc_number_east = 80
    # east_offset, east_mask = cc_calibrate(diamond_ws_name, peakpos2, peakpos2 - peak_width, peakpos2 + peak_width,
    #                                       [3234, 6468 - 1],
    #                                       ref_ws_index, cc_number_east, 1, -0.0003, 'east_{0}'.format(flag),
    #                                       peak_fit_time=fit_time)
    #
    # High angle bank
    ref_ws_index = 15555
    peak_width = 0.01
    cc_number = 20
    ha_offset, ha_mask = cc_calibrate(diamond_ws_name, peakpos3, peakpos3 - peak_width, peakpos3 + peak_width,
                                      [6468, 24900 - 1],
                                      ref_ws_index, cc_number=cc_number, max_offset=1, binning=-0.0003,
                                      index='high_angle_{0}'.format(flag),
                                      peak_fit_time=fit_time)

    westeast_offset_clone = CloneWorkspace(InputWorkspace=westeast_offset,
                                           OutputWorkspace=str(westeast_offset) + '_copy')
    westeast_mask_clone = CloneWorkspace(InputWorkspace=westeast_mask, OutputWorkspace=str(westeast_mask) + '_copy')

    combine_save_calibration(diamond_ws_name + '_{0}'.format(flag), [(westeast_offset, westeast_mask), (ha_offset, ha_mask)],
                             group_ws_name, 'vulcan_{0}'.format(flag))

    offset_dict = {'westeast': westeast_offset_clone, 'high angle': ha_offset}
    mask_dict = {'westeast': westeast_mask_clone, 'high angle': ha_mask}

    return offset_dict, mask_dict


def instrument_wide_cross_correlation(focused_ws_name, reference_ws_index, min_d, max_d):
    """

    :param focused_ws_name:
    :param reference_ws_index:
    :param min_d:
    :param max_d:
    :return:
    """
    """
    Main algorithm to do cross-correlation among different banks of VULCAN.
    This is the second round calibration using the data file
    1. calibrated by previous calibration file based on inner bank cross correlation
    2. diffraction focused
    For the instrument with west, east and high angle banks, the input file shall be a 3 bank
    :return:
    """
    CrossCorrelate(InputWorkspace='vulcan_diamond_3bank', OutputWorkspace='cc_vulcan_diamond_3bank', ReferenceSpectra=1,
                   WorkspaceIndexMax=2, XMin=1.0649999999999999, XMax=1.083)
    GetDetectorOffsets(InputWorkspace='cc_vulcan_diamond_3bank', Step=0.00029999999999999997,
                       DReference=1.0757699999999999, XMin=-20, XMax=20, OutputWorkspace='zz_test_3bank',
                       FitEachPeakTwice=True, PeakFitResultTableWorkspace='ddd', OutputFitResult=True,
                       MinimumPeakHeight=1)

    return shift_dict


def test_cross_correlate_vulcan_data(wkspName, group_ws_name):
    """
    cross correlation on a test vulcan diamond data file with reduced number of spectra
    :param wkspName:
    :param group_ws_name:
    :return:
    """
    # wkspName = 'full_diamond'
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

    ref_ws_index = 6
    peak_width = 0.04  # modified from 0.005
    cc_number_west = 80
    west_offset, west_mask = cc_calibrate(wkspName, peakpos1, peakpos1 - peak_width, peakpos1 + peak_width,
                                          [0, 3234 - 1],
                                          ref_ws_index, cc_number_west, 1, -0.0003, 'west')

    ref_ws_index = 14
    peak_width = 0.04
    cc_number_east = 80
    east_offset, east_mask = cc_calibrate(wkspName, peakpos2, peakpos2 - peak_width, peakpos2 + peak_width,
                                          [3234, 6468 - 1],
                                          ref_ws_index, cc_number_east, 1, -0.0003, 'east')

    ref_ws_index = 58
    peak_width = 0.01
    cc_number = 20
    ha_offset, ha_mask = cc_calibrate(wkspName, peakpos3, peakpos3 - peak_width, peakpos3 + peak_width,
                                      [6468, 24900 - 1],
                                      ref_ws_index, cc_number, 1, -0.0003, 'high_angle')

    combine_save_calibration(wkspName, [(west_offset, west_mask), (east_offset, east_mask), (ha_offset, ha_mask)],
                             group_ws_name, 'vulcan_vz_test')

    return


def evaluate_cc_quality(data_ws_name, fit_param_table_name):
    """ evaluate cross correlation quality by fitting the peaks
    :param data_ws_name:
    :param fit_param_table_name:
    :return:
    """
    # data_ws = AnalysisDataService.retrieve(data_ws_name)
    data_ws = mtd[data_ws_name]
    # param_table_ws = AnalysisDataService.retrieve(fit_param_table_name)
    param_table_ws = mtd[fit_param_table_name]

    cost_list = list()

    bad_ws_index_list = list()
    for row_index in range(param_table_ws.rowCount()):

        ws_index = param_table_ws.cell(row_index, 0)
        peak_pos = param_table_ws.cell(row_index, 1)
        peak_height = param_table_ws.cell(row_index, 3)
        peak_sigma = param_table_ws.cell(row_index, 2)
        bkgd_a0 = param_table_ws.cell(row_index, 4)
        bkgd_a1 = param_table_ws.cell(row_index, 5)

        # avoid bad pixels
        if peak_sigma < 1 or peak_sigma > 15 or peak_height < 1 or peak_height > 5:
            bad_ws_index_list.append(ws_index)
            continue

        peak_fwhm = peak_sigma * 2.355

        x_min = peak_pos - 0.5 * peak_fwhm
        x_max = peak_pos + 0.5 * peak_fwhm

        vec_x = data_ws.readX(ws_index)
        i_min = bisect.bisect(vec_x, x_min)
        i_max = bisect.bisect(vec_x, x_max)

        vec_x = vec_x[i_min:i_max]
        obs_y = data_ws.readY(ws_index)[i_min:i_max]
        model_y = peak_function(vec_x, peak_height, peak_pos, peak_sigma, bkgd_a0, bkgd_a1, 'guassian')
        cost = numpy.sqrt(numpy.sum((model_y - obs_y)**2))/len(obs_y)

        cost_list.append([ws_index, cost])
    # END-FOR

    print ('Bad pixels number: {0}\n\t... They are {1}'.format(len(bad_ws_index_list), bad_ws_index_list))

    return cost_list, bad_ws_index_list


# # TODO - 20180912 - Clean
# def export_diff_cal_h5(ref_ws_name, offset_ws, mask_ws, num_groups):
#     """ Export diff cal to h5 format
#     :param ref_ws_name:
#     :return:
#     """
#     # Load an existing 3-bank calibration file for grouping
#     exist3bank = '/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180530/VULCAN_calibrate_2018_04_12.h5'
#     LoadDiffCal(InputWorkspace=ref_ws_name,
#                 Filename=exist3bank,
#                 WorkspaceName='vulcan_old_3banks')
#
#     today = datetime.datetime.now()
#     for ws_name in mtd.getObjectNames():
#         print ws_name
#     offset_ws_obj = mtd['vulcan_diamond_2fit_cal']
#     SaveDiffCal(CalibrationWorkspace=offset_ws_obj,
#                 GroupingWorkspace='vulcan_old_3banks_group',
#                 MaskWorkspace=mask_ws,
#                 Filename='VULCAN_calibrate_{}_{:02}_{:02}.h5'.format(today.year, today.month, today.day))
#
#     return


def get_masked_ws_indexes(mask_ws):
    """
    get the workspace indexes that are masked
    :param mask_ws:
    :return:
    """
    if isinstance(mask_ws, str):
        mask_ws = mtd[mask_ws]

    masked_list = list()
    for iws in range(mask_ws.getNumberHistograms()):
        if mask_ws.readY(iws)[0] > 0.5:
            masked_list.append(iws)

    return masked_list


def initialize_calibration(nxs_file_name, must_load=False):
    """
    initialize the cross-correlation calibration by loading diamond data and grouping workspace if they are not loaded
    :return:
    """
    # set workspace name
    diamond_ws_name = 'vulcan_diamond'
    group_ws_name = 'vulcan_group'

    print ('Input file to load: {0}'.format(nxs_file_name))
    if mtd.doesExist(diamond_ws_name) is False or must_load:
        Load(Filename=nxs_file_name, OutputWorkspace=diamond_ws_name)
    if mtd.doesExist(group_ws_name) is False:
        CreateGroupingWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace=group_ws_name)

    return diamond_ws_name, group_ws_name


def load_calibration_file(ref_ws_name, calib_file_name, calib_ws_base_name=None):
    """
    load calibration file
    :param ref_ws_name:
    :param calib_file_name:
    :param calib_ws_base_name:
    :return:
    """
    if calib_ws_base_name is None:
        calib_ws_base_name = 'vulcan'

    # load data file
    r = LoadDiffCal(InputWorkspace=ref_ws_name,
                Filename=calib_file_name, WorkspaceName=calib_ws_base_name)

    calib_ws_name = '{}_cal'.format(calib_ws_base_name)
    mask_ws_name = '{}_mask'.format(calib_ws_base_name)
    group_ws_name = '{}_group'.format(calib_ws_base_name)

    return calib_ws_name, mask_ws_name, group_ws_name


def load_raw_nexus(file_name=None, ipts=None, run_number=None, output_ws_name=None):
    """ Reduced: aligned detector and diffraction focus, powder data
    :param file_name:
    :param ipts:
    :param run_number:
    :return:
    """
    if file_name is None:
        file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts, run_number)

    if output_ws_name is None:
        output_ws_name = 'vulcan_diamond'

    Load(Filename=file_name, OutputWorkspace=output_ws_name)

    return output_ws_name


def merge_2_masks(lhs_mask_name, rhs_mask_name, output_mask_name):
    """
    Merge (add) 2 MaskWorkspaces
    :param lhs_mask_name:
    :param rhs_mask_name:
    :param output_mask_name:
    :return:
    """
    print ('[INFO] MaskWorkspace operation: {} + {} ---> {}'.format(lhs_mask_name, rhs_mask_name, output_mask_name))

    # Plus 2 workspaces
    Plus(LHSWorkspace=lhs_mask_name, RHSWorkspace=rhs_mask_name,
         OutputWorkspace=output_mask_name)

    # now time to set everything right
    lhs_mask = mtd[lhs_mask_name]
    rhs_mask = mtd[rhs_mask_name]
    ohs_mask = mtd[output_mask_name]

    # collect the masked spectra
    mask_wsindex_list = list()
    for iws in range(lhs_mask.getNumberHistograms()):
        if lhs_mask.readY(iws)[0] > 0.5:
            mask_wsindex_list.append(iws)
    for iws in range(rhs_mask.getNumberHistograms()):
        if rhs_mask.readY(iws)[0] > 0.5:
            mask_wsindex_list.append(iws)

    # mask all detectors explicitly
    ohs_mask.maskDetectors(WorkspaceIndexList=mask_wsindex_list)

    print ('[INFO] {}: # Masked Detectors = {}'.format(output_mask_name, len(mask_wsindex_list)))

    return


def align_focus_event_ws(event_ws_name, calib_ws_name, group_ws_name):
    """
    overwrite the input
    """

    AlignDetectors(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                   CalibrationWorkspace=calib_ws_name)

    DiffractionFocussing(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                         GroupingWorkspace=group_ws_name)

    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name, Params='0.5,-0.0003,3')

    ConvertToMatrixWorkspace(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name)

    EditInstrumentGeometry(Workspace=event_ws_name, PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2',
                           Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3',
                           InstrumentName='vulcan_3bank')

    return event_ws_name


def reduced_powder_data(ipts_number, run_number, calib_file_name, event_ws_name='vulcan_diamond',
                        focus_ws_name='vulcan_diamond_3bank'):
    """
    reduced: aligned detector and diffraction focus, powder data
    :param ipts_number:
    :param run_number:
    :return:
    """
    raw_nxs_file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)
    Load(Filename=raw_nxs_file_name, OutputWorkspace=event_ws_name)

    # load data file
    LoadDiffCal(InputWorkspace=event_ws_name,
                Filename=calib_file_name, WorkspaceName='vulcan')

    AlignDetectors(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                   CalibrationWorkspace='vulcan_cal')

    DiffractionFocussing(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                         GroupingWorkspace='vulcan_group')

    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name, Params='0.5,-0.0003,3')

    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace=focus_ws_name)

    EditInstrumentGeometry(Workspace='vulcan_diamond_3bank', PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2',
                           Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3',
                           InstrumentName='vulcan_3bank')

    return


# TODO - NIGHT - better coding quality
def merge_calibration_all(diamond_ws_name, offset_mask_ws_list):
    """
    merge cross-correlated calibration and offset workspaces, which are on partial workspaces
    :param diamond_ws_name:
    :param offset_mask_ws_list:
    :return:
    """
    raise RuntimeError('Not used any more.  Kept as a  reference')
    offset_ws_name0, mask_ws_name0 = offset_mask_ws_list[0]
    offset_ws_name = diamond_ws_name + '_offset'
    mask_ws_name = diamond_ws_name + '_mask'
    if offset_ws_name != offset_ws_name0:
        RenameWorkspace(InputWorkspace=offset_ws_name0, OutputWorkspace=offset_ws_name)
    if mask_ws_name != mask_ws_name0:
        RenameWorkspace(InputWorkspace=mask_ws_name0, OutputWorkspace=mask_ws_name)

    print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))
    for ituple in range(1, len(offset_mask_ws_list)):
        offset_ws_name_i, mask_ws_name_i = offset_mask_ws_list[ituple]
        # use Plus to combine 2 offsets workspace
        Plus(LHSWorkspace=offset_ws_name, RHSWorkspace=offset_ws_name_i,
             OutputWorkspace=offset_ws_name)
        # merge masks workspace
        merge_2_masks(mask_ws_name, mask_ws_name_i, mask_ws_name + '_temp')
        # delete previous combined mask workspace and rename merged mask workspace to target MaskWorkspace
        DeleteWorkspace(Workspace=mask_ws_name)
        RenameWorkspace(InputWorkspace=mask_ws_name+'_temp', OutputWorkspace=mask_ws_name)
        print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))

    return offset_ws_name, mask_ws_name


# TODO - NIGHT - better coding quality
def merge_calibration(offset_ws_name, partial_offset_ws_name, mask_ws_name, partial_mask_ws_name):
    """
    merge cross-correlated calibration and offset workspaces, which are on partial workspaces
    :param diamond_ws_name:
    :param offset_mask_ws_list:
    :return:
    """
    # use Plus to combine 2 offsets workspace
    Plus(LHSWorkspace=offset_ws_name, RHSWorkspace=partial_offset_ws_name,
         OutputWorkspace=offset_ws_name)

    # mask:
    # merge masks workspace
    merge_2_masks(mask_ws_name, partial_mask_ws_name, mask_ws_name + '_temp')
    # delete previous combined mask workspace and rename merged mask workspace to target MaskWorkspace
    DeleteWorkspace(Workspace=mask_ws_name)
    RenameWorkspace(InputWorkspace=mask_ws_name + '_temp', OutputWorkspace=mask_ws_name)
    print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))

    return offset_ws_name, mask_ws_name


def save_calibration(offset_ws_name, mask_ws_name, group_ws_name, calib_file_prefix):
    """
    save calibration (calibration table, mask and grouping) to legacy .cal and current .h5 file
    :param offset_ws_name:
    :param mask_ws_name:
    :param group_ws_name:
    :param calib_file_prefix:
    :return:  calib_ws_name, offset_ws_name, mask_ws_name
    """
    # for the sake of legacy .cal file
    SaveCalFile(OffsetsWorkspace=offset_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=os.path.join(os.getcwd(), calib_file_prefix + '.cal'))

    # save for the .h5 version that is a standard now
    out_file_name = os.path.join(os.getcwd(), calib_file_prefix + '.h5')
    if os.path.exists(out_file_name):
        os.unlink(out_file_name)
    calib_ws_name = offset_ws_name+'_diff_cal'

    # need to convert the offsets workspace to difc calibration workspace
    ConvertDiffCal(OffsetsWorkspace=offset_ws_name,
                   OutputWorkspace=calib_ws_name)
    # save
    SaveDiffCal(CalibrationWorkspace=calib_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=out_file_name)

    # save DIFC to files
    # TODO - NIGHT - Implement writing DIFC from calibration workspace
    print ('[DB...BAT] Writing DIFC to file')
    calib_ws = mantid_helper.retrieve_workspace(calib_ws_name)
    print ('[DB...BAT] Calibration workspace: type {}, {}'.format(calib_ws, calib_ws.id))

    # last: save python file
    GeneratePythonScript(InputWorkspace=calib_ws_name, Filename=calib_file_prefix + '.py')

    print ('Calibration file is saved as {0} from {1}, {2} and {3}'
           ''.format(out_file_name, calib_ws_name, mask_ws_name, group_ws_name))

    return calib_ws_name, offset_ws_name, mask_ws_name


def combine_save_calibration(ws_name, offset_mask_list, group_ws_name, calib_file_prefix):
    """ Save calibration workspace, mask workspace and group workspace to a standard .h5 calibration file.
    It is to merge the offset workspace and mask workspace from the cross-correlation.
    :param ws_name:
    :param offset_mask_list:
    :param group_ws_name:
    :param calib_file_prefix:
    :return:
    """
    raise NotImplementedError('Shall be replaced by merge_calibration and save_calibration ')
    # combine the offset and mask workspaces
    offset_ws_name0, mask_ws_name0 = offset_mask_list[0]
    offset_ws_name = ws_name + '_offset'
    mask_ws_name = ws_name + '_mask'
    if offset_ws_name != offset_ws_name0:
        RenameWorkspace(InputWorkspace=offset_ws_name0, OutputWorkspace=offset_ws_name)
    if mask_ws_name != mask_ws_name0:
        RenameWorkspace(InputWorkspace=mask_ws_name0, OutputWorkspace=mask_ws_name)

    print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))
    for ituple in range(1, len(offset_mask_list)):
        offset_ws_name_i, mask_ws_name_i = offset_mask_list[ituple]
        Plus(LHSWorkspace=offset_ws_name, RHSWorkspace=offset_ws_name_i,
             OutputWorkspace=offset_ws_name)
        merge_2_masks(mask_ws_name, mask_ws_name_i, mask_ws_name + '_temp')
        DeleteWorkspace(Workspace=mask_ws_name)
        RenameWorkspace(InputWorkspace=mask_ws_name+'_temp', OutputWorkspace=mask_ws_name)
        print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))

    # for the sake of legacy
    SaveCalFile(OffsetsWorkspace=offset_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=os.path.join(os.getcwd(), calib_file_prefix + '.cal'))

    # save for the .h5 version that is a standard now
    out_file_name = os.path.join(os.getcwd(), calib_file_prefix + '.h5')
    if os.path.exists(out_file_name):
        os.unlink(out_file_name)
    calib_ws_name = ws_name+'_cal'
    ConvertDiffCal(OffsetsWorkspace=offset_ws_name,
                   OutputWorkspace=calib_ws_name)
    SaveDiffCal(CalibrationWorkspace=calib_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=out_file_name)

    print ('Calibration file is saved as {0} from {1}, {2} and {3}'
           ''.format(out_file_name, calib_ws_name, mask_ws_name, group_ws_name))

    return calib_ws_name, offset_ws_name, mask_ws_name


def peak_function(vec_dspace, peak_intensity, peak_center, sigma, a0, a1, function_type):
    """ calculate peak profile function from a vector
    :param vec_dspace:
    :param peak_intensity:
    :param peak_center:
    :param sigma:
    :param a0:
    :param a1:
    :param function_type:
    :return:
    """
    # function_type = gaussian:
    vec_y = peak_intensity * numpy.exp(
        -0.5 * (vec_dspace - peak_center) ** 2 / sigma ** 2) + a0 + a1 * vec_dspace

    return vec_y


def select_detectors_to_mask(cost_ws_dict, cost_threshold):
    """

    :param cost_ws_dict:
    :param cost_threshold:
    :return:
    """
    for bank_name in ['west', 'east', 'high angle']:
        cost_ws_name = cost_ws_dict[bank_name]
        cost_matrix_ws = mtd[cost_ws_name]
        vec_ws_index = cost_matrix_ws.readX(0)
        vec_cost = cost_matrix_ws.readY(0)
        raise RuntimeError('Use numpy operation to get the indexes of cost larger than threshold')

    return

# def main(argv):
#     """
#
#     :param argv:
#     :return:
#     """
#     if len(argv) == 0:
#         # default
#         nxs_file_name = 'VULCAN_150178_HighResolution_Diamond.nxs'
#     else:
#         # user specified
#         nxs_file_name = argv[0]
#
#     # decide to load or not and thus group workspace
#     diamond_ws_name, group_ws_name = initialize_calibration(nxs_file_name, False)
#
#     cross_correlate_vulcan_data(diamond_ws_name, group_ws_name)


# main([])
# 
# # WEST
# calculate_model('cc_vulcan_diamond_west', 1755, 'offset_vulcan_diamond_west_FitResult')
# # plot cost list
# cost_list, west_bad = evaluate_cc_quality('cc_vulcan_diamond_west', 'offset_vulcan_diamond_west_FitResult')
# cost_array = numpy.array(cost_list).transpose()
# CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='West_Cost')
# 
# 
# # East
# # plot cost list
# cost_list, east_bad = evaluate_cc_quality('cc_vulcan_diamond_east', 'offset_vulcan_diamond_east_FitResult')
# cost_array = numpy.array(cost_list).transpose()
# print (cost_array)
# CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='East_Cost')
# 
# # HIGH ANGLE
# calculate_model('cc_vulcan_diamond_high_angle', 12200, 'offset_vulcan_diamond_high_angle_FitResult')
# # plot cost list
# cost_list, high_angle_bad = evaluate_cc_quality('cc_vulcan_diamond_high_angle', 'offset_vulcan_diamond_high_angle_FitResult')
# cost_array = numpy.array(cost_list).transpose()
# CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='HighAngle_Cost')




