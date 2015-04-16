import sys
import os
import os.path 

import SNSPowderReductionLite as PRL

class VDProject:
    """
    """
    def __init__(self, projname):
        """
        """
        self._name = projname
        self._dataset = []
        self._baseDataPath = None 
        
        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        self._dataset.append(datafilename)

        return

    def deleteData(self, datafilename):
        """ Delete a data file in the project
        """
        self._dataset.remove(datafilename) 

    def getBaseDataPath(self):
        """ Get the base data path of the project
        """
        return self._baseDataPath

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


    def reduceToPDData(self, normByVanadium=True, eventFilteringSetup=None):
        """ Focus and process the selected data sets to powder diffraction data
        for GSAS/Fullprof/ format

        Workflow:
         1. Get a list of runs to reduce;
         2. Get a list of vanadium runs for them;
         3. Reduce all vanadium runs;
         4. Reduce (and possibly chop) runs;

        Arguments:
         - 
        """
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

        # Build list of vanadium runs
        vanrunlist = []
        if normByVanadium is True:
            for runbasename in sorted(self._datacalibfiledict.keys()):
                if (runbasename in runbasenamelist) is True:
                    print "[DB] Run %s has vanadium mapped: %s" % (runbasename, str(self._datacalibfiledict[runbasename]))
                    candidlist = self._datacalibfiledict[runbasename][0]
                    vanindex = self._datacalibfiledict[runbasename][1]
                    vanrunlist.append(int(candidlist[vanindex]))

                    rundict[runbasename] = (rundict[runbasename][0], int(candidlist[vanindex]))
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
            vpdr = PRL.SNSPowderReductionLite(vrunfilename)
            vpdr.reducePDData(params={}, vrun=None, chopdata=False)
            vanPdrDict[vrun] = vpdr
        # ENDFOR

        # Reduce all 
        runPdrDict = {}
        for basenamerun in sorted(rundict.keys()):
            # reduce 
            fullpathfname = rundict[basenamerun][0]
            vanrun = rundict[basenamerun][1]

            runpdr = PRL.SNSPowderReductionLite()
            # optinally chop
            if eventFilteringSetup is not None: 
                runpdr.setupEventFiltering(eventFilteringSetup)
                doChopData = True
            else:
                doChopData = False
            # ENDIF

            # vanadium
            if vanPdrDict.has_key(vanrun) is True:
                runpdr.reducePDData(params={}, vrun=vanPdrDict[vanrun], chopdata=doChopData)
            else:
                runpdr.reducePDData(params={}, vrun=None, chopdata=doChopData)

        raise NotImplementedError("Implemented to here so far....")

        pdd = PRL.SNSPowderReductionLite(calibfile=self._calibfilename)


        return
        
        
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
