################################################################################
# Facility utility
################################################################################
import os
import time

SUPPORTEDINSTRUMENT = ['vulcan']
SUPPORTEDINSTRUMENT_SHORT = ['vul']

class FacilityUtilityHelper(object):
    """ Helper class to find data and etc in a facility and instrument
    """
    def __init__(self, instrument):
        """ Initialize including set instrument

        Exception: NotImplementedError, TypeError
        """
        # Validate input
        if isinstance(instrument, str) is False:
            raise TypeError("Input instrument is not a string as requested, but of type %s." % (
                str(type(instrument))))

        # Standard is to use lower cases
        instrument = instrument.lower()

        # Set instrument
        if instrument in SUPPORTEDINSTRUMENT:
            self._instrumentName = instrument
        elif instrument in SUPPORTEDINSTRUMENT_SHORT:
            self._instrumentName = SUPPORTEDINSTRUMENT[SUPPORTEDINSTRUMENT_SHORT.index(instrument)]
        else:
            raise NotImplementedError("Instrument %s is not supported." % (instrument))

        # Other class variables
        self._dataRootPath = ""
        self._iptsNo = None

        return


    def getFilesInfo(self, filenamelist):
        """ Get files' information
        """
        timelist = []
        for filename in filenames:
            # modification time: return is float
            mod_time = os.path.getmtime(filename)
            create_time = os.path.getctime(filename)
            timelist.append((create_time, filename))

            #... print mod_time, create_time, mod_time-create_time
            create_time = time.ctime(create_time) # as string

            create_time = time.strptime(create_time)
            #... print create_time, type(create_time)

        # Sort time
        timelist = sorted(timelist)

        deltaT = 3600*24
        for i in xrange(len(timelist)-1):
            d_epoch = timelist[i+1][0] - timelist[i][0]
            if d_epoch > deltaT:
                print "Delta Day = %.2f" % (d_epoch/deltaT)

        return timelist

    def get_run_info(self, ipts_number):
        """

        :param ipts_number:
        :return:
        """
        # TODO - Docs
        ipts_home_dir = os.path.join(self._dataRootPath, 'IPTS-%d/data' % (ipts_number))
        run_tup_list = self.get_run_info_dir(ipts_home_dir)

        assert(isinstance(run_tup_list, list))
        print '[DB] Get %d runs from directory %s.' % (len(run_tup_list), ipts_home_dir)

        return run_tup_list

    def get_run_info_dir(self, ipts_home_dir):
        """
        :exception: RuntimeError for non-existing IPTS
        :rtype: list
        :param ipts_number:
        :return: list of 3-tuples
        """
        # Get home directory for IPTS
        if os.path.exists(ipts_home_dir) is False:
            raise RuntimeError('IPTS directory %s cannot be found.' % ipts_home_dir)

        # List all files
        all_file_list = os.listdir(ipts_home_dir)
        run_tup_list = []
        for file_name in all_file_list:
            # skip non-event Nexus file
            if file_name.endswith('_event.nxs') is False:
                continue
            else:
                full_path_name = os.path.join(ipts_home_dir, file_name)

            # get file information
            ipts_number, run_number = getIptsRunFromFileName(file_name)
            create_time = os.path.getctime(full_path_name)
            # NOTE: This is a fix to bad /SNS/ file system
            modify_time = os.path.getmtime(full_path_name)
            if modify_time < create_time:
                create_time = modify_time

            # add to list for return
            run_tup_list.append((run_number, create_time, full_path_name))
        # END-FOR

        return run_tup_list

    def searchRuns(self, deltaDays):
        """ Search files under IPTS imbed

        Exceptions: NotImplementedError, 

        Return: a list of list of 2-tuple.  
                Each element list contains runs that are in same experiment.  
                Element of sub list is 2-tuple as epoch time and file name with full path
        """
        # Check status
        if self._iptsNo is None:
            raise NotImplementedError('IPTS number has not been set up.')

        # List all the files
        datafiledir = os.path.join(self._iptsDir, 'data')
        filenamelist = []

        for filename in os.listdir(datafiledir): 
            if filename.endswith("_event.nxs") is True: 
                filename = os.path.basename(filename)
                filename = os.path.join(datafiledir, filename)
                filenamelist.append(filename)
        # ENDFOR

        # Get detailed creation time information: element is 2-tuple (epochtime, filename)
        timefilelist = []
        print "[DB] Number of files = ", len(filenamelist)
        for filename in filenamelist:
            create_time = os.path.getctime(filename)
            print "Creation time = ", create_time, filename
            timefilelist.append((create_time, filename))
        # ENDFOR
        timefilelist = sorted(timefilelist)

        # Find delta T more than 2 days
        # TODO : Need an elegant algorithm/method to set up the output list
        deltaT = deltaDays*24*3600.
        print "[DB] Delta T = %f" % (deltaT)

        periodlist = []
        sublist = [timefilelist[1]]
        timeprev = timefilelist[0][0]
       
        for i in xrange(1, len(timefilelist)):
            timenow = timefilelist[i][0]
            timediff = timenow-timeprev
            if  timediff < deltaT:
                # append current one to the list
                sublist.append(timefilelist[i])
            else:
                # start a new element in the period list as time are too sparse
                periodlist.append(sublist[:])
                # append first one 
                sublist = [timefilelist[i]]
                timeprev = timefilelist[i][0]
                print "[DB] Appending file %d  b/c time diff = %f" % (i, timediff)
            # ENDIF

        # ENDFOR
        periodlist.append(sublist)

        # DEBUG OUTPUT
        gindex = 0
        for sublist in periodlist:
            print "Group ", gindex, " Start @ ", sublist[0][0], " Size = ", len(sublist)
            gindex += 1

        return periodlist

    def setIPTS(self, ipts):
        """ Set ITPS 
        """
        self._iptsNo = ipts
        self._iptsDir = os.path.join(self._dataRootPath, 'IPTS-%d'%(ipts))

        return os.path.exists(self._iptsDir)

    def set_data_root_path(self, root_dir):
        """ Set up root path such as /SNS/ 

        Exception: 
        """
        # Determine 2 cases
        if root_dir.count(self._instrumentName.upper()) is False:
            self._dataRootPath = os.path.join(root_dir, self._instrumentName.upper())
        else:
            self._dataRootPath = root_dir

        if os.path.exists(self._dataRootPath) is False:
            raise RuntimeError('Data root directory %s is not accessible.' % self._dataRootPath)

        return

    def rollBack(self, epochtime):
        """ Roll time back to previous day
        """
        print "Ecoch time = ", epochtime, type(epochtime)

        stime = time.strptime(time.ctime(epochtime))
        print stime.tm_yday
        
        # FIXME - Delta T should be given!
        # NOTE : MOCK : 2 days
        rollbacktime = epochtime - 2*24*3600
        stime2 = time.strptime(time.ctime(rollbacktime))
        print stime2.tm_yday

        return 

# ENDCLASS

################################################################################
# External Methods
################################################################################

def convert_to_epoch(m_date, m_time="00:00:00", date_pattern='%m/%d/%Y',
                     time_pattern='%H:%M:%S'):
    """
    :param m_date:
    :param m_time:
    :param date_pattern:
    :param time_pattern:
    :return:
    """
    # Form datetime and pattern
    date_time = '%s %s' % (m_date, m_time)
    pattern = '%s %s' % (date_pattern, time_pattern)

    # Convert to epoch
    try:
        epoch = int(time.mktime(time.strptime(date_time, pattern)))
    except ValueError as e:
        raise e

    return epoch

def convert_to_date_from_epoch(epoch_time, next_day=False):
    """
    :param epoch_time:
    :param next_day:
    :return: 3-tuple (year, month, date)
    """
    # FIXME - Make this correct!
    #  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
    # Out[8]: '2015-08-01 00:00:00'

    year = 2015
    month = 4
    day = 9

    return year, month, day

def getIptsRunFromFileName(nxsfilename):
    """ Get IPTS number from a standard SNS nexus file name
    
    Return :: tuple as 2 int, IPTS and run number
    """
    basename = os.path.basename(nxsfilename)

    # Get IPTS
    if basename == nxsfilename:
        # not a full path
        ipts = None
    else:
        # Format is /SNS/VULCAN/IPTS-????/0/NeXus/VULCAN_run... 
        ipts = int(nxsfilename.split('IPTS-')[1].split('/')[0])

    # Get run number
    runnumber = int(basename.split('_')[1])

    return (ipts, runnumber)





def setGPDateTime(epochtime):
    """ Reset epoch time to standard end time
    Link: http://www.tutorialspoint.com/python/time_strptime.htm
    """
    if isinstance(epochtime, float) is False:
        raise TypeError("Epoch time must be float.  Use getmtime() or getctime().")

    sttime = time.strptime(time.ctime(epochtime))
    rollbackdays = 0
    # set hour to 12 or 15  
    if sttime.tm_hour < 9:
        rollbackdays = 1
        newhour = 15
    elif sttime.tm_hour >= 15:
        newhour = 15
    else:
        # only between 9 and 15 will be 12
        newhour = 12

    # roll back if needed
    epochtime -= rollbackdays*24*3600

    # get new wday
    sttime = time.strptime(time.ctime(epochtime))
    if sttime.tm_wday >= 5:
        rollbackdays = sttime.tm_wday-4
        # print "[DB] Rolls back for %d days" % (rollbackdays)
        epochtime -= rollbackdays*24*3600
        # if rolling back, the hour should be modified
        newhour = 15

    # set the new date by new hour
    newsttime = time.strptime(time.ctime(epochtime))
    year =  newsttime.tm_year
    month = newsttime.tm_mon
    day =   newsttime.tm_mday
    hour = newhour

    tformat = "%Y %m %d %H"
    newtime = time.strptime("%d %02d %02d %02d"%(year, month, day, hour), tformat)
    print newtime

    return


def testmain():
    """
    """
    mhelper = FacilityUtilityHelper('vulcan')
    mhelper.set_data_root_path('/SNS/')
    exists = mhelper.setIPTS(12240)
    if exists is False:
        print "IPTS 12240 does not exist."
        sys.exit(1)

    filenames = mhelper.searchRuns()
    timelist = mhelper.getFilesInfo(filenames)
    mhelper.rollBack(timelist[0][0])

    timeformat = "%Y-%m-%d %H:%M:%S"

    time1 = time.strptime("2015-02-06 19:31:24", timeformat)
    print time1
    setGPDateTime(time.mktime(time1))
    print

    time1 = time.strptime("2015-02-06 12:31:24", timeformat)
    print time1
    setGPDateTime(time.mktime(time1))
    print
    
    time1 = time.strptime("2015-02-08 12:31:24", timeformat)
    print time1
    setGPDateTime(time.mktime(time1))
    print
    
    time1 = time.strptime("2015-02-09 07:31:24", timeformat)
    print time1
    setGPDateTime(time.mktime(time1))
    print


def utilmain(argv):
    """ Get a list of runs under an IPTS    
    """
    mhelper = FacilityUtilityHelper('vulcan')
    mhelper.set_data_root_path('/SNS/')
    exists = mhelper.setIPTS(10076)
    if exists is False:
        print "IPTS 12240 does not exist."
        sys.exit(1)

    timefilenamelistlist = mhelper.searchRuns(100000)

    # suppose only 1 item in list
    timefilenamelist = sorted(timefilenamelistlist[0])

    wbuf = ""
    for timefilename in timefilenamelist:
        wbuf += "%s\n" % (timefilename[1])

    ofile = open("List10076.txt", "w")
    ofile.write(wbuf)
    ofile.close()




if __name__ == "__main__":
    """ Testing
    """
    import sys

    utilmain(sys.argv)
