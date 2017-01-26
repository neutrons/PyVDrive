# Methods for vanadium utility methods
import os
import shutil
import mantid_helper


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
        self._peakStripWorkspace = None
        self._smoothedWorkspace = None

        self._iptsNumber = None
        self._runNumber = None

        return

    def get_peak_striped_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped
        :return:
        """
        return self._peakStripWorkspace

    def get_smoothed_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped and smoothed
        :return:
        """
        return self._smoothedWorkspace

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
        self._peakStripWorkspace = None
        self._smoothedWorkspace = None

        return

    def process_vanadium(self, peak_fwhm=7, peak_pos_tol=0.01, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth',
                         param_n=20, param_order=2):
        """
        Process vanadium run including strip vanadium peaks and smooth
        :param peak_fwhm:
        :param peak_pos_tol:
        :param background_type:
        :param is_high_background:
        :param smoother_filter_type:
        :param param_n:
        :param param_order:
        :return:
        """
        # strip vanadium peaks
        out_ws_1 = self.strip_peaks(peak_fwhm=peak_fwhm, pos_tolerance=peak_pos_tol,
                                    background_type=background_type,
                                    is_high_background=is_high_background)
        assert isinstance(out_ws_1, str), 'Output must be a string'

        # smooth vanadium spectra
        out_ws_2 = self.smooth_spectra(workspace_index=None, smoother_type=smoother_filter_type,
                                       param_n=param_n, param_order=param_order)
        assert isinstance(out_ws_2, str), 'Output must be a string'

        # save
        self.save_vanadium_to_file(to_archive=True, out_file_name=self._localOutputDirectory)

        return

    def save_vanadium_to_file(self, to_archive=True, out_file_name=None):
        """
        save a processed vanadium (in workspace) to GSAS file
        Note: IPTS number must be specified for being written into GSAS file;
              run number must be specified for output file name
        :param to_archive
        :param out_file_name: if not None, then output locally
        :return: tuple (boolean, str): status, error message
        """
        # check inputs
        assert self._iptsNumber is not None, 'IPTS number must be specified.'
        assert self._runNumber is not None, 'Run number must be specified.'
        assert self._smoothedWorkspace is not None, 'Vanadium run {0} must have been processed.' \
                                                    ''.format(self._runNumber)

        # archive file name
        return_status = True
        error_msg = ''

        # write to archive
        if to_archive:
            base_name = '{0}-s.gda'.format(self._runNumber)
            van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
            archive_file_name = os.path.join(base_name, van_dir)
            if os.access(van_dir, os.W_OK):
                mantid_helper.save_vulcan_gsas(self._smoothedWorkspace, archive_file_name, self._iptsNumber,
                                               binning_reference_file='', gss_parm_file='')
            else:
                archive_file_name = None
                return_status = False
                error_msg += 'Failed to write {0} to archive due to permission error.\n'.format(archive_file_name)
        else:
            archive_file_name = None

        if out_file_name:
            # file name re-define & get directory of the output file
            if os.path.isdir(out_file_name):
                local_dir = out_file_name
                out_file_name = os.path.join(local_dir, '{0}-s.gda'.format(self._runNumber))
            else:
                local_dir = os.path.dirname(out_file_name)
                if len(local_dir) == 0:
                    local_dir = os.getcwd()
            # END-IF

            # check whether the directory is writable
            if os.access(local_dir, os.W_OK):
                if archive_file_name is None:
                    mantid_helper.save_vulcan_gsas(self._smoothedWorkspace, out_file_name, self._iptsNumber,
                                                   binning_reference_file='', gss_parm_file='')
                else:
                    shutil.copy(archive_file_name, out_file_name)
            else:
                return_status = False
                error_msg += 'Failed to write {0} to local directory due to permission error.'.format(archive_file_name)
            # END-IF

        return return_status, error_msg

    def smooth_spectra(self, workspace_index, smoother_type, param_n, param_order, workspace_name=None):
        """
        smooth focused diffraction spectra
        :param workspace_name: if it is not None then the method is called as a stic method
        :param workspace_index:
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return: output workspace name
        """
        # about workspace_name
        if workspace_name is None:
            # using previously setup raw MatrixWorkspace
            if self._peakStripWorkspace is None:
                raise RuntimeError('{0} is not set up with raw MatrixWorkspace yet.'.format(self.__class__.__name__))
            input_ws_name = self._peakStripWorkspace
        else:
            # using user specified workspace
            # check whether the workspace exists
            assert isinstance(workspace_name, str), 'User input workspace name {0} must be a string but not of type ' \
                                                    '{1}.'.format(workspace_name, type(workspace_name))
            if not mantid_helper.workspace_does_exist(workspace_name):
                raise RuntimeError('User input workspace {0} does not exist in ADS.'.format(workspace_name))

            input_ws_name = workspace_name
        # END-IF-ELSE

        # smooth vanadium spectra
        output_workspace_name = mantid_helper.smooth_vanadium(input_workspace=input_ws_name,
                                                              smooth_filter=smoother_type,
                                                              workspace_index=workspace_index,
                                                              param_n=param_n,
                                                              param_order=param_order)

        # register the output workspace if this method is not called as a static
        self._smoothedWorkspace = output_workspace_name

        return output_workspace_name

    def strip_peaks(self, peak_fwhm, pos_tolerance, background_type, is_high_background, workspace_name=None):
        """
        strip vanadium peaks
        :param workspace_name: if specified, then this method will be used as a static method
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
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

        output_ws_name = mantid_helper.strip_vanadium_peaks(input_workspace=input_ws_name,
                                                            fwhm=peak_fwhm,
                                                            peak_pos_tol=pos_tolerance,
                                                            background_type=background_type,
                                                            is_high_background=is_high_background)

        # register the output workspace if it is not called as a static
        if output_ws_name is not None:
            self._peakStripWorkspace = output_ws_name

        return output_ws_name
