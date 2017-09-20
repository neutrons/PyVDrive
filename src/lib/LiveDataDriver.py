import sys
#sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')

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
    LIVE_PROCESS_SCRIPTS = '/home/wzz/Mantid_Project/builds/vulcan_live_data_test.py'  # local test only

    def __init__(self):
        """
        initialization
        """
        # clear the existing workspace with same name
        if mantid_helper.workspace_does_exist(LiveDataDriver.COUNTER_WORKSPACE_NAME):
            mantid_helper.delete_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)

        # create workspace
        mantidsimple.CreateWorkspace(OutputWorkspace=LiveDataDriver.COUNTER_WORKSPACE_NAME,
                                     DataX=[0], DataY=[0], NSpec=1)

        # get the live reduction script
        self._live_reduction_script = LiveDataDriver.LIVE_PROCESS_SCRIPTS

        self._thread_continue = True

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

    def get_workspaces(self):
        """
        blabla
        :return:
        """
        ws_names = ADS.getObjectNames()
        
        return ws_names

    def run(self):
        """

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
                                   OutputWorkspace='whatever')

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
