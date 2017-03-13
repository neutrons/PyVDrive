# Classes to process sample log and chopping

import os
import random
import mantid_helper


FifteenYearsInSecond = 15*356*24*3600


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
        assert isinstance(run_number, int), 'Run number must be integer'
        assert isinstance(nxs_file_name, str), 'NeXus file name must be integer'

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
        self._runStartTime = mantid_helper.get_run_start(self._mtdWorkspaceName, time_unit='nanoseconds')

        return

    def chop_data(self, raw_file_name, slicer_type, output_directory):
        """
        chop data and save to GSAS file
        :param raw_file_name:
        :param slicer_type:
        :param output_directory:
        :return:
        """
        raise NotImplementedError('chop_data() requires refactor!')
        # check
        assert isinstance(raw_file_name, str), 'Raw file name %s must be a string but not %s.' % (str(raw_file_name),
                                                                                                  type(raw_file_name))
        assert isinstance(slicer_type, str), 'Slicer type %s must be a string but not %s.' % (str(slicer_type),
                                                                                              type(slicer_type))
        assert isinstance(output_directory, str), 'Output directory must be string.' % output_directory

        # load data
        # out_ws_name = os.path.basename(raw_file_name).split('.')[0]
        base = os.path.basename(raw_file_name)
        out_ws_name = os.path.splitext(base)[0]

        mantid_helper.load_nexus(data_file_name=raw_file_name,
                                 output_ws_name=out_ws_name,
                                 meta_data_only=False)

        # set up slicers
        if slicer_type == 'time':
            setup_dict = self._chopSetupDict['time']
            # {'start': start_time, 'step': time_step, 'stop': stop_time}

            # TODO/NOW - Need to find out a better name!
            tag = 'time123'

            # 2-tuple (boolean, objects): True/ws name tuple; False/error message
            status, ret_obj = self.generate_events_filter_by_time(min_time=setup_dict['start'],
                                                                  max_time=setup_dict['stop'],
                                                                  time_interval=setup_dict['step'],
                                                                  tag=tag,
                                                                  ws_name=out_ws_name)
            print '[DB...BAT] Returned from slicing setup:', status, ret_obj
            if status:
                chop_splitter_name, chop_info_name = ret_obj
            else:
                raise RuntimeError(ret_obj)

        elif slicer_type == 'log':
            raise NotImplementedError('ASAP')

        else:
            # manual
            raise NotImplementedError('ASAP')

        # chop data
        base_name = os.path.join(output_directory, tag)
        # return: 2-tuple (boolean, object): True/(list of ws names, list of ws objects); False/error message
        status, ret_obj = mantid_helper.split_event_data(raw_event_ws_name=out_ws_name,
                                                         splitter_ws_name=chop_splitter_name,
                                                         info_ws_name=chop_info_name,
                                                         split_ws_base_name=base_name,
                                                         tof_correction=False)
        if status:
            ws_name_list = ret_obj[0]
        else:
            raise RuntimeError(ret_obj)

        # save
        print '[DB...BAT] Wrokspaces to save: ', ws_name_list
        for ws_name in ws_name_list:
            mantid_helper.save_event_workspace(ws_name, out_file_name)

        return

    def delete_slicer_by_id(self, slicer_tag):
        """
        Clean workspace
        :param run_number:
        :param slicer_tag:
        :return:
        """
        # TODO/ISSUE/51 - make it work!
        status, ret_obj = self._find_workspaces_by_run(run_number, slicer_tag)
        if status is False:
            return False, ret_obj

        slice_ws, info_ws = ret_obj
        mantid_helper.delete_workspace(slice_ws)
        mantid_helper.delete_workspace(info_ws)

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
                                                                         relative_time=True,
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
        get experiment information
        :return:
        """
        # Check
        if self._mtdWorkspaceName is None:
            raise RuntimeError('DataChopper has no data loaded to Mantid workspace.')

        info_str = 'Run {0}:\t'.format(self._myRunNumber)  #, self._mtdWorkspaceName)

        # get proton charge
        proton_charge_property = mantid_helper.get_sample_log_tsp(self._mtdWorkspaceName, 'proton_charge')
        pc_times = proton_charge_property.times

        info_str += 'run start: {0} ({1:.9f});\n\t\trun stop:  {2} ({3:.9f})' \
                    ''.format(pc_times[0], 1.E-9*pc_times[0].totalNanoseconds(),
                              pc_times[-1], 1.E-9*pc_times[-1].totalNanoseconds())

        return info_str

    def get_log_workspace(self, run_number):
        """
        Get the workspace containing sample logs (only!) according to run number
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number > 0

        # return current workspace if run number is current run number
        if run_number == self._myRunNumber:
            return self._mtdWorkspaceName

        # run number (might) be in stored session
        if run_number not in self._prevSessionDict:
            stored_runs_str = str(self._prevSessionDict.keys())
            raise RuntimeError('Run %d has not been processed. Processed runs are %s.' % (run_number,
                                                                                          stored_runs_str))

        return self._prevSessionDict[run_number]

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

        # return
        #
        # # Do something fun
        # self._logNameList.sort()
        #
        # ret_list = list()
        # single_value_list = list()
        #
        # for log_name in self._logNameList:
        #     log_size = self._mtdWorkspaceName.run().getProperty(log_name).size()
        #     if log_size > 1:
        #         ret_list.append('%s (%d)' % (log_name, log_size))
        #     else:
        #         single_value_list.append('%s (1)' % log_name)
        # # END-FOR
        #
        # ret_list.extend(single_value_list)
        #
        # return ret_list

    def get_sample_data(self, sample_log_name, start_time, stop_time, relative):
        """
        Get sample log's data as 2 vectors for time (unit of second) and log value
        :exception: RuntimeError for sample log name is not in list
        :param run_number:
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

    def set_current_slicer_time(self):
        """
        Set the current slicer as a time slicer set up previously
        :return:
        """
        time_slicer_tag = generate_tag('time', self._myRunNumber)
        if time_slicer_tag in self._chopSetupDict:
            self._currentSlicerTag = time_slicer_tag

        return

    def set_current_slicer_manual(self):
        """
        Set up current splitter workspace/slicer to a previously setup slicer in manual mode.
        :return:
        """
        manual_slicer_tag = generate_tag('manual', self._myRunNumber)
        if manual_slicer_tag in self._chopSetupDict:
            self._currentSlicerTag = manual_slicer_tag

        return

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

    def set_time_slicer(self, start_time, time_step, stop_time):
        """
        :return:
        """
        # self._mtdWorkspaceName

        # Check inputs
        assert isinstance(start_time, float) or start_time is None
        assert isinstance(stop_time, float) or stop_time is None
        assert isinstance(time_step, float) or time_step is None

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

    def save_splitter_ws(self, run_number, log_name, out_file_name):
        """ Save splitters workspace to segment file
        """
        # Get slicer
        slice_tag = get_standard_log_tag(run_number, log_name)

        status, ret_obj = self.get_slicer_by_log(run_number, log_name)
        if status is False:
            err_msg = ret_obj
            return False, 'Unable to locate slicer for run %s by log %s due to %s.' % (
                str(run_number), log_name, err_msg)

        # Title
        wbuf = ''

        # Get splitters workspace

        splitter_ws_name = ret_obj[0]
        splitter_ws = mantid_helper.retrieve_workspace(splitter_ws_name)
        if splitter_ws is None:
            raise NotImplementedError('It is not likely not to locate the splitters workspace.')
        log_ws = self.get_log_workspace(run_number)
        try:
            run_start = log_ws.run().getProperty('proton_charge').times[0]
            run_start_ns = run_start.totalNanoseconds()
        except RuntimeError:
            run_start = '1990-01-01T00:00:00.0000000000'
            run_start_ns = 0
        num_rows = splitter_ws.rowCount()
        wbuf += '# Reference Run Number = %s\n' % run_number
        wbuf += '# Run Start Time = %.9f\n' % (run_start_ns * 1.E-9)
        wbuf += '# Verbose run start = %s\n' % str(run_start)
        wbuf += '# Start Time \tStop Time \tTarget\n'

        for i_row in xrange(num_rows):
            start_time = (splitter_ws.cell(i_row, 0) - run_start_ns) * 1.E-9
            stop_time = (splitter_ws.cell(i_row, 1) - run_start_ns) * 1.E-9
            target = splitter_ws.cell(i_row, 2)
            wbuf += '%.9f \t%.9f \t%d\n' % (start_time, stop_time, target)
        # END-FOR (i)

        # Write
        try:
            ofile = open(out_file_name, 'w')
            ofile.write(wbuf)
            ofile.close()
        except IOError as e:
            return False, 'Failed to write time segments to file %s due to %s' % (
                out_file_name, str(e))

        return True, None

    def save_time_segments(self, file_name, time_segment_list):
        """
        Save a list of 3-tuple or 2-tuple time segments to an ASCII file
        Time segments may be disordered.
        Format:
        # Reference Run Number =
        # Run Start Time =
        # Start Stop TargetIndex
        Note that all units of time stamp or difference of time are seconds

        :param file_name:
        :param time_segment_list:
        :return:
        """
        # Check
        assert isinstance(file_name, str), 'File name %s must be a string but not of type %s.' \
                                           '' % (str(file_name), type(file_name))
        assert isinstance(time_segment_list, list), 'Time segment list must be a list but not of type %s.' \
                                                    '' % type(time_segment_list)

        # get run start time
        run_start = mantid_helper.get_run_start(self._mtdWorkspaceName, time_unit='second')

        # convert the time segments in list of 3-tuples to a list of TimeSegment objects
        segment_list = list()
        i_target = 1
        for time_seg in time_segment_list:
            # get the target workspace index
            if len(time_seg) < 3:
                # in case that the target workspace index is not given (2-tuple). use next target-index
                tmp_target = '%d' % i_target
                i_target += 1
            else:
                # use the 3rd element in the tuple as target workspace index
                tmp_target = '%s' % str(time_seg[2])
            # create a TimeSegment object
            tmp_seg = TimeSegment(time_seg[0], time_seg[1], i_target)
            segment_list.append(tmp_seg)
        # END-IF

        # sort by segments
        segment_list.sort()

        # start to write to file buffer
        file_buffer = ''

        # comment lines
        file_buffer += '# Reference Run Number = %d' % self._myRunNumber

        file_buffer += '# Run Start Time = '
        if run_start is not None:
            assert isinstance(run_start, float)
            file_buffer += '%.9f'
        file_buffer += '\n'

        file_buffer += '# Start Time \tStop Time \tTarget\n'

        # splitters
        assert isinstance(segment_list, list)
        for segment in segment_list:
            file_buffer += '%.9f \t%.9f \t%d\n' % (segment.start, segment.stop, segment.target)

        # write file from buffer
        try:
            set_file = open(file_name, 'w')
            set_file.write(file_buffer)
            set_file.close()
        except IOError as e:
            return False, 'Failed to write time segments to file %s due to %s' % (
                file_name, str(e))

        return True, None


def parse_time_segments(file_name):
    """
    Parse the standard time segments file serving for event slicers
    :param file_name:
    :return: 2-tuple as (boolean, object): (True, (reference run, start time, segment list))
            (False, error message)
    """
    # Check
    assert isinstance(file_name, str)

    # Read file
    try:
        in_file = open(file_name, 'r')
        raw_lines = in_file.readlines()
        in_file.close()
    except IOError as e:
        return False, 'Failed to read time segment file %s due to %s.' % (
            file_name, str(e)
        )

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
                print '[Warning] Line "%s" has wrong type of value for start/stop.' % line
                continue
        # END-IF (#)
    # END-FOR

    return True, (ref_run, run_start, segment_list)


def get_standard_manual_tag(run_number):
    """
    if the tag for a manual splicer is not given, then it will be named under a routine
    :param run_number:
    :return:
    """
    random_index = random.randint(1, 1000)
    return 'manual_slicer_{0}_{1}'.format(run_number, random_index)
