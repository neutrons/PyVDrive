################################################################################
# Facility utility
################################################################################
import os
import time
import pickle
import pandas
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import vdrivehelper
from pyvdrive.lib import vulcan_util
from pyvdrive.lib import datatypeutility

SUPPORTED_INSTRUMENT = {'VULCAN': 'VULCAN'}
SUPPORTED_INSTRUMENT_SHORT = {'VUL': 'VULCAN'}

AUTO_LOG_MAP = {'run': 'RUN', 'duration': 'Duration', 'sample': 'Sample',
                'totalcounts': 'TotalCounts'}


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

        # VULCAN auto record dictionary
        self._auto_record_dict = dict()

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
        assert os.path.exists(
            self._archiveRootDirectory), 'Root archive directory %s is not accessible.' % self._archiveRootDirectory

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

    def locate_chopped_gsas(self, ipts_number, run_number, chop_seq):
        """
        get chopped data from GSAS file stored in archive server
        :param ipts_number:
        :param run_number:
        :param chop_seq:
        :return: None or GSAS name
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_int_variable('Chop sequence number', chop_seq, (1, 100000))

        # it could be in either .../ChoppedData/... or in .../binned_data/
        chop_data_dir_1 = '/SNS/VULCAN/IPTS-{0}/shared/binned_data/'.format(ipts_number)
        chop_data_dir_2 = '/SNS/VULCAN/IPTS-%d/shared/ChoppedData/' % ipts_number

        # search GSAS file (seq.gda) under given directories
        chop_gsas_name = None
        for parent_dir in [chop_data_dir_1, chop_data_dir_2]:
            chop_dir = os.path.join(parent_dir, '%d' % run_number)
            chop_gsas_name = os.path.join(chop_dir, '%d.gda' % chop_seq)
            if os.path.exists(chop_gsas_name):
                break
        # END-FOR

        # TODO - TONIGHT - Create a data structure to record searched GSAS

        return chop_gsas_name

    @staticmethod
    def locate_gsas(ipts_number, run_number):
        """
        get the path of GSAS file stored on archive server.  If not found, just return None
        :param ipts_number:
        :param run_number:
        :return: list of data or None (cannot find)
        """
        # check
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 99999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 9999999))

        # locate reduced GSAS file name
        gsas_file_name = os.path.join('/SNS/VULCAN/IPTS-%d/shared/binned_data' %
                                      ipts_number, '%d.gda' % run_number)
        if not os.path.exists(gsas_file_name):
            return None

        return gsas_file_name

    @staticmethod
    def locate_sliced_h5_logs(ipts_number, run_number):
        """
        get the file names of the sliced logs in HDF5 format
        Example:
        [wzz@analysis-node09 172282]$ cat summary.txt
        0  	/SNS/VULCAN/IPTS-22862/shared/pyvdrive_only/172282/1.hdf5  	1.gda
        1  	/SNS/VULCAN/IPTS-22862/shared/pyvdrive_only/172282/2.hdf5  	2.gda
        ... ...
        :param ipts_number:
        :param run_number:
        :return: list of 2-tuple (log h5 name, gsas file name)
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))

        archived_h5_dir = os.path.join('/SNS/VULCAN/', 'IPTS-{}/shared/pyvdrive_only/{}/'
                                                       ''.format(ipts_number, run_number))
        if not os.path.exists(archived_h5_dir):
            raise RuntimeError('Unable to locate hdf5 logs directory {}'.format(archived_h5_dir))

        summary_name = os.path.join(archived_h5_dir, 'summary.txt')
        if not os.path.exists(summary_name):
            raise RuntimeError('Unable to locate {} for sliced logs\' summary')

        # parse sliced log file
        log_file_names_tuple = list()
        summary_file = open(summary_name, 'r')
        raw_lines = summary_file.readlines()
        summary_file.close()

        for line in raw_lines:
            line = line.strip()
            if line == '' or line[0] == '#':
                continue  # ignore empty line and comment line

            items = line.split()
            if len(items) < 3:
                continue  # invalid line
            else:
                log_h5_i = items[1]
                gsas_i = items[2]
                log_file_names_tuple.append((log_h5_i, gsas_i))
        # END-FOR

        return log_file_names_tuple

    @staticmethod
    def locate_chopped_nexus(ipts_number, run_number, chop_child_list):
        """
        get the default directory for chopped NeXus file from SNS archive
        :exception: RuntimeError if unable to find the directory
        :param ipts_number:
        :param run_number: a list of string (i.e., files)
        :param chop_child_list: a list of chopped child
        :return:
        """
        # TODO/ISSUE/NOWNOW - Apply chop_child_list to this method! - NEED A SOLID USE CASE!
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))

        # form the directory name
        chop_dir = '/SNS/VULCAN/IPTS-{0}/shared/ChoppedData/{1}'.format(ipts_number, run_number)

        # scan the directory
        if os.path.exists(chop_dir) is False:
            raise RuntimeError(
                'Directory for chopped NeXus file {0} does not exist.'.format(chop_dir))

        #   from os import listdir
        # from os.path import isfile, join
        nexus_file_list = [f for f in os.listdir(chop_dir) if f.endswith('.nxs') and
                           os.path.isfile(os.path.join(chop_dir, f))]

        return nexus_file_list

    def locate_event_nexus(self, ipts_number, run_number):
        """
        get the raw event NEXUS file from archive
        :param ipts_number:
        :param run_number:
        :return: File name or None (if proposed path does not exist)
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))

        # by default, it shall be nED data: build the path for the nED NeXus file
        base_name = 'VULCAN_{0}.nxs.h5'.format(run_number)
        sns_path = os.path.join(self._archiveRootDirectory, 'IPTS-{0}/nexus'.format(ipts_number))
        raw_event_file_name = os.path.join(sns_path, base_name)

        if not os.path.exists(raw_event_file_name):
            # might be a pre-nED
            base_name = 'VULCAN_{0}_event.nxs'.format(run_number)
            sub_path = os.path.join(
                'IPTS-{0}/0/{1}/NeXus'.format(ipts_number, run_number), base_name)
            raw_event_file_name_h5 = raw_event_file_name
            raw_event_file_name = os.path.join(self._archiveRootDirectory, sub_path)
        else:
            raw_event_file_name_h5 = '<Logic Error>'
        # END-IF

        # early return
        if os.path.exists(raw_event_file_name):
            # add the dictionary
            self._runIptsDict[run_number] = ipts_number
        else:
            # return for nothing
            raw_event_file_name = None
            print('[INFO] For IPTS-{} Run-{}, neither {} nor {} exists.'
                  ''.format(ipts_number, run_number, raw_event_file_name_h5, raw_event_file_name))
        # END-IF-ELSE

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
            'Archive key %s must be a string or integer but not %s.' % (
                str(archive_key), type(archive_key))
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
            assert os.path.exists(
                filename), 'Given file %s does not exist for file time information.' % filename

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
        # check
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 999999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 99999999))

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
            'Archive key {0} must be a string or integer but not {1}.'.format(
                archive_key, type(archive_key))
        assert isinstance(run_number_list, list), 'Run numbers {0} must be given in list but not {1}.' \
                                                  ''.format(run_number_list, type(run_number_list))

        # get partial list
        partial_list = list()
        for run_number in run_number_list:
            if run_number in self._iptsInfoDict[archive_key]:
                run_dict = self._iptsInfoDict[archive_key][run_number]
                partial_list.append(run_dict)
            else:
                print('[Warning] Run number {0} is not in ArchiveManager\'s IPTS information dictionary.'
                      ''.format(run_number))

        return partial_list

    def get_run_info(self, archive_key):
        """
        get all run information
        :param archive_key:
        :return:
        """

    # TODO - FUTURE - Need to move this method to an appropriate module
    @staticmethod
    def get_proton_charge(ipts_number, run_number, chop_sequence):
        """ get proton charge (single value) from a run
        :param ipts_number:
        :param run_number:
        :param chop_sequence:
        :return:
        """
        # check inputs' types
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not a {1}.' \
                                            ''.format(run_number, type(run_number))

        # file
        if chop_sequence is None:
            # regular run: load the NeXus file and find out
            nexus_file = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(
                ipts_number, run_number)
            if not os.path.exists(nexus_file):
                nexus_file2 = '/SNS/VULCAN/IPTS-{0}/data/VULCAN_{1}_event.nxs'.format(
                    ipts_number, run_number)
                if os.path.exists(nexus_file2) is False:
                    raise RuntimeError('Unable to locate NeXus file for IPTS-{0} Run {1} with name '
                                       '{2} or {3}'.format(ipts_number, run_number, nexus_file, nexus_file2))
                else:
                    nexus_file = nexus_file2
            # END-IF

            # load data, get proton charge and delete
            out_name = '{0}_Meta'.format(run_number)
            mantid_helper.load_nexus(data_file_name=nexus_file,
                                     output_ws_name=out_name, meta_data_only=True)
            proton_charge = mantid_helper.get_sample_log_value_single(out_name, 'gd_prtn_chrg')
            # convert unit from picoCoulumb to uA.hour
            proton_charge *= 1E6 * 3600.
            mantid_helper.delete_workspace(out_name)

        else:
            # chopped run: get the proton charge value from
            record_file_name = '/SNS/VULCAN/IPTS-{0}/shared/ChoppedData/{1}/{1}sampleenv_chopped_mean.txt' \
                               ''.format(ipts_number, run_number)
            if os.path.exists(record_file_name) is False:
                raise RuntimeError(
                    'Unable to locate chopped data record file {0}'.format(record_file_name))

            # import csv
            data_set = pandas.read_csv(record_file_name, header=None,
                                       delim_whitespace=True, index_col=0)
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
        smoothed_van_file = '/SNS/VULCAN/IPTS-{0}/shared/Instrument/{1}-s.gda'.format(
            ipts_number, van_run_number)

        if check_exist and os.path.exists(smoothed_van_file) is False:
            raise RuntimeError('Smoothed vanadium run {0} cannot be found with IPTS {1} as {2}.'
                               ''.format(van_run_number, ipts_number, smoothed_van_file))

        return smoothed_van_file

    @staticmethod
    def get_archived_vanadium_gsas_name(ipts_number, run_number, check_write_permission):
        """
        Get/generate the vanadium name save to /SNS/VULCAN/shared
        :param ipts_number:
        :param run_number:
        :param check_write_permission: flag to check whether the user can have write permission to the
                                       file or directory
        :return: tuple (boolean: state, string: error message)
        """
        # check inputs
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 999999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 99999999))

        # write to archive's instrument specific calibration directory's instrument specific calibration directory
        base_name = '{0}-s.gda'.format(run_number)
        van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'

        # check directory existence and access
        if os.path.exists(van_dir) is False:
            return False, 'Vanadium directory {0} does not exist.'.format(van_dir)
        elif os.access(van_dir, os.W_OK) is False:
            return False, 'User has no privilege to write to directory {0}'.format(van_dir)

        gsas_file_name = os.path.join(van_dir, base_name)
        if os.path.exists(gsas_file_name) and os.access(gsas_file_name, os.W_OK) is False:
            return False, 'Smoothed vanadium GSAS file {0} exists and user does not have privilege to over write.' \
                          ''.format(gsas_file_name)

        return True, None

    @staticmethod
    def get_vulcan_chopped_gsas_dir(ipts_number, run_number):
        """ get the directory where the chopped GSAS files are
        :param ipts_number:
        :param run_number:
        :return: directory under ..../shared/
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 999999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 99999999))

        return '/SNS/VULCAN/IPTS-{0}/shared/binned_data/{1}/'.format(ipts_number, run_number)

    def load_auto_record(self, ipts_number, record_type):
        """
        load auto record file
        :except RuntimeError if there is no IPTS in auto record
        :param ipts_number:
        :param record_type: None for AutoRecord.txt, 'data' for AutoRecordData.txt', 'align' for AutoRecordAlign.txt
        :return:
        """
        # check input
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))
        if record_type is not None:
            datatypeutility.check_string_variable(
                'Log type', record_type, allowed_values=['data', 'align'])

        # locate IPTS folder and AutoRecord file
        ipts_shared_dir = '/SNS/VULCAN/IPTS-{}/shared'.format(ipts_number)
        if os.path.exists(ipts_shared_dir) is False:
            raise RuntimeError('IPTS {} has no directory {} in SNS archive'.format(
                ipts_number, ipts_shared_dir))

        if record_type is None:
            base_name = 'AutoRecord.txt'
        elif record_type == 'data':
            base_name = 'AutoRecordData.txt'
        elif record_type == 'align':
            base_name = 'AutoRecordAlign.txt'
        else:
            raise NotImplementedError('Impossible to reach this point')

        auto_record_file_name = os.path.join(ipts_shared_dir, base_name)
        if not os.path.exists(auto_record_file_name):
            raise RuntimeError('Auto {} record file {} does not exist.'.format(
                record_type, auto_record_file_name))

        # load and parse the file
        record_key = 'Auto{}-IPTS{}'.format(record_type, ipts_number)
        self._auto_record_dict[record_key] = vulcan_util.import_vulcan_log(auto_record_file_name)

        return record_key

    @staticmethod
    def locate_vanadium_gsas_file(ipts_number, van_run_number):
        """ Locate a smoothed vanadium run reduced to GSAS file format
        get the vanadium GSAS file name
        :param ipts_number:
        :param van_run_number:
        :return:
        """
        van_gda_file = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/PRM/{}-s.gda'.format(
            van_run_number)

        file_accessible = os.path.exists(van_gda_file)

        return file_accessible, van_gda_file

    @staticmethod
    def locate_process_vanadium(vanadium_run):
        """ locate processed vanadium GSAS file and thus also the GSAS prm file related
        :except OSError: if directory cannot be found
        :except RuntimeError: if file cannot be found
        :param vanadium_run:
        :return:
        """
        datatypeutility.check_int_variable('Vanadium run number', vanadium_run, (1, None))

        prm_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/PRM'
        if not os.path.exists(prm_dir):
            raise OSError('VULCAN PRM directory {} cannot be located.'.format(prm_dir))

        # Note: 's' for smoothed
        gsas_name = os.path.join(prm_dir, '{}-s.gda'.format(vanadium_run))
        prm_name = os.path.join(prm_dir, 'Vulcan-{}-s.prm'.format(vanadium_run))
        if not (os.path.exists(gsas_name) and os.path.exists(prm_name)):
            raise RuntimeError('Either smoothed GSAS vanadium file {} or PRM file {} cannot be found.'
                               ''.format(gsas_name, prm_name))

        return gsas_name, prm_name

    def scan_runs_from_archive(self, ipts_number, run_number_list):
        """
        Scan VULCAN archive with a specific IPTS by guessing the name of NeXus and checking its existence.
        :param ipts_number:
        :param run_number_list:
        :return: archive key and error message
        """
        # check
        assert isinstance(ipts_number, int), 'IPTS number must be an integer.'
        datatypeutility.check_list('Run numbers', run_number_list)
        assert len(run_number_list) > 0, 'Run number list cannot be empty.'

        # form IPTS
        ipts_dir = os.path.join(self._archiveRootDirectory, 'IPTS-%d' % ipts_number)
        if not os.path.exists(ipts_dir):
            raise RuntimeError(
                'IPTS dir {} does not exist for IPTS = {}'.format(ipts_dir, ipts_number))

        # archive key:
        archive_key = ipts_number
        if archive_key not in self._iptsInfoDict:
            self._iptsInfoDict[archive_key] = dict()
        err_msg = ''

        # locate file
        for run_number in sorted(run_number_list):
            # form file
            nexus_file_name = self.locate_event_nexus(ipts_number, run_number)

            if nexus_file_name is None:
                err_msg += 'Run %d does not exist in IPTS %s\n' % (run_number, ipts_number)
            else:
                # create a run information dictionary and put to information-buffering dictionaries
                run_info = {'run': run_number,
                            'ipts': ipts_number,
                            'file': nexus_file_name,
                            'time': None}
                self._iptsInfoDict[archive_key][run_number] = run_info
                self._runIptsDict[run_number] = ipts_number
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

            # try new way first: /SNS/VULCAN/IPTS-18721/nexus/VULCAN_160366.nxs.h5
            full_file_path = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(
                ipts_number, run_number)

            # try old way if new-way file name does not work
            if os.path.exists(full_file_path) is False:
                full_file_path = '/SNS/VULCAN/%s/0/%d/NeXus/VULCAN_%d_event.nxs' % (
                    ipts_str, run_number, run_number)
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
        print("[DB] Delta T = %f" % delta_seconds)

        # the list of list as return
        period_list = list()
        # the sub list inside period_list.  The first run always serves as the start
        sub_list = [time_file_list[0]]
        # time 0
        prev_time = time_file_list[0][0]

        for i in range(1, len(time_file_list)):
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
                print("Group ", gindex, " Start @ ", sublist[0][0], " Size = ", len(sublist))
                gindex += 1

        return period_list

    def rollBack(self, epochtime):
        """ Roll time back to previous day
        """
        # TODO/FIXME/ISSUE/55+ - This will be very useful when time-run-selection is simplemented
        print("Ecoch time = ", epochtime, type(epochtime))

        stime = time.strptime(time.ctime(epochtime))
        print(stime.tm_yday)

        # FIXME - Delta T should be given!
        # NOTE : MOCK : 2 days
        rollbacktime = epochtime - 2*24*3600
        stime2 = time.strptime(time.ctime(rollbacktime))
        print(stime2.tm_yday)

        return

    def sort_info(self, auto_record_ref_id, sort_by, run_range, output_items, num_outputs):
        """ sort the information loaded from auto record file
        Note: current list of indexes
        Index([u'RUN', u'IPTS', u'Title', u'Notes', u'Sample', u'ITEM', u'StartTime',
        u'Duration', u'ProtonCharge', u'TotalCounts', u'Monitor1', u'Monitor2',
        u'X', u'Y', u'Z', u'O', u'HROT', u'VROT', u'BandCentre', u'BandWidth',
        u'Frequency', u'Guide', u'IX', u'IY', u'IZ', u'IHA', u'IVA',
        u'Collimator', u'MTSDisplacement', u'MTSForce', u'MTSStrain',
        u'MTSStress', u'MTSAngle', u'MTSTorque', u'MTSLaser', u'MTSlaserstrain',
        u'MTSDisplaceoffset', u'MTSAngleceoffset', u'MTST1', u'MTST2', u'MTST3',
        u'MTST4', u'MTSHighTempStrain', u'FurnaceT', u'FurnaceOT',
        u'FurnacePower', u'VacT', u'VacOT', u'EuroTherm1Powder',
        u'EuroTherm1SP', u'EuroTherm1Temp', u'EuroTherm2Powder',
        u'EuroTherm2SP', u'EuroTherm2Temp'],
        :param auto_record_ref_id:
        :param sort_by:
        :param run_range:
        :param output_items:
        :param num_outputs:
        :return:
        """
        # check inputs
        datatypeutility.check_string_variable('Auto record reference ID', auto_record_ref_id)
        datatypeutility.check_string_variable('Column name to sort by', sort_by)
        if sort_by.lower() not in AUTO_LOG_MAP:
            raise RuntimeError('Pandas DataFrame has no columns mapped from {}; Available include '
                               '{}'.format(sort_by.lower(), AUTO_LOG_MAP.keys()))
        if run_range is not None:
            assert not isinstance(run_range, str), 'Runs range cannot be a string'
            if len(run_range) != 2:
                raise RuntimeError('Run range {} must have 2 items for start and end.'
                                   ''.format(run_range))
        # END-IF

        datatypeutility.check_list('Output column names', output_items)
        if num_outputs is not None:
            datatypeutility.check_int_variable('Number of output rows', num_outputs, (1, None))

        if auto_record_ref_id not in self._auto_record_dict:
            raise RuntimeError('Auto record ID {} is not in dictionary.  Available keys are {}'
                               ''.format(auto_record_ref_id, self._auto_record_dict.keys()))
        if run_range is not None:
            print('[ERROR] Notify developer that run range shall be implemented.')

        # get data frame (data set)
        record_data_set = self._auto_record_dict[auto_record_ref_id]

        # sort the value
        auto_log_key = AUTO_LOG_MAP[sort_by.lower()]
        record_data_set.sort_values(by=[auto_log_key], ascending=False, inplace=True)

        # filter out required
        needed_index_list = list()
        for item in output_items:
            needed_index_list.append(AUTO_LOG_MAP[item.lower()])
        filtered = record_data_set.filter(needed_index_list)

        # number of outputs
        if num_outputs is None:
            num_outputs = len(record_data_set)

        # convert to list of dictionary
        column_names = filtered.columns.tolist()
        output_list = list()
        for row_index in range(min(num_outputs, len(filtered))):
            dict_i = dict()
            for j in range(len(column_names)):
                try:
                    dict_i[output_items[j]] = filtered.iloc[row_index, j]
                except IndexError as index_err:
                    print('j = {}, row_index = {}'.format(j, row_index))
                    print(column_names)
                    print('output items: {}'.format(output_items))
                    print(output_items[j])
                    print('filtered: \n{}'.format(filtered))
                    raise index_err
            # print dict_i
            output_list.append(dict_i)

        return output_list

# END-CLASS


################################################################################
# Static Methods
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

    output = open(xml_file_name, 'wb')

    # Pickle dictionary using protocol 0.
    pickle.dump(save_dict, output)

    # Pickle the list using the highest protocol available.
    # pickle.dump(selfref_list, output, -1)

    output.close()

    return


def sns_archive_nexus_path(ipts_number, run_number):
    """
    get the SNS archived nexus file path for VULCAN
    :param ipts_number:
    :param run_number:
    :return: name
    """
    datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))
    datatypeutility.check_int_variable('Run number', run_number, (1, None))

    ned_nexus_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5' \
                     ''.format(ipts_number, run_number)

    if os.path.exists(ned_nexus_name):
        r_file_name = ned_nexus_name
    else:
        # pre-Ned case
        pre_ned_nexus_name = '/SNS/VULCAN/IPTS-{0}/0/{1}/NeXus/VULCAN_{1}_event.nxs'.format(
            ipts_number, run_number)
        if os.path.exists(pre_ned_nexus_name):
            r_file_name = pre_ned_nexus_name
        else:
            raise RuntimeError('For IPTS-{0} Run {1}: Either nED {2} or pre-nED {3} exists'
                               ''.format(ipts_number, run_number, ned_nexus_name, pre_ned_nexus_name))
    # END-IF-ELSE

    return r_file_name
