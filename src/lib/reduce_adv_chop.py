# Reduction with advanced chopping methods
# It is split from ReduceVulcanData in reduce_Vulcan.py
import os
import mantid.simpleapi as mantidsimple
from mantid.api import AnalysisDataService, ITableWorkspace, MatrixWorkspace
from mantid.dataobjects import SplittersWorkspace
import chop_utility
import reduce_VULCAN

MAX_ALLOWED_WORKSPACES = 200


class AdvancedChopReduce(reduce_VULCAN.ReduceVulcanData):
    """
    Advanced data chopping and reduction control class, which is derived from 
    standard Vulcan reduction control class
    """
    def __init__(self, reduce_setup):
        """
        initialization
        :param reduce_setup:
        """
        super(AdvancedChopReduce, self).__init__(reduce_setup)

        return

    def chop_reduce(self, chop_dir):
        """
        Chop and reduce
        :except: RuntimeError if the target directory for chopped data does not exist
        :return:
        """
        # check whether it is good to go
        assert isinstance(self._reductionSetup, reduce_VULCAN.ReductionSetup), 'ReductionSetup is not correct.'
        # configure the ReductionSetup
        self._reductionSetup.process_configurations()
        chop_dir = self._reductionSetup.get_chopped_directory(gsas=True, check_write_permission=True)

        # get splitters workspaces
        split_ws_name, split_info_table = self._reductionSetup.get_splitters(throw_not_set=True)

        # TEST/ISSUE/NOW
        # call SNSPowderReduction for chopping and reducing
        args = dict()
        args['PreserveEvents'] = True
        args['CalibrationFile'] = self._reductionSetup.get_focus_file()
        args['CharacterizationRunsFile'] = self._reductionSetup.get_characterization_file()
        # args['Binning'] = "-0.001"
        args['Binning'] = self._reductionSetup.binning_parameters
        args['SaveAS'] = ""
        args['OutputDirectory']=self._reductionSetup.get_gsas_dir()
        args['NormalizeByCurrent']=False
        args['FilterBadPulses']=0
        args['CompressTOFTolerance'] = 0.
        args['FrequencyLogNames'] = "skf1.speed"
        args['WaveLengthLogNames'] = "skf12.lambda"
        mantidsimple.SNSPowderReduction(**args)

        # mantidsimple.SNSPowderReduction(Filename=self._reductionSetup.get_event_file(),
        #                                 PreserveEvents=True,
        #                                 CalibrationFile=self._reductionSetup.get_focus_file(),
        #                                 CharacterizationRunsFile=self._reductionSetup.get_characterization_file(),
        #                                 Binning="-0.001",
        #                                 SaveAS="",
        #                                 OutputDirectory=self._reductionSetup.get_gsas_dir(),
        #                                 NormalizeByCurrent=False,
        #                                 FilterBadPulses=0,
        #                                 CompressTOFTolerance=0.,
        #                                 FrequencyLogNames="skf1.speed",
        #                                 WaveLengthLogNames="skf12.lambda",
        #                                 SplittersWorkspace=split_ws_name,
        #                                 SplitInformationWorkspace=split_info_table)

        # create GSAS file for split workspaces
        # convert the chopped data to GSAS file in VULCAN's special bin
        info_table = AnalysisDataService.retrieve(split_info_table)
        num_split_ws = info_table.rowCount()

        target_chop_index_list = self.get_target_split_ws_index(split_ws_name)

        everything_is_right = True

        # find out a naming issue
        run_str = '%d' % self._reductionSetup.get_run_number()
        if chop_dir.count(run_str) == 0:
            use_special_name = True
        else:
            use_special_name = False

        chopped_ws_name_list = list()

        print '[DB...BAT] Output workspace number: {0}'.format(num_split_ws)
        message = 'Output GSAS files include:\n'

        for i_ws in range(num_split_ws):
            # get the split workspace's name
            ws_index = int(info_table.cell(i_ws, 0))
            reduced_ws_name = 'VULCAN_%d_%d' % (self._reductionSetup.get_run_number(), ws_index)

            # check whether the proposed-chopped workspace does exist
            if AnalysisDataService.doesExist(reduced_ws_name):
                chopped_ws_name_list.append(reduced_ws_name)
            else:
                # there won't be a workspace produced if there is no neutron event within the range.
                if ws_index in target_chop_index_list:
                    message += 'Reduced workspace %s does not exist. Investigate it!\n' % reduced_ws_name
                    everything_is_right = False
                else:
                    message += 'Input reduced workspace %s does not exist, maybe no neutron.\n' % reduced_ws_name
                continue

            # convert unit and save for VULCAN-specific GSAS
            tof_ws_name = "VULCAN_%d_TOF" % self._reductionSetup.get_run_number()
            mantidsimple.ConvertUnits(InputWorkspace=reduced_ws_name,
                                      OutputWorkspace=tof_ws_name,
                                      Target="TOF",
                                      EMode="Elastic",
                                      AlignBins=False)

            # overwrite the original file
            vdrive_bin_ws_name = reduced_ws_name

            # it might be tricky to give out the name of GSAS
            if use_special_name:
                gsas_file_name = os.path.join(chop_dir, '%d_%d.gda' % (self._reductionSetup.get_run_number(),
                                                                       ws_index+1))
            else:
                gsas_file_name = os.path.join(chop_dir, '%d.gda' % (ws_index + 1))

            # save to VULCAN GSAS and add a property as Note
            mantidsimple.SaveVulcanGSS(InputWorkspace=tof_ws_name,
                                       BinFilename=self._reductionSetup.get_vulcan_bin_file(),
                                       OutputWorkspace=vdrive_bin_ws_name,
                                       GSSFilename=gsas_file_name,
                                       IPTS=self._reductionSetup.get_ipts_number(),
                                       GSSParmFilename="Vulcan.prm")

            # Add special property to output workspace
            final_ws = AnalysisDataService.retrieve(vdrive_bin_ws_name)
            final_ws.getRun().addProperty('VDriveBin', True, replace=True)

            # update message
            message += '%d-th: %s\n' % (i_ws, gsas_file_name)

        # END-FOR

        return everything_is_right, message, chopped_ws_name_list

    def chop_and_reduce_large_output(self, chop_dir):
        """
        Chop and reduce in the special case of large amount of output.
        Calling SNSPowderReduction() will have to re-load the data, which is time consuming.  Therefore,
        the workflow is to
        1. reduce the event data by SNSPowderReduction to 2-spectrum event workspace, whose events are not compressed
        2. chop the reduced workspace with limited amount of slicers a time
        :param chop_dir:
        :return:
        """
        # check whether it is good to go
        assert isinstance(self._reductionSetup, reduce_VULCAN.ReductionSetup), 'ReductionSetup is not correct.'
        # configure the ReductionSetup
        self._reductionSetup.process_configurations()

        # check chopping directory
        assert isinstance(chop_dir, str) and os.path.exists(chop_dir), 'Chopped data directory {0} (of type {1}) ' \
                                                                       'must be a string and exist.' \
                                                                       ''.format(chop_dir, type(chop_dir))

        # get splitters workspaces
        split_ws_name, split_info_table = self._reductionSetup.get_splitters(throw_not_set=True)

        # construct reduction argument diction
        sns_arg_dict = dict()
        sns_arg_dict['Filename'] = self._reductionSetup.get_event_file()
        sns_arg_dict['CalibrationFile'] = self._reductionSetup.get_focus_file()
        sns_arg_dict['CharacterizationRunsFile'] = self._reductionSetup.get_characterization_file()
        sns_arg_dict['PreserveEvents'] = True
        sns_arg_dict['Binning'] = '-0.001'
        sns_arg_dict['SaveAS'] = ''
        sns_arg_dict['OutputDirectory'] = self._reductionSetup.get_gsas_dir()
        sns_arg_dict['NormalizeByCurrent'] = False
        sns_arg_dict['FilterBadPulses'] = 0
        sns_arg_dict['CompressTOFTolerance'] = 0.  # do not compress TOF events for further chopping
        sns_arg_dict['FrequencyLogNames'] = "skf1.speed"
        sns_arg_dict['WaveLengthLogNames'] = "skf12.lambda"

        # for key in sns_arg_dict.keys():
        #     print key, ':', sns_arg_dict[key]

        # if the number of output workspaces are too much, it could cause severe memory issue.
        num_outputs = self.get_number_chopped_ws(split_ws_name)
        NUM_TARGET_WS_IN_MEM = 40
        num_loops = num_outputs / NUM_TARGET_WS_IN_MEM

        message = 'Output GSAS files include:\n'

        if num_outputs % NUM_TARGET_WS_IN_MEM > 0:
            num_loops += 1

        gsas_index = 1
        everything_is_right = True

        # TODO/FIXME/NOT TRUE/shall use the real run start time from workspace
        split_ws = AnalysisDataService.retrieve(split_ws_name)
        run_start_time_ns = int(split_ws.cell(0, 0))

        for i_loop in range(num_loops):
            # get the partial splitters workspaces
            sub_split_ws = self.get_sub_splitters(i_loop * NUM_TARGET_WS_IN_MEM, (i_loop + 1) * NUM_TARGET_WS_IN_MEM,
                                                  run_start_ns=run_start_time_ns)  # run_start_time.totalNanoseconds())

            sns_arg_dict['SplittersWorkspace'] = sub_split_ws
            sns_arg_dict['SplitInformationWorkspace'] = split_info_table

            # do regular reduction
            results = mantidsimple.SNSPowderReduction(**sns_arg_dict)
            chopped_ws_name_list = list()
            vulcan_bin_ws_list = list()
            for item in results:
                if isinstance(item, ITableWorkspace):
                    # ignore
                    pass
                elif isinstance(item, MatrixWorkspace):
                    # result
                    reduced_ws_name = item.name()
                    chopped_ws_name_list.append(reduced_ws_name)
                else:
                    # unknown
                    print '[ERROR] Unknown returned type (from SNSPowderReduction): {0} of type {1}' \
                          ''.format(item, type(item))
            # END-FOR

            # convert the chopped workspaces to VULCAN-style GSAS file
            everything_is_right = True
            for chopped_ws_name in chopped_ws_name_list:
                # get the split workspace's name
                print '[DB...BAT] Process log of chopped workspace {0}: '.format(chopped_ws_name)

                # check whether the proposed-chopped workspace does exist
                if AnalysisDataService.doesExist(chopped_ws_name):
                    pass
                else:
                    # there won't be a workspace produced if there is no neutron event within the range.
                    message += 'Reduced workspace {0} does not exist. Investigate it!\n'.format(reduced_ws_name)
                    everything_is_right = False

                # convert unit and save for VULCAN-specific GSAS
                tof_ws_name = '{0}_Vulcan_{1}'.format(os.path.basename(sns_arg_dict['Filename']).split('.')[0],
                                                      gsas_index)
                mantidsimple.ConvertUnits(InputWorkspace=chopped_ws_name,
                                          OutputWorkspace=tof_ws_name,
                                          Target="TOF",
                                          EMode="Elastic",
                                          AlignBins=False)
                vulcan_bin_ws_list.append(tof_ws_name)

                # overwrite the original file
                vdrive_bin_ws_name = chopped_ws_name

                # it might be tricky to give out the name of GSAS
                gsas_file_name = os.path.join(chop_dir, '{0}.gda'.format(gsas_index))

                # save to VULCAN GSAS and add a property as Note
                mantidsimple.SaveVulcanGSS(InputWorkspace=tof_ws_name,
                                           BinFilename=self._reductionSetup.get_vulcan_bin_file(),
                                           OutputWorkspace=vdrive_bin_ws_name,
                                           GSSFilename=gsas_file_name,
                                           IPTS=self._reductionSetup.get_ipts_number(),
                                           GSSParmFilename="Vulcan.prm")

                # Add special property to output workspace
                final_ws = AnalysisDataService.retrieve(vdrive_bin_ws_name)
                final_ws.getRun().addProperty('VDriveBin', True, replace=True)

                # update message
                message += '%d-th: %s\n' % (gsas_index, gsas_file_name)
                gsas_index += 1
            # END-FOR

            # export sample logs!
            # create the log files
            self.generate_sliced_logs(chopped_ws_name_list, self._chopExportedLogType, append=(i_loop > 0))

            # TODO/ISSUE/Now/ - Need to delete the other reduced workspaces too, ???_TOF
            for ws_name in vulcan_bin_ws_list:
                pass

            # delete all the workspaces!
            for ws_name in chopped_ws_name_list:
                mantidsimple.DeleteWorkspace(Workspace=ws_name)

        # END-FOR (loop)

        return everything_is_right, message

    def chop_and_reduce_large_output_v1(self, chop_dir):
        """
        Chop and reduce in the special case of large amount of output.
        Calling SNSPowderReduction() will have to re-load the data, which is time consuming.  Therefore,
        the workflow is to
        1. reduce the event data by SNSPowderReduction to 2-spectrum event workspace, whose events are not compressed
        2. chop the reduced workspace with limited amount of slicers a time
        :param chop_dir:
        :return:
        """
        # check whether it is good to go
        assert isinstance(self._reductionSetup, reduce_VULCAN.ReductionSetup), 'ReductionSetup is not correct.'
        # configure the ReductionSetup
        self._reductionSetup.process_configurations()

        # check chopping directory
        assert isinstance(chop_dir, str) and os.path.exists(chop_dir), 'Chopped data directory {0} (of type {1}) ' \
                                                                       'must be a string and exist.' \
                                                                       ''.format(chop_dir, type(chop_dir))

        # get splitters workspaces
        split_ws_name, split_info_table = self._reductionSetup.get_splitters(throw_not_set=True)

        # construct reduction argument diction
        sns_arg_dict = dict()
        sns_arg_dict['Filename'] = self._reductionSetup.get_event_file()
        sns_arg_dict['CalibrationFile'] = self._reductionSetup.get_focus_file()
        sns_arg_dict['CharacterizationRunsFile'] = self._reductionSetup.get_characterization_file()
        sns_arg_dict['PreserveEvents'] = True
        sns_arg_dict['Binning'] = '-0.001'
        sns_arg_dict['SaveAS'] = ''
        sns_arg_dict['OutputDirectory'] = self._reductionSetup.get_gsas_dir()
        sns_arg_dict['NormalizeByCurrent'] = False
        sns_arg_dict['FilterBadPulses'] = 0
        sns_arg_dict['CompressTOFTolerance'] = 0.  # do not compress TOF events for further chopping
        sns_arg_dict['FrequencyLogNames'] = "skf1.speed"
        sns_arg_dict['WaveLengthLogNames'] = "skf12.lambda"

        for key in sns_arg_dict.keys():
            print key, ':', sns_arg_dict[key]

        # do regular reduction
        result = mantidsimple.SNSPowderReduction(**sns_arg_dict)
        use_default = True
        if len(result) == 2:
            reduced_ws_name = str(result[1])
            if AnalysisDataService.doesExist(reduced_ws_name):
                use_default = False
        if use_default:
            reduced_ws_name = 'VULCAN_{0}'.format(self._reductionSetup.get_run_number())
            if AnalysisDataService.doesExist(reduced_ws_name) is False:
                return False, 'Failed to reduce data file {0}. Unable to locate output workspace {1}' \
                              ''.format(sns_arg_dict['Filename'], reduced_ws_name)
        # END-IF

        # get run start time
        run_start_time = AnalysisDataService.retrieve(reduced_ws_name).run().getProperty('proton_charge').times[0]

        # if the number of output workspaces are too much, it could cause severe memory issue.
        num_outputs = self.get_number_chopped_ws(split_ws_name)
        NUM_TARGET_WS_IN_MEM = 20
        num_loops = num_outputs / NUM_TARGET_WS_IN_MEM

        message = 'Output GSAS files include:\n'

        if num_outputs % NUM_TARGET_WS_IN_MEM > 0:
            num_loops += 1

        gsas_index = 1

        # sort events  TODO/FUTURE - May not need this as SortEvents will be called in FilterEvents()
        mantidsimple.SortEvents(InputWorkspace=reduced_ws_name, SortBy='Pulse Time + TOF')
        everything_is_right = True

        for i_loop in range(num_loops):
            # get the partial splitters workspaces
            sub_split_ws = self.get_sub_splitters(i_loop * NUM_TARGET_WS_IN_MEM, (i_loop + 1) * NUM_TARGET_WS_IN_MEM,
                                                  run_start_ns=run_start_time.totalNanoseconds())
            # chop
            result = mantidsimple.FilterEvents(InputWorkspace=reduced_ws_name,
                                               SplitterWorkspace=sub_split_ws,
                                               InformationWorkspace=split_info_table,
                                               FilterByPulseTime=False,  # TODO/FUTURE/ - Change to True after Mantid
                                               OutputWorkspaceIndexedFrom1=False,
                                               CorrectionToSample="None",
                                               SpectrumWithoutDetector="Skip",
                                               SplitSampleLogs=False,
                                               OutputWorkspaceBaseName=reduced_ws_name)

            # print '[DB...BAT] Filter Events Result: ',  # result
            # print type(result), len(result)
            #
            # print 'Original workspace {0} still exist? {1}' \
            #       ''.format(reduced_ws_name, AnalysisDataService.doesExist(reduced_ws_name))

            if len(result) <= 2 and not isinstance(result[2], str):
                return False, 'Failed to chop reduced workspace {0}.'.format(reduced_ws_name)

            # result tuple item 3 is the list of chopped workspaces' names
            chopped_ws_name_list = result[2]
            for chopped_ws_name in chopped_ws_name_list:
                if AnalysisDataService.doesExist(chopped_ws_name):
                    chopped_ws = AnalysisDataService.retrieve(chopped_ws_name)
                    print '[DB...BAT] Chopped workspace {0}: # events = {1}' \
                          ''.format(chopped_ws_name, chopped_ws.getNumberEvents())
                else:
                    chopped_ws_name_list.pop(chopped_ws_name_list.index(chopped_ws_name))
                    print '[ERROR] Planned chopped workspace name {0} does not exist in ADS.'.format(chopped_ws_name)
            # END-FOR

            # convert the chopped workspaces to VULCAN-style GSAS file
            everything_is_right = True
            for chopped_ws_name in chopped_ws_name_list:
                # get the split workspace's name
                print '[DB...BAT] Process log of chopped workspace {0}: '.format(chopped_ws_name)

                # check whether the proposed-chopped workspace does exist
                if AnalysisDataService.doesExist(chopped_ws_name):
                    pass
                else:
                    # there won't be a workspace produced if there is no neutron event within the range.
                    message += 'Reduced workspace {0} does not exist. Investigate it!\n'.format(reduced_ws_name)
                    everything_is_right = False

                # convert unit and save for VULCAN-specific GSAS
                tof_ws_name = '{0}_TOF'.format(chopped_ws_name)
                mantidsimple.ConvertUnits(InputWorkspace=chopped_ws_name,
                                          OutputWorkspace=tof_ws_name,
                                          Target="TOF",
                                          EMode="Elastic",
                                          AlignBins=False)

                # overwrite the original file
                vdrive_bin_ws_name = chopped_ws_name

                # it might be tricky to give out the name of GSAS
                gsas_file_name = os.path.join(chop_dir, '{0}.gda'.format(gsas_index))

                # save to VULCAN GSAS and add a property as Note
                mantidsimple.SaveVulcanGSS(InputWorkspace=tof_ws_name,
                                           BinFilename=self._reductionSetup.get_vulcan_bin_file(),
                                           OutputWorkspace=vdrive_bin_ws_name,
                                           GSSFilename=gsas_file_name,
                                           IPTS=self._reductionSetup.get_ipts_number(),
                                           GSSParmFilename="Vulcan.prm")

                # Add special property to output workspace
                final_ws = AnalysisDataService.retrieve(vdrive_bin_ws_name)
                final_ws.getRun().addProperty('VDriveBin', True, replace=True)

                # update message
                message += '%d-th: %s\n' % (gsas_index, gsas_file_name)
                gsas_index += 1
            # END-FOR

            # export sample logs!
            # create the log files
            self.generate_sliced_logs(chopped_ws_name_list, self._chopExportedLogType, append=(i_loop > 0))

            # TODO/FIXME/DEBUG: Remove this after debugging
            if True and i_loop == 3:
                break

            # delete all the workspaces!
            for ws_name in chopped_ws_name_list:
                mantidsimple.DeleteWorkspace(Workspace=ws_name)

        # END-FOR (loop)

        return everything_is_right, message
    
    def create_chop_dir(self, reduced_data=True):
        """
        create directory for chopped data
        :return:
        """
        # get output file name with creating necessary directory
        try:
            # output destination: ChoppedData/binned_data
            if reduced_data:
                # reduced data is saved to .../binned_data/
                parent_dir = '/SNS/VULCAN/IPTS-%d/shared/binned_data/' % self._reductionSetup.get_ipts_number()
            else:
                # chopped NeXus files are saved to .../ChoppedData/
                parent_dir = '/SNS/VULCAN/IPTS-%d/shared/ChoppedData/' % self._reductionSetup.get_ipts_number()

            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
            chop_dir = os.path.join(parent_dir, '%d' % self._reductionSetup.get_run_number())
            if not os.path.exists(chop_dir):
                os.mkdir(chop_dir)
            if os.access(chop_dir, os.W_OK) is False:
                raise OSError('It is very likely that standard chopped directory {0} was created by other users.'
                              ''.format(chop_dir))

        except OSError as os_err:
            # mostly because permission to write
            print '[WARNING] Unable to write to shared folder. Reason: {0}'.format(os_err)

            # get local directory
            if not os.path.exists(self._reductionSetup.output_directory):
                os.mkdir(self._reductionSetup.output_directory)
            chop_dir = os.path.join(self._reductionSetup.output_directory,
                                    '%d' % self._reductionSetup.get_run_number())
            if not os.path.exists(chop_dir):
                os.mkdir(chop_dir)
        # END

        # set chop_dir to class variable
        self._choppedDataDirectory = chop_dir

        return

    def execute_chop_reduction(self, clear_workspaces=True):
        """
        Execute the chopping and reduction including exporting the log files with chopped data
        :return:
        """
        # create output directory
        self.create_chop_dir()
        # get the chopped data directory if not specified
        if self._choppedDataDirectory is None:
            self._choppedDataDirectory = self._reductionSetup.get_reduced_data_dir()

        # find out what kind of chopping algorithm shall be used
        split_ws_name, split_info_table = self._reductionSetup.get_splitters(throw_not_set=True)
        print '[DB...BAT] Splitters workspace name: ', split_ws_name
        num_targets = self.get_number_chopped_ws(split_ws_name)

        # chop and reduce
        # FIXME/TODO/ISSUE --- getMemorySize()
        if num_targets < MAX_ALLOWED_WORKSPACES:
            # load data and chop all at the same time
            status, message, output_ws_list = self.chop_reduce(self._choppedDataDirectory)
            # create the log files
            self.generate_sliced_logs(output_ws_list, self._chopExportedLogType)
            # clear workspace? or later
            # TODO/FIXME/DEBUG/ISSUE - remove this
            clear_workspaces = False
            if clear_workspaces:
                for ws_name in output_ws_list:
                    mantidsimple.DeleteWorkspace(Workspace=ws_name)
            else:
                self._reducedWorkspaceList.extend(output_ws_list)

        else:
            # need to chop and reduce
            print '[DB...BAT] Chopping to {0} output workspaces'.format(num_targets)
            status, message = self.chop_and_reduce_large_output(self._choppedDataDirectory)

        return status, message

    @staticmethod
    def get_number_chopped_ws(split_ws_name):
        """
        get the number of expected chopped workspaces from splitters workspace
        :param split_ws_name:
        :return:
        """
        split_ws = AnalysisDataService.retrieve(split_ws_name)

        if isinstance(split_ws, ITableWorkspace):
            # table workspace
            num_rows = split_ws.rowCount()
            target_set = set()
            for i_row in range(num_rows):
                target = split_ws.cell(i_row, 2)
                target_set.add(target)
        else:
            # matrix workspace case
            target_set = set()
            for y in split_ws.readY(0):
                int_y = int(y + 0.1)
                target_set.add(int_y)
        # END-FOR

        return len(target_set)

    def get_sub_splitters(self, split_start_index, split_stop_index, run_start_ns):
        """
        chop splitters workspace to sub one
        :param split_start_index:
        :param split_stop_index:
        :param run_start_ns: run start (epoch time) in nanoseconds
        :return:
        """
        # get splitting workspace
        split_ws_name, info_ws_name = self._reductionSetup.get_splitters(throw_not_set=True)
        split_ws = AnalysisDataService.retrieve(split_ws_name)
        sub_split_ws_name = split_ws.name() + '_{0}'.format(split_start_index)

        # split
        if isinstance(split_ws, SplittersWorkspace):
            # splitters workspace
            # TODO/TEST - Need to verify
            mantidsimple.CreateEmptyTableWorkspace(OutputWorkspace=sub_split_ws_name)
            sub_split_ws = AnalysisDataService.retrieve(sub_split_ws_name)
            sub_split_ws.addColumn('float', 'start')
            sub_split_ws.addColumn('float', 'stop')
            sub_split_ws.addColumn('str', 'index')

            num_rows = split_ws.rowCount()
            for i_row in range(split_start_index, min(split_stop_index, num_rows)):
                start_time = (split_ws.cell(i_row, 0) - run_start_ns) * 1.E-9
                stop_time = (split_ws.cell(i_row, 1) - run_start_ns) * 1.E-9
                target = str(split_ws.cell(i_row, 2))
                sub_split_ws.addRow([start_time, stop_time, target])

                print '[DB...BAT] Convert Splitters {0} to {1}.'.format(i_row, [start_time, stop_time, target])
            # END-FOR

        elif isinstance(split_ws, MatrixWorkspace):
            # Matrix workspace
            # TODO/TEST - Need to test
            vec_x = split_ws.readX(0)[split_start_index:split_stop_index+1]
            vec_y = split_ws.readY(0)[split_start_index:split_stop_index]
            vec_e = split_ws.readE(0)[split_start_index:split_stop_index]

            mantidsimple.CreateWorkspace(DataX=vec_x, DataY=vec_y, DataE=vec_e, NSpec=1,
                                         OutputWorkspace=sub_split_ws_name)

        elif isinstance(split_ws, ITableWorkspace):
            # Table workspace
            # TODO/TEST - Need to verify
            mantidsimple.CreateEmptyTableWorkspace(OutputWorkspace=sub_split_ws_name)
            sub_split_ws = AnalysisDataService.retrieve(sub_split_ws_name)
            sub_split_ws.addColumn('float', 'start')
            sub_split_ws.addColumn('float', 'stop')
            sub_split_ws.addColumn('str', 'index')

            num_rows = split_ws.rowCount()
            for i_row in range(split_start_index, min(split_stop_index, num_rows)):
                start_time = split_ws.cell(i_row, 0)
                stop_time = split_ws.cell(i_row, 1)
                target = split_ws.cell(i_row, 2)
                sub_split_ws.addRow([start_time, stop_time, target])

        else:
            # unsupported format
            raise RuntimeError('Splitting workspace of type {0} is not supported.'.format(split_ws))

        return sub_split_ws_name
