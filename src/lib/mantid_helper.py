import sys
import os
import numpy

# Import mantid directory
sys.path.append('/opt/mantidnightly/bin/')
sys.path.append('/Users/wzz/MantidBuild/debug/bin/')

import mantid
import mantid.api
import mantid.geometry
import mantid.simpleapi as mantidapi

EVENT_WORKSPACE_ID = "EventWorkspace"


class UnitCell(object):
    """ A simple class to pass the unit cell information
    """
    PRIMITIVE = 0
    BCC = 1
    FCC = 2
    BC = 3   # body-centre
    FC = 4   # face-centre
    HCP = 5  # HCP

    SpaceGroupDict = {
        PRIMITIVE: 'P m m m',
        BC: 'I m m m',
        FC: 'F m m m',
        HCP: 'P 63/m m c',
        BCC: 'I m -3 m',
        FCC: 'F d -3 m',
    }

    def __init__(self, unit_cell_type, a, b=None, c=None):
        """
        Initialize and set up a unit cell
        :param unit_cell_type:
        :param a:
        :param b:
        :param c:
        :return:
        """
        # unit cell type, primitive, bcc or fcc
        assert 0 <= unit_cell_type <= 4, 'Unit cell type %d is not supported.' % unit_cell_type
        self._unitCellType = unit_cell_type

        # lattice size
        assert isinstance(a, float)
        assert a > 0, 'Lattice parameter must larger than 0.'
        self._a = a

        assert (b is None and c is None) or (b is not None and c is not None)
        if b is None and c is None:
            # cubic
            self._isCubic = True
            self._b = self._a
            self._c = self._a
        else:
            # tetrehedron
            self._isCubic = False
            assert isinstance(b, float)
            assert b > 0
            self._b = b
            assert isinstance(c, float)
            assert c > 0
            self._c = c

        return

    @property
    def space_group(self):
        """ Get space group
        :return:
        """
        return UnitCell.SpaceGroupDict[self._unitCellType]

    def get_cell_parameters(self):
        """
        Put cell parameters a, b and c to a list and return
        :return: list of 3 elements, a, b and c
        """
        return [self._a, self._b, self._c]

    def is_cubic(self):
        """ Whether it is cubic
        :return:
        """
        return self._isCubic


def calculate_reflections(unit_cell, min_d, max_d):
    """ Calculate reflections' position in d-spacing
    Purpose:
        Calculate a crystal's Bragg peaks' positions in d-spacing
    Requirements:
        Crystal unit cell must be tetrahegonal (including cubic)
        Lattice parameters (a, b, c) must be valid
        d-spacing range must be given
        Structure must be primitive, body-centre, or face-centre
    Guarantees:
        Bragg peaks' position along with HKL will be returned
    :param unit_cell: UnitCell instance
    :param min_d: minimum d-spacing value
    :param max_d: maximum d-spacing value
    :return: a list of reflections.  Each reflection is a 2-tuple as ... ...
    """
    from mantid.geometry import CrystalStructure, ReflectionGenerator, ReflectionConditionFilter

    def get_generator(lattice_parameters, space_group):
        """
        """
        crystal_structure = CrystalStructure(' '.join([str(x) for x in lattice_parameters]), space_group, '')
        generator = ReflectionGenerator(crystal_structure, ReflectionConditionFilter.Centering)
        return generator

    def get_unique_reflections(lattice_parameters, space_group, d_min, d_max):
        """
        """
        generator = get_generator(lattice_parameters, space_group)

        hkls = generator.getUniqueHKLs(d_min, d_max)

        dvalues = generator.getDValues(hkls)

        return zip(hkls, dvalues)

    def get_all_reflections(lattice_parameters, space_group, d_min, d_max):
        """
        """
        generator = get_generator(lattice_parameters, space_group)

        hkls = generator.getHKLs(d_min, d_max)

        dvalues = generator.getDValues(hkls)

        return zip(hkls, dvalues)

    # Check inputs
    assert isinstance(unit_cell, UnitCell), 'Input must be an instance of UnitCell but not %s.' % str(type(unit_cell))
    assert min_d < max_d, 'Minimum d-spacing %f must be smaller than maximum d-spacing %f.' % (min_d, max_d)
    assert 0. <= min_d, 'Minimum d-spacing %f must be larger or equal to 0.' % min_d

    # cell_parameters = [5, 4, 3]
    cell_parameters = unit_cell.get_cell_parameters()
    cell_type = unit_cell.space_group

    reflection_list = get_unique_reflections(cell_parameters, cell_type, min_d, max_d)

    """
    print get_unique_reflections(cell_parameters, 'P m m m', 0.5, 5.0)  # primitive
    print get_unique_reflections(cell_parameters, 'I m m m', 0.5, 5.0)  # body center
    print get_unique_reflections(cell_parameters, 'F m m m', 0.5, 5.0)  # face center
    print get_all_reflections(cell_parameters, 'F m m m', 0.5, 5.0)
    """

    return reflection_list


def delete_workspace(workspace):
    """ Delete a workspace in AnalysisService
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
    print '[TRACE] Generate Filter By Log'
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


def get_data_from_workspace(workspace_name, point_data):
    """
    
    :param workspace_name:
    :param point_data:
    :return:
    """
    # TODO/DOC/1st
    
    # Requirements
    # ....
    
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

