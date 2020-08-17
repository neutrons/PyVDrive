#!/usr/bin/python
# Goal: Integrate single crystal peaks given ROI file and run number
import sys
import os
import pyvdrive.lib.mantid_helper as mantid_api
import pyvdrive.lib.vulcan_util as vulcan_util
import pyvdrive.lib.archivemanager as vulcan_archive
import pyvdrive.lib.geometry_utilities as vulcan
import pyvdrive.lib.mantid_reduction as reduction

# Using default/latest calibration file
CALIBRATION_FILE_PATH = '/SNS/VULCAN/shared/CALIBRATION/2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5'


def integrate_single_crystal_peak(ws_name, mask_ws_name, central_d, delta_d, calib_ws_name):
    """

    :param ws_name:
    :param mask_ws_name:
    :param central_d:
    :param delta_d:
    :return:
    """
    # get unmasked detector from mask workspace
    roi_det_list = mantid_api.get_detectors_in_roi(mask_ws_name)
    print('Detectors are interested: {0}'.format(roi_det_list))

    # get the detector id list for rows and columns
    workspace = mantid_api.retrieve_workspace(ws_name, raise_if_not_exist=True)
    is_pre_ned = workspace.getNumberHistograms() < 7000
    vulcan_instrument = vulcan.VulcanGeometry(is_pre_ned)
    panel_row_set, panel_col_set = vulcan_instrument.get_detectors_rows_cols(roi_det_list)
    panel_complete_row_list = vulcan_instrument.get_detectors_in_row(list(panel_row_set))
    panel_complete_col_list = vulcan_instrument.get_detectors_in_column(list(panel_col_set))

    # side test : FIXME remove the next section as soon as test is over
    if True:
        # this section is for testing purpose only
        # names
        col_masked_ws = ws_name + '_column_masked'
        row_masked_ws = ws_name + '_row_masked'
        roi_ws = ws_name + '_roi'
        # cloning
        mantid_api.clone_workspace(ws_name, col_masked_ws)
        mantid_api.clone_workspace(ws_name, row_masked_ws)
        mantid_api.clone_workspace(ws_name, roi_ws)
        # mask
        mantid_api.mask_workspace_by_detector_ids(col_masked_ws, panel_complete_col_list)
        mantid_api.mask_workspace_by_detector_ids(row_masked_ws, panel_complete_row_list)
        mantid_api.mask_workspace_by_detector_ids(roi_ws, roi_det_list)
        # save for check
        mantid_api.generate_processing_history(row_masked_ws, 'mask_rows.py')
        mantid_api.save_event_workspace(col_masked_ws, 'column_masked.nxs')
        mantid_api.save_event_workspace(row_masked_ws, 'row_masked.nxs')
    # END-IF

    # align detectors
    reduction.align_instrument(ws_name, diff_cal_ws_name=calib_ws_name)
    mantid_api.mtd_convert_units(ws_name, 'dSpacing')
    mantid_api.rebin(ws_name, '-0.0003', preserve=False)

    # sum spectra
    for detid_list, file_name in [(roi_det_list, 'raw_roi'),
                                  (panel_complete_col_list, 'column'),
                                  (panel_complete_row_list, 'row')]:
        ws_index_list = vulcan_instrument.convert_detectors_to_wsindex(ws_name, detid_list)
        summed_ws_name = ws_name + '_' + file_name
        mantid_api.sum_spectra(ws_name, summed_ws_name, ws_index_list)
        mantid_api.crop_workspace(summed_ws_name, summed_ws_name,
                                  central_d - delta_d, central_d + delta_d)
        reduction.save_ws_ascii(summed_ws_name, './', file_name + '.dat')
    # ENDFOR

    return


def main(argv):
    """
    main input
    :param argv:
    :return:
    """
    if len(argv) == 1 or argv[0] == '--help':
        print('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d]'
              '"'.format(argv[0]))
        print('Example: > ./integrate_single_crystal_peaks 21356 161394 tests/data/highangle_roi_0607.xml 1.2 0.5')
        sys.exit(0)

    # get inputs
    try:
        print(argv[1])
        ipts_number = int(argv[1])
        print('IPTS = {0}'.format(ipts_number))
        run_number = int(argv[2])
        print('Run Number = {0}'.format(run_number))
        roi_file_name = str(argv[3])
        print('ROI File = {0}'.format(roi_file_name))
        central_d = float(argv[4])
        print('Peak Position (d-spacing) = {0}'.format(central_d))
        delta_d = float(argv[5])
        print('Peak range (d-spacing) = {0}'.format(delta_d))
    except IndexError:
        print('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d]  (too few arguments)'
              '"'.format(argv[0]))
        sys.exit(1)
    except ValueError:
        print('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d] (invalid value)'
              '"'.format(argv[0]))
        sys.exit(1)

    # check
    if delta_d < 0 or central_d < 0 or central_d > 20.:
        print('d and delta(d) are not valid')
        sys.exit(1)
    if os.path.exists(roi_file_name) is False:
        print('ROI file {0} does not exist.'.format(roi_file_name))
        sys.exit(1)

    # load data
    nxs_file_name = vulcan_archive.sns_archive_nexus_path(ipts_number, run_number)
    out_ws_name = 'VULCAN_{0}_events'.format(run_number)
    mantid_api.load_nexus(data_file_name=nxs_file_name,
                          output_ws_name=out_ws_name, meta_data_only=False)

    # load geometry
    mask_ws_name = mantid_api.load_roi_xml(out_ws_name, roi_file_name)

    # load calibration file
    mantid_api.load_calibration_file(
        CALIBRATION_FILE_PATH, output_name='VULCAN_SCX', ref_ws_name=out_ws_name)

    # integrate
    integrate_single_crystal_peak(out_ws_name, mask_ws_name, central_d, delta_d, 'VULCAN_SCX_cal')

    return


if __name__ == '__main__':
    if True:
        argv = sys.argv
    else:
        argv = ['blabla', '21356', '161394', 'tests/data/highangle_roi_0607.xml', '1.2', '0.5']
    main(argv)
