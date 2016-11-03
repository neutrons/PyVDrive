
        
class DeprecatedReductionProject(VDProject):
    """ Class to handle reducing powder diffraction data
    :Note: it is deprecated!
    """ 

    def __init__(self, project_name):
        """
        """
        VDProject.__init__(self, project_name)
        
        # detector calibration/focusing file
        self._detCalFilename = None
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
        
        self._tofMin = None
        self._tofMax = None

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
            self._dataFileDict.append(datafile)
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
        if datafilename not in self._dataFileDict:
            # a base file name is used
            for dfname in self._dataFileDict:
                basename = os.path.basename(dfname)
                if basename == datafilename:
                    datafilename = dfname
                    break
            # END(for)
        # ENDIF

        if datafilename not in self._dataFileDict:
            return (False, "data file %s is not in the project" % (datafilename))

        # remove from dataset
        self._dataFileDict.remove(datafilename)
        # remove from data file/van cal dict
        basename = os.path.basename(datafilename)
        vanfilename = self._datacalibfiledict.pop(basename)
        # remove from van cal/data file dict
        # FIXME - _calibfiledatadict will be set up only before reduction
        # self._calibfiledatadict.pop(vanfilename)

        return True, ""

    def getDataFilePairs(self):
        """ Get to know 
        """
        pairlist = []
        for datafile in self._datacalibfiledict.keys():
            pairlist.append( (datafile, self._datacalibfiledict[datafile]) )

        return pairlist

    def getTempSmoothedVanadium(self, run):
        """
        """
        runbasename = os.path.basename(run)
        
        returndict = None
        if self._myRunPdrDict.has_key(runbasename):
            runpdr = self._myRunPdrDict[runbasename]
            ws = runpdr.get_smoothed_vanadium()
            
            if ws is not None:
                ws = ConvertToPointData(InputWorkspace=ws)

                returndict = {}
                for iws in xrange(ws.getNumberHistograms()):
                    vecx = ws.readX(iws)[:]
                    vecy = ws.readY(iws)[:]
                    returndict[iws] = (vecx, vecy)
                # ENDFOR
            # ENDIF
        # ENDIF
        
        return returndict

    def getVanadiumRecordFile(self):
        """
        """
        return self._vanadiumRecordFile

    def info(self):
        """ Return information in nice format
        """
        ibuf = "%-50s \t%-30s\t %-5s\n" % ("File name", "Vanadium run", "Reduce?")
        for filename in self._dataFileDict:
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
        if self._dataFileDict.count(datafilename) == 1:
            return True


    def isSuccessful(self):
        """ Check whether last reduction is successful

        Return :: boolean
        """
        return self._lastReductionSuccess
        
        
    def setCalibrationFile(self, datafilenames, calibfilename):
        """ Set the vanadium calibration file to a set of data file in the 
        project
        Arguments:
         - datafilenames :: list of data file with full path
        """
        # FIXME - Rename to setVanCalFile
        errmsg = ""
        numfails = 0

        for datafilename in datafilenames:
            # check whether they exist in the project
            if datafilename not in self._dataFileDict:
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
        
        
    def setDetCalFile(self, detcalfilename):
        """ Set detector calibration file for focussing data
        """
        self._detCalFilename = detcalfilename
        if os.path.exists(self._detCalFilename) is False:
            return False
        
        return True        
        

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

    def setTOFRange(self, tofmin, tofmax):
        """ set range of TOF
        """
        self._tofMin = tofmin
        self._tofMax = tofmax

        return

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
