import sys

sys.path.append("/home/wzz/Mantid/Code/debug/bin/")

import mantid
import mantid.simpleapi as mtd

class VDProject:
    """
    """
    def __init__(self, projname):
        """
        """
        self._name = projname
        self._calibfilename = None
        self._dataset = []
        
        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        self._dataset.append(datafilename)
        
        
        
class ReductioProject(VDProject):
    """
    """
    def __init__(self, projname):
        """
        """
        VDProject.__init__(self, projname)
        
        
    def setCalibrationFile(self, calibfilename):
        """ Set the calibration file
        """
        self._calibfilename = calibfilename
        
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
        
    def reduce(self):
        """
        """
        mtd.SNSPowderReduction()
        
        return
        
 
        
class AnalysisProject(VDProject):
    """
    """
    def __init__(self):
        """
        """