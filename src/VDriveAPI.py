#####
# Ui_VDrive (beta)
#
# boundary between VDProject and API
# 1. API accepts root directory, runs and etc
# 2. VDProject accepts file names with full path
#
#####
import os

import vdrive.VDProject as vp
import vdrive.FacilityUtil as futil
import vdrive.SampleLogHelper as logHelper


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
        self._myWorkDir = '/tmp/'

        self._currentIPTS = -1

        # Project
        self._myProject = vp.VDProject('Temp')
        self._myFacilityHelper = futil.FacilityUtilityHelper(self._myInstrumentName)

        # Data slicing helper
        self._myLogHelper = None

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
        :return:
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

    def init_slicing_helper(self, nxs_file_name):
        """
        Initialize the event slicing helper object
        :param nxs_file_name:
        :return:
        """
        self._myLogHelper = logHelper.SampleLogManager()
        status, errmsg = self._myLogHelper.set_nexus_file(nxs_file_name)

        return status, errmsg

    def get_sample_log_names(self):
        """
        Get names of sample log with time series property
        :return:
        """
        if self._myLogHelper is None:
            return False, 'Log helper has not been initialized.'

        return self._myLogHelper.get_sample_log_names()

    def get_sample_log_values(self, log_name):
        """
        Get time and value of a sample log in vector
        Returned time is in unit of second as epoch time
        :param log_name:
        :return: 2-tuple as status (boolean) and 2-tuple of vectors.
        """
        try:
            vec_times, vec_value = self._myLogHelper.get_sample_data(log_name)
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
            return False, 'Directory %s cannot be found.' % (root_dir)

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
            print '[DB] Session file is saved to working directory as %s.' % out_file_name

        futil.save_to_xml(save_dict, out_file_name)

        return True, out_file_name

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


    def set_working_directory(self, work_dir):
        """
        Set up working directory for output files
        :param work_dir:
        :return:
        """
        try:
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
            print '[DB] Time range: %f, %f with dT = %f hours' % (epoch_start, epoch_end,
                                                                  (epoch_end-epoch_start)/3600.)
        except ValueError as e:
            return False, str(e)

        # Sort by time
        assert isinstance(run_tuple_list, list)
        run_tuple_list.sort(key=lambda x: x[1])
        print '[DB] Runs range from (epoch time) %f to %f' % (run_tuple_list[0][1],
                                                              run_tuple_list[-1][1])

        # FIXME - Using binary search will be great!
        result_list = []
        for tup in run_tuple_list:
            file_epoch = tup[1]
            if epoch_start <= file_epoch < epoch_end:
                result_list.append(tup[:])
            # END-IF
        # END-IF

        return True, result_list
