import os
from process_vcommand import VDriveCommand
try:
    from PyQt5.QtCore import pyqtSignal
except (ImportError, RuntimeError) as import_err:
    print('CHOP: {}'.format(import_err))
    from PyQt4.QtCore import pyqtSignal


Panel_2Theta_Ranges = {'WEST': (79., 101),
                       'WL': (79., 101),  # (79.17292440985112, 3), (100.82707559014888, 1074)
                       'WM': (79., 101),  # (79.17292445065065, 1081), (100.82707554934935, 2152)
                       'WU': (79., 101),  # (79.17292440985112, 2159), (100.82707559014888, 3230)
                       'EAST': (79., 101),  #
                       'EL': (79., 101),  # (79.17292440985112, 4308), (100.82707559014888, 3237)
                       'EM': (79., 101),  # (79.17292445065065, 5386), (100.82707554934935, 4315)
                       'EU': (79., 101)   # (79.17292440985112, 6464), (100.82707559014888, 5393)
                       }


class BinBy2Theta(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['HELP', 'IPTS', 'RUNS', 'RUNV', 'IPARM',
                     'PANEL', 'MIN', 'MAX', 'STEP', 'SCALE',
                     'BINFOLDER', 'DRYRUN', 'FULLPROF']

    reduceSignal = pyqtSignal(str)  # signal to send out

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'PANEL': "Detector to get 2theta: 'WL', 'WM', 'WU', 'EL', 'EM', 'EU', 'WEST', 'EAST'",
        'MIN': 'Minimum 2theta',
        'MAX': 'Maximum 2theta',
        'STEP': '2theta step (delta 2theta)',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'SCALE': 'Scale factor for low counts.  Default=10000',
        'BINFOLDER': 'User specified output directory. Default will be under /SNS/VULCAN/IPTS-???/shared/bin',
        'DRYRUN': 'Check inputs and display the supposed output result without reducing data'
    }

    def __init__(self, controller, command_args):
        """
        Initialization
        :param controller:
        :param command_args:
        """
        # call super
        super(BinBy2Theta, self).__init__(controller, command_args)

        # set up my name
        self._commandName = '2THETABIN'
        # check argument
        self.check_command_arguments(self.SupportedArgs)

        return

    def _get_van_run(self):
        """
        get vanadium run number
        :return:
        """
        # RUNV
        if 'RUNV' in self._commandArgsDict:
            van_run = int(self._commandArgsDict['RUNV'])
            if van_run < 0:
                return False, 'Vanadium run number {0} must be positive.'.format(van_run)
        else:
            van_run = None

        return van_run

    def _get_gsas_iparm_name(self):
        """
        get GSAS instrument parameter file
        :return:
        """
        return 'vulcan.prm'

    def get_help(self):
        """
        override base class
        :return:
        """
        help_str = 'Chop runs\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        help_str += 'Examples:\n'
        help_str += 'Group pixels on panel West-Middle with 2theta range 80 to 101 with step 1.5 degree \n'
        help_str += ' > 2THETABIN,IPTS=19079,RUNS=158581,PANEL=WM,MIN=80,MAX=101,STEP=1.5,Scale=20000\n'

        return help_str

    def parse_vulcan_panel(self):
        """
        parse
        :return:
        """
        if 'PANEL' in self._commandArgsDict:
            panel = str(self._commandArgsDict['PANEL'])
            panel = panel.upper()
            if panel not in ['WL', 'WM', 'WU', 'EL', 'EM', 'EU', 'WEST', 'EAST']:
                raise RuntimeError('Panel name {} is not recognized. ]'
                                   'Allowed panel names are WL, WM, WU, EL, EM, EU, WEST, EAST'.format(panel))
        else:
            raise RuntimeError('PANEL must be specified.')

        return panel

    def get_panel_ws_index_range(self, panel_name):

        if panel_name == 'WEST':
            ws_index_range = (0, 3234)   # [...)
        elif panel_name == 'EAST':
            ws_index_range = (3234, 6468)
        else:
            index = ['WL', 'WM', 'WU', 'EL', 'EM', 'EU'].index(panel_name)
            ws_index_range = 3234/3 * index, 3234/3 * (index+1)

        return ws_index_range

    def get_argument_value(self, arg_name, arg_type, allow_default, default_value=None):
        if arg_name in self._commandArgsDict:
            arg_value = arg_type(self._commandArgsDict[arg_name])
        elif allow_default:
            arg_value = default_value
        else:
            raise RuntimeError('{} must be specified'.format(arg_name))

        return arg_value

    def parse_2theta_range(self, panel_name):
        """ Parse 2theta range
        :param panel_name:
        :return:
        """
        two_theta_min = self.get_argument_value('MIN', float, allow_default=True,
                                                default_value=Panel_2Theta_Ranges[panel_name][0])
        two_theta_max = self.get_argument_value('MAX', float, allow_default=True,
                                                default_value=Panel_2Theta_Ranges[panel_name][1])
        two_theta_step = self.get_argument_value('STEP', float, allow_default=False,
                                                 default_value=None)

        return two_theta_min, two_theta_max, two_theta_step

    def exec_cmd(self):
        """
        Execute input command (override)
        :except: RuntimeError for bad command
        :return: 2-tuple, status, error message
        """
        # Go through all the arguments
        if 'HELP' in self._commandArgsDict:
            # pop out the window
            return True, 'pop'

        # parse inputs
        try:
            # IPTS and runs
            self.set_ipts()
            run_number_list = self.parse_run_numbers()

            # GSAS: binning parameters, vanadium run and IPARM
            use_default_binning, binning_parameters = self.parse_binning()
            van_run_number = self._get_van_run()
            iparm_name = self._get_gsas_iparm_name()

            # 2theta parameters
            vulcan_panel = self.parse_vulcan_panel()
            ws_index_range = self.get_panel_ws_index_range(vulcan_panel)
            two_theta_min, two_theta_max, two_theta_step = self.parse_2theta_range(vulcan_panel)

            scale_factor = self.get_argument_value('SCALE', float, allow_default=True,
                                                   default_value=10000.)

            # output
            output_dir = self.get_argument_value('BINFOLDER', str, True, None)
            if output_dir is None:
                # default output directory
                output_dir = os.path.join('/SNS/VULCAN/IPTS-{}/shared/'.format(self._iptsNumber),
                                          'binned_data/')
        except RuntimeError as run_err:
            return False, 'Error in parsing BINBY2THETA parameters: {0}'.format(run_err)

        # Dry run
        is_dry_run = self.get_argument_value('DRYRUN', int, True, 0) == 1
        if is_dry_run:
            message = 'IPTS-{} RUN {} Panel {} Group pixels by 2theta {}:{} with step {}' \
                      ''.format(self._iptsNumber, run_number_list, vulcan_panel, two_theta_min, two_theta_max,
                                two_theta_step)
            return True, message

        # Reduce
        two_theta_params = {'min': two_theta_min, 'max': two_theta_max, 'step': two_theta_step}
        try:
            self._controller.project.reduce_runs_2theta(self._iptsNumber, run_number_list[0], ws_index_range,
                                                        two_theta_params, (use_default_binning, binning_parameters),
                                                        scale_factor=scale_factor,
                                                        vanadium=van_run_number,
                                                        gsas_iparam=iparm_name,
                                                        output_directory=output_dir)
        except RuntimeError as run_err:
            return False, 'Unable to reduce by 2theta: {}'.format(run_err)

        return True, ''
