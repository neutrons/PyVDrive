"""
Mantid reduction scripts
"""
import mantid.simpleapi as mantidapi
import numpy
import os
from pyvdrive.lib import datatypeutility
from pyvdrive.lib import mantid_helper


class VulcanBinningHelper(object):
    """ This is a class that provides a set of static methods to handling binning for VDRIVE
    """

    def __init__(self):
        """
        initialization
        :return:
        """
        raise NotImplementedError('VulcanBinningHelper shall not be initialized.'
                                  'It is designed to be used as a collection of '
                                  'static methods')

    @staticmethod
    def create_nature_bins(num_banks, east_west_binning_parameters, high_angle_binning_parameters):
        """
        create binning parameters
        :param num_banks:
        :param east_west_binning_parameters:
        :param high_angle_binning_parameters:
        :return:
        """
        binning_parameter_dict = dict()
        if num_banks == 3:
            # west(1), east(1), high(1)
            for bank_id in range(1, 3):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            binning_parameter_dict[3] = high_angle_binning_parameters
        elif num_banks == 7:
            # west (3), east (3), high (1)
            for bank_id in range(1, 7):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            binning_parameter_dict[7] = high_angle_binning_parameters
        elif num_banks == 27:
            # west (9), east (9), high (9)
            for bank_id in range(1, 19):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            for bank_id in range(19, 28):
                binning_parameter_dict[bank_id] = high_angle_binning_parameters
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))

        return binning_parameter_dict


def align_instrument(matrix_ws, diff_cal_ws_name):
    """align whole instrument

    Parameters
    ----------
    matrix_ws
    diff_cal_ws_name

    Returns
    -------

    """
    # Align detector
    mantidapi.AlignDetectors(InputWorkspace=matrix_ws,
                             OutputWorkspace=matrix_ws,
                             CalibrationWorkspace=diff_cal_ws_name)

    return


def align_and_focus_event_ws(event_ws_name, output_ws_name, binning_params,
                             diff_cal_ws_name, grouping_ws_name,
                             reduction_params_dict, convert_to_matrix):
    """ Align and focus event workspace.  The procedure to reduce from the EventNexus includes
    1. compress event
    2. mask workspace
    3. align detectors
    4. sort events
    5. diffraction focus
    6. sort events
    7. edit instruments
    8. rebin (uniform binning)
    Output: still event workspace
    :exception RuntimeError: intolerable error
    :param event_ws_name:
    :param output_ws_name:
    :param binning_params:
    :param diff_cal_ws_name:
    :param grouping_ws_name:
    :param reduction_params_dict:
    :param convert_to_matrix:
    :return: string as ERROR message
    """
    # check inputs
    if not mantid_helper.is_event_workspace(event_ws_name):
        raise RuntimeError('Input {0} is not an EventWorkspace'.format(event_ws_name))
    if not mantid_helper.is_calibration_workspace(diff_cal_ws_name):
        diff_ws = mantid_helper.retrieve_workspace(diff_cal_ws_name)
        raise RuntimeError('Input {0} is not a Calibration workspace but a {1}'.format(diff_cal_ws_name,
                                                                                       diff_ws.__class__.__name__))
    # if not mantid_helper.is_masking_workspace(mask_ws_name):
    #     raise RuntimeError('Input {0} is not a Masking workspace'.format(mask_ws_name))
    if not mantid_helper.is_grouping_workspace(grouping_ws_name):
        raise RuntimeError('Input {0} is not a grouping workspace'.format(grouping_ws_name))

    datatypeutility.check_dict('Reduction parameter dictionary', reduction_params_dict)

    # Align detector
    mantidapi.AlignDetectors(InputWorkspace=event_ws_name,
                             OutputWorkspace=output_ws_name,
                             CalibrationWorkspace=diff_cal_ws_name)

    # # Mask detectors
    # mantid_helper.mask_workspace(to_mask_workspace_name=output_ws_name,
    #                              mask_workspace_name=mask_ws_name)

    # Sort events
    mantidapi.SortEvents(InputWorkspace=output_ws_name,
                         SortBy='X Value')

    # Diffraction focus
    event_ws = mantid_helper.retrieve_workspace(output_ws_name)
    if event_ws.getNumberEvents() == 0:
        print('[DB...BAT] {}: # events = {}'.format(event_ws, event_ws.getNumberEvents()))
        error_message = 'Unable to reduced {} as number of events = 0'.format(event_ws_name)
        raise RuntimeError(error_message)

    mantidapi.DiffractionFocussing(InputWorkspace=output_ws_name,
                                   OutputWorkspace=output_ws_name,
                                   GroupingWorkspace=grouping_ws_name,
                                   PreserveEvents=True)
    # Sort again!
    mantidapi.SortEvents(InputWorkspace=output_ws_name,
                         SortBy='X Value')

    # Compress events as an option
    if 'CompressEvents' in reduction_params_dict:
        compress_events_tolerance = reduction_params_dict['CompressEvents']['Tolerance']
        print('[DB...BAT] User-specified compress tolerance = {}'.format(compress_events_tolerance))
        mantidapi.CompressEvents(InputWorkspace=output_ws_name,
                                 OutputWorkspace=output_ws_name,
                                 Tolerance=1.E-5)

    # rebin
    if binning_params is not None:
        mantid_helper.rebin(workspace_name=output_ws_name,
                            params=binning_params, preserve=not convert_to_matrix)

    # Edit instrument as an option
    if 'EditInstrumentGeometry' in reduction_params_dict:
        try:
            # TODO - NIGHT - In case the number of histograms of output workspace does not match (masked a lot) ...
            # TODO - FIXME - 27 bank Polar and Azimuthal are all None
            print(reduction_params_dict['EditInstrumentGeometry'].keys())
            print(output_ws_name)
            print(mantid_helper.VULCAN_L1)
            print(reduction_params_dict['EditInstrumentGeometry']['SpectrumIDs'])
            print(reduction_params_dict['EditInstrumentGeometry']['L2'])
            print(reduction_params_dict['EditInstrumentGeometry']['Polar'])
            print(reduction_params_dict['EditInstrumentGeometry']['Azimuthal'])

            mantidapi.EditInstrumentGeometry(Workspace=output_ws_name,
                                             PrimaryFlightPath=mantid_helper.VULCAN_L1,
                                             SpectrumIDs=reduction_params_dict['EditInstrumentGeometry']['SpectrumIDs'],
                                             L2=reduction_params_dict['EditInstrumentGeometry']['L2'],
                                             Polar=reduction_params_dict['EditInstrumentGeometry']['Polar'],
                                             Azimuthal=reduction_params_dict['EditInstrumentGeometry']['Azimuthal'])
            """
            Workspace
            PrimaryFlightPath
            SpectrumIDs
            L2
            Polar
            Azimuthal
            DetectorIDs
            InstrumentName
            """
        except RuntimeError as run_err:
            error_message = 'Non-critical failure on EditInstrumentGeometry: {}\n'.format(run_err)
            return error_message

    return ''


# TODO - This method shall be refactored with align_and_focus_event_ws - FIXME
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
    # check inputs ... blabla

    # load data
    output_ws_name = 'VULCAN_{0}_events'.format(run_number)
    mantidapi.Load(Filename=nexus_file_name, OutputWorkspace=output_ws_name)
    mantidapi.CompressEvents(InputWorkspace=output_ws_name,
                             OutputWorkspace=output_ws_name,
                             Tolerance='0.01')

    # TODO FIXME - the calibration file name shall be set from user configuration through function method
    VULCAN_FOCUS_CAL = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5'
    VULCAN_FOCUS_CAL_GEN1 = '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'

    # calibration file
    if output_ws_name.endswith('h5'):
        cal_file_name = VULCAN_FOCUS_CAL
    else:
        cal_file_name = VULCAN_FOCUS_CAL_GEN1

    # align and focus
    final_ws_name = 'VULCAN_{0}'.format(run_number)
    print(output_ws_name)
    print(final_ws_name)
    print(cal_file_name)

    # output is TOF
    mantidapi.AlignAndFocusPowder(InputWorkspace=output_ws_name,
                                  OutputWorkspace=final_ws_name,
                                  CalFileName=cal_file_name,
                                  Params='-0.001',
                                  DMin='0.5', DMax='3.5',
                                  PreserveEvents=not convert_to_matrix)

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

    workspace = mantid_helper.retrieve_workspace(ws_name)
    print('[DB...BAT] {0} has {1} spectra'.format(ws_name, workspace.getNumberHistograms()))
    for ws_index in range(workspace.getNumberHistograms()):
        spec_id = ws_index + 1
        mantidapi.SaveAscii(InputWorkspace=ws_name,
                            Filename=os.path.join(output_directory, base_name +
                                                  '_Spec{0}.dat'.format(spec_id)),
                            Separator='Space',
                            SpectrumList='{0}'.format(ws_index))

    return
