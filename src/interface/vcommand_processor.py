"""
This module contains a class to handle standard VDRIVE commands
"""
# from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal


class VdriveCommandProcessor(object):
    """
    VDrive command processing class
    """
    # signal to reduce a run
    reduceSignal = pyqtSignal(list)

    def __init__(self, controller):
        """
        Initialization
        """
        # check input requirement
        assert controller is not None, 'controller cannot be None'
        if controller.__class__.__name__ != 'VDriveAPI':
            raise AssertionError('Controller is of wrong type %s.' % str(type(controller)))

        # set up the commands
        self._commandList = ['CHOP', 'VBIN', 'VDRIVE', 'MERGE']

        return

    def get_vdrive_commands(self):
        """
        Get list of the commands of VDRIVE
        :return:
        """
        return self._commandList[:]

    def process_commands(self, command_str):
        """
        Process commands string
        :param command_str:
        :return:
        """
        # check input requirements
        assert isinstance(command_str, str), 'Command %s must be a string but not %s.' \
                                             '' % (str(command_str),
                                                   str(type(command_str)))

        # parse
        command_str = command_str.strip()
        if len(command_str) == 0:
            # return with empty string input
            return True

        command_terms = command_str.split()
        v_command = command_terms[0]

        # return with wrong command
        if v_command not in self._commandList:
            err_msg = 'Command %s is not a supported VDRIVE command. ' \
                      'Type VDRIVE --HELP' % v_command
            return False, err_msg

        # check command parameters valid or not
        if v_command == 'VDRIVE':
            status, err_msg = self._process_vdrive(v_command[1:])
        elif v_command == 'REDUCE':
            status, err_msg = self._process_reduce(v_command[1:])
        else:
            raise NotImplementedError('Impossible situation!')

        return status, err_msg

    def _process_chop(self, args):
        """
        VDRIVE CHOP
        Example: CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
        :param args:
        :return:
        """
        arg_dict = dict()
        for arg in args:
            terms = arg.split('=')
            if len(terms) < 2:
                return False, 'argument "%s" is not valid.' % arg
            key_word = terms[0]
            value = int(terms[1])
            arg_dict[key_word] = value
        # END-FOR

        return True, ''

    def _process_reduce(self, args):
        """
        Process the reduction command
        :param args:
        :return:
        """
        if len(args) == 0:
            message = 'VREDUCTION input: ... ... ...'
            return True, message

        # parse argument
        try:
            a = 1
            b = 2
            command_args = [a, b]
            self.reduceSignal.emit(command_args)
        except IndexError:
            error_msg = '...'

    def _process_vdrive(self, args):
        """

        :param args:
        :return:
        """
        if len(args) == 0:
            help_msg = 'Options: -H (help)'
            return True, help_msg

        if args == '-H':
            msg = 'Supported commands: %s.' % str(self._commandList)
            return True, msg

        return False, 'Arguments are not supported!'
