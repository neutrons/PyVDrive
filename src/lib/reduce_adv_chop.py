# Reduction with advanced chopping methods
# It is split from ReduceVulcanData in reduce_Vulcan.py

import reduce_Vulcan

class AdvancedChopReduce(reduce_Vulcan.ReduceVulcanData):
    """
    """
    def __init__(self):
        """
        """
        return

    def chop_and_reduce_large_output(self, split_ws_name, split_info_table):
        """
        Chop and reduce in the special case of large amount of output.
        Calling SNSPowderReduction() will have to re-load the data, which is time consuming.  Therefore,
        the workflow is to
        1. reduce the event data by SNSPowderReduction to 2-spectrum event workspace, whose events are not compressed
        2. chop the reduced workspace with limited amount of slicers a time
        :param split_ws_name:
        :param split_info_table:
        :return:
        """
        # construct reduction argument diction
        sns_arg_dict = dict()
        sns_arg_dict['Filename'] = self._reductionSetup.get_event_file()
        sns_arg_dict['CalibrationFile'] = self._reductionSetup.get_focus_file()
        sns_arg_dict['CharacterizationRunsFile'] = self._reductionSetup.get_characterization_file()
        sns_arg_dict['PreserveEvents'] = True
        sns_arg_dict['Binning'] = '-0.001'
        sns_arg_dict['SaveAS'] = "",
        sns_arg_dict['OutputDirectory'] = self._reductionSetup.get_gsas_dir(),
        sns_arg_dict['NormalizeByCurrent'] = False,
        sns_arg_dict['FilterBadPulses'] = 0,
        sns_arg_dict['CompressTOFTolerance'] = 0.  # do not compress TOF events for further chopping
        sns_arg_dict['FrequencyLogNames'] = "skf1.speed"
        sns_arg_dict['WaveLengthLogNames'] = "skf12.lambda"

        # do regular reduction
        result = mantidsimple.SNSPowderReduction(**sns_arg_dict)
        print '[DB] Reduction output = ', result

        # then it is the time to splitting
        reduce_success, reduced_result_tup = self.get_reduced_workspaces(chopped=False)
        if not reduce_success:
            return False, 'Failed to reduce data file {0}'.format(sns_arg_dict['Filename']), None

        # get raw reduced workspace
        reduced_raw_ws_name = result[0]

        # if the number of output workspaces are too much, it could cause severe memory issue.
        num_outputs = self.get_number_chopped_ws(split_ws_name)
        NUM_SPLITTERS = 20
        num_loops = num_outputs / NUM_SPLITTERS

        # create chopped data directory
        chop_dir = self.create_chop_dir()

        message = ''

        if num_outputs % NUM_SPLITTERS > 0:
            num_loops += 1

        gsas_index = 1
        for i_loop in range(num_loops):
            # get the partial splitters workspaces
            sub_split_ws = self.get_sub_splitters(i_loop * NUM_SPLITTERS, (i_loop + 1) * NUM_SPLITTERS)
            result = mantidsimple.FilterEvents(InputWorkspace=reduced_ws_name,
                                               SplitterWorkspace=sub_split_ws,
                                               InformationWorkspace=split_info_table,
                                               FilterByPulseTime=True,
                                               OutputWorkspaceIndexedFrom1=False,
                                               CorrectionToSample="None",
                                               SpectrumWithoutDetector="Skip",
                                               SplitSampleLogs=False,
                                               OutputTOFCorrectionWorkspace=reduced_ws_name)
            # TODO/FIXME/ISSUE/NOW/ It doesn't work!
            print '[DB...BAT] Filter Events Result: ', result
            chopped_ws_name_list = result[1]

            # convert the chopped workspaces to VULCAN-style GSAS file
            for chopped_ws_name in chopped_ws_name_list:
                # get the split workspace's name

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
                gsas_file_name = os.path.join(chop_dir, '%d.gda'.format(gsas_index))

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

        return everything_is_right, message, chopped_ws_name_list
    
    def create_chop_dir(self):
        """
        create directory for chopped data
        :return:
        """
        # get output file name with creating necessary directory
        try:
            # output destination: ChoppedData/binned_data
            # FIXME/TODO/ISSUE/Ke - Choppeddata or binned_data?
            # parent_dir = '/SNS/VULCAN/IPTS-%d/shared/ChoppedData/' % self._reductionSetup.get_ipts_number()
            parent_dir = '/SNS/VULCAN/IPTS-%d/shared/binned_data/' % self._reductionSetup.get_ipts_number()

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
