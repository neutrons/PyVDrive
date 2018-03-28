# script to do cross-correlation
import os
from mantid.api import AnalysisDataService as mtd
from mantid.simpleapi import CrossCorrelate, GetDetectorOffsets, SaveCalFile, ConvertDiffCal, SaveDiffCal
from mantid.simpleapi import RenameWorkspace, Plus
import bisect


def cc_calibrate(ws_name, peak_position, peak_min, peak_max, ws_index_range, reference_ws_index, cc_number, max_offset,
                 binning, index=''):
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
    print ('Reference spectra=%s' % reference_ws_index)

    # Cross correlate spectra using interval around peak at peakpos (d-Spacing)
    cc_ws_name = 'cc_' + ws_name + '_' + index
    CrossCorrelate(InputWorkspace=ws_name,
                   OutputWorkspace=cc_ws_name,
                   ReferenceSpectra=reference_ws_index,
                   WorkspaceIndexMin=ws_index_range[0], WorkspaceIndexMax=ws_index_range[1],
                   XMin=peak_min, XMax=peak_max)

    # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
    offset_ws_name = ws_name+"offset"+index
    mask_ws_name = ws_name+"mask"+index
    GetDetectorOffsets(InputWorkspace=cc_ws_name,
                       OutputWorkspace=offset_ws_name, MaskWorkspace=mask_ws_name,
                       Step=abs(binning),
                       DReference=peak_position,
                       XMin=-cc_number, XMax=cc_number,
                       MaxOffset=max_offset)

    # check result and remove interval result
    if False and mtd.doesExist(ws_name+"cc"+index):
        mtd.remove(ws_name+"cc")

    return offset_ws_name, mask_ws_name


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

    for ituple in range(1, len(offset_mask_list)):
        offset_ws_name_i, mask_ws_name_i = offset_mask_list[ituple]
        Plus(LHSWorkspace=offset_ws_name, RHSWorkspace=offset_ws_name_i,
             OutputWorkspace=offset_ws_name)
        Plus(LHSWorkspace=mask_ws_name, RHSWorkspace=mask_ws_name_i,
             OutputWorkspace=mask_ws_name)

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

    print ('Calibration file is saved as {0}'.format(out_file_name))

    return calib_ws_name, offset_ws_name, mask_ws_name


def cross_correlate_vulcan_data(wkspName, group_ws_name):
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

    ref_ws_index = 1613
    peak_width = 0.04   # modified from 0.005
    cc_number = 80
    west_offset, west_mask = cc_calibrate(wkspName, peakpos1, peakpos1-peak_width, peakpos1+peak_width, [0, 3234-1],
                                          ref_ws_index, cc_number, 1, -0.0003, 'west')

    ref_ws_index = 4847
    peak_width = 0.04
    cc_number = 80
    east_offset, east_mask = cc_calibrate(wkspName, peakpos2, peakpos2-peak_width, peakpos2+peak_width, [3234, 6468-1],
                                          ref_ws_index, 80, 1, -0.0003, 'east')
                                          
    ref_ws_index = 15555
    peak_width = 0.01
    cc_number = 20
    ha_offset, ha_mask = cc_calibrate(wkspName, peakpos3, peakpos3-peak_width, peakpos3+peak_width, [6468, 24900-1],
                                          ref_ws_index, cc_number, 1, -0.0003, 'high_angle')

    save_calibration(wkspName, [(west_offset, west_mask), (east_offset, east_mask), (ha_offset, ha_mask)], group_ws_name, 'vulcan_vz_test')

    return


def peak_function(vec_x, function_type):
    """

    :param vec_x:
    :param function_type:
    :return:
    """
    # gaussian:
    vec_y = peak_inensity * numpy.exp(-(vec_x - peak_center)**2/peak_sigma**2) + bkgd_a0 + bkgd_a1 * vec_x

    return vec_y


def evaluate_cc_quality(data_ws_name, fit_param_table_name):
    """

    :param data_ws_name:
    :param fit_param_table_name:
    :return:
    """
    data_ws = AnalysisDataService.retrieve(data_ws_name)
    param_table_ws = AnalysisDataService.retrieve(fit_param_table_name)

    cost_list = list()

    for row_index in range(param_table_ws.rowCount()):

        ws_index = param_table_ws.cell(row_index, 0)
        peak_pos = param_table_ws.cell(row_index, 1)
        peak_height = param_table_ws.cell(row_index, 2)
        peak_sigma = param_table_ws.cell(row_index, 3)
        bkgd_a0 = param_table_ws.cell(row_index, 4)
        bkgd_a1 = param_table_ws.cell(row_index, 5)

        peak_fwhm = peak_sigma * whatever

        x_min = peak_pos - 0.5 * peak_fwhm
        x_max = peak_pos + 0.5 * peak_fwhm

        vec_x = data_ws.readX(ws_index)
        i_min = bisect.bisect(vec_x, x_min)
        i_max = bisect.bisect(vec_x, x_max)

        vec_x = vec_x[i_min:i_max]
        obs_y = data_ws.readY(ws_index)[i_min:i_max]
        model_y = peak_function(vec_x)
        cost = numpy.sqrt(sumpy.sum((model_y - obs_y)**2))/len(obs_y)

        cost_list.append([ws_index, cost])
    # END-FOR

    return cost_list


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
    if AnalysisDataService.doesExist('vulcan_diamond') is False:
        diamond_ws = Load(Filename=nxs_file_name, OutputWorkspace='vulcan_diamond')
        CreateGroupingWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_group')
        cross_correlate_vulcan_data(diamond_ws.name(), 'vulcan_group')
