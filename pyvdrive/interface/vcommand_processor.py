"""
This module contains a class to handle standard VDRIVE commands
"""
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtCore import pyqtSignal
except ImportError:
    from PyQt4.QtGui import QMainWindow
    from PyQt4.QtCore import pyqtSignal

import vdrive_commands.chop
import vdrive_commands.show_info
import vdrive_commands.vbin
import vdrive_commands.vmerge
import vdrive_commands.view
import vdrive_commands.vpeak
import vdrive_commands.process_vcommand
import pyvdrive.lib.datatypeutility
from pyvdrive.lib import datatypeutility
import time
from pyvdrive.lib import vulcan_util


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
        assert isinstance(main_window, QMainWindow), 'Main window must be a QtGui.QMainWindow'
        assert controller is not None, 'controller cannot be None'
        if controller.__class__.__name__ != 'VDriveAPI':
            raise AssertionError('Controller is of wrong type %s.' % str(type(controller)))

        self._mainWindow = main_window
        self._myController = controller

        # set up the commands
        self._commandList = ['CHOP', 'VBIN', 'VDRIVE', 'MERGE', 'AUTO', 'VIEW', 'VDRIVEVIEW', 'VPEAK',
                             'INFO', '2THETABIN']

        self._view_chop_run_name_map = dict()  # [run number (int)] = chop run name (in Reduced Data View)

        return

    def get_vdrive_commands(self):
        """
        Get list of the commands of VDRIVE
        :return:
        """
        return self._commandList[:]

    @staticmethod
    def parse_command_arguments(command, command_args):
        """ Parse command arguments and store to a dictionary, whose key is argument key and
        value is argument value.
        Rules:
        1. a valid argument is in format as: key=value.
        2. two arguments are separated by a comma ','.
        3. list is supported by using '~' other than ','
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

                # process argument value: remove ' and "
                arg_value = items[1]
                arg_value = arg_value.replace('\'', '')
                arg_value = arg_value.replace('"', '')

                # set
                arg_dict[command_arg] = arg_value
            else:
                err_msg = 'command %s %d-th term <%s> is not valid. Must have a = sign!' % (command, index, term)
                return False, err_msg
            # END-IF
        # END-FOR

        return True, arg_dict

    @staticmethod
    def pre_process_idl_command(idl_command):
        """ Pre-process IDL command such that
        1. list bracket [] will be identified and string inside will have ',' replaced by '~'
        2. list bracket []'s sequence will checked
        :param idl_command:
        :return:
        """
        datatypeutility.check_string_variable('IDL command', idl_command)

        # check equal of bracket
        if idl_command.count(']') != idl_command.count('['):
            raise RuntimeError('Found unpaired list bracket [ and ] in {}'.format(idl_command))

        # replace
        num_bracket = idl_command.count(']')
        for bracket_index in range(num_bracket):
            left_index = idl_command.index('[')
            right_index = idl_command.index(']')
            if left_index > right_index:
                raise RuntimeError('In ILD command {}, list bracket\' order is reversed.'.format(idl_command))

            list_str = idl_command[left_index+1:right_index]
            list_str = list_str.replace(',', '~')

            # construct new command
            idl_command = idl_command[:left_index] + list_str + idl_command[right_index+1:]
        # END-FOR

        return idl_command

    def process_commands(self, vdrive_command):
        """ Process commands string. The work include
        1. pre-process list special such as arg=[a,b,c],
        2. separate command from arguments
        3. ...
        :param vdrive_command:
        :return:
        """
        # check
        datatypeutility.check_string_variable('VDRIVE (IDL) command', vdrive_command, None)

        # pre-process in order to  accept list in bracket [...]
        vdrive_command_pp = self.pre_process_idl_command(vdrive_command)

        # split
        command_script = vdrive_command_pp.split(',')
        command = command_script[0].strip()
        command_args = command_script[1:]

        print '[INFO-IDL] Parse input IDL command: {} to {}\n\tArguments = {}' \
              ''.format(vdrive_command, vdrive_command_pp, command)

        # support command case insensitive
        raw_command = command
        command = command.upper()

        # check input command whether it is recognized
        if command not in self._commandList:
            return False, 'Command %s is not in supported command list: %s' \
                          '' % (raw_command, str(self._commandList))

        # process special command VDRIVE (for help)
        if command == 'VDRIVE':
            status, err_msg = self._process_vdrive(command_args)
            return status, err_msg

        # process regular VDRIVE command by parsing command arguments and store them to a dictionary
        status, ret_obj = self.parse_command_arguments(command, command_args)

        if status:
            arg_dict = ret_obj
        else:
            error_msg = ret_obj
            return False, error_msg

        # call the specific command class builder
        if command == 'CHOP':
            # chop
            chop_start_time = time.time()
            status, err_msg = self._process_chop(arg_dict)
            chop_stop_time = time.time()
            err_msg += '\nExecution time = {} seconds'.format(chop_stop_time - chop_start_time)
        elif command == 'VBIN' or command == 'VDRIVEBIN':
            # bin
            status, err_msg = self._process_vbin(arg_dict)

        elif command == '2THETABIN':
            # group pixels by 2theta and reduce to GSAS
            status, err_msg = self._process_2theta_bin(arg_dict)

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

        elif command == 'INFO':
            # query some information from previoulsy measured runs
            status, err_msg = self._process_info_query(arg_dict)

        else:
            raise RuntimeError('Impossible situation!')

        return status, err_msg

    def _process_2theta_bin(self, arg_dict):
        """ Group pixels by 2theta and reduce to a series of GSAS file
        :param arg_dict:
        :return:
        """
        from vdrive_commands import bin2theta

        try:
            processor = bin2theta.BinBy2Theta(self._myController, arg_dict)
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
            return False, 'Bin-by-2theta encountered command argument error: {}'.format(comm_err)

        status, message = self._process_command(processor, arg_dict)

        return status, message

    def _process_auto_reduction(self, arg_dict):
        """
        VDRIVE auto reduction
        :param arg_dict:
        :return:
        """
        try:
            processor = vdrive_commands.vbin.AutoReduce(self._myController, arg_dict)
        except vdrive_commands.process_vcommand.CommandKeyError as com_err:
            return False, 'Command argument error: %s.' % str(com_err)

        if len(arg_dict) == 0:
            status = True
            err_msg = processor.get_help()
        else:
            status, err_msg = processor.exec_cmd()

        return status, err_msg

    def _process_chop(self, arg_dict):
        """ process command VDRIVE CHOP
        Example: CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
        :param arg_dict:
        :return: 2-tuple
        """
        # create a new VdriveChop instance
        try:
            processor = vdrive_commands.chop.VdriveChop(self._myController, arg_dict, self._mainWindow)
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # execute
        status, message = self._process_command(processor, arg_dict)

        # get information from VdriveChop
        self._chopIPTSNumber, self._chopRunNumberList = processor.get_ipts_runs()

        # process for special case: log-pick-helper
        if message == 'pop':
            # pop out the log window
            log_window = self._mainWindow.do_launch_log_picker_window()
            ipts_number, run_numbers = processor.get_ipts_runs()
            # set IPTS and run if they are given
            if ipts_number:
                log_window.set_ipts(ipts_number)
            if len(run_numbers) > 0:
                log_window.set_run(run_numbers[0])

            if isinstance(self._chopRunNumberList, list) and len(self._chopRunNumberList) > 0:
                log_window.load_run(self._chopRunNumberList[0])
                log_window.setWindowTitle('IPTS {0} Run {1}'.format(self._chopIPTSNumber, self._chopRunNumberList[0]))
            else:
                log_window.load_run()
        # END-IF

        return status, message

    def _process_info_query(self, arg_dict):
        """
        process information query
        :param arg_dict:
        :return:
        """
        # create a new Info query instance
        try:
            processor = vdrive_commands.show_info.RunsInfoQuery(self._myController, arg_dict)
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # call and execute
        status, message = self._process_command(processor, arg_dict)

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
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
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
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        # execute
        status, message = self._process_command(processor, arg_dict)
        if not status:
            return status, message
        elif len(message) > 0:
            # this is for help
            return status, message

        # launch
        view_window = self._mainWindow.do_launch_reduced_data_viewer()

        # viewing: with simple launch, IPTS is not ncessary
        ipts_number = processor.get_ipts_number()

        # no IPTS: user wants to load everything in memory
        if ipts_number is None:
            return True, 'Reduced Data Viewer Window is launched'

        # set IPTS
        view_window.set_ipts_number(ipts_number)
        view_window.set_x_range(processor.x_min, processor.x_max)
        view_window.set_unit(processor.unit)

        # check whether the run is just chopped and data still in memory
        run_number, ipts_number = processor.get_run_tuple_list()[0]
        if run_number in self._myController.project.reduction_manager.get_reduced_chopped_runs():
            # TODO - TONIGHT 196 - Need to make this False @ end
            load_gsas = True
        else:
            load_gsas = True

        # proton charge normalization: complicated
        if processor.do_proton_charge_normalization:
            if processor.is_chopped_run and load_gsas:
                # chopped runs
                try:
                    log_header, log_set = vulcan_util.import_sample_log_record(ipts_number, run_number, is_chopped=True,
                                                                               record_type='start')
                except RuntimeError as run_err:
                    return False, 'Unable to import sample log record: {}'.format(run_err)
                view_window.set_chopped_logs(ipts_number, run_number, log_header, log_set, 'start')
            elif load_gsas:
                # raw runs
                try:
                    log_set = vulcan_util.import_auto_record(ipts_number, run_number)
                except RuntimeError as run_err:
                    return False, 'Unable to import AutoRecord.txt of IPTS-{} Run-{} due to {}' \
                                  ''.format(ipts_number, run_number, run_err)
                view_window.set_logs(ipts_number, run_number, log_set)
        # END-IF (proton charge normalization)

        # vanadium
        if processor.do_vanadium_normalization:
            van_run_number = processor.get_vanadium_number(run_number)
            # load vanadium to workspace workspace and get calculation prm file
            van_gsas_name, iparam_file_name = \
                self._myController.archive_manager.locate_process_vanadium(van_run_number)
            van_ws_name = self._myController.project.reduction_manager.gsas_writer.import_vanadium(van_gsas_name)
            view_window.set_vanadium_ws(van_run_number, van_ws_name)
        else:
            van_run_number = None

        # about run number
        if processor.is_chopped_run:
            # chopped run
            view_window.set_run_number(run_number)

            chop_seq_list = processor.get_chopped_sequence_range()
            if load_gsas:
                loaded_chop_seq_list = view_window.do_load_chopped_runs(ipts_number, run_number, chop_seq_list)
                if len(loaded_chop_seq_list) == 0:
                    return False, 'None sequences in user-specified list ({}) can be loaded.'.format(chop_seq_list)
                else:
                    chop_seq_list = loaded_chop_seq_list
            else:
                raise RuntimeError('TONIGHT 196')
            # END-IF

            # chop_name = '{}: GSAS'.format(run_number)
            # chop_key = run_number

            # refresh list and set to chop run
            # view_window.do_refresh_existing_runs(set_to=chop_name, set_to_seq=chop_seq_list[0], is_chopped=True)
            now_single_set, prev_single_set, now_set, prev_set = view_window.do_refresh_existing_runs()
            new_names = list(now_set - prev_set)
            if len(new_names) > 0:
                # if there are new chopped runs
                # TODO - TONIGHT 191 - Better to assign this dictionary to ReducedDataView
                self._view_chop_run_name_map[run_number] = new_names[0]
                chop_key = view_window.set_chopped_run(new_names[0], str(chop_seq_list[0]))
            else:
                print ('[DB.....BAT] No change.  Search {} from [{}]'.format(run_number, self._view_chop_run_name_map))
                chop_key = view_window.set_chopped_run(self._view_chop_run_name_map[run_number],
                                                       str(chop_seq_list[0]))

            # set a signal to view-window to make main_only True (once)
            # # TODO - TONIGHT 191 - Separate plotting individual windows!
            # TODO - TONIGHT 196 - For in-memory, requiring more than run number but whole chop-key
            if isinstance(chop_key, tuple):
                run_number = chop_key[0]
            else:
                run_number = chop_key
            view_window.plot_chopped_run(run_number, bank_id=1,
                                         seq_list=chop_seq_list,
                                         van_norm=processor.do_vanadium_normalization,
                                         van_run=van_run_number,
                                         pc_norm=processor.do_proton_charge_normalization,
                                         main_only=False,
                                         plot3d=processor.plot_3d)

        elif len(processor.get_run_tuple_list()) == 1:
            # raw/original/non-chopped run situation
            view_window.set_run_number(run_number)
            data_key = view_window.do_load_single_run(ipts_number, run_number, False)
            if data_key:
                now_single_set, prev_single_set, now_set, prev_set = view_window.do_refresh_existing_runs()
                view_window.plot_single_run(data_key,
                                            van_norm=processor.do_vanadium_normalization,
                                            van_run=van_run_number,
                                            pc_norm=processor.do_proton_charge_normalization)
                status = True
                message = ''
            else:
                status = False
                message = 'Unable to load GSAS file of IPTS-{} Run-{}'.format(ipts_number, run_number)
        else:
            # multiple but none chopped run
            raise NotImplementedError('ASAP')

        # write out the peak parameters
        if processor.do_calculate_peak_parameter:
            # TODO - NEXT - Need a use case to calculate peak parameters to further development
            raise RuntimeError('Need a solid use case to test this feature')
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
        except vdrive_commands.process_vcommand.CommandKeyError as comm_err:
            return False, str(comm_err)

        status, message = self._process_command(processor, arg_dict)

        return status, message

    @staticmethod
    def _process_command(command_processor, arg_dict):
        """ process VDrive-compatible command
        :param command_processor:
        :param arg_dict:
        :return:
        """
        assert isinstance(command_processor, vdrive_commands.process_vcommand.VDriveCommand), \
            'VDrive IDL-compatible command processor {} must be an instance of ' \
            'vdrive_commands.process_vcommand.VDriveCommandbut but not of type {}' \
            ''.format(command_processor, type(command_processor))

        pyvdrive.lib.datatypeutility.check_dict('VDrive IDL-compatible command arguments', arg_dict)

        if len(arg_dict) == 0:
            # if there is no argument, just print out the help information
            message = command_processor.get_help()
            status = True
        else:
            try:
                status, message = command_processor.exec_cmd()
            except RuntimeError as run_err:
                status = False
                message = 'Unable to execute VDRIVE command due to {}'.format(run_err)

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
