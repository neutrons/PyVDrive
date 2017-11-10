import sys
sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')

import numpy
import mantid.simpleapi as mantidsimple
import mantid
from mantid.api import AlgorithmManager
from mantid.api import AnalysisDataService as ADS
import mantid_helper
import logging
import os
import time
from PyQt4 import QtCore

# TODO/ISSUE/NEXT - Find out how to use log files
# .. LOG_NAME = 'livereduce'  # constant for logging
# .. LOG_FILE = '/var/log/SNS_applications/livereduce.log'
# .. logger = logging.getLogger(__name__)
# .. logger.setLevel(logging.INFO)


class LiveDataDriver(QtCore.QThread):
    """
    Driver/manager for live data monitoring and reduction
    """
    COUNTER_WORKSPACE_NAME = '_VULCAN_LIVE_COUNTER'
    LIVE_PROCESS_SCRIPTS = '/SNS/VULCAN/shared/livereduce/vulcan_live_data_test.py'
    # LIVE_PROCESS_SCRIPTS = '/home/wzz/Mantid_Project/builds/vulcan_live_data_test.py'  # local test only

    def __init__(self):
        """
        initialization
        """
        super(LiveDataDriver, self).__init__()

        # clear the existing workspace with same name
        if mantid_helper.workspace_does_exist(LiveDataDriver.COUNTER_WORKSPACE_NAME):
            mantid_helper.delete_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)

        # create workspace: workspace index 1 will be used to record number of events
        mantidsimple.CreateWorkspace(OutputWorkspace=LiveDataDriver.COUNTER_WORKSPACE_NAME,
                                     DataX=[0, 0], DataY=[0, 0], NSpec=2)

        # get the live reduction script
        self._live_reduction_script = LiveDataDriver.LIVE_PROCESS_SCRIPTS

        self._thread_continue = True

        return

    @staticmethod
    def convert_time_stamps(date_time_vec, relative):
        """convert a vector of DateAndTime instance to a vector of double as relative
        time to a specified time in DateAndTime
        :param date_time_vec:
        :param relative: start time
        :return: a vector of time stamps in double/float in unit of seconds
        """
        # check inputs
        assert isinstance(date_time_vec, numpy.ndarray) or \
               isinstance(date_time_vec, mantid.kernel._kernel.std_vector_dateandtime),\
            'Input time vector must be a numpy.array but not a {0}.'.format(type(date_time_vec))
        assert relative is None or relative.__class__.__name__.count('DateAndTime') > 0, \
            'Relative time {0} must be None or a DateAndTime instance but not a {1}.' \
            ''.format(relative, type(relative))

        # create an array
        shape = len(date_time_vec)
        time_vec = numpy.ndarray(shape=(shape,), dtype='float')

        if relative is None:
            start_time = 0
        else:
            start_time = relative.totalNanoseconds()

        # convert
        for i in range(shape):
            time_i = (date_time_vec[i].totalNanoseconds() - start_time) * 1.E-9
            time_vec[i] = time_i

        return time_vec

    @staticmethod
    def convert_unit(src_ws, target_unit, new_ws_name):
        """Convert the unit of a workspace
        :param src_ws:
        :param target_unit:
        :param new_ws_name:
        :return:
        """
        # check
        assert isinstance(target_unit, str), 'Target unit {0} must be string but not a {1}' \
                                             ''.format(target_unit, type(target_unit))
        assert isinstance(new_ws_name, str), 'New workspace name {0} must be string but not a {1}.' \
                                             ''.format(new_ws_name, type(new_ws_name))

        # convert workspace to workspace
        if isinstance(src_ws, str):
            if ADS.doesExist(src_ws) is False:
                raise RuntimeError('blabla')
            src_ws = ADS.retrieve(src_ws)
        else:
            assert src_ws is not None, 'Source workspace of convert unit cannot be None.'

        # check units
        src_unit = src_ws.getAxis(0).getUnit().unitID()
        if src_unit == target_unit:
            # same unit. do nothing.  copy reference and return
            new_ws = src_ws
            is_new_ws = False
        else:
            # covert unit by calling Mantid
            mantidsimple.ConvertUnits(InputWorkspace=src_ws, Target=target_unit, OutputWorkspace=new_ws_name)
            new_ws = ADS.retrieve(new_ws_name)
            is_new_ws = True
        # END-IF

        return new_ws, is_new_ws

    @staticmethod
    def delete_workspace(workspace_name, no_throw=False):
        """
        Delete a workspace from Mantid's AnalysisDataService
        Args:
            workspace_name: name of a workspace as a string instance
            no_throw: if True, then it won't throw any exception if the workspace does not exist in AnalysisDataService

        Returns: None

        """
        # check
        assert isinstance(workspace_name, str), \
            'Input workspace name must be a string, but not %s.' % str(type(workspace_name))

        # check whether the workspace exists
        does_exit = ADS.doesExist(workspace_name)
        if does_exit:
            # delete
            mantid_helper.delete_workspace(workspace=workspace_name)
        elif not no_throw:
            raise RuntimeError('Workspace %s does not exist.' % workspace_name)

        return

    @staticmethod
    def get_live_counter():
        """
        check
        :return:
        """
        counter_ws = mantid_helper.retrieve_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)
        curr_index = counter_ws.readX(0)[0]

        return curr_index

    @staticmethod
    def get_live_events():
        """
        check
        :return:
        """
        counter_ws = mantid_helper.retrieve_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)
        live_events = counter_ws.readX(1)[0]

        return live_events

    @staticmethod
    def get_workspaces():
        """get the workspace from Mantid ADS
        :except: RuntimeError if ADS crashes
        :return:
        """
        try:
            ws_names = ADS.getObjectNames()
        except RuntimeError as run_err:
            raise RuntimeError('Unable to get workspaces\' names from ADS due to \n{0}'.format(run_err))
        
        return ws_names

    def load_reduced_runs(self, ipts_number, run_number):
        # TODO/NOW/TODO/Implement
        blabla

    # TEST TODO/New Method
    @staticmethod
    def parse_sample_log(ws_name_list, sample_log_name):
        """parse the sample log time stamps and value from a series of workspaces
        :except RuntimeError:
        :param ws_name_list:
        :param sample_log_name:
        :return:
        """
        # check inputs
        assert isinstance(ws_name_list, list), 'Workspace names {0} must be given as a list but not a {1}.' \
                                               ''.format(ws_name_list, type(ws_name_list))
        assert isinstance(sample_log_name, str), 'Sample log name {0} must be a string but not a {1}.' \
                                                 ''.format(sample_log_name, type(sample_log_name))

        date_time_vec = None
        sample_value_vec = None

        for seq_index, ws_name in enumerate(ws_name_list):
            if ADS.doesExist(ws_name) is False:
                raise RuntimeError('Workspace {0} does not exist.'.format(ws_name))

            temp_workspace = ADS.retrieve(ws_name)
            time_series = temp_workspace.run().getProperty(sample_log_name)

            time_vec_i = time_series.times
            value_vec_i = time_series.value

            if date_time_vec is None:
                # first workspace to process
                date_time_vec = time_vec_i
                sample_value_vec = value_vec_i
            else:
                # in append mode
                # check
                if date_time_vec[-1] >= time_vec_i[0]:
                    raise RuntimeError('Previous workspace {0} is later than the current one {1}.'
                                       ''.format(ws_name_list[seq_index-1], ws_name))

                # append
                numpy.append(date_time_vec, time_vec_i)
                numpy.append(sample_value_vec, value_vec_i)
            # END-IF-ELSE
        # END-FOR (workspaces)

        return date_time_vec, sample_value_vec

    @staticmethod
    def sum_workspaces(workspace_name_list, target_workspace_name):
        """
        sum workspaces together
        example: [self._inAccumulationWorkspaceName, workspace_i],  self._inAccumulationWorkspaceName)
        :param workspace_name_list:
        :param target_workspace_name:
        :return:
        """
        # TODO/NOW - validate input
        # blabla

        if len(workspace_name_list) != 2:
            raise RuntimeError('Prototype must have 2 inputs')

        if True:
            mantidsimple.Plus(LHSWorkspace=workspace_name_list[0], RHSWorkspace=workspace_name_list[1],
                              OutputWorkspace=target_workspace_name)
        else:
            # old method
            ws_in_acc = mantid_helper.retrieve_workspace(workspace_name_list[0])
            workspace_i = mantid_helper.retrieve_workspace(target_workspace_name[1])
            for iws in range(workspace_i.getNumberHistograms()):
                if len(ws_in_acc.readY(iws)) != len(workspace_i.readY(iws)):
                    raise RuntimeError('Spectrum {0}: accumulated workspace {1} has a different X size ({2}) than '
                                       'incremental workspace {3} ({4}).'
                                       ''.format(iws, workspace_name_list[0], len(ws_in_acc.readX(iws)),
                                                 workspace_i.name(), len(workspace_i.readX(iws))))
                # END-IF
                ws_in_acc.setY(iws, ws_in_acc.readY(iws) + workspace_i.readY(iws))
            # END-FOR
        # END-IF-ELSE

        return

    def run(self):
        """ main method to start live data
        :return:
        """
        # Test for script: whatever has all the log information...
        # and output_1, output_2 will do good still
        mantidsimple.StartLiveData(UpdateEvery=10,
                                   Instrument='VULCAN',
                                   Listener='SNSLiveEventDataListener',
                                   Address='bl7-daq1.sns.gov:31415',
                                   StartTime='1990-01-01T00:00:00',
                                   ProcessingScriptFilename=self._live_reduction_script,
                                   PreserveEvents=False,
                                   AccumulationMethod='Add',
                                   RunTransitionBehavior='Rename',
                                   OutputWorkspace='VULCAN_Live')

        return

    def stop(self):
        """

        :return:
        """
        AlgorithmManager.cancelAll()

        self._thread_continue = False

        return


def main():
    driver = LiveDataDriver()
    driver.start_live_data()


if __name__ == '__main__':
    main()
