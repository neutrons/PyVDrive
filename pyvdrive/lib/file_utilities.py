# Zoo of utility methods for IO via file for VULCAN
# All the PyVDrive specific files will be parsed or written by methods in this module
import os
import time
import platform
import h5py
import datatypeutility
from chop_utility import TimeSegment
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


# TODO - TONIGHT 0 - Clean up this method!  It has never been used/tested
def load_sample_logs_h5(log_h5_name, log_name=None):
    """
    Load standard sample log (TimeSeriesProperty) from an HDF file
    Note: this is paired with save_sample_logs_h5
    :param log_h5_name:
    :param log_name: specified log name to load.  If None, then load all the sample logs
    :return: dictionary: d[log name] = vec_times, vec_values  of numpy arrays
    """
    def is_sample_log(h5_root, log_entry_name):
        """
        Check whether a given entry is for sample log
        :param h5_root:
        :param log_entry_name:
        :return:
        """
        try:
            entry_attr = h5_root[log_entry_name].attrs
            if 'sample log' in entry_attr.keys():
                # has such attribute
                is_s_l = True
            elif 'type' in h5_root[log_entry_name].keys() and h5_root[log_entry_name]['type'].value == 'sample log':
                # no such attribute, then check sub entry 'type'
                is_s_l = True
            else:
                # no such attribute, 'type' is not right
                is_s_l = False
        except AttributeError as att_err:  # in case the entry is not a Group
            is_s_l = False
            print('[ERROR] File {} Entry {} has error to be a sample log: {}'
                  ''.format(h5_root.filename, log_entry_name, att_err))

        return is_s_l

    def read_log(h5_root, log_entry_name):
        vec_times = h5_root[log_entry_name]['time'][:]
        vec_value = h5_root[log_entry_name]['value'][:]
        return vec_times, vec_value

    datatypeutility.check_file_name(log_h5_name, True, False, False,
                                    'PyVDRive HDF5 sample log file')

    log_h5 = h5py.File(log_h5_name, 'r')
    print('[DB...BAT] Open {}'.format(log_h5_name))

    sample_log_dict = dict()
    if log_name is None:
        for log_name in log_h5.keys():
            if not is_sample_log(log_h5, log_name):
                print('{} is not a sample log'.format(log_name))
                continue
            sample_log_dict[log_name] = read_log(log_h5, log_name)
    else:
        sample_log_dict[log_name] = read_log(log_h5, log_name)
    log_h5.close()

    return sample_log_dict


# TODO/NEXT - If parse_time_segmenets works for data slicer file too, then remove parse_data_slicer_file()
def load_event_slicers_file(file_name):
    """ Load and parse data/events slicer file
    :param file_name:
    :return: list (3-tuple, start time, stop time, target)
    """
    # check
    datatypeutility.check_file_name(file_name, True, False, False,
                                    'Event data slicers/splitters setup file')

    # load all the file content
    try:
        slicer_file = open(file_name, 'r')
        raw_lines = slicer_file.readlines()
        slicer_file.close()
    except IOError as io_err:
        raise RuntimeError('Unable to open file {0} due to {1}.'.format(file_name, io_err))
    except OSError as os_err:
        raise RuntimeError('Unable to import file {0} due to {1}.'.format(file_name, os_err))

    slicer_list = list()
    error_message = ''
    for line_number, line in enumerate(raw_lines):
        line = line.strip()

        # skip empty line and comment line
        if len(line) == 0 or line[0] == '#':
            continue

        terms = line.split()
        if len(terms) < 2:
            continue

        try:
            start_time = float(terms[0])
            stop_time = float(terms[1])
            if len(terms) >= 3:
                target_ws = str(terms[2])
            else:
                target_ws = None

            slicer_list.append((start_time, stop_time, target_ws))
        except ValueError as val_err:
            error_message += 'Skip line {} due to {}\n'.format(line_number, val_err)

    # END-FOR

    return slicer_list


def parse_multi_run_slicer_file(file_name):
    """
    Parse the ASCII file to set up event filtering on several runs

    File format:
    # comments
    # starting of a block
    [RUN] 123456
    # start_time    end_time   target_workspace_name/index
    0     -1     1   # from relative 0 to end of run, target is 12345_1, NO CHOPPING]
    [RUN] 123457
    0     200    1   #  from relative 0 to 200, target is 123457_1
    200   420    2
    [RUN] 123458
    0     100    123456_1    # from relative 0 to 100, target will be combined with RUN-123456's WS-1

    Acceptable line format
    - start_time stop_time          : auto index
    - start_time stop_time integer  : (index fro this run) ... final name: run_chopindex
    - start_time stop_time string   : string not to be confused with integer... universal among runs
    - start_time stop_time # ...    : auto index with comment after #

    :param file_name:
    :return:
    """
    # read files
    datatypeutility.check_file_name(file_name, True, False, False, 'Multiple run slicing file')
    try:
        slice_file = open(file_name, 'r')
    except IOError as io_err:
        raise RuntimeError('Unable to read file {} due to {}'.format(file_name, io_err))
    raw_lines = slice_file.readlines()
    slice_file.close()

    slicer_dict = dict()

    curr_run_number = None
    for line_no, line in enumerate(raw_lines):
        line = line.strip()
        if line == '' or line.startswith('#'):
            # empty line or comment
            continue

        # detect start of run
        if line.startswith('[RUN]'):
            # yes. start of a new block
            try:
                curr_run_number = int(line.split('[RUN]')[1].strip().split()[0])
            except ValueError as value_err:
                raise RuntimeError('Starting block line: "{}" is not valid to parse run number: {}'
                                   ''.format(line, value_err))

            slicer_dict[curr_run_number] = list()

        else:
            # slicer line
            contents = line.split()
            if len(contents) < 2:
                raise RuntimeError('{}-th line\n{}\nhas too few information'.format(line_no, line))

            try:
                start_time_curr = float(contents[0])
                stop_time_curr = float(contents[1])
            except ValueError as value_err:
                raise RuntimeError(balbla)

            if len(contents) == 2 or contents[2] == '#':
                # only
                target_ws = None

            else:
                target_ws = contents[2]
                if target_ws.isdigit():
                    target_ws = '{}_{:-05}'.format(curr_run_number, int(target_ws))
    # END-FOR

    # TODO - TONIGHT 0 - continue from here - check slicer formats and fill the ignored
    slicer_dict = format_user_splitters()

    return slicer_dict

# TODO - TONIGHT 0 - Whether there is a similar method in chop/PICKDATA?


def parse_time_segments(file_name):
    """
    Parse the standard time segments file serving for event slicers
    :param file_name:
    :return: 2-tuple as (boolean, object): (True, (reference run, start time, segment list))
            (False, error message)
    """
    # Check
    datatypeutility.check_file_name(file_name, check_exist=True, note='Time segmentation file')

    # Read file
    try:
        in_file = open(file_name, 'r')
        raw_lines = in_file.readlines()
        in_file.close()
    except IOError as e:
        raise RuntimeError('Failed to read time segment file {} due to {}'.format(file_name, e))

    ref_run = None
    run_start = None
    segment_list = list()

    i_target = 1

    for raw_line in raw_lines:
        line = raw_line.strip()

        # Skip empty line
        if len(line) == 0:
            continue

        # Comment line
        if line.startswith('#') is True:
            # remove all spaces
            line = line.replace(' ', '')
            terms = line.split('=')
            if len(terms) == 1:
                continue
            if terms[0].lower().startswith('referencerunnumber'):
                # reference run number
                ref_run_str = terms[1]
                if ref_run_str.isdigit():
                    ref_run = int(ref_run_str)
                else:
                    ref_run = ref_run_str
            elif terms[0].lower().startswith('runstarttime'):
                # run start time
                run_start_str = terms[1]
                try:
                    run_start = float(run_start_str)
                except ValueError:
                    print '[Warning] Unable to convert run start time %s to float' % run_start_str
        else:
            # remove all tab
            line = line.replace('\t', '')
            terms = line.split()
            if len(terms) < 2:
                print '[Warning] Line "%s" is of wrong format.' % line
                continue

            try:
                start_time = float(terms[0])
                stop_time = float(terms[1])
                if len(terms) < 3:
                    target_id = i_target
                    i_target += 1
                else:
                    target_id = terms[2]
                new_segment = TimeSegment(start_time, stop_time, target_id)
                segment_list.append(new_segment)
            except ValueError as e:
                print '[Warning] Line "{0}" has wrong type of value for start/stop. FYI {1}.'.format(line, e)
                continue
        # END-IF (#)
    # END-FOR

    return ref_run, run_start, segment_list


def save_sample_logs(workspace, log_names, log_h5_name, start_time, attribution_dict=None):
    """ Save sample logs to an HDF5 file
    :param workspace:
    :param log_names:
    :param log_h5_name:
    :param attribution_dict: extra attribution written to GSAS
    :return:
    """
    def write_sample_log(entry_name, vec_times, vec_value, time_0):
        """ Write a TimeSeriesProperty to an entry (group) in HDF5 file
        :param entry_name:
        :param vec_times:
        :param vec_value:
        :return:
        """
        log_entry = log_h5.create_group(entry_name)
        # convert from datetime to float (second) relative to time zero
        if time_0 is None:
            time_0 = vec_times[0]
        vec_times_second = (vec_times - time_0).astype('float') * 1.E-9
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
    datatypeutility.check_string_variable('Output HDF5 log file name', log_h5_name)
    datatypeutility.check_file_name(log_h5_name, False, True, False,
                                    'Output PyVDrive HDF5 sample log file')

    # create file
    log_h5 = h5py.File(log_h5_name, 'w')

    error_msg = ''
    written_at_least_one = False
    for log_name_i in log_names:
        try:
            vec_times_i = run_obj.getProperty(log_name_i).times
            vec_value_i = run_obj.getProperty(log_name_i).value
            # write
            write_sample_log(log_name_i, vec_times_i, vec_value_i, time_0=start_time)
            # record
            written_at_least_one = True
        except (KeyError, RuntimeError) as any_error:
            error_msg += '{}: {}'.format(log_name_i, any_error)

    # writing attribution
    if attribution_dict is not None:
        datatypeutility.check_dict('Attributions', attribution_dict)
        for attrib_name in attribution_dict.keys():
            log_h5[attrib_name] = attribution_dict[attrib_name]

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
                raise RuntimeError(
                    '{} cannot be converted to integer as run number: {}'.format(run_str, val_err))
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
