import os
import os.path
import random
from chop_utility import DataChopper
import datatypeutility
import mantid_reduction
import mantid_helper
import reductionmanager as prl
import archivemanager
import loaded_data_manager
import vanadium_utility
import peak_util
import numpy
import vulcan_util


# TODO... NEED A DOC FOR HOW TO STORE DATA KEY (WORKSPACE NAME) ...


class ProjectManager(object):
    """ VDrive Project
    Note:
        (1) run_info dictionary from archive manager:  'run', 'ipts', 'file', 'time'
    """
    def __init__(self, parent, project_name, instrument='VULCAN'):
        """ Init
        """
        # project name
        self._name = project_name
        # Data path.  With baseDataFileName, a full path to a data set can be constructed
        self._baseDataPath = None
        # parent
        self._parent = parent

        # chopping and reduction managers
        # Reduction manager
        self._reductionManager = prl.ReductionManager(instrument=instrument)
        # Loaded (previously) binned data manager
        self._loadedDataManager = loaded_data_manager.LoadedDataManager(self)
        # dictionary to manage data chopping
        self._chopManagerDict = dict()   # key: run number, value: SampleLogHelper.SampleLogManager()
        # vanadium processing manager
        self._processVanadiumManager = \
            vanadium_utility.VanadiumProcessingManager(self)

        # definition of dictionaries
        # dictionary for the information of run number, file name and IPTS
        self._dataFileDict = dict()  # key: run number, value: 2-tuple (file name, IPTS)
        # a cache of archived file scanned
        self._scannedRunDict = dict()  # key = run number, value = archive manager's run_info dictionary

        # dictionary for loaded data referenced by IPTS and run number. value is the data key
        self._loadedDataDict = dict()  # FIXME TODO - TODAY - Consider to remove too

        # dictionary for sample run mapping to vanadium run
        self._sampleRunVanadiumDict = dict()  # Key: run number (int) / Value: vanadium run number (int)
        # vanadium GSAS file to vanadium run's mapping. Key = integer vanadium run number; Value = GSAS file name
        self._vanadiumGSASFileDict = dict()

        # List of data file's base name
        self._baseDataFileNameList = list()

        # dictionary for sample run number to be flagged to reduce.
        self._sampleRunReductionFlagDict = dict()  # Key: run number. Value: boolean flag for reduction

        # name of the workspace for VDRIVE bins tempate
        # self._vdriveBinTemplateName = None

        return

    def add_run(self, run_number, file_name, ipts_number):
        """
        Add a run to project
        :param run_number:
        :param file_name:
        :param ipts_number:
        :return:
        """
        # Check input
        assert isinstance(run_number, int), 'run number blabla'

        # no need to add again
        if run_number in self._dataFileDict:
            return

        if file_name is None or ipts_number is None:
            # incomplete information.  shall be retrieved from cached
            if run_number not in self._scannedRunDict:
                raise RuntimeError('Run {0} is not previously scanned. Complete information is required.'
                                   ''.format(run_number))
            run_info = self._scannedRunDict[run_number]
            file_name = run_info['file']
            ipts_number = run_info['ipts']

        else:
            # check types
            assert isinstance(ipts_number, int), 'ipts number, blabla'
            assert isinstance(file_name, str), 'file name blabla'

        # add
        self._dataFileDict[run_number] = file_name, ipts_number
        self._baseDataFileNameList.append(os.path.basename(file_name))

        return

    def add_reduced_workspace(self, ipts_number, run_number, workspace_name):
        """
        Add workspace containing reduced diffraction data to project
        :param ipts_number:
        :param run_number:
        :param workspace_name:
        :return:
        """
        # check inputs
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not {1}.' \
                                            ''.format(run_number, type(run_number))

        # check workspace exising or not
        if not mantid_helper.workspace_does_exist(workspace_name):
            raise RuntimeError('Workspace {0} does not exist in Mantid ADS.'.format(workspace_name))

        self._loadedDataDict[ipts_number, run_number] = workspace_name

        return

    def add_scanned_information(self, run_info_dict_list):
        """
        add scanned information to a dictionary for caching information
        :param run_info_dict_list:
        :return:
        """
        # check input
        assert isinstance(run_info_dict_list, list),\
            'Input run number information {0} must be given in a list but not a {1}' \
            ''.format(run_info_dict_list, type(run_info_dict_list))

        # add
        for run_info in run_info_dict_list:
            run_number = run_info['run']
            self._scannedRunDict[run_number] = run_info
        # END-FOR

        return

    def calculate_peaks_parameter(self, ipts_number, run_number_list, chop_list, x_min, x_max, to_console, file_name):
        """Calculate a peak or several overlapped peaks' parameters

        These parameters include integral intensity, average d-spacing and variance

        :except RuntimeError:
        :param ipts_number: None or integer.  None if by run number it is able to locate workspace
        :param run_number_list:
        :param chop_list:
        :param x_min:
        :param x_max:
        :param to_console:
        :param file_name:
        :return: a dictionary of strings as formed message. key = bank ID
        """
        import itertools

        # check inputs' types
        assert isinstance(ipts_number, int) or ipts_number is None, 'IPTS number {0} must be either ' \
                                                                    'integer or None.'.format(ipts_number)
        assert isinstance(run_number_list, list), 'Run numbers must be given as list.'
        assert isinstance(x_min, float) and isinstance(x_max, float),\
            'Min X {0} and Max X {1} must be integers.'.format(x_min, x_max)
        assert chop_list is None or isinstance(chop_list, list), 'blabla'

        # check inputs' logic
        if x_min >= x_max:
            raise RuntimeError('Min X {0} cannot be equal or larger than Max X {1}'.format(x_min, x_max))
        if not to_console and not file_name:
            raise RuntimeError('At least one in to_console and file name should be specified')

        # determine units
        if x_max < 100:
            unit = 'dSpacing'
        else:
            unit = 'TOF'

        # loop over run numbers
        output_dict = dict()
        error_str = ''

        if chop_list is None:
            chop_list = [None]
        run_chop_pair = list(itertools.product(run_number_list, chop_list))

        for run_number, chop_seq in run_chop_pair:
            if chop_seq is None:
                # non-chopped data
                if self.has_reduced_workspace(ipts_number, run_number):
                    # get workspace from reduced
                    gsas_ws_name = self.get_reduced_workspace(ipts_number, run_number=run_number)
                else:
                    # from loaded data manager
                    gsas_ws_name = '{0}_gsas'.format(run_number)
                    if self.data_loading_manager.has_data(data_key=gsas_ws_name) is False:
                        error_str += 'IPTS {0} run {1} is not either reduced or loaded' \
                                     ''.format(ipts_number, run_number)
                        continue
                    # END-IF
                # END-IF-ELSE (searching workspace)
            else:
                # chopped data
                gsas_ws_name = '{0}_gsas'.format(chop_seq)
                if not self.data_loading_manager.has_data(gsas_ws_name):
                    error_str += 'IPTS {0} Run{1} Chop-seq {2} cannot be found of workspace name {3}.' \
                                 ''.format(ipts_number, run_number, chop_seq, gsas_ws_name)
                    continue
            # END

            # get data set
            data_set, unit = mantid_helper.get_data_from_workspace(gsas_ws_name, target_unit=unit,
                                                                   start_bank_id=1)

            # get data and calculate
            for bank_id in data_set.keys():
                vec_d = data_set[bank_id][0]
                vec_y = data_set[bank_id][1]

                min_x_index = max(0, numpy.searchsorted(vec_d, x_min)-1)
                max_x_index = min(len(vec_y), numpy.searchsorted(vec_d, x_max)+1)

                # estimate background
                bkgd_a, bkgd_b = peak_util.estimate_background(vec_d, vec_y, min_x_index, max_x_index)

                # calculate peak intensity parameters
                peak_integral, average_d, variance = peak_util.calculate_peak_variance(vec_d, vec_y, min_x_index,
                                                                                       max_x_index, bkgd_a, bkgd_b)

                if bank_id not in output_dict:
                    output_dict[bank_id] = ''
                output_dict[bank_id] += '{0}\t{1}\t{2}\t{3}\n'.format(run_number, peak_integral, average_d, variance)
            # END-FOR
        # END-FOR (run start)

        # output
        if file_name is not None:
            base_name, extension = os.path.splitext(file_name)
            for bank_id in output_dict.keys():
                sub_file_name = '{0}_bank{1}{2}'.format(base_name, bank_id, extension)
                try:
                    sub_file = open(sub_file_name, 'w')
                    sub_file.write(output_dict[bank_id])
                    sub_file.close()
                except IOError as io_err:
                    raise RuntimeError('Unable to write to file {0} due to {1}'.format(sub_file_name, io_err))
            # END-FOR
        # END-IF

        return output_dict

    def get_workspace_name_by_data_key(self, data_key):
        """
        :param data_key:
        :return:
        """
        if isinstance(data_key, str):
            # Check what it shall be
            print ('[DB...BAT] data key: {0}'.format(data_key))
            if data_key.endswith('G') or data_key.endswith('H'):
                ws_name = self._loadedDataManager.get_workspace_name(data_key)
                print ('[DB...BAT...33n: workspace name: {0}'.format(ws_name))
            elif data_key.isdigit():
                # reduced runs.  data key is the string version of integer run number
                run_number = int(data_key)
                found_it = self._reductionManager.has_run_reduced(run_number)
                if found_it:
                    ws_name = self._reductionManager.get_reduced_workspace(run_number=int(data_key),
                                                                           is_vdrive_bin=False)
                else:
                    raise RuntimeError('Run number {0} cannot be found in reduction manager.'.format(run_number))
            else:
                raise RuntimeError('Data key {} is not recognized.'.format(data_key))
        elif isinstance(data_key, tuple):
            # case for chopped series
            if len(data_key) != 2:
                raise RuntimeError('If data key is a tuple, it must have 2 items but not {0}.'.format(data_key))
            # TODO FIXME ASAP ASAP3 - this is a hack!
            ws_name = data_key[1]
        else:
            # non-supported
            raise AssertionError('Data key {0} of type {1} is not supported.'.format(data_key, type(data_key)))

        return ws_name

    def check_runs(self, ipts_number, run_number_list, check_archive):
        """ check whether a series of run numbers exist
        :param ipts_number:
        :param run_number_list:
        :param check_archive: flag to check archive if run number cannot be found in project
        :return:
        """
        # check input
        assert isinstance(ipts_number, int), 'IPTS number {0}  must be an integer but not a {1}' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(run_number_list, list), 'Run numbers {0} must be given in a list but not a {1}' \
                                                  ''.format(run_number_list, type(run_number_list))

        # initialize inputs
        status = True
        error_message = ''
        available_runs = run_number_list[:]

        remove_index_list = list()
        for index, run_number in enumerate(run_number_list):
            if run_number in self._dataFileDict or run_number in self._scannedRunDict:
                # run has been scanned
                continue
            elif check_archive:
                # not scanned.  then check input
                file_name_0 = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}_events.nxs.h5'.format(ipts_number, run_number)
                file_name_1 = '/SNS/VULCAN/IPTS-{1}/data/VULCAN_{1}_events.nxs'.format(ipts_number, run_number)
                if os.path.exists(file_name_0) or os.path.exists(file_name_1):
                    # found
                    continue

            # not found
            status = False
            error_message += 'Run {0} cannot be located in IPTS {1}. Removed from input.\n' \
                             ''.format(run_number, ipts_number)
            remove_index_list.append(index)
        # END-FOR

        # remove
        if not status:
            remove_index_list.sort(reverse=True)
            for index in remove_index_list:
                available_runs.pop(index)

        return status, error_message, available_runs

    # TODO - TONIGHT 0 - Better codes
    def chop_run(self, run_number, slicer_key, reduce_flag, vanadium, save_chopped_nexus,
                 number_banks, tof_correction, output_directory,
                 user_bin_parameter, roi_list, mask_list, nexus_file_name=None,
                 gsas_iparm_file='vulcan.prm',
                 overlap_mode=False, gda_start=1):
        """
        Chop a run (Nexus) with pre-defined splitters workspace and optionally reduce the
        split workspaces to GSAS

        cases to deal with difference scenarios:
        1. reduce_flag = True, output_dir is False: save to archive
        2. reduce_flag = True, output_dir is given, save_chopped_nexus is True: save both GSAS files and NeXus to same
                directory
        3. reduce_flag = False, output_dir is false: save to archive
        :param run_number:
        :param slicer_key:
        :param reduce_flag:
        :param vanadium:
        :param save_chopped_nexus: flag for saving chopped data to NeXus
        :param tof_correction:
        :param number_banks:
        :param output_directory:
        :param user_bin_parameter: None or [NOT SURE]
        :param roi_list:
        :param mask_list:
        :param nexus_file_name: None or string if user specifies one NeXus file
        :param gsas_iparm_file: GSAS IPARM file
        :return:
        """
        # TODO/ISSUE/NOWNOW 20181018 - put export_log_type ('loadframe') to chop_run; the adv_vulcan_chop support it!

        # check inputs' validity
        datatypeutility.check_string_variable('Slicer key', slicer_key)
        if nexus_file_name is None:
            # if Run number is specified
            datatypeutility.check_int_variable('Run number', run_number, (1, None))
        else:
            # if nexus file is given but not run number, then using a pseudo run number 0
            run_number = 0

        # get chopping helper
        try:
            chopper = self._chopManagerDict[run_number]
            # retrieve split workspace and split information workspace from chopper manager
            split_ws_name, info_ws_name = chopper.get_split_workspace(slicer_key)
        except KeyError as key_error:
            error_message = 'Run number %d is not registered to chopper manager (%s). Current runs are %s.' \
                            '' % (run_number, str(key_error), str(self._chopManagerDict.keys()))
            raise RuntimeError(error_message)
        # END-TYR

        # get data file path and IPTS number
        if run_number > 0:
            try:
                data_file = self.get_file_path(run_number)
                ipts_number = self.get_ipts_number(run_number)
            except RuntimeError as run_error:
                return False, 'Unable to get data file path and IPTS number of run {0} due to {1}.' \
                              ''.format(run_number, run_error)
        else:
            # user providing nexus file
            datatypeutility.check_file_name(nexus_file_name, check_exist=True, note='Event NeXus file name')
            data_file = nexus_file_name
            ipts_number = 0

        # vanadium and iparam
        if vanadium is not None:
            datatypeutility.check_int_variable('Vanadium run number', vanadium, (1, None))
            van_gsas_name, iparam_file_name = \
                self._parent.archive_manager.locate_process_vanadium(vanadium)
        else:
            van_gsas_name = None
            iparam_file_name = gsas_iparm_file

        # chop and (optionally) diffraction focus the binning data
        # TODO - NIGHT - Need to pass no_calibration_mask
        status, chop_message = self._reductionManager.chop_vulcan_run(ipts_number=ipts_number,
                                                                      run_number=run_number,
                                                                      raw_file_name=data_file,
                                                                      split_ws_name=split_ws_name,
                                                                      split_info_name=info_ws_name,
                                                                      slice_key=slicer_key,
                                                                      output_directory=output_directory,
                                                                      reduce_data_flag=reduce_flag,
                                                                      save_chopped_nexus=save_chopped_nexus,
                                                                      number_banks=number_banks,
                                                                      tof_correction=tof_correction,
                                                                      user_binning_parameter=user_bin_parameter,
                                                                      roi_list=roi_list,
                                                                      mask_list=mask_list,
                                                                      van_gda_name=van_gsas_name,
                                                                      gsas_parm_name=iparam_file_name,
                                                                      no_cal_mask=False,
                                                                      bin_overlap_mode=overlap_mode,
                                                                      gda_file_start=gda_start)

        regular_info, error_message = chop_message

        # process outputs
        if status:
            # # register: returned is a tuple
            # print ('[UND] Successful return of chop vulcan run: {}. Slice key: {}'.format(chop_message, slicer_key))
            # self._chopped_data_dict[(run_number, slicer_key)] = chop_message
            #
            # self._reductionManager.get_sliced_focused_workspaces(run_number, slicer_key)  # UND

            # better output message
            if output_directory is None:
                output_directory = '/SNS/VULCAN/IPTS-{}/shared/binned_data/{}'.format(ipts_number, run_number)
            message = 'IPTS-{0} Run {1} is chopped, reduced (?={2}) and saved to {3}\n' \
                      '\n{4}\nWarning: {5}' \
                      ''.format(ipts_number, run_number, reduce_flag, output_directory, regular_info,
                                error_message)
        else:
            message = error_message
        # END-IF-ELSE

        return status, message

    def clear_reduction_flags(self):
        """ Set to all runs' reduction flags to be False
        :return:
        """
        for run_number in self._sampleRunReductionFlagDict.keys():
            self._sampleRunReductionFlagDict[run_number] = False

        return

    @property
    def data_loading_manager(self):
        """
        return the handler to data loading manager
        :return:
        """
        return self._loadedDataManager

    # NOTE: No caller of this method so far
    def delete_slicers(self, run_number, slicer_tag=None):
        """ delete slicers from memory, i.e., mantid workspaces
        :param run_number: run number for the slicer
        :param slicer_tag:
        :return:
        """
        # check input
        if run_number not in self._chopManagerDict:
            return False, 'Run number %s does not have DataChopper associated.' % str(run_number)

        # get chopper
        data_chopper = self._chopManagerDict[run_number]

        # let DataChopper to do business
        data_chopper.delete_splitter_workspace(slicer_tag)

        return True, ''

    def clear_runs(self):
        """
        Purpose:
            Clear memory, i.e., loaded workspace
        Requirements:

        Guarantees:

        :return:
        """
        assert(isinstance(self._dataFileDict, dict))
        self._dataFileDict.clear()

        return

    def delete_data_file(self, data_file_name):
        """
        Delete a data file in the project but not delete the file physically
        :param data_file_name:
        :return: boolean.  True if it is in the data file dictionary. False it is not in the project
        """
        # check validity
        assert isinstance(data_file_name, str), 'Data file name %s must be a string but not a %s.' \
                                                '' % (str(data_file_name), type(data_file_name))

        # delete data file only if it is in the file dictionary
        if data_file_name in self._dataFileDict:
            del self._dataFileDict[data_file_name]
            self._baseDataFileNameList.remove(os.path.basename(data_file_name))
            return True

        return False

    def find_diffraction_peaks(self, data_key, bank_number, x_range,
                               peak_positions, hkl_list, profile):
        """
        Find diffraction peaks
        :param data_key: a data key (for loaded previously reduced data) or run number. For workspace or WorksapceGroup
        :param bank_number:
        :param x_range:
        :param peak_positions: If not specified (None) then it is in auto mode
        :param hkl_list:
        :param profile:
        :return:
        """
        # Check input
        assert isinstance(data_key, int) or isinstance(data_key, str), 'Data key {0} must be either an integer or a ' \
                                                                       'string but not a {1}.' \
                                                                       ''.format(data_key, type(data_key))
        assert isinstance(bank_number, int), 'Bank number must be an integer.'
        assert isinstance(x_range, tuple) and len(x_range) == 2, 'X-range must be a 2-tuple.'
        assert isinstance(profile, str), 'Peak profile must be a string.'
        if peak_positions is not None:
            datatypeutility.check_list('Peak positions', peak_positions)

        # locate the workspace
        if isinstance(data_key, int) and self._reductionManager.has_run_reduced(data_key):
            data_ws_name = self._reductionManager.get_reduced_workspace(run_number=data_key, is_vdrive_bin=True)
        elif self._loadedDataManager.has_data(data_key):
            data_ws_name = self._loadedDataManager.get_workspace_name(data_key)
        else:
            raise RuntimeError('Workspace cannot be found with data key/run number {0}'.format(data_key))

        # check WorkspaceGroup
        ws_index = bank_number - 1
        if mantid_helper.is_workspace_group(data_ws_name):
            ws_group = mantid_helper.retrieve_workspace(data_ws_name)
            data_ws_name = ws_group[ws_index].name()
            ws_index = 0

        #
        if peak_positions is None:
            # find peaks in an automatic way
            peak_info_list = mantid_helper.find_peaks(diff_data=data_ws_name,
                                                      ws_index=ws_index,
                                                      peak_profile=profile,
                                                      is_high_background=True,
                                                      background_type='Linear')
        else:
            # # find the peaks with list
            peak_info_list = mantid_helper.find_peaks(diff_data=data_ws_name,
                                                      ws_index=ws_index,
                                                      peak_profile=profile,
                                                      is_high_background=True,
                                                      background_type='Linear',
                                                      peak_pos_list=peak_positions)

        return peak_info_list

    def get_chopper(self, run_number, nxs_file_name=None):
        """
        Get data chopper (manager) of a run number
        If the run number does not have any DataChopper associated, then create a one
        :param run_number:
        :param nxs_file_name:
        :return: DataChopper instance
        """
        if run_number in self._chopManagerDict:
            # get the existing DataChopper instance
            run_chopper = self._chopManagerDict[run_number]
        else:
            # create a new DataChopper associated with this run
            if nxs_file_name is None:
                nxs_file_name = self.get_file_path(run_number)
            if not isinstance(run_number, int) or run_number < 0:
                run_number = 0
            run_chopper = DataChopper(run_number, nxs_file_name)

            # register chopper
            self._chopManagerDict[run_number] = run_chopper
        # END-IF-ELSE

        return run_chopper

    def get_data_bank_list(self, data_key):
        """ Get bank information of a loaded data file (workspace)
        Requirements: data_key is a valid string as an existing key to the MatrixWorkspace
        Guarantees: return
        :param data_key:
        :return:
        """
        if self._loadedDataManager.has_data(data_key):
            bank_list = self._loadedDataManager.get_bank_list(data_key)
        elif mantid_helper.workspace_does_exist(data_key):
            bank_list = mantid_helper.get_data_banks(data_key, 1)
        else:
            raise RuntimeError('Data key {0} cannot be found in project manager.'.format(data_key))

        return bank_list

    def gen_data_slice_manual(self, run_number, relative_time, time_segment_list, slice_tag):
        """ generate event slicer for data manually
        :param run_number:
        :param relative_time:
        :param time_segment_list:
        :param slice_tag: string for slice tag name
        :return:
        """
        # check whether there is a DataChopper instance associated
        if run_number not in self._chopManagerDict:
            return False, 'Run number %s does not have DataChopper associated.'

        # generate data slicer
        status, ret_obj = self._chopManagerDict[run_number].generate_events_filter_manual(
            run_number, time_segment_list, relative_time, slice_tag)

        return status, ret_obj

    def gen_data_slicer_sample_log(self, run_number, sample_log_name,
                                   start_time, end_time, min_log_value, max_log_value,
                                   log_value_step, slice_tag=None):
        """
        Generate data slicer/splitters by log values
        :param run_number:
        :param sample_log_name:
        :param start_time:
        :param end_time:
        :param min_log_value:
        :param max_log_value:
        :param log_value_step:
        :param slice_tag:
        :return:
        """
        raise RuntimeError('This method shall be reviewed!')
        # # TEST/NOWNOW - Need to find a test for this!
        # # check whether DataChopper
        # if run_number not in self._chopManagerDict:
        #     return False, 'Run number %s does not have DataChopper associated.' % str(run_number)
        #
        # # Get file name according to run number
        # if isinstance(run_number, int):
        #     # run number is a Run Number, locate file
        #     file_name = self.get_file_path(run_number)
        # elif isinstance(run_number, str):
        #     # run number is a file name
        #     base_file_name = run_number
        #     file_name = self.get_file_path(base_file_name)
        # else:
        #     return False, 'Input run_number %s is either an integer or string.' % str(run_number)
        #
        # # Start a session
        # # FIXE/NOWNOW - How to get slicer manager to do these jobs
        # self._mySlicingManager.load_meta_data_from_file(nxs_file_name=file_name, run_number=run_number)
        #
        # # this_ws_name = get_standard_ws_name(file_name, True)
        # # mtdHelper.load_nexus(file_name, this_ws_name, True)
        # # slicer_name, info_name = get_splitters_names(this_ws_name)
        # # print '[DB] slicer_name = ', slicer_name, 'info_name = ', info_name, 'ws_name = ', this_ws_name,
        # # print 'log_name = ', sample_log_name
        #
        # # FIXME - Need to pass value change direction
        # self._mySlicingManager.generate_events_filter_by_log(log_name=sample_log_name,
        #                                                      min_time=start_time, max_time=end_time,
        #                                                      relative_time=True,
        #                                                      min_log_value=min_log_value,
        #                                                      max_log_value=max_log_value,
        #                                                      log_value_interval=log_value_step,
        #                                                      value_change_direction='Both',
        #                                                      tag=slice_tag)
        #
        # return

    def get_file_path(self, run_number):
        """ Get file path
        Purpose: Get the file path from run number
        Requirements: run number is non-negative integer and it has been loaded to Project
        Guarantees: the file path is given
        :param run_number:
        :return:
        """
        datatypeutility.check_int_variable('Run number', run_number, (0, None))

        if run_number in self._dataFileDict:
            file_path = self._dataFileDict[run_number][0]
        else:
            raise RuntimeError('Run %d does not exist in this project.' % run_number)

        return file_path

    def get_ipts_number(self, run_number):
        """
        get the IPTS number of a run
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number >= 0, 'blabla'

        if run_number in self._dataFileDict:
            ipts_number = self._dataFileDict[run_number][1]
        else:
            raise RuntimeError('Run %d does not exist in this project.' % run_number)

        return ipts_number

    def getBaseDataPath(self):
        """ Get the base data path of the project
        """
        return self._baseDataPath

    def get_ipts_runs(self):
        """ Get IPTS numbers and runs
        :return: dictionary of list. Key: ipts number, Value: list of runs belonged to ipts
        """
        ipts_dict = dict()

        for run_number in self._dataFileDict.keys():
            ipts_number = self._dataFileDict[run_number][1]
            if ipts_number not in ipts_dict:
                ipts_dict[ipts_number] = list()
            ipts_dict[ipts_number].append(run_number)
        # END-FOR (run_number)

        # Sort
        for ipts_number in ipts_dict.keys():
            ipts_dict[ipts_number].sort()

        return ipts_dict

    def get_chopped_sequence(self, chop_data_key):
        """ Get the list of a chopped sequence (integers).
        Note: this method will examine both loaded data manager and reduced data manager
              thus, it is kept in Project
        :param chop_data_key: key to locate the chopped workspaces
        :return:
        """
        # check reduced data
        if isinstance(chop_data_key, tuple) and self._reductionManager.has_run_sliced_reduced(chop_data_key):
            # reduced runs from memory
            sequence_keys = self._reductionManager.get_sliced_focused_workspaces(chop_data_key[0],
                                                                                 chop_data_key[1])

        else:
            # loaded from GSAS files
            sequence_keys = self._loadedDataManager.get_chopped_sequences(chop_data_key)
            print ('[UND] sequence keys: {}'.format(sequence_keys))
        # END-IF-ELSE

        return sequence_keys

    def get_chopped_sequence_data(self, chop_data_key, chop_sequence, bank_id, unit='dSpacing'):
        """ Get the data (vec x and vec y) of a workspace in a chopped data sequence
        :param chop_data_key:
        :param chop_sequence: sequence index in the chopped run
        :param bank_id: bank ID
        :param unit: target unit
        :return: 2-tuple (vector X and vector Y)
        """
        # check inputs
        datatypeutility.check_int_variable('Chopped data sequence (index)', chop_sequence, (0, None))
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 999))

        # check reduced data
        if isinstance(chop_data_key, tuple) and self._reductionManager.has_run_sliced_reduced(chop_data_key):
            # reduced runs from memory
            sequence_keys = self._reductionManager.get_sliced_focused_workspaces(chop_data_key[0],
                                                                                 chop_data_key[1])
            workspace_name = sequence_keys[chop_sequence]

        else:
            # loaded from GSAS files
            datatypeutility.check_int_variable('Run number/chop data key', chop_data_key, (1, None))
            info_tuple = self._loadedDataManager.get_chopped_sequence_info(chop_data_key, chop_sequence)
            workspace_name = info_tuple[0]
        # END-IF

        data_set_dict, data_unit = mantid_helper.get_data_from_workspace(workspace_name, bank_id, unit)
        data_set = data_set_dict[bank_id]

        return data_set[0], data_set[1]

    # # TODO FIXME - TODAY - Find out how NOT to use this method
    # def get_loaded_chopped_reduced_runs(self):
    #     """
    #     get the runs that are loaded as chopped data from SNS archive or HDD
    #     :return: list of run numbers (string with special tag)
    #     """
    #     print ('[DB...BAT] Archived loaded data: {}'.format(self._loadedDataManager.get_loaded_chopped_runs()))
    #
    #     return self._chopped_data_dict.keys()

    def get_loaded_reduced_runs(self):
        """
        get the runs that are loaded as reduced data from SNS archive or HDD (for example as GSAS)
        :return:
        """
        return self._loadedDataManager.get_loaded_runs()

    def get_number_data_files(self):
        """
        Get the number/amount of the data files that have been set to the project.
        :return:
        """
        return len(self._dataFileDict)

    def get_runs_to_reduce(self):
        """
        Get run numbers that are going to be reduced
        :return: a list of integers
        """
        run_number_list = list()
        for run_number in self._sampleRunReductionFlagDict.keys():
            if self._sampleRunReductionFlagDict[run_number]:
                run_number_list.append(run_number)

        return run_number_list

    def get_reduced_data(self, run_id, target_unit, reduced_data_file=None):
        """ Get reduced data
        Purpose: Get all data from a reduced run, either from run number or data key
        - Order to locate the reduced data
          1. loaded reduced data file referenced by data_key;
          2. reduced data from reduction manager;
          3. given data file from archive;
        Requirements: run ID is either integer or data key.  target unit must be TOF, dSpacing or ...
        Guarantees: returned with 3 numpy arrays, x, y and e
        :param run_id: it is a run number or data key
        :param target_unit:
        :param reduced_data_file: flag to allow search reduced data from archive
        :return: 2-tuple: status and a dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # Check inputs
        assert isinstance(run_id, int) or isinstance(run_id, str), 'Run ID must be either integer or string,' \
                                                                   'but not %s.' % str(type(run_id))
        assert isinstance(target_unit, str), 'Target unit must be a string but not %s.' % str(type(target_unit))

        # get data
        if self._loadedDataManager.has_data(run_id):
            # get data from loaded data manager
            data_set = self._loadedDataManager.get_data_set(run_id, target_unit)

        elif self._reductionManager.has_run_reduced(run_id):
            # try to get data from reduction manager if given run number (run id)
            data_set = self._reductionManager.get_reduced_data(run_id, target_unit)

        elif isinstance(reduced_data_file, str) and os.path.exists(reduced_data_file):
            # load from a file
            data_key = self._loadedDataManager.load_binned_data(data_file_name=reduced_data_file,
                                                                data_file_type=None, prefix=None, max_int=None)
            data_set = self._loadedDataManager.get_data_set(data_key, target_unit)

        else:
            # no idea what to do
            raise RuntimeError('Unable to find reduced data run ID ={0}, unit = {1}, data file = {2}'
                               ''.format(run_id, target_unit, reduced_data_file))
        # END-IF-ELSE

        # check return
        assert isinstance(data_set, dict), 'Returned data set should be a dictionary but not %s.' % str(type(data_set))

        return data_set

    def get_reduced_workspace(self, ipts_number, run_number):
        """
        get the workspace KEY or name via IPTS number and run number
        :except: RuntimeError if there is no workspace associated
        :param ipts_number:
        :param run_number:
        :return:
        """
        if (ipts_number, run_number) in self._loadedDataDict:
            # get workspace's name from loaded gsas file
            workspace_name = self._loadedDataDict[ipts_number, run_number]
        else:
            # get workspace's name from reduction
            workspace_name = self._reductionManager.get_reduced_workspace(run_number, is_vdrive_bin=True)

        if workspace_name is None:
            raise RuntimeError('There is no reduced workspace for IPTS {0} Run {1}'.format(ipts_number, run_number))

        return workspace_name

    def get_reduced_run_information(self, run_number=None, data_key=None):
        """
        Purpose: Get the reduced run's information including list of banks
        Requirements: run number is an integer
        :param run_number:
        :return: a list of integers as bank ID. reduction history...
        """
        # Check
        if run_number:
            datatypeutility.check_int_variable('Run number', run_number, (1, 9999999))
            run_ws_name = self._reductionManager.get_reduced_workspace(run_number, is_vdrive_bin=False)
        elif data_key:
            run_ws_name = data_key
            if mantid_helper.workspace_does_exist(run_ws_name) is False:
                raise RuntimeError('Data key {} is not a workspace name in ADS'.format(data_key))
        else:
            raise RuntimeError('Either run number or data key (worksapce name) shall be given!')

        # Get workspace
        ws_info = mantid_helper.get_workspace_information(run_ws_name)

        return ws_info

    # def get_run_info(self, run_number):
    #     """
    #     Get run's information
    #     :param run_number:
    #     :return:  2-tuple (file name, IPTS number)
    #     """
    #     if run_number not in self._dataFileDict:
    #         raise RuntimeError('Unable to find run %d in project manager.' % run_number)
    #
    #     return self._dataFileDict[run_number]

    def get_runs(self):
        """
        Get runs
        :return:
        """
        run_list = self._dataFileDict.keys()
        run_list.sort()
        return run_list

    def has_reduced_workspace(self, ipts_number, run_number):
        """
        check whether a reduced workspace does exist in the workspaces managed by this ProjectManager.
        the workspace should be either in reduction manager or extra _loadedDataDict
        :return:
        """
        has_workspace = False

        if self._reductionManager.has_run_reduced(run_number):
            has_workspace = True
        elif (ipts_number, run_number) in self._loadedDataDict:
            has_workspace = True

        return has_workspace

    def has_run_information(self, run_number):
        """
        Purpose:
            Find out whether a run number is here
        Requirements:
            run number is an integer
        Guarantee:

        :return: boolean as has or not
        """
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not a {1}.' \
                                            ''.format(run_number, type(run_number))

        do_have = run_number in self._dataFileDict

        return do_have

    def load_meta_data(self, ipts_number, run_number, nxs_file_name):
        """ Load meta data from NeXus file
        :param ipts_number:
        :param run_number:
        :param nxs_file_name:
        :return:
        """
        # for log and chopping
        chopper = self.get_chopper(run_number, nxs_file_name)
        meta_ws_name = chopper.load_data_file()

        if ipts_number is None:
            ipts_number = mantid_helper.get_ipts_number(meta_ws_name)
        if nxs_file_name.endswith('.nxs') is False and nxs_file_name.endswith('.h5') is False:
            nxs_file_name = mantid_helper.get_workspace_property(meta_ws_name, 'Filename', True)

        # FIXME - I DON'T KNOW WHETHER THIS IS USEFUL???
        self.add_run(run_number, nxs_file_name, ipts_number)

        meta_ws_name = meta_ws_name

        return meta_ws_name

    # TODO FIXME - TODAY 0 - Reduction data view: how NOT to use it
    # def load_chopped_binned_file(self, data_dir, chopped_seq_list, run_number):
    #     """
    #     Load chopped workspaces
    #     :param data_dir:
    #     :param chopped_seq_list:
    #     :param run_number:
    #     :return: tuple (key, dict)
    #     """
    #     result = self._loadedDataManager.load_chopped_binned_data(data_dir,
    #                                                               chopped_seq_list,
    #                                                               file_format='gsas',
    #                                                               prefix='{}'.format(run_number))
    #
    #     chopped_data_dict = result[0]   # [seq-index] = workspace name, file name
    #
    #     self._chopped_data_dict[run_number] = chopped_data_dict
    #
    #     return run_number, chopped_data_dict

    def load_session_from_dict(self, save_dict):
        """ Load session from a dictionary
        :param save_dict:
        :return:
        """
        assert isinstance(save_dict, dict), 'Parameters to save {0} must be given by a dictionary but not a {1}.' \
                                            ''.format(save_dict, type(save_dict))

        # Set
        self._name = save_dict['name']
        self._baseDataPath = save_dict['baseDataPath']
        self._dataFileDict = save_dict['dataFileDict']
        self._baseDataFileNameList = save_dict['baseDataFileNameList']

        return

    def mark_runs_to_reduce(self, run_number_list):
        """ Mark runs to reduce
        Purpose:

        Requirements:
            1. run number does exist in this project;
            2. data file of this run is accessible
            3. input run number list must be a list of integer
        Guarantees
        :param run_number_list:
        :return: None
        """
        # Check requirements
        assert isinstance(run_number_list, list), 'Run numbers {0} must be a list but not a {1}.' \
                                                  ''.format(run_number_list, type(run_number_list))

        # Mark each runs
        for run_number in sorted(run_number_list):
            assert isinstance(run_number, int),\
                'run_number must be of type integer but not %s' % str(type(run_number))
            if self.has_run_information(run_number) is False:
                # no run
                raise RuntimeError('Run %d cannot be found.' % run_number)
            elif archivemanager.check_read_access(self.get_file_path(run_number)) is False:
                # file does not exist
                raise RuntimeError('Run %d with file path %s cannot be found.' % (run_number,
                                                                                  self.get_file_path(run_number)))
            else:
                # mark runs to reduce
                self._sampleRunReductionFlagDict[run_number] = True
        # END-FOR

        return

    def mark_runs_reduced(self, run_number_list, reduction_state_list=None):
        """
        mark runs that have been reduced
        :param run_number_list:
        :param reduction_state_list:
        :return:
        """
        # TODO/FUTURE/NEXT - Implement more for the reduction state
        assert isinstance(run_number_list, list), 'Run numbers {0} must be a list but not a {1}.' \
                                                  ''.format(run_number_list, type(run_number_list))

        for run_number in run_number_list:
            if run_number in self._sampleRunReductionFlagDict:
                self._sampleRunReductionFlagDict[run_number] = False
                print '[Info] Run {0} is in ReductionFlagDict.'.format(run_number)
            else:
                print '[Warning] Run {0} is not in ReductionFlagDict. It cannot be marked as being reduced.'.format(run_number)

        return

    @property
    def name(self):
        """ Return project name
        :return: if return None, it means that the project name has not been set up yet.
        """
        return self._name

    @name.setter
    def name(self, project_name):
        """ Set project name
        Requirements: project name is a string
        :param project_name:
        :return:
        """
        assert isinstance(project_name, str)
        self._name = project_name

        return
    
    @property
    def reduction_manager(self):
        """
        handler to _myReductionManager
        :return:
        """
        return self._reductionManager

    # NOTE : reduce_nexus_files() is merged into VDriveAPI.reduced_chopped_data_set
    # def reduce_nexus_files(self, raw_file_list, output_directory, vanadium, gsas, binning_parameters, use_idl_bin,
    #                        merge_banks, align_to_vdrive_bin, vanadium_tuple=None, standard_sample_tuple=None,
    #                        num_banks=3):
    #     """
    #     Reduce a list of NeXus files
    #     This could be similar to reduce runs
    #     :param raw_file_list:
    #     :param output_directory:
    #     :param vanadium:
    #     :param gsas:
    #     :param binning_parameters:
    #     :param use_idl_bin: bool as the flag to use IDL-VDRIVE bins. It will override binning parameters
    #     :param align_to_vdrive_bin:
    #     :param vanadium_tuple:
    #     :param standard_sample_tuple:
    #     :param num_banks:  number of banks focused to.  Now only 3, 7 and 27 are allowed.
    #     :return:
    #     """
    #     # check inputs
    #     datatypeutility.check_list('Raw Nexus files', raw_file_list)
    #
    #     # prepare
    #     sum_status = True
    #     sum_message = ''
    #
    #     for nexus_file_name in raw_file_list:
    #         status, sub_message = \
    #             self._reductionManager.process_vulcan_ipts_run(ipts_number=None, run_number=None,
    #                                                            event_file=nexus_file_name,
    #                                                            output_directory=output_directory,
    #                                                            merge_banks=merge_banks,
    #                                                            vanadium=vanadium,
    #                                                            vanadium_tuple=vanadium_tuple,
    #                                                            gsas=gsas,
    #                                                            standard_sample_tuple=standard_sample_tuple,
    #                                                            binning_parameters=binning_parameters,
    #                                                            use_idl_bin=use_idl_bin,
    #                                                            num_banks=num_banks)
    #         if not status:
    #             sum_status = False
    #             sum_message += '{0}\n'.format(sum_message)
    #     # END-FOR
    #
    #     return sum_status, sum_message

    def reduce_runs(self, run_number_list, output_directory, background,
                    vanadium, gsas, fullprof, record_file,
                    sample_log_file, standard_sample_tuple,
                    merge_banks,
                    merge_runs, binning_parameters, num_banks=3):
        """ Reduce a set of runs with selected options
        Purpose:
        Requirements:
        Guarantees:

        Workflow:
         1. Get a list of runs to reduce;
         2. Get a list of vanadium runs for them;
         3. Reduce all vanadium runs;
         4. Reduce (and possibly chop) runs;

        Arguments:
         - normByVanadium :: flag to normalize by vanadium


        Note:
        1. There is no need to call LoadCalFile explicitly, because AlignAndFocus() will
           check whether the calibration file has been loaded by standard offset and group
           workspace name.
        2. It tries to use most of the existing methods from auto reduction scripts
        Focus and process the selected data sets to powder diffraction data
        for GSAS/Fullprof/ format
        :param run_number_list:
        :param output_directory:  output directory. if not given (None) then set it up to instrument default?
        :param background:
        :param vanadium:
        :param gsas:
        :param fullprof:
        :param record_file:
        :param sample_log_file:
        :param standard_sample_tuple: 3-tuple: (sample_name, sample_directory, sample_record_name)
        :param merge_banks:
        :param merge_runs:
        :param binning_parameters:
        :param num_banks:  number of banks focused to.  Now only 3, 7 and 27 are allowed.
        :return:  (boolean, message)
        """
        # rule out the situation that the standard can be only processed one at a time
        if standard_sample_tuple is not None and len(run_number_list) > 1:
            raise RuntimeError('It is not allowed to process multiple standard samples {0} in a single call.'
                               ''.format(run_number_list))

        # check input
        assert isinstance(run_number_list, list), 'Run number must be a list.'

        reduce_all_success = True
        message = ''

        vanadium_tag = '{0:06d}'.format(random.randint(1, 999999))

        if not merge_runs:
            # reduce runs one by one
            for run_number in run_number_list:
                # get IPTS and files
                full_event_file_path, ipts_number = self._dataFileDict[run_number]

                # vanadium
                if vanadium:
                    try:
                        van_run = self._sampleRunVanadiumDict[run_number]
                        van_gda = self._vanadiumGSASFileDict[van_run]
                        vanadium_tuple = van_run, van_gda, vanadium_tag
                    except KeyError:
                        reduce_all_success = False
                        message += 'Run {0}: No valid vanadium run set up!\n.'.format(run_number)
                        continue
                else:
                    vanadium_tuple = None
                # END-IF (vanadium)

                # reduce
                print '[INFO] (Version 1) Reduce IPTS {0} Run {1}'.format(ipts_number, run_number)
                r_tup = self._reductionManager.reduce_event_nexus_ver1(ipts_number, run_number,
                                                                       full_event_file_path,
                                                                       output_directory,
                                                                       vanadium=vanadium, vanadium_tuple=vanadium_tuple,
                                                                       gsas=gsas,
                                                                       standard_sample_tuple=standard_sample_tuple,
                                                                       binning_parameters=binning_parameters,
                                                                       merge_banks=merge_banks,
                                                                       num_banks=num_banks)

                status, sub_message = r_tup
                reduce_all_success = reduce_all_success and status
                if not status:
                    message += 'Failed to reduce run {0} due to {1}.\n'.format(run_number, sub_message)
            # END-FOR
        else:
            # merge runs
            common_van_run = None
            common_van_gda = None
            ipts_run_list = list()

            # get information for all runs to merge and the vanadium run to them
            for run_number in run_number_list:
                # get IPTS and files
                full_event_file_path, ipts_number = self._dataFileDict[run_number]

                ipts_run_list.append((ipts_number, run_number, full_event_file_path))

                # vanadium
                if vanadium:
                    try:
                        van_run = self._sampleRunVanadiumDict[run_number]
                        van_gda = self._vanadiumGSASFileDict[van_run]
                    except KeyError:
                        return False, 'Vanadium for run {0} cannot be located.'.format(run_number)

                    if common_van_gda is None:
                        common_van_run = van_run
                        common_van_gda = van_gda
                    elif van_run != common_van_run:
                        return False, 'Runs to merge do not have same vanadium to normalize'
                # END-IF (vanadium)
            # END-FOR

            vanadium_tuple = common_van_run, common_van_gda, vanadium_tag

            # reduce
            status,  message = self._reductionManager.merge_reduce_runs(ipts_run_list,
                                                                        output_dir=output_directory,
                                                                        vanadium_info=vanadium_tuple, gsas=gsas,
                                                                        standard_sample_tuple=standard_sample_tuple,
                                                                        binning_parameters=binning_parameters)

        # END-IF-ELSE(merge or not)

        return reduce_all_success, message

    def reduce_vulcan_runs_v2(self, run_number_list, output_directory, d_spacing, binning_parameters,
                              number_banks, gsas, vanadium_run, merge_runs,
                              roi_list, mask_list, no_cal_mask):
        """ reduce runs in a simplied way! (it can be thought be the version 2.0!)
        Note: this method is used by VBIN
        Note 2: For merging, all the workspaces are merged to run_number_list[0].  So if the user has prference
                to the run number to be merged and saved to, put it as the first one!
        :param run_number_list: For merging, refer to Note(2)
        :param output_directory:
        :param d_spacing:
        :param binning_parameters: None for default IDL binning
        :param number_banks: number of banks to focus to
        :param gsas: flag to reduce to GSAS file
        :param vanadium_run: van run (integer or None)
        :param merge_runs: Flag to merge runs and
        :param roi_list:
        :param mask_list:
        :return: 2-tuple: list (run number), list (error message for each run reduced)
        """
        print ('[INFO] Reduction (Single Run) VULCAN Version 2 is Called')

        # check inputs
        datatypeutility.check_list('Run numbers', run_number_list)
        datatypeutility.check_file_name(output_directory, check_exist=True, is_dir=True)
        datatypeutility.check_bool_variable('Flag for output unit in dSpacing', d_spacing)
        datatypeutility.check_list('ROI XML file list', roi_list)
        datatypeutility.check_list('Mask XML file list', mask_list)

        # check binning parameters
        # if binning_parameters is None:
        #     raise RuntimeError('Binning parameters in reduce_vulcan_runs_v2 cannot be None.')
        if d_spacing and binning_parameters is not None:
            if len(binning_parameters) == 1:
                bin_size = binning_parameters[0]
            else:
                bin_size = binning_parameters[1]
            # force the binning range to be from 0.3 to 5.0
            binning_parameters = (0.3, -abs(float(bin_size)), 5.0)
        # END-IF

        # reduce one by one
        reduced_run_numbers = list()
        error_messages = list()
        for run_number in run_number_list:
            raw_file_name, ipts_number = self._dataFileDict[run_number]
            print '[DB...BAT] Attempt to reduce run {0} from {1}... Binned to {2}' \
                  ''.format(run_number, raw_file_name, binning_parameters)

            # reduce
            if d_spacing:
                unit = 'dSpacing'
            else:
                unit = 'TOF'

            try:
                # reduce event NeXus file
                out_ws_name, msg = self._reductionManager.reduce_event_nexus(ipts_number=ipts_number,
                                                                             run_number=run_number,
                                                                             event_nexus_name=raw_file_name,
                                                                             target_unit=unit,
                                                                             binning_parameters=binning_parameters,
                                                                             num_banks=number_banks,
                                                                             roi_list=roi_list,
                                                                             mask_list=mask_list,
                                                                             no_cal_mask=no_cal_mask)

                reduced_run_numbers.append((run_number, out_ws_name))
            except RuntimeError as run_error:
                error_messages.append('Failed to reduce run {0} due to {1}'.format(run_number, run_error))
            else:
                error_messages.append('[INFO] For {}: {}'.format(run_number, msg))
        # END-FOR

        # process reduced data
        if gsas and vanadium_run is not None:
            # load vanadium to workspace workspace and get calculation prm file
            van_gsas_name, iparam_file_name = \
                        self._parent.archive_manager.locate_process_vanadium(vanadium_run)
            van_ws_name = self._reductionManager.gsas_writer.import_vanadium(van_gsas_name)
        else:
            # default
            van_ws_name = None
            iparam_file_name = 'vulcan.prm'

        # binning
        if binning_parameters is None:
            align_vdrive_bin = True
        else:
            align_vdrive_bin = False

        if gsas and not merge_runs:
            # save to GSAS without merging
            for run_number, out_ws_name in reduced_run_numbers:
                # get IPTS and raw file name
                raw_file_name, ipts_number = self._dataFileDict[run_number]
                run_date_time = vulcan_util.get_run_date(out_ws_name, raw_file_name)
                gsas_file_name = os.path.join(output_directory, '{}.gda'.format(run_number))

                self._reductionManager.gsas_writer.save(out_ws_name, run_date_time=run_date_time,
                                                        gsas_file_name=gsas_file_name,
                                                        ipts_number=ipts_number,
                                                        run_number=run_number,
                                                        align_vdrive_bin=align_vdrive_bin,
                                                        gsas_param_file_name=iparam_file_name,
                                                        van_ws_name=van_ws_name,
                                                        is_chopped_run=False,
                                                        write_to_file=True)
            # END-FOR
        elif gsas and merge_runs:
            # merge and then save to GSAS file
            ws_name_list = [item[1] for item in reduced_run_numbers]
            # always merged to run_number_list[0]/ws_name_list[0]
            run_number, out_ws_name = reduced_run_numbers[0]
            print ('[DB...BAT] Input run numbers: {}'.format(run_number_list))
            print ('[DB...BAT] Redued runs: {}'.format(reduced_run_numbers))
            # merge runs
            mantid_helper.merge_runs(ws_name_list, out_ws_name)

            raw_file_name, ipts_number = self._dataFileDict[run_number]
            run_date_time = vulcan_util.get_run_date(out_ws_name, raw_file_name)
            gsas_file_name = os.path.join(output_directory, '{}.gda'.format(run_number))

            self._reductionManager.gsas_writer.save(out_ws_name, run_date_time=run_date_time,
                                                    gsas_file_name=gsas_file_name,
                                                    ipts_number=ipts_number,
                                                    run_number=run_number,
                                                    align_vdrive_bin=align_vdrive_bin,
                                                    gsas_param_file_name=iparam_file_name,
                                                    van_ws_name=van_ws_name,
                                                    is_chopped_run=False,
                                                    write_to_file=True)
        else:
            # do nothing
            pass

        return reduced_run_numbers, error_messages

    def set_reduction_flag(self, run_number, flag):
        """ Set the  reduction flag for a file in SAMPLE run dictionary of this project
        Requirements: run number is non-negative integer and flag is boolean.
        Guarantees:
        :param run_number:
        :param flag: reduction flag
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int)
        assert isinstance(flag, bool)
        assert run_number in self._dataFileDict, 'Run %d is not scanned. Current scanned runs are %s.' % (
            run_number, str(self._dataFileDict.keys()))

        # Check with full name
        file_name = self._dataFileDict[run_number][0]
        assert os.path.exists(file_name), 'Unable to find data file %s.' % file_name

        # Set value
        self._sampleRunReductionFlagDict[run_number] = flag

        return

    # def set_reduction_parameters(self, parameter_dict):
    #     """
    #     Purpose: set up the parameters to reduce run
    #     Requirements:
    #     - reduction manager is available
    #     - input is a dictionary, key=parameter name, value=parameter value
    #     :param parameter_dict:
    #     :return:
    #     """
    #     # Check requirements
    #     assert self._reductionManager is not None
    #     assert isinstance(parameter_dict, dict)
    #
    #     self._reductionManager.set_parameters(parameter_dict)
    #
    #     return

    def set_vanadium_runs(self, run_number_list, van_run_number, van_file_name):
        """
        set the corresponding vanadium run to a list of run numbers
        :param run_number_list:
        :param van_run_number:
        :return: None
        """
        # check inputs
        datatypeutility.check_list('Run numbers', run_number_list)
        datatypeutility.check_int_variable('Vanadium run', van_run_number, (1, None))

        # add vanadium information
        for run_number in run_number_list:
            self._sampleRunVanadiumDict[run_number] = van_run_number

        self._vanadiumGSASFileDict[van_run_number] = van_file_name

        return

    def set_base_data_path(self, data_dir):
        """ Set base data path such as /SNS/VULCAN/
        to locate the data via run number and IPTS
        Requirements:
        1. input is an existing file directory
        :param data_dir: base data directory. for example, /SNS/VULCAN/
        :return: None
        """
        if isinstance(data_dir, str) is True:
            assert os.path.exists(data_dir)
            self._baseDataPath = data_dir
        else:
            raise OSError("Unable to set base data path with unsupported format %s." % str(type(data_dir)))

        return

    @property
    def vanadium_processing_manager(self):
        """
        get the holder to the vanadium processing manager
        :return:
        """
        return self._processVanadiumManager

    # @property
    # def vdrive_bin_template(self):
    #     """
    #     get the VDRIVE binning template workspace name
    #     :return:
    #     """
    #     return self._vdriveBinTemplateName


def get_data_key(file_name):
    """ Generate data key according to file name
    :param file_name:
    :return:
    """
    assert isinstance(file_name, str), 'Input file name {0} must be a string but not a {1}.' \
                                       ''.format(file_name, type(file_name))

    return os.path.basename(file_name)
