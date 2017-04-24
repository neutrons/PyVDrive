#####
# Ui_VDrive (beta)
#
# boundary between VDProject and API
# 1. API accepts root directory, runs and etc
# 2. VDProject accepts file names with full path
#
#####
import os
import pandas as pd

import ProjectManager as ProjectMrg
import archivemanager
import vdrivehelper
import mantid_helper
import crystal_helper
import io_peak_file
import reduce_VULCAN
import chop_utility

SUPPORTED_INSTRUMENT = ['VULCAN']


class VDriveAPI(object):
    """
    Class containing the methods to reduce and analyze VULCAN data.
    It is a pure python layer that does not consider GUI.
    VDrivePlot is a GUI application built upon this class
    """
    def __init__(self, instrument_name, module_location=None):
        """
        Initialization
        Purpose:
            Initialize an instance of VDriveAPI
        Requirements:
            Instrument name is supported
        Guarantees:94G
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
        self._myProject = ProjectMrg.ProjectManager('New Project')

        # construct the data location
        if module_location is not None:
            template_data_dir = os.path.join(module_location, 'data')
        else:
            template_data_dir = None
        self._myProject.load_standard_binning_workspace(template_data_dir)
        self._myArchiveManager = archivemanager.DataArchiveManager(self._myInstrument)

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

    # Definition of properties
    @property
    def project(self):
        """
        Get reduction project
        :return:
        """
        return self._myProject

    @property
    def archive_manager(self):
        """ Get the access to archiving manager
        """
        return self._myArchiveManager

    # Definition of algorithms
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
            phase_type = crystal_helper.UnitCell.BCC
        elif phase_type == 'FCC':
            phase_type = crystal_helper.UnitCell.FCC
        elif phase_type == 'HCP':
            phase_type = crystal_helper.UnitCell.HCP
        elif phase_type == 'Body-Center':
            phase_type = crystal_helper.UnitCell.BC
        elif phase_type == 'Face-Center':
            phase_type = crystal_helper.UnitCell.FC
        else:
            raise RuntimeError('Unit cell type %s is not supported.' % phase_type)

        # Get reflections
        unit_cell = crystal_helper.UnitCell(phase_type, lattice_a, lattice_b, lattice_c)
        reflections = crystal_helper.calculate_reflections(unit_cell, min_d, max_d)

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
        d_list = ref_dict.keys()
        d_list.sort(reverse=True)
        reflection_list = list()
        for peak_pos in d_list:
            reflection_list.append((peak_pos, ref_dict[peak_pos]))

        return reflection_list

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
        assert os.access(out_dir, os.W_OK), 'Output directory {0} is not writable.'.format(out_dir)

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

    def find_peaks(self, data_key, bank_number, x_range,
                   auto_find, profile='Gaussian',
                   peak_positions=None, hkl_list=None):
        """
        Find peaks in a given diffraction pattern
        Requirements:
         - by run number, a workspace containing the reduced run must be found
         - either auto (mode) is on or peak positions are given;
         - peak profile is default as Gaussian and is limited to the peak profile supported by Mantid
        :param data_key: a data key (for loaded previously reduced data) or run number
        :param bank_number:
        :param x_range:
        :param peak_positions:
        :param hkl_list:
        :param profile:
        :param auto_find:
        :return: list of tuples for peak information as (peak center, height, width)
        """
        try:
            # raise exceptions if the input parameters are not allowed.
            if isinstance(peak_positions, list) and auto_find:
                raise RuntimeError('It is not allowed to specify both peak positions and turn on auto mode.')
            if peak_positions is None and auto_find is False:
                raise RuntimeError('Either peak positions is given. Or auto mode is turned on.')

            peak_info_list = self._myProject.find_diffraction_peaks(data_key, bank_number, x_range,
                                                                    peak_positions, hkl_list,
                                                                    profile)
        except AssertionError as ass_err:
            return False, 'Unable to find peaks due to {0}'.format(ass_err)

        return True, peak_info_list

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list, slice_tag):
        """ generate event slicer for data manually
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :param slice_tag: string for slice tag name
        :return: slice tag. if user gives slice tag as None, then the returned one is the auto-generated.
        """
        # get the chopper
        chopper = self._myProject.get_chopper(run_number)

        status, slice_tag = chopper.generate_events_filter_manual(run_number=run_number,
                                                                  split_list=time_segment_list,
                                                                  relative_time=relative_time,
                                                                  splitter_tag=slice_tag)

        return status, slice_tag

    def gen_data_slicer_by_time(self, run_number, start_time, end_time, time_step):
        """
        Generate data slicer by time
        :param run_number: run number (integer) or base file name (str)
        :param start_time:
        :param end_time:
        :param time_step:
        :return:
        """
        # check input
        assert run_number is not None, 'Run number cannot be None.'

        # get chopper
        chopper = self._myProject.get_chopper(run_number)

        # generate data slicer
        status, slicer_key = chopper.set_time_slicer(start_time=start_time, time_step=time_step, stop_time=end_time)

        return status, slicer_key

    def gen_data_slicer_sample_log(self, run_number, sample_log_name, log_value_step,
                                   start_time, end_time, min_log_value, max_log_value,
                                   change_direction):
        """
        Generate data slicer/splitters by log values
        :param run_number:
        :param sample_log_name:
        :param log_value_step:
        :param start_time:
        :param end_time:
        :param min_log_value:
        :param max_log_value:
        :param change_direction:
        :return: 2-tuple. [1] True/Slicer Key  [2] False/Error Message
        """
        # check input
        assert run_number is not None, 'Run number cannot be None.'

        # get chopper
        chopper = self._myProject.get_chopper(run_number)

        # generate data slicer
        status, slicer_key = chopper.set_log_value_slicer(sample_log_name, log_value_step,
                                                          start_time=start_time, stop_time=end_time,
                                                          direction=change_direction,
                                                          min_log_value=min_log_value, max_log_value=max_log_value)

        return status, slicer_key

    def get_chopped_data_info(self, run_number, slice_key, reduced):
        """
        get information of chopped data
        :param run_number:
        :param slice_key:
        :param reduced:
        :return: a dictionary
        """
        # TEST/ISSUE/33/s
        if reduced:
            # reduced data. should be found at reductionmanager.py
            tracker = self._myProject.reduction_manager.get_tracker(run_number, slice_key)
            info_dict = tracker.get_information()
        else:
            # jus chopped but not reduced
            raise RuntimeError('Need a use case or scenario to implement this part')

        return info_dict

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

    def get_reduced_chopped_data(self, ipts_number, run_number, chop_seq, search_archive=True, search_dirs=None):
        """
        Find chopped data (in GSAS) in archive or user specified directories
        :param ipts_number:
        :param run_number:
        :param chop_seq:
        :param search_archive: flag to search the chopped data from archive under
            /SNS/VULCAN/IPTS-ipts/shared/ChoppedData/run/ or
            /SNS/VULCAN/IPTS-ipts/shared/binned_data/run/
        :return: 2-tuple [1] boolean (data found) [2] data dictionary
        """
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'
        assert isinstance(run_number, int), 'Run number must be an integer'
        assert isinstance(chop_seq, int), 'chop sequence must be a non-negative integer.'

        # try to get from archive first
        data_set_dict = None
        data_found = False

        # search from archive
        if search_archive:
            try:
                data_set_dict = self._myArchiveManager.get_data_archive_chopped_gsas(ipts_number, run_number, chop_seq)
            except RuntimeError:
                pass
            else:
                data_found = True
        # END-IF

        # search from user-specified directories
        if not data_found and search_dirs is not None:
            try:
                data_set_dict = self._myArchiveManager.get_data_chopped_gsas(search_dirs, run_number, chop_seq)
            except RuntimeError:
                pass
            else:
                data_found = True
        # END-IF

        # check
        if not data_found:
            error_message = 'Unable to find chopped and reduced run %d chopped seq %d' % (run_number, chop_seq)
            ret_obj = error_message
        else:
            assert data_set_dict is not None, 'Data set dictionary cannot be None (i.e., data not found)'
            ret_obj = data_set_dict

        return data_found, ret_obj

    def get_reduced_data(self, run_id, target_unit, ipts_number=None, search_archive=False, is_workspace=False):
        """ Get reduced data
        Purpose: Get all data from a reduced run, either from run number or data key
        Requirements: run ID is either integer or data key.  target unit must be TOF, dSpacing or ...
        Guarantees: returned with 3 numpy arrays, x, y and e
        :param run_id: it is a run number or data key
        :param target_unit:
        :param ipts_number: IPTS number
        :param search_archive: flag to allow search reduced data from archive
        :return: 2-tuple: status and a dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # TODO/ISSUE/33 - Clean
        try:
            # get GSAS file name
            if search_archive and isinstance(run_id, int):
                gsas_file = self._myArchiveManager.get_data_archive_gsas(ipts_number, run_id)
            else:
                gsas_file = None

            # get data from project
            if is_workspace:
                # data_set_dict, current_unit
                data_set_dict, current_unit = mantid_helper.get_data_from_workspace(run_id)
            else:
                data_set_dict = self._myProject.get_reduced_data(run_id, target_unit, gsas_file)
        except RuntimeError as run_err:
            return False, 'Failed to to get data  {0}.  FYI: {1}'.format(run_id, run_err)

        return True, data_set_dict

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
            assert len(data_key) > 0, 'Data key cannot be an empty string.'
            try:
                # FIXME shall use this! info = self._myProject.get_data_bank_list(data_key)
                # TODO/ISSUE/NOW : broken fake
                info = [1, 2]
            except AssertionError as e:
                return False, str(e)

        else:
            # unsupported case
            raise AssertionError('run number %s and data key %s is not supported.' % (str(run_number), str(data_key)))

        return True, info

    def get_reduced_runs(self, with_ipts=True):
        """ Get the runs (run numbers) that have been reduced successfully
        :param with_ipts: if true, then return 2-tuple as (run number, IPTS)
        :return: list of strings?
        """
        return self._myProject.reduction_manager.get_reduced_runs(with_ipts)

    def get_slicer(self, run_number, slicer_id):
        """
        Get the slicer (in vectors) by run number and slicer ID
        :param run_number:
        :param slicer_id:
        :return:  2-tuple.  [1] Boolean [2] (vector time, vector workspace) | error message
        """
        chopper = self._myProject.get_chopper(run_number)
        status, ret_obj = chopper.get_slicer_by_id(slicer_tag=slicer_id, relative_time=True)

        return status, ret_obj

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

    @staticmethod
    def get_data_from_workspace(workspace_name, bank_id=None, target_unit='dSpacing', starting_bank_id=1):
        """
        get data from a workspace
        :param workspace_name:
        :param bank_id:
        :param target_unit:
        :param starting_bank_id: lowest bank ID
        :return: 2-tuple as (boolean, returned object); boolean as status of executing the method
                 if status is False, returned object is a string for error message
                 if status is True and Bank ID is None: returned object is a dictionary with all Bank IDs
                 if status is True and Bank ID is not None: returned object is a dictionary with the specified bank ID.
                 The value of each entry is a tuple with vector X, vector Y and vector Z all in numpy.array
        """
        try:
            data_set_dict, curr_unit = mantid_helper.get_data_from_workspace(workspace_name,
                                                                             bank_id=bank_id,
                                                                             target_unit=target_unit,
                                                                             start_bank_id=starting_bank_id)
        except RuntimeError as run_err:
            return False, str(run_err)

        return True, (data_set_dict, curr_unit)

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

    @staticmethod
    def get_ipts_number_from_dir(dir_name):
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
        get the IPTS configuration
        :param ipts: IPTS number; if None, then it stands for the case as local data reduction
        :return:
        """
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
            ipts_number = self._myArchiveManager.scan_runs_from_directory(ipts_dir)

            status = True
            ret_obj = ipts_number
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
        run_info_dict_list = self._myArchiveManager.get_experiment_run_info(archive_key, range(begin_run, end_run+1))

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
        # call archive manager
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

        return status, ret_obj

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

        # return
        return run_time_list[0], run_time_list[-1]

    def get_ipts_from_run(self, run_number):
        """
        Get IPTS number from run number (only archive)
        :param run_number:
        :return:
        """
        return self._myArchiveManager.get_ipts_number(run_number=run_number)

    def get_run_info(self, run_number, data_key=None):
        """ Get a run's information
        :param run_number:
        :return: 2-tuple as (boolean, 2-tuple (file path, ipts)
        """
        # TODO/ISSUE/65 - Expand this method to get information from loaded GSAS data too
        assert isinstance(run_number, int), 'blabla'

        if run_number is not None:
            try:
                run_info_tuple = self._myProject.get_run_info(run_number)
            except RuntimeError as re:
                return False, str(re)
        elif data_key is not None:
            blabla


        return True, run_info_tuple

    def get_number_runs(self):
        """
        Get the number of runs added to project.
        :return:
        """
        return self._myProject.get_number_data_files()

    def get_runs(self, start_run=None, end_run=None):
        """
        get the run (information) within a range
        :param start_run:
        :param end_run:
        :return: 2-tuple.  boolean as status, list of run information
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

    def get_run_experiment_information(self, run_number):
        """
        get run information such as start, stop time, IPTS name and etc
        :param run_number:
        :return:
        """
        # check input and find Chopper (helper object)
        assert run_number is not None, 'Run number cannot be None.'
        chopper = self._myProject.get_chopper(run_number)

        exp_info = chopper.get_experiment_information()

        return exp_info

    def get_sample_log_names(self, run_number, smart=False):
        """
        Get names of sample log with time series property
        :param run_number:
        :param smart: a smart way to show sample log name with more information
        :return:
        """
        assert run_number is not None, 'Run number cannot be None.'

        chopper = self._myProject.get_chopper(run_number)
        sample_name_list = chopper.get_sample_log_names(smart)

        return True, sample_name_list



    def get_sample_log_values(self, run_number, log_name, start_time=None, stop_time=None, relative=True):
        """
        Get time and value of a sample log in vector
        Returned time is in unit of second as epoch time
        :param run_number:
        :param log_name:
        :param start_time:
        :param stop_time:
        :param relative: if True, then the sample log's vec_time will be relative to Run_start
        :return: 2-tuple as status (boolean) and 2-tuple of vectors.
        """
        # check input
        assert run_number is not None, 'Run number cannot be None.'

        # get chopper
        chopper = self._myProject.get_chopper(run_number)

        # get log values
        vec_times, vec_value = chopper.get_sample_data(sample_log_name=log_name,
                                                       start_time=start_time, stop_time=stop_time,
                                                       relative=relative)

        return True, (vec_times, vec_value)

    @staticmethod
    def import_gsas_peak_file(peak_file_name):
        """ Import a GSAS peak file
        Purpose: import a gsas peak file
        Requirements: peak file is a valid file name
        Guarantees: all peaks are imported
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

    def load_chooped_diffraction_files(self, direcotry, file_type):
        """

        :param direcotry:
        :param file_type:
        :return:
        """
        # TODO/FIXME/NOW/65... SEE 'loaded_data_manager.py'
        self._myProject.data_loading_manager.load_chopped_binned_data

        return

    def load_diffraction_file(self, file_name, file_type):
        """ Load reduced diffraction file to analysis project
        Requirements: file name is a valid string, file type must be a string as 'gsas' or 'fullprof'
        a.k.a. load_gsas_data
        :param file_name
        :param file_type:
        :return:
        """
        data_key = self._myProject.data_loading_manager.load_binned_data(file_name, file_type)

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

    def reduce_data_set(self, auto_reduce, output_directory, background=False,
                        vanadium=False, special_pattern=False,
                        record=False, logs=False, gsas=True, fullprof=False,
                        standard_sample_tuple=None, binning_parameters=None,
                        merge=False):
        """
        Reduce a set of data
        Purpose:
            Reduce a set of event data
        Requirements:
            Project is well set up
            - At least more than 1 run is set to reduce
            -
        Guarantees:
            Event data will be reduced to diffraction pattern.
        :param auto_reduce: boolean flag whether the reduction uses auto reduction script
        :param output_directory:  output directory
        :param binning: binning parameter. [1] None for default; [2] a size 1 container as bin size
                                           [3] a size-3 container as [TOF_min, Bin Size, TOF_max]
        :param background: boolean flag to subtract background
        :param vanadium: boolean flag to normalize by vanadium
        :param special_pattern: boolean flag to normalize by special pattern
        :param record: boolean flag to output AutoRecord and etc.
        :param logs: boolean flag to output sample log files (MTS)
        :param gsas: boolean flag to produce GSAS files from reduced runs
        :param fullprof: boolean flag tro produces Fullprof files from reduced runs
        :param standard_sample_tuple: If specified, then it should process the VULCAN standard sample as #57.
        :param binning_parameters: None for default and otherwise using user specified
        :param merge: If true, then merge the run together by calling SNSPowderReduction
        :return: 2-tuple (boolean, object)
        """
        # Check requirements
        runs_to_reduce = self._myProject.get_runs_to_reduce()
        num_runs_flagged = len(runs_to_reduce)
        assert num_runs_flagged > 0, 'At least one run should be flagged for reduction.'

        # check whether all the runs to reduce are belonged to the same IPTS number
        ipts_set = set()
        for run_number in runs_to_reduce:
            try:
                tmp_ipts_number = self._myArchiveManager.get_ipts_number(run_number)
                ipts_set.add(tmp_ipts_number)
            except KeyError:
                return False, 'Run {0} has not been searched and thus found in archive.'.format(run_number)
        # END-FOR
        assert len(ipts_set) == 1, 'There are runs from different IPTS.  It is not supported in PyVDrive.'
        ipts_number = ipts_set.pop()

        # Reduce data set
        if auto_reduce:
            # auto reduction: auto reduction script does not work with vanadium normalization
            print '[INFO] (Auto) reduce data: IPTS = {0}, Runs = {1}.'.format(ipts_number, runs_to_reduce)
            status, message = self.reduce_auto_script(ipts_number=ipts_number,
                                                      run_numbers=runs_to_reduce,
                                                      output_dir=output_directory,
                                                      is_dry_run=False)
            ret_obj = message

        else:
            # manual reduction: Reduce runs
            print '[INFO] Reduce Runs: {0}.'.format(runs_to_reduce)
            try:
                status, ret_obj = self._myProject.reduce_runs(run_number_list=runs_to_reduce,
                                                              output_directory=output_directory,
                                                              background=background,
                                                              vanadium=vanadium,
                                                              gsas=gsas,
                                                              fullprof=fullprof,
                                                              record_file=record,
                                                              sample_log_file=logs,
                                                              standard_sample_tuple=standard_sample_tuple,
                                                              merge=merge,
                                                              binning_parameters=binning_parameters)

            except AssertionError as re:
                status = False
                ret_obj = '[ERROR] Assertion error from reduce_runs due to %s' % str(re)
            # END-TRY-EXCEPT
        # END-IF-ELSE

        # mark the runs be reduced so that they will not be reduced again next time.
        reduction_state_list = None
        self._myProject.mark_runs_reduced(runs_to_reduce, reduction_state_list)

        return status, ret_obj

    def reduce_auto_script(self, ipts_number, run_numbers, output_dir, is_dry_run):
        """
        Reduce the runs in the standard auto reduction workflow
        :param ipts_number:
        :param run_numbers:
        :param is_dry_run:
        :return: running information
        """
        # self._myProject.reduce_runs(ipts_number=ipts_number,
        #                             run_number_list=run_numbers,
        #                             output_dir=output_dir,
        #                             is_dry_run=is_dry_run,
        #                             mode=auto)
        # TODO/NOW/ - Merge this method with VDProject.reduce_runs()
        raise NotImplementedError('FROM HERE!!! CONTINUE')

        # check inputs' validity
        assert isinstance(ipts_number, int), 'IPTS number %s must be an integer.' % str(ipts_number)
        assert isinstance(run_numbers, list), 'Run numbers must be a list but not %s.' % type(run_numbers)
        assert isinstance(output_dir, str) or output_dir is None, 'Output directory must be a string or None (auto).'
        assert isinstance(is_dry_run, bool), 'Is-Dry-Run must be a boolean'

        status = True
        message = ''

        for run_number in run_numbers:
            # create a new ReductionSetup instance and configure
            reduce_setup = reduce_VULCAN.ReductionSetup()
            # set run number and IPTS
            reduce_setup.set_ipts_number(ipts_number)
            reduce_setup.set_run_number(run_number)
            # set and check input file
            nxs_file_name = '/SNS/VULCAN/IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs' % (ipts_number, run_number, run_number)
            assert os.path.exists(nxs_file_name), 'NeXus file %s does not exist.' % nxs_file_name
            reduce_setup.set_event_file(nxs_file_name)
            # set and check output directory
            if output_dir is None:
                output_dir = '/SNS/VULCAN/IPTS-%d/shared/autoreduce/' % ipts_number
            reduce_setup.set_output_dir(output_dir)
            # set the auto reduction configuration mode
            try:
                reduce_setup.set_auto_reduction_mode()
            except OSError as os_err:
                return False, str(os_err)
            # use default calibration files
            reduce_setup.set_default_calibration_files()

            # generate instance of ReduceVulcanData
            reducer = reduce_VULCAN.ReduceVulcanData(reduce_setup)
            # and reduce!
            if is_dry_run:
                part_status, part_message = reducer.dry_run()
            else:
                part_status, part_message = reducer.execute_vulcan_reduction()

            # contribute the overall message
            status = status and part_status
            message += part_message + '\n'
        # END-FOR (run number)

        return status, message

    def set_data_root_directory(self, root_dir):
        """ Set root archive directory
        :rtype : tuple
        :param root_dir:
        :return:
        """
        # Check existence
        if os.path.exists(root_dir) is False:
            return False, 'Directory %s cannot be found.' % root_dir

        try:
            self._myArchiveManager.root_directory = root_dir
        except OSError as err:
            return False, 'Unable to set data root directory: {0}'.format(str(err))

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
        """ Set runs for reduction by turning on the reduction flag
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
        assert isinstance(run_numbers, list), 'Input run number list must be a list.'
        assert self._myProject is not None, 'Project instance cannot be None.'

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
        assert isinstance(log_file_name, str), 'MTS log file name %s must be a string but not %s.' \
                                               '' % (str(log_file_name), type(log_file_name))
        if log_file_name not in self._mtsLogDict:
            raise KeyError('Log file %s has not been loaded. Loaded files are %s.'
                           '' % (log_file_name, str(self._mtsLogDict.keys())))

        return self._mtsLogDict[log_file_name].keys()

    @staticmethod
    def parse_time_segment_file(file_name):
        """

        :param file_name:
        :return:
        """
        status, ret_obj = chop_utility.parse_time_segments(file_name)

        return status, ret_obj

    def load_vanadium_run(self, ipts_number, run_number, use_reduced_file):
        """
        Load vanadium runs
        :param ipts_number:
        :param run_number:
        :param use_reduced_file:
        :return: 2-tuple.  boolean/string
        """
        van_file_name = None

        # highest priority: load data from
        if use_reduced_file:
            # search reduced GSAS file
            try:
                van_file_name = self._myArchiveManager.get_gsas_file(ipts_number, run_number, check_exist=True)
            except RuntimeError as run_err:
                print '[WARNING]: {0}'.format(run_err)
                van_file_name = None
        # END-IF

        if van_file_name is None:
            # if vanadium gsas file is not found, reduce it
            nxs_file = self._myArchiveManager.get_event_file(ipts_number, run_number, check_file_exist=True)
            self._myProject.add_run(run_number, nxs_file, ipts_number)
            reduced, message = self._myProject.reduce_runs([run_number], output_directory=self._myWorkDir,
                                                           vanadium=False)
            if not reduced:
                return False, 'Unable to reduce vanadium run {0} (IPTS-{1}) due to {2}.' \
                              ''.format(run_number, ipts_number, message)
            else:
                van_ws_key = self._myProject.reduction_manager.get_reduced_run(ipts_number, run_number)
            # END-IF
        else:
            # load vanadium file
            van_ws_key = self._myProject.data_loading_manager.load_binned_data(van_file_name, 'gsas')
            self._myProject.add_reduced_workspace(ipts_number, run_number, van_ws_key)

        return True, van_ws_key

    def process_vanadium_run(self, ipts_number, run_number, use_reduced_file,
                             one_bank=False, do_shift=False, local_output=None):
        """
        process vanadium runs
        :param ipts_number:
        :param run_number:
        :param use_reduced_file:
        :param one_bank:
        :param do_shift:
        :param local_output:
        :return:
        """
        try:
            # get reduced vanadium file
            status, ret_str = self.load_vanadium_run(ipts_number=ipts_number, run_number=run_number,
                                                     use_reduced_file=use_reduced_file)
            if status:
                van_ws_key = ret_str
            else:
                return False, 'Unable to load vanadium run {0} due to {1}.'.format(run_number, ret_str)

            # process vanadium
            self._myProject.vanadium_processing_manager.init_session(van_ws_key, ipts_number, run_number)
            if do_shift:
                # shift is to use a different wavelength.  To Mantid, it is good to use FWHM = 2
                self._myProject.vanadium_processing_manager.apply_shift()
            status, message = self._myProject.vanadium_processing_manager.process_vanadium(save=not one_bank,
                                                                                           output_dir=local_output)

            if one_bank:
                # merge the result to 1 bank
                # TODO/TEST/ISSUE/NOW - Test & remove the debug data
                self._myProject.vanadium_processing_manager.merge_processed_vanadium(save=True, to_archive=True,
                                                                                     local_file_name=local_output)

        except RuntimeError as run_err:
            return False, 'Unable to process vanadium run {0} due to \n\t{1}.'.format(run_number, run_err)

        if status:
            message = 'Vanadium process is successful.' + message

        return status, message

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

    def save_processed_vanadium(self, van_info_tuple, output_file_name):
        """
        save the processed vanadium to a GSAS file
        :param van_info_tuple:
        :param output_file_name:
        :return: 2-tuple (boolean, str)
        """
        assert isinstance(output_file_name, str), 'Output file name must be a string'
        assert isinstance(van_info_tuple, tuple), 'Vanadium information {0} must be a tuple but not a {1}.' \
                                                  ''.format(van_info_tuple, type(van_info_tuple))

        return self._myProject.vanadium_processing_manager.save_vanadium_to_file(vanadium_tuple=van_info_tuple,
                                                                                 to_archive=False,
                                                                                 out_file_name=output_file_name)

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

    def save_splitter_workspace(self, run_number, slicer_tag, file_name):
        """
        Save SplittersWorkspace to standard text file
        :param run_number:
        :param slicer_tag:
        :param file_name:
        :return:
        """
        # get chopper
        assert isinstance(run_number, int), 'Run number must be an integer.'
        chopper = self._myProject.get_chopper(run_number)

        chopper.save_splitter_ws_text(slicer_tag, file_name)

        return

    def save_time_segment(self, ipts_number, run_number, time_segment_list, file_name):
        """
        save the time segments
        :param ipts_number:
        :param run_number:
        :param time_segment_list:
        :param run_number:
        :param file_name:
        :return:
        """
        chopper = self._myProject.get_chopper(run_number)
        chopper.save_time_segment(time_segment_list, file_name)

        return

    def slice_data(self, run_number, slicer_id, reduce_data, output_dir, export_log_type='loadframe'):
        """ Slice data (corresponding to a run) by either log value or time.
        Requirements: slicer/splitters has already been set up for this run.
        Guarantees:
        :param run_number: run number
        :param slicer_id:
        :param reduce_data:
        :param output_dir:
        :return: 2-tuple (boolean, object): True/(list of ws names); False/error message
        """
        # chop data
        status, message = self._myProject.chop_data(run_number, slicer_id, reduce_flag=reduce_data,
                                                    output_dir=output_dir)

        return status, message

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

    # def set_ipts(self, ipts_number):
    #     """ Set IPTS to the workflow
    #     Purpose
    #
    #     Requirement:
    #
    #     Guarantees:
    #
    #     :param ipts_number: integer for IPTS number
    #     :return:
    #     """
    #     # Requirements
    #     assert isinstance(ipts_number, int), 'IPTS number %s must be an integer but not %s.' \
    #                                          '' % (str(ipts_number), type(ipts_number))
    #     assert ipts_number >= 0, 'ITPS number must be a non-negative integer but not %d.' % ipts_number
    #
    #     self._myArchiveManager.set_ipts_number(ipts_number)
    #
    #     return True, ''

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

    def set_vanadium_to_runs(self, ipts_number, run_number_list, van_run_number):
        """
        set corresponding vanadium run to a specific list of sample run numbers
        :param ipts_number:
        :param run_number_list:
        :param van_run_number:
        :return:
        """
        assert isinstance(ipts_number, int), 'ITPS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(van_run_number, int), 'Vanadium run number {0} must be an integer but not {1}.' \
                                                ''.format(van_run_number, type(van_run_number))
        assert isinstance(run_number_list, list), 'Run number list {0} must be a list but not a {1}.' \
                                                  ''.format(run_number_list, type(run_number_list))

        file_exist, van_file_name = self._myArchiveManager.locate_vanadium_gsas_file(ipts_number, van_run_number)
        if not file_exist:
            return False, 'Unable to locate vanadium GSAS file'

        self._myProject.set_vanadium_runs(run_number_list, van_run_number, van_file_name)

        return

    # Found not used
    # def set_slicer_helper(self, nxs_file_name, run_number)
    # Never been implemented
    # def set_slicer(self):

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

    def smooth_diffraction_data(self, workspace_name, bank_id=None,
                                smoother_type='Butterworth', param_n=20, param_order=2,
                                start_bank_id=1):
        """
        smooth spectra of focused diffraction data
        :param workspace_name:
        :param bank_id:
        :param smoother_type:
        :param param_n:
        :param param_order:
        :param start_bank_id:
        :return:
        """
        try:
            if bank_id is None:
                # smooth all spectra
                workspace_index = None
            else:
                # smooth one spectrum
                assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not {1}.' \
                                                 ''.format(bank_id, type(bank_id))
                assert isinstance(start_bank_id, int), 'Starting bank ID {0} must be an integer but not a {1}.' \
                                                       ''.format(start_bank_id, type(start_bank_id))

                workspace_index = bank_id - start_bank_id
            # END-IF

            smoothed_ws_name = self._myProject.vanadium_processing_manager.smooth_spectra(
                workspace_index=None, smoother_type=smoother_type, param_n=param_n, param_order=param_order)

        except RuntimeError as run_err:
            return False, 'Unable to smooth workspace {0} due to {1}.'.format(workspace_name, run_err)

        return True, smoothed_ws_name

    def strip_vanadium_peaks(self, ipts_number, run_number, peak_fwhm,
                             peak_pos_tolerance, background_type, is_high_background,
                             workspace_name):
        """
        strip vanadium peaks.
        This method supports 2 type of inputs
         (1) IPTS and run number;
         (2) workspace name
        :param ipts_number:
        :param run_number:
        :param peak_fwhm:
        :param peak_pos_tolerance:
        :param background_type:
        :param is_high_background:
        :param workspace_name:
        :return:  (boolean, string): True (successful), output workspace name; False (failed), error message
        """
        # get workspace name
        if workspace_name is None:
            # get workspace (key) from IPTS number and run number
            assert isinstance(ipts_number, int), 'Without data key specified, IPTS number must be an integer.'
            assert isinstance(run_number, int), 'Without data key specified, run number must be an integer.'
            if not self._myProject.has_reduced_workspace(ipts_number, run_number):
                error_message = 'Unable to find reduced workspace for IPTS {0} Run {1} without data key.' \
                                ''.format(ipts_number, run_number)
                return False, error_message

            workspace_name = self._myProject.get_reduced_workspace(ipts_number, run_number)
        # END-IF

        # call for strip vanadium peaks
        out_ws_name = self._myProject.vanadium_processing_manager.strip_peaks(peak_fwhm, peak_pos_tolerance,
                                                                              background_type, is_high_background,
                                                                              workspace_name=workspace_name)

        return True, out_ws_name

    def undo_vanadium_peak_strip(self, ipts_number=None, run_number=None):
        """
        undo the peak strip operation on vanadium peaks
        :param ipts_number: if both IPTS and run number are defined, then
        :param run_number:
        :return:
        """
        if ipts_number is not None and run_number is not None:
            if not self._myProject.vanadium_processing_manager.check_ipts_run(ipts_number, run_number):
                raise RuntimeError('Current vanadium processing manager does not work on IPTS {0} Run {1}'
                                   ''.format(ipts_number, run_number))
        # END-IF

        self._myProject.vanadium_processing_manager.undo_peak_strip()

        return

    def undo_vanadium_smoothing(self, ipts_number=None, run_number=None):
        """
        undo the smoothing operation on vanadium peaks
        :param ipts_number: if both IPTS and run number are defined, then
        :param run_number:
        :return:
        """
        if ipts_number is not None and run_number is not None:
            if not self._myProject.vanadium_processing_manager.check_ipts_run(ipts_number, run_number):
                raise RuntimeError('Current vanadium processing manager does not work on IPTS {0} Run {1}'
                                   ''.format(ipts_number, run_number))
        # END-IF

        self._myProject.vanadium_processing_manager.undo_smooth()

        return
