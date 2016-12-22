import procss_vcommand

# VDRIVEBIN, i.e., VBIN
# 
# Example:
# cmd = VBIN(conroller, args)
# cmd.run()


class AutoReduce(procss_vcommand.VDriveCommand):
    """
    Command processor to call auto reduce script
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'DRYRUN', 'OUTPUT']

    def __init__(self, controller, command_args):
        """
        initialization
        :param controller:
        :param command_args:
        """
        procss_vcommand.VDriveCommand.__init__(self, controller, command_args)

        self._commandName = 'AUTO/AUTOREDUCE'

        self.check_command_arguments(self.SupportedArgs)

        return

    def exec_cmd(self):
        """
        execute command AUTO
        :return: 2-tuple
        """
        try:
            ipts = int(self._commandArgsDict['IPTS'])
        except KeyError:
            return False, 'IPTS must be given!'
        else:
            print '[DB...BAT] IPTS = ', ipts

        try:
            run_number_list = self.parse_run_numbers()
        except RuntimeError as error:
            return False, 'Unable to parse run numbers due to {0}'.format(error)

        if 'DRYRUN' in self._commandArgsDict:
            dry_run = bool(int(self._commandArgsDict['DRYRUN']))
        else:
            dry_run = False

        if 'OUTPUT' in self._commandArgsDict:
            output_dir = self._commandArgsDict['OUTPUT']
        else:
            output_dir = None

        # call auto reduction
        status, message = self._controller.reduce_auto_script(ipts_number=ipts,
                                                              run_numbers=run_number_list,
                                                              output_dir=output_dir,
                                                              is_dry_run=dry_run)

        return True, message

    def get_help(self):
        """
        override base class
        :return:
        """
        help_str = 'Auto reduction\n'
        help_str += 'Run auto reduction script for 1 run on analysis cluster:\n'
        help_str += '> AUTO, IPTS=1234, RUNS=98765\n\n'
        help_str += 'Run auto reduction script for multiple runs on analysis cluster:\n'
        help_str += '> AUTO, IPTS=1234, RUNS=98765-99999\n\n'
        help_str += 'Run auto reduction script for 1 run with user specified output directory.\n'
        help_str += '> AUTO, IPTS=1234, RUNS=98765, OUTPUT=/SNS/users/whoever/data\n'
        help_str += 'Dry-Run auto reduction script for multiple runs with user specified output directory.\n'
        help_str += '> AUTO, IPTS=1234, RUNS=98765-98777, OUTPUT=/SNS/users/whoever/data, DRYRUN=1\n'

        return help_str


class VBin(procss_vcommand.VDriveCommand):
    """
    """
    SupportedArgs = ['IPTS', 'RUN', 'CHOPRUN', 'RUNE', 'RUNS', 'BINW', 'SKIPXML', 'FOCUS_EW',
            'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'OneBank', 'NoMask', 'Tag',
            'BinFoler', 'Mytofbmax', 'Mytobmin']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNE': 'First run number',
        'RUNS': 'Last run number',

        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'OneBank': 'Add 2 bank data together (=1).',
        'Tag': '"Si/V" for instrument calibration.',
    }

    def __init__(self, controller, command_args):
        """ Initialization
        """
        procss_vcommand.VDriveCommand.__init__(self, controller, command_args)

        self._commandName = 'VBIN/VDRIVEBIN'

        self.check_command_arguments(self.SupportedArgs)

        return

    def exec_cmd(self):
        """
        Execute command: override
        """
        # check whether the any non-supported args
        input_args = self._commandArgsDict.keys()
        for arg_key in input_args:
            if arg_key not in VBin.SupportedArgs:
                raise KeyError('VBIN argument %s is not recognized.' % arg_key)
        # END-FOF

        # check and set ipts
        self.set_ipts()

        # RUNS or CHOPRUN
        try:
            run_number_list = self.parse_run_number()
        except RuntimeError as run_err:
            return False, 'Unable to parse run numbers due to {0}'.format(run_err)

        # Use result from CHOP?
        if 'CHOPRUN' in input_args:
            use_chop_data = True
        else:
            use_chop_data = False

        # bin with
        if 'BINW' in input_args:
            bin_width = float(self._commandArgsDict['BINW'])
        else:
            bin_width = 0.005

        # TODO/FIXME What is SKIPXML

        # FOCUS_EW: TODO/FIXME : anything interesting?

        # RUNV
        if 'RUNV' in input_args:
            # TODO/ISSUE/55 FIND IT AT /SNS/VULCAN/IPTS-14094/shared/Instrument
            van_run = int(self._commandArgsDict['RUNV'])
        else:
            van_run = None

        if 'FullProf' in input_args:
            output_fullprof = int(self._commandArgsDict['Fullprof']) == 1
        else:
            output_fullprof = False

        if 'Mytofbmax' in input_args:
            tof_max = float(self._commandArgsDict['Mytofbmax'])
        else:
            tof_max = None

        # scan the runs with data archive manager and add the runs to project
        archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                             run_number_list)

        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.add_runs_to_project(run_info_list)

        # set flag
        run_number_list = list()
        for run_info in run_info_list:
            run_number_list.append(run_info['run'])
        self._controller.set_runs_to_reduce(run_number_list)

        # set vanadium runs
        if van_run is not None:
            self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)

        import os
        output_dir = os.getcwd()

        # reduce
        status, ret_obj = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_dir,
                                                           vanadium=(van_run is not None))

        return status, str(ret_obj)

    def get_help(self):
        """
        get help
        :return:
        """
        help_str = 'VBIN/VDRIVEBIN: binning data (without generating log files)\n'

        for arg_str in self.SupportedArgs:
            help_str += '  %-10s: ' % arg_str
            if arg_str in self.ArgsDocDict:
                help_str += '%s\n' % self.ArgsDocDict[arg_str]
            else:
                help_str += '\n'
        # END-FOR

        # examples
        help_str += 'Examples:\n'
        help_str += '> VDRIVEBIN, IPTS=1000, RUNS=2000, RUNE=2099\n'
        help_str += '> VBIN,IPTS=14094,RUNS=96450,RUNE=96451\n'
        help_str += '> VBIN,IPTS=14094,RUNS=96450,RUNV=95542\n'

        return help_str


