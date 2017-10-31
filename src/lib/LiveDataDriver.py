import sys
sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')

import mantid.simpleapi as mantidsimple
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
    def convert_unit(src_ws, target_unit, new_ws_name):
        """

        :param src_ws:
        :param target_unit:
        :param new_ws_name:
        :return:
        """
        # check
        assert isinstance(target_unit, str), 'blabla must be string'
        assert isinstance(new_ws_name, str), 'blabla must be string 2'

        # convert workspace to workspace
        if isinstance(src_ws, str):
            src_ws = ADS.retrieve(src_ws)

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
