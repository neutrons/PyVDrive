import random
from procss_vcommand import VDriveCommandProcessor
"""
VCHROP
"""


class VdriveChop(VDriveCommandProcessor):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'dbin', 'loadframe', 'bin', 'pickdate']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommandProcessor.__init__(self, controller, command_args)

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

        try:
            run_start = int(self._commandArgList['RUNS'])
            run_end = int(self._commandArgList['RUNE'])
        except KeyError as err:
            raise RuntimeError('MERGE command requires input of argument RUNS/RUNE: %s.' % str(err))

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

        # do chopping
        for run_number in range(run_start, run_end+1):
            # chop
            chop_id = random.randint(1, 100000)
            self._controller.chop_data(registry=chop_id, ipts=self._iptsNumber, run=run_number, log_name=log_name,
                                       time_step=time_step)
            if output_to_gsas:
                reduce_id = self._controller.reduce_chopped_run(chop_id)
                output_dir = '/SNS/VULCAN/IPTS-%d/shared/binned_data/%d/' % (self._iptsNumber,
                                                                             run_number)
                self._controller.export_gsas_files(registry=reduce_id, output_dir=output_dir)
            # END-IF
        # END-FOR

        self.reduceSignal.emit(command_args)

        return


"""
CHOP, IPTS=1000, RUNS=2000, dbin=60, loadframe=1, bin=1
1. dbin is the chop step size in seconds;
2. loadframe, is set when VULCAN loadframe is used for continuous loading experiment;
3. bin=1, for binning data to GSAS file after slicing the data in time. GSAS data are stored at
    /SNS/VULCAN/IPTS-1000/shared/binned_data/2000/ along with the chopped sample environment files
    2000sampleenv_chopped_start(mean or end).txt.
4. loadframe=1: furnace=1, or generic=1, when using VULCAN standard sample environment DAQ
    for the furnaces or others. For a customized sample environment file name,
    use SampleEnv=‘your sample file name.txt' (the customized sample environment file is stored in
    /SNS/VULCAN/IPTS-1000/shared/logs).
5. If no sample environment is chosen or justchop=1 keyword is selected,
    no sample environment data synchronization will be executed.
"""



