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

    def get_sample_log_names(self):
        """
        Get all sample logs' names
        :return:
        """
        if self._workspace is None:
            return False, 'Log helper has no data.'

        return True, self._logNamesList[:]

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
