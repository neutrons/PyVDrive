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

        self._vanCalibCriteriaDict = {}
        
        self._basePath = '/SNS/VULCAN'

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
            self._vanCalibCriteriaDict[projname] = [] 
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

    def setVanadiumCalibrationMatchCriterion(self, projname, criterialist):
        """ Set the criteria list for matching the vanadium calibration file
        for a reduction project
        """
        if self._vanCalibCriteriaDict.has_key(projname) is False:
            return (False, "Unable to locate reduction project %s " % (projname))

        if isinstance(criterialist, list) is False:
            return (False, "Input criterial list must be list!")

        self._vanCalibCriteriaDict[projname] = criterialist

        return (True, "")
        
    def addExperimentRuns(self, projname, operation, ipts, runnumberlist, autofindcal):
        """ Add data file to project name by run number
        
        Return :: (boolean, string)
        """ 
        import vdrive.vulcan_util

        # check input
        if self._checkProjectExistence(projname, operation) is False:
            return (False, "Project %s does not exist." % (projname))
        
        # get calibration vanadium automatically
        if autofindcal is True:
            # auto mode to link data file to calibration file

            # check whether it is good for finding calibration automatically
            if len(self._vanCalibCriteriaDict[projname]) == 0:
                return (False, "Unable to match vanadium calibration file because criteria list is empty.")

            autofinder = vdrive.vulcan_util.AutoVanadiumCalibrationLocator(ipts)
           
            # add runs
            numrunsadded, errmsg = autofinder.addRuns(runnumberlist)
            print "There are %d runs that are added among %d in input list." % (numrunsadded, len(runnumberlist))
            print "Error: \n%s\n-------------------------------\n" % (errmsg)

            # do match for calibration

            runvanrundict = autofinder.locateCalibrationFile(self._vanCalibCriteriaDict[projname])
        
        else:
            # manual mode to link data file to calibration file
            runvanrndict = {}
            
        # build the list of data file/calibration file pair 
        datacalfilesets = []
        runwithcallist = runvanrundict.keys()
        for run in runnumberlist:
            exist, datafile = vdrive.vulcan_util.locateRun(ipts, run, self._basePath)
            if exist is True:
                if run in runwithcallist:
                    vancalrun = runvanrundict[run]
                else:
                    vancalrun = None
                datacalfilesets.append( (datafile, vancalrun) )
                print "Run %d : File = %s, Calibration = %s" % (run, datafile, str(vancalrun))
            else:
                print "Run %d : %s." % (run, datafile)
        # ENDFOR (run)    
       
        # add runs
        self._projectDict[projname].addDataFileSets(datacalfilesets)

        return (True, "")
        
        
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

