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
    """ Class to manage data files from an archive server,
    especially data files in the archive of an SNS instrument.
    It only serves as an information source for archived data, including IPTS and runs.
    It won't be in charge of any activity to reduce data
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
        # flag to see whether data are stored in local computer
        self._isLocalArchive = False

        # data storage
        self._iptsInfoDict = dict()   # key: archive ID as IPTS number, value: dictionary of dictionaries: key = run
        self._runIptsDict = dict()  # key: run number value: IPTS number

        # Other class variables
        # # ipts number of type integer
        # self._iptsNo = None
        # # ipts data directory such as /SNS/VULCAN/IPTS-1234/data
        # self._iptsDataDir = None
        # # ipts root data directory such as /SNS/VULCAN/IPTS-1234/
        # self._iptsRootDir = None
        #
        # # Debug mode
        # self.__DEBUG__ = False

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

        # build the directory name from value
        if value == '/SNS/' or value == '/SNS':
            # in case only 'SNS' is given, build /SNS/VULCAN
            root_dir = os.path.join(value, self._dataArchiveInstrumentName.upper())
        else:
            # use the given one
            root_dir = value

        # check its existence
        if not os.path.exists(root_dir):
            raise OSError('Root raw data directory {0} does not exist.'.format(root_dir))

        # set root data directory
        self._archiveRootDirectory = root_dir
        # check whether it is local
        if self._archiveRootDirectory.startswith('/SNS/{0}'.format(self._dataArchiveInstrumentName)):
            self._isLocalArchive = False
        else:
            self._isLocalArchive = True

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

        # it could be in either .../ChoppedData/... or in .../binned_data/
        chop_data_dir_1 = '/SNS/VULCAN/IPTS-{0}/shared/binned_data/'.format(ipts_number)
        chop_data_dir_2 = '/SNS/VULCAN/IPTS-%d/shared/ChoppedData/' % ipts_number

        return DataArchiveManager.get_data_chopped_gsas([chop_data_dir_1, chop_data_dir_2], run_number, chop_seq)

    @staticmethod
    def get_data_archive_gsas(ipts_number, run_number):
        """
        get the path of GSAS file stored on archive server
        :param ipts_number:
        :param run_number:
        :return: list of data or None (cannot find)
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not {1}.' \
                                            ''.format(run_number, type(run_number))

        # locate reduced GSAS file name
        gsas_file_name = os.path.join('/SNS/VULCAN/IPTS-%d/shared/binned_data' % ipts_number, '%d.gda' % run_number)
        if not os.path.exists(gsas_file_name):
            return None

        return gsas_file_name

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

    @staticmethod
    def get_data_chopped_nexus(ipts_number, run_number, chop_child_list):
        """
        get the default directory for chopped NeXus file from SNS archive
        :exception: RuntimeError if unable to find the directory
        :param ipts_number:
        :param run_number: a list of string (i.e., files)
        :return:
        """
        # TODO/ISSUE/NOWNOW - Apply chop_child_list to this method!
        assert isinstance(run_number, int), 'Run number %s must be an integer.' % str(run_number)
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
                                             ''.format(ipts_number, type(ipts_number))

        # form the directory name
        chop_dir = '/SNS/VULCAN/IPTS-{0}/shared/ChoppedData/{1}'.format(ipts_number, run_number)

        # scan the directory
        if os.path.exists(chop_dir) is False:
            raise RuntimeError('Directory for chopped NeXus file {0} does not exist.'.format(chop_dir))

        #   from os import listdir
        # from os.path import isfile, join
        nexus_file_list = [f for f in os.listdir(chop_dir) if f.endswith('.nxs') and
                           os.path.isfile(os.path.join(chop_dir, f))]

        return nexus_file_list

    def get_event_file(self, ipts_number, run_number, check_file_exist):
        """
        get the raw event NEXUS file from archive
        :param ipts_number:
        :param run_number:
        :param check_file_exist: if file is not found, raise RuntimeError()
        :return:
        """
        # build the path: for the pre-nED NeXus file
        base_name = 'VULCAN_{0}_event.nxs'.format(run_number)
        sub_path = os.path.join('IPTS-{0}/0/{1}/NeXus'.format(ipts_number, run_number), base_name)
        raw_event_file_name = os.path.join(self._archiveRootDirectory, sub_path)

        if os.path.exists(raw_event_file_name):
            # return if the NeXus file exists
            pass

        else:
            # build the path for the nED NeXus file
            base_name = 'VULCAN_{0}.nxs.h5'.format(run_number)
            sns_path = os.path.join(self._archiveRootDirectory, 'IPTS-{0}/nexus'.format(ipts_number))
            ned_event_file_name = os.path.join(sns_path, base_name)

            if check_file_exist and not os.path.exists(ned_event_file_name):
                raise RuntimeError('Event NeXus file {0} or {1} cannot be not found under IPTS-{2}.'
                                   ''.format(ned_event_file_name, raw_event_file_name, ipts_number))
            # END-IF (for checking)

            raw_event_file_name = ned_event_file_name
        # END-IF-ELSE

        # add the dictionary
        self._runIptsDict[run_number] = ipts_number

        return raw_event_file_name

    def get_experiment_run_info(self, archive_key, run_number_list=None):
        """ Get the information of all runs from an IPTS that has been scanned before
        Purpose:
            Get data path information for all runs of an IPTS number
        Requirements
            A valid IPTS-number is set before
        Guarantees:
            Experimental run information including run number, creation time and full file path will be returned

        :param archive_key:
        :param run_number_list
        :return: list of dictionary, each of which is the information of a run
        """
        # check the validity of the archive key
        assert isinstance(archive_key, str) or isinstance(archive_key, int),\
            'Archive key %s must be a string or integer but not %s.' % (str(archive_key), type(archive_key))
        assert archive_key in self._iptsInfoDict,\
            'Archive key %s does not exist in archiving dictionary, which has keys %s.' \
            '' % (str(archive_key), str(self._iptsInfoDict.keys()))

        # Get run information
        if run_number_list is None:
            # all of them
            run_dict_list = self._iptsInfoDict[archive_key].values()
        else:
            run_dict_list = self.get_partial_run_info(archive_key, run_number_list)
        # END-IF

        return run_dict_list

    def get_ipts_number(self, run_number):
        """
        Get the IPTS number of a run that has been scanned
        :exception: key error if run number is not scanned
        :param run_number:
        :return:
        """
        # check inputs
        assert isinstance(run_number, int), 'Run number must be an integer.'

        return self._runIptsDict[run_number]

    # Methods
    @staticmethod
    def get_files_time_information(file_name_list):
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

            # After experiments, this is the most suitable way to define the time of a file
            create_time = os.path.getctime(filename)
            time_file_list.append((create_time, filename))
        # END-FOR (file_name)

        # Sort list by time
        time_file_list = sorted(time_file_list)

        return time_file_list

    def get_gsas_file(self, ipts_number, run_number, check_exist):
        """
        get reduced data written in GSAS.
        :param ipts_number:
        :param run_number:
        :param check_exist: if specified as True and file does not exist, a RuntimeError will be raised
        :return:
        """
        # build file name
        base_name = '{0}.gda'.format(run_number)
        sub_path = os.path.join('IPTS-{0}/shared/binned_data/'.format(ipts_number), base_name)
        gsas_full_path = os.path.join(self._archiveRootDirectory, sub_path)

        # check
        if check_exist and not os.path.exists(gsas_full_path):
            raise RuntimeError('Reduced GSAS file {0} is not found.'.format(gsas_full_path))

        return gsas_full_path

    @staticmethod
    def get_ipts_run_from_file_name(nxs_file_name):
        """
        Get IPTS number from a standard SNS nexus file name
        Note:
          - Format is /SNS/VULCAN/IPTS-????/0/NeXus/VULCAN_run...
        :param nxs_file_name:
        :return: tuple as 2 integers, IPTS and run number
        """
        # get base name of the NeXus file
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
            run_number = int(basename.split('_')[1])
        except IndexError:
            run_number = None
        except ValueError:
            run_number = None

        return ipts, run_number

    def get_partial_run_info(self, archive_key, run_number_list):
        """
        Get a subset of runs (with all information) by specified range of run numbers, i.e., the run number is in
        this object's IPTS information dictonary (_iptsInfoDict)
        :param archive_key:
        :param run_number_list:
        :return: a list of run information (in dictionary)
        """
        # check
        assert isinstance(archive_key, str) or isinstance(archive_key, int), \
            'Archive key {0} must be a string or integer but not {1}.'.format(archive_key, type(archive_key))
        assert isinstance(run_number_list, list), 'Run numbers {0} must be given in list but not {1}.' \
                                                  ''.format(run_number_list, type(run_number_list))

        # get partial list
        partial_list = list()
        for run_number in run_number_list:
            if run_number in self._iptsInfoDict[archive_key]:
                run_dict = self._iptsInfoDict[archive_key][run_number]
                partial_list.append(run_dict)
            else:
                print '[Warning] Run number {0} is not in ArchiveManager\'s IPTS information dictionary.' \
                      ''.format(run_number)

        return partial_list

    @staticmethod
    def get_proton_charge(ipts_number, run_number, chop_sequence):
        """

        :param ipts_number:
        :param run_number:
        :param chop_sequence:
        :return:
        """
        import pandas

        # check inputs' types
        assert isinstance(ipts_number, int), 'blabla1'
        assert isinstance(run_number, int), 'blabla2'

        # file
        if chop_sequence is None:
            # regular run: load the NeXus file and find out
            nexus_file = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(ipts_number, run_number)
            if not os.path.exists(nexus_file):
                nexus_file2 = '/SNS/VULCAN/IPTS-{0}/data/VULCAN_{1}_event.nxs'.format(ipts_number, run_number)
                if os.path.exists(nexus_file2) is False:
                    raise RuntimeError('Unable to locate NeXus file for IPTS-{0} Run {1} with name '
                                       '{2} or {3}'.format(ipts_number, run_number, nexus_file, nexus_file2))
                else:
                    nexus_file = nexus_file2
            # END-IF

            # load data, get proton charge and delete
            out_name = '{0}_Meta'.format(run_number)
            mantid_helper.load_nexus(data_file_name=nexus_file, output_ws_name=out_name, meta_data_only=True)
            proton_charge = mantid_helper.get_sample_log_value_single(out_name, 'gd_prtn_chrg')
            # convert unit from picoCoulumb to uA.hour
            proton_charge *= 1E6 * 3600.
            mantid_helper.delete_workspace(out_name)

        else:
            # chopped run: get the proton charge value from
            record_file_name = '/SNS/VULCAN/IPTS-{0}/shared/ChoppedData/{1}/{1}sampleenv_chopped_mean.txt' \
                               ''.format(ipts_number, run_number)
            if os.path.exists(record_file_name) is False:
                raise RuntimeError('Unable to locate chopped data record file {0}'.format(record_file_name))

            # import csv
            data_set = pandas.read_csv(record_file_name, header=None, delim_whitespace=True, index_col=0)
            try:
                proton_charge = data_set.loc[chop_sequence][1]
                proton_charge = float(proton_charge)
            except KeyError as key_err:
                raise RuntimeError('Unable to find chop sequence {0} in {1} due to {2}'
                                   ''.format(chop_sequence, record_file_name, key_err))
        # END-IF

        return proton_charge

    @staticmethod
    def get_smoothed_vanadium(ipts_number, van_run_number, check_exist=True):
        """

        :param ipts_number:
        :param van_run_number:
        :param check_exist:
        :return:
        """
        smoothed_van_file = '/SNS/VULCAN/IPTS-{0}/shared/Instrument/{1}-s.gda'.format(ipts_number, van_run_number)

        if check_exist and os.path.exists(smoothed_van_file) is False:
            raise RuntimeError('Smoothed vanadium run {0} cannot be found with IPTS {1} as {2}.'
                               ''.format(van_run_number, ipts_number, smoothed_van_file))

        return smoothed_van_file

    @staticmethod
    def get_vulcan_chopped_gsas_dir(ipts_number, run_number):
        """
        blabla
        :param ipts_number:
        :param run_number:
        :return:
        """
        return '/SNS/VULCAN/IPTS-{0}/shared/binned_data/{1}/'.format(ipts_number, run_number)

    @staticmethod
    def locate_vanadium_gsas_file(ipts_number, van_run_number):
        """ Locate a smoothed vanadium run reduced to GSAS file format
        get the vanadium GSAS file name
        :param ipts_number:
        :param van_run_number:
        :return:
        """
        van_gda_file = '/SNS/VULCAN/IPTS-{0}/shared/Instrument/{1}-s.gda'.format(ipts_number, van_run_number)

        file_accessible = os.path.exists(van_gda_file)

        return file_accessible, van_gda_file

    def scan_runs_from_archive(self, ipts_number, run_number_list):
        """
        Scan VULCAN archive with a specific IPTS by guessing the name of NeXus and checking its existence.
        :param ipts_number:
        :param run_number_list:
        :return: archive key and error message
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'
        assert isinstance(run_number_list, list), 'Run number list cannot be of type {0}' \
                                                  ''.format(type(run_number_list))
        assert len(run_number_list) > 0, 'Run number list cannot be empty.'

        # form IPTS
        ipts_dir = os.path.join(self._archiveRootDirectory, 'IPTS-%d' % ipts_number)
        assert os.path.exists(ipts_dir), 'IPTS dir %s does not exist.' % ipts_dir

        # archive key:
        archive_key = ipts_number
        if archive_key not in self._iptsInfoDict:
            self._iptsInfoDict[archive_key] = dict()
        err_msg = ''

        # locate file
        for run_number in sorted(run_number_list):
            # form file
            nexus_file_name = self.get_event_file(ipts_number, run_number, check_file_exist=True)

            if os.path.exists(nexus_file_name):
                # create a run information dictionary and put to information-buffering dictionaries
                run_info = {'run': run_number,
                            'ipts': ipts_number,
                            'file': nexus_file_name,
                            'time': None}
                self._iptsInfoDict[archive_key][run_number] = run_info
                self._runIptsDict[run_number] = ipts_number
            else:
                err_msg += 'Run %d does not exist in IPTS %s\n' % (run_number, ipts_number)
            # END-IF
        # END-FOR

        return archive_key, err_msg

    def scan_runs_from_directory(self, ipts_dir):
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
        self._iptsInfoDict[ipts_dir] = dict()

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

            # create run information
            run_info = {'run': run_number,
                        'ipts': ipts_number,
                        'file': full_path_name,
                        'time': create_time}

            # get the IPTS's information dictionary. create it if it does not exist
            if ipts_number not in self._iptsInfoDict:
                self._iptsInfoDict[ipts_number] = dict()

            # add to list for return
            self._iptsInfoDict[ipts_number][run_number] = run_info
            self._runIptsDict[run_number] = ipts_number
            # add a new entry to IPTS information
            self._iptsInfoDict[ipts_dir][run_number] = run_info
        # END-FOR

        return ipts_dir

    def scan_vulcan_record(self, record_file_path):
        """
        Scan a VULCAN record file
        :param record_file_path:
        :return: key to a dictionary
        """
        # read the file
        record_file_set = vulcan_util.import_vulcan_log(record_file_path)
        self._iptsInfoDict[record_file_path] = dict()

        # export the pandas log to a list of dictionary
        num_runs = len(record_file_set)
        for i_run in range(num_runs):
            run_number = int(record_file_set['RUN'][i_run])
            ipts_str = str(record_file_set['IPTS'][i_run])
            ipts_number = int(ipts_str.split('-')[-1])
            full_file_path = '/SNS/VULCAN/%s/0/%d/NeXus/VULCAN_%d_event.nxs' % (ipts_str, run_number, run_number)
            exp_time_str = str(record_file_set['StartTime'][i_run])
            exp_time = vdrivehelper.parse_time(exp_time_str)

            # generate run info
            run_info = {'run': run_number,
                        'ipts': ipts_number,
                        'file': full_file_path,
                        'time': exp_time}

            if ipts_number not in self._iptsInfoDict:
                self._iptsInfoDict[ipts_number] = dict()

            # add to IPTS and run number mapping dictionary
            self._iptsInfoDict[ipts_number][run_number] = run_info
            self._runIptsDict[run_number] = ipts_number
            # add the record file path to dictionary as another key
            self._iptsInfoDict[record_file_path][run_number] = run_info
        # END-FOR

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
        # TODO/FIXME/ISSUE/55+ - Make it work in beta release

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

    def rollBack(self, epochtime):
        """ Roll time back to previous day
        """
        # TODO/FIXME/ISSUE/55+ - This will be very useful when time-run-selection is simplemented
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
