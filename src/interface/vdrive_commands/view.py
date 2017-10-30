# VDRIVE VIEW
# Purpose 1:
# View one GSAS raw pattern after binning as histogram data: (short name: VIEW)
# Example
# VIEW, IPTS=####, RUNS=#### [,CHOPRUN=####, RUNV=####, PCSENV=1]
#
# Purpose 2:
# View sequential data in 2D contour and 3D surface: (short name: VIEW)
# VIEW, IPTS=####, RUNS=####, RUNE=#### [,CHOPRUN=####] [, MinV=#.#, MaxV=#.#,
# RUNV=####, NORM=1 , PCSENV=1]


from procss_vcommand import VDriveCommand
from PyVDrive.lib import vulcan_util


class VdriveView(VDriveCommand):
    """
    Process command VIEW or VDRIVEVIEW
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'CHOPRUN', 'RUNV', 'MINV', 'MAXV', 'NORM', 'DIR', 'SHOW',
                     'PEAK']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',
        'RUNV': 'Vanadium run number for calibration',
        'CHOPRUN': 'Run number of the chopped run.',
        'MINV': 'Minimum X value to plot',
        'MAXV': 'Maximum X value to plot',
        'NORM': 'Do normalize to the reduced data',
        'DIR': 'User specified directory to find the reduced data (including those being chopped)',
        'PEAK': 'Integrate peak and output value. PEAK=1: output to console. Otherwise, output '
                'to the file name',
        # TODO/ISSUE/NOWNOW - Implement this 'SHOW'
        'SHOW': 'Launch the reduced-data viewer'
    }

    def __init__(self, controller, command_args, ipts_number=None, run_number_list=None):
        """
        Initialization
        :param controller:
        :param command_args:
        :param ipts_number:
        :param run_number_list:
        """
        # call super
        super(VdriveView, self).__init__(controller, command_args)

        # set up my name
        self._commandName = 'VIEW'
        # check argument
        self.check_command_arguments(self.SupportedArgs)

        # set default
        if ipts_number is not None and isinstance(ipts_number, int) and ipts_number > 0:
            self._iptsNumber = ipts_number
        if isinstance(run_number_list, list) and len(run_number_list) > 0:
            self._runNumberList = run_number_list[:]

        # class variables
        self._figureDimension = 0
        self._isChoppedRun = False
        self._multiRuns = False
        self._choppedRunSeqList = None
        self._reducedDataDir = None  # user specified directory for reduced data
        self._minX = None  # minimum X value to plot
        self._maxX = None  # maximum X value to plot
        self._normalizeData = False  # whether the data will be normalized
        self._unit = 'dSpacing'  # unit

        self._peakValueFileName = None
        self._outputPeakValueToConsole = False

        self._normByVanadium = False
        self._vanRunNumberDict = dict()

        return

    def exec_cmd(self):
        """
        Execute input command (override)
        view's execution only collects information but not load any data at all!
        :except: RuntimeError for bad command
        :return: 2-tuple, status, error message
        """
        # parse IPTS
        self.set_ipts()

        # parse RUNS and RUNE
        if 'RUNS' in self._commandArgsDict:
            # get RUNS/RUNE from arguments
            run_start = int(self._commandArgsDict['RUNS'])
            if 'RUNE' in self._commandArgsDict:
                run_end = int(self._commandArgsDict['RUNE'])
            else:
                run_end = run_start
        else:
            # not properly set up
            return False, 'VIEW command requires input of argument RUNS.'

        # parse run numbers with chopped runs
        if 'CHOPRUN' in self._commandArgsDict:
            # chopped runs
            self._runNumberList = [int(self._commandArgsDict['CHOPRUN'])]
            self._choppedRunSeqList = range(run_start, run_end + 1)
            self._isChoppedRun = True
        else:
            # regular runs
            self._runNumberList = range(run_start, run_end + 1)
            self._isChoppedRun = False
        # END-IF

        # directory of the reduced data
        if 'DIR' in self._commandArgsDict:
            self._reducedDataDir = self._commandArgsDict['DIR']

        if len(self._runNumberList) > 1:
            self._multiRuns = True
        else:
            self._multiRuns = False

        # set up the plot dimension
        if (not self._multiRuns) and (not self._isChoppedRun):
            # not multiple Run or chopped Run
            self._figureDimension = 1
        else:
            # at least 2D
            self._figureDimension = 2

        # min and max value
        has_min = False
        has_max = False
        if 'MINV' in self._commandArgsDict:
            self._minX = float(self._commandArgsDict['MINV'])
            has_min = True
        if 'MAXV' in self._commandArgsDict:
            self._maxX = float(self._commandArgsDict['MAXV'])
            has_max = True

        # Normalized?
        if 'NORM' in self._commandArgsDict:
            norm_value = int(self._commandArgsDict['NORM'])
            if norm_value > 0:
                self._normalizeData = True
            else:
                self._normalizeData = False
        # END-IF

        # RUNV
        auto_search_van = False
        van_run_number = None
        if 'RUNV' in self._commandArgsDict:
            van_run_str = str(self._commandArgsDict['RUNV'])
            if van_run_str == 'auto':
                auto_search_van = True
            elif van_run_str.isdigit():
                van_run_number = int(van_run_str)
            else:
                return False, 'Vanadium run {0} is not recognized'.format(van_run_str)
            self._normByVanadium = True
        # END-IF

        # match vanadium run numbers
        if van_run_number is not None:
            # vanadium run number is set up by user
            for run_number in self._runNumberList:
                self._vanRunNumberDict[run_number] = van_run_number

        elif auto_search_van:
            # search vanadium
            van_locator = vulcan_util.AutoVanadiumCalibrationLocator(ipts=self._iptsNumber)
            for run_number in self._runNumberList:
                van_run_number = van_locator.search_vanadium_gda(run_number)
                if isinstance(van_run_number, list):
                    error_msg = 'Run {0} has more than {1} vanadium GSAS file corresponding.' \
                                ''.format(run_number, len(van_run_number))
                    if len(van_run_number) > 0:
                        error_msg += 'Candidates are {0}'.format(van_run_number)
                    return False, error_msg
                self._vanRunNumberDict[run_number] = van_run_number
            # END-IF
        # END-IF-ELSE

        # Calculate peak parameters
        if 'PEAK' in self._commandArgsDict:
            peak_str = str(self._commandArgsDict['PEAK']).strip()
            if peak_str != '0':
                # check
                if not (has_min and has_max):
                    return False, 'PEAK = {0}. Both MinV and MaxV must be specified.'.format(peak_str)
                if peak_str == '1':
                    self._outputPeakValueToConsole = True
                    self._peakValueFileName = None
                else:
                    self._peakValueFileName = peak_str
                    self._outputPeakValueToConsole = False
        # END-IF ('PEAK')

        # determine unit according to MinV or MaxV
        if self._maxX is not None:
            # use maximum X to determine the unit
            if self._maxX > 200.:
                self._unit = 'TOF'
            else:
                self._unit = 'dSpacing'
        elif self._minX is not None:
            # it may not be nice to use minimum X to determine the unit
            if self._minX > 100.:
                self._unit = 'TOF'
            else:
                self._unit = 'dSpacing'

        return True, ''

    @property
    def do_calculate_peak_parameter(self):
        """
        blabla
        :return:
        """
        return self._outputPeakValueToConsole or self._peakValueFileName is not None

    @property
    def do_proton_charge_normalization(self):
        """
        return flag whether data will be normalized by proton charge
        :return:
        """
        return self._normalizeData

    @property
    def do_vanadium_normalization(self):
        """check whether VIEW command is required to do vanadium calibration
        """
        return self._normByVanadium

    def get_vanadium_number(self, run_number):
        """get vanadium run number
        :return:
        """
        if self._normByVanadium:
            if run_number in self._vanRunNumberDict:
                van_number = self._vanRunNumberDict[run_number]
            else:
                raise RuntimeError('Run number {0} does not exist in vanadium number dictionary ({1})'
                                   ''.format(run_number, self._vanRunNumberDict.keys()))
        else:
            raise RuntimeError('No vanadium calibration is set up.')

        return van_number

    @property
    def is_1_d(self):
        """
        is the output figure a 1D image (X, Y, Sigma)
        :return:
        """
        return self._figureDimension == 1

    @property
    def is_2_d(self):
        """
        is the output figure a 2D image (2D contour)
        :return:
        """
        return self._figureDimension == 2

    @property
    def is_chopped_run(self):
        """
        in the case of 2D/3D output, check whether all the data to plot come from a run that is chopped.
        :return:
        """
        return self._isChoppedRun

    def get_chopped_sequence_range(self):
        """
        get the sequence range of the chopped data, which is previously parsed into this instance from VDRIVE command
        :return:
        """
        if self._choppedRunSeqList is None:
            sequence = None
        else:
            sequence = self._choppedRunSeqList[:]

        return sequence

    def get_help(self):
        """
        get help
        :return:
        """
        help_str = 'VIEW: bla bla\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        # examples
        help_str += 'Examples:\n'
        help_str += '> VIEW,IPTS=14094,RUNS=96450,RUNE=96451\n'
        help_str += '> view,IPTS=13183,choprun=68607, runs=1, rune=15\n'
        help_str += '> VIEW,IPTS=18420,RUNS=136558,MINV=0.5,MAXV=2.5,NORM=1\n'

        return help_str

    def get_ipts_number(self):
        """
        get the IPTS number
        :return:
        """
        return self._iptsNumber

    def get_run_number(self):
        """
        get the run number for plotting
        :return:
        """
        return self._runNumberList[0]

    def get_run_tuple_list(self):
        """
        for output 2D or 3D, it is required to return multiple.. including run number and IPTS number
        :return:
        """
        run_tup_list = list()
        for run_number in self._runNumberList:
            run_tup_list.append((run_number, self._iptsNumber))

        # sort
        run_tup_list.sort()

        return run_tup_list

    def get_reduced_data_directory(self):
        """
        get the direcotry where the reduced data is
        :return:
        """
        return self._reducedDataDir

    @property
    def output_peak_parameters_to_console(self):
        """
        blabla
        :return:
        """
        return self._outputPeakValueToConsole

    @property
    def peak_parameters_file(self):
        """
        blabla
        :return:
        """
        return self._peakValueFileName

    @property
    def unit(self):
        """
        get unit of output data
        :return:
        """
        return self._unit

    @property
    def x_min(self):
        """
        get minimum X to plot
        :return:
        """
        return self._minX

    @property
    def x_max(self):
        """
        get maximum X to plot
        :return:
        """
        return self._maxX
