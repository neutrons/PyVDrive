# Script 1
#
# Goal: observe the shift of the summed spectra intensity (given by pixel IDs) with option as focused/non-focused.
#
# Output: a set data in TOF-intensity
#
# Example: sum_pixels.py run_numbers=file_name pixel_range=file_name focus=1
#
# Script 2
#
# Goal: observe the counts/intensity summed from any column in 2theta angle.
#
# Output: 2theta-summed counts (or normalized intensity)
import numpy
from pyvdrive.lib import datatypeutility
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import mantid_reduction
from pyvdrive.lib import reductionmanager
from pyvdrive.lib import vulcan_util


class Collimator(object):
    """ Collimator analysis
    """
    def __init__(self):
        """ initi
        """
        self._data_set = None
        self._proton_charges = list()
        self._run_numbers = None

        return

    def help(self):
        print ("This is the the one")

    def execute_scan_rotating_collimator(self, ipts_number, run_number_list, pixels, to_focus_spectra):
        """ 
        :param run_number_list:
        :param pixels:
        :param to_focus_spectra:
        :return:
        """
        datatypeutility.check_list('Run numbers', run_number_list)
        datatypeutility.check_list('Pixel IDs', pixels)

        calib_manager = reductionmanager.CalibrationManager()

        data_set = dict()

        self._run_numbers = run_number_list[:]

        # load run numbers
        for run_number in run_number_list:
            # locate original nexus file
            if ipts_number is None:
                ipts_number = mantid_helper.get_ipts_number(run_number)
            event_file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)

            # load data from file
            ws_name_i = 'VULCAN_{}_events'.format(run_number)
            mantid_helper.load_nexus(data_file_name=event_file_name, output_ws_name=ws_name_i,
                                     meta_data_only=False)

            # align
            run_start_date = calib_manager.check_creation_date(event_file_name)
            has_loaded_cal, calib_ws_collection = calib_manager.has_loaded(run_start_date, 3)
            if not has_loaded_cal:
                calib_manager.search_load_calibration_file(run_start_date, 3, ws_name_i)
            # workspaces = calib_manager.get_loaded_calibration_workspaces(run_start_date, 3)
            calib_ws_name = calib_ws_collection.calibration
            # group_ws_name = workspaces.grouping
            # mask_ws_name = workspaces.mask

            # align and output to dSpacing
            mantid_reduction.align_instrument(ws_name_i, calib_ws_name)

            # focus or not
            out_name_i = ws_name_i + '_partial'
            workspace_index_vec = vulcan_util.convert_pixels_to_workspace_indexes_v1(pixel_id_list=pixels)
            if to_focus_spectra:
                # focus:
                # mantid_helper.mtd_convert_units(ws_name_i, target_unit='dSpacing')
                mantid_helper.rebin(ws_name_i, '-0.1', preserve=True)
                mantid_helper.sum_spectra(ws_name_i, output_workspace=out_name_i,
                                          workspace_index_list=workspace_index_vec)
                mantid_helper.mtd_convert_units(out_name_i, target_unit='TOF')
                mantid_helper.rebin(out_name_i, '3000, -0.0003, 70000', preserve=True)
            else:
                # sum spectra: rebin
                mantid_helper.mtd_convert_units(ws_name_i, target_unit='TOF')
                mantid_helper.rebin(ws_name_i, '3000, -0.0003, 70000', preserve=True)
                mantid_helper.sum_spectra(ws_name_i, output_workspace=out_name_i,
                                          workspace_index_list=workspace_index_vec)
            # END-IF

            # convert to point data
            mantid_helper.convert_to_point_data(out_name_i)

            # get workspace
            out_ws = mantid_helper.retrieve_workspace(out_name_i, True)
            data_set[run_number] = out_ws.readX(0), out_ws.readY(0)
        # END-FOR

        self._data_set = data_set

        return data_set

    def get_output_data(self):
        return self._data_set

    def execute_calculate_2theta_intensity(self, ipts_number, run_number):
        """
        sum events' counts along tube, convert tube center to 2theta
        :return:
        """
        # locate original nexus file
        if ipts_number is None:
            ipts_number = mantid_helper.get_ipts_number(run_number)
        event_file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)

        # load data from file
        ws_name_i = 'VULCAN_{}_events'.format(run_number)
        mantid_helper.load_nexus(data_file_name=event_file_name, output_ws_name=ws_name_i,
                                 meta_data_only=False)

        # now count the events per column on high angle detector
        counts_vec = self._count_events_by_det_column(ws_name_i)
        self._data_set = counts_vec

        # get proton charges
        event_ws = mantid_helper.retrieve_workspace(ws_name_i)
        plog = event_ws.run().getProperty('proton_charge')
        pcharges = plog.value.sum()
        self._proton_charges = [pcharges]

        return counts_vec

    @staticmethod
    def _count_events_by_det_column(ws_name):
        """
        count events by detector column
        :param ws_name:
        :return:
        """
        high_angle_bank_start_index = 6468

        event_ws = mantid_helper.retrieve_workspace(ws_name, raise_if_not_exist=True)

        source_pos = event_ws.getInstrument().getSource().getPos()
        sample_pos = event_ws.getInstrument().getSample().getPos()
        k_in = sample_pos - source_pos

        # form output array
        counts_array = numpy.ndarray(shape=(8*9, 2), dtype='float')

        for det_col_index in range(8*9):  # 9 8-packs
            # calculate neutron events
            ws_index_0 = high_angle_bank_start_index + 256 * det_col_index
            ws_index_f = ws_index_0 + 255
            counts_i = 0
            for iws in range(ws_index_0, ws_index_f + 1):
                counts_i += event_ws.getEventList(iws).getNumberEvents()
            # END-FOR

            # calculate two theta angle
            center_ws_index = (ws_index_0 + ws_index_f) / 2
            det_pos = event_ws.getDetector(center_ws_index).getPos()
            k_out = det_pos - sample_pos

            twotheta = k_out.angle(k_in) * 180. / numpy.pi

            counts_array[det_col_index][0] = twotheta
            counts_array[det_col_index][1] = counts_i
        # END-FOR

        return counts_array

    def save_to_ascii(self, file_name):
        """
        :param file_name:
        :return:
        """
        if self._data_set is None:
            raise RuntimeError('No data has been calculated yet')

        if isinstance(self._data_set, dict):
            wbuf = '# TOF      '
            for run_number in self._run_numbers:
                wbuf += '{:10d}'.format(run_number)
            wbuf += '\n'

            template_set = self._data_set[self._run_numbers[0]]
            num_pt = template_set[0].shape[0]

            for ipt in range(num_pt):
                wbuf += '{:.2f}    '.format(template_set[0][ipt])
                for run_number in self._run_numbers:
                    wbuf += '{:.2f}    '.format(self._data_set[run_number][1][ipt])
                wbuf += '\n'
            # END-FOR

            print (wbuf)

        elif isinstance(self._data_set, numpy.ndarray) and len(self._data_set.shape) == 2:
            wbuf = '# proton = {}\n'.format(self._proton_charges[0])
            num_pt = self._data_set.shape[0]
            for index in range(num_pt-1, -1, -1):
                wbuf += '{:.5f}    {}\n'.format(self._data_set[index][0], self._data_set[index][1])
        else:
            raise RuntimeError('Data set of type {} is not recognized'.format(self._data_set))
        # END-IF

        ofile = open(file_name, 'w')
        ofile.write(wbuf)
        ofile.close()

        return


# definition of external files
def convert_integer(int_sr):
    """
    convert a string to integer
    :param int_sr:
    :return:
    """
    try:
        int_r = int(int_sr)
    except ValueError:
        raise ValueError('String {} cannot be converted to integer'.format(int_sr))

    return int_r


def convert_integer_range(int_range_str):
    """
    convert a string as 'a:b' or 'a:b:c'
    :param int_range_str:
    :return:
    """
    items = int_range_str.split(':')

    step = 1
    try:
        int_start = convert_integer(items[0])
        int_stop = convert_integer(items[1])
        if len(items) == 3:
            step = convert_integer(items[2])
        if int_stop <= int_start:
            raise ValueError('Stop value {} must be larger than starting value {}'
                             ''.format(int_stop, int_start))
        if step <= 0:
            raise ValueError('Step {} cannot be less or equal to 0.'
                             ''.format(step))
    except ValueError as val_err:
        raise ValueError('Unable to parse {}: {}'.format(int_range_str, val_err))

    int_list = range(int_start, int_stop, step)

    return int_list


def parse_runs_file(file_name):
    """ parse a file containing run numbers in a free style
    :param file_name:
    :return:
    """
    datatypeutility.check_file_name(file_name, check_exist=True)

    # read in lines
    run_file = open(file_name, 'r')
    lines = run_file.readlines()
    run_file.close()

    # parse
    run_numbers = list()
    for line in lines:
        line = line.strip()

        if len(line) == 0:
            continue
        elif line.startswith('#'):
            # comment line
            continue

        # replace , with ' '
        line = line.replace(',', '')
        items = line.split()

        for item in items:
            try:
                run_number = int(item)
            except ValueError:
                print ('Unable to parse {} as run number'.format(item))
            else:
                run_numbers.append(run_number)
        # END-FOR
    # END-FOR

    run_numbers = sorted(run_numbers)

    return run_numbers


def parse_pixels_file(file_name):
    """
    parse a file containing pixel IDs to be reduced
    Accepted PixelIDs: a, a:b, a:b:x (i.e., a, a+x, a+2x, ...)
    :param file_name:
    :return:
    """
    datatypeutility.check_file_name(file_name, check_exist=True)

    # read in lines
    run_file = open(file_name, 'r')
    lines = run_file.readlines()
    run_file.close()

    # parse
    pixel_id_list = list()
    for line in lines:
        line = line.strip()

        if len(line) == 0:
            continue
        elif line.startswith('#'):
            # comment line
            continue

        # remove all empty space and split by ,
        line = line.replace(' ', '')
        items = line.split(',')

        for item in items:
            num_col = item.count(':')
            try:
                if num_col == 0:
                    pixel_ids = [convert_integer(item)]
                elif num_col <= 2:
                    pixel_ids = convert_integer_range(item)
                else:
                    raise ValueError('{} is not a supported format'.format(item))
            except ValueError as value_err:
                print ('Unable to parse {} to a set of integers due to {}'.format(item, value_err))
            else:
                pixel_id_list.extend(pixel_ids)
        # END-FOR
    # END-FOR

    return pixel_id_list


def scan_rotating_collimator(ipts, runs, pixels, to_focus):
    """
    scan collimator in rotation.
    :param runs: file name containing run numbers
    :param pixels: file name containing pixel IDs
    :param to_focus: flag whether the TOF shall be focused or not
    :return: tuple (bool, str): status and message
    """
    try:
        datatypeutility.check_file_name(runs, check_exist=True, note='ASCII file containing run numbers')
        datatypeutility.check_file_name(pixels, check_exist=True, note='ASCII file containing pixels IDs')
        datatypeutility.check_bool_variable('Flag to indicate whether the summed spectra shall be focused',
                                            to_focus)
    except AssertionError as ass_err:
        return False, 'Input arguments error: {}'.format(ass_err)

    try:
        run_number_list = parse_runs_file(runs)
        pixel_list = parse_pixels_file(pixels)
    except ValueError as val_err:
        return False, 'Input file error: {}'.format(val_err)

    try:
        collimator = Collimator()
        collimator.execute_scan_rotating_collimator(ipts, run_number_list, pixel_list, to_focus_spectra=to_focus)
    except RuntimeError as run_err:
        return False, 'Execution error: {}'.format(run_err)

    return True, collimator


def scan_detector_column(ipts, run_number):
    """
    integrate the counts along column of (high angle) detector
    :param ipts:
    :param base_run:
    :param target_run:
    :return:
    """
    try:
        datatypeutility.check_int_variable('Run Number', run_number, (1, None))
    except AssertionError as ass_err:
        return False, 'Input arguments error: {}'.format(ass_err)

    try:
        collimator = Collimator()
        collimator.execute_calculate_2theta_intensity(ipts, run_number)
    except RuntimeError as run_err:
        return False, 'Execution error: {}'.format(run_err)

    return True, collimator


def main(argv):
    """

    :param argv:
    :return:
    """

    return


# if __name__ == '__main__':
#     main('')
