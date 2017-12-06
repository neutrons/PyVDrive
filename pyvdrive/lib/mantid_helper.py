import os
import random
import numpy

import mantid
import mantid.api
import mantid.dataobjects
import mantid.geometry
import mantid.simpleapi as mantidapi
from mantid.api import AnalysisDataService as ADS

import vdrivehelper

from reduce_VULCAN import align_bins

EVENT_WORKSPACE_ID = "EventWorkspace"
WORKSPACE_2D_ID = 'Workspace2D'

# define constants
VULCAN_L1 = 43.754
VULCAN_1BANK_L2 = 2.009436
VULCAN_1BANK_POLAR = 90.1120
VULCAN_2BANK_1_L2 = 2.009436
VULCAN_2BANK_1_POLAR = 90.
VULCAN_2BANK_2_L2 = 2.009436
VULCAN_2BANK_2_POLAR = 360. - 90.1120


def clone_workspace(srs_ws_name, target_ws_name):
    """blabla"""

    assert isinstance(srs_ws_name, str), 'blabla'
    assert isinstance(target_ws_name, str), 'blabla'

    mantidapi.CloneWorkspace(InputWorkspace=srs_ws_name, OutputWorkspace=target_ws_name)

    output_ws = ADS.retrieve(target_ws_name)

    return output_ws


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
        'Splitters workspace {0} must be a TableWorkspace but not a {1}.'.format(split_ws, type(split_ws))

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

        prev_child_index = current_child_index

        continue_loop = True
        while continue_loop:
            if curr_split_ws.rowCount() == 0 or curr_split_ws.cell(curr_split_ws.rowCount()-1, 1) <= start_i:
                # either empty split workspace of current split workspace's last splitter's stop time is earlier
                # add a new row
                print '[DB...BT] Add split from {0} to {1} to sub-splitter {2}' \
                      ''.format(start_i, stop_i, current_child_index)
                curr_split_ws.addRow([start_i, stop_i, target_i])
                break

            if current_child_index == len(sub_split_ws_list) - 1:
                # go back to first one
                current_child_index = 0
            else:
                # advance to next one (fill evenly, right?)
                current_child_index += 1
            curr_split_ws = sub_split_ws_list[current_child_index]
            print '[DB...BT] Advance to next sub-splitter {0}'.format(current_child_index)

            if current_child_index == 0 and curr_split_ws.cell(curr_split_ws.rowCount()-1, 1) > start_i:
                # go from last one to first one. time to add a new one if still overlap with new one
                current_child_index = len(sub_split_ws_list)
                curr_split_ws = create_table_splitters(split_ws_name + '{0}'.format(current_child_index))
                sub_split_ws_list.append(curr_split_ws)
                print '[DB...BT] Create a new sub-splitter {0}.'.format(current_child_index)
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
    print '[DB...BAT] Time bin size = {0} Time segment size = {1} Num sub splitters = {2}' \
          ''.format(time_bin_size, time_segment_period, num_sub_splitters)

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
    :return: three tuple
    """
    # check inputs
    if isinstance(split_ws, str):
        # in case user input split workspace name
        split_ws = retrieve_workspace(split_ws)

    assert split_ws.__class__.__name__.count('Splitter') == 1,\
        'Input SplittersWorkspace %s must be of type SplittersWorkspace must not %s' \
        '' % (str(split_ws), split_ws.__class__.__name__)

    # go over rows
    num_rows = split_ws.rowCount()
    time_list = list()
    ws_list = list()
    for row_index in range(num_rows):
        # get start time and end time in int64
        start_time = split_ws.cell(row_index, 0)
        end_time = split_ws.cell(row_index, 1)
        ws_index = split_ws.cell(row_index, 2)

        # convert units of time from int64/nanoseconds to float/seconds
        start_time = float(start_time) * 1.0E-9
        end_time = float(end_time) * 1.0E-9

        if row_index == 0:
            # first splitter, starting with start_time[0]
            time_list.append(start_time)
        elif start_time > time_list[-1]:
            # middle splitter, there is a gap between 2 splitters, fill in with -1
            ws_list.append(-1)
            time_list.append(start_time)

        ws_list.append(ws_index)
        time_list.append(end_time)
    # END-FOR

    # get the numpy arrays
    vec_times = numpy.array(time_list)
    vec_ws = numpy.array(ws_list)

    if run_start_time is not None:
        # run start time is of float in unit of seconds
        assert isinstance(run_start_time, float), 'Starting time must be a float'
        vec_times -= run_start_time

    print '[DB...BAT] size of output vectors: ', len(vec_times), len(vec_ws)

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


def delete_workspace(workspace):
    """ Delete a workspace in AnalysisService
    :param workspace:
    :return:
    """
    mantidapi.DeleteWorkspace(Workspace=workspace)

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
    assert ADS.doesExist(diff_data), 'Input workspace {0} does not exist in Mantid AnalysisDataService.' \
                                     ''.format(diff_data)
    matrix_workspace = ADS.retrieve(diff_data)
    assert isinstance(ws_index, int) and 0 <= ws_index < matrix_workspace.getNumberHistograms(), \
        'Workspace index {0} must be an integer in [0, {1}).'.format(ws_index, matrix_workspace.getNumberHistograms())

    #  get workspace define output workspace name
    result_peak_ws_name = '{0}_FoundPeaks'.format(diff_data)

    # call Mantid's FindPeaks
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
            arg_dict['Peaks'] = numpy.array(peak_pos_list)

    try:
        mantidapi.FindPeaks(**arg_dict)
    except RuntimeError as run_err:
        raise RuntimeError('Unable to find peaks in workspace {0} due to {1}'.format(diff_data, run_err))

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

            print ('[INFO] Find peak @ {0} with chi^2 = {1}'.format(peak_i_center, peak_i_chi2))
        else:
            print ('[INFO] Ignore peak @ {0} with large chi^2 = {1}'.format(peak_i_center, peak_i_chi2))
    # END-FOR

    return peak_list


def generate_event_filters_arbitrary(ws_name, split_list, relative_time, tag, auto_target):
    """ Generate event filter (splitters workspace) by arbitrary time stamps
    :param split_list:
    :param relative_time:
    :param tag: string for tag name
    :return: 2-tuple
        1. status (boolean)
        2. 2-tuple as splitter workspace's name and information (table) workspace's name
    """
    print '[DB...BAT] Workspace Name: ', ws_name

    # # check
    # if relative_time is False:
    #     raise RuntimeError('It has not been implemented for absolute time stamp!')

    # check
    assert isinstance(split_list, list), 'split list should be a list but not a %s.' \
                                         '' % str(type(split_list))
    assert isinstance(tag, str), 'Split tag must be a string but not %s.' % str(type(tag))
    assert len(tag) > 0, 'Split tag cannot be empty.'

    # create an empty workspace
    splitters_ws_name = tag
    info_ws_name = tag + '_Info'

    # use table workspace (relative time in default)
    create_table_workspace(splitters_ws_name, [('float', 'start'), ('float', 'stop'), ('str', 'target')])
    create_table_workspace(info_ws_name, [('str', 'target'), ('str', 'description')])

    # get handler on splitters workspace and info workspace
    splitter_ws = retrieve_workspace(splitters_ws_name)
    info_ws = retrieve_workspace(info_ws_name)
    target_set = set()

    print '[DB...BAT] Number of splitters = {0}'.format(len(split_list))
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
            raise RuntimeError('Splitter tuple has only 2 entries!')

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
    assert isinstance(info_ws_name, str), 'Splitting information TableWorkspace name must be a string.'

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
    assert isinstance(info_ws_name, str), 'Splitting information TableWorkspace name must be a string.'

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
    if time_unit != 'Seconds' and time_unit is not None:
        my_arg_dict['UnitOfTime'] = time_unit

    try:
        print '[DB...BAT] Generate events by time: ', my_arg_dict
        mantidapi.GenerateEventsFilter(**my_arg_dict)
    except RuntimeError as e:
        return False, str(e)

    return True, ''


def get_run_start(workspace, time_unit):
    """ Get run start time
    :param workspace:
    :param time_unit: nanosecond(s), second(s)
    :return:
    """
    # check the situation if workspace is a string
    assert isinstance(time_unit, str)
    if isinstance(workspace, str):
        if ADS.doesExist(workspace):
            workspace = ADS.retrieve(workspace)
        else:
            raise RuntimeError('Workspace %s does not exist in Mantid AnalysisDataService.' % workspace)
    # END-IF

    try:
        pcharge_log = workspace.run().getProperty('proton_charge')
    except AttributeError as e:
        raise RuntimeError('Unable to get run start due to %s.' % str(e))
    except RuntimeError as e:
        raise RuntimeError('Unable to get run start due to %s.' % str(e))

    # Get first value in proton charge's time as run start
    run_start_ns = pcharge_log.times[0].totalNanoseconds()

    # Convert unit if
    run_start = run_start_ns
    if time_unit.lower().startswith('nanosecond'):
        pass
    elif time_unit.lower().startswith('second'):
        run_start *= 1.E-9
    else:
        raise RuntimeError('Unit %s is not supported by get_run_start().' % time_unit)

    return run_start


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
            raise RuntimeError('Workspace %s does not exist in AnalysisDataService.' % src_workspace)
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
    # assert workspace_does_exist(src_workspace)
    assert isinstance(sample_log_name, str)

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

    return vec_times, vec_value


def get_data_from_gsas(gsas_file_name, binning_template_ws=None):
    """
    Load and get data from a GSAS file
    :param gsas_file_name:
    :param binning_template_ws: name of MatrixWorkspace for binning template
    :return: a dictionary of 3-array-tuples (x, y, e). KEY = workspace index (from 0 ...)
    """
    # check input
    assert isinstance(gsas_file_name, str), 'Input GSAS file name {0} must be an integer but not a {1}.' \
                                            ''.format(gsas_file_name, type(gsas_file_name))

    # get output workspace name
    out_ws_name = os.path.basename(gsas_file_name).split('.')[0] + '_gss'

    # load GSAS file
    load_gsas_file(gss_file_name=gsas_file_name, out_ws_name=out_ws_name,
                   standard_bin_workspace=binning_template_ws)

    data_set_dict, unit = get_data_from_workspace(out_ws_name, target_unit='dSpacing', point_data=True,
                                                  start_bank_id=True)

    return data_set_dict


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
    num_hist = workspace.getNumberHistograms()

    bank_list = range(start_bank_id, start_bank_id + num_hist)

    return bank_list


def get_data_from_workspace(workspace_name, bank_id=None, target_unit=None, point_data=True, start_bank_id=1):
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
    :return: a 2-tuple:
             (1) a dictionary of 3-array-tuples (x, y, e). KEY = bank ID
             (2) unit of the returned data
    """
    # check requirements by asserting
    assert isinstance(workspace_name, str) and isinstance(point_data, bool), 'blabla'
    assert isinstance(target_unit, str) or target_unit is None,\
        'Target {0} unit must be a string {0} or None but not a {1}'.format(target_unit, type(target_unit))
    assert isinstance(start_bank_id, int) and start_bank_id >= 0,\
        'Start-Bank-ID {0} must be a non-negetive integer but not {1}.' \
        ''.format(start_bank_id, type(start_bank_id))

    if workspace_does_exist(workspace_name) is False:
        raise RuntimeError('Workspace %s does not exist.' % workspace_name)

    # check bank ID not being None
    workspace = ADS.retrieve(workspace_name)
    if bank_id is not None:
        assert isinstance(bank_id, int), 'Bank ID {0} must be None or integer but not {1}.' \
                                         ''.format(bank_id, type(bank_id))
        required_workspace_index = bank_id - start_bank_id
        if not 0 <= required_workspace_index < workspace.getNumberHistograms():
            raise RuntimeError('Bank ID {0}, aka workspace index {1} is out of spectra of workspace {2}.'
                               ''.format(bank_id, required_workspace_index, workspace_name))
    else:
        required_workspace_index = None
    # END-IF-ELSE

    # define a temporary workspace name
    use_temp = False
    temp_ws_name = workspace_name + '__{0}'.format(random.randint(1, 100000))

    # process target unit
    if target_unit is not None:
        if target_unit.lower() == 'tof':
            target_unit = 'TOF'
        elif target_unit.lower().count('spac') > 0:
            target_unit = 'dSpacing'
        elif target_unit.lower() == 'q':
            target_unit = 'MomentumTransfer'
    # END-IF

    # get unit
    current_unit = get_workspace_unit(workspace_name)
    if current_unit != target_unit and target_unit is not None:
        # convert unit if the specified target unit is different
        mantidapi.ConvertUnits(InputWorkspace=workspace_name, OutputWorkspace=temp_ws_name,
                               Target=target_unit)
        current_unit = target_unit
        use_temp = True
    # END-IF

    # Convert to point data by checking
    workspace = ADS.retrieve(workspace_name)
    num_bins_set = set()
    for iws in range(workspace.getNumberHistograms()):
        num_bins_set.add(len(workspace.readY(iws)))
    # END-FOR

    # FIXME/TODO/FUTURE - After Mantid support ConvertToPointData for workspace with various bin sizes...
    if point_data and workspace.isHistogramData() and len(num_bins_set) == 1:
        # requiring point data and input is histogram data and number of bins are same for all spectra
        if use_temp:
            input_ws_name = temp_ws_name
        else:
            input_ws_name = workspace_name
            use_temp = True
        mantidapi.ConvertToPointData(InputWorkspace=input_ws_name,
                                     OutputWorkspace=temp_ws_name)
    # END-IF

    # Set up variables
    data_set_dict = dict()
    if use_temp:
        workspace = retrieve_workspace(temp_ws_name)
    else:
        workspace = retrieve_workspace(workspace_name)
    
    # Get data: 2 cases as 1 bank or all banks
    if bank_id is None:
        # all banks
        num_spec = workspace.getNumberHistograms()
        for i_ws in xrange(num_spec):
            # TODO/FIXME/FUTURE : for point data need 1 fewer X value
            if len(num_bins_set) > 1 and point_data:
                vec_x = workspace.readX(i_ws)[:-1]
            else:
                vec_x = workspace.readX(i_ws)
            size_x = len(vec_x)
            vec_y = workspace.readY(i_ws)
            size_y = len(vec_y)
            vec_e = workspace.readE(i_ws)

            data_x = numpy.ndarray((size_x,), 'float')
            data_y = numpy.ndarray((size_y,), 'float')
            data_e = numpy.ndarray((size_y,), 'float')

            data_x[:] = vec_x[:]
            data_y[:] = vec_y[:]
            data_e[:] = vec_e[:]

            data_set_dict[i_ws + start_bank_id] = (data_x, data_y, data_e)
        # END-FOR
    else:
        # specific bank
        # TODO/FIXME/FUTURE : for point data need 1 fewer X value
        if len(num_bins_set) > 1 and point_data:
            vec_x = workspace.readX(required_workspace_index)[:-1]
        else:
            vec_x = workspace.readX(required_workspace_index)
        size_x = len(vec_x)
        vec_y = workspace.readY(required_workspace_index)
        size_y = len(vec_y)
        vec_e = workspace.readE(required_workspace_index)

        data_x = numpy.ndarray((size_x,), 'float')
        data_y = numpy.ndarray((size_y,), 'float')
        data_e = numpy.ndarray((size_y,), 'float')

        data_x[:] = vec_x[:]
        data_y[:] = vec_y[:]
        data_e[:] = vec_e[:]

        data_set_dict[bank_id] = (data_x, data_y, data_e)

    # clean the temporary workspace
    if use_temp:
        delete_workspace(temp_ws_name)
    
    return data_set_dict, current_unit


def get_ipts_number(ws_name):
    """
    get IPTS number from a standard EventWorkspace
    :param ws_name:
    :return:
    """
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
    for i_row in xrange(num_rows):
        # Get original data
        start_time = split_ws.cell(i_row, 0)
        stop_time = split_ws.cell(i_row, 1)
        target = split_ws.cell(i_row, 2)
        print '[DB-BAT] Row %d' % i_row, start_time, ', ', stop_time, ', ', target

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
    assert isinstance(run_ws_name, str), 'Input workspace name should be a string but not %s.' % str(type(run_ws_name))
    assert workspace_does_exist(run_ws_name), 'Workspace %s does not exist.' % run_ws_name

    # Retrieve workspace and get bank list (bank number is from 1)
    workspace = retrieve_workspace(run_ws_name)
    num_spec = workspace.getNumberHistograms()
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
    assert isinstance(workspace_name, str), 'Workspace name {0} must be an integer but not a {1}.' \
                                            ''.format(workspace_name, type(workspace_name))
    assert isinstance(property_name, str), 'Property name {0} must be an integer but not a {1}.' \
                                           ''.format(property_name, type(property_name))

    workspace = retrieve_workspace(workspace_name)

    if value_in_str:
        return workspace.run().getProperty(property_name).value

    return workspace.run().getProperty(property_name)


def get_workspace_unit(workspace_name):
    """ get the unit of a workspace
    :param workspace_name:
    :return:
    """
    assert isinstance(workspace_name, str) and len(workspace_name) > 0
    assert ADS.doesExist(workspace_name), 'Workspace {0} cannot be found in ADS.'.format(workspace_name)

    workspace = ADS.retrieve(workspace_name)

    return workspace.getAxis(0).getUnit().unitID()


def event_data_ws_name(run_number):
    """ workspace name for raw event data
    :param run_number:
    :return:
    """
    return 'VULCAN_%d_Raw' % run_number


def get_standard_ws_name(file_name, meta_only):
    """
    Get the standard name for a loaded workspace
    Requirements: file name is a string
    :param file_name:
    :param meta_only:
    :return:
    """
    assert isinstance(file_name, str), 'File name should be a string but not %s.' % str(type(file_name))

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
    assert isinstance(run_number, int), 'Run number must be an integer but not of type %s.' % str(type(run_number))
    assert isinstance(out_base_name, str), 'Output base workpsace name must be a string but not %s.' % \
                                           str(type(out_base_name))
    assert isinstance(instrument_name, str), 'Instrument name must be a string but not %s.' % str(type(instrument_name))

    return '%s_%d_%s' % (instrument_name, run_number, out_base_name)


def is_event_workspace(workspace_name):
    """
    Check whether a workspace, specified by name, is an event workspace
    :param workspace_name:
    :return:
    """
    # Check requirement
    assert isinstance(workspace_name, str)

    event_ws = retrieve_workspace(workspace_name)
    assert event_ws is not None

    return event_ws.id() == EVENT_WORKSPACE_ID


def is_matrix_workspace(workspace_name):
    """
    check wehther a workspace is a MatrixWorkspace
    :param workspace_name:
    :return:
    """
    # Check requirement
    assert isinstance(workspace_name, str), 'input workspace name {0} is not a string but a {1}' \
                                            ''.format(workspace_name, type(workspace_name))

    # get workspace
    matrix_workspace = retrieve_workspace(workspace_name)
    assert matrix_workspace is not None, 'blabla'

    is_matrix = matrix_workspace.id() == EVENT_WORKSPACE_ID or matrix_workspace.id() == WORKSPACE_2D_ID

    return is_matrix


def load_gsas_file(gss_file_name, out_ws_name, standard_bin_workspace):
    """ Load GSAS file and set instrument information as 2-bank VULCAN and convert units to d-spacing
    Requirements: GSAS file name is a full path; output workspace name is a string;
    Guarantees:
    :param gss_file_name:
    :param out_ws_name:
    :param standard_bin_workspace: binning template workspace. It can be None for not aligning
    :return: output workspace name
    """
    # TEST/ISSUE/NOW - Implement feature with standard_bin_workspace...
    # Check
    assert isinstance(gss_file_name, str), 'GSAS file name should be string but not %s.' % str(type(gss_file_name))
    assert isinstance(out_ws_name, str), 'Output workspace name should be a string but not %s.' % str(type(out_ws_name))
    assert isinstance(standard_bin_workspace, str) or standard_bin_workspace is None, \
        'Standard binning workspace {0} must be either a string or None but not a {1}.' \
        ''.format(standard_bin_workspace, type(standard_bin_workspace))

    # Load GSAS
    try:
        mantidapi.LoadGSS(Filename=gss_file_name, OutputWorkspace=out_ws_name)
    except IndexError as index_error:
        raise RuntimeError('GSAS {0} is corrupted. FYI: {1}'.format(gss_file_name, index_error))
    gss_ws = retrieve_workspace(out_ws_name)
    assert gss_ws is not None, 'Output workspace cannot be found.'

    # set instrument geometry: this is for VULCAN-only
    num_spec = gss_ws.getNumberHistograms()
    if num_spec == 2:
        # before nED, no high angle detector
        mantid.simpleapi.EditInstrumentGeometry(Workspace=out_ws_name,
                                                PrimaryFlightPath=43.753999999999998,
                                                SpectrumIDs='1,2',
                                                L2='2.00944,2.00944',
                                                Polar='90,270')
    elif num_spec == 3:
        # after nED, with high angle detector
        print ('[SpecialDebug] Edit Instrument: {0}'.format(out_ws_name))
        mantid.simpleapi.EditInstrumentGeometry(Workspace=out_ws_name,
                                                PrimaryFlightPath=43.753999999999998,
                                                SpectrumIDs='1,2,3',
                                                L2='2.0,2.0,2.0',
                                                Polar='90,270,135')
    else:
        raise RuntimeError('It is not implemented for GSAS file having more than 3 spectra ({0} now).'
                           ''.format(num_spec))

    # convert unit and to point data
    if num_spec == 2:
        align_bins(out_ws_name, standard_bin_workspace)
        mantidapi.ConvertUnits(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name,
                               Target='dSpacing')
    # END-IF

    return out_ws_name


def load_nexus(data_file_name, output_ws_name, meta_data_only):
    """ Load NeXus file
    :param data_file_name:
    :param output_ws_name:
    :param meta_data_only:
    :return: 2-tuple
    """
    try:
        out_ws = mantidapi.Load(Filename=data_file_name,
                                OutputWorkspace=output_ws_name,
                                MetaDataOnly=meta_data_only)
    except RuntimeError as e:
        return False, 'Unable to load Nexus file %s due to %s' % (data_file_name, str(e))

    return True, out_ws


def load_time_focus_file(instrument, time_focus_file, base_ws_name):
    """ Load time focus file (or say calibration in Mantid's nomenclature)
    :return:
    """
    # check
    assert isinstance(time_focus_file, str) and os.path.exists(time_focus_file), 'Time focus file error.'
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
    cal_ws_name  = '%s_cal' % base_ws_name

    # Check existence of the workspaces output from LoadCalFile
    assert workspace_does_exist(offset_ws_name), 'Offset workspace does not exist.'
    assert workspace_does_exist(grouping_ws_name), 'Grouping workspace does not exist.'
    assert workspace_does_exist(mask_ws_name), 'Mask worksapce does not exist.'
    assert workspace_does_exist(cal_ws_name), 'Calibration worksapce does not exist.'

    return True, [offset_ws_name, grouping_ws_name, mask_ws_name, cal_ws_name]


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
                                                   ''.format(target_workspace_name, type(target_workspace_name))
    assert isinstance(workspace_name_list, list), 'Workspace names {0} must be given as a list but not a {1}.' \
                                                  ''.format(workspace_name_list, type(workspace_name_list))
    if len(workspace_name_list) == 0:
        raise RuntimeError('Workspace name list is empty!')

    # get the workspace to get merged to
    # TEST/ISSUE/NOW - Need to verify
    if ADS.doesExist(target_workspace_name) is False:
        mantidapi.CloneWorkspace(InputWorkspace=workspace_name_list[0], OutputWorkspace=target_workspace_name)
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


def edit_compressed_chopped_workspace_geometry(ws_name):
    """
    set the geometry to the compressed workspace for chopped workspace
    prototype:
        EditInstrumentGeometry(Workspace='ws50', PrimaryFlightPath=50, L2='1,1,1,1,1,1', Polar='90,270,90,270,90,270')
    :param ws_name:
    :return:
    """
    # get workspace and check
    assert isinstance(ws_name, str), 'Workspace name {0} must be a string but not a {1}'.format(ws_name, type(ws_name))
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
            raise RuntimeError('It is impossible to have odd number of spectra in 2-bank compressed chopped workspace.')
        l2_list = [VULCAN_2BANK_1_L2, VULCAN_2BANK_2_L2] * (num_spectra/2)
        polar_list = [VULCAN_2BANK_1_POLAR,  VULCAN_2BANK_2_POLAR] * (num_spectra/2)
    else:
        raise RuntimeError('{0}-bank is not supported.'.format(num_spectra))

    # edit instrument geometry
    mantidapi.EditInstrumentGeometry(Workspace=ws_name,
                                     PrimaryFlightPath=VULCAN_L1,
                                     L2=str(l2_list).replace('[', '').replace(']',''),
                                     Polar=str(polar_list).replace('[', '').replace(']',''))

    return


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


def mtd_convert_units(ws_name, target_unit):
    """
    Convert the unit of a workspace.
    Guarantees: if the original workspace is point data, then the output must be point data
    :param ws_name:
    :param target_unit:
    :return:
    """
    # Check requirements
    assert isinstance(ws_name, str), 'Input workspace name is not a string but is a %s.' % str(type(ws_name))
    workspace = retrieve_workspace(ws_name)
    assert workspace
    assert isinstance(target_unit, str), 'Input target unit should be a string,' \
                                         'but is %s.' % str(type(target_unit))
    
    # Record whether the input workspace is histogram
    is_histogram = workspace.isHistogramData()
    
    # Correct target unit
    if target_unit.lower() == 'd' or target_unit.lower().count('spac') == 1:
        target_unit = 'dSpacing'
    elif target_unit.lower() == 'tof':
        target_unit = 'TOF'
    elif target_unit.lower() == 'q':
        target_unit = 'MomentumTransfer'
    
    # Convert to Histogram, convert unit (must work on histogram) and convert back to point data
    if is_histogram is False:
        mantidapi.ConvertToHistogram(InputWorkspace=ws_name, OutputWorkspace=ws_name)
    mantidapi.ConvertUnits(InputWorkspace=ws_name,
                           OutputWorkspace=ws_name,
                           Target=target_unit,
                           EMode='Elastic')
    if is_histogram is False:
        mantidapi.ConvertToPointData(InputWorkspace=ws_name, OutputWorkspace=ws_name)
    
    # Check output
    out_ws = retrieve_workspace(ws_name)
    assert out_ws, 'Output workspace {0} cannot be retrieved!'.format(ws_name)
    
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
        'Input workspace %s is not event workspace but of type %s.' % (ws_name, event_ws.__class__.__name__)
    
    # Get statistic
    num_events_before = event_ws.getNumberEvents()
    
    mantidapi.FilterBadPulses(InputWorkspace=ws_name, OutputWorkspace=ws_name,
                              LowerCutoff=lower_cutoff)
    
    event_ws = retrieve_workspace(ws_name)
    num_events_after = event_ws.getNumberEvents()
    
    print '[Info] FilterBadPulses reduces number of events from %d to %d (under %.3f percent) ' \
          'of workspace %s.' % (num_events_before, num_events_after, lower_cutoff, ws_name)
    
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

def rebin(workspace_name, params, preserve):
    # TODO/ISSUE/NOW/DOC
    mantidapi.Rebin(InputWorkspace=workspace_name, OutputWorkspace=workspace_name,
                    Params=params,
                    PreserveEvents=preserve)
    return

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


def save_vulcan_gsas(source_ws_name, out_gss_file, ipts, binning_reference_file, gss_parm_file):
    """ Convert to VULCAN's IDL and save_to_buffer to GSAS file
    Purpose: Convert a reduced workspace to IDL binning workspace and export to GSAS file
    Requirements:
    1. input source workspace is reduced
    2. output gsas file name is a string
    3. ipts number is integer
    4. binning reference file exists
    5. gss parameter file name is a string
    :param source_ws_name:
    :param out_gss_file:
    :param ipts:
    :param binning_reference_file:
    :param gss_parm_file:
    :return:
    """
    # Check requirements
    assert isinstance(source_ws_name, str), 'source workspace name {0} must be a string but not {1}.' \
                                            ''.format(source_ws_name, type(source_ws_name))
    src_ws = retrieve_workspace(source_ws_name)
    assert src_ws.getNumberHistograms() < 10, 'Source workspace {0} cannot have more than 10 histograms ({1}).' \
                                              ''.format(source_ws_name, src_ws.getNumberHistograms())
    
    assert isinstance(out_gss_file, str), 'Output GSAS file name {0} must be a string but not a {1}.' \
                                          ''.format(out_gss_file, type(out_gss_file))
    assert isinstance(ipts, int), 'IPTS number must be an integer but not %s.' % str(type(ipts))
    assert isinstance(binning_reference_file, str), 'Binning referece file name {0} must be a string but not a {1}.' \
                                                    ''.format(binning_reference_file, type(binning_reference_file))
    if len(binning_reference_file) > 0:
        assert os.path.exists(binning_reference_file), 'Binning reference file {0} does not exist.' \
                                                       ''.format(binning_reference_file)
    assert isinstance(gss_parm_file, str), 'GSAS parmm file name {0} must be a string but not a {1}.' \
                                           ''.format(gss_parm_file, type(gss_parm_file))

    # using a new workspace if and only if it is required to be re-binned
    if len(binning_reference_file) > 0:
        final_ws_name = source_ws_name + '_IDL'
    else:
        final_ws_name = source_ws_name

    source_ws = ADS.retrieve(source_ws_name)
    if not source_ws.isHistogramData():
        mantidapi.ConvertToHistogram(InputWorkspace=source_ws_name,
                                     OutputWorkspace=source_ws_name)

    # Save to GSAS
    mantidapi.SaveVulcanGSS(InputWorkspace=source_ws_name,
                            BinFilename=binning_reference_file,
                            OutputWorkspace=final_ws_name,
                            GSSFilename=out_gss_file,
                            IPTS=ipts,
                            GSSParmFilename=gss_parm_file)

    # Add special property to output workspace
    final_ws = ADS.retrieve(final_ws_name)
    final_ws.getRun().addProperty('VDriveBin', True, replace=True)

    return


def save_event_workspace(event_ws_name, nxs_file_name):
    """

    :param event_ws_name:
    :param nxs_file_name:
    :return:
    """
    mantidapi.SaveNexus(InputWorkspace=event_ws_name, Filename=nxs_file_name)

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
    assert workspace_does_exist(split_ws_name), 'splitters workspace {0} does not exist.'.format(split_ws_name)
    assert workspace_does_exist(info_table_name), 'splitting information workspace {0} does not exist.' \
                                                  ''.format(info_table_name)
    assert workspace_does_exist(raw_ws_name), 'raw event workspace {0} does not exist.'.format(raw_ws_name)

    # get the input event workspace
    # rule out some unsupported scenario
    if output_directory is None and delete_split_ws:
        raise RuntimeError('It is not supported that no file is written (output_dir is None) '
                           'and split workspace is to be delete.')
    elif output_directory is not None:
        assert isinstance(output_directory, str), 'Output directory %s must be a string but not %s.' \
                                                  '' % (str(output_directory), type(output_directory))

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
                print '[ERROR] Chopped workspace {0} cannot be found.'.format(ws_name)
        # END-FOR
        assert num_split_ws == len(chopped_ws_name_list), 'Number of split workspaces {0} must be equal to number of ' \
                                                          'chopped workspaces names {1} ({2}).' \
                                                          ''.format(num_split_ws, len(chopped_ws_name_list),
                                                                    chopped_ws_name_list)
    except IndexError:
        return False, 'Failed to split data by FilterEvents.'

    if len(ret_list) != 3 + len(chopped_ws_name_list):
        print '[WARNING] Returned List Size = {0}'.format(len(ret_list))

    # Save result
    chop_list = list()
    if output_directory is not None:
        # saved the output
        for index, chopped_ws_name in enumerate(chopped_ws_name_list):
            base_file_name = '{0}_event.nxs'.format(chopped_ws_name)
            file_name = os.path.join(output_directory, base_file_name)
            print '[INFO] Save chopped workspace {0} to {1}.'.format(chopped_ws_name, file_name)
            mantidapi.SaveNexusProcessed(InputWorkspace=chopped_ws_name, Filename=file_name)
            chop_list.append((file_name, chopped_ws_name))

        # Clear only if file is saved
        print '[INFO] Delete correction workspace {0}'.format(correction_ws)
        delete_workspace(correction_ws)

        # DEBUG: where does raw workspace go?
        if ADS.doesExist(raw_ws_name):
            print '[DB...BAT] Check3 Raw workspace {0} is still there.'.format(raw_ws_name)
            mantidapi.GeneratePythonScript(InputWorkspace=raw_ws_name, Filename='/tmp/raw_1.py')

        else:
            print '[DB...BAT] Check3 Raw workspace {0} disappears after FilterEvents.'.format(raw_ws_name)

        if delete_split_ws:
            for chopped_ws_name in chopped_ws_name_list:
                print '[INFO] Delete chopped child workspace {0}'.format(chopped_ws_name)
                mantidapi.DeleteWorkspace(Workspace=chopped_ws_name)
                # DEBUG: where does raw workspace go?
                if ADS.doesExist(raw_ws_name):
                    print '[DB...BAT] Check2 Raw workspace {0} is still there after deleting {1}.' \
                          ''.format(raw_ws_name, chopped_ws_name)
                else:
                    print '[DB...BAT] Check2 Raw workspace {0} disappears after FilterEvents after deleting {1}.' \
                          ''.format(raw_ws_name, chopped_ws_name)
                    return False, str(RuntimeError('.... Debug Stop ... Debug Stop ...'))
    else:
        if delete_split_ws:
            print '[WARNING] Chopped workspaces cannot be deleted if the output directory is not specified.'
        for chopped_ws_name in chopped_ws_name_list:
            chop_list.append((None, chopped_ws_name))
    # END-IF

    # DEBUG: where does raw workspace go?
    if ADS.doesExist(raw_ws_name):
        print '[DB...BAT] Check2 Raw workspace {0} is still there.'.format(raw_ws_name)
        mantidapi.GeneratePythonScript(InputWorkspace=raw_ws_name, Filename='/tmp/raw_2.py')
    else:
        print '[DB...BAT] Check2 Raw workspace {0} disappears after FilterEvents.'.format(raw_ws_name)

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
    assert smooth_filter in ['Butterworth', 'Zeroing'], 'Smooth filter {0} is not supported.'.format(smooth_filter)
    assert isinstance(input_workspace, str), 'Input workspace name {0} must be a string but not a {1}.' \
                                             ''.format(input_workspace, type(input_workspace))
    assert workspace_does_exist(input_workspace), 'Input workspace {0} cannot be found in Mantid ADS.' \
                                                  ''.format(input_workspace)
    assert isinstance(param_order, int), 'Smoothing parameter "order" must be an integer.'
    assert isinstance(param_n, int), 'Smoothing parameter "n" must be an integer.'

    # get output workspace
    if output_workspace is None:
        output_workspace = '{0}_{1}_{2}_{3}'.format(input_workspace, smooth_filter, param_n, param_order)

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
            raise RuntimeError('Workspace index {0} is out of range [0, {0}).'
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
            workspace_index_list = range(smooth_ws.getNumberHistogram())
        else:
            workspace_index_list = [workspace_index]

        for ws_index in workspace_index_list:
            vec_y = smooth_ws.dataY(ws_index)
            for i_y in vec_y:
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
        raise RuntimeError('Unable to convert workspace {0} to dSpacing due to {1}.'.format(input_ws_name, run_err))

    # call Mantid algorithm StripVanadiumPeaks
    assert isinstance(fwhm, int), 'FWHM {0} must be an integer but not {1}.'.format(fwhm, type(fwhm))
    assert isinstance(background_type, str), 'Background type {0} must be a string but not {1}.' \
                                             ''.format(background_type, type(background_type))
    assert background_type in ['Linear', 'Quadratic'], 'Background type {0} is not supported.' \
                                                       'Candidates are {1}'.format(background_type, 'Linear, Quadratic')
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
            output_ws_name_i = output_ws_name + '__bank_{0}'.format(bank_id)
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


def sum_spectra(input_workspace, output_workspace):
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
    mantidapi.SumSpectra(InputWorkspsace=input_workspace,
                         OutputWorkspace=output_workspace)

    return


def workspace_does_exist(workspace_name):
    """ Check whether a workspace exists in analysis data service by its name
    Requirements: input workspace name must be a non-empty string
    :param workspace_name:
    :return: boolean
    """
    # Check
    assert isinstance(workspace_name, str), 'Workspace name must be string but not %s.' % str(type(workspace_name))
    assert len(workspace_name) > 0, 'It is impossible to for a workspace with empty string as name.'

    #
    does_exist = ADS.doesExist(workspace_name)

    return does_exist
