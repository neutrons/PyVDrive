################################################################################
# Facility utility
################################################################################
import os
import time
import pickle

import mantid_helper
import vdrivehelper
import vulcan_util

SUPPORTED_INSTRUMENT = {'VULCAN': 'VULCAN'}
SUPPORTED_INSTRUMENT_SHORT = {'VUL': 'VULCAN'}


class DataArchiveManager(object):
    """ Class to manage data files, especially data files in the archive of an SNS instrument
    """
    def __init__(self, instrument):
        """ Initialize including set instrument
        Purpose:
            Initialize the instance and set up defaults
        Requirements:
            Input name of instrument must be a supported one
        Guarantees:
            A data archive manager is initialized

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

        # Instrument name is for archive purpose
        if instrument in SUPPORTED_INSTRUMENT:
            self._dataArchiveInstrumentName = SUPPORTED_INSTRUMENT[instrument]
        else:
            self._dataArchiveInstrumentName = SUPPORTED_INSTRUMENT_SHORT[instrument]

        # Set default data archive
        self._archiveRootDirectory = '/SNS/%s' % self._dataArchiveInstrumentName

        # Other class variables
        # ipts number of type integer
        self._iptsNo = None
        # ipts data directory such as /SNS/VULCAN/IPTS-1234/data
        self._iptsDataDir = None
        # ipts root data directory such as /SNS/VULCAN/IPTS-1234/
        self._iptsRootDir = None
        # flag to see whether data are stored in local computer
        self._localData = False

        # data storage
        self._infoDict = dict()     # key: archive ID
        self._runInfoDict = dict()  # key: run number

        # Debug mode
        self.__DEBUG__ = False

        return

    # Properties
    @property
    def root_directory(self):
        """ Root archive directory
        Purpose:
            Get root data archive directory.  For example, /SNS/VULCAN/
        Requirements:
            It is accessible
        Guarantees:
            The root archive directory will be returned
        :return:
        """
        # Check requirements:
        assert os.path.exists(self._archiveRootDirectory), 'Root archive directory %s is not accessible.' % self._archiveRootDirectory

        return self._archiveRootDirectory

    @root_directory.setter
    def root_directory(self, value):
        """ Set archive's root directory
        Purpose:
            Set up the root archiving directory
        Requirements:
            Value must be a file path and accessible
        Guarantees:
            Give file path is set to root
        :param value:
        :return:
        """
        # check requirements
        assert isinstance(value, str), \
            'Input value for root directory must be of string type. Given is %s' % str(type(value))
        assert os.path.exists(value), 'Input root path %s does not exist.' % value

        # set
        self._archiveRootDirectory = value

        return

    @staticmethod
    def get_data_archive_chopped_gsas(ipts_number, run_number, chop_seq):
        """
        get chopped data from GSAS file stored in archive server
        :param ipts_number:
        :param run_number:
        :param chop_seq:
        :return:
        """
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'

        chop_data_dir = '/SNS/VULCAN/IPTS-%d/shared/ChoppedData/' % ipts_number

        return DataArchiveManager.get_data_chopped_gsas([chop_data_dir], run_number, chop_seq)

    @staticmethod
    def get_data_archive_gsas(ipts_number, run_number):
        """
        get reduced data from GSAS file stored on archive server
        :param ipts_number:
        :param run_number:
        :return: list of data or None (cannot find)
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'
        assert isinstance(run_number, int), 'Run number must be an integer.'

        # check whether the IPTS/run is valid
        nexus_dir = '/SNS/VULCAN/IPTS-%d/0/%d/' % (ipts_number, run_number)
        if not os.path.exists(nexus_dir):
            return None

        # locate reduced GSAS file name
        gsas_file_name = os.path.join('/SNS/VULCAN/IPTS-%d/shared/binned_data' % ipts_number, '%d.gda' % run_number)
        if not os.path.exists(gsas_file_name):
            return None

        # get data
        data_set = mantid_helper.get_data_from_gsas(gsas_file_name)

        return data_set

    @staticmethod
    def get_data_chopped_gsas(search_dirs, run_number, chop_seq):
        """
        get chopped data from GSAS files in designated directories.
        :param search_dirs: list of strings
        :param run_number:
        :param chop_seq:
        :return: dictionary of reduced data. keys are spectral numbers.
        """
        assert isinstance(search_dirs, list), 'Search directories must be a list of strings.'
        assert len(search_dirs) > 0, 'There must be at least 1 diretory to search for chopped data.'
        assert isinstance(run_number, int), 'Run number %s must be an integer.' % str(run_number)
        assert isinstance(chop_seq, int), 'Chop sequence %s must be a non-negative integer.' % str(chop_seq)

        # search GSAS file (seq.gda) under given directories
        found = False
        chop_gsas_name = None
        for parent_dir in search_dirs:
            chop_dir = os.path.join(parent_dir, '%d' % run_number)
            chop_gsas_name = os.path.join(chop_dir, '%d.gda' % chop_seq)
            if os.path.exists(chop_gsas_name):
                found = True
                break
        # END-FOR

        if not found:
            raise RuntimeError('Unable to locate chopped run %d seq %d from these directories: %s.'
                               '' % (run_number, chop_seq, str(search_dirs)))

        # parse gsas
        assert chop_gsas_name is not None, 'It is impossible to have a None value of GSAS file name here.'
        data_set = mantid_helper.get_data_from_gsas(chop_gsas_name)

        return data_set

    def get_experiment_run_info(self, archive_key, start_run=None, end_run=None):
        """ Get runs' information of an IPTS
        Purpose:
            Get data path information for all runs of an IPTS number
        Requirements
            A valid IPTS-number is set before
        Guarantees:
            Experimental run information including run number, creation time and full file path will be returned

        :param archive_key:
        :param start_run:
        :param end_run:
        :param sort_by:
        :return: list of dictionary
        """
        # check
        assert isinstance(archive_key, str), 'Archive key %s must be a string but not %s.' \
                                             '' % (str(archive_key), type(archive_key))
        assert archive_key in self._infoDict, 'Archive key %s does not exist in archiving dictionary,' \
                                              'which has keys %s.' % (str(archive_key), str(self._infoDict.keys()))

        # Get run information
        if start_run is None and end_run is None:
            run_dict_list = self._infoDict[archive_key][:]
        else:
            run_dict_list = self.get_partial_run_info(archive_key, start_run, end_run)
        # END-IF

        return run_dict_list

    def get_partial_run_info(self, archive_key, start_run, end_run):
        """
        Get a subset of runs (with all information) by specified range of run numbers
        :param archive_key:
        :param start_run:
        :param end_run:
        :return:
        """
        # check
        assert isinstance(archive_key, str), 'Archive key %s must be a string but not %d.' \
                                             '' % (str(archive_key), type(archive_key))
        assert isinstance(start_run, int) and isinstance(end_run, int) and start_run <= end_run, \
            'start run %s (%s vs int) must be less or equal to end run %s (%d vs int).' \
            '' % (str(start_run), type(start_run), str(end_run), type(end_run))

        # get partial list
        partial_list = list()
        for run_dict in self._infoDict[archive_key]:
            if start_run <= run_dict['run'] <= end_run:
                partial_list.append(run_dict)

        return partial_list

    def get_experiment_run_info_from_archive(self, directory, start_run, end_run):
        """ Get information of standard SNS event NeXus files in a given directory.
        Purpose:
            Get full path of a subset of NeXus files from a directory according to given run number
        Requirements:
            Given directory does exist
        Guarantees:
            Experimental run information including run number, creation time and full file path will be returned
        Note:
            Data archiving might put wrong time stamps on the event NeXus files.  For example,
            the creation time sometime is later than modified time.  In this case,
            return the earliest time between creation time and modified time.

        :exception: RuntimeError for non-existing IPTS
        :rtype: list
        :param directory:
        :param start_run:
        :param end_run
        :return: list of 3-tuples (integer as run number, time as creation time, string as full path)
        """
        # Check requirements
        assert os.path.exists(directory), 'IPTS directory %s cannot be found.' % directory
        assert isinstance(start_run, int), 'Start run number should be an integer but is %s.' % str(type(start_run))
        assert isinstance(end_run, int), 'End run number should be an integer but is %s.' % str(type(end_run))
        assert start_run <= end_run, 'Start run %d must be less or equal to end run %d.' % (start_run, end_run)

        # Go through VULCAN_StartRun_event.nxs to VULCAN_EndRun_event.nxs, and get information for existing run
        # numbers, i.e., existing event file
        run_tup_list = list()
        for run_number in xrange(start_run, end_run+1):
            file_name = '%s_%d_event.nxs' % (self._dataArchiveInstrumentName, run_number)
            full_file_path = os.path.join(directory, file_name)

            # skip non-existing file
            if os.path.exists(full_file_path) is False:
                # print '[DB-BAT] Skip non-existing run number %d with name %s' % (run_number, full_file_path)
                continue

            # get file information
            # NOTE: This is a fix to bad /SNS/ file system in case the last modified time is earlier than creation time
            ipts_number, run_number = self.get_ipts_run_from_file_name(file_name)
            create_time = os.path.getctime(full_file_path)
            modify_time = os.path.getmtime(full_file_path)
            if modify_time < create_time:
                create_time = modify_time

            # add to list for return
            run_tup_list.append((run_number, create_time, full_file_path))
        # END-FOR

        return run_tup_list

    # Methods
    def get_files_time_information(self, file_name_list):
        """ Get files' information
        Purpose:
            Get the time information of a list of files
        Requirements:
            Given files do exist
        Guarantees:
            Creation time of given files are returned
        :param file_name_list: list of string of file names
        :return: a list of 2-tuple (time as creation time, string as file name)
        """
        # Check requirements
        assert isinstance(file_name_list, list), 'Input must be a list'

        time_file_list = list()

        for filename in file_name_list:
            # Check whether file exists
            assert os.path.exists(filename), 'Given file %s does not exist for file time information.' % filename

            # modification time: return is float
            # mod_time = os.path.getmtime(filename)
            # create_time = time.ctime(create_time) # as string
            # create_time = time.strptime(create_time)
            # After experiments, this is the most suitable way
            create_time = os.path.getctime(filename)
            time_file_list.append((create_time, filename))
        # END-FOR (file_name)

        # Sort list by time
        time_file_list = sorted(time_file_list)

        if self.__DEBUG__ is True:
            delta_t = 3600*24
            for i in xrange(len(time_file_list)-1):
                d_epoch = time_file_list[i+1][0] - time_file_list[i][0]
                if d_epoch > delta_t:
                    print "Delta Day = %.2f" % (d_epoch/delta_t)

        return time_file_list

    def get_local_run_info(self, archive_key, local_dir, begin_run, end_run, standard_sns_file):
        """
        Get the file information for data files stored in local directory
        :param archive_key:
        :param local_dir:
        :param begin_run:
        :param end_run:
        :param standard_sns_file:
        :return: run_info_dict_list
        """
        # check
        assert isinstance(archive_key, str), 'Archive key %s must be a string but not %s.' \
                                             '' % (str(archive_key), type(archive_key))
        assert isinstance(local_dir, str) and os.path.exists(local_dir), \
            'Local data directory %s (of type %s) must be a string and exist.' % (str(local_dir), type(local_dir))
        assert isinstance(begin_run, int) and isinstance(end_run, int) and begin_run < end_run

        # Info dictionary contains a list of dictionary
        # FIXME/TODO/now - IS THERE ANY EASY/EFFICIENT WAY TO FIND OUT RUN INFORMATION BY RUN NUMBER?
        print '[DB...BAT] : Archived information! ', self._infoDict[archive_key]

        for run_number in range(begin_run, end_run):
            # TODO/NOW/FIXME - continue from here!
            pass

    @staticmethod
    def get_ipts_run_from_file_name(nxs_file_name):
        """
        Get IPTS number from a standard SNS nexus file name
        :param nxs_file_name:
        :return: tuple as 2 integers, IPTS and run number
        """
        basename = os.path.basename(nxs_file_name)

        # Get IPTS
        if basename == nxs_file_name:
            # not a full path
            ipts = None
        else:
            # Format is /SNS/VULCAN/IPTS-????/0/NeXus/VULCAN_run...
            try:
                ipts = int(nxs_file_name.split('IPTS-')[1].split('/')[0])
            except IndexError:
                ipts = None

        # Get run number
        try:
            runnumber = int(basename.split('_')[1])
        except IndexError:
            runnumber = None
        except ValueError:
            runnumber = None

        return ipts, runnumber

    def get_ipts_number(self, run_number, throw):
        """
        Find out IPTS number from a run number
        :param run_number:
        :param throw: a flag to throw an exception if run number does not exist in current Run-Info dictionary.
        :return: IPTS number or None if not thrown
        """
        assert isinstance(run_number, int), 'Run number must be an integer.'

        if run_number in self._runInfoDict:
            ipts_number = self._runInfoDict[run_number]['ipts']
        elif not throw:
            ipts_number = None
        else:
            raise RuntimeError('Run number %d does not exist in current Run-Info-Dictionary' % run_number)

        return ipts_number

    def scan_archive(self, ipts_number, start_run, end_run):
        """
        Scan VULCAN archive
        :param ipts_number:
        :param start_run:
        :param end_run:
        :return:
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'
        assert isinstance(start_run, int), 'Start run number must be an integer.'
        assert isinstance(end_run, int), 'End run number must be an integer.'
        assert start_run <= end_run, 'Start run must be ahead of end run.'

        # form IPTS
        ipts_dir = os.path.join(self._archiveRootDirectory, 'IPTS-%d' % ipts_number)
        assert os.path.exists(ipts_dir), 'IPTS dir %s does not exist.' % ipts_dir

        # archive key:
        archive_key = 'IPTS-%d-%d-%d' % (ipts_number, start_run, end_run)
        self._infoDict[archive_key] = list()
        err_msg = ''

        # locate file
        for run_number in range(start_run, end_run+1):
            # form file
            nexus_file_name = os.path.join(ipts_dir, 'data/VULCAN_%d_event.nxs' % run_number)
            if os.path.exists(nexus_file_name):
                run_info = {'run': run_number,
                            'ipts': ipts_number,
                            'file': nexus_file_name,
                            'time': None}
                self._infoDict[archive_key].append(run_info)
            else:
                err_msg += 'Run %d does not exist in IPTS %s\n' % (run_number, ipts_number)
            # END-IF
        # END-FOR

        return archive_key, err_msg

    def scan_experiment_run_info(self, ipts_dir):
        """ Get information of standard SNS event NeXus files in a given directory.
        Purpose:
            Get full path of all SNS event NeXus files from a directory
        Requirements:
            Given directory does exist
        Guarantees:
            Experimental run information including run number, creation time and full file path will be returned
        Note:
            Data archiving might put wrong time stamps on the event NeXus files.  For example,
            the creation time sometime is later than modified time.  In this case,
            return the earliest time between creation time and modified time.

        :exception: RuntimeError for non-existing IPTS
        :rtype: list
        :param ipts_dir:
        :return: key to the dictionary
        """
        # check validity of inputs
        assert isinstance(ipts_dir, str) and os.path.exists(ipts_dir), \
            'IPTS directory %s (%s) cannot be found.' % (str(ipts_dir), str(type(ipts_dir)))

        # List all files
        all_file_list = os.listdir(ipts_dir)
        run_tup_list = []
        for file_name in all_file_list:
            # skip non-event Nexus file
            if file_name.endswith('_event.nxs') is False:
                continue
            else:
                full_path_name = os.path.join(ipts_dir, file_name)

            # get file information
            ipts_number, run_number = DataArchiveManager.get_ipts_run_from_file_name(file_name)

            # NOTE: This is a fix to bad /SNS/ file system in case the last modified time is earlier than creation time
            create_time = os.path.getctime(full_path_name)
            modify_time = os.path.getmtime(full_path_name)
            if modify_time < create_time:
                create_time = modify_time

            # add to list for return
            run_tup_list.append({'run': run_number,
                                 'ipts': ipts_number,
                                 'file': full_path_name,
                                 'time': create_time})
        # END-FOR

        self._infoDict[ipts_dir] = run_tup_list

        return ipts_dir

    def scan_vulcan_record(self, record_file_path):
        """
        Scan a VULCAN record file
        :param record_file_path:
        :return: key to a dictionary
        """
        # read the file
        record_file_set = vulcan_util.import_vulcan_log(record_file_path)

        # export the pandas log to a list of dictionary
        run_dict_list = list()
        num_runs = len(record_file_set)
        for i_run in range(num_runs):
            run_number = int(record_file_set['RUN'][i_run])
            ipts_str = str(record_file_set['IPTS'][i_run])
            ipts_number = int(ipts_str.split('-')[-1])
            full_file_path = '/SNS/VULCAN/%s/0/%d/NeXus/VULCAN_%d_event.nxs' % (ipts_str, run_number, run_number)
            exp_time_str = str(record_file_set['StartTime'][i_run])
            exp_time = vdrivehelper.parse_time(exp_time_str)

            run_dict_list.append({'run': run_number,
                                  'ipts': ipts_number,
                                  'file': full_file_path,
                                  'time': exp_time})
        # END-FOR

        self._infoDict[record_file_path] = run_dict_list

        return record_file_path

    def search_experiment_runs_by_time(self, delta_days):
        """ Search files under IPTS and return with the runs created within a certain
        days from its previous run.
        For example, if run i is delta_days+1 days earlier than run i+1, then only
        all the runs before run i will be grouped in a sub list

        Purpose:

        Requirements:
            delta_days must be an integer
        Guarantees:

        :exception: RuntimeError, AssertionError

        :param delta_days: number of days to search from the first run

        :return: a LIST of LISTs of 2-tuple.
                 Each element list contains runs that are in same experiment.
                 Element of sub list is 2-tuple as epoch time and file name with full path
        """
        # Check requirements
        if self._iptsNo is None:
            raise RuntimeError('IPTS number has not been set up.')
        assert isinstance(delta_days, int), 'Input delta of days must be an integer.'

        # Get the list of event NeXus files under the IPTS's data directory
        # TODO/FIXME/NOW: This following section of codes are used at least twice in this class. It should be
        #                 converted to a method
        event_file_list = list()
        for filename in os.listdir(self._iptsDataDir):
            if filename.endswith("_event.nxs") is True:
                # not sure whether the returned file names are of relative path or absolute path
                filename = os.path.basename(filename)
                filename = os.path.join(self._iptsDataDir, filename)
                event_file_list.append(filename)
        # END-FOR

        # Get detailed creation time information: element is 2-tuple (epoch time, filename) and sort by time
        time_file_list = []
        for filename in event_file_list:
            create_time = os.path.getctime(filename)
            # print "Creation time = ", create_time, filename
            time_file_list.append((create_time, filename))
        # END-FOR
        time_file_list = sorted(time_file_list)

        # TODO : Need an elegant algorithm/method to set up the output list
        # convert delta days to seconds
        delta_seconds = delta_days * 24 * 3600.
        print "[DB] Delta T = %f" % delta_seconds

        # the list of list as return
        period_list = list()
        # the sub list inside period_list.  The first run always serves as the start
        sub_list = [time_file_list[0]]
        # time 0
        prev_time = time_file_list[0][0]
       
        for i in xrange(1, len(time_file_list)):
            # Get the difference in time between previous time and current time
            curr_time = time_file_list[i][0]
            assert isinstance(curr_time, float)

            diff_time = curr_time - prev_time
            if diff_time < delta_seconds:
                # append current run to current sub list
                sub_list.append(time_file_list[i])
            else:
                # start a new element in the period list as time are too sparse
                period_list.append(sub_list[:])
                # reset sub list by starting with the first one run after big gap
                sub_list = [time_file_list[i]]
                prev_time = time_file_list[i][0]
            # END-IF
        # END-FOR

        # Don't forget the last sub list
        period_list.append(sub_list)

        if self.__DEBUG__:
            # DEBUG OUTPUT
            gindex = 0
            for sublist in period_list:
                print "Group ", gindex, " Start @ ", sublist[0][0], " Size = ", len(sublist)
                gindex += 1

        return period_list

    def set_ipts_number(self, ipts):
        """ Set ITPS
        Purpose:
            By given an IPTS number, set up the IPTS number of this and also its data directory and
            IPTS root directory
        Requirements:
            IPTS is an integer and valid
        Guarantees:
            IPTS root directory and data directory will be set up.
        """
        assert isinstance(ipts, int), 'Given IPTS number must be an integer'

        # Set
        self._iptsNo = ipts

        # special case (local directory)
        if ipts == 0:
            # case for local data
            self._localData = True
            self._iptsRootDir = None
            self._iptsDataDir = None
        else:
            # case for archive data with IPTS information
            self._localData = False
            self._iptsRootDir = os.path.join(self._archiveRootDirectory, 'IPTS-%d' % ipts)
            self._iptsDataDir = os.path.join(self._iptsRootDir, 'data')

            # Check
            assert os.path.exists(self._iptsRootDir), 'IPTS root directory %s does not exist.' \
                                                      '' % self._iptsRootDir
            assert os.path.exists(self._iptsDataDir), 'IPTS data directory %s does not exist.' \
                                                      '' % self._iptsDataDir

        return

    def set_data_root_path(self, root_dir):
        """ Set up root path such as /SNS/
        :exception: RuntimeError if given root directory is not
        :param root_dir: root archive directory
        """
        # Determine 2 cases
        if root_dir.count(self._dataArchiveInstrumentName.upper()) is False:
            self._archiveRootDirectory = os.path.join(root_dir, self._dataArchiveInstrumentName.upper())
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
def check_read_access(file_name):
    """ Check whether it is possible to access a file
    :param file_name:
    :return:
    """
    assert isinstance(file_name, str)
    return os.path.exists(file_name)


def load_from_xml(xml_file_name):
    """

    :param xml_file_name:
    :return:
    """
    # import saved xml project file
    try:
        pkl_file = open(xml_file_name, 'rb')
    except IOError as error:
        return False, 'Unable to open saved project xml file <%s> due to %s.' % (
            xml_file_name, str(error))

    save_dict = pickle.load(pkl_file)
    # pprint.pprint(save_dict)

    pkl_file.close()

    return True, save_dict


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
