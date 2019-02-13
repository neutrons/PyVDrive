# Methods for processing vanadiums
import os
import shutil
import mantid_helper
import datatypeutility
from reduce_VULCAN import align_bins
import save_vulcan_gsas
import mantid_reduction


class VanadiumProcessingManager(object):
    """
    Controller of the workflow to process vanadium data for calibration purpose
    """
    def __init__(self, parent, calibration_manager):
        """
        initialization
        :param parent:
        """
        self._myParent = parent

        # state flag
        self._is_setup = False   # flag such that a parent workspace (to smooth from) has been set up
        self._bank_group_dict = None
        self._output_ws_name = None  # workspace from merged smoothed/vanadium-peaks-striped workspace
        # NOTE: output workspace shall be of the same range, number of spectra and instrument geometry as input

        # by default
        self._output_dir = os.getcwd()

        # single spectrum workspace for the internal steps
        self._source_single_bank_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._striped_peaks_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._smoothed_ws_dict = dict()  # [bank id (1, 2, 3)] = ws names

        self._default_fwhm_dict = {1: 7, 2: 7, 3: 12}

        # final output binning
        self._calibration_manager = calibration_manager
        self._tof_bin_dict = dict()

        # these are updated class variables
        self._workspace = None
        self._van_workspace_name = None   # input vanadium workspace (focused)
        self._ipts_number = None
        self._van_run_number = None
        self._output_gsas_name = None

        return

    def __str__(self):
        """
        pretty print information
        :return:
        """
        if self._is_setup:
            source_ws = mantid_helper.retrieve_workspace(self._van_workspace_name, raise_if_not_exist=True)
            output_str = 'Process (reduced) vanadium (workspace) {} with {} banks\n' \
                         ''.format(self._van_workspace_name, source_ws.getNumberHistograms())
            output_str += 'Internal workspaces with vanadium peaks striped: {}\n'.format(self._striped_peaks_ws_dict)
            output_str += 'Internal workspaces smoothed: {}\n'.format(self._smoothed_ws_dict)
        else:
            output_str = 'No workspace has been set up for vanadium processing.\n'

        return output_str

    def shift_fwhm_for_wavelength(self):
        """
        apply shift-of-wavelength to the vanadium to process
        :return:
        """
        # TODO FIXME - TONIGHT 3 - Experiment
        raise RuntimeError('Shift FWHM shall be experimented')
        self._default_fwhm = 2

        return

    def get_peak_striped_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped
        :return:
        """
        return self._striped_peaks_ws_dict

    def get_raw_vanadium(self):
        # TODO
        return self._source_single_bank_ws_dict

    def get_smoothed_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped and smoothed
        :return:
        """
        return self._smoothed_ws_dict

    # TODO - TONIGHT 1 - Code Quality
    def init_session(self, workspace_name, ipts_number, van_run_number, out_gsas_name,
                     sample_log_ws_name):

        workspace = mantid_helper.retrieve_workspace(workspace_name)
        if workspace.id() == 'WorkspaceGroup':
            pass
        else:
            # create dictionary and etc
            raise NotImplementedError('Need to implement single workspace case to extract spectra')

        self._workspace = workspace
        self._van_workspace_name = workspace_name
        self._van_workspace_name = workspace_name

        self._ipts_number = ipts_number
        self._van_run_number = van_run_number
        self._output_gsas_name = out_gsas_name

        # convert to point data as a request
        mantid_helper.convert_to_point_data(self._van_workspace_name)

        self._sample_log_ws_name = sample_log_ws_name

        return

    def process_vanadium(self, peak_pos_tol=0.1, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth',
                         param_n=20, param_order=2):
        #  Process vanadium run including strip vanadium peaks and smooth
        # This is a high-level call to do all the work with good setup in one action

        self._workspace = mantid_helper.retrieve_workspace(self._van_workspace_name)

        for ws_index in range(mantid_helper.get_number_spectra(self._workspace)):
            # strip vanadium peaks
            bank_id = ws_index + 1
            self.strip_v_peaks(bank_id=ws_index+1, peak_fwhm=self._default_fwhm_dict[bank_id],
                               pos_tolerance=peak_pos_tol,
                               background_type=background_type,
                               is_high_background=is_high_background)
            # smoooth
            self.smooth_v_spectrum(bank_id=bank_id, smoother_filter_type=smoother_filter_type,
                                   param_n=20, param_order=2)
        # END-FOR

        # save
        message = 'Vanadium {0} has peaks removed and is smoothed.'
        status = True
        if self._output_gsas_name:
            #  save GSAS file
            try:
                self.save_vanadium_to_file()
                message += 'Processed vanadium is saved to {}'.format(self._output_gsas_name)
            except RuntimeError as run_err:
                message += 'Processed vanadium failed to be written to {0} due to {1}.' \
                           ''.format(self._output_gsas_name, run_err)
                status = False
        else:
            raise NotImplementedError('Is there any case that on one wants GSAS?')

        return status, message

    # TODO - TONIGHT 3 - Better QA
    def save_vanadium_to_file(self):
        """
        save a processed vanadium (in workspace) to GSAS file
        Note: IPTS number must be specified for being written into GSAS file;
              run number must be specified for output file name
        :param vanadium_tuple: None or 3-tuple for vanadium workspace name/IPTS number/run number
        :param to_archive
        :param out_file_name: if not None, then output locally
        :return: tuple (boolean, str): status, error message
        """
        #
        #
        # # check inputs
        # if vanadium_tuple is None:
        #     # use the class variables of this instance
        #     assert self._iptsNumber is not None, 'IPTS number must be specified.'
        #     assert self._runNumber is not None, 'Run number must be specified.'
        #     assert self._smoothed_ws_dict is not None, 'Vanadium run {0} must have been processed.' \
        #                                                 ''.format(self._runNumber)
        #
        #     workspace_name = self._smoothed_ws_dict
        #     ipts_number = self._iptsNumber
        #     run_number = self._runNumber
        #
        # else:
        #     raise RuntimeError('It is not supported to save vanadium with given workspace name.')
        #     # assert len(vanadium_tuple) == 3, 'A not-None vanadium tuple must have 3 elements but not {0}' \
        #     #                                  ''.format(len(vanadium_tuple))
        #     # workspace_name, ipts_number, run_number = vanadium_tuple
        #     # assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
        #     #                                      ''.format(ipts_number, type(ipts_number))
        #     # assert isinstance(run_number, int), 'Run number must be an integer but not a {1}.' \
        #     #                                     ''.format(run_number, type(run_number))
        # # END-IF-ELSE
        #
        # # archive file name
        # return_status = True
        # error_msg = ''
        #
        # # determine the output file name with full path
        # if to_archive:
        #     # write to archive's instrument specific calibration directory's instrument specific calibration directory
        #     base_name = '{0}-s.gda'.format(self._runNumber)
        #     van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
        #
        #     # TODO - TONIGHT - Clean: The below can be organized to a method in file_util
        #     if os.path.exists(van_dir) is False:
        #         return False, 'Vanadium directory {0} does not exist.'.format(van_dir)
        #     elif os.access(van_dir, os.W_OK) is False:
        #         return False, 'User has no privilege to write to directory {0}'.format(van_dir)
        #
        #     archive_file_name = os.path.join(van_dir, base_name)
        #     if os.path.exists(archive_file_name) and os.access(archive_file_name, os.W_OK) is False:
        #         return False, 'Smoothed vanadium GSAS file {0} exists and user does not have privilege to over write.' \
        #                       ''.format(archive_file_name)
        #     out_file_name = archive_file_name
        #
        # elif out_file_name is not None:
        #     # file name re-define & get directory of the output file
        #     if os.path.isdir(out_file_name):
        #         # get the file name
        #         local_dir = out_file_name
        #         out_file_name = os.path.join(local_dir, '{0}-s.gda'.format(run_number))
        #     else:
        #         local_dir = os.path.dirname(out_file_name)
        #     # END0F
        #     if os.access(local_dir, os.W_OK):
        #         return False, 'User cannot write to directory {0}'.format(local_dir)
        #     elif os.path.exists(out_file_name) and os.access(out_file_name, os.W_OK):
        #         return False, 'Smoothed vanadium file {0} exists but user cannot over write.'.format(out_file_name)
        #
        # else:
        #     # neither to archive nor to local directory
        #     return False, 'User does not specify either to-archive nor a local directory'

        # write to GSAS file for VDRIVE
        bank_id_list = sorted(self._smoothed_ws_dict.keys())
        # group workspaces
        input_ws_names = ''
        for bank_id in bank_id_list:
            input_ws_names += '{},'.format(self._smoothed_ws_dict[bank_id])
        input_ws_names = input_ws_names[:-1]
        processed_vanadium_name = '{}_processed'.format(self._van_workspace_name)
        mantid_helper.group_workspaces(input_ws_names, processed_vanadium_name)
        print (mantid_helper.workspace_does_exist(processed_vanadium_name))

        gsas_writer = save_vulcan_gsas.SaveVulcanGSS()
        # TODO - TONIGHT 11 - convert_to_vdrive_bins shall be considered if source file is from a high resolution
        # TODO - cont.      - ProcessedNeXus file: It shall call save() instead
        gsas_writer.save_vanadium(diff_ws_name=processed_vanadium_name, gsas_file_name=self._output_gsas_name,
                                  ipts_number=self._ipts_number, van_run_number=self._van_run_number,
                                  sample_log_ws_name=self._sample_log_ws_name)

        return

    # TODO - TONIGHT - Code Quality
    def smooth_v_spectrum(self, bank_id, smoother_filter_type, param_n, param_order, ws_name=None):

        if ws_name is None:
            ws_name = self._striped_peaks_ws_dict[bank_id]

        # output workspace name
        out_ws_name = ws_name + '_Smoothed'

        # convert unit
        mantid_helper.mtd_convert_units(ws_name, 'TOF', out_ws_name)

        # smooth vanadium spectra
        mantid_helper.smooth_vanadium(input_workspace=out_ws_name,
                                      output_workspace=out_ws_name,
                                      smooth_filter=smoother_filter_type,
                                      workspace_index=None,
                                      param_n=param_n,
                                      param_order=param_order,
                                      push_to_positive=True)

        self._smoothed_ws_dict[bank_id] = out_ws_name

        return

    def smooth_spectra(self, bank_group_index, smoother_type, param_n, param_order, smooth_original=False):
        """ Smooth focused diffraction spectra
        :param bank_group_index: integer, 90 or 150 for west/east or high angle... future will be extended
                               to 90, 85, 135, 150 and etc
        :param bank_group_index: if it is not None then the method is called as a static method
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return: output workspace name
        """
        datatypeutility.check_int_variable('Banks group index (90 or 150 degrees)', bank_group_index, (-180, 180))

        for bank_id in sorted(self._bank_group_dict[bank_group_index]):
            # get workspace with peak striped
            if bank_id in self._striped_peaks_ws_dict:
                input_ws_name = self._striped_peaks_ws_dict[bank_id]
            elif smooth_original:
                input_ws_name = self._source_single_bank_ws_dict[bank_id]
            else:
                raise RuntimeError('Bank {0} has not been striped peaks while user requires that.'.format(bank_id))

            # output workspace name
            out_ws_name = input_ws_name + '_Smoothed'

            # smooth vanadium spectra
            mantid_helper.smooth_vanadium(input_workspace=input_ws_name,
                                          output_workspace=out_ws_name,
                                          smooth_filter=smoother_type,
                                          workspace_index=None,
                                          param_n=param_n,
                                          param_order=param_order,
                                          push_to_positive=True)

            input_ws = mantid_helper.retrieve_workspace(input_ws_name)
            # NOTE: upon this point the workspace is dSpacing
            ws_unit = input_ws.getAxis(0).getUnit().unitID()
            # print ('[DB...BAT] Input workspace {} to smooth has unit {}'
            #        ''.format(input_ws_name, ws_unit))

            # rebin to final TOF binning
            if ws_unit != 'TOF':
                mantid_helper.mtd_convert_units(input_ws_name, 'TOF')

            # rebin
            mantid_reduction.VulcanBinningHelper.rebin_workspace(input_ws_name,
                                                                 binning_param_dict=self._tof_bin_dict[bank_id],
                                                                 output_ws_name=input_ws_name)
            self._smoothed_ws_dict[bank_id] = out_ws_name
        # END-FOR

        return

    def strip_v_peaks(self, bank_id, peak_fwhm, pos_tolerance, background_type, is_high_background):
        """
        strip vanadium peaks
        Note: result is stored in _striped_peaks_ws_dict
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        print (self._workspace)
        print (self._van_workspace_name)

        if self._workspace.id() == 'WorkspaceGroup':
            input_ws_name = self._workspace[bank_id-1].name()
            bank_list = 0
        else:
            input_ws_name = self._van_workspace_name
            bank_list = bank_id - 1

        print ('[DB...BAT] Strip Peaks: workspace name: {}'.format(input_ws_name))

        output_ws_name = input_ws_name + '_NoPeak'
        mantid_helper.strip_vanadium_peaks(input_ws_name=input_ws_name,
                                               output_ws_name=output_ws_name,
                                               bank_list=None,
                                               binning_parameter=None,
                                               fwhm=peak_fwhm,
                                               peak_pos_tol=pos_tolerance,
                                               background_type=background_type,
                                               is_high_background=is_high_background)
        self._striped_peaks_ws_dict[bank_id] = output_ws_name

        return output_ws_name

    def strip_peaks(self, bank_group_index, peak_fwhm, pos_tolerance, background_type, is_high_background):
        """
        strip vanadium peaks
        Note: result is stored in _striped_peaks_ws_dict
        :param bank_group_index: 90/150
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        print ('[DB...BAT] Strip Peaks: workspace name: {}'.format(input_ws_name))

        # check input
        datatypeutility.check_int_variable('Banks group index (90 degree or 150 degree)', bank_group_index, (-180, 180))

        for bank_id in sorted(self._bank_group_dict[bank_group_index]):
            input_ws_name = self._source_single_bank_ws_dict[bank_id]
            output_ws_name = input_ws_name + '_NoPeak'
            mantid_helper.strip_vanadium_peaks(input_ws_name=input_ws_name,
                                               output_ws_name=output_ws_name,
                                               bank_list=None,
                                               binning_parameter=None,
                                               fwhm=peak_fwhm,
                                               peak_pos_tol=pos_tolerance,
                                               background_type=background_type,
                                               is_high_background=is_high_background)
            self._striped_peaks_ws_dict[bank_id] = output_ws_name
        # END-FOR

        return

    def undo_peak_strip(self):
        """
        undo peak strip
        :return:
        """
        self._striped_peaks_ws_dict.clear()

        return

    def undo_smooth(self):
        """
        undo spectra smoothing
        :return:
        """
        self._smoothed_ws_dict = None

        return
