import os
from procss_vcommand import VDriveCommand


class VdriveMerge(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNFILE', 'CHOPRUN']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNFILE': 'Name of the file containing runs to merge.',
        'CHOPRUN': '',
        'RUNLIST': 'Run number to merge',
        'OUTPUT': 'Directory to which the reduced merged data is saved.'
    }

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommand.__init__(self, controller, command_args)

        self.check_command_arguments(self.SupportedArgs)
        
        return

    @staticmethod
    def convert_to_list(list_str):
        """
        list in format of string. with separation as &
        :param list_str:
        :return:
        """
        assert isinstance(list_str, str), 'Input must be a string'

        # remove all the space
        list_str = list_str.replace(' ', '')

        # split
        terms = list_str.split('&')
        if len(terms) < 2:
            raise RuntimeError('There must be at least 2 run numbers given.')

        run_number_list = list()
        for term in terms:
            try:
                run = int(term)
            except ValueError as value_err:
                raise RuntimeError('In given run numbers, {0} is not a valid integer.'.format(term))
            if run < 0:
                raise RuntimeError('blabla')
            run_number_list.append(run)

        return run_number_list

    def exec_cmd(self):
        """ Execute input command
        """
        # parse
        self.set_ipts()

        # get run numbers to
        run_number_list = self.parse_run_numbers()

        # output directory
        output_directory = self.parse_output_directory()

        # set up
        archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                             run_number_list)

        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.add_runs_to_project(run_info_list)

        # # set vanadium runs
        # TODO/FUTURE: Optionally add support of vanadium run
        # if van_run is not None:
        #     self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)

        # TODO/FUTURE: Optionally add support of 'TAG'
        standard_tuple = None

        # TODO/FUTURE: Optionally add support of user-specified binning parameters
        binning_parameters = None

        # set flag
        run_number_list = list()
        for run_info in run_info_list:
            run_number_list.append(run_info['run'])
        self._controller.set_runs_to_reduce(run_number_list)

        # reduce by regular runs
        # TODO/FIXME/NOW - Binning parameters
        status, ret_obj = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_directory,
                                                           vanadium=None,
                                                           standard_sample_tuple=standard_tuple,
                                                           binning_parameter=binning_parameters,
                                                           merge=True)

        pass

    def generate_data_save_dir(self, chop_run):
        """
        Generate the directory to save file
        :param chop_run:
        :return:
        """
        assert isinstance(chop_run, str), 'Parameter chop_run (%s) must be a string but not a %s.' \
                                          '' % (str(chop_run), chop_run.__class__.__name__)
        chop_run_dir = '/SNS/VULCAN/IPTS-%d/shared/chopped_data/%s/' % (self._iptsNumber, chop_run)

        return chop_run_dir

    def get_help(self):
        """
        get help
        :return:
        """
        help_str = 'MERGE: Merge runs and reduce the merged data.\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        # examples
        help_str += 'Examples:\n'
        help_str += '> MERGE, IPTS=18420, RUN=135318 & 135775\n'

        return help_str

    def parse_output_directory(self):
        """

        :return:
        """
        if 'OUTPUT' in self._commandArgsDict and 'CHOPRUN' in self._commandArgsDict:
            # specify too many
            raise RuntimeError('It is not permitted to specify both OUTPUT and CHOPRUN')

        elif 'OUTPUT' in self._commandArgsDict:
            output_directory = self._commandArgsDict['OUTPUT']

        elif 'CHOPRUN' in self._commandArgsDict:
            chop_run = str(self._commandArgsDict['CHOPRUN'])
            # parse run file
            output_directory = self.generate_data_save_dir(chop_run)

        else:
            raise RuntimeError('MERGE command requires input of argument {0}.'
                               ''.format('RUNFILE and CHOPRUN'))

        return output_directory

    def parse_run_numbers(self):
        """
        parse run numbers from command's input
        :return:
        """
        if 'RUNFILE' in self._commandArgsDict and 'RUNLIST' in self._commandArgsDict:
            raise RuntimeError('RUNFILE and RUNLIST  cannot be specified simultaneously.')
        elif 'RUNFILE' not in self._commandArgsDict and 'RUNLIST' not in self._commandArgsDict:
            raise RuntimeError('Either RUNFILE or RUNLIST must be specified.')

        if 'RUNFILE' in self._commandArgsDict:
            run_file = str(self._commandArgsDict['RUNFILE'])
            to_merge_runs = self.read_merge_run_file(run_file)
        else:
            to_merge_runs = self.convert_to_list(str(self._commandArgsDict['RUNLIST']))

        return to_merge_runs

    @staticmethod
    def read_merge_run_file(run_file_name):
        """ Read a standard VDRIVE run file
        Data are combined from the runs of rest columns to the runs of the first column in the runfile.txt.
        """
        # check input
        assert os.path.exists(run_file_name), 'RUNFILE %s cannot be found or accessed.' % run_file_name

        # import run-merge file
        run_file = open(run_file_name, 'r')
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