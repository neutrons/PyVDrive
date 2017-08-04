# Methods for vanadium utility methods
import os
import shutil
import mantid_helper
from reduce_VULCAN import align_bins


class VanadiumProcessingManager(object):
    """
    Controller of the workflow to process vanadium data for calibration purpose
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        self._myParent = parent

        self._localOutputDirectory = os.getcwd()

        self._rawMatrixWorkspace = None
        self._peakStripedWorkspaceDict = dict()
        self._smoothedWorkspaceDict = None
        self._oneBankWorkspace = None

        self._iptsNumber = None
        self._runNumber = None

        self._defaultFWHM = 7

        return

    def apply_shift(self):
        """
        apply shift-of-wavelength to the vanadium to process
        :return:
        """
        self._defaultFWHM = 2

        return

    def get_peak_striped_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped
        :return:
        """
        return self._peakStripedWorkspaceDict

    def get_smoothed_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped and smoothed
        :return:
        """
        return self._smoothedWorkspaceDict

    def init_session(self, workspace_name, ipts_number, run_number):
        """
        initialize a new session to process vanadium
        :param workspace_name:
        :param ipts_number:
        :param run_number:
        :return:
        """
        # check inputs
        if not mantid_helper.workspace_does_exist(workspace_name):
            raise RuntimeError('Raw matrix workspace {0} does not exist.'.format(workspace_name))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not a {1}.' \
                                            ''.format(run_number, type(run_number))

        # set
        self._rawMatrixWorkspace = workspace_name
        self._iptsNumber = ipts_number
        self._runNumber = run_number

        # reset processed workspaces
        self._peakStripedWorkspaceDict.clear()
        self._smoothedWorkspaceDict = None
        self._oneBankWorkspace = None

        # default FWHM
        self._defaultFWHM = 7  # non-shift case

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
        if self._smoothedWorkspaceDict is None:
            raise RuntimeError('Vanadium run {0} has not been processed yet.'.format(self._runNumber))

        # merge
        one_bank_name = self._rawMatrixWorkspace + '_1bank'
        mantid_helper.sum_spectra(input_workspace=self._smoothedWorkspaceDict, output_workspace=one_bank_name)
        self._oneBankWorkspace = one_bank_name

        # export
        if save:
            buffer_name = self._smoothedWorkspaceDict
            self._smoothedWorkspaceDict = self._oneBankWorkspace
            status, message = self.save_vanadium_to_file(to_archive, local_file_name)
            self._smoothedWorkspaceDict = buffer_name
        else:
            status = True
            message = ''
        # END-IF

        return status, message

    def process_vanadium(self, peak_fwhm=None, peak_pos_tol=0.01, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth',
                         param_n=20, param_order=2, save=True, output_dir=None):
        """
        Process vanadium run including strip vanadium peaks and smooth
        :param peak_fwhm:
        :param peak_pos_tol:
        :param background_type:
        :param is_high_background:
        :param smoother_filter_type:
        :param param_n:
        :param param_order:
        :param save: flag to save the processed vanadium
        :return:
        """
        # strip vanadium peaks
        if peak_fwhm is None:
            peak_fwhm = self._defaultFWHM
        out_ws_1 = self.strip_peaks(peak_fwhm=peak_fwhm, pos_tolerance=peak_pos_tol,
                                    background_type=background_type,
                                    is_high_background=is_high_background)
        assert isinstance(out_ws_1, str), 'Output must be a string'

        # smooth vanadium spectra
        out_ws_2 = self.smooth_spectra(bank_id_list=None, smoother_type=smoother_filter_type,
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
                           ''.format(self._localOutputDirectory, sub_message)
        else:
            status = True

        return status, message

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
            assert self._smoothedWorkspaceDict is not None, 'Vanadium run {0} must have been processed.' \
                                                        ''.format(self._runNumber)

            workspace_name = self._smoothedWorkspaceDict
            ipts_number = self._iptsNumber
            run_number = self._runNumber

        else:
            assert len(vanadium_tuple) == 3, 'A not-None vanadium tuple must have 3 elements but not {0}' \
                                             ''.format(len(vanadium_tuple))
            workspace_name, ipts_number, run_number = vanadium_tuple
            assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
                                                 ''.format(ipts_number, type(ipts_number))
            assert isinstance(run_number, int), 'Run number must be an integer but not a {1}.' \
                                                ''.format(run_number, type(run_number))
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
        if to_archive and len(bank_id_list) <= 2:
            # regular
            # base_name = '{0}-s.gda'.format(self._runNumber)
            # van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
            # archive_file_name = os.path.join(van_dir, base_name)
            # if os.access(van_dir, os.W_OK):
            mantid_helper.save_vulcan_gsas(workspace_name, out_file_name, ipts_number,
                                           binning_reference_file='', gss_parm_file='')
        else:
            # nED data: 3 banks
            import save_vulcan_gsas
            bin_dict = None  # use default
            save_vulcan_gsas.save_vulcan_gss(workspace_name, bin_dict, out_file_name, ipts_number, 'Vulcan.prm')
        # END-IF-ELSE

        return return_status, error_msg

    def smooth_spectra(self, bank_id_list, smoother_type, param_n, param_order, require_to_align=False):
        """
        smooth focused diffraction spectra
        :param workspace_name: if it is not None then the method is called as a static method
        :param bank_id_list:
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return: output workspace name
        """
        if bank_id_list is None:
            bank_id_list = self._peakStripedWorkspaceDict.keys()

        processed_input_dict = dict()
        for bank_id in bank_id_list:
            # get workspace with peak striped
            if bank_id not in self._peakStripedWorkspaceDict:
                raise RuntimeError('Bank {0} has not been striped peaks.'.format(bank_id))
            input_ws_name = self._peakStripedWorkspaceDict[bank_id]

            # skip if same workspace has been processed
            if input_ws_name in processed_input_dict:
                self._smoothedWorkspaceDict[bank_id] = processed_input_dict[input_ws_name]
                continue

            # smooth vanadium spectra
            output_workspace_name = mantid_helper.smooth_vanadium(input_workspace=input_ws_name,
                                                                  smooth_filter=smoother_type,
                                                                  workspace_index=bank_id_list,
                                                                  param_n=param_n,
                                                                  param_order=param_order,
                                                                  push_to_positive=True)
            self._smoothedWorkspaceDict[bank_id] = output_workspace_name
            processed_input_dict[input_ws_name] = output_workspace_name
        # END-FOR

        # check the workspace whether it can be aligned
        if require_to_align:
            output_workspace_name = self._smoothedWorkspaceDict[1]
            alignable, diff_reason = mantid_helper.check_bins_can_align(output_workspace_name, self._myParent.vdrive_bin_template)
            if alignable:
                # align bins
                align_bins(output_workspace_name, self._myParent.vdrive_bin_template)
        # END-IF (align bins)

        return self._smoothedWorkspaceDict

    def strip_peaks(self, peak_fwhm, pos_tolerance, background_type, is_high_background, workspace_name=None,
                    bank_list=None):
        """
        strip vanadium peaks
        :param workspace_name: if specified, then this method will be used as a static method
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
        :param bank_list:
        :return:
        """
        # about workspace_name
        if workspace_name is None:
            # using previously setup raw MatrixWorkspace
            if self._rawMatrixWorkspace is None:
                raise RuntimeError('{0} is not set up with raw MatrixWorkspace yet.'.format(self.__class__.__name__))
            input_ws_name = self._rawMatrixWorkspace
        else:
            # using user specified workspace
            # check whether the workspace exists
            assert isinstance(workspace_name, str), 'User input workspace name {0} must be a string but not of type ' \
                                                    '{1}.'.format(workspace_name, type(workspace_name))
            if not mantid_helper.workspace_does_exist(workspace_name):
                raise RuntimeError('User input workspace {0} does not exist in ADS.'.format(workspace_name))

            input_ws_name = workspace_name
        # END-IF-ELSE

        # output workspace dictionary
        output_ws_dict = dict()

        # identify output workspace type
        raw_ws = mantid_helper.retrieve_workspace(input_ws_name)
        if raw_ws.__class__.__name__.count('EventWorkspace') == 1:
            # event workspace. possible to rebin
            if 1 in bank_list or 2 in bank_list:
                # east/west bank
                binning_parameter = '5000., -0.001, 70000.'
                output_ws_name_ew = mantid_helper.strip_vanadium_peaks(input_ws_name=input_ws_name,
                                                                       bank_list=bank_list,
                                                                       binning_parameter=binning_parameter,
                                                                       fwhm=peak_fwhm,
                                                                       peak_pos_tol=pos_tolerance,
                                                                       background_type=background_type,
                                                                       is_high_background=is_high_background)
                for bank_id in [1, 2]:
                    if bank_id in bank_list:
                        output_ws_dict[bank_id] = output_ws_name_ew
            if 3 in bank_list:
                # high angle bank
                binning_parameter = '5000., -0.001, 70000.'
                output_ws_name_high = mantid_helper.strip_vanadium_peaks(input_ws_name=input_ws_name,
                                                                         bank_list=bank_list,
                                                                         binning_parameter=binning_parameter,
                                                                         fwhm=peak_fwhm,
                                                                         peak_pos_tol=pos_tolerance,
                                                                         background_type=background_type,
                                                                         is_high_background=is_high_background)
                output_ws_dict[3] = output_ws_name_high

        else:
            # regular one!
            output_ws_name = mantid_helper.strip_vanadium_peaks(input_workspace=input_ws_name,
                                                                bank_list=bank_list,
                                                                binning_parameter=None,
                                                                fwhm=peak_fwhm,
                                                                peak_pos_tol=pos_tolerance,
                                                                background_type=background_type,
                                                                is_high_background=is_high_background)
            for bank_id in bank_list:
                output_ws_dict[bank_id] = output_ws_name
        # END-IF-ELSE

        # register the output workspace if it is not called as a static
        for bank_id in output_ws_dict:
            self._peakStripedWorkspaceDict[bank_id] = output_ws_dict[bank_id]

        return output_ws_dict

    def undo_peak_strip(self):
        """
        undo peak strip
        :return:
        """
        self._peakStripedWorkspaceDict.clear()

        return

    def undo_smooth(self):
        """
        undo spectra smoothing
        :return:
        """
        self._smoothedWorkspaceDict = None

        return
