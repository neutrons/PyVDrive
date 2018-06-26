"""
Mantid reduction scripts
"""
import mantid.simpleapi as mantidapi
from mantid.api import AnalysisDataService as ADS
import numpy
import os
import datatypeutility
import mantid_helper

VULCAN_FOCUS_CAL = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5'
VULCAN_FOCUS_CAL_GEN1 = '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'


def align_instrument(matrix_ws, diff_cal_ws_name):
    """
    align whole instrument
    :param matrix_ws:
    :return:
    """
    # Align detector
    mantidapi.AlignDetectors(InputWorkspace=matrix_ws,
                             OutputWorkspace=matrix_ws,
                             CalibrationWorkspace=diff_cal_ws_name)

    return


def align_and_focus_event_ws(event_ws_name, output_ws_name, binning_params,
                             diff_cal_ws_name, mask_ws_name, grouping_ws_name,
                             keep_raw_ws, reduction_params_dict, convert_to_matrix=False):
    """
    align and focus event workspace
    :param event_ws_name:
    :param output_ws_name:
    :param binning_params:
    :param diff_cal_ws_name:
    :param mask_ws_name:
    :param grouping_ws_name:
    :param keep_raw_ws:
    :param reduction_params_dict:
    :param convert_to_matrix:
    :return:
    """
    # check input
    if not mantid_helper.is_event_workspace(event_ws_name):
        raise RuntimeError('Input {0} is not an EventWorkspace'.format(event_ws_name))
    if not mantid_helper.is_calibration_workspace(diff_cal_ws_name):
        diff_ws = mantid_helper.retrieve_workspace(diff_cal_ws_name)
        raise RuntimeError('Input {0} is not a Calibration workspace but a {1}'.format(diff_cal_ws_name,
                                                                                       diff_ws.__class__.__name__))
    if not mantid_helper.is_masking_workspace(mask_ws_name):
        raise RuntimeError('Input {0} is not a Masking workspace'.format(mask_ws_name))
    if not mantid_helper.is_grouping_workspace(grouping_ws_name):
        raise RuntimeError('Input {0} is not a grouping workspace'.format(grouping_ws_name))

    datatypeutility.check_dict('Reduction parameter dictionary', reduction_params_dict)

    # set some fags
    if event_ws_name == output_ws_name:
        keep_raw_ws = True

    # Compress events
    compress_events_tolerance = reduction_params_dict['CompressEvents']['Tolerance']
    mantidapi.CompressEvents(InputWorkspace=event_ws_name,
                             OutputWorkspace=output_ws_name,
                             Tolerance=compress_events_tolerance)

    # Mask detectors
    mask_detectors_by_mask_ws(output_ws_name, mask_ws_name)

    # Align detector
    mantidapi.AlignDetector(InputWorkspace=event_ws_name,
                            OutputWorkspace=output_ws_name,
                            CalibratoionWorkspace=diff_cal_ws_name)

    # Sort events
    mantidapi.SortEvents(InputWorkspace=output_ws_name,
                         SortBy='X Value')

    # Diffraction focus
    mantidapi.DiffractionFocussing(InputWorkspace=output_ws_name,
                                   OutputWorkspace=output_ws_name,
                                   GroupingWorkspace=grouping_ws_name,
                                   PreserveEvents=not convert_to_matrix)

    # Sort again!
    mantidapi.SortEvents(InputWorkspace=output_ws_name,
                         SortBy='X Value')

    # Edit instrument
    mantidapi.EditInstrumentGeometry(Workspace=output_ws_name,
                                     PrimaryFlightPath=mantid_helper.VULCAN_L1,
                                     SpectrumIDs=reduction_params_dict['EditInstrumentGeometry']['SpectrumIDs'],
                                     L2=reduction_params_dict['EditInstrumentGeometry']['L2'],
                                     Polar=reduction_params_dict['EditInstrumentGeometry']['Polar'],
                                     Azimuthal=reduction_params_dict['EditInstrumentGeometry']['Azimuthal'])

    # rebin
    if binning_params is not None:
        mantid_helper.rebin(workspace_name=output_ws_name, params=binning_params, preserve=not convert_to_matrix)

    # remove
    if not keep_raw_ws:
        mantid_helper.delete_workspace(event_ws_name)

    return


def mask_detectors_by_mask_ws(workspace_name, mask_ws_name):
    """
    mask detectors by masking workspace
    :param workspace_name:
    :param mask_ws_name:
    :return:
    """
    # TODO/FIXME/NOWNOW - Need to find out by AlignAndFocusPowder()
    raise NotImplementedError('ASAP')


def align_and_focus(run_number, nexus_file_name, target_unit, binning_parameters, convert_to_matrix):
    """
    align and focus a run
    :param run_number:
    :param nexus_file_name:
    :param target_unit:
    :param binning_parameters:
    :param convert_to_matrix:
    :return:
    """




    """

    :param nexus_file_name:
    :param target_unit:
    :return:
    """
    # check inputs ... blabla

    # load data
    output_ws_name = 'VULCAN_{0}_events'.format(run_number)
    mantidapi.Load(Filename=nexus_file_name, OutputWorkspace=output_ws_name)
    mantidapi.CompressEvents(InputWorkspace=output_ws_name,
                             OutputWorkspace=output_ws_name,
                             Tolerance='0.01')

    # calibration file
    if output_ws_name.endswith('h5'):
        cal_file_name = VULCAN_FOCUS_CAL
    else:
        cal_file_name = VULCAN_FOCUS_CAL_GEN1

    # align and focus
    final_ws_name = 'VULCAN_{0}'.format(run_number)
    print output_ws_name
    print final_ws_name
    print cal_file_name

    # output is TOF
    mantidapi.AlignAndFocusPowder(InputWorkspace=output_ws_name,
                                  OutputWorkspace=final_ws_name,
                                  CalFileName=cal_file_name,
                                  Params='-0.001',
                                  DMin='0.5', DMax='3.5',
                                  PreserveEvents=True)

    # clean
    mantidapi.DeleteWorkspace(Workspace=output_ws_name)

    # convert unit
    if target_unit == 'dSpacing':
        mantidapi.ConvertUnits(InputWorkspace=final_ws_name,
                               OutputWorkspace=final_ws_name,
                               Target='dSpacing',
                               EMode='Elastic')

    # binning
    mantidapi.Rebin(InputWorkspace=final_ws_name,
                    OutputWorkspace=final_ws_name,
                    Params=numpy.array(binning_parameters))

    return final_ws_name


def save_ws_ascii(ws_name, output_directory, base_name):
    """

    :param ws_name:
    :param output_directory:
    :param base_name:
    :return:
    """
    # check input blabla
    mantidapi.SaveAscii(InputWorkspace=ws_name, Filename=os.path.join(output_directory, base_name),
                        Separator='Space')

    return
