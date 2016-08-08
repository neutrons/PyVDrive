import os
from process_vcommand import VDriveCommandProcessor


class VdriveMerge(VDriveCommandProcessor):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNFILE', 'CHOPRUN']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommandProcessor.__init__(self, controller, command_args)

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec(self):
        """ Execute input command
        """
        # parse
        try:
            ipts_number = int(self._commandArgList['IPTS'])
            run_file = str(self._commandArgList['RUNFILE'])
            chop_run = str(self._commandArgList['CHOPRUN'])

        except KeyError as err:
            raise RuntimeError('MERGE command requires input of argument %s.' % dd)

        # parse run file
        to_merge_runs = self.read_merge_run_file(run_file)
        dir_2_save = self.generate_data_save_dir(ipts, chop_run)

        # set up
        self._controller.setup_merge(ipts_number=ipts_number, runs=to_merge_runs, save_dir=dir_2_save)

        pass


    @staticmethod
    def read_merge_run_file(run_file_name):
        """ Read a standard VDRIVE run file
        Data are combined from the runs of rest columns to the runs of the first column in the runfile.txt.
        """
        # check input
        assert os.path.exists(run_file), 'RUNFILE %s cannot be found or accessed.' % run_file

        # import
        run_file = file.open(run_file, 'r')
        lines = run_file.readlines()
        run_file.close()

        # run_merge_list
