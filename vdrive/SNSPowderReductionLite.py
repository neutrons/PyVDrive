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
import mantid.simpleapi as mtd

EVENT_WORKSPACE_ID = "EventWorkspace"

class SNSPowderReductionLite:
    """ Class SNSPowderReductionLite 
    is a light version of SNSPowderReduction. 
    
    It is able to reduce the data file in the format of data file, 
    run number and etc. 

    It supports event chopping. 
    """
    def __init__(self, nxsfilename):
        """ Init
        """
        # Set up parameters
        self._myRawNeXusFileName = nxsfilename

        # Status variables
        self._statusVanadium = False

        # min, step, max
        self._binParam = [None, -0.01, None]

        return


    def reducePDData(self, params, vrun, chopdata):
        """ Reduce powder diffraction data
        This is the core functional methods of this class

        Arguments:
         - params :: dictionary to set up reduction parameters
         - vrun :: an SNSPowderReductionLite instance for reduced vanadium run
         - dochopdata :: a boolean as the flag to chop data 
        """
        # Load file 
        wksp = self._loadData()

        # Chop data if specified
        if chopdata is True:
            wksplist = self._chopData(wksp)
        else:
            wksplist = [wksp]

        # Align and focus
        self._reducedWkspList = []
        for wksp in wksplist:   
            focusedwksp = self._doFocusAlign(wksp)
            self._reducedWkspList.append(focusedwksp)

        return 


    def reduceProcessVanadiumData(self, params):
        """
        """
        # TODO - ASAP

        return


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



    def reducePowderData(self, dataws, bkgdws, vanws, keeporiginal):
        """ Reduce a single powder data
        """
        raise NotImplementedError("Need to look into SNSPowderReduction")


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


    def _doAlignFocus(self, eventwksp):
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
        # FIXME - ignored 'focuspos = self._focusPos' temporarily
        COMPRESS_TOL_TOF = float(self.getProperty("CompressTOFTolerance").value)
        if COMPRESS_TOL_TOF < 0.:
            COMPRESS_TOL_TOF = 0.01

        # TODO - Set up variables via class config

        outws = mtd.AlignAndFocusPowder(
                InputWorkspace  = eventwksp, 
                OutputWorkspace = eventwksp,   # in-place align and focus
                CalFileName     = self._focusFileName, 
                Params          = self._binning, 
                #Dspacing        = self._bin_in_dspace,
                #DMin            = self._info["d_min"], 
                #DMax            = self._info["d_max"], 
                #TMin            = self._info["tof_min"], 
                #TMax            = self._info["tof_max"],
                PreserveEvents  = self._flagPreserveEvents,
                UnwrapRef       = self._LRef,    # default = 0
                LowResRef       = self._DIFCref, # default = 0
                RemovePromptPulseWidth  = self._removePromptPulseWidth, # default = 0.0
                CompressTolerance       = COMPRESS_TOL_TOF,             
                LowResSpectrumOffset    = self._lowResTOFoffset,        # default = -1
                CropWavelengthMin       = self._wavelengthMin,          # defalut = 0.0
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

        return outws


    def _filterBadPulese(self, wksp):
        """ Filter bad pulse
        """
        # TODO - ASAP
        if self._filterBadPulses > 0.:
            isEventWS = isinstance(wksp, mantid.api._api.IEventWorkspace)
            if isEventWS is True:
                # Event workspace: record original number of events
                numeventsbefore =  wksp.getNumberEvents()

            wksp = api.FilterBadPulses(InputWorkspace=wksp, OutputWorkspace=wksp,
                                       LowerCutoff=self._filterBadPulses)

            if isEventWS is True:
                # Event workspace
                self.log().information("FilterBadPulses reduces number of events from %d to %d (under %s percent) of workspace %s." % (\
                        numeventsbefore, wksp.getNumberEvents(), str(self._filterBadPulses), str(wksp)))

    
    def _loadData(self):
        """ Load data
        """  
        # FIXME - ignored 'filterWall' here
        rawinpws = mtd.Load(self._myRawNeXusFileName)
        
        # debug output 
        if rawinpws.id() == EVENT_WORKSPACE_ID:
            # Event workspace
            print "[DB] There are %d events after data is loaded in workspace %s." % (
                rawinpws.getNumberEvents(), str(rawinpws))
        # ENDIF(rawinpws.id)

        return rawinpws


    def _noralizeByCurrent(self):
        """ 
        """
        # TODO - ASAP
        try:
            if self._normalisebycurrent is True:
                vanRun = api.NormaliseByCurrent(InputWorkspace=vanRun,
                                                OutputWorkspace=vanRun)
                vanRun.getRun()['gsas_monitor'] = 1
        except Exception, e:
            self.log().warning(str(e))



        return


    def _processVanadium(self):
        """ 
        """ 
        # FIXME TODO - ASAP
        if vanRun.id() == EVENT_WORKSPACE_ID:
                        vanRun = api.CompressEvents(InputWorkspace=vanRun, OutputWorkspace=vanRun,
                                                    Tolerance=COMPRESS_TOL_TOF) # 10ns

        # do the absorption correction
        vanRun = api.ConvertUnits(InputWorkspace=vanRun, OutputWorkspace=vanRun, Target="TOF")
        api.SetSampleMaterial(InputWorkspace=vanRun, ChemicalFormula="V", SampleNumberDensity=0.0721)
        vanRun = api.MultipleScatteringCylinderAbsorption(InputWorkspace=vanRun, OutputWorkspace=vanRun)

        self._doAlignFocus()

        vanRun = api.ConvertUnits(InputWorkspace=vanRun, OutputWorkspace=vanRun, Target="dSpacing")
        vanRun = api.StripVanadiumPeaks(InputWorkspace=vanRun, OutputWorkspace=vanRun, FWHM=self._vanPeakFWHM,\
                           PeakPositionTolerance=self.getProperty("VanadiumPeakTol").value,\
                                           BackgroundType="Quadratic", HighBackground=True)
        vanRun = api.ConvertUnits(InputWorkspace=vanRun, OutputWorkspace=vanRun, Target="TOF")
        vanRun = api.FFTSmooth(InputWorkspace=vanRun, OutputWorkspace=vanRun, Filter="Butterworth",\
                  Params=self._vanSmoothing,IgnoreXBins=True,AllSpectra=True)
        vanRun = api.SetUncertainties(InputWorkspace=vanRun, OutputWorkspace=vanRun)
        vanRun = api.ConvertUnits(InputWorkspace=vanRun, OutputWorkspace=vanRun, Target="TOF")
        

        return
