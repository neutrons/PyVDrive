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


class VdriveView(VDriveCommand):
    """
    Process command VIEW or VDRIVEVIEW
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'CHOPRUN', 'RUNV', 'MinV', 'MaxV', 'NORM']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',
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

        return

    def exec_cmd(self):
        """
        Execute input command (override)
        :except: RuntimeError for bad command
        :return: 2-tuple, status, error message
        """
        # parse arguments
        self.set_ipts()

        #

        return True, ''

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

    def get_run_number_list(self):
        """
        for output 2D or 3D, it is required to return multiple
        :return:
        """
        return self._runNumberList[:]

