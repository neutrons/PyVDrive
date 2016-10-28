import random
from procss_vcommand import VDriveCommand
"""
VCHROP
"""


class VdriveChop(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'dbin', 'loadframe', 'bin', 'pickdate']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommand.__init__(self, controller, command_args)

        self._commandName = 'CHOP'

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec_cmd(self):
        """
        Execute input command (override)
        statu
        :return: 2-tuple, status, error message
        """
        # parse arguments
        self.set_ipts()

        # parse the scope of runs
        try:
            run_start = int(self._commandArgList['RUNS'])
        except KeyError as err:
            raise RuntimeError('CHOP command requires input of argument RUNS: %s.' % str(err))
        if 'RUNE' in self._commandArgList:
            run_end = int(self._commandArgList['RUNE'])
        else:
            run_end = run_start

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

        # locate the runs and add the reduction project
        archive_key, error_message = self._controller.archive_manager.scan_archive(self._iptsNumber, run_start,
                                                                                   run_end)
        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.project.add_runs(run_info_list)

        # do chopping
        for run_number in range(run_start, run_end+1):
            # chop
            if time_step is not None:
                self._controller.project.chop_data_by_time(run_number=run_number,
                                                           start_time=None,
                                                           stop_time=None,
                                                           time_interval=time_step)
            else:
                raise RuntimeError('Not implemented yet for chopping by log value.')

            # export
            if output_to_gsas:
                # FIXME/TODO/NOW - Implement how to reduced chopped data
                pass
                # reduce_id = self._controller.reduce_chopped_run(chop_id)
                # output_dir = '/SNS/VULCAN/IPTS-%d/shared/binned_data/%d/' % (self._iptsNumber,
                #                                                              run_number)
                # self._controller.export_gsas_files(registry=reduce_id, output_dir=output_dir)

        # END-FOR (run_number)

        # self.reduceSignal.emit(command_args)

        return True, 'Still try to figure out how to write in the message'

    def get_help(self):
        """
        override base class
        :return:
        """
        help_str = 'Chop runs\n'
        help_str += 'CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1\n'
        help_str += 'Debug:\n'
        help_str += 'CHOP, IPTS=14094, RUNS=96450, dbin=60'

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



