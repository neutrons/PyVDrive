import os

import mantid_helper as mtd


class SampleLogManager(object):
    """
    """
    def __init__(self):
        """
        Initialization
        :return:
        """
        self._currentLogFile = ''

        self._workspace = None
        self._workspace_name = ''
        self._logNamesList = None
        self._logInfoList = None

        # key = log file name (base name), sample log name
        self._splitterWSDict = dict()

        return

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

        print '[DB]', 'InputWorkspace =', self._workspace_name, 'LogName =', log_name, 'StartTime =', min_time,
        print 'StopTime =', max_time, 'LogValueInterval =', log_value_interval
        print

        # create output workspace as a standard
        splitter_ws_name = '%s_splitter_%s' % (self._workspace_name, log_name)
        info_ws_name = '%s_info_%s' % (self._workspace_name, log_name)

        mtd.generate_event_filters_by_log(self._workspace_name, splitter_ws_name, info_ws_name,
                                          min_time, max_time, log_name, min_log_value, max_log_value,
                                          log_value_interval, value_change_direction)

        # Store
        self._splitterWSDict[log_name] = (splitter_ws_name, info_ws_name)

        return

    def create_splitters_by_time(self, start_time, stop_time, delta_time, unit='second', relative=True):
        """
        Create splitters by time
        :param start_time:
        :param stop_time:
        :param delta_time:
        :param unit:
        :param relative:
        :return:
        """
        # Check
        assert isinstance(start_time, float)
        assert isinstance(stop_time, float)
        assert isinstance(delta_time, float) or (delta_time is None)
        assert isinstance(unit, str)
        assert isinstance(relative, bool)
        assert self._workspace

        # Generate event filters
        status, ret_obj = mtd.generate_event_filters(self._workspace, start_time, stop_time, delta_time, unit, relative)
        if status is False:
            return status, ret_obj

        # Store
        splitters, information = ret_obj
        self._splitterWSDict[(self._currentLogFile, 'Time')] = (splitters, information)

        return True, ''

    def get_sample_log_names(self, with_info=False):
        """
        Get all sample logs' names
        :param with_info: output name with more information i.e., size of sample log
        :return:
        """
        # Check
        if self._workspace is None:
            return False, 'Log helper has no data.'

        # Easy return
        if with_info is False:
            return True, self._logNamesList[:]

        # Do something fun
        self._logNamesList.sort()

        ret_list = list()
        single_value_list = list()

        for log_name in self._logNamesList:
            log_size = self._workspace.run().getProperty(log_name).size()
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
        if sample_log_name not in self._logNamesList:
            raise RuntimeError('Sample log name %s is not a FloatSeries.' % sample_log_name)

        # Get property
        return mtd.get_sample_log_value(self._workspace, sample_log_name, relative)

    def get_splitters_absolute_time(self):

        return


    def get_splitters_relative_time(self):

        return

    def set_nexus_file(self, nxs_file_name):
        """ Load NeXus file
        :param nxs_file_name:
        :return:
        """
        #
        base_name = os.path.basename(nxs_file_name)
        if base_name == self._currentLogFile:
            return True, 'Try to reload sample logs of file %s' % base_name
        else:
            self._currentLogFile = base_name

        # Output ws name
        out_ws_name = os.path.basename(nxs_file_name).split('.')[0] + '_Meta'

        # Load sample logs
        status, ret_obj = mtd.load_nexus(data_file_name=nxs_file_name,
                                         output_ws_name=out_ws_name,
                                         meta_data_only=True)

        if status is False:
            return False, ret_obj

        self._workspace = ret_obj
        self._workspace_name = out_ws_name

        # Set up log names list
        try:
            self._logNamesList = mtd.get_sample_log_names(self._workspace)
            assert isinstance(self._logNamesList, list)
        except RuntimeError as err:
            return False, 'Unable to retrieve series log due to %s.' % str(err)

        # Set up log list
        self._logInfoList = mtd.get_sample_log_info(self._workspace)

        return True, ''

    def set_current_slicer_sample_log(self, sample_log_name):
        """
        TODOD
        :param sample_log_name:
        :return:
        """
        self._currentSplitterWS = self._splitterWSDict[(self._currentLogFile, sample_log_name)]

        return

    def set_current_slicer_time(self):
        """
        TODO
        :return:
        """
        self._currentSplitterWS = self._splitterWSDict['Time']

        return

    def set_current_slicer_manaul(self):
        """
        TODO
        :return:
        """
        self._currentSplitterWS = self._splitterWSDict['Manual']

        return
