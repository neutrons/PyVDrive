####
# Utility methods for VULCAN
####
import os
import math
import mantid_helper


def export_vanadium_intensity_to_file(van_nexus_file, gsas_van_int_file):
    """
    export a vanadium to intensity file, whic is of GSAS format
    NOTE: THIS IS VERY INSTRUMENT GEOMETRY SENSITIVE!
    :param van_nexus_file:
    :param gsas_van_int_file:
    :return:
    """
    # check
    assert isinstance(van_nexus_file, str), 'Vanadium NeXus file {0} must be a string but not a {1}.' \
                                            ''.format(van_nexus_file, type(van_nexus_file))
    if os.path.exists(van_nexus_file) is False:
        raise RuntimeError('Given vanadium NeXus path {0} is incorrect.'.format(van_nexus_file))

    assert isinstance(gsas_van_int_file, str), 'Target GSAS vanadium intensity file {0} must be a string but not a ' \
                                               '{1}.'.format(gsas_van_int_file, type(gsas_van_int_file))

    # write to file
    try:
        int_file = open(gsas_van_int_file, 'w')
    except IOError as io_err:
        raise RuntimeError('Unable to write to file {0} due to {1}'.format(gsas_van_int_file, io_err))
    except OSError as os_err:
        raise RuntimeError('Unable to write to file {0} due to {1}'.format(gsas_van_int_file, os_err))

    # load data file
    out_file_name = os.path.basename(van_nexus_file).split('.')[0]
    mantid_helper.load_nexus(data_file_name=van_nexus_file, output_ws_name=out_file_name, meta_data_only=False)
    event_ws = mantid_helper.retrieve_workspace(out_file_name)

    # Parse to intensity file
    int_buf = ''
    # num_spec = event_ws.getNumberHistograms()
    det_count = 0

    for row_index in range(0, 1224 + 1, 8):
        pack_index_west = range(0, 2464 + 1, 1232)
        pack_index_east = range(3696, 6160 + 1, 1232)
        pack_index_both = pack_index_west + pack_index_east
        for pack_index in pack_index_both:
            for i_ws in range(8):
                ws_index = row_index + pack_index + i_ws

                num_events = event_ws.getEventList(ws_index).getNumberEvents()
                # format to float with 8 significant digit
                format_event_str = format_float_number(num_events, 8)

                int_buf += '{0:>16}'.format(format_event_str)
                # start a new line at 8th detector's count
                if det_count == 8 * 6 - 1:
                    int_buf += '\n'
                    det_count = 0
                else:
                    det_count += 1
                    # END-FOR
    # END-FOR

    int_file.write(int_buf)
    int_file.close()

    return


def format_float_number(value, significant_digits):
    """
    format a number (integer or float) into a string with specified significant digit
    :param value:
    :param significant_digits:
    :return:
    """
    # check input
    assert isinstance(value, int), 'Input value {0} must be integer but cannot be {1}.'.format(value, type(value))
    assert isinstance(significant_digits, int) and significant_digits > 0,\
        'Significant digit {0} must be a positive integer but not a {1}.' \
        ''.format(significant_digits, type(significant_digits))

    # make sure the input is a float
    value = float(value)
    if abs(value) < math.pow(10., significant_digits):
        # contain decimal point
        format_str = '{0:.7f}'.format(value)
        assert format_str.count('.') == 1, 'If value is within {0}, decimal points must be in {1}.' \
                                           ''.format(math.pow(10., significant_digits), format_str)
        # trim to significant digits
        format_str = format_str[:significant_digits+1]
    else:
        # number is larger than 10^8, which is not likely to happen.
        raise RuntimeError('Not implemented because it is not thought possible!')

    return format_str


def get_default_binned_directory(ipts_number, check_write_and_throw=False):
    """
    get VDRIVE default directory for binned data
    :param ipts_number: IPTS number in integer
    :param check_write_and_throw: check whether the user has write permission and thus throw if not
    :return:
    """
    # check
    assert isinstance(ipts_number, int), 'IPTS number {0}  must be an integer but not a {1}.' \
                                         ''.format(ipts_number, type(ipts_number))

    # get directory
    binned_dir = '/SNS/VULCAN/IPTS-{0}/shared/binned_data/'.format(ipts_number)

    # check write permission
    if check_write_and_throw:
        if os.path.exists(binned_dir) is False:
            raise RuntimeError('VULCAN binned data directory {0} does not exist.'.format(binned_dir))
        if os.access(binned_dir, os.W_OK) is False:
            raise RuntimeError('User has no write permission to directory {0}.'.format(binned_dir))

    return binned_dir


def get_vulcan_record(ipts_number, auto):
    """
    Get ITPS number
    :param ipts_number:
    :param auto: auto record or legacy VULCAN record
    :return: vulcan record file or False for non-exiting file
    """
    # check
    assert isinstance(ipts_number, int), 'IPTS number %s must be an integer but not %s.' \
                                         '' % (str(ipts_number), str(type(ipts_number)))
    assert isinstance(auto, bool)

    # get vulcan file
    if auto:
        record_file_name = '/SNS/VULCAN/IPTS-%d/shared/AutoRecord.txt' % ipts_number
    else:
        record_file_name = '/SNS/VULCAN/IPTS-%d/shared/Record.txt' % ipts_number

    if not os.path.exists(record_file_name):
        return False

    return record_file_name


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

    return titlelist, examples


def import_vulcan_log(log_file_name):
    """
    Import VULCAN's standard log file in CSV format
    :param log_file_name:
    :return: pandas pandas.core.frame.DataFrame
    """
    import pandas as pd
    # check
    assert isinstance(log_file_name, str), 'Log file name %s must be a string but not of type %s.' \
                                           '' % (str(log_file_name), type(log_file_name))
    assert os.path.exists(log_file_name), 'Log file %s does not exist.' % log_file_name
    # use pandas to load the file

    # import
    log_set = pd.read_csv(log_file_name, sep='\t', header=0)

    # check
    assert len(log_set) > 1, 'Separation is not tab for VULCAN record file %s.' % log_file_name

    return log_set


def search_vulcan_runs(record_data, start_time, end_time):
    """
    Search runs from Pandas data loaded from record file according to time.
    :param record_data:
    :param start_time:
    :param end_time:
    :return:
    """


def locateRun(ipts, runnumber, basepath='/SNS/VULCAN/'):
    """ Add a list of run numbers and check whether they are valid or not.
    """
    errmsg = ""

    # build the name according to the convention
    run = int(runnumber)
    relpathname = "IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs" % (ipts, run, run)
    # FIXME - ASAP
    raise NotImplementedError('ASAP {0} is an old file path.'.format(relpathname))
    nxsfilename = os.path.join(basepath, relpathname)

    # check existence of file
    if os.path.isfile(nxsfilename) is False:
        good = False
        errmsg = "Run %d does not exist in IPTS %d.  NeXus file cannot be found at %s. " % (run, ipts, nxsfilename)
        return (False, errmsg)

    return (True, nxsfilename)


class AutoVanadiumCalibrationLocator(object):
    """ Class to locate Vanadium calibration file automatically
    """
    def __init__(self, ipts, base_path='/SNS/VULCAN/', vrecordfile=None, autorecordfile=None):
        """ Initialization
        Arguments:
         - ipts     :: ipts number
         - basepath :: base data path
         - vrecordfile :: name of the vanadium runs record file
         - autorecordfile :: name of experiment record file, i.e., 'AutoRecord.txt'
        """
        # IPTS
        assert isinstance(ipts, int)
        self._iptsNumber = ipts

        # root path to data archive
        assert isinstance(base_path, str)
        assert os.path.exists(base_path)
        self._rootArchiveDirectory = base_path

        # check access to IPTS
        is_ipts_valid, message = self.check_ipts_valid()
        if is_ipts_valid is False:
            raise RuntimeError('IPTS %d does not exist for VULCAN. FYI: %s' % (ipts, message))

        # set up v-record file
        if vrecordfile is None:
            vrecordfile = self.locate_vulcan_vanadium_record_file()
        else:
            assert isinstance(vrecordfile, str)
            assert os.path.exists(vrecordfile), 'User specified V-record file %s cannot be found.' % vrecordfile
        
        # import v-record
        self._importVRecord(vrecordfile)
        
        # import auto record
        if autorecordfile is None:
            autorecordfile = self.locate_auto_record()
        else:
            assert isinstance(autorecordfile, str)
            assert os.path.exists(autorecordfile), 'User specified AutoRecord file %s cannot be found.' % autorecordfile
        self._importExperimentRecord(autorecordfile)
        
        # runs
        self._runs = []
        
        return

    @property
    def ipts_number(self):
        """
        :return: IPTS number
        """
        return self._iptsNumber
       
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
                errmsg += "Run %d does not exist in IPTS %d (record file)\n" % (run, self._iptsNumber)
        # ENDFOR
        
        return numrunsadded, errmsg

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
        # Check input's validity
        if isinstance(criterion, list) is False:
            raise NotImplementedError('Input argument criterion is not List')
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

    def locate_vulcan_vanadium_record_file(self):
        """ Get the path and name of a VULCAN's vanadium record file
        Purpose:
            locate the v-record file from archive under shared/Calibrationfiles/Instrument/Standard/Vanadium
        Requirements:
            root data archive path exists
        Guarantees:
            an accessible file path is returned
        :return: string as full path to v-record file
        """
        # check requirements: no need as the check is done in __init__()

        rel_path = "shared/Calibrationfiles/Instrument/Standard/Vanadium"
        rel_path_v_name = os.path.join(rel_path, "VRecord.txt")
        vrecord_filename = os.path.join(self._rootArchiveDirectory, rel_path_v_name)

        return vrecord_filename

    def locate_auto_record(self):
        """ Get the path and name of a VULCAN's experiment record file, i.e., AutoRecord.txt
        Purpose:
            get the full path to an IPTS's auto record file
        Requirements:
            input IPTS is valid and root path exists
        Guarantees:
            return the full path to AutoRecord.txt of the given IPTS
        """
        # there is no need to check requirement because __init__() check it already
        rel_path = "IPTS-%d/shared/" % (int(ipts))
        rel_path_name = os.path.join(rel_path, "AutoRecord.txt")
        exprecordfilename = os.path.join(self._rootArchiveDirectory, rel_path_name)

        return exprecordfilename

    def check_ipts_valid(self):
        """ Check whether an IPTS number is valid
        """
        ipts_dir = os.path.join(self._rootArchiveDirectory, "IPTS-%d" % (self._iptsNumber))
        if os.path.isdir(ipts_dir) is True:
            return True, ''

        msg = "IPTS directory: %s does not exist." % ipts_dir

        return False, msg


if __name__ == '__main__':
    van_file = '/SNS/VULCAN/IPTS-18420/0/136771/NeXus/VULCAN_136771_event.nxs'
    out_name = '/tmp/van136771.int'
    export_vanadium_intensity_to_file(van_file, out_name)
