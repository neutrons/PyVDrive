import os
from procss_vcommand import VDriveCommand


class VanadiumPeak(VDriveCommand):
    """ process vanadium peaks
    """
    SupportedArgs = ['IPTS', 'RUNV', 'HELP', 'Nsmooth', 'OneBank', 'Shift', 'OUTPUT']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'HELP': 'Launch General Plot Viewer',
        'OneBank': 'Add 2 bank data together (=1).',
        'Shift': 'the chopper center is shift to large lambda aggressively.',
        'Nsmooth': 'the number of points to be used in the boxcar smoothing algorithm, the bigger the smoother.',
        'OUTPUT': 'the directory where the smooth vanadium gsas file will be saved other than default.'
    }

    def __init__(self, controller, command_args):
        """
        initialization of an object

        [Input]
        VPEAK, IPTS=1000, RUNV=5000
        Additional keyword:
        Nsmooth =51: The number of points to be used in the boxcar smoothing
             algorithm, the bigger the smoother.
        OneBank=1:  all banks data are binned as one bank data.
        Shift=1: the chopper center is shift to large lambda aggressively.

        [Output]
        The smoothed data is named as ####-s.gda and located at /SNS/VULCAN/IPTS-1000/shared/Instrument
            as well as a copy in the VULCAN shared fold

        :param controller:
        :param command_args:
        """
        super(VanadiumPeak, self).__init__(controller, command_args)

        # define variables
        self._vanRunNumber = None
        self._doShift = False
        self._mergeToOneBank = False

        return

    def exec_cmd(self):
        """
        Execute command: override
        """
        # check
        if 'RUNV' not in self._commandArgsDict:
            return False, 'RUNV must be specified!'

        # parse IPTS
        self.set_ipts()

        # parse the parameters
        self._vanRunNumber = int(self._commandArgsDict['RUNV'])
        assert self._vanRunNumber > 0, 'Vanadium run number {0} cannot be non-positive.'.format(self._vanRunNumber)

        if 'OneBank' in self._commandArgsDict:
            self._mergeToOneBank = bool(int(self._commandArgsDict['OneBank']))

        if 'Shift' in self._commandArgsDict:
            self._doShift = bool(int(self._commandArgsDict['Shift']))

        if 'HELP' in self._commandArgsDict:
            do_launch_gui = bool(int(self._commandArgsDict['HELP']))
        else:
            do_launch_gui = False

        # return to pop
        if do_launch_gui:
            return True, 'pop'

        return True, None

    def get_help(self):
        """
        get helping strings for this VBIN command
        :return:
        """
        help_str = 'VPEAK: Strip peaks and smooth vanadium spectra and save to GSAS.\n'
        help_str += '       By default, the smoothed data is named as ####-s.gda and saved to ' \
                    '/SNS/VULCAN/IPTS-XXXX/shared/Instrument, as well as a copy in the VULCAN shared fold.'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        # examples
        help_str += 'Examples:\n'
        help_str += '> VVPEAK, IPTS=1000, RUNV=5000\n'

        return help_str

    @property
    def to_merge_to_one_bank(self):
        """

        :return:
        """
        return self._mergeToOneBank

    @property
    def to_shift(self):
        """

        :return:
        """
        return self._doShift

    @property
    def vanadium_run_number(self):
        """
        property as vanadium run number
        :return:
        """
        assert self._vanRunNumber is not None, 'Vanadium run number is not set yet.'
        return self._vanRunNumber
