import sys
import os
import random
import numpy

# Import mantid directory
sys.path.append('/opt/mantidnightly/bin/')
sys.path.append('/Users/wzz/MantidBuild/debug/bin/')

import mantid
import mantid.api
import mantid.geometry
import mantid.simpleapi as mantidapi
from mantid.api import AnalysisDataService as ADS

EVENT_WORKSPACE_ID = "EventWorkspace"


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

    print '[DB...BAT] splitters: vector of time: ', vec_times.tolist()
    print '[DB...BAT] size of output vectors: ', len(vec_times), len(vec_ws)

    return vec_times, vec_ws


def delete_workspace(workspace):
    """ Delete a workspace in AnalysisService
    :param workspace:
    :return:
    """
    mantidapi.DeleteWorkspace(Workspace=workspace)

    return


def find_peaks(diff_data, ws_index, is_high_background, background_type, peak_profile='Gaussian',
               min_peak_height = 200,
               peak_pos_list=None):
    """
    Use FindPeaks() to find peaks in a given diffraction pattern
    :param diff_data: diffraction data in workspace
    :param peak_profile: specified peak profile
    :param auto: auto find peak profile or
    :return:
    """

    """ Use
    :param diff_data:
    :param peak_profile:
    :param auto:
    :return: List of tuples for peak information. Tuple = (peak center, height, width)
    """
    # check inputs
    assert ADS.doesExist(diff_data), 'Input workspace {0} does not exist in Mantid AnalysisDataService.' \
                                     ''.format(diff_data)
    matrix_workspace = ADS.retrieve(diff_data)
    assert isinstance(ws_index, int) and 0 <= ws_index < matrix_workspace.getNumberHistograms(), \
        'Workspace index {0} must be an integer in [0, {1}).'.format(ws_index, matrix_workspace.getNumberHistograms())

    # define output workspace name
    result_peak_ws_name = '{0}_FoundPeaks'.format(diff_data)

    # call Mantid
    arg_dict = {'InputWorkspace': diff_data,
                'WorkspaceIndex': ws_index,
                'HighBackground': is_high_background,
                'PeaksList': result_peak_ws_name,
                'MinimumPeakHeight': min_peak_height,
                'PeakFunction': peak_profile,
                'BackgroundType': background_type
                }
    mantidapi.FindPeaks(**arg_dict)

    # check
    if ADS.doesExist(result_peak_ws_name):
        peak_ws = mantidapi.AnalysisDataService.retrieve(result_peak_ws_name)
    else:
        raise RuntimeError('Failed to find peaks.')

    # mantidapi.FindPeaks(InputWorkspace=diff_data,
    #                     WorkspaceIndex=ws_index,
    #                     HighBackground=False,
    #                     PeaksList=out_ws_name,
    #                     MinimumPeakHeight=min_peak_height,
    #                     PeakFunction=peak_profile,
    #                     BackgroundType='Linear')


    # check the table from mantid algorithm FindPeaks
    col_names = peak_ws.getColumnNames()
    col_index_centre = col_names.index('centre')
    col_index_height = col_names.index('height')
    col_index_width = col_names.index('width')
    col_index_chi2 = col_names.index('chi2')

    peak_list = list()
    for index in range(peak_ws.rowCount()):
        peak_i_center = peak_ws.cell(index, col_index_centre)
        peak_i_chi2 = peak_ws.cell(index, col_index_chi2)
        if peak_i_chi2 < 100:
            peak_i_height = peak_ws.cell(index, col_index_height)
            peak_i_width = peak_ws.cell(index, col_index_width)
            peak_list.append((peak_i_center, peak_i_height, peak_i_width))

            print ('Find peak @ ', peak_i_center, 'chi2 = ', peak_i_chi2)
        else:
            print ('No peak   @ ', peak_i_center)

    return peak_list


def generate_event_filters_arbitrary(split_list, relative_time, tag):
    """ Generate event filter (splitters workspace) by arbitrary time stamps
    :param split_list:
    :param relative_time:
    :param tag: string for tag name
    :return: 2-tuple
        1. status (boolean)
        2. 2-tuple as splitter workspace's name and information (table) workspace's name
    """
    # check
    if relative_time is False:
        raise RuntimeError('It has not been implemented for absolute time stamp!')

    # check
    assert isinstance(split_list, list), 'split list should be a list but not a %s.' \
                                         '' % str(type(split_list))
    assert isinstance(tag, str), 'Split tag must be a string but not %s.' % str(type(tag))
    assert len(tag) > 0, 'Split tag cannot be empty.'

    # create an empty workspace
    splitters_ws_name = tag
    info_ws_name = tag + '_Info'

    # create matrix workspace for splitter
    time_list = list()
    ws_list = list()

    # convert tuple list to time list and ws index list
    for index, split_tup in enumerate(split_list):
        # get start time and stop time
        start_time = split_tup[0]
        stop_time = split_tup[1]
        ws_index = split_tup[2]
        print '[DB...BAT] stop time = ', stop_time

        # append to list
        if index == 0:
            # add start time
            time_list.append(start_time)
        elif start_time > time_list[-1] + 1.0E-15:
            # add gap
            time_list.append(start_time)
            ws_list.append(-1)
        # add stop time
        time_list.append(stop_time)
        ws_list.append(ws_index)
    # END-FOR

    # convert list to numpy vector
    time_vec = numpy.array(time_list)
    ws_vec = numpy.array(ws_list)

    # create workspace
    mantidapi.CreateWorkspace(DataX=time_vec, DataY=ws_vec, NSpec=1, WorkspaceTitle='relative',
                              OutputWorkspace=splitters_ws_name)

    # TODO/NOW
    print '[NOT FINISHED YET!]'

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


def get_sample_log_info(src_workspace):
    """ Ger sample log information including size of log and name of log
    :param src_workspace: workspace which the sample logs are from
    :return: a list of 2-tuples as property's length and name
    """
    run = src_workspace.run()

    prop_info_list = list()
    for p in run.getProperties():
        p_name = p.name
        if isinstance(p, mantid.kernel.FloatTimeSeriesProperty) is False:
            continue
        size = p.size()
        prop_info_list.append((size, p_name))

    prop_info_list.sort()

    return prop_info_list


def get_sample_log_names(src_workspace, smart=False):
    """
    From workspace get sample log names as FloatTimeSeriesProperty
    :param src_workspace:
    :param smart:
    :return:
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

    # FIXME: find out the difference!
    vec_times = out_ws.readX(0)[:]
    vec_value = out_ws.readY(0)[:]

    return vec_times, vec_value


def get_data_from_gsas(gsas_file_name):
    """
    Load and get data from a GSAS file
    :param gsas_file_name:
    :return: a dictionary of 3-array-tuples (x, y, e). KEY = workspace index (from 0 ...)
    """
    # check input
    assert isinstance(gsas_file_name, str), 'Input GSAS file name {0} must be an integer but not a {1}.' \
                                            ''.format(gsas_file_name, type(gsas_file_name))

    # get output workspace name
    out_ws_name = os.path.basename(gsas_file_name).split('.')[0] + '_gss'

    # load GSAS file
    load_gsas_file(gss_file_name=gsas_file_name, out_ws_name=out_ws_name)

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
    assert isinstance(workspace_name, str) and isinstance(point_data, bool)
    assert workspace_does_exist(workspace_name), 'Workspace %s does not exist.' % workspace_name
    assert isinstance(target_unit, str) or target_unit is None,\
        'Target {0} unit must be a string {0} or None but not a {1}'.format(target_unit, type(target_unit))
    assert isinstance(start_bank_id, int) and start_bank_id >= 0,\
        'Start-Bank-ID {0} must be a non-negetive integer but not {1}.' \
        ''.format(start_bank_id, type(start_bank_id))

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

    # get unit
    current_unit = get_workspace_unit(workspace_name)
    if current_unit != target_unit and target_unit is not None:
        # convert unit if the specified target unit is different
        mantidapi.ConvertUnits(InputWorkspace=workspace_name, OutputWorkspace=temp_ws_name,
                               Target=target_unit)
        current_unit = target_unit
        use_temp = True
    # END-IF

    # Convert to point data
    workspace = ADS.retrieve(workspace_name)
    if point_data and workspace.isHistogramData():
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


def get_workspace_unit(workspace_name):
    """

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


def retrieve_workspace(ws_name):
    """ Retrieve workspace from AnalysisDataService
    Purpose:
        Get workspace from Mantid's analysis data service
    Requirements:
        workspace name is a string
    Guarantee:
        return the reference to the workspace or None if it does not exist
    :param ws_name:
    :return: workspace instance
    """
    assert isinstance(ws_name, str), 'Input ws_name %s is not of type string, but of type %s.' % (str(ws_name),
                                                                                                  str(type(ws_name)))

    if ADS.doesExist(ws_name) is False:
        return None

    return mantidapi.AnalysisDataService.retrieve(ws_name)


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


def load_gsas_file(gss_file_name, out_ws_name, standard_bin_workspace):
    """ Load GSAS file and set instrument information as 2-bank VULCAN and convert units to d-spacing
    Requirements: GSAS file name is a full path; output workspace name is a string;
    Guarantees:
    :param gss_file_name:
    :param out_ws_name:
    :param standard_bin_workspace:
    :return: output workspace name
    """
    # TODO/ISSUE/62 - Implement feature with standard_bin_workspace...
    from reduce_VULCAN import align_bins

    # Check
    assert isinstance(gss_file_name, str), 'GSAS file name should be string but not %s.' % str(type(gss_file_name))
    assert isinstance(out_ws_name, str), 'Output workspace name should be a string but not %s.' % str(type(out_ws_name))

    # Load GSAS
    mantidapi.LoadGSS(Filename=gss_file_name, OutputWorkspace=out_ws_name)
    gss_ws = retrieve_workspace(out_ws_name)
    assert gss_ws is not None, 'Output workspace cannot be found.'

    # set instrument geometry: this is for VULCAN-only
    if gss_ws.getNumberHistograms() == 2:
        mantid.simpleapi.EditInstrumentGeometry(Workspace=out_ws_name,
                                                PrimaryFlightPath=43.753999999999998,
                                                SpectrumIDs='1,2',
                                                L2='2.00944,2.00944',
                                                Polar='90,270')
    else:
        raise RuntimeError('It is not implemented for cases more than 2 spectra.')

    # convert unit and to point data
    align_bins(out_ws_name, standard_bin_workspace)
    mantidapi.ConvertUnits(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name,
                           Target='dSpacing')
    # mantidapi.ConvertToPointData(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name)

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


def match_bins():
    # TODO/ISSUE/62 - Implement
    return True


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
    assert out_ws
    
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
    # TODO/ISSUE/62 - Replace all blabla by words making sense
    # Check requirements
    assert isinstance(source_ws_name, str), 'source workspace name blabla'
    src_ws = retrieve_workspace(source_ws_name)
    assert src_ws.getNumberHistograms() < 10, 'blabla'
    
    assert isinstance(out_gss_file, str), 'out gss blabla'
    assert isinstance(ipts, int), 'IPTS number must be an integer but not %s.' % str(type(ipts))
    assert isinstance(binning_reference_file, str), 'blabla333'
    if len(binning_reference_file) > 0:
        assert os.path.exists(binning_reference_file), 'blabla444'
    assert isinstance(gss_parm_file, str), 'blabla555'

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


def split_event_data(raw_file_name, split_ws_name, info_table_name, target_ws_name=None,
                     tof_correction=False, output_directory=None, delete_split_ws=True):
    """
    split event data file according pre-defined split workspace. optionally the split workspace
    can be saved to NeXus files
    :param raw_file_name:
    :param split_ws_name:
    :param info_table_name:
    :param target_ws_name:
    :param tof_correction:
    :param output_directory:
    :param delete_split_ws: True/(list of ws names, list of ws objects); False/error message
    :return:
    """
    # Check requirements
    assert workspace_does_exist(split_ws_name)
    assert workspace_does_exist(info_table_name)
    assert isinstance(raw_file_name, str), 'Input file name must be a string but not %s.' % type(raw_file_name)

    # rule out some unsupported scenario
    if output_directory is None and delete_split_ws:
        raise RuntimeError('It is not supported that no file is written (output_dir is None) '
                           'and split workspace is to be delete.')
    elif output_directory is not None:
        assert isinstance(output_directory, str), 'Output directory %s must be a string but not %s.' \
                                                  '' % (str(output_directory), type(output_directory))

    # load the file to workspace
    event_ws_name = os.path.split(raw_file_name)[1].split('.')[0]
    load_nexus(data_file_name=raw_file_name, output_ws_name=event_ws_name, meta_data_only=False)

    # process TOF correction
    if tof_correction is True:
        correction = 'Elastic'
    else:
        correction = 'None'

    # process the target workspace name
    if target_ws_name is None:
        target_ws_name = event_ws_name + '_split'
    else:
        assert isinstance(target_ws_name, str), 'Target workspace name %s must be a string but not %s.' \
                                                '' % (str(target_ws_name), type(target_ws_name))

    # split workspace
    ret_list = mantidapi.FilterEvents(InputWorkspace=event_ws_name,
                                      SplitterWorkspace=split_ws_name,
                                      InformationWorkspace=info_table_name,
                                      OutputWorkspaceBaseName=target_ws_name,
                                      FilterByPulseTime=False,
                                      GroupWorkspaces=True,
                                      CorrectionToSample=correction,
                                      SplitSampleLogs=True,
                                      OutputWorkspaceIndexedFrom1=True
                                      )

    try:
        correction_ws = ret_list[0]
        num_split_ws = ret_list[1]
        chopped_ws_name_list = ret_list[2]
        assert num_split_ws == len(chopped_ws_name_list)
    except IndexError:
        return False, 'Failed to split data by FilterEvents.'

    if len(ret_list) != 3 + len(chopped_ws_name_list):
        return False, 'Failed to split data by FilterEvents due incorrect objects returned.'

    # Save result
    if output_directory is not None:
        for chopped_ws_name in chopped_ws_name_list:
            file_name = os.path.join(output_directory, chopped_ws_name) + '.nxs'
            mantidapi.SaveNexusProcessed(InputWorkspace=chopped_ws_name, Filename=file_name)

    # Clear
    delete_workspace(correction_ws)
    if delete_split_ws:
        for chopped_ws_name in chopped_ws_name_list:
            mantidapi.DeleteWorkspace(Workspace=chopped_ws_name)

    # Output
    if delete_split_ws:
        ret_obj = False
    else:
        ret_obj = (chopped_ws_name_list, ret_list[3:])

    return True, ret_obj


def smooth_vanadium(input_workspace, output_workspace=None, workspace_index=None,
                    smooth_filter='Butterworth', param_n=20, param_order=2):
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

    return output_workspace


def strip_vanadium_peaks(input_workspace, output_workspace=None, fwhm=7, peak_pos_tol=0.05,
                         background_type="Quadratic", is_high_background=True):
    """
    Strip vanadium peaks
    :except: run time error

    :param input_workspace:
    :param output_workspace:
    :param fwhm: integer peak FWHM
    :param peak_pos_tol: float peak position tolerance
    :param background_type:
    :param is_high_background:
    :return: output workspace's name, indicating it successfully strips vanadium peaks.
    """
    # check inputs
    assert isinstance(input_workspace, str), 'Input workspace {0} must be a string but not a {1}.' \
                                             ''.format(input_workspace, type(input_workspace))
    if not workspace_does_exist(input_workspace):
        raise RuntimeError('Workspace {0} does not exist in ADS.'.format(input_workspace))

    if output_workspace is None:
        output_workspace = input_workspace + '_no_peak'

    # make sure that the input workspace is in unit dSpacing
    try:
        if get_workspace_unit(input_workspace) != 'dSpacing':
            mantidapi.ConvertUnits(InputWorkspace=input_workspace, OutputWorkspace=input_workspace,
                                   Target='dSpacing')
    except RuntimeError as run_err:
        raise RuntimeError('Unable to convert workspace {0} to dSpacing due to {1}.'.format(input_workspace), run_err)

    # call Mantid algorithm StripVanadiumPeaks
    assert isinstance(fwhm, int), 'FWHM {0} must be an integer but not {1}.'.format(fwhm, type(fwhm))
    assert isinstance(background_type, str), 'Background type {0} must be a string but not {1}.' \
                                             ''.format(background_type, type(background_type))
    assert background_type in ['Linear', 'Quadratic'], 'Background type {0} is not supported.' \
                                                       'Candidates are {1}'.format(background_type, 'Linear, Quadratic')
    try:
        # strip vanadium peaks. and the output workspace is Histogram/PointData (depending on input) in unit dSpacing
        mantidapi.StripVanadiumPeaks(InputWorkspace=input_workspace,
                                     OutputWorkspace=output_workspace,
                                     FWHM=fwhm,
                                     PeakPositionTolerance=peak_pos_tol,
                                     BackgroundType=background_type,
                                     HighBackground=is_high_background)

        # peakless_ws = ADS.retrieve(output_workspace)
        # print '[DB...BAT] Peakless WS: ', peakless_ws.isHistogramData(), peakless_ws.getAxis(0).getUnit().unitID()

    except RuntimeError as run_err:
        raise RuntimeError('Failed to execute StripVanadiumPeaks on workspace {0} due to {1}'
                           ''.format(input_workspace, run_err))

    return output_workspace


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

