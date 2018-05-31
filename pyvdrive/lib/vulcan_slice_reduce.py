# This is a class to slice and focus data for parallelization (multiple threading)
import time
from mantid.simpleapi import Load, GenerateEventsFilter, FilterEvents, LoadDiffCal, AlignAndFocusPowder, Rebin
from mantid.simpleapi import AlignDetectors, ConvertUnits, RenameWorkspace, ExtractSpectra, CloneWorkspace
from mantid.simpleapi import ConvertToPointData, ConjoinWorkspaces, SaveGSS, Multiply, CreateWorkspace
from mantid.simpleapi import DiffractionFocussing, CreateEmptyTableWorkspace, CreateWorkspace, SaveVulcanGSS
from mantid.api import AnalysisDataService
import threading
import numpy
import os
import h5py
import time
import file_utilities
import datatypeutility


# chop data
# ipts = 18522
# run_number = 160560
# event_file_name = '/SNS/VULCAN/IPTS-13924/nexus/VULCAN_160989.nxs.h5'
# event_file_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(ipts, run_number)
# event_file_name = '/SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5'


CALIBRATION_FILES = {3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                     7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_7bank.h5',
                     27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_27bank.h5'}


class SliceFocusVulcan(object):
    """ Class to handle the slice and focus on vulcan data
    """
    def __init__(self, number_banks=3, num_threads=24):
        """
        initialization
        :param number_banks:
        :param num_threads:
        """
        datatypeutility.check_int_variable('Number of banks', number_banks, [1, None])
        datatypeutility.check_int_variable('Number of threads', number_banks, [1, 256])

        if number_banks in CALIBRATION_FILES:
            self._detector_calibration_file = CALIBRATION_FILES[number_banks]
            self._number_banks = number_banks
        else:
            raise RuntimeError('{0}-bank case is not supported.'.format(number_banks))

        # other directories
        self._output_dir = '/tmp/'
        self._ws_name_dict = dict()
        self._last_loaded_event_ws = None
        self._last_loaded_ref_id = ''
        self._det_eff_ws_name = None

        # calibration, grouping and mask file
        self._diff_base_name = 'Vulcan_Bank{0}'.format(self._number_banks)
        self._diff_cal_ws_name = '{0}_cal'.format(self._diff_base_name)
        self._group_ws_name = '{0}_group'.format(self._diff_base_name)
        self._mask_ws_name = '{0}_mask'.format(self._diff_base_name)

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

    def align_detectors(self, ref_id):
        """
        Align detector of an EventWorkspace indexed by reference ID
        :param ref_id:
        :return:
        """
        datatypeutility.check_string_variable('Workspace/data reference ID', ref_id)
        if ref_id not in self._ws_name_dict:
            raise RuntimeError('Workspace/data reference ID {0} does not exist. Existing IDs are {1}'
                               ''.format(ref_id, self._ws_name_dict.keys()))

        # get event workspace name
        event_ws_name = self._ws_name_dict[ref_id]

        # get calibration file name
        if not AnalysisDataService.doesExist(self._diff_cal_ws_name):
            self.load_diff_calibration(self._diff_base_name)

        AlignDetectors(InputWorkspace=event_ws_name,
                       OutputWorkspace=event_ws_name,
                       CalibrationWorkspace=self._diff_cal_ws_name)

        return

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
    def create_idl_bins(num_banks, h5_bin_file_name):
        """
        create a Mantid to VDRIVE-IDL mapping binning
        :param num_banks:
        :param h5_bin_file_name:
        :return:
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

    def focus_workspace_list(self, ws_name_list, binning_parameter_dict):
        """
        do diffraction focus on a list workspaces and also convert them to IDL GSAS
        :param ws_name_list:
        :param binning_parameter_dict: dictionary for binning parameters. it is used for convert binning to VDRIVE-IDL
        :return:
        """
        datatypeutility.check_list('Workspace names', ws_name_list)
        datatypeutility.check_dict('Binning parameters dict', binning_parameter_dict)

        for ws_name in ws_name_list:
            # check input
            datatypeutility.check_string_variable('Workspace name', ws_name)
            # skip empty workspace name that might be returned from FilterEvents
            if len(ws_name) == 0:
                continue
            # focus (simple) it is the same but simplied version in diffraction_focus()
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
            # diffraction focus
            DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
            # convert unit to TOF
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
            # convert VULCAN binning
            self.rebin_workspace(input_ws=ws_name, binning_param_dict=binning_parameter_dict,
                                 output_ws_name=ws_name)
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
        self._last_loaded_event_ws = Load(Filename=event_file_name, MetaDataOnly=False, OutputWorkspace=out_ws_name)
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
        rebin input workspace with user specified binning parameters
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

        # check input binning parameters
        for ws_index in range(input_ws.getNumberHistograms()):
            bank_id = ws_index + 1
            bin_params = binning_param_dict[bank_id]
            if len(bin_params) % 2 == 0:
                # odd number and cannot be binning parameters
                raise RuntimeError('Binning parameter {0} cannot be accepted.'.format(bin_params))

        # rebin input workspace
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

    def write_to_gsas(self, workspace_name_list, ipts_number, parm_file_name):
        """
        Write all the workspaces to GSAS file sequentially
        :param workspace_name_list:
        :return:
        """
        assert isinstance(workspace_name_list, list)

        for index, ws_name in enumerate(workspace_name_list):
            if len(ws_name) == 0:
                continue

            gsas_file_name = os.path.join(self._output_dir, '{0}.gda'.format(index))

            # check that workspace shall be point data
            output_workspace = AnalysisDataService.retrieve(ws_name)
            if output_workspace.isHistogramData():
                raise RuntimeError('Output workspace {0} for {1} shall be point data at this stage.'
                                   ''.format(ws_name, gsas_file_name))

            # construct the headers
            vulcan_gsas_header = self.create_vulcan_gsas_header(output_workspace, gsas_file_name, ipts_number,
                                                                parm_file_name)

            vulcan_bank_headers = list()
            for ws_index in range(output_workspace.getNumberHistograms()):
                bank_id = output_workspace.getSpectrum(ws_index).getSpectrumNo()
                bank_header = self.create_bank_header(bank_id, output_workspace.readX(ws_index))
                vulcan_bank_headers.append(bank_header)
            # END-F

            # Save
            try:
                SaveGSS(InputWorkspace=output_workspace, Filename=gsas_file_name, SplitFiles=False, Append=False,
                        Format="SLOG", MultiplyByBinWidth=False,
                        ExtendedHeader=False,
                        UserSpecifiedGSASHeader=vulcan_gsas_header,
                        UserSpecifiedBankHeader=vulcan_bank_headers,
                        UseSpectrumNumberAsBankID=True,
                        SLOGXYEPrecision=[1, 1, 2])
            except RuntimeError as run_err:
                raise RuntimeError('Failed to call SaveGSS() due to {0}'.format(run_err))

        return

    def slice_focus_event_workspace(self, event_file_name, event_ws_name, split_ws_name, info_ws_name,
                                    output_ws_base, idl_bin_file_name, east_west_binning_parameters,
                                    high_angle_binning_parameters):

        # starting time
        t0 = time.time()

        # Load event file
        Load(Filename=event_file_name, OutputWorkspace=event_ws_name)

        # Load diffraction calibration file
        LoadDiffCal(InputWorkspace=event_ws_name,
                    Filename=self._detector_calibration_file,
                    WorkspaceName='Vulcan')

        # Align detectors
        AlignDetectors(InputWorkspace=event_ws_name,
                       OutputWorkspace=event_ws_name,
                       CalibrationWorkspace='Vulcan_cal')

        t1 = time.time()

        # Filter events
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
                # print r.name(), type(r)

        t2 = time.time()

        # process binning parameters
        if idl_bin_file_name is not None:
            binning_parameter_dict = self.create_idl_bins(self._number_banks, idl_bin_file_name)
        else:
            binning_parameter_dict = self.create_nature_bins(self._number_banks, east_west_binning_parameters,
                                                             high_angle_binning_parameters)

        # Now start to use multi-threading
        num_outputs = len(output_names)
        number_ws_per_thread = int(num_outputs / self._num_threads)
        extra = num_outputs % self._num_threads

        print ('[DB...IMPORTANT] Output workspace number = {0}, workspace per thread = {1}\n'
               'Output workspaces names: {2}'.format(num_outputs, number_ws_per_thread, output_names))
        thread_pool = dict()
        # create threads and start
        end = 0  # exclusive last
        for thread_id in range(self._num_threads):
            start = end
            end = min(start + number_ws_per_thread + int(thread_id < extra), num_outputs)
            thread_pool[thread_id] = threading.Thread(target=self.focus_workspace_list,
                                                      args=(output_names[start:end], binning_parameter_dict,))
            thread_pool[thread_id].start()
            print ('thread {0}: [{1}: {2}) ---> {3} workspaces'.format(thread_id, start, end, end-start))

        # join the threads
        for thread_id in range(self._num_threads):
            thread_pool[thread_id].join()

        # kill any if still alive
        for thread_id in range(self._num_threads):
            thread_i = thread_pool[thread_id]
            if thread_i is not None and thread_i.isAlive():
                thread_i._Thread_stop()

        t3 = time.time()

        # write all the processed workspaces to GSAS
        self.write_to_gsas(output_names, ipts_number=12345, parm_file_name='vulcan.prm')

        tf = time.time()

        # processing time output
        process_info = '{0}: Runtime = {1}   Total output workspaces = {2}' \
                       ''.format(event_file_name, tf - t0, len(output_names))
        process_info += 'Details for thread = {4}:\n\tLoading  = {0}\n\tChopping = {1}\n\tFocusing = {2}\n\t' \
                        'SaveGSS = {3}'.format(t1 - t0, t2 - t1, t3 - t2, tf - t3, self._num_threads)
        print (process_info)

        end = 0
        for thread_id in range(self._num_threads):
            start = end
            end = min(start + number_ws_per_thread + int(thread_id < extra), num_outputs)
            print ('thread {0}: [{1}: {2}) ---> {3} workspaces'.format(thread_id, start, end, end-start))

        return process_info

    @staticmethod
    def create_vulcan_gsas_header(workspace, gsas_file_name, ipts, parm_file_name):
        """
        create specific GSAS header required by VULCAN team/VDRIVE
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
            run_start = run.getProperty("run_start").value
            duration = float(run.getProperty("duration").value)

            # separate second and sub-seconds
            run_start_seconds = run_start.split(".")[0]
            run_start_sub_seconds = run_start.split(".")[1]
            # self.log().warning('Run start {0} is split to {1} and {2}'.format(run_start, run_start_seconds,
            #                                                                   run_start_sub_seconds))

            # property run_start and duration exist
            utctime = numpy.datetime64(run.getProperty('run_start').value)
            time0 = numpy.datetime64("1990-01-01T00:00:00")
            total_nanosecond_start = int((utctime - time0) / numpy.timedelta64(1, 'ns'))
            total_nanosecond_stop = total_nanosecond_start + int(duration*1.0E9)

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