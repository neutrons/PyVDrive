"""
This module contains a class to handle standard VDRIVE commands
"""
# from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import vdrive_commands.chop
import vdrive_commands.vbin
import vdrive_commands.vmerge
import vdrive_commands.view
import vdrive_commands.vpeak
import vdrive_commands.procss_vcommand


class VdriveCommandProcessor(object):
    """
    VDrive command processing class
    """
    # signal to reduce a run
    reduceSignal = pyqtSignal(list)

    def __init__(self, main_window, controller):
        """
        Initialization
        """
        # check input requirement
        assert isinstance(main_window, QtGui.QMainWindow), 'Main window must be a QtGui.QMainWindow'
        assert controller is not None, 'controller cannot be None'
        if controller.__class__.__name__ != 'VDriveAPI':
            raise AssertionError('Controller is of wrong type %s.' % str(type(controller)))

        self._mainWindow = main_window
        self._myController = controller

        # set up the commands
        self._commandList = ['CHOP', 'VBIN', 'VDRIVE', 'MERGE', 'AUTO', 'VIEW', 'VDRIVEVIEW', 'VPEAK']

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
        :param command_args: arguments of a command, excluding command
        :return:
        """
        print '[DB...COMMAND PROCESSOR] Command = %s; Arguments = %s' % (command, str(command_args))

        # check command (type, whether it is supported)
        assert isinstance(command, str), 'Command %s must be a string but not %s.' \
                                         '' % (str(command),  str(type(command)))

        if command not in self._commandList:
            return False, 'Command %s is not in supported command list, which includes %s' \
                          '' % (str(self._commandList), str(self._commandList))

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
                err_msg = 'Command %s %d-th term <%s> is not valid.' % (command, index, term)
                print '[DB...ERROR] ', err_msg
                return False, err_msg
            # END-IF
        # END-FOR

        # call the specific command class builder
        if command == 'CHOP':
            status, err_msg = self._process_chop(arg_dict)
        elif command == 'VBIN':
            status, err_msg = self._process_vbin(arg_dict)
        elif command == 'VDRIVEVIEW' or command == 'VIEW':
            status, err_msg = self._process_view(arg_dict)
        elif command == 'MERGE':
            status, err_msg = self._process_merge(arg_dict)
        elif command == 'AUTO':
            # auto reduction command
            status, err_msg = self._process_auto_reduction(arg_dict)
        elif command == 'VPEAK':
            # process vanadium peak
            status, err_msg = self._process_vanadium_peak(arg_dict)
        else:
            raise RuntimeError('Impossible situation!')

        return status, err_msg

    def _process_auto_reduction(self, arg_dict):
        """
        VDRIVE auto reduction
        :param arg_dict:
        :return:
        """
        print '[DB...BAT] Am I reached 2'
        try:
            processor = vdrive_commands.vbin.AutoReduce(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as com_err:
            return False, 'Command argument error: %s.' % str(com_err)

        print '[DB...BAT] Am I reached 3'
        if len(arg_dict) == 0:
            status = True
            err_msg = processor.get_help()
        else:
            status, err_msg = processor.exec_cmd()

        return status, err_msg

    def _process_chop(self, arg_dict):
        """
        VDRIVE CHOP
        Example: CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
        :param arg_dict:
        :return: 2-tuple
        """
        # create a new VdriveChop instance
        try:
            processor = vdrive_commands.chop.VdriveChop(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # execute
        status, message = self._process_command(processor, arg_dict)

        # get information from VdriveChop
        self._chopIPTSNumber, self._chopRunNumberList = processor.get_ipts_runs()

        # process for special case: log-pick-helper
        if message == 'pop':
            log_window = self._mainWindow.do_launch_log_picker_window()
            log_window.load_run(self._chopRunNumberList[0])
            log_window.setWindowTitle('IPTS {0} Run {1}'.format(self._chopIPTSNumber, self._chopRunNumberList[0]))
        # END-IF

        return status, message

    def _process_view(self, arg_dict):
        """
        process command VIEW or VDRIVEVIEW
        :param arg_dict:
        :return:
        """
        # create a new VdriveView instance
        try:
            processor = vdrive_commands.view.VdriveView(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # execute
        status, message = self._process_command(processor, arg_dict)
        if not status:
            return status, message

        view_window = self._mainWindow.do_view_reduction()
        view_window.set_ipts_number(processor.get_ipts_number())

        if processor.is_1_d:
            # 1-D image
            view_window.set_canvas_type(dimension=1)
            view_window.add_run_numbers(processor.get_run_number_list())
            # plot
            view_window.plot_run(processor.get_run_number(), bank_id=1)
        elif processor.is_chopped_run:
            # 2-D image for chopped run
            view_window.set_canvas_type(dimension=2)
            view_window.set_chop_run_number(processor.get_run_number())
            view_window.set_chop_sequence(processor.get_chopped_sequence_range())
            view_window.plot_chopped_run(chopped_data_dir=processor.get_reduced_data_directory())
        else:
            # 2-D or 3-D image for multiple runs
            view_window.set_canvas_type(dimension=2)
            view_window.add_run_numbers(processor.get_run_number_list())
            view_window.plot_multiple_runs(bank_id=1, bank_id_from_1=True)
        # END-FOR

        return status, message

    def _process_vanadium_peak(self, arg_dict):
        """
        process vanadium peak
        :param arg_dict:
        :return:
        """
        # generate a VanadiumPeak object to process the command
        processor = vdrive_commands.vpeak.VanadiumPeak(self._myController, arg_dict)

        # process command
        status, message = self._process_command(processor, arg_dict)
        if not status:
            return False, message

        # process for special case: log-pick-helper
        if message == 'pop':
            data_viewer = self._mainWindow.do_view_reduction()
            # title
            data_viewer.set_title('Processing vanadium')
            # get data (key), set to viewer and plot
            controller_data_key = processor.get_loaded_data()
            ipts_number, run_number_list = processor.get_ipts_runs()
            van_run_number = processor.get_vanadium_run()
            viewer_data_key = data_viewer.add_data_set(ipts_number, van_run_number, controller_data_key)
            data_viewer.plot_data(viewer_data_key, bank_id=1)
        # END-IF

        return status, message

    def _process_vbin(self, arg_dict):
        """
         VBIN
         :param arg_dict:
         :return:
         """
        processor = vdrive_commands.vbin.VBin(self._myController, arg_dict)

        return self._process_command(processor, arg_dict)

    @staticmethod
    def _process_command(command_processor, arg_dict):
        """

        :param command_processor:
        :param arg_dict:
        :return:
        """
        assert isinstance(command_processor, vdrive_commands.procss_vcommand.VDriveCommand), \
            'not command processor but ...'
        assert isinstance(arg_dict, dict), 'Arguments dictionary %s must be a dictionary but not a %s.' \
                                           '' % (str(arg_dict), type(arg_dict))

        if len(arg_dict) == 0:
            message = command_processor.get_help()
            status = True
        else:
            status, message = command_processor.exec_cmd()

        return status, message

    def _process_vdrive(self, args):
        """

        :param args:
        :return:
        """
        if len(args) == 0:
            help_msg = 'VDRIVE: -H (help)'
            return True, help_msg

        if args == '-H':
            msg = 'Supported commands: %s.' % str(self._commandList)
            return True, msg

        return False, 'Arguments are not supported!'
