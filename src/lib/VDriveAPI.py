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
import pandas as pd

import VDProject as vp
from analysisproject import AnalysisProject
import archivemanager
import SampleLogHelper
import vdrivehelper
import mantid_helper
import io_peak_file

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
        self._myAnalysisProject = AnalysisProject('New Analysis Project')
        self._myArchiveManager = archivemanager.DataArchiveManager(self._myInstrument)
        self._mySlicingManager = SampleLogHelper.SampleLogManager()

        # default working directory to current directory.
        #  if it is not writable, then use /tmp/
        self._myWorkDir = os.getcwd()
        if os.access(self._myWorkDir, os.W_OK) is False:
            self._myWorkDir = '/tmp/'
        self._rootDataDir = '/SNS/VULCAN/'
        # relative data directory to IPTS data directory for binned GSAS data
        self._relativeBinnedDir = 'binned/'
        # IPTS configuration: key = IPTS number (int), value = list as [raw data dir, binned data dir]
        self._iptsConfigDict = dict()
        # MTS file log
        self._mtsLogDict = dict()
        self._currentMTSLogFileName = None
        return

    @staticmethod
    def _get_default_session_file(mkdir_dir=False):
        """
        Get the default session file name and with full path
        :return:
        """
        session_path = os.path.expanduser('~/.vdrive/')
        if mkdir_dir is True and os.path.exists(session_path) is False:
            os.mkdir(session_path)

        session_file_name = os.path.join(session_path, 'vdrive_session.dat')

        return session_file_name

    def add_runs_to_project(self, run_info_list):
        """
        Add runs under an IPTS dir to project
        :param run_info_list: list of dictionaries. Each dictionary contains information for 1 run
        :param ipts_number:
        :return:
        """
        # check  input
        assert isinstance(run_info_list, list), 'Input run-tuple list must be instance of list but not %s.' \
                                               '' % type(run_info_list)
        # add each run to project
        for index, run_info in enumerate(run_info_list):
            # check type
            assert isinstance(run_info, dict), 'Run information must be an instance of dictionary but not %s.' \
                                          '' % type(run_info)

            # get information and add run
            run_number = run_info['run']
            file_name = run_info['file']
            ipts_number = run_info['ipts']

            self._myProject.add_run(run_number, file_name, ipts_number)

        return True, ''

    @staticmethod
    def calculate_peaks_position(phase, min_d, max_d):
        """
        Purpose: calculate the bragg peaks' position from

        Requirements:
            minimum d-spacing value cannot be 0.
        Guarantees:
          1. return a list of reflections
          2. each reflection is a tuple. first is a float for peak position. second is a list of list for HKLs

        :param phase: [name, type, a, b, c]
        :param min_d: minimum d-spacing value
        :param max_d:
        :return: list of 2-tuples.  Each tuple is a float as d-spacing and a list of HKL's
        """
        # Check requirements
        assert isinstance(phase, list), 'Input Phase must be a list but not %s.' % (str(type(phase)))
        assert len(phase) == 5, 'Input phase  of type list must have 5 elements'
        assert min_d < max_d
        assert min_d > 0.01

        # Get information
        phase_type = phase[1]
        lattice_a = phase[2]
        lattice_b = phase[3]
        lattice_c = phase[4]

        # Convert phase type to
        phase_type = phase_type.split()[0]
        if phase_type == 'BCC':
            phase_type = mantid_helper.UnitCell.BCC
        elif phase_type == 'FCC':
            phase_type = mantid_helper.UnitCell.FCC
        elif phase_type == 'HCP':
            phase_type = mantid_helper.UnitCell.HCP
        elif phase_type == 'Body-Center':
            phase_type = mantid_helper.UnitCell.BC
        elif phase_type == 'Face-Center':
            phase_type = mantid_helper.UnitCell.FC
        else:
            raise RuntimeError('Unit cell type %s is not supported.' % phase_type)

        # Get reflections
        unit_cell = mantid_helper.UnitCell(phase_type, lattice_a, lattice_b, lattice_c)
        reflections = mantid_helper.calculate_reflections(unit_cell, min_d, max_d)

        # Sort by d-space... NOT FINISHED YET
        num_ref = len(reflections)
        ref_dict = dict()
        for i_ref in xrange(num_ref):
            ref_tup = reflections[i_ref]
            assert isinstance(ref_tup, tuple)
            assert len(ref_tup) == 2
            pos_d = ref_tup[1]
            assert isinstance(pos_d, float)
            assert pos_d > 0
            # HKL should be an instance of mantid.kernel._kernel.V3D
            hkl_v3d = ref_tup[0]
            hkl = [hkl_v3d.X(), hkl_v3d.Y(), hkl_v3d.Z()]

            # pos_d has not such key, then add it
            if pos_d not in ref_dict:
                ref_dict[pos_d] = list()
            ref_dict[pos_d].append(hkl)
        # END-FOR

        # Merge all the peaks with peak position within tolerance
        TOL = 0.0001
        # sort the list again with peak positions...
        peak_pos_list = ref_dict.keys()
        peak_pos_list.sort()
        print '[DB] List of peak positions: ', peak_pos_list
        curr_list = None
        curr_pos = -1
        for peak_pos in peak_pos_list:
            if peak_pos - curr_pos < TOL:
                # combine the element (list)
                assert isinstance(curr_list, list)
                curr_list.extend(ref_dict[peak_pos])
                del ref_dict[peak_pos]
            else:
                curr_list = ref_dict[peak_pos]
                curr_pos = peak_pos
        # END-FOR

        # Convert from dictionary to list as 2-tuples

        print '[DB-BAT] List of final reflections:', type(ref_dict)
        d_list = ref_dict.keys()
        d_list.sort(reverse=True)
        reflection_list = list()
        for peak_pos in d_list:
            reflection_list.append((peak_pos, ref_dict[peak_pos]))
            print '[DB-BAT] d = %f\treflections: %s' % (peak_pos, str(ref_dict[peak_pos]))

        return reflection_list

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
        1. run number is a valid integer
        2. run number exists in project
        3. gsas file name includes a path that is writable
        Guarantees: A gsas file is written
        :param run_number:
        :param gsas_file_name:
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int)
        assert run_number > 0

        assert isinstance(gsas_file_name, str)
        out_dir = os.path.dirname(gsas_file_name)
        assert os.writable(out_dir)

        try:
            self._myProject.export_reduced_run_gsas(run_number, gsas_file_name)
        except KeyError as e:
            return False, 'Unable to export reduced run %d to GSAS file due to %s.' % (run_number, gsas_file_name)
        raise

    @staticmethod
    def export_gsas_peak_file(bank_peak_dict, out_file_name):
        """ Export a list of peaks to a GSAS peak file
        Purpose: export a list of peaks to an ASCII file of GSAS peak file format
        Requirements:
            1. peak parameter dictionary is a dictionary of list of list, key is the bank number, value is list of peaks
                of that bank
            2. each sub-list is for one peak.  it should be composed of bank, name, peak centre, peak width and a list
                of centres of overlapped peaks
        Guarantees: a GSAS peak file is created
        :param bank_peak_dict: a dictionary of list of peak value list
        :param out_file_name:
        :return:
        """
        # check requirements
        assert isinstance(bank_peak_dict, dict), 'Input must be a dict but not %s.' % str(type(bank_peak_dict))
        assert isinstance(out_file_name, str)

        # create a manager
        peak_file_manager = io_peak_file.GSASPeakFileManager()

        # add peaks
        for bank_id in sorted(bank_peak_dict.keys()):
            peak_param_list = bank_peak_dict[bank_id]
            assert isinstance(peak_param_list, list)
            for peak_i in peak_param_list:
                assert len(peak_i) == 5
                bank = peak_i[0]
                peak_name = peak_i[1]
                centre = peak_i[2]
                width = peak_i[3]
                overlapped_list = peak_i[4]
                peak_file_manager.add_peak(bank=bank, name=peak_name, position=centre,
                                           width=width, group_id=overlapped_list)
            # END-FOR(peak_i)
        # END-FOR (bank)

        # write
        peak_file_manager.export_peaks(out_file_name)

        return

    def find_peaks(self, data_key, run_number, bank_number, x_range,
                   auto_find, profile='Gaussian',
                   peak_positions=None, hkl_list=None):
        """
        Find peaks in a given diffraction pattern
        Requirements:
         - by run number, a workspace containing the reduced run must be found
         - either auto (mode) is on or peak positions are given;
         - peak profile must be Gaussian and blabla
        :param run_number:
        :param bank_number:
        :param x_range:
        :param peak_positions:
        :param hkl_list:
        :param profile:
        :param auto_find:
        :return: list of tuples for peak information as (peak center, height, width)
        """
        # TODO/NOW - Make more logic!

        if isinstance(run_number, int) is False:
            print '[DB...BAT] To find_peaks(), run number %s is not integer.' % str(run_number)

        # Check
        # ... ... assert isinstance(run_number, int)
        assert isinstance(bank_number, int)
        assert isinstance(x_range, tuple) and len(x_range) == 2
        assert isinstance(profile, str)
        assert isinstance(peak_positions, list) or peak_positions is None

        if isinstance(peak_positions, list) and auto_find:
            raise RuntimeError('It is not allowed to specify both peak positions and turn on auto mode.')
        if peak_positions is None and auto_find is False:
            raise RuntimeError('Either peak positions is given. Or auto mode is turned on.')

        # Get workspace from
        data_ws_name = self._myAnalysisProject.get_workspace_name(data_key)

        if auto_find:
            # find peaks in an automatic way
            peak_info_list = mantid_helper.find_peaks(diff_data=data_ws_name, peak_profile=profile, auto=auto_find)
        else:
            # ... ...
            peak_info_list = mantid_helper.find_peaks(data_ws_name, bank_number, x_range, peak_positions,
                                                      hkl_list, profile)

        return peak_info_list

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list, slice_tag):
        """ generate event slicer for data manually
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :param slice_tag: string for slice tag name
        :return:
        """
        status, ret_obj = self._mySlicingManager.generate_events_filter_manual(
            run_number, time_segment_list, relative_time, slice_tag)

        return status, ret_obj

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

    def get_reduced_data(self, run_id, target_unit):
        """ Get reduced data
        Purpose: Get all data from a reduced run, either from run number or data key
        Requirements: run ID is either integer or data key.  target unit must be TOF, dSpacing or ...
        Guarantees: returned with 3 numpy arrays, x, y and e
        :param run_id: it is a run number or data key
        :param target_unit:
        :return: 2-tuple: status and a dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # Check
        assert isinstance(run_id, int) or isinstance(run_id, str), 'Run ID must be either integer or string,' \
                                                                   'but not %s.' % str(type(run_id))

        assert isinstance(target_unit, str), 'Target unit must be a string but not %s.' % str(type(target_unit))

        if isinstance(run_id, int):
            # case as run number
            run_number = run_id
            data_set = self._myProject.get_reduced_data(run_number, target_unit)
        else:
            # case as dat key
            data_key = run_id
            print '[DB-BAT] VDriveAPI... get data of data key', data_key, 'of type', type(run_id)
            status, ret_obj = self._myAnalysisProject.get_data(data_key=data_key)
            if status is False:
                return False, ret_obj
            data_set = ret_obj
        # END-IF

        assert isinstance(data_set, dict), 'Returned data set should be a dictionary but not %s.' % str(type(data_set))

        return True, data_set

    def get_reduced_run_info(self, run_number, data_key=None):
        """
        Purpose: get information of a reduced run
        Requirements: either run number is specified as a valid integer or data key is given;
        Guarantees: ... ...
        :param run_number:
        :param data_key:
        :return: list of bank ID
        """
        if isinstance(run_number, int):
            # given run number
            try:
                info = self._myProject.get_reduced_run_information(run_number)
            except AssertionError as e:
                return False, str(e)

        elif run_number is None and isinstance(data_key, str):
            # given data key
            assert len(data_key) > 0, 'bla bla'
            try:
                info = self._myAnalysisProject.get_data_information(data_key)
            except AssertionError as e:
                return False, str(e)

        else:
            # unsupported case
            raise AssertionError('run number %s and data key %s is not supported.' % (str(run_number), str(data_key)))

        return True, info

    def get_reduced_runs(self):
        """ Get the runs (run numbers) that have been reduced successfully
        :return: list of strings?
        """
        return self._myProject.get_reduced_runs()

    def get_working_dir(self):
        """
        Working directory
        :return:
        """
        return self._myWorkDir

    def get_binned_data_directory(self, ipts_number=None, run_info_list=None):
        """ Get the directory for the binned data.
        :param ipts_number:
        :param run_info_list: a list of run information in format of dictionary
        :return:
        """
        # check inputs
        assert ipts_number is None or isinstance(ipts_number, int), \
            'IPTS number %s must either be None or an integer but not %s.' % (str(ipts_number), type(ipts_number))

        # if IPTS number is not given, set IPTS number from run information list
        if ipts_number is None:
            if run_info_list is None:
                ipts_number = None
            else:
                assert isinstance(run_info_list, list) and len(run_info_list) > 0, \
                    'Run information list must be a list but not %s.' % type(run_info_list)
                assert isinstance(run_info_list[0], tuple), \
                    'run information is an unexpected %s.' % type(run_info_list[0])
                ipts_number = self.get_run_info(run_info_list[0])

        # set up binned directory
        if ipts_number is None:
            # if IPTS number is still not given, use either current working directory or from configuration
            if len(self._iptsConfigDict) == 0:
                binned_dir = os.getcwd()
            else:
                ipts0 = self._iptsConfigDict.keys()[0]
                binned_dir = self._iptsConfigDict[ipts0][1]
        else:
            # from configuration dictionary using key as ipts number
            binned_dir = self._iptsConfigDict[ipts_number][1]

        return binned_dir

    def get_data_root_directory(self, throw=False):
        """ Get root data directory such as /SNS/VULCAN
        :return: data root directory, such as /SNS/VULCAN/ or None if throw is False
        """
        try:
            root_dir = self._myArchiveManager.root_directory
        except AssertionError as ass_err:
            if throw:
                raise ass_err
            else:
                root_dir = None
            # END-IF-ELSE

        return root_dir

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

    def get_ipts_number_from_dir(self, dir_name):
        """
        Parse IPTS number from a directory path if it is a standard VULCAN archive directory
        :param dir_name: path to the directory
        :return: (boolean, ipts number/error message)
        """
        # check inputs
        assert isinstance(dir_name, str), 'Directory name %s must be a string but not of type %s.' \
                                          '' % (str(dir_name), type(dir_name))

        return vdrivehelper.get_ipts_number_from_dir(dir_name)

    def get_file_by_run(self, run_number):
        """ Get data file path by run number
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int)
        file_name, ipts_number = self._myProject.get_run_info(run_number)

        return file_name

    def get_ipts_config(self, ipts=None):
        """

        :param ipts:
        :return:
        """
        # TODO/NOW - Doc

        print '[DB-BAT] IPTS config dict = ', self._iptsConfigDict

        if ipts is None:
            if len(self._iptsConfigDict) == 0:
                return [None, None]
            else:
                ipts = self._iptsConfigDict.keys()[0]
                return self._iptsConfigDict[ipts]
        # END-IF

        return self._iptsConfigDict[ipts]

    def scan_ipts_archive(self, ipts_dir):
        """
        Scan IPTS archive
        :param ipts_dir:
        :return: str as key to locate the loaded IPTS information from API/data archive
        """
        status = False

        try:
            archive_key = self._myArchiveManager.scan_experiment_run_info(ipts_dir)

            status = True
            ret_obj = archive_key
        except AssertionError as ass_err:
            ret_obj = str(ass_err)

        return status, ret_obj

    def scan_vulcan_record(self, log_file_path):
        """
        Scan a standard VULCAN record/log file
        :param log_file_path:
        :return:
        """
        status = False

        try:
            archive_key = self._myArchiveManager.scan_vulcan_record(log_file_path)
            status = True
            ret_obj = archive_key
        except AssertionError as ass_err:
            ret_obj = str(ass_err)

        return status, ret_obj

    def get_archived_runs(self, archive_key, begin_run, end_run):
        """
        Get runs from archived data
        :param archive_key:
        :param begin_run:
        :param end_run:
        :return:
        """
        # check input
        assert isinstance(archive_key, str), 'Archive key %s must be a string but not of type %s.' \
                                             '' % (str(archive_key), type(archive_key))
        run_info_dict_list = self._myArchiveManager.get_experiment_run_info(archive_key, begin_run, end_run)

        if len(run_info_dict_list) > 0:
            status = True
            ret_obj = run_info_dict_list
        else:
            status = False
            ret_obj = 'No run is selected from %d to %d' % (begin_run, end_run)

        return status, ret_obj

    def get_local_runs(self, archive_key, local_dir, begin_run, end_run, standard_sns_file):
        """
        Get the local runs (data file)
        :param archive_key:
        :param local_dir:
        :param begin_run:
        :param end_run:
        :param standard_sns_file:
        :return:
        """
        print '[DB...BAT] Archive key = ', archive_key

        # call archive mananger
        run_info_dict_list = self._myArchiveManager.get_local_run_info(archive_key, local_dir, begin_run, end_run,
                                                                       standard_sns_file)

        if len(run_info_dict_list) > 0:
            status = True
            ret_obj = run_info_dict_list
        else:
            status = False
            ret_obj = 'No valid data file is found in directory %s from run %d to run %d.' % (local_dir,
                                                                                              begin_run,
                                                                                              end_run)

        return

    def get_ipts_run_range(self, archive_key):
        """
        Get range of run in IPTS
        :param archive_key:
        :return: 2-tuples of 2-tuple
        """
        # check
        assert isinstance(archive_key, str), 'Archive key must be a string.'

        # get run-dict list
        run_info_list = self._myArchiveManager.get_experiment_run_info(archive_key)

        # sort by run number
        run_time_list = list()
        for run_dict in run_info_list:
            run_number = run_dict['run']
            run_time = run_dict['time']
            run_time_list.append((run_number, run_time))
        # END-IF
        run_time_list.sort()

        print '[DB....BAT] Run-Time List: Size = ', len(run_time_list)

        # return
        return run_time_list[0], run_time_list[-1]

    def get_ipts_from_run(self, run_number):
        """
        Get IPTS number from run number (only archive)
        :param run_number:
        :return:
        """
        return self._myArchiveManager.get_ipts_number(run_number=run_number, throw=False)

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

    @staticmethod
    def import_gsas_peak_file(peak_file_name):
        """ Import a GSAS peak file
        Purpose: import a gsas peak file
        Requirements: peak file is a valid file name
        Guarantees: all peaks are imported
        :param self:
        :param peak_file_name:
        :return:
        """
        # Check requirements
        assert isinstance(peak_file_name, str)

        # Import peak file and get peaks
        peak_manager = io_peak_file.GSASPeakFileManager()
        peak_manager.import_peaks(peak_file_name)
        peak_list = peak_manager.get_peaks()

        return peak_list

    def load_diffraction_file(self, file_name, file_type):
        """ Load reduced diffraction file to analysis project
        Requirements: file name is a valid string, file type must be a string as 'gsas' or 'fullprof'
        :param file_type:
        :return:
        """
        # Check requirements
        assert isinstance(file_name, str), 'blabla'
        assert isinstance(file_type, str), 'blabla'

        # Load
        if file_type.lower() == 'gsas':
            # load
            data_key = self._myAnalysisProject.load_data(data_file_name=file_name, data_type=file_type)
            """
            gss_ws_name = get_standard_ws_name(file_name, False)
            mantid_helper.load_gsas_file(file_name, gss_ws_name)
            """
        else:
            raise RuntimeError('Unable to support %s file.' % file_type)

        # data_key = os.path.basename(file_name)

        print '[DB-BAT] Load %s and reference it by %s.' % (file_name, data_key)

        return data_key

    def load_session(self, in_file_name=None):
        """ Load session from saved file
        Load session from a session file
        :param in_file_name:
        :return: 2-tuple: (boolean, object)
        """
        # Check requirements
        assert isinstance(in_file_name, str) or in_file_name is None

        # get default session file if is not given
        if in_file_name is None:
            in_file_name = self._get_default_session_file()
            if os.path.exists(in_file_name) is False:
                return False, 'Unable to locate default session file %s.' % in_file_name

        # check session file
        assert len(in_file_name) > 0

        status, save_dict = archivemanager.load_from_xml(in_file_name)
        if status is False:
            error_message = save_dict
            return status, error_message

        # Set from dictionary
        # matching instrument name
        loaded_instrument = save_dict['myInstrumentName']
        assert loaded_instrument == self._myInstrument

        # archive root directory and working directory
        self._myArchiveManager.root_directory = save_dict['myRootDataDir']
        self._myWorkDir = save_dict['myWorkDir']

        # ipts dir
        # TODO/NOW - more work!
        ipts_number = int(save_dict['IPTSConfig'])
        if ipts_number > 0:
            bin_dir = save_dict['IPTSGSSDir']
            self._iptsConfigDict[ipts_number] = ['', bin_dir]

        # load vdrive project to _myProject
        self._myProject.load_session_from_dict(save_dict['myProject'])

        return True, in_file_name

    def reduce_data_set(self, norm_by_vanadium=False, bin_size=None):
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

    def setup_merge(self, ipts_number, merge_run_dict):
        """
        Set up merge information
        :param ipts_number:
        :param merge_run_dict:
        :return:
        """
        # check inputs
        assert isinstance(ipts_number, int) and ipts_number > 0, 'IPTS number must be a positive integer.'
        assert isinstance(merge_run_dict, dict)

        # set up
        self._mergeSetupDict[ipts_number] = merge_run_dict

        return

    def set_reduction_flag(self, file_flag_list, clear_flags):
        """ Turn on the flag to reduce for files in the list
        Requirements: input a list of data files with reduction flag
        Guarantees: the reduction flag is set properly on the file
        Note: this is a complicated version of set_runs_to_reduce
        :param file_flag_list: list of tuples as "base" file name and boolean flag
        :param clear_flags: clear reduction previously-set reduction flags
        :return:
        """
        # Check requirements
        assert isinstance(file_flag_list, list), 'Input file/flag must be a list ' \
                                                 'but not %s.' % str(type(file_flag_list))
        assert isinstance(clear_flags, bool)

        # Clear
        if clear_flags is True:
            self._myProject.clear_reduction_flags()

        # Create a list of runs to reduce
        run_number_list = list()
        for run_number, reduction_flag in file_flag_list:
            if reduction_flag:
                run_number_list.append(run_number)
            # END-IF
        # END-FOR

        status, err_msg = self.set_runs_to_reduce(run_number_list)

        return status, err_msg

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

    def get_mts_log_data(self, log_file_name, header_list):
        """
        Get MTS log data from loaded MTS log (may partially)
        :param log_file_name: key to find out log file
        :param header_list: column to return
        :return: dictionary: key is column name given in header_list, value: 1D numpy array
        """
        # get default
        if log_file_name is None:
            log_file_name = self._currentMTSLogFileName

        # check
        assert isinstance(log_file_name, str), 'get_mts_log_data(): Log file %s must be a string but not %s.' \
                                               '' % (str(log_file_name), str(type(log_file_name)))
        assert log_file_name in self._mtsLogDict, 'Log file %s has not been loaded. Current loaded are' \
                                                  '%s.' % (log_file_name, str(self._mtsLogDict.keys()))
        assert isinstance(header_list, list), 'Header list must a list'
        for name in header_list:
            assert name in self._mtsLogDict[log_file_name], 'Header %s is not in Pandas series, which ' \
                                                            'current has headers as %s.' % \
                                                            (name, self._mtsLogDict[log_file_name].keys())

        # form the return by converting to numpy array
        return_dict = dict()
        for name in header_list:
            log_array = self._mtsLogDict[log_file_name][name].values
            return_dict[name] = log_array

        return return_dict

    def get_mts_log_headers(self, log_file_name):
        """
        Get the headers of the loaded MTS log file
        :param log_file_name:
        :return:
        """
        # check
        assert isinstance(log_file_name, str), 'blabla'
        if log_file_name not in self._mtsLogDict:
            raise KeyError('Log file %s has not been loaded. Loaded files are %s.'
                           '' % (log_file_name, str(self._mtsLogDict.keys())))

        return self._mtsLogDict[log_file_name].keys()

    def read_mts_log(self, log_file_name, format_dict, block_index, start_point_index, end_point_index):
        """
        Read (partially) MTS file
        :return:
        """
        # check existence of file
        assert isinstance(log_file_name, str)
        assert os.path.exists(log_file_name)

        # get format information
        assert isinstance(format_dict, dict), 'format_dict must be a dictionary but not %s.' \
                                              '' % str(type(format_dict))
        assert isinstance(block_index, int)
        assert block_index in format_dict['data'], \
            'Format dictionary does not have block key %d. Current keys are %s.' \
            '' % (block_index, str(format_dict['data'].keys()))

        # get format parameters
        header = format_dict['header'][block_index]
        block_start_line = format_dict['data'][block_index][0]
        block_end_line = format_dict['data'][block_index][1]

        data_line_number = block_start_line + start_point_index
        num_points = min(end_point_index - start_point_index, block_end_line - data_line_number)

        print '[DB.,,,,..BAT] Read MTS Block %d, Start Point = %d, End Point = %d: block : %d, %d ' % (
            block_index, start_point_index, end_point_index, block_start_line, block_end_line),
        print 'read from line %d with number of points = %d' % (data_line_number, num_points)

        # load file
        # TODO/FIXME - sep is fixed to \t now.  It might not be a good approach
        print '[DB...BAT] File name = ', log_file_name, 'Skip = ', data_line_number, 'Names: ', header,
        print 'Number of points = ', num_points
        mts_series = pd.read_csv(log_file_name, skiprows=data_line_number,
                                 names=header, nrows=num_points,
                                 sep='\t')

        self._mtsLogDict[log_file_name] = mts_series
        self._currentMTSLogFileName = log_file_name

        return

    def save_session(self, out_file_name=None):
        """ Save current session
        :param out_file_name: target file name to save session. If left None, a default will be created
        :return:
        """
        # check
        if out_file_name is None:
            out_file_name = self._get_default_session_file(mkdir_dir=True)
        else:
            assert isinstance(out_file_name, str)

        # Create a dictionary for current set up
        save_dict = dict()
        save_dict['myInstrumentName'] = self._myInstrument
        save_dict['myRootDataDir'] = self._myArchiveManager.root_directory
        save_dict['myWorkDir'] = self._myWorkDir

        # IPTS configuration
        # TODO/NOW - More data to be saved
        if len(self._iptsConfigDict) > 0:
            curr_ipts = self._iptsConfigDict.keys()[0]
            binned_dir = self._iptsConfigDict[curr_ipts][1]
            save_dict['IPTSConfig'] = curr_ipts
            save_dict['IPTSGSSDir'] = binned_dir
        else:
            save_dict['IPTSConfig'] = -1

        save_dict['myProject'] = self._myProject.save_session(out_file_name=None)

        # Out file name
        if os.path.isabs(out_file_name) is False:
            out_file_name = os.path.join(self._myWorkDir, out_file_name)
            print '[INFO] Session file is saved to working directory as %s.' % out_file_name

        archivemanager.save_to_xml(save_dict, out_file_name)

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
            tmp_seg = SampleLogHelper.TimeSegment(time_seg[0], time_seg[1], i_target)
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
        SampleLogHelper.save_time_segments(file_name, segment_list, ref_run_number, run_start)

        return

    def slice_data(self, run_number, sample_log_name=None, by_time=False):
        """ Slice data (corresponding to a run) by either log value or time.
        Requirements: slicer/splitters has already been set up for this run.
        Guarantees:
        :param run_number: run number
        :param sample_log_name:
        :param by_time:
        :return: 2-tuple (boolean, object): True/(list of ws names); False/error message
        """
        # Check. Must either by sample log or by time
        if sample_log_name is not None and by_time is True:
            return False, 'It is not allowed to specify both sample log name and time!'
        elif sample_log_name is None and by_time is False:
            return False, 'it is not allowed to specify neither sample log nor time!'

        # Get and check slicers/splitters
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

        # Slice/split data
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
        assert isinstance(ipts_number, int), 'IPTS number %s must be an integer but not %s.' \
                                             '' % (str(ipts_number), type(ipts_number))
        assert ipts_number >= 0, 'ITPS number must be a non-negative integer but not %d.' % ipts_number

        self._myArchiveManager.set_ipts_number(ipts_number)

        return True, ''

    def set_ipts_config(self, ipts_number, data_dir, binned_data_dir):
        """
        Set configuration for a particular IPTS
        :param ipts_number:
        :param data_dir:
        :param binned_data_dir:
        :return:
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number %s must be an integer but not %s.' \
                                             '' % (str(ipts_number), type(ipts_number))
        assert isinstance(data_dir, str) and os.path.exists(data_dir), \
            'Data directory %s of type (%s) must be a string and exists.' % (str(data_dir), type(data_dir))
        assert isinstance(binned_data_dir, str) and os.path.exists(binned_data_dir), \
            'Binned data directory %s of type (%s) must be a string and exists.' % (str(binned_data_dir),
                                                                                    type(binned_data_dir))

        # set up the configuration as a 2-item list
        self._iptsConfigDict[ipts_number] = [data_dir, binned_data_dir]

        return

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
            run_number = archivemanager.DataArchiveManager.get_ipts_run_from_file_name(nxs_file_name)[1]

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
    file_type = os.path.basename(file_name).split('.')[1]
    if file_type.lower() == 'gsa' or file_type.lower() == 'gda':
        ws_name += '_gda'

    if meta_only is True:
        ws_name += '_Meta'

    return ws_name


def parse_time_segment_file(file_name):
    """

    :param file_name:
    :return:
    """
    status, ret_obj = SampleLogHelper.parse_time_segments(file_name)

    return status, ret_obj


