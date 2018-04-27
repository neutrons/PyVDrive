# Reduction with advanced chopping methods
# It is split from ReduceVulcanData in reduce_Vulcan.py
import os
import math
import pandas as pd

import mantid.simpleapi as mantidsimple
from mantid.api import AnalysisDataService, ITableWorkspace, MatrixWorkspace
from mantid.dataobjects import SplittersWorkspace
from mantid.kernel import DateAndTime

import reduce_VULCAN
import chop_utility
import mantid_helper

MAX_ALLOWED_WORKSPACES = 200
MAX_CHOPPED_WORKSPACE_IN_MEM = 200

# FIXME/NOWNOW : Clean this python module!


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

    def chop_data(self, split_ws_name=None, info_ws_name=None):
        """
        chop data and save to GSAS file
        :param split_ws_name:
        :return:
        """
        # get data file names, splitters workspace and output directory from reduction setup object
        raw_file_name = self._reductionSetup.get_event_file()
        if split_ws_name is None:
            split_ws_name, info_ws_name = self._reductionSetup.get_splitters(throw_not_set=True)
        elif info_ws_name is None:
            raise RuntimeError('Splitters workspace name must be given with information workspace name.')
        useless, output_directory = self._reductionSetup.get_chopped_directory(True, nexus_only=True)

        # FIXME/TODO/FUTURE/ISSUE - do_tof_correction : should get from somewhere
        do_tof_correction = False

        # get number of target workspace
        number_target_ws, is_epoch_time = chop_utility.get_number_chopped_ws(split_ws_name)

        # load data from file to workspace
        event_ws_name = os.path.split(raw_file_name)[1].split('.')[0]
        mantid_helper.load_nexus(data_file_name=raw_file_name, output_ws_name=event_ws_name, meta_data_only=False)

        if number_target_ws < MAX_CHOPPED_WORKSPACE_IN_MEM:
            # chop event workspace with regular method
            # TODO/DEBUG - Split workspace won't be deleted at this stage
            status, ret_obj = mantid_helper.split_event_data(raw_ws_name=event_ws_name,
                                                             split_ws_name=split_ws_name,
                                                             info_table_name=info_ws_name,
                                                             target_ws_name=None,
                                                             tof_correction=do_tof_correction,
                                                             output_directory=output_directory,
                                                             delete_split_ws=False)
        else:
            # chop event workspace to too many target workspaces which cannot be hold in memory
            # simultaneously
            status, ret_obj = self.chop_data_large_number_targets(event_ws_name,
                                                                  tof_correction=do_tof_correction,
                                                                  output_dir=output_directory,
                                                                  is_epoch_time=is_epoch_time,
                                                                  num_target_ws=number_target_ws,
                                                                  delete_split_ws=True)
        # delete raw workspace
        # TODO/ISSUE/NOWNOW - Requiring a user option for this!
        print '[INFO] Deleting raw event workspace {0} which {1} exists.' \
              ''.format(event_ws_name, AnalysisDataService.doesExist(event_ws_name))
        if AnalysisDataService.doesExist(event_ws_name):
            mantid_helper.delete_workspace(event_ws_name)

        return status, ret_obj

    # TODO/NOW - Implement this!
    def chop_data_overlap_slicers(self, raw_ws_name, tof_correction,
                                       output_dir, is_epoch_time, num_target_ws,
                                       delete_split_ws=True):
        """

        :param raw_ws_name:
        :param tof_correction:
        :param output_dir:
        :param is_epoch_time:
        :param num_target_ws:
        :param delete_split_ws:
        :return:
        """
        # get split information workspace
        split_ws_name, split_info_name = self._reductionSetup.get_splitters(throw_not_set=True)
        # check that the splitters workspace must be a TableWorkspace
        assert mantid_helper.is_table_workspace(split_ws_name),'Splitters workspace {0} must be a table workspace.' \
                                                               ''.format(split_ws_name)

        # convert to a set of non-overlapping splitters
        time_segment_period = self._reductionSetup.get_time_segment_period()
        if time_segment_period is None:
            split_ws_list = mantid_helper.convert_to_non_overlap_splitters_bf(split_ws_name)
        else:
            split_ws_list = mantid_helper.convert_to_non_overlap_splitters_period(split_ws_name, time_segment_period)

        # reduce
        for split_ws_name in split_ws_list:
            self.chop_data(split_ws_name, split_info_name)

        return True, ''

    def chop_data_large_number_targets(self, raw_ws_name, tof_correction,
                                       output_dir, is_epoch_time, num_target_ws,
                                       delete_split_ws=True):
        """
        chop data to a large number of output targets
        :param raw_ws_name: raw event workspace to get split
        :param tof_correction:
        :param output_dir:
        :param is_epoch_time:
        :return:
        """
        # get raw workspace
        raw_ws = mantid_helper.retrieve_workspace(raw_ws_name)

        # get run start time
        if is_epoch_time:
            run_start_ns = raw_ws.run().getProperty('proton_charge').firstTime().totalNanoseconds()
        else:
            run_start_ns = 0

        # get split information workspace
        split_ws_name, split_info_name = self._reductionSetup.get_splitters(throw_not_set=True)

        # in loop generate data
        num_loops = int(math.ceil(num_target_ws * 1. / MAX_CHOPPED_WORKSPACE_IN_MEM))

        total_status = True
        total_tup_list = list()
        total_error_message = ''
        for i_loop in range(num_loops):
            # get the subset of the splitters
            sub_split_ws_name = self.get_sub_splitters(split_start_index=i_loop * MAX_CHOPPED_WORKSPACE_IN_MEM,
                                                       split_stop_index=(i_loop + 1) * MAX_CHOPPED_WORKSPACE_IN_MEM,
                                                       run_start_ns=run_start_ns)

            # split
            # pre-check
            if AnalysisDataService.doesExist(raw_ws_name) is False:
                raise NotImplementedError('Pre-check Raw workspace {0} cannot be found at loop {1} ({2}).'
                                          ''.format(raw_ws_name, i_loop, num_loops))

            status, ret_obj = mantid_helper.split_event_data(raw_ws_name=raw_ws_name, split_ws_name=sub_split_ws_name,
                                                             info_table_name=split_info_name,
                                                             target_ws_name=raw_ws_name+'_split',
                                                             tof_correction=False,
                                                             output_directory=output_dir,
                                                             delete_split_ws=delete_split_ws)

            # post check
            if AnalysisDataService.doesExist(raw_ws_name) is False:
                return False, str(NotImplementedError('Post-check Raw workspace {0} cannot be found at loop {1} ({2}).'
                                  ''.format(raw_ws_name, i_loop, num_loops)))

            # process
            if status:
                # split with success
                assert isinstance(ret_obj, list), 'Successful returned value must be a list of 2-tuples'
                total_tup_list.extend(ret_obj)
            else:
                # failed: append error message
                total_status = False
                total_error_message += '{0}\n'.format(ret_obj)

        # END-FOR

        if not total_status:
            return False, total_error_message

        return True, total_tup_list

    def chop_reduce(self, chop_dir):
        """
        Chop and reduce (this is a method calling Mantid algorithm directly)
        :except: RuntimeError if the target directory for chopped data does not exist
        :return:
        """
        # check whether it is good to go
        assert isinstance(self._reductionSetup, reduce_VULCAN.ReductionSetup), 'ReductionSetup is not correct.'

        # configure the ReductionSetup
        self._reductionSetup.process_configurations()
        gsas_dir, nexus_dir = self._reductionSetup.get_chopped_directory(check_write_permission=True)

        # get splitters workspaces
        split_ws_name, split_info_table = self._reductionSetup.get_splitters(throw_not_set=True)
        # TODO/NOW/ISSUE/FIXME/TODAY - Examine input workspace. Ke's overapping time slicer is not supported.
        is_over_split = chop_utility.is_overlap_splitter(split_ws_name)
        if is_over_split:
            raise RuntimeError('Overlapped splitter will be supported soon!')

        # TEST/NOW
        # call SNSPowderReduction for chopping and reducing
        args = dict()
        args['Filename'] = self._reductionSetup.get_event_file()
        args['PreserveEvents'] = True
        args['CalibrationFile'] = self._reductionSetup.get_focus_file()
        args['CharacterizationRunsFile'] = self._reductionSetup.get_characterization_file()
        # args['Binning'] = "-0.001"
        print '[DB...BAT] Binning parameter: {0}.'.format(self._reductionSetup.binning_parameters)
        args['Binning'] = self._reductionSetup.binning_parameters
        args['SaveAS'] = ""
        args['OutputDirectory'] = self._reductionSetup.get_gsas_dir()
        args['NormalizeByCurrent'] = False
        args['FilterBadPulses'] = 0
        args['CompressTOFTolerance'] = 0.
        args['FrequencyLogNames'] = "skf1.speed"
        args['WaveLengthLogNames'] = "skf12.lambda"
        args['SplittersWorkspace'] = split_ws_name
        args['SplitInformationWorkspace'] = split_info_table
        mantidsimple.SNSPowderReduction(**args)

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
            ws_index = str(info_table.cell(i_ws, 0))
            reduced_ws_name = 'VULCAN_{0}_{1}'.format(self._reductionSetup.get_run_number(), ws_index)

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
            # now ws_index might not be an integer
            if isinstance(ws_index, int):
                new_tag = ws_index + 1
            else:
                new_tag = ws_index
            if use_special_name:
                # special name: including run number
                gsas_file_name = os.path.join(chop_dir, '{0}_{1}.gda'.format(self._reductionSetup.get_run_number(),
                                                                             new_tag))
            else:
                # just a number
                gsas_file_name = os.path.join(chop_dir, '{0}.gda'.format(ws_index))

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

        # disabled self.examine_slicing_workspace(split_ws_name)

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
        NUM_TARGET_WS_IN_MEM = 200
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
                                                  run_start_ns=run_start_time_ns)

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
                    message += 'Reduced workspace {0} does not exist. Investigate it!\n'.format(chopped_ws_name)
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
                print '[DB...BAT] Vulcan BIN workspace: {0}'.format(ws_name)
                pass

            # delete all the workspaces!
            # TODO/ISSUE/FIXME/NOW/TODAY - Delete the workspace by option
            # for ws_name in chopped_ws_name_list:
            #     mantidsimple.DeleteWorkspace(Workspace=ws_name)

        # END-FOR (loop)

        return everything_is_right, message

    def chop_save_reduce(self):
        """
        chop the data, save to NeXus file and then reduce them
        :return: 2-tuple.  (1) boolean: successful or failed  (2) list of 3-tuples: chopped file name,
                                                                                    reduced successful,
                                                                                    reduced result
        """
        # TODO/FIXME/NEXT/FUTURE - Data will be read from HDD to reduce.  This might not be efficient.
        #   But it is a quick solution.

        # chop and save data
        status, ret_obj = self.chop_data()
        if status:
            raw_chopped_tuples = ret_obj
        else:
            return False, ret_obj, None

        # reduce
        chopped_tup_list = list()
        lookup_list = list()
        gsas_index = 1
        for chop_tup in raw_chopped_tuples:
            # get the nexus file and workspace tuple
            event_nexus_name, ws_name = chop_tup
            assert isinstance(ws_name, str), 'Workspace name {0} must be a string but not a {1}.' \
                                             ''.format(ws_name, type(ws_name))
            # check TODO/ISSUE/TODAY - Delete raw workspace to reduce from file or reduce directly from workspace
            print '[DB...BAT] Previously split workspace (not used): {0}.  Exist? {1}' \
                  ''.format(ws_name, mantid_helper.workspace_does_exist(ws_name))

            # skip unfiltered
            if ws_name.endswith('_unfiltered'):
                continue

            # reduce data
            gsas_new_name = os.path.join(self._reductionSetup.get_gsas_dir(), '{0}.gda'.format(gsas_index))
            status, message, reduced_ws_name = self.reduce_powder_diffraction_data(event_nexus_name, user_gsas_file_name=gsas_new_name)
            chopped_tup_list.append((status, event_nexus_name, reduced_ws_name))
            gsas_file_name = self._reductionSetup.get_gsas_file(main_gsas=True)
            print '[INFO] Reduced chopped event file {0} successfully ({1}) to {2} with file {3}.' \
                  ''.format(event_nexus_name, status, reduced_ws_name, gsas_file_name)

            # rename to VULCAN VDrive compatible name
            if os.path.exists(gsas_file_name):
                # no need to rename
                # gsas_new_name = os.path.join(self._reductionSetup.get_gsas_dir(), '{0}.gda'.format(gsas_index))
                # os.rename(gsas_file_name, gsas_new_name)
                lookup_list.append((gsas_new_name, event_nexus_name, reduced_ws_name))
                gsas_index += 1
            # END-IF
        # END-IF

        # export a table-lookup file for workspace, event nexus file and target GSAS
        self.export_chopped_information(lookup_list)

        return status, '', chopped_tup_list

    def create_chop_dir(self, reduced_data=True, chopped_data=True):
        """
        create directory for chopped data.
        If user specified output directory: then chopped to user specified directory. otherwise to archive
        :return:
        """
        def check_or_create_dir(dir_name):
            """
            check whether a directory exists.
            if it does, check whether it is writable;
            otherwise, create this directory
            :param dir_name:
            :return:
            """
            if os.path.exists(dir_name):
                # directory exists
                if os.access(dir_name, os.W_OK) is False:
                    raise RuntimeError('Directory {0} exists but user has no privilege to write.'.format(dir_name))
            else:
                # new directory
                try:
                    os.mkdir(dir_name)
                except OSError as os_err:
                    raise RuntimeError('Unable to make directory {0} due to {1}'.format(dir_name, os_err))

            return

        # get GSAS directory and NeXus file directory for set up
        gsas_dir, nexus_dir = self._reductionSetup.get_chopped_directory(False)

        if reduced_data:
            print '[INFO] Reduced data will be written to {0}'.format(gsas_dir)
            check_or_create_dir(gsas_dir)

        if chopped_data:
            print '[INFO] Chopped data will be saved to {0} as NeXus files.'.format(nexus_dir)
            check_or_create_dir(nexus_dir)

            # set chop_dir to class variable
            self._choppedDataDirectory = nexus_dir

        return

    @staticmethod
    def examine_slicing_workspace(split_ws_name):
        """
        Examine the split workspace that has the slicers
        :param split_ws_name:
        :return:
        """
        # check input
        assert isinstance(split_ws_name, str), 'Splitters workspace name {0} must be a string but not a {1}.' \
                                               ''.format(split_ws_name, type(split_ws_name))
        if mantid_helper.workspace_does_exist(split_ws_name) is False:
            raise RuntimeError('Splitters workspace with name {0} cannot be found in ADS.'.format(split_ws_name))

        # get the splitters
        split_ws = AnalysisDataService.retrieve(split_ws_name)

        if split_ws.__class__.__name__.count('Table') == 1:
            # table workspace for splitters
            num_rows = split_ws.rowCount()
            message = '[INFO] There are {0} splitters '.format(num_rows)
            if num_rows > 0:
                message += 'from {0} to {1}.'.format(split_ws.cell(0, 0), split_ws.cell(num_rows-1, 0))
            else:
                message += '.'
            print message
        else:
            # matrix workspace
            print '[DB...BAT] It is MatrixWorkspace!'

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
            status, message, chopped_tup_list = self.chop_save_reduce()
            print '[DB...BAT] chop-reduction status: {0}; chop-reduction message: {1}'.format(status, message)
            output_ws_list = list()
            for tup3 in chopped_tup_list:
                output_ws_list.append(tup3[2])

            # create the log files
            self.generate_sliced_logs(output_ws_list, self._chopExportedLogType)
            # clear workspace? or later
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

    def export_chopped_information(self, lookup_list):
        """
        Export the chopped data information to a csv-compatible file
        standard name of the output file will be run_{0}_chop_info.txt
        :param lookup_list: a list of 3-tuples
        :return:
        """
        # check the input
        assert isinstance(lookup_list, list), 'Lookup table {0} must be given by list but not {1}.' \
                                              ''.format(lookup_list, type(lookup_list))

        # generate file name with full path: to main GSAS directory
        directory = self._reductionSetup.get_gsas_dir()
        run_number = self._reductionSetup.get_run_number()
        out_file_name = os.path.join(directory, 'run_{0}_chop_info.txt'.format(run_number))

        wbuf = ''
        for tup3 in lookup_list:
            wbuf += '{0} \t{1}\t {2}\n'.format(tup3[0], tup3[1], tup3[2])

        # export to file
        try:
            ofile = open(out_file_name, 'w')
            ofile.write(wbuf)
            ofile.close()
        except OSError as os_err:
            raise RuntimeError('Unable to export chopped information to {0} due to {1}.'.format(out_file_name,
                                                                                                os_err))

        return

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

    def generate_sliced_logs(self, ws_name_list, log_type, append=False):
        """
        generate sliced logs
        :param ws_name_list:
        :param log_type: either loadframe or furnace
        :param append: if true and if the file to output exists, then just append the new content at the end
        :return:
        """
        # check inputs
        assert isinstance(ws_name_list, list) and len(ws_name_list) > 0,\
            'Workspace name list {0} must be a non-empty list, but not a {1}.'.format(ws_name_list, type(ws_name_list))
        assert self._choppedDataDirectory is not None, 'Chopped data directory cannot be None.'

        if log_type != 'loadframe' and log_type != 'furnace':
            raise RuntimeError('Exported sample log type {0} of type {1} is not supported.'
                               'It must be either furnace or loadframe'.format(log_type, type(log_type)))

        # get workspaces and properties
        ws_name_list.sort()

        # get the properties' names list
        ws_name = ws_name_list[0]
        workspace = AnalysisDataService.retrieve(ws_name)
        property_name_list = list()
        for sample_log in workspace.run().getProperties():
            p_name = sample_log.name
            property_name_list.append(p_name)
        property_name_list.sort()
        run_start = DateAndTime(workspace.run().getProperty('run_start').value)

        # start value
        start_file_name = os.path.join(self._choppedDataDirectory,
                                       '{0}sampleenv_chopped_start.txt'.format(self._reductionSetup.get_run_number()))
        mean_file_name = os.path.join(self._choppedDataDirectory,
                                      '{0}sampleenv_chopped_mean.txt'.format(self._reductionSetup.get_run_number()))
        end_file_name = os.path.join(self._choppedDataDirectory,
                                     '{0}sampleenv_chopped_end.txt'.format(self._reductionSetup.get_run_number()))

        # output
        # create Pandas series dictionary
        start_series_dict = dict()
        mean_series_dict = dict()
        end_series_dict = dict()
        mts_columns = list()

        # set up correct header list
        if log_type == 'loadframe':
            # load frame
            header_list = reduce_VULCAN.MTS_Header_List
        else:
            # furnace
            header_list = reduce_VULCAN.Furnace_Header_List

        # initialize the data structure for output
        for entry in reduce_VULCAN.MTS_Header_List:
            pd_series = pd.Series()
            mts_name, log_name = entry
            start_series_dict[mts_name] = pd_series
            mean_series_dict[mts_name] = pd_series
            end_series_dict[mts_name] = pd_series
            mts_columns.append(mts_name)

            if log_name not in property_name_list:
                print '[WARNING] Log {0} is not a sample log in NeXus.'.format(log_name)
        # END-FOR

        for i_ws, ws_name in enumerate(ws_name_list):
            # get workspace
            workspace_i = AnalysisDataService.retrieve(ws_name)
            self.export_chopped_logs(i_ws=i_ws,
                                     run_start_time=run_start,
                                     property_name_list=property_name_list,
                                     header_list=header_list,
                                     workspace_i=workspace_i,
                                     start_series_dict=start_series_dict,
                                     mean_series_dict=mean_series_dict,
                                     end_series_dict=end_series_dict)
        # END-FOR (workspace)

        # export to csv file
        # start file
        pd_data_frame = pd.DataFrame(start_series_dict, columns=mts_columns)
        if append and os.path.exists(start_file_name):
            with open(start_file_name, 'a') as f:
                pd_data_frame.to_csv(f, header=False)
        else:
            pd_data_frame.to_csv(start_file_name, sep='\t', float_format='%.5f')

        # mean file
        pd_data_frame = pd.DataFrame(mean_series_dict, columns=mts_columns)
        if os.path.exists(mean_file_name) and append:
            with open(mean_file_name, 'a') as f:
                pd_data_frame.to_csv(f, header=False)
        else:
            pd_data_frame.to_csv(mean_file_name, sep='\t', float_format='%.5f')

        # end file
        pd_data_frame = pd.DataFrame(end_series_dict, columns=mts_columns)
        if os.path.exists(end_file_name) and append:
            with open(end_file_name, 'a') as f:
                pd_data_frame.to_csv(f, header=False)
        else:
            pd_data_frame.to_csv(end_file_name, sep='\t', float_format='%.5f')

        print '[INFO] Chopped log files are written to %s, %s and %s.' % (start_file_name, mean_file_name,
                                                                          end_file_name)

        return

    @staticmethod
    def export_chopped_logs(i_ws, property_name_list, header_list,
                            run_start_time,
                            workspace_i, start_series_dict,
                            mean_series_dict, end_series_dict):
        """
        Export sample logs to a set of dictionaries
        :param i_ws:
        :param property_name_list:
        :param header_list:
        :param run_start_time:
        :param workspace_i:
        :param start_series_dict:
        :param mean_series_dict:
        :param end_series_dict:
        :return:
        """
        # check: log "run_start" should be the same for workspaces split from the same EventWorkspace.
        run_start_i = DateAndTime(workspace_i.run().getProperty('run_start').value)
        assert run_start_time == run_start_i, '{0}-th workspace\'s "run_start {1}" should be same as others\'s start ' \
                                              'time {2}'.format(i_ws, run_start_i, run_start_time)

        # get difference in REAL starting time (proton_charge[0])
        try:
            real_start_time_i = workspace_i.run().getProperty('proton_charge').times[0]
        except IndexError:
            print '[ERROR] Workspace {0} has proton charge with zero entry.'.format(workspace_i)
            return

        time_stamp = real_start_time_i.total_nanoseconds()
        # time (step) in seconds
        diff_time = (real_start_time_i - run_start_time).total_nanoseconds() * 1.E-9

        for entry in header_list:
            mts_name, log_name = entry
            pd_index = float(i_ws + 1)
            if len(log_name) > 0 and log_name in property_name_list:
                # regular log
                try:
                    sample_log = workspace_i.run().getProperty(log_name).value
                except RuntimeError as run_err:
                    print '[ERROR] Exporting chopped logs: {0}'.format(run_err)
                    start_series_dict[mts_name].set_value(pd_index, 0.)
                    mean_series_dict[mts_name].set_value(pd_index, 0.)
                    end_series_dict[mts_name].set_value(pd_index, 0.)
                    continue

                if len(sample_log) > 0:
                    start_value = sample_log[0]
                    mean_value = sample_log.mean()
                    end_value = sample_log[-1]
                else:
                    # TODO/DEBUG/ERROR/ASAP: CHOP,IPTS=14430,RUNS=77149,HELP=1
                    # loadframe.MPTIndex for 0-th workspace VULCAN_77149_0 due to index 0 is out of bounds for
                    # axis 0 with size 0
                    error_message = '[ERROR] Unable to export "loadframe" log {3} for {0}-th workspace {1} ' \
                                    'due to {2}'.format(i_ws, workspace_i.name(), 'index error', log_name)
                    print error_message
                    start_value = 0.
                    mean_value = 0.
                    end_value = 0.
            elif mts_name == 'TimeStamp':
                # time stamp
                start_value = mean_value = end_value = float(time_stamp)
            elif mts_name == 'Time [sec]':
                # time step
                start_value = mean_value = end_value = diff_time
            elif len(log_name) > 0:
                # sample log does not exist in NeXus file. warned before. ignore!
                start_value = mean_value = end_value = 0.
            else:
                # unknown
                print '[ERROR] MTS log name %s is cannot be found.' % mts_name
                start_value = mean_value = end_value = 0.
            # END-IF-ELSE

            start_series_dict[mts_name].set_value(pd_index, start_value)
            mean_series_dict[mts_name].set_value(pd_index, mean_value)
            end_series_dict[mts_name].set_value(pd_index, end_value)

        # END-FOR (entry)

        return

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


# TODO/ISSUE/NOW - Generalize this method with same method in reduce_adv_chop.py
def get_sub_splitters2(split_ws_name, split_start_index, split_stop_index, run_start_ns):
    """

    :param split_ws_name:
    :param split_start_index:
    :param split_stop_index:
    :param run_start_ns:
    :return:
    """
    # get splitting workspace
    split_ws = mantid_helper.retrieve_workspace(split_ws_name)

    # get the sub splitters name
    sub_split_ws_name = split_ws.name() + '_{0}'.format(split_start_index)

    # split
    if isinstance(split_ws, SplittersWorkspace):
        # splitters workspace
        mantid_helper.create_table_workspace(sub_split_ws_name,
                                             [('float', 'start'), ('float', 'stop'), ('str', 'index')])
        sub_split_ws = mantid_helper.retrieve_workspace(sub_split_ws_name)

        num_rows = split_ws.rowCount()
        for i_row in range(split_start_index, min(split_stop_index, num_rows)):
            start_time = (split_ws.cell(i_row, 0) - run_start_ns) * 1.E-9
            stop_time = (split_ws.cell(i_row, 1) - run_start_ns) * 1.E-9
            target = str(split_ws.cell(i_row, 2))
            sub_split_ws.addRow([start_time, stop_time, target])
        # END-FOR

    elif isinstance(split_ws, MatrixWorkspace):
        # Matrix workspace
        # TODO/TEST - Need to test
        vec_x = split_ws.readX(0)[split_start_index:split_stop_index + 1]
        vec_y = split_ws.readY(0)[split_start_index:split_stop_index]
        vec_e = split_ws.readE(0)[split_start_index:split_stop_index]

        mantid_helper.create_workspace_2d(vec_x, vec_y, vec_e, sub_split_ws_name)

    elif isinstance(split_ws, ITableWorkspace):
        # Table workspace
        # TODO/TEST - Need to verify
        mantid_helper.create_table_workspace(sub_split_ws_name,
                                             [('float', 'start'), ('float', 'stop'), ('str', 'index')])
        sub_split_ws = mantid_helper.retrieve_workspace(sub_split_ws_name)
        num_rows = split_ws.rowCount()
        for i_row in range(split_start_index, min(split_stop_index, num_rows)):
            start_time = split_ws.cell(i_row, 0)
            stop_time = split_ws.cell(i_row, 1)
            target = split_ws.cell(i_row, 2)
            sub_split_ws.addRow([start_time, stop_time, target])
        # END-FOR

    else:
        # unsupported format
        raise RuntimeError('Splitting workspace of type {0} is not supported.'.format(split_ws))

    return sub_split_ws_name

