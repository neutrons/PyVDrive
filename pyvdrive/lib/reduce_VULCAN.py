################################################################################
#
# Auto reduction script for VULCAN
# Version 3.0 for both auto reduction service and manual
# Version 4.0 (in test) for new nED (071_vbin_improve)
#
# Last version: reduce_VULCAN_20170723.py
#
# Input
# - Event file name with path
# - Output directory
#
# New Features:
# 1. Universal version for auto reduction service and manual reduction
# 2. AutoRecord.txt will be written to 2 directories in auto reduction mode
# a) .../shared/autoreduce/ to be untouchable and owned by auto reduction service;
# b) .../shared/ for users to modify and manual reduction
#
# Output
# 1. Furnace log;
# 2. Generic DAQ log;
# 3. MTS log;
# 4. Experiment log record (AutoRecord.txt)
# 5. Reduce for GSAS
#
# Test example:
# 1. reduce_VULCAN.py /SNS/VULCAN/IPTS-11090/0/41703/NeXus/VULCAN_41703_event.nxs
#                     /SNS/users/wzz/Projects/VULCAN/AutoReduction/autoreduce/Temp
#
# 2. reduce_VULCAN.py /SNS/VULCAN/IPTS-11090/0/41739/NeXus/VULCAN_41739_event.nxs
#                     /SNS/users/wzz/Projects/VULCAN/AutoReduction/autoreduce/Temp
#
# Notes:
# * 15.12.04:
#   1. Modify 'FileMode' of ExportExperimentLog to 'append' mode.
#   2. items.id (ITEM) to AutoRecord.txt
#   3. Operations to all loadframe logs are changed to 'average'
# * 16.02.08
#   1. In 'auto' mode, the AutoRecord file will be written to .../logs/ and then
#      copied to .../autoreduce/
# * 16.09.01
#   1. Refactor the code
#
################################################################################
import getopt
import os
import datetime
import stat
import shutil
import xml.etree.ElementTree as ET
import sys
import numpy
import bisect
import save_vulcan_gsas
import vdrivehelper as helper

#sys.path.append("/opt/mantidnightly/bin")
sys.path.append('/SNS/users/wzz/Mantid_Project/builds/debug/bin')
import mantid.simpleapi as mantidsimple
import mantid
from mantid.api import AnalysisDataService
from mantid.kernel import DateAndTime
import h5py

"""
VULCAN_calibrate_2018_04_03_27bank.h5  VULCAN_calibrate_2018_04_03.h5  VULCAN_calibrate_2018_04_04_7bank.h5

"""


CalibrationFilesList = [['/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal',
                         '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/VULCAN_Characterization_2Banks_v2.txt',
                         '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vdrive_log_bin.dat'],
                        # east/west bank
                        [{3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_11.h5',
                          7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_11_7bank.h5',
                          27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_11_27bank.h5'},
                         {3: '/SNS/VULCAN/shared/CALIBRATION/2017_1_7_CAL/VULCAN_Characterization_3Banks_v1.txt',
                          7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_Characterization_7Banks_v1.txt',
                          27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_Characterization_27Banks_v1.txt'},
                         '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5']
                        # east/west and high angle bank
                        ]
ValidDateList = [datetime.datetime(2000, 1, 1), datetime.datetime(2017, 7, 1), datetime.datetime(2100, 1, 1)]


def get_auto_reduction_calibration_files(nexus_file_name):
    """
    get calibration files for auto reduction according to the date of the NeXus event file is generated
    :param nexus_file_name:
    :return:
    """
    # check input
    assert isinstance(nexus_file_name, str), 'Input event NeXus file {0} must be a string but not a {1}.' \
                                             ''.format(nexus_file_name, type(nexus_file_name))
    if os.path.exists(nexus_file_name) is False:
        raise RuntimeError('Event NeXus file {0} does not exist or is not accessible.'.format(nexus_file_name))

    # get the date of the NeXus file
    event_file_time = datetime.datetime.fromtimestamp(os.path.getmtime(nexus_file_name))

    # locate the position of the date in the list
    char_index = bisect.bisect_right(ValidDateList, event_file_time) - 1
    if char_index < 0 or char_index >= len(ValidDateList):
        raise RuntimeError('File date is out of range.')

    return CalibrationFilesList[char_index]
# END-DEF


TIMEZONE1 = 'America/New_York'
TIMEZONE2 = 'UTC'

# record file header list: list of 3-tuples
RecordBase = [
    ("RUN",             "run_number", None),
    ("IPTS",            "experiment_identifier", None),
    ("Title",           "run_title", None),
    ("Notes",           "file_notes", None),
    ("Sample",          "SampleInfo", None),  # stored on sample object
    ('ITEM',            'items.id', '0'),
    ("StartTime",       "run_start", "time"),
    ("Duration",        "duration", None),
    ("ProtonCharge",    "proton_charge", "sum"),
    ("TotalCounts",     "das.counts", "sum"),
    ("Monitor1",        "das.monitor2counts", "sum"),
    ("Monitor2",        "das.monitor3counts", "sum"),
    ("X",               "X", "0"),
    ("Y",               "Y", "0"),
    ("Z",               "Z", "0"),
    ("O",               "Omega", "0"),
    ("HROT",            "HROT", "0"),
    ("VROT",            "VROT", "0"),
    ("BandCentre",      "lambda", "0"),
    ("BandWidth",       "bandwidth", "0"),
    ("Frequency",       "skf1.speed", "0"),
    ("Guide",           "Guide", "0"),
    ("IX",              "IX",   "average"),
    ("IY",              "IY",   "average"),
    ("IZ",              "IZ",   "average"),
    ("IHA",             "IHA",  "average"),
    ("IVA",             "IVA",  "average"),
    ("Collimator",      "Vcollimator", None),
    ("MTSDisplacement", "loadframe.displacement",   "average"),
    ("MTSForce",        "loadframe.force",          "average"),
    ("MTSStrain",       "loadframe.strain",         "average"),
    ("MTSStress",       "loadframe.stress",         "average"),
    ("MTSAngle",        "loadframe.rot_angle",      "average"),
    ("MTSTorque",       "loadframe.torque",         "average"),
    ("MTSLaser",        "loadframe.laser",          "average"),
    ("MTSlaserstrain",  "loadframe.laserstrain",    "average"),
    ("MTSDisplaceoffset","loadframe.x_offset",      "average"),
    ("MTSAngleceoffset", "loadframe.rot_offset",    "average"),
    ("MTST1",           "loadframe.furnace1",       "average"),
    ("MTST2",           "loadframe.furnace2",       "average"),
    ("MTST3",           "loadframe.extTC3",         "average"),
    ("MTST4",           "loadframe.extTC4",         "average"),
    ("MTSHighTempStrain", "loadframe.strain_hightemp", "average"),
    ("FurnaceT",          "furnace.temp1",  "average"),
    ("FurnaceOT",         "furnace.temp2",  "average"),
    ("FurnacePower",      "furnace.power",  "average"),
    ("VacT",              "partlow1.temp",  "average"),
    ("VacOT",             "partlow2.temp",  "average"),
    ('EuroTherm1Powder', 'eurotherm1.power', 'average'),
    ('EuroTherm1SP',     'eurotherm1.sp',    'average'),
    ('EuroTherm1Temp',   'eurotherm1.temp',  'average'),
    ('EuroTherm2Powder', 'eurotherm2.power', 'average'),
    ('EuroTherm2SP',     'eurotherm2.sp',    'average'),
    ('EuroTherm2Temp',   'eurotherm2.temp',  'average'),
]


# Standard Vulcan sample log file header
VulcanSampleLogList = [("TimeStamp           ", ""),
                       ("Time [sec]          ", ""),
                       ("MPTIndex            ", "loadframe.MPTIndex"),
                       ("X                   ", "X"),
                       ("Y                   ", "Y"),
                       ("Z                   ", "Z"),
                       ("O", "OMEGA"),
                       ("HROT", "HROT"),
                       ("VROT", "VROT"),
                       ("MTSDisplacement", "loadframe.displacement"),
                       ("MTSForce", "loadframe.force"),
                       ("MTSStrain", "loadframe.strain"),
                       ("MTSStress", "loadframe.stress"),
                       ("MTSAngle", "loadframe.rot_angle"),
                       ("MTSTorque", "loadframe.torque"),
                       ("MTSLaser", "loadframe.laser"),
                       ("MTSlaserstrain", "loadframe.laserstrain"),
                       ("MTSDisplaceoffset", "loadframe.x_offset"),
                       ("MTSAngleceoffset", "loadframe.rot_offset"),
                       ("MTS1", "loadframe.furnace1"),
                       ("MTS2", "loadframe.furnace2"),
                       ("MTS3", "loadframe.extTC3"),
                       ("MTS4", "loadframe.extTC4"),
                       ("MTSHighTempStrain", "loadframe.strain_hightemp"),
                       ("FurnaceT", "furnace.temp1"),
                       ("FurnaceOT", "furnace.temp2"),
                       ("FurnacePower", "furnace.power"),
                       ("VacT", "partlow1.temp"),
                       ("VacOT", "partlow2.temp"),
                       ('EuroTherm1Powder', 'eurotherm1.power'),
                       ('EuroTherm1SP', 'eurotherm1.sp'),
                       ('EuroTherm1Temp', 'eurotherm1.temp'),
                       ('EuroTherm2Powder', 'eurotherm2.power'),
                       ('EuroTherm2SP', 'eurotherm2.sp'),
                       ('EuroTherm2Temp', 'eurotherm2.temp')]


MTS_Header_List = [
    ("TimeStamp", ""),
    ("Time [sec]", ""),
    ("MPTIndex", "loadframe.MPTIndex"),
    ("X", "X"),
    ("Y", "Y"),
    ("Z", "Z"),
    ("O", "OMEGA"),
    ("HROT", "HROT"),
    ("VROT", "VROT"),
    ("MTSDisplacement", "loadframe.displacement"),
    ("MTSForce", "loadframe.force"),
    ("MTSStrain", "loadframe.strain"),
    ("MTSStress", "loadframe.stress"),
    ("MTSAngle", "loadframe.rot_angle"),
    ("MTSTorque", "loadframe.torque"),
    ("MTSLaser", "loadframe.laser"),
    ("MTSlaserstrain", "loadframe.laserstrain"),
    ("MTSDisplaceoffset", "loadframe.x_offset"),
    ("MTSAngleceoffset", "loadframe.rot_offset"),
    ("MTS1", "loadframe.furnace1"),
    ("MTS2", "loadframe.furnace2"),
    ("MTS3", "loadframe.extTC3"),
    ("MTS4", "loadframe.extTC4"),
    ("MTSHighTempStrain", "loadframe.strain_hightemp"),
    ("FurnaceT", "furnace.temp1"),
    ("FurnaceOT", "furnace.temp2"),
    ("FurnacePower", "furnace.power"),
    ("VacT", "partlow1.temp"),
    ("VacOT", "partlow2.temp"),
    ('EuroTherm1Powder', 'eurotherm1.power'),
    ('EuroTherm1SP', 'eurotherm1.sp'),
    ('EuroTherm1Temp', 'eurotherm1.temp'),
    ('EuroTherm2Powder', 'eurotherm2.power'),
    ('EuroTherm2SP', 'eurotherm2.sp'),
    ('EuroTherm2Temp', 'eurotherm2.temp')]

Furnace_Header_List = ["furnace.temp1", "furnace.temp2", "furnace.power"]


# Generic DAQ log output.  first: head title; second: unit
Generic_DAQ_List = [("TimeStamp", ""),
                    ("Time [sec]", ""),
                    ("Current", "Current"),
                    ("Voltage", "Voltage")]


class ReductionSetup(object):
    """
    Class to contain reduction setup parameters
    """
    def __init__(self):
        """
        Initialization
        """
        self._runNumber = None
        self._iptsNumber = None

        self._isDryRun = False

        self._eventFileFullPath = None
        self._nexusDirectory = None
        self._eventFileName = None  # base name of source event file

        self._outputDirectory = None

        self._mainRecordFileName = None
        self._2ndRecordFileName = None

        self._mainGSASDir = None
        self._2ndGSASDir = None
        self._mainGSASName = None
        self._2ndGSASName = None

        self._sampleLogDirectory = None

        self._pngFileName = None

        # flag whether auto reduction just include log value only
        self._autoReduceLogOnly = False

        # about reduction required files
        self._focusFileName = None
        self._characterFileName = None
        self._vulcanBinsFileName = None

        # binning parameters
        self._binningParameters = None
        self._defaultBinSize = -0.001

        # flag whether the run is an alignment run or not
        self._isAlignmentRun = None
        self._reducedWorkspaceName = None

        # for data chopping
        self._splitterWsName = None
        self._splitterInfoName = None

        # reduction type
        self._isFullReduction = True

        # standard
        self._isStandardSample = False
        self._standardSampleName = None
        self._standardDirectory = None
        self._standardRecordFile = None

        # vanadium related
        self._vanadiumFlag = False
        self._vanadium3Tuple = None

        # about chopping
        self._exportToSNSArchive = True
        self._choppedSampleLogType = 'loadframe'
        self._saveChoppedWorkspaceToNeXus = False
        self._choppedNeXusDir = None

        # post diffraction focusing operations
        self._mergeBanks = False
        self._alignVDriveBinFlag = True

        return

    def __str__(self):
        """
        prettily formatted string for output
        :return:
        """
        pretty = ''
        pretty += 'Main GSAS dir   : {0}\n'.format(self._mainGSASDir)
        pretty += 'Main GSAS output: {0}\n'.format(self._mainGSASName)

        return pretty

    @property
    def align_bins_to_vdrive_standard(self):
        """
        blabla
        :return:
        """
        return self._alignVDriveBinFlag

    @property
    def binning_parameters(self):
        """
        return the binning parameters
        :return:
        """
        if self._binningParameters is None:
            # using default binning parameter
            bin_param_str = '5000., -0.001, 70000.'
        elif len(self._binningParameters) == 1:
            # only bin size is defined
            bin_param_str = '{0}, {1}, {2}'.format(5000., -1*abs(self._binningParameters[0]), 70000.)
        elif len(self._binningParameters) == 3:
            # 3 are given
            bin_param_str = '{0}, {1}, {2}'.format(self._binningParameters[0], -1*abs(self._binningParameters[1]),
                                                   self._binningParameters[2])
        else:
            # error case
            raise RuntimeError('Binning parameter {0} is error!'.format(self._binningParameters))

        return bin_param_str

    @staticmethod
    def change_output_directory(original_directory, user_specified_dir=None):
        """ Purpose:
          Change the output direction from
          * .../autoreduce/ to .../logs/
          * .../autoreduce/ to .../<user_specified>
        :param original_directory: if it is not ends with /autoreduce/, then the target directory will be the same,
                while if the directory does not exist, the method will create ethe directory.
        :param user_specified_dir: if it is not specified, change to .../logs/ as default
        """
        # Check validity
        assert isinstance(original_directory, str), 'Directory must be string but not %s.' % type(original_directory)

        # Change path from ..../autoreduce/ to .../logs/
        if original_directory.endswith("/"):
            original_directory = os.path.split(original_directory)[0]
        parent_dir, last_sub_dir = os.path.split(original_directory)

        if last_sub_dir == "autoreduce":
            # original directory ends with 'autoreduce'
            if user_specified_dir is None:
                # from .../autoreduce/ to .../logs/
                new_output_dir = os.path.join(parent_dir, "logs")
            else:
                # from .../autoreduce/ to .../<user_specified>/
                new_output_dir = os.path.join(parent_dir, user_specified_dir)
            # print "Log file will be written to directory %s. " % new_output_dir
        else:
            # non-auto reduction mode.
            new_output_dir = original_directory
            # print "Log file will be written to the original directory %s. " % new_output_dir

        # Create path
        if os.path.exists(new_output_dir) is False:
            # create
            os.mkdir(new_output_dir)

        return new_output_dir

    def check_validity(self):
        """
        check whether the current setup is valid, focusing on whether all the required files are set and exist
        :return:
        """
        error_message = ''

        # check whether the directory is writable
        if not os.access(self._outputDirectory, os.W_OK):
            error_message += 'Output data directory %s is not writable.\n' % self._outputDirectory

        # source event file
        if os.path.exists(self._eventFileFullPath) is False:
            error_message += 'NeXus file %s is not accessible or does not exist.' \
                             '' % self._eventFileFullPath

        # focusing file
        for file_name in [self._focusFileName, self._characterFileName]:
            if not os.path.exists(file_name):
                error_message += 'Calibration file %s cannot be found.\n' % file_name
        if self._vulcanBinsFileName is not None and os.path.exists(self._vulcanBinsFileName) is False:
            error_message += 'Calibration file %s cannot be found.\n' % self._vulcanBinsFileName

        # GSAS file
        if self._mainGSASName is not None:
            if os.path.exists(self._mainGSASName):
                # check whether it is over-writable
                if not os.access(self._mainGSASName, os.W_OK):
                    error_message += 'Existing main GSAS file %s cannot be over-written.' \
                                     '' % self._mainGSASName
            else:
                # check whether the directory is writable
                if not os.access(self._mainGSASDir, os.W_OK):
                    error_message += 'Directory %s is not writable for main gSAS file.' % self._mainGSASDir
        # END-IF

        # Record file
        if self._mainRecordFileName is not None:
            if os.path.exists(self._mainRecordFileName):
                # check whether it is over-writable
                if not os.access(self._mainRecordFileName, os.W_OK):
                    error_message += 'Main record file %s exists but cannot be written.' % self._mainRecordFileName
            else:
                # check whether the directory is writable
                record_dir = os.path.dirname(self._mainRecordFileName)
                if not os.access(record_dir, os.W_OK):
                    error_message += 'Directory %s is not writable for main record file.' % record_dir
        # END-IF

        if error_message == '':
            status = True
        else:
            status = False

        return status, error_message

    def get_chopped_directory(self, check_write_permission=True, nexus_only=False):
        """
        get the directory for chopped data (GSAS or NeXus)
        :param check_write_permission:
        :param
        :return:
        """
        # chopped data directory or chopped GSAS directory
        if self._exportToSNSArchive:
            gsas_dir = self._mainGSASDir
            nexus_dir = self._choppedNeXusDir
        else:
            # local
            gsas_dir = self._outputDirectory
            nexus_dir = self._outputDirectory

        if not nexus_only and check_write_permission and os.access(gsas_dir, os.W_OK) is False:
            raise RuntimeError('User has no privilege to write to {0} for chopped data.'.format(gsas_dir))
        if check_write_permission and os.access(nexus_dir, os.W_OK) is False:
            raise RuntimeError('User has no privilege to write to {0} for chopped data.'.format(nexus_dir))

        return gsas_dir, nexus_dir

    def get_characterization_file(self):
        """
        get characterization file
        :return:
        """
        return self._characterFileName

    def get_focus_file(self):
        """
        get diffraction focus (calibration) file
        :return:
        """
        # set to default if it is not set up yet
        if self._focusFileName is None:
            raise RuntimeError('Focus file is not set up.')

        return self._focusFileName

    def get_event_file(self):
        """
        Get event file's pull path
        :return:
        """
        return self._eventFileFullPath

    def get_gsas_dir(self):
        """
        get output GSAS file name
        :return:
        """
        return self._mainGSASDir

    def get_gsas_2nd_dir(self):
        """
        get secondary GSAS file name
        :return:
        """
        return self._2ndGSASDir

    def get_gsas_file(self, main_gsas):
        """
        get GSAS file
        :param main_gsas:
        :return:
        """
        if main_gsas:
            return self._mainGSASName
    
    def set_gsas_file(self, gsas_file_name, main_gsas):
        """
        get GSAS file
        :param main_gsas:
        :return:
        """
        if main_gsas:
            self._mainGSASName = gsas_file_name
        else:
            self._2ndGSASName = gsas_file_name

    def get_ipts_number(self):
        """
        get IPTS number
        :return:
        """
        return self._iptsNumber

    def get_plot_file(self):
        """
        get the 1-D plot png file name to save the reduced data' plot
        :return:
        """
        return self._pngFileName

    def get_record_file(self):
        """
        get the (sample log) Record file name with full path
        :return:
        """
        return self._mainRecordFileName

    def get_record_2nd_file(self):
        """
        get the 2nd (sample log) record file name with full path
        :return:
        """
        return self._2ndRecordFileName

    def get_reduced_data_dir(self):
        """
        get directory for output
        :return:
        """
        return self._outputDirectory

    def get_reduced_workspace(self):
        """

        :return:
        """
        return self._reducedWorkspaceName

    def get_run_number(self):
        """
        get run number
        :return:
        """
        if self._runNumber is None:
            raise RuntimeError('Run number is not set yet.')

        return self._runNumber

    def get_splitters(self, throw_not_set):
        """
        get splitters including SplittersWorkspace and Split-information workspace
        :param throw_not_set: if it is true and the splitters are not set. raise RuntimeError
        :return: 2-tuple
        """
        # check validity
        if throw_not_set:
            if self._splitterWsName is None or self._splitterInfoName is None:
                raise RuntimeError('Splitters (workspaces) have not been set.')
            if not AnalysisDataService.doesExist(self._splitterWsName):
                raise RuntimeError('Splitters workspace {0} cannot be found in ADS.'.format(self._splitterWsName))
            if not AnalysisDataService.doesExist(self._splitterInfoName):
                print '[WARNING] Splitters information workspace {0} do not exist.'.format(self._splitterInfoName)
                self._splitterInfoName = None
        # END-IF

        return self._splitterWsName, self._splitterInfoName

    def get_standard_processing_setup(self):
        """
        get the processing setup for VULCAN standard
        :return: 2-tuple
        """
        return self._standardDirectory, self._standardRecordFile

    def get_vanadium_info(self):
        """
        get vanadium calibration parameters
        :return:
        """
        return self._vanadium3Tuple

    def get_vdrive_log_dir(self):
        """
        Get the directory for vdrive log files
        :return:
        """
        return self._sampleLogDirectory

    def get_vulcan_bin_file(self):
        """
        get the VULCAN binning file (compatible to IDL) name
        :return:
        """
        return self._vulcanBinsFileName

    def is_dry_run(self):
        """
        check if it is a dry run
        :return:
        """
        return self._isDryRun

    @property
    def is_alignment_run(self):
        """
        Check whether the run set to this instance is an alignment run
        :return:
        """
        assert self._isAlignmentRun is not None, 'Not set up for alignment or not yet.'

        return self._isAlignmentRun

    @is_alignment_run.setter
    def is_alignment_run(self, value):
        """
        set to the instance whether it is an alignment run
        :param value:
        :return:
        """
        assert isinstance(value, bool)

        self._isAlignmentRun = value

        return

    @property
    def is_auto_reduction_service(self):
        """
        check the state whether the current reduction is a standard (auto) reduction in SNS archive
        :return:
        """
        return self._isFullReduction

    @is_auto_reduction_service.setter
    def is_auto_reduction_service(self, value):
        """
        set the state whether current reduction is for a full reduction
        :param value:
        :return:
        """
        assert isinstance(value, bool), 'Allowed value for is_full_reduction is bool only.'

        self._isFullReduction = value

        return

    @property
    def is_standard(self):
        """
        get whether the reduction is about a Standard sample (Si or Vanadium)
        :return:
        """
        return self._isStandardSample

    @is_standard.setter
    def is_standard(self, state):
        """
        set whether the reduction is about a standard sample
        :param state:
        :return:
        """
        assert isinstance(state, bool)

        self._isStandardSample = state

        return

    @property
    def merge_banks(self):
        """
        blabla
        :return:
        """
        return self._mergeBanks

    @property
    def output_directory(self):
        """
        get output directory
        :return:
        """
        return self._outputDirectory

    def process_configurations(self):
        """ Obtain information from full path to input NeXus file including
        1. base NeXus file name
        2. directory to NeXus file
        3. IPTS numbe and run number
        4. GSAS file name wit the knowledge of run number
        5. PNG file name for reduced pattern
        It must be called!
        :return:
        """
        # get event file name (base name) and directory for NeXus file
        self._nexusDirectory, self._eventFileName = os.path.split(self._eventFileFullPath)

        # set the data file path in the search list
        data_search_path = mantid.config.getDataSearchDirs()
        data_search_path.append(self._nexusDirectory)
        mantid.config.setDataSearchDirs(";".join(data_search_path))

        # parse the run number file name is in form as VULCAN_RUNNUBER_event.nxs
        if self._eventFileName.endswith('.nxs'):
            # pre-nED file name: ends with .nxs
            self._runNumber = int(self._eventFileName.split('_')[1])
        else:
            # nED file name: ends with .nxs.h5 '151206.nxs.h5'
            self._runNumber = int(self._eventFileName.split('_')[1].split('.')[0])

        # parse IPTS from NeXus directory: as /SNS/.../IPTS-XXX/...
        if self._nexusDirectory.count('IPTS') == 1:
            # standard SNS archive reduction
            dir_list = MainUtility.split_all_path(self._nexusDirectory)
            for dir_name in dir_list:
                if dir_name.count('IPTS') == 1:
                    self._iptsNumber = int(dir_name.split("-")[1])
                    break
            # END-FOR
        else:
            # none standard local machine reduction
            self._iptsNumber = 0
        # END-IF

        # about GSAS file
        if self._mainGSASDir is not None:
            self._mainGSASName = os.path.join(self._mainGSASDir, '%d.gda' % self._runNumber)

        if self._2ndGSASDir is not None:
            self._2ndGSASName = os.path.join(self._2ndGSASDir, '%d.gda' % self._runNumber)

        # 1D plot file name
        auto_reduction_dir = self.get_reduced_data_dir()
        if isinstance(auto_reduction_dir, str):
            self._pngFileName = os.path.join(auto_reduction_dir, 'VULCAN_' + str(self._runNumber) + '.png')
        else:
            self._pngFileName = os.path.join(self._mainGSASDir, 'VULCAN_{0}.png'.format(self._runNumber))

        return

    @property
    def save_chopped_workspace(self):
        """
        flag whether the chopped workspace will be saved in NeXus format
        :return:
        """
        return self._saveChoppedWorkspaceToNeXus

    @save_chopped_workspace.setter
    def save_chopped_workspace(self, save):
        """
        set the flag to save the chopped workspace in NeXus format
        :param save:
        :return:
        """
        assert isinstance(save, bool), 'Flag {0} must be a boolean but not a {1}.'.format(save, type(save))

        self._saveChoppedWorkspaceToNeXus = save

        return

    def set_align_vdrive_bin(self, flag):
        """
        set the flag to align the output GSAS workspace with VDRIVE's IDL-style binning
        :param flag:
        :return:
        """
        assert isinstance(flag, bool), 'Flag to align with VDRIVE GSAS binns {0} must be a boolean.'.format(flag)

        self._alignVDriveBinFlag = flag

        return

    def set_banks_to_merge(self, merge):
        """
        blabla
        :param merge:
        :return:
        """
        assert isinstance(merge, bool), 'Flag to merge banks {0} must be a boolean.'.format(merge)

        self._mergeBanks = merge

        return

    def set_binning_parameters(self, min_tof, bin_size, max_tof):
        """ set binning parameters
        :param min_tof:
        :param max_tof:
        :param bin_size:
        :return:
        """
        # check input
        assert isinstance(min_tof, float), 'Minimum TOF value {0} must be a float but not a {1}.' \
                                           ''.format(min_tof, type(min_tof))
        assert isinstance(min_tof, float), 'Minimum TOF value {0} must be a float but not a {1}.' \
                                           ''.format(max_tof, type(max_tof))
        assert isinstance(bin_size, float) or bin_size is None, 'Bin size {0} must be either a float or ' \
                                                                'a None but not a {1}.'.format(bin_size, type(bin_size))

        if bin_size is None:
            bin_size = self._defaultBinSize

        self._binningParameters = min_tof, -1 * abs(bin_size), max_tof

        return

    def set_charact_file(self, file_name):
        """
        set the characterization file name
        :param file_name:
        :return:
        """
        assert isinstance(file_name, str), 'Characterization file {0} must be a string but not a {1}.' \
                                           ''.format(file_name, type(file_name))

        self._characterFileName = file_name

        return

    def set_chopped_nexus_dir(self, dir_name):
        """
        set the directory for the chopped data in NeXus format
        :param dir_name:
        :return:
        """
        # check
        assert isinstance(dir_name, str), 'Directory name {0} must be a string but not a {1}.' \
                                          ''.format(dir_name, type(dir_name))

        self._choppedNeXusDir = dir_name

        return

    def set_focus_file(self, file_name):
        """
        set the diffraction focusing calibration file name
        :param file_name:
        :return:
        """
        assert isinstance(file_name, str), 'Input arg type error.'

        self._focusFileName = file_name

        return

    def set_splitters(self, splitter_ws_name, info_ws_name):
        """
        set workspaces' names related to chopping data
        :param splitter_ws_name:
        :param info_ws_name:
        :return:
        """
        assert isinstance(splitter_ws_name, str), 'Splitters workspace name must be a string.'
        assert isinstance(info_ws_name, str), 'Splitters information workspace name must be a string.'

        self._splitterWsName = splitter_ws_name
        self._splitterInfoName = info_ws_name

        return

    @property
    def normalized_by_vanadium(self):
        """
        check whether the reduced data will be normalized by vanadium
        :return:
        """
        return self._vanadiumFlag

    @normalized_by_vanadium.setter
    def normalized_by_vanadium(self, flag):
        """
        set the flag whether the data is reduced by vanadium
        :param flag:
        :return:
        """
        assert isinstance(flag, bool), 'Input flag {0} must be a boolean but not {1}.'.format(flag, type(flag))

        self._vanadiumFlag = flag

        return

    def set_auto_reduction_mode(self):
        """
        Set the reduction to default mode, which is the standard VULCAN auto-reduction setup,
        in the case that only event file name and output directory is given.
        In this method, the following directories will be set:
        1. sample log directory;
        2. main record file name;
        3. 2nd record file name;
        4. GSAS directory;
        5. 2nd GSAS directory;
        :return:
        """
        # sample log outputs (MTS, Generic, and etc)
        try:
            self._sampleLogDirectory = self.change_output_directory(self._outputDirectory)
        except OSError as os_err:
            raise OSError('Unable to create/get sample log directory due to %s.' % str(os_err))

        # record files
        self._mainRecordFileName = os.path.join(self._outputDirectory, "AutoRecord.txt")
        self._2ndRecordFileName = os.path.join(self.change_output_directory(self._outputDirectory, ""),
                                               "AutoRecord.txt")
        print ('[DEBUG LOG] auto reduction mode: output directory: {0}; 2nd record file: {1}'
               ''.format(self._outputDirectory, self._2ndRecordFileName))

        # output GSAS directory
        self._mainGSASDir = self.change_output_directory(self._outputDirectory, 'autoreduce/binnedgda')
        self._2ndGSASDir = self.change_output_directory(self._outputDirectory, 'binned_data')

        self.is_auto_reduction_service = True

        return

    def set_default_calibration_files(self, num_focused_banks):
        """
        set default calibration files
        :param num_focused_banks:
        :return:
        """
        helper.check_int_variable('Number of focused banks/spectra', num_focused_banks, (0, None))

        # get the reduction calibration and etc files from event data file
        file_list = get_auto_reduction_calibration_files(self._eventFileFullPath)

        calibrate_file_name = file_list[0][num_focused_banks]
        character_file_name = file_list[1][num_focused_banks]
        binning_ref_file_name = file_list[2]

        self.set_focus_file(calibrate_file_name)
        print ('[INFO] number of focused banks = {1}: calibration file: {0}, '
               'characterization file: {2}'.format(calibrate_file_name, num_focused_banks,
                                                   character_file_name))
        self.set_charact_file(character_file_name)
        if binning_ref_file_name is not None:
            self.set_vulcan_bin_file(binning_ref_file_name)

        return

    def set_dry_run(self, status):
        """
        set whether it is a dry run or a normal run
        :param status: True for dry run
        :return:
        """
        assert isinstance(status, bool)

        self._isDryRun = status

        return

    def set_event_file(self, event_file_path):
        """
        set full path of event file
        :param event_file_path:
        :return:
        """
        assert isinstance(event_file_path, str), 'Event file must be a string but not %s.' % type(event_file_path)
        assert os.path.exists(event_file_path), 'Event file %s does not exist.' % event_file_path

        self._eventFileFullPath = event_file_path

        return

    def set_gsas_dir(self, dir_name, main_gsas):
        """
        Set the GSAS file name or directory name
        :param dir_name:
        :param main_gsas:
        :return:
        """
        assert isinstance(dir_name, str), 'GSAS (or GSAS2) directory name must be a string.'

        if main_gsas:
            self._mainGSASDir = dir_name
        else:
            self._2ndGSASDir = dir_name

        return

    def set_ipts_number(self, ipts):
        """
        set IPTS number
        :param ipts:
        :return:
        """
        assert isinstance(ipts, int) and ipts >= 0

        self._iptsNumber = ipts

        return

    def set_log_dir(self, dir_name):
        """
        set the output directory for sample log files
        :param dir_name:
        :return:
        """
        assert isinstance(dir_name, str), 'directory name {0} must be of type string'.format(dir_name)
        if os.path.exists(dir_name) is False:
            raise RuntimeError('Output sample log directory {0} does not exist.'.format(dir_name))
        if os.path.isfile(dir_name):
            raise RuntimeError('Use input {0} is an existing file.'.format(dir_name))

        self._sampleLogDirectory = dir_name

        return

    def set_log_only(self, state):
        """
        """
        # blabla
        self._autoReduceLogOnly = state

    def set_output_dir(self, dir_path):
        """
        set output directory
        :param dir_path:
        :return:
        """
        # check input's validity
        assert isinstance(dir_path, str), 'Output directory must be a string but not %s.' % type(dir_path)

        # set up
        self._outputDirectory = dir_path

        # set the flag
        self._exportToSNSArchive = False

        return

    def set_chopped_output_to_archive(self, create_parent_directories=False):
        """
        set chopped data's output directories to SNS archive, including
        (1) chopped NeXus files and (2) reduced data files
        :param create_parent_directories: create directories if they do not exist
        :return:
        """
        # set the flag
        self._exportToSNSArchive = True

        # gsas/binned files
        binned_parent_dir = '/SNS/VULCAN/IPTS-{0}/shared/binned_data/'.format(self._iptsNumber)
        if os.path.exists(binned_parent_dir) is False and create_parent_directories:
            os.mkdir(binned_parent_dir, mode=0o777)  # global writable
        self._mainGSASDir = os.path.join(binned_parent_dir, '{0}'.format(self._runNumber))

        # Nexus files
        nexus_parent_dir = '/SNS/VULCAN/IPTS-{0}/shared/ChoppedData/'.format(self._iptsNumber)
        if os.path.exists(nexus_parent_dir) is False and create_parent_directories:
            os.mkdir(nexus_parent_dir, mode=0o777)
        self._choppedNeXusDir = os.path.join(nexus_parent_dir, '{0}'.format(self._runNumber))

        print '[INFO] Save chopping result to archive: {0} and {1}.'.format(self._mainGSASDir, self._choppedNeXusDir)

        return

    def set_plot_file_name(self, plot_file_name):
        """
        ISSUE44 doc
        :param plot_file_name:
        :return:
        """
        assert isinstance(plot_file_name, str)

        self._pngFileName = plot_file_name

        return

    def set_record_file(self, file_name, main_record):
        """
        Set record file
        :param file_name:
        :param main_record: flag to indicate the file name is for main record file. Otherwise, it is for 2nd record
        :return:
        """
        assert isinstance(file_name, str), 'Record file name %s must be a string but not %s.' \
                                           '' % (str(file_name), type(file_name))

        if main_record:
            self._mainRecordFileName = file_name
        else:
            self._2ndRecordFileName = file_name

        return

    def set_reduced_workspace(self, ws_name):
        """
        Set the name for the target reduced workspace
        :param ws_name:
        :return:
        """
        assert isinstance(ws_name, str), 'Workspace name must be a string.'
        self._reducedWorkspaceName = ws_name

        return

    def set_run_number(self, run_number):
        """
        set run number
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int), 'run number must be an integer.'

        self._runNumber = run_number

        return

    def set_standard_sample(self, standard, directory, base_record_file):
        """
        set the VULCAN standard output option
        :param standard:
        :param directory:
        :param base_record_file:
        :return:
        """
        # check inputs
        assert isinstance(standard, str), 'Standard material {0} must be a string but not a {1}.' \
                                          ''.format(standard, type(standard))
        assert isinstance(directory, str), 'Standard directory {0} must be a string but not a {1}.' \
                                           ''.format(directory, type(directory))
        assert isinstance(base_record_file, str), 'Base AutoRecord file {0} must be a string but not a {1}.' \
                                                  ''.format(base_record_file, type(base_record_file))

        self._standardSampleName = standard
        self._standardDirectory = directory
        self._standardRecordFile = os.path.join(directory, base_record_file)

        return

    def set_vanadium(self, van_run_number, van_gda_file, vanadium_tag):
        """
        set up vanadium run
        :param van_run_number:
        :param van_gda_file:
        :param vanadium_tag:
        :return:
        """
        self._vanadium3Tuple = (van_run_number, van_gda_file, vanadium_tag)

        return

    def set_vulcan_bin_file(self, file_name):
        """
        set the VULCAN binning (compatible with IDL) file name
        :param file_name:
        :return:
        """
        assert isinstance(file_name, str), 'Input arg type error.'

        self._vulcanBinsFileName = file_name

        return

    def to_reduce_gsas(self):
        """
        check whether it is to reduce GSAS file
        :return:
        """
        if self._mainGSASDir is None:
            return False

        return True


class PatchRecord:
    """ A class whose task is to make patch to Record.txt generated from
    Mantid.simpleapi.ExportExperimentLog(), which may not be able to retrieve
    all information from NeXus file.

    This class will not be used after all the required information/logs are
    added to NeXus file or exported to Mantid workspace
    """
    # PatchLogList = ['TotalCounts', 'Monitor1', 'Monitor2', 'Sample']
    PatchLogList = ['TotalCounts', 'Monitor1', 'Monitor2', 'VROT', 'Collimator', 'Sample']

    def __init__(self, instrument, ipts, run):
        """ Init
        """
        # Generate run_info and cv_info files
        self._cvInfoFileName = "/SNS/%s/IPTS-%d/0/%d/preNeXus/%s_%d_cvinfo.xml" % (
            instrument, ipts, run, instrument, run)

        self._runInfoFileName = "/SNS/%s/IPTS-%d/0/%d/preNeXus/%s_%d_runinfo.xml" % (
            instrument, ipts, run, instrument, run)

        self._beamInfoFileName = "/SNS/%s/IPTS-%d/0/%d/preNeXus/%s_beamtimeinfo.xml" % (
            instrument, ipts, run, instrument)

        # Verify whether these 2 files are accessible
        self._noPatchRecord = False
        if os.path.exists(self._cvInfoFileName) is False or \
                        os.path.exists(self._runInfoFileName) is False or \
                        os.path.exists(self._beamInfoFileName) is False:
            self._noPatchRecord = True

        return

    @property
    def do_not_patch(self):
        """
        return state whether a patch should be done or not
        :return:
        """
        return self._noPatchRecord

    def export_patch_list(self):
        """ Export patch as a list of strings
        """
        cvdict = self._readCvInfoFile()
        rundict = self._read_run_info_file()

        patchdict = {}
        for title in cvdict.keys():
            patchdict[title] = cvdict[title]

        for title in rundict.keys():
            patchdict[title] = rundict[title]

        patch_list = []
        for key in patchdict:
            if key in self.PatchLogList:
                patch_list.append(str(key))
                patch_list.append(str(patchdict[key]))

        return patch_list

    def _readCvInfoFile(self):
        """ read CV info
        """
        cvinfodict = {}

        # Parse the XML file to tree
        tree = ET.parse(self._cvInfoFileName)
        root = tree.getroot()

        # Find "DAS_process"
        das_process = None
        for child in root:
            if child.tag == "DAS_process":
                das_process = child
        if das_process is None:
            raise NotImplementedError("DAS_process is not in cv_info.")

        # Parse all the entries to a dictionary
        attribdict = {}
        for child in das_process:
            attrib = child.attrib
            name = attrib['name']
            value = attrib['value']
            attribdict[name] = value

        name = "das.neutrons"
        if name in attribdict:
            cvinfodict["TotalCounts"] = attribdict[name]

        name = "das.protoncharge"
        if name in attribdict:
            cvinfodict["ProtonCharge"] = attribdict[name]

        name = "das.runtime"
        if name in attribdict:
            cvinfodict["Duration(sec)"] = attribdict[name]

        name = "das.monitor2counts"
        if name in attribdict:
            cvinfodict["Monitor1"] = attribdict[name]

        name = "das.monitor3counts"
        if name in attribdict:
            cvinfodict["Monitor2"] = attribdict[name]

        return cvinfodict

    def _read_run_info_file(self):
        """ Read Run info file
        """
        runinfodict = {}

        tree = ET.parse(self._runInfoFileName)
        root = tree.getroot()

        # Get SampleInfo and GenerateInfo node
        sampleinfo = None
        generalinfo = None
        for child in root:
            if child.tag == "SampleInfo":
                sampleinfo = child
            elif child.tag == "GeneralInfo":
                generalinfo = child

        if sampleinfo is None:
            raise NotImplementedError("SampleInfo is missing.")
        if generalinfo is None:
            raise NotImplementedError("GeneralInfo is missing.")

        for child in sampleinfo:
            if child.tag == "SampleDescription":
                sampledes = child
                runinfodict["Sample"] = sampledes.text.replace("\n", " ")
                break

        for child in generalinfo:
            if child.tag == "Notes":
                origtext = child.text
                if origtext is None:
                    runinfodict["Notes"] = "(No Notes)"
                else:
                    runinfodict["Notes"] = child.text.replace("\n", " ")
                break

        return runinfodict
# END-CLASS


class PatchRecordHDF5(object):
    """Get the missing information in the loaded workspace from original hdf5 file
    """
    H5Path = {'Sample': ('entry', 'sample', 'name', 0, 0),
              'ITEM': ('entry', 'sample', 'identifier', 0, 0),
              'Monitor1': ('entry', 'monitor1', 'total_counts', 0),
              'Monitor2': ('entry', 'monitor2', 'total_counts', 0),
              'Comment': ('entry', 'DASlogs', 'comments', 'value', 0, 0),
              'NOTES': ('entry', 'notes', 0),
              'Collimator': ('entry', 'DASlogs', 'East_Collimator', 'average_value', 0),
              'TotalCounts': ('entry', 'total_counts', 0)
              }

    def __init__(self, h5name, sample_log_names):
        """initialization
        :param h5name:
        :param sample_log_names:
        """
        # check input
        assert isinstance(h5name, str), 'HDF5 file name {0} must be a string.'.format(h5name)
        assert isinstance(sample_log_names, list), 'Sample logs names must be given by list'

        if os.path.exists(h5name) is False:
            raise RuntimeError('Input HDF5 {0} cannot be found.'.format(h5name))

        self._h5name = h5name
        self._sample_log_list = sorted(sample_log_names)

        return

    def export_patch_list(self):
        """search the HDF5 for the sample logs
        :return:
        """
        import h5py

        try:
            h5file = h5py.File(self._h5name, 'r')
        except IOError as io_err:
            raise RuntimeError('Unable to open hdf5 file {0} due to {1}'.format(self._h5name, io_err))

        log_value_dict = dict()

        for log_name in self._sample_log_list:
            if log_name in PatchRecordHDF5.H5Path:
                h5_path = PatchRecordHDF5.H5Path[log_name]
                node = h5file
                try:
                    for item in h5_path:
                        if isinstance(item, str):
                            node = node[item]
                        elif isinstance(item, int):
                            node = node[item]
                    # END-FOR
                except KeyError as key_err:
                    if log_name == 'Notes':
                        node = 'Not Set'
                    else:
                        raise key_err
                # END-TRY-EXCEPT
                log_value_dict[log_name] = str(node)
        # END-FOR

        h5file.close()

        # convert to list
        patch_list = []
        for log_name in log_value_dict:
            patch_list.append(log_name)
            patch_list.append(log_value_dict[log_name])

        return patch_list


class ReduceVulcanData(object):
    """
    Class to reduce VULCAN data
    """
    def __init__(self, reduce_setup):
        """
        Initialization
        """
        assert isinstance(reduce_setup, ReductionSetup), 'Reduction setup must be a ReductionSetup instance but not ' \
                                                         '%s.' % type(reduce_setup)

        self._reductionSetup = reduce_setup

        # class variables' definition
        self._instrumentName = 'VULCAN'  # instrument name
        self._dataWorkspaceName = None   # source event data workspace' name

        # for output workspaces
        self._reducedWorkspaceMtd = None
        self._reducedWorkspaceVDrive = None
        self._reducedWorkspaceDSpace = None
        self._reduceGood = False

        self._reducedWorkspaceList = list()
        self._reducedDataFiles = list()

        self._choppedDataDirectory = None
        self._chopExportedLogType = 'loadframe'

        self._myLogInfo = ''

        # check whether the run is nED
        if self._reductionSetup.get_event_file().endswith('.h5'):
            # nED NeXus
            self._is_nED = True
        else:
            self._is_nED = False

        return

    def check_alignment_run(self):
        """

        :return:
        """
        log_ws = mantid.AnalysisDataService.retrieve(self._dataWorkspaceName)
        run_title = log_ws.getTitle()
        if run_title.startswith('Align:'):
            is_alignment_run = True
        else:
            is_alignment_run = False

        return is_alignment_run

    def clear(self):
        """
        clear the workspaces that contain the reduced data
        :return:
        """
        error_message = ''

        for ws_name in self._reducedWorkspaceList:
            try:
                mantidsimple.DeleteWorkspace(Workspace=ws_name)
            except RuntimeError as run_err:
                error_message += 'Unable to delete workspace {0} due to {1}.\n'.format(ws_name, run_err)

        # clear the list
        self._reducedWorkspaceList = list()

        # log error message
        if len(error_message) > 0:
            self._myLogInfo += '[ERROR] Clear the reduced workspaces:\n{0}'.format(error_message)

        return

    @staticmethod
    def get_target_split_ws_index(table_ws):
        """

        :param table_ws:
        :return:
        """
        target_set = set()
        if table_ws.__class__.__name__.count('SplittersWorkspace') == 1:
            # splitters workspace
            for i_row in range(table_ws.rowCount()):
                target_ws_index = int(table_ws.cell(i_row, 2))
                target_set.add(target_ws_index)
                # END-FOR
        # END-IF

        return sorted(list(target_set))

    def dry_run(self):
        """
        Dry run to verify the output
        :return: 2-tuple (boolean, string)
        """
        # check
        reduction_setup = self._reductionSetup
        assert isinstance(reduction_setup, ReductionSetup),\
            'Reduction setup {0} of type ({1}) is of wrong type, which should be ReductionSetup.' \
            ''.format(reduction_setup, type(reduction_setup))

        # configure the ReductionSetup
        self._reductionSetup.process_configurations()

        dry_run_str = ''

        # Output result in case it is a dry-run
        dry_run_str += "Input NeXus file    : %s\n" % reduction_setup.get_event_file()
        dry_run_str += "Output directory    : %s\n" % reduction_setup.get_reduced_data_dir()
        dry_run_str += "Log directory       : %s\n" % reduction_setup.get_vdrive_log_dir()  # logDir

        gsas_dir = reduction_setup.get_gsas_dir()
        if gsas_dir is None:
            dry_run_str += 'GSAS  directory     : not specified; No GSAS will be written\n'
        else:
            dry_run_str += 'GSAS  directory     : %s; GSAS file : %s.\n' \
                           '' % (gsas_dir, reduction_setup.get_gsas_file(main_gsas=True))
            # 2nd GSAS file
            if reduction_setup.get_gsas_dir() is not None:
                dry_run_str += "GSAS2 directory     : %s\n" % str(reduction_setup.get_gsas_2nd_dir())

        dry_run_str += "Record file name    : %s\n" % str(reduction_setup.get_record_file())
        dry_run_str += "Record(2) file name : %s\n" % str(reduction_setup.get_record_2nd_file())
        dry_run_str += "1D plot file name   : %s\n" % reduction_setup.get_plot_file()

        return True, dry_run_str

    def duplicate_gsas_file(self, source_gsas_file_name, target_directory):
        """ Duplicate gsas file to a new directory with file mode 664
        """
        # Verify input
        if os.path.exists(source_gsas_file_name) is False:
            self._myLogInfo += "[Warning]  Input file wrong\n"
            return
        elif os.path.isdir(source_gsas_file_name) is True:
            self._myLogInfo += "[Warning]  Input file is not file but directory.\n"
            return
        if os.path.isabs(source_gsas_file_name) is not True:
            self._myLogInfo += '[Warning] Source file name {0} is not an absolute path.\n'.format(source_gsas_file_name)
            return

        # Create directory if it does not exist
        if os.path.isdir(target_directory) is not True:
            os.makedirs(target_directory)

        # Copy
        target_file_name = os.path.join(target_directory, os.path.basename(source_gsas_file_name))
        if source_gsas_file_name == target_file_name:
            print '[INFO] Source GSAS file (1) {0} is same as target GSAS file (1) {1}.  No copy operation.'.format(source_gsas_file_name, target_file_name)
            return

        # copy the file
        try:
            if os.path.isfile(target_file_name) is True:
                # delete existing file
                self._myLogInfo += "Destination GSAS file {0} exists and will be overwritten.\n" \
                                   "".format(target_file_name)
                os.remove(target_file_name)
            shutil.copy(source_gsas_file_name, target_directory)
            new_gsas_file_name = os.path.join(target_directory, os.path.basename(source_gsas_file_name))
            os.chmod(new_gsas_file_name, 0666)
        except IOError as io_err:
            raise RuntimeError('Unable to cropy {0} to {1} due to {2}.'
                               ''.format(source_gsas_file_name, target_file_name, io_err))
        # modify the file property
        try:
            os.chmod(target_file_name, 0666)
        except OSError as os_err:
            self._myLogInfo += '[ERROR] Unable to change file {0}\'s mode to {1} due to {2}.\n' \
                               ''.format(source_gsas_file_name, '666', os_err)

        return

    def execute_vulcan_reduction(self, output_logs):
        """
        Execute the command for reduce, including
        (1) reduce to GSAS file
        (2) export log file
        (3) special reduction output for VULCAN auto reduction service
        (4) process VULCAN standard sample

        Note: VULCAN standard sample can only be processed in the sub methods because it needs a lot of
              variables defined in expoort_experiment_records() only
        Raise RuntimeError
        :return: (boolean, string) as success/fail and error message
        """
        # check whether it is good to go
        assert isinstance(self._reductionSetup, ReductionSetup), 'ReductionSetup is not correct.'
        final_message = ''

        # configure the ReductionSetup
        self._reductionSetup.process_configurations()

        # reduce and write to GSAS file ... it is reduced HERE!
        if not self._reductionSetup._autoReduceLogOnly:
            print '[DB...BAT...BAT] Reduce data here!'
            return_list = self.reduce_powder_diffraction_data()
            reduction_is_successful = return_list[0]
            msg_gsas = return_list[1]
            final_message += '{0}\n'.format(msg_gsas)

            # post process: error code: Code001 does not mean a bad reduction
            if not reduction_is_successful:
                # reduction failure
                return False, 'Reduction failure:\n{0}\n'.format(msg_gsas)
            elif self._reductionSetup.is_auto_reduction_service:
                self.generate_1d_plot()

            # VULCAN: process a standard sample (Si, V or C) for VULCAN: copy the GSAS file to directory for
            #         standard materials
            if self._reductionSetup.is_standard:
                gsas_file = self.get_reduced_files()[0]
                standard_dir, standard_record = self._reductionSetup.get_standard_processing_setup()
                try:
                    shutil.copy(gsas_file, standard_dir)
                    new_gsas_file_name = os.path.join(standard_dir, os.path.basename(gsas_file))
                    os.chmod(new_gsas_file_name, 0666)
                except (IOError, OSError) as copy_err:
                    msg_gsas += 'Unable to write standard GSAS file to {0} and change mode to 666 due to {1}\n' \
                                ''.format(standard_dir, copy_err)
            # END-IF
        else:
            # no reduction
            print '[INFO] Auto reduction only: {0}.'.format(self._reductionSetup._autoReduceLogOnly)
        # END-IF

        # load the sample run as an option
        if output_logs:
            # load data again with meta data only
            is_load_good, msg_load_file = self.load_meta_data_from_file()
            if not is_load_good:
                raise RuntimeError('It is not likely to be unable to load {0} at this stage'
                                   ''.format(self._reductionSetup.get_event_file()))

            # check whether it is an alignment run
            self._reductionSetup.is_alignment_run = self.check_alignment_run()

            # export the sample log record file: AutoRecord.txt and etc.
            is_record_good, msg_record = self.export_experiment_records()
            final_message += msg_record + '\n'

            # write experiment files
            is_log_good, msg_log = self.export_log_files()
            final_message += msg_log + '\n'

            is_log_good = is_load_good and is_record_good
        else:
            is_log_good = True
            final_message += 'No sample logs record is required to export.\n'
        # END-IF

        # special operations for auto reduction
        is_auto_good, msg_auto = self.special_operation_auto_reduction_service()
        final_message += msg_auto + '\n'

        return is_log_good and is_auto_good, final_message

    def _export_experiment_log(self, target_file, sample_name_list,
                               sample_title_list, sample_operation_list, patch_list):
        """
        export experiment log
        :param target_file:
        :return:
        """
        # check inputs
        assert isinstance(target_file, str), 'Target file name {0} must be a string but not a {1}.' \
                                             ''.format(target_file, type(target_file))
        assert isinstance(sample_name_list, list), 'Sample name list {0} must be a list but not a {1}.' \
                                                   ''.format(sample_name_list, type(sample_name_list))
        assert isinstance(sample_title_list, list), 'Sample title list {0} must be a list but not a {1}.' \
                                                    ''.format(sample_title_list, type(sample_title_list))
        assert isinstance(sample_operation_list, list), 'Sample operation list {0} must be a list but not a {1}.' \
                                                        ''.format(sample_operation_list, type(sample_operation_list))
        assert len(sample_name_list) == len(sample_title_list) and len(sample_name_list) == len(sample_operation_list), \
            'Sample name list ({0}), sample title list ({1}) and sample operation list ({2}) must have the same ' \
            'size'.format(len(sample_name_list), len(sample_title_list), len(sample_operation_list))

        # get file mode
        if os.path.exists(target_file):
            file_write_mode = 'append'
        else:
            file_write_mode = 'new'

        # write
        try:
            mantidsimple.ExportExperimentLog(InputWorkspace=self._dataWorkspaceName,
                                             OutputFilename=target_file,
                                             FileMode=file_write_mode,
                                             SampleLogNames=sample_name_list,
                                             SampleLogTitles=sample_title_list,
                                             SampleLogOperation=sample_operation_list,
                                             TimeZone="America/New_York",
                                             OverrideLogValue=patch_list,
                                             OrderByTitle='RUN',
                                             RemoveDuplicateRecord=True)
        except RuntimeError as run_err:
            message = 'Exporting experiment record to %s due to %s.' % (self._reductionSetup.get_record_file(),
                                                                        str(run_err))
            return False, message
        except ValueError as value_err:
            message = 'Exporting experiment record to {0} failed due to {1}.' \
                      ''.format(self._reductionSetup.get_record_file(), value_err)
            return False, message

        # Set up the mode for global access
        file_access_mode = oct(os.stat(target_file)[stat.ST_MODE])
        file_access_mode = file_access_mode[-3:]
        if file_access_mode != '666' and file_access_mode != '676':
            try:
                os.chmod(target_file, 0666)
            except OSError as os_err:
                self._myLogInfo += '[ERROR] Unable to set file {0} to mode 666 due to {1}.\n' \
                                   ''.format(target_file, os_err)
        # END-IF

        return True, ''

    def export_experiment_records(self):
        """ Write the summarized sample logs of this run number to the record files
        :return: True if it is an alignment run
        """
        # return if there is no requirement to export record file
        record_file_name = self._reductionSetup.get_record_file()
        user_record_name = self._reductionSetup.get_record_2nd_file()

        if record_file_name is None and user_record_name is None and not self._reductionSetup.is_standard:
            return True, 'No record file is required to write out.'

        # Convert the record base to input arrays
        sample_title_list, sample_name_list, sample_operation_list = self.generate_record_file_format()

        # Patch for logs that do not exist in event NeXus yet
        sample_log_list = ['Comment', 'Sample', 'ITEM', 'Monitor1', 'Monitor2']
        if self._reductionSetup.get_event_file().endswith('.h5'):
            # HDF5 file
            patcher = PatchRecordHDF5(self._reductionSetup.get_event_file(), sample_log_list)
            patch_list = patcher.export_patch_list()
        else:
            # with preNexus and others. pre nED
            patcher = PatchRecord(self._instrumentName,
                                  self._reductionSetup.get_ipts_number(),
                                  self._reductionSetup.get_run_number())
            if patcher.do_not_patch:
                patch_list = list()
            else:
                patch_list = patcher.export_patch_list()
        # END-IF-ELSE

        # define over all message
        return_status = True
        return_message = ''

        # export to AutoRecord.txt
        if record_file_name:
            # export main experiment log
            status1, message1 = self._export_experiment_log(self._reductionSetup.get_record_file(),
                                                            sample_name_list, sample_title_list,
                                                            sample_operation_list, patch_list)
            if not status1:
                return status1, message1
            else:
                return_message += message1 + '\n'

            # export to either data or align log file
            record_file_path = os.path.dirname(self._reductionSetup.get_record_file())
            if self._reductionSetup.is_alignment_run:
                categorized_record_file = os.path.join(record_file_path, 'AutoRecordAlign.txt')
            else:
                categorized_record_file = os.path.join(record_file_path, 'AutoRecordData.txt')

            status2, message2 = self._export_experiment_log(categorized_record_file,
                                                            sample_name_list, sample_title_list,
                                                            sample_operation_list, patch_list)
            return_status = return_status and status2
            return_message += message2 + '\n'
        else:
            # no need to export main AutoRecord file
            status2 = False
            categorized_record_file = None
        # END-IF-ELSE

        # Auto reduction only: record file for users
        if user_record_name:
            # 2nd copy of AutoRecord.txt
            # change_2nd_record_mode = False
            if os.path.exists(self._reductionSetup.get_record_2nd_file()):
                # if the target copy of AutoRecord.txt exists, then append
                status3, message3 = self._export_experiment_log(self._reductionSetup.get_record_2nd_file(),
                                                                sample_name_list, sample_title_list,
                                                                sample_operation_list, patch_list)
                return_status = status3 and return_status
                return_message += message3 + '\n'
                # change_2nd_record_mode = True
            else:
                # if the target copy of AutoRecord.txt does not exist
                try:
                    shutil.copy(self._reductionSetup.get_record_file(),
                                self._reductionSetup.get_record_2nd_file())
                    os.chmod(self._reductionSetup.get_record_2nd_file(), 0666)
                except IOError as io_err:
                    return_status = False
                    return_message += 'Unable to copy file {0} to {1} due to {2}.\n' \
                                      ''.format(self._reductionSetup.get_record_file(),
                                                self._reductionSetup.get_record_2nd_file(), io_err)
                # TRY-EXCEPT
            # END-IF-ELSE

            # if change_2nd_record_mode:
            #     # change mode to 666
            #     try:
            #         os.chmod(self._reductionSetup.get_record_2nd_file(), 0666)
            #     except IOError as io_err:
            #         return_status = False
            #         return_message += 'Unable to change file {0} mode to 666 due to {1}.\n' \
            #                           ''.format(self._reductionSetup.get_record_2nd_file(), io_err)
            # # END-IF

            # 2nd copy of auto align/sample
            # find out the path of the target file
            record_file_2_path = os.path.dirname(self._reductionSetup.get_record_2nd_file())
            if self._reductionSetup.is_alignment_run:
                categorized_2_record_file = os.path.join(record_file_2_path, 'AutoRecordAlign.txt')
            else:
                categorized_2_record_file = os.path.join(record_file_2_path, 'AutoRecordData.txt')

            if os.path.exists(categorized_2_record_file) is False and status2:
                # target record file does not exist and previous write-to-file is successful
                try:
                    shutil.copy(categorized_record_file, categorized_2_record_file)
                    os.chmod(categorized_2_record_file, 0666)
                except IOError as io_err:
                    return_status = False
                    return_message += 'Unable to copy {0} to {1} due to {2}.\n' \
                                      ''.format(categorized_record_file, categorized_2_record_file,
                                                io_err)
            else:
                # write to the 2nd copy
                status4, message4 = self._export_experiment_log(categorized_2_record_file,
                                                                sample_name_list, sample_title_list,
                                                                sample_operation_list, patch_list)
                return_status = return_status and status4
                return_message += message4 + '\n'
            # END-IF-ELSE
        # END-IF-ELSE (auto record only)

        # process standard sample for VULCAN/VDRIVE
        if self._reductionSetup.is_standard:
            standard_dir, standard_record = self._reductionSetup.get_standard_processing_setup()
            status5, message5 = self._export_experiment_log(standard_record,
                                                            sample_name_list, sample_title_list,
                                                            sample_operation_list, patch_list)
            return_status = return_status and status5
            return_message += message5 + '\n'
        # END-IF

        return return_status, return_message

    def export_log_files(self):
        """
        Export sample logs to multiple CSV files.  The log files include
        1. Furnace log;
        2. Generic DAQ log;
        3. Load frame/MTS log;
        4. VULCAN sample environment log;
        NOTE: Log files are not RECORD files
        :return: 2-tuple. (boolean: status, string: message)
        """
        # check whether it is necessary
        if self._reductionSetup.get_vdrive_log_dir() is None:
            return True, 'No requirement'

        # get essential parameters
        log_dir = self._reductionSetup.get_vdrive_log_dir()
        run_number = self._reductionSetup.get_run_number()
        ipts = self._reductionSetup.get_ipts_number()

        # export Furnace log
        self.export_furnace_log(self._dataWorkspaceName, log_dir, run_number)

        # Export Generic DAQ log
        self.export_generic_daq_log(log_dir, ipts, run_number)

        # Export load frame /MTS log
        self.export_mts_log()

        # Export standard VULCAN sample environment data
        self.export_sample_environment_log(log_dir, ipts, run_number)

        return True, 'Exporting log file successfully.'

    def export_furnace_log(self, log_ws_name, output_directory, run_number):
        """
        Export the furnace log.
        1. File name: furnace
        :param log_ws_name:
        :param output_directory:
        :param run_number:
        :return:
        """
        # check inputs
        assert isinstance(log_ws_name, str), 'Log workspace name must be a string'
        assert AnalysisDataService.doesExist(log_ws_name), 'Log workspace %s does not exist in data service.' \
                                                           '' % log_ws_name
        assert isinstance(output_directory, str), 'Output directory {0} must be a string.'.format(output_directory)
        assert isinstance(run_number, int), 'Run number must be an integer.'
        assert os.path.exists(output_directory) and os.path.isdir(output_directory), \
            'Output directory must be an existing directory.'

        furnace_log_file_name = os.path.join(output_directory, "furnace%d.txt" % run_number)
        self.generate_csv_log(furnace_log_file_name, Furnace_Header_List, None)

        return

    def export_generic_daq_log(self, output_directory, ipts, run_number):
        """
        Export the generic DAQ log
        :param output_directory:
        :param ipts:
        :param run_number:
        :return:
        """
        # organized by dictionary
        if run_number >= 69214:
            for ilog in xrange(1, 17):
                Generic_DAQ_List.append(("tc.user%d" % ilog, "tc.user%d" % ilog))

        # Format to lists for input
        sample_log_name_list = list()
        header_item_list = list()
        for i in xrange(len(Generic_DAQ_List)):
            title = Generic_DAQ_List[i][0]
            log_name = Generic_DAQ_List[i][1]

            header_item_list.append(title)
            if len(log_name) > 0:
                sample_log_name_list.append(log_name)

        header_str = ""
        for title in header_item_list:
            header_str += "%s\t" % title

        output_file_name = os.path.join(output_directory, 'IPTS-%d-GenericDAQ-%d.txt' % (ipts, run_number))
        self.generate_csv_log(output_file_name, sample_log_name_list, header_str)

        return

    def export_sample_environment_log(self, output_dir, ipts, run_number):
        """ Export Vulcan sample environment log
        Requirements
        Guarantees: export the file name as 'Vulcan-IPTS-XXXX-SEnv-RRRR.txt'
        """
        # Check inputs
        assert isinstance(ipts, int), 'IPTS must be integer.'
        assert isinstance(run_number, int), 'Run number must be integer'

        # Create list of the sample logs to be exported.
        # each element is a 2-tuple of string as (log name in output log file, log name in workspace)
        sample_log_name_list = []
        header_title_list = []
        for i in xrange(len(VulcanSampleLogList)):
            title = VulcanSampleLogList[i][0].strip()
            log_name = VulcanSampleLogList[i][1].strip()

            header_title_list.append(title)
            if len(log_name) > 0:
                sample_log_name_list.append(log_name)
        # END-FOR

        # For header string from list
        header_str = ''
        for title in header_title_list:
            header_str += "%s\t" % title

        # export file
        env_log_name = 'Vulcan-IPTS-%d-SEnv-%d.txt' % (ipts, run_number)
        env_log_name = os.path.join(output_dir, env_log_name)
        self.generate_csv_log(log_file_name=env_log_name,
                              sample_log_names=sample_log_name_list,
                              header=header_str)

        return

    def export_mts_log(self):
        """
        Export MTS log
        :return:
        """
        # Format to lists for input
        sample_log_names_list = list()
        header = list()
        for i in xrange(len(MTS_Header_List)):
            title = MTS_Header_List[i][0]
            log_name = MTS_Header_List[i][1]

            header.append(title)
            if len(log_name) > 0:
                sample_log_names_list.append(log_name)

        head_string = ""
        for title in header:
            head_string += "%s\t" % title

        # output file name
        out_log_file_name = 'IPTS-%d-MTSLoadFrame-%d.txt' % (self._reductionSetup.get_ipts_number(),
                                                             self._reductionSetup.get_run_number())
        out_log_file_name = os.path.join(self._reductionSetup.get_vdrive_log_dir(),
                                         out_log_file_name)

        # Make a new name
        self.generate_csv_log(log_file_name=out_log_file_name,
                              sample_log_names=sample_log_names_list,
                              header=head_string)
        return

    @staticmethod
    def generate_record_file_format():
        """
        """
        sample_title_list = list()
        sample_name_list = list()
        sample_operation_list = list()
        for i_sample in xrange(len(RecordBase)):
            sample_title_list.append(RecordBase[i_sample][0])
            sample_name_list.append(RecordBase[i_sample][1])
            sample_operation_list.append(RecordBase[i_sample][2])

        return sample_title_list, sample_name_list, sample_operation_list

    def generate_csv_log(self, log_file_name, sample_log_names, header):
        """
        Generate a log file in csv format.
        If the log file has existed, then rename the existing log file.  It will be tried for 100 times
        :param log_file_name:
        :param sample_log_names:
        :param header:
        :return:
        """
        # Make a new name by avoiding deleting the existing one.
        if os.path.exists(log_file_name):
            # if the file does exists, then save the original file
            # split extension and file name
            file_name, file_ext = os.path.splitext(log_file_name)
            max_attempts = 99
            num_attempts = 0
            while num_attempts < max_attempts:
                # form new name
                back_file_name = file_name + '_%02d' % num_attempts + file_ext
                # check backup file name
                if os.path.exists(back_file_name) and num_attempts < max_attempts - 1:
                    num_attempts += 1
                else:
                    # save last file
                    shutil.copy(log_file_name, back_file_name)
                    os.chmod(back_file_name, 0666)
                    break
            # END-WHILE()
        # END-IF

        # export log to CSV file
        mantidsimple.ExportSampleLogsToCSVFile(InputWorkspace=self._dataWorkspaceName,
                                               OutputFilename=log_file_name,
                                               SampleLogNames=sample_log_names,
                                               WriteHeaderFile=True,
                                               TimeZone=TIMEZONE2,
                                               Header=header)

        # change the file permission
        try:
            os.chmod(log_file_name, 0666)
        except OSError as os_err:
            self._myLogInfo += 'Unable to modify permission mode of {0}.\n'.format(log_file_name)

        return log_file_name

    def generate_1d_plot(self):
        """
        Export 1-D plot of the reduced powder pattern
        :return:
        """
        try:
            mantidsimple.SavePlot1D(InputWorkspace=self._reductionSetup.get_reduced_workspace(),
                                    OutputFilename=self._reductionSetup.get_plot_file(),
                                    YLabel='Intensity')
        except ValueError as err:
            self._myLogInfo += "Unable to generate 1D plot for run %s caused by %s. \n" \
                               "" % (str(self._reductionSetup.get_run_number()), str(err))
        except RuntimeError as err:
            self._myLogInfo += "Unable to generate 1D plot for run %s caused by %s. \n" \
                               "" % (str(self._reductionSetup.get_run_number()), str(err))
        # Try-Exception

        return

    def get_reduced_files(self):
        """
        get the list of output reduced files
        :return:
        """
        return self._reducedDataFiles[:]

    def get_reduced_workspaces(self, chopped):
        """

        :param chopped:
        :return: 2-tuples
        [1] non-chopped data: True/False, (VDrive workspace, Mantid TOF workspace, Mantid DSpacing workspace)
        """
        # early return for chopped data
        if chopped:
            return True, self._reducedWorkspaceList[:]

        return self._reduceGood, (self._reducedWorkspaceVDrive, self._reducedWorkspaceMtd, self._reducedWorkspaceDSpace)

    def load_meta_data_from_file(self):
        """
        Load NeXus file. If reducing to GSAS is also required, then load the complete NeXus file. Otherwise,
        load the sample log only
        :return:
        """
        # in case of GSAS is reduced
        self._dataWorkspaceName = 'VULCAN_%d_event' % self._reductionSetup.get_run_number()
        if AnalysisDataService.doesExist(self._dataWorkspaceName):
            return True, ''

        # no such workspace exists, then only need to load the meta data
        self._dataWorkspaceName = "VULCAN_%d_MetaDataOnly" % (self._reductionSetup.get_run_number())
        try:
            mantidsimple.Load(Filename=self._reductionSetup.get_event_file(),
                              OutputWorkspace=self._dataWorkspaceName,
                              MetaDataOnly=True,
                              LoadLogs=True)
        except RuntimeError as err:
            message = 'Unable to load NeXus file %s due to %s. ' % (self._reductionSetup.get_event_file(),
                                                                    str(err))
            return False, message

        return True, ''

    @staticmethod
    def load_vanadium_gda(van_gda_file, van_run_number, vanadium_tag):
        """
        :param van_gda_file:
        :param van_run_number:
        :param vanadium_tag:
        :return:
        """
        assert isinstance(van_gda_file, str), 'Vanadium GSAS file {0} must be a string but not a {1}.' \
                                              ''.format(van_gda_file, type(van_gda_file))

        van_ws_name = 'Vanadium_{0}_{1}'.format(van_run_number, vanadium_tag)
        if not AnalysisDataService.doesExist(van_ws_name):
            mantidsimple.LoadGSS(Filename=van_gda_file, OutputWorkspace=van_ws_name)

        return van_ws_name

    def reduce_powder_diffraction_data(self, event_file_name=None, user_gsas_file_name=None):
        """
        Reduce powder diffraction data.
        required parameters:  ipts, run number, output dir
        :return: 3-tuples, status, message, output workspace name
        """
        # check whether it is required to reduce GSAS
        # TODO/FIXME/ASAP - How to specify GSAS dir from GUI
        if self._reductionSetup.get_gsas_dir() is None:
            return False, 'No reduction as it is not required because GSAS directory is not specified.', None

        message = ''
        # get the event file name
        if event_file_name is None:
            raw_event_file = self._reductionSetup.get_event_file()
        else:
            raw_event_file = event_file_name
        assert isinstance(raw_event_file, str), 'User specified event file name {0} must be a string but not a {1}.'.format(raw_event_file, type(raw_event_file))
        # END-IF-ELSE

        # set up binning parameters
        if self._is_nED is False and self._reductionSetup.align_bins_to_vdrive_standard:
            # pre-nED: required to align bins to VDRIVE standard
            binning_parameter = "5000, -0.0005, 70000"
            bin_in_d = False
        else:
            # regular binning parameters
            binning_parameter = self._reductionSetup.binning_parameters
            # print 'Default or user given binning parameters? {0}'.format(binning_parameter)
            if binning_parameter.count(',') == 0:
                bin_in_d = True
            elif binning_parameter.count(',') == 2:
                max_x = float(binning_parameter.split(',')[2])
                if max_x < 100:
                    bin_in_d = True
                else:
                    bin_in_d = False
            else:
                # unacceptable binning parameters. return with False
                return False, 'Binnig parameters {0} is not acceptable.'.format(binning_parameter), None
        # END-IF

        # get the output directory for GSAS file
        if user_gsas_file_name is None:
            gsas_file_name = self._reductionSetup.get_gsas_file(main_gsas=True)
        else:
            gsas_file_name = user_gsas_file_name
            self._reductionSetup.set_gsas_file(gsas_file_name, main_gsas=True)

        orig_gsas_name = gsas_file_name
        gsas_file_name, gsas_message, output_access_error, del_exist = self.pre_process_output_gsas(gsas_file_name)
        if output_access_error:
            return False, 'Unable to write GSAS file {0} due to {1}'.format(gsas_file_name, gsas_message), None

        self._myLogInfo += gsas_message + '\n'

        # reduce data
        try:
            print ('[INFO] SNSPowderReduction On File {0} to {1}'.format(raw_event_file, gsas_file_name))
            mantidsimple.SNSPowderReduction(Filename=raw_event_file,
                                            PreserveEvents=True,
                                            CalibrationFile=self._reductionSetup.get_focus_file(),
                                            CharacterizationRunsFile=self._reductionSetup.get_characterization_file(),
                                            Binning=binning_parameter,
                                            BinInDspace=bin_in_d,
                                            SaveAS="",
                                            OutputDirectory=self._reductionSetup.get_gsas_dir(),
                                            NormalizeByCurrent=False,
                                            FilterBadPulses=0,
                                            CompressTOFTolerance=0.,
                                            FrequencyLogNames="skf1.speed",
                                            WaveLengthLogNames="skf12.lambda",
                                            FinalDataUnits='dSpacing')

            # reduced workspace should be in unit as dSpacing
            reduced_ws_name = 'VULCAN_%d' % self._reductionSetup.get_run_number()
            if AnalysisDataService.doesExist(reduced_ws_name) is False:
                # special case for random event file
                reduced_ws_name = os.path.basename(raw_event_file).split('_event.nxs')[0]
            assert AnalysisDataService.doesExist(reduced_ws_name), 'Reduced workspace %s is not in ' \
                                                                   'ADS.' % reduced_ws_name

        except RuntimeError as run_err:
            self._myLogInfo += '[Error] Unable to reduce workspace %s due to %s.\n' \
                               '' % (self._dataWorkspaceName, str(run_err))
            return False, str(run_err), None
        except AssertionError as ass_err:
            return False, str(ass_err), None
        # END-IF-ELSE

        # check the binning parameters
        # NOTE: no constant binning step is allowed here to avoid confusion from users
        bin_param_str_list = binning_parameter.split(',')
        if len(bin_param_str_list) == 1:
            bin_size = abs(float(bin_param_str_list[0]))
        elif len(bin_param_str_list) == 3:
            bin_size = abs(float(bin_param_str_list[1]))
        else:
            bin_size = -0.001

        if abs(bin_size - 0.001) > 1.E-6:
            # different from IDL binning
            not_align_idl = True
        else:
            # same as IDL binning
            not_align_idl = False

        # reconstruct
        if not_align_idl:
            ew_params = '5000, {0}, 70000'.format(-1*abs(bin_size))
        else:
            ew_params = '5000.,-0.001,70000.'

        # Save to GSAS file
        # TODO/NEXT - vulcan.prm should be input as an argument
        self.export_to_gsas(reduced_workspace=reduced_ws_name,
                            gsas_file_name=gsas_file_name,
                            gsas_iparm_file_name='vulcan.prm',
                            delete_exist_gsas_file=del_exist,
                            east_west_binning_parameters=ew_params,
                            high_angle_binning_parameters='5000.,-0.0003,70000.',
                            not_align_idl=not_align_idl)

        if output_access_error:
            error_message = 'Code001: Unable to write GSAS file to {0}. Write to {1} instead.\n' \
                            ''.format(orig_gsas_name, gsas_file_name)
            self._myLogInfo += error_message

        return True, self._myLogInfo, reduced_ws_name

    def export_to_gsas(self, reduced_workspace, gsas_file_name, gsas_iparm_file_name, delete_exist_gsas_file,
                       east_west_binning_parameters, high_angle_binning_parameters, not_align_idl):
        """ export reduced workspace to GSAS file
        :param reduced_workspace:
        :param gsas_file_name:
        :param gsas_iparm_file_name: default '"Vulcan.prm"'
        :param delete_exist_gsas_file:
        :param east_west_binning_parameters:
        :param high_angle_binning_parameters:
        :param not_align_idl:
        :return:
        """
        # convert unit to TOF and Rebin for exporting reduced data to GSAS
        mantidsimple.ConvertUnits(InputWorkspace=reduced_workspace,
                                  OutputWorkspace=reduced_workspace,
                                  Target="TOF",
                                  EMode="Elastic",
                                  AlignBins=False)

        # # delete existing GSAS file
        # if delete_exist_gsas_file:
        #     os.remove(gsas_file_name)

        pre_ned = False
        if self._is_nED is False and self._reductionSetup.align_bins_to_vdrive_standard:
            # align bins to VDrive standard for VDRIVE to analyze the data (pre-nED)
            vdrive_bin_ws_name = '{0}_V2Bank'.format(reduced_workspace)

            # # rebin to regular bin size: east and west
            # mantidsimple.Rebin(InputWorkspace=reduced_workspace,
            #                    OutputWorkspace=reduced_workspace,
            #                    Params=east_west_binning_parameters)

            # save to Vuclan GSAS
            bin_file_name = self._reductionSetup.get_vulcan_bin_file()
            try:
                mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_workspace,
                                           BinFilename=bin_file_name,
                                           OutputWorkspace=vdrive_bin_ws_name,
                                           GSSFilename=gsas_file_name,
                                           IPTS=self._reductionSetup.get_ipts_number(),
                                           GSSParmFilename=gsas_iparm_file_name)
                # Add special property to output workspace
                final_ws = AnalysisDataService.retrieve(vdrive_bin_ws_name)
                final_ws.getRun().addProperty('VDriveBin', True, replace=True)
                pre_ned = True
            except ValueError as value_err:
                # write again to a temporary directory
                raise RuntimeError('[ERROR] Failed to run SaveVulcanGSS to GSAS file {0}. FYI ValueError: {1}.'
                                   ''.format(gsas_file_name, value_err))

        elif self._is_nED:
            # nED NeXus. save to VDRIVE GSAS format with 3 banks of different resolution
            # NOTE: The bank ID (from 1) is required here

            # TODO FIXME NOW3 (1) size of binning table! (2) instrument geometry for 27 banks!
            bin_table_name = create_bin_table(reduced_workspace, not_align_idl,
                                              self._reductionSetup.get_vulcan_bin_file(),
                                              (east_west_binning_parameters, high_angle_binning_parameters))

            # TEST ASAP NOW3 - Create a binning table!
            # save. it is an option to use IDL bin provided from VDRIVE
            mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_workspace,
                                       BinningTable=bin_table_name,
                                       OutputWorkspace=reduced_workspace,
                                       GSSFilename=gsas_file_name,
                                       IPTS=self._reductionSetup.get_ipts_number(),
                                       GSSParmFileName=gsas_iparm_file_name)
            print ('[DB...BAT] gsas iparm file: {0}, Output GSS: {1}'.format(gsas_iparm_file_name, gsas_file_name))
            # save_vulcan_gsas.save_vulcan_gss(reduced_workspace,
            #                                  binning_parameter_list=bin_param_list,
            #                                  output_file_name=gsas_file_name,
            #                                  ipts=self._reductionSetup.get_ipts_number(),
            #                                  gsas_param_file=gsas_iparm_file_name)

            vdrive_bin_ws_name = reduced_workspace
        else:
            # write to GSAS file with Mantid bins
            mantidsimple.SaveGSS(InputWorkspace=reduced_workspace,
                                 Filename=gsas_file_name,
                                 SplitFiles=False)
            vdrive_bin_ws_name = reduced_workspace
        # END-IF-ELSE

        # check whether it is correctly reduced
        if not os.path.exists(gsas_file_name):
            raise RuntimeError('Output GSAS file {0} cannot be found.'.format(gsas_file_name))

        self._reductionSetup.set_reduced_workspace(vdrive_bin_ws_name)

        # merge banks
        if self._reductionSetup.merge_banks:
            # merge all the banks to 1
            mantidsimple.SumSpectra(InputWorkspace=vdrive_bin_ws_name,
                                    OutputWorkspace=vdrive_bin_ws_name,
                                    StartWorkspaceIndex=0,
                                    EndWorkspaceIndex=1)

        # set up the output file's permit for other users to modify
        os.chmod(gsas_file_name, 0666)
        self._reducedDataFiles.append(gsas_file_name)

        if self._reductionSetup.normalized_by_vanadium:
            gsas_name2 = os.path.splitext(gsas_file_name)[0] + '_v.gda'
            self._normalize_by_vanadium(vdrive_bin_ws_name, gsas_name2, pre_ned)

        # END-IF (vanadium)

        # collect result
        self._reducedWorkspaceDSpace = None  # dSpacing reduced workspace has been replaced by TOF
        self._reducedWorkspaceMtd = reduced_workspace
        self._reducedWorkspaceVDrive = vdrive_bin_ws_name
        self._reduceGood = True

        # TODO FIXME ASAP NOW3 - Delete workspace (event or etc) as an option!

        return

    @staticmethod
    def pre_process_output_gsas(gsas_file_name):
        """
        get the full path for output GSAS file
        :param gsas_file_name: proposed GSAS file
        :return: 4-tuple. (final (may be modified) GSAS file name, message, flag for access error, flag to delete existing gsas
        """
        message = ''
        output_access_error = False
        del_curr_gsas = False

        # check directory
        gsas_dir = os.path.dirname(gsas_file_name)
        if os.path.exists(gsas_dir) is False:
            # directory for proposed output GSAS file does not exist
            output_access_error = True
            message += 'Output directory "{0}" does not exist.'.format(gsas_dir)
        elif os.access(gsas_dir, os.W_OK) is False:
            # user has no write permission for the directory
            output_access_error = True
            message += 'User hasn\'t the write permission to directory {0}'.format(gsas_dir)
        elif os.path.exists(gsas_file_name) and os.access(gsas_file_name, os.W_OK) is False:
            # GSAS file exists but user cannot rewrite
            output_access_error = True
            message += 'User cannot overwrite existing GSAS file {0}'.format(gsas_file_name)
        elif os.path.exists(gsas_file_name):
            # re-write: so delete the original gsas file first
            message += 'Previously reduced GSAS file {0} is to be overwritten.'.format(gsas_file_name)
            del_curr_gsas = True

        return gsas_file_name, message, output_access_error, del_curr_gsas

    def _normalize_by_vanadium(self, reduced_gss_ws_name, output_file_name, is_pre_ned):
        """
        normalize by vanadium
        :param reduced_gss_ws_name:
        :param output_file_name:
        :param is_pre_ned: flag to show whether the data is collect before nED was installed.
        :return:
        """
        # check inputs and get input workspace
        assert isinstance(reduced_gss_ws_name, str), 'Reduced GSAS workspace name {0} must be a string but not a {1}.' \
                                                     ''.format(reduced_gss_ws_name, type(reduced_gss_ws_name))
        reduced_gss_ws = AnalysisDataService.retrieve(reduced_gss_ws_name)

        # get vanadium information according to vanadium run number
        van_info_tuple = self._reductionSetup.get_vanadium_info()
        assert van_info_tuple is not None, 'Vanadium information tuple cannot be None.'
        van_run_number, van_gda_file, vanadium_tag = van_info_tuple
        van_ws_name = self.load_vanadium_gda(van_gda_file, van_run_number, vanadium_tag)

        # get vanadium workspace
        van_ws = AnalysisDataService.retrieve(van_ws_name)

        # align bins
        if not self._is_nED:
            check_result, message = check_point_data_log_binning(van_ws_name, standard_bin_size=0.01, tolerance=1.E-5)
            align_bins(van_ws_name, reduced_gss_ws_name)
        # END-IF

        # normalize and write out again
        reduced_gss_ws = reduced_gss_ws / van_ws

        mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_gss_ws,
                                   OutputWorkspace=reduced_gss_ws_name,
                                   GSSFilename=output_file_name,
                                   IPTS=self._reductionSetup.get_ipts_number(),
                                   GSSParmFilename="Vulcan.prm")

        return

    def special_operation_auto_reduction_service(self):
        """some special operations used in auto reduction service only
        :return:
        """
        if not self._reductionSetup.is_auto_reduction_service:
            return True, 'No operation for auto reduction special.'

        # 2nd copy for Ke if it IS NOT an alignment run
        if not self._reductionSetup.is_alignment_run and self._reductionSetup.get_gsas_2nd_dir() and self._reductionSetup._autoReduceLogOnly is False:
            first_gsas_file = self._reductionSetup.get_gsas_file(main_gsas=True)
            if os.path.exists(first_gsas_file) is False:
                raise RuntimeError('First GSAS file {0} cannot be found.'.format(first_gsas_file))

            self.duplicate_gsas_file(self._reductionSetup.get_gsas_file(main_gsas=True),
                                     self._reductionSetup.get_gsas_2nd_dir())

        return True, ''


def align_bins(src_workspace_name, template_workspace_name):
    """
    Align X bins in order to make up the trivial difference of binning between MatrixWorkspace,
    which is caused by numerical error
    :except: RuntimeError if the workspace cannot be found in ADS
    :except: AssertionError if the inputs are not strings
    :param src_workspace_name:
    :param template_workspace_name:
    :return:
    """
    # check and get workspace
    assert isinstance(src_workspace_name, str), 'Name of workspace to align {0} must be a string but not a {1}.' \
                                                ''.format(src_workspace_name, type(src_workspace_name))
    assert isinstance(template_workspace_name, str), 'Name of binning template workspace {0} must be a string ' \
                                                     'but not a {1}.'.format(template_workspace_name,
                                                                             type(template_workspace_name))

    # check workspaces existing or not
    if AnalysisDataService.doesExist(src_workspace_name) is False:
        raise RuntimeError('Workspace {0} to align cannot be found in ADS.'.format(src_workspace_name))
    if AnalysisDataService.doesExist(template_workspace_name) is False:
        raise RuntimeError('Binning template workspace {0} does not exist in ADS.'.format(template_workspace_name))

    align_ws = AnalysisDataService.retrieve(src_workspace_name)
    template_ws = AnalysisDataService.retrieve(template_workspace_name)

    if not (template_ws.isHistogramData() and align_ws.isHistogramData()):
        raise RuntimeError('Neither template workspace nor ready-to-align workspace can be PointData.')

    # get template X
    num_histograms = align_ws.getNumberHistograms()
    template_vec_x = template_ws.readX(0)
    for i_ws in range(num_histograms):
        array_x = align_ws.dataX(i_ws)
        if len(array_x) != len(template_vec_x):
            raise RuntimeError('Template workspace and workspace to align bins do not have same number of bins.')
        numpy.copyto(array_x, template_vec_x)
    # END-FOR

    return


def check_point_data_log_binning(ws_name, standard_bin_size=0.01, tolerance=1.E-5):
    """
    check bin size with standard deviation for a PointData MatrixWorkspace
    :param ws_name:
    :param standard_bin_size: standard logarithm bin size 0.01
    :param tolerance: maximum standard deviation
    :return: 2-tuple. boolean/str as True/False and message
    """
    # check input & get workspace
    assert isinstance(ws_name, str), 'Workspace name {0} must be a string but not a {1}'.format(ws_name, type(ws_name))

    workspace = AnalysisDataService.retrieve(ws_name)

    # convert to PointData if necessary
    if workspace.isHistogramData():
        # convert to PointData
        temp_ws_name = ws_name + '_temp123'
        mantidsimple.ConvertToPointData(InputWorkspace=ws_name, OutputWorkspace=temp_ws_name)
        temp_ws = AnalysisDataService.retrieve(temp_ws_name)
        vec_x = temp_ws.readX(0)
    else:
        vec_x = workspace.readX(0)
        temp_ws_name = None

    # check logarithm binning
    bins = (vec_x[1:] - vec_x[:-1])/vec_x[:-1]
    bin_size = numpy.average(bins)
    bin_std = numpy.std(bins)

    if abs(bin_size - standard_bin_size) > 1.E-7:
        return False, 'Bin size {0} != standard bin size {1}'.format(bin_size, standard_bin_size)

    if bin_std > tolerance:
        return False, 'Standard deviation of bin sizes {0} is beyond tolerance {1}.'.format(bin_std, tolerance)

    # delete temp
    if temp_ws_name is not None:
        mantidsimple.DeleteWorkspace(Workspace=temp_ws_name)

    return True, ''


class MainUtility(object):
    """
    Utility methods for main
    """
    @staticmethod
    def parse_argv(opts, argv):
        """
        Parse arguments and put to dictionary
        :param opts:
        :param argv:
        :return: 2-tuple : status (boolean) and ReductionSetup (or None)
        """
        # Initialize
        reduction_setup = ReductionSetup()

        # process input arguments in 2 different modes: auto-reduction and manual reduction (options)
        if len(argv) == 0:
            print "Auto   reduction Inputs: [--dry] 'File name with full length'  'Output directory' "
            print "Manual reduction Inputs:   --help"
            return False, reduction_setup

        # test dry run
        if len(opts) == 0:
            # auto mode
            is_default_mode = True
            if '-d' in argv or '--dryrun' in argv:
                reduction_setup.set_dry_run(True)

            if '--log' in argv:
                reduction_setup.set_log_only(True)

        elif len(opts) == 1 and opts[0][0] in ("-d", "--dryrun"):
            # dry run for auto mode
            reduction_setup.set_dry_run(True)
            is_default_mode = True

        else:
            # manual mode
            is_default_mode = False
        # END-IF-ELSE

        # parse or set up as default
        if is_default_mode:
            # auto reduction mode (as default)

            # set up event file path and output directory
            reduction_setup.set_event_file(argv[0])
            reduction_setup.set_output_dir(argv[1])

            # set up log directory, record files and etc.
            reduction_setup.set_auto_reduction_mode()

        else:
            # manual reduction mode
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    # Help
                    MainUtility.print_main_help()
                    return False, None
                elif opt in ("-i", "--ifile"):
                    # Input NeXus file
                    reduction_setup.set_event_file(arg)
                elif opt in ("-o", "--ofile"):
                    # Output directory
                    reduction_setup._outputDirectory = arg
                elif opt in ("-l", "--log") and arg != '0':
                    # Log file
                    reduction_setup.set_log_dir(arg)
                elif opt in ("-g", "--gsas") and arg != '0':
                    # GSAS file
                    reduction_setup.set_gsas_dir(arg, main_gsas=True)
                elif opt in ("-G", "--gsas2") and arg != '0':
                    # GSAS file of 2nd copy
                    reduction_setup.set_gsas_dir(arg, main_gsas=False)
                elif opt in ("-r", "--record") and arg != '0':
                    # AutoReduce.txt
                    reduction_setup.set_record_file(arg, main_record=True)
                elif opt in ("-R", "--record2") and arg != '0':
                    # AutoReduce.txt in 2nd directory as a backup
                    reduction_setup.set_record_file(arg, main_record=False)
                elif opt in ("-d", "--dryrun"):
                    # Dry run
                    reduction_setup.set_dry_run(True)
                elif opt in ('-f', '--focus') and arg != '0':
                    # focus file
                    reduction_setup.set_focus_file(arg)
                elif opt in ('-c', '--charact') and arg != '0':
                    # characterization file
                    reduction_setup.set_charact_file(arg)
                elif opt in ('-b', '--bin') and arg != '0':
                    # VULCAN binning file
                    reduction_setup.set_vulcan_bin_file(arg)
                # END-IF-ELSE
            # END-FOR (opt)
        # END-IF-ELSE (len(opt)==0)

        # Check requirements
        if reduction_setup.get_event_file() is None or reduction_setup.get_reduced_data_dir() is None:
            print "Both input event Nexus file %s and output directory %s must be given!" % (
                str(reduction_setup.get_event_file()), str(reduction_setup.get_reduced_data_dir()))
            return False, reduction_setup

        return True, reduction_setup

    @staticmethod
    def print_main_help():
        """
        Print help message1884
        :return:
        """
        help_str = ''

        help_str += "%s -i <inputfile> -o <outputdirectory> ... ...\n" % (sys.argv[0])
        help_str += "-i/ifile    : mandatory input NeXus file name. \n"
        help_str += "-o/ofile    : mandatory directory for output files. \n"
        help_str += "-l/log      : optional directory for sample log files. \n"
        help_str += "-g/gsas     : optional directory for GSAS file owned by owner. \n"
        help_str += "-G/gsas2    : optional directory to copy GSAS file to  with file mode 664.\n"
        help_str += "-r/record   : optional experiment record file name (writable only to auot reduction service).\n"
        help_str += "-R/record2  : experiment record file (can be modified by manual reduction).\n"
        help_str += "-d/dry      : dry run to check output status, file names and directories.\n"
        help_str += '-f/focus    : diffraction focus file.\n'
        help_str += '-c/charact  : characterization file.\n'
        help_str += '-b/bin      : binning file.\n'

        print 'Vulcan reduction helping: \n{0}'.format(help_str)

        return

    @staticmethod
    def process_inputs(argv):
        """

        :param argv:
        :return: 2-tuple
        """
        try:
            opts, args = getopt.getopt(argv, "hdi:o:l:g:G:r:R:", ["help", "ifile=", "ofile=", "log=",
                                                                  "gsas=", "gsas2=", "record=", "record2=",
                                                                  "dryrun"])
        except getopt.GetoptError:
            print "Exception: %s" % (str(getopt.GetoptError))
            print 'test.py -i <inputfile> -o <outputfile>'
            return False, None

        return True, (opts, args)

    @staticmethod
    def split_all_path(file_path):
        """
        split a path completely to each directory
        :return:
        """
        all_parts = []
        while 1:
            parts = os.path.split(file_path)
            if parts[0] == file_path:  # sentinel for absolute paths
                all_parts.insert(0, parts[0])
                break
            elif parts[1] == file_path:  # sentinel for relative paths
                all_parts.insert(0, parts[1])
                break
            else:
                file_path = parts[0]
                all_parts.insert(0, parts[1])

        return all_parts

# END-CLASS


def create_bin_table(data_ws, not_align_idl, h5_bin_file_name=None, binning_parameters=None):
    """
    create a TableWorkspace with binning information
    :param not_align_idl:
    :param data_ws:
    :param h5_bin_file_name:
    :param binning_parameters:
    :return:
    """
    def generate_binning_table(table_name):
        """
        generate an EMPTY binning TableWorkspace
        :param table_name:
        :return:
        """
        bin_table = mantidsimple.CreateEmptyTableWorkspace(OutputWorkspace=table_name)
        bin_table.addColumn('str', 'indexes')
        bin_table.addColumn('str', 'params')

        return bin_table

    def extrapolate_last_bin(bins):
        """
        :param bins:
        :return:
        """
        assert isinstance(bins, numpy.ndarray) and len(bins.shape) == 1, '{0} must be a 1D array but not {1}.' \
                                                                         ''.format(bins, type(bins))

        delta_bin = (bins[-1] - bins[-2]) / bins[-2]
        next_bin = bins[-1] * (1 + delta_bin)

        return next_bin

    # get input workspace
    if isinstance(data_ws, str):
        data_ws = AnalysisDataService.retrieve(data_ws)
    num_banks = data_ws.getNumberHistograms()

    if not_align_idl:
        # not aligned IDL
        assert isinstance(binning_parameters, list) or isinstance(binning_parameters, tuple),\
            'Binning parameters must be either tuple of list'
        assert len(binning_parameters) == 2, 'Must have both low resolution and high resolution'

        # create binning table
        bin_table_name = 'VULCAN_Binning_Table_{0}Banks'.format(num_banks)
        # if AnalysisDataService.doesExist(bin_table_name) is False:  FIXME how to avoid duplicate operation?
        bin_table_ws = generate_binning_table(bin_table_name)
        east_west_binning_parameters, high_angle_binning_parameters = binning_parameters

        if num_banks == 3:
            # west(1), east(1), high(1)
            bin_table_ws.addRow(['0, 1', '{0}'.format(east_west_binning_parameters)])
            bin_table_ws.addRow(['2', '{0}'.format(high_angle_binning_parameters)])
        elif num_banks == 7:
            # west (3), east (3), high (1)
            bin_table_ws.addRow(['0-5', '{0}'.format(east_west_binning_parameters)])
            bin_table_ws.addRow(['6', '{0}'.format(high_angle_binning_parameters)])
        elif num_banks == 27:
            # west (3), east (3), high (1)
            bin_table_ws.addRow(['0-17', '{0}'.format(east_west_binning_parameters)])
            bin_table_ws.addRow(['18-26', '{0}'.format(high_angle_binning_parameters)])
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))

    else:
        # use explicitly defined bins and thus matrix workspace is required
        # import h5 file
        base_table_name = os.path.basename(h5_bin_file_name).split('.')[0]

        # load vdrive bin file to 2 different workspaces
        bin_file = h5py.File(h5_bin_file_name, 'r')
        low_bins = bin_file['west_east_bank'][:]
        high_bins = bin_file['high_angle_bank'][:]
        bin_file.close()

        # append last value for both east/west bin and high angle bin
        low_bins = numpy.append(low_bins, extrapolate_last_bin(low_bins))
        high_bins = numpy.append(high_bins, extrapolate_last_bin(high_bins))

        low_bin_ws_name = '{0}_LowResBin'.format(base_table_name)
        high_bin_ws_name = '{0}_HighResBin'.format(base_table_name)
        if AnalysisDataService.doesExist(low_bin_ws_name) is False:
            mantidsimple.CreateWorkspace(low_bins, low_bins, NSpec=1, OutputWorkspace=low_bin_ws_name)
        if AnalysisDataService.doesExist(high_bin_ws_name) is False:
            mantidsimple.CreateWorkspace(high_bins, high_bins, NSpec=1, OutputWorkspace=high_bin_ws_name)

        # create binning table name
        bin_table_name = '{0}_{1}Bank'.format(base_table_name, num_banks)

        # no need to create this workspace again and again
        if AnalysisDataService.doesExist(bin_table_name):
            return bin_table_name

        # create binning table
        ref_bin_table = generate_binning_table(bin_table_name)

        if num_banks == 3:
            # west(1), east(1), high(1)
            ref_bin_table.addRow(['0, 1', '{0}: {1}'.format(low_bin_ws_name, 0)])
            ref_bin_table.addRow(['2', '{0}: {1}'.format(high_bin_ws_name, 0)])
        elif num_banks == 7:
            # west (3), east (3), high (1)
            ref_bin_table.addRow(['0-5', '{0}: {1}'.format(low_bin_ws_name, 0)])
            ref_bin_table.addRow(['6', '{0}: {1}'.format(high_bin_ws_name, 0)])
        elif num_banks == 27:
            # west (3), east (3), high (1)
            ref_bin_table.addRow(['0-17', '{0}: {1}'.format(low_bin_ws_name, 0)])
            ref_bin_table.addRow(['18-26', '{0}: {1}'.format(high_bin_ws_name, 0)])
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
    # END-IF-ELSE

    return bin_table_name


def main(argv):
    """ Main method
    1. Generating log files including
        1) Furnace log;
        2) Generic DAQ log;
        3) MTS log;
        4) New sample environment log
    2. Experiment log record including
        1) AutoRecord.txt
        2) AutoRecordAlign.txt (run title starts with 'Align:'
        3) AutoRecordData.txt
    3. Reducing and generating GSAS file
    """
    # process inputs
    status, ret_tuple = MainUtility.process_inputs(argv)
    if not status:
        return
    else:
        opts, args = ret_tuple

    # parse arguments
    status, reduction_setup = MainUtility.parse_argv(opts, argv)
    if not status:
        return

    # process and set calibration files
    reduction_setup.process_configurations()
    reduction_setup.set_default_calibration_files()

    # create reducer
    reducer = ReduceVulcanData(reduction_setup)

    # dry run
    if reduction_setup.is_dry_run():
        # dry run
        status, msg = reducer.dry_run()
        if status:
            print (msg)
        else:
            print ('Unable to execute dry run due to {0}'.format(msg))
        # check validity
        status, error_message = reduction_setup.check_validity()
        if not status:
            print ('Reduction setup is not valid due to {0}'.format(error_message))

    else:
        # execute
        if status and not reduction_setup.is_dry_run():
            # reduce data
            status, message = reducer.execute_vulcan_reduction(output_logs=True)
            if not status:
                raise RuntimeError('Auto reduction error: {0}'.format(message))
            print ('[Auto Reduction Successful: {0}]'.format(message))
        elif not status:
            # error message
            raise RuntimeError('Reduction Setup is not valid:\n%s' % error_message)

    return


# Command line
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        input_args = []
    else:
        input_args = sys.argv[1:]
    main(input_args)
