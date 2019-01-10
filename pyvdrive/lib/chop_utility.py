# Classes to process sample log and chopping
import os
import random
import math
import mantid_helper
from mantid.api import ITableWorkspace, MatrixWorkspace
from mantid.dataobjects import SplittersWorkspace
import datatypeutility

FifteenYearsInSecond = 15*356*24*3600
# MAX_CHOPPED_WORKSPACE_IN_MEM = 40
NUMERIC_TOLERANCE = 1.E-10
LARGE_NUMBER_SPLITTER = 10000


class TimeSegment(object):
    """ Time segment for splitters
    Class variables:
    - start time (_data[0]) and stop time (_data[1]) can be either epoch time or relative time.
      and their units are SECONDS
    """
    def __init__(self, start_time, stop_time, target_id):
        """
        Initialization
        Requirements:
         - start time and stop time are float
         - target id is a string or an integer
        :param start_time:
        :param stop_time:
        :param target_id:
        :return:
        """
        assert isinstance(start_time, float)
        assert isinstance(stop_time, float)
        assert isinstance(target_id, int) or isinstance(target_id, str)

        self._data = [0., 0., 0]

        if start_time >= stop_time:
            raise RuntimeError('Unable to create a TimeSegment object '
                               'because start time %f is equal to larger than '
                               'stop time %f' % (start_time, stop_time))

        self._data[0] = start_time
        self._data[1] = stop_time

        if self._data[0] > FifteenYearsInSecond:
            self._isRelative = False
        else:
            self._isRelative = True

        self._data[2] = target_id

        return

    def get_time_segment(self):
        """
        Get the segment of time
        :return:
        """
        return self._data[0], self._data[1]

    def get_target_id(self):
        """
        Get the target ID (very likely the ID to identify the output workspace
        :return:
        """
        return self._data[2]

    @property
    def start(self):
        """
        start time
        :return:
        """
        return self._data[0]

    @property
    def stop(self):
        """ stop time
        :return:
        """
        return self._data[1]


class DataChopper(object):
    """ Sample log manager for

    Assumptions:
    1. No 2 NeXus data files have the same name
    2. Run number can be retrieved
    """
    def __init__(self, run_number, nxs_file_name):
        """
        Initialization
        :return:
        """
        # Check input's validity
        datatypeutility.check_int_variable('Run number', run_number, (0, None))
        datatypeutility.check_file_name(nxs_file_name, check_exist=True, check_writable=False,
                                        is_dir=False, note='NeXus file name')

        # Data structure for log data that is worked on now
        self._myNeXusFileName = nxs_file_name
        self._myRunNumber = run_number

        # workspace name (might be sample log only)
        self._mtdWorkspaceName = None
        self._logNameList = None
        self._runStartTime = None

        # splitters
        self._currSplitterWorkspace = None
        self._currInfoTableWorkspace = None
        self._chopSetupDict = dict()  # key: user-specified tag   value: dictionary including everything!

        # initialization operation
        self.load_data_file()

        return

    # TEST - Implemented in #65
    def delete_splitter_workspace(self, slicer_tag):
        """
        delete a splitter workspace by its tag
        :param slicer_tag:
        :return:
        """
        # get splitters workspaces
        try:
            slicer_ws_name, info_ws_name = self.get_split_workspace(slicer_tag)
        except RuntimeError as run_err:
            return False, 'Unable to delete slicer with tag {0} of run {1} due to {2}.' \
                          ''.format(slicer_tag, self._myRunNumber, run_err)

        # delete workspaces
        mantid_helper.delete_workspace(slicer_ws_name)
        mantid_helper.delete_workspace(info_ws_name)

        return True, ''

    def generate_events_filter_manual(self, run_number, split_list, relative_time, splitter_tag):
        """ Generate a split workspace with arbitrary input time
        :param run_number:
        :param split_list:
        :param relative_time:
        :param splitter_tag: 2-tuple : split workspace, information workspace OR None
                boolean, ???? (...)/string (error message)
        :return:
        """
        # Check
        if self._myRunNumber != run_number:
            return False, 'It is not supported to use stored run number for generate_events_filter_manual.'
        # Determine tag
        if splitter_tag is None:
            splitter_tag = get_standard_manual_tag(run_number)

        # check
        assert isinstance(splitter_tag, str), 'Splitter tag must be a string but not %s.' \
                                              '' % str(type(splitter_tag))

        # Check split list
        assert isinstance(split_list, list), 'Splitters {0} must be given by list but not {1}.' \
                                             ''.format(split_list, type(split_list))

        # Generate split workspace
        status, ret_obj = mantid_helper.generate_event_filters_arbitrary(self._mtdWorkspaceName,
                                                                         split_list,
                                                                         relative_time=relative_time,
                                                                         tag=splitter_tag,
                                                                         auto_target=True)
        if status:
            split_ws_name, info_ws_name = ret_obj
        else:
            err_msg = ret_obj
            return False, err_msg

        # Store
        self._chopSetupDict[splitter_tag] = {'splitter': split_ws_name,
                                             'info': info_ws_name}

        return True, splitter_tag

    def get_experiment_information(self):
        """
        get experiment information in a well-formed string
        :return:
        """
        # Check
        if self._mtdWorkspaceName is None:
            raise RuntimeError('DataChopper has no data loaded to Mantid workspace.')

        info_str = 'Run {0}:\t'.format(self._myRunNumber)

        # get proton charge
        proton_charge_property = mantid_helper.get_sample_log_tsp(self._mtdWorkspaceName, 'proton_charge')
        pc_times = proton_charge_property.times

        info_str += 'run start: {0}; run stop:  {1}' \
                    ''.format(pc_times[0], pc_times[-1])

        return info_str

    def get_sample_log_names(self, with_info=False):
        """
        Get all sample logs' names
        :exception: run time error for mantid workspace does not exist.
        :param with_info: output name with more information i.e., size of sample log
        :return: List of sample logs
        """
        # Check
        if self._mtdWorkspaceName is None:
            raise RuntimeError('DataChopper has no data loaded to Mantid workspace.')

        # Easy return
        if not with_info:
            return self._logNameList[:]

        return mantid_helper.get_sample_log_names(self._mtdWorkspaceName, smart=True)

    def get_sample_data(self, sample_log_name, start_time, stop_time, relative):
        """
        Get sample log's data as 2 vectors for time (unit of second) and log value
        :exception: RuntimeError for sample log name is not in list
        :param sample_log_name:
        :param start_time:
        :param stop_time:
        :param relative:
        :return: 2-tuple as (numpy.array, numpy.array) for time and log value
        """
        # Check
        assert isinstance(sample_log_name, str), 'Sample log name must be a string but not a %s.' \
                                                 '' % type(sample_log_name)
        if sample_log_name not in self._logNameList:
            raise RuntimeError('Sample log name %s is not a FloatSeries.' % sample_log_name)

        # Get property
        vec_times, vec_value = mantid_helper.get_sample_log_value(src_workspace=self._mtdWorkspaceName,
                                                                  sample_log_name=sample_log_name,
                                                                  start_time=start_time,
                                                                  stop_time=stop_time,
                                                                  relative=relative)

        return vec_times, vec_value

    def get_split_workspace(self, slice_id):
        """
        Get the workspace for splitting with slice ID
        :param slice_id:
        :return: splitters workspace and splitter information table workspace
        """
        # check inputs
        assert isinstance(slice_id, str), 'Slicer ID %s must be a string but not of type %s.' % (str(slice_id),
                                                                                                 type(slice_id))

        # whether the slicer ID is in the set up dictionary?
        if slice_id not in self._chopSetupDict:
            raise RuntimeError('Splitters dictionary does not have ID %s.  Supported IDs are %s.'
                               '' % (str(slice_id), str(self._chopSetupDict.keys())))

        split_ws_name = self._chopSetupDict[slice_id]['splitter']
        info_table_name = self._chopSetupDict[slice_id]['info']

        return split_ws_name, info_table_name

    def get_slicer_by_id(self, slicer_tag, relative_time=True):
        """ Get slicer by slicer ID
        :param slicer_tag:
        :param relative_time:
        :return: 2-tuple
        """
        # check
        assert isinstance(slicer_tag, str), 'Slicer tag %s must be a string but not a %s.' \
                                            '' % (str(slicer_tag), type(slicer_tag))
        try:
            chopper = self._chopSetupDict[slicer_tag]
        except KeyError:
            return False, 'Slice tag %s does not exist for run %d. Existing tags include %s.' \
                          '' % (slicer_tag, self._myRunNumber, str(self._chopSetupDict.keys()))

        # relative time?
        if relative_time:
            run_start_time = mantid_helper.get_run_start(self._mtdWorkspaceName, time_unit='second')
        else:
            run_start_time = None
        print '[INFO] Run start time = ', run_start_time, 'of type ', type(run_start_time)

        # get workspace
        slice_ws_name = chopper['splitter']
        try:
            vec_times, vec_ws_index = mantid_helper.convert_splitters_workspace_to_vectors(
                split_ws=slice_ws_name, run_start_time=run_start_time)
        except AssertionError as ass_err:
            return False, 'Unable to convert splitters workspace %s to vectors due to %s.' \
                          '' % (slice_ws_name, str(ass_err))

        return True, (vec_times, vec_ws_index)

    def load_data_file(self):
        """ Load NeXus file
        :return:
        """
        # use base name for output workspace
        base_name = os.path.basename(self._myNeXusFileName)
        out_ws_name = base_name.split('.')[0] + '_MetaData'

        # Load sample logs
        status, ret_obj = mantid_helper.load_nexus(data_file_name=self._myNeXusFileName,
                                                   output_ws_name=out_ws_name,
                                                   meta_data_only=True)

        if status is False:
            err_msg = str(ret_obj)
            raise RuntimeError(err_msg)
        else:
            self._mtdWorkspaceName = out_ws_name

        # Set up log names list
        try:
            self._logNameList = mantid_helper.get_sample_log_names(self._mtdWorkspaceName)
            assert isinstance(self._logNameList, list)
        except RuntimeError as err:
            return False, 'Unable to retrieve series log due to %s.' % str(err)

        # Set up run start time
        self._runStartTime = mantid_helper.get_run_start(self._mtdWorkspaceName, time_unit='nanosecond')

        return out_ws_name

    def set_log_value_slicer(self, log_name, log_value_step, start_time=None, stop_time=None,
                             min_log_value=None, max_log_value=None, direction='Both'):
        """
        set up a slicer by log value
        :param log_name:
        :param start_time:
        :param stop_time:
        :param min_log_value:
        :param max_log_value:
        :param log_value_step:
        :param direction: log value change direction
        :return: 2-tuple. (1) boolean (2) string: key to the slicer
        """
        # check validity of inputs
        assert isinstance(log_name, str), 'Log name must be a string.'
        assert isinstance(log_value_step, float) or log_value_step is None,\
            'Log value step must be float or None but not %s.' % type(log_value_step)
        assert isinstance(start_time, float) or start_time is None, 'Start time must be None or float.'
        assert isinstance(stop_time, float) or stop_time is None, 'Stop time must be None or float'
        assert isinstance(min_log_value, float) or min_log_value is None, 'Min log value must be None or float'
        assert isinstance(max_log_value, float) or max_log_value is None, 'Max log value must be None or float'

        assert isinstance(direction, str), 'Direction must be a string but not %s.' % type(direction)
        if direction not in ['Both', 'Increase', 'Decrease']:
            return False, 'Value change direction %s is not supported.' % direction

        # generate filter
        tag = 'Slicer_%06d_%s' % (self._myRunNumber, log_name)

        # set default
        if isinstance(start_time, float) is True:
            min_time = '%.15E' % start_time
        else:
            min_time = None
        if isinstance(stop_time, float):
            max_time = '%.15E' % stop_time
        else:
            max_time = None

        # create output workspace as a standard
        splitter_ws_name = tag
        info_ws_name = '%s_Info' % tag

        mantid_helper.generate_event_filters_by_log(self._mtdWorkspaceName, splitter_ws_name, info_ws_name,
                                                    min_time, max_time, log_name, min_log_value, max_log_value,
                                                    log_value_step, direction)

        # add the values to the dictionary for later reference.
        self._chopSetupDict[tag] = {'start': start_time,
                                    'stop': stop_time,
                                    'step': log_value_step,
                                    'min': min_log_value,
                                    'max': max_log_value,
                                    'direction': direction,
                                    'splitter': splitter_ws_name,
                                    'info': info_ws_name}

        # user tag as slicer
        slicer_key = tag

        return True, slicer_key

    def set_overlap_time_slicer(self, start_time, stop_time, time_interval, overlap_time_interval,
                                splitter_tag=None):
        """
        set slicers for constant time period with overlapping
        will be
        t0, t0 + dbin
        t0 + dt, t0 + dbin + dt
        ... ...
        :param start_time:
        :param stop_time:
        :param time_interval:
        :param overlap_time_interval:
        :return:
        """
        # Check inputs
        if start_time is not None:
            datatypeutility.check_float_variable('Event filters starting time', start_time, (0., None))
        if stop_time is not None:
            datatypeutility.check_float_variable('Event filtering stopping time', stop_time, (1.E-10, None))
        if start_time is not None and stop_time is not None and start_time >= stop_time:
            raise RuntimeError('User specified event filters starting time {} is after stopping time {}'
                               ''.format(start_time, stop_time))

        datatypeutility.check_float_variable('Time interval', time_interval, (0., None))
        datatypeutility.check_float_variable('Overlap time interval', overlap_time_interval, (0., None))
        if time_interval <= overlap_time_interval:
            raise RuntimeError('Time step/interval {} cannot be equal or less than overlapped time period '
                               '{}'.format(time_interval, overlap_time_interval))

        # create time bins
        if start_time is None:
            start_time = 0
        if stop_time is None:
            stop_time = mantid_helper.get_run_stop(self._mtdWorkspaceName, 'second', is_relative=True)
        print ('[DB...BAT] Run stop = {}'.format(stop_time))

        split_list = list()
        split_t0 = start_time
        split_tf = -1
        while split_tf < stop_time:
            # get split stop time
            split_tf = split_t0 + time_interval
            if split_tf > stop_time:
                split_tf = stop_time + 1.E-10
            # add to list
            split_list.append((split_t0, split_tf))
            # advance the start time
            split_t0 += overlap_time_interval
        # END-WHILE

        # Determine tag
        if splitter_tag is None:
            splitter_tag = get_standard_manual_tag(self._mtdWorkspaceName)

        # Generate split workspaces
        splitter_tag_list = list()
        for i_split, split_tup in enumerate(split_list):
            splitter_tag_i = splitter_tag + '_{:05}'.format(i_split)
            splitter_info_i = splitter_tag_i + '_info'
            status, message = mantid_helper.generate_event_filters_by_time(self._mtdWorkspaceName,
                                                                             splitter_tag_i,
                                                                             splitter_info_i,
                                                                             split_tup[0],
                                                                             split_tup[1],
                                                                             delta_time=None,
                                                                             time_unit='second')

            if not status:
                return False, message

            # good
            splitter_tag_list.append(splitter_tag_i)
            self._chopSetupDict[splitter_tag_i] = {'splitter': splitter_tag_i,
                                                 'info': splitter_info_i}
        # END-FOR

        return True, splitter_tag_list

    def set_time_slicer(self, start_time, time_step, stop_time):
        """
        :return:
        """
        # self._mtdWorkspaceName

        # Check inputs
        if start_time is not None:
            datatypeutility.check_float_variable('Event filters starting time', start_time, (0., None))
        if stop_time is not None:
            datatypeutility.check_float_variable('Event filtering stopping time', stop_time, (1.E-10, None))
        if start_time is not None and stop_time is not None and start_time >= stop_time:
            raise RuntimeError('User specified event filters starting time {} is after stopping time {}'
                               ''.format(start_time, stop_time))
        if start_time is None and stop_time is None and time_step is None:
            raise RuntimeError('It is not allowed to give all 3 Nones. Generate events filter by time '
                               'must specify at least one of min_time, max_time and time_interval')

        # define tag
        tag = 'TimeSlicer_%06d' % self._myRunNumber

        # define output workspace
        splitter_ws_name = tag
        info_ws_name = tag + '_Info'

        assert self._mtdWorkspaceName is not None, 'Mantid workspace has not been loaded yet.'
        status, message = mantid_helper.generate_event_filters_by_time(self._mtdWorkspaceName,
                                                                       splitter_ws_name, info_ws_name,
                                                                       start_time, stop_time,
                                                                       time_step, 'Seconds')
        # return with error message
        if status is False:
            return status, message

        # set up splitter record
        self._chopSetupDict[tag] = {'start': start_time, 'step': time_step, 'stop': stop_time,
                                    'splitter': splitter_ws_name, 'info': info_ws_name}

        # user tag to serve as slicer key
        slicer_key = tag

        return True, slicer_key


# TODO/NEXT - If parse_time_segmenets works for data slicer file too, then remove parse_data_slicer_file()
def parse_data_slicer_file(file_name):
    """
    parse data slicer file
    :param file_name:
    :return:
    """
    slicer_file = open(file_name, 'r')
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

    return slicer_list


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


def get_standard_manual_tag(run_number):
    """
    if the tag for a manual splicer is not given, then it will be named under a routine
    :param run_number:
    :return:
    """
    random_index = random.randint(1, 1000)
    return 'manual_slicer_{0}_{1}'.format(run_number, random_index)


def get_number_chopped_ws(split_ws_name):
    """
    get the number of expected chopped workspaces from splitters workspace and also find out whether the
    slicers' time are relative time or
    :param split_ws_name:
    :return:
    """
    split_ws = mantid_helper.retrieve_workspace(split_ws_name)

    if isinstance(split_ws, ITableWorkspace):
        # table workspace
        num_rows = split_ws.rowCount()
        target_set = set()
        for i_row in range(num_rows):
            target = split_ws.cell(i_row, 2)
            target_set.add(target)

        run_start_time = split_ws.cell(0, 0)
    else:
        # matrix workspace case
        target_set = set()
        for y in split_ws.readY(0):
            int_y = int(y + 0.1)
            target_set.add(int_y)

        run_start_time = split_ws.readX(0)[0]
    # END-FOR

    # judge whether the run start time is relative or epoch.  even the relative time in second cannot be too large
    if run_start_time > 3600 * 24 * 356:
        epoch_time = True
    else:
        epoch_time = False

    return len(target_set), epoch_time


def is_overlap_splitter(split_ws_name):
    """
            check whether a workspace contains overlapped splits
            :return:
            """
    # get the workspace
    if mantid_helper.workspace_does_exist(split_ws_name):
        split_ws = mantid_helper.retrieve_workspace(split_ws_name)
    else:
        raise RuntimeError('Splitters workspace {0} cannot be found in ADS.'.format(split_ws_name))

    # return True if the number of splitters is too large, i.e., exceeds 10,000
    split_number = get_splitters_number(split_ws)
    if split_number >= LARGE_NUMBER_SPLITTER:
        print '[Notice] Number of splitters = {0}.  It is too large to check. Return True instead' \
              ''.format(split_number)
        return True

    vec_splitter = get_splitters(split_ws)
    for i_splitter in range(split_number - 1):
        stop_time_i = vec_splitter[i_splitter][1]
        start_time_ip1 = vec_splitter[i_splitter + 1][1]
        if stop_time_i > start_time_ip1 + NUMERIC_TOLERANCE:
            return False

    return True


def get_splitters_number(split_ws):
    """
    get number of splitters in a splitters workspace
    :param split_ws:
    :return:
    """
    if split_ws.__class__.__name__.count('Splitter') > 0:
        # splitters workspace
        number_splitters = split_ws.rowCount()
    elif split_ws.__class__.__name__.count('Table') > 0:
        # table workspace for splitters
        number_splitters = split_ws.rowCount()
    else:
        # matrix workspace
        number_splitters = len(split_ws.readX(0))-1

    return number_splitters


def get_splitters(split_ws):
    """
    get the splitters for a splitters workspace
    :param split_ws:
    :return: a list of splitters in the same order of splitters workspace
    """
    splitter_vec = list()
    splitter_type = split_ws.__class__.__name__

    if splitter_type.count('Splitter') > 0 or splitter_type.count('Table') > 0:
        # table-styled workspace
        for row_index in range(split_ws.rowCount()):
            start_time = split_ws.cell(row_index, 0)
            stop_time = split_ws.cell(row_index, 1)
            target = split_ws.cell(row_index, 2)
            splitter_vec.append((start_time, stop_time, target))
        # END-FOR

    else:
        # matrix workspace
        vec_x = split_ws.readX(0)
        vec_y = split_ws.readY(0)
        for index in range(len(vec_x)-1):
            start_time = vec_x[index]
            stop_time = vec_x[index]
            target = vec_y[index]
            splitter_vec.append((start_time, stop_time, target))

    # END-IF-ELSE

    return splitter_vec


def save_slicers(time_segment_list, file_name):
    """
    Save a list of 3-tuple or 2-tuple time segments to an ASCII file
    Time segments may be disordered.
    Format:
        # Reference Run Number =
        # Run Start Time =
        # Start Stop TargetIndex
        Note that all units of time stamp or difference of time are seconds
    :param time_segment_list:
    :param file_name:
    :return:
    """
    # Check
    assert isinstance(file_name, str), 'File name %s must be a string but not of type %s.' \
                                       '' % (str(file_name), type(file_name))
    assert isinstance(time_segment_list, list), 'Time segment list must be a list but not of type %s.' \
                                                '' % type(time_segment_list)

    # sort by segments
    time_segment_list.sort()

    # start to write to file buffer
    file_buffer = '# Start Time \tStop Time \tTarget\n'

    # splitters
    for segment in time_segment_list:
        file_buffer += '%.9f \t%.9f \t%s\n' % (segment[0], segment[1], str(segment[2]))

    # write file from buffer
    try:
        set_file = open(file_name, 'w')
        set_file.write(file_buffer)
        set_file.close()
    except IOError as e:
        return False, 'Failed to write time segments to file %s due to %s' % (
            file_name, str(e))

    return True, None
