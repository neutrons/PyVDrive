import os
import os.path

from chop_utility import DataChopper
import mantid_helper
import reductionmanager as prl
import archivemanager


class ProjectManager(object):
    """ VDrive Project
    """
    def __init__(self, project_name, instrument='VULCAN'):
        """ Init
        """
        # project name
        self._name = project_name
        # Data path.  With baseDataFileName, a full path to a data set can be constructed
        self._baseDataPath = None

        # chopping and reduction managers
        # Reduction manager
        self._reductionManager = prl.ReductionManager(instrument=instrument)
        # dictionary to manage data chopping
        self._chopManagerDict = dict()   # key: run number, value: SampleLogHelper.SampleLogManager()

        # definition of dictionaries
        # dictionary for the information of run number, file name and IPTS
        self._dataFileDict = dict()  # key: run number, value: 2-tuple (file name, IPTS)
        # dictionary for sample run mapping to vanadium run
        self._sampleRunVanadiumDict = dict()  # Key: run number (int) / Value: vanadium run number (int)
        # vanadium GSAS file to vanadium run's mapping. Key = integer vanadium run number; Value = GSAS file name
        self._vanadiumGSASFileDict = dict()

        # List of data file's base name
        self._baseDataFileNameList = list()

        # dictionary for sample run number to be flagged to reduce.
        self._sampleRunReductionFlagDict = dict()  # Key: run number. Value: boolean flag for reduction

        return

    def add_run(self, run_number, file_name, ipts_number):
        """
        Add a run to project
        :param run_number:
        :param file_name:
        :param ipts_number:
        :return:
        """
        # Check input
        assert isinstance(run_number, int)
        assert isinstance(ipts_number, int)
        assert isinstance(file_name, str)

        self._dataFileDict[run_number] = (file_name, ipts_number)
        self._baseDataFileNameList.append(os.path.basename(file_name))

        return

    def chop_data(self, run_number, slicer_key, reduce_flag, output_dir):
        """
        Chop a run (Nexus) with pre-defined splitters workspace and optionally reduce the
        split workspaces to GSAS
        :param run_number:
        :param slicer_key:
        :param reduce_flag:
        :param output_dir:
        :return:
        """
        # check inputs' validity
        assert isinstance(slicer_key, str), 'Slicer key %s of type %s is not supported. It ' \
                                            'must be a string.' % (str(slicer_key), type(slicer_key))
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            '' % (str(run_number), type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.' % (str(output_dir), type(output_dir))

        # get chopping helper
        try:
            chopper = self._chopManagerDict[run_number]
        except KeyError as key_error:
            error_message = 'Run number %d is not registered to chopper manager (%s). Current runs are %s.' \
                            '' % (run_number, str(key_error), str(self._chopManagerDict.keys()))
            raise RuntimeError(error_message)

        if reduce_flag:
            # reduce to GSAS
            src_file_name, ipts_number = self.get_run_info(run_number)
            self._reductionManager.reduce_chopped_data(ipts_number, run_number, src_file_name, chopper, slicer_key,
                                                       output_dir)

            status = True,
            message = ''

        else:
            # just chop the files and save to Nexus
            data_file = self.get_file_path(run_number)
            self._reductionManager.chop_data(data_file, chopper, slicer_key, output_dir)

            status = True
            message = 'Run %d is chopped and reduced. ' % run_number

        return status, message

    def clear_reduction_flags(self):
        """ Set to all runs' reduction flags to be False
        :return:
        """
        for run_number in self._sampleRunReductionFlagDict.keys():
            self._sampleRunReductionFlagDict[run_number] = False

        return

    def delete_slicers(self, run_number, slicer_tag=None):
        """ delete slicers from memory, i.e., mantid workspaces
        :param run_number: run number for the slicer
        :param slicer_tag:
        :return:
        """
        # NOTE: No caller of this method so far
        if run_number not in self._chopManagerDict:
            return False, 'Run number %s does not have DataChopper associated.' % str(run_number)

        # get chopper
        data_chopper = self._chopManagerDict[run_number]

        # let DataChopper to do business
        data_chopper.delete_slicer_by_id(slicer_tag)

        return True, ''

    def clear_runs(self):
        """
        Purpose:
            Clear memory, i.e., loaded workspace
        Requirements:

        Guarantees:

        :return:
        """
        assert(isinstance(self._dataFileDict, dict))
        self._dataFileDict.clear()

        return

    def delete_data_file(self, data_file_name):
        """
        Delete a data file in the project but not delete the file physically
        :param data_file_name:
        :return: boolean.  True if it is in the data file dictionary. False it is not in the project
        """
        # check validity
        assert isinstance(data_file_name, str), 'Data file name %s must be a string but not a %s.' \
                                                '' % (str(data_file_name), type(data_file_name))

        # delete data file only if it is in the file dictionary
        if data_file_name in self._dataFileDict:
            del self._dataFileDict[data_file_name]
            self._baseDataFileNameList.remove(os.path.basename(data_file_name))
            return True

        return False

    def get_chopper(self, run_number):
        """
        Get data chopper (manager) of a run number
        If the run number does not have any DataChopper associated, then create a one
        :param run_number:
        :return: DataChopper instance
        """
        if run_number in self._chopManagerDict:
            # get the existing DataChopper instance
            run_chopper = self._chopManagerDict[run_number]
        else:
            # create a new DataChopper associated with this run
            nxs_file_name = self.get_file_path(run_number)
            print '[DB...BAT 104022] NeXus file name: ', nxs_file_name
            run_chopper = DataChopper(run_number, nxs_file_name)

            # register chopper
            self._chopManagerDict[run_number] = run_chopper
        # END-IF-ELSE

        return run_chopper

    def get_data(self, data_key=None, data_file_name=None):
        """ Get whole data set as a dictionary.  Each entry is of a bank
        Requirements: data key or data file name is specified
        Guarantees:
        :param data_key: data key generated in Vdrive project
        :param data_file_name: full path data file
        :return:
        """
        # Check requirements
        assert (data_key is None and data_file_name is None) is False, \
            'Neither data key %s nor data file %s is given.' % (str(data_key), str(data_file_name))
        assert (data_key is not None and data_file_name is not None) is False, \
            'Both data key and data file name are given.'

        # check and convert to data key
        if data_file_name is not None:
            assert isinstance(data_file_name, str), 'blabla'
            # TODO: make this to a method ???
            data_key = get_data_key(data_file_name)
        else:
            assert isinstance(data_key, str), 'blabla'

        # check existence
        if data_key not in self._dataWorkspaceDict:
            raise KeyError('data key %s does not exist.' % data_key)

        # FIXME - data set dictionary can be retrieved from workspace long long time ago to save_to_buffer time
        data_set_dict = mantid_helper.get_data_from_workspace(self._dataWorkspaceDict[data_key], True)

        return True, data_set_dict

    def get_data_information(self, data_key):
        """ Get bank information of a loaded data file (workspace)
        Requirements: data_key is a valid string as an existing key to the MatrixWorkspace
        Guarantees: return
        :param data_key:
        :return:
        """
        # Check requirements
        assert isinstance(data_key, str), 'Data key must be a string but not %s.' % str(type(data_key))
        assert data_key in self._dataWorkspaceDict, 'Data key %s does not exist.' % data_key

        # FIXME - data set dictionary can be retrieved from workspace long long time ago to save_to_buffer time
        data_set_dict = mantid_helper.get_data_from_workspace(self._dataWorkspaceDict[data_key], True)

        return data_set_dict.keys()

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list, slice_tag):
        """ generate event slicer for data manually
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :param slice_tag: string for slice tag name
        :return:
        """
        # check whether there is a DataChopper instance associated
        if run_number not in self._chopManagerDict:
            return False, 'Run number %s does not have DataChopper associated.'

        # generate data slicer
        status, ret_obj = self._chopManagerDict[run_number].generate_events_filter_manual(
            run_number, time_segment_list, relative_time, slice_tag)

        return status, ret_obj

    def gen_data_slicer_sample_log(self, run_number, sample_log_name,
                                   start_time, end_time, min_log_value, max_log_value,
                                   log_value_step, slice_tag=None):
        """
        Generate data slicer/splitters by log values
        :param run_number:
        :param sample_log_name:
        :param start_time:
        :param end_time:
        :param min_log_value:
        :param max_log_value:
        :param log_value_step:
        :param slice_tag:
        :return:
        """
        # check whether DataChopper
        if run_number not in self._chopManagerDict:
            return False, 'Run number %s does not have DataChopper associated.' % str(run_number)

        # Get file name according to run number
        if isinstance(run_number, int):
            # run number is a Run Number, locate file
            file_name, ipts_number = self._myProject.get_run_info(run_number)
        elif isinstance(run_number, str):
            # run number is a file name
            base_file_name = run_number
            file_name = self._myProject.get_file_path(base_file_name)
        else:
            return False, 'Input run_number %s is either an integer or string.' % str(run_number)

        # Start a session
        self._mySlicingManager.load_data_file(nxs_file_name=file_name, run_number=run_number)

        # this_ws_name = get_standard_ws_name(file_name, True)
        # mtdHelper.load_nexus(file_name, this_ws_name, True)
        # slicer_name, info_name = get_splitters_names(this_ws_name)
        # print '[DB] slicer_name = ', slicer_name, 'info_name = ', info_name, 'ws_name = ', this_ws_name,
        # print 'log_name = ', sample_log_name

        # FIXME - Need to pass value change direction
        self._mySlicingManager.generate_events_filter_by_log(log_name=sample_log_name,
                                                             min_time=start_time, max_time=end_time,
                                                             relative_time=True,
                                                             min_log_value=min_log_value,
                                                             max_log_value=max_log_value,
                                                             log_value_interval=log_value_step,
                                                             value_change_direction='Both',
                                                             tag=slice_tag)

        return

    def get_file_path(self, run_number):
        """ Get file path
        Purpose: Get the file path from run number
        Requirements: run number is non-negative integer and it has been loaded to Project
        Guarantees: the file path is given
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number >= 0

        if run_number in self._dataFileDict:
            file_path = self._dataFileDict[run_number][0]
        else:
            raise RuntimeError('Run %d does not exist in this project.' % run_number)

        return file_path

    def get_workspace_name(self, data_key):
        """ Get workspace name
        :param data_key:
        :return:
        """
        # TODO/NOW - Doc and Check requirements

        assert data_key in self._dataWorkspaceDict, 'There is no workspace for data key %s. ' \
                                                    'Candidates are %s.' % (str(data_key),
                                                                            str(self._dataWorkspaceDict.keys()))

        return self._dataWorkspaceDict[data_key]

    def getBaseDataPath(self):
        """ Get the base data path of the project
        """
        return self._baseDataPath

    def get_ipts_runs(self):
        """ Get IPTS numbers and runs
        :return: dictionary of list. Key: ipts number, Value: list of runs belonged to ipts
        """
        ipts_dict = dict()

        for run_number in self._dataFileDict.keys():
            ipts_number = self._dataFileDict[run_number][1]
            if ipts_number not in ipts_dict:
                ipts_dict[ipts_number] = list()
            ipts_dict[ipts_number].append(run_number)
        # END-FOR (run_number)

        # Sort
        for ipts_number in ipts_dict.keys():
            ipts_dict[ipts_number].sort()

        return ipts_dict

    def get_number_data_files(self):
        """
        Get the number/amount of the data files that have been set to the project.
        :return:
        """
        return len(self._dataFileDict)

    def get_runs_to_reduce(self):
        """
        Get run numbers that are going to be reduced
        :return: a list of integers
        """
        run_number_list = list()
        for run_number in self._sampleRunReductionFlagDict.keys():
            if self._sampleRunReductionFlagDict[run_number]:
                run_number_list.append(run_number)

        return run_number_list

    def get_reduced_runs(self):
        """ Get the run/run numbers of the reduced runs
        :return: list of strings
        """
        return self._reductionManager.get_reduced_runs()

    def get_reduced_data(self, run_number, unit):
        """ Get data (x, y and e) of a reduced run in the specified unit
        Purpose: Get reduced data including all spectra
        Requirements: run number is a valid integer; unit is a string for supported unit
        Guarantees: all data of the reduced run will be returned
        :param run_number:
        :param unit: target unit for the output X vector.  If unit is None, then no request
        :return: dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # check
        assert isinstance(run_number, int), 'Input run number must be an integer.'
        assert unit is None or isinstance(unit, str), 'Output data unit must be either None (default) or a string.'

        # get reduced workspace name
        reduced_ws_name = self._reductionManager.get_reduced_workspace(run_number, is_vdrive_bin=True, unit='TOF')

        # get data
        data_set_dict = mantid_helper.get_data_from_workspace(reduced_ws_name, point_data=True)
        assert isinstance(data_set_dict, dict), 'Returned value from get_data_from_workspace must be a dictionary,' \
                                                'but not %s.' % str(type(data_set_dict))

        return data_set_dict

    def get_reduced_file(self, run_number, file_type):
        """
        get the path of the reduced file
        :param run_number:
        :param file_type:
        :return:
        """
        self._reductionManager.get_reduced_runs()
        self.get_run_info(run_number)

    def get_reduced_run_history(self, run_number):
        """ Get the processing history of a reduced run
        :param run_number:
        :return:
        """
        # TODO/NOW/1st: think of how to implement!
        return ReductionHistory

    def get_reduced_run_information(self, run_number):
        """
        Purpose: Get the reduced run's information including list of banks
        Requirements: run number is an integer
        :param run_number:
        :return: a list of integers as bank ID. reduction history...
        """
        # Check
        assert isinstance(run_number, int), 'Run number must be an integer.'

        # Get workspace
        run_ws_name = self._reductionManager.get_reduced_workspace(run_number, is_vdrive_bin=True, unit='TOF')
        ws_info = mantid_helper.get_workspace_information(run_ws_name)

        return ws_info

    def get_run_info(self, run_number):
        """
        Get run's information
        :param run_number:
        :return:  2-tuple (file name, IPTS number)
        """
        if run_number not in self._dataFileDict:
            raise RuntimeError('Unable to find run %d in project manager.' % run_number)

        return self._dataFileDict[run_number]

    def get_runs(self):
        """
        Get runs
        :return:
        """
        run_list = self._dataFileDict.keys()
        run_list.sort()
        return run_list

    def getReducedRuns(self):
        """ Get the the list of the reduced runs
        
        Return :: list of data file names 
        """
        return self._myRunPdrDict.keys()

    def has_run(self, run_number):
        """
        Purpose:
            Find out whether a run number is here
        Requirements:
            run number is an integer
        Guarantee:

        :return: boolean as has or not
        """
        assert isinstance(run_number, int)

        do_have = run_number in self._dataFileDict

        return do_have

    def hasData(self, datafilename):
        """ Check whether project has such data file 
        """
        if self._dataFileDict.count(datafilename) == 1:
            # Check data set with full name
            return True
        elif self._baseDataFileNameList.count(datafilename) == 1:
            # Check data set with base name
            return True

        return False

    def load_session_from_dict(self, save_dict):
        """ Load session from a dictionary
        :param save_dict:
        :return:
        """
        assert isinstance(save_dict, dict)

        # Set
        self._name = save_dict['name']
        self._baseDataPath = save_dict['baseDataPath']
        self._dataFileDict = save_dict['dataFileDict']
        self._baseDataFileNameList = save_dict['baseDataFileNameList']

        return

    def mark_runs_to_reduce(self, run_number_list):
        """ Mark runs to reduce
        Purpose:

        Requirements:
            1. run number does exist in this project;
            2. data file of this run is accessible
            3. input run number list must be a list of integer
        Guarantees
        :param run_number_list:
        :return: None
        """
        # Check requirements
        assert isinstance(run_number_list, list)

        # Mark each runs
        for run_number in sorted(run_number_list):
            assert isinstance(run_number, int),\
                'run_number must be of type integer but not %s' % str(type(run_number))
            if self.has_run(run_number) is False:
                # no run
                raise RuntimeError('Run %d cannot be found.' % run_number)
            elif archivemanager.check_read_access(self.get_file_path(run_number)) is False:
                # file does not exist
                raise RuntimeError('Run %d with file path %s cannot be found.' % (run_number,
                                                                                  self.get_file_path(run_number)))
            else:
                # mark runs to reduce
                self._sampleRunReductionFlagDict[run_number] = True
        # END-FOR

        return

    @property
    def name(self):
        """ Return project name
        :return: if return None, it means that the project name has not been set up yet.
        """
        return self._name

    @name.setter
    def name(self, project_name):
        """ Set project name
        Requirements: project name is a string
        :param project_name:
        :return:
        """
        assert isinstance(project_name, str)
        self._name = project_name

        return

    def reduce_vanadium_runs(self):
        """ Reduce vanadium runs
        Purpose:
            Get or reduce vanadium runs according to the runs that are flagged for reduction
        Requirements:
            There are some vanadium runs that can be found
        Guarantees:
            The corresponding vanadium runs are reduced with the proper binning parameters
        :return:
        """
        # Check requirements
        van_run_number_set = set()
        for sample_run_number in self._sampleRunReductionFlagDict:
            if self._sampleRunReductionFlagDict[sample_run_number] is True:
                assert sample_run_number in self._sampleRunVanadiumDict
                van_run_number = self._sampleRunVanadiumDict[sample_run_number]
                van_run_number_set.add(van_run_number)
        # END-FOR
        assert len(van_run_number_set) > 0, 'There must be at least more than 1 vanadium runs for the sample runs.'

        # Get binning parameters and decide whether to reduce or not
        for van_run_number in van_run_number_set:
            if self._vanadiumRunsManager.has(van_run_number) is False:
                handler = self._reductionManager.reduce_sample_run(van_run_number)
                self._vanadiumRunsManager.set_reduced_vanadium(handler)
            # END-IF
        # END-FOR

        return

    def reduce_runs(self, ipts_number, run_number_list, output_directory, background=False,
                    vanadium=False, gsas=True, fullprof=False, record_file=False,
                    sample_log_file=False):
        """
        Reduce a set of runs with selected options
        Purpose:
        Requirements:
        Guarantees:

        Workflow:
         1. Get a list of runs to reduce;
         2. Get a list of vanadium runs for them;
         3. Reduce all vanadium runs;
         4. Reduce (and possibly chop) runs;

        Arguments:
         - normByVanadium :: flag to normalize by vanadium


        Note:
        1. There is no need to call LoadCalFile explicitly, because AlignAndFocus() will
           check whether the calibration file has been loaded by standard offset and group
           workspace name.
        2. It tries to use most of the existing methods from auto reduction scripts
        Focus and process the selected data sets to powder diffraction data
        for GSAS/Fullprof/ format
        :param run_number_list:
        :param output_directory:
        :param background:
        :param vanadium:
        :param gsas:
        :param fullprof:
        :param record_file:
        :param sample_log_file:
        :return:
        """
        import reduce_VULCAN
        import random

        print 'VANADIUM IS', vanadium

        # check input
        assert isinstance(run_number_list, list), 'Run number must be a list.'

        # set up reduction general
        reduction_setup = reduce_VULCAN.ReductionSetup()
        reduction_setup.set_default_calibration_files()
        reduction_setup.set_output_dir(output_directory)
        if gsas:
            reduction_setup.set_gsas_dir(output_directory, True)

        reduce_all_success = True
        message = ''

        vanadium_tag = '{0:06d}'.format(random.randint(1, 999999))

        for run_number in run_number_list:
            # set up
            reduction_setup.set_run_number(run_number)
            full_event_file_path, ipts_number = self._dataFileDict[run_number]
            reduction_setup.set_event_file(full_event_file_path)
            reduction_setup.set_ipts_number(ipts_number)
            reduction_setup.normalized_by_vanadium = vanadium
            # set up vanadium
            if vanadium:
                try:
                    van_run = self._sampleRunVanadiumDict[run_number]
                    van_gda = self._vanadiumGSASFileDict[van_run]
                except KeyError:
                    reduce_all_success = False
                    message += 'Run {0} has no valid vanadium run set up\n.'.format(run_number)
                    continue
                reduction_setup.set_vanadium(van_run, van_gda, vanadium_tag)


            # init tracker
            self._reductionManager.init_tracker(run_number)

            # reduce
            reducer = reduce_VULCAN.ReduceVulcanData(reduction_setup)
            reduce_good, message = reducer.execute_vulcan_reduction()

            status, ret_obj = reducer.get_reduced_workspaces(chopped=False)
            reduce_all_success = reduce_all_success and status
            if status:
                vdrive_ws, tof_ws, d_ws = ret_obj
                self._reductionManager.set_reduced_workspaces(run_number, vdrive_ws, tof_ws, d_ws)
            else:
                message += 'Failed to reduce run {0} due to {1}.\n'.format(run_number, str(ret_obj))

        # END-FOR

        return reduce_all_success, message

    def save_session(self, out_file_name):
        """ Save session to a dictionary
        :param out_file_name:
        :return:
        """
        # Save to a dictionary
        save_dict = dict()
        save_dict['name'] = self._name
        save_dict['dataFileDict'] = self._dataFileDict
        save_dict['baseDataFileNameList'] = self._baseDataFileNameList
        save_dict['baseDataPath'] = self._baseDataPath

        # Return if out_file_name is None
        if out_file_name is None:
            return save_dict

        assert isinstance(out_file_name, str)
        futil.save_xml(save_dict, out_file_name)

        return None

    def save_splitter_workspace(self, run_number, sample_log_name, file_name):
        """
        Save SplittersWorkspace to standard text file
        :param run_number:
        :param sample_log_name:
        :param file_name:
        :return:
        """
        # TODO/ISSUE/51
        status, err_msg = self._mySlicingManager.save_splitter_ws(run_number, sample_log_name, file_name)

        return status, err_msg

    def save_time_segment(self, time_segment_list, ref_run_number, file_name):
        """
        :param time_segment_list:
        :param ref_run_number:
        :param file_name:
        :return:
        """
        # TODO/ISSUE/51
        # Check
        assert isinstance(time_segment_list, list)
        assert isinstance(ref_run_number, int) or ref_run_number is None
        assert isinstance(file_name, str)

        # Form Segments
        run_start = self._mySlicingManager.get_run_start(ref_run_number, unit='second')

        segment_list = list()
        i_target = 1
        for time_seg in time_segment_list:
            if len(time_seg < 3):
                tmp_target = '%d' % i_target
                i_target += 1
            else:
                tmp_target = '%s' % str(time_seg[2])
            tmp_seg = SampleLogHelper.TimeSegment(time_seg[0], time_seg[1], i_target)
            segment_list.append(tmp_seg)
        # END-IF

        segment_list.sort()

        # Check validity
        num_seg = len(segment_list)
        if num_seg >= 2:
            prev_stop = segment_list[0].stop
            for index in xrange(1, num_seg):
                if prev_stop >= segment_list[index].start:
                    return False, 'Overlapping time segments!'
        # END-IF

        # Write to file
        SampleLogHelper.save_time_segments(file_name, segment_list, ref_run_number, run_start)

        return

    def set_focus_calibration_file(self, focus_cal_file):
        """
        Set the time-focus calibration to reduction manager.
        :param focus_cal_file:
        :return:
        """
        self._reductionManager.set_focus_calibration_file(focus_cal_file)

        return

    def set_reduction_flag(self, run_number, flag):
        """ Set the  reduction flag for a file in SAMPLE run dictionary of this project
        Requirements: run number is non-negative integer and flag is boolean.
        Guarantees:
        :param run_number:
        :param flag: reduction flag
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int)
        assert isinstance(flag, bool)
        assert run_number in self._dataFileDict, 'Run %d is not scanned. Current scanned runs are %s.' % (
            run_number, str(self._dataFileDict.keys()))

        # Check with full name
        file_name = self._dataFileDict[run_number][0]
        assert os.path.exists(file_name), 'Unable to find data file %s.' % file_name

        # Set value
        self._sampleRunReductionFlagDict[run_number] = flag

        return

    def set_reduction_parameters(self, parameter_dict):
        """
        Purpose: set up the parameters to reduce run
        Requirements:
        - reduction manager is available
        - input is a dictionary, key=parameter name, value=parameter value
        :param parameter_dict:
        :return:
        """
        # Check requirements
        assert self._reductionManager is not None
        assert isinstance(parameter_dict, dict)

        self._reductionManager.set_parameters(parameter_dict)

        return

    def set_vanadium_runs(self, run_number_list, van_run_number, van_file_name):
        """
        set the corresponding vanadium run to a list of run numbers
        :param run_number_list:
        :param van_run_number:
        :return: None
        """
        assert isinstance(run_number_list, list), 'blabla 129'
        assert isinstance(van_run_number, int), 'blabla 129B'

        for run_number in run_number_list:
            self._sampleRunVanadiumDict[run_number] = van_run_number

        self._vanadiumGSASFileDict[van_run_number] = van_file_name

        return

    def set_base_data_path(self, data_dir):
        """ Set base data path such as /SNS/VULCAN/
        to locate the data via run number and IPTS
        Requirements:
        1. input is an existing file directory
        :param data_dir: base data directory. for example, /SNS/VULCAN/
        :return: None
        """
        if isinstance(data_dir, str) is True:
            assert os.path.exists(data_dir)
            self._baseDataPath = data_dir
        else:
            raise OSError("Unable to set base data path with unsupported format %s." % str(type(data_dir)))

        return

    def _generateFileName(self, runnumber, iptsstr):
        """ Generate a NeXus file name with full path with essential information

        Arguments:
         - runnumber :: integer run number
         - iptsstr   :: string for IPTS.  It can be either an integer or in format as IPTS-####. 
        """
        # Parse run number and IPTS number
        run = int(runnumber)
        iptsstr = str(iptsstr).lower().split('ipts-')[-1]
        ipts = int(iptsstr)

        # Build file name with path
        # FIXME : VULCAN only now!
        nxsfname = os.path.join(self._baseDataPath, 'IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs'%(ipts, run, run))
        if os.path.exists(nxsfname) is False:
            print "[Warning] NeXus file %s does not exist.  Check run number and IPTS." % (nxsfname)
        else:
            print "[DB] Successfully generate an existing NeXus file with name %s." % (nxsfname)

        return nxsfname


def get_data_key(file_name):
    """ Generate data key according to file name
    :param file_name:
    :return:
    """
    # TODO/NOW - Doc!
    assert isinstance(file_name, str)

    return os.path.basename(file_name)
