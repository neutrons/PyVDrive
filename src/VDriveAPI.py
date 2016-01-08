#####
# Ui_VDrive (beta)
#
# boundary between VDProject and API
# 1. API accepts root directory, runs and etc
# 2. VDProject accepts file names with full path
#
#####
import os
import datetime

import vdrive.VDProject as vp
import vdrive.archivemanager as futil
import vdrive.SampleLogHelper as logHelper
import vdrive.vdrivehelper as vdrivehelper

SUPPORTED_INSTRUMENT = ['VULCAN']


class VDriveAPI(object):
    """
    Class containing the methods to reduce and analyze VULCAN data.
    It is a pure python layer that does not consider GUI.
    VDrivePlot is a GUI applicaton built upon this class
    """
    def __init__(self, instrument_name):
        """
        Initialization
        Purpose:
            Initialize an instance of VDriveAPI
        Requirements:
            Instrument name is supported
        Guarantees:
          Set
            1. Instrument name
          Initialize and set up
            1. myProject
            2. myArchiveManager
            3. mySlicingManager
          Set defaults to
            1. working directory
        :param instrument_name:
        :return:
        """
        # Set up instrument
        assert isinstance(instrument_name, str), 'instrument_name must be string.'
        instrument_name = instrument_name.upper()
        assert instrument_name in SUPPORTED_INSTRUMENT, 'instrument %s is not supported.' % instrument_name
        self._myInstrument = instrument_name

        # initialize (1) vdrive project for reducing data, (2) data archiving manager, and (3) slicing manager
        self._myProject = vp.VDProject('New Project')
        self._myArchiveManager = futil.DataArchiveManager(self._myInstrument)
        self._mySlicingManager = logHelper.SampleLogManager()

        # default working directory to current directory. if it is not writable, then use /tmp/
        self._myWorkDir = os.getcwd()
        if os.access(self._myWorkDir, os.W_OK) is False:
            self._myWorkDir = '/tmp/'

        return

    def add_runs(self, run_tup_list, ipts_number):
        """
        Add runs under an IPTS dir to project
        :param run_tup_list: list of 3-tuple as (1) run number, (2)
        :return:
        """
        assert(isinstance(run_tup_list, list))
        for tup in run_tup_list:
            assert(isinstance(tup, tuple))
            run_number, epoch_time, file_name = tup
            self._myProject.add_run(run_number, file_name, ipts_number)

        return True, ''

    def clean_memory(self, run_number, slicer_tag=None):
        """ Clear memory by deleting workspaces
        :param run_number: run number for the slicer
        :param slicer_tag:
        :return:
        """
        if slicer_tag is not None:
            self._mySlicingManager.clean_workspace(run_number, slicer_tag)

    def clear_runs(self):
        """
        Clear all runs in the VProject. 
        :return:
        """
        try:
            self._myProject.clear_runs()
        except TypeError as e:
            return False, str(e)

        return True, ''

    def export_gsas_file(self, run_number, gsas_file_name):
        """
        Purpose: export a reduced run to GSAS data file
        Requirements:

        Guarantees:

        :param run_number:
        :param gsas_file_name:
        :return:
        """
        # TODO/NOW - 1st Doc, assertion and implement

        raise

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list):
        """
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :return:
        """
        self._mySlicingManager.generate_events_filter_manual(run_number, time_segment_list,relative_time)

    def gen_data_slicer_by_time(self, run_number, start_time, end_time, time_step, tag=None):
        """
        Generate data slicer by time
        :param run_number: run number (integer) or base file name (str)
        :param start_time:
        :param end_time:
        :param time_step:
        :param tag: name of the output workspace
        :return:
        """
        # Get full-path file name according to run number
        if isinstance(run_number, int):
            # run number is a Run Number, locate file
            file_name, ipts_number = self._myProject.get_run_info(run_number)
        elif isinstance(run_number, str):
            # run number is a file name
            base_file_name = run_number
            file_name = self._myProject.get_file_path(base_file_name)
            run_number = None
        else:
            return False, 'Input run_number %s is either an integer or string.' % str(run_number)

        # Checkout log processing session
        self._mySlicingManager.checkout_session(nxs_file_name=file_name, run_number=run_number)

        status, ret_obj = self._mySlicingManager.generate_events_filter_by_time(min_time=start_time,
                                                                           max_time=end_time,
                                                                           time_interval=time_step,
                                                                           tag=tag)

        return status, ret_obj

    def gen_data_slicer_sample_log(self, run_number, sample_log_name,
                                   start_time, end_time, min_log_value, max_log_value,
                                   log_value_step, tag=None):
        """
        Generate data slicer/splitters by log values
        :param run_number:
        :param sample_log_name:
        :param start_time:
        :param end_time:
        :param min_log_value:
        :param max_log_value:
        :param log_value_step:
        :return:
        """
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
        self._mySlicingManager.checkout_session(nxs_file_name=file_name, run_number=run_number)

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
                                                        tag=tag)

        return

    def get_instrument_name(self):
        """
        Instrument's name
        :return:
        """
        return self._myInstrument

    def get_project_runs(self):
        """
        Get project runs
        :return:
        """
        return self._myProject.get_ipts_runs()

    def get_recent_data_directory(self):
        """
        Get the last accessed data directory
        :return:
        """
        return self._myLastDataDirectory

    def get_reduced_runs(self):
        """ Get the runs (run numbers) that have been reduced successfully
        :return:
        """
        return self._myProject.get_reduced_runs()

    def get_reduced_data(self, run_number, target_unit):
        """ Get reduced data
        Purpose:
        Requirements:
        Guarantees: returned with 3 numpy arrays, x, y and e
        :param run_number:
        :param target_unit:
        :return: dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # TODO/NOW - Doc
        assert isinstance(run_number, int), 'blabla'
        assert isinstance(target_unit, str), 'blabla'

        try:
            data_set = self._myProject.get_reduced_data(run_number, target_unit)
            assert isinstance(data_set, dict), 'bla bla bla... ...'
        except RuntimeError as e:
            return False, str(e)

        return True, data_set

    def get_working_dir(self):
        """
        Working directory
        :return:
        """
        return self._myWorkDir

    def get_data_root_directory(self):
        """ Get root data directory such as /SNS/VULCAN
        :return: data root directory, such as /SNS/VULCAN
        """
        return self._myArchiveManager.root_directory

    def get_event_slicer(self, run_number, slicer_type, slicer_id=None, relative_time=True):
        """
        TODO/FIXME What am I supposed to do???
        :param run_number: run number for locate slicer
        :param slicer_id: log name, manual, time (decreasing priority)
        :param slicer_type: string as type of slicer
        :param relative_time: if True, time is in relative to run_start
        :return: vector of floats as time in unit of second
        """
        # Check
        assert isinstance(run_number, int)
        assert isinstance(slicer_type, str)
        assert isinstance(slicer_id, str)

        if slicer_type.lower() == 'time':
            status, ret_obj = self._mySlicingManager.get_slicer_by_time()
        elif slicer_type.lower() == 'log':
            status, ret_obj = self._mySlicingManager.get_slicer_by_log(run_number, slicer_id)
        else:
            status, ret_obj = self._mySlicingManager.get_slicer_by_id(run_number, slicer_id, relative_time)

        if status is False:
            err_msg = ret_obj
            return False, err_msg
        else:
            time_segment_list = ret_obj

        return True, time_segment_list

    def get_file_by_run(self, run_number):
        """ Get data file path by run number
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int)
        file_name, ipts_number = self._myProject.get_run_info(run_number)

        return file_name

    def get_ipts_info(self, ipts):
        """
        Get runs and their information for a certain IPTS
        :param ipts: integer or string as ipts number or ipts directory respectively
        :return: list of 3-tuple: int (run), time (file creation time) and string (full path of run file)
        """
        try:
            if isinstance(ipts, int):
                run_tuple_list = self._myArchiveManager.get_experiment_run_info(ipts)
            elif isinstance(ipts, str):
                ipts_dir = ipts
                run_tuple_list = self._myArchiveManager.get_experiment_run_info_from_directory(ipts_dir)
            else:
                return False, 'IPTS %s is not IPTS number of IPTS directory.' % str(ipts)
        except RuntimeError as e:
            return False, str(e)

        return True, run_tuple_list

    def get_ipts_number_from_dir(self, ipts_dir):
        """ Guess IPTS number from directory
        The routine is that there should be some called /'IPTS-????'/
        :param ipts_dir:
        :return: 2-tuple: integer as IPTS number; 0 as unable to find
        """
        return futil.get_ipts_number_from_dir(ipts_dir)

    def get_run_info(self, run_number):
        """ Get a run's information
        :param run_number:
        :return: 2-tuple as (boolean, 2-tuple (file path, ipts)
        """
        assert isinstance(run_number, int)

        try:
            run_info_tuple = self._myProject.get_run_info(run_number)
        except RuntimeError as re:
            return False, str(re)

        return True, run_info_tuple

    def get_number_runs(self):
        """
        Get the number of runs added to project.
        :return:
        """
        return self._myProject.get_number_data_files()

    def get_runs(self, start_run=None, end_run=None):
        """

        :param start_run:
        :param end_run:
        :return:
        """
        run_list = self._myProject.get_runs()

        # Determine index of start run and end run
        try:
            if start_run is None:
                i_start_run = 0
            else:
                i_start_run = run_list.index(start_run)

            if end_run is None:
                i_end_run = len(run_list) - 1
            else:
                i_end_run = run_list.index(end_run)
        except IndexError as ie:
            return False, 'Either start run %d or end run %d is not added to project.' % (start_run, end_run)

        ret_list = run_list[i_start_run:i_end_run+1]

        return True, ret_list

    def get_sample_log_names(self, smart=False):
        """
        Get names of sample log with time series property
        :param smart: a smart way to show sample log name with more information
        :return:
        """
        if self._mySlicingManager is None:
            return False, 'Log helper has not been initialized.'

        status, ret_obj = self._mySlicingManager.get_sample_log_names(with_info=smart)
        if status is False:
            return False, str(ret_obj)
        else:
            name_list = ret_obj

        return True, name_list

    def get_sample_log_values(self, run_number, log_name, start_time=None, stop_time=None, relative=True):
        """
        Get time and value of a sample log in vector
        Returned time is in unit of second as epoch time
        :param log_name:
        :param relative: if True, then the sample log's vec_time will be relative to Run_start
        :return: 2-tuple as status (boolean) and 2-tuple of vectors.
        """
        assert isinstance(log_name, str)
        try:
            vec_times, vec_value = self._mySlicingManager.get_sample_data(run_number=run_number,
                                                                     sample_log_name=log_name,
                                                                     start_time=start_time,
                                                                     stop_time=stop_time,
                                                                     relative=relative)
        except RuntimeError as e:
            return False, 'Unable to get log %s\'s value due to %s.' % (log_name, str(e))

        return True, (vec_times, vec_value)

    def load_session(self, in_file_name):
        """ Load session from saved file
        Load session from a session file
        :param in_file_name:
        :return: 2-tuple: (boolean, object)
        """
        save_dict = futil.load_from_xml(in_file_name)

        # Set from dictionary
        # matching instrument name
        loaded_instrument = save_dict['myInstrumentName']
        assert loaded_instrument == self._myInstrument

        # archive root directory and working directory
        self._myArchiveManager.root_directory = save_dict['myRootDataDir']
        self._myWorkDir = save_dict['myWorkDir']

        # load vdrive project to _myProject
        self._myProject.load_session_from_dict(save_dict['myProject'])

        return True, in_file_name

    def reduce_data_set(self, norm_by_vanadium=False):
        """ Reduce a set of data
        Purpose:
            Reduce a set of event data
        Requirements:
            Project is well set up
            - At least more than 1 run is set to reduce
            -
        Guarantees:
            Event data will be reduced to diffraction pattern.

        :param norm_by_vanadium: flag to normalize the final reduction data by vanadium
        :return: 2-tuple (boolean, object)
        """
        # Check requirements
        num_runs_flagged = self._myProject.get_number_reduction_runs()
        assert num_runs_flagged > 0, 'At least one run should be flagged for reduction.'

        # Reduce vanadium run for calibration
        if norm_by_vanadium is True:
            try:
                self._myProject.reduce_vanadium_runs()
            except RuntimeError as run_err:
                err_msg = 'Unable to reduce vanadium runs due to %s.' % str(run_err)
                return False, err_msg
        # END-IF (nom_by_vanadium)

        # Reduce runs
        status, ret_obj = self._myProject.reduce_runs()
        # FIXME/TODO/SOON/NOW Remove the previous line!
        try:
            status, ret_obj = self._myProject.reduce_runs()
        except AssertionError as re:
            print '[ERROR] Assertion error from reduce_runs.'
            status = False
            ret_obj = str(re)

        return status, ret_obj

    def set_data_root_directory(self, root_dir):
        """ Set root archive directory
        :rtype : tuple
        :param root_dir:
        :return:
        """
        # Check existence
        if os.path.exists(root_dir) is False:
            return False, 'Directory %s cannot be found.' % root_dir

        self._myArchiveManager.set_data_root_path(root_dir)

        return True, ''

    def set_reduction_flag(self, file_flag_list, clear_flags):
        """ Turn on the flag to reduce for files in the list
        TODO/FIXME/NOW Doc and Fill-in

        :param file_flag_list: list of tuples as "base" file name and boolean flag
        :param clear_flags: clear reduction previously-set reduction flags
        :return:
        """
        # FIXME - This has the same functionality as method set_runs_to_reduce()
        # Check requirements
        assert isinstance(file_flag_list, list), 'bla bla ...'
        assert isinstance(clear_flags, bool)

        # Clear
        if clear_flags is True:
            self._myProject.clear_reduction_flags()

        # Set flags
        num_flags_set = 0
        err_msg = ''
        for run_number, reduction_flag in file_flag_list:
            print '[DB] Set reduction flag for run %d with flag %s.' % (run_number, str(reduction_flag))
            try:
                self._myProject.set_reduction_flag(run_number=run_number, flag=reduction_flag)
                num_flags_set += 1
            except AssertionError as e:
                err_msg += 'Unable to set flag to run %d due to %s\n' % (run_number, str(e))
        # END-FOR

        # Return with error
        if err_msg != '':
            return False, '%d of %d runs cannot be set to reduce due to %s. ' % (
                len(file_flag_list)-num_flags_set, len(file_flag_list), err_msg
            )

        return True, ''

    def save_session(self, out_file_name):
        """ Save current session
        :param out_file_name:
        :return:
        """
        # Create a dictionary for current set up
        save_dict = dict()
        save_dict['myInstrumentName'] = self._myInstrument
        save_dict['myRootDataDir'] = self._myArchiveManager.root_directory
        save_dict['myWorkDir'] = self._myWorkDir
        save_dict['myProject'] = self._myProject.save_session(out_file_name=None)

        # Out file name
        if os.path.isabs(out_file_name) is False:
            out_file_name = os.path.join(self._myWorkDir, out_file_name)
            print '[INFO] Session file is saved to working directory as %s.' % out_file_name

        futil.save_to_xml(save_dict, out_file_name)

        return True, out_file_name

    def save_splitter_workspace(self, run_number, sample_log_name, file_name):
        """
        Save SplittersWorkspace to standard text file
        :param run_number:
        :param sample_log_name:
        :param file_name:
        :return:
        """
        status, err_msg = self._mySlicingManager.save_splitter_ws(run_number, sample_log_name, file_name)

        return status, err_msg

    def save_time_segment(self, time_segment_list, ref_run_number, file_name):
        """
        :param time_segment_list:
        :param ref_run_number:
        :param file_name:
        :return:
        """
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
            tmp_seg = logHelper.TimeSegment(time_seg[0], time_seg[1], i_target)
            segment_list.append(tmp_seg)
        # END-IF

        segment_list.sort(ascending=True)

        # Check validity
        num_seg = len(segment_list)
        if num_seg >= 2:
            prev_stop = segment_list[0].stop
            for index in xrange(1, num_seg):
                if prev_stop >= segment_list[index].start:
                    return False, 'Overlapping time segments!'
        # END-IF

        # Write to file
        logHelper.save_time_segments(file_name, segment_list, ref_run_number, run_start)

        return

    def slice_data(self, run_number, sample_log_name=None, by_time=False):
        """ TODO - DOC
        :return: 2-tuple (boolean, object): True/(list of ws names); False/error message
        """
        # Check
        if sample_log_name is not None and by_time is True:
            return False, 'It is not allowed to specify both sample log name and time!'
        elif sample_log_name is None and by_time is False:
            return False, 'it is not allowed to specify neither sample log nor time!'

        if by_time is True:
            # Slice data by time
            status, ret_obj = self._mySlicingManager.get_slicer_by_time(run_number)
            if status is False:
                err_msg = ret_obj
                return False, err_msg
            else:
                slicer = ret_obj
                sample_log_name = '_TIME_'
                print '[DB] Slicer = ', str(slicer), '\n'
        else:
            # Slice data by log value
            assert isinstance(sample_log_name, str)
            print '[DB] Run number = ', run_number, '\n'
            status, ret_obj = self._mySlicingManager.get_slicer_by_log(run_number, sample_log_name)
            if status is False:
                print '[DB]', ret_obj, '\n'
                return False, ret_obj
            else:
                slicer = ret_obj
            # slicer is a tuple for names of splitter workspace and information workspace
            # print '[DB] Slicer = %s of type %s\n' % (str(slicer), str(type(slicer)))

        status, ret_obj = self._myProject.slice_data(run_number, slicer[0], slicer[1],
                                                     sample_log_name.replace('.', '-'))

        return status, ret_obj

    def set_focus_calibration_file(self, calibration_file):
        """
        Purpose:
            Set the time focusing calibration file to reduction manager
        Requirements:
            Input calibration file is a string
        Guarantees:
            The file is set to reduction manager for future usage
        :param calibration_file:
        :return:
        """
        # Check requirement
        assert isinstance(calibration_file, str), 'Input calibration_file must be of type str.'

        # Set to reduction manager
        self._myProject.set_focus_calibration_file(calibration_file)

        return

    def set_ipts(self, ipts_number):
        """ Set IPTS to the workflow
        Purpose

        Requirement:

        Guarantees:

        :param ipts_number: integer for IPTS number
        :return:
        """
        # Requirements
        assert isinstance(ipts_number, int)
        assert ipts_number > 0

        self._myArchiveManager.set_ipts_number(ipts_number)

        return True, ''

    def set_reduction_parameters(self, parameter_dict):
        """ Set parameters used for reducing powder event data
        Purpose:
            Set up the reduction parameters
        Requirements:
            Parameters' value are given via dictionary
        Guarantees:
            ... ...
        :return:
        """
        assert isinstance(parameter_dict, dict)

        try:
            self._myProject.set_reduction_parameters(parameter_dict)
            status = True
            error_msg = ''
        except RuntimeError as re:
            status = False
            error_msg = 'Unable to set reduction parameters due to %s.' % str(re)

        return status, error_msg

    def set_vanadium_calibration_files(self, run_numbers, vanadium_file_names):
        """
        Purpose:

        Requirements:
            1. run_numbers is list of integers
            2. vanadium_file_names is a list of string
            3. size of run_numbers is equal to size of vanadium file names
        Guarantees:
            1. vanadium calibration file is linked to run number in myProject
        :param run_numbers:
        :param vanadium_file_names:
        :return:
        """
        # TODO/NOW/COMPLETE

        # Check requirements

        # Set pair by pair

        return

    def set_runs_to_reduce(self, run_numbers):
        """ Set runs for reduction
        Purpose:
            Mark the runs to be reduced;
        Requirements:
            Run numbers given should be already loaded
        Guarantees:
            All raw data file should be accessible
        :param run_numbers:
        :return: 2-tuple (boolean, string) for status and error message
        """
        # Check requirements
        assert isinstance(run_numbers, list)
        assert self._myProject is not None

        # Pass the run number list to VDriveProject
        return_status = True
        error_message = ''
        try:
            self._myProject.mark_runs_to_reduce(run_numbers)
        except RuntimeError as re:
            return_status = False
            error_message = 'Unable to set runs %s to reduce due to %s.' % (str(run_numbers), str(re))

        return return_status, error_message

    def set_slicer_helper(self, nxs_file_name, run_number):
        """
        Initialize the event slicing helper object
        :param nxs_file_name:
        :param run_number:
        :return:
        """
        if run_number is not None:
            assert isinstance(run_number, int)
        else:
            run_number = futil.getIptsRunFromFileName(nxs_file_name)[1]

        status, errmsg = self._mySlicingManager.checkout_session(nxs_file_name, run_number)

        return status, errmsg

    def set_slicer(self, splitter_src, sample_log_name=None):
        """ Set slicer from
        'SampleLog', 'Time', 'Manual'
        :param splitter_src:
        :param sample_log_name:
        :return:
        """
        splitter_src = splitter_src.lower()

        if splitter_src == 'samplelog':
            assert isinstance(sample_log_name, str)
            self._mySlicingManager.set_current_slicer_sample_log(sample_log_name)
        elif splitter_src == 'time':
            self._mySlicingManager.set_current_slicer_time()
        elif splitter_src == 'manual':
            self._mySlicingManager.set_current_slicer_manaul()
        else:
            raise RuntimeError('Splitter source %s is not supported.' % splitter_src)

        return

    def set_working_directory(self, work_dir):
        """
        Set up working directory for output files
        :param work_dir:
        :return:
        """
        # Process input working directory
        assert isinstance(work_dir, str)
        if work_dir.startswith('~'):
            work_dir = os.path.expanduser(work_dir)

        try:
            if os.path.exists(work_dir) is False:
                os.mkdir(work_dir)
        except IOError as e:
            return False, 'Unable to create working directory due to %s.' % str(e)

        # Check writable
        if os.access(work_dir, os.W_OK) is False:
            return False, 'Working directory %s is not writable.' % (work_dir)
        else:
            self._myWorkDir = work_dir

        return True, ''


def filter_runs_by_run(run_tuple_list, start_run, end_run):
    """
    Filter runs by range of run numbers
    :param run_tuple_list:
    :param start_run:
    :param end_run:
    :return:
    """
    # Check
    assert(isinstance(run_tuple_list, list))
    assert(isinstance(start_run, int))
    assert(isinstance(end_run, int))
    assert(start_run <= end_run)
    
    # Sort by runs
    run_tuple_list.sort(key=lambda x: x[0])
    
    # FIXME - Use binary search for determine the range of run numbers in the tuple-list
    result_list = []
    for tup in run_tuple_list:
        assert(isinstance(tup[0], int))
        if start_run <= tup[0] <= end_run:
            result_list.append(tup)
    
    return True, result_list


def filter_runs_by_date(run_tuple_list, start_date, end_date, include_end_date=False):
    """
    Filter runs by date.  Any runs ON and AFTER start_date and BEFORE end_date
    will be included.
    :param run_tuple_list: 3-tuple: run number, epoch time in second, file name with full path
    :param start_date:
    :param end_date:
    :param include_end_date: Flag whether the end-date will be included in the return
    :return:
    """
    # Get starting date and end date's epoch time
    try:
        assert(isinstance(start_date, str))
        epoch_start = vdrivehelper.convert_to_epoch(start_date)
        epoch_end = vdrivehelper.convert_to_epoch(end_date)
        if include_end_date is True:
            # Add one day for next date
            epoch_end += 24*3600
        print '[INFO] Time range: %f, %f with dT = %f hours' % (epoch_start, epoch_end,
                                                               (epoch_end-epoch_start)/3600.)
    except ValueError as e:
        return False, str(e)
    
    # Sort by time
    assert isinstance(run_tuple_list, list)
    run_tuple_list.sort(key=lambda x: x[1])
    
    # FIXME - Using binary search will be great!
    result_list = []
    for tup in run_tuple_list:
        file_epoch = tup[1]
        if epoch_start <= file_epoch < epoch_end:
            result_list.append(tup[:])
        # END-IF
    # END-IF

    return True, result_list


def get_splitters_names(base_name):
    """ Get splitter workspaces's name including
    (1) SplittersWS and (2) InformationWS
    using current epoch time
    :param base_name:
    :return:
    """
    now = datetime.datetime.now()
    special_key = '%02d06%d' % (now.second, now.microsecond)

    splitter_ws = '%s_%s_Splitters' % (base_name, special_key)
    info_ws = '%s_%s_Info' % (base_name, special_key)

    return splitter_ws, info_ws


def get_standard_ws_name(file_name, meta_only):
    """
    Get the standard name for a loaded workspace
    :param file_name:
    :return:
    """
    ws_name = os.path.basename(file_name).split('.')[0]

    if meta_only is True:
        ws_name += '_Meta'

    return ws_name


def parse_time_segment_file(file_name):
    """

    :param file_name:
    :return:
    """
    status, ret_obj = logHelper.parse_time_segments(file_name)

    return status, ret_obj


