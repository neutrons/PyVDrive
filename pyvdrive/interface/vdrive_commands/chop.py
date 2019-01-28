"""
Implement VDRIVE command VCHOP
"""
import os
import time
from procss_vcommand import VDriveCommand
from procss_vcommand import convert_string_to
from pyvdrive.lib import datatypeutility
try:
    from PyQt5 import QtCore
    from PyQt5.QtCore import pyqtSignal
except (ImportError, RuntimeError) as import_err:
    print ('CHOP: {}'.format(import_err))
    from PyQt4 import QtCore
    from PyQt4.QtCore import pyqtSignal


class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'HELP', 'RUNS', 'RUNE', 'DBIN', 'LOADFRAME', 'FURNACE', 'BIN', 'PICKDATA', 'OUTPUT',
                     'BINFOLDER','MYTOFMIN', 'MYTOFMAX', 'BINW',
                     'PULSETIME', 'DT', 'RUNV', 'ROI', 'MASK', 'NEXUS', 'STARTTIME', 'STOPTIME',
                     'NUMBANKS', 'SAVECHOPPED2NEXUS', 'IPARM', 'DRYRUN']

    reduceSignal = QtCore.pyqtSignal(str)  # signal to send out

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',
        'NEXUS': 'NeXus file name (It cannot be used with IPTS/RUNS/RUNE)',
        'DBIN': 'time step for binning interval',
        'PICKDATA': 'Name of a plain text 2-column data file for start and stop time for splitters.',
        'LOADFRAME': 'Chop LoadFrame log (MTSLoadFrame) along with',
        'FURNACE': 'Chop Furnace log (MTSFurnace) along with',
        'BIN': 'If bin=1, chopped data will be reduced to GSAS files',
        'BANKS': 'Number of banks in the output GSAS file',
        'MYTOFMIN': 'User defined TOF min in binning parameter. It must be used with MYTOFMAX and BINW',
        'MYTOFMAX': 'User defined TOF max in binning parameter. It must be used with MYTOFMIN and BINW',
        'BINW': 'Logarithm binning step. It must be used with MYTOFMIN and MYTOFMAX',
        'OUTPUT': 'If specified, then the chopped files will be saved to the directory. Otherwise, these files '
                  'will be saved to /SNS/VULCAN/IPTS-????/shared.',
        'BINFOLDER': 'It is an alias for "OUTPUT"',
        'IPARM': 'GSAS profile calibration file (.iparam). Default is vulcan.prm',
        'DRYRUN': 'If equal to 1, then it is a dry run to check input and output.',
        'HELP': 'the Log Picker Window will be launched and set up with given RUN number.\n',
        'DT': 'the period between two adjacent time segments',
        'STARTTIME': 'The starting time of the first slicer.  Default is the run start',
        'STOPTIME': 'The stopping time of the last slicer. Default is the run stop',
        'RUNV': 'vanadium run number',
        'ROI': 'Files for Mantid made region of interest file in XML format',
        'MASK': 'Files for Mantid made mask file in XML format',
        'SAVECHOPPED2NEXUS': 'If equal to 1, then the chopped and reduced workspace will be save to a NeXus file. '
                             'Default is 0 (as False)'
    }

    def __init__(self, controller, command_args, main_window, ipts_number=None, run_number_list=None):
        """
        Initialization
        :param controller:
        :param command_args:
        :param ipts_number:
        :param run_number_list:
        """
        # call super
        super(VdriveChop, self).__init__(controller, command_args)

        # set up my name
        self._commandName = 'CHOP'
        # check argument
        self.check_command_arguments(self.SupportedArgs)
        #
        self._main_window = main_window

        # set default
        if ipts_number is not None and isinstance(ipts_number, int) and ipts_number > 0:
            self._iptsNumber = ipts_number
        if isinstance(run_number_list, list) and len(run_number_list) > 0:
            self._runNumberList = run_number_list[:]

        # define signal
        # TODO - NIGHT - Do this one step by one step: Long exec separate thread
        self.reduceSignal.connect(self._main_window.vdrive_command_return)

        return

    # TODO - NIGHT - Code quality
    def chop_data_by_log(self, run_number, start_time, stop_time, log_name, min_log_value, max_log_value,
                         log_step_value, reduce_flag, num_banks, exp_log_type, binning_parameters,
                         mask_list, roi_list, output_dir, dry_run, vanadium, iparm_file_name, save_to_nexus):
        """
        chop data by log value.
        Note: always save the chopped NeXus
        :param run_number:
        :param start_time:
        :param stop_time:
        :param log_name:
        :param min_log_value:
        :param max_log_value:
        :param log_step_value:
        :param reduce_flag:
        :param output_dir:
        :param dry_run:
        :return:
        """
        # check inputs
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_file_name(output_dir, True, True, True, 'Output directory')

        # dry run: return input options
        if dry_run:
            outputs = 'Slice IPTS-{0} Run {1} by log {2}  with ({3}, {4}, {5}) ' \
                      'within wall time ({6}, {7})'.format(self._iptsNumber, run_number, log_name,
                                                           min_log_value, log_step_value, max_log_value,
                                                           start_time, stop_time)
            if reduce_flag:
                outputs += '\n\tand reduce (to GSAS) '
            else:
                outputs += '\n\tand save to NeXus files '
            outputs += 'to directory %s' % output_dir

            if not os.access(output_dir, os.W_OK):
                outputs += '\n[WARNING] Output directory %s is not writable!' % output_dir
            return True, outputs
        # END-IF (dry run)

        # generate data slicer by log value
        status, ret_obj = self._controller.generate_data_slicer_by_log(run_number, start_time, stop_time,
                                                                       log_name, min_log_value, log_step_value,
                                                                       max_log_value)
        if not status:
            error_msg = str(ret_obj)
            return False, 'Unable to generate data slicer by time due to %s.' % error_msg
        else:
            slicer_key = ret_obj

        # chop and reduce
        print ('[DB...BAT] user_bin_parameters = {}  ... type = {}'.format(binning_parameters, type(binning_parameters)))
        status, message = self._controller.project.chop_run(run_number, slicer_key, reduce_flag=reduce_flag,
                                                            vanadium=vanadium, save_chopped_nexus=save_to_nexus,
                                                            output_dir=output_dir,
                                                            number_banks=num_banks,
                                                            tof_correction=False,
                                                            output_directory=output_dir,
                                                            user_bin_parameter=binning_parameters,
                                                            roi_list=roi_list,
                                                            mask_list=mask_list,
                                                            nexus_file_name=self._raw_nexus_file_name,
                                                            gsas_iparam_name=iparm_file_name)

        return status, message

    def chop_data_by_time(self, run_number, start_time, stop_time, time_interval, reduce_flag, vanadium,
                          output_dir, dry_run, chop_loadframe_log, chop_furnace_log, roi_list,
                          mask_list, num_banks, binning_parameters, save_to_nexus, iparm_file_name):
        """
        Chop data by time interval
        :param run_number:
        :param start_time:
        :param stop_time:
        :param time_interval:
        :param reduce_flag: flag to reduce the data afterwards
        :param vanadium: vanadium run number for normalization. None for no normalization;
        :param output_dir:
        :param dry_run:
        :param chop_loadframe_log:
        :param chop_furnace_log:
        :param roi_list: list (region of interest files)
        :param mask_list: list (mask files)
        :param binning_parameters: binning parameters
        :return:
        """
        # check inputs
        if self._raw_nexus_file_name is None:
            datatypeutility.check_int_variable('Run number', run_number, (1, None))
        else:
            datatypeutility.check_file_name(self._raw_nexus_file_name, check_exist=True,
                                            check_writable=False, is_dir=False, note='Event Nexus file')
            run_number = 0

        datatypeutility.check_file_name(output_dir, check_exist=True, check_writable=True,
                                        is_dir=True, note='Output directory')

        # dry run: return input options
        if dry_run:
            outputs = 'Slice IPTS-%d Run %d by time with (%s, %s, %s) ' % (self._iptsNumber, run_number,
                                                                           str(start_time), str(time_interval),
                                                                           str(stop_time))
            if reduce_flag:
                outputs += 'and reduce (to GSAS) '
            else:
                outputs += 'and save to NeXus files '
            outputs += 'to directory %s' % output_dir

            if not os.access(output_dir, os.W_OK):
                outputs += '\n[WARNING] Output directory %s is not writable!' % output_dir

            return True, outputs
        # END-IF (dry run)

        # generate data slicer
        status, slicer_key = self._controller.gen_data_slicer_by_time(run_number, start_time, stop_time,
                                                                      time_interval,
                                                                      raw_nexus_name=self._raw_nexus_file_name)
        if not status:
            error_msg = str(slicer_key)
            return False, 'Unable to generate data slicer by time due to %s.' % error_msg

        # chop and reduce
        if chop_loadframe_log:
            exp_log_type = 'loadframe'
        elif chop_furnace_log:
            exp_log_type = 'furnace'
        else:
            exp_log_type = None

        # chop
        status, message = self._controller.project.chop_run(run_number, slicer_key,
                                                            reduce_flag=reduce_flag,
                                                            vanadium=vanadium, save_chopped_nexus=save_to_nexus,
                                                            number_banks=num_banks,
                                                            tof_correction=False,
                                                            output_directory=output_dir,
                                                            user_bin_parameter=binning_parameters,
                                                            roi_list=roi_list,
                                                            mask_list=mask_list,
                                                            nexus_file_name=self._raw_nexus_file_name,
                                                            gsas_iparm_file=iparm_file_name)

        return status, message

    def chop_data_overlap_time_period(self, run_number, start_time, stop_time, time_interval, overlap_time_interval,
                                      reduce_flag, vanadium, output_dir, dry_run, chop_loadframe_log, chop_furnace_log,
                                      roi_list, mask_list, num_banks, binning_parameters,
                                      save_to_nexus, iparm_file_name):
        """
        Chop data by time interval
        :param run_number:
        :param start_time:
        :param stop_time:
        :param time_interval:
        :param reduce_flag: flag to reduce the data afterwards
        :param vanadium: vanadium run number for normalization. None for no normalization;
        :param output_dir:
        :param dry_run:
        :param chop_loadframe_log:
        :param chop_furnace_log:
        :return:
        """
        # check inputs
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        datatypeutility.check_file_name(output_dir, True, True, is_dir=True, note='Output directory')

        # dry run: return input options
        if dry_run:
            outputs = 'Slice IPTS-{0} Run {1} by time with ({2}, {3}, {4}) and dt = {5}' \
                      ''.format(self._iptsNumber, run_number, start_time, time_interval, stop_time, overlap_time_interval)
            if reduce_flag:
                outputs += 'and reduce (to GSAS) '
            else:
                outputs += 'and save to NeXus files '
            outputs += 'to directory %s' % output_dir

            if not os.access(output_dir, os.W_OK):
                outputs += '\n[WARNING] Output directory %s is not writable!' % output_dir

            return True, outputs
        # END-IF (dry run)

        # generate data slicer
        # get chopper
        chopper = self._controller.project.get_chopper(run_number)
        status, slice_key_list = chopper.set_overlap_time_slicer(start_time, stop_time, time_interval,
                                                                 overlap_time_interval)

        if not status:
            error_msg = slice_key_list
            return False, error_msg

        # chop
        for i_slice, slice_key in enumerate(slice_key_list):
            status, message = self._controller.project.chop_run(run_number, slice_key,
                                                                reduce_flag=reduce_flag,
                                                                vanadium=vanadium, save_chopped_nexus=save_to_nexus,
                                                                number_banks=num_banks,
                                                                tof_correction=False,
                                                                output_directory=output_dir,
                                                                user_bin_parameter=binning_parameters,
                                                                roi_list=roi_list,
                                                                mask_list=mask_list,
                                                                nexus_file_name=self._raw_nexus_file_name,
                                                                gsas_iparm_file=iparm_file_name,
                                                                overlap_mode=False,
                                                                gda_start=i_slice)

            print ('[DB...BAT] Processed: {} '.format(slice_key))

            if not status:
                return False, message
        # END-FOR

        return True, 'DT is implemented but not efficient'

    def chop_data_manually(self, run_number, slicer_list, reduce_flag, vanadium, output_dir, epoch_time, dry_run,
                           chop_loadframe_log, chop_furnace_log,roi_list, mask_list,  num_banks,
                           binning_parameters,  save_to_nexus, iparm_file_name):
        """
        chop and/or reduce data with arbitrary slicers
        :param run_number:
        :param slicer_list:
        :param reduce_flag:
        :param vanadium: vanadium run number for normalization. None for no normalization;
        :param output_dir:
        :param epoch_time:
        :param dry_run:
        :param chop_loadframe_log:
        :param chop_furnace_log:
        :return:
        """
        # check inputs
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            '' % (str(run_number), type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.' % (str(output_dir), type(output_dir))

        # sort slice list
        slicer_list = self.sort_slice_list(slicer_list)

        # dry run: return input options
        if dry_run:
            outputs = 'Slice IPTS-%d Run %d by user-specified slicers ' % (self._iptsNumber, run_number)
            for slicer in slicer_list:
                outputs += '{0:.10f}, {1:.10f},\n'.format(slicer[0], slicer[1])
            if reduce_flag:
                outputs += 'and reduce (to GSAS) '
            else:
                outputs += 'and save to NeXus files '
            outputs += 'to directory %s' % output_dir

            if not os.access(output_dir, os.W_OK):
                outputs += '\n[WARNING] Output directory %s is not writable!' % output_dir

            return True, outputs
        # END-IF (dry run)

        # generate data slicer
        status, slicer_key = self._controller.gen_data_slice_manual(run_number,
                                                                    relative_time=not epoch_time,
                                                                    time_segment_list=slicer_list,
                                                                    slice_tag=None)

        if not status:
            error_msg = str(slicer_key)
            return False, 'Unable to generate data slicer by time due to %s.' % error_msg

        # chop and reduce
        status, message = self._controller.project.chop_run(run_number, slicer_key,
                                                            reduce_flag=reduce_flag,
                                                            vanadium=vanadium, save_chopped_nexus=save_to_nexus,
                                                            number_banks=num_banks,
                                                            tof_correction=False,
                                                            output_directory=output_dir,
                                                            user_bin_parameter=binning_parameters,
                                                            roi_list=roi_list,
                                                            mask_list=mask_list,
                                                            nexus_file_name=self._raw_nexus_file_name,
                                                            gsas_iparm_file=iparm_file_name)

        return status, message

    def _is_dry_run(self):
        """
        check about DRYRUN
        :return:
        """
        try:
            if 'DRYRUN' in self._commandArgsDict and int(self._commandArgsDict['DRYRUN']) == 1:
                # dry run
                is_dry_run = True
            else:
                is_dry_run = False
        except ValueError as run_err:
            raise RuntimeError('DRYRUN value {} cannot be recognized due to {}.' \
                               ''.format(self._commandArgsDict['DRYRUN'], run_err))

        return is_dry_run

    def _get_chop_log_setup(self):
        """ Get LOADFRAME or FURNACE information
        :return:
        """
        # chopping method: by constant time or input
        # how to deal with sample logs
        if 'LOADFRAME' in self._commandArgsDict:
            chop_load_frame = True
        else:
            chop_load_frame = False
        if 'FURNACE' in self._commandArgsDict:
            chop_furnace_log = True
        else:
            chop_furnace_log = False
        if chop_furnace_log and chop_load_frame:
            raise RuntimeError('LOADFRAME and FURNACE cannot be chosen simultaneously.')

        return chop_load_frame, chop_furnace_log

    def _get_mask_or_roi(self):
        """
        Get mask or ROI files
        :return:
        """
        # region of interest or mask file
        if 'ROI' in self._commandArgsDict:
            roi_file_names = self.get_argument_as_list('ROI', str)
        else:
            roi_file_names = list()
        if 'MASK' in self._commandArgsDict:
            mask_file_names = self.get_argument_as_list('MASK', str)
        else:
            mask_file_names = list()

        if len(roi_file_names) > 0 and len(mask_file_names) > 0:
            raise RuntimeError('It is not allowed to specify ROI and Mask simultaneously.')

        return roi_file_names, mask_file_names

    def _get_van_run(self):
        """
        get vanadium run number for normalization and GSAS IPARM
        :return:
        """
        # vanadium run
        if 'RUNV' in self._commandArgsDict:
            try:
                van_run_number = int(self._commandArgsDict['RUNV'])
            except ValueError:
                raise RuntimeError('RUNV value {} cannot be converted to integer'
                                   ''.format(self._commandArgsDict['RUNV']))

        else:
            van_run_number = None

        return van_run_number

    def _get_gsas_iparm_name(self):
        """ Get the GSAS IPARM file name or default written to GSAS file
        :return:
        """
        # GSAS iparam
        if 'IPARM' in self._commandArgsDict:
            iparm_name = self._commandArgsDict['IPARM']
        else:
            # default
            iparm_name = 'vulcan.prm'

        return iparm_name

    def _process_output_directory(self):
        """
        process output directory
        :return:
        """
        if 'OUTPUT' in self._commandArgsDict and 'BINFOLDER' in self._commandArgsDict:
            raise RuntimeError('OUTPUT and BINFOLER cannot be used simultaneously')
        elif 'OUTPUT' in self._commandArgsDict:
            output_dir = str(self._commandArgsDict['OUTPUT'])
        elif 'BINFOLDER' in self._commandArgsDict:
            output_dir = str(self._commandArgsDict['BINFOLDER'])
        else:
            output_dir = None
        # END-IF-ELSE

        # create output dir
        if output_dir:
            if os.path.exists(output_dir) and not os.access(output_dir, os.W_OK):
                raise RuntimeError('Current user has no writing permit to output directory {}'.format(output_dir))
            elif not os.path.exists(output_dir):
                try:
                    os.mkdir(output_dir)
                except (OSError, IOError) as dir_err:
                    raise RuntimeError('Unable to create output directory {} due to {}'.format(output_dir, dir_err))
            # END-IF-ELSE
        # END-IF-ELSE

        return output_dir

    def _process_chopping_setup(self):
        """ Process the various type of chopping setup
        :return: 4-tuple: dict, start time, stop time, pulse time
        """
        # start and stop time
        if 'STARTTIME' in self._commandArgsDict:
            start_time = convert_string_to(self._commandArgsDict['STARTTIME'], float)
        else:
            start_time = 0
        if 'STOPTIME' in self._commandArgsDict:
            stop_time = convert_string_to(self._commandArgsDict['STOPTIME'], float)
        else:
            stop_time = None

        # extra chopping option
        if 'PULSETIME' in self._commandArgsDict:
            pulse_time = convert_string_to(self._commandArgsDict['PULSETIME'], int)
        else:
            pulse_time = 1

        chop_option_dict = dict()
        if 'DBIN' in self._commandArgsDict:
            time_step = convert_string_to(self._commandArgsDict['DBIN'], float)
            chop_option_dict['DBIN'] = time_step

        if 'DT' in self._commandArgsDict:
            # DT must be checked after DBIN
            if 'DBIN' not in chop_option_dict:
                raise RuntimeError('DT must be used with DBIN specified')
            # set DT as a tuple from DBIN, DT and remove DBIN entry in output dictionary
            chop_over_lap_period = convert_string_to(self._commandArgsDict['DT'], float)
            chop_option_dict['DT'] = (chop_option_dict['DBIN'], chop_over_lap_period)
            del chop_option_dict['DBIN']

        if 'PICKDATA' in self._commandArgsDict:
            user_slice_file = self._commandArgsDict['PICKDATA']
            chop_option_dict['PICKDATA'] = user_slice_file

        # check inputs' validity: at most 1 chopping option can be used
        if len(chop_option_dict) > 1:
            err_msg = 'It is not allow to use '
            for option in chop_option_dict.keys():
                err_msg += '{}, '.format(option)
            err_msg += ' simultaneously.  At most one of DBIN, PICKDATA and LOG canot be used'
            raise RuntimeError(err_msg)

        return chop_option_dict, start_time, stop_time, pulse_time

    def _process_vulcan_runs(self):
        """
        Process RUNS and RUNE
        :return:
        """
        # run numbers
        if self._iptsNumber:
            # IPTS/run number
            if 'RUNS' in self._commandArgsDict:
                # get RUNS/RUNE from arguments
                run_start = convert_string_to(self._commandArgsDict['RUNS'], int)
                if 'RUNE' in self._commandArgsDict:
                    run_end = convert_string_to(self._commandArgsDict['RUNE'], int)
                else:
                    run_end = run_start
                self._runNumberList = range(run_start, run_end + 1)
            elif len(self._commandArgsDict) > 0:
                # from previously stored value
                run_start = convert_string_to(self._commandArgsDict[0], int)
                run_end = convert_string_to(self._commandArgsDict[-1], int)
            else:
                # not properly set up
                raise RuntimeError('CHOP command requires input of argument RUNS or previously stored Run number')
            # END-IF

            # check run start and run end range
            if run_start > run_end:
                raise RuntimeError('Run start {} must be less or equal to run end {}'.format(run_start, run_end))

            # locate the runs and add the reduction project
            run_number_list = range(run_start, run_end + 1)
            archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                                 run_number_list)
            if len(error_message) > 0:
                print '[DB...BAT] Error archive key: ', archive_key
                return False, error_message
            run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
            self._controller.add_runs_to_project(run_info_list)
        else:
            # NeXus file
            run_start = None
            run_end = None
        # END-IF

        return run_start, run_end

    def _process_binning_setup(self):
        """ Processing diffraction focus and save to GSAS related setup
        :return: bool (bin chopped data), int (number of banks)
        """
        if 'BIN' in self._commandArgsDict:
            bin_run = convert_string_to(self._commandArgsDict['BIN'], int) > 0
        else:
            # default is True
            bin_run = True

        # number of banks in output GSAS file
        if 'BANKS' in self._commandArgsDict:
            num_banks = convert_string_to(self._commandArgsDict['BANKS'], int)
            if num_banks <= 0:
                raise RuntimeError('Banks number cannot be zero or less')
        else:
            # default is 3
            num_banks = 3

        return bin_run, num_banks

    def exec_cmd(self):
        """
        Execute input command (override)
        :except: RuntimeError for bad command
        :return: 2-tuple, status, error message
        """
        time0 = time.time()

        # Go through all the arguments
        if 'HELP' in self._commandArgsDict:
            # pop out the window
            return True, 'pop'

        if 'NEXUS' in self._commandArgsDict:
            # set NeXus file name other other IPTS/RUN NUMBER
            self.set_raw_nexus()
        else:
            # parse arguments
            self.set_ipts()

        # parse the scope of runs
        run_start, run_end = self._process_vulcan_runs()

        try:
            is_dry_run = self._is_dry_run()

            # chopping options
            chop_option_dict, start_time, stop_time, pulse_time = self._process_chopping_setup()

            # ROI or Mask
            roi_file_names, mask_file_names = self._get_mask_or_roi()

            # GSAS binning section
            output_to_gsas, num_banks = self._process_binning_setup()
            # binning parameters
            use_default_binning, binning_parameters = self.parse_binning()
            # vanadium calibration
            van_run_number = self._get_van_run()
            iparm_name = self._get_gsas_iparm_name()

            # extra sample log information
            chop_load_frame, chop_furnace_log = self._get_chop_log_setup()

            # output
            output_dir = self._process_output_directory()

            if 'SAVECHOPPED2NEXUS' in self._commandArgsDict:
                save_to_nexus = convert_string_to(self._commandArgsDict['VDRIVEBIN'], int) > 0
            else:
                # default to False
                save_to_nexus = False
            # END-IF
        except RuntimeError as run_err:
            return False, 'CHOP failed: {}'.format(run_err)

        # record time before chopping
        time1 = time.time()
        duration_process_command = time1 - time0

        # do chopping
        sum_msg = 'CHOP command preparation: {} seconds\n'.format(duration_process_command)
        final_success = True

        # set run numbers
        if self._iptsNumber:
            run_number_list = range(run_start, run_end + 1)
            event_nexus_file = None
        else:
            run_number_list = [-1]
        # END-IF

        # chop
        for run_number in run_number_list:
            # output directory
            if output_dir is None:
                try:
                    output_dir = self.create_default_chop_output_dir(run_number)
                except (OSError, IOError) as os_err:
                    return False, 'Failed to create default chopping directory for run {} due to {}' \
                                  ''.format(run_number, os_err)
            # END-IF

            if 'DBIN' in chop_option_dict:
                # binning by constant time step
                time_step = chop_option_dict['DBIN']

                # chop by time and reduce
                status, message = self.chop_data_by_time(run_number=run_number,
                                                         start_time=start_time, stop_time=stop_time,
                                                         time_interval=time_step,
                                                         reduce_flag=output_dir, vanadium=van_run_number,
                                                         num_banks=num_banks, iparm_file_name=iparm_name,
                                                         binning_parameters=binning_parameters,
                                                         save_to_nexus=save_to_nexus,
                                                         output_dir=output_dir,
                                                         dry_run=is_dry_run,
                                                         chop_loadframe_log=chop_load_frame,
                                                         chop_furnace_log=chop_furnace_log,
                                                         roi_list=roi_file_names, mask_list=mask_file_names)
            elif 'DT' in chop_option_dict:
                # chopping with OVERLAPPED period
                time_step, overlap_period = chop_option_dict['DT']

                # TEST - This is JUST implemented and SHALL be tested
                status, message = self.chop_data_overlap_time_period(run_number=run_number,
                                                                     start_time=None,
                                                                     stop_time=None,
                                                                     time_interval=time_step,
                                                                     overlap_time_interval=overlap_period,
                                                                     reduce_flag=output_to_gsas,
                                                                     vanadium=van_run_number,
                                                                     output_dir=output_dir,
                                                                     dry_run=is_dry_run,
                                                                     chop_loadframe_log=chop_load_frame,
                                                                     chop_furnace_log=chop_furnace_log,
                                                                     roi_list=roi_file_names,
                                                                     mask_list=mask_file_names,
                                                                     num_banks=num_banks,
                                                                     binning_parameters=binning_parameters,
                                                                     save_to_nexus=save_to_nexus,
                                                                     iparm_file_name=iparm_name)

            elif 'PICKDATA' in chop_option_dict:
                # chop by user specified time splitters
                # TEST - Need to wait for Mantid
                try:
                    # TODO FIXME - NIGHT
                    """
                      File "/home/wzz/Projects/PyVDrive/build/lib.linux-x86_64-2.7/pyvdrive/interface/vdrive_commands/chop.py", line 715, in exec_cmd
                      slicer_list = self.parse_pick_data(user_slice_file)
                      NameError: global name 'user_slice_file' is not defined
                    """
                    user_slice_file = chop_option_dict['PICKDATA']
                    slicer_list = self.parse_pick_data(user_slice_file)

                    print ('[DB...BAT] slice list: {}'.format(slicer_list))

                    status, message = self.chop_data_manually(run_number=run_number,
                                                              slicer_list=slicer_list,
                                                              reduce_flag=output_to_gsas,
                                                              vanadium=van_run_number,
                                                              output_dir=output_dir,
                                                              dry_run=is_dry_run,
                                                              epoch_time=(pulse_time == 1),
                                                              chop_loadframe_log=chop_load_frame,
                                                              chop_furnace_log=chop_furnace_log,
                                                              num_banks=num_banks, iparm_file_name=iparm_name,
                                                              binning_parameters=binning_parameters,
                                                              save_to_nexus=save_to_nexus,
                                                              roi_list=roi_file_names, mask_list=mask_file_names)
                except RuntimeError as run_err:
                    return False, 'Failed to chop: {0}'.format(run_err)

            elif 'LOG' in chop_option_dict:
                # chop by log value
                # FIXME/TODO/ISSUE/FUTURE - shall we implement this?
                status, message = self.chop_data_by_log(run_number=run_number,
                                                        start_time=None,
                                                        stop_time=None,
                                                        log_name=log_name,
                                                        log_value_stepl=delta_log_value,
                                                        reduce_flag=output_to_gsas,
                                                        output_dir=output_dir,
                                                        dry_run=is_dry_run)

            else:
                # do nothing but launch log window
                status = True
                message = 'pop'
            # END-IF-ELSE

            # chop time
            time2 = time.time()
            duration_chop = time2 - time1
            time1 = time.time()
            final_success = final_success and status
            sum_msg += 'Run {}: duration = {}: {}\n'.format(run_number, duration_chop, message)
        # END-FOR (run_number)

        # TODO/THINK/ISSUE/55 - shall a signal be emit???
        self.reduceSignal.emit(sum_msg)

        return final_success, sum_msg

    def create_default_chop_output_dir(self, run_number):
        """
        find out the default output directory for the run from /SNS/VULCAN/IPTS-???/shared/
        and create it!
        :exception: OSError if there is no permit to create the directory
        :param run_number:
        :return: directory name
        """
        # check root
        ipts_root_dir = '/SNS/VULCAN/IPTS-%d/shared' % self._iptsNumber
        if not os.access(ipts_root_dir, os.W_OK):
            raise OSError('User has no writing permission to ITPS shared directory for chopped data %s.'
                          '' % ipts_root_dir)

        # check and create directory ../../ChoppedData/
        # TODO/FIXME/ISSUE/Ke: ChoppedData or binned_data
        # chop_dir = os.path.join(ipts_root_dir, 'ChoppedData')
        chop_dir = os.path.join(ipts_root_dir, 'binned_data')
        if os.path.exists(chop_dir):
            if not os.access(chop_dir, os.W_OK):
                raise OSError('User has no writing permission to directory %s for chopped data.'
                              '' % chop_dir)
        else:
            os.mkdir(chop_dir)
            os.chmod(chop_dir, 0777)

        # create the Chopped data for the run
        default_dir = os.path.join(chop_dir, '%d' % run_number)
        if os.path.exists(default_dir):
            if not os.access(default_dir, os.W_OK):
                raise OSError('User has no writing permission to previously-generated %s for chopped data.'
                              '' % default_dir)
        else:
            os.mkdir(default_dir)
            os.chmod(default_dir, 0777)

        return default_dir

    def get_help(self):
        """
        override base class
        :return:
        """
        help_str = 'Chop runs\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        help_str += 'Examples:\n'
        help_str += '1. Chop run 96450 by 60 seconds:\n'
        help_str += ' > CHOP, IPTS=14094, RUNS=96450, dbin=60,loadframe=1,bin=1,DRYRUN=1\n'
        help_str += '2. Chop arbitrary NeXus file with user speficied starting and stopping time.:\n'
        help_str += 'chop, nexus=\'/SNS/VULCAN/IPTS-19577/nexus/VULCAN_152782.nxs.h5\', dbin=10, bin=1, output=/tmp/, '
        help_str += 'StartTime=0, StopTime=3600\n'

        return help_str

    @staticmethod
    def parse_pick_data(file_name):
        """ Parse an ascii file for slicer setup
        Format:
          start_time0  stop_time0
          start_time1  stop_time1
          ...          ...
        :exception: RuntimeError for unabling to import the file
        :param file_name:
        :return:
        """
        # check file existence
        assert isinstance(file_name, str), 'File name {0} must be a string but not a {1}.' \
                                           ''.format(file_name, type(file_name))
        try:
            in_file = open(file_name, 'r')
            lines = in_file.readlines()
            in_file.close()
        except IOError as io_err:
            raise RuntimeError('Unable to open file {0} due to {1}.'.format(file_name, io_err))
        except OSError as os_err:
            raise RuntimeError('Unable to import file {0} due to {1}.'.format(file_name, os_err))

        split_list = list()
        for raw_line in lines:
            # clean the line
            line = raw_line.strip()
            if len(line) == 0:
                continue

            # split
            terms = line.split()
            if len(terms) < 2:
                continue

            try:
                start_time = float(terms[0])
                stop_time = float(terms[1])
                split_list.append((start_time, stop_time))
            except ValueError:
                # ignore if the line does not contain 2 floats
                continue
        # END-FOR

        return split_list

    @staticmethod
    def sort_slice_list(slicer_list):
        """
        sort slice list
        :param slicer_list:
        :return:
        """
        assert isinstance(slicer_list, list), 'Slicer list {0} must be a list but not a {1}.' \
                                              ''.format(slicer_list, type(slicer_list))

        slicer_list = sorted(slicer_list)

        return slicer_list


"""
CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
1. dbin is the chop step size in seconds;
2. loadframe, is set when VULCAN loadframe is used for continuous loading experiment;
3. bin=1, for binning data to GSAS file after slicing the data in time. GSAS data are stored at
    /SNS/VULCAN/IPTS-1000/shared/binned_data/2000/ along with the chopped sample environment files
    2000sampleenv_chopped_start(mean or end).txt.
4. loadframe=1: furnace=1, or generic=1, when using VULCAN standard sample environment DAQ
    for the furnaces or others. For a customized sample environment file name,
    use SampleEnv='your sample file name.txt' (the customized sample environment file is stored in
    /SNS/VULCAN/IPTS-1000/shared/logs).
5. If no sample environment is chosen or justchop=1 keyword is selected,
    no sample environment data synchronization will be executed.


Current Example:
CHOP,IPTS=13183,RUNS=68607,PICKDATA="/SNS/VULCAN/IPTS-13183/SHARED/VARIABLECHOP_SERRATION_2ND SERIES_4.TXT",BIN=1,LOADFRAME=1,PULSETIME=1

PICKDATA FILE
801266555.006	801266615.006
801266615.006	801266675.006
801266675.006	801266735.006
801266735.006	801266795.006
801266795.006	801266855.006
801266875.610	801266898.41
801266898.41	801266921.741
801266921.741	801266945.073
801266945.073	801266968.404
801266972.223	801266995.002
801266995.002	801267016.939
801267016.939	801267038.877
801267038.877	801267060.814
801267065.202	801267087.998
801267087.998	801267111.666
801267111.666	801267135.335
801267135.335	801267159.003
801267163.796	801267186.596
801267186.596	801267217.133
801267217.133	801267247.669
801267247.669	801267278.206
801267280.60	801267301.000
801267301.000	801267326.873
801267326.873	801267352.745
801267352.745	801267378.618
801267379.81	801267402.607
801267402.607	801267428.407
801267428.407	801267454.208
801267454.208	801267480.008
801267480.008	801267505.008
801267505.008	801267530.008

"""



