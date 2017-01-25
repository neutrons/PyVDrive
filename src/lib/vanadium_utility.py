# Methods for vanadium utility methods
import os
import shutil
import mantid_helper


class VanadiumProcessingManager(object):
    """
    blabla
    """
    def __init__(self, parent):
        """

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
        assert isinstance(ipts_number, int), 'blabla'
        assert isinstance(run_number), 'blabla'

        # set
        self._rawMatrixWorkspace = workspace_name
        self._iptsNumber = ipts_number
        self._runNumber = run_number

        # reset processed workspaces
        self._peakStripWorkspace = None
        self._smoothedWorkspace = None

        return

    def process_vanadium(self,
                         peak_fwhm=7, peak_pos_tol=0.01, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth',
                         param_n=20, param_order=2):
        """
        process vanadium including peak striping and smooth
        :param ipts_number:
        :param run_number:
        :param workspace_name: only this MATTERS with real input for write out
        :return:
        """
        # strip vanadium peaks
        out_ws_1 = self.strip_peaks(workspace_name, peak_fwhm=peak_fwhm, pos_tolerance=peak_pos_tol,
                                    background_type=background_type,
                                    is_high_background=is_high_background)

        out_ws_2 = self.smooth_spectra(out_ws_1, workspace_index=None, smoother_type=smoother_filter_type,
                                       param_n=param_n, param_order=param_order)

        # save
        self.save_vanadium_to_file(ipts_number, run_number, out_ws_2, to_archive=True,
                                   out_file_name=self._localOutputDirectory)

        return

    @staticmethod
    def save_vanadium_to_file(ipts_number, run_number, vanadium_workspace, to_archive=True,
                              out_file_name=None):
        """
        save a processed vanadium (in workspace) to GSAS file
        :param ipts_number:
        :param run_number:
        :param vanadium_workspace:
        :param to_archive
        :param out_file_name: if not None, then output locally
        :return:
        """
        # TODO/ISSUE/59/ - check inputs

        # append output directory
        base_name = None
        archive_file_name = None
        local_file_name = None

        if out_file_name is None:
            base_name = '{0}-s.gda'.format(run_number)
        else:
            base_name = os.path.basename(local_file_name)

        # archive file name
        return_status = True
        error_msg = ''

        # write to archive
        if to_archive:
            base_name = '{0}-s.gda'.format(run_number)
            van_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
            archive_file_name = os.path.join(base_name, van_dir)
            if os.access(van_dir, os.W_OK):
                mantid_helper.save_vulcan_gsas(vanadium_workspace, archive_file_name, ipts_number,
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
                out_file_name = os.path.join(local_dir, '{0}-s.gda'.format(run_number))
            else:
                local_dir = os.path.dirname(out_file_name)
                if len(local_dir) == 0:
                    local_dir = os.getcwd()
            # END-IF

            # check whether the directory is writable
            if os.access(local_dir, os.W_OK):
                if archive_file_name is None:
                    mantid_helper.save_vulcan_gsas(vanadium_workspace, out_file_name, ipts_number,
                                                   binning_reference_file='', gss_parm_file='')
                else:
                    shutil.copy(archive_file_name, out_file_name)
            else:
                return_status = False
                error_msg += 'Failed to write {0} to local directory due to permission error.'.format(archive_file_name)
            # END-IF

        return return_status, error_msg

    @staticmethod
    def smooth_spectra(workspace_name, workspace_index, smoother_type, param_n, param_order):
        """
        smooth focused diffraction spectra
        :param workspace_name:
        :param workspace_index:
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return: output workspace name
        """
        output_workspace_name = mantid_helper.smooth_vanadium(input_workspace=workspace_name,
                                                              smooth_filter=smoother_type,
                                                              workspace_index=workspace_index,
                                                              param_n=param_n,
                                                              param_order=param_order)

        return output_workspace_name


    def strip_peaks(self, workspace_name, peak_fwhm, pos_tolerance,
                    background_type, is_high_background):
        """
        blabla
        :param workspace_name:
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        # FIXME - Do we really need this method?
        output_ws_name = mantid_helper.strip_vanadium_peaks(input_workspace=workspace_name, fwhm=peak_fwhm,
                                                            peak_pos_tol=pos_tolerance,
                                                            background_type=background_type,
                                                            is_high_background=is_high_background)

        return output_ws_name