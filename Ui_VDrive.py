################################################################################
# UI class for project Py-VDrive
# - A GUI application will call this class for data reduction and analysis;
# - User can write script on this class to reduce and analyze data;
################################################################################

import vdrive
import vdrive.VDProject as vp

class VDriveAPI:
    """ Class PyVDrive
    """
    def __init__(self):
        """ Init
        """
        self._projectDict = {}
        
        return
        
        
    def newProject(self, projname, projtype):
        """ Add a new project
        """         
        # check project type
        if projtype != 'reduction' and projtype != 'fit':
            raise NotImplementedError("Project type %s is not supported." % (projtype))
        
        # check available to add this new project
        if self._projectDict.has_key(projname):
            raise NotImplementedError("Project with name %s has existed.  Unable to add a new project with sname name." 
                % (projname) )        
        
        # new project
        if projtype == 'reduction':
           newproject = vp.ReductioProject(projname)
        elif projtype == 'analysis':
            newproject = vp.AnalysisProject(projname)
        
        # add project to dictionary
        self._projectDict[projname] = newproject
                        
        return False
        
        
    def loadProject(self, projfilename):
        """ Load an existing project
        """
        raise NotImplementedError("Implement ASAP")
        
        
        return False
        
    def hasProject(self, projname):
        """ 
        """
        return self._projectDict.has_key(projname)
        
        
    def deleteProject(self, projname):
        """ Delete an existing project
        """
        self._checkProjectNotExistence(projname)
        raise NotImplementedError("Implement ASAP")
        
        return False
        
    def reduce(self, projname):
        """ Reduce the data
        """
        self._checkProjectExistence(projname, "reduce powder diffraction")
        
        self._projectDict[projname].reduce()
        
        
    def addDataFile(self, projname, datafilename):
        """ Add data
        Argument:
         - projname: used to identify project object
         - datafilename: new data file to add
        """
        self._checkProjectExistence(projname, "add data set")
        
        self._projectDict[projname].addData(datafilename)
        
        return
        
    def addExperimentRuns(self, projname, operation, ipts, runnumberlist, autofindcal):
        """ Add data file to project name by run number
        
        Return :: (boolean, string)
        """
        # check input
        if self._checkProjectExistence(projname, operation) is False:
            return (False, "Project %s does not exist." % (projname))
        
        # get calibration vanadium automatically
        if autofindcal is True:
            import vdrive.vulcan_util
            autofinder = vdrive.vulcan_util.AutoVanadiumCalibrationLocator(ipts)
       
        # add runs
        self._projectDict[projname].add()
        
        
        
    def setCalibFile(self, projname, calfilename):
        """ Set calibration file in reduction mode in manual mode
        """
        self._checkProjectExistence(projname, "set calibration file")
        
        self._projectDict[projname].setCalibrationFile(calfilename)
        
        return
        
        
    def setCharactFile(self, projname, charactfilename):
        """ Set SNS characterization file name to reduction
        """
        self._checkProjectExistence(projname, "set characterization file")
        
        self._projectDict[projname].setCharacterFile(charactfilename)
        
        return
        
    def setReductionParameters(self, projname, reductionparamdict):
        """ Set reduction parameters
        """
        self._checkProjectExistence(projname, "set characterization file")
        
        self._projectDict[projname].setParameters(reductionparamdict)
        
        return
        
    def setEventFilter(self, projname, logname, minvalue, maxvalue, step):
        """ Set event file
        """
        self._checkProjectExistence(projname, "set event filter.")

        return

        
    def _checkProjectExistence(self, projname, operation):
        """ Check wehtehr a project (name) does exist
        """
        if self._projectDict.has_key(projname) is False:
            raise NotImplementedError("Project %s exists. Unable to proceed the operation %s." % (
                projname, operation))
        
        return

