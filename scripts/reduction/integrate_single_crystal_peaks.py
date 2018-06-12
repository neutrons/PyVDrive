#!/usr/bin/python
# Goal: Integrate single crystal peaks given ROI file and run number
import sys
import os
import pyvdrive.lib.mantid_helper as mantid_api
import pyvdrive.lib.vulcan_util as vulcan_util
import pyvdrive.lib.archivemanager as vulcan_archive
import pyvdrive.lib.geometry_utilities as vulcan
import pyvdrive.lib.mantid_reduction as reduction


def integrate_single_crystal_peak(ws_name, mask_ws_name, central_d, delta_d):
    """

    :param ws_name:
    :param mask_ws_name:
    :param central_d:
    :param delta_d:
    :return:
    """
    # get unmasked detector from mask workspace
    roi_det_list = mantid_api.get_detectors_in_roi(mask_ws_name)
    print ('Detectors are interested: {0}'.format(roi_det_list))

    # get the detector id list for rows and columns
    workspace = mantid_api.retrieve_workspace(ws_name, raise_if_not_exist=True)
    is_pre_ned = workspace.getNumberHistograms() < 7000
    vulcan_instrument = vulcan.VulcanGeometry(is_pre_ned)
    panel_row_set, panel_col_set = vulcan_instrument.get_detectors_rows_cols(roi_det_list)
    panel_complete_row_list = vulcan_instrument.get_detectors_in_row(list(panel_row_set))
    panel_complete_col_list = vulcan_instrument.get_detectors_in_column(list(panel_col_set))

    # align detectors
    # need a lot of work on this TODO! about how to locate the calibration file!
    reduction.align_workspace(ws_name, output=ws_name, calibration=whatever)

    # sum spectra
    for detid_list in [panel_complete_col_list, panel_complete_row_list]:
        mantid_api.sum_spectra(ws_name, ws_name, detid_list)
        mantid_api.save_ascii(ws_name)

    return


def main(argv):
    """
    main input
    :param argv:
    :return:
    """
    if len(argv) == 1:
        print ('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d]'
               '"'.format(argv[0]))
        sys.exit(0)

    # get inputs
    try:
        ipts_number = int(argv[1])
        run_number = int(argv[2])
        roi_file_name = str(argv[3])
        central_d = float(argv[4])
        delta_d = float(argv[5])
    except IndexError:
        print ('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d]'
               '"'.format(argv[0]))
        sys.exit(1)
    except ValueError:
        print ('Integrate single crystal peaks\nRun: "{0} [IPTS] [Run Number] [ROI File] [d-value] [delta d]'
               '"'.format(argv[0]))
        sys.exit(1)

    # check
    if delta_d < 0 or central_d < 0 or central_d > 20.:
        print ('d and delta(d) are not valid')
        sys.exit(1)
    if os.path.exists(roi_file_name) is False:
        print ('ROI file {0} does not exist.'.format(roi_file_name))
        sys.exit(1)

    # load data
    nxs_file_name = vulcan_archive.sns_archive_nexus_path(ipts_number, run_number)
    out_ws_name = 'VULCAN_{0}_events'.format(run_number)
    mantid_api.load_nexus(data_file_name=nxs_file_name, output_ws_name=out_ws_name, meta_data_only=False)

    # load geometry
    mask_ws_name = mantid_api.load_roi_xml(out_ws_name, roi_file_name)

    # integrate
    integrate_single_crystal_peak(out_ws_name, mask_ws_name, central_d, delta_d)

    return


if __name__ == '__main__':
    if False:
        argv = sys.argv
    else:
        argv = ['blabla', '21356', '161394', 'tests/data/highangle_roi_0607.xml', '1.2', '0.5']
    main(argv)
