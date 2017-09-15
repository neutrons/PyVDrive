# Set up path to PyVDrive
import sys
import os
import socket
# Import PyVDRive expliclity, if it is on analysis computer
if socket.gethostname().count('analysis-') > 0 or os.path.exists('/home/wzz') is False:
    sys.path.append('/SNS/users/wzz/local/lib/python/site-packages/')
import PyVDrive.lib.VDriveAPI as VdriveAPI

"""
Base class for VDRIVE command processors
"""


class CommandKeyError(Exception):
    """
    Self-defined VDRIVE command key error
    """
    def __init__(self, error):
        """

        """
        super(CommandKeyError, self).__init__(error)

        return


class VDriveCommand(object):
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
        assert isinstance(controller, VdriveAPI.VDriveAPI), 'Controller must be a VdriveAPI.VDriveAPI' \
                                                            'instance but not %s.' % controller.__class__.__name__
        assert isinstance(command_args, dict), 'Argument commands dictionary cannot be a %s.' \
                                               '' % str(type(command_args))

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

        return

    def exec_cmd(self):
        """ Execute VDRIVE command
        """
        raise NotImplementedError('Method exec_cmd must be override')

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
                print '[ERROR] {0}'.format(error_message)
                raise CommandKeyError(error_message)
        # END-FOF

        return

    def get_help(self):
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

        if 'Mytofbmin'.upper() in self._commandArgsDict:
            user_tof_min = float(self._commandArgsDict['Mytofbmin'.upper()])
        else:
            user_tof_min = None

        if 'Mytofbmax'.upper() in self._commandArgsDict:
            user_tof_max = float(self._commandArgsDict['Mytofbmax'.upper()])
        else:
            user_tof_max = None

        # get default setup
        if user_tof_min is None and user_tof_max is None and user_bin_width is None:
            # none of the 3 parameters is given. use default binning
            use_default_binning = True
            binning_parameters = None

        else:
            # parse by set up the default value
            use_default_binning = False

            if user_bin_width is None:
                user_bin_width = 0.001   # set to default in case only TOF range is customized value
            if user_tof_min is None:
                user_tof_min = 5000.
            if user_tof_max is None:
                user_tof_max = 70000.

            binning_parameters = (user_tof_min, user_bin_width, user_tof_max)
        # END-IF-ELSE

        return use_default_binning, binning_parameters

    def parse_run_number(self):
        """
        parse run numbers from RUNS and RUNE
        :return:
        """
        run_numbers_str = 'NO DEFINED'
        try:
            run_numbers_str = self._commandArgsDict['RUNS']
            run_number_list = self.split_run_numbers(run_numbers_str)
            if len(run_number_list) == 1 and 'RUNE' in self._commandArgsDict:
                # allow RUNE if RUNS is just 1 value
                run_end = int(self._commandArgsDict['RUNE'])
                if run_end < run_number_list[0]:
                    raise RuntimeError('RUNE {0} is less than RUNS {1}'.format(run_end, run_number_list[0]))
                run_number_list = range(run_number_list[0], run_end)
        except KeyError:
            raise RuntimeError('RUNS is not found.')
        except (ValueError, TypeError):
            raise RuntimeError('RUNS {0} is not an integer.'.format(run_numbers_str))

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

            standard_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard'
            if os.access(standard_dir, os.W_OK) is False:
                # if standard VDRIVE default directory is not writable, then use the local one
                # very likely the current PyVdrive is running in a testing mode.
                standard_dir = os.getcwd()

            if material_type == 'si':
                material_type = 'Si'
                standard_dir = os.path.join(standard_dir, 'Si')
                standard_file = 'SiRecord.txt'
            elif material_type == 'v':
                material_type = 'Vanadium'
                standard_dir = os.path.join(standard_dir, 'Vanadium')
                standard_file = 'VRecord.txt'
            elif material_type == 'c':
                material_type = 'C'
                standard_dir = os.path.join(standard_dir, 'C')
                standard_file = 'CRecord.txt'
            elif material_type == 'ceo2':
                material_type = 'CeO3'
                standard_dir = os.path.join(standard_dir, 'CeO2')
                standard_file = 'CeO2Record.txt'
            elif len(material_type) > 0:
                # create arbitrary tag
                # use the user specified TAG as the type of material
                material_type = self._commandArgsDict['TAG']
                standard_dir = os.path.join(standard_dir, material_type)
                standard_file = '{0}Record.txt'.format(material_type)
            else:
                raise RuntimeError('TAG cannot be an empty string.')
            # END-IF-ELSE

            standard_tuple = material_type, standard_dir, standard_file

            # create workspace if not existing
            if os.path.exists(standard_dir) is False:
                self._create_standard_directory(standard_dir)
        else:
            standard_tuple = None

        return standard_tuple

    def set_ipts(self):
        """
        Set IPTS
        """
        # get IPTS from setup
        if 'IPTS' in self._commandArgsDict:
            # ITPS from command as highest priority
            self._iptsNumber = int(self._commandArgsDict['IPTS'])
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
