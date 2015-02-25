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
        
        
class ReductionProject(VDProject):
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
        # vanadium record (database) file
        self._vanadiumRecordFile = None
        # flags to reduce specific data set: key = file with full path
        self._reductionFlagDict = {}

        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        raise NotImplementedError("addData is private")

    def addDataFileSets(self, reddatasets):
        """ Add data file and calibration file sets 
        """
        for datafile, vcalfile in reddatasets:
            # data file list
            self._dataset.append(datafile)
            # data file / van cal dict
            databasefname = os.path.basename(datafile)
            self._datacalibfiledict[databasefname] = vcalfile
            # van cal /data file dict
            if self._calibfiledatadict.has_key(vcalfile) is False:
                self._calibfiledatadict[vcalfile] = []
            self._calibfiledatadict[vcalfile].append(datafile)
        # ENDFOR
        
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
        self._calibfiledatadict.pop(vanfilename)

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
            reduceBool = self._reductionFlagDict[filename]
            ibuf += "%-50s \t%-30s\t %-5s\n" % (filename, str(vanrun), str(reduceBool))
        # ENDFOR

        return ibuf
        
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

    def setVanadiumDatabaseFile(self, datafilename):
        """ Set the vanadium data base file
        """
        self._vanadiumRecordFile = datafilename

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
