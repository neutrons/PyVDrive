# This is a class to slice and focus data for parallelization (multiple threading)
import time
from mantid.simpleapi import Load, LoadEventNexus, GenerateEventsFilter, FilterEvents, LoadDiffCal, AlignAndFocusPowder
from mantid.simpleapi import AlignDetectors, ConvertUnits, RenameWorkspace, ExtractSpectra, CloneWorkspace, Rebin
from mantid.simpleapi import ConvertToPointData, ConjoinWorkspaces, SaveGSS, Multiply, CreateWorkspace
from mantid.simpleapi import DiffractionFocussing, CreateEmptyTableWorkspace, CreateWorkspace
from mantid.simpleapi import EditInstrumentGeometry
from mantid.api import AnalysisDataService
import threading
import numpy
import os
import h5py
import time
import file_utilities
import datatypeutility
import mantid_mask as mask_util
import mantid_reduction
import mantid_helper

# chop data
# ipts = 18522
# run_number = 160560
# event_file_name = '/SNS/VULCAN/IPTS-13924/nexus/VULCAN_160989.nxs.h5'
# event_file_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(ipts, run_number)
# event_file_name = '/SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5'


# NOTE: Calibration file shall be made more flexible
# TODO - FIXME - 20180930 - Calibration file shall be disabled and passed in
CALIBRATION_FILES = {3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                     7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_7bank.h5',
                     27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_27bank.h5'}


class SliceFocusVulcan(object):
    """ Class to handle the slice and focus on vulcan data
    """
    def __init__(self, number_banks=3, num_threads=24, output_dir=None):
        """
        initialization
        :param number_banks:
        :param num_threads:
        """
        datatypeutility.check_int_variable('Number of banks', number_banks, [1, None])
        datatypeutility.check_int_variable('Number of threads', number_banks, [1, 256])

        if number_banks in CALIBRATION_FILES:
            # TODO FIXME - 20180822 - Calibration file or workspace shall be passed in
            # TODO       - continue - pre-nED is not supported due to this
            # TODO       - continue - flexible-bank (other than 3) is not supported due to this
            self._detector_calibration_file = CALIBRATION_FILES[number_banks]
            self._number_banks = number_banks
        else:
            raise RuntimeError('{0}-bank case is not supported.'.format(number_banks))

        # other directories
        self._output_dir = '/tmp/'
        if output_dir is not None:
            datatypeutility.check_file_name(output_dir, True, True, True, 'Output directory for generated GSAS')
            self._output_dir = output_dir

        # run number (current or coming)
        self._run_number = 0

        self._ws_name_dict = dict()
        self._last_loaded_event_ws = None
        self._last_loaded_ref_id = ''
        self._det_eff_ws_name = None

        # calibration, grouping and mask file
        self._diff_base_name = 'Vulcan_Bank{0}'.format(self._number_banks)
        self._diff_cal_ws_name = '{0}_cal'.format(self._diff_base_name)
        self._group_ws_name = '{0}_group'.format(self._diff_base_name)
        self._mask_ws_name = '{0}_mask'.format(self._diff_base_name)

        self._focus_instrument_dict = dict()
        self._init_focused_instruments()

        # multiple threading variables
        self._number_threads = num_threads

        return

    def __str__(self):
        """
        nice output
        :return:
        """
        return 'Slice and focus VULCAN data into {0}-bank with {1} threads'.format(self._number_banks,
                                                                                   self._number_threads)

    @staticmethod
    def create_bank_header(bank_id, vec_x):
        """
        create bank header of VDRIVE/GSAS convention
        as: BANK bank_id data_size data_size  binning_type 'SLOG' tof_min tof_max deltaT/T
        :param bank_id:
        :param vec_x:
        :return:
        """
        raise NotImplementedError('create_bank_header() Moved to mantid_reduction')

    @staticmethod
    def create_nature_bins(num_banks, east_west_binning_parameters, high_angle_binning_parameters):
        """
        create binning parameters
        :param num_banks:
        :param east_west_binning_parameters:
        :param high_angle_binning_parameters:
        :return:
        """
        raise NotImplementedError('(create_nature_bins) Moved to mantid_reduction')

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
        raise NotImplementedError('create_vulcan_gsas_header() Moved to mantid_reduction')

    def diffraction_focus(self, ref_id, binning, apply_det_efficiency):
        """
        Do diffraction focus to a workspace indexed by its reference ID
        :param ref_id:
        :param binning:
        :param apply_det_efficiency:
        :return:
        """
        # check input
        datatypeutility.check_string_variable('Workspace/data reference ID', ref_id)
        assert isinstance(binning, str) or isinstance(binning, numpy.ndarray) or isinstance(binning, list),\
            'Binning parameter {0} of type is not acceptible.'.format(binning, type(binning))

        # workspace
        if ref_id in self._ws_name_dict:
            ws_name = self._ws_name_dict[ref_id]
        else:
            raise RuntimeError('Workspace/data reference ID {0} does not exist.'.format(ref_id))

        # convert unit to d-spacing
        ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')

        # convert to matrix workspace to apply detector efficiency?
        convert_to_matrix = self._det_eff_ws_name is not None and apply_det_efficiency
        if apply_det_efficiency:
            # rebin
            Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params=binning, PreserveEvents=not convert_to_matrix)
            # apply detector efficiency
            Multiply(LHSWorkspace=ws_name, RHSWorkspace=self._det_eff_ws_name, OutputWorkspace=ws_name)

        # sum spectra: not binned well
        DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace=self._group_ws_name)

        return

    def _init_focused_instruments(self):
        """
        set up the dictionary for the instrument geometry after focusing
        each detector (virtual) will have 3 value as L2, polar (2theta) and azimuthal (phi)
        and the angles are in unit as degree
        :return:
        """
        # TODO - FIXME - 20181030 - There shall be 1 and only 1 place to define focused geometry in PyVDRive!
        # TODO                      Now it is diverted.  Grep L1 and _init_focused_instrument (same copy diffrent place)
        self._focus_instrument_dict['L1'] = 43.753999999999998

        # L2, Polar and Azimuthal
        self._focus_instrument_dict['L2'] = dict()
        self._focus_instrument_dict['Polar'] = dict()
        self._focus_instrument_dict['Azimuthal'] = dict()
        self._focus_instrument_dict['SpectrumIDs'] = dict()

        # east_bank = [2.0, 90., 0.]
        # west_bank = [2.0, -90., 0.]
        # high_angle_bank = [2.0, 155., 0.]

        # 2 bank
        self._focus_instrument_dict['L2'][2] = [2., 2.]
        self._focus_instrument_dict['Polar'][2] = [-90.,  90]
        self._focus_instrument_dict['Azimuthal'][2] = [0., 0.]
        self._focus_instrument_dict['SpectrumIDs'][2] = [1, 2]

        # 3 bank
        self._focus_instrument_dict['L2'][3] = [2., 2., 2.]
        self._focus_instrument_dict['Polar'][3] = [-90, 90., 155]
        self._focus_instrument_dict['Azimuthal'][3] = [0., 0, 0.]
        self._focus_instrument_dict['SpectrumIDs'][3] = [1, 2, 3]

        # 7 bank
        self._focus_instrument_dict['L2'][7] = None  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][7] = None
        self._focus_instrument_dict['Azimuthal'][7] = None
        self._focus_instrument_dict['SpectrumIDs'][7] = range(1, 8)

        # 27 banks
        self._focus_instrument_dict['L2'][27] = None  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][27] = None
        self._focus_instrument_dict['Azimuthal'][27] = None
        self._focus_instrument_dict['SpectrumIDs'][27] = range(1, 28)

        return

    def focus_workspace_list(self, ws_name_list, gsas_ws_name_list, binning_parameter_dict):
        """ Do diffraction focus on a list workspaces and also convert them to IDL GSAS
        This is the main execution body to be executed in multi-threading environment
        :param ws_name_list:
        :param binning_parameter_dict: dictionary for binning parameters. it is used for convert binning to VDRIVE-IDL
        :return:
        """
        datatypeutility.check_list('Workspace names', ws_name_list)
        datatypeutility.check_dict('Binning parameters dict', binning_parameter_dict)
        datatypeutility.check_list('(Output) GSAS workspace name list', gsas_ws_name_list)
        if len(ws_name_list) != len(gsas_ws_name_list):
            raise RuntimeError('Input workspace names {} have different number than output GSAS workspace names {}'
                               ''.format(ws_name_list, gsas_ws_name_list))

        for index in range(len(ws_name_list)):
            # check input
            ws_name = ws_name_list[index]
            gsas_ws_name = gsas_ws_name_list[index]
            datatypeutility.check_string_variable('Workspace name', ws_name)
            datatypeutility.check_string_variable('Output GSAS workspace name', gsas_ws_name)
            # skip empty workspace name that might be returned from FilterEvents
            if len(ws_name) == 0:
                continue
            # focus (simple) it is the same but simplied version in diffraction_focus()
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
            # diffraction focus
            DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
            # convert unit to TOF
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
            # edit instrument
            num_banks = 3
            EditInstrumentGeometry(Workspace=ws_name,
                                   PrimaryFlightPath=self._focus_instrument_dict['L1'],
                                   SpectrumIDs=self._focus_instrument_dict['SpectrumIDs'][num_banks],
                                   L2=self._focus_instrument_dict['L2'][num_banks],
                                   Polar=self._focus_instrument_dict['Polar'][num_banks],
                                   Azimuthal=self._focus_instrument_dict['Azimuthal'][num_banks])
            # convert VULCAN binning: to a different workspace that will be discarded after SaveVulcanGSS
            mantid_reduction.VulcanBinningHelper.rebin_workspace(input_ws=ws_name,
                                                                 binning_param_dict=binning_parameter_dict,
                                                                 output_ws_name=gsas_ws_name)
            # rebin the original workspace that won't be deleted and kept for visualization
            mantid_helper.rebin(ws_name, '3000., -0.001, 70000.', preserve=True)
        # END-FOR

        return

    def generate_output_workspace_name(self, event_file_name):
        """
        generate output workspace name from the input event file
        :param event_file_name:
        :return:
        """
        out_ws_name = os.path.basename(event_file_name).split('.')[0] + '_{0}banks'.format(self._number_banks)
        ref_id = out_ws_name

        return out_ws_name, ref_id

    def load_detector_eff_file(self, file_name):
        """
        load detector efficency factor file (HDF5)
        :param file_name:
        :return:
        """
        datatypeutility.check_file_name(file_name, check_exist=True, note='Detector efficiency (HDF5) file')

        try:
            returned = file_utilities.import_detector_efficiency(file_name)
            pid_vector = returned[0]
            det_eff_vector = returned[1]   # inverted efficiency.  so need to multiply
        except RuntimeError as run_err:
            raise RuntimeError('Unable to load detector efficiency file {0} due to {1}'.format(file_name,
                                                                                               run_err))

        # create the detector efficiency workspace
        self._det_eff_ws_name = os.path.basename(file_name).split(',')[0]
        CreateWorkspace(OutputWorkspace=self._det_eff_ws_name,
                        DataX=pid_vector,  # np.arange(len(det_eff_vector)),
                        DataY=det_eff_vector,
                        NSpec=len(det_eff_vector))

        return

    def load_data(self, event_file_name):
        """
        Load an event file
        :param event_file_name:
        :return:
        """
        datatypeutility.check_file_name(event_file_name, check_exist=True, note='Event data file')

        # generate output workspace and data key
        out_ws_name, data_key = self.generate_output_workspace_name(event_file_name)

        # keep it as the current workspace
        if event_file_name.endswith('.h5'):
            self._last_loaded_event_ws = LoadEventNexus(Filename=event_file_name, MetaDataOnly=False, Precount=True,
                                                        OutputWorkspace=out_ws_name)
        else:
            self._last_loaded_event_ws = Load(Filename=event_file_name, OutputWorkspace=out_ws_name)

        self._last_loaded_ref_id = data_key

        self._ws_name_dict[data_key] = out_ws_name

        return data_key

    def load_diff_calibration(self, base_name):
        """
        Load diffraction calibration file (.h5)
        :param base_name:
        :return:
        """
        datatypeutility.check_file_name(file_name=self._detector_calibration_file, check_exist=True,
                                        note='Diffraction calibration/group/mask file')

        # Load diffraction calibration file
        LoadDiffCal(InputWorkspace=self._last_loaded_event_ws,
                    Filename=self._detector_calibration_file,
                    WorkspaceName=base_name)

        return

    @staticmethod
    def rebin_workspace(input_ws, binning_param_dict, output_ws_name):
        """
        rebin input workspace with user specified binning parameters and support various number of bins across
        the whole spectra
        :param input_ws:
        :param binning_param_dict:
        :param output_ws_name:
        :return:
        """
        raise NotImplementedError('rebin_workspace() Moved to mantid_reduction')
        # # check
        # datatypeutility.check_dict('Binning parameters', binning_param_dict)
        # datatypeutility.check_string_variable('Output workspace name', output_ws_name)
        #
        # # check input workspace
        # if isinstance(input_ws, str):
        #     input_ws = AnalysisDataService.retrieve(input_ws)
        #
        # # check input binning parameters
        # for ws_index in range(input_ws.getNumberHistograms()):
        #     bank_id = ws_index + 1
        #     bin_params = binning_param_dict[bank_id]
        #     if not isinstance(bin_params, str) and len(bin_params) % 2 == 0:
        #         # odd number and cannot be binning parameters
        #         raise RuntimeError('Binning parameter {0} of type {1} with size {2} cannot be accepted.'
        #                            ''.format(bin_params, type(bin_params), len(bin_params)))
        #     elif isinstance(bin_params, str) and bin_params.count(',') % 2 == 1:
        #         raise RuntimeError('Binning parameter {0} (as a string) cannot be accepted.'
        #                            ''.format(bin_params))
        #
        # # rebin input workspace
        # processed_single_spec_ws_list = list()
        # for ws_index in range(input_ws.getNumberHistograms()):
        #     # rebin on each
        #     temp_out_name = output_ws_name + '_x_' + str(ws_index)
        #     processed_single_spec_ws_list.append(temp_out_name)
        #     # extract a spectrum out
        #     ExtractSpectra(input_ws, WorkspaceIndexList=[ws_index], OutputWorkspace=temp_out_name)
        #     # get binning parameter
        #     bin_params = binning_param_dict[ws_index + 1]  # bank ID
        #     Rebin(InputWorkspace=temp_out_name, OutputWorkspace=temp_out_name,
        #           Params=bin_params, PreserveEvents=True)
        #     rebinned_ws = AnalysisDataService.retrieve(temp_out_name)
        #     print ('[WARNING] Rebinnd workspace Size(x) = {0}, Size(y) = {1}'.format(len(rebinned_ws.readX(0)),
        #                                                                              len(rebinned_ws.readY(0))))
        #
        #     # Upon this point, the workspace is still HistogramData.
        #     # Check whether it is necessary to reset the X-values to reference TOF from VDRIVE
        #     temp_out_ws = AnalysisDataService.retrieve(temp_out_name)
        #     if len(bin_params) == 2 * len(temp_out_ws.readX(0)) - 1:
        #         reset_bins = True
        #     else:
        #         reset_bins = False
        #
        #     # convert to point data
        #     ConvertToPointData(InputWorkspace=temp_out_name, OutputWorkspace=temp_out_name)
        #     # align the bin boundaries if necessary
        #     temp_out_ws = AnalysisDataService.retrieve(temp_out_name)
        #
        #     if reset_bins:
        #         # good to align:
        #         for tof_i in range(len(temp_out_ws.readX(0))):
        #             temp_out_ws.dataX(0)[tof_i] = int(bin_params[2 * tof_i] * 10) / 10.
        #         # END-FOR (tof-i)
        #     # END-IF (align)
        # # END-FOR
        #
        # # merge together
        # RenameWorkspace(InputWorkspace=processed_single_spec_ws_list[0],
        #                 OutputWorkspace=output_ws_name)
        # for ws_index in range(1, len(processed_single_spec_ws_list)):
        #     ConjoinWorkspaces(InputWorkspace1=output_ws_name,
        #                       InputWorkspace2=processed_single_spec_ws_list[ws_index])
        # # END-FOR
        # output_workspace = AnalysisDataService.retrieve(output_ws_name)
        #
        # # END-IF-ELSE
        #
        # return output_workspace

    def save_nexus(self, ws_ref_id, output_file_name):
        """
        Save workspace to processed NeXus
        :param ws_ref_id:
        :param output_file_name:
        :return:
        """
        datatypeutility.check_string_variable('Workspace/data reference ID', ws_ref_id)

        if ws_ref_id in self._ws_name_dict:
            ws_name = self._ws_name_dict[ws_ref_id]
            file_utilities.save_workspace(ws_name, output_file_name, file_type='nxs')
        else:
            raise RuntimeError('Workspace/data reference ID {0} does not exist.'.format(ws_ref_id))

        return

    def set_run_number(self, run_number):
        """
        set the run number associated with current/next event file to slice
        :param run_number:
        :return:
        """
        self._run_number = run_number

    def slice_focus_event_workspace(self, event_file_name, event_ws_name, split_ws_name, info_ws_name,
                                    output_ws_base, binning_parameters, gsas_info_dict,
                                    roi_list, mask_list):
        """ Slice and diffraction focus event workspace with option to write the reduced data to GSAS file with
        SaveGSS().
        Each workspace is
        1. sliced from original event workspace
        2. diffraction focused
        3. optionally rebinned to IDL binning and read for SaveGSS()
        :param event_file_name:
        :param event_ws_name:
        :param split_ws_name:
        :param info_ws_name:
        :param output_ws_base:
        :param binning_parameters:
        :param gsas_info_dict: keys (IPTS, 'parm file' = 'vulcan.prm')
        :param roi_list:
        :param mask_list:
        :return: tuple: [1] slicing information, [2] output workspace names
        """
        # check inputs
        datatypeutility.check_dict('Binning parameters', binning_parameters)
        datatypeutility.check_dict('GSAS information', gsas_info_dict)

        # get to understand binning parameters!
        for key in binning_parameters.keys():
            print binning_parameters[key]
        raise NotImplemented('Binning parameters debugging!')

        # starting time
        t0 = time.time()

        # Load event file
        if event_file_name.endswith('.h5'):
            LoadEventNexus(Filename=event_file_name, OutputWorkspace=event_ws_name,
                           Precount=True)
        else:
            Load(Filename=event_file_name, OutputWorkspace=event_ws_name)

        # mask detectors
        # TODO - FIXME - 20180930 - Masking is transferred to a MaskManager class... Need to apply this!
        # event_ws =  mask_util.mask_detectors(event_ws_name, roi_list, mask_list)
        # if event_ws.getNumberEvents() == 0:
        #     raise RuntimeError('No events after masked/not masked! Do not know how to handle')

        # Load diffraction calibration file
        # TODO - 20180822 - LoadDffCal shall be an option such that if 'Vulcan_cal' exists... FIXME
        try:
            LoadDiffCal(InputWorkspace=event_ws_name,
                        Filename=self._detector_calibration_file,
                        WorkspaceName='Vulcan')
        except ValueError as val_err:
            err_msg = 'Unable to load diffraction calibration file {} with reference to workspace {} due to {}' \
                      ''.format(self._detector_calibration_file, event_ws_name, val_err)
            print ('[ERROR] {}'.format(err_msg))
            raise RuntimeError(err_msg)

        # Align detectors: OpenMP
        AlignDetectors(InputWorkspace=event_ws_name,
                       OutputWorkspace=event_ws_name,
                       CalibrationWorkspace='Vulcan_cal')

        t1 = time.time()

        # Filter events: OpenMP
        result = FilterEvents(InputWorkspace=event_ws_name,
                              SplitterWorkspace=split_ws_name, InformationWorkspace=info_ws_name,
                              OutputWorkspaceBaseName=output_ws_base,
                              FilterByPulseTime=False, GroupWorkspaces=True,
                              OutputWorkspaceIndexedFrom1=True,
                              SplitSampleLogs=True)

        # get output workspaces' names
        output_names = None
        for r in result:
            if isinstance(r, int):
                # print r
                pass
            elif isinstance(r, list):
                output_names = r
            else:
                continue
            # END-IF-ELSE
        # END-IF

        t2 = time.time()

        # construct output GSAS names
        gsas_names = list()
        for index in range(len(output_names)):
            out_ws_name = output_names[index]
            if len(out_ws_name) == 0:
                gsas_name = ''
            else:
                gsas_name = out_ws_name + '_RaggedGSAS'
            gsas_names.append(gsas_name)
        # END-FOR

        # Now start to use multi-threading to diffraction focus the sliced event data
        num_outputs = len(output_names)
        number_ws_per_thread = int(num_outputs / self._number_threads)
        extra = num_outputs % self._number_threads

        print ('[DB...IMPORTANT] Output workspace number = {0}, workspace per thread = {1}\n'
               'Output workspaces names: {2}'.format(num_outputs, number_ws_per_thread, output_names))

        thread_pool = dict()
        # create threads and start
        end_sliced_ws_index = 0  # exclusive last
        for thread_id in range(self._number_threads):
            start_sliced_ws_index = end_sliced_ws_index
            end_sliced_ws_index = min(start_sliced_ws_index + number_ws_per_thread + int(thread_id < extra),
                                      num_outputs)
            # call method self.focus_workspace_list() in multiple threading
            # Note: Tread(target=[method name], args=(method argument 0, method argument 1, ...,)
            workspace_name_list = output_names[start_sliced_ws_index:end_sliced_ws_index]
            gsas_workspace_name_list = gsas_names[start_sliced_ws_index:end_sliced_ws_index]
            thread_pool[thread_id] = threading.Thread(target=self.focus_workspace_list,
                                                      args=(workspace_name_list, gsas_workspace_name_list,
                                                            binning_parameters,))
            thread_pool[thread_id].start()
            print ('[DB] thread {0}: [{1}: {2}) ---> {3} workspaces'.
                   format(thread_id, start_sliced_ws_index,  end_sliced_ws_index,
                          end_sliced_ws_index-start_sliced_ws_index))
        # END-FOR

        # join the threads after the diffraction focus is finished
        for thread_id in range(self._number_threads):
            thread_pool[thread_id].join()

        # kill any if still alive
        for thread_id in range(self._number_threads):
            thread_i = thread_pool[thread_id]
            if thread_i is not None and thread_i.isAlive():
                thread_i._Thread_stop()

        t3 = time.time()

        # write all the processed workspaces to GSAS:  IPTS number and parm_file_name shall be passed
        self.write_to_gsas(gsas_names, ipts_number=gsas_info_dict['IPTS'], parm_file_name=gsas_info_dict['parm file'])

        # write to logs
        self.write_log_records(gsas_names, log_type='load_frame')
        tf = time.time()

        # processing time output
        process_info = '{0}: Runtime = {1}   Total output workspaces = {2}' \
                       ''.format(event_file_name, tf - t0, len(output_names))
        process_info += 'Details for thread = {4}:\n\tLoading  = {0}\n\tChopping = {1}\n\tFocusing = {2}\n\t' \
                        'SaveGSS = {3}'.format(t1 - t0, t2 - t1, t3 - t2, tf - t3, self._number_threads)
        print (process_info)

        end_sliced_ws_index = 0
        for thread_id in range(self._number_threads):
            start_sliced_ws_index = end_sliced_ws_index
            end_sliced_ws_index = min(start_sliced_ws_index + number_ws_per_thread + int(thread_id < extra),
                                      num_outputs)
            print ('thread {0}: [{1}: {2}) ---> {3} workspaces'
                   .format(thread_id, start_sliced_ws_index, end_sliced_ws_index,
                           end_sliced_ws_index-start_sliced_ws_index))

        return process_info, output_names

    def write_to_nexuses(self, workspace_name_list, output_file_name_base):
        """

        :param workspace_name_list:
        :param output_file_name_base:
        :return:
        """
        # TODO FIXME TODO - 20180807 - This is a test case for multiple threading! FIXME

        # NOTE: this method shall create a thread but return without thread returns

    def write_log_records(self, workspace_name_list, log_type='load_frame'):
        """
        write to all log workspaces
        :return:
        """
        import reduce_adv_chop

        log_writer = reduce_adv_chop.WriteSlicedLogs(chopped_data_dir=self._output_dir, run_number=self._run_number)

        log_writer.generate_sliced_logs(workspace_name_list, log_type)

        return

    def write_to_gsas(self, workspace_name_list, ipts_number, parm_file_name):
        """
        write to GSAS
        :param workspace_name_list:
        :param ipts_number:
        :param parm_file_name:
        :return:
        """
        import save_vulcan_gsas

        gsas_writer = save_vulcan_gsas.SaveVulcanGSS(self._ref_tof_set)

        for index_ws, ws_name in enumerate(workspace_name_list):
            gsas_file_name = os.path.join(self._output_dir, '{0}.gda'.format(index_ws))
            gsas_writer.save(diff_ws_name=ws_name, gsas_file_name=gsas_file_name, ipts_number=ipts_number,
                             gsas_param_file_name=parm_file_name)

        return

    def write_to_gsas_old(self, workspace_name_list, ipts_number, parm_file_name):
        """
        Write all the workspaces to GSAS file sequentially
        :param parm_file_name
        :param ipts_number
        :param workspace_name_list:
        :return:
        """
        # TODO - 20181030 - Consider to merge with mantid_reduction....save_vulcan_gsas
        # check inputs
        datatypeutility.check_list('Workspace name list', workspace_name_list)
        datatypeutility.check_int_variable('IPTS number', ipts_number, (0, None))  # IPTS=1: pseudo IPTS for arb. NeXus
        datatypeutility.check_string_variable('GSAS parm file name', parm_file_name)

        for index, ws_name in enumerate(workspace_name_list):
            # skip empty workspace
            if len(ws_name) == 0:
                continue

            gsas_file_name = os.path.join(self._output_dir, '{0}.gda'.format(index))

            # check that workspace shall be point data
            output_workspace = AnalysisDataService.retrieve(ws_name)
            if output_workspace.isHistogramData():
                raise RuntimeError('Output workspace {0} of type {1} to export to {2} shall be point data '
                                   'at this stage.'
                                   ''.format(ws_name, type(output_workspace), gsas_file_name))

            # construct the headers
            vulcan_gsas_header = mantid_reduction.VulcanGSASHelper.create_vulcan_gsas_header(output_workspace,
                                                                                             gsas_file_name,
                                                                                             ipts_number,
                                                                                             parm_file_name)

            vulcan_bank_headers = list()
            for ws_index in range(output_workspace.getNumberHistograms()):
                bank_id = output_workspace.getSpectrum(ws_index).getSpectrumNo()
                bank_header = mantid_reduction.VulcanGSASHelper.create_bank_header(bank_id,
                                                                                   output_workspace.readX(ws_index))
                vulcan_bank_headers.append(bank_header)
            # END-IF

            # Save
            try:
                print ('[DB...BAT] Save GSS to {} from {}'.format(gsas_file_name, format(output_workspace)))
                SaveGSS(InputWorkspace=output_workspace, Filename=gsas_file_name, SplitFiles=False, Append=False,
                        Format="SLOG", MultiplyByBinWidth=False,
                        ExtendedHeader=False,
                        UserSpecifiedGSASHeader=vulcan_gsas_header,
                        UserSpecifiedBankHeader=vulcan_bank_headers,
                        UseSpectrumNumberAsBankID=True,
                        SLOGXYEPrecision=[1, 1, 2])
                mantid_helper.delete_workspace(output_workspace)
            except RuntimeError as run_err:
                raise RuntimeError('Failed to call SaveGSS() due to {0}'.format(run_err))

        return

# END-DEF-CLASS


# t1 = threading.Thread(target=reduce_data, args=(output_names[:half_num], ))
# t2 = threading.Thread(target=reduce_data, args=(output_names[half_num:],))
# t1.start()
# t2.start()
# t1.join()
# t2.join()


# # # reduce
# for ws_name in output_names:
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
#     DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
#     # Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params='5000,-0.001,50000', FullBinsOnly=True)


# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 226.181304932   Total output workspaces = 733
# Details for thread = 32:
# 	Loading  = 97.1458098888
# 	Chopping = 35.0766251087
# 	Focusing = 93.9588699341
#
# new algorithm: mutex
# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 307.683965921   Total output workspaces = 733
# Details for thread = 16:
# 	Loading  = 93.5135071278
# 	Chopping = 35.1256639957
# 	Focusing = 179.044794798
