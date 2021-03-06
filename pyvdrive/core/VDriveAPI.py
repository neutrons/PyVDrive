#####
# Ui_VDrive (beta)
#
# boundary between VDProject and API
# 1. API accepts root directory, runs and etc
# 2. VDProject accepts file names with full path
#
#####
import os

from pyvdrive.core import ProjectManager
from pyvdrive.core import archivemanager
from pyvdrive.core import vdrivehelper
from pyvdrive.core import mantid_helper
from pyvdrive.core import crystal_helper
from pyvdrive.core import io_peak_file
from pyvdrive.core import reduce_VULCAN
from pyvdrive.core import chop_utility
from pyvdrive.core import datatypeutility

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
        self._myProject = ProjectManager.ProjectManager(self, 'New Project', 'VULCAN')

        # construct the data location
        # if module_location is not None:
        #     template_data_dir = os.path.join(module_location, 'data')
        # else:
        #     template_data_dir = None
        # REMOVED 2018 TODO self._myProject.load_standard_binning_workspace(template_data_dir)
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
        :param run_info_list: list of dictionaries or integer.
            (1) Each dictionary contains information for 1 run
            (2) integer shall be a run number such that it will use the stored information in Project
        :return:
        """
        # check  input
        assert isinstance(run_info_list, list), 'Input run-tuple list must be instance of list but not %s.' \
                                                '' % type(run_info_list)
        # add each run to project
        for index, run_info in enumerate(run_info_list):
            # treat differently according to type
            if isinstance(run_info, dict):
                # get information and add run
                run_number = run_info['run']
                file_name = run_info['file']
                ipts_number = run_info['ipts']
            elif isinstance(run_info, int):
                # a run number is given
                run_number = run_info
                file_name = None
                ipts_number = None
            else:
                # not supported type
                raise RuntimeError(
                    'Run information must be an instance of dictionary but not %s.' % type(run_info))
            # END-IF

            # add
            self._myProject.add_run(run_number, file_name, ipts_number)
        # END-FOR

        return True, ''

    def calculate_peak_parameters(self, ipts_number, run_number_list, chop_list, x_min, x_max, write_to_console,
                                  output_file):
        """Calculate a peak or several overlapped peaks' parameters

        These parameters include integral intensity, average d-spacing and variance
        :param ipts_number:
        :param run_number_list:
        :param chop_list:
        :param x_min:
        :param x_max:
        :param write_to_console:
        :param output_file:
        :return: 2-tuple.  status, message
        """
        try:
            data_dict = self._myProject.calculate_peaks_parameter(ipts_number, run_number_list,
                                                                  chop_list,
                                                                  x_min, x_max, write_to_console,
                                                                  output_file)

        except RuntimeError as run_err:
            return False, 'Unable to calculate peak parameters due to {0}'.format(run_err)

        return True, data_dict

    @staticmethod
    def calculate_peaks_position(phase, min_d, max_d):
        """
        Purpose: calculate the bragg peaks' position from lattice structure

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
        assert isinstance(phase, list), 'Input Phase must be a list but not %s.' % (
            str(type(phase)))
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
        for i_ref in range(num_ref):
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
        assert isinstance(bank_peak_dict, dict), 'Input must be a dict but not %s.' % str(
            type(bank_peak_dict))
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

    def gen_data_slicer_by_time(self, run_number, start_time, end_time, time_step, raw_nexus_name=None):
        """
        Generate data slicer by time
        if base file name is given, then run number will be ignored, even it is specified with an integer,
        which may not make any sense.
        :param run_number: run number (integer)
        :param start_time:
        :param end_time:
        :param time_step:
        :param raw_nexus_name: Base file name (str)
        :return:
        """
        # check input
        if raw_nexus_name is None:
            datatypeutility.check_int_variable('Run number', run_number, (1, None))

        # get chopper:
        if raw_nexus_name is not None:
            chopper = self._myProject.get_chopper(None, nxs_file_name=raw_nexus_name)
        else:
            chopper = self._myProject.get_chopper(run_number, nxs_file_name=None)

        # generate data slicer
        status, slicer_key = chopper.set_time_slicer(
            start_time=start_time, time_step=time_step, stop_time=end_time)

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

    def get_sliced_focused_workspaces(self, run_number, slice_id):
        """
        Find chopped data (in GSAS) in archive or user specified directories
        :param run_number:
        :param slice_id:
        :return: list of workspace names
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_string_variable('Slice ID', slice_id)

        return self._myProject.reduction_manager.get_sliced_focused_workspaces(run_number, slice_id)

    def get_reduced_data(self, run_id, target_unit, bank_id=None):
        """ Get reduced data from workspace
        Purpose: Get all data from a reduced run, either from run number or data key
        Requirements: run ID is either integer or data key.  target unit must be TOF, dSpacing or ...
        Guarantees: returned with 3 numpy arrays, x, y and e

        Removed arguments: ipts_number=None, search_archive=False, is_workspace=False

        :param run_id: A flexible input that can be (1) data key (str), (2) data key (tuple), (3) workspace name
        :param target_unit: TOF, dSpacing
        :param bank_id: Bank ID (from 1) or None (for all banks)
        :return: a dictionary of 3-array-tuples (x, y, e). KEY = bank ID
        """
        # TEST - Modified on 181217 - Not Tested
        # check whether run ID is a data key or a workspace name
        if isinstance(run_id, str) and mantid_helper.workspace_does_exist(run_id):
            workspace_name = run_id
        else:
            workspace_name = self._myProject.get_workspace_name_by_data_key(run_id)

        # get data
        status, ret_obj = self.get_data_from_workspace(workspace_name, bank_id=bank_id, target_unit=target_unit,
                                                       starting_bank_id=1)

        if not status:
            raise RuntimeError('Failed get_reduced_data(): {}'.format(ret_obj))

        data_set_dict, curr_unit = ret_obj

        return data_set_dict

    def get_reduced_run_info(self, run_number, data_key=None):
        """
        Purpose: get information of a reduced run such as bank ID and etc.
        Requirements: either run number is specified as a valid integer or data key is given;
        Guarantees: ... ...
        :param run_number: integer or string that can be converted to an integer
        :param data_key: string for workspace name
        :return: list of bank ID
        """
        if isinstance(run_number, int):
            # given run number
            try:
                info = self._myProject.get_reduced_run_information(run_number)
            except AssertionError as e:
                return False, str(e)

        elif run_number is None and isinstance(data_key, str):
            # given data key: mostly from loaded GSAS
            assert len(data_key) > 0, 'Data key cannot be an empty string.'
            try:
                # bank_list = self._myProject.data_loading_manager.get_bank_list(data_key)
                bank_list = self._myProject.get_data_bank_list(data_key)
                info = bank_list
            except AssertionError as assert_err:
                return False, str(assert_err)

        else:
            # unsupported case
            raise AssertionError('run number %s and data key %s is not supported.' %
                                 (str(run_number), str(data_key)))

        return True, info

    def get_reduced_workspace_name(self, run_id):
        """
        get reduced workspace name
        :param run_id:
        :return:
        """
        # check whether run ID is a data key or a workspace name
        if isinstance(run_id, str) and mantid_helper.workspace_does_exist(run_id):
            workspace_name = run_id
        else:
            workspace_name = self._myProject.get_workspace_name_by_data_key(run_id)

        return workspace_name

    def get_slicer(self, run_number, slicer_id):
        """
        Get the slicer (in vectors) by run number and slicer ID
        :param run_number:
        :param slicer_id: string or integer???
        :return:  2-tuple.  [1] Boolean [2] (vector time, vector workspace) | error message
        """
        assert slicer_id is not None, 'blabla'

        try:
            chopper = self._myProject.get_chopper(run_number)
            status, ret_obj = chopper.get_slicer_by_id(slicer_tag=slicer_id, relative_time=True)
        except RuntimeError as run_err:
            status = False
            ret_obj = 'Unable to get slicer dur to {}'.format(run_err)

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
            'IPTS number %s must either be None or an integer but not %s.' % (
                str(ipts_number), type(ipts_number))

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
    def get_data_from_workspace(workspace_name, bank_id=None, target_unit=None, starting_bank_id=1):
        """
        get data from a workspace
        Note: this method is to HIDE mantid from callers from INTERFACE
        :param workspace_name:
        :param bank_id:
        :param target_unit: None for using current unit
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
        return self._myProject.get_file_path(run_number)

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
            scanned_runs_information = self._myArchiveManager.get_experiment_run_info(
                archive_key=archive_key)
            self._myProject.add_scanned_information(scanned_runs_information)
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
        run_info_dict_list = self._myArchiveManager.get_experiment_run_info(
            archive_key, range(begin_run, end_run+1))
        self._myProject.add_scanned_information(run_info_dict_list)

        if len(run_info_dict_list) > 0:
            status = True
            ret_obj = run_info_dict_list
        else:
            status = False
            ret_obj = 'No run is selected from %d to %d' % (begin_run, end_run)

        return status, ret_obj

    def get_archived_data_dir(self, ipts_number, run_number, chopped_data):
        """
        get the directory of the SNS archived data (GSAS file) by ITPS number, Run number and whether it is the
        previously chopped and reduced data
        :param ipts_number:
        :param run_number:
        :param chopped_data:
        :return:
        """
        from pyvdrive.core import vdrive_constants
        if chopped_data:
            # chopped data
            sns_dir = self.archive_manager.get_vulcan_chopped_gsas_dir(ipts_number, run_number)
            vdrive_constants.run_ipts_dict[run_number] = ipts_number
        else:
            # regular GSAS file directory
            sns_dir = self.archive_manager.get_vulcan_gsas_dir(ipts_number)

        return sns_dir

    def get_focused_runs(self, chopped):
        """
        get the data keys of focused data that are loaded or reduced data in memory
        :param chopped: if flag is True, then get chopped (reduced data); otherwise, get the single run
        :return: (1) list of integers (for single runs); (2) list of integers (for chopped runs)
        """
        if chopped:
            # chopped runs
            # from archive
            loaded_runs_list = self._myProject.data_loading_manager.get_loaded_chopped_runs()
            print('[DB...BAT] API: Loaded chopped gsas: {}'.format(loaded_runs_list))

            # from memory
            if False:
                # FIXME TODO - TODAY 191 - only runs loaded from GSASs
                reduced_runs_list = self._myProject.reduction_manager.get_reduced_chopped_runs()
                print('[DB...BAT] API: In-Memory chopped runs: {}'.format(reduced_runs_list))

        else:
            # from archive
            loaded_runs_list = self._myProject.get_loaded_reduced_runs()

            # from project
            if False:
                # FIXME TODO - TODAY 191 - only runs loaded from GSASs
                reduced_runs_list = self._myProject.reduction_manager.get_reduced_single_runs()
                print('[DB...BAT] API: In-Memory reduced single-runs: {}'.format(reduced_runs_list))

        # END-IF-ELSE

        # combine
        run_in_mem = loaded_runs_list[:]
        # FIXME TODO - TODAY 191 - only runs loaded from GSASs
        # run_in_mem.extend(reduced_runs_list)

        return run_in_mem

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
        # FIXME TODO - 20180821
        raise NotImplementedError('Method need to be reviewed and refactored.')
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
        # check
        if run_number is None and data_key is None:
            raise RuntimeError('Either run number or data key must be given.')
        elif run_number is not None and data_key is not None:
            raise RuntimeError('Only one of run number and data key can be given.')
        elif run_number is not None:
            assert isinstance(run_number, int), 'run number {0} must be an integer but not {1}' \
                                                ''.format(run_number, type(run_number))
        else:
            assert isinstance(data_key, str), 'Data key {0} must be a string but not a {1}.' \
                                              ''.format(data_key, type(data_key))

        # get information
        if run_number is not None:
            # get information from _myProject's reduced data
            try:
                nexus_file_name = self._myProject.get_file_path(run_number)
                ipts_number = self._myProject.get_ipts_number(run_number)
                run_info_tuple = nexus_file_name, ipts_number
                #  run_info_tuple = self._myProject.get_run_info(run_number)
            except RuntimeError as re:
                return False, str(re)
        elif data_key is not None:
            # get detailed information from a loaded GSAS file
            try:
                bank_list = self._myProject.data_loading_manager.get_bank_list(data_key)
            except RuntimeError as run_err:
                return False, str(run_err)
            return True, bank_list
        else:
            raise NotImplementedError('Impossible')

        return True, run_info_tuple

    def get_number_runs(self):
        """
        Get the number of runs added to project.
        :return:
        """
        return self._myProject.get_number_data_files()

    def check_runs(self, ipts_number, run_list):
        """

        :param run_list:
        :return:
        """
        status, error_message, available_runs = self._myProject.check_runs(
            ipts_number, run_list, check_archive=True)

        return status, error_message, available_runs

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
            return False, 'Either start run {} or end run {} is not added to project. {}'.format(start_run, end_run, ie)

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

    def get_sample_log_names(self, run_number, smart=False, limited=True):
        """
        Get names of sample log with time series property
        :param run_number: run number (integer/string) or workspace name
        :param smart: a smart way to show sample log name with more information
        :param limited: Flag (boolean) to limit the log names to be those written to AutoRecord
        :return:
        """
        if run_number is None:
            raise RuntimeError('Run number cannot be None.')

        if isinstance(run_number, str) and mantid_helper.workspace_does_exist(run_number):
            # input (run number) is workspace's name
            ws_name = run_number
            sample_name_list = mantid_helper.get_sample_log_names(ws_name, smart=True)
        else:
            # a key or run
            chopper = self._myProject.get_chopper(run_number)
            sample_name_list = chopper.get_sample_log_names(smart)

        # check: remove
        if limited:
            return_list = list()
            # get the list of allowed name
            allowed_names = [log_tup[1] for log_tup in reduce_VULCAN.RecordBase]

            for sample_name in sample_name_list:
                name_i = sample_name.split()[0]   # sample name = [name] (# entries)
                if name_i in allowed_names:
                    return_list.append(sample_name)
            # END-FOR

            # check
            if len(return_list) == 0:
                raise RuntimeError('There is no sample log that is in pre-defined sample log list ({})'
                                   ''.format(allowed_names))

        else:
            return_list = sample_name_list

        return return_list

    def get_2_sample_log_values(self, data_key, log_name_x, log_name_y, start_time, stop_time):
        # get 2 sample logs and merge them along stamp time and return the sample log values

        # check input
        assert data_key is not None, 'Data key cannot be None.'
        print('Data Key / current run number = {}'.format(data_key))

        # 2 cases: run_number is workspace or run_number is run number
        if isinstance(data_key, str) and mantid_helper.workspace_does_exist(data_key):
            # input (run number) is workspace's name
            ws_name = data_key

            vec_times, vec_log_x, vec_log_y = mantid_helper.map_sample_logs(
                ws_name, log_name_x, log_name_y)

        else:
            # get chopper for (integer) run number
            chopper = self._myProject.get_chopper(data_key)

            vec_times, vec_log_x, vec_log_y = chopper.map_sample_logs(log_name_x=log_name_x, log_name_y=log_name_y,
                                                                      start_time=start_time, stop_time=stop_time)
            #
            # # get log values
            # vec_times, vec_value = chopper.get_sample_data(sample_log_name=log_name,
            #                                                start_time=start_time, stop_time=stop_time,
            #                                                relative=relative)
        # END-IF

        # TODO - TONIGHT 0 (ISSUE 164) -
        # TODO - Add a place to store vec_times, vec_log_x, vec_log_y (external method in chopper?)
        # TODO - UI - (1) add a section for line integral (2) option: section length, smooth, plot
        # TODO - Lib - (1) algorithm to smooth (X intact) (2) trace back from X/Y to time (using vec T, vecX, vecY)
        # TODO - UI - Table to show the result

        # vec_log_x, vec_log_y = vdrivehelper.merge_2_logs(vec_times_x, vec_value_x, vec_times, vec_value_y)

        return vec_times, vec_log_x, vec_log_y

    @staticmethod
    def create_curve_slicer_generator(vec_times, plot_x, plot_y):
        """ create an CurveSlicerGenerator instance
        :param vec_times
        :param plot_x:
        :param plot_y:
        :return:
        """
        return chop_utility.CurveSlicerGenerator(vec_times, plot_x, plot_y)

    def get_sample_log_values(self, data_key, log_name, start_time=None, stop_time=None, relative=True):
        """
        Get time and value of a sample log in vector
        Returned time is in unit of second as epoch time
        :param data_key: Run number or workspace name
        :param log_name:
        :param start_time:
        :param stop_time:
        :param relative: if True, then the sample log's vec_time will be relative to Run_start
        :return: 2-tuple as status (boolean) and 2-tuple of vectors.
        """
        # check input
        assert data_key is not None, 'Data key cannot be None.'

        # 2 cases: run_number is workspace or run_number is run number
        if isinstance(data_key, str) and mantid_helper.workspace_does_exist(data_key):
            # input (run number) is workspace's name
            ws_name = data_key
            vec_times, vec_value = mantid_helper.get_sample_log_value(ws_name, log_name, start_time=None,
                                                                      stop_time=None, relative=relative)
        else:
            # get chopper for (integer) run number
            chopper = self._myProject.get_chopper(data_key)

            # get log values
            vec_times, vec_value = chopper.get_sample_data(sample_log_name=log_name,
                                                           start_time=start_time, stop_time=stop_time,
                                                           relative=relative)
        # END-IF

        return vec_times, vec_value

    @staticmethod
    def is_workspace(workspace_name):
        """
        check whether a given string is a workspace's name in Mantid ADS
        :param workspace_name:
        :return:
        """
        return mantid_helper.workspace_does_exist(workspace_name)

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

    def has_native_sliced_reduced_workspaces(self, run_number):
        """check whether IN MEMORY, the specified run has been sliced and reduced
        :param run_number:
        :return:
        """
        return self._myProject.reduction_manager.has_run_reduced(run_number)

    def load_meta_data(self, ipts_number, run_number, file_name):
        """
        Load NeXus file to ADS
        IPTS/run number OR file name
        :param ipts_number:
        :param run_number:
        :param file_name: could be NONE
        :return: output worskpace name
        """
        # get NeXus file name
        if file_name is None:
            # nexus file name is not given, then use the standard SNS archive name
            if ipts_number is None:
                # get IPTS number if it is not given
                ipts_number = self._myProject.get_ipts_number(run_number)
            # END-IF

            file_name = self._myArchiveManager.locate_event_nexus(
                ipts_number, run_number=run_number)
            if file_name is None:
                raise RuntimeError('Unable to find or access NeXus file of IPTS-{} Run-{}'
                                   ''.format(ipts_number, run_number))
        # END-IF

        # add to project
        self._myProject.add_run(run_number, file_name, ipts_number)

        # load file
        output_ws_name = self._myProject.load_meta_data(ipts_number=ipts_number, run_number=run_number,
                                                        nxs_file_name=file_name)

        return output_ws_name

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
        if len(in_file_name) == 0:
            raise RuntimeError('Input session file name cannot be an empty string.')

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

    def normalize_by_proton_charge(self, ws_name, ipts_number, run_number, chop_sequence=None):
        """normalize by proton charges
        :param ws_name:
        :param ipts_number:
        :param run_number:
        :param chop_sequence:
        :return:
        """
        # get information
        proton_charge = self._myArchiveManager.get_proton_charge(
            ipts_number, run_number, chop_sequence)

        workspace = mantid_helper.retrieve_workspace(ws_name, True)
        print('[DB...BAT...TRACE] PC = {0}, Acting on workspace {1}'.format(proton_charge, workspace))

        workspace *= (1./proton_charge)

        return

    @staticmethod
    def normalise_by_vanadium(data_ws_name, van_ws_name):
        """
        normalize by vanadium
        :param data_ws_name:
        :param van_ws_name:
        :return:
        """
        try:
            mantid_helper.normalize_by_vanadium(data_ws_name, van_ws_name)
        except RuntimeError as run_err:
            return False, 'Unable to normalize by vanadium due to {0}'.format(run_err)

        return True, None

    def reduce_chopped_data_set(self, ipts_number, run_number, chop_child_list, raw_data_directory,
                                output_directory, vanadium,
                                binning_parameters, use_idl_bin,
                                merge_banks, gsas=True, num_banks=3):
        """ reduce a set of chopped data
        :param ipts_number:
        :param run_number:
        :param raw_data_directory:
        :param output_directory:
        :param vanadium:
        :param binning_parameters:
        :param use_idl_bin: flag to use IDL-VDRIVE binning from a pre-defined data file with calibration files
                            It will override binning parameters
        :param align_to_vdrive_bin:
        :param merge_banks:
        :param gsas:
        :param num_banks: number of banks focused to.  Now only 3, 7 and 27 are allowed.
        :return:
        """
        # get list of files
        if raw_data_directory is None:
            # raw data is not given, then search the data in archive
            try:
                raw_file_list = self._myArchiveManager.locate_chopped_nexus(
                    ipts_number, run_number, chop_child_list)
            except AssertionError as assert_err:
                raise AssertionError(
                    'Error in calling ArchiveManager.get_data_chopped_nexus(): {0}'.format(assert_err))
            except RuntimeError as run_err:
                return False, 'Failed to locate chopped NeXus files. FYI: {0}.'.format(run_err)
        else:
            # scan the directory for file
            try:
                raw_file_list = [f for f in os.listdir(raw_data_directory) if f.endswith('.nxs') and
                                 os.path.isfile(os.path.join(raw_data_directory, f))]

                # raw_file_list = chop_utility.scan_chopped_nexus(raw_data_directory)
            except AssertionError as assert_err:
                raise AssertionError('Error in scanning files in {0}: {1}'.format(
                    raw_data_directory, assert_err))
        # END-IF-ELSE

        if len(raw_file_list) == 0:
            # return False if there is not file found
            return False, 'Unable to find chopped files for IPTS-{0} Run {1} directory {2}' \
                          ''.format(ipts_number, run_number, raw_data_directory)
        # END-IF

        # reduce
        sum_status = True
        sum_message = ''

        vanadium_tuple = False
        standard_sample_tuple = False
        for nexus_file_name in raw_file_list:
            status, sub_message = \
                self._myProject.reduction_manager.reduce_event_nexus_ver1(ipts_number=None, run_number=None,
                                                                          event_file=nexus_file_name,
                                                                          output_directory=output_directory,
                                                                          merge_banks=merge_banks,
                                                                          vanadium=vanadium,
                                                                          vanadium_tuple=vanadium_tuple,
                                                                          gsas=gsas,
                                                                          standard_sample_tuple=standard_sample_tuple,
                                                                          binning_parameters=binning_parameters,
                                                                          use_idl_bin=use_idl_bin,
                                                                          num_banks=num_banks)
            if not status:
                sum_status = False
                sum_message += '{0}\n'.format(sum_message)
        # END-FOR

        return sum_status, sum_message

    def reduce_data_set(self, auto_reduce, output_directory, merge_banks,
                        background=False, vanadium=None,
                        record=False, logs=False, gsas=True, output_to_fullprof=False,
                        standard_sample_tuple=None, binning_parameters=None,
                        merge_runs=False, merged_run=None,  dspace=False, num_banks=3, roi_list=None,
                        mask_list=None, no_cal_mask=False,
                        version=2):
        """ Reduce a set of VULCAN runs
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
        :param merge_banks:
        :param background:  boolean flag to subtract background
        :param vanadium: integer as vanadium run numbers or None for not normalized
        :param record: boolean flag to output AutoRecord and etc.
        :param logs: boolean flag to output sample log files (MTS)
        :param gsas: boolean flag to produce GSAS files from reduced runs
        :param output_to_fullprof:  boolean flag tro produces Fullprof files from reduced runs
        :param standard_sample_tuple: If specified, then it should process the VULCAN standard sample as #57.
        :param binning_parameters: binning parameter. [1] None for default; [2] a size 1 container as bin size
                                           [3] a size-3 container as [TOF_min, Bin Size, TOF_max]
        :param merge_runs: If true, then merge the run together by calling SNSPowderReduction
        :param merged_run: Paired with flag merge_runs.  It is the run number to be merged to
        :param dspace: If true, then data will reduced to workspace in dSpacing and exported with unit dSpacing
        :param num_banks: number of banks focused to.  Now only 3, 7 and 27 are allowed; Also a special grouping file
        :param roi_list:
        :param mask_list:
        :param no_cal_mask:
        :param version: reduction algorithm version in integer
        :return: 2-tuple (boolean, object)
        """
        # Check requirements
        runs_to_reduce = self._myProject.get_runs_to_reduce()
        num_runs_flagged = len(runs_to_reduce)
        if num_runs_flagged == 0:
            raise RuntimeError('At least one run should be flagged for reduction.')

        # check whether all the runs to reduce are belonged to the same IPTS number
        ipts_set = set()
        for run_number in runs_to_reduce:
            try:
                tmp_ipts_number = self._myArchiveManager.get_ipts_number(run_number)
                ipts_set.add(tmp_ipts_number)
            except KeyError:
                return False, 'Run {0} has not been searched and thus found in archive.'.format(run_number)
        # END-FOR
        if len(ipts_set) != 1:
            raise RuntimeError(
                'There are runs from different IPTS.  It is not supported in PyVDrive.')
        ipts_number = ipts_set.pop()

        # check ROI list and Mask list: force ROI/MASK file list to be 'list()'
        if roi_list is None:
            roi_list = list()
        else:
            datatypeutility.check_list('ROI list', roi_list)
        if mask_list is None:
            mask_list = list()
        else:
            datatypeutility.check_list('Mask list', mask_list)

        # Reduce data set
        if auto_reduce:
            # auto reduction: auto reduction script does not work with vanadium normalization
            # print '[INFO] (Auto) reduce data: IPTS = {0}, Runs = {1}.'.format(ipts_number, runs_to_reduce)
            status, error_message = self.reduce_auto_script(ipts_number=ipts_number,
                                                            run_numbers=runs_to_reduce,
                                                            output_dir=output_directory,
                                                            is_dry_run=False,
                                                            roi_list=roi_list,
                                                            mask_list=mask_list)
            error_message = error_message

        elif dspace or version == 2:
            # user version 2 reduction algorithm
            if merge_runs and merged_run is not None:
                if merged_run not in runs_to_reduce:
                    raise RuntimeError('Run number {} to merge to is not the list of run numbers to reduce {}'
                                       ''.format(merged_run, runs_to_reduce))
                else:
                    # put the run number to merge to at the first element in the list
                    run_index = runs_to_reduce.index(merged_run)
                    runs_to_reduce.pop(run_index)
                    runs_to_reduce.insert(0, merged_run)

            run_number_list, msg_list = self._myProject.reduce_vulcan_runs_v2(run_number_list=runs_to_reduce,
                                                                              output_directory=output_directory,
                                                                              d_spacing=True,
                                                                              binning_parameters=binning_parameters,
                                                                              number_banks=num_banks,
                                                                              gsas=gsas,
                                                                              vanadium_run=vanadium,
                                                                              merge_runs=merge_runs,
                                                                              roi_list=roi_list,
                                                                              mask_list=mask_list,
                                                                              no_cal_mask=no_cal_mask)

            # post process:

            if len(run_number_list) == 0:
                # no runs reduced successfully
                status = False

            elif standard_sample_tuple:
                # deal with sample logs
                if len(run_number_list) != 1:
                    return False, 'Standard tag {} can only work with 1 run'.format(standard_sample_tuple)

                # get information of run number and workspace
                run_number, ws_name = run_number_list[0]
                status, error_message = vdrivehelper.export_standard_sample_log(ipts_number, run_number, ws_name,
                                                                                standard_sample_tuple)

            elif merge_runs:
                # merge runs
                record_file_name = os.path.join(output_directory, 'AutoRecord.txt')
                run_number, ws_name = run_number_list[0]
                status, error_message = vdrivehelper.export_normal_sample_log(ipts_number, run_number, ws_name,
                                                                              record_file_name)
            else:
                status = True
            # END-IF

            # deal with error message
            error_message = ''
            for msg in msg_list:
                if msg.count('Failed'):
                    status = False
                error_message += msg + '\n'

        else:
            # Not auto reduction and Not reduction with version=2
            # TODO - TONIGHT 0 - Better error message
            raise RuntimeError('blabla')
        # END-IF-ELSE

        # mark the runs be reduced so that they will not be reduced again next time.
        reduction_state_list = None
        self._myProject.mark_runs_reduced(runs_to_reduce, reduction_state_list)

        print('[DB......BAT.......BAT] status = {}, error: "{}"'.format(status, error_message))

        return status, error_message

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
        assert isinstance(
            run_numbers, list), 'Run numbers must be a list but not %s.' % type(run_numbers)
        assert isinstance(
            output_dir, str) or output_dir is None, 'Output directory must be a string or None (auto).'
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
            nxs_file_name = '/SNS/VULCAN/IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs' % (
                ipts_number, run_number, run_number)
            raise NotImplementedError('ASAP {0} is old file path.'.format(nxs_file_name))
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
                part_status, part_message = reducer.execute_vulcan_reduction(output_logs=True)

            # contribute the overall message
            status = status and part_status
            message += part_message + '\n'
        # END-FOR (run number)

        return status, message

    @staticmethod
    def save_time_slicers(splitters_list, file_name):
        """ save a set of time splitters to a file
        :param splitters_list:
        :param file_name:
        :return:
        """
        status, error_message = chop_utility.save_slicers(splitters_list, file_name)

        return status, error_message

    def scan_ipts_runs(self, ipts_number, start_run, stop_run):
        """

        :param ipts_number:
        :param start_run:
        :param stop_run:
        :return:
        """
        run_info_dict_list = list()
        for run_number in range(start_run, stop_run+1):
            event_file_name = self._myArchiveManager.locate_event_nexus(ipts_number, run_number)
            if event_file_name is None:
                continue
            else:
                run_info = dict()
                run_info['run'] = run_number
                run_info['ipts'] = ipts_number
                run_info['file'] = event_file_name
                run_info_dict_list.append(run_info)
        # END-FOR

        return run_info_dict_list

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
            error_message = 'Unable to set runs %s to reduce due to %s.' % (
                str(run_numbers), str(re))

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
                                                  '%s.' % (log_file_name, str(
                                                      self._mtsLogDict.keys()))
        assert isinstance(header_list, list), 'Header list must a list'
        for name in header_list:
            assert name in self._mtsLogDict[log_file_name], 'Header %s is not in Pandas series, which ' \
                                                            'current has headers as %s.' % \
                                                            (name,
                                                             self._mtsLogDict[log_file_name].keys())

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

    # TODO - NOW - - New feature on binning_parameters
    def load_vanadium_run(self, ipts_number, run_number, use_reduced_file, unit='dSpacing',
                          binning_parameters=None, smoothed=False):
        """
        Load vanadium runs
        :param ipts_number:
        :param run_number:
        :param use_reduced_file:
        :param unit:
        :return: 2-tuple.  boolean/string
        """
        van_file_name = None

        # highest priority: load data from
        if use_reduced_file:
            # search reduced GSAS file
            try:
                if smoothed:
                    van_file_name = self._myArchiveManager.get_smoothed_vanadium(ipts_number, run_number,
                                                                                 check_exist=True)
                else:
                    van_file_name = self._myArchiveManager.get_gsas_file(
                        ipts_number, run_number, check_exist=True)
            except RuntimeError as run_err:
                print('[WARNING]: {0}'.format(run_err))
                van_file_name = None
        # END-IF

        if van_file_name is None:
            # if vanadium gsas file is not found, reduce it
            nxs_file = self._myArchiveManager.locate_event_nexus(ipts_number, run_number)
            if nxs_file is None:
                return False, 'Vanadium file of IPTS {} Run {} does not exist.'.format(ipts_number, run_number)
            self._myProject.add_run(run_number, nxs_file, ipts_number)
            reduced, message = self._myProject.reduce_runs(run_number_list=[run_number],
                                                           output_directory=self._myWorkDir,
                                                           background=False,
                                                           vanadium=None,
                                                           gsas=True,
                                                           fullprof=False,
                                                           sample_log_file=None,
                                                           standard_sample_tuple=None,
                                                           merge_banks=False,
                                                           merge_runs=False,
                                                           binning_parameters=binning_parameters)

            if reduced:
                van_ws_key = ipts_number, run_number
            else:
                return False, 'Unable to reduce vanadium run {0} (IPTS-{1}) due to {2}.' \
                              ''.format(run_number, ipts_number, message)
            # END-IF
        else:
            # load vanadium file
            van_ws_key = self._myProject.data_loading_manager.load_binned_data(van_file_name, 'gsas',
                                                                               None, 1000)
            self._myProject.add_reduced_workspace(ipts_number, run_number, van_ws_key)
        # END-IF-ELSE

        # convert unit
        print('[DB...BAT] Load vanadium and convert unit???  from {0}'.format(van_file_name))
        mantid_helper.mtd_convert_units(van_ws_key, unit)

        return True, van_ws_key

    def read_mts_log(self, log_file_name, format_dict, block_index, start_point_index, end_point_index):
        """
        Read (partially) MTS file
        :return:
        """
        import pandas as pd
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

        # load file
        # TODO/FIXME - sep is fixed to \t now.  It might not be a good approach
        mts_series = pd.read_csv(log_file_name, skiprows=data_line_number,
                                 names=header, nrows=num_points,
                                 sep='\t')

        self._mtsLogDict[log_file_name] = mts_series
        self._currentMTSLogFileName = log_file_name

        return mts_series

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
        # TODO/NOW - More parameters to be saved for GUI ... Waiting for further notice
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
            print('[INFO] Session file is saved to working directory as %s.' % out_file_name)

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
        datatypeutility.check_int_variable('Run number', run_number, (1, 99999999))
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

    def set_ipts_config(self, ipts_number, data_dir, binned_data_dir):
        """
        Set configuration for a particular IPTS
        :param ipts_number:
        :param data_dir:
        :param binned_data_dir:
        :return:
        """
        # check
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 9999999))
        assert isinstance(data_dir, str) and os.path.exists(data_dir), \
            'Data directory %s of type (%s) must be a string and exists.' % (
                str(data_dir), type(data_dir))
        assert isinstance(binned_data_dir, str) and os.path.exists(binned_data_dir), \
            'Binned data directory %s of type (%s) must be a string and exists.' % (str(binned_data_dir),
                                                                                    type(binned_data_dir))

        # set up the configuration as a 2-item list
        self._iptsConfigDict[ipts_number] = [data_dir, binned_data_dir]

        return

    def set_vanadium_to_runs(self, ipts_number, run_number_list, van_run_number):
        """
        set corresponding vanadium run to a specific list of sample run numbers
        :param ipts_number:
        :param run_number_list:
        :param van_run_number:
        :return:
        """
        # check inputs
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))
        datatypeutility.check_list('Run numbers', run_number_list)
        datatypeutility.check_int_variable('Vanadium run number', van_run_number, (1, None))

        # locate vanadium GSAS file
        file_exist, van_file_name = self._myArchiveManager.locate_vanadium_gsas_file(
            ipts_number, van_run_number)
        if not file_exist:
            return False, 'Unable to locate vanadium GSAS file'

        self._myProject.reduction_manager.add_reduced_vanadium(van_run_number, van_file_name)
        self._myProject.set_vanadium_runs(run_number_list, van_run_number, van_file_name)

        return True, None

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

    # Migrate the call to vanadium_processing_manager.smooth_diffraction_data directly
    # def smooth_diffraction_data(self, workspace_name, bank_id=None,
    #                             smoother_type='Butterworth', param_n=20, param_order=2,
    #                             start_bank_id=1):
    #     """
    #     smooth spectra of focused diffraction data
    #     :param workspace_name:
    #     :param bank_id:
    #     :param smoother_type:
    #     :param param_n:
    #     :param param_order:
    #     :param start_bank_id:
    #     :return:
    #     """
    #     try:
    #         if bank_id is None:
    #             # smooth all spectra
    #             workspace_index = None
    #         else:
    #             # smooth one spectrum
    #             assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not {1}.' \
    #                                              ''.format(bank_id, type(bank_id))
    #             assert isinstance(start_bank_id, int), 'Starting bank ID {0} must be an integer but not a {1}.' \
    #                                                    ''.format(start_bank_id, type(start_bank_id))
    #
    #             workspace_index = bank_id - start_bank_id
    #         # END-IF
    #
    #         smoothed_ws_name = self._myProject.vanadium_processing_manager.smooth_spectra(
    #             bank_id_list=None, smoother_type=smoother_type, param_n=param_n, param_order=param_order)
    #
    #     except RuntimeError as run_err:
    #         return False, 'Unable to smooth workspace {0} due to {1}.'.format(workspace_name, run_err)
    #
    #     return True, smoothed_ws_name

    # Migrate the call to vanadium_processing_manager.strip_peaks directly
    # def strip_vanadium_peaks(self, ipts_number, run_number, bank_list, peak_fwhm,
    #                          peak_pos_tolerance, background_type, is_high_background,
    #                          workspace_name):
    #     """
    #     strip vanadium peaks.
    #     This method supports 2 type of inputs
    #      (1) IPTS and run number;
    #      (2) workspace name
    #     :param ipts_number:
    #     :param run_number:
    #     :param bank_list:
    #     :param peak_fwhm:
    #     :param peak_pos_tolerance:
    #     :param background_type:
    #     :param is_high_background:
    #     :param workspace_name:
    #     :return:  (boolean, string): True (successful), output workspace name; False (failed), error message
    #     """
    #     # get workspace name
    #     # check whether run ID is a data key or a workspace name
    #     if isinstance(workspace_name, str) and mantid_helper.workspace_does_exist(workspace_name):
    #         # workspace name is workspace name
    #         pass
    #     elif isinstance(workspace_name, str):
    #         # workspace name is run id
    #         run_id = workspace_name
    #         workspace_name = self._myProject.get_workspace_name_by_data_key(run_id)
    #         print ('[DB...BAT] Strip vanadium peak: retrieve workspace {} from run ID {}'
    #                ''.format(workspace_name, run_id))
    #     else:
    #         assert workspace_name is None, 'workspace name {} (of type {}) must be None' \
    #                                        ''.format(workspace_name, type(workspace_name))
    #         # get workspace (key) from IPTS number and run number
    #         datatypeutility.check_int_variable('IPTS number', ipts_number, (None, None))
    #         datatypeutility.check_int_variable('Run number', run_number, (None, None))
    #         # assert isinstance(ipts_number, int), 'Without data key specified, IPTS number must be an integer.'
    #         # assert isinstance(run_number, int), 'Without data key specified, run number must be an integer.'
    #         if self._myProject.has_reduced_workspace(ipts_number, run_number):
    #             workspace_name = self._myProject.get_reduced_workspace(ipts_number, run_number)
    #         else:
    #             error_message = 'Unable to find reduced workspace for IPTS {0} Run {1} without data key.' \
    #                             ''.format(ipts_number, run_number)
    #             return False, error_message
    #     # END-IF
    #
    #     # call for strip vanadium peaks
    #     try:
    #         out_ws_name = self._myProject.vanadium_processing_manager.strip_peaks(peak_fwhm, peak_pos_tolerance,
    #                                                                               background_type, is_high_background,
    #                                                                               workspace_name=workspace_name,
    #                                                                               bank_list=bank_list)
    #     except RuntimeError as run_err:
    #         return False, 'Unable to strip vanadium due to {0}'.format(run_err)
    #
    #     return True, out_ws_name

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
