"""
This module contains a class to handle standard VDRIVE commands
"""
# from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal

import vdrive_commands.chop
import vdrive_commands.vbin
import vdrive_commands.vmerge


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

    def process_commands(self, command, command_args):
        """
        Process commands string
        :param command:
        :param command_args: arguments of a command
        :return:
        """
        # check command (type, whether it is supported)
        assert isinstance(command, str), 'Command %s must be a string but not %s.' \
                                         '' % (str(command),  str(type(command)))

        if command not in self._commandList:
            return False, 'Command %s is not in supported command list, which includes %s' \
                          '' % str(self._commandList)

        # command body
        assert isinstance(command_args, list)

        # process special command VDRIVE (for help)
        if command == 'VDRIVE':
            status, err_msg = self._process_vdrive(command_args)
            return status, err_msg

        # process regular VDRIVE command
        # parse command arguments to dictionary
        arg_dict = dict()
        for index, term in enumerate(command_args):
            items = term.split('=', 1)
            if len(items) == 2:
                arg_dict[items[0]] = items[1]
            else:
                return False, 'Command %s %d-th term "%s" is not valid.' % (command, index,
                                                                            term)
            # END-IF
        # END-FOR

        # call the specific command class builder
        if command == 'CHOP':
            status, err_msg = self._process_chop(arg_dict)
        elif command == 'VBIN':
            status, err_msg = self._process_vbin(arg_dict)
        elif command == 'MERGE':
            status, err_msg = self._process_merge(arg_dict)
        else:
            raise RuntimeError('Impossible situation!')

        return status, err_msg

    def _process_chop(self, arg_dict):
        """
        VDRIVE CHOP
        Example: CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
        :param arg_dict:
        :return:
        """
        assert isinstance(arg_dict, dict) and len(arg_dict) > 0

        processor = vdrive_commands.chop.VdriveChop(self._myParent.get_controller(), arg_dict)

        status, err_msg = processor.exec_cmd()

        return status, err_msg

    def _process_vbin(self, arg_dict):
        """
         VBIN
         :param arg_dict:
         :return:
         """
        assert isinstance(arg_dict, dict) and len(arg_dict) > 0

        processor = vdrive_commands.vbin(self._myParent.get_controller(), arg_dict)

        status, err_msg = processor.exec_cmd()

        return status, err_msg

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
