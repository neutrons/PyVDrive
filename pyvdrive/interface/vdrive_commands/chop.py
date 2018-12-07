"""
Implement VDRIVE command VCHOP
"""
import os
import time
from procss_vcommand import VDriveCommand
from pyvdrive.lib import datatypeutility

class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    # TODO/ISSUE/NOWNOW - Implement DT and RUNV
    SupportedArgs = ['IPTS', 'HELP', 'RUNS', 'RUNE', 'DBIN', 'LOADFRAME', 'FURNACE', 'BIN', 'PICKDATA', 'OUTPUT',
                     'DRYRUN', 'PULSETIME', 'DT', 'RUNV', 'INFO', 'ROI', 'MASK', 'NEXUS', 'STARTTIME', 'STOPTIME',
                     'VDRIVEBIN', 'NUMBANKS', 'SAVECHOPPED2NEXUS']

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
        'OUTPUT': 'If specified, then the chopped files will be saved to the directory. Otherwise, these files '
                  'will be saved to /SNS/VULCAN/IPTS-????/shared.',
        'DRYRUN': 'If equal to 1, then it is a dry run to check input and output.',
        'HELP': 'the Log Picker Window will be launched and set up with given RUN number.\n',
        'DT': 'the period between two adjacent time segments',
        'STARTTIME': 'The starting time of the first slicer.  Default is the run start',
        'STOPTIME': 'The stopping time of the last slicer. Default is the run stop',
        'RUNV': 'vanadium run number',
        'ROI': 'Files for Mantid made region of interest file in XML format',
        'MASK': 'Files for Mantid made mask file in XML format',
        'VDRIVEBIN': 'If equal to 1, using VDRIVE GSAS binning template to re-bin and output to GSAS.  Default is 3',
        'NUMBANKS': 'Number of banks in the output GSAS file',
        'SAVECHOPPED2NEXUS': 'If equal to 1, then the chopped and reduced workspace will be save to a NeXus file. '
                             'Default is 0 (as False)'
    }

    def __init__(self, controller, command_args, ipts_number=None, run_number_list=None):
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

        # set default
        if ipts_number is not None and isinstance(ipts_number, int) and ipts_number > 0:
            self._iptsNumber = ipts_number
        if isinstance(run_number_list, list) and len(run_number_list) > 0:
            self._runNumberList = run_number_list[:]
        
        return

    def chop_data_by_log(self, run_number, start_time, stop_time, log_name, min_log_value, max_log_value,
                         log_step_value, reduce_flag, output_dir, dry_run):
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
        # TEST/ISSUE/59 - Test
        # check inputs
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.'.format(output_dir, type(output_dir))

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
        status, message = self._controller.slice_data(run_number, slicer_key, reduce_data=reduce_flag,
                                                      save_chopped_nexus=True,
                                                      output_dir=output_dir)

        return status, message

    def chop_data_by_time(self, run_number, start_time, stop_time, time_interval, reduce_flag, vanadium,
                          output_dir, dry_run, chop_loadframe_log, chop_furnace_log, roi_list,
                          mask_list, use_idl_bin, num_banks, save_to_nexus):
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
        :param use_idl_bin: use VDRIVE GSAS binning as a template
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
        status, message = self._controller.slice_data(run_number, slicer_key, reduce_data=reduce_flag,
                                                      vanadium=vanadium, save_chopped_nexus=save_to_nexus,
                                                      output_dir=output_dir,
                                                      number_banks=num_banks,
                                                      export_log_type=exp_log_type,
                                                      user_bin_parameter=None,
                                                      use_idl_bin=use_idl_bin,
                                                      roi_list=roi_list,
                                                      mask_list=mask_list,
                                                      raw_nexus_name=self._raw_nexus_file_name)

        return status, message

    def chop_data_by_time_period(self, run_number, start_time, stop_time, time_interval, chop_period, reduce_flag,
                                 vanadium, output_dir, dry_run, chop_loadframe_log, chop_furnace_log):
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
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            '' % (str(run_number), type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.' % (str(output_dir), type(output_dir))

        # dry run: return input options
        if dry_run:
            outputs = 'Slice IPTS-{0} Run {1} by time with ({2}, {3}, {4}) and dt = {5}' \
                      ''.format(self._iptsNumber, run_number, start_time, time_interval, stop_time, chop_period)
            if reduce_flag:
                outputs += 'and reduce (to GSAS) '
            else:
                outputs += 'and save to NeXus files '
            outputs += 'to directory %s' % output_dir

            if not os.access(output_dir, os.W_OK):
                outputs += '\n[WARNING] Output directory %s is not writable!' % output_dir

            return True, outputs
        # END-IF (dry run)

        # chop and reduce
        if chop_loadframe_log:
            exp_log_type = 'loadframe'
        elif chop_furnace_log:
            exp_log_type = 'furnace'
        else:
            exp_log_type = None

        # generate data slicer
        status, ret_obj = self._controller.gen_data_slicer_by_time(run_number, start_time, stop_time,
                                                                      time_interval)

        # TODO TODO - 20180727 - Is it called for DT????
        raise RuntimeError('Chop No Chop????')
        if status:
            slicer_key = ret_obj
        else:
            return False, 'Unable to generate data slicer by time due to {0}.'.format(ret_obj)

        return False, 'DT option is not implemented. Contact developer!'
        # status, message = self._controller.slice_data_segment_period(run_number, slicer_key,
        #                                                              chop_period,
        #                                                              reduce_data=reduce_flag,
        #                                                              vanadium=vanadium, save_chopped_nexus=True,
        #                                                              output_dir=output_dir,
        #                                                              export_log_type=exp_log_type)
        #
        # return status, message

    def chop_data_manually(self, run_number, slicer_list, reduce_flag, vanadium, output_dir, epoch_time, dry_run,
                           chop_loadframe_log, chop_furnace_log):
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
        if chop_loadframe_log:
            exp_log_type = 'loadframe'
        elif chop_furnace_log:
            exp_log_type = 'furnace'
        else:
            exp_log_type = None
        status, message = self._controller.slice_data(run_number, slicer_key, reduce_data=reduce_flag,
                                                      vanadium=None,
                                                      save_chopped_nexus=True, output_dir=output_dir,
                                                      export_log_type=exp_log_type)

        return status, message

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
        # run numbers
        if self._iptsNumber:
            # IPTS/run number
            if 'RUNS' in self._commandArgsDict:
                # get RUNS/RUNE from arguments
                run_start = int(self._commandArgsDict['RUNS'])
                if 'RUNE' in self._commandArgsDict:
                    run_end = int(self._commandArgsDict['RUNE'])
                else:
                    run_end = run_start
                self._runNumberList = range(run_start, run_end + 1)
            elif len(self._commandArgsDict) > 0:
                # from previously stored value
                run_start = self._commandArgsDict[0]
                run_end = self._commandArgsDict[-1]
                assert isinstance(run_start, int) and isinstance(run_end, int) and run_start <= run_end, \
                    'Run start %s (%s) and run end %s (%s) must be integers and run start <= run end' % (
                        str(run_start), str(type(run_start)), str(run_end), str(type(run_end))
                    )
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

        if 'INFO' in self._commandArgsDict:
            # get the chopping-help information
            # TODO/ISSUE/33/ - organize some information
            pass

        try:
            if 'DRYRUN' in self._commandArgsDict and int(self._commandArgsDict['DRYRUN']) == 1:
                # dry run
                is_dry_run = True
            else:
                is_dry_run = False
        except ValueError as run_err:
            return False, 'DRYRUN value {} cannot be recognized.'.format(self._commandArgsDict['DRYRUN'])

        # vanadium run
        if 'RUNV' in self._commandArgsDict:
            van_run_number = int(self._commandArgsDict['RUNV'])
        else:
            van_run_number = None

        # chopping method: by constant time or input
        # how to deal with sample logs
        if 'LOADFRAME' in self._commandArgsDict:
            chop_load_frame = True
        else:
            chop_load_frame = False
        if 'Furnace' in self._commandArgsDict:
            chop_furnace_log = True
        else:
            chop_furnace_log = False
        if chop_furnace_log and chop_load_frame:
            return False, 'Only 1 option in LOADFRAME and FURNACE can be chosen.'

        if 'STARTTIME' in self._commandArgsDict:
            start_time = float(self._commandArgsDict['STARTTIME'])
        else:
            start_time = 0
        if 'STOPTIME' in self._commandArgsDict:
            stop_time = float(self._commandArgsDict['STOPTIME'])
        else:
            stop_time = None

        if 'DBIN' in self._commandArgsDict:
            time_step = float(self._commandArgsDict['DBIN'])
        else:
            time_step = None
        if 'DT' in self._commandArgsDict:
            chop_period = float(self._commandArgsDict['DT'])
        else:
            chop_period = None
        if 'PICKDATA' in self._commandArgsDict:
            user_slice_file = self._commandArgsDict['PICKDATA']
        else:
            user_slice_file = False
        if 'PULSETIME' in self._commandArgsDict:
            pulse_time = int(self._commandArgsDict['PULSETIME'])
        else:
            pulse_time = 1

        # region of interest or mask file
        if 'ROI' in self._commandArgsDict:
            roi_file_names = self.get_argument_as_list('ROI', str)
        else:
            roi_file_names = list()
        if 'MASK' in self._commandArgsDict:
            mask_file_names = self.get_argument_as_list('MASK', str)
        else:
            mask_file_names = list()

        # binning parameters
        use_idl_bin = True
        if 'VDRIVEBIN' in self._commandArgsDict:
            try:
                use_idl_bin = int(self._commandArgsDict['VDRIVEBIN']) > 0
            except ValueError:
                return False, 'VDRIVEBIN {} must be an integer '.format(self._commandArgsDict['VDRIVEBIN'])
        else:
            use_idl_bin = True
        # END-OF (VDRIVE-BIN)

        # number of banks in output GSAS file
        num_banks = 3
        if 'NUMBANKS' in self._commandArgsDict:
            try:
                num_banks = int(self._commandArgsDict['VDRIVEBIN'])
                if num_banks <= 0:
                    return False, 'Number of banks ({}) cannot be zero or negative.'.format(num_banks)
            except ValueError:
                return False, 'VDRIVEBIN {} must be an integer '.format(self._commandArgsDict['VDRIVEBIN'])
        # END-OF (NUMBANKS)

        save_to_nexus = False
        if 'SAVECHOPPED2NEXUS' in self._commandArgsDict:
            try:
                save_to_nexus = int(self._commandArgsDict['VDRIVEBIN']) > 0
            except ValueError:
                return False, 'SAVECHOPPED2NEXUS {} must be an integer' \
                              ''.format(self._commandArgsDict['SAVECHOPPED2NEXUS'])
        # END-OF (SAVECHOPPED2NEXUS)

        # check
        if time_step and user_slice_file:
            return False, 'Only 1 option in DBIN and PICKDATA can be chosen.'
        elif time_step is None and not user_slice_file:
            message = 'pop'
        else:
            message = None

        if message == 'pop':
            # no choice, just pop out the window
            return True, 'pop'

        # about output
        # binning to GSAS is by default
        output_to_gsas = True
        if 'BIN' in self._commandArgsDict and int(self._commandArgsDict['BIN']) == 0:
            output_to_gsas = False

        if 'OUTPUT' in self._commandArgsDict:
            # use user defined
            output_dir = str(self._commandArgsDict['OUTPUT'])
        else:
            output_dir = None

        # check inputs' validity
        if chop_period is not None and time_step is None:
            return False, 'Chopping period (DT) = {0}. Under this case, DBIN must be given.'.format(chop_period)

        # record time before chopping
        time1 = time.time()
        duration_process_command = time1 - time0

        # do chopping
        sum_msg = 'CHOP command preparation: {} seconds\n'.format(duration_process_command)
        final_success = True

        if self._iptsNumber:
            # regular
            for run_number in range(run_start, run_end + 1):
                # create default directory
                if output_dir is None:
                    try:
                        output_dir = self.create_default_chop_output_dir(run_number)
                    except OSError as os_err:
                        final_success = False
                        sum_msg += 'Unable to chop and reduce run %d due to %s.' % (run_number, str(os_err))
                        continue

                # chop and optionally reduce
                if chop_period is not None:
                    # chopping with OVERLAPPED period
                    # FIXME - This is NOTE implemented and tested
                    status, message = self.chop_data_by_time_period(run_number=run_number,
                                                                    start_time=None,
                                                                    stop_time=None,
                                                                    time_interval=time_step,
                                                                    chop_period=chop_period,
                                                                    reduce_flag=output_to_gsas,
                                                                    vanadium=van_run_number,
                                                                    output_dir=output_dir,
                                                                    dry_run=is_dry_run,
                                                                    chop_loadframe_log=chop_load_frame,
                                                                    chop_furnace_log=chop_furnace_log)

                elif time_step is not None:
                    # chop by time and reduce
                    status, message = self.chop_data_by_time(run_number=run_number,
                                                             start_time=start_time,
                                                             stop_time=stop_time,
                                                             time_interval=time_step,
                                                             reduce_flag=output_to_gsas,
                                                             vanadium=van_run_number,
                                                             output_dir=output_dir,
                                                             dry_run=is_dry_run,
                                                             chop_loadframe_log=chop_load_frame,
                                                             chop_furnace_log=chop_furnace_log,
                                                             roi_list=roi_file_names,
                                                             mask_list=mask_file_names,
                                                             use_idl_bin=use_idl_bin,
                                                             num_banks=num_banks,
                                                             save_to_nexus=save_to_nexus
                                                             )
                # elif log_name is not None:
                #     # chop by log value
                #     # FIXME/TODO/ISSUE/FUTURE - shall we implement this?
                #     status, message = self.chop_data_by_log(run_number=run_number,
                #                                             start_time=None,
                #                                             stop_time=None,
                #                                             log_name=log_name,
                #                                             log_value_stepl=delta_log_value,
                #                                             reduce_flag=output_to_gsas,
                #                                             output_dir=output_dir,
                #                                             dry_run=is_dry_run)
                elif user_slice_file is not None:
                    # chop by user specified time splitters
                    # TEST - Need to wait for Mantid
                    try:
                        slicer_list = self.parse_pick_data(user_slice_file)
                        status, message = self.chop_data_manually(run_number=run_number,
                                                                  slicer_list=slicer_list,
                                                                  reduce_flag=output_to_gsas,
                                                                  vanadium=van_run_number,
                                                                  output_dir=output_dir,
                                                                  dry_run=is_dry_run,
                                                                  epoch_time=(pulse_time == 1),
                                                                  chop_loadframe_log=chop_load_frame,
                                                                  chop_furnace_log=chop_furnace_log)
                    except RuntimeError as run_err:
                        return False, 'Failed to chop: {0}'.format(run_err)

                else:
                    # do nothing but launch log window
                    status = True
                    message = 'pop'
                    return status, message
                # END-IF-ELSE

                # chop time
                time2 = time.time()
                duration_chop = time2 - time1
                time1 = time.time()

                final_success = final_success and status
                sum_msg += 'Run {}: duration = {}: {}\n'.format(run_number, duration_chop, message)
            # END-FOR (run_number)
        else:
            # NeXus
            if time_step is not None:
                # chop by time and reduce
                final_success, sum_msg = self.chop_data_by_time(run_number=-1,
                                                                start_time=start_time,
                                                                stop_time=stop_time,
                                                                time_interval=time_step,
                                                                reduce_flag=output_to_gsas,
                                                                vanadium=van_run_number,
                                                                output_dir=output_dir,
                                                                dry_run=is_dry_run,
                                                                chop_loadframe_log=chop_load_frame,
                                                                chop_furnace_log=chop_furnace_log,
                                                                roi_list=roi_file_names,
                                                                mask_list=mask_file_names)

            else:
                raise RuntimeError('NeXus file only support chop time by')
        # END-IF-ELSE

        # TODO/THINK/ISSUE/55 - shall a signal be emit???
        # self.reduceSignal.emit(command_args)

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



