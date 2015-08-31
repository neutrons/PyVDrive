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
        self._workspace = None
        self._workspace_name = ''
        self._logNamesList = None
        self._logInfoList = None

        return

    def get_sample_log_names(self):
        """
        Get all sample logs' names
        :return:
        """
        if self._workspace is None:
            return False, 'Log helper has no data.'

        return True, self._logNamesList[:]

    def get_sample_data(self, sample_log_name):
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
        return mtd.get_sample_log_value(self._workspace, sample_log_name)

    def get_splitters_absolute_time(self):

        return


    def get_splitters_relative_time(self):

        return

    def set_nexus_file(self, nxs_file_name):
        """ Load NeXus file
        :param nxs_file_name:
        :return:
        """
        # Output ws name
        out_ws_name = os.path.basename(nxs_file_name).split('.')[0] + '_Meta'

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
   
    def set_splitters(self):

        return
