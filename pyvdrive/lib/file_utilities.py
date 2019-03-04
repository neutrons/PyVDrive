# Zoo of utility methods for IO via file for VULCAN
# All the PyVDrive specific files will be parsed or written by methods in this module
import os
import time
import platform
import h5py
import datatypeutility
from mantid.simpleapi import SaveNexusProcessed, LoadNexusProcessed


def check_file_creation_date(file_name):
    """
    check the create date (year, month, date) for a file
    :except RuntimeError: if the file does not exist
    :param file_name:
    :return: Date string as 'YYYY-MM-DD
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


def convert_to_list(list_str, sep, element_type):
    """
    list in format of string. with separation as &
    :param list_str:
    :param sep: char or string to separate the list
    :return:
    """
    datatypeutility.check_string_variable('List in string format to convert from', list_str)
    datatypeutility.check_string_variable('Separation string/font to split the list', sep)
    assert isinstance(element_type, type), 'Input element type {} must be a type but not {}' \
                                           ''.format(element_type, type(element_type))

    # remove all the space
    if sep != '':
        # separation cannot be SPACE in this case
        list_str = list_str.replace(' ', '')

    # split
    terms = list_str.split(sep)
    if len(terms) < 2:
        raise RuntimeError('There must be at least 2 run numbers given.')

    run_number_list = list()
    for term in terms:
        try:
            run = element_type(term)
        except ValueError as value_err:
            raise RuntimeError('In given run numbers, {} cannot be converted to {} due to {}.'
                               ''.format(term, element_type, value_err))
        run_number_list.append(run)
    # END-FOR

    return run_number_list


def import_detector_efficiency(h5_name):
    """
    import detector efficiency file
    :param h5_name:
    :return:
    """
    assert isinstance(h5_name, str)
    assert os.path.exists(h5_name)

    # open file
    det_file = h5py.File(h5_name, 'r')

    pid_vec = det_file['entry']['detector_efficiency']['pid'].value
    det_eff_factor_vec = det_file['entry']['detector_efficiency']['inverted efficiency'].value

    # close file
    det_file.close()

    return pid_vec, det_eff_factor_vec


# TODO - TODAY - TEST : with new workflow test on cyclic data
def load_sample_logs_h5(log_h5_name, log_name=None):
    """
    Load standard sample log (TimeSeriesProperty) from an HDF file
    Note: this is paired with save_sample_logs_h5
    :param log_h5_name:
    :param log_name: specified log name to load.  If None, then load all the sample logs
    :return: dictionary: d[log name] = vec_times, vec_values  of numpy arrays
    """
    def is_sample_log(log_entry_name):
        return log_h5[log_entry_name].has_attribute('sample log')

    def read_log(log_entry_name):
        vec_times = log_h5[log_entry_name]['time']
        vec_value = log_h5[log_entry_name]['value']
        return vec_times, vec_value

    datatypeutility.check_file_name(log_h5_name, True, False, False, 'PyVDRive HDF5 sample log file')

    log_h5 = h5py.File(log_h5_name, 'r')

    sample_log_dict = dict()
    if log_name is None:
        for log_name in log_h5.keys():
            if not is_sample_log(log_name):
                continue
            sample_log_dict[log_name] = read_log(log_name)
    else:
        sample_log_dict[log_name] = read_log(log_name)

    return sample_log_dict


def save_sample_logs(workspace, log_names, log_h5_name):
    """ Save sample logs to an HDF5 file
    :param workspace:
    :param log_names:
    :param log_h5_name:
    :return:
    """

    def write_sample_log(entry_name, vec_times, vec_value):
        """ Write a TimeSeriesProperty to an entry (group) in HDF5 file
        :param entry_name:
        :param vec_times:
        :param vec_value:
        :return:
        """
        log_entry = log_h5.create_group(entry_name)
        # convert from datetime to float (second)
        vec_times_second = (vec_times - vec_times[0]).astype('float') * 1.E-9
        log_entry.create_dataset('time', data=vec_times_second)
        log_entry.create_dataset('value', data=vec_value)
        log_entry["type"] = 'sample log'

        return

    # check inputs
    try:
        run_obj = workspace.run()
    except AttributeError as any_err:
        raise RuntimeError('Input {} shall be a workspace with Run object but not a {}: FYI {}'
                           ''.format(workspace, type(workspace), any_err))
    datatypeutility.check_list('Sample log names', log_names)
    datatypeutility.check_string_variable('Output HDF5 log file name', log_names)
    datatypeutility.check_file_name(log_h5_name, False, True, False, 'Output PyVDrive HDF5 sample log file')

    # create file
    log_h5 = h5py.File(log_h5_name, 'w')

    error_msg = ''
    written_at_least_one = False
    for log_name_i in log_names:
        try:
            vec_times_i = run_obj.getProperty(log_name_i).times
            vec_value_i = run_obj.getProperty(log_name_i).value
            # write
            write_sample_log(log_name_i, vec_times_i, vec_value_i)
            # record
            written_at_least_one = True
        except (KeyError, RuntimeError) as any_error:
            error_msg += '{}: {}'.format(log_name_i, any_error)

    log_h5.close()

    if not written_at_least_one:
        raise RuntimeError(error_msg)

    return error_msg


def load_event_slice_file():
    slicer_file = open(slicer_file_name, 'r')
    raw_lines = slicer_file.readlines()
    slicer_file.close()

    slicer_list = list()
    for line in raw_lines:
        # print '[DB...BAT] Line: {0}'.format(line)
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue

        terms = line.split()
        # print '[DB...BAT] Line split to {0}'.format(terms)
        if len(terms) < 3:
            continue
        start_time = float(terms[0])
        stop_time = float(terms[1])
        target_ws = str(terms[2])
        slicer_list.append((start_time, stop_time, target_ws))
        # END-FOR


def load_processed_nexus(nexus_file_name, output_ws_name):
    """
    load a Mantid processed Nexus file
    :param nexus_file_name:
    :param output_ws_name:
    :return:
    """
    datatypeutility.check_file_name(nexus_file_name, check_exist=True, check_writable=False,
                                    note='Mantid processed NeXus file')
    datatypeutility.check_string_variable('Output workspace name', output_ws_name)
    # LoadNexusProcessed(Filename='/home/wzz/Projects/PyVDrive/tests/data/vulcan_vanadium.nxs',
    #                    OutputWorkspace='7bankvanadium')

    LoadNexusProcessed(Filename=nexus_file_name, OutputWorkspace=output_ws_name)

    return


def read_merge_run_file(run_file_name):
    """ Read a standard VDRIVE run file
    Data are combined from the runs of rest columns to the runs of the first column in the runfile.txt.
    """
    # check input
    datatypeutility.check_file_name(run_file_name, True, False, False,
                                    note='Run number file')

    # import run-merge file
    run_file = open(run_file_name, 'r')
    lines = run_file.readlines()
    run_file.close()

    # parse run-merge file
    # merge_run_dict = dict()

    run_number_list = list()
    for line in lines:
        line = line.strip()

        # skip if empty line or command line
        if len(line) == 0:
            continue
        elif line[0] == '#':
            continue

        # set up: replace any supported separator (',', '&', ..) by space
        line = line.replace(',', ' ').replace('&', ' ')
        run_str_list = line.split()

        for run_str in run_str_list:
            try:
                run_number = int(run_str)
            except ValueError as val_err:
                raise RuntimeError('{} cannot be converted to integer as run number: {}'.format(run_str, val_err))
            run_number_list.append(run_number)

        # TODO - FIXME - FUTURE-AFTER-RELEAE - I don't know why parse with this format
        # target_run_number = None
        # for index, run_str in enumerate(run_str_list):
        #
        #     run_number = int(run_str)
        #     if index == 0:
        #         # create a new item (i.e., node) in the return dictionary
        #         target_run_number = run_number
        #         merge_run_dict[target_run_number] = list()
        #
        #     assert target_run_number is not None
        #     merge_run_dict[target_run_number].append(run_number)
        # # END-FOR (term)
    # END-FOR (line)

    return run_number_list  # merge_run_dict


def save_workspace(ws_name, file_name, file_type='nxs', title=''):
    """
    save a workspace to Mantid processed Nexus file
    :param ws_name:
    :param file_name:
    :param file_type:
    :param title:
    :return:
    """
    datatypeutility.check_string_variable('Workspace name', ws_name)
    datatypeutility.check_file_name(file_name=file_name, check_writable=True,
                                    check_exist=False,
                                    note='Output processed NeXus file')
    datatypeutility.check_string_variable('Workspace title', title)

    if (file_type is None and file_name.lower().ends('.nxs')) or file_type == 'nxs':
        SaveNexusProcessed(InputWorkspace=ws_name,
                           Filename=file_name,
                           Title=title)
    else:
        raise RuntimeError('File type {0} or output file postfix {1} is not supported for saving.'
                           ''.format(file_type, file_name.lower()))

    return
