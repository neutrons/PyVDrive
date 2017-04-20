"""
Implement VDRIVE command VCHOP
"""
import os
from procss_vcommand import VDriveCommand


class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'HELP', 'RUNS', 'RUNE', 'DBIN', 'LOADFRAME', 'FURNACE', 'BIN', 'PICKDATA', 'OUTPUT',
                     'DRYRUN', 'PULSETIME', 'INFO']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',

        'DBIN': 'time step for binning interval',
        'PICKDATA': 'Name of a plain text 2-column data file for start and stop time for splitters.',
        'LOADFRAME': 'Chop LoadFrame log (MTSLoadFrame) along with',
        'FURNACE': 'Chop Furnace log (MTSFurnace) along with',
        'BIN': 'If bin=1, chopped data will be reduced to GSAS files',
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
                          dry_run, chop_loadframe_log, chop_furnace_log):
        """
        Chop data by time interval
        :param run_number:
        :param start_time:
        :param stop_time:
        :param time_interval:
        :param reduce_flag: flag to reduce the data afterwards
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
        if chop_loadframe_log:
            exp_log_type = 'loadframe'
        elif chop_furnace_log:
            exp_log_type = 'furnace'
        else:
            exp_log_type = None

        status, message = self._controller.slice_data(run_number, slicer_key,
                                                      reduce_data=reduce_flag, output_dir=output_dir,
                                                      export_log_type=exp_log_type)

        return status, message

    def chop_data_manually(self, run_number, slicer_list, reduce_flag, output_dir, epoch_time, dry_run,
                           chop_loadframe_log, chop_furnace_log):
        """
        chop and/or reduce data with arbitrary slicers
        :param run_number:
        :param slicer_list:
        :param reduce_flag:
        :param output_dir:
        :param epoch_time:
        :param dry_run:
        :param chop_loadframe_log:
        :param chop_furnace_log:
        :return:
        """
        # TODO/TEST/NOW/ISSUE/33 -
        # check inputs
        assert isinstance(run_number, int), 'Run number %s must be a string but not %s.' \
                                            '' % (str(run_number), type(run_number))
        assert isinstance(output_dir, str) and os.path.exists(output_dir), \
            'Directory %s must be a string (now %s) and exists.' % (str(output_dir), type(output_dir))

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
        status, message = self._controller.slice_data(run_number, slicer_key,
                                                      reduce_data=reduce_flag, output_dir=output_dir,
                                                      export_log_type=exp_log_type)

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
        if len(error_message) > 0:
            print '[DB...BAT] Error archive key: ', archive_key 
            return False, error_message
        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.add_runs_to_project(run_info_list)

        # Go through all the arguments
        if 'HELP' in self._commandArgsDict:
            # pop out the window
            return True, 'pop'

        if 'INFO' in self._commandArgsDict:
            # get the chopping-help information
            # TODO/ISSUE/33/ - organize some information
            pass

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

        if 'DBIN' in self._commandArgsDict:
            time_step = float(self._commandArgsDict['DBIN'])
        else:
            time_step = None
        if 'PICKDATA' in self._commandArgsDict:
            user_slice_file = self._commandArgsDict['PICKDATA']
        else:
            user_slice_file = False
        if 'PULSETIME' in self._commandArgsDict:
            pulse_time = int(self._commandArgsDict['PULSETIME'])
        else:
            pulse_time = 1

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
        if 'BIN' in self._commandArgsDict:
            output_to_gsas = True
        else:
            output_to_gsas = False

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
                                                         dry_run=is_dry_run,
                                                         chop_loadframe_log=chop_load_frame,
                                                         chop_furnace_log=chop_furnace_log)
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
                # FIXME/TODO/ISSUE/33 - Need to wait for Mantid
                try:
                    slicer_list = self.parse_pick_data(user_slice_file)
                    status, message = self.chop_data_manually(run_number=run_number,
                                                              slicer_list=slicer_list,
                                                              reduce_flag=output_to_gsas,
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
        help_str += ' > CHOP, IPTS=14094, RUNS=96450, dbin=60,loadframe=1,bin=1,DRYRUN=1\n\n'

        return help_str

    @staticmethod
    def parse_pick_data(file_name):
        """

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



