################################################################################
# UI class for project Py-VDrive
# - A GUI application will call this class for data reduction and analysis;
# - User can write script on this class to reduce and analyze data;
################################################################################
import pickle

import PyVDrive
import PyVDrive.vdrive
import PyVDrive.vdrive.VDProject

import vdrive
import vdrive.VDProject as vp

class VDriveAPI:
    """ Class PyVDrive to mananger a sets of reduction and analysis projects
    """
    def __init__(self):
        """ Init
        """
        # reduction projects
        self._rProjectDict = {}

        # analysis projects
        self._aProjectDict = {}

        # FIXME - should move to other layers
        self._vanCalibCriteriaDict = {}
       
        # defaults
        self._myInstrument = "VULCAN"
        self._baseDataPath = '/SNS/%s' % (self._myInstrument)

        # logging for tuple (logtype, log message), logtype = 'i', 'w', 'e' as information, warning and error
        self._myLogList = []

        return

    
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
        If auto vanadium run location mode is on, then a run-vanadium run is added. 
        
        Return :: (boolean, string)
        """ 
        import vdrive.vulcan_util

        # check input
        if self._checkProjectExistence(projname, operation) is False:
            return (False, "Project %s does not exist." % (projname))

        # get handler on project
        try: 
            curproject = self._rProjectDict[projname]
        except KeyError:
            return (False, "Project %s does not exist." % (projname), None)

        # get calibration vanadium automatically
        if autofindcal is True:
            # auto mode to link data file to calibration file

            # check whether it is good for finding calibration automatically
            if len(self._vanCalibCriteriaDict[projname]) == 0:
                return (False, "Unable to match vanadium calibration file because criteria list is empty.")

            autofinder = vdrive.vulcan_util.AutoVanadiumCalibrationLocator(ipts, curproject.getBaseDataPath())
           
            # add runs
            numrunsadded, errmsg = autofinder.addRuns(runnumberlist)
            print "There are %d runs that are added among %d in input list." % (numrunsadded, len(runnumberlist))
            print "Error: \n%s\n-------------------------------\n" % (errmsg, )

            # do match for calibration

            runvanrundict = autofinder.locateCalibrationFile(self._vanCalibCriteriaDict[projname])
        
        else:
            # manual mode to link data file to calibration file
            runvanrundict = {}
            
        # build the list of data file/calibration file pair 
        datacalfilesets = []
        runwithcallist = runvanrundict.keys()
        for run in runnumberlist:
            exist, datafile = vdrive.vulcan_util.locateRun(ipts, run, curproject.getBaseDataPath())
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
        # FIXME - only applied to reduction project?
        thisproject = self._rProjectDict[projname]
        thisproject.addDataFileSets(datacalfilesets)

        return (True, "", datacalfilesets)
        
        
    def deleteProject(self, projtype, projname):
        """ Delete an existing project
        """
        self._checkProjectExistence(projname, "delete project")

        if projtype == 'r':
            self._rProjectDict.pop(projname)
        elif projtype == 'a':
            self._aProjectDict.pop(projname)
        else:
            return (False, "Project type is not supported.")
        
        return (True, "")

    def getDataFiles(self, projname):
        """ Get names of the data files and their calibration files
        of a reduction project
        """
        # get data files
        try:
            project = self._rProjectDict[projname]
        except KeyError:
            return (False, "Project %s does not exist in reduction projects." % (projname),
                    None)

        # form the return
        datafilelist = project.getDataFilePairs()

        return (True, "", datafilelist)

    def getProjectNames(self):
        """ Return the names of all projects
        """
        projnames = []

        projnames.extend(self._rProjectDict.keys())
        projnames.extend(self._aProjectDict.keys())

        return projnames

    def getReductionProjectNames(self):
        """ Get the names of all reduction projects
        """
        return sorted(self._rProjectDict.keys())
    
        
    def hasProject(self, projname):
        """ 
        """
        hasproject = False
        projecttype = ''

        if self._rProjectDict.has_key(projname) is True:
            hasproject = True
            projecttype += 'r'

        if self._aProjectDict.has_key(projname) is True:
            hasproject = True
            projecttype += 'a'

        return (hasproject, projecttype)
        
        
        
    def newProject(self, projname, projtype):
        """ Add a new project
        """         
        # Convert to str
        projname = str(projname)
        projtype = str(projtype)

        # check project type
        if projtype != 'reduction' and projtype != 'fit':
            raise NotImplementedError("Project type %s is not supported." % (projtype))
        
        # check available to add this new project
        if self._rProjectDict.has_key(projname) and projtype == 'reduction':
            raise NotImplementedError("Project with name %s has existed.  Unable to add a new project with sname name." 
                % (projname) )        
        elif self._aProjectDict.has_key(projname) and projtype == 'fit':
            raise NotImplementedError("Project with name %s has existed.  Unable to add a new project with sname name." 
                % (projname) )        
        
        # new project and register
        if projtype == 'reduction': 
            newproject = vp.ReductionProject(projname)
            self._vanCalibCriteriaDict[projname] = [] 
            self._rProjectDict[projname] = newproject
        elif projtype == 'analysis':
            newproject = vp.AnalysisProject(projname)
            self._aProjectDict[projname] = newproject
        
        newproject.setBaseDataPath(self._baseDataPath)

        return False
        
        
    def loadProject(self, projfilename):
        """ Load an existing project
        """
        # FIXME - Pickle may not be used in future.
        project = pickle.load(open(projfilename, 'r'))
        projname = project.name()

        if isinstance(project, PyVDrive.vdrive.VDProject.ReductionProject) is True:
            self._rProjectDict[project.name()] = project
            projtype = 'r'

        elif isinstance(project, PyVDrive.vdrive.VDProject.AnalysisProject) is True:
            self._aProjectDict[project.name()] = project
            projtype = 'a'

        else:
            raise NotImplementedError("Project %s is of an unsupported type %s." % (projfilename,
                project.__class__.__name__))
        
        return (True, (projtype, projname))


    def saveProject(self, projtype, projname, projfilename):
        """ Save an existing (in the memory) to a project file
        """
        # Convert to strs
        projtype = str(projtype)
        projname = str(projname)
        projfilename = str(projfilename)

        # check whether the project exists or not
        if projtype == 'r':
            # reduction project
            if self._rProjectDict.has_key(projname) is False:
                existingprojects = self._rProjectDict.keys()
                return (False, "Reduction project %s does not exist. Existing projects:  %s" % (
                    projname, str(existingprojects)))
            else:
                project = self._rProjectDict[projname]
        
        elif projtype == 'a':
            # analysis project
            if self._aProjectDict.has_key(projname) is False:
                return (False, "Analysis project %s does not exist." % (projname))
            else:
                project = self._aProjectDict[projname]

        else:
            # exceptin
            raise NotImplementedError("Project type %s is not supported." % (projtype))

        # FIXME - Use a better file than pickle later
        # save
        pickle.dump(project, open(projfilename, 'w'))

        return (True, "")

    
    def setDefaultDataPath(self, basedatapath):
        """ Set the global/default data path for all projects
        """
        self._baseDataPath = basedatapath

        return


    def setDataPath(self, projname, basedatapath):
        """ Set the base data path to a project
        """
        try: 
            project = self._rProjectDict[projname]
        except KeyError:
            return (False, "Reduction project %s does not exist." % (projname))

        project.setBaseDataPath(basedatapath)

        return (True, "")


        
    def reduce(self, projname):
        """ Reduce the data
        """
        self._checkProjectExistence(projname, "reduce powder diffraction")
        
        self._projectDict[projname].reduce()
        
        

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
        # FIXME - how about to combine with self.hasProject()???
        if self.hasProject(projname)[0] is False:
            raise NotImplementedError("Project %s exists. Unable to proceed the operation %s." % (
                projname, operation))
        
        return

    def addLogInformation(self, logstr):
        """ Add a log information at information level
        """
        self._myLogList.append( ('i', logstr) )

        return

