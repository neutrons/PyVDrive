import sys
import os
import numpy

# Import mantid directory
user_root = os.path.expanduser('~')
for p in sys.path:
    if os.path.isdir(p):
        dir_p = p
    else:
        dir_p = os.path.dirname(p)
    print p, dir_p
    if dir_p.startswith(user_root) and dir_p.count('site-package') > 0:
        mantid_path = os.path.join(dir_p, 'Mantid')
        print 'mantid path = ', mantid_path
        if os.path.exists(mantid_path) is True:
            sys.path.append(mantid_path)
            break

import mantid
import mantid.api
import mantid.simpleapi as mantidapi


def delete_workspace(workspace):
    """
    :param workspace:
    :return:
    """
    mantidapi.DeleteWorkspace(Workspace=workspace)

    return


def generate_event_filters_by_log(ws_name, splitter_ws_name, info_ws_name,
                                  min_time, max_time,
                                  log_name, min_log_value, max_log_value, log_value_interval,
                                  log_value_change_direction):
    """

    :return:
    """
    # TODO/FIXME Doc
    print '[TRACE] Generate Filter By Log'
    mantidapi.GenerateEventsFilter(InputWorkspace=ws_name,
                                   OutputWorkspace=splitter_ws_name, InformationWorkspace=info_ws_name,
                                   LogName=log_name,
                                   StartTime=min_time, StopTime=max_time,
                                   MinimumLogValue=min_log_value,
                                   MaximumLogValue=max_log_value,
                                   LogValueInterval=log_value_interval,
                                   FilterLogValueByChangingDirection=log_value_change_direction)

    return


def generate_event_filters_by_time(ws_name, splitter_ws_name, info_ws_name,
                                   start_time, stop_time, delta_time, time_unit):
    """
    TODO/FIXME Doc!
    :param ws_name:
    :param start_time:
    :param stop_time:
    :param delta_time:
    :param time_unit:
    :param relative_time:
    :return:
    """
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

    print my_arg_dict
    print

    try:
        mantidapi.GenerateEventsFilter(**my_arg_dict)
        """
        mantidapi.GenerateEventsFilter(InputWorkspace=ws_name,
                                       OutputWorkspace=splitter_ws_name,
                                       InformationWorkspace=info_ws_name,
                                       StartTime=start_time,
                                       StopTime=stop_time,
                                       TimeInterval=delta_time)
        """
    except RuntimeError as e:
        return False, str(e)

    return True, (splitter_ws_name, info_ws_name)


def get_run_start(workspace, unit):
    """ Get run start time
    :param workspace:
    :param unit: nanosecond(s), second(s)
    :return:
    """
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
    if unit.lower().startswith('nanosecond'):
        pass
    elif unit.lower().startswith('second'):
        run_start *= 1.E-9
    else:
        raise RuntimeError('Unit %s is not supported by get_run_start().' % unit)

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


def get_sample_log_names(src_workspace):
    """
    From workspace get sample log names as FloatTimeSeriesProperty
    :param src_workspace:
    :return:
    """
    run = src_workspace.run()
    property_list = run.getProperties()
    name_list = list()

    for item in property_list:
        if isinstance(item, mantid.kernel.FloatTimeSeriesProperty):
            name_list.append(item.name)

    return name_list


def get_sample_log_value(src_workspace, sample_log_name, start_time, stop_time, relative):
    """
    Get sample log value
    :param src_workspace:
    :param sample_log_name:
    :return: 2-tuple.  vector of epoch time in unit of second. vector of log value
    """
    # Get property
    run = src_workspace.getRun()
    this_property = run.getProperty(sample_log_name)
    assert isinstance(this_property, mantid.kernel.FloatTimeSeriesProperty)

    # Get vectors
    vec_time_raw = this_property.times
    vec_times = numpy.ndarray(shape=(len(vec_time_raw), ), dtype='float')
    for i in xrange(len(vec_time_raw)):
        vec_times[i] = vec_time_raw[i].totalNanoseconds()*1.0E-9

    vec_value = this_property.value

    # Relative time?
    if relative is True:
        run_start_time = run.startTime().totalNanoseconds()*1.0E-9
        vec_times -= run_start_time

    # Get partial data
    get_partial = False
    start_index = 0
    stop_index = len(vec_times)
    if start_time is not None:
        assert isinstance(start_time, float)
        start_index = numpy.searchsorted(vec_times, start_time)
        get_partial = True
    if stop_time is not None:
        stop_index = numpy.searchsorted(vec_times, stop_time)
        get_partial = True
    if get_partial:
        vec_times = vec_times[start_index:stop_index]
        vec_value = vec_value[start_index:stop_index]

    if len(vec_times) == 0:
        print 'Start = ', start_time, 'Stop = ', stop_time
        raise XXX
        raise NotImplementedError('DB Stop')

    return vec_times, vec_value


def get_time_segments_from_splitters(split_ws_name, time_shift, unit):
    """
    TODO/NOW - Doc!
    :param split_ws_name:
    :param time_shift: always in the same unit as
    :return:
    """
    split_ws = retrieve_workspace(split_ws_name)
    if split_ws is None:
        raise RuntimeError('Workspace %s does not exist.' % split_ws_name)

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


def event_data_ws_name(run_number):
    """ workspace name for raw event data
    :param run_number:
    :return:
    """
    return 'VULCAN_%d_Raw' % run_number


def retrieve_workspace(ws_name):
    """

    :param ws_name:
    :return:
    """
    if isinstance(ws_name, str) is False:
        raise RuntimeError('Input ws_name %s is not of type string, but of type %s.' % (str(ws_name),
                                                                                        str(type(ws_name))))

    if mantid.AnalysisDataService.doesExist(ws_name) is False:
        return None

    return mantidapi.AnalysisDataService.retrieve(ws_name)



def splitted_ws_base_name(run_number, out_base_name):
    """
    Workspace name for splitted event data
    :param run_number:
    :param out_base_name:
    :return:
    """
    return 'VULCAN_%d_%s' % (run_number, out_base_name)


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


def split_event_data(raw_event_ws_name, splitter_ws_name, info_ws_name, splitted_ws_base_name, tof_correction=False):
    """
    Split workspaces
    :param raw_event_ws_name:
    :param splitter_ws_name:
    :param info_ws_name:
    :param tof_correction:
    :return: 2-tuple (boolean, object): True/(list of ws names, list of ws objects); False/error message
    """
    if tof_correction is True:
        correction = 'Elastic'
    else:
        correction = 'None'

    print '[DB] Information workspace = %s of type %s\n' % (str(info_ws_name), str(type(info_ws_name)))
    ret_list = mantidapi.FilterEvents(InputWorkspace=raw_event_ws_name,
                                      SplitterWorkspace=splitter_ws_name,
                                      InformationWorkspace=info_ws_name,
                                      OutputWorkspaceBaseName=splitted_ws_base_name,
                                      FilterByPulseTime=False,
                                      GroupWorkspaces=True,
                                      CorrectionToSample=correction,
                                      # FIXME/TODO This should be fixed in Mantid. Upon that, this option will be true.
                                      SplitSampleLogs=False
                                      )

    try:
        correction_ws = ret_list[0]
        num_split_ws = ret_list[1]
        split_ws_name_list = ret_list[2]
        assert num_split_ws == len(split_ws_name_list)
    except IndexError:
        return False, 'Failed to split data by FilterEvents.'

    if len(ret_list) != 3 + len(split_ws_name_list):
        return False, 'Failed to split data by FilterEvents due incorrect objects returned.'

    # Clear
    delete_workspace(correction_ws)

    # Output
    ret_obj = (split_ws_name_list, ret_list[3:])

    return True, ret_obj
