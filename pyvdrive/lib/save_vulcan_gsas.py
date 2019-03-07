import datetime
import os
import os.path
import h5py
import math
from pyvdrive.lib import datatypeutility
import mantid_helper
from mantid.simpleapi import ConvertToHistogram, ConvertUnits, Rebin, Divide

PHASE_NED = datetime.datetime(2017, 6, 1)
PHASE_X1 = datetime.datetime(2019, 7, 1)


class SaveVulcanGSS(object):
    """
    class to save VULCAN GSAS
    mostly it is used as static
    """
    def __init__(self, vulcan_ref_name=None):
        """ constructor of GSAS writer for VDRIVE
        :param vulcan_ref_name:
        """
        # set up the default reference file name
        if vulcan_ref_name is None:
            vulcan_ref_name = '/SNS/VULCAN/shared/CALIBRATION/VDRIVE/vdrive_tof_bin.h5'

        datatypeutility.check_file_name(file_name=vulcan_ref_name, check_exist=True,
                                        check_writable=False, is_dir=False,
                                        note='VDRIVE GSAS binning reference file')

        # parse the file
        lower_res_tof_vec, high_res_tof_vec = self._import_tof_ref_file(vulcan_ref_name)

        # convert TOF bin boundaries to Mantid binning parameters
        # key = 'bank type', value = TOF vec, binning parameters
        self._mantid_bin_param_dict = dict()
        # lower resolution: east/west
        self._mantid_bin_param_dict['lower'] = lower_res_tof_vec, self._create_binning_parameters(lower_res_tof_vec)
        # higher resolution: high angle bank
        self._mantid_bin_param_dict['higher'] = high_res_tof_vec, self._create_binning_parameters(high_res_tof_vec)

        # about vanadium
        self._van_ws_names = dict()

        return

    @staticmethod
    def _create_binning_parameters(tof_vector):
        """ Create binning parameters for Mantid::Rebin
        :param
        :return:
        """
        # Create a complicated bin parameter
        bin_params = list()
        xf = None
        dx = None
        x0 = None
        for ibin in range(len(tof_vector) - 1):
            x0 = tof_vector[ibin]
            xf = tof_vector[ibin + 1]
            dx = xf - x0
            bin_params.append(x0)
            bin_params.append(dx)
        # END-FOR

        # check
        if xf is None or dx is None or x0 is None:
            raise RuntimeError('It is impossible to have x0, dx or xf without value set')

        # last bin
        bin_params.append(xf)

        # extend bin
        const_delta_t = dx / x0
        dx = const_delta_t * xf
        bin_params.extend([dx, xf + dx])

        return bin_params

    @staticmethod
    def _calculate_run_start_stop_time(gsas_workspace, from_sliced_ws):
        """

        :param gsas_workspace:
        :param from_sliced_ws:
        :return:
        """
        run = gsas_workspace.getRun()

        # check
        if not ((run.hasProperty("run_start") and run.hasProperty("duration")) or run.hasProperty('proton_charge')):
            raise RuntimeError('Workspace {} must have either (run_start/duration) or proton_charge '
                               'for calculating run start/stop in nanoseconds'.format(gsas_workspace.name()))

        # zero time:
        try:
            time0 = datetime.datetime.strptime("1990-01-01T0:0:0", '%Y-%m-%dT%H:%M:%S')
        except AttributeError as any_error:
            print (any_error)
            time0 = datetime.strptime("1990-01-01T0:0:0", '%Y-%m-%dT%H:%M:%S')

        if run.hasProperty('proton_charge'):
            # use proton charge to calculate run start/stop
            proton_charge_log = run.getProperty('proton_charge')
            pc_start_time = proton_charge_log.times[0]
            pc_stop_time = proton_charge_log.times[-1]

            duration_ns = (pc_stop_time - pc_start_time).astype('int')
            # convert proton charge first time to datetime.datetime
            run_start_time = datetime.datetime.utcfromtimestamp(pc_start_time.astype('O') * 1.E-9)

            delta_to_t0_ns = run_start_time - time0
            total_nanosecond_start = int(delta_to_t0_ns.total_seconds() * int(1.0E9))
            total_nanosecond_stop = total_nanosecond_start + duration_ns
            # print ('[DB...BAT...CHECK...Method 2] Run start/stop = {}, {}'.format(total_nanosecond_start,
            #                                                                       total_nanosecond_stop))

        elif from_sliced_ws:
            # if workspace is from sliced event, then proton_charge is required
            raise RuntimeError('proton_charge log is required if the GSAS workspace is reduced from '
                               'a sliced EventWorkspace.')

        elif run.hasProperty("run_start") and run.hasProperty("duration"):
            # export processing time information
            runstart = run.getProperty("run_start").value
            duration = float(run.getProperty("duration").value)
            # property run_start and duration exist
            runstart_sec = runstart.split(".")[0]
            runstart_ns = runstart.split(".")[1]
            try:
                utctime = datetime.datetime.strptime(runstart_sec, '%Y-%m-%dT%H:%M:%S')
                time0 = datetime.datetime.strptime("1990-01-01T0:0:0", '%Y-%m-%dT%H:%M:%S')
                print ('UTC time: {}, Time 0: {}'.format(str(utctime), str(time0)))
            except AttributeError as attrib_error:
                print ('[DB...BAT] run start sec = {}'.format(str(runstart_sec)))
                raise RuntimeError('Unable to convert run start {} to UTC time due to {}'
                                   ''.format(runstart_sec, attrib_error))

            delta = utctime - time0
            try:
                total_nanosecond_start = int(delta.total_seconds() * int(1.0E9)) + int(runstart_ns)
            except AttributeError:
                total_seconds = delta.days * 24 * 3600 + delta.seconds
                total_nanosecond_start = total_seconds * int(1.0E9) + int(runstart_ns)
            total_nanosecond_stop = total_nanosecond_start + int(duration * 1.0E9)
            print ('[DB...BAT...CHECK...Method 1] Run start/stop = {}, {}'.format(total_nanosecond_start,
                                                                                  total_nanosecond_stop))
        else:
            # no sample logs for start and stop
            raise RuntimeError('There is no sample log (proton_charge, run_start/duration) existing '
                               'to support calculating start and stop time.')

        return total_nanosecond_start, total_nanosecond_stop

    def _generate_vulcan_gda_header(self, gsas_workspace, gsas_file_name, ipts, run_number,
                                    gsas_param_file_name, from_sliced_ws):
        """
        generate a VDRIVE compatible GSAS file's header
        :param gsas_workspace:
        :param gsas_file_name:
        :param ipts:
        :param run_number
        :param gsas_param_file_name:
        :param from_sliced_ws: flag to indicate whether the GSAS workspace is from sliced
        :return: string : multiple lines
        """
        # check
        assert isinstance(gsas_workspace, str) is False, 'GSAS workspace must not be a string.'
        datatypeutility.check_string_variable('(Output) GSAS file name', gsas_file_name)
        datatypeutility.check_string_variable('GSAS IParam file name', gsas_param_file_name)
        assert isinstance(ipts, int) or isinstance(ipts, str), 'IPTS number {0} must be either string or integer.' \
                                                               ''.format(ipts)
        if isinstance(ipts, str):
            assert ipts.isdigit(), 'IPTS {0} must be convertible to an integer.'.format(ipts)

        # Get necessary information
        title = gsas_workspace.getTitle()

        # Get information on start/stop
        total_nanosecond_start, total_nanosecond_stop = self._calculate_run_start_stop_time(gsas_workspace,
                                                                                            from_sliced_ws)

        # Construct new header
        new_header = ""

        if len(title) > 80:
            title = title[0:80]
        new_header += "%-80s\n" % title
        new_header += "%-80s\n" % ("Instrument parameter file: %s" % gsas_param_file_name)
        new_header += "%-80s\n" % ("#IPTS: %s" % str(ipts))
        if run_number is not None:
            new_header += "%-80s\n" % ("#RUN: %s" % str(run_number))
        new_header += "%-80s\n" % ("#binned by: Mantid. From refrence workspace: {})".format(str(gsas_workspace)))
        new_header += "%-80s\n" % ("#GSAS file name: %s" % os.path.basename(gsas_file_name))
        new_header += "%-80s\n" % ("#GSAS IPARM file: %s" % gsas_param_file_name)
        new_header += "%-80s\n" % ("#Pulsestart:    %d" % total_nanosecond_start)
        new_header += "%-80s\n" % ("#Pulsestop:     %d" % total_nanosecond_stop)
        new_header += '%-80s\n' % '#'

        return new_header

    def _get_tof_bin_params(self, phase, num_banks):
        """
        get VDRIVE reference TOF file name
        :param num_banks:
        :return: list of tuple:  [bank ids (from 1)], binning parameters, tof vector
        """
        bank_tof_sets = list()

        if phase == 'prened':
            lower_tof_vec, lower_binning_params = self._mantid_bin_param_dict['lower']

            if num_banks == 1:
                # east and west together
                bank_tof_sets.append(([1], lower_binning_params, lower_tof_vec))
            elif num_banks == 2:
                # east and west bank separate
                bank_tof_sets.append(([1, 2], lower_binning_params, lower_tof_vec))
            else:
                raise RuntimeError('Pre-nED VULCAN does not allow {}-bank case. Contact developer ASAP '
                                   'if this case is really needed.'.format(num_banks))

        elif phase == 'ned':
            # nED but pre-vulcan-X

            lower_tof_vec, lower_binning_params = self._mantid_bin_param_dict['lower']
            higher_tof_vec, higher_binnig_params = self._mantid_bin_param_dict['higher']

            if num_banks == 2:
                # merge west and east (as bank 1) but leave high angle alone
                bank_tof_sets.append(([1], lower_binning_params, lower_tof_vec))
                bank_tof_sets.append(([2], higher_binnig_params, higher_tof_vec))

            elif num_banks == 3:
                # west(1), east(1), high(1)
                bank_tof_sets.append(([1, 2], lower_binning_params, lower_tof_vec))
                bank_tof_sets.append(([3], higher_binnig_params, higher_tof_vec))

            elif num_banks == 7:
                # west (3), east (3), high (1)
                bank_tof_sets.append((range(1, 7), lower_binning_params, lower_tof_vec))
                bank_tof_sets.append(([7], higher_binnig_params, higher_tof_vec))

            elif num_banks == 27:
                # west (9), east (9), high (9)
                bank_tof_sets.append((range(1, 19), lower_binning_params, lower_tof_vec))
                bank_tof_sets.append((range(19, 28), higher_binnig_params, higher_tof_vec))

            else:
                raise RuntimeError('nED VULCAN does not allow {}-bank case. Contact developer ASAP '
                                   'if this case is really needed.'.format(num_banks))
            # END-IF-ELSE
        else:
            raise RuntimeError('VULCAN at phase {} is not supported!'.format(phase))
        # END-IF-ELSE

        return bank_tof_sets

    @staticmethod
    def _get_vulcan_phase(run_date_time):
        """
        get the Phase (prened, ned, vulcanx1, vulcanx) of VULCAN
        :param run_date_time: datetime instance
        :return:
        """
        assert isinstance(run_date_time,datetime.datetime), 'Run date {} must be a datetime.datetime instance ' \
                                                    'but not of type {}'.format(run_date_time,
                                                                                type(run_date_time))

        if run_date_time < PHASE_NED:
            vulcan_phase = 'prened'
        elif run_date_time < PHASE_X1:
            vulcan_phase = 'ned'
        else:
            vulcan_phase = 'vulcanx1'

        return vulcan_phase

    @staticmethod
    def _import_tof_ref_file(tof_reference_h5):
        """ Import TOF reference file for vectors
        :param tof_reference_h5:
        :return: 2-tuple as 2 vectors for reference TOF bins
        """
        # load vdrive bin file to 2 different workspaces
        bin_file = h5py.File(tof_reference_h5, 'r')
        west_east_bins = bin_file['west_east_bank'][:]
        high_angle_bins = bin_file['high_angle_bank'][:]
        bin_file.close()

        return west_east_bins, high_angle_bins

    @staticmethod
    def _cal_l1(matrix_workspace):
        """ Get L1
        :param matrix_workspace:
        :return:
        """
        source_pos = matrix_workspace.getInstrument().getSource().getPos()
        sample_pos = matrix_workspace.getInstrument().getSample().getPos()

        l1 = math.sqrt((source_pos.X() - sample_pos.X())**2 +
                       (source_pos.Y() - sample_pos.Y())**2 +
                       (source_pos.Z() - sample_pos.Z())**2)

        return l1

    @staticmethod
    def _cal_2theta_l2(matrix_workspace, ws_index):
        """
        calculate L2 and two theta
        :param matrix_workspace:
        :param ws_index:
        :return: tuple (L2, 2theta in arcs)
        """
        source_pos = matrix_workspace.getInstrument().getSource().getPos()
        sample_pos = matrix_workspace.getInstrument().getSample().getPos()
        det_pos = matrix_workspace.getDetector(ws_index).getPos()

        # calculate in and out K and then 2theta
        k_in = sample_pos - source_pos
        k_out = det_pos - sample_pos
        two_theta_arc = k_out.angle(k_in)

        # calculate L2
        l2 = det_pos.distance(sample_pos)

        return l2, two_theta_arc

    @staticmethod
    def _cal_difc(l1, l2, two_theta_arc):
        """
        calculate DIFC
        :param l1:
        :param l2:
        :param two_theta_arc:
        :return:
        """
        neutron_mass = 1.674927211e-27
        constant_h = 6.62606896e-34
        difc = (2.0 * neutron_mass * math.sin(two_theta_arc * 0.5) * (l1 + l2)) / (constant_h * 1.e4)

        return difc

    def _get_2theta_difc(self, matrix_workspace, l1, ws_index):
        """
        get the DIFC
        :param matrix_workspace:
        :param l1:
        :param ws_index:
        :return:
        """
        l2, two_theta = self._cal_2theta_l2(matrix_workspace, ws_index)

        difc = self._cal_difc(l1, l2, two_theta)

        return two_theta * 180. / math.pi, difc

    def _write_slog_bank_gsas(self, ws_name, bank_id, vulcan_tof_vector, van_ws):
        """
        1. X: format to VDRIVE tradition (refer to ...)
        2. Y: native value
        3. Z: error bar
        :param ws_name:
        :param bank_id:
        :param vulcan_tof_vector: If None, then use vector X of workspace
        :param ...
        :return:
        """
        # check vanadium: if not None, assume that number of bins and bin edges are correct
        if van_ws is not None:
            if van_ws.id() == 'WorkspaceGroup':
                van_vec_y = van_ws[bank_id-1].readY(0)
                van_vec_e = van_ws[bank_id-1].readE(0)
            else:
                van_vec_y = van_ws.readY(bank_id - 1)
                van_vec_e = van_ws.readE(bank_id - 1)
        else:
            van_vec_y = None
            van_vec_e = None

        # get workspace
        diff_ws = mantid_helper.retrieve_workspace(ws_name)
        if vulcan_tof_vector is None:
            vec_x = diff_ws.readX(bank_id - 1)
        else:
            vec_x = vulcan_tof_vector
        vec_y = diff_ws.readY(bank_id - 1)  # convert to workspace index
        vec_e = diff_ws.readE(bank_id - 1)
        data_size = len(vec_y)

        # get geometry information
        l1 = self._cal_l1(diff_ws)
        two_theta, difc = self._get_2theta_difc(diff_ws, l1, bank_id-1)

        bank_buffer = ''

        # write the virtual detector geometry information
        # Example:
        # Total flight path 45.754m, tth 90deg, DIFC 16356.3
        # Data for spectrum :0
        bank_buffer += '%-80s\n' % '# Total flight path {}m, tth {}deg, DIFC {}'.format(l1, two_theta, difc)
        bank_buffer += '%-80s\n' % '# Data for spectrum :{}'.format(bank_id - 1)

        # ws.getInstrument().getSource().getPos()
        # ws.getDetector(2).getPos(): Out[15]: [0.845237,0,-1.81262]
        # math.sqrt(0.845237**2 + 1.81262**2)
        # 2theta = acos(v1 dot v2 / abs(v1) / abs(v2)

        # bank header: min TOF, max TOF, delta TOF
        bc1 = '%.1f' % (vec_x[0])
        bc2 = '%.1f' % (vec_x[-1])
        bc3 = '%.7f' % ((vec_x[1] - vec_x[0])/vec_x[0])
        # check
        if bc1 < 0:
            raise RuntimeError('Cannot write out logarithmic data starting at zero or less')

        bank_header = 'BANK %d %d %d %s %s %s %s 0 FXYE' % (bank_id, data_size, data_size, 'SLOG', bc1, bc2, bc3)
        bank_buffer += '%-80s\n' % bank_header

        # write lines: not multiplied by bin width
        if van_vec_y is None:
            for index in range(data_size):
                x_i = '%.1f' % vec_x[index]
                y_i = '%.1f' % vec_y[index]
                e_i = '%.2f' % vec_e[index]
                data_line_i = '%12s%12s%12s' % (x_i, y_i, e_i)
                bank_buffer += '%-80s\n' % data_line_i
            # END-FOR
        else:
            # normalize by vanadium
            for index in range(data_size):
                x_i = '%.1f' % vec_x[index]
                y_i = '%.5f' % (vec_y[index] / van_vec_y[index])
                if vec_y[index] < 1.E-10:
                    alpha = 1.
                else:
                    alpha = vec_e[index] / vec_y[index]
                beta = van_vec_e[index] / van_vec_y[index]
                e_i = '%.5f' % (abs(vec_y[index]/van_vec_y[index]) * math.sqrt(alpha**2 + beta**2))
                data_line_i = '%12s%12s%12s' % (x_i, y_i, e_i)
                bank_buffer += '%-80s\n' % data_line_i
            # END-FOR

        return bank_buffer

    def import_vanadium(self, vanadium_gsas_file):
        """
        Import vanadium GSAS file for normalization
        :param vanadium_gsas_file:
        :return:
        """
        # NOTE (algorithm) use hash to determine the workspace name from file location
        base_name = os.path.basename(vanadium_gsas_file).split('.')[0]
        van_gsas_ws_name = 'Van_{}_{}'.format(base_name, hash(vanadium_gsas_file))
        if mantid_helper.workspace_does_exist(van_gsas_ws_name):
            pass
        else:
            mantid_helper.load_gsas_file(vanadium_gsas_file, van_gsas_ws_name, None)
            mantid_helper.convert_to_point_data(van_gsas_ws_name)
        self._van_ws_names[vanadium_gsas_file] = van_gsas_ws_name

        return van_gsas_ws_name

    def save_vanadium(self, diff_ws_name, gsas_file_name,
                      ipts_number, van_run_number, sample_log_ws_name):
        """  Save a WorkspaceGroup which comes from original GSAS workspace
        :param diff_ws_name: diffraction workspace (group) name
        :param gsas_file_name: output GSAS file name
        :param ipts_number: ITPS
        :param van_run_number: (van) run number
        :param sample_log_ws_name: workspace containing sample logs (proton charges)
        :return:
        """
        datatypeutility.check_string_variable('Diffraction workspace (group) name', diff_ws_name)
        datatypeutility.check_file_name(gsas_file_name, False, True, False, 'Smoothed vanadium GSAS file')
        datatypeutility.check_int_variable('IPTS', ipts_number, (1, None))
        datatypeutility.check_string_variable('Sample log workspace name', sample_log_ws_name)

        # rebin and then write output
        gsas_bank_buffer_dict = dict()
        van_ws = mantid_helper.retrieve_workspace(diff_ws_name)
        num_banks = mantid_helper.get_number_spectra(van_ws)
        datatypeutility.check_file_name(gsas_file_name, check_exist=False,
                                        check_writable=True, is_dir=False, note='Output GSAS file')

        # TODO - TONIGHT 5 - This will break if input is a Workspace but not GroupingWorkspace!!!
        for ws_index in range(num_banks):
            # get value
            bank_id = ws_index + 1
            # write GSAS head considering vanadium
            tof_vector = None
            ws_name_i = van_ws[ws_index].name()
            gsas_section_i = self._write_slog_bank_gsas(ws_name_i, 1, tof_vector, None)
            gsas_bank_buffer_dict[bank_id] = gsas_section_i
        # END-FOR

        # header
        log_ws = mantid_helper.retrieve_workspace(sample_log_ws_name)
        gsas_header = self._generate_vulcan_gda_header(log_ws, gsas_file_name, ipts_number, van_run_number,
                                                       gsas_file_name, False)

        # form to a big string
        gsas_buffer = gsas_header
        for bank_id in sorted(gsas_bank_buffer_dict.keys()):
            gsas_buffer += gsas_bank_buffer_dict[bank_id]

        # write to HDD
        g_file = open(gsas_file_name, 'w')
        g_file.write(gsas_buffer)
        g_file.close()

        return

    def save(self, diff_ws_name, run_date_time, gsas_file_name, ipts_number, run_number, gsas_param_file_name,
             align_vdrive_bin, van_ws_name, is_chopped_run, write_to_file=True):
        """
        Save a workspace to a GSAS file or a string
        :param diff_ws_name: diffraction data workspace
        :param run_date_time: date and time of the run
        :param gsas_file_name: output file name. None as not output
        :param ipts_number:
        :param run_number: if not None, run number
        :param gsas_param_file_name:
        :param align_vdrive_bin: Flag to align with VDRIVE bin edges/boundaries
        :param van_ws_name: name of vanadium workspaces loaded from GSAS (replacing vanadium_gsas_file)
        :param is_chopped_run: Flag such that the input workspaces is from an event-sliced workspace
        :param write_to_file: flag to write the text buffer to file
        :return: string as the file content
        """
        diff_ws = mantid_helper.retrieve_workspace(diff_ws_name)

        # set the unit to TOF
        if diff_ws.getAxis(0).getUnit() != 'TOF':
            ConvertUnits(InputWorkspace=diff_ws_name, OutputWorkspace=diff_ws_name, Target='TOF',
                         EMode='Elastic')
            diff_ws = mantid_helper.retrieve_workspace(diff_ws_name)

        # convert to Histogram Data
        if not diff_ws.isHistogramData():
            ConvertToHistogram(diff_ws_name, diff_ws_name)

        # get the binning parameters
        if align_vdrive_bin:
            bin_params_set = self._get_tof_bin_params(self._get_vulcan_phase(run_date_time),
                                                      diff_ws.getNumberHistograms())
        else:
            # a binning parameter set for doing nothing
            bin_params_set = [(range(1, diff_ws.getNumberHistograms()+1), None, None)]

        # check for vanadium GSAS file name
        if van_ws_name is not None:
            # check whether a workspace exists
            if not mantid_helper.workspace_does_exist(van_ws_name):
                raise RuntimeError('Vanadium workspace {} does not exist in Mantid ADS'.format(van_ws_name))
            van_ws = mantid_helper.retrieve_workspace(van_ws_name)

            # check number of histograms
            if mantid_helper.get_number_spectra(van_ws) != mantid_helper.get_number_spectra(diff_ws):
                raise RuntimeError('Numbers of histograms between vanadium spectra and output GSAS are different')
        else:
            van_ws = None
        # END-IF

        # rebin and then write output
        gsas_bank_buffer_dict = dict()
        num_bank_sets = len(bin_params_set)

        for bank_set_index in range(num_bank_sets):
            # get value
            bank_id_list, bin_params, tof_vector = bin_params_set[bank_set_index]

            # Rebin to these banks' parameters (output = Histogram)
            if bin_params is not None:
                Rebin(InputWorkspace=diff_ws_name, OutputWorkspace=diff_ws_name,
                      Params=bin_params, PreserveEvents=True)

            # Create output
            for bank_id in bank_id_list:
                # check vanadium bin edges
                if van_ws is not None:
                    # check whether the bins are same between GSAS workspace and vanadium workspace
                    unmatched, reason = self._compare_workspaces_dimension(van_ws, bank_id, tof_vector)
                    if unmatched:
                        raise RuntimeError('Vanadium GSAS workspace {} does not match workspace {}: {}'
                                           ''.format(van_ws_name, diff_ws_name, reason))
                # END-IF

                # write GSAS head considering vanadium
                gsas_section_i = self._write_slog_bank_gsas(diff_ws_name, bank_id, tof_vector, van_ws)
                gsas_bank_buffer_dict[bank_id] = gsas_section_i
        # END-FOR

        # header
        diff_ws = mantid_helper.retrieve_workspace(diff_ws_name)
        gsas_header = self._generate_vulcan_gda_header(diff_ws, gsas_file_name, ipts_number, run_number,
                                                       gsas_param_file_name, is_chopped_run)

        # form to a big string
        gsas_buffer = gsas_header
        for bank_id in sorted(gsas_bank_buffer_dict.keys()):
            gsas_buffer += gsas_bank_buffer_dict[bank_id]

        # write to HDD
        if write_to_file:
            datatypeutility.check_file_name(gsas_file_name, check_exist=False,
                                            check_writable=True, is_dir=False, note='Output GSAS file')
            g_file = open(gsas_file_name, 'w')
            g_file.write(gsas_buffer)
            g_file.close()
        else:
            pass

        return gsas_buffer

    @staticmethod
    def _normalize_by_vanadium(diff_ws, van_ws, diff_ws_name):
        """ Normalize by vanadium
        :param van_ws:
        :param diff_ws_name:
        :return:
        """
        Divide(LHSWorkspace=diff_ws,
                   RHSWorkspace=van_ws,
                   OutputWorkspace=diff_ws_name)
        diff_ws = mantid_helper.retrieve_workspace(diff_ws_name)

        return diff_ws

    @staticmethod
    def _compare_workspaces_dimension(van_ws, bank_id, diff_tof_vec):
        """
        compare the workspace dimensions between vanadium workspace and diffraction TOF vector
        :param van_ws:
        :param bank_id:
        :param diff_tof_vec:
        :return: Being different (bool), Reason (str)
        """
        iws = bank_id - 1
        if van_ws.id() == 'WorkspaceGroup':
            van_vec_x = van_ws[iws].readX(0)
        else:
            van_vec_x = van_ws.readX(iws)
        diff_vec_x = diff_tof_vec
        if len(van_vec_x) != len(diff_vec_x):
            return True, 'Numbers of bins are different between vanadium workspace {} ws-index {}' \
                         ' and diffraction pattern: {}  != {}'.format(van_ws, iws, len(van_vec_x), len(diff_tof_vec))

        if abs(van_vec_x[0] - diff_vec_x[0]) / (van_vec_x[0]) > 1.E-5:
            # return True, 'X[0] are different for spectrum {}: {} != {}'.format(iws, van_vec_x[0], diff_vec_x[0])
            print ('X[0] are different for spectrum {}: {} != {}'.format(iws, van_vec_x[0], diff_vec_x[0]))
        if abs(van_vec_x[-1] - diff_vec_x[-1]) / (van_vec_x[-1]) > 1.E-5:
            # return True, 'X[-1] are different for spectrum {}; {} != {}'.format(iws, van_vec_x[-1], diff_vec_x[-1])
            print ('X[-1] are different for spectrum {}; {} != {}'.format(iws, van_vec_x[-1], diff_vec_x[-1]))
        # END-IF-ELSE

        return False, None

# END-DEF-CLASS
