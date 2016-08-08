# VDRIVEBIN, i.e., VBIN
# 
# Example:
# cmd = VBIN(conroller, args)
# cmd.run()

class VBin(object):
    """
    """
    SupportedArgs = ['IPTS', 'RUN', 'CHOPRUN', 'RUNE', 'RUNS', 'BINW', 'SKIPXML', 'FOCUS_EW',
            'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'OneBank', 'NoMask', 'Tag',
            'BinFoler', 'Mytofbmax', 'Mytobmin']

    def __init__(self, controller, command_args):
        """
        """
        assert isinstance(controller, VdriveAPI)
        assert isinstance(command_args, dict)

        # set controller
        self._controller = controller

        # set arguments
        self._commandArgList = command_args

        return

    def exec(self):
        """
        Execute command
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

        # run
        for run_number in range(run_start, run_end+1):
            self._controller.set_bin_parameters(self._iptsNumber, run=run_number,
                    bin_size, fullprof, vanadium_run=van_run)

        return



    def set_ipts(self):
        """
        Set IPTS
        """ 
        # TODO/FIXME - promote to base class
        self._iptsNumber = int(self._commandArgList['IPTS'])

        assert 0 < self._iptsNumber, 'IPTS number %d is an invalid integer.' % self._iptsNumber

        return

