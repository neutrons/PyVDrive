import sys
import os
import os.path 

# FIXME : This is for local development only!
homedir = os.path.expanduser('~')
mantidpath = os.path.join(homedir, 'Mantid/Code/debug/bin/')
sys.path.append(mantidpath)

import mantid
import mantid.simpleapi as mantidapi

import SNSPowderReductionLite as PRL

class VDProject:
    """
    """
    def __init__(self, projname):
        """
        """
        self._name = projname
        self._dataset = []
        self._baseDataFileNameList = []
        self._baseDataPath = None 
        
        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        self._dataset.append(datafilename)
        self._baseDataFileNameList.append(os.path.basename(datafilename))

        return

    def deleteData(self, datafilename):
        """ Delete a data file in the project
        """
        self._dataset.remove(datafilename) 
        self._baseDataFileNameList.remove(os.path.basename(datafilename))

        return

    def getBaseDataPath(self):
        """ Get the base data path of the project
        """
        return self._baseDataPath


    def hasData(self, datafilename):
        """ Check whether project has such data file 
        """
        if self._dataset.count(datafilename) == 1:
            # Check data set with full name
            return True
        elif self._baseDataFileNameList.count(datafilename) == 1:
            # Check data set with base name
            return True

        return False

    def name(self):
        return self._name
       

    def setBaseDataPath(self, datadir):
        """ Set base data path such as /SNS/VULCAN/
        to locate the data via run number and IPTS
        """
        if isinstance(datadir, str) is True: 
            self._baseDataPath = datadir

        else:
            raise NotImplementedError("Unable to set base data path with unsupported format %s." % (str(type(datadir))))

        return
        

    def _generateFileName(self, runnumber, iptsstr):
        """ Generate a NeXus file name with full path with essential information

        Arguments:
         - runnumber :: integer run number
         - iptsstr   :: string for IPTS.  It can be either an integer or in format as IPTS-####. 
        """
        # Parse run number and IPTS number
        run = int(runnumber)
        iptsstr = str(iptsstr).lower().split('ipts-')[-1]
        ipts = int(iptsstr)

        # Build file name with path
        # FIXME : VULCAN only now!
        nxsfname = os.path.join(self._baseDataPath, 'IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs'%(ipts, run, run))
        if os.path.exists(nxsfname) is False:
            print "[Warning] NeXus file %s does not exist.  Check run number and IPTS." % (nxsfname)
        else:
            print "[DB] Successfully generate an existing NeXus file with name %s." % (nxsfname)

        return nxsfname

        
class ReductionProject(VDProject):
    """ Class to handle reducing powder diffraction data
    """ 

    def __init__(self, projname):
        """
        """
        VDProject.__init__(self, projname)
        
        # calibration file dictionary: key = base data file name, value = (cal file list, index)
        self._datacalibfiledict = {}
        # calibration file to run look up table: key = calibration file with fullpath. value = list
        self._calibfiledatadict = {}
        # vanadium record (database) file
        self._vanadiumRecordFile = None
        # flags to reduce specific data set: key = file with full path
        self._reductionFlagDict = {} 
        # dictionary to map vanadium run with IPTS. key: integer  
        self._myVanRunIptsDict = {}

        # Reduction status
        self._lastReductionSuccess = None

        # Reduction result dictionary
        self._myRunPdrDict = {}

        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        raise NotImplementedError("addData is private")

    def addDataFileSets(self, reddatasets):
        """ Add data file and calibration file sets 
        """
        for datafile, vcalfilelist in reddatasets:
            # data file list
            self._dataset.append(datafile)
            # data file and set default to 0th element
            databasefname = os.path.basename(datafile)
            self._baseDataFileNameList.append(databasefname)
            self._datacalibfiledict[databasefname] = (vcalfilelist, 0)


            # FIXME : This will be moved to a stage that is just before reduction
            # van cal /data file dict
            # print "_calibfiledatadict: ", type(self._calibfiledatadict)
            # print "key: ", vcalfile

            # raise NotImplementedError("Need to determine the calibration file first!")
            # if self._calibfiledatadict.has_key(vcalfile) is False:
            #     self._calibfiledatadict[vcalfile] = []
            # # self._calibfiledatadict[vcalfile].append(datafile)
        # ENDFOR
        
        return

    def addVanadiumIPTSInfo(self, vaniptsdict):
        """ Add vanadium's IPTS information for future locating NeXus file
        """
        for vanrun in vaniptsdict.keys():
            self._myVanRunIptsDict[int(vanrun)] = vaniptsdict[vanrun]

        return


    def deleteData(self, datafilename):
        """ Delete a data: override base class
        Arguments: 
         - datafilename :: data file name with full path
        """
        # FIXME - A better file indexing data structure should be used
        # search data file list
        if datafilename not in self._dataset:
            # a base file name is used
            for dfname in self._dataset:
                basename = os.path.basename(dfname)
                if basename == datafilename:
                    datafilename = dfname
                    break
            # END(for)
        # ENDIF

        if datafilename not in self._dataset:
            return (False, "data file %s is not in the project" % (datafilename))

        # remove from dataset
        self._dataset.remove(datafilename)
        # remove from data file/van cal dict
        basename = os.path.basename(datafilename)
        vanfilename = self._datacalibfiledict.pop(basename)
        # remove from van cal/data file dict
        # FIXME - _calibfiledatadict will be set up only before reduction
        # self._calibfiledatadict.pop(vanfilename)

        return (True, "")

    def getDataFilePairs(self):
        """ Get to know 
        """
        pairlist = []
        for datafile in self._datacalibfiledict.keys():
            pairlist.append( (datafile, self._datacalibfiledict[datafile]) )

        return pairlist
        
    def getProcessedVanadium(self, run):
        """          vandatalist, history = project.
        """
        runbasename = os.path.basename(run)

        returndict = None
        if self._myRunPdrDict.has_key(runbasename):
            runpdr = self._myRunPdrDict[runbasename]
            ws = runpdr.getProcessedVanadium()
            
            if ws is not None:
                ws = mantidapi.ConvertToPointData(InputWorkspace=ws)

                returndict = {}
                for iws in xrange(ws.getNumberHistograms()):
                    vecx = ws.readX(iws)[:]
                    vecy = ws.readY(iws)[:]
                    print type(vecx), type(vecy)
                    returndict[iws] = (vecx, vecy)
                    print "[DB Vanadium] iws = %d, vecx = "%(iws), str(vecx)
                # ENDFOR
            # ENDIF
        # ENDIF
        
        return (returndict, "Blabla;blabla")


    def getReducedData(self, run, unit):
        """ Get reduced data including all spectra

        Arguments: 
         - unit :: target unit for the output X vector.  If unit is None, then no request

        Return :: dictionary: key = spectrum number, value = 2-tuple (vecx, vecy)
        """
        runbasename = os.path.basename(run)

        if self._myRunPdrDict.has_key(runbasename): 
            runpdr = self._myRunPdrDict[runbasename]
            ws = runpdr.getReducedWorkspace(unit)

            newws = mantidapi.ConvertToPointData(InputWorkspace=ws)

            returndict = {}
            for iws in xrange(ws.getNumberHistograms()):
                vecx = newws.readX(iws)[:]
                vecy = newws.readY(iws)[:]
                returndict[iws] = (vecx, vecy)
            # ENDFOR

        else:
            # Not reduced
            returndict = None

        return returndict


    def getTempSmoothedVanadium(self, run):
        """
        """
        runbasename = os.path.basename(run)
        
        returndict = None
        if self._myRunPdrDict.has_key(runbasename):
            runpdr = self._myRunPdrDict[runbasename]
            ws = runpdr.getTempSmoothedVanadium()
            
            if ws is not None:
                ws = mantidapi.ConvertToPointData(InputWorkspace=ws)

                returndict = {}
                for iws in xrange(ws.getNumberHistograms()):
                    vecx = ws.readX(iws)[:]
                    vecy = ws.readY(iws)[:]
                    returndict[iws] = (vecx, vecy)
                # ENDFOR
            # ENDIF
        # ENDIF
        
        return (returndict)


    def getVanadiumRecordFile(self):
        """
        """
        return self._vanadiumRecordFile

    def info(self):
        """ Return information in nice format
        """
        ibuf = "%-50s \t%-30s\t %-5s\n" % ("File name", "Vanadium run", "Reduce?")
        for filename in self._dataset:
            basename = os.path.basename(filename)
            vanrun = self._datacalibfiledict[basename]
            try: 
                reduceBool = self._reductionFlagDict[filename]
            except KeyError as e:
                # print "Existing keys for self._reductionFlagDict are : %s." % (
                #         str(sorted(self._reductionFlagDict.keys())))
                ibuf += "%-50s \tUnable to reduce!\n" % (filename)
            else: 
                ibuf += "%-50s \t%-30s\t %-5s\n" % (filename, str(vanrun), str(reduceBool))
        # ENDFOR

        return ibuf

    def hasData(self, datafilename):
        """ Check whether project has such data file 
        """
        # Check data set with full name
        if self._dataset.count(datafilename) == 1:
            return True


    def isSuccessful(self):
        """ Check whether last reduction is successful

        Return :: boolean
        """
        return self._lastReductionSuccess


    def reduceToPDData(self, normByVanadium=True, eventFilteringSetup=None):
        """ Focus and process the selected data sets to powder diffraction data
        for GSAS/Fullprof/ format

        Workflow:
         1. Get a list of runs to reduce;
         2. Get a list of vanadium runs for them;
         3. Reduce all vanadium runs;
         4. Reduce (and possibly chop) runs;

        Arguments:
         - normByVanadium :: flag to normalize by vanadium
        """
        self._lastReductionSuccess = False

        # Build list of files to reduce
        rundict = {}
        runbasenamelist = []
        for run in self._reductionFlagDict.keys():
            if self._reductionFlagDict[run] is True:
                basenamerun = os.path.basename(run)
                rundict[basenamerun] = (run, None)
                runbasenamelist.append(basenamerun)
        # ENDFOR
        print "[DB] Runs to reduce: %s." % (str(runbasenamelist))
        if len(rundict.keys()) == 0:
            return (False, 'No run is selected to reduce!')

        # Build list of vanadium runs
        vanrunlist = []
        if normByVanadium is True:
            for runbasename in sorted(self._datacalibfiledict.keys()):
                if (runbasename in runbasenamelist) is True:
                    print "[DB] Run %s has vanadium mapped: %s" % (runbasename, str(self._datacalibfiledict[runbasename]))
                    candidlist = self._datacalibfiledict[runbasename][0]
                    if candidlist is None:
                        # no mapped vanadium
                        continue
                    elif isinstance(candidlist, list) is False:
                        # unsupported case
                        raise NotImplementedError("Vanadium candidate list 'candidlist' must be either list or None. \
                                Now it is %s." % (str(candidlist)))
                    vanindex = self._datacalibfiledict[runbasename][1]
                    try:
                        vanrunlist.append(int(candidlist[vanindex]))
                        rundict[runbasename] = (rundict[runbasename][0], int(candidlist[vanindex]))
                    except TypeError as te:
                        print "[Warning] Van run in candidate list is %s.  \
                                Cannot be converted to van run du to %s. " % (str(candidlist[vanindex]), str(te))
                    except IndexError as ie:
                        raise ie
                # ENDIF
            # ENDFOR
            vanrunlist = list(set(vanrunlist))
        # ENDIF
        print "[DB] Vanadium runs (to reduce): %s" % (str(vanrunlist))

        # from vanadium run to create vanadium file 
        vanfilenamedict = {}
        for vrun in vanrunlist:
            vanfilename = self._generateFileName(vrun, self._myVanRunIptsDict[int(vrun)])
            vanfilenamedict[int(vrun)] = vanfilename
        # ENDFOR

        # Reduce all vanadium runs
        vanPdrDict = {}
        for vrun in vanrunlist:
            vrunfilename = vanfilenamedict[vrun]
            vpdr = PRL.SNSPowderReductionLite(vrunfilename, isvanadium=True) 
            vanws = vpdr.reduceVanadiumData(params={})
            if vanws is None:
                raise NotImplementedError("Unable to reduce vanadium run %s." % (str(vrun)))
            vanPdrDict[vrun] = vpdr
        # ENDFOR

        # Reduce all 
        for basenamerun in sorted(rundict.keys()):
            # reduce regular powder diffraction data
            fullpathfname = rundict[basenamerun][0]
            vanrun = rundict[basenamerun][1]
            
            runpdr = PRL.SNSPowderReductionLite(fullpathfname, isvanadium=False)

            # optinally chop
            doChopData = False
            if eventFilteringSetup is not None: 
                runpdr.setupEventFiltering(eventFilteringSetup)
                doChopData = True
            # ENDIF

            # set up vanadium
            if vanPdrDict.has_key(vanrun) is True and normByVanadium is True:
                vrun = vanPdrDict[vanrun]
            else:
                vrun = None
            # ENDIF (vrun)

            # reduce data
            runpdr.reducePDData(params=PRL.AlignFocusParameters(), 
                                vrun=vrun,
                                chopdata=doChopData)

            self._myRunPdrDict[basenamerun] = runpdr
        # ENDFOR(basenamerun)

        self._lastReductionSuccess = True

        return (True, '')
        
        
    def setCalibrationFile(self, datafilenames, calibfilename):
        """ Set the calibration file to a set of data file in the 
        project
        Arguments:
         - datafilenames :: list of data file with full path
        """
        errmsg = ""
        numfails = 0

        for datafilename in datafilenames:
            # check whether they exist in the project
            if datafilename not in self._dataset:
                errmsg += "Data file %s does not exist.\n" % (datafilename)
                numfails += 1
                continue

            # get base name
            basefilename = os.path.basename(datafilenames)
            # data file/calib dict 
            self._datacalibfiledict[basefilename] = calibfilename
           
            # calib / data file dict
            if self._calibfiledatadict.has_key(calibfilename) is False:
                self._calibfiledatadict[calibfilename] = []
            self._calibfiledatadict[calibfilename].append(datafilename)
        # ENDFOR(datafilename)

        if numfails == len(datafilenames):
            r = False
        else:
            r = True
    
        return (r, errmsg)

    def setCharacterFile(self, characerfilename):
        """ Set characterization file
        """
        self._characterfilename = characerfilename
        
        

    def setFilter(self):
        """ Set events filter for chopping the data
        """

        return
    def setParameters(self, paramdict):
        """ Set parameters in addition to those necessary
        """
        if isinstance(paramdict, dict) is False:
            raise NotImplementedError("setParameters is supposed to get a dictionary")
            
        self._paramDict = paramdict
        
        return

    def setReductionFlag(self, filename, flag):
        """ Turn on the reduction flag for a file of this project

        Assumption: if the file name is not the name in full path, then 
        there is only one file name with the same base name
        """
        # check with full name
        exist = filename in self._dataset
        if exist:
            self._reductionFlagDict[filename] = flag
            return True

        # check as base name
        for fpname in self._dataset:
            basename = os.path.basename(fpname)
            if basename == filename:
                self._reductionFlagDict[fpname] = flag
                return True

        return False
        
    def setVanadiumDatabaseFile(self, datafilename):
        """ Set the vanadium data base file
        """
        self._vanadiumRecordFile = datafilename

        return
        
    def stripVanadiumPeaks(self, datafilename): 
        """ Strip vanadium peaks from a reduced run
        """
        basefname = os.path.basename(datafilename)
        reductmanager = self._myRunPdrDict[basefname]

        status, errmsg = reductmanager.stripVanadiumPeaks()

        return status, errmsg


class AnalysisProject(VDProject):
    """
    """
    def __init__(self):
        """ Initialization
        """

        return


    def getData(self, basedatafilename):
        """ Get data X, Y and E
        """
        # get file name
        fullpathdatafname = self._getFullpathFileName(basedatafilename)
        if fullpathdatafname is None:
            return (False, "Data file name %s does not exist in project. " % (basedatafilename))
        
        if os.path.exists(fullpathdatafname):
            return (False, "Data file name %s cannot be found. " % (fullpathdatafname))

        # retrieve 
        ws = mantid.LoadGSS(Filename=fullpathdatafname)

        # FIXME - Consider single-spectrum GSS file only!

        return (True, [ws.readX(0), ws.readY(0), ws.readE(0)])
