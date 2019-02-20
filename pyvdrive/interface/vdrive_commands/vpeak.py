from process_vcommand import VDriveCommand
import os


class VanadiumPeak(VDriveCommand):
    """ process vanadium peaks
    """
    SupportedArgs = ['IPTS', 'RUNV', 'REDUCEDVANADIUM', 'HELP', 'NSMOOTH', 'SHIFT', 'OUTPUT',
                     'BINFOLDER']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'REDUCEDVANADIUM': 'Path to a reduced vanadium file (GSAS or ProcessedNeXus or HDF5)',
        'SHIFT': 'the chopper center is shift to large lambda aggressively.',
        'NSMOOTH': 'the number of points to be used in the boxcar smoothing algorithm, the bigger the smoother.',
        'OUTPUT': 'the directory where the smooth vanadium gsas file will be saved other than default.',
        'BINFOLDER': 'an alias of vanadium ouput',
        'HELP': 'Launch Peak processing UI to process vanadium with visualization'
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
        # obtain the reduced Vanadium GSAS/ProcessedNexus file
        if 'REDUCEDVANADIUM' in self._commandArgsDict:
            # user-specified vanadium file
            van_file_name = self._commandArgsDict['REDUCEDVANADIUM']
            if not os.path.exists(van_file_name):
                return False, 'blabla'
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
            # TODO - NIGHT - shall find the fine binned ProcessedNexus first!
            van_file_name = self._controller.archive_manager.locate_gsas(ipts_number=self._iptsNumber,
                                                                         run_number=self._vanRunNumber)
            if van_file_name is None:
                return False, 'blabla'
        # END-IF-ELSE

        if 'ONEBANK' in self._commandArgsDict:
            self._mergeToOneBank = bool(int(self._commandArgsDict['ONEBANK']))

        if 'SHIFT' in self._commandArgsDict:
            self._doShift = bool(int(self._commandArgsDict['SHIFT']))

        if 'HELP' in self._commandArgsDict:
            do_launch_gui = bool(int(self._commandArgsDict['GUI']))
        else:
            do_launch_gui = False

        # init and load gsas file
        if self._iptsNumber and self._vanRunNumber:
            # the output file name
            out_file_name = self._process_output_file()
            # load GSAS file or ProcessedNeXus file
            van_file_name = self._controller.archive_manager.locate_gsas(self._iptsNumber, self._vanRunNumber)
            self._myVanDataKey = self._controller.project.data_loading_manager.load_binned_data(van_file_name, 'gsas',
                                                                                        max_int=10, prefix='van',
                                                                                        data_key=None,
                                                                                        target_unit='dSpacing')

            # load logs for future
            if True:
                # only support vanadium now
                sample_log_ws_name = self._controller.load_nexus_file(self._iptsNumber, self._vanRunNumber, None, True)
            else:
                sample_log_ws_name = None
            self._controller.project.vanadium_processing_manager.init_session(self._myVanDataKey,
                                                                              self._iptsNumber,
                                                                              self._vanRunNumber,
                                                                              out_file_name,
                                                                              sample_log_ws_name)
        elif not do_launch_gui:
            return False, 'IPTS number and run number is not given!'
        else:
            # only option HELP/launching GUI given: nothing to init
            self._myVanDataKey = None

        if do_launch_gui:
            # launch GUI.  load vanadium data now!
            status = True
            ret_obj = 'pop'
        else:
            # execute vanadium strip command
            van_processor = self._controller.project.vanadium_processing_manager
            status, ret_obj = van_processor.process_vanadium()   # do_shift=self._doShift)
        # END-IF-ELSE

        return status, ret_obj

    def _process_output_file(self):
        """ Determine the output GSAS file name
        :return:
        """
        if 'OUTPUT' in self._commandArgsDict or 'BINFOLDER' in self._commandArgsDict:
            # user specified
            if 'OUTPUT' in self._commandArgsDict:
                output_gsas_file = str(self._commandArgsDict['OUTPUT'])
            else:
                output_gsas_file = str(self._commandArgsDict['BINFOLDER'])
            if os.path.isdir(output_gsas_file):
                output_gsas_file = os.path.join(output_gsas_file, '{}-s.gda'.format(self._vanRunNumber))
        else:
            # using archive
            output_gsas_file = self._controller.archive_manager.get_archived_vanadium_gsas_name()

        return output_gsas_file

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
