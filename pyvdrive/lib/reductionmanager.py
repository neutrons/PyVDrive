################################################################################
# Manage the reduced VULCAN runs
################################################################################
import os
import reduce_VULCAN
import mantid_helper
import chop_utility
import reduce_adv_chop
import mantid_reduction
import datatypeutility
import h5py
import numpy
import platform
import time

EVENT_WORKSPACE_ID = "EventWorkspace"


class CalibrationManager(object):
    """
    A container and manager for calibration files loaded, number of banks of groupings and etc
    """
    def __init__(self):
        """
        initialization
        """
        # important dates
        self._ned_date = '2017-06-01'  # string only

        self._calibration_dict = None

        # binning
        self._vdrive_bin_ref_file_dict = None
        self._vdrive_binning_ref_dict = dict()   # [date, num_banks] ...
        self._default_tof_bins_dict = None   # [cal_date, num_banks]

        self._loaded_calibration_file_dict = dict()
        self._focus_instrument_dict = dict()

        # set up
        self._init_vulcan_calibration_files()
        self._init_vdrive_binning_refs()
        self._init_focused_instruments()
        self._init_default_tof_bins()

        return

    def _init_default_tof_bins(self):
        """ initialize default TOF bins
        :return:
        """
        self._default_tof_bins_dict = dict()

        self.get_default_binning_reference(self._ned_date, 3)

        return

    def _init_focused_instruments(self):
        """
        set up the dictionary for the instrument geometry after focusing
        each detector (virtual) will have 3 value as L2, polar (2theta) and azimuthal (phi)
        and the angles are in unit as degree
        :return:
        """
        self._focus_instrument_dict['L1'] = 43.753999999999998

        # L2, Polar and Azimuthal
        self._focus_instrument_dict['L2'] = dict()
        self._focus_instrument_dict['Polar'] = dict()
        self._focus_instrument_dict['Azimuthal'] = dict()
        self._focus_instrument_dict['SpectrumIDs'] = dict()

        # east_bank = [2.0, 90., 0.]
        # west_bank = [2.0, -90., 0.]
        # high_angle_bank = [2.0, 155., 0.]

        # 2 bank
        self._focus_instrument_dict['L2'][2] = [2., 2.]
        self._focus_instrument_dict['Polar'][2] = [-90.,  90]
        self._focus_instrument_dict['Azimuthal'][2] = [0., 0.]
        self._focus_instrument_dict['SpectrumIDs'][2] = [1, 2]

        # 3 bank
        self._focus_instrument_dict['L2'][3] = [2., 2., 2.]
        self._focus_instrument_dict['Polar'][3] = [-90, 90., 155]
        self._focus_instrument_dict['Azimuthal'][3] = [0., 0, 0.]
        self._focus_instrument_dict['SpectrumIDs'][3] = [1, 2, 3]

        # 7 bank
        self._focus_instrument_dict['L2'][7] = None  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][7] = None
        self._focus_instrument_dict['Azimuthal'][7] = None
        self._focus_instrument_dict['SpectrumIDs'][7] = range(1, 8)

        # 27 banks
        self._focus_instrument_dict['L2'][27] = None  # [2., 2., 2.]
        self._focus_instrument_dict['Polar'][27] = None
        self._focus_instrument_dict['Azimuthal'][27] = None
        self._focus_instrument_dict['SpectrumIDs'][27] = range(1, 28)

        return

    def _init_vulcan_calibration_files(self):
        """
        generate a dictionary for vulcan's hard coded calibration files
        :return:
        """
        base_calib_dir = '/SNS/VULCAN/shared/CALIBRATION'

        # hard coded list of available calibration file names
        pre_ned_setup = {3: '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vulcan_foc_all_2bank_11p.cal'}

        ned_2017_setup = {3: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                          7: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_7bank.h5',
                          27: '/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12_27bank.h5'}

        ned_2018_setup = {3: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5'),
                          7: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_7bank.h5'),
                          27: os.path.join(base_calib_dir, '2018_6_1_CAL/VULCAN_calibrate_2018_06_01_27bank.h5')}

        self._calibration_dict = dict()
        self._calibration_dict['2010-01-01'] = pre_ned_setup
        self._calibration_dict['2017-06-01'] = ned_2017_setup
        self._calibration_dict['2018-05-31'] = ned_2018_setup

        return

    def _init_vdrive_binning_refs(self):
        """ initialize binning references
        :return:
        """
        base_calib_dir = '/SNS/VULCAN/shared/CALIBRATION'

        # hard coded list of available calibration file names
        pre_ned_setup = '/SNS/VULCAN/shared/CALIBRATION/2011_1_7_CAL/vdrive_log_bin.dat'

        ned_2017_setup = '/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5'

        ned_2018_setup = os.path.join(base_calib_dir, '2018_6_1_CAL/vdrive_3bank_bin.h5')

        self._vdrive_bin_ref_file_dict = dict()
        self._vdrive_bin_ref_file_dict['2010-01-01'] = pre_ned_setup
        self._vdrive_bin_ref_file_dict['2017-06-01'] = ned_2017_setup
        self._vdrive_bin_ref_file_dict['2018-05-31'] = ned_2018_setup

        # parse the files and create bins: better to choose the latest and with 3 banks
        dates_list = sorted(self._vdrive_bin_ref_file_dict.keys())
        cal_date = dates_list[-1]

        self._vdrive_binning_ref_dict[cal_date, 3] = \
            self.create_idl_bins(num_banks=3, h5_bin_file_name=self._vdrive_bin_ref_file_dict[cal_date])

        return

    @staticmethod
    def create_idl_bins(num_banks, h5_bin_file_name):
        """
        create a Mantid to VDRIVE-IDL mapping binning
        :param num_banks:
        :param h5_bin_file_name:
        :return:
        """
        def process_bins_to_binning_params(bins_vector):
            """
            convert a list of bin boundaries to x1, dx, x2, dx, ... style
            :param bins_vector:
            :return:
            """
            assert isinstance(bins_vector, numpy.ndarray)
            assert len(bins_vector.shape) == 1

            delta_tof_vec = bins_vector[1:] - bins_vector[:-1]

            bin_param = numpy.empty((bins_vector.size + delta_tof_vec.size), dtype=bins_vector.dtype)
            bin_param[0::2] = bins_vector
            bin_param[1::2] = delta_tof_vec

            # extrapolate_last_bin
            delta_bin = (bins_vector[-1] - bins_vector[-2]) / bins_vector[-2]
            next_x = bins_vector[-1] * (1 + delta_bin)

            # append last value for both east/west bin and high angle bin
            numpy.append(bin_param, delta_bin)
            numpy.append(bin_param, next_x)

            return bin_param

        # use explicitly defined bins and thus matrix workspace is required
        # import h5 file
        # load vdrive bin file to 2 different workspaces
        bin_file = h5py.File(h5_bin_file_name, 'r')
        west_east_bins = bin_file['west_east_bank'][:]
        high_angle_bins = bin_file['high_angle_bank'][:]
        bin_file.close()

        # convert a list of bin boundaries to x1, dx, x2, dx, ... style
        west_east_bin_params = process_bins_to_binning_params(west_east_bins)
        high_angle_bin_params = process_bins_to_binning_params(high_angle_bins)

        binning_parameter_dict = dict()
        if num_banks == 3:
            # west(1), east(1), high(1)
            # west(1), east(1), high(1)
            for bank_id in range(1, 3):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[3] = high_angle_bin_params
        elif num_banks == 7:
            # west (3), east (3), high (1)
            for bank_id in range(1, 7):
                binning_parameter_dict[bank_id] = west_east_bin_params
            binning_parameter_dict[7] = high_angle_bin_params
        elif num_banks == 27:
            # west (9), east (9), high (9)
            for bank_id in range(1, 19):
                binning_parameter_dict[bank_id] = west_east_bin_params
            for bank_id in range(19, 28):
                binning_parameter_dict[bank_id] = high_angle_bin_params
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
        # END-IF-ELSE

        return binning_parameter_dict

    @staticmethod
    def create_nature_bins(num_banks, east_west_binning_parameters, high_angle_binning_parameters):
        """
        create binning parameters
        :param num_banks:
        :param east_west_binning_parameters:
        :param high_angle_binning_parameters:
        :return:
        """
        binning_parameter_dict = dict()
        if num_banks == 3:
            # west(1), east(1), high(1)
            for bank_id in range(1, 3):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            binning_parameter_dict[3] = high_angle_binning_parameters
        elif num_banks == 7:
            # west (3), east (3), high (1)
            for bank_id in range(1, 7):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            binning_parameter_dict[7] = high_angle_binning_parameters
        elif num_banks == 27:
            # west (9), east (9), high (9)
            for bank_id in range(1, 19):
                binning_parameter_dict[bank_id] = east_west_binning_parameters
            for bank_id in range(19, 28):
                binning_parameter_dict[bank_id] = high_angle_binning_parameters
        else:
            raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))

        return binning_parameter_dict

    # TODO - 2018 - May move this to a utility module
    @staticmethod
    def check_creation_date(file_name):
        """
        check the create date (year, month, date) for a file
        :except RuntimeError: if the file does not exist
        :param file_name: 
        :return: 
        """
        datatypeutility.check_file_name(file_name, check_exist=True)
    
        # get the creation date in float (epoch time)
        if platform.system() == 'Windows':
            # windows not tested
            epoch_time = os.path.getctime(file_name)
        else:
            # mac osx/linux
            stat = os.stat(file_name)
            try:
                epoch_time = stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                epoch_time = stat.st_mtime
            # END-TRY
        # END-IF-ELSE
    
        # convert epoch time to a string as YYYY-MM-DD
        file_create_time = time.localtime(epoch_time)
        file_create_time_str = time.strftime('%Y-%m-%d', file_create_time)
    
        return file_create_time_str

    @property
    def calibration_dates(self):
        """
        get sorted dates for all the calibration files
        :return: a list of string. date in format YYY-MM-DD
        """
        return sorted(self._calibration_dict.keys())

    def create_vdrive_reference(self, num_banks, h5_bin_file_name=None, binning_parameters=None):
        """ Create a TableWorkspace with binning information
        Modified from "reduceVulcan.create_bin_table"
        :param num_banks:
        :param h5_bin_file_name:
        :param binning_parameters:
        :return:
        """
        def generate_binning_table(table_name):
            """
            generate an EMPTY binning TableWorkspace
            :param table_name:
            :return:
            """
            column_definitions = [('str', 'indexes'),
                                  ('str', 'params')]

            bin_table = mantid_helper.create_table_workspace(table_ws_name=table_name,
                                                             column_def_list=column_definitions)

            return bin_table
        # END-DEF:

        def extrapolate_last_bin(bins):
            """
            :param bins:
            :return:
            """
            datatypeutility.check_numpy_arrays('TOF bins', [bins], dimension=1, check_same_shape=False)
            delta_bin = (bins[-1] - bins[-2]) / bins[-2]
            next_bin = bins[-1] * (1 + delta_bin)

            return next_bin
        # END-DEF:

        # check inputs
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 1000000))
        if (h5_bin_file_name is not None) and (binning_parameters is not None):
            raise RuntimeError('It is not allowed to specify both h5_bin_file and binning parameter')

        if binning_parameters:
            # using user-specified binning parameters
            # NOTE/FIXME/TODO - This will be broken when east/west/high resolution changes
            assert isinstance(binning_parameters, list) or isinstance(binning_parameters, tuple), \
                'Binning parameters {} must be either tuple of list but not {}' \
                ''.format(binning_parameters, type(binning_parameters))
            if num_banks > 2 and len(binning_parameters) != 2:
                raise RuntimeError('In east/west/high resolution bank mode, it is required for 2 binning '
                                   'parameters for normal and high resolution serving method to '
                                   'save as GSAS file')

            # create binning table
            # TODO - 2018 - NEED TO FIND a method to get a unique name for such a workspace that no need to
            # TODO        - create the table workspace again and again
            # Example
            # import hashlib
            # mystring = input('Enter String to hash: ')
            # # Assumes the default UTF-8
            # hash_object = hashlib.md5('{}_{}...'.format(num_banks)
            # print(hash_object.hexdigest()): type = str
            bin_table_name = 'VULCAN_Binning_Table_{0}Banks'.format(num_banks)
            # if AnalysisDataService.doesExist(bin_table_name) is False:  FIXME how to avoid duplicate operation?
            bin_table_ws = generate_binning_table(bin_table_name)
            east_west_binning_parameters, high_angle_binning_parameters = binning_parameters

            if num_banks == 3:
                # west(1), east(1), high(1)
                bin_table_ws.addRow(['0, 1', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['2', '{0}'.format(high_angle_binning_parameters)])
            elif num_banks == 7:
                # west (3), east (3), high (1)
                bin_table_ws.addRow(['0-5', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['6', '{0}'.format(high_angle_binning_parameters)])
            elif num_banks == 27:
                # west (3), east (3), high (1)
                bin_table_ws.addRow(['0-17', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['18-26', '{0}'.format(high_angle_binning_parameters)])
            else:
                raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))

        else:
            # use explicitly defined bins and thus matrix workspace is required
            # import h5 file
            base_table_name = os.path.basename(h5_bin_file_name).split('.')[0]

            # load vdrive bin file to 2 different workspaces
            bin_file = h5py.File(h5_bin_file_name, 'r')
            low_bins = bin_file['west_east_bank'][:]
            high_bins = bin_file['high_angle_bank'][:]
            bin_file.close()

            # append last value for both east/west bin and high angle bin
            low_bins = numpy.append(low_bins, extrapolate_last_bin(low_bins))
            high_bins = numpy.append(high_bins, extrapolate_last_bin(high_bins))

            # TODO - 20180813 - Need a unique name!
            low_bin_ws_name = '{0}_LowResBin'.format(base_table_name)
            high_bin_ws_name = '{0}_HighResBin'.format(base_table_name)
            if not mantid_helper.workspace_does_exist(low_bin_ws_name):
                mantid_helper.create_workspace_2d(vec_x=low_bins, vec_y=low_bins, vec_e=low_bins,
                                                  output_ws_name=low_bin_ws_name)
                # mantidsimple.CreateWorkspace(low_bins, low_bins, NSpec=1, OutputWorkspace=)
            if not mantid_helper.workspace_does_exist(high_bin_ws_name):
                mantid_helper.create_workspace_2d(vec_x=high_bins, vec_y=high_bins, vec_e=high_bins,
                                                  output_ws_name=high_bin_ws_name)
                # mantidsimple.CreateWorkspace(high_bins, high_bins, NSpec=1, OutputWorkspace=high_bin_ws_name)

            # create binning table name
            bin_table_name = self.vdrive_binning_ref_ws_name(h5_bin_file_name)

            # no need to create this workspace again and again
            if mantid_helper.workspace_does_exist(bin_table_name):
                return bin_table_name

            # create binning table
            ref_bin_table = generate_binning_table(bin_table_name)

            if num_banks == 3:
                # west(1), east(1), high(1)
                ref_bin_table.addRow(['0, 1', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['2', '{0}: {1}'.format(high_bin_ws_name, 0)])
            elif num_banks == 7:
                # west (3), east (3), high (1)
                ref_bin_table.addRow(['0-5', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['6', '{0}: {1}'.format(high_bin_ws_name, 0)])
            elif num_banks == 27:
                # west (3), east (3), high (1)
                ref_bin_table.addRow(['0-17', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['18-26', '{0}: {1}'.format(high_bin_ws_name, 0)])
            else:
                raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
        # END-IF-ELSE

        return bin_table_name

    @staticmethod
    def get_base_name(file_name, num_banks):
        """ get the base name for the calbration workspace, grouping workspace and mask workspace
        :param file_name:
        :param num_banks:
        :return:
        """
        datatypeutility.check_string_variable('Calibration file name', file_name)

        base_name = os.path.basename(file_name).split('.')[0] + '{0}banks'.format(num_banks)

        return base_name

    def get_calibration_file(self, year_month_date, num_banks):
        """
        get the calibration file by date and number of banks
        :param year_month_date:
        :param num_banks:
        :return: calibration file date, calibration file name
        """
        datatypeutility.check_string_variable('YYYY-MM-DD string', year_month_date)
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 28))

        # search the previous date
        # check format first
        if len(year_month_date) != 10 or year_month_date.count('-') != 2:
            raise RuntimeError('Year-Month-Date string must be of format YYYY-MM-DD but not {0}'
                               ''.format(year_month_date))

        # search the list
        date_list = sorted(self._calibration_dict.keys())
        if year_month_date < date_list[0]:
            raise RuntimeError('Input year-month-date {0} is too early comparing to {1}'
                               ''.format(year_month_date, date_list[0]))

        print ('[DB...BAT] File YYYY-MM-DD: {}'.format(year_month_date))
        # do a brute force search (as there are only very few of them)
        cal_date_index = None
        for i_date in range(len(date_list)-1, -1, -1):
            print ('[DB...BAT] Calibration Date: {}'.format(date_list[i_date]))
            if year_month_date > date_list[i_date]:
                cal_date_index = date_list[i_date]
                break
            # END-IF
        # END-FOR  

        print ('[DB...BAT] calibration dict: {}'.format(self._calibration_dict.keys()))

        calibration_file_name = self._calibration_dict[cal_date_index][num_banks]

        return cal_date_index, calibration_file_name

    def get_default_binning_reference(self, run_date, num_banks):
        """ get default binning reference parameters
        :param run_date:
        :param num_banks:
        :return:
        """
        datatypeutility.check_string_variable('Run date', run_date)
        if run_date.count('-') != 2:
            raise RuntimeError('{} is not a standard YYYY-MM-DD format'.format(run_date))

        if run_date >= self._ned_date:
            calib_date = self._ned_date
        else:
            calib_date = '1990-01-01'

        if (calib_date, num_banks) in self._default_tof_bins_dict:
            return self._default_tof_bins_dict[calib_date, num_banks]

        # hard coded default binning parameters
        ew_bin_params = '5000.,-0.001,70000.'
        if run_date >= self._ned_date:
            high_angle_params = '5000.,-0.0003,70000.'
        else:
            high_angle_params = None

        # create binning
        self._default_tof_bins_dict[calib_date, num_banks] = \
            self.create_nature_bins(num_banks=num_banks, east_west_binning_parameters=ew_bin_params,
                                    high_angle_binning_parameters=high_angle_params)

        print ('[DB...BAT] Binning: {}'.format(self._default_tof_bins_dict[calib_date, num_banks]))

        return self._default_tof_bins_dict[calib_date, num_banks]

    def get_focused_instrument_parameters(self, num_banks):
        """

        :param num_banks:
        :return:
        """
        # check input
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, 28))

        edit_instrument_param_dict = dict()

        try:
            edit_instrument_param_dict['L1'] = self._focus_instrument_dict['L1']
            edit_instrument_param_dict['L2'] = self._focus_instrument_dict['L2'][num_banks]
            edit_instrument_param_dict['Polar'] = self._focus_instrument_dict['Polar'][num_banks]
            edit_instrument_param_dict['Azimuthal'] = self._focus_instrument_dict['Azimuthal'][num_banks]
            edit_instrument_param_dict['SpectrumIDs'] = self._focus_instrument_dict['SpectrumIDs'][num_banks]
        except KeyError as key_err:
            err_msg = 'Unable to retrieve virtual instrument geometry for {}-bank case. FYI: {}' \
                      ''.format(num_banks, key_err)
            print ('[ERROR CAUSING CRASH] {}'.format(err_msg))
            raise RuntimeError(err_msg)

        return edit_instrument_param_dict

    def get_loaded_calibration_workspaces(self, run_start_date, num_banks):
        """
        get the loaded workspaces
        :param run_start_date:
        :param num_banks:
        :return:
        """
        cal_date, cal_file_name = self.get_calibration_file(run_start_date, num_banks)

        try:
            calib_ws_collection = self._loaded_calibration_file_dict[cal_date][num_banks]
        except KeyError as key_err:
            error_msg = 'File {0} is not loaded yet! Client shall check the loaded workspace first.' \
                        'FYI: {1}'.format(cal_file_name, key_err)
            print ('[Crash Error] {}'.format(error_msg))
            raise RuntimeError(error_msg)

        return calib_ws_collection

    def get_vdrive_binning_reference(self, run_date):
        """
        find the VDRIVE binning reference file by run start date (YYYY-MM-DD)
        :param run_date:
        :return: None or reference file name
        """
        datatypeutility.check_string_variable('Run start date in format YYYY-MM-DD', run_date)

        ref_date_index = sorted(self._vdrive_bin_ref_file_dict.keys())
        start_date_index = None
        for index in range(len(ref_date_index)-1, -1, -1):
            if run_date > ref_date_index[index]:
                start_date_index = ref_date_index[index]
                break
        # END-FOR

        if start_date_index is None:
            # not found
            err_msg = 'Run start date {} is before all VDRIVE reference file date {}'.format(run_date, ref_date_index)
            print ('[ERROR CAUSING CRASH] {0}'.format(err_msg))
            raise RuntimeError(err_msg)
        # END-IF

        return self._vdrive_bin_ref_file_dict[start_date_index]

    # TESTME - 20180730 - Updated
    def has_loaded(self, run_start_date, num_banks, check_workspaces=False):
        """ check whether a run's corresponding calibration file has been loaded
        If check_workspace is True, then check the real workspaces if they are not in the dictionary;
        If the workspaces are there, then add the calibration files to the dictionary
        :param run_start_date:
        :param num_banks:
        :param check_workspaces: if True, then check the workspace names instead of dictionary.
        :return:
        """
        # get calibration date and file name
        calib_file_date, calib_file_name = self.get_calibration_file(run_start_date, num_banks)
        print ('[DB...BAT] ID/Date: {}; Calibration file name: {}'.format(calib_file_date, calib_file_name))

        # regular check with dictionary
        has_them = True
        if calib_file_date not in self._loaded_calibration_file_dict:
            has_them = False
        elif num_banks not in self._loaded_calibration_file_dict[calib_file_date]:
            has_them = False

        if not has_them and check_workspaces:
            # check with workspace name
            base_ws_name = self.get_base_name(calib_file_name, num_banks)
            has_all = True
            has_some = False
            for sub_ws_name in ['calib', 'mask', 'grouping']:
                ws_name = '{}_{}'.format(base_ws_name, sub_ws_name)
                if mantid_helper.workspace_does_exist(ws_name) is False:
                    has_all = False
                else:
                    has_some = True
            # END-FOR

            if has_all != has_some:
                raise RuntimeError('Some calibration workspace existed but not all!')
            if has_all:
                # add to dictionary
                has_them = True
                if calib_file_date not in self._loaded_calibration_file_dict:
                    self._loaded_calibration_file_dict[calib_file_date] = dict()
                calib_ws_collection = DetectorCalibrationWorkspaces()
                calib_ws_collection.calibration = '{}_{}'.format(base_ws_name, 'calib')
                calib_ws_collection.mask = '{}_{}'.format(base_ws_name, 'mask')
                calib_ws_collection.grouping = '{}_{}'.format(base_ws_name, 'grouping')
                self._loaded_calibration_file_dict[calib_file_date][num_banks] = calib_ws_collection

            # END-IF
        # END-IF-NOT

        return has_them

    def load_calibration_file(self, calibration_file_name, cal_date_index, num_banks, ref_ws_name):
        """ load calibration file
        :return:
        """
        # check inputs
        datatypeutility.check_file_name(calibration_file_name, check_exist=True, note='Calibration file')
        datatypeutility.check_int_variable('Number of banks', num_banks, (1, None))

        # load calibration
        base_name = self.get_base_name(calibration_file_name, num_banks)
        outputs = mantid_helper.load_calibration_file(calibration_file_name, base_name, ref_ws_name)
        # get output workspaces for their names
        calib_ws_collection = DetectorCalibrationWorkspaces()
        calib_ws_collection.calibration = outputs.OutputCalWorkspace.name()
        calib_ws_collection.mask = outputs.OutputMaskWorkspace.name()
        calib_ws_collection.grouping = outputs.OutputGroupingWorkspace.name()
        print ('[DB...BAT] Output: {}'.format(calib_ws_collection))

        # add to loaded calibration file container
        if cal_date_index not in self._loaded_calibration_file_dict:
            self._loaded_calibration_file_dict[cal_date_index] = dict()
        self._loaded_calibration_file_dict[cal_date_index][num_banks] = calib_ws_collection

        return calib_ws_collection

    def search_load_calibration_file(self, run_start_date, bank_numbers, ref_workspace_name):
        """
        search for calibration and load it
        :param run_start_date: string in YYYY-MM-DD format
        :param bank_numbers:
        :return:
        """
        # use run_start_date (str) to search in the calibration date time string
        cal_date_index, calibration_file_name = self.get_calibration_file(run_start_date, bank_numbers)
        print ('[DB...BAT] Located calibration file {0} with reference ID {1}'
               ''.format(calibration_file_name, cal_date_index))

        # check whether this file has been loaded
        if self.has_loaded(cal_date_index, bank_numbers):
            return

        # load
        self.load_calibration_file(calibration_file_name, cal_date_index, bank_numbers, ref_workspace_name)

        return

    @staticmethod
    def vdrive_binning_ref_ws_name(file_name):
        """
        get the standard workspace name for VDrive binning reference
        :param file_name:
        :return:
        """
        datatypeutility.check_string_variable('VDrive binning reference file', file_name)
        base_name = os.path.basename(file_name)
        ws_name = base_name.split('.')[0]

        return ws_name


class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """
    FilterBadPulse = 1
    AlignAndFocus = 2
    NormaliseByCurrent = 3
    CalibratedByVanadium = 4

    def __init__(self, run_number, ipts_number):
        """
        Purpose:
            Initialize an object of DataReductionTracer
        Requirements:
            1. run number is integer
            2. file path is string
            3. vanadium calibration is a string for calibration file. it could be none
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not {1}.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))

        # set up
        self._iptsNumber = ipts_number
        self._runNumber = run_number

        # vanadium run number. it will be used as a key to the dictionary to look for a vanadium workspace
        self._vanadiumCalibrationRunNumber = None

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._vdriveWorkspace = None
        self._tofWorkspace = None
        self._dspaceWorkspace = None

        # compressed chopped workspace name
        self._compressedChoppedWorkspaceName = None

        # status flag
        self._isReduced = False
        self._isChopped = False

        # detailed reduction information
        self._reductionStatus = None
        self._reductionInformation = None

        # initialize states of reduction beyond
        self._badPulseRemoved = False
        self._normalisedByCurrent = False
        self._correctedByVanadium = False

        # reduced file list
        self._reducedFiles = None

        # variables about chopped workspaces
        self._slicerKey = None   # None stands for the reduction is without chopping
        self._choppedWorkspaceNameList = None
        self._choppedNeXusFileList = list()

        return

    @property
    def compressed_ws_name(self):
        """
        get compressed workspace name
        if the name is not set up yet, then make it and set
        :return:
        """
        if self._compressedChoppedWorkspaceName is None:
            # not set yet.
            self._compressedChoppedWorkspaceName = 'Chopped_{0}_Slicer_{1}.'.format(self._runNumber, self._slicerKey)

        return self._compressedChoppedWorkspaceName

    @property
    def dspace_workspace(self):
        """
        Mantid binned d-Spacing workspace
        :return:
        """
        return self._dspaceWorkspace

    @property
    def event_workspace_name(self):
        """
        Get the name of the event workspace
        :return:
        """
        return self._eventWorkspace

    @event_workspace_name.setter
    def event_workspace_name(self, value):
        """
        Set the name of the event workspace.  This operation might be called
        before the workspace is created.
        Requirements:
            1. Input is a string
        :param value:
        :return:
        """
        # Check
        assert isinstance(value, str), 'Input workspace name must be string but not %s.' % str(type(value))
        # Set
        self._eventWorkspace = value

    def get_information(self):
        """
        construct information about the chopped workspace
        :return: a dictionary containing all the information about the reduction tracker
        """
        info_dict = dict()
        info_dict['run'] = self._runNumber
        info_dict['reduced'] = self._isReduced
        if self._slicerKey is None:
            # regular reduced data
            info_dict['slicer_key'] = None
        else:
            # chopped run
            info_dict['slicer_key'] = self._slicerKey
            info_dict['workspaces'] = self._choppedWorkspaceNameList[:]
            info_dict['raw_files'] = self._choppedNeXusFileList[:]
            if self._reducedFiles is not None:
                info_dict['files'] = self._reducedFiles[:]
            else:
                info_dict['files'] = None

        return info_dict

    def get_reduced_gsas(self):
        """

        :return:
        """
        gsas_file = None

        for file_name in self._reducedFiles:
            main_file_name, file_ext = os.path.splitext(file_name)
            if file_ext.lower() in ['.gda', '.gsas', '.gsa']:
                gsas_file = file_name
                break

        if gsas_file is None:
            raise RuntimeError('Unable to locate reduced GSAS file of run {0}.  '
                               'Files found are {1}'.format(self._runNumber, self._reducedFiles))

        return gsas_file

    @property
    def ipts_number(self):
        """
        get the IPTS number set to this run number
        :return:
        """
        return self._iptsNumber

    @property
    def is_chopped(self):
        """
        check whether the reduction is about a chopped run
        :return:
        """
        return self._isChopped

    @is_chopped.setter
    def is_chopped(self, status):
        """
        set the state that the run is chopped
        :return:
        """
        self._isChopped = status

        return

    @property
    def is_chopped_run(self):
        """
        check whether the reduction is about a chopped run
        :return:
        """
        return self._slicerKey is not None

    @property
    def is_corrected_by_vanadium(self):
        """

        :return:
        """
        return self._correctedByVanadium

    @is_corrected_by_vanadium.setter
    def is_corrected_by_vanadium(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool), 'Flag/state must be a boolean'
        self._correctedByVanadium = state

    @property
    def is_normalized_by_current(self):
        """

        :return:
        """
        return self._normalisedByCurrent

    @is_normalized_by_current.setter
    def is_normalized_by_current(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool)

        self._normalisedByCurrent = state

    @property
    def is_reduced(self):
        """ Check whether the event data that has been reduced
        :return:
        """
        return self._isReduced

    @is_reduced.setter
    def is_reduced(self, value):
        """
        Purpose: set the status that the event data has been reduced
        Requirements: value is boolean
        Guarantees:
        :param value:
        :return:
        """
        assert isinstance(value, bool), 'Input for is_reduced must be a boolean but not %s.' % str(type(value))
        self._isReduced = value

    @property
    def is_raw(self):
        """
        Show the status whether the workspace has never been processed
        :return:
        """
        return not self._isReduced

    @property
    def run_number(self):
        """ Read only to return the run number that this tracker
        :return:
        """
        return self._runNumber

    @property
    def vdrive_workspace(self):
        """
        VDrive-binned workspace
        :return:
        """
        return self._vdriveWorkspace

    @property
    def sliced_focused_workspaces(self):
        """
        get the names of sliced and focused workspaces
        :return:
        """
        if self._choppedWorkspaceNameList is None or len(self._choppedWorkspaceNameList) == 0:
            return None
        elif self.is_reduced is False:
            return None

        return self._choppedWorkspaceNameList[:]

    @property
    def tof_workspace(self):
        """
        Mantid binned TOF workspace
        :return:
        """
        return self._tofWorkspace

    def set_chopped_workspaces(self, workspace_name_list, append):
        """
        set the chopped workspaces' names
        :param workspace_name_list:
        :param append: append chopped workspaces
        :return:
        """
        # check inputs
        datatypeutility.check_list('Workspace names', workspace_name_list)

        # reset self._choppedWorkspaceNameList if needed
        if self._choppedWorkspaceNameList is None or not append:
            self._choppedWorkspaceNameList = list()

        # append input workspace names by checking valid or existence
        err_msg = ''

        for ws_name in workspace_name_list:
            # check type
            if not isinstance(ws_name, str):
                err_msg += 'Input {} of type {} is invalid to be a workspace name'.format(ws_name, type(ws_name))
                continue

            # check name and existence
            ws_name = ws_name.strip()
            # skip
            if len(ws_name) == 0 or mantid_helper.workspace_does_exist(ws_name) is False:
                err_msg += 'Workspace "{}" does not exist'
                continue

            # append
            self._choppedWorkspaceNameList.append(ws_name)
        # END-FOR

        if len(err_msg) == 0:
            err_msg = None

        return err_msg

    def set_chopped_nexus_files(self, chopped_file_list, append=True):
        """ set NeXus files that are saved from chopped workspace to this tracker
        """
        # check input
        assert isinstance(chopped_file_list, list), 'Chopped NeXus files {0} must be given by list but not {1}.' \
                                                    ''.format(chopped_file_list, type(chopped_file_list))

        # clear previous data
        if not append:
            self._choppedNeXusFileList = list()

        # append the input file lsit
        self._choppedNeXusFileList.extend(chopped_file_list)

        return

    def set_reduced_files(self, file_name_list, append):
        """
        add reduced file
        :param file_name_list:
        :param append:
        :return:
        """
        assert isinstance(file_name_list, list), 'Input file names must be in a list but not {0}.' \
                                                 ''.format(type(file_name_list))

        if not append or self._reducedFiles is None:
            self._reducedFiles = file_name_list[:]
        else:
            self._reducedFiles.extend(file_name_list[:])

        return

    def set_reduced_workspaces(self, vdrive_bin_ws, tof_ws, dspace_ws):
        """

        :param vdrive_bin_ws:
        :param tof_ws:
        :param dspace_ws: it could be None or name of workspace in d-spacing
        :return:
        """
        # check workspaces existing
        if vdrive_bin_ws is not None:
            assert mantid_helper.workspace_does_exist(vdrive_bin_ws), 'VDrive-binned workspace {0} does not exist ' \
                                                                      'in ADS'.format(vdrive_bin_ws)
        if tof_ws is not None:
            assert mantid_helper.workspace_does_exist(tof_ws), 'Mantid-binned TOF workspace {0} does not exist ' \
                                                               'in ADS.'.format(tof_ws)

        if dspace_ws is not None:
            assert mantid_helper.workspace_does_exist(dspace_ws),\
                'Mantid-binned D-space workspace {0} does not exist in ADS.'.format(dspace_ws)
            dspace_ws_unit = mantid_helper.get_workspace_unit(dspace_ws)
            assert dspace_ws_unit == 'dSpacing',\
                'Unable to set reduced d-space workspace: The unit of DSpace workspace {0} should be dSpacing but ' \
                'not {1}.'.format(str(dspace_ws), dspace_ws_unit)
        # END-IF

        self._vdriveWorkspace = vdrive_bin_ws
        self._tofWorkspace = tof_ws
        self._dspaceWorkspace = dspace_ws

        # TODO - 20180821 - Find out all the isReduced.setter() usage
        self._isReduced = True

        return

    def set_reduction_status(self, status, message, chopped_data):
        """
        set the reduction status for this tracker
        :param status:
        :param message:
        :param chopped_data
        :return:
        """
        # check input
        assert isinstance(status, bool), 'Reduction status must be given by bool but not {0}'.format(type(status))
        assert isinstance(message, str), 'Reduction message {0} must be string but not {1}' \
                                         ''.format(message, type(message))
        assert isinstance(chopped_data, bool), 'Flag for being chopped run must be boolean but not {0}' \
                                               ''.format(type(chopped_data))

        self._reductionStatus = status
        self._reductionInformation = message
        self._isChopped = chopped_data

        return

    def set_slicer_key(self, slicer_key):
        """
        set slicer key to the
        :param slicer_key:
        :return:
        """
        self._slicerKey = slicer_key

        return

    @property
    def vanadium_calibration(self):
        """
        Return vanadium calibration run number
        :return:
        """
        return self._vanadiumCalibrationRunNumber

    @vanadium_calibration.setter
    def vanadium_calibration(self, value):
        """
        Set vanadium calibration run number
        Purpose:
        Requirements:
            value is integer
        Guarantees:
            vanadium run number is set
        :param value:
        :return:
        """
        assert isinstance(value, int), 'Input value should be integer for run number'
        self._vanadiumCalibrationRunNumber = value

        return
# END-CLASS


class ReductionManager(object):
    """ Class ReductionManager takes the control of reducing SNS/VULCAN's event data
    to diffraction pattern for Rietveld analysis.

    * Business model and technical model
      - Run number as integers or data file name are used to communicate with client;
      - Workspace names are used for internal communications.

    Its main data structure contains
    1. a dictionary of reduction controller
    2. a dictionary of loaded vanadium

    ??? It is able to reduce the data file in the format of data file,
    run number and etc. 

    ??? It supports event chopping.
    """
    SUPPORTED_INSTRUMENT = ['VULCAN']

    def __init__(self, instrument):
        """
        Purpose:

        Requirements:
            1. instrument is a valid instrument's name
        Guarantees:
        :param instrument:
        :return:
        """
        # Check requirements
        assert isinstance(instrument, str), 'Input instrument must be of type str'
        instrument = instrument.upper()
        assert instrument in ReductionManager.SUPPORTED_INSTRUMENT, \
            'Instrument %s is not in the supported instruments (%s).' % (instrument,
                                                                         ReductionManager.SUPPORTED_INSTRUMENT)

        # Set up including default
        self._myInstrument = instrument

        # reduction tracker: key = run number (integer), value = DataReductionTracker
        self._reductionTrackDict = dict()

        # simplified reduced workspace manager.  key = run number, value = workspace name
        # self._runFocusedWorkspaceDict = dict()

        # calibration file and workspaces management
        self._calibrationFileManager = CalibrationManager()   # key = calibration file name

        # init standard diffraction focus parameters
        self._diff_focus_params = self._init_vulcan_diff_focus_params()

        # some initialization operation
        self.load_vdrive_bins(default=True)

        # masks and ROI
        self._loaded_masks = dict()  # [mask/roi xml] = mask_ws_name, is_roi

        return

    @staticmethod
    def _init_vulcan_diff_focus_params():
        """
        initial setup for diffraction focus algorithm parameters
        :return:
        """
        params_dict = dict()
        params_dict['CompressEvents'] = dict()
        params_dict['EditInstrumentGeometry'] = dict()

        # compress events
        params_dict['CompressEvents']['Tolerance'] = 0.01

        # edit instrument
        params_dict['EditInstrumentGeometry']['L1'] = None
        params_dict['EditInstrumentGeometry']['SpectrumIDs'] = None
        params_dict['EditInstrumentGeometry']['L2'] = None
        params_dict['EditInstrumentGeometry']['Polar'] = None
        params_dict['EditInstrumentGeometry']['Azimuthal'] = None

        return params_dict

    def chop_vulcan_run(self, ipts_number, run_number, raw_file_name, split_ws_name, split_info_name, slice_key,
                        output_directory, reduce_data_flag, save_chopped_nexus, number_banks,
                        tof_correction, vanadium, user_binning_parameter, vdrive_binning):
        """
        chop VULCAN run with reducing to GSAS file as an option
        :param ipts_number: IPTS number (serving as key for reference)
        :param run_number: Run number (serving as key for reference)
        :param raw_file_name:
        :param split_ws_name:
        :param split_info_name:
        :param slice_key: a general keyword to refer from the reduction tracker
        :param output_directory: string for directory or None for saving to archive
        :param number_banks:
        :param vanadium: vanadium run number of None for not normalizing
        :param tof_correction:
        :param user_binning_parameter: float (for user specified binning parameter) or None
        :param vdrive_binning: flag to use vdrive binning
        :return: 2-tuple.  (1) boolean as status  (2) error message
        """
        if tof_correction:
            raise NotImplementedError('[WARNING] TOF correction is not implemented yet.')

        # check other inputs
        if user_binning_parameter is not None and vdrive_binning:
            raise RuntimeError('User binning parameter {} and vdrive binning flag {} cannot be specified '
                               'simultaneously'.format(user_binning_parameter, vdrive_binning))
        if user_binning_parameter is not None:
            datatypeutility.check_float_variable('User specified binning', user_binning_parameter, (0.00001, None))

        # set up reduction parameters
        reduction_setup = reduce_VULCAN.ReductionSetup()

        reduction_setup.set_ipts_number(ipts_number)
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(raw_file_name)

        # splitters workspace suite
        reduction_setup.set_splitters(split_ws_name, split_info_name)

        # define chop processor
        # TODO - 20180820 - How to manager this!
        chop_reducer = reduce_adv_chop.AdvancedChopReduce(reduction_setup)

        # option to save to archive
        if output_directory is None:
            # save to SNS archive.
            reduction_setup.set_chopped_output_to_archive(create_parent_directories=True)
        else:
            # save to user-specified directories. GSAS and NeXus will be in the same directory
            reduction_setup.set_output_dir(output_directory)
            reduction_setup.set_gsas_dir(output_directory, main_gsas=True)
            reduction_setup.set_chopped_nexus_dir(output_directory)
        # END-IF-ELSE

        # use run number to check against with calibration manager
        run_start_date = self._calibrationFileManager.check_creation_date(raw_file_name)
        cal_loaded = self._calibrationFileManager.has_loaded(run_start_date=run_start_date, num_banks=number_banks,
                                                             check_workspaces=True)

        # set up the calibration workspaces
        if not cal_loaded:
            cal_file_date, cal_file_name = self._calibrationFileManager.get_calibration_file(year_month_date=run_start_date,
                                                                              num_banks=number_banks)
            cal_ws_base_name = self._calibrationFileManager.get_base_name(cal_file_name, number_banks)
        else:
            cal_file_name = None
            cal_ws_base_name = None

        if not cal_loaded:
            assert cal_ws_base_name is not None, 'Impossible to have None cal base name'
            reduction_setup.set_calibration_file(calib_file_name=cal_file_name,
                                                 base_ws_name=cal_ws_base_name)
        else:
            # TODO FIXME - 20180820 - This is not correct!
            reduction_setup.set_calibration_workspaces(self._calibrationFileManager.get_caibration_workspaces())
        # reduction_setup.set_default_calibration_files(num_focused_banks=number_banks,
        #                                               cal_file_name=cal_file_name,
        #                                               base_ws_name=cal_ws_base_name)

        # initialize tracker
        tracker = self.init_tracker(ipts_number, run_number, slice_key)
        tracker.is_reduced = False

        error_message = None

        if reduce_data_flag and not save_chopped_nexus:
            # chop and reduce chopped data to GSAS: NOW, it is Version 2.0 speedup
            # set up the flag to save chopped raw data
            reduction_setup.save_chopped_workspace = save_chopped_nexus

            # set the flag for not being an auto reduction
            reduction_setup.is_auto_reduction_service = False

            # TODO - 20180821 - Need to have this as an option and verify what if flag is True
            reduction_setup.set_align_vdrive_bin(flag=False)

            # set up reducer
            reduction_setup.process_configurations()

            # Slice and focus the data *** V2.0
            # determine the binning for output GSAS workspace
            if vdrive_binning:
                # vdrive binning
                binning_param_dict = self._calibrationFileManager.get_vdrive_binning_reference(run_start_date)

            elif user_binning_parameter:
                binning_param_dict = self.form_binning_parameters(number_banks, user_binning_parameter)
                vs
                binning_parameter_dict = self.create_nature_bins(self._number_banks, east_west_binning_parameters,
                                                                 high_angle_binning_parameters)
            else:
                # default binning
                binning_param_dict = self._calibrationFileManager.get_default_binning_reference(run_start_date,
                                                                                                number_banks)
            # END-IF-ELSE

            gsas_info = {'IPTS': ipts_number, 'parm file': 'vulcan.prm'}
            status, message = chop_reducer.execute_chop_reduction_v2(clear_workspaces=False,
                                                                     binning_parameters=binning_param_dict,
                                                                     gsas_info_dict=gsas_info)

            # set up the reduced file names and workspaces and add to reduction tracker dictionary
            tracker.set_reduction_status(status, message, True)

            reduced, workspace_name_list = chop_reducer.get_reduced_workspaces(chopped=True)
            error_message = self.set_chopped_reduced_workspaces(run_number, slice_key, workspace_name_list, append=True)
            self.set_chopped_reduced_files(run_number, slice_key, chop_reducer.get_reduced_files(), append=True)

            tracker.is_reduced = True

        elif reduce_data_flag and save_chopped_nexus:
            # required to save the chopped workspace to NeXus file
            # slow algorithm is then used
            raise NotImplementedError('Find out the old way to reduce and save data')

        else:
            # chop data only without reduction
            status, ret_obj = chop_reducer.chop_data()

            if not status:
                return False, 'Unable to chop run {0} due to {1}.'.format(run_number, ret_obj)

            # get chopped workspaces' names, saved NeXus file name; check them and store to lists
            chopped_ws_name_list = list()
            chopped_file_list = list()
            for file_name, ws_name in ret_obj:
                if file_name is not None:
                    chopped_file_list.append(file_name)
                if isinstance(ws_name, str) and mantid_helper.workspace_does_exist(ws_name):
                    chopped_ws_name_list.append(ws_name)
            # END-FOR

            # initialize tracker
            tracker = self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=slice_key)
            tracker.is_reduced = False
            tracker.is_chopped = True
            if len(chopped_ws_name_list) > 0:
                tracker.set_chopped_workspaces(chopped_ws_name_list, append=True)
            if len(chopped_file_list) > 0:
                tracker.set_chopped_nexus_files(chopped_file_list, append=True)
        # END-IF

        return True, error_message

    def get_event_workspace_name(self, run_number):
        """
        Get or generate the name of a raw event workspace
        Requirements: run number must be a positive integer
        :param run_number:
        :return:
        """
        # check
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        # form the reduction-manager-standard name
        event_ws_name = '%s_%d_events' % (self._myInstrument, run_number)

        return event_ws_name

    def get_reduced_data(self, run_number, unit):
        """ Get data (x, y and e) of a reduced run in the specified unit
        Purpose: Get reduced data including all spectra
        Requirements: run number is a valid integer; unit is a string for supported unit
        Guarantees: all data of the reduced run will be returned
        :param run_number:
        :param unit: target unit for the output X vector.  If unit is None, then no request
        :return: dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # check
        assert isinstance(run_number, int), 'Input run number must be an integer.'
        assert unit is None or isinstance(unit, str), 'Output data unit must be either None (default) or a string.'

        # get reduced workspace name
        reduced_ws_name = self.get_reduced_workspace(run_number, is_vdrive_bin=True, unit='TOF')

        # get data
        data_set_dict, unit = mantid_helper.get_data_from_workspace(reduced_ws_name, target_unit=unit,
                                                                    point_data=True, start_bank_id=True)
        assert isinstance(data_set_dict, dict), 'Returned value from get_data_from_workspace must be a dictionary,' \
                                                'but not %s.' % str(type(data_set_dict))

        return data_set_dict

    def get_reduced_file(self, run_number, file_type):
        """

        :param run_number:
        :param file_type:
        :return:
        """
        # check inputs
        assert isinstance(file_type, str) and file_type in ['gda', 'gsas', 'gss'],\
            'File type {0} is not supported.'.format(file_type)

        if file_type in ['gda', 'gsas', 'gsa']:
            file_name = self._reductionTrackDict[run_number].get_reduced_gsas()
        else:
            raise RuntimeError('Not Implemented yet!')

        return file_name

    def get_reduced_runs(self, with_ipts=False, chopped=False):
        """
        get reduced VULCAN runs with option for single run or chopped run
        (It is just for information)
        :param with_ipts:
        :param chopped:
        :return: a list of [case 1] run numbers [case 2] (run number, ipts) [case 3] (run number, slice key, ipts)
                           [case 4] (run number, slice key)
        """
        return_list = list()

        print ('[DB...BAT] Reduction track dict: {}'.format(self._reductionTrackDict.keys()))

        # from tracker
        for tracker_key in self._reductionTrackDict.keys():
            # get tracker with is_reduced being True
            tracker = self._reductionTrackDict[tracker_key]
            if not tracker.is_reduced:
                continue

            # filter out the tracker with key type and flag-chopped
            if isinstance(tracker_key, tuple):
                # slicing reduction case
                if not chopped:
                    continue

                run_number, slice_id = tracker_key
                if with_ipts:
                    new_item = run_number, slice_id, tracker.ipts_number
                else:
                    new_item = run_number, slice_id
            else:
                # single run
                if chopped:
                    continue

                run_number = tracker_key
                if with_ipts:
                    new_item = run_number, tracker.ipts_number
                else:
                    new_item = run_number
            # END-IF-ELSE

            print new_item

            return_list.append(new_item)
        # END-FOR

        return return_list

    def get_sliced_focused_workspaces(self, run_number, slice_key):
        """
        get the sliced and diffraction focused data in workspace
        :param run_number:
        :param slice_key:
        :return: a list of string as workspace names
        """
        tracker = self.get_tracker(run_number, slice_key)

        return tracker.sliced_focused_workspaces

    def get_reduced_workspace(self, run_number, binning_params=None, is_vdrive_bin=True, unit=None):
        """ Get the reduced matrix workspace
        Requirements:
            1. Specified run is correctly reduced;
        Guarantees:
            2. Return reduced workspace's name
        Arguments:
         - unit :: target unit; If None, then no need to convert unit
        :exception: Assertion Error if run number does not exist in self._reductionTrackDict
        :exception: RuntimeError if unit is not supported
        :param run_number:
        :param binning_params: binning parameters string
        :param is_vdrive_bin:
        :param unit:
        :return: Workspace (success) or 2-tuple (False and error message)
        """
        # Check requirements
        datatypeutility.check_int_variable('Run number', run_number, (1, None))
        if binning_params is not None:
            datatypeutility.check_string_variable('Binning parameter (string)', binning_params)

        # full reduction
        # get tracker
        assert run_number in self._reductionTrackDict, 'Run number {0} is not reduced.'.format(run_number)
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker), \
            'Stored tracker must be an instance of DataReductionTracker.'

        if is_vdrive_bin and unit != 'TOF':
            raise RuntimeError('It is possible to get a VDrive-binned workspace in unit {0} other than TOF.'
                               ''.format(unit))
        elif unit is not None and unit != 'TOF' and unit.lower() != 'dspace':
            raise RuntimeError('Unit {0} is not supported.'.format(unit))

        # get the position
        if is_vdrive_bin:
            return_ws_name = tracker.vdrive_workspace
        elif unit is None:
            return_ws_name = tracker.tof_workspace
            if return_ws_name is None:
                return_ws_name = tracker.dspace_workspace
        elif unit == 'TOF':
            return_ws_name = tracker.tof_workspace
        elif unit.lower() == 'dSpacing':
            return_ws_name = tracker.dspace_workspace
        else:
            raise RuntimeError('It is very hardly to happen!')
        # END-IF-ELSE

        return return_ws_name

    def get_tracker(self, run_number, slicer_key):
        """
        get a reduction tracker
        :param run_number:
        :param slicer_key:
        :return:
        """
        # construct a tracker key
        tracker_key = run_number, slicer_key
        if tracker_key in self._reductionTrackDict:
            tracker = self._reductionTrackDict[tracker_key]
        else:
            raise RuntimeError('Unable to locate tracker with run: {0} slicer: {1}.  Existing keys are {2}'
                               ''.format(run_number, slicer_key, self._reductionTrackDict.keys()))

        return tracker

    def has_run_reduced(self, run_number):
        """
        check whether a certain run number is reduced and stored
        :param run_number:
        :return:
        """
        datatypeutility.check_int_variable('Run number', run_number, (1, None))

        has = run_number in self._reductionTrackDict

        return has

    def init_tracker(self, ipts_number, run_number, slicer_key=None):
        """ Initialize tracker
        :param ipts_number:
        :param run_number:
        :param slicer_key: if not specified, then the reduction is without chopping
        :return: a DataReductionTracker object that is just created and initialized
        """
        # Check requirements
        datatypeutility.check_int_variable('IPTS', ipts_number, (1, None))
        datatypeutility.check_int_variable('Run number', run_number, (1, None))

        # Initialize a new tracker
        if slicer_key is None:
            tracker_key = run_number
        else:
            tracker_key = run_number, slicer_key

        if ipts_number is None:
            raise NotImplementedError('Figure out how to track a reduction without a good IPTS number!')

        if tracker_key not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number, ipts_number)
            new_tracker.set_slicer_key(slicer_key)
            self._reductionTrackDict[tracker_key] = new_tracker
        else:
            # existing tracker: double check
            assert isinstance(self._reductionTrackDict[tracker_key], DataReductionTracker),\
                'It is not DataReductionTracker but a {0}.'.format(type(self._reductionTrackDict[tracker_key]))
            # NOTE: new_tracker here is not new tracker at all!
            new_tracker = self._reductionTrackDict[tracker_key]

        return new_tracker

    def diffraction_focus_workspace(self, event_ws_name, output_ws_name, binning_params, target_unit,
                                    calibration_workspace, mask_workspace, grouping_workspace,
                                    virtual_instrument_geometry, keep_raw_ws, convert_to_matrix):
        """ focus workspace
        :param event_ws_name:
        :param output_ws_name:
        :param binning_params:
        :param target_unit:
        :param calibration_workspace:
        :param mask_workspace:
        :param grouping_workspace:
        :param virtual_instrument_geometry:
        :param keep_raw_ws:
        :param convert_to_matrix:
        :return: string as reduction message for successful reduction
        """
        def check_binning_parameter_range(x_min, x_max, ws_unit):
            """
            check whether range of X values of binning makes sense with target unit
            :param x_min:
            :param x_max:
            :param ws_unit:
            :return:
            """
            if ws_unit == 'dSpacing' and not 0 < x_min < x_max < 20:
                # dspacing within (0, 20)
                x_range_is_wrong = True
            elif ws_unit == 'TOF' and not 1000 < x_min < x_max < 1000000:
                # TOF within (1000, 1000000)
                x_range_is_wrong = True
            elif ws_unit != 'dSpacing' and ws_unit != 'TOF':
                raise NotImplementedError('Impossible case for unit {}'.format(ws_unit))
            else:
                # good cases
                x_range_is_wrong = False

            if x_range_is_wrong:
                ero_msg = 'For {0}, X range ({1}, {2}) does not make sense' \
                          ''.format(ws_unit, x_min, x_max)
                print ('[ERROR CAUSING CRASH] {}'.format(ero_msg))
                raise RuntimeError(ero_msg)

            return

        # check inputs
        datatypeutility.check_string_variable('Target unit', target_unit, ['TOF', 'dSpacing'])
        datatypeutility.check_dict('Virtual (focused) instrument geometry', virtual_instrument_geometry)

        if binning_params is None:
            # do nothing
            pass
        else:
            datatypeutility.check_tuple('Binning parameters', binning_params)
            if len(binning_params) == 1:
                # it is fine
                pass
            elif len(binning_params) == 3:
                # check against the unit
                check_binning_parameter_range(binning_params[0], binning_params[2], target_unit)
            else:
                # unsupported number of binning parameters
                err_msg = 'Binning parameters {0} with {1} items are not supported.' \
                          ''.format(binning_params, len(binning_params))
                print ('[Crash Error] {}'.format(err_msg))
                raise RuntimeError(err_msg)
        # END-IF-ELSE

        # virtual instrument
        self._diff_focus_params['EditInstrumentGeometry'] = virtual_instrument_geometry

        # align and focus
        red_msg = mantid_reduction.align_and_focus_event_ws(event_ws_name, output_ws_name, binning_params,
                                                            calibration_workspace, mask_workspace, grouping_workspace,
                                                            reduction_params_dict=self._diff_focus_params,
                                                            convert_to_matrix=convert_to_matrix)

        # remove input event workspace
        if output_ws_name != event_ws_name and keep_raw_ws is False:
            # if output name is same as input. no need to do the operation
            mantid_helper.delete_workspace(event_ws_name)

        return red_msg

    def load_vdrive_bins(self, default=False, file_name=None):
        """
        load VDRIVE reference binning file
        :param default: True to load most recent file
        :param file_name:
        :return:
        """
        # get file name
        if default:
            most_recent = self._calibrationFileManager.calibration_dates[-1]
            file_name = self._calibrationFileManager.get_vdrive_binning_reference(most_recent)
        else:
            datatypeutility.check_file_name(file_name, check_exist=True, note='VDRive binning reference file')

        # name
        ref_bin_ws_name = self._calibrationFileManager.vdrive_binning_ref_ws_name(file_name)
        if file_name.endswith('.dat'):
            # NeXus file format
            status, ret_obj = mantid_helper.load_nexus(file_name, ref_bin_ws_name, meta_data_only=False)
            if not status:
                raise RuntimeError('Unable to load VDRIVE reference binning file {} due to {}'
                                   ''.format(file_name, ret_obj))
        elif file_name.endswith('.h5'):
            # load to binning table
            self._calibrationFileManager.create_vdrive_reference(num_banks=3, h5_bin_file_name=file_name)
        else:
            raise RuntimeError('VDRIVE binning reference file {} is not supported. Only .dat and .h5 '
                               'are recognized and supported.'.format(file_name))

        return

    def mask_detectors(self, event_ws_name, mask_file_name, is_roi=False):
        """ Mask detectors and optionally load the mask file for first time
        :param event_ws_name:
        :param mask_file_name:
        :param is_roi:
        :return:
        """
        # check input file
        datatypeutility.check_file_name(mask_file_name, check_exist=True, check_writable=False,
                                        is_dir=False, note='Mask/ROI (Mantiod) XML file')

        if mask_file_name in self._loaded_masks:
            # pre-loaded
            mask_ws_name, is_roi = self._loaded_masks[mask_file_name]
        else:
            # create workspace name
            mask_ws_name = mask_file_name.lower().split('.xml')[0].replace('/', '.')
            # load
            if is_roi:
                mask_ws_name = 'roi.' + mask_ws_name
                mantid_helper.load_roi_xml(event_ws_name, mask_file_name, mask_ws_name)
            else:
                mask_ws_name = 'mask.' + mask_ws_name
                mantid_helper.load_mask_xml(event_ws_name, mask_file_name, mask_ws_name)

            # record
            self._loaded_masks[mask_file_name] = mask_ws_name, is_roi

        # Mask detectors
        mantid_helper.mask_workspace(to_mask_workspace_name=event_ws_name,
                                     mask_workspace_name=mask_ws_name)

        return

    def process_vulcan_ipts_run(self, ipts_number, run_number, event_file, output_directory, merge_banks,
                                vanadium=False,
                                vanadium_tuple=None, gsas=True, standard_sample_tuple=None, binning_parameters=None,
                                num_banks=3):
        """
        Reduce run with selected options
        Purpose:
        Requirements:
        Guarantees:
        :param ipts_number:
        :param run_number:
        :param event_file:
        :param output_directory:
        :param merge_banks:
        :param vanadium:
        :param vanadium_tuple:
        :param gsas:
        :param standard_sample_tuple:
        :param binning_parameters:
        :param num_banks: number of banks focused to.  Now only 3, 7 and 27 are allowed.

        :return:
        """
        # set up reduction options
        reduction_setup = reduce_VULCAN.ReductionSetup()

        # run number, ipts and etc
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(event_file)
        reduction_setup.set_ipts_number(ipts_number)
        reduction_setup.set_banks_to_merge(merge_banks)
        reduction_setup.set_default_calibration_files(num_focused_banks=num_banks)

        # parse binning parameters
        if binning_parameters is not None:
            if len(binning_parameters) == 3:
                tof_min, bin_size, tof_max = binning_parameters
            elif len(binning_parameters) == 1:
                bin_size = binning_parameters[0]
                tof_min = 3000.
                tof_max = 70000.
            else:
                raise RuntimeError('Binning parameters {0} must have 3 parameters.'
                                   ''.format(binning_parameters))
            reduction_setup.set_binning_parameters(tof_min, bin_size, tof_max)
            reduction_setup.set_align_vdrive_bin(False)
        else:
            reduction_setup.set_align_vdrive_bin(True)
        # END-IF

        # vanadium
        reduction_setup.normalized_by_vanadium = vanadium
        if vanadium:
            assert isinstance(vanadium_tuple, tuple) and len(vanadium_tuple) == 3,\
                'Input vanadium-tuple must be a tuple with length 3.'
            van_run, van_gda, vanadium_tag = vanadium_tuple
            reduction_setup.set_vanadium(van_run, van_gda, vanadium_tag)

        # outputs
        if output_directory is not None:
            reduction_setup.set_output_dir(output_directory)
            if gsas:
                reduction_setup.set_gsas_dir(output_directory, True)

        # process on standards
        if standard_sample_tuple:
            assert isinstance(standard_sample_tuple, tuple) and len(standard_sample_tuple) == 3,\
                'Input standard sample-tuple must be a tuple with length 3 but not a {0}.'.format(standard_sample_tuple)
            standard_sample, standard_dir, standard_record_file = standard_sample_tuple
            reduction_setup.is_standard = True
            reduction_setup.set_standard_sample(standard_sample, standard_dir, standard_record_file)
        # END-IF (standard sample tuple)

        # reduce
        reduction_setup.is_auto_reduction_service = False
        reducer = reduce_VULCAN.ReduceVulcanData(reduction_setup)
        # TODO/TODO/NOW/NOW - This shall be re-writen???
        reduce_good, message = reducer.execute_vulcan_reduction(output_logs=False)

        # record reduction tracker
        if reduce_good:
            self.init_tracker(ipts_number, run_number)

            if vanadium:
                self._reductionTrackDict[run_number].is_corrected_by_vanadium = True

            # set reduced files
            self._reductionTrackDict[run_number].set_reduced_files(reducer.get_reduced_files(), append=False)
            # set workspaces
            status, ret_obj = reducer.get_reduced_workspaces(chopped=False)
            if status:
                # it may not have the workspace because
                vdrive_ws, tof_ws, d_ws = ret_obj
                self.set_reduced_workspaces(run_number, vdrive_ws, tof_ws, d_ws)

        # END-IF

        return reduce_good, message

    # TODO | Code Quality - 20180713 - Find out how to reuse codes from vulcan_slice_reduce.SliceFocusVulcan
    def reduce_event_nexus(self, ipts_number, run_number, event_nexus_name, target_unit, binning_parameters,
                           convert_to_matrix, num_banks, roi_list, mask_list):
        """
        reduce event workspace including load and diffraction focus
        :param run_number:
        :param event_nexus_name:
        :param target_unit:
        :param binning_parameters:
        :param convert_to_matrix:
        :param num_banks:
        :param roi_list:
        :param mask_list:
        :return:
        """
        # Load data
        event_ws_name = self.get_event_workspace_name(run_number=run_number)
        mantid_helper.load_nexus(event_nexus_name, event_ws_name, meta_data_only=False)
        print ('[DB...INFO] Successfully loaded {0} to {1}'.format(event_nexus_name, event_ws_name))

        # Mask data
        datatypeutility.check_list('Region of interest file list', roi_list)
        datatypeutility.check_list('Mask file list', mask_list)
        for roi_file_name in roi_list:
            self.mask_detectors(event_ws_name, roi_file_name, is_roi=True)
        for mask_file_name in mask_list:
            self.mask_detectors(event_ws_name, mask_file_name, is_roi=False)

        # get start time: it is not convenient to get date/year/month from datetime64.
        # use the simple but fragile method first
        run_start_time = mantid_helper.get_run_start(event_ws_name, time_unit=None)
        if run_start_time.__class__.__name__.count('DateAndTime') == 1:
            run_start_date = str(run_start_time).split('T')[0]
        else:
            err_msg = 'Run start time from Mantid TSP is not DateAndTime anymore, but is {0}' \
                      ''.format(run_start_time.__class__.__name__)
            print ('[RAISING ERROR] {0}'.format(err_msg))
            raise NotImplementedError(err_msg)

        # check (and load as an option) calibration file
        has_loaded_cal = self._calibrationFileManager.has_loaded(run_start_date, num_banks)
        if not has_loaded_cal:
            self._calibrationFileManager.search_load_calibration_file(run_start_date, num_banks, event_ws_name)
        workspaces = self._calibrationFileManager.get_loaded_calibration_workspaces(run_start_date, num_banks)
        calib_ws_name = workspaces.calibration
        group_ws_name = workspaces.grouping
        mask_ws_name = workspaces.mask

        # set tracker
        tracker = self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=None)
        tracker.is_reduced = False

        # diffraction focus
        virtual_geometry_dict = self._calibrationFileManager.get_focused_instrument_parameters(num_banks)
        red_message = self.diffraction_focus_workspace(event_ws_name, event_ws_name,
                                                       binning_params=binning_parameters,
                                                       target_unit=target_unit,
                                                       calibration_workspace=calib_ws_name,
                                                       mask_workspace=mask_ws_name,
                                                       grouping_workspace=group_ws_name,
                                                       virtual_instrument_geometry=virtual_geometry_dict,
                                                       convert_to_matrix=convert_to_matrix,
                                                       keep_raw_ws=False)

        if target_unit.lower().count('d'):
            tracker.set_reduced_workspaces(vdrive_bin_ws=None, tof_ws=None, dspace_ws=event_ws_name)
        else:
            tracker.set_reduced_workspaces(vdrive_bin_ws=None, tof_ws=event_ws_name, dspace_ws=None)

        # set tracker
        tracker.is_reduced = True

        # END-IF

        return event_ws_name, red_message

    def set_chopped_reduced_workspaces(self, run_number, slicer_key, workspace_name_list, append, compress=False):
        """
        set the chopped and reduced workspaces to reduction manager
        :param run_number:
        :param slicer_key:
        :param workspace_name_list:
        :param append:
        :param compress: if compress, then merge all the 2-bank workspace together   NOTE: using ConjoinWorkspaces???
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)

        # add files
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'
        error_messge = tracker.set_chopped_workspaces(workspace_name_list, append=append)

        if compress:
            target_ws_name = tracker.compressed_ws_name
            mantid_helper.make_compressed_reduced_workspace(workspace_name_list, target_workspace_name=target_ws_name)

        return error_messge

    def set_chopped_reduced_files(self, run_number, slicer_key, gsas_file_list, append):
        """
        set the reduced file
        :param run_number:
        :param slicer_key:
        :param gsas_file_list:
        :param append:
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'

        # add files
        tracker.set_reduced_files(gsas_file_list, append)

        return

    def set_reduced_workspaces(self, run_number, vdrive_bin_ws, tof_ws, dspace_ws):
        """
        set a run's reduced workspaces
        :param run_number: int
        :param vdrive_bin_ws: str
        :param tof_ws: str
        :param dspace_ws: str
        :return:
        """
        # check input
        if run_number not in self._reductionTrackDict:
            raise RuntimeError('Run number {0} has no ReductionTracker yet. Existing keys are {1}.'
                               ''.format(run_number, self._reductionTrackDict.keys()))

        try:
            self._reductionTrackDict[run_number].set_reduced_workspaces(vdrive_bin_ws, tof_ws, dspace_ws)
        except AssertionError as ass_err:
            raise AssertionError('ReductionManage unable to set reduced workspace for run {0} due to {1}.'
                                 ''.format(run_number, ass_err))
        # TRY-EXCEPT

        return


class DetectorCalibrationWorkspaces(object):
    """
    a simple workspace for detector instrument calibration workspaces
    """
    def __init__(self):
        """
        initialization: all workspaces shall be workspace names but not references to workspaces
        """
        self.calibration = None
        self.mask = None
        self.grouping = None

    def __str__(self):
        """
        customized nice output
        :return:
        """
        nice = 'Calibration workspace: {}\nGrouping workspace: {}\nMask workspace: {}' \
               ''.format(self.calibration, self.grouping, self.mask)

        return nice
