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
        :return:
        """
        try:
            ipts = int(self._commandArgList['IPTS'])
        except KeyError:
            return False, 'IPTS must be given!'
        else:
            print '[DB...BAT] IPTS = ', ipts

        run_numbers_str = 'NO DEFINED'
        try:
            run_numbers_str = self._commandArgList['RUNS']
            run_number_list = self.split_run_numbers(run_numbers_str)
            if len(run_number_list) == 1 and 'RUNE' in self._commandArgList:
                # allow RUNE if RUNS is just 1 value
                run_end = int(self._commandArgList['RUNE'])
                run_number_list = range(run_number_list[0], run_end)
        except KeyError:
            return False, 'RUNS number must be given.'
        except ValueError:
            return False, 'RUNS number string %s cannot be parsed.' % run_numbers_str
        except TypeError:
            return False, 'RUNS number string %s cannot be parsed due to TypeError.' % run_numbers_str
        else:
            print '[DB...BAT] Runs = ', run_number_list

        if 'DRYRUN' in self._commandArgList:
            dry_run = bool(int(self._commandArgList['DRYRUN']))
        else:
            dry_run = False

        if 'OUTPUT' in self._commandArgList:
            output_dir = self._commandArgList['OUTPUT']
        else:
            output_dir = None

        # call auto reduction
        status, message = self._controller.reduce_auto_script(ipts_number=ipts,
                                                              run_numbers=run_number_list,
                                                              output_dir=output_dir,
                                                              is_dry_run=dry_run)

        return True, message

    @staticmethod
    def split_run_numbers(run_numbers_str):
        """
        split run numbers from a string.
        example: run1, run2-run10, run11, run12,
        :param run_numbers_str:
        :return:
        """
        def pop_range(range_str):
            """
            replace a range a - b to a list such as a, a1, a2, .., b
            :param range_str:
            :return:
            """
            terms = range_str.split('-')
            start_value = int(terms[0])
            stop_value = int(terms[1])
            assert start_value <= stop_value, 'Start value %d must be smaller or euqal to stop value %s.' \
                                              '' % (start_value, stop_value)
            return range(start_value, stop_value+1)

        run_numbers_str = run_numbers_str.replace(' ', '')
        terms = run_numbers_str.split(',')
        run_number_list = list()
        for term in terms:
            if term.count('-') == 0:
                run_number_list.append(int(term))
            elif term.count('-') == 1:
                run_number_list.extend(pop_range(term))
            else:
                raise ValueError('Single term contains more than 2 -')
        # END-FOR

        return run_number_list

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

        return help_str


