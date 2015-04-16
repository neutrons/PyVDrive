####
# Utility methods for VULCAN
####

import os

def locateVulcanVRecordFile(basepath):
    """ Get the path and name of a VULCAN's vanadium record file
    """
    relpath = "shared/Calibrationfiles/Instrument/Standard/Vanadium"
    relpathname = os.path.join(relpath, "VRecord.txt")    
    vrecordfilename = os.path.join(basepath, relpathname)

    return vrecordfilename
    
    
def locateVulcanExpRecordFile(ipts, basepath):
    """ Get the path and name of a VULCAN's experiment record file
    """
    relpath = "IPTS-%d/shared/" % (int(ipts))
    relpathname = os.path.join(relpath, "AutoRecord.txt")
    exprecordfilename = os.path.join(basepath, relpathname)
    
    return exprecordfilename
    
    
def locateRun(ipts, runnumber, basepath='/SNS/VULCAN/'):
    """ Add a list of run numbers and check whether they are valid or not.
    """
    errmsg = ""
    
    # build the name according to the convention
    run = int(runnumber)
    relpathname = "IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs" % (ipts, run, run)
    nxsfilename = os.path.join(basepath, relpathname)
    
    # check existence of file
    if os.path.isfile(nxsfilename) is False:
        good = False
        errmsg =  "Run %d does not exist in IPTS %d.  NeXus file cannot be found at %s. " % (run, ipts, nxsfilename)
        return (False, errmsg)
    
    return (True, nxsfilename)
    
    
def checkIPTSExist(ipts, basepath):
    """ Check whether an IPTS number is valid
    """
    ipts = int(ipts)
    print "[DB] base path = ", basepath, " type = ", type(basepath)
    iptsdir = os.path.join(basepath, "IPTS-%d"%(ipts))
    msg = "IPTS directory: %s" %(iptsdir)
    
    if os.path.isdir(iptsdir) is True:
        return (True, msg)
    
    return (False, msg)


def getLogsList(vandbfile):
    """ Get the log list from vanadium database file (van record.txt)
    The returned value will be a list of tuples.  
    In each tuple, there are log name and one example
    """
    try:
        vfile = open(vandbfile,'r')
        lines = vfile.readlines()
        vfile.close()
    except IOError as ioe:
        return (False, str(ioe))
        
    # parse title line
    titlelist = []
    for iline in xrange(len(lines)):
        line = lines[iline]
        line = line.strip()

        # skip the comment line and empty line
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
    # ENDFOR(iline)

    # parse an example line
    examples = []
    errmsg = ""
    numvanruns = 0
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
            errmsg += "Line \n'%s'\nhas different number of items %d from titles %d.\n" % (line, len(datarow),
                len(titlelist))
            continue
        
        examples = datarow
        break
    # ENDFOR

    return (titlelist, examples)
    

class AutoVanadiumCalibrationLocator:
    """ Class to locate calibration file automatically
    """
    def __init__(self, ipts, basepath="/SNS/VULCAN/", vrecordfile=None, autorecordfile=None):
        """ Initialization
        Arguments:
         - ipts     :: ipts number
         - basepath :: base data path
         - vrecordfile :: name of the vanadium runs record file
         - autorecordfile :: name of experiment record file, i.e., 'AutoRecord.txt'
        """
        # check whether the IPTS exist
        iptsgood, msg = checkIPTSExist(ipts, basepath)
        if iptsgood is False:
            raise NotImplementedError("IPTS %d does not exist for VULCAN. FYI: %s" % (ipts, msg))
        
        # ipts number
        self._ipts = ipts
        
        # import v-record
        if vrecordfile is None:
            vrecordfile = locateVulcanVRecordFile(basepath)
        if os.path.isfile(vrecordfile) is False:
            raise NotImplementedError("VRecord file %s does not exist." % (vrecordfile))
        self._importVRecord(vrecordfile)
        
        # import auto record
        if autorecordfile is None:
            autorecordfile = locateVulcanExpRecordFile(ipts, basepath)
        if os.path.isfile(autorecordfile) is False:
            raise NotImplementedError("Experiment record file %s does not exist." % 
                    (autorecordfile))
        self._importExperimentRecord(autorecordfile)
        
        # runs
        self._runs = []
        
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
            run = int(run)
            if self._expRecordDict.has_key(run):
                self._runs.append(run)
                numrunsadded += 1
            else:
                errmsg += "Run %d does not exist in IPTS %d (record file)\n" % (run, self._ipts)
        # ENDFOR
        
        return (numrunsadded, errmsg)


    def getVanRunLogs(self, logname):
        """ Get a specific log's value of all vanadium runs
        Arguments:
         - logname :: string as the name of the log to have value exported

        Return :: dictionary (key: run, value: log value)
        """
        rdict = {}
        for run in self._vanRecordDict.keys():
            rdict[run] = self._vanRecordDict[run][logname]

        return rdict
        
        
    def locateCalibrationFile(self, criterion):
        """ Locate matched vanadium runs for each run added to this instance

        Arguments
         - criterion :: list of the criterion to match between run and 

        Return :: dictionary (key = run number, value = vanadium runs)
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
            numfail = 0
            for (logname, valuetype) in criterion:
                try: 
                    cvalue = self._expRecordDict[run][logname]
                except KeyError as e:
                    print "[DB300] Log %s is not supported in Vulcan auto log." % (logname)
                    numfail += 1
                    continue

                #print "Run %d Match log %s = %s." % (run, logname, cvalue)
                for vanrun in vancadidaterunlist:
                    good = False
                    vanvalue = self._vanRecordDict[vanrun][logname]
                    #print "\tVanadium %d log %s = %s." % (vanrun, logname, vanvalue)
                    if valuetype.startswith('int'):
                        if int(cvalue) == int(vanvalue):
                            good = True
                    elif valuetype.startswith('str'):
                        good = (cvalue == vanvalue)
                    elif valuetype.startswith('float'):
                        if abs(float(cvalue)-float(vanvalue)) < 1.:
                            good = True
                    else:
                        raise NotImplementedError("Value type %s is not supported. " % (valuetype))
                    
                    if good is False:
                        vancadidaterunlist.remove(vanrun)
            # ENDFOR (criterion)

            if numfail == len(criterion):
                raise NotImplementedError("None of the log name in criterion is supported by Vulcan's auto log.")
            
            if len(vancadidaterunlist) == 0:
                # unable to find vanadium run to match
                print "Error: There is no match for run %d. " % (run)
            else:
                # find one or more vanadium runs. sorted with reversed order (new on top)
                runvandict[run] = sorted(vancadidaterunlist, reverse=True)

                if len(vancadidaterunlist) > 1:
                    print "There are too many vanadium runs (%d out of %d) matching to run %d.  \
                            The latest vnadium run is picked up. " % (
                                    len(vancadidaterunlist), len(self._vanRecordDict.keys()), run)
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
            line = lines[iline]
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
        errmsg = ""
        numvanruns = 0
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
                errmsg += "Line \n'%s'\nhas different number of items %d from titles %d.\n" % (line, len(datarow),
                    len(titlelist))
                continue

            numvanruns += 1
            dataset.append(datarow)
        # ENDFOR

        print "Number of vanadium runs added = %d" % (numvanruns)
            
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

        # error message
        if len(errmsg) > 0:
            print "Error during import vanadium profile data: \n", errmsg, "\n"
        
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
            line = lines[iline].strip()
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
        errmsg = ""
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
                errmsg += "Line \n'%s'\nhas different number of items %d from titles %d.\n" % (line, len(datarow),
                    len(titlelist))
                continue

            # add to data set
            dataset.append(datarow)
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

        # output error message
        if len(errmsg) > 0: 
            print "Error during importing AutoRecord.txt:\n%s\n" % (errmsg)

        print "There are %d runs that are found in record file %s." % (len(self._expRecordDict.keys()), exprecfile)
        
        return 
        
