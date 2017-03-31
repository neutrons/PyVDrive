import os
import procss_vcommand
import PyVDrive.lib.vulcan_util as vulcan_util

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
                     'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'OneBank', 'NoMask', 'TAG',
                     'BinFoler', 'Mytofbmax', 'Mytofbmin', 'OUTPUT']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNE': 'First run number',
        'RUNS': 'Last run number',

        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'OneBank': 'Add 2 bank data together (=1).',
        'Tag': '"Si/V" for instrument calibration.',
        'OUTPUT': 'User specified output directory. Default will be under /SNS/VULCAN/IPTS-???/shared/bin'
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
        # TODO/FIXME What is SKIPXML
        # FOCUS_EW: TODO/FIXME : anything interesting?

        # check whether the any non-supported args
        input_args = self._commandArgsDict.keys()
        for arg_key in input_args:
            if arg_key not in VBin.SupportedArgs:
                raise KeyError('VBIN argument %s is not recognized.' % arg_key)
        # END-FOF

        # check and set IPTS
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

        # binning parameters
        use_default_binning, binning_parameters = self.parse_binning()

        # RUNV
        if 'RUNV' in input_args:
            van_run = int(self._commandArgsDict['RUNV'])
            assert van_run > 0, 'Vanadium run number {0} must be positive.'.format(van_run)
        else:
            van_run = None

        # TAG
        standard_tuple = self.process_tag()

        # output directory
        if 'OUTPUT' in input_args:
            output_dir = self._commandArgsDict['OUTPUT']
        else:
            output_dir = vulcan_util.get_default_binned_directory(self._iptsNumber)

        if 'FullProf' in input_args:
            output_fullprof = int(self._commandArgsDict['Fullprof']) == 1
        else:
            output_fullprof = False

        # scan the runs with data archive manager and add the runs to project
        if use_chop_data:
            # reducing chopped data
            # set vanadium runs
            if van_run is not None:
                self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)
            status, ret_obj = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_dir,
                                                               vanadium=(van_run is not None),
                                                               standard_sample_tuple=standard_tuple,
                                                               binning_parameter=binning_parameters,
                                                               output_to_fullprof=output_fullprof)

        else:
            # reduce regular data
            archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                                 run_number_list)

            run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key)
            self._controller.add_runs_to_project(run_info_list)

            # set vanadium runs
            if van_run is not None:
                self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)

            # set flag
            run_number_list = list()
            for run_info in run_info_list:
                run_number_list.append(run_info['run'])
            self._controller.set_runs_to_reduce(run_number_list)

            # reduce by regular runs
            # TODO/FIXME/NOW - Binning parameters
            status, ret_obj = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_dir,
                                                               vanadium=(van_run is not None),
                                                               standard_sample_tuple=standard_tuple,
                                                               binning_parameters=binning_parameters,
                                                               merge=False)

        # END-IF-ELSE

        # process special tag for vanadium
        print '[DB...BAT] Standard tuple: ', standard_tuple
        if standard_tuple is not None and standard_tuple[0] == 'Vanadium':
            for run_number in run_number_list:
                standard_dir = standard_tuple[1]
                nexus_file_name = '/SNS/VULCAN/IPTS-{0}/data/VULCAN_{1}_event.nxs'.format(self._iptsNumber, run_number)
                intensity_file_name = os.path.join(standard_dir, '{0}.int'.format(run_number))
                print '[DB...BAT] Export GSAS intensity of file {0} to {1}'.format(nexus_file_name, intensity_file_name)
                vulcan_util.export_vanadium_intensity_to_file(van_nexus_file=nexus_file_name,
                                                              gsas_van_int_file=intensity_file_name)
            # END-FOR
        # END-IF

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

    def parse_binning(self):
        """
        process binning parameters configuration from inputs
        :return:
        """
        binning_parameters = None

        if not ('BINW' in self._commandArgsDict or 'Mytofbmax' in self._commandArgsDict
                or 'Mytofbmin' in self._commandArgsDict):
            # using default binning parameters as VDRIVE standard
            use_default_binning = True

        elif 'BINW' in self._commandArgsDict and abs(self._commandArgsDict['BINW'] - 0.005) < 1.0E-7:
            # Bin width is same as default
            use_default_binning = True

        else:
            use_default_binning = False
            if 'BINW' in self._commandArgsDict:
                bin_width = float(self._commandArgsDict['BINW'])
            else:
                bin_width = 0.005  # set to default in case only TOF range is customized

            if 'Mytofbmax' in self._commandArgsDict:
                tof_max = float(self._commandArgsDict['Mytofbmax'])
            else:
                tof_max = None

            if 'Mytofbmin' in self._commandArgsDict:
                tof_min = float(self._commandArgsDict['Mytofbmin'])
            else:
                tof_min = None

            binning_parameters = (tof_min, bin_width, tof_max)
        # END-IF-ELSE

        return use_default_binning, binning_parameters

    def process_tag(self):
        """
        process for 'TAG'
        for example
            TAG='V'  to /SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium
            TAG='Si' to /SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Si

        :return: standard_tuple = material_type, standard_dir, standard_file
        """
        if 'TAG' in self._commandArgsDict:
            # process material type
            material_type = self._commandArgsDict['TAG']
            material_type = material_type.lower()

            standard_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard'
            if os.access(standard_dir, os.W_OK) is False:
                # if standard VDRIVE default directory is not writable, then use the local one
                # very likely the current PyVdrive is running in a testing mode.
                standard_dir = os.getcwd()

            if material_type == 'si':
                material_type = 'Si'
                standard_dir = os.path.join(standard_dir, 'Si')
                standard_file = 'SiRecord.txt'
            elif material_type == 'v':
                material_type = 'Vanadium'
                standard_dir = os.path.join(standard_dir, 'Vanadium')
                standard_file = 'VRecord.txt'
            elif material_type == 'c':
                material_type = 'C'
                standard_dir = os.path.join(standard_dir, 'C')
                standard_file = 'CRecord.txt'
            elif material_type == 'ceo2':
                material_type = 'CeO3'
                standard_dir = os.path.join(standard_dir, 'CeO2')
                standard_file = 'CeO2Record.txt'
            elif len(material_type) > 0:
                # create arbitrary tag
                # use the user specified TAG as the type of material
                material_type = self._commandArgsDict['TAG']
                standard_dir = os.path.join(standard_dir, material_type)
                standard_file = '{0}Record.txt'.format(material_type)
            else:
                raise RuntimeError('TAG cannot be an empty string.')
            # END-IF-ELSE

            standard_tuple = material_type, standard_dir, standard_file

            # create workspace if not existing
            if os.path.exists(standard_dir) is False:
                self._create_standard_directory(standard_dir)
        else:
            standard_tuple = None

        return standard_tuple

    @staticmethod
    def _create_standard_directory(tag_dir):
        """
        create a directory for standard
        :param tag_dir:
        :return:
        """
        assert isinstance(tag_dir, str), 'Standard directory {0} must be a string but not a {1}.' \
                                         ''.format(tag_dir, type(tag_dir))
        try:
            os.mkdir(tag_dir)
        except IOError as io_error:
            raise RuntimeError('Unable to create directory {0} due to {1}'.format(tag_dir, io_error))
        except OSError as os_error:
            raise RuntimeError('Unable to create directory {0} due to {1}'.format(tag_dir, os_error))

        # change access control
        os.chmod(tag_dir, 0777)

        return
