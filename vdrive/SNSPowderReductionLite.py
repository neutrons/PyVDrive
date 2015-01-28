################################################################################
#
# Modified SNS Powder Reduction
#
################################################################################

sys.path.append("/home/wzz/Mantid/Code/debug/bin/")
sys.path.append("/Users/wzz/Mantid/Code/debug/bin/")

import mantid
import mantid.simpleapi as mtd

class SNSPowderReductionLite:
    """ Class SNSPowderReductionLite 
    is a light version of SNSPowderReduction. 
    
    It is able to reduce the data file in the format of data file, 
    run number and etc. 

    It supports event chopping. 
    """
    def __init__(self):
        """ Init
        """
        self._doVanadium = True
        self._eventFilter = None
        self._filterMode = 'NONE'

        # min, step, max
        self._binParam = [None, -0.01, None]

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


    def reduceData(self, rawdataws):
        """
        """
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


    def reducePowderData(self, dataws, bkgdws, vanws, keeporiginal):
        """ Reduce a single powder data
        """
        raise NotImplementedError("Need to look into SNSPowderReduction")
