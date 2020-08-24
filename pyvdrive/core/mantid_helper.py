import os
import random
import numpy

import mantid
import mantid.api
import mantid.dataobjects
import mantid.geometry
import mantid.simpleapi as mantidapi
from mantid.api import AnalysisDataService as ADS
from pyvdrive.core import vdrivehelper
from pyvdrive.core import datatypeutility
import datetime

EVENT_WORKSPACE_ID = "EventWorkspace"
WORKSPACE_2D_ID = 'Workspace2D'
MASK_WORKSPACE_ID = 'MaskWorkspace'
GROUPING_WORKSPACE_ID = 'GroupingWorkspace'
CALIBRATION_WORKSPACE_ID = 'TableWorkspace'

# define constants
VULCAN_L1 = 43.754
VULCAN_1BANK_L2 = 2.009436
VULCAN_1BANK_POLAR = 90.1120
VULCAN_2BANK_1_L2 = 2.009436
VULCAN_2BANK_1_POLAR = 90.
VULCAN_2BANK_2_L2 = 2.009436
VULCAN_2BANK_2_POLAR = 360. - 90.1120

HIGH_ANGLE_BANK_2THETA = 150.


def check_bins_can_align(workspace_name, template_workspace_name):
    """
    match the bins of workspace to the template workspace
    :param workspace_name:
    :param template_workspace_name:
    :return: 2-tuple (boolean as align-able, string for reason
    """
    # get workspace
    try:
        target_workspace = ADS.retrieve(workspace_name)
        template_workspace = ADS.retrieve(template_workspace_name)
    except KeyError as key_err:
        return False, 'Unable to retrieve workspace {0} and/or {1} due to {2}.' \
                      ''.format(workspace_name, template_workspace_name, key_err)

    # check number of spectra
    num_template_hist = template_workspace.getNumberHistograms()
    num_target_hist = target_workspace.getNumberHistograms()

    if num_template_hist == 1:
        single_template_bin = True
    elif num_template_hist == num_target_hist:
        single_template_bin = False
    else:
        return False, 'There are unequal numbers of histograms of {0} and {1}.' \
                      ''.format(workspace_name, template_workspace_name)

    # mapping
    if single_template_bin:
        template_vec_x = template_workspace.readX(0)
    else:
        template_vec_x = None

    for i_ws in range(num_target_hist):
        # get vector X of template and target
        if template_vec_x is None:
            template_vec_x = template_workspace.readX(i_ws)
        target_vec_x = target_workspace.readX(i_ws)

        # check number of bins
        if len(template_vec_x) != len(target_vec_x):
            return False, 'Of workspace index {0}, {1} and {2} has different number of bins, such that {3} and {4} ' \
                          'respectively.'.format(i_ws, workspace_name, template_workspace_name,
                                                 len(template_vec_x), len(target_vec_x))

        # check difference in bins
        sum_vec_target = numpy.sum(target_vec_x)
        sum_vec_template = numpy.sum(template_vec_x)

        diff_vec = target_vec_x - template_vec_x
        diff_vec_square = diff_vec**2
        diff_sum = numpy.sqrt(numpy.sum(diff_vec_square))

        if diff_sum/min(sum_vec_target, sum_vec_template) > 1.:
            return False, 'Difference of workspace index {0} is huge!'.format(i_ws)
    # END-FOR

    return True, ''


def clone_workspace(srs_ws_name, target_ws_name):
    """
    clone workspace
    :param srs_ws_name:
    :param target_ws_name:
    :return:
    """
    datatypeutility.check_string_variable('Source workspace name', srs_ws_name)
    datatypeutility.check_string_variable('Target workspace name', target_ws_name)

    mantidapi.CloneWorkspace(InputWorkspace=srs_ws_name, OutputWorkspace=target_ws_name)

    output_ws = ADS.retrieve(target_ws_name)

    return output_ws


def is_workspace_point_data(ws_name):
    """
    Check whether a workspace point data
    :param ws_name:
    :return:
    """
    workspace = retrieve_workspace(ws_name)
    num_spec = get_number_spectra(workspace)

    if workspace.id() == 'WorkspaceGroup':
        is_point_data = True
        for ws_index in range(num_spec):
            if workspace[ws_index].isHistogramData():
                is_point_data = False
                break
    else:
        is_point_data = not workspace.isHistogramData()

    return is_point_data


def convert_to_point_data(ws_name):
    """ Convert to point data from histogram
    :param ws_name:
    :return:
    """
    if is_workspace_point_data(ws_name):
        print('[INFO] Workspace {} is already of PointData. No need to convert anymore'
              ''.format(ws_name))
    else:
        mantidapi.ConvertToPointData(InputWorkspace=ws_name,
                                     OutputWorkspace=ws_name)

    return


def convert_to_non_overlap_splitters_bf(split_ws_name):
    """
    convert a Table splitters workspace containing overlapped time segment
    to a set of splitters workspace without overlap by brute force
    :param split_ws_name:
    :return:
    """
    # get splitters workspace and check its type
    split_ws = retrieve_workspace(split_ws_name)
    assert isinstance(split_ws, mantid.dataobjects.TableWorkspace), \
        'Splitters workspace {0} must be a TableWorkspace but not a {1}.'.format(
            split_ws, type(split_ws))

    # output data structure
    current_child_index = 0
    curr_split_ws = create_table_splitters(split_ws_name + '0')
    sub_split_ws_list = [curr_split_ws]

    for i_row in split_ws.rowCount():
        # get start and stop
        start_i = split_ws.cell(i_row, 0)
        stop_i = split_ws.cell(i_row, 1)
        target_i = split_ws.cell(i_row, 2)
        # always tends to append to the current one.  if not, then search till beginning of the list

        continue_loop = True
        while continue_loop:
            if curr_split_ws.rowCount() == 0 or curr_split_ws.cell(curr_split_ws.rowCount()-1, 1) <= start_i:
                # either empty split workspace of current split workspace's last splitter's stop time is earlier
                # add a new row
                print('[DB...BT] Add split from {0} to {1} to sub-splitter {2}'
                      ''.format(start_i, stop_i, current_child_index))
                curr_split_ws.addRow([start_i, stop_i, target_i])
                break

            if current_child_index == len(sub_split_ws_list) - 1:
                # go back to first one
                current_child_index = 0
            else:
                # advance to next one (fill evenly, right?)
                current_child_index += 1
            curr_split_ws = sub_split_ws_list[current_child_index]

            if current_child_index == 0 and curr_split_ws.cell(curr_split_ws.rowCount()-1, 1) > start_i:
                # go from last one to first one. time to add a new one if still overlap with new one
                current_child_index = len(sub_split_ws_list)
                curr_split_ws = create_table_splitters(
                    split_ws_name + '{0}'.format(current_child_index))
                sub_split_ws_list.append(curr_split_ws)
            # END-IF
        # END-WHILE
    # END-FOR

    return sub_split_ws_list


def create_overlap_splitters(ws_name, start_time, stop_time, time_bin_size, time_segment_period):
    """

    :param ws_name:
    :param start_time:
    :param stop_time:
    :param time_bin_size:
    :param time_segment_period:
    :return:
    """
    # checking condition
    if time_bin_size <= time_segment_period:
        raise RuntimeError('The case that time segment bin size {0} is smaller than time segment period/distance {1} '
                           'is not applied by method create_overlap_splitters.'
                           ''.format(time_bin_size, time_segment_period))

    # get number of sub-splitters workspaces
    num_sub_splitters = int(time_bin_size / time_segment_period + 0.5)

    # get the element of each splitters workspace
    splitters_size = (stop_time - start_time) / time_segment_period

    splitter_ws_list = list()
    for i_sub in range(num_sub_splitters):
        # define for array size
        vec_x = numpy.ndarray(shape=(splitters_size*2, ), dtype='double')
        vec_y = numpy.ndarray(shape=(splitters_size*2-1, ), dtype='double')
        vec_y.fill(-1)
        vec_e = vec_y

        # set up the value
        for i_split in range(splitters_size):
            vec_x[i_split*2] = start_time + i_split * time_segment_period
            vec_x[i_split*2+1] = vec_x[i_split] + time_bin_size

            vec_y[i_split*2] = i_split * num_sub_splitters + i_sub
        # END-FOR

        splitters_ws = create_workspace_2d(vec_x, vec_y, vec_e, ws_name + '{0}'.format(i_sub))

        splitter_ws_list.append(splitters_ws)
    # END-FOR

    return splitter_ws_list


def create_table_splitters(split_ws_name):
    """
    create splitters workspace in form of TableWorkspace
    :param split_ws_name:
    :return:
    """
    column_definitions = list()
    column_definitions.append(('float', 'start'))
    column_definitions.append(('float', 'stop'))
    column_definitions.append(('str', 'target'))

    return create_table_workspace(split_ws_name, column_definitions)


def convert_splitters_workspace_to_vectors(split_ws, run_start_time=None):
    """
    convert SplittersWorkspace to vectors of time and target workspace index
    :param split_ws:
    :param run_start_time:
    :return: 2-tuple: numpy.array, numpy.array (times, target_ws)... [t_i, t_{i+1}] --> ws_i
    """
    # check inputs
    if isinstance(split_ws, str):
        # in case user input split workspace name
        split_ws = retrieve_workspace(split_ws)

    is_splitter_ws = False
    is_arb_table_ws = False
    if split_ws.id() == 'TableWorkspace':
        if split_ws.__class__.__name__.count('Splitter') == 1:
            is_splitter_ws = True
        else:
            is_arb_table_ws = True
    elif split_ws.id() == 'Workspace2D':
        pass
    else:
        raise AssertionError('Input SplittersWorkspace %s must be of type'
                             'SplittersWorkspace/TableWorkspace/Workspace2D '
                             'but not %s' % (str(split_ws), split_ws.__class__.__name__))

    if is_splitter_ws or is_arb_table_ws:
        # splitters workspace
        #  go over rows
        num_rows = split_ws.rowCount()
        print('Splitter/table workspace {} has {} rows'
              ''.format(split_ws, num_rows))
        time_list = list()
        ws_list = list()
        for row_index in range(num_rows):
            # get start time and end time in int64
            start_time = split_ws.cell(row_index, 0)
            end_time = split_ws.cell(row_index, 1)
            ws_index = split_ws.cell(row_index, 2)

            # convert units of time from int64/nanoseconds to float/seconds
            if is_splitter_ws:
                start_time = float(start_time) * 1.0E-9
                end_time = float(end_time) * 1.0E-9

            if row_index == 0:
                # first splitter, starting with start_time[0]
                time_list.append(start_time)
            elif start_time > time_list[-1]:
                # middle splitter, there is a gap between 2 splitters, fill in with -1
                ws_list.append(-1)
                time_list.append(start_time)

            # append workspace index and end time
            ws_list.append(ws_index)
            time_list.append(end_time)
        # END-FOR

        # get the numpy arrays
        vec_times = numpy.array(time_list)
        vec_ws = numpy.array(ws_list)
    else:
        # for matrix workspace splitter
        # TODO - TONIGHT -1 - Make this method work with Matrix
        raise RuntimeError('TODO FUTURE Implement matrix parser')

    # reset to run start time
    if run_start_time is not None and is_splitter_ws:
        # run start time is of float in unit of seconds
        datatypeutility.check_float_variable('Run start', run_start_time, (None, None))
        vec_times -= run_start_time
    elif run_start_time is not None and is_arb_table_ws:
        # it is assumed that TableWorkspace is relative time and in seconds already
        pass
    # END-IF

    return vec_times, vec_ws


def create_table_workspace(table_ws_name, column_def_list):
    """
    create a table workspace with user-specified column
    :param table_ws_name:
    :param column_def_list: list of 2-tuples (string as column data type, string as column name)
    :return:
    """
    mantidapi.CreateEmptyTableWorkspace(OutputWorkspace=table_ws_name)
    table_ws = retrieve_workspace(table_ws_name)
    for col_tup in column_def_list:
        data_type = col_tup[0]
        col_name = col_tup[1]
        table_ws.addColumn(data_type, col_name)

    return table_ws


def create_workspace_2d(vec_x, vec_y, vec_e, output_ws_name):
    """

    :param vec_x:
    :param vec_y:
    :param vec_e:
    :param output_ws_name:
    :return: reference to the generated workspace
    """
    # check size
    assert len(vec_x) == len(vec_y) or len(vec_x) == len(vec_y) + 1, 'blabla'
    assert len(vec_y) == len(vec_e), 'blabla'

    mantidapi.CreateWorkspace(DataX=vec_x, DataY=vec_y, DataE=vec_e, NSpec=1,
                              OutputWorkspace=output_ws_name)

    return ADS.retrieve(output_ws_name)


def crop_workspace(ws_name, cropped_ws_name, x_min, x_max):
    """

    :param ws_name:
    :param cropped_ws_name:
    :param x_min:
    :param x_max:
    :return:
    """
    # check type
    datatypeutility.check_float_variable('XMin', x_min, (0, None))
    datatypeutility.check_float_variable('XMax', x_max, (0, None))
    if x_max <= x_min:
        raise RuntimeError('Xmin {0} >= Xmax {1} for cropping!'.format(x_min, x_max))
    if is_a_workspace(ws_name) is False:
        raise RuntimeError('Workspace {0} does not exist in ADS.'.format(ws_name))
    datatypeutility.check_string_variable('Output cropped workspace name', cropped_ws_name)

    mantidapi.CropWorkspace(InputWorkspace=ws_name,
                            OutputWorkspace=cropped_ws_name,
                            XMin=x_min, XMax=x_max)

    return


def delete_workspace(workspace):
    """ Delete a workspace in AnalysisService
    :param workspace:
    :return:
    """
    mantidapi.DeleteWorkspace(Workspace=workspace)

    return


def export_fullprof(ws_name, file_name):
    """
    Export a workspace to Fullprof file
    :param ws_name:
    :param file_name:
    :return:
    """
    mantidapi.SaveFocusedXYE(ws_name, file_name, SplitFiles=False, IncludeHeader=True, Format='XYE')

    return


def extract_spectrum(input_workspace, output_workspace, workspace_index):
    """
    extract a spectrum from a workspace
    :param input_workspace: str
    :param output_workspace: str
    :param workspace_index: str
    :return:
    """
    datatypeutility.check_string_variable('Input workspace name', input_workspace)
    datatypeutility.check_string_variable('Output workspace name', output_workspace)

    source_ws = retrieve_workspace(input_workspace, True)
    if source_ws.id() == 'WorkspaceGroup':
        raise RuntimeError(
            'Input {} is a WorkspaceGroup, which cannot be extracted'.format(input_workspace))

    datatypeutility.check_int_variable(
        'Workspace index', workspace_index, (0, source_ws.getNumberHistograms()))

    mantidapi.ExtractSpectra(input_workspace, WorkspaceIndexList=[workspace_index],
                             OutputWorkspace=output_workspace)

    return


def find_peaks(diff_data, ws_index, is_high_background, background_type, peak_profile='Gaussian',
               min_peak_height=200, peak_pos_list=None):
    """
    Find peaks in a diffraction pattern
    :param diff_data: diffraction data in workspace
    :param ws_index:
    :param is_high_background:
    :param background_type:
    :param peak_profile: specified peak profile
    :param min_peak_height:
    :param peak_pos_list:  List of tuples for peak information. Tuple = (peak center, height, width)
    :return:
    """
    # check input workspace
    if not workspace_does_exist(diff_data):
        raise RuntimeError(
            'Input workspace {0} does not exist in Mantid AnalysisDataService.'.format(diff_data))
    matrix_workspace = ADS.retrieve(diff_data)
    datatypeutility.check_int_variable(
        'Workspace index', ws_index, (0, matrix_workspace.getNumberHistograms()))

    #  get workspace define output workspace name
    result_peak_ws_name = '{0}_FoundPeaks'.format(diff_data)

    # call Mantid's FindPeaks
    print('[DB...BAT] Input diffraction data: {}'.format(diff_data))
    arg_dict = {'InputWorkspace': diff_data,
                'WorkspaceIndex': ws_index,
                'HighBackground': is_high_background,
                'PeaksList': result_peak_ws_name,
                'MinimumPeakHeight': min_peak_height,
                'PeakFunction': peak_profile,
                'BackgroundType': background_type
                }
    if peak_pos_list is not None:
        assert isinstance(peak_pos_list, list), 'Peak positions {0} must be given by a list but not a {1}.' \
                                                ''.format(peak_pos_list, type(peak_pos_list))
        if len(peak_pos_list) > 0:
            arg_dict['PeakPositions'] = numpy.array(peak_pos_list)

    try:
        mantidapi.FindPeaks(**arg_dict)
    except RuntimeError as run_err:
        raise RuntimeError(
            'Unable to find peaks in workspace {0} due to {1}'.format(diff_data, run_err))

    # check output workspace
    if ADS.doesExist(result_peak_ws_name):
        peak_ws = mantidapi.AnalysisDataService.retrieve(result_peak_ws_name)
    else:
        raise RuntimeError('Failed to find peaks.')

    # check the table from mantid algorithm FindPeaks
    col_names = peak_ws.getColumnNames()
    col_index_centre = col_names.index('centre')
    col_index_height = col_names.index('height')
    col_index_width = col_names.index('width')
    col_index_chi2 = col_names.index('chi2')

    # form output as list of peak tuples
    peak_list = list()
    for index in range(peak_ws.rowCount()):
        peak_i_center = peak_ws.cell(index, col_index_centre)
        peak_i_chi2 = peak_ws.cell(index, col_index_chi2)
        if peak_i_chi2 < 100:
            peak_i_height = peak_ws.cell(index, col_index_height)
            peak_i_width = peak_ws.cell(index, col_index_width)
            peak_list.append((peak_i_center, peak_i_height, peak_i_width))

            print('[INFO] Find peak @ {0} with chi^2 = {1}'.format(peak_i_center, peak_i_chi2))
        else:
            print('[INFO] Ignore peak @ {0} with large chi^2 = {1}'.format(
                peak_i_center, peak_i_chi2))
    # END-FOR

    return peak_list


def generate_event_filters_arbitrary(split_list, relative_time, tag, auto_target):
    """ Generate event filter (splitters workspace) by arbitrary time stamps
    :param split_list: list of 2-element or 3-element
    :param relative_time:
    :param tag: string for tag name
    :return: 2-tuple
        1. status (boolean)
        2. 2-tuple as splitter workspace's name and information (table) workspace's name
    """
    # check
    datatypeutility.check_list('Splitters', split_list)
    datatypeutility.check_string_variable('Splitter tag', tag, None)
    if len(tag) == 0:
        raise RuntimeError('Split tag cannot be empty for generate_event_filters_arbitrary')

    # create an empty workspace
    splitters_ws_name = tag
    info_ws_name = tag + '_Info'

    # use table workspace (relative time in default)
    create_table_workspace(splitters_ws_name, [(
        'float', 'start'), ('float', 'stop'), ('str', 'target')])
    create_table_workspace(info_ws_name, [('str', 'target'), ('str', 'description')])

    # get handler on splitters workspace and info workspace
    splitter_ws = retrieve_workspace(splitters_ws_name)
    info_ws = retrieve_workspace(info_ws_name)
    target_set = set()

    if len(split_list) == 0:
        return False, 'Empty time slice list'

    for index, split_tup in enumerate(split_list):
        # print '[DB...BAT] Splitter {0}: start = {1}, stop = {2}.'.format(index, split_tup[0], split_tup[1])
        start_time = split_tup[0]
        stop_time = split_tup[1]

        if len(split_tup) >= 3:
            # user specified target
            target = str(split_tup[2])
        elif auto_target:
            # in some case, such as VDRIVE chopper file, only contains start and stop time. then use sequence number
            target = '{0}'.format(index + 1)
        else:
            # not allowing auto target, then must have a coding error
            raise RuntimeError('Splitter tuple has only 2 entries but auto target is turned on!')

        # add splitter
        splitter_ws.addRow([start_time, stop_time, target])

        # add information
        if target not in target_set:
            info_ws.addRow([target, ''])
            target_set.add(target)
        # END-IF

    # END-FOR

    return True, (splitters_ws_name, info_ws_name)


def generate_event_filters_by_log(ws_name, splitter_ws_name, info_ws_name,
                                  min_time, max_time,
                                  log_name, min_log_value, max_log_value, log_value_interval,
                                  log_value_change_direction):
    """
    Generate event filter by log value
    Purpose: call Mantid GenerateEventsFilter to generate splitters workspace in AnalysisDataService
    Requirements:
        input workspace name points to an existing workspace
        splitters_ws_name and info_ws_name are string
        log_name is string
        minimum log value is smaller than maximum log value
    :param ws_name:
    :param splitter_ws_name:
    :param info_ws_name:
    :param min_time:
    :param max_time:
    :param log_name:
    :param min_log_value:
    :param max_log_value:
    :param log_value_interval:
    :param log_value_change_direction:
    :return: 2-tuple. (boolean, (string, string)).  Strings as (1) split workspace name and (2) information table
    """
    # Check requirements
    assert isinstance(ws_name, str), 'Workspace name must be a string but not %s.' % str(ws_name)
    src_ws = retrieve_workspace(ws_name)
    assert src_ws is not None, 'Workspace %s does not exist.' % ws_name

    assert isinstance(splitter_ws_name, str), 'SplittersWorkspace name must be a string.'
    assert isinstance(
        info_ws_name, str), 'Splitting information TableWorkspace name must be a string.'

    assert isinstance(log_name, str), 'Log name must be a string but not %s.' % type(log_name)

    # Call Mantid algorithm
    # default is to start from min_log_value and go up
    mantidapi.GenerateEventsFilter(InputWorkspace=ws_name,
                                   OutputWorkspace=splitter_ws_name, InformationWorkspace=info_ws_name,
                                   LogName=log_name,
                                   StartTime=min_time, StopTime=max_time,
                                   MinimumLogValue=min_log_value,
                                   MaximumLogValue=max_log_value,
                                   LogValueInterval=log_value_interval,
                                   FilterLogValueByChangingDirection=log_value_change_direction,
                                   LogValueTolerance=0)

    return True, (splitter_ws_name, info_ws_name)


def generate_processing_history(workspace_name, output_python_name):
    """
    Create a python file for the history of workspace
    :param workspace_name:
    :param output_python_name:
    :return:
    """
    datatypeutility.check_string_variable('Workspace name', workspace_name)
    datatypeutility.check_file_name(output_python_name, False, True, False, 'Output Python file')

    mantidapi.GeneratePythonScript(InputWorkspace=workspace_name,
                                   Filename=output_python_name,
                                   UnrollAll=True)

    return


def generate_event_filters_by_time(ws_name, splitter_ws_name, info_ws_name,
                                   start_time, stop_time, delta_time, time_unit):
    """
    Generate event filters by time interval
    Purpose: Generate splitters by calling Mantid's GenerateEventsFilter
    Requirements:
    :param ws_name:
    :param splitter_ws_name:
    :param info_ws_name:
    :param start_time:
    :param stop_time:
    :param delta_time:
    :param time_unit:
    :return: 2-tuple. (1) boolean (2) message
    """
    # Check requirements
    assert isinstance(ws_name, str), 'Workspace name must be a string but not %s.' % str(ws_name)
    src_ws = retrieve_workspace(ws_name)
    assert src_ws is not None, 'Workspace %s does not exist.' % ws_name

    assert isinstance(splitter_ws_name, str), 'SplittersWorkspace name must be a string.'
    assert isinstance(
        info_ws_name, str), 'Splitting information TableWorkspace name must be a string.'

    # define optional inputs
    my_arg_dict = dict()
    my_arg_dict['InputWorkspace'] = ws_name
    my_arg_dict['OutputWorkspace'] = splitter_ws_name
    my_arg_dict['InformationWorkspace'] = info_ws_name
    if start_time is not None:
        my_arg_dict['StartTime'] = '%.15E' % start_time
    if stop_time is not None:
        my_arg_dict['StopTime'] = '%.15E' % stop_time
    if delta_time is not None:
        my_arg_dict['TimeInterval'] = delta_time

    if time_unit is None or time_unit.lower().startswith('second'):
        # more flexible to set time unit as Seconds
        time_unit = 'Seconds'
    my_arg_dict['UnitOfTime'] = time_unit

    try:
        mantidapi.GenerateEventsFilter(**my_arg_dict)
    except RuntimeError as e:
        return False, str(e)
    except ValueError as value_err:
        print('[ERROR] Workspace {} exists = {}'.format(ws_name, workspace_does_exist(ws_name)))
        if workspace_does_exist(ws_name):
            print('[ERROR] Workspace {} ID = {}'.format(ws_name, retrieve_workspace(ws_name).id()))
        return False, str(value_err)

    return True, ''


def get_ads_memory(unit='MB'):
    """ calculate the memory of all the workspace in ADS.
    Note that it is an estimate of how much memory used by PyVDrive.  In some case, it is different from
    what system monitor gives
    :param unit: unit of memory.  By default it is MB
    :return: memory size (float) in Bytes, KB or MB depending on unit
    """
    total_mem = 0
    for ws_name in ADS.getObjectNames():
        wksp = ADS[ws_name]
        total_mem += wksp.getMemorySize()

    datatypeutility.check_string_variable('Memory unit', unit, ['MB', 'KB', 'B'])

    if unit == 'MB':
        total_mem = total_mem / 1024.0**2
    elif unit == 'KB':
        total_mem = total_mem / 1024
    else:
        total_mem = float(total_mem)

    return total_mem


def get_run_start(workspace, time_unit):
    """ Get run start time from proton charge or sample log run_start
    :param workspace:
    :param time_unit: nanosecond(s), second(s), None
    :return: int (nanoseconds), float (second), datetime.datetime (None)
    """
    # get workspace
    if isinstance(workspace, str):
        if ADS.doesExist(workspace):
            workspace = ADS.retrieve(workspace)
        else:
            raise RuntimeError(
                'Workspace %s does not exist in Mantid AnalysisDataService.' % workspace)
    # END-IF

    # get run start from proton charge
    pcharge_log = None
    try:
        pcharge_log = workspace.run().getProperty('proton_charge')
    except AttributeError:
        pass
    except RuntimeError:
        pass

    if time_unit is None:
        if pcharge_log:
            pcharge_time0 = pcharge_log.times[0]
            start_date = str(pcharge_time0)
        else:
            try:
                start_date = workspace.run().getProperty('run_start').value
            except RuntimeError as run_err:
                raise RuntimeError('Workspace {} has neither proton_charge nor run_start in sample log.'
                                   'Unable to get run start from it due to {}'.format(str(workspace),
                                                                                      run_err))
        # END-IF

        # example: '2018-05-28T15:04:33.540623666-0400' or 2018-05-28T19:04:33.540623666'
        terms = start_date.split('T')[0].split('-')
        year = int(terms[0])
        month = int(terms[1])
        date = int(terms[2])
        run_start = datetime.datetime(year, month, date)

    elif pcharge_log:
        # convert to seconds or nanoseconds
        # Get first value in proton charge's time as run start
        pcharge_time0 = pcharge_log.firstTime()
        run_start_ns = pcharge_time0.totalNanoseconds()

        # check time unit
        datatypeutility.check_string_variable(
            'Time Unit', time_unit, allowed_values=['nanosecond', 'second'])

        # Convert unit if
        if time_unit.lower().startswith('nanosecond'):
            run_start = run_start_ns
        elif time_unit.lower().startswith('second'):
            run_start = run_start_ns * 1.E-9
        else:
            raise RuntimeError('Impossible to reach')
    else:
        raise RuntimeError(
            'Proton charge log must exist for run start in absolute time (second/nano second)')
    # END-IF-ELSE

    return run_start


def get_run_stop(workspace, time_unit, is_relative):
    """
    Get the run stop time from a workspace
    :param workspace:
    :param time_unit:
    :param is_relative:
    :return:
    """
    if isinstance(workspace, str):
        workspace = retrieve_workspace(workspace, True)

    # get run start from proton charge
    try:
        pcharge_log = workspace.run().getProperty('proton_charge')
    except (AttributeError, RuntimeError) as error:
        raise RuntimeError(
                'Unable to access proton_charge log in given workspace {}: {}'.format(workspace, error))

    if pcharge_log.size() == 0:
        raise RuntimeError('Workspace {} has an empty proton charge log.  Unable to determine run stop'
                           ''.format(workspace))

    run_stop_time = pcharge_log.times[-1]

    if is_relative:
        run_start_time = pcharge_log.times[0]
        run_stop_time = float(run_stop_time - run_start_time)
        if time_unit == 'second':
            run_stop_time *= 1.E-9

    return run_stop_time


def get_sample_log_tsp(src_workspace, sample_log_name):
    """
    get the reference to the sample log
    :param src_workspace:
    :return:
    """
    workspace = retrieve_workspace(src_workspace)
    if workspace is None:
        raise RuntimeError('Workspace {0} does not exist in ADS.'.format(sample_log_name))

    run = workspace.run()
    assert isinstance(sample_log_name, str), 'sample log name {0} must be a string but not a {1}.' \
                                             ''.format(sample_log_name, type(sample_log_name))
    if run.hasProperty(sample_log_name):
        tsp_property = run.getProperty(sample_log_name)
    else:
        raise RuntimeError('Workspace {0} does not have property {1}. Property list: {2}.'
                           ''.format(src_workspace, sample_log_name, get_sample_log_names(src_workspace)))

    return tsp_property


def get_sample_log_info(src_workspace):
    """ Ger sample log information including size of log and name of log
    :param src_workspace: workspace which the sample logs are from
    :return: a list of 2-tuples as property's length and name
    """
    run = src_workspace.run()

    prop_info_list = list()
    for property_i in run.getProperties():
        if isinstance(property_i, mantid.kernel.FloatTimeSeriesProperty) or \
                isinstance(property_i, mantid.kernel.Int32TimeSeriesProperty) or \
                isinstance(property_i, mantid.kernel.Int64TimeSeriesProperty):
            p_name = property_i.name
            size = property_i.size()
            prop_info_list.append((size, p_name))
    # END-FOR

    prop_info_list.sort()

    return prop_info_list


def get_sample_log_names(src_workspace, smart=False):
    """
    From workspace get sample log names as FloatTimeSeriesProperty
    :param src_workspace:
    :param smart:
    :return: list of strings
    """
    # check input
    if isinstance(src_workspace, str):
        # very likely the input is workspace name
        if not ADS.doesExist(src_workspace):
            raise RuntimeError(
                'Workspace %s does not exist in AnalysisDataService.' % src_workspace)
        src_workspace = ADS.retrieve(src_workspace)

    # get the Run object
    run_obj = src_workspace.run()
    property_list = run_obj.getProperties()
    name_list = list()
    single_value_log_list = list()

    for item in property_list:
        # rule out any Non-FloatTimeSeriesProperty
        if not isinstance(item, mantid.kernel.FloatTimeSeriesProperty):
            continue

        # get log name
        log_name = item.name
        if not smart:
            # non-smart mode, just simply log name
            name_list.append(log_name)
        else:
            log_size = item.size()
            if log_size > 1:
                name_list.append('%s (%d)' % (log_name, log_size))
            else:
                single_value_log_list.append('%s (1)' % log_name)
        # END-IF-ELSE
    # END-FOR

    name_list.extend(single_value_log_list)

    return name_list


def get_sample_log_value_single(src_workspace, sample_log_name):
    """

    :param src_workspace:
    :param sample_log_name:
    :return:
    """
    meta_ws = retrieve_workspace(src_workspace, True)

    log_value = meta_ws.getRun().getProperty(sample_log_name).value

    return log_value


def get_sample_log_value(src_workspace, sample_log_name, start_time, stop_time, relative):
    """
    Get sample log value
    :param src_workspace:
    :param sample_log_name:
    :return: 2-tuple.  vector of epoch time in unit of second. vector of log value
    """
    # Check
    datatypeutility.check_string_variable('Sample log name', sample_log_name)
    if isinstance(src_workspace, str):
        src_workspace = retrieve_workspace(src_workspace, True)

    if start_time is None and stop_time is None:
        # access sample log directly
        try:
            log_property = src_workspace.run().getProperty(sample_log_name)
        except KeyError as key_err:
            raise RuntimeError('Unable to locate sample log {}: {}'.format(
                sample_log_name, key_err))

        vec_times = log_property.times
        vec_value = log_property.value

        if relative:
            # relative time: get run 0
            run_start = src_workspace.run().getProperty('proton_charge').times[0]
            vec_times = (vec_times - run_start).astype('float') * 1.E-9
        else:
            vec_times = vec_times[:]
        # END-IF
        vec_value = vec_value[:]  # copy data for reference safe

    else:
        # need part of sample logs
        # Form args
        args = dict()
        if start_time is not None:
            args['StartTime'] = start_time
        if stop_time is not None:
            args['StopTime'] = stop_time

        # Call
        temp_out_ws_name = str(src_workspace) + '_' + sample_log_name
        mantidapi.ExportTimeSeriesLog(InputWorkspace=src_workspace,
                                      OutputWorkspace=temp_out_ws_name,
                                      LogName=sample_log_name,
                                      UnitOfTime='Seconds',
                                      OutputAbsoluteTime=not relative,
                                      IsEventWorkspace=False,
                                      **args)

        out_ws = mantid.AnalysisDataService.retrieve(temp_out_ws_name)

        # copy the vector of X (time) and Y (value) for returning
        # FUTURE - what if the returned values are the reference to the vectors in workspace?
        vec_times = out_ws.readX(0)[:]
        vec_value = out_ws.readY(0)[:]
    # END-IF-ELSE

    return vec_times, vec_value


def get_data_banks(workspace_name, start_bank_id=1):
    """
    get bank number
    :param workspace_name:
    :param start_bank_id:
    :return:
    """
    # Requirements
    assert isinstance(workspace_name, str), 'Input workspace name {0} must be a string but not a {1}.' \
                                            ''.format(workspace_name, type(workspace_name))
    assert workspace_does_exist(workspace_name), 'Workspace %s does not exist.' % workspace_name

    workspace = retrieve_workspace(workspace_name)
    if workspace.id() == 'WorkspaceGroup':
        num_hist = len(workspace)
    else:
        num_hist = workspace.getNumberHistograms()

    bank_list = range(start_bank_id, start_bank_id + num_hist)

    return bank_list


def get_data_from_workspace(workspace_name, bank_id=None, target_unit=None, point_data=True, start_bank_id=1,
                            keep_untouched=True):
    """
    Purpose: get data from a workspace
    Requirements: a valid matrix workspace is given.
    Guarantees: transform all the data to 1-dimension arrays.   If the current unit is not same as target unit,
                then the workspace's unit will be converted
    :param workspace_name:
    :param bank_id: integer, ID of the bank to get data from; If left None, then return all banks
    :param target_unit: TOF or dSpacing or None (i.e., using current one)
    :param point_data: If point data is true, then the output arrays must have equal sizes of x and y arrays
    :param start_bank_id:
    :param keep_untouched: Flag for not changing the original workspace
    :return: a 2-tuple:
             (1) a dictionary of 3-array-tuples (x, y, e). KEY = bank ID
             (2) unit of the returned data
    """
    # check requirements by asserting
    datatypeutility.check_string_variable('Workspace name', workspace_name, None)
    datatypeutility.check_bool_variable('Point data flag', point_data)
    if target_unit is not None:
        datatypeutility.check_string_variable('Target unit (can be None)', target_unit, None)
    datatypeutility.check_int_variable(
        'Starting bank ID (min Bank ID value)', start_bank_id, (0, None))

    if not workspace_does_exist(workspace_name):
        raise RuntimeError('Workspace %s does not exist.' % workspace_name)

    # check bank ID not being None: input spectra
    if bank_id is None:
        required_workspace_index = None
    else:
        workspace = retrieve_workspace(workspace_name)
        num_specs = get_number_spectra(workspace)
        required_workspace_index = bank_id - start_bank_id
        if not 0 <= required_workspace_index < num_specs:
            raise RuntimeError('Bank ID {0}, aka workspace index {1} is out of spectra of workspace {2}.'
                               ''.format(bank_id, required_workspace_index, workspace_name))
    # END-IF-ELSE

    # if is_a_workspace(workspace_name):
    #     # grouping workspace, then choose the right one
    #     if bank_id is None:
    #         raise RuntimeError('Bank ID None does not work with {} as a WorkspaceGroup'.format(workspace_name))
    # else:
    #     # regular single workspace
    #     if bank_id is None:
    #         # all banks
    #         required_workspace_index = None
    #     else:
    #         #  single bank
    #         datatypeutility.check_int_variable('Bank ID', bank_id, (1, None))
    #         required_workspace_index = bank_id - start_bank_id
    #         workspace = retrieve_workspace(workspace_name)
    #         if not 0 <= required_workspace_index < get_number_spectra(workspace):
    #             raise RuntimeError('Bank ID {0}, aka workspace index {1} is out of spectra of workspace {2}.'
    #                                ''.format(bank_id, required_workspace_index, workspace_name))
    #     # END-IF
    # # END-IF-ELSE

    # Process unit
    # about: target unit shall be converted to standard name
    if target_unit is not None:
        if target_unit.lower() == 'tof':
            target_unit = 'TOF'
        elif target_unit.lower().count('spac') > 0:
            target_unit = 'dSpacing'
        elif target_unit.lower() == 'q':
            target_unit = 'MomentumTransfer'
    # END-IF

    # define a temporary workspace name:
    if keep_untouched:
        temp_ws_name = workspace_name + '__{0}'.format(random.randint(1, 100000))
    else:
        temp_ws_name = workspace_name
    orig_ws_name = workspace_name   # workspace name can be used for temporary workspace

    # get unit
    current_unit = get_workspace_unit(workspace_name)
    if target_unit is not None and target_unit != current_unit:
        # convert unit if the specified target unit is different
        try:
            mantidapi.ConvertUnits(InputWorkspace=workspace_name, OutputWorkspace=temp_ws_name,
                                   Target=target_unit)
        except RuntimeError as run_err:
            raise RuntimeError('Convert units of workspace {} to {} failed due to {}'
                               ''.format(workspace_name, target_unit, run_err))
        current_unit = target_unit
        workspace_name = temp_ws_name
    # END-IF

    # Convert to point data by checking
    workspace = retrieve_workspace(workspace_name)
    if workspace.id() == 'WorkspaceGroup':
        # space group
        if workspace[0].isHistogramData():
            mantidapi.ConvertToPointData(InputWorkspace=workspace_name,
                                         OutputWorkspace=temp_ws_name)
        else:
            temp_ws_name = workspace_name
        # END-IF
    else:
        # single group
        num_bins_set = set()
        for iws in range(get_number_spectra(workspace)):
            num_bins_set.add(len(workspace.readY(iws)))
        # END-FOR

        if point_data and workspace.isHistogramData() and len(num_bins_set) == 1:
            # requiring point data and input is histogram data and number of bins are same for all spectra
            mantidapi.ConvertToPointData(InputWorkspace=workspace_name,
                                         OutputWorkspace=temp_ws_name)
        elif point_data and workspace.isHistogramData() and len(num_bins_set) > 1:
            raise NotImplementedError('Mantid does not support convert workspace with non-common-bins to point '
                                      'data.')
        else:
            temp_ws_name = workspace_name
        # END-IF
    # END-IF
    # set to workspace: workspace_name
    workspace_name = temp_ws_name

    # Get data: 2 cases as 1 bank or all banks
    workspace = retrieve_workspace(workspace_name)
    is_group = workspace.id() == 'WorkspaceGroup'
    num_spec = get_number_spectra(workspace)
    print('[DB........................BAT] Workspace {}: # spec = {}, required index = {}, start bank id = {}'
          ''.format(workspace_name, num_spec, required_workspace_index, start_bank_id))
    data_set_dict = dict()
    for ws_index in range(num_spec):
        if bank_id is None or ws_index == required_workspace_index:
            if is_group:
                curr_ws = workspace[ws_index]
                vec_x = curr_ws.readX(0)
                vec_y = curr_ws.readY(0)
                vec_e = curr_ws.readE(0)
            else:
                curr_ws = workspace
                vec_x = curr_ws.readX(ws_index)
                vec_y = curr_ws.readY(ws_index)
                vec_e = curr_ws.readE(ws_index)
            # END-IF

            # convert to numpy array
            size_x = len(vec_x)
            size_y = len(vec_y)

            data_x = numpy.ndarray((size_x,), 'float')
            data_y = numpy.ndarray((size_y,), 'float')
            data_e = numpy.ndarray((size_y,), 'float')

            data_x[:] = vec_x[:]
            data_y[:] = vec_y[:]
            data_e[:] = vec_e[:]

            print('[DB...BAT] ws_index = {}, required index = {}, start bank id = {}'
                  ''.format(ws_index, required_workspace_index, start_bank_id))
            data_set_dict[ws_index + start_bank_id] = data_x, data_y, data_e
        # END-IF
    # END-FOR

    # clean the temporary workspace
    if workspace_name != orig_ws_name:
        delete_workspace(workspace_name)

    return data_set_dict, current_unit


def get_number_spectra(workspace):
    """ Get number of histograms/spectra from a single-multi-spectra workspace or a WorkspaceGroup containing a
    set of single spectrum workspaces
    :param workspace:
    :return:
    """
    if workspace.id() == 'WorkspaceGroup':
        num_spec = len(workspace)
    else:
        num_spec = workspace.getNumberHistograms()

    return num_spec


def get_detectors_in_roi(mask_ws_name):
    """

    :param mask_ws_name:
    :return:
    """
    if not is_masking_workspace(mask_ws_name):
        raise RuntimeError('Not MaskingWorkspace {0}'.format(mask_ws_name))

    mask_ws = ADS.retrieve(mask_ws_name)

    det_id_list = list()
    for iws in range(mask_ws.getNumberHistograms()):
        # get ROI
        if mask_ws.readY(iws)[0] < 0.9:
            det_id_i = mask_ws.getDetector(iws).getID()
            det_id_list.append(det_id_i)
    # END-FOR
    # print (len(det_id_list))
    # print (mask_ws.getNumberHistograms() - len(det_id_list))
    # print (mask_ws.getNumberMasked())

    return det_id_list


def get_ipts_number(input):
    """
    get IPTS number from a standard EventWorkspace
    :param input: run number or string
    :return:
    """
    if isinstance(input, str):
        # workspace name
        ws_name = input
        workspace = retrieve_workspace(ws_name)
        if not workspace.run().hasProperty('Filename'):
            return None

        # get file name
        file_name = workspace.run().getProperty('Filename').value

        status, ret_obj = vdrivehelper.get_ipts_number_from_dir(ipts_dir=file_name)
        if status:
            ipts_number = ret_obj
        else:
            ipts_number = None
    elif isinstance(input, int):
        # run number
        run_number = input
        ipts_number = mantidapi.GetIPTS(Instrument='VULCAN', RunNumber=run_number)
    else:
        # not supported
        raise TypeError('Input {} of type {} is either a workspace name (str) nor a run number (int)'
                        ''.format(input, type(input)))

    return ipts_number


def get_time_segments_from_splitters(split_ws_name, time_shift, unit):
    """ Get time segments from splitters workspace
    Purpose:
        Get the time segments from a splitters workspace
    Requirements:
        - a valid splitters workspace
        - time shift is float
        - unit is either nanosecond or second
    :param split_ws_name:
    :param time_shift: always in the same unit as
    :param unit:
    :return: a list of 3 tuples as float (start time), float (stop time) and integer (target)
    """
    # Check input
    split_ws = retrieve_workspace(split_ws_name)
    assert split_ws, 'Workspace %s does not exist.' % split_ws_name

    segment_list = list()
    if unit == 'Seconds':
        factor = 1.E-9
    else:
        factor = 1

    num_rows = split_ws.rowCount()
    for i_row in range(num_rows):
        # Get original data
        start_time = split_ws.cell(i_row, 0)
        stop_time = split_ws.cell(i_row, 1)
        target = split_ws.cell(i_row, 2)

        # calibrated by time shift
        start_time = start_time * factor - time_shift
        stop_time = stop_time * factor - time_shift

        segment_list.append((start_time, stop_time, target))
    # END-FOR(i_row)

    return segment_list


def get_workspace_information(run_ws_name):
    """
    Purpose: Get bank information from a workspace in analysis data service
    Requirements: Workspace name is a string for an existing workspace in analysis data service
    Guarantees: a list of banks
    :param run_ws_name:
    :return: list of bank ID, [1, 2, ...]
    """
    # Check requirements
    assert isinstance(run_ws_name, str), 'Input workspace name should be a string but not %s.' % str(
        type(run_ws_name))
    assert workspace_does_exist(run_ws_name), 'Workspace %s does not exist.' % run_ws_name

    # Retrieve workspace and get bank list (bank number is from 1)
    workspace = retrieve_workspace(run_ws_name)
    # num_spec = workspace.getNumberHistograms()
    num_spec = get_number_spectra(workspace)
    bank_id_list = range(1, num_spec+1)

    return bank_id_list


def get_workspace_property(workspace_name, property_name, value_in_str=False):
    """get a property's handler from a workspace's run object
    :param workspace_name:
    :param property_name:
    :param value_in_str: flag for returned value. True: return property's value as a string. False: property instance
    :return: a string (value of property) or an instance of property
    """
    # check
    datatypeutility.check_string_variable('Workspace name', workspace_name)
    datatypeutility.check_string_variable('Property name', property_name)

    workspace = retrieve_workspace(workspace_name)

    if value_in_str:
        return workspace.run().getProperty(property_name).value

    return workspace.run().getProperty(property_name)


def get_workspace_unit(workspace_name):
    """ get the unit of a workspace
    :param workspace_name:
    :return:
    """
    datatypeutility.check_string_variable('Workspace name', workspace_name)
    if workspace_name == '':
        raise RuntimeError('mantid_helper.get_workspace_unit(): workspace name cannot be empty')
    if not ADS.doesExist(workspace_name):
        raise RuntimeError('mantid_helper.get_workspace_unit(): Workspace {0} cannot be found in ADS.'
                           .format(workspace_name))

    workspace = ADS.retrieve(workspace_name)
    if workspace.id() == 'WorkspaceGroup':
        workspace = workspace[0]

    return workspace.getAxis(0).getUnit().unitID()


def event_data_ws_name(run_number):
    """ workspace name for raw event data
    :param run_number:
    :return:
    """
    return 'VULCAN_%d_Raw' % run_number


def get_filter_events_outputs(result, excluding_unfiltered=True):
    """ get the output workspace names from FilterEvents
    :param result:  return from FilterEvents
    :param excluding_unfiltered: flag to exclude the events no in any event filters
    :return: workspace names in the order as being returned from FilterEvents
    """
    output_names = None
    for r in result:
        if isinstance(r, int):
            # other returns
            continue
        elif isinstance(r, list):
            output_names = r
            # process the output workspaces
            num_outputs = len(output_names)
            for i_ws in range(num_outputs - 1, -1, -1):
                ws_name = output_names[i_ws].strip()
                if ws_name == '':
                    # remove the empty string in returned workspace names
                    output_names.pop(i_ws)
                elif ws_name.lower().endswith('_unfiltered') and excluding_unfiltered:
                    # remove unfiltered
                    output_names.pop(i_ws)
            # END-FOR
        else:
            continue
        # END-IF-ELSE
    # END-IF

    return output_names


def get_standard_ws_name(file_name, meta_only):
    """
    Get the standard name for a loaded workspace
    Requirements: file name is a string
    :param file_name:
    :param meta_only:
    :return:
    """
    datatypeutility.check_string_variable('File name', file_name)

    ws_name = os.path.basename(file_name).split('.')[0]
    file_type = os.path.basename(file_name).split('.')[1]
    if file_type.lower() == 'gsa' or file_type.lower() == 'gda':
        ws_name += '_gda'

    if meta_only is True:
        ws_name += '_Meta'

    return ws_name


def get_split_workpsace_base_name(run_number, out_base_name, instrument_name='VULCAN'):
    """
    Workspace name for split event data
    :param run_number:
    :param out_base_name:
    :param instrument_name: name of the instrument
    :return:
    """
    assert isinstance(run_number, int), 'Run number must be an integer but not of type %s.' % str(
        type(run_number))
    assert isinstance(out_base_name, str), 'Output base workpsace name must be a string but not %s.' % \
                                           str(type(out_base_name))
    assert isinstance(instrument_name, str), 'Instrument name must be a string but not %s.' % str(
        type(instrument_name))

    return '%s_%d_%s' % (instrument_name, run_number, out_base_name)


def is_a_workspace(workspace_name):
    """
    check whether a string is a workspace
    :param workspace_name:
    :return:
    """
    datatypeutility.check_string_variable('Workspace name', workspace_name)

    if ADS.doesExist(workspace_name):
        return True

    return False


def is_calibration_workspace(workspace_name):
    """
    check whether a workspace is a calibration workspace, which is in fact a TableWorkspace
    :param workspace_name:
    :return:
    """
    if is_a_workspace(workspace_name):
        event_ws = retrieve_workspace(workspace_name)
        return event_ws.id() == CALIBRATION_WORKSPACE_ID

    return False


def is_event_workspace(workspace_name):
    """
    Check whether a workspace, specified by name, is an event workspace
    :param workspace_name:
    :return:
    """
    if is_a_workspace(workspace_name):
        event_ws = retrieve_workspace(workspace_name)
        return event_ws.id() == EVENT_WORKSPACE_ID

    return False


def is_grouping_workspace(workspace_name):
    """
    check whether a workspace is a grouping workspace
    :param workspace_name:
    :return:
    """
    if is_a_workspace(workspace_name):
        group_ws = retrieve_workspace(workspace_name)
        return group_ws.id() == GROUPING_WORKSPACE_ID

    return False


def is_workspace_group(group_name):
    ws_group = retrieve_workspace(group_name)

    return ws_group.id() == 'WorkspaceGroup'


def is_masking_workspace(workspace_name):
    """
    check whether a workspace is a mask workspace
    :param workspace_name:
    :return:
    """
    if is_a_workspace(workspace_name):
        mask_ws = retrieve_workspace(workspace_name)
        return mask_ws.id() == MASK_WORKSPACE_ID

    return False


def is_matrix_workspace(workspace_name):
    """
    check whether a workspace is a MatrixWorkspace
    :param workspace_name:
    :return:
    """
    if is_a_workspace(workspace_name):
        matrix_workspace = retrieve_workspace(workspace_name)
        is_matrix = matrix_workspace.id() == EVENT_WORKSPACE_ID or matrix_workspace.id() == WORKSPACE_2D_ID
        return is_matrix

    return False


def convert_gsas_ws_to_group(ws_name):
    """

    :param ws_name:
    :return:
    """
    single_ws_name_list = list()

    # for the rest of the spectra
    orig_ws = retrieve_workspace(ws_name)
    for iws in range(orig_ws.getNumberHistograms()):
        # extract, convert to point data, conjoin and clean
        temp_out_name_i = '{}_B{:04}'.format(ws_name, iws+1)
        print('[DB...BAt 1377] Extract {} To {}'.format(ws_name, temp_out_name_i))
        mantidapi.ExtractSpectra(ws_name, WorkspaceIndexList=[iws], OutputWorkspace=temp_out_name_i)
        single_ws_name_list.append(temp_out_name_i)
    # END-IF

    # remove original workspace
    mantidapi.DeleteWorkspace(ws_name)

    # group
    mantidapi.GroupWorkspaces(InputWorkspaces=single_ws_name_list, OutputWorkspace=ws_name)

    return retrieve_workspace(ws_name)


def load_gsas_file(gss_file_name, out_ws_name, standard_bin_workspace):
    """ Load VULCAN GSAS file and set instrument information.
    Output workspace will be set to PointData
    Optionally:
    (1) as 2-bank VULCAN and convert units to d-spacing
    Requirements: GSAS file name is a full path; output workspace name is a string;
    Guarantees:
    :param gss_file_name:
    :param out_ws_name:
    :param standard_bin_workspace: binning template workspace. It can be None for not aligning
    :return: output workspace name
    """
    from pyvdrive.core import reduce_VULCAN

    # TEST/ISSUE/NOW - Implement feature with standard_bin_workspace...
    # Check
    datatypeutility.check_file_name(gss_file_name, True, False, False, 'GSAS file')
    datatypeutility.check_string_variable('Output workspace name', out_ws_name)
    if len(out_ws_name) == 0:
        raise RuntimeError('Caller-specified output workspace name for GSAS file cannot be empty')

    # Load GSAS
    try:
        mantidapi.LoadGSS(Filename=gss_file_name, OutputWorkspace=out_ws_name)
    except IndexError as index_error:
        raise RuntimeError('GSAS {0} is corrupted. FYI: {1}'.format(gss_file_name, index_error))
    gss_ws = retrieve_workspace(out_ws_name)
    if gss_ws is None:
        raise RuntimeError('Output workspace {} of {} cannot be found in ADS'.format(
            out_ws_name, gss_file_name))

    # set instrument geometry: this is for VULCAN-only
    num_spec = gss_ws.getNumberHistograms()
    if num_spec == 2:
        # before nED, no high angle detector
        mantidapi.EditInstrumentGeometry(Workspace=out_ws_name,
                                         PrimaryFlightPath=43.753999999999998,
                                         SpectrumIDs='1,2',
                                         L2='2.00944,2.00944',
                                         Polar='90,270')
    elif num_spec == 3:
        # after nED, with high angle detector
        print('[SpecialDebug] Edit Instrument: {0}'.format(out_ws_name))
        mantidapi.EditInstrumentGeometry(Workspace=out_ws_name,
                                         PrimaryFlightPath=43.753999999999998,
                                         SpectrumIDs='1,2,3',
                                         L2='2.0,2.0,2.0',
                                         Polar='-90,90,{}'.format(HIGH_ANGLE_BANK_2THETA))
    else:
        raise RuntimeError('It is not implemented for GSAS file having more than 3 spectra ({0} now).'
                           ''.format(num_spec))

    # convert to workspace group
    convert_gsas_ws_to_group(out_ws_name)

    # convert unit and to point data
    if standard_bin_workspace is not None and num_spec == 2:
        assert isinstance(standard_bin_workspace, str) or standard_bin_workspace is None, \
            'Standard binning workspace {0} must be either a string or None but not a {1}.' \
            ''.format(standard_bin_workspace, type(standard_bin_workspace))
        reduce_VULCAN.align_bins(out_ws_name, standard_bin_workspace)
        mantidapi.ConvertUnits(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name,
                               Target='dSpacing')
    # END-IF

    return out_ws_name


def load_grouping_file(grouping_file_name, grouping_ws_name):
    """
    Load a detector grouping file (saved by SaveDetectorsGroupingFile) to a GroupingWorkspace
    :param grouping_file_name:
    :param grouping_ws_name:
    :return:
    """
    # check input
    datatypeutility.check_file_name(grouping_file_name, check_exist=True,
                                    check_writable=False, is_dir=False, note='Detector grouping file')
    datatypeutility.check_string_variable('Nmae of GroupingWorkspace to load {} to'.format(grouping_file_name),
                                          grouping_ws_name)

    mantid.simpleapi.LoadDetectorsGroupingFile(InputFile=grouping_file_name,
                                               OutputWorkspace=grouping_ws_name)

    return


def load_calibration_file(calib_file_name, output_name, ref_ws_name, load_cal=False):
    """
    load calibration file
    :param calib_file_name:
    :param output_name: this is NOT calibration workspace name but the root name for calib, mask and group
    :param ref_ws_name:
    :return: (1) output workspaces (2) output offsets workspace (as LoadDiffCal_returns cannot have an arbitrary member)
    """
    # check
    datatypeutility.check_file_name(calib_file_name, check_exist=True, check_writable=False, is_dir=False,
                                    note='Calibration file')
    datatypeutility.check_string_variable(
        'Calibration/grouping/masking workspace name', output_name)

    # determine file names
    diff_cal_file = None   # new .h5 file
    offset_cal_file = None   # old .cal file
    if calib_file_name.endswith('.h5'):
        diff_cal_file = calib_file_name
        if load_cal:
            offset_cal_file = diff_cal_file.replace('.h5', '.cal')
            if not os.path.exists(offset_cal_file):
                raise RuntimeError('User intends to load {1} along with {0}.  But {1} cannot be found.'
                                   ''.format(diff_cal_file, offset_cal_file))
        # END-IF
    elif calib_file_name.endswith('.cal'):
        offset_cal_file = calib_file_name
    else:
        raise RuntimeError('Calibration file {} does not end with .h5 or .dat.  Unable to support'
                           ''.format(calib_file_name))

    # Load files
    if offset_cal_file:
        # old style calibration file
        outputs_cal = mantidapi.LoadCalFile(CalFilename=offset_cal_file,
                                            InstrumentName='VULCAN',
                                            WorkspaceName=output_name)
    else:
        outputs_cal = None

    if diff_cal_file:
        # new diff calib file
        outputs = mantidapi.LoadDiffCal(InputWorkspace=ref_ws_name,
                                        Filename=diff_cal_file,
                                        WorkspaceName=output_name)
    else:
        outputs = None

    # set up output
    if outputs is None:
        outputs = outputs_cal
        offset_ws = outputs_cal.OutputOffsetsWorkspace
    elif outputs_cal is not None:
        offset_ws = outputs_cal.OutputOffsetsWorkspace
    else:
        offset_ws = None

    return outputs, offset_ws


def load_mask_xml(data_ws_name, mask_file_name, mask_ws_name=None):
    """
    load Mantid compatible masking file in XML format
    :param data_ws_name:
    :param mask_file_name:
    :param mask_ws_name:
    :return:
    """
    datatypeutility.check_file_name(mask_file_name, check_exist=True, note='ROI XML file')
    if not is_matrix_workspace(data_ws_name):
        raise RuntimeError('Workspace {0} is not a MatrixWorkspace in ADS.'.format(data_ws_name))

    if mask_ws_name is None:
        mask_ws_name = os.path.basename(mask_file_name).split('.')[0] + '_MASK'

    # load XML file: Mantid can recognize the ROI or mask file
    # In output workspace, 1 is for being masked
    mantidapi.LoadMask(Instrument='VULCAN',
                       RefWorkspace=data_ws_name,
                       InputFile=mask_file_name,
                       OutputWorkspace=mask_ws_name)

    return mask_ws_name


def load_nexus(data_file_name, output_ws_name, meta_data_only, max_time=None):
    """ Load NeXus file
    :param data_file_name:
    :param output_ws_name:
    :param meta_data_only:
    :param max_time: relative max time (stop time) to load from Event Nexus file in unit of seconds
    :return: 2-tuple
    """
    if meta_data_only:
        # load logs to an empty workspace
        out_ws = mantidapi.CreateWorkspace(DataX=[0], DataY=[0], DataE=[
                                           0], NSpec=1, OutputWorkspace=output_ws_name)
        try:
            mantidapi.LoadNexusLogs(Workspace=output_ws_name,
                                    Filename=data_file_name, OverwriteLogs=True)
        except RuntimeError as run_err:
            return False, 'Unable to load Nexus (log) file {} due to {}'.format(data_file_name, run_err)
    else:
        # regular workspace with data
        try:
            if not data_file_name.endswith('.h5'):
                out_ws = mantidapi.Load(Filename=data_file_name,
                                        OutputWorkspace=output_ws_name,
                                        MetaDataOnly=False)
            elif max_time is None:
                out_ws = mantidapi.LoadEventNexus(Filename=data_file_name,
                                                  OutputWorkspace=output_ws_name,
                                                  MetaDataOnly=False)
            else:
                out_ws = mantidapi.LoadEventNexus(Filename=data_file_name,
                                                  OutputWorkspace=output_ws_name,
                                                  FilterByTimeStop=max_time)

        except RuntimeError as e:
            return False, 'Unable to load Nexus file %s due to %s' % (data_file_name, str(e))
    # END-IF-ELSE

    return True, out_ws


def load_nexus_processed(nexus_name, workspace_name):
    """

    :param nexus_name:
    :param workspace_name:
    :return:
    """
    out_ws = mantidapi.LoadNexusProcessed(Filename=nexus_name,
                                          OutputWorkspace=workspace_name)

    return out_ws


def load_roi_xml(data_ws_name, roi_file_name, roi_ws_name=None):
    """
    load standard ROI XML file
    :param data_ws_name: name of the workspace to be masked
    :param roi_file_name:
    :param roi_ws_name: Region of interest workspace name
    :return: ROI workspace name
    """
    datatypeutility.check_file_name(roi_file_name, check_exist=True, note='ROI XML file')
    if not is_matrix_workspace(data_ws_name):
        raise RuntimeError('Workspace {0} is not a MatrixWorkspace in ADS.'.format(data_ws_name))

    if roi_file_name is None:
        roi_ws_name = os.path.basename(roi_file_name).split('.')[0] + '_ROI'
    else:
        datatypeutility.check_string_variable('ROI workspace name', roi_ws_name)

    # load XML file: Mantid can recognize the ROI or mask file
    # In output workspace, 1 is for being masked
    mantidapi.LoadMask(Instrument='VULCAN',
                       RefWorkspace=data_ws_name,
                       InputFile=roi_file_name,
                       OutputWorkspace=roi_ws_name)

    return roi_ws_name


def load_time_focus_file(instrument, time_focus_file, base_ws_name):
    """ Load time focus file (or say calibration in Mantid's nomenclature)
    :return:
    """
    # check
    assert isinstance(time_focus_file, str) and os.path.exists(
        time_focus_file), 'Time focus file error.'
    assert isinstance(base_ws_name, str), 'Base workspace name must be a string.'

    mantidapi.LoadCalFile(InstrumentName=instrument,
                          CalFilename=time_focus_file,
                          WorkspaceName=base_ws_name,
                          MakeGroupingWorkspace=True,
                          MakeOffsetsWorkspace=True,
                          MakeMaskWorkspace=True)

    offset_ws_name = '%s_offsets' % base_ws_name
    grouping_ws_name = '%s_group' % base_ws_name
    mask_ws_name = '%s_mask' % base_ws_name
    cal_ws_name = '%s_cal' % base_ws_name

    # Check existence of the workspaces output from LoadCalFile
    assert workspace_does_exist(offset_ws_name), 'Offset workspace does not exist.'
    assert workspace_does_exist(grouping_ws_name), 'Grouping workspace does not exist.'
    assert workspace_does_exist(mask_ws_name), 'Mask worksapce does not exist.'
    assert workspace_does_exist(cal_ws_name), 'Calibration worksapce does not exist.'

    return True, [offset_ws_name, grouping_ws_name, mask_ws_name, cal_ws_name]


def make_compressed_reduced_workspace(workspace_name_list, target_workspace_name):
    """
    add the all the workspaces given by their names to a target workspace with certain geometry
    prototype:
        ConjoinWorkspaces(InputWorkspace1='ws50', InputWorkspace2='ws60', CheckOverlapping=False)
        ConjoinWorkspaces(InputWorkspace1='ws50', InputWorkspace2='ws70', CheckOverlapping=False)
    :param workspace_name_list:
    :return:
    """
    # check inputs
    assert isinstance(target_workspace_name, str), 'Target workspace name {0} must be a string but not a {1}.' \
                                                   ''.format(target_workspace_name,
                                                             type(target_workspace_name))
    assert isinstance(workspace_name_list, list), 'Workspace names {0} must be given as a list but not a {1}.' \
                                                  ''.format(workspace_name_list,
                                                            type(workspace_name_list))
    if len(workspace_name_list) == 0:
        raise RuntimeError('Workspace name list is empty!')

    # get the workspace to get merged to
    # TEST/ISSUE/NOW - Need to verify
    if ADS.doesExist(target_workspace_name) is False:
        mantidapi.CloneWorkspace(
            InputWorkspace=workspace_name_list[0], OutputWorkspace=target_workspace_name)
        # add a new property to the target workspace for more information
        target_ws = retrieve_workspace(target_workspace_name)
        num_banks = target_ws.getNumberHistograms()
        target_ws.getRun().addProperty('Number of banks', num_banks, '', True)
    else:
        target_ws = retrieve_workspace(target_workspace_name)
        num_banks = int(target_ws.run().getProperty('Number of banks').value)

    # then do conjoin the workspace
    for i_workspace in range(1, len(workspace_name_list)):
        # check whether the input workspace has the same number of banks
        src_ws = retrieve_workspace(workspace_name_list[i_workspace])
        src_ws_banks = src_ws.getNumberHistograms()
        if src_ws_banks != num_banks:
            raise RuntimeError('Unable to conjoin workspace {0} to target workspace {1} due to unmatched '
                               'bank number ({2}).'.format(workspace_name_list[i_workspace], target_workspace_name,
                                                           src_ws_banks))

        # conjoin workspaces
        mantidapi.ConjoinWorkspaces(InputWorkspace1=target_workspace_name,
                                    InputWorkspace2=workspace_name_list[i_workspace],
                                    CheckOverlapping=False)
    # END-IF

    return target_workspace_name


# TODO/FIXME/TEST - ASAP
def mask_workspace(to_mask_workspace_name, mask_workspace_name):
    """
    mask a MatrixWorkspace
    :param to_mask_workspace_name:
    :param mask_workspace_name:
    :return:
    """
    # check inputs
    if not is_matrix_workspace(to_mask_workspace_name):
        raise RuntimeError(
            '{0} does not exist in ADS as a MatrixWorkspace'.format(to_mask_workspace_name))
    if not is_masking_workspace(mask_workspace_name):
        raise RuntimeError(
            '{0} does not exist in ADS as a MaskingWorkspace'.format(mask_workspace_name))

    # retrieve masked detectors
    mask_ws = retrieve_workspace(mask_workspace_name, raise_if_not_exist=True)
    detid_vector = mask_ws.getMaskedDetectors()

    # mask detectors
    mantidapi.MaskInstrument(InputWorkspace=to_mask_workspace_name,
                             OutputWorkspace=to_mask_workspace_name,
                             DetectorIDs=detid_vector)

    # clear masked spectra
    mantidapi.ClearMaskedSpectra(InputWorkspace=to_mask_workspace_name,
                                 OutputWorkspace=to_mask_workspace_name)

    return


def mask_workspace_by_detector_ids(to_mask_workspace_name, detector_ids):
    """

    :param to_mask_workspace_name:
    :param detector_ids:
    :return:
    """
    # mask detectors
    print('[DB...BAT] Mask {0} detectors.'.format(len(detector_ids)))
    # print ('[DB...BAT] Mask detectors:\n{0}'.format(detector_ids))
    mantidapi.MaskInstrument(InputWorkspace=to_mask_workspace_name,
                             OutputWorkspace=to_mask_workspace_name,
                             DetectorIDs=detector_ids)

    # clear masked spectra
    mantidapi.ClearMaskedSpectra(InputWorkspace=to_mask_workspace_name,
                                 OutputWorkspace=to_mask_workspace_name)

    return


def edit_compressed_chopped_workspace_geometry(ws_name):
    """
    set the geometry to the compressed workspace for chopped workspace
    prototype:
        EditInstrumentGeometry(Workspace='ws50', PrimaryFlightPath=50, L2='1,1,1,1,1,1', Polar='90,270,90,270,90,270')
    :param ws_name:
    :return:
    """
    # get workspace and check
    assert isinstance(ws_name, str), 'Workspace name {0} must be a string but not a {1}'.format(
        ws_name, type(ws_name))
    workspace = retrieve_workspace(ws_name)
    if workspace is None:
        raise RuntimeError('Chopped workspace {0} (name) cannot be found in ADS.'.format(ws_name))

    # check the number of banks
    num_banks = int(workspace.run().getProperty('Number of banks').value)
    num_spectra = workspace.getNumberHistograms()
    if num_banks == 1:
        l2_list = [VULCAN_1BANK_L2] * num_spectra
        polar_list = [VULCAN_1BANK_POLAR] * num_spectra
    elif num_banks == 2:
        if num_spectra % 2 != 0:
            raise RuntimeError(
                'It is impossible to have odd number of spectra in 2-bank compressed chopped workspace.')
        l2_list = [VULCAN_2BANK_1_L2, VULCAN_2BANK_2_L2] * (num_spectra/2)
        polar_list = [VULCAN_2BANK_1_POLAR,  VULCAN_2BANK_2_POLAR] * (num_spectra/2)
    else:
        raise RuntimeError('{0}-bank is not supported.'.format(num_spectra))

    # edit instrument geometry
    mantidapi.EditInstrumentGeometry(Workspace=ws_name,
                                     PrimaryFlightPath=VULCAN_L1,
                                     L2=str(l2_list).replace('[', '').replace(']', ''),
                                     Polar=str(polar_list).replace('[', '').replace(']', ''))

    return


def group_workspaces(input_ws_names, group_name):
    """ Group workspaces
    :param input_ws_names: list of names of the workspaces to be grouped
    :param group_name: target workspace group ame
    :return:
    """
    datatypeutility.check_list('Names of workspaces to group', input_ws_names)
    datatypeutility.check_string_variable('Target WorkspaceGroup name', group_name)

    input_ws_names_str = ''
    for index, ws_name in enumerate(input_ws_names):
        input_ws_names_str += '{},'.format(ws_name)
    input_ws_names_str = input_ws_names_str[:-1]  # remove last ','

    mantidapi.GroupWorkspaces(InputWorkspaces=input_ws_names_str, OutputWorkspace=group_name)

    return


def merge_runs(ws_name_list, out_ws_name):
    """
    Merge runs
    :param ws_name_list:
    :param out_ws_name:
    :return:
    """
    datatypeutility.check_list('Workspace names', ws_name_list)
    datatypeutility.check_string_variable('Output workspace name for merged runs', out_ws_name)

    # construct the workspaces
    input_ws_names = ''
    for ws_name in ws_name_list:
        input_ws_names += ws_name + ','
    input_ws_names = input_ws_names[:-1]

    mantidapi.MergeRuns(InputWorkspaces=input_ws_names, OutputWorkspace=out_ws_name)

    return


def map_sample_logs(meta_ws_name, log_name_x, log_name_y):
    """
    Map 2 sample logs by aligning them on the same time stamps
    :param meta_ws_name:
    :param log_name_x:
    :param log_name_y:
    :return: 3-tuple of vectors: (1) time, (2) log x, (3) log y
    """
    datatypeutility.check_string_variable('Meta data workspace', meta_ws_name)
    datatypeutility.check_string_variable('Name of log on X axis', log_name_x)
    datatypeutility.check_string_variable('Name of log on Y axis', log_name_y)

    if not ADS.doesExist(meta_ws_name):
        raise RuntimeError('Workspace {} for meta data does not exist'.format(meta_ws_name))
    sample_logs = get_sample_log_names(meta_ws_name, False)
    if not (log_name_x in sample_logs and log_name_y in sample_logs):
        raise RuntimeError('Sample log {} or {} does not exist in {}. Available logs are {}'
                           ''.format(log_name_x, log_name_y, meta_ws_name, sample_logs))

    mantidapi.ExportSampleLogsToCSVFile(InputWorkspace=meta_ws_name,
                                        OutputFilename='/tmp/test.dat',
                                        SampleLogNames=[log_name_x, log_name_y],
                                        WriteHeaderFile=False,
                                        TimeZone='UTC',
                                        Header='')

    from pyvdrive.core import vulcan_util

    log_set = vulcan_util.import_vulcan_log('/tmp/test.dat', header=None)  # no header

    return log_set[1].values, log_set[2].values, log_set[3].values


def mtd_compress_events(event_ws_name, tolerance=0.01):
    """ Call Mantid's CompressEvents algorithm
    :param event_ws_name:
    :param tolerance: default as 0.01 as 10ns
    :return:
    """
    # Check requirements
    assert isinstance(event_ws_name, str), 'Input event workspace name is not a string,' \
                                           'but is a %s.' % str(type(event_ws_name))
    event_ws = retrieve_workspace(event_ws_name)
    assert is_event_workspace(event_ws)

    mantidapi.CompressEvents(InputWorkspace=event_ws_name,
                             OutputWorkspace=event_ws_name,
                             Tolerance=tolerance)

    out_event_ws = retrieve_workspace(event_ws_name)
    assert out_event_ws

    return


def mtd_convert_units(ws_name, target_unit, out_ws_name=None):
    """
    Convert the unit of a workspace.
    Guarantees: if the original workspace is point data, then the output must be point data
    :param ws_name:
    :param target_unit:
    :return:
    """
    # Check requirements
    datatypeutility.check_string_variable('Input workspace name', ws_name)
    datatypeutility.check_string_variable('Unit to convert to', target_unit)
    if not workspace_does_exist(ws_name):
        raise RuntimeError('Workspace {} does not exist in ADS'.format(ws_name))

    if out_ws_name is None:
        out_ws_name = ws_name

    # Record whether the input workspace is histogram
    # if workspace.id() == 'WorkspaceGroup':
    #     is_histogram = workspace[0]
    # else:
    #     is_histogram = workspace.isHistogramData()
    #
    # Correct target unit
    if target_unit.lower() == 'd' or target_unit.lower().count('spac') == 1:
        target_unit = 'dSpacing'
    elif target_unit.lower() == 'tof':
        target_unit = 'TOF'
    elif target_unit.lower() == 'q':
        target_unit = 'MomentumTransfer'

    workspace = retrieve_workspace(ws_name, True)
    if workspace.id() == 'WorkspaceGroup':
        workspace = workspace[0]
    if workspace.getAxis(0).getUnit().unitID() == target_unit:
        print('[INFO] Workspace {} has unit {} already. No need to convert'.format(ws_name, target_unit))
        return

    # Convert to Histogram, convert unit (must work on histogram) and convert back to point data
    mantidapi.ConvertUnits(InputWorkspace=ws_name,
                           OutputWorkspace=out_ws_name,
                           Target=target_unit,
                           EMode='Elastic',
                           ConvertFromPointData=True)

    # Check output
    if not workspace_does_exist(out_ws_name):
        raise RuntimeError('Output workspace {0} cannot be retrieved!'.format(ws_name))

    return


def mtd_filter_bad_pulses(ws_name, lower_cutoff=95.):
    """ Filter bad pulse
    Requirements: input workspace name is a string for a valid workspace
    :param ws_name:
    :param lower_cutoff: float as (self._filterBadPulses)
    :return:
    """
    # Check requirements
    assert isinstance(ws_name, str), 'Input workspace name should be string,' \
                                     'but is of type %s.' % str(type(ws_name))
    assert isinstance(lower_cutoff, float)

    event_ws = retrieve_workspace(ws_name)
    assert isinstance(event_ws, mantid.api.IEventWorkspace), \
        'Input workspace %s is not event workspace but of type %s.' % (
            ws_name, event_ws.__class__.__name__)

    # Get statistic
    num_events_before = event_ws.getNumberEvents()

    mantidapi.FilterBadPulses(InputWorkspace=ws_name, OutputWorkspace=ws_name,
                              LowerCutoff=lower_cutoff)

    event_ws = retrieve_workspace(ws_name)
    num_events_after = event_ws.getNumberEvents()

    print('[Info] FilterBadPulses reduces number of events from %d to %d (under %.3f percent) '
          'of workspace %s.' % (num_events_before, num_events_after, lower_cutoff, ws_name))

    return


def mtd_normalize_by_current(event_ws_name):
    """
    Normalize by current
    Purpose: call Mantid NormalisebyCurrent
    Requirements: a valid string as an existing workspace's name
    Guarantees: workspace is normalized by current
    :param event_ws_name:
    :return:
    """
    # Check requirements
    assert isinstance(event_ws_name, str), 'Input event workspace name must be a string.'
    event_ws = retrieve_workspace(event_ws_name)
    assert event_ws is not None

    # Call mantid algorithm
    mantidapi.NormaliseByCurrent(InputWorkspace=event_ws_name,
                                 OutputWorkspace=event_ws_name)

    # Check
    out_ws = retrieve_workspace(event_ws_name)
    assert out_ws is not None

    return


def normalize_by_vanadium(data_ws_name, van_ws_name):
    """
    normalize by vanadium
    :param data_ws_name:
    :param van_ws_name:
    :return:
    """
    # check inputs
    assert isinstance(data_ws_name, str), 'blabla 123'
    assert isinstance(van_ws_name, str), 'blabla 124'

    # get workspace
    data_ws = retrieve_workspace(data_ws_name, True)
    van_ws = retrieve_workspace(van_ws_name, True)

    if data_ws.getNumberHistograms() != van_ws.getNumberHistograms():
        raise RuntimeError('Unmatched histograms')

    mantidapi.Divide(LHSWorkspace=data_ws, RHSWorkspace=van_ws, OutputWorkspace=data_ws_name,
                     AllowDifferentNumberSpectra=False, ClearRHSWorkspace=False,
                     WarnOnZeroDivide=True)

    return


def rebin(workspace_name, params, preserve, output_ws_name=None):
    """
    rebin the workspace
    :param workspace_name:
    :param params:
    :param preserve:
    :return:
    """
    if not is_a_workspace(workspace_name):
        raise RuntimeError('{0} is not a workspace in ADS'.format(workspace_name))
    assert isinstance(params, str) or isinstance(params, list) or isinstance(params, tuple) \
        or isinstance(params, numpy.ndarray), 'Params {0} of type {1} is not supported.' \
        ''.format(params, type(params))

    if output_ws_name is None:
        output_ws_name = workspace_name

    mantidapi.Rebin(InputWorkspace=workspace_name, OutputWorkspace=output_ws_name,
                    Params=params,
                    PreserveEvents=preserve)
    return output_ws_name


def retrieve_workspace(ws_name, raise_if_not_exist=False):
    """
    Retrieve workspace from AnalysisDataService
    Purpose:
        Get workspace from Mantid's analysis data service

    Requirements:
        workspace name is a string
    Guarantee:
        return the reference to the workspace or None if it does not exist
    :param ws_name:
    :param raise_if_not_exist:
    :return: workspace instance (1)
    """
    assert isinstance(ws_name, str), 'Input ws_name %s is not of type string, but of type %s.' % (str(ws_name),
                                                                                                  str(type(
                                                                                                      ws_name)))

    if ADS.doesExist(ws_name) is False:
        if raise_if_not_exist:
            raise RuntimeError('ADS does not exist workspace named as {0}.'.format(ws_name))
        else:
            return None

    return mantidapi.AnalysisDataService.retrieve(ws_name)


def create_vulcan_binning_table(binning_reference_file):
    """

    :param binning_reference_file:
    :return:
    """
    raise NotImplementedError('Not Implemented Yet')


def save_event_workspace(event_ws_name, nxs_file_name):
    """

    :param event_ws_name:
    :param nxs_file_name:
    :return:
    """
    mantidapi.SaveNexusProcessed(InputWorkspace=event_ws_name, Filename=nxs_file_name)

    return


def split_event_data(raw_ws_name, split_ws_name, info_table_name, target_ws_name=None,
                     tof_correction=False, output_directory=None, delete_split_ws=True):
    """
    Split event data file according pre-defined split workspace.
    Optionally the split workspace
    Optionally the split workspace
    can be saved to NeXus files
    :param raw_ws_name:
    :param split_ws_name:
    :param info_table_name:
    :param target_ws_name:
    :param tof_correction:
    :param output_directory:
    :param delete_split_ws: True/(list of ws names, list of ws objects); False/error message
    :return: 2-tuple.  [1] boolean (success or fail) [2a] List of 2-tuples (output file name + workspace name)
                                                     [2b] Error message
    """
    # Check requirements
    assert workspace_does_exist(
        split_ws_name), 'splitters workspace {0} does not exist.'.format(split_ws_name)
    assert workspace_does_exist(info_table_name), 'splitting information workspace {0} does not exist.' \
                                                  ''.format(info_table_name)
    assert workspace_does_exist(
        raw_ws_name), 'raw event workspace {0} does not exist.'.format(raw_ws_name)

    # get the input event workspace
    # rule out some unsupported scenario
    if output_directory is None and delete_split_ws:
        raise RuntimeError('It is not supported that no file is written (output_dir is None) '
                           'and split workspace is to be delete.')
    elif output_directory is not None:
        assert isinstance(output_directory, str), 'Output directory %s must be a string but not %s.' \
                                                  '' % (str(output_directory),
                                                        type(output_directory))

    # process TOF correction
    if tof_correction is True:
        correction = 'Elastic'
    else:
        correction = 'None'

    # process the target workspace name
    if target_ws_name is None:
        target_ws_name = raw_ws_name + '_split'
    else:
        assert isinstance(target_ws_name, str), 'Target workspace name %s must be a string but not %s.' \
                                                '' % (str(target_ws_name), type(target_ws_name))

    # find out whether it is relative time
    split_ws = retrieve_workspace(split_ws_name)
    if split_ws.__class__.__name__.count('Table'):
        # table workspace
        time0 = split_ws.cell(0, 0)
    elif split_ws.__class__.__name__.count('Splitter'):
        # splitters workspace
        time0 = float(split_ws.cell(0, 0)) * 1.E-9
    else:
        # matrix workspace
        time0 = split_ws.readX(0)[0]
    if time0 < 3600. * 24. * 356:
        is_relative_time = True
    else:
        is_relative_time = False

    # split workspace
    ret_list = mantidapi.FilterEvents(InputWorkspace=raw_ws_name,
                                      SplitterWorkspace=split_ws_name,
                                      InformationWorkspace=info_table_name,
                                      OutputWorkspaceBaseName=target_ws_name,
                                      FilterByPulseTime=False,
                                      GroupWorkspaces=True,
                                      CorrectionToSample=correction,
                                      SplitSampleLogs=True,
                                      OutputWorkspaceIndexedFrom1=True,
                                      RelativeTime=is_relative_time
                                      )

    try:
        correction_ws = ret_list[0]
        num_split_ws = ret_list[1]
        chopped_ws_name_list = ret_list[2]
        # check the workspace name
        for i_w, ws_name in enumerate(chopped_ws_name_list):
            if len(ws_name) == 0:
                chopped_ws_name_list.pop(i_w)
            elif ADS.doesExist(ws_name) is False:
                print('[ERROR] Chopped workspace {0} cannot be found.'.format(ws_name))
        # END-FOR
        assert num_split_ws == len(chopped_ws_name_list), 'Number of split workspaces {0} must be equal to number of ' \
                                                          'chopped workspaces names {1} ({2}).' \
                                                          ''.format(num_split_ws, len(chopped_ws_name_list),
                                                                    chopped_ws_name_list)
    except IndexError:
        return False, 'Failed to split data by FilterEvents.'

    if len(ret_list) != 3 + len(chopped_ws_name_list):
        print('[WARNING] Returned List Size = {0}'.format(len(ret_list)))

    # Save result
    chop_list = list()
    if output_directory is not None:
        # saved the output
        for index, chopped_ws_name in enumerate(chopped_ws_name_list):
            base_file_name = '{0}_event.nxs'.format(chopped_ws_name)
            file_name = os.path.join(output_directory, base_file_name)
            print('[INFO] Save chopped workspace {0} to {1}.'.format(chopped_ws_name, file_name))
            mantidapi.SaveNexusProcessed(InputWorkspace=chopped_ws_name, Filename=file_name)
            chop_list.append((file_name, chopped_ws_name))

        # Clear only if file is saved
        print('[INFO] Delete correction workspace {0}'.format(correction_ws))
        delete_workspace(correction_ws)

        if delete_split_ws:
            for chopped_ws_name in chopped_ws_name_list:
                print('[INFO] Delete chopped child workspace {0}'.format(chopped_ws_name))
                mantidapi.DeleteWorkspace(Workspace=chopped_ws_name)
                # DEBUG: where does raw workspace go?
                if ADS.doesExist(raw_ws_name) is False:
                    return False, str(RuntimeError('.... Debug Stop ... Debug Stop ...'))
    else:
        if delete_split_ws:
            print('[WARNING] Chopped workspaces cannot be deleted if the output directory is not specified.')
        for chopped_ws_name in chopped_ws_name_list:
            chop_list.append((None, chopped_ws_name))
    # END-IF

    return True, chop_list


def smooth_vanadium(input_workspace, output_workspace=None, workspace_index=None,
                    smooth_filter='Butterworth', param_n=20, param_order=2,
                    push_to_positive=True):
    """
    Use Mantid FFTSmooth to smooth vanadium diffraction data
    :except: RuntimeError if failed to execute. AssertionError if input is wrong

    :param input_workspace:
    :param output_workspace:
    :param workspace_index:
    :param smooth_filter:
    :param param_order:
    :param param_n:
    :return: output workspace name if
    """
    # check inputs
    assert smooth_filter in ['Butterworth',
                             'Zeroing'], 'Smooth filter {0} is not supported.'.format(smooth_filter)
    assert isinstance(input_workspace, str), 'Input workspace name {0} must be a string but not a {1}.' \
                                             ''.format(input_workspace, type(input_workspace))
    assert workspace_does_exist(input_workspace), 'Input workspace {0} cannot be found in Mantid ADS.' \
                                                  ''.format(input_workspace)
    assert isinstance(param_order, int), 'Smoothing parameter "order" must be an integer.'
    assert isinstance(param_n, int), 'Smoothing parameter "n" must be an integer.'

    # get output workspace
    if output_workspace is None:
        output_workspace = '{0}_{1}_{2}_{3}'.format(
            input_workspace, smooth_filter, param_n, param_order)

    # check input workspace's unit and convert to TOF if needed
    if get_workspace_unit(input_workspace) != 'TOF':
        mtd_convert_units(input_workspace, 'TOF')

    # smooth
    if smooth_filter == 'Zeroing':
        smooth_params = '{0}'.format(param_n)
    else:
        smooth_params = '{0},{1}'.format(param_n, param_order)   # default '20, 2'

    if workspace_index is None:
        try:
            mantidapi.FFTSmooth(InputWorkspace=input_workspace,
                                OutputWorkspace=output_workspace,
                                Filter=smooth_filter,
                                Params=smooth_params,
                                IgnoreXBins=True,
                                AllSpectra=True)
        except RuntimeError as run_err:
            raise RuntimeError('Unable to smooth all spectra of workspace {0} due to {1}.'
                               ''.format(input_workspace, run_err))
    else:
        # do for one specific workspace
        assert isinstance(workspace_index, int), 'Workspace index {0} must be an integer but not a {1}.' \
                                                 ''.format(workspace_index, type(workspace_index))
        input_ws = ADS.retrieve(input_workspace)
        if not 0 <= workspace_index < input_ws.getNumberHistograms():
            raise RuntimeError('Workspace index {} is out of range [0, {}).'
                               ''.format(workspace_index, input_ws.getNumberHistograms()))
        try:
            mantidapi.FFTSmooth(InputWorkspace=input_workspace,
                                OutputWorkspace=output_workspace,
                                WorkspaceIndex=workspace_index,
                                Filter=smooth_filter,
                                Params=smooth_params,
                                IgnoreXBins=True,
                                AllSpectra=False)
        except RuntimeError as run_err:
            raise RuntimeError('Unable to smooth spectrum {2} of workspace {0} due to {1}.'
                               ''.format(input_workspace, run_err, workspace_index))
    # END-IF-ELSE

    if push_to_positive:
        # push all the Y values to positive integer
        smooth_ws = ADS.retrieve(input_workspace)
        if workspace_index is None:
            workspace_index_list = range(smooth_ws.getNumberHistograms())
        else:
            workspace_index_list = [workspace_index]

        for ws_index in workspace_index_list:
            vec_y = smooth_ws.dataY(ws_index)
            for i_y in range(len(vec_y)):
                vec_y[i_y] = max(1, int(vec_y[i_y] + 1))
        # END-FOR
    # END-IF

    return output_workspace


def strip_vanadium_peaks(input_ws_name, output_ws_name=None,
                         bank_list=None, binning_parameter=None,
                         fwhm=7, peak_pos_tol=0.05,
                         background_type="Quadratic", is_high_background=True):
    """
    Strip vanadium peaks
    :except: run time error

    :param input_ws_name:
    :param output_ws_name:
    :param bank_list:
    :param binning_parameter:
    :param fwhm: integer peak FWHM
    :param peak_pos_tol: float peak position tolerance
    :param background_type:
    :param is_high_background:
    :return: dictionary to workspace names
    """
    # check inputs
    assert isinstance(input_ws_name, str), 'Input workspace {0} must be a string but not a {1}.' \
        ''.format(input_ws_name, type(input_ws_name))
    if not workspace_does_exist(input_ws_name):
        raise RuntimeError('Workspace {0} does not exist in ADS.'.format(input_ws_name))
    else:
        input_workspace = ADS.retrieve(input_ws_name)

    if bank_list is None:
        bank_list = range(1, 1+input_workspace.getNumberHistograms())
    else:
        assert isinstance(bank_list, list), 'Banks must be given by list'
        if len(bank_list) == 0:
            raise RuntimeError('Empty bank list')

    if output_ws_name is None:
        output_ws_name = input_ws_name + '_no_peak'

    # make sure that the input workspace is in unit dSpacing
    try:
        if get_workspace_unit(input_ws_name) != 'dSpacing':
            mantidapi.ConvertUnits(InputWorkspace=input_ws_name, OutputWorkspace=input_ws_name,
                                   Target='dSpacing')
    except RuntimeError as run_err:
        raise RuntimeError(
            'Unable to convert workspace {0} to dSpacing due to {1}.'.format(input_ws_name, run_err))

    # call Mantid algorithm StripVanadiumPeaks
    assert isinstance(fwhm, int), 'FWHM {0} must be an integer but not {1}.'.format(
        fwhm, type(fwhm))
    assert isinstance(background_type, str), 'Background type {0} must be a string but not {1}.' \
                                             ''.format(background_type, type(background_type))
    assert background_type in ['Linear', 'Quadratic'], 'Background type {0} is not supported.' \
                                                       'Candidates are {1}'.format(
                                                           background_type, 'Linear, Quadratic')
    try:
        # rebin if asked
        # workspace unit before striping:  dSpacing.  therefore, cannot use the TOF binning range
        if binning_parameter is not None:
            mantidapi.Rebin(InputWorkspace=input_ws_name, OutputWorkspace=output_ws_name,
                            Params='-0.001')
        #                    Params=binning_parameter)

        # strip vanadium peaks. and the output workspace is Histogram/PointData (depending on input) in unit dSpacing
        # before striping: EventWorkspace
        output_ws_dict = dict()
        for bank_id in bank_list:
            if len(bank_list) > 1:
                output_ws_name_i = output_ws_name + '__bank_{0}'.format(bank_id)
            else:
                output_ws_name_i = output_ws_name
            mantidapi.StripVanadiumPeaks(InputWorkspace=input_ws_name,
                                         OutputWorkspace=output_ws_name_i,
                                         FWHM=fwhm,
                                         PeakPositionTolerance=peak_pos_tol,
                                         BackgroundType=background_type,
                                         HighBackground=is_high_background,
                                         WorkspaceIndex=bank_id-1
                                         )
            output_ws_dict[bank_id] = output_ws_name_i
            # After strip: Workspace2D
        # END-FOR

    except RuntimeError as run_err:
        raise RuntimeError('Failed to execute StripVanadiumPeaks on workspace {0} due to {1}'
                           ''.format(input_ws_name, run_err))

    return output_ws_dict


def sum_spectra(input_workspace, output_workspace, workspace_index_list):
    """
    sum spectra
    :param input_workspace:
    :param output_workspace:
    :return:
    """
    # check
    assert isinstance(input_workspace, str), 'Input workspace must be string'
    assert isinstance(output_workspace, str), 'Output workspace must be string'

    # call Mantid
    mantidapi.SumSpectra(InputWorkspace=input_workspace,
                         OutputWorkspace=output_workspace,
                         ListOfWorkspaceIndices=workspace_index_list,
                         IncludeMonitors=False, RemoveSpecialValues=True)

    return


def workspace_does_exist(workspace_name):
    """ Check whether a workspace exists in analysis data service by its name
    Requirements: input workspace name must be a non-empty string
    :param workspace_name:
    :return: boolean
    """
    # Check
    assert isinstance(workspace_name, str), 'Workspace name must be string but not %s.' % str(
        type(workspace_name))
    assert len(workspace_name) > 0, 'It is impossible to for a workspace with empty string as name.'

    #
    does_exist = ADS.doesExist(workspace_name)

    return does_exist
