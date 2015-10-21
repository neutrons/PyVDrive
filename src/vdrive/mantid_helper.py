import sys
import numpy

import mantid
import mantid.simpleapi as mantidapi


def generate_events_filter(ws_name, log_name, min_time, max_time, relative_time,
                           min_log_value, max_log_value, log_value_interval,
                           value_change_direction,
                           splitter_ws_name, info_ws_name):
    """
    Generate event filter by log value
    :param ws_name:
    :param log_name:
    :param min_time:
    :param max_time:
    :param relative_time:
    :param min_log_value:
    :param max_log_value:
    :param log_value_interval:
    :param splitter_ws_name:
    :param info_ws_name:
    :return:
    """
    if relative_time is False:
        raise RuntimeError('It has not been implemented to use absolute start/stop time.')

    if log_value_interval is None:
        # one and only one interval from min_log_value to max_log_value
        raise RuntimeError('I need to think of how to deal with this case.')

    if value_change_direction is None:
        value_change_direction = 'Both'
    elif value_change_direction not in ['Both', 'Increase', 'Decrease']:
        return False, 'Value change direction %s is not supported.' % value_change_direction

    mantidapi.GenerateEventsFilter(InputWorkspace=ws_name,
                                   OutputWorkspace=splitter_ws_name, InformationWorkspace=info_ws_name,
                                   LogName=log_name,
                                   StartTime=min_time, StopTime=max_time,
                                   MinimumLogValue=min_log_value,
                                   MaximumLogValue=max_log_value,
                                   LogValueInterval=log_value_interval,
                                   FilterLogValueByChangingDirection=value_change_direction)

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
