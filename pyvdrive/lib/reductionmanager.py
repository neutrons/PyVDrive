################################################################################
# Manage the reduced VULCAN runs
################################################################################
import os
import reduce_VULCAN
import mantid_helper
import chop_utility
import reduce_adv_chop
import mantid_reduction
import datatypeutility

EVENT_WORKSPACE_ID = "EventWorkspace"


class CalibrationManager(object):
    """
    A container and manager for calibration files loaded, number of banks of groupings and etc
    """
    def __init__(self):
        """
        initialization
        """
        self._calibration_dict = None
        self._vdrive_bin_ref_dict = None

        self._calibration_ws_name_list = list()
        self._grouping_ws_name_list = list()
        self._masking_ws_name_list = list()

        self._reference_container = dict()   # key: [location][num_banks][..]
        self._loaded_file_dict = dict()  # key: file name (full path).  value: tuple as path: location, number banks ...
        self._current_calibration_loc = None    #

        # set up
        self._init_vulcan_calibration_files()
        self._init_vdrive_binning_refs()


        return

    def _init_vulcan_calibration_files(self):
        """
        generate a dictionary for vulcan's hard coded calibration files
        :return:
        """
        base_calib_dir = '/SNS/VULCAN/shared/CALIBRATION'

        # hard coded list of available calibration file names
        pre_ned_setup = {3: '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'}

        ned_2017_setup = {3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                          7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_7bank.h5',
                          27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_27bank.h5'}

        ned_2018_setup = {3: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5'),
                          7: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_7bank.h5'),
                          27: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_27bank.h5')}

        self._calibration_dict = dict()
        self._calibration_dict['2010-01-01'] = pre_ned_setup
        self._calibration_dict['2017-06-01'] = ned_2017_setup
        self._calibration_dict['2018-05-31'] = ned_2018_setup

        return

    def _init_vdrive_binning_refs(self):
        """

        :return:
        """
        base_calib_dir = '/SNS/VULCAN/shared/CALIBRATION'

        # hard coded list of available calibration file names
        pre_ned_setup = '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vdrive_log_bin.dat'

        ned_2017_setup = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5'

        ned_2018_setup = os.path.join(base_calib_dir, '2018_6_1_CAL/vdrive_3bank_bin.h5')

        self._vdrive_bin_ref_dict = dict()
        self._vdrive_bin_ref_dict['2010-01-01'] = pre_ned_setup
        self._vdrive_bin_ref_dict['2017-06-01'] = ned_2017_setup
        self._vdrive_bin_ref_dict['2018-05-31'] = ned_2018_setup

        return

    def _init_focused_instruments(self):
        """
        set up the dictionary for the instrument geometry after focusing
        each detector (virtual) will have 3 value as L2, polar (2theta) and azimuthal (phi)
        and the angles are in unit as degree
        :return:
        """
        self._focus_instrument_dict = dict()
        self._focus_instrument_dict['L1'] = 43.753999999999998

        east_bank = [2.0, 90., 0.]
        west_bank = [2.0, -90., 0.]
        high_angle_bank = [2.0, 155., 0.]

        # 2 bank
        self._focus_instrument_dict[2] = {1: west_bank,
                                          2: east_bank}

        # 3 bank
        self._focus_instrument_dict[3] = {1: west_bank,
                                          2: east_bank,
                                          3: high_angle_bank}

        # 7 bank
        # TODO - 2018-07-18 Fill the blanks for all the focused banks
        self._focus_instrument_dict[7] = {7: high_angle_bank}

        # 27 banks
        # TODO - 2018-07-18 Fill the blanks for all the focused banks
        self._focus_instrument_dict[27] = {}

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

    def get_calibration_file(self, year_month_date, num_banks):
        """
        get the calibration file by date and number of banks
        :param year_month_date:
        :param num_banks:
        :return:
        """
        datatypeutility.check_string_variable('YYYY-MM-DD string', year_month_date)
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 28))

        # search the previous date
        # check format first
        if len(year_month_date) != 10 or year_month_date.count('-') != 2:
            raise RuntimeError('Year-Month-Date string must be of format YYYY-MM-DD but not {0}'
                               ''.format(year_month_date))

        # search the list
        date_list = sorted(self._calibration_dict.keys())
        if year_month_date < date_list[0]:
            raise RuntimeError('Input year-month-date {0} is too early comparing to {1}'
                               ''.format(year_month_date, date_list[0]))

        # do a brute force search (as there are only very few of them)
        cal_date_index = None
        for i_date in range(len(date_list)-1, 0, -1):
            if year_month_date > date_list[i_date]:
                cal_date_index = date_list[i_date]
                break
            # END-IF
        # END-FOR

        calibration_file_name = self._calibration_dict[cal_date_index][num_banks]

        return cal_date_index, calibration_file_name

    def is_file_load(self, cal_file_name):
        """
        check whether a calibration file loaded
        :param cal_file_name:
        :return:
        """
        datatypeutility.check_string_variable('Calibration file name', cal_file_name)

        return cal_file_name in self._loaded_file_dict

    def load_calibration_file(self, calibration_file_name, num_banks, ref_ws_name):
        """

        :return:
        """
        datatypeutility.check_file_name(calibration_file_name, check_exist=True, note='Calibration file')

        base_name = self.get_base_name(calibration_file_name, num_banks)
        mantid_reduction.load_diff_cal_file(ref_ws_name, calibration_file_name, base_name)

        # record
        location = os.path.dirname(calibration_file_name)
        raise NotImplementedError('ASAP')

        return



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
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not {1}.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))

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
            self._compressedChoppedWorkspaceName = 'Chopped_{0}_Slicer_{1}.'.format(self._runNumber, self._slicerKey)

        return self._compressedChoppedWorkspaceName

    @property
    def dpsace_worksapce(self):
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
        assert isinstance(value, str), 'Input workspace name must be string but not %s.' % str(type(value))
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
        assert isinstance(value, bool), 'Input for is_reduced must be a boolean but not %s.' % str(type(value))
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
        assert isinstance(workspace_name_list, list), 'Input list of workspaces names {1} must be list but not a {1}.' \
                                                      ''.format(workspace_name_list, type(workspace_name_list))

        if self._choppedWorkspaceNameList is None or not append:
            self._choppedWorkspaceNameList = workspace_name_list[:]
        else:
            self._choppedWorkspaceNameList.extend(workspace_name_list)

        return

    def set_chopped_nexus_files(self, chopped_file_list, append=True):
        """ set NeXus files that are saved from chopped workspace to this tracker
        """
        # check input
        assert isinstance(chopped_file_list, list), 'Chopped NeXus files {0} must be given by list but not {1}.' \
                                                    ''.format(chopped_file_list, type(chopped_file_list))

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
        assert mantid_helper.workspace_does_exist(vdrive_bin_ws), 'VDrive-binned workspace {0} does not exist ' \
                                                                  'in ADS'.format(vdrive_bin_ws)
        assert mantid_helper.workspace_does_exist(tof_ws), 'Mantid-binned TOF workspace {0} does not exist in ADS.' \
                                                           ''.format(tof_ws)
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

        self._isReduced = True

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
        assert isinstance(status, bool), 'Reduction status must be given by bool but not {0}'.format(type(status))
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
        assert isinstance(instrument, str), 'Input instrument must be of type str'
        instrument = instrument.upper()
        assert instrument in ReductionManager.SUPPORTED_INSTRUMENT, \
            'Instrument %s is not in the supported instruments (%s).' % (instrument,
                                                                         ReductionManager.SUPPORTED_INSTRUMENT)

        # Set up including default
        self._myInstrument = instrument

        # reduction tracker: key = run number (integer), value = DataReductionTracker
        self._reductionTrackDict = dict()

        # simplified reduced workspace manager.  key = run number, value = workspace name
        self._runFocusedWorkspaceDict = dict()

        # calibration file and workspaces management
        self._calibrationFileManager = CalibrationManager()   # key = calibration file name

        return

    def add_reduced_workspace(self, run_number, out_ws_name, binning_parameters=None):
        """
        add a reduced workspace
        :param run_number:
        :param out_ws_name:
        :param binning_parameters:
        :return:
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_string_variable('Reduced workspace name', out_ws_name)

        # add
        if run_number not in self._runFocusedWorkspaceDict:
            self._runFocusedWorkspaceDict = dict()

        if binning_parameters is not None:
            binning_key = str(binning_parameters)
        else:
            binning_key = None

        self._runFocusedWorkspaceDict[run_number][binning_key] = out_ws_name

        return

    # TEST NOW - Goal: This method will replace chop_run() and chop_reduce_run()
    def chop_vulcan_run(self, ipts_number, run_number, raw_file_name, split_ws_name, split_info_name, slice_key,
                        output_directory, reduce_data_flag, save_chopped_nexus,
                        tof_correction, vanadium):
        """
        chop VULCAN run with reducing to GSAS file as an option
        :param ipts_number: IPTS number (serving as key for reference)
        :param run_number: Run number (serving as key for reference)
        :param raw_file_name:
        :param split_ws_name:
        :param split_info_name:
        :param slice_key: a general keyword to refer from the reduction tracker
        :param output_directory: string for directory or None for saving to archive
        :param vanadium: vanadium run number of None for not normalizing
        :param tof_correction:
        :return: 2-tuple.  (1) boolean as status  (2) error message
        """
        if tof_correction:
            raise NotImplementedError('[WARNING] TOF correction is not implemented yet.')

        # set up reduction parameters
        reduction_setup = reduce_VULCAN.ReductionSetup()
        reduction_setup.set_ipts_number(ipts_number)
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(raw_file_name)

        # splitters workspace suite
        reduction_setup.set_splitters(split_ws_name, split_info_name)

        # define chop processor
        chop_reducer = reduce_adv_chop.AdvancedChopReduce(reduction_setup)

        # option to save to archive
        if output_directory is None:
            # save to SNS archive.
            reduction_setup.set_chopped_output_to_archive(create_parent_directories=True)
        else:
            # save to user-specified directories. GSAS and NeXus will be in the same directory
            reduction_setup.set_output_dir(output_directory)
            reduction_setup.set_gsas_dir(output_directory, main_gsas=True)
            reduction_setup.set_chopped_nexus_dir(output_directory)
        # END-IF-ELSE

        if reduce_data_flag:
            # chop and reduce chopped data to GSAS
            # set up the flag to save chopped raw data
            reduction_setup.save_chopped_workspace = save_chopped_nexus

            # set the flag for not being an auto reduction
            reduction_setup.is_auto_reduction_service = False
            # TODO FIXME ASAP3 - Need to pass number of banks to focus on
            reduction_setup.set_default_calibration_files(num_focused_banks=3)

            # set up reducer
            reduction_setup.process_configurations()

            # set up reduction tracker
            tracker = self.init_tracker(ipts_number, run_number, slice_key)

            # reduce data
            status, message = chop_reducer.execute_chop_reduction_v2(clear_workspaces=False)

            # set up the reduced file names and workspaces and add to reduction tracker dictionary
            tracker.set_reduction_status(status, message, True)

            reduced, workspace_name_list = chop_reducer.get_reduced_workspaces(chopped=True)
            self.set_chopped_reduced_workspaces(run_number, slice_key, workspace_name_list, append=True)
            self.set_chopped_reduced_files(run_number, slice_key, chop_reducer.get_reduced_files(), append=True)

        else:
            # chop data only without reduction
            status, ret_obj = chop_reducer.chop_data()

            if not status:
                return False, 'Unable to chop run {0} due to {1}.'.format(run_number, ret_obj)

            # get chopped workspaces' names, saved NeXus file name; check them and store to lists
            chopped_ws_name_list = list()
            chopped_file_list = list()
            for file_name, ws_name in ret_obj:
                if file_name is not None:
                    chopped_file_list.append(file_name)
                if isinstance(ws_name, str) and mantid_helper.workspace_does_exist(ws_name):
                    chopped_ws_name_list.append(ws_name)
            # END-FOR

            # initialize tracker
            tracker = self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=slice_key)

            tracker.is_reduced = False
            tracker.is_chopped = True
            if len(chopped_ws_name_list) > 0:
                tracker.set_chopped_workspaces(chopped_ws_name_list, append=True)
            if len(chopped_file_list) > 0:
                tracker.set_chopped_nexus_files(chopped_file_list, append=True)
        # END-IF

        return True, None

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
        assert unit is None or isinstance(unit, str), 'Output data unit must be either None (default) or a string.'

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

    def get_reduced_run(self, ipts_number, run_number):
        """
        get the workspace key to a reduced run
        :param ipts_number:
        :param run_number:
        :return:
        """
        if (ipts_number, run_number) in self._reductionTrackDict:
            return ipts_number, run_number

        return None

    def get_reduced_runs(self, with_ipts=False):
        """
        Get the runs that have been reduced. It is just for information
        :return:  a list of run numbers
        """
        return_list = list()

        # from tracker
        for run_number in self._reductionTrackDict.keys():
            tracker = self._reductionTrackDict[run_number]
            if tracker.is_reduced is True:
                if with_ipts:
                    new_item = run_number, tracker.ipts_number
                else:
                    new_item = run_number

                return_list.append(new_item)
            # END-IF
        # END-FOR

        # from simple reduced runs manager
        run_number_list = self._runFocusedWorkspaceDict.keys()

        # combine
        return_list = list(set(return_list).union(set(run_number_list)))

        return return_list

    def get_reduced_workspace(self, run_number, binning_params=None, is_vdrive_bin=True, unit='TOF'):
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
        :return: Workspace (success) or 2-tuple (False and error message)
        """
        # Check requirements
        import datatypeutility
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        if binning_params is not None:
            datatypeutility.check_string_variable('Binning parameter (string)', binning_params)

        # where is this run?
        if run_number in self._runFocusedWorkspaceDict:
            # simple reduce
            return_ws_name = self._runFocusedWorkspaceDict[run_number][binning_params]
        else:
            # full reduction
            # get tracker
            assert run_number in self._reductionTrackDict, 'Run number {0} is not reduced.'.format(run_number)
            tracker = self._reductionTrackDict[run_number]
            assert isinstance(tracker, DataReductionTracker), \
                'Stored tracker must be an instance of DataReductioTracker.'

            if is_vdrive_bin and unit != 'TOF':
                raise RuntimeError('It is possible to get a VDrive-binned workspace in unit {0} other than TOF.'
                                   ''.format(unit))
            elif unit != 'TOF' and unit.lower() != 'dspace':
                raise RuntimeError('Unit {0} is not supported.'.format(unit))

            if is_vdrive_bin:
                return_ws_name = tracker.vdrive_workspace
            elif unit == 'TOF':
                return_ws_name = tracker.tof_workspace
            else:
                return_ws_name = tracker.dpsace_worksapce
            # END-IF-ELSE
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

    def has_run(self, run_number):
        """
        check whether a certain run number is reduced and stored
        :param run_number:
        :return:
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))

        has = False
        if run_number in self._runFocusedWorkspaceDict:
            has = True
        elif run_number in self._reductionTrackDict:
            has = True

        return has

    def init_tracker(self, ipts_number, run_number, slicer_key=None):
        """ Initialize tracker
        :param ipts_number:
        :param run_number:
        :param slicer_key: if not specified, then the reduction is without chopping
        :return: a DataReductionTracker object that is just created and initialized
        """
        # Check requirements
        assert isinstance(ipts_number, int) or ipts_number is None, 'IPTS number {0}  must be an integer or None but ' \
                                                                    'not a {1}.'.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number %s must be integer but not %s' % (str(run_number),
                                                                                          str(type(run_number)))

        # Initialize a new tracker
        if slicer_key is None:
            tracker_key = run_number
        else:
            tracker_key = run_number, slicer_key

        if ipts_number is None:
            raise NotImplementedError('Figure out how to track a reduction without a good IPTS number!')

        if tracker_key not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number, ipts_number)
            new_tracker.set_slicer_key(slicer_key)
            self._reductionTrackDict[tracker_key] = new_tracker
        else:
            # existing tracker: double check
            assert isinstance(self._reductionTrackDict[tracker_key], DataReductionTracker),\
                'It is not DataReductionTracker but a {0}.'.format(type(self._reductionTrackDict[tracker_key]))
            # NOTE: new_tracker here is not new tracker at all!
            new_tracker = self._reductionTrackDict[tracker_key]

        return new_tracker

    def check_calibration_mask_grouping(self, run_start_date, bank_numbers):
        """
        check whether the calibration file is loaded. If not then load the files
        :param run_start_date: string in YYYY-MM-DD format
        :param bank_numbers:
        :return: status, calibration workspace name, mask workspace name
        """
        # TODO - 20180812 - Make this part work! Now it is a temporary solution - FIXME

        # 1. use run_start_date (str) to search in the calibration date time string (TODO)

        # 2. locate the calibration file key (TODO)

        # 3. check whether the workspaces are loaded or not (workspace =? None) (TODO)

        # # check calibration
        # if calibration_file is None and self._default_calibration_ws_name is None:
        #     # no calibration
        #     self.load_default_calibration_file(num_banks)
        # elif calibration_file is not None:
        #     self.load_calibration_file(calibration_file, num_banks)
        # elif user_grouping_file_name is not None:
        #     self.load_user_grouping_file(user_grouping_file_name)
        #
        # return calibration_ws_name, mask_ws_name, grouping_ws_name

        return False, None, None

    def load_calibration_file(self, run_start_date, ref_ws_name, bank_numbers):
        """ load a calibration file according to its start date and number of banks
        :param run_start_date:
        :param ref_ws_name:
        :param bank_numbers:
        :return:
        """
        # TODO - 20180818 - It is not in a good shape to have the all the calibration file managed!

        cal_date_key, calibration_file = self._calibrationFileManager.get_calibration_file(run_start_date, bank_numbers)

        calib_key = self._calibrationFileManager.load_calibration_file(calibration_file, ref_ws_name)

        calibration_ws_name, mask_ws_name, grouping_ws_name = self._calibrationFileManager.get_workspaces(calib_key)

        return calibration_ws_name, mask_ws_name, grouping_ws_name


    # TODO - 20180713 - Find out how to reuse codes from vulcan_slice_reduce.SliceFocusVulcan
    def reduce_event_nexus(self, run_number, event_nexus_name, target_unit,  binning_parameters, convert_to_matrix,
                           num_banks):
        """ reduce event workspace

        :param event_nexus_name:
        :param target_unit:
        :param binning_parameters:
        :param convert_to_matrix:
        :return:
        """
        # Load data
        event_ws_name = self.get_event_workspace_name(run_number=run_number)
        mantid_helper.load_nexus(event_nexus_name, event_ws_name, meta_data_only=False)

        # get start time: it is not convenient to get date/year/month from datetime64.
        # use the simple but fragile method first
        run_start_time = mantid_helper.get_run_start(event_ws_name, time_unit=None)
        if run_start_time.__class__.__name__ == 'mantid.kernel._kernel.DateAndTime':
            run_start_date = str(run_start_time).split('T')[0]
        else:
            raise NotImplementedError('Run start time from Mantid TSP is not DateAndTime anymore, '
                                      'but is {0}'.format(run_start_time.__class__.__name__))

        # TODO - 20180712 - Continue to implement!
        # use 'run_start' or 'start_time' to determine the calibration file!
        status, calib_ws_name, mask_ws_name, group_ws_name = self.check_calibration_mask_grouping(run_start_date,
                                                                                                  num_banks)
        if not status:
            calib_ws_name, mask_ws_name, group_ws_name = self.load_calibration_file(run_start_date, event_nexus_name,
                                                                                    num_banks)

        self.reduce_workspace(event_ws_name, event_ws_name, keep_raw_ws=False)

        return

    # TODO FIXME - From here!  Reduction 2.0!
    def reduce_workspace(self, event_ws_name, output_ws_name, binning_params, target_unit,
                         calibration_file_name, user_grouping_file_name, keep_raw_ws,
                         convert_to_matrix):
        """ focus workspace

        :param event_ws_name:
        :param output_ws_name:
        :param keep_raw_ws:
        :param calibration_file_name: standard calibration file name
        :return:
        """
        def check_binning_parameter_range(x_min, x_max, target_unit):
            """
            check whether range of X values of binning makes sense with target unit
            :param x_min:
            :param x_max:
            :param target_unit:
            :return:
            """
            if target_unit == 'dSpacing':
                if not 0 < x_min < x_max < 20:
                    raise RuntimeError('For dSpacing, X range ({0}, {1}) does not make sense'
                                       ''.format(x_min, x_max))
            elif target_unit == 'TOF':
                if not 1000 < x_min < x_max < 1000000:
                    raise RuntimeError('For TOF, X range ({0}, {1}) does not make sense'
                                       ''.format(x_min, x_max))
            else:
                raise RuntimeError('Impossible case')

            return

        # check inputs
        datatypeutility.check_string_variable('Target unit', target_unit, ['TOF', 'dSpacing'])

        if binning_params is None:
            # do nothing
            pass
        else:
            datatypeutility.check_tuple('Binning parameters', binning_params)
            if len(binning_params) == 1:
                # it is fine
                pass
            elif len(binning_params) == 3:
                # check against the unit
                check_binning_parameter_range(binning_params[0], binning_params[1], target_unit)
            else:
                # unsupported number of binning parameters
                raise RuntimeError('Binning parameters {0} with {1} items are not supported.'
                                   ''.format(binning_params, len(binning_params)))
        # END-IF-ELSE

        # check and load calibration workspace
        datatypeutility.check_file_name(calibration_file_name, check_exist=True, note='Calibration file')
        if calibration_file_name not in self._calibration_workspace_container:
            raise NotImplementedError('ASAP')

        # align and focus
        mantid_reduction.align_and_focus_event_ws(event_ws_name, output_ws_name, binning_params,
                                                  calibration_file_name, user_grouping_file_name,
                                                  keep_raw_ws, reduction_params_dict=reduction_param_dict,
                                                  convert_to_matrix=False)

        return

    def process_vulcan_ipts_run(self, ipts_number, run_number, event_file, output_directory, merge_banks, vanadium=False,
                                vanadium_tuple=None, gsas=True, standard_sample_tuple=None, binning_parameters=None,
                                num_banks=3):
        """
        Reduce run with selected options
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
                'Input standard sample-tuple must be a tuple with length 3 but not a {0}.'.format(standard_sample_tuple)
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
            self._reductionTrackDict[run_number].set_reduced_files(reducer.get_reduced_files(), append=False)
            # set workspaces
            status, ret_obj = reducer.get_reduced_workspaces(chopped=False)
            if status:
                # it may not have the workspace because
                vdrive_ws, tof_ws, d_ws = ret_obj
                self.set_reduced_workspaces(run_number, vdrive_ws, tof_ws, d_ws)

        # END-IF

        return reduce_good, message

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
        tracker.set_chopped_workspaces(workspace_name_list, append=append)

        if compress:
            target_ws_name = tracker.compressed_ws_name
            mantid_helper.make_compressed_reduced_workspace(workspace_name_list, target_workspace_name=target_ws_name)

        return

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
            self._reductionTrackDict[run_number].set_reduced_workspaces(vdrive_bin_ws, tof_ws, dspace_ws)
        except AssertionError as ass_err:
            raise AssertionError('ReductionManage unable to set reduced workspace for run {0} due to {1}.'
                                 ''.format(run_number, ass_err))
        # TRY-EXCEPT

        return
