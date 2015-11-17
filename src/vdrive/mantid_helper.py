import sys
import numpy

import mantid
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


def get_sample_log_value(src_workspace, sample_log_name, relative):
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
    vec_time = numpy.ndarray(shape=(len(vec_time_raw), ), dtype='float')
    for i in xrange(len(vec_time_raw)):
        vec_time[i] = vec_time_raw[i].totalNanoseconds()*1.0E-9

    vec_value = this_property.value

    # Relative time?
    if relative is True:
        start_time = run.startTime().totalNanoseconds()*1.0E-9
        vec_time -= start_time

    return vec_time, vec_value


def event_data_ws_name(run_number):
    """ workspace name for raw event data
    :param run_number:
    :return:
    """
    return 'VULCAN_%d_Raw' % run_number


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
