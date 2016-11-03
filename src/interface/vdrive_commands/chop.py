import random
from procss_vcommand import VDriveCommand
"""
VCHROP
"""


class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'HELP', 'RUNS', 'RUNE', 'dbin', 'loadframe', 'bin', 'pickdate', 'OUTPUT']

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
        if 'RUNS' in self._commandArgList:
            # get RUNS/RUNE from arguments
            run_start = int(self._commandArgList['RUNS'])
            if 'RUNE' in self._commandArgList:
                run_end = int(self._commandArgList['RUNE'])
            else:
                run_end = run_start
            self._runNumberList = range(run_start, run_end + 1)
        elif len(self._commandArgList) > 0:
            # from previously stored value
            run_start = self._commandArgList[0]
            run_end = self._commandArgList[-1]
        else:
            # not properly set up
            raise RuntimeError('CHOP command requires input of argument RUNS or previously stored Run number')
        # END-IF

        # locate the runs and add the reduction project
        archive_key, error_message = self._controller.archive_manager.scan_archive(self._iptsNumber, run_start,
                                                                                   run_end)
        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.project.add_runs(run_info_list)

        if 'HELP' in self._commandArgList:
            # pop out the window
            return True, 'pop'

        # check input parameters
        assert isinstance(run_start, int) and isinstance(run_end, int) and run_start <= run_end, \
            'Run start %s (%s) and run end %s (%s) must be integers and run start <= run end' % (
                str(run_start), str(type(run_start)), str(run_end), str(type(run_end))
            )

        # parse other optional parameters
        if 'dbin' in self._commandArgList:
            time_step = float(self._commandArgList['dbin'])
        else:
            time_step = None

        if 'loadframe' in self._commandArgList:
            use_load_frame = True
        else:
            use_load_frame = False

        if 'bin' in self._commandArgList:
            output_to_gsas = True
        else:
            output_to_gsas = False

        if use_load_frame:
            log_name = 'Load Frame'
        else:
            log_name = None

        if 'OUTPUT' in self._commandArgList:
            output_dir = str(self._commandArgList['OUTPUT'])
        else:
            output_dir = None

        # do chopping
        sum_msg = ''
        final_success = True
        for run_number in range(run_start, run_end+1):
            # chop
            if time_step is not None:
                status, message = self._controller.project.chop_data_by_time(run_number=run_number,
                                                                             start_time=None,
                                                                             stop_time=None,
                                                                             time_interval=time_step,
                                                                             reduce=output_to_gsas,
                                                                             output_dir=output_dir)
                final_success = final_success and status
                sum_msg += 'Run %d: %s\n' % (run_number, message)
            else:
                raise RuntimeError('Not implemented yet for chopping by log value.')

        # END-FOR (run_number)

        # TODO/THINK/ISSUE/51 - shall a signal be emit???
        # self.reduceSignal.emit(command_args)

        print '[DB...BAT] CHOP Message: ', sum_msg

        return final_success, sum_msg

    def get_help(self):
        """
        override base class
        :return:
        """
        help_str = 'Chop runs\n'
        help_str += 'CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1\n'
        help_str += 'Debug (chop run 96450) by 60 seconds:\n'
        help_str += 'CHOP, IPTS=14094, RUNS=96450, dbin=60\n\n'

        help_str += 'HELP:      the Log Picker Window will be launched and set up with given RUN number.\n'
        help_str += 'bin=1:     chopped data will be reduced to GSAS files.\n'
        help_str += 'loadframe: \n'

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



