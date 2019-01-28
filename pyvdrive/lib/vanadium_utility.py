# Methods for processing vanadiums
import os
import shutil
import mantid_helper
import datatypeutility
from reduce_VULCAN import align_bins
import mantid_reduction
import save_vulcan_gsas


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
        self._source_workspace_name = None  # shall be a Workspace2D workspace
        self._bank_group_dict = None
        self._output_ws_name = None  # workspace from merged smoothed/vanadium-peaks-striped workspace
        # NOTE: output workspace shall be of the same range, number of spectra and instrument geometry as input

        # by default
        self._output_dir = os.getcwd()

        # single spectrum workspace for the internal steps
        self._source_single_bank_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._striped_peaks_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._smoothed_ws_dict = dict()  # [bank id (1, 2, 3)] = ws names

        self._default_fwhm = 7

        # final output binning
        self._calibration_manager = calibration_manager
        self._tof_bin_dict = dict()

        return

    def __str__(self):
        """
        pretty print information
        :return:
        """
        if self._is_setup:
            source_ws = mantid_helper.retrieve_workspace(self._source_workspace_name, raise_if_not_exist=True)
            output_str = 'Process (reduced) vanadium (workspace) {} with {} banks\n' \
                         ''.format(self._source_workspace_name, source_ws.getNumberHistograms())
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

    def init_session(self, workspace_name, bank_group_dict):
        """
        initialize a new session to process vanadium
        :param workspace_name:
        :param bank_group_dict:
        :return:
        """
        # TODO - 20181030 - Need to add this to configuration
        bin_param_dict = {1: (0.5, -0.001, 3.0),
                          2: (0.5, -0.001, 3.0),
                          3: (0.3, -0.0003, 3.0)}

        # check inputs
        if not mantid_helper.workspace_does_exist(workspace_name):
            raise RuntimeError('Raw matrix workspace {0} does not exist.'.format(workspace_name))
        datatypeutility.check_dict('Banks group assignment', bank_group_dict)

        # set
        self._source_workspace_name = workspace_name
        self._bank_group_dict = bank_group_dict

        # reset processed workspaces
        self._source_single_bank_ws_dict = dict()
        self._striped_peaks_ws_dict = dict()
        self._smoothed_ws_dict = dict()
        self._output_ws_name = dict()

        # prepare source single bank
        source_ws = mantid_helper.retrieve_workspace(workspace_name, True)
        for bank_id in range(1, source_ws.getNumberHistograms()+1):
            single_spec_ws_name = self._source_workspace_name + '_VBank{}'.format(bank_id)
            # extract spectrum
            mantid_helper.extract_spectrum(input_workspace=self._source_workspace_name,
                                           output_workspace=single_spec_ws_name,
                                           workspace_index=bank_id-1)

            # check
            temp_ws = mantid_helper.retrieve_workspace(single_spec_ws_name)
            assert temp_ws.getAxis(0).getUnit().unitID() == 'dSpacing', 'Input shall be in unit dSpacing'
            mantid_helper.rebin(single_spec_ws_name, bin_param_dict[bank_id], preserve=False)

            self._source_single_bank_ws_dict[bank_id] = single_spec_ws_name
        # END-FOR

        # output bins
        tof_binning_dict = self._calibration_manager.get_last_gsas_bin_ref()
        for bank_id in [1, 2, 3]:
            self._tof_bin_dict[bank_id] = {1: tof_binning_dict[bank_id]}
            print (self._tof_bin_dict[bank_id])

        # default FWHM
        self._default_fwhm = 7  # non-shift case

        self._is_setup = True

        return

    def merge_processed_vanadium(self, save, to_archive=None, local_file_name=None):
        """
        merge process vanadium to single bank data and optionally saved
        :except: RuntimeError() for being called too early
        :param save:
        :param to_archive:
        :param local_file_name:
        :return:
        """
        # check whether the data that has been smoothed
        if self._smoothed_ws_dict is None:
            raise RuntimeError('Vanadium run {0} has not been processed yet.'.format(self._runNumber))

        # merge
        one_bank_name = self._source_workspace_name + '_1bank'
        mantid_helper.sum_spectra(input_workspace=self._smoothed_ws_dict, output_workspace=one_bank_name)
        self._output_ws_name = one_bank_name

        # export
        if save:
            buffer_name = self._smoothed_ws_dict
            self._smoothed_ws_dict = self._output_ws_name
            status, message = self.save_vanadium_to_file(to_archive, local_file_name)
            self._smoothed_ws_dict = buffer_name
        else:
            status = True
            message = ''
        # END-IF

        return status, message

    def process_vanadium(self, peak_fwhm=None, peak_pos_tol=0.01, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth',
                         param_n=20, param_order=2, save=True, output_dir=None, write_to_gsas=True):
        """ Process vanadium run including strip vanadium peaks and smooth
        :param peak_fwhm:
        :param peak_pos_tol:
        :param background_type:
        :param is_high_background:
        :param smoother_filter_type:
        :param param_n:
        :param param_order:
        :param save:  flag to save the processed vanadium
        :param output_dir:
        :param write_to_gsas:
        :return:
        """
        import mantid_reduction
        # strip vanadium peaks
        if peak_fwhm is None:
            peak_fwhm = self._default_fwhm

        # strip peaks
        for bank_group_name in bank_group_dict.keys():
            self.strip_peaks(bank_group_index=bank_group_name,
                             peak_fwhm=peak_fwhm, pos_tolerance=peak_pos_tol,
                             background_type=background_type,
                             is_high_background=is_high_background)

        if write_to_gsas:
            mantid_reduction.VulcanBinningHelper.rebin_workspace()

        # smooth vanadium spectra
        for bank_group_name in bank_group_dict.keys():
            self.smooth_spectra(bank_group_index=None, smoother_type=smoother_filter_type,
                            param_n=param_n, param_order=param_order)
        assert isinstance(out_ws_2, str), 'Output must be a string'

        # save
        message = 'Vanadium {0} has peaks removed and is smoothed. '
        if output_dir is None:
            save_to_archive = True
        else:
            save_to_archive = False
        if save:
            status, sub_message = self.save_vanadium_to_file(to_archive=save_to_archive, out_file_name=output_dir)
            if status:
                message += 'Processed vanadium is saved to {0} or archive. '.format(output_dir)
            else:
                message += 'Processed vanadium failed to be written to {0} due to {1}.' \
                           ''.format(self._output_dir, sub_message)
        else:
            status = True

        return status, message

    def save_to_gsas(self, run_number, gsas_file_name):
        """

        :param run_number:
        :param gsas_file_name:
        :return:
        """
        # use run number to check against current one
        # TODO - 20181103 - Implement this method!
        # check out the 3 workspaces and merge them to save GSAS!

    def save_vanadium_to_file(self, vanadium_tuple=None,
                              to_archive=True, out_file_name=None):
        """
        save a processed vanadium (in workspace) to GSAS file
        Note: IPTS number must be specified for being written into GSAS file;
              run number must be specified for output file name
        :param vanadium_tuple: None or 3-tuple for vanadium workspace name/IPTS number/run number
        :param to_archive
        :param out_file_name: if not None, then output locally
        :return: tuple (boolean, str): status, error message
        """


        # check inputs
        if vanadium_tuple is None:
            # use the class variables of this instance
            assert self._iptsNumber is not None, 'IPTS number must be specified.'
            assert self._runNumber is not None, 'Run number must be specified.'
            assert self._smoothed_ws_dict is not None, 'Vanadium run {0} must have been processed.' \
                                                        ''.format(self._runNumber)

            workspace_name = self._smoothed_ws_dict
            ipts_number = self._iptsNumber
            run_number = self._runNumber

        else:
            raise RuntimeError('It is not supported to save vanadium with given workspace name.')
            # assert len(vanadium_tuple) == 3, 'A not-None vanadium tuple must have 3 elements but not {0}' \
            #                                  ''.format(len(vanadium_tuple))
            # workspace_name, ipts_number, run_number = vanadium_tuple
            # assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
            #                                      ''.format(ipts_number, type(ipts_number))
            # assert isinstance(run_number, int), 'Run number must be an integer but not a {1}.' \
            #                                     ''.format(run_number, type(run_number))
        # END-IF-ELSE

        # archive file name
        return_status = True
        error_msg = ''

        # determine the output file name with full path
        if to_archive:
            # write to archive's instrument specific calibration directory's instrument specific calibration directory
            base_name = '{0}-s.gda'.format(self._runNumber)
            van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
            if os.path.exists(van_dir) is False:
                return False, 'Vanadium directory {0} does not exist.'.format(van_dir)
            elif os.access(van_dir, os.W_OK) is False:
                return False, 'User has no privilege to write to directory {0}'.format(van_dir)

            archive_file_name = os.path.join(van_dir, base_name)
            if os.path.exists(archive_file_name) and os.access(archive_file_name, os.W_OK) is False:
                return False, 'Smoothed vanadium GSAS file {0} exists and user does not have privilege to over write.' \
                              ''.format(archive_file_name)
            out_file_name = archive_file_name

        elif out_file_name is not None:
            # file name re-define & get directory of the output file
            if os.path.isdir(out_file_name):
                # get the file name
                local_dir = out_file_name
                out_file_name = os.path.join(local_dir, '{0}-s.gda'.format(run_number))
            else:
                local_dir = os.path.dirname(out_file_name)
            # END0F
            if os.access(local_dir, os.W_OK):
                return False, 'User cannot write to directory {0}'.format(local_dir)
            elif os.path.exists(out_file_name) and os.access(out_file_name, os.W_OK):
                return False, 'Smoothed vanadium file {0} exists but user cannot over write.'.format(out_file_name)

        else:
            # neither to archive nor to local directory
            return False, 'User does not specify either to-archive nor a local directory'

        # write to GSAS file for VDRIVE
        bank_id_list = mantid_helper.get_workspace_information(workspace_name)

        default_bank_number = len(bank_id_list)

        # if to_archive and len(bank_id_list) <= 2:
        #     # regular
        #     # base_name = '{0}-s.gda'.format(self._runNumber)
        #     # van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
        #     # archive_file_name = os.path.join(van_dir, base_name)
        #     # if os.access(van_dir, os.W_OK):
        #     default_bank_number = 2
        #
        #     # mantid_helper.save_vulcan_gsas(workspace_name, out_file_name, ipts_number,
        #     #                                binning_reference_file='', gss_parm_file='')
        # elif
        #     # nED data: 3 banks
        #     default_bank_number = 3
        #     #
        #     #
        #     # gsas_writer = save_vulcan_gsas.SaveVulcanGSS(use_default_tof_ref=3)
        #     # gsas_writer =
        #     #
        #     #
        #     #
        #     # bin_dict = None  # use default
        #     # save_vulcan_gsas.save_vanadium_gss(self._smoothed_ws_dict, out_file_name, ipts_number, 'Vulcan.prm')
        # # END-IF-ELSE

        gsas_writer = save_vulcan_gsas.SaveVulcanGSS(use_default_tof_ref=default_bank_number)
        gsas_writer.save(diff_ws_name=workspace_name, gsas_file_name=out_file_name,
                         ipts_number=ipts_number, gsas_param_file_name=None,
                         van_ws_name=None)

        return return_status, error_msg

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
