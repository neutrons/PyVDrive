################################################################################
# Facility utility
################################################################################
import os
import time
import pickle

import vdrivehelper

SUPPORTED_INSTRUMENT = ['VULCAN']
SUPPORTED_INSTRUMENT_SHORT = ['VUL']


class DataArchiveManager(object):
    """ Helper class to find data and etc in the archive of an SNS instrument
    """
    def __init__(self, instrument):
        """ Initialize including set instrument

        Exception: NotImplementedError, TypeError
        """
        # Check requirements and set instrument
        assert isinstance(instrument, str), \
            'Input instrument is not a string as requested, but of type %s.' % (
                str(type(instrument)))

        # Standard is to use lower cases
        instrument = instrument.upper()
        assert instrument in SUPPORTED_INSTRUMENT or instrument in SUPPORTED_INSTRUMENT_SHORT, \
            'Instrument %s is not supported.' % instrument

        self._instrumentName = instrument

        # Set default data archive
        self._archiveRootDirectory = '/SNS/%s' % self._instrumentName

        # Other class variables
        self._iptsNo = None

        return

    @property
    def root_directory(self):
        """ Root archive directory
        :return:
        """
        # TODO/NOW/DOC
        return self._archiveRootDirectory

    @root_directory.setter
    def root_directory(self, value):
        """ Set archive's root directory
        Purpose:

        Requirements:


        :param value:
        :return:
        """
        # TODO/NOW/DOC
        # check requirements
        assert True

        # set
        self._archiveRootDirectory = value

    def get_data_root_dir(self):
        """
        Get default data root directory
        :return:
        """

    def getFilesInfo(self, file_name_list):
        """ Get files' information
        :param file_name_list: list of string of file names
        :return: a list of 2-tuple (time as creation time, string as file name)
        """
        timelist = []
        for filename in file_name_list:
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
        Get runs' information of an IPTS
        :param ipts_number: integer as IPTS number
        :return: list of 3-tuples
        """
        ipts_home_dir = os.path.join(self._archiveRootDirectory, 'IPTS-%d/data' % ipts_number)
        print '[DB] IPTS dir is %s' % ipts_home_dir

        run_tup_list = self.get_run_info_dir(ipts_home_dir)

        assert(isinstance(run_tup_list, list))
        print '[DB] Get %d runs from directory %s.' % (len(run_tup_list), ipts_home_dir)

        return run_tup_list

    def get_run_info_dir(self, ipts_home_dir):
        """
        Get information of runs in a directory.
        :exception: RuntimeError for non-existing IPTS
        :rtype: list
        :param ipts_home_dir:
        :return: list of 3-tuples (integer as run number, time as creation time, string as full path)
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
            ipts_number, run_number = vdrivehelper.getIptsRunFromFileName(file_name)
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
        self._iptsDir = os.path.join(self._archiveRootDirectory, 'IPTS-%d'%(ipts))

        return os.path.exists(self._iptsDir)

    def set_data_root_path(self, root_dir):
        """ Set up root path such as /SNS/ 

        Exception: 
        """
        # Determine 2 cases
        if root_dir.count(self._instrumentName.upper()) is False:
            self._archiveRootDirectory = os.path.join(root_dir, self._instrumentName.upper())
        else:
            self._archiveRootDirectory = root_dir

        if os.path.exists(self._archiveRootDirectory) is False:
            raise RuntimeError('Data root directory %s is not accessible.' % self._archiveRootDirectory)

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

# END-CLASS


################################################################################
# External Methods
################################################################################







def load_from_xml(xml_file_name):
    """

    :param xml_file_name:
    :return:
    """
    #import pprint
    pkl_file = open(xml_file_name, 'rb')

    save_dict = pickle.load(pkl_file)
    # pprint.pprint(save_dict)

    pkl_file.close()

    return save_dict

def save_to_xml(save_dict, xml_file_name):
    """
    Save a dictionary to an XML file
    :param save_dict:
    :param xml_file_name:
    :return:
    """
    # FIXME - Before the GUI tool is developed, python pickle is used temporarily
    import pickle

    output = open(xml_file_name, 'wb')

    # Pickle dictionary using protocol 0.
    pickle.dump(save_dict, output)

    # Pickle the list using the highest protocol available.
    # pickle.dump(selfref_list, output, -1)

    output.close()

    return



def testmain():
    """
    """
    mhelper = DataArchiveManager('vulcan')
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
    mhelper = DataArchiveManager('vulcan')
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
