################################################################################
# Manage the reduced VULCAN runs
################################################################################
import os
import datetime
from pyvdrive.core import reduce_VULCAN
from pyvdrive.core import mantid_helper
from pyvdrive.core import reduce_adv_chop
from pyvdrive.core import mantid_reduction
from pyvdrive.core import datatypeutility
from pyvdrive.core import save_vulcan_gsas
from pyvdrive.core import vulcan_util
import mantid.simpleapi as mantid_api

EVENT_WORKSPACE_ID = "EventWorkspace"


class CalibrationManager(object):
    """
    A container and manager for calibration files loaded, number of banks of groupings and etc
    """

    def __init__(self):
        """
        initialization
        """
        # important dates
        self._ned_date = '2017-06-01'  # string only

        self._calibration_dict = None  # [starting date] = {bank number: file name}

        # binning
        self._vdrive_bin_ref_file_dict = dict()  # [date (standard)][num banks] = file name
        self._vdrive_binning_ref_dict = dict()   # [date, num_banks] ...
        self._default_tof_bins_dict = None   # [cal_date, num_banks]

        self._loaded_calibration_file_dict = dict()
        self._focus_instrument_dict = dict()

        # set up
        self._init_vulcan_calibration_files()
        # self._init_vdrive_binning_refs()
        self._init_focused_instruments()
        self._init_default_tof_bins()

        return

    def _init_default_tof_bins(self):
        """ initialize default TOF bins
        :return:
        """
        self._default_tof_bins_dict = dict()

        self.get_default_binning_reference(self._ned_date, 3)

        return

    def _init_focused_instruments(self):
        """
        set up the dictionary for the instrument geometry after focusing
        each detector (virtual) will have 3 value as L2, polar (2theta) and azimuthal (phi)
        and the angles are in unit as degree
        :return:
        """
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
        self._focus_instrument_dict['Polar'][3] = [-90, 90., mantid_helper.HIGH_ANGLE_BANK_2THETA]
        self._focus_instrument_dict['Azimuthal'][3] = [0., 0, 0.]
        self._focus_instrument_dict['SpectrumIDs'][3] = [1, 2, 3]

        # 7 bank
        # all the sub-banks in each bank will be focused to the center of east bank;
        # all the sub-banks belonged to west bank will be focused to the center of west bank;
        # unless the users have specific requirement.
        self._focus_instrument_dict['L2'][7] = [2.] * 7  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][7] = [-90.] * 3
        self._focus_instrument_dict['Polar'][7].extend([90.] * 3)
        self._focus_instrument_dict['Polar'][7].extend([mantid_helper.HIGH_ANGLE_BANK_2THETA])
        self._focus_instrument_dict['Azimuthal'][7] = [0.] * 7
        self._focus_instrument_dict['SpectrumIDs'][7] = range(1, 8)

        # 27 banks: Note that
        # all the sub-banks in each bank will be focused to the center of east bank;
        # all the sub-banks belonged to west bank will be focused to the center of west bank;
        # and all the sub-banks of high angle bank will be focused to the center of high angle bank
        # unless the users have specific requirement.
        self._focus_instrument_dict['L2'][27] = [2.] * 27  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][27] = [None] * 27
        self._focus_instrument_dict['Azimuthal'][27] = [0.] * 27
        self._focus_instrument_dict['SpectrumIDs'][27] = range(1, 28)
        for ws_index in range(9):
            self._focus_instrument_dict['Polar'][27][ws_index] = -90.
            self._focus_instrument_dict['Polar'][27][ws_index + 9] = 90.
            self._focus_instrument_dict['Polar'][27][ws_index +
                                                     18] = mantid_helper.HIGH_ANGLE_BANK_2THETA

        return

    def _init_vulcan_calibration_files(self):
        """
        generate a dictionary for vulcan's hard coded calibration files
        :return:
        """
        base_calib_dir = '/SNS/VULCAN/shared/CALIBRATION'

        # hard coded list of available calibration file names
        pre_ned_setup = {
            3: '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'}

        ned_2017_setup = {3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                          7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_7bank.h5',
                          27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_27bank.h5'}

        ned_2018_setup = {3: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5'),
                          7: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_7bank.h5'),
                          27: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_27bank.h5')}

        ned_2019_setup = {3: os.path.join(base_calib_dir, '2019_1_20/VULCAN_calibrate_2019_01_21.h5'),
                          7: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_7bank.h5'),
                          27: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_27bank.h5')}

        ned_2019B_setup = {3: os.path.join(base_calib_dir, '2019_6_27/VULCAN_calibrate_2019_06_27.h5'),
                           7: os.path.join(base_calib_dir, '2019_6_27/VULCAN_calibrate_2019_06_27_07banks.h5'),
                           27: os.path.join(base_calib_dir, '2019_6_27/VULCAN_calibrate_2019_06_27_27banks.h5')}

        self._calibration_dict = dict()
        self._calibration_dict[datetime.datetime(2010, 1, 1)] = pre_ned_setup
        self._calibration_dict[datetime.datetime(2017, 6, 1)] = ned_2017_setup
        self._calibration_dict[datetime.datetime(2018, 5, 30)] = ned_2018_setup
        self._calibration_dict[datetime.datetime(2019, 1, 1)] = ned_2019_setup
        self._calibration_dict[datetime.datetime(2019, 6, 1)] = ned_2019B_setup

        return

    @property
    def calibration_dates(self):
        """
        get sorted dates for all the calibration files
        :return: a list of string. date in format YYY-MM-DD
        """
        return sorted(self._calibration_dict.keys())

    def load_idl_vulcan_bins(self, cal_index_date, num_banks):
        """ Load the corresponding .h5 reference binning file to _vdrive_binning_ref_dict
        :param cal_index_date: index (date) of the calibration file
        :param num_banks: number of banks
        :return:
        """
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 1000))
        try:
            ref_template_name = self._vdrive_bin_ref_file_dict[cal_index_date][num_banks]
        except KeyError as run_err:
            raise RuntimeError('Calibration date {} bank number {} does not exist for VDRIVE GSAS reference '
                               'binnign file.  FYI {}\nAvailable are {}'
                               ''.format(cal_index_date, num_banks, run_err, self._vdrive_bin_ref_file_dict))

        if cal_index_date not in self._vdrive_binning_ref_dict:
            self._vdrive_binning_ref_dict[cal_index_date] = dict()

        self._vdrive_binning_ref_dict[cal_index_date][num_banks] = \
            mantid_reduction.VulcanBinningHelper.create_idl_bins(num_banks, ref_template_name)

        return

    @staticmethod
    def get_base_name(file_name, num_banks):
        """ get the base name for the calbration workspace, grouping workspace and mask workspace
        :param file_name:
        :param num_banks:
        :return:
        """
        datatypeutility.check_string_variable('Calibration file name', file_name)

        base_name = os.path.basename(file_name).split('.')[0] + '{0}banks'.format(num_banks)

        return base_name

    def get_calibration_index(self, vulcan_run_date):
        """
        Get the calibration index defined in CalibrationManager for computational efficiency
        :param vulcan_run_date: an experimental run's run start time/date
        :return: Date index of the calibration suite.  String as YYYY-MM-DD
        """
        # check input
        datatypeutility.check_date_time('VULCAN run start time\'s date', vulcan_run_date)

        # search the list
        date_list = sorted(self._calibration_dict.keys())
        if vulcan_run_date < date_list[0]:
            raise RuntimeError('Input VULCAN run date {0} is too early comparing to {1}'
                               ''.format(vulcan_run_date, date_list[0]))

        # do a brute force search (as there are only very few of them) against starting date of calibration
        cal_date_index = None
        for i_date in range(len(date_list)-1, -1, -1):
            if vulcan_run_date > date_list[i_date]:
                cal_date_index = date_list[i_date]
                break
            # END-IF
        # END-FOR

        return cal_date_index

    def get_calibration_file(self, run_start_date, num_banks):
        """
        get the calibration file by date and number of banks
        :param run_start_date: Time stamp of type datetime.datetime
        :param num_banks:
        :return: calibration file date, calibration file name
        """
        # check inputs
        datatypeutility.check_date_time('Run start date', run_start_date)
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 28))

        # search the list
        date_list = sorted(self._calibration_dict.keys())
        if run_start_date < date_list[0]:
            raise RuntimeError('Input year-month-date {0} is too early comparing to {1}'
                               ''.format(run_start_date, date_list[0]))

        # print ('[DB...BAT] File YYYY-MM-DD: {}'.format(run_start_date))
        # do a brute force search (as there are only very few of them)
        cal_date_index = None
        for i_date in range(len(date_list)-1, -1, -1):
            print('[DB...BAT] Calibration Date: {}'.format(date_list[i_date]))
            if run_start_date > date_list[i_date]:
                cal_date_index = date_list[i_date]
                break
            # END-IF
        # END-FOR

        try:
            calibration_file_name = self._calibration_dict[cal_date_index][num_banks]
        except KeyError as key_err:
            print('[DB...BAT] calibration dict: {}.  {} with calibration date index = {}.  number banks = {}'
                  ''.format(self._calibration_dict.keys(), run_start_date, cal_date_index, num_banks))
            raise key_err

        return cal_date_index, calibration_file_name

    def get_default_binning_reference(self, run_date, num_banks):
        """ get default binning reference parameters
        :param run_date:
        :param num_banks:
        :return:
        """
        datatypeutility.check_string_variable('Run date', run_date)
        if run_date.count('-') != 2:
            raise RuntimeError('{} is not a standard YYYY-MM-DD format'.format(run_date))

        if run_date >= self._ned_date:
            calib_date = self._ned_date
        else:
            calib_date = '1990-01-01'

        if (calib_date, num_banks) in self._default_tof_bins_dict:
            return self._default_tof_bins_dict[calib_date, num_banks]

        # hard coded default binning parameters
        ew_bin_params = '5000.,-0.001,70000.'
        if run_date >= self._ned_date:
            high_angle_params = '5000.,-0.0003,70000.'
        else:
            high_angle_params = None

        # create binning
        self._default_tof_bins_dict[calib_date, num_banks] = \
            mantid_reduction.VulcanBinningHelper.create_nature_bins(num_banks=num_banks,
                                                                    east_west_binning_parameters=ew_bin_params,
                                                                    high_angle_binning_parameters=high_angle_params)

        print('[DB...BAT] Binning: {}'.format(self._default_tof_bins_dict[calib_date, num_banks]))

        return self._default_tof_bins_dict[calib_date, num_banks]

    def get_focused_instrument_parameters(self, num_banks):
        """ Get a dictionary for the focused instrument parameters including virtual detectors' positions
        :param num_banks:
        :return: a dictionary for EditInstrumentGeometry
        """
        # check input
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 28))

        edit_instrument_param_dict = dict()

        try:
            edit_instrument_param_dict['L1'] = self._focus_instrument_dict['L1']
            edit_instrument_param_dict['L2'] = self._focus_instrument_dict['L2'][num_banks]
            edit_instrument_param_dict['Polar'] = self._focus_instrument_dict['Polar'][num_banks]
            edit_instrument_param_dict['Azimuthal'] = self._focus_instrument_dict['Azimuthal'][num_banks]
            edit_instrument_param_dict['SpectrumIDs'] = self._focus_instrument_dict['SpectrumIDs'][num_banks]
        except KeyError as key_err:
            err_msg = 'Unable to retrieve virtual instrument geometry for {}-bank case. FYI: {}' \
                      ''.format(num_banks, key_err)
            print('[ERROR CAUSING CRASH] {}'.format(err_msg))
            raise RuntimeError(err_msg)

        return edit_instrument_param_dict

    def get_loaded_calibration_workspaces(self, run_start_date, num_banks):
        """
        get the loaded workspaces
        :param run_start_date:
        :param num_banks:
        :return:
        """
        cal_date, cal_file_name = self.get_calibration_file(run_start_date, num_banks)

        try:
            calib_ws_collection = self._loaded_calibration_file_dict[cal_date][num_banks]
        except KeyError as key_err:
            error_msg = 'File {0} is not loaded yet! Client shall check the loaded workspace first.' \
                        'FYI: {1}'.format(cal_file_name, key_err)
            print('[Crash Error] {}'.format(error_msg))
            raise RuntimeError(error_msg)

        return calib_ws_collection

    def get_last_gsas_bin_ref(self):
        return self._last_ref_dict

    def get_vulcan_idl_bins(self, cal_index_date, num_banks):
        """ Get the reference binning (dictionary of vectors) for VDRIVE GSAS file
        :param cal_index_date:
        :param num_banks:
        :return:
        """
        # return self._vdrive_binning_ref_dict[cal_index_date][num_banks]
        # check inputs
        datatypeutility.check_string_variable('Start date index', cal_index_date)
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 1000))

        try:
            ref_dict = self._vdrive_binning_ref_dict[cal_index_date][num_banks]
        except KeyError as key_err:
            raise RuntimeError('VDRIVE GSAS binning reference binning dictionary {} has not key [{}][{}]. FYI {}'
                               ''.format(self._vdrive_binning_ref_dict, cal_index_date, num_banks, key_err))

        self._last_ref_dict = ref_dict

        return ref_dict

    def has_loaded(self, run_start_date, num_banks, search_unregistered_workspaces=False):
        """ check whether a run's corresponding calibration file has been loaded
        If check_workspace is True, then check the real workspaces if they are not in the dictionary;
        If the workspaces are there, then add the calibration files to the dictionary
        :param run_start_date: run start date to search calibration file
        :param num_banks:
        :param search_unregistered_workspaces: if True, then check the workspace names instead of dictionary.
        :return: 2-tuple (bool: has loaded to workspace?, calibration workspace collection instance)
        """
        # get calibration date and file name
        calib_file_date, calib_file_name = self.get_calibration_file(run_start_date, num_banks)
        print('[DB...BAT] CalibrationMananger: ID/Date: {}; Calibration file name: {}'
              ''.format(calib_file_date, calib_file_name))

        # regular check with dictionary
        has_them = True
        if calib_file_date not in self._loaded_calibration_file_dict:
            has_them = False
        elif num_banks not in self._loaded_calibration_file_dict[calib_file_date]:
            has_them = False

        # search for unregistered
        if has_them:
            calib_ws_collection = self._loaded_calibration_file_dict[calib_file_date][num_banks]

        elif search_unregistered_workspaces:
            # search un-registered calibration workspace by workspace names
            base_ws_name = self.get_base_name(calib_file_name, num_banks)
            has_all = True
            has_some = False
            for sub_ws_name in ['calib', 'mask', 'grouping']:
                ws_name_i = '{}_{}'.format(base_ws_name, sub_ws_name)
                if mantid_helper.workspace_does_exist(ws_name_i) is False:
                    has_all = False
                else:
                    has_some = True
            # END-FOR

            if has_all != has_some:
                raise RuntimeError(
                    'Problematic case: Some calibration workspace existed but not all!')
            elif has_all:
                # add to dictionary
                has_them = True
                if calib_file_date not in self._loaded_calibration_file_dict:
                    self._loaded_calibration_file_dict[calib_file_date] = dict()
                calib_ws_collection = DetectorCalibrationWorkspaces()
                calib_ws_collection.calibration = '{}_{}'.format(base_ws_name, 'calib')
                calib_ws_collection.mask = '{}_{}'.format(base_ws_name, 'mask')
                calib_ws_collection.grouping = '{}_{}'.format(base_ws_name, 'grouping')
                self._loaded_calibration_file_dict[calib_file_date][num_banks] = calib_ws_collection
            else:
                # has none
                calib_ws_collection = None
            # END-IF
        else:
            # no there
            calib_ws_collection = None
        # END-IF-NOT

        return has_them, calib_ws_collection

    def load_calibration_file(self, calibration_file_name, cal_date_index, num_banks, ref_ws_name):
        """ load calibration file with
        :return:
        """
        # check inputs
        datatypeutility.check_file_name(
            calibration_file_name, check_exist=True, note='Calibration file')
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, None))

        # load calibration
        base_name = self.get_base_name(calibration_file_name, num_banks)
        outputs, offset_ws = mantid_helper.load_calibration_file(
            calibration_file_name, base_name, ref_ws_name)
        # get output workspaces for their names
        calib_ws_collection = DetectorCalibrationWorkspaces()
        calib_ws_collection.calibration = outputs.OutputCalWorkspace.name()
        calib_ws_collection.mask = outputs.OutputMaskWorkspace.name()
        calib_ws_collection.grouping = outputs.OutputGroupingWorkspace.name()

        # add to loaded calibration file container
        if cal_date_index not in self._loaded_calibration_file_dict:
            self._loaded_calibration_file_dict[cal_date_index] = dict()
        self._loaded_calibration_file_dict[cal_date_index][num_banks] = calib_ws_collection

        return calib_ws_collection

    def search_load_calibration_file(self, run_start_date, bank_numbers, ref_workspace_name):
        """
        search for calibration and load it
        :param run_start_date: string in YYYY-MM-DD format
        :param bank_numbers:
        :return:
        """
        # check whether this file has been loaded
        if self.has_loaded(run_start_date, bank_numbers)[0]:
            print('[INFO] Calibration file for run on and before {} has been loaded'
                  ''.format(run_start_date))
            return

        # use run_start_date (str) to search in the calibration date time string
        cal_date_index, calibration_file_name = self.get_calibration_file(
            run_start_date, bank_numbers)
        print('[DB...BAT] Located calibration file {0} with reference ID {1}'
              ''.format(calibration_file_name, cal_date_index))

        # load calibration file
        self.load_calibration_file(calibration_file_name, cal_date_index,
                                   bank_numbers, ref_workspace_name)

        return

    @staticmethod
    def vdrive_binning_ref_ws_name(file_name):
        """
        get the standard workspace name for VDrive binning reference
        :param file_name:
        :return:
        """
        datatypeutility.check_string_variable('VDrive binning reference file', file_name)
        base_name = os.path.basename(file_name)
        ws_name = base_name.split('.')[0]

        return ws_name


class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """
    FilterBadPulse = 1
    AlignAndFocus = 2
    NormaliseByCurrent = 3
    CalibratedByVanadium = 4

    def __init__(self, run_number, ipts_number):
        """
        Purpose:
            Initialize an object of DataReductionTracer
        Requirements:
            1. run number is integer
            2. file path is string
            3. vanadium calibration is a string for calibration file. it could be none
        :return:
        """
        # Check requirements
        datatypeutility.check_int_variable('Run number', run_number, (0, None))
        datatypeutility.check_int_variable('IPTS number', ipts_number, (0, None))

        # set up
        self._iptsNumber = ipts_number
        self._runNumber = run_number

        # vanadium run number. it will be used as a key to the dictionary to look for a vanadium workspace
        self._vanadiumCalibrationRunNumber = None

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._vdriveWorkspace = None
        self._tofWorkspace = None
        self._dspaceWorkspace = None

        # compressed chopped workspace name
        self._compressedChoppedWorkspaceName = None

        # status flag
        self._isReduced = False
        self._isChopped = False

        # detailed reduction information
        self._reductionStatus = None
        self._reductionInformation = None

        # initialize states of reduction beyond
        self._badPulseRemoved = False
        self._normalisedByCurrent = False
        self._correctedByVanadium = False

        # reduced file list
        self._reducedFiles = None

        # variables about chopped workspaces
        self._slicerKey = None   # None stands for the reduction is without chopping
        self._choppedWorkspaceNameList = None
        self._choppedNeXusFileList = list()

        return

    @property
    def compressed_ws_name(self):
        """
        get compressed workspace name
        if the name is not set up yet, then make it and set
        :return:
        """
        if self._compressedChoppedWorkspaceName is None:
            # not set yet.
            self._compressedChoppedWorkspaceName = 'Chopped_{0}_Slicer_{1}.'.format(
                self._runNumber, self._slicerKey)

        return self._compressedChoppedWorkspaceName

    @property
    def dspace_workspace(self):
        """
        Mantid binned d-Spacing workspace
        :return:
        """
        return self._dspaceWorkspace

    @property
    def event_workspace_name(self):
        """
        Get the name of the event workspace
        :return:
        """
        return self._eventWorkspace

    @event_workspace_name.setter
    def event_workspace_name(self, value):
        """
        Set the name of the event workspace.  This operation might be called
        before the workspace is created.
        Requirements:
            1. Input is a string
        :param value:
        :return:
        """
        # Check
        datatypeutility.check_string_variable('Input event workspace', value)

        # Set
        self._eventWorkspace = value

    def get_information(self):
        """
        construct information about the chopped workspace
        :return: a dictionary containing all the information about the reduction tracker
        """
        info_dict = dict()
        info_dict['run'] = self._runNumber
        info_dict['reduced'] = self._isReduced
        if self._slicerKey is None:
            # regular reduced data
            info_dict['slicer_key'] = None
        else:
            # chopped run
            info_dict['slicer_key'] = self._slicerKey
            info_dict['workspaces'] = self._choppedWorkspaceNameList[:]
            info_dict['raw_files'] = self._choppedNeXusFileList[:]
            if self._reducedFiles is not None:
                info_dict['files'] = self._reducedFiles[:]
            else:
                info_dict['files'] = None

        return info_dict

    def get_reduced_gsas(self):
        """

        :return:
        """
        gsas_file = None

        for file_name in self._reducedFiles:
            main_file_name, file_ext = os.path.splitext(file_name)
            if file_ext.lower() in ['.gda', '.gsas', '.gsa']:
                gsas_file = file_name
                break

        if gsas_file is None:
            raise RuntimeError('Unable to locate reduced GSAS file of run {0}.  '
                               'Files found are {1}'.format(self._runNumber, self._reducedFiles))

        return gsas_file

    @property
    def ipts_number(self):
        """
        get the IPTS number set to this run number
        :return:
        """
        return self._iptsNumber

    @property
    def is_chopped(self):
        """
        check whether the reduction is about a chopped run
        :return:
        """
        return self._isChopped

    @is_chopped.setter
    def is_chopped(self, status):
        """
        set the state that the run is chopped
        :return:
        """
        self._isChopped = status

        return

    @property
    def is_chopped_run(self):
        """
        check whether the reduction is about a chopped run
        :return:
        """
        return self._slicerKey is not None

    @property
    def is_corrected_by_vanadium(self):
        """

        :return:
        """
        return self._correctedByVanadium

    @is_corrected_by_vanadium.setter
    def is_corrected_by_vanadium(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool), 'Flag/state must be a boolean'
        self._correctedByVanadium = state

    @property
    def is_normalized_by_current(self):
        """

        :return:
        """
        return self._normalisedByCurrent

    @is_normalized_by_current.setter
    def is_normalized_by_current(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool)

        self._normalisedByCurrent = state

    @property
    def is_reduced(self):
        """ Check whether the event data that has been reduced
        :return:
        """
        return self._isReduced

    @is_reduced.setter
    def is_reduced(self, value):
        """
        Purpose: set the status that the event data has been reduced
        Requirements: value is boolean
        Guarantees:
        :param value:
        :return:
        """
        assert isinstance(
            value, bool), 'Input for is_reduced must be a boolean but not %s.' % str(type(value))
        self._isReduced = value

    @property
    def is_raw(self):
        """
        Show the status whether the workspace has never been processed
        :return:
        """
        return not self._isReduced

    @property
    def run_number(self):
        """ Read only to return the run number that this tracker
        :return:
        """
        return self._runNumber

    @property
    def vdrive_workspace(self):
        """
        VDrive-binned workspace
        :return:
        """
        return self._vdriveWorkspace

    @property
    def sliced_focused_workspaces(self):
        """
        get the names of sliced and focused workspaces
        :return:
        """
        if self._choppedWorkspaceNameList is None or len(self._choppedWorkspaceNameList) == 0:
            return None
        elif self.is_reduced is False:
            return None

        return self._choppedWorkspaceNameList[:]

    @property
    def tof_workspace(self):
        """
        Mantid binned TOF workspace
        :return:
        """
        return self._tofWorkspace

    def set_chopped_workspaces(self, workspace_name_list, append):
        """
        set the chopped workspaces' names
        :param workspace_name_list:
        :param append: append chopped workspaces
        :return:
        """
        # check inputs
        datatypeutility.check_list('Workspace names', workspace_name_list)

        # reset self._choppedWorkspaceNameList if needed
        if self._choppedWorkspaceNameList is None or not append:
            self._choppedWorkspaceNameList = list()

        # append input workspace names by checking valid or existence
        err_msg = ''

        for ws_name in workspace_name_list:
            # check type
            if not isinstance(ws_name, str):
                err_msg += 'Input {} of type {} is invalid to be a workspace name'.format(
                    ws_name, type(ws_name))
                continue

            # check name and existence
            ws_name = ws_name.strip()
            # skip
            if len(ws_name) == 0 or mantid_helper.workspace_does_exist(ws_name) is False:
                err_msg += 'Workspace "{}" does not exist\n'.format(ws_name)
                continue

            # append
            self._choppedWorkspaceNameList.append(ws_name)
        # END-FOR

        if len(err_msg) == 0:
            err_msg = None

        return err_msg

    def set_chopped_nexus_files(self, chopped_file_list, append=True):
        """ set NeXus files that are saved from chopped workspace to this tracker
        """
        # check input
        assert isinstance(chopped_file_list, list), 'Chopped NeXus files {0} must be given by list but not {1}.' \
                                                    ''.format(chopped_file_list,
                                                              type(chopped_file_list))

        # clear previous data
        if not append:
            self._choppedNeXusFileList = list()

        # append the input file lsit
        self._choppedNeXusFileList.extend(chopped_file_list)

        return

    def set_reduced_files(self, file_name_list, append):
        """
        add reduced file
        :param file_name_list:
        :param append:
        :return:
        """
        assert isinstance(file_name_list, list), 'Input file names must be in a list but not {0}.' \
                                                 ''.format(type(file_name_list))

        if not append or self._reducedFiles is None:
            self._reducedFiles = file_name_list[:]
        else:
            self._reducedFiles.extend(file_name_list[:])

        return

    def set_reduced_workspaces(self, vdrive_bin_ws, tof_ws, dspace_ws):
        """

        :param vdrive_bin_ws:
        :param tof_ws:
        :param dspace_ws: it could be None or name of workspace in d-spacing
        :return:
        """
        # check workspaces existing
        if vdrive_bin_ws is not None:
            assert mantid_helper.workspace_does_exist(vdrive_bin_ws), 'VDrive-binned workspace {0} does not exist ' \
                                                                      'in ADS'.format(vdrive_bin_ws)
        if tof_ws is not None:
            assert mantid_helper.workspace_does_exist(tof_ws), 'Mantid-binned TOF workspace {0} does not exist ' \
                                                               'in ADS.'.format(tof_ws)

        if dspace_ws is not None:
            assert mantid_helper.workspace_does_exist(dspace_ws),\
                'Mantid-binned D-space workspace {0} does not exist in ADS.'.format(dspace_ws)
            dspace_ws_unit = mantid_helper.get_workspace_unit(dspace_ws)
            assert dspace_ws_unit == 'dSpacing',\
                'Unable to set reduced d-space workspace: The unit of DSpace workspace {0} should be dSpacing but ' \
                'not {1}.'.format(str(dspace_ws), dspace_ws_unit)
        # END-IF

        self._vdriveWorkspace = vdrive_bin_ws
        self._tofWorkspace = tof_ws
        self._dspaceWorkspace = dspace_ws

        # set reduced signal
        self.is_reduced = True

        return

    def set_reduction_status(self, status, message, chopped_data):
        """
        set the reduction status for this tracker
        :param status:
        :param message:
        :param chopped_data
        :return:
        """
        # check input
        assert isinstance(
            status, bool), 'Reduction status must be given by bool but not {0}'.format(type(status))
        assert isinstance(message, str), 'Reduction message {0} must be string but not {1}' \
                                         ''.format(message, type(message))
        assert isinstance(chopped_data, bool), 'Flag for being chopped run must be boolean but not {0}' \
                                               ''.format(type(chopped_data))

        self._reductionStatus = status
        self._reductionInformation = message
        self._isChopped = chopped_data

        return

    def set_slicer_key(self, slicer_key):
        """
        set slicer key to the
        :param slicer_key:
        :return:
        """
        self._slicerKey = slicer_key

        return

    @property
    def vanadium_calibration(self):
        """
        Return vanadium calibration run number
        :return:
        """
        return self._vanadiumCalibrationRunNumber

    @vanadium_calibration.setter
    def vanadium_calibration(self, value):
        """
        Set vanadium calibration run number
        Purpose:
        Requirements:
            value is integer
        Guarantees:
            vanadium run number is set
        :param value:
        :return:
        """
        assert isinstance(value, int), 'Input value should be integer for run number'
        self._vanadiumCalibrationRunNumber = value

        return
# END-CLASS


class ReductionManager(object):
    """ Class ReductionManager takes the control of reducing SNS/VULCAN's event data
    to diffraction pattern for Rietveld analysis.

    * Business model and technical model
      - Run number as integers or data file name are used to communicate with client;
      - Workspace names are used for internal communications.

    Its main data structure contains
    1. a dictionary of reduction controller
    2. a dictionary of loaded vanadium

    ??? It is able to reduce the data file in the format of data file,
    run number and etc.

    ??? It supports event chopping.
    """
    SUPPORTED_INSTRUMENT = ['VULCAN']

    def __init__(self, instrument):
        """
        Purpose:

        Requirements:
            1. instrument is a valid instrument's name
        Guarantees:
        :param instrument:
        :return:
        """
        # Check requirements
        datatypeutility.check_string_variable('Instrument name', instrument, None)
        instrument = instrument.upper()
        if instrument not in ReductionManager.SUPPORTED_INSTRUMENT:
            raise RuntimeError('Instrument %s is not in the supported instruments (%s).'
                               '' % (instrument, ReductionManager.SUPPORTED_INSTRUMENT))

        # Set up including default
        self._myInstrument = instrument

        # reduction tracker: key = run number (integer), value = DataReductionTracker
        # [run number] = Tracker or [run number, slicer key] = Tracker
        self._reductionTrackDict = dict()

        # calibration file and workspaces management
        self._calibrationFileManager = CalibrationManager()   # key = calibration file name

        # init standard diffraction focus parameters: instrument geometry parameters
        self._diff_focus_params = self._init_vulcan_diff_focus_params()

        # masks and ROI
        self._loaded_masks = dict()  # [mask/roi xml] = mask_ws_name, is_roi

        # gsas output
        # TODO - FIXME - TONIGHT - In setup.py: if _vdrive_tof_bin.h5 does not exist in /SNS/...
        # TODO - cont. - TONIGHT - then, copy this file from /data/ to .pyvdrive/...
        try:
            self._gsas_writer = save_vulcan_gsas.SaveVulcanGSS(None)
        except RuntimeError as run_err:
            print('[ERROR] Unable to initialize GSAS writer due to {}'.format(run_err))
            self._gsas_writer = None

        # vanadium: key = vanadium run number, value = vanadium GSAS file
        self._vanadium_run_dict = dict()

        return

    @property
    def calibration_manager(self):
        """ Handler to instrument geometry calibration file manager
        :return:
        """
        return self._calibrationFileManager

    @property
    def gsas_writer(self):
        """
        instance of VDRIVE-compatible GSAS writer
        :return:
        """
        return self._gsas_writer

    @staticmethod
    def _init_vulcan_diff_focus_params():
        """
        initial setup for diffraction focus algorithm parameters
        :return:
        """
        params_dict = dict()
        params_dict['CompressEvents'] = dict()
        params_dict['EditInstrumentGeometry'] = dict()

        # compress events
        params_dict['CompressEvents']['Tolerance'] = 0.01

        # edit instrument
        params_dict['EditInstrumentGeometry']['L1'] = None
        params_dict['EditInstrumentGeometry']['SpectrumIDs'] = None
        params_dict['EditInstrumentGeometry']['L2'] = None
        params_dict['EditInstrumentGeometry']['Polar'] = None
        params_dict['EditInstrumentGeometry']['Azimuthal'] = None

        return params_dict

    def add_reduced_vanadium(self, van_run_number, van_file_name):
        """
        add a reduced vanadium gsas file information
        :param van_run_number:
        :param van_file_name:
        :return:
        """
        # check input
        datatypeutility.check_int_variable('Vanadium run number', van_run_number, (1, None))
        datatypeutility.check_file_name(van_file_name, True, False, False, 'Vanadium GSAS file')
        self._vanadium_run_dict[van_run_number] = van_file_name

        return

    def apply_detector_efficiency(self, to_fill):
        """
        As name
        :param to_fill:
        :return:
        """
        #     # convert to matrix workspace to apply detector efficiency?
        #     convert_to_matrix = self._det_eff_ws_name is not None and apply_det_efficiency
        #     if apply_det_efficiency:
        #         # rebin
        #         Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params=binning,
        #               PreserveEvents=not convert_to_matrix)
        #         # apply detector efficiency
        #         Multiply(LHSWorkspace=ws_name, RHSWorkspace=self._det_eff_ws_name, OutputWorkspace=ws_name)
        raise NotImplementedError('ASAP')

    def chop_vulcan_run(self, ipts_number, run_number, raw_file_name, split_ws_name, split_info_name, slice_key,
                        output_directory, reduce_data_flag, save_chopped_nexus, number_banks,
                        tof_correction, user_binning_parameter,
                        roi_list, mask_list, no_cal_mask, van_gda_name, gsas_parm_name='vulcan.prm',
                        fullprof=False, bin_overlap_mode=False, gda_file_start=1):
        """
        Latest version: version 3
        :param ipts_number:
        :param run_number:
        :param raw_file_name:
        :param split_ws_name:
        :param split_info_name:
        :param slice_key:
        :param output_directory:
        :param reduce_data_flag:
        :param save_chopped_nexus:
        :param number_banks:
        :param tof_correction: TOF correction
        :param van_gda_name: None (for no-correction) or GSAS file name of smoothed vanadium
        :param user_binning_parameter:
        :param fullprof: Flag to write out Fullprof file format
        :param roi_list:
        :param mask_list:
        :param no_cal_mask:
        :param bin_overlap_mode: if True, then 'time bins' (time splitters) will have overlapped time
        :param gsas_parm_name:
        :param gda_file_start: starting order (index) of the chopped and reduced GSAS file name (0.gda or 1.gda)
        :return: 2-tuple (string: regular message, string: error message)
        """
        # Load data
        event_ws_name = self.get_event_workspace_name(run_number=run_number)
        mantid_helper.load_nexus(raw_file_name, event_ws_name, meta_data_only=False)
        print('[INFO] Successfully loaded {0} to {1}'.format(raw_file_name, event_ws_name))

        # Load user specified masks/ROIs
        datatypeutility.check_list('Region of interest file list', roi_list)
        datatypeutility.check_list('Mask file list', mask_list)
        if len(roi_list) > 0 and len(mask_list) > 0:
            raise RuntimeError('Unable to support both user-specified ROI and Mask simultaneously')
        elif len(roi_list) > 0:
            user_mask_name = self.load_mask_files(event_ws_name, roi_list, is_roi=True)
        elif len(mask_list) > 0:
            user_mask_name = self.load_mask_files(event_ws_name, roi_list, is_roi=False)
        else:
            print('[INFO] No user specified masking and ROI files')
            user_mask_name = None
        # END-IF-ELSE

        # Load geometry calibration file
        calib_ws_name, group_ws_name, mask_ws_name = self._get_calibration_workspaces_names(
            event_ws_name, number_banks)

        # apply mask
        if user_mask_name:
            mantid_helper.mask_workspace(event_ws_name, user_mask_name)
        if not no_cal_mask:
            mantid_helper.mask_workspace(event_ws_name, mask_ws_name)

        # create a reduction setup instance
        reduction_setup = reduce_VULCAN.ReductionSetup()
        # set up reduction parameters
        reduction_setup.set_ipts_number(ipts_number)
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(raw_file_name)

        # splitters workspace suite
        reduction_setup.set_splitters(split_ws_name, split_info_name)

        # option to save to archive
        if output_directory is None:
            # save to SNS archive.
            reduction_setup.set_chopped_output_to_archive(create_parent_directories=True)
        else:
            # save to user-specified directories. GSAS and NeXus will be in the same directory
            reduction_setup.set_output_dir(output_directory)
            reduction_setup.set_gsas_dir(output_directory, main_gsas=True)
            reduction_setup.set_chopped_nexus_dir(output_directory)

        # create an AdavancedChopReduce instance
        chop_reducer = reduce_adv_chop.AdvancedChopReduce(reduction_setup)
        # set calibrated instrument
        chop_reducer.set_focus_virtual_instrument(
            self._calibrationFileManager.get_focused_instrument_parameters(number_banks))
        if reduce_data_flag:
            # chop and reduce chopped data to GSAS: NOW, it is Version 2.0 speedup
            reduction_setup.set_calibration_workspaces(calib_ws_name, group_ws_name, mask_ws_name)

            # initialize tracker
            tracker = self.init_tracker(ipts_number, run_number, slice_key)
            tracker.is_reduced = False

            # set up the flag to save chopped raw data
            reduction_setup.save_chopped_workspace = save_chopped_nexus

            # set the flag for not being an auto reduction
            reduction_setup.is_auto_reduction_service = False

            # set up reducer
            reduction_setup.process_configurations()

            # Slice and focus the data *** V2.0
            # determine the binning for output GSAS workspace
            if user_binning_parameter is None:
                binning_param_dict = None
            else:
                binning_param_dict = user_binning_parameter

            # END-IF-ELSE
            # virtual_geometry_dict = self._calibrationFileManager.get_focused_instrument_parameters(num_banks)

            gsas_info = {'IPTS': ipts_number, 'parm file': gsas_parm_name, 'vanadium': van_gda_name}
            status, message = chop_reducer.execute_chop_reduction_v2(event_ws_name=event_ws_name,
                                                                     calib_ws_name=calib_ws_name,
                                                                     group_ws_name=group_ws_name,
                                                                     binning_parameters=binning_param_dict,
                                                                     gsas_info_dict=gsas_info,
                                                                     fullprof=fullprof,
                                                                     clear_workspaces=True,
                                                                     gsas_writer=self._gsas_writer,
                                                                     num_reduced_banks=number_banks,
                                                                     chop_overlap_mode=bin_overlap_mode,
                                                                     gsas_file_index_start=gda_file_start)

            # set up the reduced file names and workspaces and add to reduction tracker dictionary
            tracker.set_reduction_status(status, message, True)

            reduced, workspace_name_list = chop_reducer.get_reduced_workspaces(chopped=True)
            chop_message = 'Output GSAS: {}.gda - {}.gda'.format(gda_file_start,
                                                                 gda_file_start - 1 + len(workspace_name_list))

            error_message = self.set_chopped_reduced_workspaces(
                run_number, slice_key, workspace_name_list, append=True)
            self.set_chopped_reduced_files(
                run_number, slice_key, chop_reducer.get_reduced_files(), append=True)

            tracker.is_reduced = True

        else:
            # chop data only without reduction
            raise NotImplementedError('This branch is temporarily disabled')
            # status, ret_obj = chop_reducer.chop_data()
            #
            # if not status:
            #     return False, ('', 'Unable to chop run {0} due to {1}.'.format(run_number, ret_obj))
            #
            # # get chopped workspaces' names, saved NeXus file name; check them and store to lists
            # chopped_ws_name_list = list()
            # chopped_file_list = list()
            # for file_name, ws_name in ret_obj:
            #     if file_name is not None:
            #         chopped_file_list.append(file_name)
            #     if isinstance(ws_name, str) and mantid_helper.workspace_does_exist(ws_name):
            #         chopped_ws_name_list.append(ws_name)
            # # END-FOR
            # chop_message = '{}'.format(chopped_file_list)
            #
            # # initialize tracker
            # tracker = self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=slice_key)
            # tracker.is_reduced = False
            # tracker.is_chopped = True
            # if len(chopped_ws_name_list) > 0:
            #     tracker.set_chopped_workspaces(chopped_ws_name_list, append=True)
            # if len(chopped_file_list) > 0:
            #     tracker.set_chopped_nexus_files(chopped_file_list, append=True)
        # END-IF

        return True, (chop_message, error_message)

    def get_event_workspace_name(self, run_number):
        """
        Get or generate the name of a raw event workspace
        Requirements: run number must be a positive integer
        :param run_number:
        :return:
        """
        # check
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        # form the reduction-manager-standard name
        event_ws_name = '%s_%d_events' % (self._myInstrument, run_number)

        return event_ws_name

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
        assert unit is None or isinstance(
            unit, str), 'Output data unit must be either None (default) or a string.'

        # get reduced workspace name
        reduced_ws_name = self.get_reduced_workspace(run_number, is_vdrive_bin=True, unit='TOF')

        # get data
        data_set_dict, unit = mantid_helper.get_data_from_workspace(reduced_ws_name, target_unit=unit,
                                                                    point_data=True, start_bank_id=True)
        assert isinstance(data_set_dict, dict), 'Returned value from get_data_from_workspace must be a dictionary,' \
                                                'but not %s.' % str(type(data_set_dict))

        return data_set_dict

    def get_reduced_file(self, run_number, file_type):
        """

        :param run_number:
        :param file_type:
        :return:
        """
        # check inputs
        assert isinstance(file_type, str) and file_type in ['gda', 'gsas', 'gss'],\
            'File type {0} is not supported.'.format(file_type)

        if file_type in ['gda', 'gsas', 'gsa']:
            file_name = self._reductionTrackDict[run_number].get_reduced_gsas()
        else:
            raise RuntimeError('Not Implemented yet!')

        return file_name

    def get_reduced_single_runs(self):
        """
        :return: a list of [case 1] run numbers [case 2]
        """
        return_list = list()

        print('[DB...BAT...Single] Reduction-track dict keys: {}'.format(self._reductionTrackDict.keys()))

        # from tracker
        for tracker_key in self._reductionTrackDict.keys():
            # get tracker with is_reduced being True
            tracker = self._reductionTrackDict[tracker_key]
            if not tracker.is_reduced:
                continue

            # filter out the tracker with key of type, tuple, which are for chopped runs
            if not isinstance(tracker_key, int):
                continue

            # using run number (for name) and tracker key (for accessing the specific workspace)
            run_number = tracker.run_number
            return_list.append((run_number, tracker_key))
        # END-FOR

        return return_list

    def get_reduced_chopped_runs(self):
        """
        get reduced VULCAN runs with option for single run or chopped run
        (It is just for information)
        :param with_ipts:
        :param chopped:
        :return: a list of tracker key , i.e., tuple (run number, slice key)
        """
        return_list = list()

        # from tracker
        for tracker_key in self._reductionTrackDict.keys():
            # get tracker with is_reduced being True
            tracker = self._reductionTrackDict[tracker_key]
            if not tracker.is_reduced:
                continue

            # filter out the tracker with key type and flag-chopped
            if not isinstance(tracker_key, tuple):
                if not isinstance(tracker_key, int):
                    raise RuntimeError('Tracker key {} of type {} is not well defined'
                                       ''.format(tracker_key, type(tracker_key)))
                continue

            new_item = tracker_key
            print('[DB...BAT] Reduced run with {} of type {}'.format(new_item, type(new_item)))
            return_list.append(new_item)
        # END-FOR

        return return_list

    def get_sliced_focused_workspaces(self, run_number, slice_key):
        """
        get the sliced and diffraction focused data in workspace
        :param run_number:
        :param slice_key:
        :return: a list of string as workspace names
        """
        tracker = self.get_tracker(run_number, slice_key)

        return tracker.sliced_focused_workspaces

    def get_reduced_workspace(self, run_number, binning_params=None, is_vdrive_bin=True, unit=None):
        """ Get the reduced matrix workspace
        Requirements:
            1. Specified run is correctly reduced;
        Guarantees:
            2. Return reduced workspace's name
        Arguments:
         - unit :: target unit; If None, then no need to convert unit
        :exception: Assertion Error if run number does not exist in self._reductionTrackDict
        :exception: RuntimeError if unit is not supported
        :param run_number:
        :param binning_params: binning parameters string
        :param is_vdrive_bin:
        :param unit:
        :return: Workspace name
        """
        # Check requirements
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        if binning_params is not None:
            datatypeutility.check_string_variable('Binning parameter (string)', binning_params)

        # full reduction
        # get tracker
        assert run_number in self._reductionTrackDict, 'Run number {0} is not reduced.'.format(
            run_number)
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker), \
            'Stored tracker must be an instance of DataReductionTracker.'

        if is_vdrive_bin and unit != 'TOF':
            raise RuntimeError('It is possible to get a VDrive-binned workspace in unit {0} other than TOF.'
                               ''.format(unit))
        elif unit is not None and unit != 'TOF' and unit.lower() != 'dspace':
            raise RuntimeError('Unit {0} is not supported.'.format(unit))

        # get the position
        if is_vdrive_bin:
            return_ws_name = tracker.vdrive_workspace
        elif unit is None:
            return_ws_name = tracker.tof_workspace
            if return_ws_name is None:
                return_ws_name = tracker.dspace_workspace
        elif unit == 'TOF':
            return_ws_name = tracker.tof_workspace
        elif unit.lower() == 'dSpacing':
            return_ws_name = tracker.dspace_workspace
        else:
            raise RuntimeError('It is very hardly to happen!')
        # END-IF-ELSE

        return return_ws_name

    def get_tracker(self, run_number, slicer_key):
        """
        get a reduction tracker
        :param run_number:
        :param slicer_key:
        :return:
        """
        # construct a tracker key
        tracker_key = run_number, slicer_key
        if tracker_key in self._reductionTrackDict:
            tracker = self._reductionTrackDict[tracker_key]
        else:
            raise RuntimeError('Unable to locate tracker with run: {0} slicer: {1}.  Existing keys are {2}'
                               ''.format(run_number, slicer_key, self._reductionTrackDict.keys()))

        return tracker

    def has_run_reduced(self, run_number):
        """
        check whether a certain run number is reduced and stored
        :param run_number:
        :return:
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))

        has = run_number in self._reductionTrackDict

        return has

    def has_run_sliced_reduced(self, chop_data_key):
        """
        check whether input 'chopped data key' corresponds to any reduced runs
        :param chop_data_key:  run number, slicer key
        :return:
        """
        datatypeutility.check_tuple('Chopped data (lookup) key', chop_data_key, 2)
        run_number, slicer_key = chop_data_key
        datatypeutility.check_int_variable('Run number', run_number, (1, 999999999))
        datatypeutility.check_string_variable('Slicer key', slicer_key)

        return chop_data_key in self._reductionTrackDict

    def init_tracker(self, ipts_number, run_number, slicer_key=None):
        """ Initialize tracker
        :param ipts_number:
        :param run_number:
        :param slicer_key: if not specified, then the reduction is without chopping
        :return: a DataReductionTracker object that is just created and initialized
        """
        # Check requirements: IPTS / run number == 1 is for pseudo IPTS/RUN in the case of arbitrary NeXus file
        datatypeutility.check_int_variable('IPTS', ipts_number, (0, None))
        datatypeutility.check_int_variable('Run number', run_number, (0, None))

        # Initialize a new tracker
        if slicer_key is None:
            tracker_key = run_number
        else:
            tracker_key = run_number, slicer_key

        if ipts_number is None:
            raise NotImplementedError(
                'Figure out how to track a reduction without a good IPTS number!')

        if tracker_key not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number, ipts_number)
            new_tracker.set_slicer_key(slicer_key)
            self._reductionTrackDict[tracker_key] = new_tracker
        else:
            # existing tracker: double check
            assert isinstance(self._reductionTrackDict[tracker_key], DataReductionTracker),\
                'It is not DataReductionTracker but a {0}.'.format(
                    type(self._reductionTrackDict[tracker_key]))
            # NOTE: new_tracker here is not new tracker at all!
            new_tracker = self._reductionTrackDict[tracker_key]

        return new_tracker

    def diffraction_focus_workspace(self, event_ws_name, output_ws_name, binning_params,
                                    target_unit,
                                    calibration_workspace, grouping_workspace,
                                    virtual_instrument_geometry, keep_raw_ws):
        """ Diffraction focus an EventWorkspace
        :exception: Intolerable error
        :param event_ws_name:
        :param output_ws_name:
        :param binning_params:
        :param target_unit:
        :param calibration_workspace:
        :param grouping_workspace:
        :param virtual_instrument_geometry:
        :param keep_raw_ws:
        :return: string as reduction message for successful reduction
        """
        def check_binning_parameter_range(x_min, x_max, ws_unit):
            """
            check whether range of X values of binning makes sense with target unit
            :param x_min:
            :param x_max:
            :param ws_unit:
            :return:
            """
            if ws_unit == 'dSpacing' and not 0 < x_min < x_max < 20:
                # dspacing within (0, 20)
                x_range_is_wrong = True
            elif ws_unit == 'TOF' and not 1000 < x_min < x_max < 1000000:
                # TOF within (1000, 1000000)
                x_range_is_wrong = True
            elif ws_unit != 'dSpacing' and ws_unit != 'TOF':
                raise NotImplementedError('Impossible case for unit {}'.format(ws_unit))
            else:
                # good cases
                x_range_is_wrong = False

            if x_range_is_wrong:
                ero_msg = 'For {0}, X range ({1}, {2}) does not make sense' \
                          ''.format(ws_unit, x_min, x_max)
                print('[ERROR CAUSING CRASH] {}'.format(ero_msg))
                raise RuntimeError(ero_msg)

            return

        # check inputs
        datatypeutility.check_string_variable('Target unit', target_unit, ['TOF', 'dSpacing'])
        datatypeutility.check_dict('Virtual (focused) instrument geometry',
                                   virtual_instrument_geometry)

        # set up default binning parameters: only support uniform binning parameters, i.e., no ragged workspace
        if binning_params is None:
            # do nothing: eventually using default binning?
            if target_unit == 'TOF':
                binning_params = 5000, -0.01, 30000
            else:
                binning_params = 0.5, -0.01, 3.5  # use a very coarse binning
        else:
            datatypeutility.check_tuple('Binning parameters', binning_params)
            if len(binning_params) == 1:
                # it is fine
                pass
            elif len(binning_params) == 3:
                # check against the unit
                check_binning_parameter_range(binning_params[0], binning_params[2], target_unit)
            else:
                # unsupported number of binning parameters
                err_msg = 'Binning parameters {0} with {1} items are not supported.' \
                          ''.format(binning_params, len(binning_params))
                print('[Crash Error] {}'.format(err_msg))
                raise RuntimeError(err_msg)
        # END-IF-ELSE

        # virtual instrument
        self._diff_focus_params['EditInstrumentGeometry'] = virtual_instrument_geometry

        # align and focus
        print('[DB...PROGRESS...] ReductionManager: align and focus workspace from {} to {} with binning {}'
              ''.format(event_ws_name, output_ws_name, binning_params))
        red_msg = mantid_reduction.align_and_focus_event_ws(event_ws_name, output_ws_name, binning_params,
                                                            calibration_workspace, grouping_workspace,
                                                            reduction_params_dict=self._diff_focus_params,
                                                            convert_to_matrix=False)

        # remove input event workspace
        if output_ws_name != event_ws_name and keep_raw_ws is False:
            # if output name is same as input. no need to do the operation
            mantid_helper.delete_workspace(event_ws_name)

        return red_msg

    @staticmethod
    def load_mask_files(event_ws_name, mask_file_name_list, is_roi=False):
        """ Mask detectors and optionally load the mask file for first time
        :param event_ws_name:
        :param mask_file_name_list:
        :param is_roi:
        :return:
        """
        # check
        datatypeutility.check_list('Mask files', mask_file_name_list)

        # return as None for empty list
        if len(mask_file_name_list) == 0:
            raise RuntimeError('Mask XML file names list is empty')

        mask_ws_names = list()
        hash_sum = 0
        for mask_file_name in mask_file_name_list:
            # use mask/ROI file to get hash() and check in dictionary whether a ... is loaded
            if is_roi:
                mask_ws_name = 'roi_{}'.format(hash(mask_file_name))
            else:
                mask_ws_name = 'mask_{}'.format(hash(mask_file_name))
            hash_sum += hash(mask_ws_name)

            # load mask file and roi file if not loaded yet
            if not mantid_helper.workspace_does_exist(mask_ws_name):
                mantid_helper.load_mask_xml(event_ws_name, mask_file_name, mask_ws_name)

            # set
            mask_ws_names.append(mask_ws_name)
        # END-FOR

        # do binary operation among mask files or ... files
        if is_roi:
            mask_operation = 'AND'
        else:
            mask_operation = 'OR'

        if len(mask_ws_names) > 1:
            combine_mask_name = 'roi_{}_{}'.format(is_roi, hash_sum)
            mantid_helper.clone_workspace(mask_ws_names[0], combine_mask_name)
            for ws_name_index in range(1, len(mask_ws_names)):
                mantid_api.BinaryOperateMasks(InputWorkspace1=combine_mask_name,
                                              InputWorkspace2=mask_ws_names[ws_name_index],
                                              OutputWorkspace=combine_mask_name,
                                              OperationType=mask_operation)
        else:
            combine_mask_name = mask_ws_names[0]

        return combine_mask_name

    def reduce_event_nexus_ver1(self, ipts_number, run_number, event_file, output_directory, merge_banks,
                                vanadium=False,
                                vanadium_tuple=None, gsas=True, standard_sample_tuple=None, binning_parameters=None,
                                num_banks=3):
        """
        Reduce run with selected options by calling SNSPowderReduction (eventually).
        It will be replaced by reduce_event_nexus() later
        Purpose:
        Requirements:
        Guarantees:
        :param ipts_number:
        :param run_number:
        :param event_file:
        :param output_directory:
        :param merge_banks:
        :param vanadium:
        :param vanadium_tuple:
        :param gsas:
        :param standard_sample_tuple:
        :param binning_parameters:
        :param num_banks: number of banks focused to.  Now only 3, 7 and 27 are allowed.
        :return:
        """
        # set up reduction options
        reduction_setup = reduce_VULCAN.ReductionSetup()

        # run number, ipts and etc
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(event_file)
        reduction_setup.set_ipts_number(ipts_number)
        reduction_setup.set_banks_to_merge(merge_banks)
        reduction_setup.set_default_calibration_files(num_focused_banks=num_banks)

        # parse binning parameters
        if binning_parameters is not None:
            if len(binning_parameters) == 3:
                tof_min, bin_size, tof_max = binning_parameters
            elif len(binning_parameters) == 1:
                bin_size = binning_parameters[0]
                tof_min = 3000.
                tof_max = 70000.
            else:
                raise RuntimeError('Binning parameters {0} must have 3 parameters.'
                                   ''.format(binning_parameters))
            reduction_setup.set_binning_parameters(tof_min, bin_size, tof_max)
            reduction_setup.set_align_vdrive_bin(False)
        else:
            reduction_setup.set_align_vdrive_bin(True)
        # END-IF

        # vanadium
        reduction_setup.normalized_by_vanadium = vanadium
        if vanadium:
            assert isinstance(vanadium_tuple, tuple) and len(vanadium_tuple) == 3,\
                'Input vanadium-tuple must be a tuple with length 3.'
            van_run, van_gda, vanadium_tag = vanadium_tuple
            reduction_setup.set_vanadium(van_run, van_gda, vanadium_tag)

        # outputs
        if output_directory is not None:
            reduction_setup.set_output_dir(output_directory)
            if gsas:
                reduction_setup.set_gsas_dir(output_directory, True)

        # process on standards
        if standard_sample_tuple:
            assert isinstance(standard_sample_tuple, tuple) and len(standard_sample_tuple) == 3,\
                'Input standard sample-tuple must be a tuple with length 3 but not a {0}.'.format(
                    standard_sample_tuple)
            standard_sample, standard_dir, standard_record_file = standard_sample_tuple
            reduction_setup.is_standard = True
            reduction_setup.set_standard_sample(standard_sample, standard_dir, standard_record_file)
        # END-IF (standard sample tuple)

        # reduce
        reduction_setup.is_auto_reduction_service = False
        reducer = reduce_VULCAN.ReduceVulcanData(reduction_setup)
        # TODO/TODO/NOW/NOW - This shall be re-writen???
        reduce_good, message = reducer.execute_vulcan_reduction(output_logs=False)

        # record reduction tracker
        if reduce_good:
            self.init_tracker(ipts_number, run_number)

            if vanadium:
                self._reductionTrackDict[run_number].is_corrected_by_vanadium = True

            # set reduced files
            self._reductionTrackDict[run_number].set_reduced_files(
                reducer.get_reduced_files(), append=False)
            # set workspaces
            status, ret_obj = reducer.get_reduced_workspaces(chopped=False)
            if status:
                # it may not have the workspace because
                vdrive_ws, tof_ws, d_ws = ret_obj
                self.set_reduced_workspaces(run_number, vdrive_ws, tof_ws, d_ws)

        # END-IF

        return reduce_good, message

    def _get_calibration_workspaces_names(self, ws_name, num_banks):
        """ Read the run start date/time to get the calibrtion workspaces' names
        :param ws_name:
        :param num_banks:
        :return:
        """
        # get start time: it is not convenient to get date/year/month from datetime64.
        # use the simple but fragile method first
        run_start_date = mantid_helper.get_run_start(ws_name, time_unit=None)

        has_loaded_cal, workspaces = self._calibrationFileManager.has_loaded(
            run_start_date, num_banks)
        if not has_loaded_cal:
            print('[DB...BAT...INFO] Calibration file has not been loaded')
            self._calibrationFileManager.search_load_calibration_file(
                run_start_date, num_banks, ws_name)
            workspaces = self._calibrationFileManager.get_loaded_calibration_workspaces(
                run_start_date, num_banks)
        else:
            print('[DB...BAT...INFO] Calibration file for {} has been loaded to {}'.format(
                run_start_date, workspaces))
        calib_ws_name = workspaces.calibration
        group_ws_name = workspaces.grouping
        mask_ws_name = workspaces.mask

        return calib_ws_name, group_ws_name, mask_ws_name

    def reduce_event_2theta_group(self, run_number, event_nexus_name, ws_index_range,
                                  two_theta_range, two_theta_step,
                                  binning_parameters, van_run_number,
                                  iparam_name, output_dir):
        # reduce a workspace with pixels grouped by 2theta

        # Load data
        event_ws_name = self.get_event_workspace_name(run_number=run_number)
        mantid_helper.load_nexus(event_nexus_name, event_ws_name, meta_data_only=False)

        # Generate a group workspace for given 2theta range
        group_ws_name = '{}_2theta_group'.format(event_ws_name)
        results = vulcan_util.group_pixels_2theta(vulcan_ws_name=event_ws_name,
                                                  tth_group_ws_name=group_ws_name,
                                                  start_iws=ws_index_range[0],
                                                  end_iws=ws_index_range[1],
                                                  two_theta_bin_range=two_theta_range,
                                                  two_theta_step=two_theta_step)
        two_theta_array, group_ws, num_pixels_array = results

        # Regular calibration workspace
        calib_ws_name, no_use_grp, mask_ws_name = self._get_calibration_workspaces_names(
            event_ws_name, 3)
        template_virtual_geometry_dict = self._calibrationFileManager.get_focused_instrument_parameters(
            3)
        virtual_geometry_dict = vulcan_util.group_pixels_2theta_geometry(template_virtual_geometry_dict,
                                                                         ws_index_range, num_pixels_array.shape[0])

        # Reduce to Rietveld
        red_message = self.diffraction_focus_workspace(event_ws_name=event_ws_name,
                                                       output_ws_name=event_ws_name,  # keep the workspace name
                                                       binning_params=binning_parameters,
                                                       target_unit='TOF',
                                                       calibration_workspace=calib_ws_name,
                                                       grouping_workspace=group_ws_name,
                                                       virtual_instrument_geometry=virtual_geometry_dict,
                                                       keep_raw_ws=False)

        return event_ws_name, two_theta_array, num_pixels_array, red_message

    # TODO - TONIGHT 0 - Code Quality - 20180713 - Find out how to reuse codes from vulcan_slice_reduce.SliceFocusVulcan
    def reduce_event_nexus(self, ipts_number, run_number, event_nexus_name, target_unit, binning_parameters,
                           num_banks, roi_list, mask_list, no_cal_mask):
        """ Reduce event workspace including load and diffraction focus. V2
        It is, in fact, version 2. by using the essential parts in SNSPowderReduction
        The result, i.e., output workspace shall be an EventWorkspace still
        :param ipts_number:
        :param run_number:
        :param event_nexus_name:
        :param target_unit:
        :param binning_parameters:
        :param num_banks:
        :param roi_list:
        :param mask_list:
        :return: reduced workspace name, (ragged) GSAS worksapce (only for SaveGSS) and error message
        """
        # check inputs
        if len(roi_list) > 0 and len(mask_list) > 0:
            raise RuntimeError('It is not allowed to define ROI and mask simultaneously, which causing logic'
                               ' confusion')
        elif len(roi_list) + len(mask_list) > 0 and no_cal_mask:
            raise RuntimeError(
                'It is not allowed to define ROI or Mask with NO-CALIBRATION-MASK simultaneously')

        # Load data
        event_ws_name = self.get_event_workspace_name(run_number=run_number)
        mantid_helper.load_nexus(event_nexus_name, event_ws_name, meta_data_only=False)

        # Mask data
        datatypeutility.check_list('Region of interest file list', roi_list)
        datatypeutility.check_list('Mask file list', mask_list)
        if len(roi_list) + len(mask_list) > 0:
            print('[INFO] Processing masking and ROI files: {} and {}'.format(roi_list, mask_list))
            if len(roi_list) > 0:
                user_mask_name = self.load_mask_files(event_ws_name, roi_list, is_roi=True)
            else:
                user_mask_name = self.load_mask_files(event_ws_name, mask_list, is_roi=False)
        else:
            print('[INFO] No user specified masking and ROI files')
            user_mask_name = None
        # END-IF-ELSE

        calib_ws_name, group_ws_name, mask_ws_name = self._get_calibration_workspaces_names(
            event_ws_name, num_banks)

        # apply mask
        if user_mask_name:
            mantid_helper.mask_workspace(event_ws_name, user_mask_name)
        if not no_cal_mask:
            mantid_helper.mask_workspace(event_ws_name, mask_ws_name)

        # set tracker
        tracker = self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=None)
        tracker.is_reduced = False

        # diffraction focus
        virtual_geometry_dict = self._calibrationFileManager.get_focused_instrument_parameters(
            num_banks)

        red_message = self.diffraction_focus_workspace(event_ws_name=event_ws_name,
                                                       output_ws_name=event_ws_name,  # keep the workspace name
                                                       binning_params=binning_parameters,
                                                       target_unit=target_unit,
                                                       calibration_workspace=calib_ws_name,
                                                       grouping_workspace=group_ws_name,
                                                       virtual_instrument_geometry=virtual_geometry_dict,
                                                       keep_raw_ws=False)

        if target_unit.lower().count('d'):
            tracker.set_reduced_workspaces(vdrive_bin_ws=None, tof_ws=None, dspace_ws=event_ws_name)
        else:
            tracker.set_reduced_workspaces(vdrive_bin_ws=None, tof_ws=event_ws_name, dspace_ws=None)

        # set tracker
        tracker.is_reduced = True

        # END-IF

        return event_ws_name, red_message

    def set_chopped_reduced_workspaces(self, run_number, slicer_key, workspace_name_list, append, compress=False):
        """
        set the chopped and reduced workspaces to reduction manager
        :param run_number:
        :param slicer_key:
        :param workspace_name_list:
        :param append:
        :param compress: if compress, then merge all the 2-bank workspace together   NOTE: using ConjoinWorkspaces???
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)

        # add files
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'
        error_messge = tracker.set_chopped_workspaces(workspace_name_list, append=append)

        if compress:
            target_ws_name = tracker.compressed_ws_name
            mantid_helper.make_compressed_reduced_workspace(
                workspace_name_list, target_workspace_name=target_ws_name)

        return error_messge

    def set_chopped_reduced_files(self, run_number, slicer_key, gsas_file_list, append):
        """
        set the reduced file
        :param run_number:
        :param slicer_key:
        :param gsas_file_list:
        :param append:
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'

        # add files
        tracker.set_reduced_files(gsas_file_list, append)

        return

    def set_reduced_workspaces(self, run_number, vdrive_bin_ws, tof_ws, dspace_ws):
        """
        set a run's reduced workspaces
        :param run_number: int
        :param vdrive_bin_ws: str
        :param tof_ws: str
        :param dspace_ws: str
        :return:
        """
        # check input
        if run_number not in self._reductionTrackDict:
            raise RuntimeError('Run number {0} has no ReductionTracker yet. Existing keys are {1}.'
                               ''.format(run_number, self._reductionTrackDict.keys()))

        try:
            self._reductionTrackDict[run_number].set_reduced_workspaces(
                vdrive_bin_ws, tof_ws, dspace_ws)
        except AssertionError as ass_err:
            raise AssertionError('ReductionManage unable to set reduced workspace for run {0} due to {1}.'
                                 ''.format(run_number, ass_err))
        # TRY-EXCEPT

        return


class DetectorCalibrationWorkspaces(object):
    """
    A simple workspace for detector instrument calibration workspaces
    """

    def __init__(self):
        """
        initialization: all workspaces shall be workspace names but not references to workspaces
        """
        self.calibration = None
        self.mask = None
        self.grouping = None
        self.vdrive_bins_dict = None    # for VDRIVE-GSAS binnings

    def __str__(self):
        """
        customized nice output
        :return:
        """
        nice = 'Calibration workspace: {}\nGrouping workspace: {}\nMask workspace: {}' \
               ''.format(self.calibration, self.grouping, self.mask)

        return nice
