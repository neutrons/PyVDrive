from datetime import datetime
import os
import os.path
import h5py
import numpy
import mantid.simpleapi as api
from mantid.api import AnalysisDataService as ADS
from pyvdrive.lib import datatypeutility


PHASE_NED = datetime(2017, 6, 1)
PHASE_X1 = datetime(2019, 7, 1)


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
        self._mantid_bin_param_dict = dict()
        # lower resolution: east/west
        self._mantid_bin_param_dict['lower'] = lower_res_tof_vec, self._create_binning_parameters(lower_res_tof_vec)
        # higher resolution: high angle bank
        self._mantid_bin_param_dict['higher'] = high_res_tof_vec, self._create_binning_parameters(high_res_tof_vec)

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
    def _generate_vulcan_gda_header(gsas_workspace, gsas_file_name, ipts, gsas_param_file_name):
        """
        generate a VDRIVE compatible GSAS file's header
        :param gsas_workspace:
        :param gsas_file_name:
        :param ipts:
        :param gsas_param_file_name:
        :return: string : multiple lines
        """
        # check
        assert isinstance(gsas_workspace, str) is False, 'GSAS workspace must not be a string.'
        assert isinstance(gsas_file_name, str), 'GSAS file name {0} must be a string.'.format(gsas_file_name)
        assert isinstance(ipts, int) or isinstance(ipts, str), 'IPTS number {0} must be either string or integer.' \
                                                               ''.format(ipts)
        assert isinstance(gsas_param_file_name, str), 'GSAS iparm file name {0} must be an integer.' \
                                                      ''.format(gsas_param_file_name)
        if isinstance(ipts, str):
            assert ipts.isdigit(), 'IPTS {0} must be convertible to an integer.'.format(ipts)

        # Get necessary information
        title = gsas_workspace.getTitle()
        run = gsas_workspace.getRun()

        # Get information on start/stop
        if run.hasProperty("run_start") and run.hasProperty("duration"):
            # export processing time information
            runstart = run.getProperty("run_start").value
            duration = float(run.getProperty("duration").value)
            # property run_start and duration exist
            runstart_sec = runstart.split(".")[0]
            runstart_ns = runstart.split(".")[1]

            utctime = datetime.strptime(runstart_sec, '%Y-%m-%dT%H:%M:%S')
            time0 = datetime.strptime("1990-01-01T0:0:0", '%Y-%m-%dT%H:%M:%S')

            delta = utctime - time0
            try:
                total_nanosecond_start = int(delta.total_seconds() * int(1.0E9)) + int(runstart_ns)
            except AttributeError:
                total_seconds = delta.days * 24 * 3600 + delta.seconds
                total_nanosecond_start = total_seconds * int(1.0E9) + int(runstart_ns)
            total_nanosecond_stop = total_nanosecond_start + int(duration * 1.0E9)
        else:
            # not both property is found
            total_nanosecond_start = 0
            total_nanosecond_stop = 0

        # Construct new header
        newheader = ""

        if len(title) > 80:
            title = title[0:80]
        newheader += "%-80s\n" % title

        newheader += "%-80s\n" % ("Instrument parameter file: %s" % gsas_param_file_name)

        newheader += "%-80s\n" % ("#IPTS: %s" % str(ipts))

        newheader += "%-80s\n" % "#binned by: Mantid"

        newheader += "%-80s\n" % ("#GSAS file name: %s" % os.path.basename(gsas_file_name))

        newheader += "%-80s\n" % ("#GSAS IPARM file: %s" % gsas_param_file_name)

        newheader += "%-80s\n" % ("#Pulsestart:    %d" % total_nanosecond_start)

        newheader += "%-80s\n" % ("#Pulsestop:     %d" % total_nanosecond_stop)

        return newheader

    def _get_tof_bin_params(self, phase, num_banks):
        """
        get VDRIVE reference TOF file name
        :param num_banks:
        :return:
        """
        binning_parameter_dict = dict()
        bank_tof_sets = list()

        if phase == 'prened':
            if num_banks == 1:
                # east and west together
                binning_parameter_dict[1] = self._mantid_bin_param_dict['lower']
                bank_tof_sets.append(([1],
                                      self._mantid_bin_param_dict['lower'][0],
                                      self._mantid_bin_param_dict['lower'][1]))
            elif num_banks == 2:
                # east and west bank separate
                binning_parameter_dict[1] = self._mantid_bin_param_dict['lower'][1]
                binning_parameter_dict[2] = self._mantid_bin_param_dict['lower'][1]
                bank_tof_sets.append(([1, 2],
                                      self._mantid_bin_param_dict['lower'][0],
                                      self._mantid_bin_param_dict['lower'][1]))
            else:
                raise RuntimeError('Pre-nED VULCAN does not allow {}-bank case. Contact developer ASAP '
                                   'if this case is really needed.'.format(num_banks))

        elif phase == 'ned':
            # nED but pre-vulcan-X
            if num_banks == 3:
                # west(1), east(1), high(1)
                for bank_id in range(1, 3):
                    binning_parameter_dict[bank_id] = self._mantid_bin_param_dict['lower'][1]
                binning_parameter_dict[3] = self._mantid_bin_param_dict['higher'][1]

                bank_tof_sets.append(([1, 2], self._mantid_bin_param_dict['lower'][0],
                                      self._mantid_bin_param_dict['lower'][1]))
                bank_tof_sets.append(([3], self._mantid_bin_param_dict['higher'][0],
                                      self._mantid_bin_param_dict['higher'][1]))

            elif num_banks == 7:
                # west (3), east (3), high (1)
                for bank_id in range(1, 7):
                    binning_parameter_dict[bank_id] = self._mantid_bin_param_dict['lower']
                binning_parameter_dict[7] = self._mantid_bin_param_dict['higher']

                bank_tof_sets.append((range(1, 7), self._mantid_bin_param_dict['lower']))
                bank_tof_sets.append(([7], self._mantid_bin_param_dict['higher']))

            elif num_banks == 27:
                # west (9), east (9), high (9)
                for bank_id in range(1, 19):
                    binning_parameter_dict[bank_id] = self._mantid_bin_param_dict['lower']
                for bank_id in range(19, 28):
                    binning_parameter_dict[bank_id] = self._mantid_bin_param_dict['higher']

                bank_tof_sets.append((range(1, 19), self._mantid_bin_param_dict['lower']))
                bank_tof_sets.append((range(19, 28), self._mantid_bin_param_dict['higher']))

            else:
                raise RuntimeError('nED VULCAN does not allow {}-bank case. Contact developer ASAP '
                                   'if this case is really needed.'.format(num_banks))
            # END-IF-ELSE
        else:
            raise RuntimeError('VULCAN at phase {} is not supported!'.format(phase))
        # END-IF-ELSE

        return binning_parameter_dict, bank_tof_sets

    @staticmethod
    def _get_vulcan_phase(run_date_time):
        """
        get the Phase (prened, ned, vulcanx1, vulcanx) of VULCAN
        :param run_date_time: datetime instance
        :return:
        """
        assert isinstance(run_date_time, datetime), 'Run date {} must be a datetime.datetime instance ' \
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
    def _write_slog_bank_gsas(ws_name, bank_id, vulcan_tof_vector):
        """
        1. X: format to VDRIVE tradition (refer to ...)
        2. Y: native value
        3. Z: error bar
        :param ws_name:
        :param bank_id:
        :return:
        """
        # get workspace
        diff_ws = ADS.retrieve(ws_name)
        vec_x = vulcan_tof_vector
        vec_y = diff_ws.readY(bank_id - 1)
        vec_e = diff_ws.readE(bank_id - 1)
        data_size = len(vec_y)

        bank_buffer = ''

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
        for index in range(data_size):
            x_i = '%.1f' % vec_x[index]
            y_i = '%.1f' % vec_y[index]
            e_i = '%.2f' % vec_e[index]
            data_line_i = '%12s%12s%12s' % (x_i, y_i, e_i)
            bank_buffer += '%-80s\n' % data_line_i
        # END-FOR

        return bank_buffer

    def save(self, diff_ws_name, run_date_time, gsas_file_name, ipts_number, gsas_param_file_name):
        """
        Save a workspace to a GSAS file or a string
        :param diff_ws_name: diffraction data workspace
        :param run_date_time: date and time of the run
        :param gsas_file_name: output file name. None as not output
        :param ipts_number:
        :param gsas_param_file_name:
        :return: string as the file content
        """
        diff_ws = ADS.retrieve(diff_ws_name)

        # convert to Histogram Data
        if not diff_ws.isHistogramData():
            api.ConvertToHistogram(diff_ws_name, diff_ws_name)

        # get the binning parameters
        bin_param_dict, bin_params_set = self._get_tof_bin_params(self._get_vulcan_phase(run_date_time),
                                                                  diff_ws.getNumberHistograms())

        # rebin and then write output
        gsas_buffer_dict = dict()
        num_bank_sets = len(bin_params_set)

        for bank_set_index in range(num_bank_sets):
            # get value
            bank_id_list, bin_params, tof_vector = bin_params_set[bank_set_index]

            # Rebin to these banks' parameters (output = Histogram)
            api.Rebin(InputWorkspace=diff_ws_name, OutputWorkspace=diff_ws_name, Params=bin_params, PreserveEvents=True)

            # Create output
            for bank_id in bank_id_list:
                gsas_section_i = self._write_slog_bank_gsas(diff_ws_name, bank_id, tof_vector)
                gsas_buffer_dict[bank_id] = gsas_section_i
        # END-FOR

        # header
        diff_ws = ADS.retrieve(diff_ws_name)
        gsas_header = self._generate_vulcan_gda_header(diff_ws, gsas_file_name, ipts_number, gsas_param_file_name)

        # form to a big string
        gsas_buffer = gsas_header
        for bank_id in sorted(gsas_buffer_dict.keys()):
            gsas_buffer += gsas_buffer_dict[bank_id]

        if gsas_file_name:
            datatypeutility.check_file_name(gsas_file_name, check_exist=False,
                                            check_writable=True, is_dir=False, note='Output GSAS file')
            g_file = open(gsas_file_name, 'w')
            g_file.write(gsas_buffer)
            g_file.close()

        return gsas_buffer
# END-DEF-CLASS







