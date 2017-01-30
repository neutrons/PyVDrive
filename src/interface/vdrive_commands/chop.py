"""
Implement VDRIVE command VCHOP
"""
import os
from procss_vcommand import VDriveCommand


class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'HELP', 'RUNS', 'RUNE', 'dbin', 'loadframe', 'bin', 'pickdate', 'OUTPUT', 'DRYRUN']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',

        'dbin': 'time step for binning interval',
        'loadframe': 'chop load frame data',
        'bin': 'If bin=1, chopped data will be reduced to GSAS files',

        'DRYRUN': 'If equal to 1, then it is a dry run to check input and output.',
        'HELP': 'the Log Picker Window will be launched and set up with given RUN number.\n'
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
        chop data by log value
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
        # TODO/ISSUE/59 - Test
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
        status, message = self._controller.slice_data(run_number, slicer_key,
                                                      reduce_data=reduce_flag, output_dir=output_dir)

        return status, message

    def chop_data_by_time(self, run_number, start_time, stop_time, time_interval, reduce_flag, output_dir,
                          dry_run):
        """
        Chop data by time interval
        :param run_number:
        :param start_time:
        :param stop_time:
        :param time_interval:
        :param reduce_flag: flag to reduce the data afterwards
        :param output_dir:
        :param dry_run:
        :return:
        """
        # check inputs
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            '' % (str(run_number), type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.' % (str(output_dir), type(output_dir))

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
                                                                      time_interval)
        if not status:
            error_msg = str(slicer_key)
            return False, 'Unable to generate data slicer by time due to %s.' % error_msg

        # chop and reduce
        status, message = self._controller.slice_data(run_number, slicer_key,
                                                      reduce_data=reduce_flag, output_dir=output_dir)

        return status, message

    def exec_cmd(self):
        """
        Execute input command (override)
        :except: RuntimeError for bad command
        :return: 2-tuple, status, error message
        """
        # parse arguments
        self.set_ipts()

        # parse the scope of runs
        # run numbers
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
        else:
            # not properly set up
            raise RuntimeError('CHOP command requires input of argument RUNS or previously stored Run number')
        # END-IF

        # locate the runs and add the reduction project
        run_number_list = range(run_start, run_end+1)
        archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                             run_number_list)
        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.add_runs_to_project(run_info_list)

        # Go through all the arguments
        if 'HELP' in self._commandArgsDict:
            # pop out the window
            return True, 'pop'

        if 'DRYRUN' in self._commandArgsDict and int(self._commandArgsDict['DRYRUN']) == 1:
            # dry run
            is_dry_run = True
        else:
            is_dry_run = False

        # check input parameters
        assert isinstance(run_start, int) and isinstance(run_end, int) and run_start <= run_end, \
            'Run start %s (%s) and run end %s (%s) must be integers and run start <= run end' % (
                str(run_start), str(type(run_start)), str(run_end), str(type(run_end))
            )

        # parse other optional parameters
        if 'dbin' in self._commandArgsDict:
            time_step = float(self._commandArgsDict['dbin'])
        else:
            time_step = None

        if 'loadframe' in self._commandArgsDict:
            use_load_frame = True
        else:
            use_load_frame = False

        if 'bin' in self._commandArgsDict:
            output_to_gsas = True
        else:
            output_to_gsas = False

        if use_load_frame:
            log_name = 'Load Frame'
        else:
            log_name = None

        if 'OUTPUT' in self._commandArgsDict:
            # use user defined
            output_dir = str(self._commandArgsDict['OUTPUT'])
        else:
            output_dir = None

        # do chopping
        sum_msg = ''
        final_success = True
        for run_number in range(run_start, run_end+1):
            # create default directory
            if output_dir is None:
                try:
                    output_dir = self.create_default_chop_output_dir(run_number)
                except OSError as os_err:
                    final_success = False
                    sum_msg += 'Unable to chop and reduce run %d due to %s.' % (run_number, str(os_err))
                    continue

            # chop and optionally reduce
            if time_step is not None:
                # chop by time and reduce
                status, message = self.chop_data_by_time(run_number=run_number,
                                                         start_time=None,
                                                         stop_time=None,
                                                         time_interval=time_step,
                                                         reduce_flag=output_to_gsas,
                                                         output_dir=output_dir,
                                                         dry_run=is_dry_run)
            else:
                # chop by log value
                status, message = self.chop_data_by_log(run_number=run_number,
                                                        start_time=None,
                                                        stop_time=None,
                                                        log_name=log_name,
                                                        log_value_stepl=delta_log_value,
                                                        reduce_flag=output_to_gsas,
                                                        output_dir=output_dir,
                                                        dry_run=is_dry_run)
            # END-IF-ELSE

            final_success = final_success and status
            sum_msg += 'Run %d: %s\n' % (run_number, message)
        # END-FOR (run_number)

        # TODO/THINK/ISSUE/55 - shall a signal be emit???
        # self.reduceSignal.emit(command_args)

        print '[DB...BAT] CHOP Message: ', sum_msg

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
        chop_dir = os.path.join(ipts_root_dir, 'ChoppedData')
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
        help_str += ' > CHOP, IPTS=14094, RUNS=96450, dbin=60,loadframe=1,bin=1,DRYRUN=1\n\n'

        return help_str

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
"""



