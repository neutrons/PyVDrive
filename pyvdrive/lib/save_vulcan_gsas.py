from datetime import datetime
import os
import os.path
import h5py
import math
import random
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
        # key = 'bank type', value = TOF vec, binning parameters
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
        new_header = ""

        if len(title) > 80:
            title = title[0:80]
        new_header += "%-80s\n" % title
        new_header += "%-80s\n" % ("Instrument parameter file: %s" % gsas_param_file_name)
        new_header += "%-80s\n" % ("#IPTS: %s" % str(ipts))
        new_header += "%-80s\n" % "#binned by: Mantid"
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

    def _write_slog_bank_gsas(self, ws_name, bank_id, vulcan_tof_vector):
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
        if vulcan_tof_vector is None:
            vec_x = diff_ws.readX(bank_id -1)
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
        for index in range(data_size):
            x_i = '%.1f' % vec_x[index]
            y_i = '%.1f' % vec_y[index]
            e_i = '%.2f' % vec_e[index]
            data_line_i = '%12s%12s%12s' % (x_i, y_i, e_i)
            bank_buffer += '%-80s\n' % data_line_i
        # END-FOR

        return bank_buffer

    def save(self, diff_ws_name, run_date_time, gsas_file_name, ipts_number, gsas_param_file_name,
             align_vdrive_bin, vanadium_gsas_file):
        """
        Save a workspace to a GSAS file or a string
        :param diff_ws_name: diffraction data workspace
        :param run_date_time: date and time of the run
        :param gsas_file_name: output file name. None as not output
        :param ipts_number:
        :param gsas_param_file_name:
        :param align_vdrive_bin: Flag to align with VDRIVE bin edges/boundaries
        :param vanadium_gsas_file:
        :return: string as the file content
        """
        diff_ws = ADS.retrieve(diff_ws_name)

        # set the unit to TOF
        if diff_ws.getAxis(0).getUnit() != 'TOF':
            api.ConvertUnits(InputWorkspace=diff_ws_name, OutputWorkspace=diff_ws_name, Target='TOF',
                             EMode='Elastic')
            diff_ws = ADS.retrieve(diff_ws_name)

        # convert to Histogram Data
        if not diff_ws.isHistogramData():
            api.ConvertToHistogram(diff_ws_name, diff_ws_name)

        # get the binning parameters
        if align_vdrive_bin:
            bin_params_set = self._get_tof_bin_params(self._get_vulcan_phase(run_date_time),
                                                      diff_ws.getNumberHistograms())
        else:
            # a binning parameter set for doing nothing
            print ('[DB...BAT] Using user specified binning parameters')
            bin_params_set = [(range(1, diff_ws.getNumberHistograms()+1), None, None)]

        # rebin and then write output
        gsas_buffer_dict = dict()
        num_bank_sets = len(bin_params_set)

        for bank_set_index in range(num_bank_sets):
            # get value
            bank_id_list, bin_params, tof_vector = bin_params_set[bank_set_index]

            # Rebin to these banks' parameters (output = Histogram)
            if bin_params is not None:
                api.Rebin(InputWorkspace=diff_ws_name, OutputWorkspace=diff_ws_name,
                          Params=bin_params, PreserveEvents=True)

            # Create output
            for bank_id in bank_id_list:
                gsas_section_i = self._write_slog_bank_gsas(diff_ws_name, bank_id, tof_vector)
                gsas_buffer_dict[bank_id] = gsas_section_i
        # END-FOR

        # check for vanadium GSAS file name
        if vanadium_gsas_file is not None:
            # check whether a workspace exists
            # NOTE (algorithm) use hash to determine the workspace name from file location
            van_gsas_ws_name = 'van_{}'.format(hash(vanadium_gsas_file))
            if ADS.doesExist(van_gsas_ws_name):
                van_ws = ADS.retrieve(van_gsas_ws_name)
            else:
                van_ws = load_vulcan_gsas(vanadium_gsas_file, van_gsas_ws_name)

            # check whether the bins are same between GSAS workspace and vanadium workspace
            unmatched, reason = self._compare_workspaces_dimension(van_ws, ADS.retrieve(diff_ws_name))
            if unmatched:
                raise RuntimeError('Vanadium GSAS file {} does not match workspace {}: {}'
                                   ''.format(van_gsas_ws_name, diff_ws_name, reason))

            # normalize
            self._normalize_by_vanadium(diff_ws, van_ws, diff_ws_name)
        # END-IF

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

    @staticmethod
    def _normalize_by_vanadium(diff_ws, van_ws, diff_ws_name):
        """ Normalize by vanadium
        :param van_ws:
        :param diff_ws_name:
        :return:
        """
        api.Divide(LHSWorkspace=diff_ws,
                   RHSWorkspace=van_ws,
                   OutputWorkspace=diff_ws_name)
        diff_ws = ADS.retrieve(diff_ws_name)

        return diff_ws

    @staticmethod
    def _compare_workspaces_dimension(van_ws, diff_ws):
        """
        compare the workspace dimensions
        :param van_ws:
        :param diff_ws:
        :return:
        """
        if van_ws.getNumberHistograms() != diff_ws.getNumberHistograms():
            return False, 'Numbers of histograms are different'

        for iws in range(van_ws.getNumberHistograms()):
            van_vec_x = van_ws.readX(iws)
            diff_vec_x = diff_ws.readX(iws)
            if len(van_vec_x) != len(diff_vec_x):
                return True, 'Numbers of bins are different of workspace index {}'.format(iws)
            elif abs(van_vec_x[0] - diff_vec_x[0])/(van_vec_x[0]) > 1.E-5:
                return True, 'X[0] are different for spectrum {}'.format(iws)
            elif abs(van_vec_x[-1] - diff_vec_x[-1])/(van_vec_x[-1]) > 1.E-5:
                return True, 'X[-1] are different for spectrum {}'.format(iws)
        # END-FOR

        return False, None

# END-DEF-CLASS


def load_vulcan_gsas(gsas_name, gsas_ws_name):
    """
    Load VULCAN GSAS and create a Ragged workspace
    :param gsas_name:
    :param gsas_ws_name:s
    :return:
    """
    # load VULCAN's GSAS file into ragged workspace for vec x and vec y information
    assert isinstance(gsas_name, str), 'GSAS file name {} must be a string but not a {}' \
                                       ''.format(gsas_name, type(gsas_name))
    if not os.path.exists(gsas_name):
        raise RuntimeError('GSAS file {} does not exist.'.format(gsas_name))

    # load GSAS to a ragged workspace
    temp_out_name = 'temp_{}'.format(random.randint(1, 10000))
    temp_gss_ws = api.LoadGSS(Filename=gsas_name, OutputWorkspace=temp_out_name)

    # extract, convert to point data workspace for first spectrum
    api.ExtractSpectra(temp_out_name, WorkspaceIndexList=[0], OutputWorkspace=gsas_ws_name)
    api.ConvertToPointData(InputWorkspace=gsas_ws_name, OutputWorkspace=gsas_ws_name)

    # for the rest of the spectra
    for iws in range(1, temp_gss_ws.getNumberHistograms()):
        # extract, convert to point data, conjoin and clean
        temp_out_name_i = 'temp_i_x'
        api.ExtractSpectra(temp_out_name, WorkspaceIndexList=[iws], OutputWorkspace=temp_out_name_i)
        api.ConvertToPointData(InputWorkspace=temp_out_name_i, OutputWorkspace=temp_out_name_i)
        api.ConjoinWorkspaces(InputWorkspace1=gsas_name,
                              InputWorkspace2=temp_out_name_i)
        api.DeleteWorkspace(temp_out_name_i)
    # END-FOR

    # clean temp GSAS
    api.DeleteWorkspace(temp_out_name)

    gsas_ws = ADS.retrieve(gsas_ws_name)

    return gsas_ws
