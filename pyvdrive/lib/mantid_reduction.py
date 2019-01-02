"""
Mantid reduction scripts
"""
import mantid.simpleapi as mantidapi
from mantid.api import AnalysisDataService
from mantid.simpleapi import ExtractSpectra, RenameWorkspace, Rebin, ConvertToPointData, ConjoinWorkspaces, SaveGSS
import numpy
import os
import datatypeutility
import mantid_helper
import h5py


VULCAN_FOCUS_CAL = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5'
VULCAN_FOCUS_CAL_GEN1 = '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'


class VulcanBinningHelper(object):
    """ This is a class that provides a set of static methods to handling binning for VDRIVE
    """
    def __init__(self):
        """
        initialization
        :return:
        """
        raise NotImplementedError('VulcanBinningHelper shall be removed')

    def __str__(self):
        """
        helping methods
        :return:
        """
        help_str = 'Vulcan-Binning-Helper:\n'
        help_str += 'Create bins: (1) create_nature_bins (2) create_idl_bins\n'
        help_str += 'Rebin      : rebin_workspace'

        return help_str

    @staticmethod
    def create_idl_bins(num_banks, h5_bin_file_name):
        """
        Create a dictionary with list of IDL-VDRIVE TOF
        :param num_banks:
        :param h5_bin_file_name:
        :return:
        """
        # use explicitly defined bins and thus matrix workspace is required
        # import h5 file
        # load vdrive bin file to 2 different workspaces
        bin_file = h5py.File(h5_bin_file_name, 'r')
        west_east_bins = bin_file['west_east_bank'][:]
        high_angle_bins = bin_file['high_angle_bank'][:]
        bin_file.close()

        # convert a list of bin boundaries to x1, dx, x2, dx, ... style
        west_east_bin_params = west_east_bins
        high_angle_bin_params = high_angle_bins

        binning_parameter_dict = dict()
        bank_tof_sets = list()
        if num_banks == 3:
            # west(1), east(1), high(1)
            # west(1), east(1), high(1)
            for bank_id in range(1, 3):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[3] = high_angle_bin_params

            bank_tof_sets.append(([1, 2], west_east_bins))
            bank_tof_sets.append(([3], high_angle_bins))

        elif num_banks == 7:
            # west (3), east (3), high (1)
            for bank_id in range(1, 7):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[7] = high_angle_bin_params

            bank_tof_sets.append((range(1, 7), west_east_bins))
            bank_tof_sets.append(([7], high_angle_bins))

        elif num_banks == 27:
            # west (9), east (9), high (9)
            for bank_id in range(1, 19):
                binning_parameter_dict[bank_id] = west_east_bin_params
            for bank_id in range(19, 28):
                binning_parameter_dict[bank_id] = high_angle_bin_params

            bank_tof_sets.append((range(1, 19), west_east_bins))
            bank_tof_sets.append((range(19, 28), high_angle_bins))

        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
        # END-IF-ELSE

        # return binning_parameter_dict

        return bank_tof_sets

    @staticmethod
    def create_idl_bins_2(num_banks, h5_bin_file_name):
        """
        create a Mantid to VDRIVE-IDL mapping binning
        :param num_banks:
        :param h5_bin_file_name:
        :return: dictionary: [Bank-ID] = vector of binning parameters
        """
        def process_bins_to_binning_params(bins_vector):
            """
            convert a list of bin boundaries to x1, dx, x2, dx, ... style
            :param bins_vector:
            :return:
            """
            assert isinstance(bins_vector, numpy.ndarray)
            assert len(bins_vector.shape) == 1

            delta_tof_vec = bins_vector[1:] - bins_vector[:-1]

            bin_param = numpy.empty((bins_vector.size + delta_tof_vec.size), dtype=bins_vector.dtype)
            bin_param[0::2] = bins_vector
            bin_param[1::2] = delta_tof_vec

            # extrapolate_last_bin
            delta_bin = (bins_vector[-1] - bins_vector[-2]) / bins_vector[-2]
            next_x = bins_vector[-1] * (1 + delta_bin)

            # append last value for both east/west bin and high angle bin
            numpy.append(bin_param, delta_bin)
            numpy.append(bin_param, next_x)

            return bin_param

        # use explicitly defined bins and thus matrix workspace is required
        # import h5 file
        # load vdrive bin file to 2 different workspaces
        bin_file = h5py.File(h5_bin_file_name, 'r')
        west_east_bins = bin_file['west_east_bank'][:]
        high_angle_bins = bin_file['high_angle_bank'][:]
        bin_file.close()

        # convert a list of bin boundaries to x1, dx, x2, dx, ... style
        west_east_bin_params = process_bins_to_binning_params(west_east_bins)
        high_angle_bin_params = process_bins_to_binning_params(high_angle_bins)

        binning_parameter_dict = dict()
        if num_banks == 3:
            # west(1), east(1), high(1)
            # west(1), east(1), high(1)
            for bank_id in range(1, 3):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[3] = high_angle_bin_params
        elif num_banks == 7:
            # west (3), east (3), high (1)
            for bank_id in range(1, 7):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[7] = high_angle_bin_params
        elif num_banks == 27:
            # west (9), east (9), high (9)
            for bank_id in range(1, 19):
                binning_parameter_dict[bank_id] = west_east_bin_params
            for bank_id in range(19, 28):
                binning_parameter_dict[bank_id] = high_angle_bin_params
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
        # END-IF-ELSE

        return binning_parameter_dict

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

    @staticmethod
    def rebin_workspace(input_ws, binning_param_dict, output_ws_name):
        """
        rebin input workspace with user specified binning parameters and support various number of bins across
        the whole spectra
        The algorithm is modified from Mantid.SaveVulcanGSS
        :param input_ws:
        :param binning_param_dict:
        :param output_ws_name:
        :return:
        """
        # check
        datatypeutility.check_dict('Binning parameters', binning_param_dict)
        datatypeutility.check_string_variable('Output workspace name', output_ws_name)

        # check input workspace
        if isinstance(input_ws, str):
            input_ws = AnalysisDataService.retrieve(input_ws)

        print ('[DB...BAT] binning dictionary keys: {}\n{}'.format(binning_param_dict.keys(), binning_param_dict))

        # check input binning parameters
        for ws_index in range(input_ws.getNumberHistograms()):
            bank_id = ws_index + 1
            bin_params = binning_param_dict[bank_id]
            if not isinstance(bin_params, str) and len(bin_params) % 2 == 0:
                # odd number and cannot be binning parameters
                raise RuntimeError('Binning parameter {0} of type {1} with size {2} cannot be accepted.'
                                   ''.format(bin_params, type(bin_params), len(bin_params)))
            elif isinstance(bin_params, str) and bin_params.count(',') % 2 == 1:
                raise RuntimeError('Binning parameter {0} (as a string) cannot be accepted.'
                                   ''.format(bin_params))
        # END-FOR

        # rebin input workspace: extract each single spectrum, rebinning and combine them back
        processed_single_spec_ws_list = list()
        for ws_index in range(input_ws.getNumberHistograms()):
            # rebin on each
            temp_out_name = output_ws_name + '_x_' + str(ws_index)
            processed_single_spec_ws_list.append(temp_out_name)
            # extract a spectrum out
            ExtractSpectra(input_ws, WorkspaceIndexList=[ws_index], OutputWorkspace=temp_out_name)
            # get binning parameter
            bin_params = binning_param_dict[ws_index + 1]  # bank ID
            Rebin(InputWorkspace=temp_out_name, OutputWorkspace=temp_out_name,
                  Params=bin_params, PreserveEvents=True)
            rebinned_ws = AnalysisDataService.retrieve(temp_out_name)
            print ('[WARNING] Rebinnd workspace Size(x) = {0}, Size(y) = {1}'.format(len(rebinned_ws.readX(0)),
                                                                                     len(rebinned_ws.readY(0))))

            # Upon this point, the workspace is still HistogramData.
            # Check whether it is necessary to reset the X-values to reference TOF from VDRIVE
            temp_out_ws = AnalysisDataService.retrieve(temp_out_name)
            if len(bin_params) == 2 * len(temp_out_ws.readX(0)) - 1:
                reset_bins = True
            else:
                reset_bins = False

            # convert to point data
            ConvertToPointData(InputWorkspace=temp_out_name, OutputWorkspace=temp_out_name)
            # align the bin boundaries if necessary
            temp_out_ws = AnalysisDataService.retrieve(temp_out_name)

            if reset_bins:
                # good to align:
                for tof_i in range(len(temp_out_ws.readX(0))):
                    temp_out_ws.dataX(0)[tof_i] = int(bin_params[2 * tof_i] * 10) / 10.
                # END-FOR (tof-i)
            # END-IF (align)
        # END-FOR

        # merge together
        RenameWorkspace(InputWorkspace=processed_single_spec_ws_list[0],
                        OutputWorkspace=output_ws_name)
        for ws_index in range(1, len(processed_single_spec_ws_list)):
            ConjoinWorkspaces(InputWorkspace1=output_ws_name,
                              InputWorkspace2=processed_single_spec_ws_list[ws_index])
        # END-FOR
        output_workspace = AnalysisDataService.retrieve(output_ws_name)

        # END-IF-ELSE

        return output_workspace


class VulcanGSASHelper(object):
    """
    This is a class that provides a set of static methods to handling binning and writing to GSAS for VDRIVE
    """
    def __init__(self):
        """
        initialization
        :return:
        """
        raise NotImplementedError('This shall be removed!')

    def __str__(self):
        """
        helping methods
        :return:
        """
        help_str = 'Vulcan-GSAS-Helper:\n'
        help_str += 'Binning: (1) create_nature_bins'
        help_str += 'Creating GSAS File: (1) create_vulcan_gsas_header() (2) create_bank_header'

    @staticmethod
    def create_bank_header(bank_id, vec_x):
        """
        create bank header of VDRIVE/GSAS convention
        as: BANK bank_id data_size data_size  binning_type 'SLOG' tof_min tof_max deltaT/T
        :param bank_id:
        :param vec_x:
        :return:
        """
        tof_min = vec_x[0]
        tof_max = vec_x[-1]
        delta_tof = (vec_x[1] - tof_min) / tof_min  # deltaT/T
        data_size = len(vec_x)

        bank_header = 'BANK {0} {1} {2} {3} {4} {5:.1f} {6:.7f} 0 FXYE' \
                      ''.format(bank_id, data_size, data_size, 'SLOG', tof_min, tof_max, delta_tof)

        bank_header = '{0:80s}'.format(bank_header)

        return bank_header

    @staticmethod
    def create_vulcan_gsas_header(workspace, gsas_file_name, ipts, parm_file_name):
        """
        create specific GSAS header required by VULCAN team/VDRIVE.
        It is found that calling Mantid for writing GSAS can cause contending among threads
        :param workspace:
        :param gsas_file_name:
        :param ipts:
        :param parm_file_name:
        :return:
        """
        # Get necessary information including title, run start, duration and etc.
        title = workspace.getTitle()

        # Get run object for sample log information
        run = workspace.getRun()

        # Get information on start/stop
        if run.hasProperty("run_start") and run.hasProperty("duration"):
            # have run start and duration information
            duration = float(run.getProperty("duration").value)

            # property run_start and duration exist
            utctime = numpy.datetime64(run.getProperty('run_start').value)
            time0 = numpy.datetime64("1990-01-01T00:00:00")
            total_nanosecond_start = int((utctime - time0) / numpy.timedelta64(1, 'ns'))
            total_nanosecond_stop = total_nanosecond_start + int(duration * 1.0E9)

        else:
            # not both property is found
            total_nanosecond_start = 0
            total_nanosecond_stop = 0
        # END-IF

        # self.log().debug("Start = %d, Stop = %d" % (total_nanosecond_start, total_nanosecond_stop))

        # Construct new header
        vulcan_gsas_header = list()

        if len(title) > 80:
            title = title[0:80]
        vulcan_gsas_header.append("%-80s" % title)

        vulcan_gsas_header.append("%-80s" % ("Instrument parameter file: %s" % parm_file_name))

        vulcan_gsas_header.append("%-80s" % ("#IPTS: %s" % str(ipts)))

        vulcan_gsas_header.append("%-80s" % "#binned by: Mantid")

        vulcan_gsas_header.append("%-80s" % ("#GSAS file name: %s" % os.path.basename(gsas_file_name)))

        vulcan_gsas_header.append("%-80s" % ("#GSAS IPARM file: %s" % parm_file_name))

        vulcan_gsas_header.append("%-80s" % ("#Pulsestart:    %d" % total_nanosecond_start))

        vulcan_gsas_header.append("%-80s" % ("#Pulsestop:     %d" % total_nanosecond_stop))

        vulcan_gsas_header.append('{0:80s}'.format('#'))

        return vulcan_gsas_header

    @staticmethod
    def save_vulcan_gsas(workspace_name, output_directory, ipts_number, run_number, parm_file_name):
        """
        save a workspace to VULCAN GSAS file name
        :param workspace_name:
        :return:
        """
        raise NotImplementedError('This method shall be replaced by SaveVulcanGSS')
        # TODO TODO - 20180813 - Doc & Check

        input_ws = AnalysisDataService.retrieve(workspace_name)
        if input_ws.isHistogramData():
            raise RuntimeError('Output workspace {0} of type {1} to export to {2} shall be point data '
                               'at this stage.'
                               ''.format(workspace_name, type(input_ws), workspace_name))

        # construct the headers
        gsas_file_name = os.path.join(output_directory, '{}.gda'.format(run_number))

        vulcan_gsas_header = VulcanGSASHelper.create_vulcan_gsas_header(input_ws, gsas_file_name, ipts_number,
                                                                        parm_file_name)

        vulcan_bank_headers = list()
        for ws_index in range(input_ws.getNumberHistograms()):
            bank_id = input_ws.getSpectrum(ws_index).getSpectrumNo()
            bank_header = VulcanGSASHelper.create_bank_header(bank_id, input_ws.readX(ws_index))
            vulcan_bank_headers.append(bank_header)
        # END-IF

        # Save
        try:
            print ('[DB...BAT] Save GSS to {} from {}'.format(gsas_file_name, format(input_ws)))
            SaveGSS(InputWorkspace=input_ws, Filename=gsas_file_name, SplitFiles=False, Append=False,
                    Format="SLOG", MultiplyByBinWidth=False,
                    ExtendedHeader=False,
                    UserSpecifiedGSASHeader=vulcan_gsas_header,
                    UserSpecifiedBankHeader=vulcan_bank_headers,
                    UseSpectrumNumberAsBankID=True,
                    SLOGXYEPrecision=[1, 1, 2])
        except RuntimeError as run_err:
            raise RuntimeError('Failed to call SaveGSS() due to {0}'.format(run_err))

        return


# END-DEF-CLASS


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
        print ('[DB...BAT] {}: # events = {}'.format(event_ws, event_ws.getNumberEvents()))
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
        print ('[DB...BAT] User-specified compress tolerance = {}'.format(compress_events_tolerance))
        mantidapi.CompressEvents(InputWorkspace=output_ws_name,
                                 OutputWorkspace=output_ws_name,
                                 Tolerance=1.E-5)

    # rebin
    if binning_params is not None:
        mantid_helper.rebin(workspace_name=output_ws_name, params=binning_params, preserve=not convert_to_matrix)

    # Edit instrument as an option
    if 'EditInstrumentGeometry' in reduction_params_dict:
        try:
            # TODO - NIGHT - In case the number of histograms of output workspace does not match (masked a lot) ...
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
    print ('[DB...BAT] {0} has {1} spectra'.format(ws_name, workspace.getNumberHistograms()))
    for ws_index in range(workspace.getNumberHistograms()):
        spec_id = ws_index + 1
        mantidapi.SaveAscii(InputWorkspace=ws_name,
                            Filename=os.path.join(output_directory, base_name + '_Spec{0}.dat'.format(spec_id)),
                            Separator='Space',
                            SpectrumList='{0}'.format(ws_index))

    return
