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


# sys.path.append("/opt/mantidnightly/bin")
# sys.path.append('/opt/mantidunstable/bin/')
# sys.path.append("/opt/Mantid/bin")
# sys.path.append('/home/wzz/Mantid/Code/debug/bin/')
# sys.path.append('/Users/wzz/Mantid/Code/debug/bin')

import mantid.simpleapi as mantidsimple
import mantid

refLogTofFilename = "/SNS/VULCAN/shared/autoreduce/vdrive_log_bin.dat"
calibrationfilename = "/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal"
characterfilename = "/SNS/VULCAN/shared/autoreduce/VULCAN_Characterization_2Banks_v2.txt"

TIMEZONE1 = 'America/New_York'
TIMEZONE2 = 'UTC'

# record file header list: list of 3-tuples
RecordBase = [
    ("RUN",             "run_number", None),
    ("IPTS",            "experiment_identifier", None),
    ("Title",           "run_title", None),
    ("Notes",           "file_notes", None),
    ("Sample",          "Sample", None),  # stored on sample object
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

        self._mode = None
        self.dryRun = False

        self._eventFileFullPath = None

        self._outputDirectory = None

        self._mainRecordFileName = None
        self._2ndRecordFileName = None

        self._mainGSASFileName = None
        self._2ndGSASFileName = None

        self._sampleLogDirectory = None

        self._pngFileName = None

        return

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
        return self._mainGSASFileName

    def get_gsas_2nd_dir(self):
        """
        get secondary GSAS file name
        :return:
        """
        return self._2ndGSASFileName

    def get_ipts_number(self):
        """
        get IPTS number
        :return:
        """
        return self._iptsNumber

    def get_mode(self):
        """
        get mode
        :return:
        """
        return self._mode

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

    def get_run_number(self):
        """
        get run number
        :return:
        """
        if self._runNumber is None:
            raise RuntimeError('Run number is not set yet.')

        return self._runNumber

    def get_vdrive_log_dir(self):
        """
        Get the directory for vdrive log files
        :return:
        """
        return self._sampleLogDirectory

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

    def set_ipts_number(self, ipts):
        """
        set IPTS number
        :param ipts:
        :return:
        """
        assert isinstance(ipts, int) and ipts >= 0

        self._iptsNumber = ipts

        return

    def set_mode(self, mode):
        """
        set reduction mode
        :param mode:
        :return:
        """
        self._mode = mode

    def set_output_dir(self, dir_path):
        """
        set output directory
        :param dir_path:
        :return:
        """
        # check input's validity
        assert isinstance(dir_path, str), 'Output directory must be a string but not %s.' % type(dir_path)

        # check whether the directory is writable
        if not os.access(dir_path, os.W_OK):
            raise RuntimeError('Output data direcotry %s is not writable.' % dir_path)

        else:
            self._outputDirectory = dir_path

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


class PatchRecord:
    """ A class whose task is to make patch to Record.txt generated from
    Mantid.simpleapi.ExportExperimentLog(), which may not be able to retrieve
    all information from NeXus file.

    This class will not be used after all the required information/logs are
    added to NeXus file or exported to Mantid workspace
    """
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

    def exportPatch(self):
        """ Export patch as a list of strings
        """
        cvdict = self._readCvInfoFile()
        rundict = self._readRunInfoFile()

        patchdict = {}
        for title in cvdict.keys():
            patchdict[title] = cvdict[title]

        for title in rundict.keys():
            patchdict[title] = rundict[title]

        patchlist = []
        for key in patchdict:
            patchlist.append(str(key))
            patchlist.append(str(patchdict[key]))

        return patchlist

    def patchRecord(self, recordfilename):
        """ Patch record, including ITPS, ...
        """
        raise NotImplementedError("Invalid!")

        # # Get last line
        # titleline, lastline = self.get_last_line_in_binary_file(recordfilename)

        # # print "First line: ", titleline
        # # print "Last line: ", lastline

        # # Parse last line and first line
        # rtitles = titleline.split("\t")
        # titles = []
        # for title in rtitles:
        #     title = title.strip()
        #     titles.append(title)

        # values = lastline.split("\t")

        # valuedict = {}
        # if len(titles) != len(values):
        #     raise NotImplementedError("Number of tiles are different than number of values.")
        # for itit in xrange(len(titles)):
        #     valuedict[titles[itit]] = values[itit]

        # # Substitute
        # ipts = self._getIPTS()
        # cvdict = self._readCvInfoFile()
        # rundict = self._readRunInfoFile()

        # valuedict["IPTS"] = "%s" % (str(ipts))
        # for title in cvdict.keys():
        #     valuedict[title] = cvdict[title]

        # # print valuedict.keys()

        # for title in rundict.keys():
        #     valuedict[title] = rundict[title]

        # # Form the line again: with 7 spaces in front
        # newline = "       "
        # for i in xrange(len(titles)):
        #     title = titles[i]
        #     if i > 0:
        #         newline += "\t"
        #     newline += "%s" % (str(valuedict[title]))

        # # Remove last line and append the patched line
        # self.remove_last_line_in_text(recordfilename)

        # with open(recordfilename, "a") as myfile:
        #     myfile.write("\n"+newline)

        # return

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
        if attribdict.has_key(name):
            cvinfodict["TotalCounts"] = attribdict[name]

        name = "das.protoncharge"
        if attribdict.has_key(name):
            cvinfodict["ProtonCharge"] = attribdict[name]

        name = "das.runtime"
        if attribdict.has_key(name):
            cvinfodict["Duration(sec)"] = attribdict[name]

        name = "das.monitor2counts"
        if attribdict.has_key(name):
            cvinfodict["Monitor1"] = attribdict[name]

        name = "das.monitor3counts"
        if attribdict.has_key(name):
            cvinfodict["Monitor2"] = attribdict[name]

        return cvinfodict

    def _readRunInfoFile(self):
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

# ENDCLASS


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

        self._reductionSetup = ReductionSetup()

        return

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
        assert isinstance(original_directory, str)

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

    @staticmethod
    def dry_run(reduction_setup):
        """
        Dry run to verify the output
        :param reduction_setup:
        :return:
        """
        # check
        assert isinstance(reduction_setup, ReductionSetup), 'Input type is wrong!'

        dry_run_str = ''

        # Output result in case it is a dry-run
        dry_run_str += "Input NeXus file    : %s\n" % reduction_setup.get_event_file()
        dry_run_str += "Output directory    : %s\n" % reduction_setup.get_reduced_data_dir()
        dry_run_str += "Log directory       : %s\n" % reduction_setup.get_vdrive_log_dir()  # logDir
        dry_run_str += "GSAS  directory     : %s;  If it is None, no GSAS will be written." \
                       "\n" % str(reduction_setup.get_gsas_dir())
        if reduction_setup.get_gsas_dir() is not None:
            dry_run_str += "GSAS2 directory     : %s\n" % str(reduction_setup.get_gsas_2nd_dir())
        dry_run_str += "Record file name    : %s\n" % str(reduction_setup.get_record_file())
        dry_run_str += "Record(2) file name : %s\n" % str(reduction_setup.get_record_2nd_file())
        dry_run_str += "1D plot file name   : %s\n" % reduction_setup.get_plot_file()

        print 'Dry run:\n%s' % dry_run_str

        return False

    def exportGenericDAQLog(self, log_ws_name, outputDir, ipts, run_number):
        """
        Export the generic DAQ log
        :param log_ws_name:
        :param outputDir:
        :param ipts:
        :param run_number:
        :return:
        """
        # organized by dictionary
        if run_number >= 69214:
            for ilog in xrange(1, 17):
                Generic_DAQ_List.append(("tc.user%d" % (ilog), "tc.user%d" % (ilog)))

        # Format to lists for input
        samplelognames = []
        header = []
        for i in xrange(len(Generic_DAQ_List)):
            title = Generic_DAQ_List[i][0]
            log_name = Generic_DAQ_List[i][1]

            header.append(title)
            if len(log_name) > 0:
                samplelognames.append(log_name)

        headstr = ""
        for title in header:
            headstr += "%s\t" % (title)

        # make a new file name
        is_new_file_name = False
        max_attempts = 100
        num_attempts = 0
        output_file_name = ''
        while is_new_file_name is False and num_attempts < max_attempts:
            if num_attempts == 0:
                output_file_name = "IPTS-%d-GenericDAQ-%d.txt" % (ipts, run_number)
            else:
                output_file_name = "IPTS-%d-GenericDAQ-%d_%d.txt" % (ipts, run_number, num_attempts)
            output_file_name = os.path.join(outputDir, output_file_name)

            if os.path.isfile(output_file_name) is False:
                is_new_file_name = True
            else:
                num_attempts += 1
        # ENDWHILE
        assert len(output_file_name) > 0

        # Raise exception
        if is_new_file_name is False:
            raise NotImplementedError("Unable to find an unused log file name for run %d. " % (run_number))
        else:
            print "Log file will be written to %s. " % output_file_name
        # TODO/NOW - better to rename the existing GenericDAQ file

        # Export
        try:
            ExportSampleLogsToCSVFile(InputWorkspace=log_ws_name,
                                      OutputFilename=output_file_name,
                                      SampleLogNames=samplelognames,
                                      WriteHeaderFile=True,
                                      TimeZone=TIMEZONE2,
                                      Header=headstr)
        except RuntimeError:
            print "Error in exporting Generic DAQ log for run %s. " % (str(run_number))

        return

    def exportVulcanSampleEnvLog(self, log_ws_name, output_dir, ipts, run_number):
        """ Export Vulcan sample environment log
        Requirements
        Guarantees: export the file name as 'Vulcan-IPTS-XXXX-SEnv-RRRR.txt'
        """
        # Check inputs
        assert isinstance(ipts, int)
        assert isinstance(run_number, int)

        # Create list of the sample logs to be exported.
        # each element is a 2-tuple of string as (log name in output log file, log name in workspace)


        # Generate title/header list and log name list from
        sample_log_name_list = []
        header_title_list = []
        for i in xrange(len(VulcanSampleLogList)):
            title = VulcanSampleLogList[i][0].strip()
            log_name = VulcanSampleLogList[i][1].strip()

            header_title_list.append(title)
            if len(log_name) > 0:
                sample_log_name_list.append(log_name)
        # END-FOR

        # For header string frrom list
        header_str = ''
        for title in header_title_list:
            header_str += "%s\t" % title

        # Make a new name in case an old one exists. Try max 10 times
        is_new_file_name = False
        max_attempts = 10
        num_attempt = 0
        output_file_name = None
        while is_new_file_name is False and num_attempt < max_attempts:
            # create file name
            if num_attempt == 0:
                output_file_name = 'Vulcan-IPTS-%d-SEnv-%d.txt' % (ipts, run_number)
            else:
                output_file_name = 'Vulcan-IPTS-%d-SEnv-%d-%d.txt' % (ipts, run_number, num_attempt)
            output_file_name = os.path.join(output_dir, output_file_name)

            # check whether it is a new file such that no old file will be overwritten
            is_new_file_name = not os.path.exists(output_file_name)
            num_attempt += 1
        # END-WHILE
        assert output_file_name is not None
        assert is_new_file_name, 'Unable to find an unused log file name for run %d.' % run_number
        print 'Log file will be written to %s.' % output_file_name

        # Export sample logs
        ExportSampleLogsToCSVFile(InputWorkspace=log_ws_name,
                                  OutputFilename=output_file_name,
                                  SampleLogNames=sample_log_name_list,
                                  WriteHeaderFile=True,
                                  SeparateHeaderFile=False,
                                  DateTitleInHeader=False,
                                  TimeZone=TIMEZONE2,
                                  Header=header_str)

        return

    def generate_record_file_format(self):
        """
        """
        sampletitles = []
        samplenames = []
        sampleoperations = []
        for ib in xrange(len(RecordBase)):
            sampletitles.append(RecordBase[ib][0])
            samplenames.append(RecordBase[ib][1])
            sampleoperations.append(RecordBase[ib][2])

        return sampletitles, samplenames, sampleoperations

    def export_experiment_records(self, log_ws_name, instrument, ipts, run, auto_reduction_record_file_name,
                                  logs_record_file_name, export_mode):
        """ Write the summarized sample logs of this run number to the record files
        :param log_ws_name:
        :param instrument:
        :param ipts:
        :param run:
        :param auto_reduction_record_file_name:
        :param logs_record_file_name
        :param export_mode: sample log exporting mode
        :return: True if it is an alignment run
        """
        # Convert the record base to input arrays
        sample_title_list, sample_name_list, sample_operation_list = self.generate_record_file_format()

        # Patch for logs that do not exist in event NeXus yet
        patcher = PatchRecord(instrument, ipts, run)
        patch_list = patcher.exportPatch()

        # Auto reduction and manual reduction
        if os.path.exists(logs_record_file_name) is True:
            # Determine mode: append is safer, as the list of titles changes, the old record
            # will be written to the a new file.
            filemode = "append"
        else:
            # New a file
            filemode = "new"

        # Export to auto record
        ExportExperimentLog(InputWorkspace=log_ws_name,
                            OutputFilename=logs_record_file_name,
                            FileMode=filemode,
                            SampleLogNames=sample_name_list,
                            SampleLogTitles=sample_title_list,
                            SampleLogOperation=sample_operation_list,
                            TimeZone="America/New_York",
                            OverrideLogValue=patch_list,
                            OrderByTitle='RUN',
                            RemoveDuplicateRecord=True)

        # Set up the mode for global access
        file_access_mode = oct(os.stat(logs_record_file_name)[stat.ST_MODE])
        file_access_mode = file_access_mode[-3:]
        if file_access_mode != '666' and file_access_mode != '676':
            print "Current file %s's mode is %s." % (logs_record_file_name, file_access_mode)
            os.chmod(logs_record_file_name, 0666)

        # Export to either data or align
        try:
            log_ws = mantid.AnalysisDataService.retrieve(log_ws_name)
            title = log_ws.getTitle()
            record_file_path = os.path.dirname(logs_record_file_name)
            if title.startswith('Align:'):
                categorized_record_file = os.path.join(record_file_path, 'AutoRecordAlign.txt')
                is_alignment_run = True
            else:
                categorized_record_file = os.path.join(record_file_path, 'AutoRecordData.txt')
                is_alignment_run = False

            if os.path.exists(categorized_record_file) is False:
                filemode2 = 'new'
            else:
                filemode2 = 'append'
            ExportExperimentLog(InputWorkspace=log_ws_name,
                                OutputFilename=categorized_record_file,
                                FileMode=filemode2,
                                SampleLogNames=sample_name_list,
                                SampleLogTitles=sample_title_list,
                                SampleLogOperation=sample_operation_list,
                                TimeZone="America/New_York",
                                OverrideLogValue=patch_list,
                                OrderByTitle='RUN',
                                RemoveDuplicateRecord=True)

            # Change file  mode
            if file_access_mode != '666' and file_access_mode != '676':
                os.chmod(categorized_record_file, 0666)
        except NameError as e:
            print '[Error] %s.' % str(e)

        # Auto reduction only
        if export_mode == "auto":
            # Check if it is necessary to copy AutoRecord.txt from rfilename2 to rfilename1
            if os.path.exists(auto_reduction_record_file_name) is False:
                # File do not exist, the copy
                shutil.copy(logs_record_file_name, auto_reduction_record_file_name)
            else:
                # Export the log by appending
                ExportExperimentLog(InputWorkspace=log_ws_name,
                                    OutputFilename=auto_reduction_record_file_name,
                                    FileMode=filemode,
                                    SampleLogNames=sample_name_list,
                                    SampleLogTitles=sample_title_list,
                                    SampleLogOperation=sample_operation_list,
                                    TimeZone=TIMEZONE1,
                                    OverrideLogValue=patch_list,
                                    OrderByTitle='RUN',
                                    RemoveDuplicateRecord=True)

        return is_alignment_run

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


    @staticmethod
    def exportFurnaceLog(log_ws_name, output_directory, run_number):
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

        # Make a new name
        is_new_file = False
        max_attempts = 10
        out_file_name = ''

        # find out whether the furnace file is a new file or an old one.
        num_attempts = 0
        while is_new_file is False and num_attempts < max_attempts:
            if num_attempts == 0:
                out_file_name = os.path.join(output_directory, "furnace%d.txt" % (run_number))
            else:
                out_file_name = os.path.join(output_directory, "furnace%d_%d.txt" % (run_number, num_attempts))

            if os.path.isfile(out_file_name) is False:
                is_new_file = True
            else:
                num_attempts += 1
        # END- WHILE

        # Raise exception
        if is_new_file is False:
            raise NotImplementedError("Unable to find an unused log file name for run %d. " % (run_number))
        else:
            print "Log file will be written to %s. " % out_file_name

        try:
            ExportSampleLogsToCSVFile(InputWorkspace=log_ws_name,
                                      OutputFilename=out_file_name,
                                      SampleLogNames=["furnace.temp1", "furnace.temp2", "furnace.power"],
                                      TimeZone=TIMEZONE2)
        except RuntimeError as run_err:
            raise RuntimeError('Unable to export sample log to %s due to %s.' % (out_file_name, str(run_err)))

        return


    def exportMTSLog(self, logwsname, outputDir, ipts, run_number):
        """ Export MTS log
        List of MTS Log:
            X       Y       Z       O       HROT     VROT
            MTSDisplacement MTSForce        MTSStrain       MTSStress      MTSAngle
            MTSTorque       MTSLaser        MTSlaserstrain  MTSDisplaceoffset       MTSAngleceoffset
            MTST1   MTST2   MTST3   MTST4   FurnaceT
            FurnaceOT       FurnacePower    VacT    VacOT
        """
        # Format to lists for input
        samplelognames = []
        header = []
        for i in xrange(len(MTS_Header_List)):
            title = MTS_Header_List[i][0]
            log_name = MTS_Header_List[i][1]

            header.append(title)
            if len(log_name) > 0:
                samplelognames.append(log_name)

        headstr = ""
        for title in header:
            headstr += "%s\t" % (title)

        # Make a new name
        self.generate_csv_log(blba)

        return

    def generate_csv_log(self, log_ws_name, log_file_base_name, log_file_posfix, output_dir, sample_log_names, header):
        """

        :param log_ws_name:
        :param log_file_base_name:
        :param log_file_posfix:
        :param output_dir
        :param sample_log_names:
        :return:
        """
        # Make a new name by avoiding deleting the existing one.
        is_new_file = False
        max_attempts = 10
        log_file_name = ''

        num_attempts = 0
        while is_new_file is False and num_attempts < max_attempts:
            if num_attempts == 0:
                log_file_name = '%s.%s' % (log_file_base_name, log_file_posfix)
            else:
                log_file_name = "'%s_%d.%s" % (log_file_name, num_attempts, log_file_posfix)
            log_file_name = os.path.join(output_dir, log_file_name)
            if os.path.isfile(log_file_name) is False:
                is_new_file = True
            else:
                num_attempts += 1
        # ENDWHILE
        assert len(log_file_name) > 0

        # Raise exception
        if is_new_file is False:
            raise RuntimeError("Unable to find an unused log file name %s. " % log_file_base_name)

        ExportSampleLogsToCSVFile(
            InputWorkspace=log_ws_name,
            OutputFilename=log_file_name,
            SampleLogNames=sample_log_names,
            WriteHeaderFile=True,
            TimeZone=TIMEZONE2,
            Header=header)

        return log_file_name

    def load_data_file(self, reduce_to_gsas):
        """
        Load NeXus file. If reducing to GSAS is also required, then load the complete NeXus file. Otherwise,
        load the sample log only
        :param reduce_to_gsas:
        :return:
        """
        if reduce_to_gsas:
            ws_name = 'VULCAN_%d_event' % self._reductionSetup.get_run_number()
        else:
            ws_name = "VULCAN_%d_MetaDataOnly" % (self._reductionSetup.get_run_number())
        try:
            mantidsimple.Load(Filename=self._reductionSetup.get_event_file(),
                              OutputWorkspace=ws_name,
                              MetaDataOnly=not reduce_to_gsas,
                              LoadLogs=True)
        except RuntimeError as err:
            raise RuntimeError('Unable to load NeXus file %s due to %s. ' % (self._reductionSetup.get_event_file(),
                                                                             str(err)))

        return

    def generate_experiment_records(self):
        """

        :return:
        """
        # check condition
        if self._reductionSetup.get_record_file() is None and self._reductionSetup.get_record_2nd_file() is None:
            return

        if self._reductionSetup.logDir is None and self._reductionSetup.recordFileName is None and self._reductionSetup.record2FileName is None:
            return



        # export sample log file for this run
        if logDir is not None:
            # Export furnace log
            exportFurnaceLog(meta_ws_name, logDir, runNumber)

            # Export Generic DAQ log
            exportGenericDAQLog(meta_ws_name, logDir, ipts, runNumber)

            # Export load frame /MTS log
            exportMTSLog(meta_ws_name, logDir, ipts, runNumber)

            # Export standard VULCAN sample environment data
            exportVulcanSampleEnvLog(meta_ws_name, logDir, ipts, runNumber)
        # ENDIF

        # export sample log summary to this IPTS
        if recordFileName is not None or record2FileName is not None:
            # Append auto record file
            instrument = "VULCAN"
            is_alignment_run = export_experiment_records(meta_ws_name, instrument, ipts, runNumber, recordFileName,
                                                         record2FileName, mode)
            # ENDIF

    def execute(self):
        """

        :return:
        """
        # load the sample run


        # export the sample log record file
        if self._reductionSetup.get_record_file() is not None or self._reductionSetup.get_record_2nd_file() is not None:
            self.export_experiment_records()

        # write experiment files
        if required:
            self.exportFurnaceLog()
            self.exportMTSLog()
            self.exportVulcanSampleEnvLog()
            self.exportGenericDAQLog()

        # write GSAS
        if self._reductionSetup.get_gsas_dir() is not None:
            gsas_file_name = self.reduce_powder_diffraction_data(self._reductionSetup.ipts, self._reductionSetup.runNumber, self._reductionSetup.gsasDir)

            # 2nd copy for Ke if it IS NOT an alignment run
            if self._reductionSetup.is_alignment_run() is False:
                self.duplicate_gsas_file(gsas_file_name, self._reductionSetup.get_gsas_2nd_dir())

            # save the plot
            self.export_1d_plot()
        # END-IF

        return

    def export_1d_plot(self):
        """
        Export 1-D plot of the reduced powder pattern
        :return:
        """
        try:
            mantidsimple.SavePlot1D(InputWorkspace="Proto2Bank", OutputFilename=self._reductionSetup.get_plot_file(),
                                    YLabel='Intensity')
        except ValueError as err:
            print "Unable to generate 1D plot for run %s caused by %s. " % (str(self._reductionSetup.get_run_number()),
                                                                            str(err))
        except RuntimeError as err:
            print "Unable to generate 1D plot for run %s caused by %s. " % (str(self._reductionSetup.get_run_number()),
                                                                            str(err))
        # Try-Exception

        return

    def reduce_powder_diffraction_data(ipts, runnumber, outputdir):
        """ Save for Nexus file
        """
        import os

        outfilename = os.path.join(outputdir, "%s.gda" % (str(runnumber)))
        if os.path.isfile(outfilename) is True:
            print "GSAS file (%s) has been reduced for run %s already. " % (outfilename, str(runnumber))
            return outfilename

        SNSPowderReduction(Filename='VULCAN_%s' % runnumber,
                       #Instrument='VULCAN',
                       #Extension="_event.nxs",
                       PreserveEvents=True,
                       CalibrationFile=calibrationfilename,
                       CharacterizationRunsFile=characterfilename,
                       Binning="-0.001",
                       SaveAS="",
                       OutputDirectory=outputdir,
                       NormalizeByCurrent=False,
                       FilterBadPulses=0,
                       CompressTOFTolerance=0.,
                       FrequencyLogNames="skf1.speed",
                       WaveLengthLogNames="skf12.lambda")

        # convert unit and save for VULCAN-specific GSAS
        input_ws_name = 'VULCAN_%d' % runnumber
        vulcan_ws_name = "VULCAN_%d_SNSReduc" % runnumber
        ConvertUnits(InputWorkspace=input_ws_name, OutputWorkspace=vulcan_ws_name,
                 Target="TOF", EMode="Elastic", AlignBins=False)

        SaveVulcanGSS(InputWorkspace=vulcan_ws_name, BinFilename=refLogTofFilename,
                  OutputWorkspace="Proto2Bank", GSSFilename=outfilename,
                  IPTS=ipts, GSSParmFilename="Vulcan.prm")

        return outfilename


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


def print_main_help():
    """
    Print help message
    :return:
    """
    # FIXME/TODO/NOW - Make these string!
    print "%s -i <inputfile> -o <outputdirectory> ... ..." % (sys.argv[0])
    print "-i/ifile  : mandatory input NeXus file name. "
    print "-o/ofile  : mandatory directory for output files. "
    print "-l/log    : optional directory for sample log files. "
    print "-g/gsas   : optional directory for GSAS file owned by owner. "
    print "-G/gsas2  : optional directory to copy GSAS file to  with file mode 664."
    print "-r/record : optional experiment record file name (writable only to auot reduction service)."
    print "-R/record2: experiment record file (can be modified by manual reduction)."
    print "-d/dry    : dry run to check output status, file names and directories."

    return


def parse_argv(opts, argv):
    """ Parse arguments and put to dictionary
    :param opts:
    :param argv
    :return: 2-tuple : status (boolean) and ReductionSetup (or None)
    """
    # Initialize
    reduction_setup = ReductionSetup()

    # process input arguments in 2 different modes: auto-reduction and manual reduction (options)
    if len(argv) == 0:
        print "Auto   reduction Inputs:   [1. File name with full length] [2. Output directory]"
        print "Manual reduction Inputs:   --help"
        return False, reduction_setup

    elif len(opts) == 0:
        # auto reduction mode (as default)
        reduction_setup.mode = "auto"

        # set up event file path and output directory
        reduction_setup._eventFileFullPath = argv[0]
        reduction_setup._outputDirectory = argv[1]

        # set up log directory, record files and etc.
        reduction_setup._sampleLogDirectory = change_output_directory(reduction_setup._outputDirectory)

        reduction_setup._mainRecordFileName = os.path.join(reduction_setup._outputDirectory, "AutoRecord.txt")
        reduction_setup.copy2Dir = change_output_directory(reduction_setup._outputDirectory, "")
        reduction_setup._2ndRecordFileName = os.path.join(reduction_setup.copy2Dir, "AutoRecord.txt")

        # output GSAS directory
        reduction_setup._mainGSASFileName = change_output_directory(reduction_setup._outputDirectory, "autoreduce/binned")
        reduction_setup._2ndGSASFileName = change_output_directory(reduction_setup._outputDirectory, "binned_data")

    else:
        # manual reduction mode
        reduction_setup.mode = 'manual'

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                # Help
                print_main_help()
                return False
            elif opt in ("-i", "--ifile"):
                # Input NeXus file
                reduction_setup._eventFileFullPath = arg
            elif opt in ("-o", "--ofile"):
                # Output directory
                reduction_setup._outputDirectory = arg
            elif opt in ("-l", "--log") and arg != '0':
                # Log file
                reduction_setup._sampleLogDirectory = arg
            elif opt in ("-g", "--gsas") and arg != '0':
                # GSAS file
                reduction_setup._mainGSASFileName = arg
            elif opt in ("-G", "--gsas2") and arg != '0':
                # GSAS file of 2nd copy
                reduction_setup._2ndGSASFileName = arg
            elif opt in ("-r", "--record") and arg != '0':
                # AutoReduce.txt
                reduction_setup._mainRecordFileName = arg
            elif opt in ("-R", "--record2") and arg != '0':
                # AutoReduce.txt in 2nd directory as a backup
                reduction_setup._2ndRecordFileName = arg
            elif opt in ("-d", "--dryrun"):
                # Dry run
                reduction_setup.dryRun = True
            # END-IF-ELSE
        # END-FOR (opt)
    # END-IF-ELSE (len(opt)==0)

    # Check requirements
    if reduction_setup.get_event_file() is None or reduction_setup.get_reduced_data_dir() is None:
        print "Both input event Nexus file %s and output directory %s must be given!" % (
            str(reduction_setup.get_event_file()), str(reduction_setup.get_reduced_data_dir()))
        return False, reduction_setup

    return True, reduction_setup


def configure_reduction_setup(reduction_setup):
    """ Obtain information from full path to input NeXus file including
    1. base NeXus file name
    2. directory to NeXus file
    3. IPTS number
    :param reduction_setup:
    :return:
    """
    # check type
    assert isinstance(reduction_setup, ReductionSetup), 'Input object of type %s is not ReductionSetup.' \
                                                        '' % reduction_setup.__class__.__name__

    # Check file's existence
    if os.path.exists(reduction_setup.get_event_file()) is False:
        raise RuntimeError('NeXus file %s is not accessible or does not exist. '
                           '' % reduction_setup.get_event_file())

    # get event file name (base name) and directory for NeXus file
    reduction_setup.eventFile = os.path.split(reduction_setup.get_event_file())[-1]
    reduction_setup.nexusDir = reduction_setup.get_event_file().replace(reduction_setup.eventFile, '')

    # set the data file path in the search list
    data_search_path = mantid.config.getDataSearchDirs()
    data_search_path.append(reduction_setup.nexusDir)
    mantid.config.setDataSearchDirs(";".join(data_search_path))

    # parse the run number and IPTS
    run_number = int(reduction_setup.eventFile.split('_')[1])
    if reduction_setup.get_event_file().count("IPTS") == 1:
        terms = reduction_setup.get_event_file().split("/")
        ipts_str = ''
        for t in terms:
            if t.count("IPTS") == 1:
                ipts_str = t
                break
        assert len(ipts_str) > 0, 'Impossible that IPTS string does not exist!'
        ipts = int(ipts_str.split("-")[1])
    else:
        ipts = 0
    reduction_setup.set_run_number(run_number)
    reduction_setup.set_ipts_number(ipts)

    # 1D plot file name
    plot_image_file_name = os.path.join(reduction_setup.get_reduced_data_dir(), 'VULCAN_' + str(run_number) + '.png')
    reduction_setup.set_plot_file_name(plot_image_file_name)

    return reduction_setup


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
    status, ret_tuple = process_inputs(argv)
    if not status:
        return
    else:
        opts, args = ret_tuple

    # parse arguments
    print '[DB...BAT] args = ', args, type(args), 'argv = ', argv, type(argv)

    status, reduction_setup = parse_argv(opts, argv)
    if not status:
        return
    # process
    reduction_setup = configure_reduction_setup(reduction_setup)

    # create reducer
    reducer = ReduceVulcanData(reduction_setup)

    # execute
    if reduction_setup.dryRun:
        # dry run
        reducer.dry_run(reduction_setup)
    else:
        # real reduction
        reducer.execute()

    return


# Command line
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        input_args = []
    else:
        input_args = sys.argv[1:]
    main(input_args)
