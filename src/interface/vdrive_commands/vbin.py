import procss_vcommand

# VDRIVEBIN, i.e., VBIN
# 
# Example:
# cmd = VBIN(conroller, args)
# cmd.run()

class VBin(procss_vcommand.VDriveCommandProcessor):
    """
    """
    SupportedArgs = ['IPTS', 'RUN', 'CHOPRUN', 'RUNE', 'RUNS', 'BINW', 'SKIPXML', 'FOCUS_EW',
            'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'OneBank', 'NoMask', 'Tag',
            'BinFoler', 'Mytofbmax', 'Mytobmin']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        procss_vcommand.VDriveCommandProcessor.__init__(self, controller, command_args)

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
        assert 0 < run_start < run_end, 'It is impossible to have run_start = %d and run_end = %d' % (run_start, run_end)
        
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
        run_info_list = self._controller.get_runs(start_run=run_start, end_run=run_end)
        self._controller.add_runs(run_info_list)

        # reduce
        self._controller.reduce_data_set(norm_by_vanadium=(van_run is not None))

        return


