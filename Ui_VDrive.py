################################################################################
# UI class for project Py-VDrive
# - A GUI application will call this class for data reduction and analysis;
# - User can write script on this class to reduce and analyze data;
################################################################################
import os
import pickle

#import PyVDrive
#import PyVDrive.vdrive
#import PyVDrive.vdrive.VDProject
#import PyVDrive.vdrive.FacilityUtil as futil

import vdrive
import vdrive.VDProject as vdproj
import vdrive.FacilityUtil as futil

VanadiumPeakPositions = [0.5044,0.5191,0.5350,0.5526,0.5936,0.6178,0.6453,0.6768, 
        0.7134,0.7566,0.8089,0.8737,0.9571,1.0701,1.2356,1.5133,2.1401]

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
        self._dataRootPath = '/SNS/'
        self._baseDataPath = '/SNS/%s' % (self._myInstrument)
        self._vanadiumRecordFile = None

        # logging for tuple (logtype, log message), logtype = 'i', 'w', 'e' as information, 
        # ... warning and error
        self._myLogList = []
        self._projRunInfoDict = {}

        self._loadConfig()

        return

    def addDataFile(self, projname, datafilename):
        """ Add data
        Argument:
         - projname: used to identify project object
         - datafilename: new data file to add
        """
        self._checkProjectExistence(projname, "add data set")
       
        raise NotImplementedError('_projectDict is removed.')
        self._projectDict[projname].addData(datafilename)
        
        return


    def addExperimentRuns(self, projname, operation, ipts, runnumberlist, autofindcal):
        """ Add data file to project name by run number
        If auto vanadium run location mode is on, then a run-vanadium run is added. 
        
        Return :: (boolean, errmsg, list of 2-tuple, filename/list of van_run (or None))
        """ 
        import vdrive.vulcan_util

        # Check input
        if self._checkProjectExistence(projname, operation) is False:
            return (False, "Project %s does not exist." % (projname), None)

        # Get the handler on project
        try: 
            curproject = self._rProjectDict[projname]
        except KeyError:
            return (False, "Project %s does not exist." % (projname), None)

        # Get calibration vanadium automatically
        if autofindcal is True:
            # Entering auto mode to link data file to calibration file

            # check whether it is good for finding calibration automatically
            if len(self._vanCalibCriteriaDict[projname]) == 0:
                return (False, "Unable to match vanadium calibration file because \
                        criteria list is empty.", None)

            autofinder = vdrive.vulcan_util.AutoVanadiumCalibrationLocator(ipts, \
                    curproject.getBaseDataPath())
           
            # add runs
            numrunsadded, errmsg = autofinder.addRuns(runnumberlist)
            print "There are %d runs that are added among %d in input list." % (numrunsadded,
                    len(runnumberlist))
            print "Error: \n%s\n-------------------------------\n" % (errmsg, )

            # do match for calibration & export IPTS of all vanadium runs to locate NeXus file
            runvanrundict = autofinder.locateCalibrationFile(self._vanCalibCriteriaDict[projname])
            vaniptsdict = autofinder.getVanRunLogs('IPTS')

        else:
            # manual mode to link data file to calibration file
            print "Add run: ", runnumberlist
            runvanrundict = {}
            vaniptsdict = {}
            
        # build the list of data file/calibration file pair 
        datacalfilesets = []
        runwithcallist = runvanrundict.keys()
        for run in runnumberlist:
            print "[DB] Load run '%s'." % (str(run))
            runexist, datafile = vdrive.vulcan_util.locateRun(ipts, run, curproject.getBaseDataPath())
            if runexist is True:
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
        thisproject.addVanadiumIPTSInfo(vaniptsdict)

        return (True, "", datacalfilesets)
        
        
    def deleteProject(self, projtype, projname):
        """ Delete an existing project
        """
        project, errmsg = self._checkProjectExistence(projname, "delete project")
        if project is None:
            raise NotImplementedError(errmsg) 

        if projtype == 'r':
            self._rProjectDict.pop(projname)
        elif projtype == 'a':
            self._aProjectDict.pop(projname)
        else:
            return (False, "Project type is not supported.")
        
        return (True, "")

    def deleteRuns(self, projname, filenamelist):
        """ Delete some runs/data files from a project
        """
        # check project's existence
        project, errmsg = self._checkProjectExistence(projname, "delete runs/data files")
        if project is None:
            return (False, errmsg)
      
        # delete files
        errmsg = ""
        numfails = 0 
        for filename in filenamelist: 
            execstatus, errmsg = project.deleteData(filename)
            if execstatus is False:
                errmsg += errmsg + "\n"
                numfails += 1
            # ENDIF
        # ENDFOR(filename)

        if numfails == len(filenamelist):
            r = False
        else:
            r = True

        return (r, errmsg)


    def getReducedData(self, projname, datafilename, unit=None):
        """ Get reduced data from a ReductionProject

        Arguments: 
         - unit :: required unit for the output data X.  If None, then no requirement on output unit

        Return :: Dictionary (key = spectrum number, value = 2-tuple (vecx, vecy))
        """
        # Validate
        if self._rProjectDict.has_key(projname) is False:
            raise NotImplementedError('Project %s does not exist.'%(projname))
        else:
            project = self._rProjectDict[projname]

        if project.hasData(datafilename) is False:
            raise NotImplementedError('Project %s does not have run %s.'%(projname, datafilename))

        # Get data
        reduceddatadict = project.getReducedData(datafilename, unit)
        if reduceddatadict is None:
            raise NotImplementedError('Run %s is not reduced in project %s.'%(datafilename, projname))
        else:
            for iws in reduceddatadict.keys():
                print "[DB UI-Reduced] iws = %d, vecx = ", reduceddatadict[iws][0], ", vecy = ", reduceddatadict[iws][1]

        return reduceddatadict
        

    def getDataFiles(self, projname):
        """ Get names of the data files and their calibration files
        of a reduction project
        
        Return :: 3-tuple.  Status, Error Message, List of file pair
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


    def getIptsRunInfo(self, ipts):
        """ Get runs' information of an IPTS under a project name
        """
        # Validate
        if self._iptsRunDict.has_key(ipts) is False:
            raise KeyError('In iptsRunDict, there is no key for IPTS %d'%(ipts))

        periodtimefilelist = self._iptsRunDict[ipts]

        for timefilelsit in periodtimefilelist: 
            startrun_ctime = time.ctime(timefilelist[0][0])
            endrun_ctime = time.ctime(timefilelist[-1][0])
            startrun = timefilelist[0][1]
            endrun = timefilelist[-1][1]

            returnlist.append([startrun_ctime, endrun_ctime, startrun, endrun])

        # ENDFOR

        return returnlist



    def getProcessedVanadium(self, projname, datafilename):
        """ Get data sets from processed vanadium runs
        """
        project = self._rProjectDict[projname]
        vandatadict, history = project.getProcessedVanadium(datafilename)
        print "[DB Ui_VDrive] History = ", history

        return vandatadict
        

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


    def getTempSmoothedVanadium(self, projname, datafilename):
        """
        """
        project = self._rProjectDict[projname]
        smoothdatadict = project.getTempSmoothedVanadium(datafilename)

        return smoothdatadict


    def getVanadiumPeakPosList(self, dmin, dmax):
        """

        Return :: a list of sorted peak positions in dSpacing
        """
        peaklist = []
        for peakpos in VanadiumPeakPositions:
            if peakpos >= dmin and peakpos <= dmax:
                peaklist.append(peakpos)
        # ENDFOR

        return sorted(peaklist)
       

    def hasProject(self, projname):
        """  Check wehther a certain project does exist
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

    
    def info(self, projname):
        """
        """
        if self._rProjectDict.has_key(projname):
            info = self._rProjectDict[projname].info()
            return (True, "Reduction information:\n%s" % (info))

        elif self._aProjectDict.has_key(projname):
            info = self._aProjectDict[projname].info()
            return (True, "Analysis information:\n%s" % (info))

        return (False, "Project %s does not exist." % (projname))


    def isReductionSuccessful(self, projname):
        """ Check whether previous reduction is successful or not
        """
        # Get project
        try: 
            rdproj = self._rProjectDict[projname]
        except KeyError:
            return (False, "Project %s does not exist." % (projname))

        # Return
        return (rdproj.isSuccessful(), '')
        
        
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
            # create a reduction project
            newproject = vdproj.ReductionProject(projname)
            self._vanCalibCriteriaDict[projname] = [] 
            self._rProjectDict[projname] = newproject
            self._rProjectDict[projname].setVanadiumDatabaseFile(self._vanadiumRecordFile)
        elif projtype == 'analysis':
            # create an analysis project
            newproject = vdproj.AnalysisProject(projname)
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


    def searchFilesIPTS(self, projectname, ipts):
        """ Search files under IPTS

        Exceptions: KeyError, RuntimeError

        Return :: (run-status-flag, error message/dictionary
        """
        # Get project 
        vdriveproj = self._rProjectDict[projectname]

        # Search runs under IPTS according
        myfacility = futil.FacilityUtilityHelper(self._myInstrument)
        myfacility.setRootPath(self._dataRootPath)

        doexist = myfacility.setIPTS(ipts)
        if doexist is False:
            raise RuntimeError("IPTS %d does not exist." % (ipts))

        # Search runs 
        self._projRunInfoDict[projname][ipts] = myfacility.searchRuns()

        return (True, '')


    # def setDefaultDataPath(self, basedatapath):
    #     """ Set the global/default data path for all projects
    #     """
    #     if isinstance(basedatapath, str) is True: 
    #         self._baseDataPath = basedatapath
    #     else:
    #         raise NotImplementedError("Unable to set base data path with unsupported type %s." % (str(type(basedatapath))))

    #     return

    def setDefaultVanadiumDatabaseFile(self, vandbfile):
        """ Set the default/global vanadium database file
        """
        self._vanadiumRecordFile = vandbfile

        return


    def setCalibration(self, projname, datafilename, calibrun):
        """ Set a calibration run (van run) to a data file in a reduction project
        """
        try: 
            project = self._rProjectDict[projname]
        except KeyError:
            return (False, "Reduction project %s does not exist." % (projname))

        project.setCalibrationFile([datafilename], calibrun)

        return



    def setDataPath(self, projname, basedatapath=None):
        """ Set the base data path to a project
        """
        try: 
            project = self._rProjectDict[projname]
        except KeyError:
            return (False, "Reduction project %s does not exist." % (projname))

        # set up from default
        if basedatapath is None:
            basedatapath = self._myConfig['default.BaseDataPath']

        # set data path to particular project
        project.setBaseDataPath(basedatapath)

        return (True, "")


    def setReductionFlags(self, projname, filepairlist):
        """ Turn on the flag to reduce for files in the list

        Arguments: 
         - projname :: string as the name of reduction project
        """
        try:
            project = self._rProjectDict[projname]
        except KeyError:
            return (False, "Reduction project %s does not exist." % (projname))

        numflagson = 0
        for filename, rflag in filepairlist: 
            good = project.setReductionFlag(filename, rflag)
            if good is True:
                numflagson += 1
        # ENDFOR

        if numflagson == 0:
            return (False, "None of the input files that exist in the project %s." % (projname))

        return (True, "")

        
    def reduceData(self, projname):
        """ Reduce the data
        """
        project, errmsg = self._checkProjectExistence(projname, "reduce powder diffraction")
        if project is None:
            raise NotImplementedError(errmsg)
        else:
            # FIXME - Need a control for normByVanadium!
            status, errmsg = project.reduceToPDData(normByVanadium=True)

        return
        

    def setVanadiumCalibrationMatchCriterion(self, projname, criterialist):
        """ Set the criteria list for matching the vanadium calibration file
        for a reduction project
        Arguments:
         - criterialist :: list of 2-tuples as (sample-log-name, data-type)
        """
        if self._vanCalibCriteriaDict.has_key(projname) is False:
            return (False, "Unable to locate reduction project %s " % (projname))

        if isinstance(criterialist, list) is False:
            return (False, "Input criterial list must be list!")

        for c in criterialist:
            if isinstance(c, tuple) is False:
                raise NotImplementedError("Elements in criterialist must be 2-tuples")

        self._vanCalibCriteriaDict[projname] = criterialist

        return (True, "")
        

    def setCalibFile(self, projname, calfilename):
        """ Set calibration file in reduction mode in manual mode
        """
        self._checkProjectExistence(projname, "set calibration file")
        
        raise NotImplementedError('_projectDict is removed.')
        self._projectDict[projname].setCalibrationFile(calfilename)
        
        return
        
        
    def setCharactFile(self, projname, charactfilename):
        """ Set SNS characterization file name to reduction
        """
        self._checkProjectExistence(projname, "set characterization file")
        
        raise NotImplementedError('_projectDict is removed.')
        self._projectDict[projname].setCharacterFile(charactfilename)
        
        return
        
    def setReductionParameters(self, projname, reductionparamdict):
        """ Set reduction parameters
        """
        self._checkProjectExistence(projname, "set characterization file")
        
        self._rProjectDict[projname].setParameters(reductionparamdict)
        
        return
        
    def setEventFilter(self, projname, logname, minvalue, maxvalue, step):
        """ Set event file
        """
        self._checkProjectExistence(projname, "set event filter.")

        return


    def smoothVanadiumData(self, projname, datafilename):
        """ Smooth vanadium data
        """
        project = self._rProjectDict[projname]

        status, errmsg = project.smoothVanadiumData(datafilename=datafilename)

        return status, errmsg


    def stripVanadiumPeaks(self, projname, datafilename):
        """ Strip vanadium peaks
        """
        project = self._rProjectDict[projname]

        status, errmsg = project.stripVanadiumPeaks(datafilename=datafilename)

        return status, errmsg

        
    def addLogInformation(self, logstr):
        """ Add a log information at information level
        """
        self._myLogList.append( ('i', logstr) )

        return

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def _checkProjectExistence(self, projname, operation):
        """ Check wehtehr a project (name) does exist
        Return :: (project/None, errmsg)
        """
        # FIXME - how about to combine with self.hasProject()???
        hasproject, projtype = self.hasProject(projname)
        if hasproject is False:
            project = None
            errmsg = "Project %s exists. Unable to proceed the operation %s." % (
                projname, operation)
        elif projtype == 'a':
            project = self._aProjectDict[projname]
            errmsg = ""
        else:
            project = self._rProjectDict[projname]
            errmsg = ""
        
        return (project, errmsg)

    def _loadConfig(self):
        """ Load and possibly set up configuration directory
        """
        # vdrive configuration directory
        homdir = os.path.expanduser("~")
        configdir = os.path.join(homdir, ".vdrive")
        if os.path.exists(configdir) is False:
            os.makedirs(configdir)

        # copy over the configuration file if local does not have 
        localconffname = os.path.join(os.getcwd(), 'config.py')
        if os.path.exists(localconffname) is False:
            configfile = os.path.join(configdir, 'config.py')
            if os.path.exists(configfile) is True: 
                shutil.copyfile(configfile, localconffname)
            else:
                print "No configuration file can be found."
                return False
        # ENDIF

        try:
            import config
        except ImportError as e:
            print e
            raise e
        else:
            self._myConfig = config.configdict

        return True

