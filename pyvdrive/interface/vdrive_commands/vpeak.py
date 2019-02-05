from procss_vcommand import VDriveCommand


class VanadiumPeak(VDriveCommand):
    """ process vanadium peaks
    """
    SupportedArgs = ['IPTS', 'RUNV', 'REDUCEDVANADIUM', 'VIEWER', 'NSMOOTH', 'ONEBANK', 'SHIFT', 'OUTPUT',
                     'BINFOLDER']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'REDUCEDVANADIUM': 'Path to a reduced vanadium file (GSAS or ProcessedNeXus or HDF5)',
        'ONEBANK': 'Add 2 bank data together (=1).',
        'SHIFT': 'the chopper center is shift to large lambda aggressively.',
        'NSMOOTH': 'the number of points to be used in the boxcar smoothing algorithm, the bigger the smoother.',
        'OUTPUT': 'the directory where the smooth vanadium gsas file will be saved other than default.',
        'BINFOLDER': 'an alias of vanadium ouput',
        'GUI': 'Launch Peak processing UI to process vanadium with visualization'
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
        self._myVanDataKey = None

        return

    def exec_cmd(self):
        """
        Execute command: override
        """
        if 'REDUCEDVANADIUM' in self._commandArgsDict:
            # user-specified vanadium file
            van_file_name = self._commandArgsDict['REDUCEDVANADIUM']
        else:
            # parse IPTS
            try:
                self.set_ipts()
            except RuntimeError as run_err:
                return False, 'Without option'.format(run_err)

            # get run v
            if 'RUNV' not in self._commandArgsDict:
                return False, 'RUNV must be specified!'

            # parse the parameters
            try:
                self._vanRunNumber = int(self._commandArgsDict['RUNV'])
            except ValueError as val_err:
                raise RuntimeError('Unable to convert RUNV={} to integer due to {}'
                                   ''.format(self._commandArgsDict['RUNV'], val_err))

            # get the vanadium file
            van_file_name = self._controller.archive_manager.locate_reduced_data(ipts_nubmer=self._iptsNumber,
                                                                                 run_number=self._vanRunNumber)
        # END-IF-ELSE

        if 'ONEBANK' in self._commandArgsDict:
            self._mergeToOneBank = bool(int(self._commandArgsDict['ONEBANK']))

        if 'SHIFT' in self._commandArgsDict:
            self._doShift = bool(int(self._commandArgsDict['SHIFT']))

        if 'GUI' in self._commandArgsDict:
            do_launch_gui = bool(int(self._commandArgsDict['GUI']))
        else:
            do_launch_gui = False

        if 'OUTPUT' in self._commandArgsDict:
            local_output_dir = str(self._commandArgsDict['OUTPUT'])
        else:
            local_output_dir = None

        # check vanadium run: if not reduced, then
        if not self._controller.archive_manager.has_reduced_run(self._iptsNumber, self._vanRunNumber):
            return False, 'IPTS-{} Vanadium Run-{} has not been reduced.'

        # return to pop
        if do_launch_gui:
            # launch GUI.  load vanadium data now!
            self._myVanDataKey = self._controller.archive_manager.load_reduced_data(reduced_file=van_file_name)
            status = True
            ret_obj = 'pop'

        else:
            # execute vanadium strip command
            status, ret_obj = self._controller.process_vanadium_run(ipts_number=self._iptsNumber,
                                                                    run_number=self._vanRunNumber,
                                                                    reduced_file=van_file_name,
                                                                    one_bank=self._mergeToOneBank,
                                                                    do_shift=self._doShift,
                                                                    local_output=local_output_dir)

        return status, ret_obj

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
        help_str += '> VPEAK, IPTS=1000, RUNV=5000\n'
        help_str += '> VPEAK, IPTS=16062, RUNV=132261\n'
        # /SNS/VULCAN/IPTS-16062/0/132261/NeXus/VULCAN_132261_event.nxs'

        return help_str

    def get_loaded_data(self):
        """
        get the loaded vanadium's data key in controller
        :return:
        """
        if self._myVanDataKey is None:
            raise RuntimeError('There is no vanadium data loaded.')

        return self._myVanDataKey

    def get_vanadium_run(self):
        """
        get the vanadium run number from command
        :return:
        """
        return self._vanRunNumber

    @property
    def to_merge_to_one_bank(self):
        """
        get the user option whether the reduced data will be merged to one peak
        :return:
        """
        return self._mergeToOneBank

    @property
    def to_shift(self):
        """
        get the user option whether the vanadium peak will be shifted
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
