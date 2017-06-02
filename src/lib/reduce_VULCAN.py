################################################################################
#
# Auto reduction script for VULCAN
# Version 3.0 for both auto reduction service and manual
#
# Last version: reduce_VULCAN_141028.py
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
import stat
import shutil
import xml.etree.ElementTree as ET
import sys
import numpy
import pandas as pd

# sys.path.append("/opt/mantidnightly/bin")
import mantid.simpleapi as mantidsimple
import mantid
from mantid.api import AnalysisDataService
from mantid.kernel import DateAndTime

refLogTofFilename = "/SNS/VULCAN/shared/autoreduce/vdrive_log_bin.dat"
CalibrationFileName = "/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal"
CharacterFileName = "/SNS/VULCAN/shared/autoreduce/VULCAN_Characterization_2Banks_v2.txt"

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
    def binning_parameters(self):
        """
        return the binning parameters
        :return:
        """
        if self._binningParameters is None:
            # using default binning parameter
            bin_param_str = '5000., -0.001, 50000.'
        elif len(self._binningParameters) == 1:
            # only bin size is defined
            bin_param_str = '{0}, {1}, {2}'.format(5000., self._binningParameters[0], 50000.)
        elif len(self._binningParameters) == 3:
            # 3 are given
            bin_param_str = '{0}, {1}, {2}'.format(self._binningParameters[0], self._binningParameters[1],
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
            print "Log file will be written to directory %s. " % new_output_dir
        else:
            # non-auto reduction mode.
            new_output_dir = original_directory
            print "Log file will be written to the original directory %s. " % new_output_dir

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
        for file_name in [self._focusFileName, self._characterFileName, self._vulcanBinsFileName]:
            if not os.path.exists(file_name):
                error_message += 'Calibration file %s cannot be found.\n' % file_name

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
        self._runNumber = int(self._eventFileName.split('_')[1])

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

    def set_binning_parameters(self, min_tof, max_tof, bin_size):
        """

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
        assert isinstance(file_name, str), 'Input arg type error.'

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
        # output GSAS directory
        self._mainGSASDir = self.change_output_directory(self._outputDirectory, 'autoreduce/binnedgda')
        self._2ndGSASDir = self.change_output_directory(self._outputDirectory, 'binned_data')

        self.is_auto_reduction_service = True

        return

    def set_default_calibration_files(self):
        """
        set default calibration files
        :return:
        """
        self.set_focus_file(CalibrationFileName)
        self.set_charact_file(CharacterFileName)
        self.set_vulcan_bin_file(refLogTofFilename)

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
        assert isinstance(dir_name, str), 'directory name must be string'

        self._sampleLogDirectory = dir_name

        return

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

    def set_output_dir_to_archive(self, create_parent_directories=False):
        """
        set output directories as SNS archive
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
        if os.path.exists(self._cvInfoFileName) is False or \
                        os.path.exists(self._runInfoFileName) is False or \
                        os.path.exists(self._beamInfoFileName) is False:
            raise RuntimeError("PreNexus log file %s and/or %s cannot be accessed. " % (
                self._cvInfoFileName, self._runInfoFileName))

        return

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

        print '[DB...BAT] Patch List: ', patch_list

        return patch_list

    @staticmethod
    def get_last_line_in_binary_file(filename):
        """ Get the first and last line of a (possibly long) file
        """
        # Open an binary file
        with open(filename, 'rb') as binary_file:
            # Determine a roughly the size of a line
            first_line = next(binary_file).decode().strip()
            second_line = next(binary_file).decode().strip()
            line_size = len(second_line)

            try:
                # search from the end of line
                binary_file.seek(-2*line_size, 2)
                last_line = binary_file.readlines()[-1].decode().strip()
                binary_file.close()
            except IOError:
                # File is too short
                # close the file and re-open
                binary_file.close()
                binary_file = open(filename, 'rb')

                lines = binary_file.readlines()
                last_line = lines[-1]
        # END-WITH

        return first_line, last_line

    @staticmethod
    def remove_last_line_in_text(filename):
        """ Remove last line
        """
        # ifile = open(sys.argv[1], "r+", encoding = "utf-8")
        ifile = open(filename, "r+")

        ifile.seek(0, os.SEEK_END)
        pos = ifile.tell() - 1
        while pos > 0 and ifile.read(1) != "\n":
            pos -= 1
            ifile.seek(pos, os.SEEK_SET)

        if pos > 0:
            ifile.seek(pos, os.SEEK_SET)
            ifile.truncate()

        ifile.close()

        return

    def _getIPTS(self):
        """ Get IPTS
        Return: integer
        """
        tree = ET.parse(self._beamInfoFileName)

        root = tree.getroot()
        if root.tag != 'Instrument':
            raise NotImplementedError("Not an instrument")

        proposal = None
        for child in root:
            if child.tag == "Proposal":
                proposal = child
                break
        if proposal is None:
            raise NotImplementedError("Not have proposal")

        id_node = None
        for child in proposal:
            if child.tag == "ID":
                id_node = child
                break
        if id_node is None:
            raise NotImplementedError("No ID")

        ipts = id_node.text
        ipts = int(ipts)

        return ipts

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

        # print out error
        if len(error_message) > 0:
            print '[ERROR] Clear the reduced workspaces:\n{0}'.format(error_message)

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

        print 'Dry run:\n%s' % dry_run_str

        return True, dry_run_str

    @staticmethod
    def duplicate_gsas_file(source_gsas_file_name, target_directory):
        """ Duplicate gsas file to a new directory with file mode 664
        """
        # Verify input
        if os.path.exists(source_gsas_file_name) is False:
            print "Warning.  Input file wrong"
            return
        elif os.path.isdir(source_gsas_file_name) is True:
            print "Warning.  Input file is not file but directory."
            return
        if os.path.isabs(source_gsas_file_name) is not True:
            print "Warning"
            return

        # Create directory if it does not exist
        if os.path.isdir(target_directory) is not True:
            os.makedirs(target_directory)

        # Copy
        target_file_name = os.path.join(target_directory, os.path.basename(source_gsas_file_name))
        if os.path.isfile(target_file_name) is True:
            print "Destination GSAS file exists. "
            return
        else:
            shutil.copy(source_gsas_file_name, target_directory)
            os.chmod(target_file_name, 0664)

        return

    def execute_vulcan_reduction(self):
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
        # configure the ReductionSetup
        self._reductionSetup.process_configurations()

        # reduce and write to GSAS file
        is_reduce_good, msg_gsas, reduced_ws_name = self.reduce_powder_diffraction_data()
        if not is_reduce_good and msg_gsas.count('Code001') == 0:
            # error code: Code001 does not mean a bad reduction
            return False, 'Unable to generate GSAS file due to %s.' % msg_gsas
        if self._reductionSetup.is_standard:
            # standard sample for VULCAN
            gsas_file = self.get_reduced_files()[0]
            print '[DB...BAT] GSAS file generated is {0}.'.format(gsas_file)
            standard_dir, standard_record = self._reductionSetup.get_standard_processing_setup()
            try:
                shutil.copy(gsas_file, standard_dir)
            except IOError as io_err:
                print '[ERROR] Unable to write standard GSAS file to {0} due to IOError {1}' \
                      ''.format(standard_dir, io_err)
            except OSError as os_err:
                print '[ERROR] Unable to write standard GSAS file to {0} due to OSError {1}' \
                      ''.format(standard_dir, os_err)

        # load the sample run
        is_load_good, msg_load_file = self.load_data_file()
        if not is_load_good:
            return False, 'Unable to load source data file %s.' % self._reductionSetup.get_event_file()

        # check whether it is an alignment run
        self._reductionSetup.is_alignment_run = self.check_alignment_run()

        # export the sample log record file: AutoRecord.txt and etc.
        is_record_good, msg_record = self.export_experiment_records()

        # write experiment files
        is_log_good, msg_log = self.export_log_files()

        # special operations for auto reduction
        is_auto_good, msg_auto = self.special_operation_auto_reduction_service()

        final_message = ''
        final_message += msg_gsas + '\n'
        final_message += msg_load_file + '\n'
        final_message += msg_record + '\n'
        final_message += msg_log + '\n'
        final_message += msg_log + '\n'

        return is_record_good and is_log_good and is_auto_good, final_message

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
            print "Current file %s's mode is %s." % (target_file, file_access_mode)
            try:
                os.chmod(target_file, 0666)
            except OSError as os_err:
                print '[ERROR] Unable to set file {0} to mode 666 due to {1}.'.format(target_file, os_err)
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
        patcher = PatchRecord(self._instrumentName,
                              self._reductionSetup.get_ipts_number(),
                              self._reductionSetup.get_run_number())
        patch_list = patcher.export_patch_list()

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
            # 2nd copy of Auto Record . txt
            if os.path.exists(self._reductionSetup.get_record_2nd_file()):
                # if the target copy of AutoRecord.txt exists, then append
                status3, message3 = self._export_experiment_log(self._reductionSetup.get_record_2nd_file(),
                                                                sample_name_list, sample_title_list,
                                                                sample_operation_list, patch_list)
                return_status += status3
                return_message += message3 + '\n'
            else:
                # if the target copy of AutoRecord.txt does not exist
                if os.access(self._reductionSetup.get_record_2nd_file(), os.W_OK):
                    shutil.copy(self._reductionSetup.get_record_file(),
                                self._reductionSetup.get_record_2nd_file())
                    # change mode to 666
                    try:
                        os.chmod(self._reductionSetup.get_record_2nd_file(), 0666)
                    except IOError as io_err:
                        return_status = False
                        return_message += 'Unable to change file {0} mode to 666 due to {1}.\n' \
                                          ''.format(self._reductionSetup.get_record_2nd_file(), io_err)
                else:
                    return_status = False
                    return_message += 'Unable to write file {0} without writing permission.\n' \
                                      ''.format(self._reductionSetup.get_record_2nd_file())
            # END-IF-ELSE

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
        4. VULCAN sample environment log
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
        assert isinstance(output_directory, str), 'Output directory must be a string.'
        assert os.path.exists(output_directory) and os.path.isdir(output_directory), \
            'Output directory must be an existing directory.'
        assert isinstance(run_number, int), 'Run number must be an integer.'

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
        os.chmod(log_file_name, 0666)

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
            print "Unable to generate 1D plot for run %s caused by %s. " % (str(self._reductionSetup.get_run_number()),
                                                                            str(err))
        except RuntimeError as err:
            print "Unable to generate 1D plot for run %s caused by %s. " % (str(self._reductionSetup.get_run_number()),
                                                                            str(err))
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

    def load_data_file(self):
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

    def reduce_powder_diffraction_data(self, event_file_name=None):
        """
        Reduce powder diffraction data.
        required parameters:  ipts, run number, output dir
        :return: 3-tuples, status, message, output workspace name
        """
        # check whether it is required to reduce GSAS
        if self._reductionSetup.get_gsas_dir() is None:
            return True, 'No reduction as it is not required.', None

        # reduce data
        message = ''
        try:
            gsas_file_name = self._reductionSetup.get_gsas_file(main_gsas=True)
            if os.path.isfile(gsas_file_name):
                if os.access(gsas_file_name, os.W_OK):
                    # file is writable
                    message += 'GSAS file (%s) has been reduced for run %s already.  It will be overwritten.\n' \
                               '' % (gsas_file_name, str(self._reductionSetup.get_run_number()))
                else:
                    # file cannot be overwritten, then abort!
                    message += 'GSAS file (%s) exists and cannot be overwritten.\n' % gsas_file_name
                    return False, message, None
            # END-IF

            # check output
            out_dir = self._reductionSetup.get_gsas_dir()
            if os.path.exists(out_dir) is False:
                return False, 'Output directory "{0}" does not exist.'.format(out_dir), None

            # get the event file name
            if event_file_name is None:
                raw_event_file = self._reductionSetup.get_event_file()
            else:
                assert isinstance(event_file_name, str), 'User specified event file name {0} must be a string,' \
                                                         ' but not a {1}.'.format(event_file_name,
                                                                                  type(event_file_name))
                raw_event_file = event_file_name
            # END-IF

            mantidsimple.SNSPowderReduction(Filename=raw_event_file,
                                            PreserveEvents=True,
                                            # CalibrationFile=CalibrationFileName,
                                            CalibrationFile=self._reductionSetup.get_focus_file(),
                                            CharacterizationRunsFile=self._reductionSetup.get_characterization_file(),
                                            Binning="-0.001",
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
            print '[Error] Unable to reduce workspace %s due to %s.' % (self._dataWorkspaceName, str(run_err))
            return False, str(run_err), None
        except AssertionError as ass_err:
            return False, str(ass_err), None

        # convert unit and save for VULCAN-specific GSAS. There is not d-spacing left now
        mantidsimple.ConvertUnits(InputWorkspace=reduced_ws_name,
                                  OutputWorkspace=reduced_ws_name,
                                  Target="TOF",
                                  EMode="Elastic",
                                  AlignBins=False)

        vdrive_bin_ws_name = '{0}_V2Bank'.format(reduced_ws_name)

        # get the output workspace
        output_access_error = False
        orig_gsas_name = gsas_file_name
        if os.path.exists(gsas_file_name) and os.access(gsas_file_name, os.W_OK) is False:
            # gsas file does exist and cannot be modified: write to a temporary account
            gsas_file_name = os.path.join('/tmp/', os.path.basename(gsas_file_name))
            output_access_error = True
        elif not os.path.exists(gsas_file_name) and os.access(os.path.dirname(gsas_file_name), os.W_OK) is False:
            # gsas file does not exist and use has no write permit to directory: write to a temporary account
            gsas_file_name = os.path.join('/tmp/', os.path.basename(gsas_file_name))
            output_access_error = True

        # check whether the file is writable
        gsas_dir = os.path.dirname(gsas_file_name)
        if os.access(gsas_dir, os.W_OK) is False:
            raise RuntimeError('Unable to write GSAS file {0} as user has no write permission to directory {1}.'
                               ''.format(gsas_file_name, gsas_dir))

        # save to Vuclan GSAS
        try:
            mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_ws_name,
                                       BinFilename=self._reductionSetup.get_vulcan_bin_file(),
                                       OutputWorkspace=vdrive_bin_ws_name,
                                       GSSFilename=gsas_file_name,
                                       IPTS=self._reductionSetup.get_ipts_number(),
                                       GSSParmFilename="Vulcan.prm")
        except ValueError as value_err:
            # write again to a temporary directory
            print '[ValueError]: {0}.'.format(value_err)
            gsas_file_name = os.path.join('/tmp/', os.path.basename(gsas_file_name))
            output_access_error = True
            mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_ws_name,
                                       BinFilename=self._reductionSetup.get_vulcan_bin_file(),
                                       OutputWorkspace=vdrive_bin_ws_name,
                                       GSSFilename=gsas_file_name,
                                       IPTS=self._reductionSetup.get_ipts_number(),
                                       GSSParmFilename="Vulcan.prm")

        # set up the output file's permit for other users to modify
        os.chmod(gsas_file_name, 0774)

        # Add special property to output workspace
        final_ws = AnalysisDataService.retrieve(vdrive_bin_ws_name)
        final_ws.getRun().addProperty('VDriveBin', True, replace=True)

        self._reductionSetup.set_reduced_workspace(vdrive_bin_ws_name)
        self._reducedDataFiles.append(gsas_file_name)

        if self._reductionSetup.normalized_by_vanadium:
            gsas_name2 = os.path.splitext(orig_gsas_name)[0] + '_v.gda'
            self._normalize_by_vanadium(vdrive_bin_ws_name, gsas_name2)
        # END-IF (vanadium)

        # collect result
        self._reducedWorkspaceDSpace = None  # dSpacing reduced workspace has been replaced by TOF
        self._reducedWorkspaceMtd = reduced_ws_name
        self._reducedWorkspaceVDrive = vdrive_bin_ws_name
        self._reduceGood = True

        # return with False
        if output_access_error:
            return False, 'Code001: Unable to write GSAS file to {0}. Write to {1} instead.' \
                          ''.format(orig_gsas_name, gsas_file_name), None

        return True, message, reduced_ws_name

    def _normalize_by_vanadium(self, reduced_gss_ws_name, output_file_name):
        """

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

        check_result, message = check_point_data_log_binning(van_ws_name, standard_bin_size=0.01, tolerance=1.E-5)
        if not check_result:
            print '[INFO] ', message

        align_bins(van_ws_name, reduced_gss_ws_name)

        print '[INFO] ', reduced_gss_ws_name, reduced_gss_ws.run().getProperty('VDriveBin')

        # # check whether the reduced GSAS workspace has the same binning with vanadium workspace
        # gda_vec_x = reduced_gss_ws.readX(0)
        # van_vec_x = van_ws.readX(0)
        # diff_vec = numpy.abs((van_vec_x - gda_vec_x) / gda_vec_x)
        # if numpy.max(diff_vec) >= 0.01:
        #     raise RuntimeError('Binning between vanadium run {0} and reduced run {1} '
        #                        'differs too much!'.format(van_run_number, reduced_gss_ws_name))
        #
        # # check whether vanadium and sample run workspace have the same number of spectra
        # num_spec = reduced_gss_ws.getNumberHistograms()
        # if num_spec != van_ws.getNumberHistograms():
        #     raise RuntimeError('Number of reduced workspace {0}\'s histogram {1} does not equal to that of vanadium '
        #                        '{2} as {3}.'.format(reduced_gss_ws_name, num_spec, van_ws_name,
        #                                             van_ws.getNumberHistograms()))
        #
        # # normalize by vanadium
        # # make the binning exactly the same because there is always some tiny difference between loaded GSAS
        # for ws_index in range(num_spec):
        #     numpy.copyto(van_ws.dataX(ws_index), reduced_gss_ws.readX(ws_index))

        # normalize and write out again
        reduced_gss_ws = reduced_gss_ws / van_ws

        mantidsimple.SaveVulcanGSS(InputWorkspace=reduced_gss_ws,
                                   OutputWorkspace=reduced_gss_ws_name,
                                   GSSFilename=output_file_name,
                                   IPTS=self._reductionSetup.get_ipts_number(),
                                   GSSParmFilename="Vulcan.prm")

        return

    def special_operation_auto_reduction_service(self):
        """
        some special operations used in auto reduction service only
        :return:
        """
        if not self._reductionSetup.is_auto_reduction_service:
            return True, 'No operation for auto reduction special.'

        # 2nd copy for Ke if it IS NOT an alignment run
        if not self._reductionSetup.is_alignment_run and self._reductionSetup.get_gsas_2nd_dir():
            self.duplicate_gsas_file(self._reductionSetup.get_gsas_file(main_gsas=True),
                                     self._reductionSetup.get_gsas_2nd_dir())

        # save the plot
        self.generate_1d_plot()

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
        Print help message
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
        reducer.dry_run()

    # execute
    status, error_message = reduction_setup.check_validity()
    if status and not reduction_setup.is_dry_run():
        # reduce data
        reducer.execute_vulcan_reduction()
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
