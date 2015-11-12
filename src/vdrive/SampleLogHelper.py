import os

import mantid_helper as mtd


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
        # key = log file name (base name), sample log name
        self._currSplittersDict = dict()
        # self._logInfoList = None

        # Stored session
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
        # Check and store
        if os.path.basename(nxs_file_name) == os.path.basename(self._currNexusFilename):
            # same: no op
            print '[INFO] Same NeXus file. No operation.'
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
        else:
            print '[DB] Input run number is None for NeXus file %s' % nxs_base_name

        base_name = os.path.basename(nxs_file_name)
        if base_name == self._currNexusFilename:
            return True, 'Try to reload sample logs of file %s' % base_name
        else:
            self._currNexusFilename = base_name

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

    def generate_events_filter_by_log(self, log_name, min_time, max_time, relative_time,
                                      min_log_value, max_log_value, log_value_interval,
                                      value_change_direction):
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
        self._currSplittersDict[log_name] = (splitter_ws_name, info_ws_name)

        return

    def generate_events_filter_by_time(self, min_time, max_time, time_interval):
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
        self._currSplittersDict['_TIME_'] = (splitter_ws_name, info_ws_name)

        return True, ret_obj

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

    def get_sample_data(self, sample_log_name, relative):
        """
        Get sample log's data as 2 vectors for time (unit of second) and log value
        :exception: RuntimeError for sample log name is not in list
        :param sample_log_name:
        :return: 2-tuple as (numpy.array, numpy.array) for time and log value
        """
        # Check
        if sample_log_name not in self._currLogNamesList:
            raise RuntimeError('Sample log name %s is not a FloatSeries.' % sample_log_name)

        # Get property
        return mtd.get_sample_log_value(self._currWorkspace, sample_log_name, relative)

    def get_slicer_by_log(self, run_number, log_name, nxs_name=None):
        """ Get slicer by log value
        :param run_number:
        :param log_name:
        :param nxs_name:
        :return:
        """
        # Check
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
            splitter_dict = tup[2]

        if log_name not in splitter_dict:
            return False, 'There is no processed slicer by log %s for NeXus file %s' % (log_name, nxs_name)

        return True, splitter_dict[log_name]

    def get_slicer_by_time(self, run_number, nxs_name=None):
        """ Get slicer by log value
        :param run_number:
        :param log_name:
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
            split_dict = self._prevSessionDict[nxs_name][2]
        if '_TIME_' not in split_dict:
            return False, 'There is no splitters by time for %s. Candidates are %s.\n' % (
                nxs_name, str(split_dict.keys())
            )

        return True, split_dict['_TIME_']

    def set_current_slicer_sample_log(self, sample_log_name):
        """
        TODOD
        :param sample_log_name:
        :return:
        """
        self._currentSplitterWS = self._currSplittersDict[(self._currNexusFilename, sample_log_name)]

        return

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
        ws_name = self._currWorkspaceName
        splitter_dict = self._currSplittersDict.copy()

        dict_key = os.path.basename(nxs_name)
        self._prevSessionDict[dict_key] = [nxs_name, ws_name, splitter_dict]

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
        nxs_name, ws_name, splitter_dict = self._prevSessionDict[nxs_base_name]

        # Check workspace existence
        if mtd.has_workspace(ws_name) is False:
            return False, 'Log workspace %s does not exist.' % ws_name

        # Retrieve
        self._currNexusFilename = nxs_name
        self._currWorkspaceName = ws_name
        self._currWorkspace = mtd.get_workspace(ws_name)
        self._currSplittersDict = splitter_dict

        return True, ''
