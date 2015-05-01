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


    def searchRuns(self):
        """ Search files under IPTS imbed

        Exceptions: NotImplementedError, 
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

        # TODO 1: Get detailed creation time information

        # TODO 2: Find delta T more than 2 days

        # TODO 3: Split Files into different groups and get the begin and end time 

        return sorted(filenamelist)


    def setIPTS(self, ipts):
        """ Set ITPS 
        """
        self._iptsNo = ipts
        self._iptsDir = os.path.join(self._dataRootPath, 'IPTS-%d'%(ipts))

        return os.path.exists(self._iptsDir)


    def setRootPath(self, root):
        """ Set up root path such as /SNS/ 

        Exception: 
        """
        if self._instrumentName == "vulcan":
            self._dataRootPath = os.path.join(root, 'VULCAN')
        else:
            raise NotImplementedError('Instrument %s is not supported.'%(self._instrumentName))

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


if __name__ == "__main__":
    """ Testing
    """
    import sys

    mhelper = FacilityUtilityHelper('vulcan')
    mhelper.setRootPath('/SNS/')
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
