# Goal 1: show information about vanadium with automatic vanadium locator!
from pyvdrive.interface.vdrive_commands.process_vcommand import VDriveCommand
import pyvdrive.core.datatypeutility


# TEST ME - 20180730 - Newly Implemented
class RunsInfoQuery(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'DURATION', '-N']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number to search information from',
        'RUNE': 'Last run number to search information from',
        'DURATION': 'Show duration of the runs in the IPTS folder',
        '-N': 'Number of items to show.  Default = 20'
    }

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommand.__init__(self, controller, command_args)

        self.check_command_arguments(self.SupportedArgs)

        return

    def exec_cmd(self):
        """ Execute input command
        """
        # check whether the any non-supported args
        input_args = self._commandArgsDict.keys()
        for arg_key in input_args:
            if arg_key not in RunsInfoQuery.SupportedArgs:
                raise KeyError('INFO argument {} is not recognized.  Supported arguments include '
                               '{}'.format(arg_key, self.ArgsDocDict.keys()))
        # END-FOF

        # parse
        self.set_ipts()

        # get run numbers to
        if 'RUNS' in input_args:
            first_run_number = int(self._commandArgsDict['RUNS'])
        else:
            first_run_number = None

        if 'RUNE' in input_args:
            last_run_number = int(self._commandArgsDict['RUNE'])
        else:
            last_run_number = None

        if '-N' in input_args:
            num_to_show = int(self._commandArgsDict['-N'])
        else:
            num_to_show = 20

        # TODO - 20180822 - New Feature Important : Can show and order by 'TotalCounts' - TODO

        # load AUTO-DATA
        auto_data_key = self._controller.archive_manager.load_auto_record(self._iptsNumber, 'data')

        if 'DURATION' in input_args:
            duration_info_list = self._controller.archive_manager.sort_info(auto_data_key,
                                                                            sort_by='duration',
                                                                            run_range=(first_run_number,
                                                                                       last_run_number),
                                                                            output_items=['run', 'duration',
                                                                                          'sample'],
                                                                            num_outputs=num_to_show)
            if len(duration_info_list) == 0:
                info_str = 'IPTS is empty!'
            else:
                info_str = self.format_list_to_str(duration_info_list, keys=['run', 'duration', 'sample'])

        else:
            return False, 'There is no sort key that is specified by user.  Inputs are {}, while the ' \
                          'available sort keys are {}.' \
                          ''.format(input_args, 'DURATION')

        return True, info_str

    @staticmethod
    def format_list_to_str(info_dict_list, keys):
        """ format the run information dictionary list into nice string to print out
        :param info_dict_list:
        :param keys:
        :return:
        """
        # check inputs
        pyvdrive.core.datatypeutility.check_list('Run information dictionary list', info_dict_list)
        if len(info_dict_list) == 0:
            return 'Input run information dictionary list is empty'
        pyvdrive.core.datatypeutility.check_list('Column name list', keys)
        if len(keys) == 0:
            raise RuntimeError('It is not allowed to input an empty column name list')

        # format nice output
        nice_str = ''

        # title
        for col_name in keys:
            nice_str += '{:20s}'.format(col_name)
        nice_str += '\n'

        for info_dict in info_dict_list:
            # check
            pyvdrive.core.datatypeutility.check_dict('Run information dictionary', info_dict)
            # if it fails due to KeyError, let it be
            for col_name in keys:
                col_value = '{}'.format(info_dict[col_name])
                nice_str += '{:20s}'.format(col_value)
            nice_str += '\n'
        # END-FOR

        return nice_str

    def get_help(self):
        """
        get help
        :return:
        """
        help_str = 'Query and show information of an IPTS\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        # examples
        help_str += 'Examples:\n'
        help_str += '> INFO, IPTS=21356, DURATION=1, -n=40\n'
        help_str += '> INFO, IPTS=21356, RUNS=20000, RUNE=30000, DURATION=1, -n=40\n'

        return help_str
