import os
from procss_vcommand import VDriveCommand


class VdriveMerge(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNFILE', 'CHOPRUN']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommand.__init__(self, controller, command_args)

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec_cmd(self):
        """ Execute input command
        """
        # parse
        self.set_ipts()

        try:
            run_file = str(self._commandArgsDict['RUNFILE'])
            chop_run = str(self._commandArgsDict['CHOPRUN'])

        except KeyError as err:
            raise RuntimeError('MERGE command requires input of argument %s.' % 'RUNFILE and CHOPRUN')

        # parse run file
        to_merge_runs = self.read_merge_run_file(run_file)
        dir_2_save = self.generate_data_save_dir(chop_run)

        # set up
        self._controller.setup_merge(ipts_number=self._iptsNumber, runs=to_merge_runs, save_dir=dir_2_save)
        run_info_list = self._controller.get_runs(run_number_list=to_merge_runs)

        # reduce
        self._controller.add_runs_to_project(run_info_list, self._iptsNumber)
        reduce_id = self._controller.reduce_data_set(merge=True)
        self._controller.export_gsas_file(registry=reduce_id, output_dir=dir_2_save)

        pass

    def generate_data_save_dir(self, chop_run):
        """
        Generate the directory to save file
        :param chop_run:
        :return:
        """
        assert isinstance(chop_run, str), 'Parameter chop_run (%s) must be a string but not a %s.' \
                                          '' % (str(chop_run), chop_run.__class__.__name__)
        dir = '/SNS/VULCAN/IPTS-%d/shared/chopped_data/%s/' % (self._iptsNumber, chop_run)

        return dir

    @staticmethod
    def read_merge_run_file(run_file_name):
        """ Read a standard VDRIVE run file
        Data are combined from the runs of rest columns to the runs of the first column in the runfile.txt.
        """
        # check input
        assert os.path.exists(run_file_name), 'RUNFILE %s cannot be found or accessed.' % run_file_name

        # import run-merge file
        run_file = file.open(run_file_name, 'r')
        lines = run_file.readlines()
        run_file.close()

        # parse run-merge file
        merge_run_dict = dict()
        for line in lines:
            line = line.strip()
            
            # skip if empty line or command line
            if len(line) == 0:
                return
            elif line[0] == '#':
                return

            # set up
            run_str_list = line.split()

            target_run_number = None
            for index, run_str in enumerate(run_str_list):
                run_number = int(run_str)
                if index == 0:
                    # create a new item (i.e., node) in the return dictionary
                    target_run_number = run_number
                    merge_run_dict[target_run_number] = list()

                assert target_run_number is not None
                merge_run_dict[target_run_number].append(run_number)
            # END-FOR (term)
        # END-FOR (line)

        return merge_run_dict


"""
MERGE, IPTS=1000, RUNFILE="/SNS/VULCAN/IPTS-1000/shared/runfile.txt", CHOPRUN=2
The combined data are saved to /SNS/VULCAN/IPTS-1000/shared/chopped_data/2/ To bin the data combined by VDRIVEMERGE:
VDRIVEBIN, IPTS=1000, CHOPRUN=2
GSAS files are stored in /SNS/VULCAN/IPTS-1000/shared/binned_data/2/
Example of the tab delimited runfile.txt:
----------------------------
1001 1002 1003 1004 1005 1006 1007
1008 1009 1010
...
----------------------------
Additional keywords:
NONE
"""