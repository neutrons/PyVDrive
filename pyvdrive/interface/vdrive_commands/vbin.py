import os
import procss_vcommand
import pyvdrive.lib.vulcan_util as vulcan_util

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
            run_number_list = self.parse_run_number()
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
    SupportedArgs = ['IPTS', 'RUN', 'CHOPRUN', 'RUNE', 'RUNS', 'BANKS', 'BINW', 'SKIPXML', 'FOCUS_EW',
                     'RUNV', 'IParm', 'FullProf', 'NoGSAS', 'PlotFlag', 'ONEBANK', 'NoMask', 'TAG',
                     'BinFolder', 'Mytofbmax', 'Mytofbmin', 'OUTPUT', 'GROUP', 'VERSION',
                     'ROI', 'MASK']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNE': 'First run number',
        'RUNS': 'Last run number',
        'BANKS': 'Number of banks in output GSAS file.  Allowed values are 3, 7 and 27.  Default is 3.',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'OneBank': 'Add 2 bank data together (=1).',
        'GROUP': 'User specified a special group file other than usual 3/7/27 banks. (It cannot be used with BANKS)',
        'Mytofbmin': 'User defined TOF min in binning parameter',
        'Tag': '"Si/V" for instrument calibration.',
        'ROI': 'Files for Mantid made region of interest file in XML format',
        'MASK': 'Files for Mantid made mask file in XML format',
        'OUTPUT': 'User specified output directory. Default will be under /SNS/VULCAN/IPTS-???/shared/bin',
        'VERSION': 'User specified version of reduction algorithm.  Mantid conventional = 1, PyVDrive simplified = 2'
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

        # check and set IPTS
        try:
            self.set_ipts()
        except RuntimeError as run_err:
            return False, 'Error in setting IPTS: {0}'.format(run_err)

        # RUNS or CHOPRUN
        try:
            run_number_list = self.parse_run_number()
        except RuntimeError as run_err:
            return False, 'Unable to parse run numbers due to {0}'.format(run_err)

        # Use result from CHOP?
        if 'CHOPRUN' in self._commandArgsDict:
            use_chop_data = True
            chop_run_number = int(self._commandArgsDict['CHOPRUN'])
        else:
            use_chop_data = False
            chop_run_number = None

        # binning parameters
        use_default_binning, binning_parameters = self.parse_binning()

        # RUNV
        if 'RUNV' in self._commandArgsDict:
            van_run = int(self._commandArgsDict['RUNV'])
            assert van_run > 0, 'Vanadium run number {0} must be positive.'.format(van_run)
        else:
            van_run = None

        # TAG
        standard_tuple = self.process_tag()

        # output directory
        if 'OUTPUT' in self._commandArgsDict:
            output_dir = self._commandArgsDict['OUTPUT']
        else:
            output_dir = vulcan_util.get_default_binned_directory(self._iptsNumber)

        # Option FullProf is temporarily disabled
        # if 'FULLPROF' in self._commandArgsDict:
        #     output_fullprof = int(self._commandArgsDict['Fullprof']) == 1
        # else:
        #     output_fullprof = False

        if 'ONEBANK' in self._commandArgsDict:
            merge_to_one_bank = bool(int(self._commandArgsDict['ONEBANK']))
        else:
            merge_to_one_bank = False

        # banks/grouping
        if 'BANKS' in self._commandArgsDict:
            bank_group = int(self._commandArgsDict['BANKS'])
            if bank_group not in [3, 7, 27]:
                raise RuntimeError('BANKS can only be 3 (east, west, high-angle), 7 (6+1)), or 27 (9+9+9).'
                                   'So {0} is not allowed.'.format(bank_group))
        elif 'GROUP' in self._commandArgsDict:
            # user specified calibration file for group
            user_group_calib_name = self._commandArgsDict['GROUP']
            if user_group_calib_name == '':
                return False, 'User specified group/calibration file is empty.'
            bank_group = user_group_calib_name
        else:
            # default
            bank_group = 3

        # region of interest or mask file
        if 'ROI' in self._commandArgsDict:
            roi_file_names = self.get_argument_as_list('ROI', str)
        else:
            roi_file_names = list()
        if 'MASK' in self._commandArgsDict:
            mask_file_names = self.get_argument_as_list('MASK', str)
        else:
            mask_file_names = list()

        # reduction algorithm version
        if 'VERSION' in self._commandArgsDict:
            reduction_alg_ver = int(self._commandArgsDict['VERSION'])
        else:
            reduction_alg_ver = 1

        # scan the runs with data archive manager and add the runs to project
        if use_chop_data:
            # reducing chopped data
            # set vanadium runs
            if van_run is not None:
                self._controller.set_vanadium_to_runs(self._iptsNumber, run_number_list, van_run)
            status, message = self._controller.reduce_chopped_data_set(ipts_number=self._iptsNumber,
                                                                       run_number=chop_run_number,
                                                                       chop_child_list=run_number_list,
                                                                       raw_data_directory=None,
                                                                       output_directory=output_dir,
                                                                       vanadium=(van_run is not None),
                                                                       binning_parameters=binning_parameters,
                                                                       align_to_vdrive_bin=use_default_binning,
                                                                       num_banks=bank_group,
                                                                       merge_banks=merge_to_one_bank,
                                                                       roi_list=roi_file_names,
                                                                       mask_list=mask_file_names)

        else:
            # reduce event data without chopping
            try:
                archive_key, error_message = self._controller.archive_manager.scan_runs_from_archive(self._iptsNumber,
                                                                                                     run_number_list)
            except RuntimeError as run_err:
                return False, 'Failed to find nexus file for IPTS {0} Runs {1} due to {2}' \
                              ''.format(self._iptsNumber, run_number_list, run_err)

            run_info_list = self._controller.archive_manager.get_experiment_run_info(archive_key, run_number_list)
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
            status, message = self._controller.reduce_data_set(auto_reduce=False, output_directory=output_dir,
                                                               merge_banks=merge_to_one_bank,
                                                               vanadium=(van_run is not None),
                                                               standard_sample_tuple=standard_tuple,
                                                               binning_parameters=binning_parameters,
                                                               merge_runs=False,
                                                               num_banks=bank_group,
                                                               version=reduction_alg_ver,
                                                               roi_list=roi_file_names,
                                                               mask_list=mask_file_names)

        # END-IF-ELSE

        # process special tag for vanadium: create intensity file for each detector pixel
        if use_chop_data is False and standard_tuple is not None and standard_tuple[0] == 'Vanadium':
            for run_number in run_number_list:
                standard_dir = standard_tuple[1]
                # vanadium NeXus file
                nexus_file_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(self._iptsNumber, run_number)
                if os.path.exists(nexus_file_name) is False:
                    nexus_file_name = '/SNS/VULCAN/IPTS-{0}/data/VULCAN_{1}_event.nxs' \
                                      ''.format(self._iptsNumber, run_number)

                # get intensity file
                intensity_file_name = os.path.join(standard_dir, '{0}.int'.format(run_number))
                write_intensity = True
                if os.path.exists(intensity_file_name):
                    try:
                        os.remove(intensity_file_name)
                    except OSError as err:
                        message += 'Unable to write vanadium intensity to file {0} due to {1}\n' \
                                   ''.format(intensity_file_name, err)
                        status = False
                        write_intensity = False
                
                if write_intensity:
                    message += '\nExport GSAS intensity of file {0} to {1}'.format(nexus_file_name, intensity_file_name)
                    vulcan_util.export_vanadium_intensity_to_file(van_nexus_file=nexus_file_name,
                                                                  gsas_van_int_file=intensity_file_name)
                    os.chmod(intensity_file_name, 0666)

            # END-FOR
        # END-IF

        return status, message

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
        help_str += '> VBIN,RUNS=152782, RUNE=153144, BANKS=7\n'
        help_str += 'New (in test):\n'
        help_str += '> VBIN,IPTS=Latest,RUNS=Latest,VERSION=2\n'
        help_str += '> VBIN,IPTS=Latest,RUNS=Latest,GROUP="~/Projects/VULCAN/PoleFigure/l2_group_cal.h5\n'
        help_str += 'Support list of ROI and Mask\n'
        help_str += '> VBIN,IPTS=Latest,RUNS=Latest,ROI=[file1.xml, file2.xml]'

        return help_str

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
