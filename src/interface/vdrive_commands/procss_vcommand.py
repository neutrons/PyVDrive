# Set up path to PyVDrive
import sys
import os
import socket
# if it is on analysis computer...
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
    SupportedArgs = []

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

        # set arguments
        self._commandArgList = command_args

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
        # check whether the any non-supported args
        input_args = self._commandArgList.keys()
        for arg_key in input_args:
            if arg_key not in supported_arg_list:
                error_message = 'Command %s\'s argument "%s" is not recognized. Supported ' \
                                'commands are %s.' % (self._commandName, arg_key, str(supported_arg_list))
                print error_message
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
        blabla
        :return:
        """
        return self._iptsNumber, self._runNumberList[:]

    def set_ipts(self):
        """
        Set IPTS
        """
        # get IPTS from setup
        if 'IPTS' in self._commandArgList:
            # ITPS from command as highest priority
            self._iptsNumber = int(self._commandArgList['IPTS'])
        elif self._iptsNumber is not None:
            # IPTS is previously stored and to be used
            pass
        else:
            raise RuntimeError('IPTS is not given in the command arguments. Or default is not set.')

        # check validity
        assert 0 < self._iptsNumber, 'IPTS number %d is an invalid integer.' % self._iptsNumber

        # set
        self._controller.set_ipts(self._iptsNumber)

        return

