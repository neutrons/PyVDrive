# Set up path to PyVDrive
import os
import pyvdrive.lib.VDriveAPI as VdriveAPI
from pyvdrive.lib import datatypeutility
from pyvdrive.lib import file_utilities
try:
    from PyQt5.QtCore import QObject
except (ImportError, RuntimeError) as import_err:
    print('Process_VCommand: {}'.format(import_err))
    from PyQt4.QtCore import QObject


def convert_string_to(string, datatype):
    """
    convert a string to ...
    :param string:
    :param datatype:
    :return:
    """
    try:
        value = datatype(string)
    except ValueError as value_err:
        raise RuntimeError('Unable to parse string "{}" to a {} due to {}'.format(string, datatype, value_err))
    except TypeError as type_err:
        raise RuntimeError('Unable to convert a string {} due to {}'.format(string, type_err))

    return value


class CommandKeyError(Exception):
    """
    Self-defined VDRIVE command key error
    """
    def __init__(self, error):
        """
        Base class for VDRIVE command processors
        """
        super(CommandKeyError, self).__init__(error)

        return


class VDriveCommand(QObject):
    """
    Base class to process VDRIVE commands
    """
    SupportedArgs = list()
    ArgsDocDict = dict()

    def __init__(self, controller, command_args):
        """
        Initialization
        :param controller: VDrive controller class
        :param command_args:
        """
        # call base init
        super(VDriveCommand, self).__init__(None)

        # check input
        assert isinstance(controller, VdriveAPI.VDriveAPI), 'Controller must be a VdriveAPI.VDriveAPI' \
                                                            'instance but not %s.' % controller.__class__.__name__
        datatypeutility.check_dict('VDrive command arguments', command_args)

        # my name
        self._commandName = 'VDRIVE (base)'

        # set controller
        self._controller = controller

        # set arguments to command arguments dictionary: it is only set once here
        # and they must be capital
        self._commandArgsDict = {command: command_args[command] for command in command_args}

        # create a dictionary to compare the capital command arguments with VDrive argument
        self._commandMapDict = {command.upper(): command for command in self.SupportedArgs}

        # other command variables
        self._iptsNumber = None   # IPTS
        self._runNumberList = list()   # RUN numbers
        # alternative
        self._raw_nexus_file_name = None

        return

    def check_command_arguments(self, supported_arg_list):
        """ Check whether the command arguments are valid
        """
        upper_args = [arg.upper() for arg in supported_arg_list]

        # check whether the any non-supported args
        input_args = self._commandArgsDict.keys()
        for arg_key in input_args:
            if arg_key not in upper_args:
                error_message = 'Command %s\'s argument "%s" is not recognized. Supported ' \
                                'arguments are %s.' % (self._commandName, arg_key, str(supported_arg_list))
                print('[ERROR] {0}'.format(error_message))
                raise CommandKeyError(error_message)
        # END-FOF

        return

    def process_binning_setup(self):
        """ Processing diffraction focus and save to GSAS related setup
        :return: bool (bin chopped data), int (number of banks)
        """
        if 'BIN' in self._commandArgsDict:
            bin_run = convert_string_to(self._commandArgsDict['BIN'], int) > 0
        else:
            # default is True
            bin_run = True

        if 'FULLPROF' in self._commandArgsDict:
            write_fp = convert_string_to(self._commandArgsDict['FULLPROF'], int) > 0
        else:
            # default is False
            write_fp = False

        # number of banks in output GSAS file
        if 'BANKS' in self._commandArgsDict:
            num_banks = convert_string_to(self._commandArgsDict['BANKS'], int)
            if num_banks <= 0:
                raise RuntimeError('Banks number cannot be zero or less')
        else:
            # default is 3
            num_banks = 3

        return bin_run, num_banks, write_fp

    def exec_cmd(self):
        """ Execute VDRIVE command
        """
        raise NotImplementedError('Method exec_cmd must be override')

    @staticmethod
    def get_help():
        """
        Get help message
        :return:
        """
        return 'Invalid to call base class'

    def get_ipts_runs(self):
        """
        retrieve IPTS number and run numbers from the command
        :return: 2-tuple: (1) integer for IPTS (2) list of integers for run numbers
        """
        return self._iptsNumber, self._runNumberList[:]

    def get_argument_as_list(self, arg_name, data_type):
        """ The argument is pre-processed such that ',' is replaced by '~', which is rarely used in any case
        :param arg_name:
        :param data_type:
        :return:
        """
        datatypeutility.check_string_variable('{} argument'.format(self._commandName), arg_name)
        arg_input_value = self._commandArgsDict[arg_name]

        arg_values = arg_input_value.split('~')
        return_list = list()

        for value in arg_values:
            # string value: remove space at two ends
            value = value.strip()
            # convert value
            value = data_type(value)
            # append
            return_list.append(value)

        return return_list

    def parse_binning(self):
        """
        process binning parameters configuration from inputs
        :return: 2-tuple: (1) flag whether binning parameter is default
                          (2) 3-tuple as TOF min, bin width, TOF max
        """
        # check input
        if 'BINW' in self._commandArgsDict:
            user_bin_width = float(self._commandArgsDict['BINW'])
        else:
            user_bin_width = None

        if 'MYTOFMIN' in self._commandArgsDict:
            user_tof_min = float(self._commandArgsDict['MYTOFMIN'])
        else:
            user_tof_min = None

        if 'MYTOFMAX'.upper() in self._commandArgsDict:
            user_tof_max = float(self._commandArgsDict['MYTOFMAX'])
        else:
            user_tof_max = None

        # get default setup
        if user_tof_min is None and user_tof_max is None and user_bin_width is None:
            # none of the 3 parameters is given. use default binning
            use_default_binning = True
            binning_parameters = None

        elif user_tof_min is None or user_tof_max is None or user_bin_width is None:
            # they must be defined all
            raise RuntimeError('User must specify MyTOFMin, MyTOFMax and BINW altogether.')

        else:
            # parse by set up the default value
            use_default_binning = False

            # if user_bin_width is None:
            #     user_bin_width = 0.001   # set to default in case only TOF range is customized value
            # if user_tof_min is None:
            #     user_tof_min = 5000.
            # if user_tof_max is None:
            #     user_tof_max = 70000.

            binning_parameters = (user_tof_min, user_bin_width, user_tof_max)
        # END-IF-ELSE

        return use_default_binning, binning_parameters

    def parse_run_numbers(self):
        """
        parse run numbers from RUNS and RUNE, or RUNLIST or RUNFILE
        :return:
        """
        # initialize variables
        num_setup = 0
        run_number_list = None

        # RUNFILE
        if 'RUNFILE' in self._commandArgsDict:
            run_file = self._commandArgsDict['RUNFILE']
            run_number_list = file_utilities.read_merge_run_file(run_file)
            num_setup += 1

        # RUNLIST
        if 'RUNLIST' in self._commandArgsDict:
            run_number_list = file_utilities.convert_to_list(self._commandArgsDict['RUNLIST'], sep='&',
                                                             element_type=int)
            num_setup += 1

        # RUNS and RUNE
        if 'RUNS' in self._commandArgsDict:
            try:
                start_run_number = int(self._commandArgsDict['RUNS'])
            except (ValueError, TypeError) as convert_err:
                raise RuntimeError('RUNS {} cannot be converted to integer: {}'
                                   '.'.format(self._commandArgsDict['RUNS'], convert_err))

            if 'RUNE' in self._commandArgsDict:
                # parse RUNE
                try:
                    end_run_number = int(self._commandArgsDict['RUNE'])
                except (ValueError, TypeError) as convert_err:
                    raise RuntimeError('RUNE {} cannot be converted to integer: {}'
                                       '.'.format(self._commandArgsDict['RUNE'], convert_err))
                if end_run_number < start_run_number:
                    raise RuntimeError('RUNE {0} is less than RUNS {1}'.format(end_run_number, start_run_number))

            else:
                # default RUNE
                end_run_number = start_run_number
            # END-IF-ELSE

            run_number_list = range(start_run_number, end_run_number + 1)
            num_setup += 1
        # END-IF

        # check
        if num_setup == 0:
            raise RuntimeError('Use must specify one and only in RUNFILE, RUNLIST and RUNS/RUNE.'
                               'Now none of them is specified.')
        elif num_setup > 1:
            raise RuntimeError('Use must specify one and only in RUNFILE, RUNLIST and RUNS/RUNE.'
                               'Now {} of them is specified'.format(num_setup))

        return run_number_list

    def process_tag(self):
        """
        process for 'TAG'
        for example
            TAG='V'  to /SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium
            TAG='Si' to /SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Si

        :return: standard_tuple = material_type, standard_dir, standard_file
        """
        if 'TAG' in self._commandArgsDict:
            # process material type
            material_type = self._commandArgsDict['TAG']
            material_type = material_type.lower()

            if 'TAGDIR' in self._commandArgsDict:
                standard_dir_root = self._commandArgsDict['TAGDIR']
            else:
                standard_dir_root = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard'

            if not os.access(standard_dir_root, os.W_OK):
                # if standard VDRIVE default directory is not writable, then use the local one
                # very likely the current PyVdrive is running in a testing mode.
                raise RuntimeError('User does not have permission to write to {}'.format(standard_dir_root))

            if material_type == 'si':
                material_type = 'Si'
                standard_dir = os.path.join(standard_dir_root, 'Si')
                standard_file = 'SiRecord.txt'
            elif material_type == 'v':
                material_type = 'Vanadium'
                standard_dir = os.path.join(standard_dir_root, 'Vanadium')
                standard_file = 'VRecord.txt'
            elif material_type == 'c':
                material_type = 'C'
                standard_dir = os.path.join(standard_dir_root, 'C')
                standard_file = 'CRecord.txt'
            elif material_type == 'ceo2':
                material_type = 'CeO2'
                standard_dir = os.path.join(standard_dir_root, 'CeO2')
                standard_file = 'CeO2Record.txt'
            elif len(material_type) > 0:
                # create arbitrary tag
                # use the user specified TAG as the type of material
                material_type = self._commandArgsDict['TAG']
                standard_dir = os.path.join(standard_dir_root, material_type)
                standard_file = '{0}Record.txt'.format(material_type)
            else:
                raise RuntimeError('TAG cannot be an empty string.')
            # END-IF-ELSE

            standard_tuple = material_type, standard_dir, standard_file

            # create workspace if not existing
            if os.path.exists(standard_dir) is False:
                self._create_standard_directory(standard_dir, material_type)
            print(material_type, standard_dir)
        else:
            standard_tuple = None
            print(self._commandArgsDict.keys())

        return standard_tuple

    @staticmethod
    def _create_standard_directory(standard_dir, material_type):
        """
        create a standard sample directory for GSAS file and sample log record
        :param standard_dir:
        :param material_type: name/type of the standard type
        :return:
        """
        datatypeutility.check_file_name(standard_dir, check_exist=False,
                                        is_dir=True,
                                        check_writable=True,
                                        note='Standard (tag) directory')

        try:
            os.mkdir(standard_dir, 0o777)
            print('[INFO VBIN TAG] Created directory {}'.format(standard_dir))
        except OSError as os_err:
            raise RuntimeError('Failed to create {} for standard material {} due to {}'
                               ''.format(standard_dir, material_type, os_err))

        return

    def set_ipts(self):
        """
        Set IPTS
        """
        # get IPTS from setup
        if 'IPTS' in self._commandArgsDict:
            # ITPS from command as highest priority
            try:
                self._iptsNumber = int(self._commandArgsDict['IPTS'])
            except ValueError as value_err:
                raise RuntimeError('Unable to set IPTS {} due to {}'
                                   ''.format(self._commandArgsDict['IPTS'], value_err))
        elif self._iptsNumber is not None:
            # IPTS is previously stored and to be used
            pass
        else:
            raise RuntimeError('IPTS is not given in the command arguments. Or default is not set.')

        # check validity
        assert 0 < self._iptsNumber, 'IPTS number %d is an invalid integer.' % self._iptsNumber

        # set
        # self._controller.set_ipts(self._iptsNumber)

        return

    def set_raw_nexus(self):
        """
        Set raw NeXus file name
        :return:
        """
        self._raw_nexus_file_name = self._commandArgsDict['NEXUS']
        if os.path.exists(self._raw_nexus_file_name) is False:
            raise RuntimeError('NeXus file {} does not exist.'.format(self._raw_nexus_file_name))
        self._iptsNumber = False

        return

    @staticmethod
    def split_run_numbers(run_numbers_str):
        """
        split run numbers from a string.
        example: run1, run2-run10, run11, run12,
        :param run_numbers_str:
        :return:
        """
        def pop_range(range_str):
            """
            replace a range a - b to a list such as a, a1, a2, .., b
            :param range_str:
            :return:
            """
            terms = range_str.split('-')
            start_value = int(terms[0])
            stop_value = int(terms[1])
            assert start_value <= stop_value, 'Start value %d must be smaller or euqal to stop value %s.' \
                                              '' % (start_value, stop_value)
            return range(start_value, stop_value+1)

        run_numbers_str = run_numbers_str.replace(' ', '')
        terms = run_numbers_str.split(',')
        run_number_list = list()
        for term in terms:
            if term.count('-') == 0:
                run_number_list.append(int(term))
            elif term.count('-') == 1:
                run_number_list.extend(pop_range(term))
            else:
                raise ValueError('Single term contains more than 2 -')
        # END-FOR

        return run_number_list
