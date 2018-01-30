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

    @staticmethod
    def parse_command_arguments(command, command_args):
        """
        parse command arguments and store to a dictionary, whose key is argument key and
        value is argument value
        a valid argument is in format as: key=value
        and two arguments are separated by a comma ','
        :param command:
        :param command_args:
        :return:
        """
        arg_dict = dict()
        for index, term in enumerate(command_args):
            term = term.strip()
            if len(term) == 0:
                # empty string. might appear at the end of the command
                continue

            items = term.split('=', 1)
            if len(items) == 2:
                # force command argument to be UPPER case in order to support case-insensitive syntax
                command_arg = items[0].upper()

                # special treatment for typical user type
                if command_arg == 'ITPS':
                    print '[WARNING] Argument ITPS is not supported. Auto correct it to IPTS.'
                    command_arg = 'IPTS'

                # process argument value. replace all the ', "
                arg_value = items[1]
                arg_value = arg_value.replace('\'', '')
                arg_value = arg_value.replace('"', '')

                # set
                arg_dict[command_arg] = arg_value
            else:
                err_msg = 'command %s %d-th term <%s> is not valid. Must have a = sign!' % (command, index, term)
                print '[DB...ERROR] ', err_msg
                return False, err_msg
            # END-IF
        # END-FOR

        return arg_dict

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

        # support command case insensitive
        raw_command = command
        command = command.upper()

        # check command's validity
        if command not in self._commandList:
            return False, 'Command %s is not in supported command list: %s' \
                          '' % (raw_command, str(self._commandList))

        # command body
        assert isinstance(command_args, list)

        # process special command VDRIVE (for help)
        if command == 'VDRIVE':
            status, err_msg = self._process_vdrive(command_args)
            return status, err_msg

        # process regular VDRIVE command by parsing command arguments and store them to a dictionary
        arg_dict = self.parse_command_arguments(command, command_args)

        # call the specific command class builder
        if command == 'CHOP':
            # chop
            status, err_msg = self._process_chop(arg_dict)
        elif command == 'VBIN' or command == 'VDRIVEBIN':
            # bin
            status, err_msg = self._process_vbin(arg_dict)

        elif command == 'VDRIVEVIEW' or command == 'VIEW':
            # view
            status, err_msg = self._process_view(arg_dict)

        elif command == 'MERGE':
            # merge
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
        try:
            processor = vdrive_commands.vbin.AutoReduce(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as com_err:
            return False, 'Command argument error: %s.' % str(com_err)

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
            if isinstance(self._chopRunNumberList, list) and len(self._chopRunNumberList) > 0:
                log_window.load_run(self._chopRunNumberList[0])
                log_window.setWindowTitle('IPTS {0} Run {1}'.format(self._chopIPTSNumber, self._chopRunNumberList[0]))
        # END-IF

        return status, message

    def _process_merge(self, arg_dict):
        """
        process command MERGE
        :param arg_dict:
        :return:
        """
        # create a new VdriveMerge instance
        try:
            processor = vdrive_commands.vmerge.VdriveMerge(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # execute
        status, message = self._process_command(processor, arg_dict)

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
        elif len(message) > 0:
            # this is for help
            return status, message

        # viewing
        view_window = self._mainWindow.do_launch_reduced_data_viewer()
        view_window.set_ipts_number(processor.get_ipts_number())

        view_window.set_x_range(processor.x_min, processor.x_max)
        view_window.set_unit(processor.unit)

        if processor.is_1_d:
            # 1-D image
            view_window.set_canvas_type(dimension=1)

            vanadium_dict = None
            if processor.do_vanadium_normalization:
                vanadium_dict = dict()
                for run_number in processor.get_run_number():
                    vanadium_dict[run_number] = processor.get_vanadium_number(run_number)

            # view_window.add_reduced_runs(processor.get_run_tuple_list(), vanadium_dict)
            # TODO ASAP Need to find out how to set vanadium information... but now
            # ipts_run_list = processor.get_run_tuple_list()
            # run_list = list()
            # for run, ipts in ipts_run_list:
            #     run_list.append(run)
            # view_window.add_reduced_runs(run_list, True)

            # view_window.plot_by_run_number(processor.get_run_number(), bank_id=1)

        elif processor.is_chopped_run:
            # chopped run... can be 1D (only 1 chopped data) or 2D (more than 1 chopped data)
            # get normalization information
            if processor.do_vanadium_normalization:
                van_run = processor.get_vanadium_number(processor.get_run_number())
            else:
                van_run = None
            pc_norm = processor.do_proton_charge_normalization

            view_window.plot_chopped_data_2d(run_number=processor.get_run_number(),
                                             chop_sequence=processor.get_chopped_sequence_range(),
                                             bank_id=1,
                                             bank_id_from_1=True,
                                             chopped_data_dir=processor.get_reduced_data_directory(),
                                             vanadium_run_number=van_run,
                                             proton_charge_normalization=pc_norm)
        else:
            # 2-D or 3-D image for multiple runs
            view_window.set_canvas_type(dimension=2)
            view_window.add_reduced_runs(processor.get_run_tuple_list())
            view_window.plot_multiple_runs_2d(bank_id=1, bank_id_from_1=True)
        # END-FOR

        # write out the peak parameters
        if processor.do_calculate_peak_parameter:
            ipts_number, run_number_list = processor.get_ipts_runs()
            chop_list = processor.get_chopped_sequence_range()
            status, ret_obj = self._myController.calculate_peak_parameters(ipts_number, run_number_list, chop_list,
                                                                           processor.x_min, processor.x_max,
                                                                           processor.output_peak_parameters_to_console,
                                                                           processor.peak_parameters_file)

            if status:
                message = ''
                for bank_id in ret_obj.keys():
                    message += 'Bank {0}\n{1}\n'.format(bank_id, ret_obj[bank_id])
            else:
                message = ret_obj
        # END-IF-ELSE

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
            data_viewer = self._mainWindow.do_launch_reduced_data_viewer()
            # title
            data_viewer.set_title_plot_run('Processing vanadium')
            # get data (key), set to viewer and plot
            controller_data_key = processor.get_loaded_data()
            ipts_number, run_number_list = processor.get_ipts_runs()
            van_run_number = processor.get_vanadium_run()
            # TODO/FUTURE/BETTER:QUALITY - shall we merge add_data_set() to add_run_numbers()???
            # TODO/ISSUE/NOW - unit should be set in a softer way...
            viewer_data_key = data_viewer.add_data_set(ipts_number, van_run_number, controller_data_key,
                                                       unit='dSpacing')
            data_viewer.plot_1d_diffraction(viewer_data_key, bank_id=1)

            if processor.to_shift:
                data_viewer.set_vanadium_fwhm(2)
            else:
                data_viewer.set_vanadium_fwhm(7)
        # END-IF

        return status, message

    def _process_vbin(self, arg_dict):
        """
         VBIN
         :param arg_dict:
         :return:
         """
        try:
            processor = vdrive_commands.vbin.VBin(self._myController, arg_dict)
        except vdrive_commands.procss_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        status, message = self._process_command(processor, arg_dict)

        return status, message

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
            msg = 'Supported arguments: %s.' % str(self._commandList)
            return True, msg

        return False, 'Arguments {0} are not supported!'.format(args)
