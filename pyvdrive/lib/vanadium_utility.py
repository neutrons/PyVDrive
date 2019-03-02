# Methods for processing vanadiums
import os
import mantid_helper
import datatypeutility
import save_vulcan_gsas
import shutil


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

        # state flag
        self._is_setup = False   # flag such that a parent workspace (to smooth from) has been set up
        self._output_ws_name = None  # workspace from merged smoothed/vanadium-peaks-striped workspace
        # NOTE: output workspace shall be of the same range, number of spectra and instrument geometry as input

        # by default
        self._output_dir = os.getcwd()

        # peak striping
        self._default_fwhm_dict = {1: 7, 2: 7, 3: 12}
        # smoothing
        self._is_shift_case = False
        self._smooth_param_shift_dict = {'n': dict(), 'order': dict()}
        self._smooth_param_dict = {'n': dict(), 'order': dict()}
        for bank_id in range(1, 4):
            self._smooth_param_dict['n'][bank_id] = 20
            self._smooth_param_shift_dict['n'][bank_id] = 20
            self._smooth_param_dict['order'][bank_id] = 2
            self._smooth_param_shift_dict['order'][bank_id] = 2
        # TODO - TONIGHT - NEED TO FILL THE RIGHT VALUES

        # # final output binning
        # self._calibration_manager = calibration_manager
        # self._tof_bin_dict = dict()

        # these are updated class variables
        self._van_workspace_name = None   # input vanadium workspace (focused)
        self._van_workspace_name_tof = None
        self._sample_log_ws_name = None   # sample log workspace's name
        self._ipts_number = None
        self._van_run_number = None
        self._output_gsas_name = None

        # single spectrum workspace for the internal steps
        self._source_single_bank_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._striped_peaks_ws_dict = dict()  # [bank id (1, 2, 3)] = ws name
        self._smoothed_ws_dict = dict()  # [bank id (1, 2, 3)] = ws names

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
        self._is_shift_case = True

        return

    def get_default_smooth_n(self, smoother_type, bank_id):
        return self._smooth_param_dict['n'][bank_id]

    def get_default_smooth_order(self, smoother_type, bank_id):
        return self._smooth_param_dict['order'][bank_id]

    def get_peak_striped_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped
        :return:
        """
        return self._striped_peaks_ws_dict

    def get_peak_striped_data(self, bank_id):
        """
        Get the data (x, y) for spectrum with peaks stripped
        :param bank_id:
        :return:
        """
        if bank_id in self._striped_peaks_ws_dict:
            ws_name = self._striped_peaks_ws_dict[bank_id]
        else:
            ws_name = None
        if ws_name is None:
            raise RuntimeError('Bank {} does not have peak striped'.format(bank_id))

        workspace = mantid_helper.retrieve_workspace(ws_name)

        return workspace.readX(0), workspace.readY(0)

    def get_peak_smoothed_data(self, bank_id):
        """
        Get the data (x, y) for spectrum smoothed
        :param bank_id:
        :return:
        """
        if bank_id in self._smoothed_ws_dict:
            ws_name = self._smoothed_ws_dict[bank_id]
        else:
            ws_name = None
        if ws_name is None:
            raise RuntimeError('Bank {} is not smoothed'.format(bank_id))

        workspace = mantid_helper.retrieve_workspace(ws_name)

        return workspace.readX(0), workspace.readY(0)

    def get_raw_data(self, bank_id, unit):
        """
        Get raw data
        :param bank_id:
        :param unit:
        :return:
        """
        if self._van_workspace_name is None:
            raise RuntimeError('Vanadium workspace has not been set up yet!')

        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 99))
        datatypeutility.check_string_variable('Unit', unit, ['TOF', 'dSpacing'])

        if unit == 'TOF':
            if self._van_workspace_name_tof is None:
                self._van_workspace_name_tof = self._van_workspace_name + '_tof'
                mantid_helper.mtd_convert_units(self._van_workspace_name, 'TOF', self._van_workspace_name_tof)
            workspace = mantid_helper.retrieve_workspace(self._van_workspace_name_tof)
        else:
            workspace = mantid_helper.retrieve_workspace(self._van_workspace_name)

        return workspace[bank_id-1].readX(0), workspace[bank_id-1].readY(0)

    def get_raw_vanadium(self):
        """ get the raw vanadium spectra dictionary
        :return:
        """
        return self._source_single_bank_ws_dict

    def get_smoothed_vanadium(self):
        """
        get the vanadium workspace (name) that has peaks striped and smoothed
        :return:
        """
        return self._smoothed_ws_dict

    def init_session(self, workspace_name, ipts_number, van_run_number, out_gsas_name,
                     sample_log_ws_name):
        """
        Initialize vanadium processing session
        :param workspace_name:
        :param ipts_number:
        :param van_run_number:
        :param out_gsas_name:
        :param sample_log_ws_name: required for proton charge
        :return:
        """
        datatypeutility.check_string_variable('Workspace name', workspace_name)
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 99999))
        datatypeutility.check_int_variable('Vanadium run number', van_run_number, (1, 999999))
        datatypeutility.check_file_name(out_gsas_name, False, True, False, 'Output GSAS file name')
        datatypeutility.check_string_variable('Sample log workspace name', sample_log_ws_name)

        workspace = mantid_helper.retrieve_workspace(workspace_name)
        if workspace.id() == 'WorkspaceGroup':
            pass
        else:
            # create dictionary and etc
            raise NotImplementedError('Need to implement single workspace case to extract spectra')

        self._van_workspace_name = workspace_name

        self._ipts_number = ipts_number
        self._van_run_number = van_run_number
        self._output_gsas_name = out_gsas_name

        # parameter set up
        self._is_shift_case = False

        # convert to point data as a request
        mantid_helper.convert_to_point_data(self._van_workspace_name)
        mantid_helper.mtd_convert_units(self._van_workspace_name, 'dSpacig')

        self._sample_log_ws_name = sample_log_ws_name

        return

    def process_vanadium(self, peak_pos_tol=0.1, background_type='Quadratic',
                         is_high_background=True, smoother_filter_type='Butterworth'):
        """ Process vanadium run including strip vanadium peaks and smooth
        This is a high-level call to do all the work with good setup in one action
        :param peak_pos_tol:
        :param background_type:
        :param is_high_background:
        :param smoother_filter_type:
        :return:
        """
        try:
            raw_van_ws = mantid_helper.retrieve_workspace(self._van_workspace_name)
        except RuntimeError as run_err:
            raise False, 'Unable to process vanadium due to {}'.format(run_err)

        for ws_index in range(mantid_helper.get_number_spectra(raw_van_ws)):
            # strip vanadium peaks
            bank_id = ws_index + 1
            self.strip_v_peaks(bank_id=ws_index+1, peak_fwhm=self._default_fwhm_dict[bank_id],
                               pos_tolerance=peak_pos_tol,
                               background_type=background_type,
                               is_high_background=is_high_background)
            # smooth
            if self._is_shift_case:
                param_n = self._smooth_param_shift_dict['n'][bank_id]
                param_order = self._smooth_param_shift_dict['order'][bank_id]
            else:
                param_n = self._smooth_param_dict['n'][bank_id]
                param_order = self._smooth_param_dict['order'][bank_id]

            self.smooth_v_spectrum(bank_id=bank_id, smoother_filter_type=smoother_filter_type,
                                   param_n=param_n, param_order=param_order)
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

    def save_vanadium_to_file(self):
        """
        save a processed vanadium (in workspace) to GSAS file
        Note: IPTS number must be specified for being written into GSAS file;
              run number must be specified for output file name
        :return: tuple (boolean, str): status, error message
        """
        bank_id_list = sorted(self._smoothed_ws_dict.keys())
        # group workspaces
        input_ws_names = ''
        for bank_id in bank_id_list:
            input_ws_names += '{},'.format(self._smoothed_ws_dict[bank_id])
        input_ws_names = input_ws_names[:-1]
        processed_vanadium_name = '{}_processed'.format(self._van_workspace_name)
        mantid_helper.group_workspaces(input_ws_names, processed_vanadium_name)

        print ('[DB...BAT] OUTPUT GSAS File: {}'.format(self._output_gsas_name))

        gsas_writer = save_vulcan_gsas.SaveVulcanGSS()
        # TODO - TONIGHT 11 - convert_to_vdrive_bins shall be considered if source file is from a high resolution
        # TODO - cont.      - ProcessedNeXus file: It shall call save() instead
        gsas_writer.save_vanadium(diff_ws_name=processed_vanadium_name, gsas_file_name=self._output_gsas_name,
                                  ipts_number=self._ipts_number, van_run_number=self._van_run_number,
                                  sample_log_ws_name=self._sample_log_ws_name)

        #  copy file to 2nd location
        try:
            gsas_copy = '/SNS/VULCAN/IPTS-{}/shared/Instrument/{}'.format(self._ipts_number,
                                                                      os.path.basename(self._output_gsas_name))
            shutil.copyfile(self._output_gsas_name, gsas_copy)
        except (IOError, OSError) as io_error:
            raise RuntimeError('Unable to save to {} due to {}'.format(gsas_copy, io_error))

        return self._output_gsas_name

    def smooth_v_spectrum(self, bank_id, smoother_filter_type, param_n, param_order, ws_name=None):
        """
        smooth vanadium peaks
        :param bank_id:
        :param smoother_filter_type:
        :param param_n:
        :param param_order:
        :param ws_name:
        :return:
        """
        # check inputs:
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 99))
        datatypeutility.check_string_variable('Smoothing filter type', smoother_filter_type,
                                              ['Zeroing', 'Butterworth'])
        datatypeutility.check_int_variable('Smoothing parameter "n"', param_n, (1, 100))
        datatypeutility.check_int_variable('Smoothing order', param_order, (1, 100))

        # get workspace
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

    def strip_v_peaks(self, bank_id, peak_fwhm, pos_tolerance, background_type, is_high_background):
        """ Strip vanadium peaks
        Note: result is stored in _striped_peaks_ws_dict
        :param bank_id:
        :param peak_fwhm:
        :param pos_tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 99))
        datatypeutility.check_int_variable('FWHM (number of pixels)', peak_fwhm, (1, 100))
        datatypeutility.check_float_variable('Peak position tolerance', pos_tolerance, (0, None))

        raw_van_ws = mantid_helper.retrieve_workspace(self._van_workspace_name)
        if mantid_helper.is_workspace_group(self._van_workspace_name):
            input_ws_name = raw_van_ws[bank_id-1].name()
            bank_list = [1]
        else:
            input_ws_name = self._van_workspace_name
            bank_list = [bank_id]

        output_ws_name = input_ws_name + '_NoPeak'
        output_ws_dict = mantid_helper.strip_vanadium_peaks(input_ws_name=input_ws_name,
                                                            output_ws_name=output_ws_name,
                                                            bank_list=bank_list,
                                                            binning_parameter=None,
                                                            fwhm=peak_fwhm,  # PEAK FWHM must be integer (legacy)
                                                            peak_pos_tol=pos_tolerance,
                                                            background_type=background_type,
                                                            is_high_background=is_high_background)
        self._striped_peaks_ws_dict[bank_id] = output_ws_name

        return output_ws_name

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
