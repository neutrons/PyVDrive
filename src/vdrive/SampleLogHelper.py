import os

import mantid_helper as mtd


class SampleLogManager(object):
    """
    """
    def __init__(self):
        """

        :return:
        """
        self._workspace = None
        self._workspace_name = ''


    def get_sample_log_names(self):
        """

        :return:
        """
        if self._workspace is None:
            return False, 'Log helper has no data.'

        return True, self._logNamesList

    def get_sample_data(self, do_skip, num_sec_skip):
        """

        :param do_skip:
        :param num_sec_skip:
        :return:
        """
        # TODO

        return

    def get_splitters_absolute_time(self):

        return


    def get_splitters_relative_time(self):

        return

    def set_nexus_file(self, nxs_file_name):
        """ Load NeXus file
        :param nxs_file_name:
        :return:
        """
        # TODO - DOC
        # Output ws name
        out_ws_name = os.path.basename(nxs_file_name).split('.')[0] + '_Meta'

        status, ret_obj = mtd.load_nexus(data_file_name=nxs_file_name,
                                         output_ws_name=out_ws_name,
                                         meta_data_only=True)

        if status is False:
            return False, ret_obj

        self._workspace = ret_obj
        self._workspace_name = out_ws_name

        try:
            self._logNamesList = mtd.get_sample_log_names(self._workspace)
        except RuntimeError as err:
            return False, 'Unable to retrieve series log due to %s.' % str(err)

        # Set up log list
        # FIXME - Put the next section into Mantid
        """
        import mantid
        ws = mtd["VULCAN_71087_event"]
        run = ws.run()

        prop_info_list = list()
        for p in run.getProperties():
            p_name = p.name
            if isinstance(p, mantid.kernel.FloatTimeSeriesProperty) is False:
                continue
            size = p.size()
            prop_info_list.append( (size, p_name) )

        prop_info_list.sort()
        for tup in prop_info_list:
        print '%-5d\t\t%s' % (tup[0], tup[1])
        """

        return True, ''
   
    def set_splitters(self):

        return
