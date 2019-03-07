# This is a class to slice and focus data for parallelization (multiple threading)
import time
from mantid.simpleapi import Load, LoadEventNexus, GenerateEventsFilter, FilterEvents, LoadDiffCal, AlignAndFocusPowder
from mantid.simpleapi import AlignDetectors, ConvertUnits, RenameWorkspace, ExtractSpectra, CloneWorkspace, Rebin
from mantid.simpleapi import DiffractionFocussing, CreateEmptyTableWorkspace, CreateWorkspace
from mantid.simpleapi import EditInstrumentGeometry, GeneratePythonScript
import threading
import os
import time
import datatypeutility
import mantid_helper
import reduce_adv_chop
import vulcan_util
import file_utilities
import reduce_VULCAN


class SliceFocusVulcan(object):
    """ Class to handle the slice and focus on vulcan data
    """
    def __init__(self, number_banks, focus_instrument_dict, num_threads=24, output_dir=None):
        """
        initialization
        :param number_banks: number of banks to focus to
        :param focus_instrument_dict: dictionary of parameter for instrument
        :param output_dir:
        :param num_threads:
        """
        datatypeutility.check_int_variable('Number of banks', number_banks, [1, None])
        datatypeutility.check_int_variable('Number of threads', num_threads, [1, 256])
        datatypeutility.check_dict('Focused instrument dictionary', focus_instrument_dict)

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

        self._number_banks = number_banks

        self._focus_instrument_dict = focus_instrument_dict
        # self._init_focused_instruments()

        # multiple threading variables
        self._number_threads = num_threads

        # dictionary for gsas content (multiple threading)
        self._gsas_buffer_dict = dict()

        return

    def __str__(self):
        """
        nice output
        :return:
        """
        return 'Slice and focus VULCAN data into {0}-bank with {1} threads'.format(self._number_banks,
                                                                                   self._number_threads)

    @staticmethod
    def export_split_logs(split_ws_names, gsas_file_index_start, output_dir):
        """
        Export split sample logs to a series of HDF5
        and also the special mantid log + workspace name
        :param split_ws_names:
        :param gsas_file_index_start:
        :param output_dir:
        :return:
        """
        log_names = [log_pair[1] for log_pair in reduce_VULCAN.VulcanSampleLogList]
        info = ''

        for index, ws_name in enumerate(split_ws_names):
            ws_i = mantid_helper.retrieve_workspace(ws_name, True)
            out_file_name = os.path.join(output_dir, '{}.hdf5'.format(index + gsas_file_index_start))
            gda_name = '{}.gda'.format(index + gsas_file_index_start)
            attribute_dict = {'GSAS': gda_name, 'Workspace': ws_name}
            file_utilities.save_sample_logs(ws_i, log_names, out_file_name, attribute_dict)
            info += '{}  \t{}  \t{}\n'.format(index, out_file_name, gda_name)
        # END-FOR

        sum_file = open(os.path.join(output_dir, 'summary.txt'), 'w')
        sum_file.write(info)
        sum_file.close()

        return

    def focus_workspace_list(self, ws_name_list, gsas_ws_name_list, group_ws_name):
        """ Do diffraction focus on a list workspaces and also convert them to IDL GSAS
        This is the main execution body to be executed in multi-threading environment
        :param ws_name_list:
        :param gsas_ws_name_list: name for GSAS
        :param group_ws_name: name for grouping workspace
        :return:
        """
        datatypeutility.check_list('Workspace names', ws_name_list)
        datatypeutility.check_list('(Output) GSAS workspace name list', gsas_ws_name_list)
        if len(ws_name_list) != len(gsas_ws_name_list):
            raise RuntimeError('Input workspace names {} have different number than output GSAS workspace names {}'
                               ''.format(ws_name_list, gsas_ws_name_list))

        for index in range(len(ws_name_list)):
            # set GSAS workspace name same as input workspace name
            ws_name = ws_name_list[index]
            gsas_ws_name_list[index] = ws_name
            gsas_ws_name = ws_name

            datatypeutility.check_string_variable('Workspace name', ws_name)
            datatypeutility.check_string_variable('Output GSAS workspace name', gsas_ws_name)
            # skip empty workspace name that might be returned from FilterEvents
            if len(ws_name) == 0:
                continue
            # focus (simple) it is the same but simplied version in diffraction_focus()
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
            # diffraction focus
            DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace=group_ws_name)
            # convert unit to TOF
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
            # edit instrument
            try:
                EditInstrumentGeometry(Workspace=ws_name,
                                       PrimaryFlightPath=self._focus_instrument_dict['L1'],
                                       SpectrumIDs=self._focus_instrument_dict['SpectrumIDs'],
                                       L2=self._focus_instrument_dict['L2'],
                                       Polar=self._focus_instrument_dict['Polar'],
                                       Azimuthal=self._focus_instrument_dict['Azimuthal'])
            except RuntimeError as run_err:
                print ('[WARNING] Non-critical error from EditInstrumentGeometry for {}: {}'
                       ''.format(ws_name, run_err))
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

    def slice_focus_event_workspace(self, event_ws_name, geometry_calib_ws_name, group_ws_name,
                                    split_ws_name, info_ws_name,
                                    output_ws_base, binning_parameters, chop_overlap_mode,
                                    gsas_info_dict, gsas_writer, gsas_file_index_start):
        """ Slice and diffraction focus event workspace with option to write the reduced data to GSAS file with
        SaveGSS().
        Each workspace is
        1. sliced from original event workspace
        2. diffraction focused
        3. optionally rebinned to IDL binning and read for SaveGSS()
        :param event_ws_name: name of EventWorkspace that has been masked if there is a mask
        :param geometry_calib_ws_name: DIFC calibration Table workspace
        :param group_ws_name: name of Grouping workspace
        :param split_ws_name:
        :param info_ws_name:
        :param output_ws_base:
        :param chop_overlap_mode: whether the chopped workspace will have overlapped events (in time)
        :param binning_parameters: None for IDL binning; otherwise, use defined binning
        :param gsas_info_dict: required for writing GSAS files keys (IPTS, 'parm file' = 'vulcan.prm', 'vanadium')
        :param gsas_writer: GSASWriter instance to export to VULCAN GSAS file
        :param gsas_file_index_start: starting index of GSAS file (1.gda, 2.gda.. whether 0.gda?)
        :return: tuple: [1] slicing information, [2] output workspace names
        """
        # check inputs
        if binning_parameters is not None:
            datatypeutility.check_list('Binning parameters', binning_parameters)
        datatypeutility.check_dict('GSAS information', gsas_info_dict)

        # starting time
        t0 = time.time()

        # Align detectors: OpenMP
        AlignDetectors(InputWorkspace=event_ws_name,
                       OutputWorkspace=event_ws_name,
                       CalibrationWorkspace=geometry_calib_ws_name)

        t1 = time.time()

        # Filter events: OpenMP
        # is relative or not?  TableWorkspace has to be relative!
        split_ws = mantid_helper.retrieve_workspace(split_ws_name, raise_if_not_exist=True)
        if split_ws.__class__.__name__.count('TableWorkspace'):
            is_relative_time = True
        else:
            is_relative_time = False

        result = FilterEvents(InputWorkspace=event_ws_name,
                              SplitterWorkspace=split_ws_name, InformationWorkspace=info_ws_name,
                              OutputWorkspaceBaseName=output_ws_base,
                              FilterByPulseTime=False,
                              GroupWorkspaces=True,
                              OutputWorkspaceIndexedFrom1=True,
                              SplitSampleLogs=True,
                              RelativeTime=is_relative_time)

        # get output workspaces' names
        output_names = mantid_helper.get_filter_events_outputs(result)
        if output_names is None:
            raise RuntimeError('There is no workspace found in the result of FilterEvents (vulcan_slice_reduce)')

        t2 = time.time()

        # construct output GSAS names
        gsas_names = list()
        for index in range(len(output_names)):
            out_ws_name = output_names[index]
            if len(out_ws_name) == 0:
                gsas_name = ''
            else:
                gsas_name = out_ws_name + '_gsas_not_binned'
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
            workspace_names_i = output_names[start_sliced_ws_index:end_sliced_ws_index]
            gsas_workspace_name_list = gsas_names[start_sliced_ws_index:end_sliced_ws_index]
            thread_pool[thread_id] = threading.Thread(target=self.focus_workspace_list,
                                                      args=(workspace_names_i, gsas_workspace_name_list,
                                                            group_ws_name,))
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

        # process overlapping chop
        if chop_overlap_mode:
            # FIXME - Shan't be used anymore unless an optimized algorithm developed for DT option
            output_names = self.process_overlap_chopped_data(output_names)
        # END-IF

        # save ONE python script for future reference
        if len(output_names) > 0:
            python_name = os.path.join(self._output_dir,
                                       '{}_{}.py'.format(self._run_number, split_ws_name))
            GeneratePythonScript(InputWorkspace=output_names[0], Filename=python_name)
        else:
            print ('[ERROR] No output workspace to export to GSAS!')

        # write all the processed workspaces to GSAS:  IPTS number and parm_file_name shall be passed
        run_date_time = vulcan_util.get_run_date(event_ws_name, '')
        self.write_to_gsas(output_names, ipts_number=gsas_info_dict['IPTS'], parm_file_name=gsas_info_dict['parm file'],
                           vanadium_gda_name=gsas_info_dict['vanadium'],
                           gsas_writer=gsas_writer, run_start_date=run_date_time,  # ref_tof_sets=binning_parameters,
                           gsas_file_index_start=gsas_file_index_start)

        if True:
            self.export_split_logs(output_names, gsas_file_index_start=gsas_file_index_start,
                                   output_dir=self._output_dir)

        # write to logs
        self.write_log_records(output_names, log_type='loadframe')
        tf = time.time()

        # processing time output
        process_info = '{0}: Runtime = {1}   Total output workspaces = {2}' \
                       ''.format(event_ws_name, tf - t0, len(output_names))
        process_info += 'Details for thread = {4}:\n\tLoading  = {0}\n\tChopping = {1}\n\tFocusing = {2}\n\t' \
                        'SaveGSS = {3}'.format(t1 - t0, t2 - t1, t3 - t2, tf - t3, self._number_threads)
        print (process_info)

        # FIXME - FUTURE - Whether this for-loop is useful?
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
        # TODO - FUTURE - Implement! - This is a test case for multiple threading! FIXME

        # NOTE: this method shall create a thread but return without thread returns

    def write_log_records(self, workspace_name_list, log_type='loadframe'):
        """
        write to all log workspaces
        :return:
        """
        log_writer = reduce_adv_chop.WriteSlicedLogs(chopped_data_dir=self._output_dir, run_number=self._run_number)

        log_writer.generate_sliced_logs(workspace_name_list, log_type)

        return

    def write_gsas_files(self, workspace_name_list, ipts_number, van_ws_name, parm_file_name, gsas_writer,
                         run_start_date, gsas_file_name_list):
        """ Export a series of workspaces to text buffer, which later will be exported to GSAS files, but not
        in this method
        Note: this is a single thread method designed for multi-threading case
        :param workspace_name_list:
        :param ipts_number:
        :param parm_file_name:
        :param gsas_writer:
        :param gsas_file_name_list: list of GSAS file names corresponding to workspace names
        :param van_ws_name: vanadium workspace name (string or None)
        :param run_start_date:
        :return:
        """
        for index_ws, ws_name in enumerate(workspace_name_list):
            if ws_name == '':
                continue
            text_buffer = gsas_writer.save(diff_ws_name=ws_name, run_date_time=run_start_date,
                                           gsas_file_name=gsas_file_name_list[index_ws],
                                           ipts_number=ipts_number,
                                           run_number=self._run_number,
                                           gsas_param_file_name=parm_file_name, align_vdrive_bin=True,
                                           van_ws_name=van_ws_name, is_chopped_run=True, write_to_file=False)
            self._gsas_buffer_dict[ws_name] = text_buffer

        return

    def write_to_gsas(self, workspace_name_list, ipts_number, parm_file_name, vanadium_gda_name,
                      gsas_writer, run_start_date, gsas_file_index_start=1):
        """ Write a set of workspaces to GSAS file in parallel (mutliple threading)
        :param workspace_name_list:
        :param ipts_number:
        :param parm_file_name:
        :param vanadium_gda_name: name of reduced vanadium in GSAS file
        :param gsas_writer:
        :param run_start_date:
        :param gsas_file_index_start:
        :return:
        """
        # define the holder of the text buffers
        num_workspaces = len(workspace_name_list)
        self._gsas_buffer_dict = dict()

        # thread management
        thread_pool = [None] * self._number_threads

        # define workspaces assigned to each thread
        number_ws_per_thread = num_workspaces / self._number_threads
        extra = num_workspaces % self._number_threads

        # import vanadium if needed
        if vanadium_gda_name:
            van_diff_ws_name = gsas_writer.import_vanadium(vanadium_gda_name)
        else:
            van_diff_ws_name = None

        end_sliced_ws_index = 0
        for thread_id in range(self._number_threads):
            start_sliced_ws_index = end_sliced_ws_index
            end_sliced_ws_index = min(start_sliced_ws_index + number_ws_per_thread + int(thread_id < extra),
                                      num_workspaces)

            # workspace names and gsas file names
            workspace_names_i = workspace_name_list[start_sliced_ws_index:end_sliced_ws_index]
            gsas_file_name_list = list()
            for index_ws in range(start_sliced_ws_index, end_sliced_ws_index):
                gsas_file_name = '{0}.gda'.format(index_ws + gsas_file_index_start)
                gsas_file_name_list.append(gsas_file_name)
            if len(gsas_file_name_list) != len(workspace_names_i):
                raise RuntimeError('Number of GSAS file names ({}) does not equal to number of workspaces '
                                   '({}) to export for thread {}'
                                   ''.format(len(gsas_file_name_list), len(workspace_names_i), thread_id))
            
            thread_pool[thread_id] = threading.Thread(target=self.write_gsas_files,
                                                      args=(workspace_names_i, ipts_number, van_diff_ws_name,
                                                            parm_file_name, gsas_writer, run_start_date,
                                                            gsas_file_name_list,))

            thread_pool[thread_id].start()
            print ('[DB...Write GSAS] thread {0}: [{1}: {2}) ---> {3} workspaces'.
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

        # Now output GSAS workspace one to one
        for index_ws in range(num_workspaces):
            ws_name_i = workspace_name_list[index_ws]
            if ws_name_i == '':
                continue
            gsas_file_name = os.path.join(self._output_dir, '{0}.gda'.format(index_ws + gsas_file_index_start))
            print ('[DB...BAT]: {}'.format(self._gsas_buffer_dict.keys()))
            gsas_content = self._gsas_buffer_dict[ws_name_i]
            gsas_file = open(gsas_file_name, 'w')
            gsas_file.write(gsas_content)
            gsas_file.close()
        # END-FOR

        return

# END-DEF-CLASS


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
