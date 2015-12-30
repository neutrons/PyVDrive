################################################################################
#
# Modified SNS Powder Reduction
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

        self._focusFileName     = calibrationfilename
        self._preserveEvents    = True
        self._LRef              = 0   # default = 0
        self._DIFCref           = 0
        self._compressTolerance = 0.01
        self._removePromptPulseWidth = 0.0
        self._lowResTOFoffset   = -1
        self._wavelengthMin     = 0.0

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

    def set_from_dictionary(self, param_dict):
        """
        TODO/NOW/DOC + Fill-in
        :param param_dict:
        :return:
        """
        # Check requirements
        print 'Fill me'

        # Set
        for param_name in param_dict:
            if param_name in dir(self):
                setattr(self, param_name, param_dict[param_name])
            elif param_name in self.__dict__:
                setattr(self, param_name, param_dict[param_name])
            else:
                pass
                # print '[DB] Parameter %s is not an attribute' % param_name

        return


class ReductionHistory(object):
    """
    Class to describe the reduction history on one data set

    The default history is 'being loaded'
    """
    def __init__(self, workspace_name):
        """
        The key to a reduction history is its workspace name
        :param workspace_name:
        :return:
        """
        assert isinstance(workspace_name, str), 'Workspace name must be a string.'
        assert mantid_helper.workspace_does_exist(workspace_name), 'Workspace %s does not exist.' % workspace_name

        self._workspaceName = workspace_name

        self._isFocused = False
        self._badPulseRemoved = False
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

class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """

    OperationList = ['loaded', 'focused', 'bad_pulse_filtered', '']

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
        # TODO - it is not clear whether it is better to use vanadium file name or vanadium run number
        self._vanadiumCalibrationRunNumber = vanadium_calibration

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._operationsOnEventWS = list()

        return

    @property
    def event_workspace_name(self):
        """
        TODO/NOW/DOC
        :return:
        """
        return self._eventWorkspace

    @event_workspace_name.setter
    def event_workspace_name(self, value):
        """
        TODO/NOW/DOC
        :param value:
        :return:
        """
        print 'Check requirements'

        self._eventWorkspace = value

    @property
    def run_number(self):
        """ Read only

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


class ReductionManager(object):
    """ Class ReductionManager takes the control of reducing SNS/VULCAN's event data
    to diffraction pattern for Rietveld analysis.

    Its main data structure contains
    1. a dictionary of reduction controller
    2. a dictionary of loaded vanadium p

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

        return

    def align_and_focus(self, event_wksp, temp_ws_name):
        """ Align and focus raw event workspaces
        Purpose:
            Run Mantid.AlignAndFocus() by current parameters
        Requirements:
            Input event_wksp is not None
            Output workspace name is string
            All requirements for align and focus in Mantid is satisifed
        Guarantees:
            Event workspace is reduced

        Arguments:
         - eventwksp

        Return: focussed event workspace
        """
        # Check requirement
        assert event_wksp.id() == EVENT_WORKSPACE_ID, \
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
        outws = mantidapi.AlignAndFocusPowder(InputWorkspace=event_wksp,
                                              OutputWorkspace=temp_ws_name,   # in-place align and focus
                                              GroupingWrokspace=self._myGroupWorkspaceName,
                                              OffsetsWorkspace=self._myOffsetWorkspaceName,
                                              MaskWorkspace=None, # FIXME - NO SURE THIS WILL WORK!
                                              Params=params.binning,
                                              PreserveEvents=params.preserveEvents,
                                              RemovePromptPulseWidth=0, # Fixed to 0
                                              CompressTolerance=params.compressTolerance, # 0.01 as default
                                              Dspacing=True,            # fix the option
                                              UnwrapRef=0,              # do not use = 0
                                              LowResRef=0,              # do not use  = 0
                                              CropWavelengthMin=0,      # no in use = 0
                                              LowResSpectrumOffset=1,   # powgen's option. not used by vulcan
                                              **user_geometry_dict)

        return

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

    def get_reduced_workspace(self, run_number, unit='TOF', listindex=0):
        """ Get the reduced matrix workspace
        Purpose:

        Requirements:
            1. Specified run is correctly reduced;
        Guarantees:
            2. Return reduced workspace's name
        Arguments:
         - unit :: target unit; If None, then no need to convert unit

        Return :: Workspace (success) or 2-tuple (False and error message)
        """
        # TODO/NOW/FIXME - Complete it

        # Check requirements
        ChangeNextSection
        try:
            retws = self._anyRunWSList[listindex]
        except IndexError:
            return (False, "Index %d exceeds the range of _anyRunWSList with size %d. "% (listindex, len(self._anyRunWSList)))
        print "[DB] Type of reduced workspace: ", type(retws)
        print "[DB] Name of reduced workspace: ", str(retws)

        if unit is None or retws.getAxis(0).getUnit().unitID() == unit :
            # no request of target unit or target unit is same as current unit
            return retws

        # convert unit if necessary
        retws = mantidapi.ConvertUnits(InputWorkspace=retws,
                                       OutputWorkspace=retws.name(),
                                       Target=unit,
                                       EMode='Elastic')

        return reduced_ws_name

    def reduce_sample_run(self, run_number):
        """ Reduce one run
        Requirements:
            Run number is in list to reduce

        Example:
            Instrument  = "VULCAN",
            RunNumber   = runnumber,
            Extension   = "_event.nxs",
            PreserveEvents  = True,
            CalibrationFile = calibrationfilename,
            CharacterizationRunsFile = characterfilename,
            Binning = "-0.001",
            SaveAS  = "",
            OutputDirectory = outputdir,
            NormalizeByCurrent = False,
            FilterBadPulses=0,
            CompressTOFTolerance = 0.,
            FrequencyLogNames="skf1.speed",
            WaveLengthLogNames="skf12.lambda")
        :param run_number:
        :param full_file_path:
        :return:
        """
        # TODO/DOC/COMPLETE IT 1st

        # Check
        assert isinstance(run_number, int), 'Run number %s to reduce sample run must be integer' % str(run_number)
        assert run_number in self._reductionTrackDict, 'Run %d is not managed by reduction tracker. ' \
                                                       'Current tracked runs are %s.' % \
                                                       (run_number, str(self._reductionTrackDict.keys()))
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker)

        # Get data or load
        event_ws_name = tracker.event_workspace_name

        if event_ws_name is None:
            # never been loaded: get a name a load
            event_ws_name = self.get_event_workspace_name(run_number)
            data_file_name = tracker.file_path
            mantid_helper.load_nexus(data_file_name=data_file_name, output_ws_name=event_ws_name,
                                     meta_data_only=False)
        else:
            # already loaded or even processed
            pass


        do_load = False
        try:
            event_ws_name = self.get_event_workspace_name(run_number)
        except KeyError:
            event_ws_name = self._reductionProject.load_event_data(run_number)

        # Option for chopping
        # Chop data if specified
        if chopdata is True:
            wksplist = self._chopData(wksp)
        else:
            wksplist = [wksp]

        # Filter bad pulses as an option
        if self._reductionParameters.filterBadPulese is True:
            self._filterBadPulese(run_number)

        # Align and focus
        self.align_and_focus(run_number)

        # Normalize by current as an option
        if self._reductionParameters.normalizeByCurrent:
            self.noramlize_by_current(run_number)

        # Normalize/calibrate by vanadium
        if self._reductionParameters.calibrateByVanadium is True:
            self.normalizeByVanadium(run_number)

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
        Purpose:
        Requirements:
        Guarantees:
        :return:
        """
        # TODO/NOW/Complete it
        # Check requirements
        print 'Fill me'

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
            self._myMaskWorkspaceName = '%s_mask' % self._myMaskWorkspaceName

        # Check
        assert mantid_helper.workspace_does_exist(self._myOffsetWorkspaceName), \
            'Workspace %s cannot be found in AnalysisDataService.' % self._myOffsetWorkspaceName

        return

    def reduceVanadiumData(self, params):
        """ Reduce vanadium data and strip vanadium peaks

        Argumements:
         - params :: AlignFocusParameters object

        Return :: reduced workspace or None if failed to reduce
        """
        # Check status 
        if self._isVanadiumRun is False:
            raise NotImplementedError("This object is not set as a Vanadium run.")

        # Load data from file
        wksp = self._loadData()

        # Compress event 
        # FIXME - Understand Tolerance/COMPRESS_TOL_TOF 
        COMPRESS_TOL_TOF = 0.01
        wksp = mantidapi.CompressEvents(InputWorkspace=wksp,
                                     OutputWorkspace=wksp.name(),
                                     Tolerance=COMPRESS_TOL_TOF) # 10ns

        # Do absorption and multiple scattering correction in TOF with sample parameters set
        wksp = mantidapi.ConvertUnits(InputWorkspace=wksp, 
                                   OutputWorkspace=wksp.name(), 
                                   Target="TOF")
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
        Purpose:

        Requirements:

        Guarantees:
        :param param_dict:
        :return:
        """
        # TODO/NOW/Doc and etc
        # Check requirements

        assert self._reductionParameters is not None

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


    def setNoFilter(self):
        """ Non-filtering mode
        """
        self._filterMode = 'NONE'


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

    #---------------------------------------------------------------------------
    # Private Methods
    #---------------------------------------------------------------------------
    def _chopData(self, rawdataws):
        """
        """
        raise NotImplementedError("ASAP")
        # check validity
        if isinstance(rawdataws, mtd.EventWorkspace) is False:
            print "Input workspace is not event workspace"
            return False

        # check filtering
        if self._filterMode == 'TIME':
            datawslist = self.filterByTime(rawdataws)
        elif self._filterMode == 'LOG':
            datawslist = self.filterByLogValue(rawdataws)
        else:
            datawslist = [rawdataws]

        # process vanadium
        processedvanadiumws = self.reduceVanadium()

        # reduce data (no more event filtering)
        reducedlist = []
        for dataws in datawslist:
            redws = self.reducePowerData(dataws, processedvanadiumws, keeporiginal=False)
            reducedlist.append(redws)

        return reducedlist



    def _filterBadPulese(self, wksp, lowercutoff):
        """ Filter bad pulse
        Arguments: 
         - lowercutoff :: float as (self._filterBadPulses)
        """
        # Validate
        isEventWS = isinstance(wksp, mantid.api._api.IEventWorkspace)
        if isEventWS is True:
            # Event workspace: record original number of events
            numeventsbefore =  wksp.getNumberEvents()
        else:
            raise RuntimeError("Input workspace %s is not event workspace but of type %s." % (
                wksp.name(), wksp.__class__.__name__))
        # ENDIFELSE

        wksp = mantidapi.FilterBadPulses(InputWorkspace=wksp, OutputWorkspace=wksp, 
                LowerCutoff=lowercutoff)

        print "[Info] FilterBadPulses reduces number of events from %d to %d (under %.3f percent) of workspace %s." % (
                numeventsbefore, wksp.getNumberEvents(), lowercutoff, str(wksp))

        return wksp

    
    def _loadData(self):
        """ Load data
        """  
        # FIXME - ignored 'filterWall' here
        outwsname = os.path.basename(self._myRawNeXusFileName).split('.')[0]
        rawinpws = mantidapi.Load(self._myRawNeXusFileName, OutputWorkspace=outwsname)
        
        # debug output 
        if rawinpws.id() == EVENT_WORKSPACE_ID:
            # Event workspace
            print "[DB] There are %d events after data is loaded in workspace %s." % (
                rawinpws.getNumberEvents(), str(rawinpws))
        # ENDIF(rawinpws.id)

        return rawinpws


    def _normalizeByCurrent(self, wksp):
        """  Normalize the workspace by proton charge, i.e., current
        """ 
        outwsname = str(wksp)
        outws = mantidapi.NormaliseByCurrent(InputWorkspace=wksp,
                                             OutputWorkspace=outwsname)

        outws.getRun()['gsas_monitor'] = 1

        return outws


    def _processVanadium(self):
        """ Process reduced vanadium runs
        """ 

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
