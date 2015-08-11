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


class AlignFocusParameters:
    """ Class to contain align and focus parameters
    """
    def __init__(self):
        """ Init 
        """
        refLogTofFilename = "/SNS/VULCAN/shared/autoreduce/vdrive_log_bin.dat"
        calibrationfilename = "/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal"
        characterfilename = "/SNS/VULCAN/shared/autoreduce/VULCAN_Characterization_2Banks_v2.txt"

        self._focusFileName     = calibrationfilename
        self._binning           = -0.001
        self._preserveEvents    = True
        self._LRef              = 0   # default = 0
        self._DIFCref           = 0
        self._compressTolerance = 0.01
        self._removePromptPulseWidth = 0.0
        self._lowResTOFoffset   = -1
        self._wavelengthMin     = 0.0

        return


class SNSPowderReductionLite:
    """ Class SNSPowderReductionLite 
    is a light version of SNSPowderReduction. 
    
    It is able to reduce the data file in the format of data file, 
    run number and etc. 

    It supports event chopping. 
    """
    def __init__(self, nxsfilename, isvanadium=False):
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
        
    def getProcessedVanadium(self):
        """ Get processed vanadium data 
        """
        return self._processedVanadiumWS


    def getReducedWorkspace(self, unit, listindex=0):
        """ Get the reduced matrix workspace
        Arguments: 
         - unit :: target unit; If None, then no need to convert unit
         
        Return :: Workspace (success) or 2-tuple (False and error message)
        """
        # FIXME - Need more consideration 
        try:
            retws = self._anyRunWSList[listindex]
        except IndexError:
            return (False, "Index %d exceeds the range of _anyRunWSList with size %d. "% (listindex, len(self._anyRunWSList)))
        print "[DB] Type of reduced workspace: ", type(retws)
        print "[DB] Name of reduced workspace: ", str(retws)
       
        if unit is None or retws.getAxis(0).getUnit().unitID() == unit :
            # no request of target unit or target unit is same as current unit
            return retws

        # convert unit
        retws = mantidapi.ConvertUnits(InputWorkspace=retws, 
                                       OutputWorkspace=retws.name(), 
                                       Target=unit, 
                                       EMode='Elastic')
        
        # set back to class list
        self._anyRunWSList[listindex] = retws
        
        return retws

    def getTempSmoothedVanadium(self):
        """
        """
        return self._tempSmoothedVanadiumWS


    def reducePDData(self, params, vrun=None, bkgdrun=None, chopdata=False, tofmin=None, tofmax=None):
        """ Reduce powder diffraction data
        This is the core functional methods of this class

        Arguments:
         - params   :: AlignFocusParameters object
         - vrun     :: an SNSPowderReductionLite instance for reduced vanadium run
         - bkgdrun  :: an SNSPowderReductionLite instance for reduced background run
         - dochopdata :: a boolean as the flag to chop data 
        """
        # Load file 
        wksp = self._loadData()

        # Chop data if specified
        if chopdata is True:
            wksplist = self._chopData(wksp)
        else:
            wksplist = [wksp]
        
        # Clear previous result if there is any without removing previos objects
        self._anyRunWSList = []

        # Align and focus
        for wksp in wksplist:   
            # Focus
            print "[DB] Do Align and Focus: TOF range: ", tofmin, tofmax
            focusedwksp = self._doAlignFocus(wksp, params, tofmin, tofmax)
            # Normalize by vanadium
            if vrun is not None:
                focusedwksp = focusedwksp._normByVanadium(wksp)
            # Check unit
            # FIXME Test Only Now!
            numspec = focusedwksp.getNumberHistograms()
            print "[DB] Range of X = %f, %f." % (focusedwksp.readX(0)[0], focusedwksp.readX(0)[-1])

            self._anyRunWSList.append(focusedwksp)
        # ENDFOR

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
            params = AlignFocusParameters()
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


    def _doAlignFocus(self, eventwksp, params, tofmin=None, tofmax=None):
        """ Align and focus raw event workspaces

        Current examle
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

        Arguments:
         - eventwksp

        Return: focussed event workspace
        """
        # FIXME/TODO ASAP - How to set up parameter???
        # Validate input
        if eventwksp.id() != EVENT_WORKSPACE_ID:
            raise NotImplementedError("Input must be an EventWorkspace for align and focus")
        elif isinstance(params, AlignFocusParameters) is False:
            raise NotImplementedError("Input parameter must be of class AlignFocusParameters")

        outwsname = eventwksp.name()+"_Foc_TOF"
        outws = mantidapi.AlignAndFocusPowder(InputWorkspace  = eventwksp, 
                                              OutputWorkspace = outwsname,   # in-place align and focus
                                              CalFileName     = params._focusFileName, 
                                              Params          = params._binning, 
                                              PreserveEvents  = params._preserveEvents,
                                              UnwrapRef       = params._LRef,    # default = 0
                                              LowResRef       = params._DIFCref, # default = 0
                                              RemovePromptPulseWidth  = params._removePromptPulseWidth, # default = 0.0
                                              CompressTolerance       = params._compressTolerance,
                                              LowResSpectrumOffset    = params._lowResTOFoffset,        # default = -1
                                              CropWavelengthMin       = params._wavelengthMin,          # defalut = 0.0
                                              ) #, **(focuspos))

        #if DEBUGOUTPUT is True:
        #    for iws in xrange(temp.getNumberHistograms()):
        #        spec = temp.getSpectrum(iws)
        #        self.log().debug("[DBx131] ws %d: spectrum ID = %d. " % (iws, spec.getSpectrumNo()))
        #        
        #    if preserveEvents is True and isinstance(temp, mantid.api._api.IEventWorkspace) is True:
        #        self.log().information("After being aligned and focussed workspace %s; Number of events = %d \
        #            of chunk %d " % (str(temp),temp.getNumberEvents(), ichunk))
        ## ENDIFELSE

        # Normalize by current
        # FIXME - Should be an optional operation by input argument
        outws = self._normalizeByCurrent(outws)

        if tofmin is not None and tofmax is not None:
            params = "%.5f, %.5f, %.5f"%(tofmin, params._binning, tofmax)
            print "[DB] Params to rebin = %s." %(params)
            outws = mantidapi.Rebin(InputWorkspace=outws, Params=params,
                    PreserveEvents=True, OutputWorkspace=outwsname)

        return outws


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
