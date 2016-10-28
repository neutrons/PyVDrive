import procss_vcommand

# VDRIVEBIN, i.e., VBIN
# 
# Example:
# cmd = VBIN(conroller, args)
# cmd.run()


class VBin(procss_vcommand.VDriveCommand):
    """
    """
    SupportedArgs = ['IPTS', 'RUN', 'CHOPRUN', 'RUNE', 'RUNS', 'BINW', 'SKIPXML', 'FOCUS_EW',
            'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'OneBank', 'NoMask', 'Tag',
            'BinFoler', 'Mytofbmax', 'Mytobmin']

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
        input_args = self._commandArgList.keys()
        for arg_key in input_args:
            if arg_key not in VBin.SupportedArgs:
                raise KeyError('VBIN argument %s is not recognized.' % arg_key)
        # END-FOF

        # check and set ipts
        self.set_ipts()

        # RUNS or CHOPRUN
        run_start = int(self._commandArgList['RUNS'])
        run_end = int(self._commandArgList['RUNE'])
        assert 0 < run_start < run_end, 'It is impossible to have run_start = %d and run_end = %d' \
                                        '' % (run_start, run_end)
        
        # Use result from CHOP?
        if 'CHOPRUN' in input_args:
            use_chop_data = True
        else:
            use_chop_data = False

        # bin with
        if 'BINW' in input_args:
            bin_width = float(self._commandArgList['BINW'])
        else:
            bin_width = 0.005

        # TODO/FIXME What is SKIPXML

        # FOCUS_EW: TODO/FIXME : anything interesting?

        # RUNV
        if 'RUNV' in input_args:
            van_run = int(self._commandArgList['RUNV'])
        else:
            van_run = None

        if 'FullProf' in input_args:
            output_fullprof = int(self._commandArgList['Fullprof']) == 1
        else:
            output_fullprof = False

        if 'Mytofbmax' in input_args:
            tof_max = float(self._commandArgList['Mytofbmax'])
        else:
            tof_max = None

        # set the runs
        archive_key, error_message = self._controller.archive_manager.scan_archive(self._iptsNumber, run_start,
                                                                                   run_end)
        run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
        self._controller.project.add_runs(run_info_list)

        # set flag
        run_number_list = list()
        for run_info in run_info_list:
            run_number_list.append(run_info['run'])
        self._controller.set_runs_to_reduce(run_number_list)

        # reduce
        self._controller.reduce_data_set(norm_by_vanadium=(van_run is not None))

        return True, error_message

    @staticmethod
    def get_help():
        """

        :return:
        """
        help_str = 'VBIN/VDRIVEBIN: binning data\n' \
                   'Example: VDRIVEBIN, IPTS=1000, RUNS=2000, RUNE=2099\n' \
                   '\n' \
                   'Debug: "VBIN,IPTS=14094,RUNS=96450,RUNE=96451"'

        return help_str


