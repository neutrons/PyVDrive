import sys
import os
import os.path

class VDProject:
    """
    """
    def __init__(self, projname):
        """
        """
        self._name = projname
        self._dataset = []
        
        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        self._dataset.append(datafilename)

        return
        
        
        
class ReductioProject(VDProject):
    """
    """
    def __init__(self, projname):
        """
        """
        VDProject.__init__(self, projname)
        
        # calibration file dictionary: key = data file name without full path
        self._datacalibfiledict = {}
        # calibration file to run look up table: key = calibration file with fullpath. value = list
        self._calibfiledatadict = {}
        
    def addDataFileSets(self, reddatasets):
        """ Add data file and calibration file sets 
        """
        for datafile, vcalfile in reddatasets:
            databasefname = os.path.basename(datafile)
            self._datacalibfiledict[databasefname] = vcalfile
            if self._calibfiledatadict.has_key(vcalfile) is False:
                self._calibfiledatadict[vcalfile] = []
            self._calibfiledatadict[vcalfile].append(datafile)
        # ENDFOR
        
        return
        
    def setCalibrationFile(self, datafilenames, calibfilename):
        """ Set the calibration file
        """
        for datafilename in datafilenames:
            basefilename = os.path.basename(datafilenames)
        
            self._datacalibfiledict[basefilename] = calibfilename
            
            if self._calibfiledatadict.has_key(calibfilename) is False:
                self._calibfiledatadict[calibfilename] = []
            self._calibfiledatadict[calibfilename].append(datafilename)
        
        # ENDFOR(datafilename)
    
        return
        
        
    def setCharacterFile(self, characerfilename):
        """ Set characterization file
        """
        self._characterfilename = characerfilename
        
        
    def setParameters(self, paramdict):
        """ Set parameters in addition to those necessary
        """
        if isinstance(paramdict, dict) is False:
            raise NotImplementedError("setParameters is supposed to get a dictionary")
            
        self._paramDict = paramdict
        
        return


    def setFilter(self):
        """ Set events filter for chopping the data
        """

        
    def reduce(self):
        """ Reduce by calling SNSPowderReduction
        """
        import SNSPowderReductionLite as PRL

        pdd = PRL.SNSPowderReductionLite(calibfile=self._calibfilename)

        raise NotImplementedError("From here!")

        return
        
 
        
class AnalysisProject(VDProject):
    """
    """
    def __init__(self):
        """
        """
