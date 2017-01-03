################################################################################
# Manage the reduced VULCAN runs
################################################################################
import reduce_VULCAN
import mantid_helper

EVENT_WORKSPACE_ID = "EventWorkspace"


class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """
    FilterBadPulse = 1
    AlignAndFocus = 2
    NormaliseByCurrent = 3
    CalibratedByVanadium = 4

    def __init__(self, run_number):
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
        assert isinstance(run_number, int)

        # set up
        self._runNumber = run_number
        # FIXME - it is not clear whether it is better to use vanadium file name or vanadium run number
        self._vanadiumCalibrationRunNumber = None

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._vdriveWorkspace = None
        self._tofWorkspace = None
        self._dspaceWorkspace = None

        # status flag
        self._isReduced = False

        # initialize states of reduction beyond
        self._badPulseRemoved = False
        self._normalisedByCurrent = False
        self._correctedByVanadium = False

        return

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
        assert isinstance(state, bool), 'blabla 1423'
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
    def dpsace_worksapce(self):
        """
        Mantid binned DSpaceing workspace
        :return:
        """
        return self._dspaceWorkspace

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

    def set_reduced_workspaces(self, vdrive_bin_ws, tof_ws, dspace_ws):
        """

        :param vdrive_bin_ws:
        :param tof_ws:
        :param dspace_ws:
        :return:
        """
        # check workspaces existing
        assert mantid_helper.workspace_does_exist(vdrive_bin_ws), 'blabla'
        assert mantid_helper.workspace_does_exist(tof_ws), 'blabla'
        assert mantid_helper.workspace_does_exist(dspace_ws), 'blabla'
        dspace_ws_unit = mantid_helper.get_workspace_unit(dspace_ws)
        assert dspace_ws_unit == 'dSpacing',\
            'The unit of DSpace workspace {0} should be dSpacing but not {1}.'.format(str(dspace_ws), dspace_ws_unit)

        self._vdriveWorkspace = vdrive_bin_ws
        self._tofWorkspace = tof_ws
        self._dspaceWorkspace = dspace_ws

        self._isReduced = True

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

        return

    def chop_data(self, data_file, chop_manager, slice_key, output_dir):
        """

        :param data_file:
        :param chop_manager:
        :param slice_key:
        :param output_dir:
        :return:
        """
        split_ws_name, info_ws_name = chop_manager.get_split_workspace(slice_key)

        mantid_helper.split_event_data(raw_file_name=data_file,
                                       split_ws_name=split_ws_name,
                                       info_table_name=info_ws_name,
                                       target_ws_name=None,
                                       tof_correction=False,
                                       output_directory=output_dir,
                                       delete_split_ws=True)

        # TODO/ISSUE/57 - implement the code to manage output workspace and data

        return

    def get_event_workspace_name(self, run_number):
        """
        Get or generate the name of a raw event workspace
        Requirements: run number must be a positive integer
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int), 'blabla'
        assert run_number > 0, 'blabla'

        event_ws_name = '%s_%d_events' % (self._myInstrument, run_number)

        return event_ws_name

    def get_processed_vanadium(self, vanadium_run_number):
        """ Get processed vanadium data (workspace name)
        Purpose: Get process vanadium workspace (name) by vanadium run number
        Requirements: vanadium run number is a valid integer and it is reduced
        Guarantees: the workspace's name of the reduced vanadium is returned
        :param vanadium_run_number:
        :return:
        """
        # TODO/NEXT:
        raise NotImplementedError('Implement ASAP!')

    def get_reduced_runs(self):
        """
        Get the runs that have been reduced. It is just for information
        :return:  a list of run numbers
        """
        return_list = list()
        for run_number in self._reductionTrackDict.keys():
            tracker = self._reductionTrackDict[run_number]
            if tracker.is_reduced is True:
                return_list.append(run_number)

        return return_list

    def get_reduced_workspace(self, run_number, is_vdrive_bin, unit='TOF'):
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
        :param is_vdrive_bin:
        :param unit:
        :return: Workspace (success) or 2-tuple (False and error message)
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number must be integer but not %s.' % str(type(run_number))
        # get tracker
        assert run_number in self._reductionTrackDict, 'Run number {0} is not reduced.'.format(run_number)
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker), 'Stored tracker must be an instance of DataReductioTracker.'

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

        return return_ws_name

    def get_smoothed_vanadium(self, van_run_number):
        """
        Purpose:
            Get the smooth vanadium run (workspace) which has not been accepted.
        Requirements:

        Guarantees:

        :param van_run_number:
        :return:
        """
        # TODO/FIXME/ISSUE/55++ -- Required in next**2 step
        # Check requirements
        # assert isinstance(van_run_number, int)
        # assert self.does_van_ws_exist(van_run_number)
        #
        # # Call method to smooth vnadium
        # smooth_parameter = self._redctionParameter.vanadium_smooth_parameter
        # temp_van_ws_name = self._workspaceManager.get_vanadium_workspace_name('smooth')
        # mantid.SmoothVanadium(van_run_number, temp_van_ws_name, smooth_parameter)

        temp_van_ws_name = 'Not Implemented Yet!'

        return temp_van_ws_name

    def init_tracker(self, run_number):
        """ Initialize tracker
        :param run_number:
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number %s must be integer but not %s' % (str(run_number),
                                                                                          str(type(run_number)))

        # Initialize a new tracker
        if run_number not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number)
            self._reductionTrackDict[run_number] = new_tracker
        else:
            # existing tracker: double check
            assert isinstance(self._reductionTrackDict[run_number], DataReductionTracker),\
                'It is not DataReductionTracker but a {0}.'.format(type(self._reductionTrackDict[run_number]))

        return

    def reduce_chopped_data(self, ipts_number, run_number, src_file_name, chop_manager, slicer_key, output_dir):
        """

        :param run_number:
        :param chop_manager:
        :return:
        """
        # check inputs
        assert isinstance(ipts_number, int), 'IPTS number blabla 1329'
        assert isinstance(run_number, int), 'Input run number {0} must be an integer ' \
                                            'but not {1}.'.format(run_number, type(run_number))

        split_ws_name, info_ws_name = chop_manager.get_split_workspace(slicer_key)
        reduce_setup = reduce_VULCAN.ReductionSetup()

        reduce_setup.set_ipts_number(ipts_number)
        reduce_setup.set_run_number(run_number)
        reduce_setup.set_event_file(src_file_name)

        reduce_setup.set_output_dir(output_dir)
        reduce_setup.set_gsas_dir(output_dir, main_gsas=True)
        reduce_setup.is_full_reduction = False
        reduce_setup.set_default_calibration_files()

        # add splitter workspace and splitter information workspace
        reduce_setup.set_splitters(split_ws_name, info_ws_name)

        reducer = reduce_VULCAN.ReduceVulcanData(reduce_setup)
        reducer.execute_chop_reduction(clear_workspaces=False)

        # get the reduced file names and workspaces
        # TODO/ISSUE/57 - Implement ASAP

        return True, None

    def set_reduced_workspaces(self, run_number, vdrive_bin_ws, tof_ws, dspace_ws):
        """
        set a run's reduced workspaces
        :param run_number: int
        :param vdrive_bin_ws: str
        :param tof_ws: str
        :param dspace_ws: str
        :return:
        """
        # check
        assert isinstance(run_number, int), 'blabla'
        assert isinstance(vdrive_bin_ws, str) and isinstance(tof_ws, str) and isinstance(dspace_ws, str), 'blabla'

        self._reductionTrackDict[run_number].set_reduced_workspaces(vdrive_bin_ws, tof_ws, dspace_ws)

        return

