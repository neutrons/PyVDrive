# Classes to process sample log and chopping

import os
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


class SampleLogManager(object):
    """ Sample log manager for

    Assumptions:
    1. No 2 NeXus data files have the same name
    2. Run number can be retrieved
    """
    def __init__(self):
        """
        Initialization
        :return:
        """
        # Data structure for log data that is worked on now
        self._currNexusFilename = ''
        self._currRunNumber = None

        self._currLogWorkspace = None
        self._currLogWorkspaceName = ''

        self._currSplitterWorkspace = None
        self._currLogNamesList = list()
        self._currSplittersDict = dict()  # key = sample log name, value = (split ws name, info ws name)

        # Stored session:
        # key = log file name (base name), value = tuple as file name with full path, workspace name, splitter dict
        self._prevSessionDict = dict()
        # Keys map
        self._runNxsNameMap = dict()
        # Some useful value
        self._runStartTimeDict = dict()

        # pure log value setup (independent of NeXus file or workspace)
        self._currentChopTime = None  # option: 'time', 'log', 'manual'
        self._chopSetupDict = dict()

        return

    def checkout_session(self, nxs_file_name, run_number):
        """ Load NeXus file
        This is the only way to set new and save_to_buffer old session
        :param nxs_file_name:
        :return:
        """
        # Check and store
        if os.path.basename(nxs_file_name) == os.path.basename(self._currNexusFilename):
            # same: no op
            print '[INFO] Same NeXus file %s. No operation.' % str(self._currNexusFilename)
            return True, ''
        else:
            # different: store current
            self.store_current_session()

        nxs_base_name = os.path.basename(nxs_file_name)

        # Restore the previous log
        if nxs_base_name in self._prevSessionDict:
            self.restore_session(nxs_base_name)
            return True, ''

        # Start a brand new session
        # Deal with run number
        if run_number is not None:
            assert isinstance(run_number, int)
            self._runNxsNameMap[run_number] = nxs_base_name
            self._currRunNumber = run_number

        base_name = os.path.basename(nxs_file_name)
        if base_name == self._currNexusFilename:
            return True, 'Try to reload sample logs of file %s' % base_name
        else:
            # Start a new session
            self._currNexusFilename = base_name
            self._currRunNumber = run_number

        # Output ws name
        out_ws_name = os.path.basename(nxs_file_name).split('.')[0] + '_Meta'

        # Load sample logs
        status, ret_obj = mantid_helper.load_nexus(data_file_name=nxs_file_name,
                                                   output_ws_name=out_ws_name,
                                                   meta_data_only=True)

        if status is False:
            return False, ret_obj

        self._currLogWorkspace = ret_obj
        self._currLogWorkspaceName = out_ws_name

        # Set up log names list
        try:
            self._currLogNamesList = mantid_helper.get_sample_log_names(self._currLogWorkspace)
            assert isinstance(self._currLogNamesList, list)
        except RuntimeError as err:
            return False, 'Unable to retrieve series log due to %s.' % str(err)

        # Set up run start time
        self._runStartTimeDict[nxs_base_name] = mantid_helper.get_run_start(self._currLogWorkspace, unit='nanoseconds')

        # Set up log list
        # self._logInfoList = mtd.get_sample_log_info(self._currWorkspace)

        return True, ''

    def _find_workspaces_by_run(self, run_number, slicer_tag):
        """

        :param run_number:
        :param slicer_tag:
        :return: 2-tuple as (boolean, ....)
        """
        # Access
        if self._currRunNumber == run_number:
            # current run
            if slicer_tag in self._currSplittersDict:
                split_ws, info_ws = self._currSplittersDict[slicer_tag]
            else:
                return False, 'Unable to find slicer tag %s of run %s' % (slicer_tag, str(run_number))

        elif run_number not in self._runNxsNameMap:
            # unable to find the run store
            return False, 'Unable to find run %s' % str(run_number)

        else:
            # saved session
            file_name = self._runNxsNameMap[run_number]
            if slicer_tag not in self._prevSessionDict[file_name]:
                return False, 'Unable to find slicer %s in run %s / %s' % (slicer_tag,
                                                                           str(run_number),
                                                                           file_name)
            split_ws, info_ws = self._prevSessionDict[file_name][slicer_tag]

        return True, (split_ws, info_ws)

    def chop_data(self, raw_file_name, slicer_type, output_directory):
        """
        chop data and save
        :param raw_file_name:
        :param slicer_type:
        :param output_directory:
        :return:
        """
        # check
        # TODO/NOW - Do it!

        # load data
        # out_ws_name = os.path.basename(raw_file_name).split('.')[0]
        base = os.path.basename(raw_file_name)
        print '[DB]... raw file name: ', raw_file_name, 'base name:', base,
        out_ws_name = os.path.splitext(base)[0]
        print out_ws_name

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

    def clean_workspace(self, run_number, slicer_tag):
        """
        Clean workspace
        :param run_number:
        :param slicer_tag:
        :return:
        """
        status, ret_obj = self._find_workspaces_by_run(run_number, slicer_tag)
        if status is False:
            return False, ret_obj

        slice_ws, info_ws = ret_obj
        mantid_helper.delete_workspace(slice_ws)
        mantid_helper.delete_workspace(info_ws)

        return True, ''

    def generate_events_filter_by_log(self, log_name, min_time, max_time, relative_time,
                                      min_log_value, max_log_value, log_value_interval,
                                      value_change_direction, tag):
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
        :param tag:
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

        if isinstance(min_time, int) is True:
            min_time = float(min_time)
        if isinstance(min_time, float) is True:
            min_time = '%.15E' % min_time
        if isinstance(max_time, int):
            max_time = float(max_time)
        if isinstance(max_time, float):
            max_time = '%.15E' % max_time

        # create output workspace as a standard
        splitter_ws_name = '%s_splitter_%s' % (self._currLogWorkspaceName, log_name)
        info_ws_name = '%s_info_%s' % (self._currLogWorkspaceName, log_name)

        mantid_helper.generate_event_filters_by_log(self._currLogWorkspaceName, splitter_ws_name, info_ws_name,
                                                    min_time, max_time, log_name, min_log_value, max_log_value,
                                                    log_value_interval, value_change_direction)

        # Store
        if tag is None:
            tag = log_name
        self._currSplittersDict[tag] = (splitter_ws_name, info_ws_name)

        return

    def generate_events_filter_by_time(self,min_time, max_time, time_interval, tag,  ws_name=None):
        """
        Create splitters by time
        :param ws_name
        :param min_time:
        :param max_time:
        :param time_interval:
        :param tag:
        :return: 2-tuple (boolean, objects): True/ws name tuple; False/error message
        """
        # defaults to set up workspaces
        if ws_name is None:
            ws_name = self._currLogWorkspaceName

        # Check
        assert isinstance(min_time, float) or isinstance(min_time, None)
        assert isinstance(max_time, float) or isinstance(max_time, None)
        assert isinstance(time_interval, float) or (time_interval is None)
        # assert event_ws, 'Current log workspace cannot be zero'
        if min_time is None and max_time is None and time_interval is None:
            raise RuntimeError('Generate events filter by time must specify at least one of'
                               'min_time, max_time and time_interval')
        assert isinstance(ws_name, str), 'Workspace name %s must be a string but not %s.' % (str(ws_name),
                                                                                             type(ws_name))

        # Generate event filters
        if tag is None:
            tag = '_TIME_'
            splitter_ws_name = '%s_splitter_TIME_' % ws_name
            info_ws_name = '%s_info__TIME_' % ws_name
        else:
            splitter_ws_name = tag
            info_ws_name = tag + '_info'

        status, ret_obj = mantid_helper.generate_event_filters_by_time(ws_name, splitter_ws_name, info_ws_name,
                                                                       min_time, max_time,
                                                                       time_interval, 'Seconds')

        # Get result
        if status is False:
            err_msg = ret_obj
            return status, err_msg

        # Store
        # FIXME/NOW how splitter_ws_name is None!
        self._currSplittersDict[tag] = (splitter_ws_name, info_ws_name)
        print '[BUG-TRACE] Splitter Dict: Tag = %s, Workspace Names = %s' % (tag, str(self._currSplittersDict[tag]))

        return True, ret_obj

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
        if self._currRunNumber != run_number:
            return False, 'It is not supported to use stored run number for generate_events_filter_manual.'
        # Determine tag
        if splitter_tag is None:
            splitter_tag = get_standard_manual_tag(run_number)

        # check
        assert isinstance(splitter_tag, str), 'Splitter tag must be a string but not %s.' \
                                              '' % str(type(splitter_tag))

        # Check split list
        assert isinstance(split_list, list)

        # Generate split workspace
        status, ret_obj = mantid_helper.generate_event_filters_arbitrary(split_list, relative_time=True, tag=splitter_tag)
        if status is False:
            err_msg = ret_obj
            return False, err_msg

        # Store
        split_ws_name, info_ws_name = ret_obj
        self._currSplittersDict['_MANUAL_'] = (split_ws_name, info_ws_name)

        return True, ret_obj

    def get_log_workspace(self, run_number):
        """
        Get the workspace containing sample logs (only!) according to run number
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number > 0

        # return current workspace if run number is current run number
        if run_number == self._currRunNumber:
            return self._currLogWorkspace

        # run number (might) be in stored session
        if run_number not in self._prevSessionDict:
            stored_runs_str = str(self._prevSessionDict.keys())
            raise RuntimeError('Run %d has not been processed. Processed runs are %s.' % (run_number,
                                                                                          stored_runs_str))

        return self._prevSessionDict[run_number]

    def get_sample_log_names(self, with_info=False):
        """
        Get all sample logs' names
        :param with_info: output name with more information i.e., size of sample log
        :return:
        """
        # Check
        if self._currLogWorkspace is None:
            return False, 'Log helper has no data.'

        # Easy return
        if with_info is False:
            return True, self._currLogNamesList[:]

        # Do something fun
        self._currLogNamesList.sort()

        ret_list = list()
        single_value_list = list()

        for log_name in self._currLogNamesList:
            log_size = self._currLogWorkspace.run().getProperty(log_name).size()
            if log_size > 1:
                ret_list.append('%s (%d)' % (log_name, log_size))
            else:
                single_value_list.append('%s (1)' % log_name)
        # END-FOR

        ret_list.extend(single_value_list)

        return True, ret_list

    def get_sample_data(self, run_number, sample_log_name, start_time, stop_time, relative):
        """
        Get sample log's data as 2 vectors for time (unit of second) and log value
        # run_number, log_name, start_time, stop_time, relative
        :exception: RuntimeError for sample log name is not in list
        :param sample_log_name:
        :return: 2-tuple as (numpy.array, numpy.array) for time and log value
        """
        # Check
        if run_number is not None and run_number != self._currRunNumber:
            # FIXME - Deal with this situation
            raise RuntimeError('It has not been considered to retrieve previous run from Mantid.')
        if sample_log_name not in self._currLogNamesList:
            raise RuntimeError('Sample log name %s is not a FloatSeries.' % sample_log_name)

        # Get property
        print '[DB-Trace-Bug Helper 2] run number = ', run_number, 'sample log name = ', sample_log_name,
        print 'start time  = ', start_time

        vec_times, vec_value = mantid_helper.get_sample_log_value(src_workspace=self._currLogWorkspace,
                                                                  sample_log_name=sample_log_name,
                                                                  start_time=start_time,
                                                                  stop_time=stop_time,
                                                                  relative=relative)

        return vec_times, vec_value

    def get_slicer_by_id(self, run_number, slicer_tag, relative_time=True):
        """ Get slicer by slicer ID
        :param run_number:
        :param slicer_tag:
        :return: 2-tuple
        """
        # Get workspaces
        print '[DB Get Slicer] Run number = ', run_number, ', Tag = ', slicer_tag
        status, ret_obj = self._find_workspaces_by_run(run_number, slicer_tag)
        if status is False:
            err_msg = ret_obj
            return False, err_msg

        # Get time segments from file
        split_ws_name = ret_obj[0]
        print '[DB-TEST get_slicer] workspace names for ', slicer_tag, 'are ', ret_obj
        print '[DB-TEST weird] ', self._currSplittersDict
        # FIXME/TODO/NOW : Need to find a way to get run_start in nanosecond
        if relative_time is True:
            nxs_base_name = self._runNxsNameMap[run_number]
            run_start_sec = self._runStartTimeDict[nxs_base_name] * 1.E-9
        else:
            run_start_sec = 0
        print '[DB-BAR] run start tie in second = ', run_start_sec

        segment_list = mantid_helper.get_time_segments_from_splitters(split_ws_name, time_shift=run_start_sec, unit='Seconds')

        return True, segment_list

    def get_slicer_by_log(self, run_number, log_name, nxs_name=None):
        """ Get slicer by log value
        :param run_number:
        :param log_name:
        :param nxs_name:
        :return: 2-tuple as (boolean, object)
        """
        # Check
        assert isinstance(run_number, int)
        assert isinstance(nxs_name, str) or nxs_name is None
        assert isinstance(log_name, str)

        use_current = False

        if run_number is not None and nxs_name is not None:
            # specified both
            raise RuntimeError('It is not allowed to use both run_number and nxs_name')

        elif nxs_name is not None:
            # use NeXus file name
            if nxs_name == os.path.basename(self._currNexusFilename):
                use_current = True
            elif nxs_name not in self._prevSessionDict:
                return False, 'NeXus file name %s has not been processed.' % nxs_name

        elif run_number is not None:
            # use run number
            if run_number in self._prevSessionDict:
                nxs_name = self._runNxsNameMap[run_number]
            elif run_number == self._currRunNumber:
                use_current = True
                nxs_name = os.path.basename(self._currNexusFilename)
            else:
                return False, 'Run %d has not been processed. Current run = %s.' % (run_number,
                                                                                    str(self._currRunNumber))

        else:
            # specified neither
            raise RuntimeError('It is not allowed not to use neither run_number nor nxs_name')

        # Get splitter
        if use_current is True:
            # Current log
            splitter_dict = self._currSplittersDict
        else:
            # Stored
            tup = self._prevSessionDict[nxs_name]
            splitter_dict = tup[3]

        if log_name not in splitter_dict:
            return False, 'There is no processed slicer by log %s for NeXus file %s' % (log_name, nxs_name)

        return True, splitter_dict[log_name]

    def get_slicer_by_time(self, run_number, nxs_name=None):
        """ Get slicer by log value
        :param run_number:
        :param nxs_name:
        :return:
        """
        # Check for using run number or nxs file name
        use_current = False

        if run_number is not None and nxs_name is not None:
            # specified both
            raise RuntimeError('It is not allowed to use both run_number and nxs_name')

        elif nxs_name is not None:
            # use NeXus file name
            if nxs_name == os.path.basename(self._currNexusFilename):
                use_current = True
            elif nxs_name not in self._prevSessionDict:
                return False, 'NeXus file name %s has not been processed.' % nxs_name

        elif run_number is not None:
            # use run number
            if run_number in self._prevSessionDict:
                nxs_name = self._runNxsNameMap[run_number]
            elif run_number == self._currRunNumber:
                use_current = True
                nxs_name = os.path.basename(self._currNexusFilename)
            else:
                return False, 'Run %d has not been processed. Current run = %s.' % (run_number,
                                                                                    str(self._currRunNumber))

        else:
            # specified neither
            raise RuntimeError('It is not allowed not to use neither run_number nor nxs_name')

        # Check for time
        if use_current is True:
            split_dict = self._currSplittersDict
        else:
            split_dict = self._prevSessionDict[nxs_name][3]
        if '_TIME_' not in split_dict:
            return False, 'There is no splitters by time for %s. Candidates are %s.\n' % (
                nxs_name, str(split_dict.keys())
            )

        return True, split_dict['_TIME_']

    def set_current_slicer_time(self):
        """
        Set the current slicer as a time slicer set up previously
        :return:
        """
        assert 'Time' in self._currSplittersDict, 'No time slicer set up.'

        self._currSplitterWorkspace = self._currSplittersDict['Time']

        return

    def set_current_slicer_manual(self):
        """
        Set up current splitter workspace/slicer to a previously setup slicer in manual mode.
        :return:
        """
        assert 'Manual' in self._currSplittersDict, 'No manually set up slicer found in splicers dictionary.'

        self._currSplitterWorkspace = self._currSplittersDict['Manual']

        return

    def set_time_slicer(self, start_time, time_step, stop_time):
        """

        :return:
        """
        self._currentChopTime = 'time'
        self._chopSetupDict['time'] = {'start': start_time, 'step': time_step, 'stop': stop_time}

        return

    def store_current_session(self):
        """ Store current session
        :return:
        """
        nxs_name = self._currNexusFilename
        run_number = self._currRunNumber
        ws_name = self._currLogWorkspaceName
        splitter_dict = self._currSplittersDict.copy()

        dict_key = os.path.basename(nxs_name)
        self._prevSessionDict[dict_key] = [nxs_name, run_number, ws_name, splitter_dict]

        return

    def restore_session(self, nxs_base_name):
        """
        Restore a save_to_buffer session
        :param nxs_base_name: as key
        :return:
        """
        # Check existence
        nxs_base_name = os.path.basename(nxs_base_name)
        if nxs_base_name not in self._prevSessionDict:
            return False, 'File %s does not exist in stored sessions. ' % nxs_base_name

        # Get parameters for recovering
        nxs_name, run_number, ws_name, splitter_dict = self._prevSessionDict[nxs_base_name]

        # Check workspace existence
        if mantid_helper.workspace_does_exist(ws_name) is False:
            return False, 'Log workspace %s does not exist.' % ws_name

        # Retrieve
        self._currNexusFilename = nxs_name
        self._currRunNumber = run_number
        self._currLogWorkspaceName = ws_name
        self._currLogWorkspace = mantid_helper.get_workspace(ws_name)
        self._currSplittersDict = splitter_dict

        return True, ''

    def save_splitter_ws(self, run_number, log_name, out_file_name):
        """ Save splitters workspace to segment file
        """
        # Get slicer
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
                print '[Warning] Line "%s" has wrong type of vlaue for start/stop.' % line
                continue
        # END-IF (#)
    # END-FOR

    return True, (ref_run, run_start, segment_list)


def save_time_segments(file_name, segment_list, ref_run=None, run_start=None):
    """
    Format:
    # Reference Run Number =
    # Run Start Time =
    # Start Stop TargetIndex
    Note that all units of time stamp or difference of time are seconds
    :param file_name:
    :param segment_list:
    :param ref_run:
    :param run_start:
    :return:
    """
    # Check
    assert isinstance(file_name, str)

    # Write to buffer
    wbuf = ''

    # comment lines
    wbuf += '# Reference Run Number = '
    if ref_run is not None:
        assert isinstance(ref_run, int) or isinstance(ref_run, str)
        wbuf += '%s\n' % str(ref_run)
    else:
        wbuf += '\n'

    wbuf += '# Run Start Time = '
    if run_start is not None:
        assert isinstance(run_start, float)
        wbuf += '%.9f'
    wbuf += '\n'

    wbuf += '# Start Time \tStop Time \tTarget\n'

    # splitters
    assert isinstance(segment_list, list)
    for segment in segment_list:
        wbuf += '%.9f \t%.9f \t%d\n' % (segment.start, segment.stop, segment.target)

    # Write
    try:
        ofile = open(file_name, 'w')
        ofile.write(wbuf)
        ofile.close()
    except IOError as e:
        return False, 'Failed to write time segments to file %s due to %s' % (
            file_name, str(e))

    return True, None
