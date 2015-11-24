import os

import mantid_helper as mtd


FifteenYearsInSecond = 15*356*24*3600


class TimeSegment(object):
    """ Time segment for splitters
    """
    def __init__(self, start_time, stop_time, target_id):
        """

        :param start_time:
        :param stop_time:
        :param target_id:
        :return:
        """
        assert isinstance(start_time, float)
        assert isinstance(stop_time, float)
        assert isinstance(target_id, int) or isinstance(target_id, str)

        if start_time >= stop_time:
            raise RuntimeError('Unable to create a TimeSegment object '
                               'because start time %f is equal to larger than '
                               'stop time %f' % (start_time, stop_time))

        self.start = start_time
        self.stop = stop_time

        if self.start > FifteenYearsInSecond:
            self._isRelative = False
        else:
            self._isRelative = True

        self.target = target_id

        return

    def get_time_segment(self):
        """

        :return:
        """
        return self.start, self.start

    def get_target_id(self):
        """

        :return:
        """
        return self.target


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
        self._currWorkspace = None
        self._currWorkspaceName = ''
        self._currLogNamesList = list()
        self._currSplittersDict = dict()  # key = sample log name, value = (split ws name, info ws name)

        # Stored session:
        # key = log file name (base name), value = tuple as file name with full path, workspace name, splitter dict
        self._prevSessionDict = dict()
        # Keys map
        self._runNxsNameMap = dict()

        return

    def checkout_session(self, nxs_file_name, run_number):
        """ Load NeXus file
        This is the only way to set new and save old session
        :param nxs_file_name:
        :return:
        """
        print '[DB-BAF] Checkout session of file %s / run %s.' % (str(nxs_file_name),
                                                                  str(run_number))
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
            print '[DB-BAR] Sample Log Helper\'s currRunNumber is set to %s' % str(self._currRunNumber)
        else:
            print '[DB] Input run number is None for NeXus file %s' % nxs_base_name

        base_name = os.path.basename(nxs_file_name)
        if base_name == self._currNexusFilename:
            return True, 'Try to reload sample logs of file %s' % base_name
        else:
            # Start a new session
            self._currNexusFilename = base_name
            self._currRunNumber = run_number
            print '[DB-BAR] Start a new session: %s and %s' % (self._currNexusFilename,
                                                               str(self._currRunNumber))

        # Output ws name
        out_ws_name = os.path.basename(nxs_file_name).split('.')[0] + '_Meta'

        # Load sample logs
        status, ret_obj = mtd.load_nexus(data_file_name=nxs_file_name,
                                         output_ws_name=out_ws_name,
                                         meta_data_only=True)

        if status is False:
            return False, ret_obj

        self._currWorkspace = ret_obj
        self._currWorkspaceName = out_ws_name

        # Set up log names list
        try:
            self._currLogNamesList = mtd.get_sample_log_names(self._currWorkspace)
            assert isinstance(self._currLogNamesList, list)
        except RuntimeError as err:
            return False, 'Unable to retrieve series log due to %s.' % str(err)

        # Set up log list
        self._logInfoList = mtd.get_sample_log_info(self._currWorkspace)

        return True, ''

    def _find_workspaces_by_run(self, run_number, slicer_tag):
        """

        :param run_number:
        :param slicer_tag:
        :return:
        """
        slice_ws = None
        info_ws = None

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
            slice_ws, info_ws = self._prevSessionDict[file_name][slicer_tag]

        return True, (slice_ws, info_ws)

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
        mtd.delete_workspace(slice_ws)
        mtd.delete_workspace(info_ws)

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
        splitter_ws_name = '%s_splitter_%s' % (self._currWorkspaceName, log_name)
        info_ws_name = '%s_info_%s' % (self._currWorkspaceName, log_name)

        mtd.generate_event_filters_by_log(self._currWorkspaceName, splitter_ws_name, info_ws_name,
                                          min_time, max_time, log_name, min_log_value, max_log_value,
                                          log_value_interval, value_change_direction)

        # Store
        if tag is None:
            tag = log_name
        self._currSplittersDict[tag] = (splitter_ws_name, info_ws_name)

        return

    def generate_events_filter_by_time(self, min_time, max_time, time_interval, tag):
        """
        Create splitters by time
        :param min_time:
        :param max_time:
        :param time_interval:
        :return: 2-tuple (boolean, objects): True/ws name tuple; False/error message
        """
        # Check
        assert isinstance(min_time, float) or isinstance(min_time, None)
        assert isinstance(max_time, float) or isinstance(max_time, None)
        assert isinstance(time_interval, float) or (time_interval is None)
        assert self._currWorkspace
        if min_time is None and max_time is None and time_interval is None:
            raise RuntimeError('Generate events filter by time must specify at least one of'
                               'min_time, max_time and time_interval')

        # Generate event filters
        splitter_ws_name = '%s_splitter_TIME_' % self._currWorkspaceName
        info_ws_name = '%s_info__TIME_' % self._currWorkspaceName

        status, ret_obj = mtd.generate_event_filters_by_time(self._currWorkspaceName, splitter_ws_name, info_ws_name,
                                                             min_time, max_time,
                                                             time_interval, 'Seconds')

        # Get result
        if status is False:
            err_msg = ret_obj
            return status, err_msg

        # Store
        if tag is None:
            tag = '_TIME_'
        self._currSplittersDict[tag] = (splitter_ws_name, info_ws_name)

        return True, ret_obj

    def get_log_workspace(self, run_number, nxs_file_name=None):
        """

        :param run_number:
        :param nxs_file_name:
        :return:
        """
        # FIXME/TODO/NOW : Make it more robust with run_number is None
        if run_number is None:
            raise NotImplementedError('ASAP')

        if run_number == self._currRunNumber:
            return self._currWorkspace

        raise NotImplementedError('ASAP if it is in stored session.')

    def get_sample_log_names(self, with_info=False):
        """
        Get all sample logs' names
        :param with_info: output name with more information i.e., size of sample log
        :return:
        """
        # Check
        if self._currWorkspace is None:
            return False, 'Log helper has no data.'

        # Easy return
        if with_info is False:
            return True, self._currLogNamesList[:]

        # Do something fun
        self._currLogNamesList.sort()

        ret_list = list()
        single_value_list = list()

        for log_name in self._currLogNamesList:
            log_size = self._currWorkspace.run().getProperty(log_name).size()
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
        print '[DB-Trace-Bug Helper] run number = ', run_number, 'sample log name = ', sample_log_name,
        print 'start time  = ', start_time
        # Check
        if run_number is not None and run_number != self._currRunNumber:
            # FIXME - Deal with this situation
            raise RuntimeError('It has not been considered to retrieve previous run from Mantid.')
        if sample_log_name not in self._currLogNamesList:
            raise RuntimeError('Sample log name %s is not a FloatSeries.' % sample_log_name)

        print '[DB-Trace-Bug] current workspace = ', str(self._currWorkspace), 'log name = ', sample_log_name

        # Get property
        print '[DB-Trace-Bug Helper 2] run number = ', run_number, 'sample log name = ', sample_log_name,
        print 'start time  = ', start_time
        return mtd.get_sample_log_value(src_workspace=self._currWorkspace,
                                        sample_log_name=sample_log_name,
                                        start_time=start_time,
                                        stop_time=stop_time,
                                        relative=relative)

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

        # print '[DBX] Use current = ', use_current, 'Current run = ', self._currRunNumber, '\n'

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
        TODO
        :return:
        """
        self._currentSplitterWS = self._currSplittersDict['Time']

        return

    def set_current_slicer_manaul(self):
        """
        TODO
        :return:
        """
        self._currentSplitterWS = self._currSplittersDict['Manual']

        return

    def store_current_session(self):
        """ Store current session
        :return:
        """
        nxs_name = self._currNexusFilename
        run_number = self._currRunNumber
        ws_name = self._currWorkspaceName
        splitter_dict = self._currSplittersDict.copy()

        dict_key = os.path.basename(nxs_name)
        self._prevSessionDict[dict_key] = [nxs_name, run_number, ws_name, splitter_dict]

        return

    def restore_session(self, nxs_base_name):
        """
        Restore a save session
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
        if mtd.has_workspace(ws_name) is False:
            return False, 'Log workspace %s does not exist.' % ws_name

        # Retrieve
        self._currNexusFilename = nxs_name
        self._currRunNumber = run_number
        self._currWorkspaceName = ws_name
        self._currWorkspace = mtd.get_workspace(ws_name)
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
        splitter_ws = mtd.retrieve_workspace(splitter_ws_name)
        if splitter_ws is None:
            raise NotImplementedError('It is not likely not to locate the splitters workspace.')
        log_ws = self.get_log_workspace(run_number)
        try:
            run_start = log_ws.run().getProperty('proton_charge').times[0]
            run_start_ns = run_start.totalNanoseconds()
        except RuntimeError:
            run_start = '1990-01-01T00:00:00.0000000000'
            run_start_ns = 0
        print '[DB-BAR] run start = ', run_start_ns
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
            print '[BAF] Line: ', line
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
                print '[BAF] Found reference run %s' % str(ref_run)
            elif terms[0].lower().startswith('runstarttime'):
                # run start time
                run_start_str = terms[1]
                try:
                    run_start = float(run_start_str)
                except ValueError:
                    print '[Error] Unable to convert run start time %s to float' % run_start_str
        else:
            # remove all tab
            line = line.replace('\t', '')
            terms = line.split()
            if len(terms) < 2:
                print '[Error] Line "%s" is of wrong format.' % line
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
                print '[Error] Line "%s" has wrong type of vlaue for start/stop.' % line
                continue
        # END-IF (#)
    # END-FOR

    print '[DB] Parse segment file with reference run %s started at %s. Total %d segments' % (
            str(ref_run), str(run_start), len(segment_list)
    )

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
