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

import mantid
import mantid.simpleapi as mantidapi

EVENT_WORKSPACE_ID = "EventWorkspace"

DEBUGMODE = True
DEBUGDIR = os.path.join(homedir, 'Temp')


class PowderReductionParameters:
    """ Class to contain align and focus parameters
    Many of them server as default values
    """
    def __init__(self):
        """ Initialization
        """
        raise NotImplementedError('It has not been designed well how to use this class!')
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
    def binStep(self):
        """

        :return:
        """
        return

    BlaBlaBlaBla


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
        # check requirements
        assert isinstance(run_number, int)
        assert isinstance(file_path, str)
        assert vanadium_calibration is None or isinstance(vanadium_calibration, str)

        # set up
        self._runNumber = run_number
        self._filePath = file_path
        # TODO - it is not clear whether it is better to use vanadium file name or vanadium run number
        self._vanadiumCalibrationRunNumber = vanadium_calibration

        return

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

        # Set up including default
        self._myInstrument = instrument
        self._myTimeFocusFile = None
        self._reductionTrackDict = dict()

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
        assert isinstance(params, PowderReductionParameters), \
            'Input parameter must be of class AlignFocusParameters'

        assert isinstance(self._groupWSName, str)
        assert mantid.api.AnalysisDataService.has(self._groupWSName)
        assert isinstance(self._offsetWSName, str)
        assert AnalysisDataService.has(self._offsetWSName)

        # Execute algorithm AlignAndFocusPowder()
        # Unused properties: DMin, DMax, TMin, TMax, MaskBinTable,
        user_geometry_dict = dict()
        outws = mantidapi.AlignAndFocusPowder(InputWorkspace=event_wksp,
                                              OutputWorkspace=temp_ws_name,   # in-place align and focus
                                              GroupingWrokspace=self._groupWSName,
                                              OffsetsWorkspace=self._offsetWSName,
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

    def reduce_one_run(self, run_number):
        """
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
        :return:
        """
        # TODO/DOC/COMPLETE IT

        # Check
        assert isinstance(run_number)
        assert run_number in self._reductionTrackDict

        # Get data or load
        do_load = False
        try:
            event_ws_name = self._reductionProject.get_event_workspace_name(run_number)
        except KeyError:
            event_ws_name = self._reductionProject.load_event_data(run_number)

        # Option for chopping
        # Chop data if specified
        if chopdata is True:
            wksplist = self._chopData(wksp)
        else:
            wksplist = [wksp]

        # Filter bad pulses as an option
        if self._reductionParameter.filterBadPulese is True:
            self._filterBadPulese(run_number)

        # Align and focus
        self.align_and_focus(run_number)

        # Normalize by current as an option
        if self._reductionParameter.normalizeByCurrent:
            self.noramlize_by_current(run_number)

        # Normalize/calibrate by vanadium
        if self._reductionParameter.calibrateByVanadium is True:
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
        # TODO/NOW Implement it!
        raise NotImplementedError('ASAP')
        return self._tempSmoothedVanadiumWS

    def set_focus_calibration_file(self, focus_calibration_file):
        """ Set time focusing calibration file
        Purpose:
        Requirements:
        Guarantees:
        :return:
        """
        # TODO/NOW/Complete it
        blabla

        self._focusCalibrationFile = focus_calibration_file

        return

    def reduce_runs(self, vanadium_calibrate):
        """ Reduce marked runs
        Purpose:

        Requirements:

        Guarantees:

        :return:
        """
        # TODO/NOW/Implement this!
        # Check input
        blabla

        # Get list of runs that are marked to refine
        blabla

        # Check whether all runs to reduce have vanadium calibration set up
        # and create a list of required vanadium calibration files

        # Load calibration file if it is not loaded
        if self._myGroupWSName is None or self._myOffsetWSName is None:
            self.load_focus_calibration()

        # Load vanadium calibration file if required
        if vanadium_calibrate:
            pass

        # Reduce runs
        for run_number in self._runsToReduce:
            self.reduce_one_run(run_number)

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


    def setParameters(self, paramdict):
        """ Set parameters for reduction
        """
        if binparam is not None:
            if len(binparam) == 3:
                self._binParam = binparam
            else:
                raise NotImplementedError("Input bin parameters must be a list of 3 elements")
        # ENDIF(binparam)




        raise NotImplementedError("Need to figure out which parameters required.")


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