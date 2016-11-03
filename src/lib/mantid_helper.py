import sys
import os
import math
import numpy

# Import mantid directory
sys.path.append('/opt/mantidnightly/bin/')
sys.path.append('/Users/wzz/MantidBuild/debug/bin/')

import mantid
import mantid.api
import mantid.geometry
import mantid.simpleapi as mantidapi

EVENT_WORKSPACE_ID = "EventWorkspace"


def delete_workspace(workspace):
    """ Delete a workspace in AnalysisService
    :param workspace:
    :return:
    """
    mantidapi.DeleteWorkspace(Workspace=workspace)

    return


def find_peaks(diff_data, peak_profile, auto):
    """ Use FindPeaks() to find peaks in a given diffraction pattern
    :param diff_data:
    :param peak_profile:
    :param auto:
    :return: List of tuples for peak information. Tuple = (peak center, height, width)
    """
    #mantidapi.FindPeaks(InputWorkspace=diff_data, # '82403_gda',
    #                    WorkspaceIndex=1,
    #                    BackgroundType='Quadratic',
    #                    PeaksList='peaks')

    # TODO/NOW - Make it work in the code!

    ws_index = 0
    out_ws_name = '70269_gda_peaks'
    min_peak_height = 200
    peak_profile = 'Gaussian'

    mantidapi.FindPeaks(InputWorkspace=diff_data,
                        WorkspaceIndex=ws_index,
                        HighBackground=False,
                        PeaksList=out_ws_name,
                        MinimumPeakHeight=min_peak_height,
                        PeakFunction=peak_profile,
                        BackgroundType='Linear')

    peak_ws = mantidapi.AnalysisDataService.retrieve(out_ws_name)
    # check blablabla...

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
    :return:
    """
    # TODO/ISSUE/51: clean and doc and etc.

    # Check requirements
    assert isinstance(ws_name, str)
    src_ws = retrieve_workspace(ws_name)
    assert src_ws is not None

    assert isinstance(splitter_ws_name, str)
    assert isinstance(info_ws_name)

    assert isinstance(log_name, str)

    # Call Mantid algorithm
    mantidapi.GenerateEventsFilter(InputWorkspace=ws_name,
                                   OutputWorkspace=splitter_ws_name, InformationWorkspace=info_ws_name,
                                   LogName=log_name,
                                   StartTime=min_time, StopTime=max_time,
                                   MinimumLogValue=min_log_value,
                                   MaximumLogValue=max_log_value,
                                   LogValueInterval=log_value_interval,
                                   FilterLogValueByChangingDirection=log_value_change_direction)

    return True, (splitter_ws_name, info_ws_name)


def generate_event_filters_by_time(ws_name, splitter_ws_name, info_ws_name,
                                   start_time, stop_time, delta_time, time_unit):
    """
    Generate event filters by time interval
    Purpose: Generate splitters by calling Mantid's GenerateEventsFilter
    Requirements:
    :param ws_name:
    :param start_time:
    :param stop_time:
    :param delta_time:
    :param time_unit:
    :return: 2-tuple. (1) boolean (2) message
    """
    # TODO/ISSUE/51: clean and doc and etc.
    # assert
    # assert

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
        mantidapi.GenerateEventsFilter(**my_arg_dict)
    except RuntimeError as e:
        return False, str(e)

    return True, ''


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


def get_data_from_workspace(workspace_name, point_data):
    """
    Purpose: get data from a workspace
    Requirements: a valid matrix workspace is given
    Guarantees: transform all the data to 1-dimension arrays.
    :param workspace_name:
    :param point_data: If point data is true, then the output arrays must have equal sizes of x and y arrays
    :return: a dictionary of 3-array-tuples (x, y, e). KEY = workspace index (from 0 ...)
    """
    # Requirements
    assert isinstance(workspace_name, str) and isinstance(point_data, bool)
    assert workspace_does_exist(workspace_name), 'Workspace %s does not exist.' % workspace_name

    # Convert to point data
    if point_data is True:
        mantidapi.ConvertToPointData(InputWorkspace=workspace_name,
                                     OutputWorkspace=workspace_name)

    # Set up variables
    data_set_dict = dict()
    workspace = retrieve_workspace(workspace_name)
    
    # Get data
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
    
        data_set_dict[i_ws] = (data_x, data_y, data_e)
    
    # END-FOR
    
    return data_set_dict


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

    if mantid.AnalysisDataService.doesExist(ws_name) is False:
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


def load_gsas_file(gss_file_name, out_ws_name):
    """ Load GSAS file and set instrument information as 2-bank VULCAN and convert units to d-spacing
    Requirements: GSAS file name is a full path; output workspace name is a string;
    Guarantees:
    :param gss_file_name:
    :param out_ws_name:
    :return: output workspace name
    """
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
    mantidapi.ConvertUnits(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name,
                           Target='dSpacing')
    mantidapi.ConvertToPointData(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name)

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
    # TODO/NOW/40 - Doc and check!
    # bla..bla..bla..

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

    # TODO/NOW/40 - Check existence of the workspaces output from LoadCalFile
    # blablabal

    return True, [offset_ws_name, grouping_ws_name, mask_ws_name, cal_ws_name]


def mtd_align_and_focus(event_ws_name, reduction_parameters, group_ws_name, offset_ws_name, cal_ws_name):
    """ Align and focus raw event workspaces: the original workspace will be replaced
    Purpose:
        Run Mantid.AlignAndFocus() by current parameters
    Requirements:
        Input event_wksp is not None
        Output workspace name is string
        All requirements for align and focus in Mantid is satisifed
    Guarantees:
        Event workspace is reduced
    :param event_ws_name:
    :param reduction_parameters:
    :param group_ws_name:
    :param offset_ws_name:
    :return: focused event workspace
    """
    # FIXME/TODO/NOW/40 Make PowderReductionParameters a new module
    from reductionmanager import PowderReductionParameters

    # Check requirement
    assert isinstance(event_ws_name, str)
    event_ws = retrieve_workspace(event_ws_name)
    
    assert event_ws.id() == EVENT_WORKSPACE_ID, \
        'Input must be an EventWorkspace for align and focus. Current input is %s' % event_ws.id()
    assert isinstance(reduction_parameters, PowderReductionParameters), \
        'Input parameter must be of an instance of PowderReductionParameters'
    
    assert isinstance(group_ws_name, str)
    assert workspace_does_exist(group_ws_name)
    assert isinstance(offset_ws_name, str)
    assert workspace_does_exist(offset_ws_name)
    
    # Execute algorithm AlignAndFocusPowder()
    # Unused properties: DMin, DMax, TMin, TMax, MaskBinTable,
    user_geometry_dict = dict()
    if reduction_parameters.min_tof is None or reduction_parameters.max_tof is None:
        # if TOF range is not set up, use default min and max
        user_geometry_dict['DMin'] = 0.5
        user_geometry_dict['DMax'] = 5.5
    
    # FIXME - Need to find out what it is in __snspowderreduction
    mantidapi.AlignAndFocusPowder(InputWorkspace=event_ws_name,
                                  OutputWorkspace=event_ws_name,   # in-place align and focus
                                  GroupingWorkspace=group_ws_name,
                                  OffsetsWorkspace=offset_ws_name,
                                  CalibrationWorkspace=cal_ws_name,
                                  MaskWorkspace=None,  # FIXME - NO SURE THIS WILL WORK!
                                  Params=reduction_parameters.form_binning_parameter(),
                                  PreserveEvents=reduction_parameters.preserve_events,
                                  RemovePromptPulseWidth=0,  # Fixed to 0
                                  CompressTolerance=reduction_parameters.compress_tolerance,
                                  # 0.01 as default
                                  Dspacing=True,            # fix the option
                                  UnwrapRef=0,              # do not use = 0
                                  LowResRef=0,              # do not use  = 0
                                  CropWavelengthMin=0,      # no in use = 0
                                  CropWavelengthMax=0,
                                  LowResSpectrumOffset=-1,  # powgen's option. not used by vulcan
                                  PrimaryFlightPath=43.753999999999998,
                                  SpectrumIDs='1,2',
                                  L2='2.00944,2.00944',
                                  Polar='90.122,90.122',
                                  Azimuthal='0,0',
                                  ReductionProperties='__snspowderreduction',
                                  **user_geometry_dict)
    
    # Check
    out_ws = retrieve_workspace(event_ws_name)
    assert out_ws is not None
    
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
    :param event_ws_name:
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


def mtd_save_vulcan_gss(source_ws_name, out_gss_file, ipts, binning_reference_file, gss_parm_file):
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
    assert isinstance(source_ws_name, str)
    src_ws = retrieve_workspace(source_ws_name)
    assert src_ws.getNumberHistograms() < 10
    
    assert isinstance(out_gss_file, str)
    assert isinstance(ipts, int), 'IPTS number must be an integer but not %s.' % str(type(ipts))
    assert isinstance(binning_reference_file, str)
    assert os.path.exists(binning_reference_file)
    assert isinstance(gss_parm_file, str)
    
    final_ws_name = source_ws_name + '_IDL'
    
    mantidapi.SaveVulcanGSS(InputWorkspace=source_ws_name,
                            BinFilename=binning_reference_file,
                            OutputWorkspace=final_ws_name,
                            GSSFilename=gss_parm_file,
                            IPTS = ipts,
                            GSSParmFilename=gss_parm_file)

    return


def save_event_workspace(event_ws_name, nxs_file_name):
    """

    :param event_ws_name:
    :param nxs_file_name:
    :return:
    """
    mantidapi.SaveNexus(InputWorkspace=event_ws_name, Filename=nxs_file_name)

    return


def split_event_data(raw_event_ws_name, splitter_ws_name, info_ws_name, split_ws_base_name, tof_correction=False):
    """
    Split events in a workspace
    Requirements: given raw event workspace, splitter workspace, information workspace are in ADS.
    :param raw_event_ws_name:
    :param splitter_ws_name:
    :param info_ws_name:
    :param split_ws_base_name:
    :param tof_correction:
    :return: 2-tuple (boolean, object): True/(list of ws names, list of ws objects); False/error message
    """
    # Check requirements
    assert workspace_does_exist(raw_event_ws_name)
    assert workspace_does_exist(splitter_ws_name)
    assert workspace_does_exist(info_ws_name)
    assert isinstance(splitter_ws_name, str)

    if tof_correction is True:
        correction = 'Elastic'
    else:
        correction = 'None'

    # print '[DB] Information workspace = %s of type %s\n' % (str(info_ws_name), str(type(info_ws_name)))
    ret_list = mantidapi.FilterEvents(InputWorkspace=raw_event_ws_name,
                                      SplitterWorkspace=splitter_ws_name,
                                      InformationWorkspace=info_ws_name,
                                      OutputWorkspaceBaseName=split_ws_base_name,
                                      FilterByPulseTime=False,
                                      GroupWorkspaces=True,
                                      CorrectionToSample=correction,
                                      SplitSampleLogs=True,
                                      OutputWorkspaceIndexedFrom1=True
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
    does_exist = mantid.AnalysisDataService.doesExist(workspace_name)

    return does_exist

