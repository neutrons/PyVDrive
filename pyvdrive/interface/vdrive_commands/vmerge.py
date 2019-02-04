import os
from pyvdrive.lib import datatypeutility
from procss_vcommand import VDriveCommand
from pyvdrive.lib import file_utilities


class VdriveMerge(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNFILE', 'RUNLIST', 'CHOPRUN', 'RUNV', 'OUTPUT', 'BINFOLDER', 'BINW', 'MYTOFMIN',
                     'MYTOFMAX']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNFILE': 'Name of the file containing runs to merge.',
        'RUNLIST': 'Run number to merge',
        'RUNV': 'Vanadium run to normalize the data',
        'OUTPUT': 'Directory to which the reduced merged data is saved'
    }

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommand.__init__(self, controller, command_args)

        self._commandName = 'MERGE'

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec_cmd(self):
        """ Execute input command
        """
        # check and set IPTS
        try:
            self.set_ipts()
        except RuntimeError as run_err:
            return False, 'Error in setting IPTS: {0}'.format(run_err)

        # get run numbers to
        run_number_list = self.parse_run_numbers()

        # Use result from CHOP?
        if 'CHOPRUN' in self._commandArgsDict:
            use_chop_data = True
            chop_run_number = int(self._commandArgsDict['CHOPRUN'])
        else:
            use_chop_data = False
            chop_run_number = None

        # output directory
        output_directory = self.parse_output_directory()

        # binning parameters
        use_default_binning, binning_parameters = self.parse_binning()

        # RUNV
        if 'RUNV' in self._commandArgsDict:
            van_run = int(self._commandArgsDict['RUNV'])
            if van_run < 0:
                return False, 'Vanadium run number {0} must be positive.'.format(van_run)
        else:
            van_run = None

        # reduce
        if use_chop_data:
            # merged chopped data
            raise RuntimeError('This option is not supported in 2019 March Release.'
                               'Contact developer!')

        else:
            # reduce from NeXus file in archive
            try:
                archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                                     run_number_list)
            except RuntimeError as run_err:
                return False, 'Failed to find nexus file for IPTS {0} Runs {1} due to {2}' \
                              ''.format(self._iptsNumber, run_number_list, run_err)

            # add the run numbers to
            run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
            self._controller.add_runs_to_project(run_info_list)

            # set vanadium runs
            if van_run is not None:
                status, msg = self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)
                if not status:
                    return False, msg

            # set flag
            run_number_list = list()
            for run_info in run_info_list:
                run_number_list.append(run_info['run'])
            self._controller.set_runs_to_reduce(run_number_list)

            # reduce by regular runs
            status, message = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_directory,
                                                               merge_banks=True,
                                                               vanadium=(van_run is not None),
                                                               standard_sample_tuple=None,
                                                               binning_parameters=binning_parameters,
                                                               merge_runs=True,
                                                               num_banks=3,
                                                               version=2,
                                                               roi_list=None,
                                                               mask_list=None,
                                                               no_cal_mask=False)

        return status, message

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
            run_file = self._commandArgsDict['RUNFILE']
            to_merge_runs = file_utilities.read_merge_run_file(run_file)
        else:
            to_merge_runs = file_utilities.convert_to_list(self._commandArgsDict['RUNLIST'], sep='&',
                                                           element_type=int)

        for run_i in to_merge_runs:
            if run_i <= 0:
                raise RuntimeError('User input run {} is not valid'.format(run_i))

        return to_merge_runs

