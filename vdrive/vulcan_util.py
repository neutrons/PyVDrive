####
# Utility methods for VULCAN
####

import os

def locateVulcanVRecordFile(ipts):
    """ Get the path and name of a VULCAN's vanadium record file
    """
    raise NotImplementedError("ASAP1")
    return ""
    
    
def locateVulcanExpRecordFile(ipts):
    """ Get the path and name of a VULCAN's experiment record file
    """
    raise NotImplementedError("ASAP2")
    return ""
    
    
def checkIPTSExist(ipts, basepath):
    """ Check whether an IPTS number is valid
    """
    ipts = int(ipts)
    iptsdir = os.path.join(basepath, "IPTS-%d"%(ipts))
    print "IPTS directory = ", iptsdir
    
    if os.path.isdir(iptsdir) is True:
        return True
    
    return False    
    

class AutoVanadiumCalibrationLocator:
    """ Class to locate calibration file automatically
    """
    def __init__(self, ipts, basepath="/SNS/VULCAN/", vrecordfile=None, autorecordfile=None):
        """ Initialization
        """
        # check whether the IPTS exist
        iptsgood = checkIPTSExist(ipts, basepath)
        if iptsgood is False:
            raise NotImplementedError("IPTS %d does not exist for VULCAN" % (ipts))
        
        # ipts number
        self._ipts = ipts
        
        # import v-record
        if vrecordfile is None:
            vrecordfile = locateVulcanVRecordFile(self._ipts)
        if os.path.isfile(vrecordfile) is False:
            raise NotImplementedError("VRecord file %s does not exist." % (vrecordfile))
        self._importVRecord(vrecordfile)
        
        # import auto record
        if autorecordfile is None:
            autorecordfile = locateVulcanExpRecordFile(ipts)
        if os.path.isfile(autorecordfile) is False:
            raise NotImplementedError("Experimetn record file %s does not exist." % (autorecordfile))
        self._importExperimentRecord(autoreordfile)
        
        # runs
        self._runs = None
        
        return
        
    def getIPTS(self):
        """ IPTS is a key to the object
        """
        return self._ipts
       
    def addRuns(self, runs):
        """ Add a runs to find whether they are in experiment record file
        """
        numrunsadded = 0
        errmsg = ""
        for run in runs:
            run = int(runs)
            if self._expRecordDict.has_key(run):
                self._runs.append(run)
                numrunsadded ++ 1
            else:
                errmsg += "Run %d does not exist in IPTS %d (record file)\n" % (run, self._ipts)
        # ENDFOR
        
        return (numrunsaded, errmsg)
        
        
    def locatedRuns(self, runs):
        """ Add a list of run numbers and check whether they are valid or not.
        """
        errmsg = ""
        
        numrunsadded = 0
        for run in runs:
            run = int(run)
            relpathname = "IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs" % (self._ipts, run, run)
            nxsfilename = os.path.join(basepath, relpathname)
            if os.path.isfile(nxsfilename) is True:
                self._nxsFileList.append(nxsfilname)
                numrunsadded ++ 1
            else:
                errmsg += "Run %d does not exist in IPTS %d\n" % (run, self._ipts)
        # ENDFOR
        
        return (numrunsaded, errmsg)
        
        
    def locateCalibrationFile(self, criterion):
        """ 
        Arguments
         - criterion :: list of the criterion to match between run and 
        """
        # check
        if len(self._runs) == 0:
            return (False, "No run number in the list to locate")
            
        if len(criterion) == 0:
            return (False, "No criteria is defined by user.")
            
        # create dictionary for return
        runvandict = {}
            
        # filter van record by criterion
        for run in self._runs:
            # get the full list of runs
            vancadidaterunlist = self._vanRecordDict.keys()  
            
            # loop around criterion to remove all van runs that does not meet the requirement         
            for (logname, valuetype) in criterion:
                cvalue = self._expRecordDict[run][logname]
                for vanrun in vancadidaterunlist:
                    good = False
                    vanvalue = self._vanRecordDict[vanrun][logname]
                    if valuetype == 'int':
                        if int(cvalue) == int(vanvalue):
                            good = True
                    elif valuetype == 'str':
                        good = (cvalue == vanvalue)
                    elif valuetype == 'float':
                        if abs(float(cvalue)-float(vanvalue)) < 1.:
                            good = True
                    else:
                        raise NotImplementedError("Value type %s is not supported. " % (valuetype))
                    
                    if good is False:
                        vancadidaterunlist.remove(vanrun)
            # ENDFOR (criterion)
            
            if len(vancadidaterunlist) == 0:
                print "Error: There is no match for run %d. " % (run)
            elif len(vancadidaterunlist) > 1:
                print "Error: There are too many vanadium runs matching to run %d." % (run)
            else:
                runvandict[run] = vancadidaterunlist[0]
        # ENDFOR (run)
        
        return runvandict
    
    def _importVRecord(self, vrecordfile):
        """
        """
        try:
            vfile = open(vrecordfile,'r')
            lines = vfile.readlines()
            vfile.close()
        except IOError as ioe:
            return (False, str(ioe))
            
        # parse title line
        titlelist = []
        for iline in xrange(len(lines)):
            line = line.strip()
            if len(line) == 0:
                continue
            elif line.startswith('#') is True:
                continue
                
            terms = line.split('\t')
            if terms[0].strip().isdigit() is True:
                # skip if starts with a number
                continue
            else:
                for term in terms:
                    titlelist.append(term.strip())
                break
        
        # parse content line
        dataset = []
        for line in lines:
            line = line.strip()
            if len(line) == 0 or line.startswith('#') is True:
                continue
            terms = line.split('\t')
            if terms[0].strip().isdigit() is False:
                continue
                
            datarow = []
            for term in terms:
                datarow.append(term.strip())
            
            # check
            if len(datarow) != len(titlelist):
                print "Line %s has different number of items %d from titles %d." % (line, len(datarow),
                    len(titlelist))
        # ENDFOR
            
        # build dictionary
        self._vanRecordDict = {}
        try:
            irun = titlelist.index('RUN')
        except ValueError as e:
            return (False, "There is no title named 'RUN'.")
            
        for datarow in dataset:
            run = int(datarow[irun])
            datadict = {}
            for ititle in xrange(len(titlelist)):
                title = titlelist[ititle]
                value = datarow[ititle]
                datadict[title] = value
            # ENDFOR (ititle)
            self._vanRecordDict[run] = datadict
        
        return        
        
        
    def _importExperimentRecord(self, exprecfile):
        """
        """
        try:
            rfile = open(exprecfile,'r')
            lines = rfile.readlines()
            rfile.close()
        except IOError as ioe:
            return (False, str(ioe))
            
        # parse title line
        titlelist = []
        for iline in xrange(len(lines)):
            line = line.strip()
            if len(line) == 0:
                continue
            elif line.startswith('#') is True:
                continue
                
            terms = line.split('\t')
            if terms[0].strip().isdigit() is True:
                # skip if starts with a number
                continue
            else:
                for term in terms:
                    titlelist.append(term.strip())
                break
        
        # parse content line
        dataset = []
        for line in lines:
            line = line.strip()
            if len(line) == 0 or line.startswith('#') is True:
                continue
            terms = line.split('\t')
            if terms[0].strip().isdigit() is False:
                continue
                
            datarow = []
            for term in terms:
                datarow.append(term.strip())
            
            # check
            if len(datarow) != len(titlelist):
                print "Line %s has different number of items %d from titles %d." % (line, len(datarow),
                    len(titlelist))
        # ENDFOR
            
        # build dictionary
        self._expRecordDict = {}
        try:
            irun = titlelist.index('RUN')
        except ValueError as e:
            return (False, "There is no title named 'RUN'.")
            
        for datarow in dataset:
            run = int(datarow[irun])
            datadict = {}
            for ititle in xrange(len(titlelist)):
                title = titlelist[ititle]
                value = datarow[ititle]
                datadict[title] = value
            # ENDFOR (ititle)
            self._expRecordDict[run] = datadict
        
        return 
        