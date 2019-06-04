import os
import time
from process_vcommand import VDriveCommand
from process_vcommand import convert_string_to
from pyvdrive.lib import datatypeutility
try:
    from PyQt5 import QtCore
    from PyQt5.QtCore import pyqtSignal
except (ImportError, RuntimeError) as import_err:
    print ('CHOP: {}'.format(import_err))
    from PyQt4 import QtCore
    from PyQt4.QtCore import pyqtSignal


class BinBy2Theta(VDriveCommand):
    """
    Process command MERGE
    """
    SupportedArgs = ['HELP', 'IPTS', 'RUNS', 'RUNE', 'RUNV', 'IPARM',
                     'PANEL', 'MIN', 'MAX', 'STEP',
                     'BINFOLDER', 'DRYRUN', 'FULLPROF']

    reduceSignal = QtCore.pyqtSignal(str)  # signal to send out

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNS': 'First run number',
        'RUNE': 'Last run number (if not specified, then only 1 run will be processed)',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
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
        self._commandName = 'BINBY2THETA'
        # check argument
        self.check_command_arguments(self.SupportedArgs)

        return

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
            vulcan_panel_list = self.parse_vulcan_panels()
            two_theta_min, two_theta_max, two_theta_step = self.parse_2theta_range()

            # output
            output_dir = self._process_output_directory()
        except RuntimeError as run_err:
            return False, 'Error in parsing BINBY2THETA parameters: {0}'.format(run_err)

        # Dry run
        if self._is_dry_run():
            message = 'IPTS-{} RUN {} Panel {} Group pixels by 2theta {}:{} with step {}' \
                      ''.format(self._iptsNumber, run_number_list, vulcan_panel_list, two_theta_min, two_theta_max,
                                two_theta_step)
            return True, message

        # Reduce
        two_theta_params = {'min': two_theta_min, 'max': two_theta_max, 'step': two_theta_step}
        try:
            self._controller.reduce_runs_2theta(self._iptsNumber, run_number_list, two_theta_params,
                                                (use_default_binning, binning_parameters),
                                                vanadium=van_run_number,
                                                gsas_iparam=iparm_name,
                                                output_dir=output_dir)
        except RuntimeError as run_err:
            return False, 'Unable to reduce by 2theta: {}'.format(run_err)

        return True, ''

