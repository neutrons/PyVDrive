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
import vdrive.FacilityUtil as futil
import vdrive.SampleLogHelper as logHelper
import vdrive.mantid_helper as mtdHelper


class VDriveAPI(object):
    """
    Class containing the methods to reduce and analyze VULCAN data.
    It is a pure python layer that does not consider GUI.
    VDrivePlot is a GUI applicaton built upon this class
    """
    def __init__(self):
        """
        Initialization
        :return:
        """
        # Define class variables with defaults
        self._myInstrumentName = 'VULCAN'
        self._myRootDataDir = '/SNS/VULCAN'

        self._myWorkDir = os.getcwd()
        if os.access(self._myWorkDir, os.W_OK) is False:
            self._myWorkDir = '/tmp/'

        self._currentIPTS = -1
        self._myLastDataDirectory = '/tmp'

        # Project
        self._myProject = vp.VDProject('Temp')
        self._myFacilityHelper = futil.FacilityUtilityHelper(self._myInstrumentName)

        # Data slicing helper
        self._myLogHelper = logHelper.SampleLogManager()
        self._splitterDict = dict()

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
            self._myLogHelper.clean_workspace(run_number, slicer_tag)

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

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list):
        """
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :return:
        """
        self._myLogHelper.generate_events_filter_manual(run_number, time_segment_list,relative_time)

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
        self._myLogHelper.checkout_session(nxs_file_name=file_name, run_number=run_number)

        status, ret_obj = self._myLogHelper.generate_events_filter_by_time(min_time=start_time,
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
        self._myLogHelper.checkout_session(nxs_file_name=file_name, run_number=run_number)

        # this_ws_name = get_standard_ws_name(file_name, True)
        # mtdHelper.load_nexus(file_name, this_ws_name, True)
        # slicer_name, info_name = get_splitters_names(this_ws_name)
        # print '[DB] slicer_name = ', slicer_name, 'info_name = ', info_name, 'ws_name = ', this_ws_name,
        # print 'log_name = ', sample_log_name

        # FIXME - Need to pass value change direction
        self._myLogHelper.generate_events_filter_by_log(log_name=sample_log_name,
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
        return self._myInstrumentName

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
        return self._myRootDataDir

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
            status, ret_obj = self._myLogHelper.get_slicer_by_time()
        elif slicer_type.lower() == 'log':
            status, ret_obj = self._myLogHelper.get_slicer_by_log(run_number, slicer_id)
        else:
            status, ret_obj = self._myLogHelper.get_slicer_by_id(run_number, slicer_id)

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
                ipts_number = ipts
                run_tuple_list = self._myFacilityHelper.get_run_info(ipts_number)
            elif isinstance(ipts, str):
                ipts_dir = ipts
                run_tuple_list = self._myFacilityHelper.get_run_info_dir(ipts_dir)
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
        if self._myLogHelper is None:
            return False, 'Log helper has not been initialized.'

        status, ret_obj = self._myLogHelper.get_sample_log_names(with_info=smart)
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
            vec_times, vec_value = self._myLogHelper.get_sample_data(run_number=run_number,
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
        :return:
        """
        save_dict = futil.load_from_xml(in_file_name)

        # Set from dictionary
        # class variables
        self._myInstrumentName = save_dict['myInstrumentName']
        self._myRootDataDir = save_dict['myRootDataDir']
        self._myWorkDir = save_dict['myWorkDir']

        self._myFacilityHelper = futil.FacilityUtilityHelper(self._myInstrumentName)

        # create a VDProject
        self._myProject.load_session_from_dict(save_dict['myProject'])

        return True, in_file_name

    def set_data_root_directory(self, root_dir):
        """ Set root data directory to
        :rtype : tuple
        :param root_dir:
        :return:
        """
        # Check existence
        if os.path.exists(root_dir) is False:
            return False, 'Directory %s cannot be found.' % root_dir

        self._myRootDataDir = root_dir
        self._myFacilityHelper.set_data_root_path(self._myRootDataDir)

        return True, ''

    def save_session(self, out_file_name):
        """ Save current session
        :param out_file_name:
        :return:
        """
        # Create a dictionary for current set up
        save_dict = dict()
        save_dict['myInstrumentName'] = self._myInstrumentName
        save_dict['myRootDataDir'] = self._myRootDataDir
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
        status, err_msg = self._myLogHelper.save_splitter_ws(run_number, sample_log_name, file_name)

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
        run_start = self._myLogHelper.get_run_start(ref_run_number, unit='second')

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
            status, ret_obj = self._myLogHelper.get_slicer_by_time(run_number)
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
            status, ret_obj = self._myLogHelper.get_slicer_by_log(run_number, sample_log_name)
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

    def set_ipts(self, ipts_number):
        """ Set IPTS to the workflow
        :param ipts_number: intege for IPTS number
        :return:
        """
        try:
            self._currentIPTS = int(ipts_number)
        except ValueError as e:
            return False, 'Unable to set IPTS number due to %s.' % str(e)

        return True, ''

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

        status, errmsg = self._myLogHelper.checkout_session(nxs_file_name, run_number)

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
            self._myLogHelper.set_current_slicer_sample_log(sample_log_name)
        elif splitter_src == 'time':
            self._myLogHelper.set_current_slicer_time()
        elif splitter_src == 'manual':
            self._myLogHelper.set_current_slicer_manaul()
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
            epoch_start = futil.convert_to_epoch(start_date)
            epoch_end = futil.convert_to_epoch(end_date)
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


