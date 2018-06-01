# script to do cross-correlation
import os
import math
from mantid.api import AnalysisDataService as mtd
from mantid.simpleapi import CrossCorrelate, GetDetectorOffsets, SaveCalFile, ConvertDiffCal, SaveDiffCal
from mantid.simpleapi import RenameWorkspace, Plus, CreateWorkspace, Load, CreateGroupingWorkspace
from mantid.simpleapi import CloneWorkspace, DeleteWorkspace
import bisect
import numpy


def initialize_calibration(nxs_file_name, must_load=False):
    """
    initialize the cross-correlation calibration by loading data if it is not loaded
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

def cal_2theta(workspace, ws_index):
    detpos = workspace.getDetector(ws_index).getPos()
    samplepos = workspace.getInstrument().getPos()
    sourcepos = workspace.getInstrument().getSource().getPos()
    q_out = detpos - samplepos
    q_in = samplepos - sourcepos
    
    twotheta = q_out.angle(q_in) / math.pi * 180
    
    return twotheta


def cc_calibrate(ws_name, peak_position, peak_min, peak_max, ws_index_range, reference_ws_index, cc_number, max_offset,
                 binning, index='', peak_fit_time=1):
    """
    cross correlation calibration on a
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
    :param peak_fit_time:
    :return:
    """
    workspace = mtd[ws_name]

    # find reference workspace
    if reference_ws_index is None:
        # Find good peak for reference: strongest???
        ymax = 0
        for s in range(0, workspace.getNumberHistograms()):
            y_s = workspace.readY(s)
            midBin = int(workspace.blocksize() / 2)
            if y_s[midBin] > ymax:
                reference_ws_index = s
                ymax = y_s[midBin]
    # END-IF
    det_pos = workspace.getDetector(reference_ws_index).getPos()
    twotheta = cal_2theta(workspace, reference_ws_index)
    print ('Reference spectra = {0}  @ {1}   2-theta = {2}'.format(reference_ws_index, det_pos, twotheta))

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
    
    GetDetectorOffsets(InputWorkspace=cc_ws_name,
                       OutputWorkspace=offset_ws_name,
                       MaskWorkspace=mask_ws_name,
                       Step=abs(binning),
                       DReference=peak_position,
                       XMin=-cc_number,
                       XMax=cc_number,
                       MaxOffset=max_offset,
                       OutputFitResult=True,
                       FitEachPeakTwice=fit_twice,
                       PeakFunction='Gaussian',  # 'PseudoVoigt', # Gaussian
                       MinimumPeakHeight=min_peak_height,  # any peak is lower than 1 shall be masked!
                       PeakFitResultTableWorkspace=cc_ws_name + '_fit'
                       )

    # check result and remove interval result
    if False and mtd.doesExist(ws_name+"cc"+index):
        mtd.remove(ws_name+"cc")

    return offset_ws_name, mask_ws_name


def PlusMaskWorkspace(lhs_mask_name, rhs_mask_name, output_mask_name):
    """
    """
    Plus(LHSWorkspace=lhs_mask_name, RHSWorkspace=rhs_mask_name,
         OutputWorkspace=output_mask_name)

    # now time to set everything right
    lhs_mask = mtd[lhs_mask_name]
    rhs_mask = mtd[rhs_mask_name]
    ohs_mask = mtd[output_mask_name]

    print ('Inputs: {0}, {1}'.format(lhs_mask_name, rhs_mask_name))

    mask_wsindex_list = list()
    for iws in range(lhs_mask.getNumberHistograms()):
        if lhs_mask.readY(iws)[0] > 0.5:
            mask_wsindex_list.append(iws)
    for iws in range(rhs_mask.getNumberHistograms()):
        if rhs_mask.readY(iws)[0] > 0.5:
            mask_wsindex_list.append(iws)

    print ('Total masked: {0}'.format(len(mask_wsindex_list)))

    ohs_mask.maskDetectors(WorkspaceIndexList=mask_wsindex_list)

    return


def save_calibration(ws_name, offset_mask_list, group_ws_name, calib_file_prefix):
    """

    :param ws_name:
    :param offset_mask_list:
    :param group_ws_name:
    :param calib_file_prefix:
    :return:
    """
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
        #Plus(LHSWorkspace=mask_ws_name, RHSWorkspace=mask_ws_name_i,
        #     OutputWorkspace=mask_ws_name)
        PlusMaskWorkspace(mask_ws_name, mask_ws_name_i, mask_ws_name+'_temp')
        DeleteWorkspace(Workspace=mask_ws_name)
        RenameWorkspace(InputWorkspace=mask_ws_name+'_temp', OutputWorkspace=mask_ws_name)
        print ('Number of masked spectra = {0} in {1}'.format(mtd[mask_ws_name].getNumberMasked(), mask_ws_name))

     # for the sake of legacy
    SaveCalFile(OffsetsWorkspace=offset_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=os.path.join(os.getcwd(), calib_file_prefix + '.cal'))

    # the real version
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

    print ('Calibration file is saved as {0} from {1}, {2} and {3}'.format(out_file_name, calib_ws_name, mask_ws_name, group_ws_name))

    return calib_ws_name, offset_ws_name, mask_ws_name


def cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=1, flag='1fit'):
    """
    main cross-correlation (for VULCAN west/east/high angle)
    :param diamond_ws_name:
    :param group_ws_name:
    :param fit_time:
    :param flag:
    :return:
    """
    # peak position in d-Spacing
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

    # West bank
    ref_ws_index = 1613
    peak_width = 0.04   # modified from 0.005
    cc_number_west = 80
    west_offset, west_mask = cc_calibrate(diamond_ws_name, peakpos1, peakpos1 - peak_width, peakpos1 + peak_width,
                                          [0, 3234 - 1],
                                          ref_ws_index, cc_number_west, 1, -0.0003, 'west_{0}'.format(flag),
                                          peak_fit_time=fit_time)

    # East bank
    ref_ws_index = 4847 - 7    # 4854 ends with an even right-shift spectrum
    peak_width = 0.04
    cc_number_east = 80
    east_offset, east_mask = cc_calibrate(diamond_ws_name, peakpos2, peakpos2 - peak_width, peakpos2 + peak_width,
                                          [3234, 6468 - 1],
                                          ref_ws_index, cc_number_east, 1, -0.0003, 'east_{0}'.format(flag),
                                          peak_fit_time=fit_time)
                                          
    # High angle bank
    ref_ws_index = 15555
    peak_width = 0.01
    cc_number = 20
    ha_offset, ha_mask = cc_calibrate(diamond_ws_name, peakpos3, peakpos3 - peak_width, peakpos3 + peak_width,
                                      [6468, 24900 - 1],
                                      ref_ws_index, cc_number=cc_number, max_offset=1, binning=-0.0003, index='high_angle_{0}'.format(flag),
                                      peak_fit_time=fit_time)

    west_offset_clone = CloneWorkspace(InputWorkspace=west_offset, OutputWorkspace=str(west_offset) + '_copy')
    west_mask_clone = CloneWorkspace(InputWorkspace=west_mask, OutputWorkspace=str(west_mask) + '_copy')

    save_calibration(diamond_ws_name+'_{0}'.format(flag), [(west_offset, west_mask), (east_offset, east_mask), (ha_offset, ha_mask)],
                     group_ws_name, 'vulcan_{0}'.format(flag))

    offset_dict = {'west': west_offset_clone, 'east': east_offset, 'high angle': ha_offset}
    mask_dict = {'west': west_mask_clone, 'east': east_mask, 'high angle': ha_mask}

    return offset_dict, mask_dict


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
    peak_width = 0.04   # modified from 0.005
    cc_number_west = 80
    westeast_offset, westeast_mask = cc_calibrate(diamond_ws_name, peakpos1, peakpos1 - peak_width, peakpos1 + peak_width,
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
                                      ref_ws_index, cc_number=cc_number, max_offset=1, binning=-0.0003, index='high_angle_{0}'.format(flag),
                                      peak_fit_time=fit_time)

    westeast_offset_clone = CloneWorkspace(InputWorkspace=westeast_offset, OutputWorkspace=str(westeast_offset) + '_copy')
    westeast_mask_clone = CloneWorkspace(InputWorkspace=westeast_mask, OutputWorkspace=str(westeast_mask) + '_copy')

    save_calibration(diamond_ws_name+'_{0}'.format(flag), [(westeast_offset, westeast_mask), (ha_offset, ha_mask)],
                     group_ws_name, 'vulcan_{0}'.format(flag))


    offset_dict = {'westeast': westeast_offset_clone, 'high angle': ha_offset}
    mask_dict = {'westeast': westeast_mask_clone, 'high angle': ha_mask}

    return offset_dict, mask_dict

def cross_correlate_vulcan_data_test(wkspName, group_ws_name):
    """
    cross correlation on vulcan data
    :param wkspName:
    :param group_ws_name:
    :return:
    """
    # wkspName = 'full_diamond'
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

    ref_ws_index = 6
    peak_width = 0.04   # modified from 0.005
    cc_number_west = 80
    west_offset, west_mask = cc_calibrate(wkspName, peakpos1, peakpos1-peak_width, peakpos1+peak_width, [0, 3234-1],
                                          ref_ws_index, cc_number_west, 1, -0.0003, 'west')

    ref_ws_index = 14
    peak_width = 0.04
    cc_number_east = 80
    east_offset, east_mask = cc_calibrate(wkspName, peakpos2, peakpos2-peak_width, peakpos2+peak_width, [3234, 6468-1],
                                          ref_ws_index, cc_number_east, 1, -0.0003, 'east')
                                          
    ref_ws_index = 58
    peak_width = 0.01
    cc_number = 20
    ha_offset, ha_mask = cc_calibrate(wkspName, peakpos3, peakpos3-peak_width, peakpos3+peak_width, [6468, 24900-1],
                                          ref_ws_index, cc_number, 1, -0.0003, 'high_angle')

    save_calibration(wkspName, [(west_offset, west_mask), (east_offset, east_mask), (ha_offset, ha_mask)], group_ws_name, 'vulcan_vz_test')

    return


def peak_function(vec_x, peak_intensity, peak_center, peak_sigma, bkgd_a0, bkgd_a1, function_type):
    """

    :param vec_x:
    :param function_type:
    :return:
    """
    # gaussian:
    vec_y = peak_intensity * numpy.exp(-0.5*(vec_x - peak_center)**2/peak_sigma**2) + bkgd_a0 + bkgd_a1 * vec_x

    return vec_y


def evaluate_cc_quality(data_ws_name, fit_param_table_name):
    """

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


def main(argv):
    """

    :param argv:
    :return:
    """
    if len(argv) == 0:
        # default
        nxs_file_name = 'VULCAN_150178_HighResolution_Diamond.nxs'
    else:
        # user specified
        nxs_file_name = argv[0]

    # decide to load or not and thus group workspace
    diamond_ws_name, group_ws_name = initialize_calibration(nxs_file_name, False)
        
    cross_correlate_vulcan_data(diamond_ws_name, group_ws_name)


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




