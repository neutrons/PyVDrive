import os
from pyvdrive.lib import datatypeutility
from vbin import VBin


class VdriveMerge(VBin):
    """
    Process command MERGE
    """
    SupportedArgs = VBin.SupportedArgs

    ArgsDocDict = VBin.ArgsDocDict
    ArgsDocDict['CHOPRUN'] = 'Run number for the merged data to be save to in chopped run directory'

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VBin.__init__(self, controller, command_args)

        self._commandName = 'MERGE'

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec_cmd(self):
        """ Execute input command
        """
        self.set_merge_flag(True)

        return VBin.exec_cmd(self)

    def _generate_chop_run_dir(self, chop_run):
        """
        Generate the directory to save file
        :param chop_run:
        :return:
        """
        datatypeutility.check_string_variable('CHOP RUN', chop_run)
        # create the directory in archive
        chop_run_dir = '/SNS/VULCAN/IPTS-{}/shared/binned_data/{}/'.format(self._iptsNumber, chop_run)

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
        help_str += '> MERGE,IPTS=22752,RUNLIST=171834 & 171836 & 171837,RUNV=163021\n'

        return help_str

    def process_merge_output_dir(self):
        """ Process different options for output directory.
        Options are 'output', 'choprun' and 'binfolder'
        :return:
        """
        num_outputs = 0
        output_directory = None

        if 'OUTPUT' in self._commandArgsDict:
            output_directory = self._commandArgsDict['OUTPUT']
            num_outputs += 1

        if 'BINFOLDER' in self._commandArgsDict:
            output_directory = self._commandArgsDict['BINFOLDER']
            num_outputs += 1

        if 'CHOPRUN' in self._commandArgsDict:
            chop_run = str(self._commandArgsDict['CHOPRUN'])
            output_directory = self._generate_chop_run_dir(chop_run)
            num_outputs += 1

        # check output
        if num_outputs == 0:
            raise RuntimeError('User must specify one and only one in OUTPUT, BINFOLDER and CHOPRUN.'
                               'Now there is nothing given.')
        elif num_outputs > 1:
            raise RuntimeError('User must specify one and only one in OUTPUT, BINFOLDER and CHOPRUN.'
                               'Now there are too much: OUTPUT: {}, BINFOLDER: {}, CHOPRUN: {}.'
                               ''.format('OUTPUT' in self._commandArgsDict,
                                         'BINFOLDER' in self._commandArgsDict,
                                         'CHOPRUN' in self._commandArgsDict))

        # check write permission
        datatypeutility.check_file_name(output_directory, False, True, True, 'MERGE outpout directory')

        return output_directory


