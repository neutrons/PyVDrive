################################################################################
#
# Modified SNS Powder Reduction
#
# Example:
# AlignAndFocusPowder(InputWorkspace='VULCAN_80239_0', OutputWorkspace='VULCAN_80239_0',
#        CalFileName='/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal',
#        GroupingWorkspace='VULCAN_group',
#        CalibrationWorkspace='VULCAN_cal',
#        MaskWorkspace='VULCAN_mask',
#        Params='-0.001',
#        CompressTolerance=0,
#        CropWavelengthMax=0,
#        PrimaryFlightPath=43.753999999999998,
#        SpectrumIDs='1,2',
#        L2='2.00944,2.00944',
#        Polar='90.122,90.122',
#        Azimuthal='0,0', ReductionProperties='__snspowderreduction')
# RenameWorkspace(InputWorkspace='VULCAN_80239_0', OutputWorkspace='VULCAN_80239')
# CompressEvents(InputWorkspace='VULCAN_80239', OutputWorkspace='VULCAN_80239', Tolerance=0)
# PDDetermineCharacterizations(InputWorkspace='VULCAN_80239', Characterizations='characterizations', ReductionProperties='__snspowderreduction', FrequencyLogNames='skf1.speed', WaveLengthLogNames='skf12.lambda')
# CompressEvents(InputWorkspace='VULCAN_80239', OutputWorkspace='VULCAN_80239', Tolerance=0)
# GeneratePythonScript(InputWorkspace='VULCAN_80239', Filename='/home/wzz/Projects/MantidTests/Instruments_Specific/Vulcan/Reduction/temp/VULCAN_80239.py')
# ConvertUnits(InputWorkspace='VULCAN_80239', OutputWorkspace='VULCAN_80239', Target='dSpacing')
#
################################################################################
import sys
import os

# FIXME : This is for local development only!
homedir = os.path.expanduser('~')
mantidpath = os.path.join(homedir, 'Mantid/Code/debug/bin/')
sys.path.append(mantidpath)

import mantid_helper
import mantid
import mantid.simpleapi as mantidapi

EVENT_WORKSPACE_ID = "EventWorkspace"

DEBUGMODE = True
DEBUGDIR = os.path.join(homedir, 'Temp')


class PowderReductionParameters(object):
    """ Class to contain align and focus parameters
    Many of them server as default values
    """
    # FIXME/TODO/NOW Improve & refine!
    def __init__(self):
        """ Initialization
        """
        # binning parameters
        self._binStep = -0.001
        self._tofMin = None
        self._tofMax = None

        # events related

        refLogTofFilename = "/SNS/VULCAN/shared/autoreduce/vdrive_log_bin.dat"
        calibrationfilename = "/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal"
        characterfilename = "/SNS/VULCAN/shared/autoreduce/VULCAN_Characterization_2Banks_v2.txt"

        self._focusFileName = calibrationfilename
        self._preserveEvents = True
        self._LRef              = 0   # default = 0
        self._DIFCref           = 0
        self._compressTolerance = 0.01
        self._removePromptPulseWidth = 0.0
        self._lowResTOFoffset   = -1
        self._wavelengthMin     = 0.0

        self._filterBadPulse = False
        self._normalizeByCurrent = True
        self._calibrateByVanadium = False

        return

    @property
    def bin_step(self):
        """
        Purpose:
            Get the binning step
        Guarantees:
        :return:
        """
        return self._binStep

    @bin_step.setter
    def bin_step(self, value):
        """
        Purpose: Set up bin size (or say bin step)
        Requirements: input value must be a float
        :param value:
        :return:
        """
        assert isinstance(value, float)
        self._binStep = value

        return

    @property
    def calibrate_by_vanadium(self):
        """

        :return:
        """
        return self._calibrateByVanadium

    @property
    def compress_tolerance(self):
        """
        :return: value of compress tolerance
        """
        return self._compressTolerance

    @compress_tolerance.setter
    def compress_tolerance(self, value):
        """ Set value to _compressTolerance
        Requirements: positive float
        :return:
        """
        assert isinstance(value, float)
        assert value > 0

        self._compressTolerance = value

        return

    @property
    def filter_bad_pulse(self):
        """
        Get the status whether bad pulse will be filtered
        :return: boolean
        """
        return self._filterBadPulse

    @filter_bad_pulse.setter
    def filter_bad_pulse(self, value):
        """
        Set the flag whether bad pulse shall be filtered
        :param value:
        :return:
        """
        isinstance(value, bool)

        self._filterBadPulse = value

        return

    @property
    def focus_calibration_file(self):
        """ Get time focusing calibration file.
        :return:
        """
        return self._focusFileName

    @focus_calibration_file.setter
    def focus_calibration_file(self, value):
        """ Set time focusing calibration file
        Requirements:
        - value must be an existing calibration file
        :param value:
        :return:
        """
        assert isinstance(value, str)
        assert os.path.exists(value)

        self._focusFileName = value

    @property
    def min_tof(self):
        """ Return mininum TOF
        :return:
        """
        return self._tofMin

    @min_tof.setter
    def min_tof(self, value):
        """
        Purpose: set up the minimum TOF value
        Requirements: input value must be either None for automatic min value or a postive float number,
        which is smaller than maxTOF if is set up
        :return:
        """
        # check requirements
        assert (value is None) or isinstance(value, float)

        # set up for None issue
        if value is None:
            # auto mode
            self._tofMin = None
        else:
            # explicit set up
            assert value > 0

            if self._tofMax is None:
                self._tofMin = value
            else:
                assert value < self._tofMax
                self._tofMin = value
            # END-IF-ELSE
        # END-IF

        return

    @property
    def max_tof(self):
        """ Return maximum TOF
        :return:
        """
        return self._tofMax

    @max_tof.setter
    def max_tof(self, value):
        """
        Purpose: set up the maximum TOF value
        Requirements: input value must be either None for automatic min value or a postive float number,
        which is smaller than maxTOF if is set up
        :return:
        """
        # check requirements
        assert (value is None) or isinstance(value, float)

        # set up for None issue
        if value is None:
            # auto mode
            self._tofMax = None
        else:
            # explicit set up
            assert value > 0

            if self._tofMin is None:
                self._tofMax = value
            else:
                assert value > self._tofMin
                self._tofMax = value
            # END-IF-ELSE
        # END-IF

        return

    @property
    def normalize_by_current(self):
        """

        :return:
        """
        return self._normalizeByCurrent

    @property
    def preserve_events(self):
        """
        Return the flag whether events will be preserved during reduction
        :return:
        """
        return self._preserveEvents

    @preserve_events.setter
    def preserve_events(self, value):
        """
        Set the flag to preserve events during reduciton
        Requirements: value must be bool
        :param value:
        :return:
        """
        assert isinstance(value, bool)

        self._preserveEvents = value

        return

    def form_binning_parameter(self):
        """
        form the binning parameter for Mantid's input
        :return: string, either as 'min_tof, bin_step, max_tof' or 'bin_step'
        """
        # Check
        assert isinstance(self._binStep, float)

        if self._tofMin is None or self._tofMax is None:
            bin_par = '%.7f' % self._binStep
        else:
            bin_par = '%.7f, %.7f, %.7f' % (self._tofMin, self._binStep, self._tofMax)

        print '[DB-BAT] binning parameter is [%s]' % bin_par

        return bin_par

    def set_from_dictionary(self, param_dict):
        """ Set reduction parameters' values from a dictionary
        :param param_dict:
        :return:
        """
        # Check requirements
        assert isinstance(param_dict, dict), 'Input must be a dictionary but not %s.' % str(type(param_dict))

        # Set
        for param_name in param_dict:
            if param_name in dir(self):
                setattr(self, param_name, param_dict[param_name])
            elif param_name in self.__dict__:
                setattr(self, param_name, param_dict[param_name])
            else:
                print '[Warning] Parameter %s is not an attribute for ' \
                      'reduction parameter' % param_name

        return


class ReductionHistory(object):
    """
    Class to describe the reduction history on one data set

    The default history is 'being loaded'
    """
    FilterBadPulse = 1
    AlignAndFocus = 2
    NormaliseByCurrent = 3
    CalibratedByVanadium = 4

    def __init__(self, workspace_name=None):
        """
        The key to a reduction history is its workspace name
        :param workspace_name:
        :return:
        """
        if workspace_name is not None:
            assert isinstance(workspace_name, str), 'Workspace name must be a string.'
            assert mantid_helper.workspace_does_exist(workspace_name), 'Workspace %s ' \
                                                                       'does not exist.' % workspace_name
            self._workspaceName = workspace_name

        self._isFocused = False
        self._badPulseRemoved = False
        self._normalisedByCurrent = False
        self._correctedByVanadium = False

        return

    @property
    def is_raw(self):
        """
        Show the status whether the workspace has never been processed
        :return:
        """
        if self._isFocused is True or self._badPulseRemoved is True:
            return False
        return True

    @property
    def is_focused(self):
        """
        Whether
        :return:
        """
        return self._isFocused

    def exec_focused(self):
        """

        :return:
        """
        assert self._isFocused is False, 'A focused workspace cannot be focused again.'

        self._isFocused = True

    @property
    def is_corrected_by_vanadium(self):
        """

        :return:
        """
        return self._correctedByVanadium

    def set(self, history):
        """
        Set history
        Requirements: history must be an integer for enum of history
        :param history:
        :return:
        """
        # Check requirements
        assert isinstance(history, int)

        # Set
        if history == ReductionHistory.AlignAndFocus:
            self._isFocused = True
        elif history == ReductionHistory.FilterBadPulse:
            self._badPulseRemoved = True
        elif history == ReductionHistory.NormaliseByCurrent:
            self._normalisedByCurrent = True
        elif history == ReductionHistory.CalibratedByVanadium:
            self._correctedByVanadium = True
        else:
            raise RuntimeError('History with value %d is not defined.' % history)

        return


class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """
    def __init__(self, run_number, file_path, vanadium_calibration):
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
        assert isinstance(file_path, str)
        assert vanadium_calibration is None or isinstance(vanadium_calibration, str)

        # set up
        self._runNumber = run_number
        self._filePath = file_path
        # FIXME - it is not clear whether it is better to use vanadium file name or vanadium run number
        self._vanadiumCalibrationRunNumber = vanadium_calibration

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._operationsOnEventWS = list()

        # status flag
        self._myHistory = ReductionHistory()
        self._isReduced = False

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
    def run_number(self):
        """ Read only to return the run number that this tracker
        :return:
        """
        return self._runNumber

    @property
    def file_path(self):
        """ Read only
        :return:
        """
        return self._filePath

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

    def add_history(self, reduction_history):
        """
        Add reduction history
        Purpose:
        Requirements: the reduction history must be a valid
        Guarantees:
        :param reduction_history: a reduction history defined in ReductionHistory
        :return:
        """
        # Check requirements
        assert isinstance(reduction_history, int), 'Reduction history must be an integer but not %s.' % \
                                                   str(type(reduction_history))

        # Set
        if reduction_history == ReductionHistory.AlignAndFocus:
            self._isReduced = True

        self._myHistory.set(reduction_history)

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

        # Reduction parameters
        self._reductionParameters = PowderReductionParameters()

        # Set up including default
        self._myInstrument = instrument
        self._reductionTrackDict = dict()

        # time focusing calibration file
        self._focusCalibrationFile = None

        # Cached workspaces
        self._myOffsetWorkspaceName = None
        self._myGroupWorkspaceName = None
        self._myMaskWorkspaceName = None
        self._myCalibrationWorkspaceName = None

        return

    def get_event_workspace_name(self, run_number):
        """
        Get or generate the name of a run
        Requirements: run number must be a positive integer
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int)
        assert run_number > 0

        event_ws_name = '%s_%d_events' % (self._myInstrument, run_number)

        return event_ws_name

    def get_processed_vanadium(self, vanadium_run_number):
        """ Get processed vanadium data (workspace name)
        Purpose:

        Requirements:

        Guarantees

        :param vanadium_run_number:
        :return:
        """
        # TODO/NOW/ ... ...
        return self._processedVanadiumWSDict[vanadium_run_number]

    def get_reduced_runs(self):
        """
        Get the runs that have been reduced. It is just for information
        :return:
        """
        return_list = list()
        for run_number in self._reductionTrackDict.keys():
            tracker = self._reductionTrackDict[run_number]
            if tracker.is_reduced is True:
                return_list.append(run_number)

        return return_list

    def get_reduced_workspace(self, run_number, unit='TOF'):
        """ Get the reduced matrix workspace
        Requirements:
            1. Specified run is correctly reduced;
        Guarantees:
            2. Return reduced workspace's name
        Arguments:
         - unit :: target unit; If None, then no need to convert unit
        :param run_number:
        :param unit:
        :param listindex:
        :return: Workspace (success) or 2-tuple (False and error message)
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number must be integer but not %s.' % str(type(run_number))
        # get tracker
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker)

        reduced_ws_name = tracker.event_workspace_name

        # Convert unit
        self.mtd_convert_units(reduced_ws_name, unit)

        return reduced_ws_name

    def mtd_align_and_focus(self, event_ws_name):
        """ Align and focus raw event workspaces: the original workspace will be replaced
        Purpose:
            Run Mantid.AlignAndFocus() by current parameters
        Requirements:
            Input event_wksp is not None
            Output workspace name is string
            All requirements for align and focus in Mantid is satisifed
        Guarantees:
            Event workspace is reduced
        :param event_ws_name:
        :return: focused event workspace
        """
        # Check requirement
        assert isinstance(event_ws_name, str)
        event_ws = mantid_helper.retrieve_workspace(event_ws_name)

        assert event_ws.id() == EVENT_WORKSPACE_ID, \
            'Input must be an EventWorkspace for align and focus. Current input is %s' % event_wksp.id()
        assert isinstance(self._reductionParameters, PowderReductionParameters), \
            'Input parameter must be of an instance of PowderReductionParameters'

        assert isinstance(self._myGroupWorkspaceName, str)
        assert mantid_helper.workspace_does_exist(self._myGroupWorkspaceName)
        assert isinstance(self._myOffsetWorkspaceName, str)
        assert mantid_helper.workspace_does_exist(self._myOffsetWorkspaceName)

        # Execute algorithm AlignAndFocusPowder()
        # Unused properties: DMin, DMax, TMin, TMax, MaskBinTable,
        user_geometry_dict = dict()
        if self._reductionParameters.min_tof is None or self._reductionParameters.max_tof is None:
            # if TOF range is not set up, use default min and max
            user_geometry_dict['DMin'] = 0.5
            user_geometry_dict['DMax'] = 5.5

        # FIXME - Need to find out what it is in __snspowderreduction
        mantidapi.AlignAndFocusPowder(InputWorkspace=event_ws_name,
                                      OutputWorkspace=event_ws_name,   # in-place align and focus
                                      GroupingWorkspace=self._myGroupWorkspaceName,
                                      OffsetsWorkspace=self._myOffsetWorkspaceName,
                                      CalibrationWorkspace=self._myCalibrationWorkspaceName,
                                      MaskWorkspace=None,  # FIXME - NO SURE THIS WILL WORK!
                                      Params=self._reductionParameters.form_binning_parameter(),
                                      PreserveEvents=self._reductionParameters.preserve_events,
                                      RemovePromptPulseWidth=0,  # Fixed to 0
                                      CompressTolerance=self._reductionParameters.compress_tolerance,
                                      # 0.01 as default
                                      Dspacing=True,            # fix the option
                                      UnwrapRef=0,              # do not use = 0
                                      LowResRef=0,              # do not use  = 0
                                      CropWavelengthMin=0,      # no in use = 0
                                      CropWavelengthMax=0,
                                      LowResSpectrumOffset=-1,  # powgen's option. not used by vulcan
                                      PrimaryFlightPath=43.753999999999998,
                                      SpectrumIDs='1,2',
                                      L2='2.00944,2.00944',
                                      Polar='90.122,90.122',
                                      Azimuthal='0,0',
                                      ReductionProperties='__snspowderreduction',
                                      **user_geometry_dict)

        # Check
        out_ws = mantid_helper.retrieve_workspace(event_ws_name)
        assert out_ws is not None

        return True

    @staticmethod
    def mtd_compress_events(event_ws_name, tolerance=0.01):
        """ Call Mantid's CompressEvents algorithm
        :param event_ws_name:
        :param tolerance: default as 0.01 as 10ns
        :return:
        """
        # Check requirements
        assert isinstance(event_ws_name, str), 'Input event workspace name is not a string,' \
                                               'but is a %s.' % str(type(event_ws_name))
        event_ws = mantid_helper.retrieve_workspace(event_ws_name)
        assert mantid_helper.is_event_workspace(event_ws)

        mantidapi.CompressEvents(InputWorkspace=event_ws_name,
                                 OutputWorkspace=event_ws_name,
                                 Tolerance=tolerance)

        out_event_ws = mantid_helper.retrieve_workspace(event_ws_name)
        assert out_event_ws

        return

    @staticmethod
    def mtd_convert_units(ws_name, target_unit):
        """
        Convert the unit of a workspace
        :param event_ws_name:
        :param target_unit:
        :return:
        """
        # Check requirements
        assert isinstance(ws_name, str), 'Input workspace name is not a string but is a %s.' % str(type(ws_name))
        workspace = mantid_helper.retrieve_workspace(ws_name)
        assert workspace
        assert isinstance(target_unit, str), 'Input target unit should be a string,' \
                                             'but is %s.' % str(type(target_unit))

        # Correct target unit
        if target_unit.lower() == 'd' or target_unit.lower().count('spac') == 1:
            target_unit = 'dSpacing'
        elif target_unit.lower() == 'tof':
            target_unit = 'TOF'

        # Do absorption and multiple scattering correction in TOF with sample parameters set
        mantidapi.ConvertUnits(InputWorkspace=ws_name,
                               OutputWorkspace=ws_name,
                               Target=target_unit,
                               EMode='Elastic')
        # Check output
        out_ws = mantid_helper.retrieve_workspace(ws_name)
        assert out_ws

        return

    @staticmethod
    def mtd_filter_bad_pulses(ws_name, lower_cutoff=95.):
        """ Filter bad pulse
        Requirements: input workspace name is a string for a valid workspace
        :param ws_name:
        :param lower_cutoff: float as (self._filterBadPulses)
        :return:
        """
        # Check requirements
        assert isinstance(ws_name, str), 'Input workspace name should be string,' \
                                         'but is of type %s.' % str(type(ws_name))
        assert isinstance(lower_cutoff, float)

        event_ws = mantid_helper.retrieve_workspace(ws_name)
        assert isinstance(event_ws, mantid.api.IEventWorkspace), \
            'Input workspace %s is not event workspace but of type %s.' % (ws_name, event_ws.__class__.__name__)

        # Get statistic
        num_events_before = event_ws.getNumberEvents()

        mantidapi.FilterBadPulses(InputWorkspace=ws_name, OutputWorkspace=ws_name,
                                  LowerCutoff=lower_cutoff)

        event_ws = mantid_helper.retrieve_workspace(ws_name)
        num_events_after = event_ws.getNumberEvents()

        print '[Info] FilterBadPulses reduces number of events from %d to %d (under %.3f percent) ' \
              'of workspace %s.' % (num_events_before, num_events_after, lower_cutoff, ws_name)

        return

    @staticmethod
    def mtd_normalize_by_current(event_ws_name):
        """
        Normalize by current
        Purpose: call Mantid NormalisebyCurrent
        Requirements: a valid string as an existing workspace's name
        Guarantees: workspace is normalized by current
        :param event_ws_name:
        :return:
        """
        # Check requirements
        assert isinstance(event_ws_name, str), 'Input event workspace name must be a string.'
        event_ws = mantid_helper.retrieve_workspace(event_ws_name)
        assert event_ws is not None

        # Call mantid algorithm
        mantidapi.NormaliseByCurrent(InputWorkspace=event_ws_name,
                                     OutputWorkspace=event_ws_name)

        # Check
        out_ws = mantid_helper.retrieve_workspace(event_ws_name)
        assert out_ws is not None

        return

    def reduce_sample_run(self, run_number):
        """ Reduce one sample run, which is not a vanadium run
        Purpose:
            Reduce a sample run
        Requirements:
            Run number is in list to reduce
        Guarantees:
            A sample run is reduced to a Rietveld diffraction pattern
        :param run_number:
        :param full_file_path:
        :return: 2-tuple as boolean (status, error message)
        """
        # Check
        assert isinstance(run_number, int), 'Run number %s to reduce sample run must be integer' % str(run_number)
        assert run_number in self._reductionTrackDict, 'Run %d is not managed by reduction tracker. ' \
                                                       'Current tracked runs are %s.' % \
                                                       (run_number, str(self._reductionTrackDict.keys()))
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker)
        if tracker.is_reduced is True:
            return False, 'Run %d has been reduced.' % run_number

        # Get data or load
        event_ws_name = tracker.event_workspace_name

        if event_ws_name is None:
            # never been loaded: get a name a load
            event_ws_name = self.get_event_workspace_name(run_number)
            tracker.event_workspace_name = event_ws_name
            data_file_name = tracker.file_path
            mantid_helper.load_nexus(data_file_name=data_file_name, output_ws_name=event_ws_name,
                                     meta_data_only=False)
        else:
            # already loaded or even processed
            pass

        # Filter bad pulses as an option
        # FIXME - Need to apply reduction-history here in the case that the workspace has been processed
        if self._reductionParameters.filter_bad_pulse is True:
            self.mtd_filter_bad_pulses(event_ws_name)
            tracker.add_history(ReductionHistory.FilterBadPulse)

        # Align and focus
        status = self.mtd_align_and_focus(event_ws_name)
        assert status
        tracker.add_history(ReductionHistory.AlignAndFocus)

        # Normalize by current as an option
        if self._reductionParameters.normalize_by_current:
            self.mtd_normalize_by_current(event_ws_name)
            tracker.add_history(ReductionHistory.NormaliseByCurrent)

        # Normalize/calibrate by vanadium
        if self._reductionParameters.calibrate_by_vanadium is True:
            self.normalizeByVanadium(event_ws_name)
            tracker.add_history(ReductionHistory.CalibratedByVanadium)

        tracker.is_reduced = True

        return

    def get_smoothed_vanadium(self, van_run_number):
        """
        Purpose:
            Get the smooth vanadium run (workspace) which has not been accepted.
        Requirements:

        Guarantees:

        :param van_run_number:
        :return:
        """
        # Check requirements
        assert isinstance(van_run_number, int)
        assert self.does_van_ws_exist(van_run_number)

        # Call method to smooth vnadium
        smooth_parameter = self._redctionParameter.vanadium_smooth_parameter
        temp_van_ws_name = self._workspaceManager.get_vanadium_workspace_name('smooth')
        mantid.SmoothVanadium(van_run_number, temp_van_ws_name, smooth_parameter)

        return temp_van_ws_name

    @property
    def time_focus_calibration_file(self):
        """ Get the full path of time focusing calibration file
        Requirements:
            the calibration file should have been set up
        Guarantees:
            calibration file with pull path
        :return:
        """
        assert self._focusCalibrationFile is not None
        return self._focusCalibrationFile

    @time_focus_calibration_file.setter
    def time_focus_calibration_file(self, value):
        """
        Purpose: set up the calibration file for time focusing
        Requirements: value must be a string and file exists
        Guarantees: calibration file is set up.
        :param value:
        :return:
        """
        assert isinstance(value, str)
        assert os.path.exists(value), 'Input file path %s does not exist.' % value

        self._focusCalibrationFile = value

        return

    def set_focus_calibration_file(self, focus_calibration_file):
        """ Set time focusing calibration file
        Purpose: Get the calibration file to do time focusing (offset, calibration, mask and etc)
        Requirements: Input file must exist
        Guarantees: file name is set to class variable
        :return:
        """
        # Check requirements
        assert isinstance(focus_calibration_file, str)
        assert os.path.exists(focus_calibration_file), 'Focus calibration file %s ' \
                                                       'does not exist.' % focus_calibration_file

        # Set value
        self._focusCalibrationFile = focus_calibration_file

        return

    def clear_time_focus_calibration(self):
        """ Clear the loaded time focusing calibration
        :return:
        """
        if self._myGroupWorkspaceName is not None:
            mantidapi.DeleteWorkspace(Workspace=self._myGroupWorkspaceName)
        if self._myOffsetWorkspaceName is not None:
            mantidapi.DeleteWorkspace(Workspace=self._myOffsetWorkspaceName)
        if self._myMaskWorkspaceName is not None:
            mantidapi.DeleteWorkspace(Workspace=self._myOffsetWorkspaceName)

        return

    def convert_to_vulcan_bin(self, run_number, out_gss_name):
        """ Convert to VULCAN binning
        Purpose: Convert the workspace to vulcan's IDL bin and write out GSAS file
        Requirements:
        Guarantees:
        :param run_number:
        :param out_gss_name: name of the output GSAS file name
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Input run number must be an integer but %s.' % str(type(run_number))
        assert run_number in self._reductionTrackDict, 'Run number %d is not tracked.' % run_number

        # Tracker
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker), 'The object in track dictionary is not correct.'

        # Get workspace name
        assert tracker.is_reduced, 'Run %d is not reduced yet.' % run_number
        ipts_number = self._myProject.get_ipts_number(run_number)

        # Convert unit and save for VULCAN GSS
        reduced_ws_name = tracker.event_workspace_name
        self.mtd_convert_units(reduced_ws_name, 'TOF')
        self.mtd_save_vulcan_gss(source_ws_name=reduced_ws_name,
                                 out_gss_file=out_gss_name,
                                 ipts=ipts_number,
                                 binning_reference_file=self._binningReferenceFile,
                                 gss_parm_file='Vulcan.parm')

        return

    @staticmethod
    def mtd_save_vulcan_gss(source_ws_name, out_gss_file, ipts, binning_reference_file, gss_parm_file):
        """ Convert to VULCAN's IDL and save to GSAS file
        Purpose: Convert a reduced workspace to IDL binning workspace and export to GSAS file
        Requirements:
        1. input source workspace is reduced
        2. output gsas file name is a string
        3. ipts number is integer
        4. binning reference file exists
        5. gss parameter file name is a string
        :param source_ws_name:
        :param out_gss_file:
        :param ipts:
        :param binning_reference_file:
        :param gss_parm_file:
        :return:
        """
        # Check requirements
        assert isinstance(source_ws_name, str)
        src_ws = mantid_helper.retrieve_workspace(source_ws_name)
        assert src_ws.getNumberHistograms() < 10

        assert isinstance(out_gss_file, str)
        assert isinstance(ipts, int), 'IPTS number must be an integer but not %s.' % str(type(ipts))
        assert isinstance(binning_reference_file, str)
        assert os.path.exists(binning_reference_file)
        assert isinstance(gss_parm_file, str)

        final_ws_name = source_ws_name + '_IDL'

        mantidapi.SaveVulcanGSS(InputWorkspace=source_ws_name,
                                BinFilename=binning_reference_file,
                                OutputWorkspace=final_ws_name,
                                GSSFilename=gss_parm_file,
                                IPTS = ipts,
                                GSSParmFilename=gss_parm_file)

        return

    def init_tracker(self, run_number, full_data_path):
        """ Initialize tracker
        :param run_number:
        :param full_data_path: full path to the data file to reduce
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number %s must be integer but not %s' % (str(run_number),
                                                                                          str(type(run_number)))

        # Initialize a new tracker
        if run_number not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number, file_path=full_data_path,
                                               vanadium_calibration=None)
            self._reductionTrackDict[run_number] = new_tracker

        # Check
        assert isinstance(self._reductionTrackDict[run_number], DataReductionTracker), 'It is not DataReductionTracker.'

        return

    def load_time_focus_calibration(self):
        """ Load time focusing calibration file if it has not been loaded
        :return:
        """
        # Check requirement
        assert self._reductionParameters.focus_calibration_file is not None, 'Time focus file has not been setup.'

        # Load calibration file if it is not loaded
        if self._myOffsetWorkspaceName is None:
            mantidapi.LoadCalFile(InstrumentName=self._myInstrument,
                                  CalFilename=self._reductionParameters.focus_calibration_file,
                                  WorkspaceName=self._myInstrument,
                                  MakeGroupingWorkspace=True,
                                  MakeOffsetsWorkspace=True,
                                  MakeMaskWorkspace=True)

            self._myOffsetWorkspaceName = '%s_offsets' % self._myInstrument
            self._myGroupWorkspaceName = '%s_group' % self._myInstrument
            self._myMaskWorkspaceName = '%s_mask' % self._myInstrument
            self._myCalibrationWorkspaceName = '%s_cal' % self._myInstrument

        # Check
        assert mantid_helper.workspace_does_exist(self._myOffsetWorkspaceName), \
            'Workspace %s cannot be found in AnalysisDataService.' % self._myOffsetWorkspaceName

        return

    def reduce_vanadium_run(self, run_number):
        """ Reduce vanadium data and strip vanadium peaks

        Requirements:
            Input run number is a valid integer run number
        :param run_number:
        :return: reduced workspace or None if failed to reduce
        """
        # FIXME/TODO/NOW : heavy-modification! On going!

        # Check requirements
        assert isinstance(run_number, int), 'Input vanadium run number must be integer but not %s.' % \
                                            str(type(run_number))
        assert run_number in self._reductionTrackDict, 'Reduction tracker does not have run %d.' % run_number

        # Get tracker
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker)

        # Load data
        mantid_helper.load_nexus(data_file_name=van_file_name, meta_data_only=False, output_ws_name=van_ws_name)
        assert mantid_helper.is_van_run(van_ws_name)

        # Filter bad pulse
        self.mtd_filter_bad_pulses(van_ws_name)
        self.mtd_align_and_focus(van_ws_name)
        self.mtd_compress_events(van_ws_name)
        self.mtd_convert_units(van_ws_name, 'TOF')

        mantidapi.SetSampleMaterial(InputWorkspace=wksp, 
                                 ChemicalFormula="V", 
                                 SampleNumberDensity=0.0721)
        wksp = mantidapi.MultipleScatteringCylinderAbsorption(InputWorkspace=wksp, 
                                                           OutputWorkspace=wksp.name())

        # Align and focus
        if params is None:
            params = PowderReductionParameters()
        wksp = self._doAlignFocus(wksp, params)

        # Strip vanadium peaks in d-spacd
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(), 
                                   Target="dSpacing")
        if DEBUGMODE is True:
            filename = os.path.join(DEBUGDIR, wksp.name()+"_beforeStripVPeak.nxs")
            mantidapi.SaveNexusProcessed(InputWorkspace=wksp,
                                         FileName= filename)

        wksp = mantidapi.StripVanadiumPeaks(InputWorkspace=wksp, 
                                         OutputWorkspace=wksp.name(), 
                                         FWHM=self._vanPeakFWHM, 
                                         PeakPositionTolerance=self._vanPeakTol,
                                         BackgroundType="Quadratic", 
                                         HighBackground=True)

        if DEBUGMODE is True:
            filename = os.path.join(DEBUGDIR, wksp.name()+"_afterStripVPeaks.nxs")
            mantidapi.SaveNexusProcessed(InputWorkspace=wksp,
                                         FileName= filename)
        # Smooth
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(),
                                   Target="TOF")
        wksp = mantidapi.FFTSmooth(InputWorkspace=wksp, 
                                OutputWorkspace=wksp.name(), 
                                Filter="Butterworth", 
                                Params=self._vanSmoothing,
                                IgnoreXBins=True,
                                AllSpectra=True)
        wksp = mantidapi.SetUncertainties(InputWorkspace=wksp, 
                                       OutputWorkspace=wksp.name())
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(), 
                                   Target="TOF")

        if wksp is not None: 
            self._vanRunWS = wksp

        return wksp


    def setVanadium(self, vanws, vanbkgdws):
        """ Set vanadium 
        """
        # set vanadium ws
        if vanws is None:
            self._doVanadium = False
        else:
            self._doVanadium = True
            self.vanWS = vanws

        # remove background
        if vanbkgdws is not None:
            self.vanWS -= vanbkgdws

        return

    def set_parameters(self, param_dict):
        """ Set parameters for reduction
        Purpose: set parameters' value from a parameter dictionary with parameter name as key and value as value
        Requirements: input is a dictionary
        Guarantees: parameters' value are set
        :param param_dict:
        :return:
        """
        # Check requirements
        assert isinstance(param_dict, dict)
        assert self._reductionParameters is not None

        # Set
        self._reductionParameters.set_from_dictionary(param_dict)

        return

    def setTimeFilter(self, tmin, tmax, tstep):
        """ Set event filtering

        Arguments:
         - tmin  :: min (relative) time in unit of seconds for time filter 
         - tmax  :: max (relative) time in unit of seconds for time filter 
         - tstep :: step of time in unit of seconds for time filter.  
        """
        # set event filtering
        self._filterMode = 'TIME'

        # check validity
        self._tmin = tmin
        self._tmax = tmax
        self._tstep = tstep

        return


    def setSampleLogFilter(self, logname, minvalue, maxvalue, step): 
        """ Set event filter by sample log
        """
        # set event mode
        self._filterMode = 'LOG'

        # check validity

        # set values
        self._logname = logname
        self._minvalue = minvalue
        self._maxvalue = maxvalue
        self._logstep = step

        return

    def stripVanadiumPeaks(self):
        """ 
        """
        # FIXME - Make sure there is one and only 1 workspace
        wksp = self._anyRunWSList[0]

        # Strip vanadium peaks in d-spacd
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                      OutputWorkspace=wksp.name(), 
                                      Target="dSpacing")
        self._anyRunWSList[0] = wksp

        wksp = mantidapi.StripVanadiumPeaks(InputWorkspace=wksp, 
                                            OutputWorkspace=wksp.name()+"_van", 
                                            FWHM=self._vanPeakFWHM, 
                                            PeakPositionTolerance=self._vanPeakTol,
                                            BackgroundType="Quadratic", 
                                            HighBackground=True)
        self._processedVanadiumWS = wksp

        return (True, '')

    def smoothVanadiumSpectra(self):
        """
        """
        wksp = self._processedVanadiumWS

        # Smooth
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(),
                                   Target="TOF")
        wksp = mantidapi.FFTSmooth(InputWorkspace=wksp, 
                                OutputWorkspace=wksp.name(), 
                                Filter="Butterworth", 
                                Params=self._vanSmoothing,
                                IgnoreXBins=True,
                                AllSpectra=True)
        wksp = mantidapi.SetUncertainties(InputWorkspace=wksp, 
                                       OutputWorkspace=wksp.name())
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(), 
                                   Target="TOF")

        self._processedVanadiumWS = wksp

        return

    def __init_old__(self, nxsfilename, isvanadium=False):
        """ Init
        """
        # Set up parameters
        self._myRawNeXusFileName = nxsfilename

        # Status variables
        self._statusVanadium = False

        # min, step, max
        self._binParam = [None, -0.01, None]

        # Is vanadium
        self._isVanadiumRun = bool(isvanadium)

        self._anyRunWSList = []

        # Define class variables
        if self._isVanadiumRun is True:
            self._vanRunWS = None
            self._vanPeakFWHM = 7
            self._vanPeakTol = 0.05
            self._vanSmoothing = "20,2"
        else:
            # FIXME - Need to get a way to set up these parameters!
            self._vanRunWS = None
            self._vanPeakFWHM = 7
            self._vanPeakTol = 0.05
            self._vanSmoothing = "20,2"

        self._tempSmoothedVanadiumWS = None

        # general align and focussing
        self._tofMin = None
        self._tofMax = None

        return
