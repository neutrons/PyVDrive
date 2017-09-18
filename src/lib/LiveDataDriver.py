import mantid.simpleapi as mantidsimple
import mantid_helper
import logging
import pyinotify
import os
from PyQt4 import QtCore

LOG_NAME = 'livereduce'  # constant for logging
LOG_FILE = '/var/log/SNS_applications/livereduce.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# # create a file handler
# if os.environ['USER'] == 'snsdata':
#     handler = logging.FileHandler(LOG_FILE)
# else:
#     handler = logging.FileHandler('livereduce.log')
# handler.setLevel(logging.INFO)
#
# # create a logging format
# format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# handler.setFormatter(logging.Formatter(format))
#
# # add the handlers to the logger
# logger.addHandler(handler)
#
# logger.info('logging started by user \'' + os.environ['USER'] + '\'')
#
#
# class EventHandler(pyinotify.ProcessEvent):
#     logger = logger or logging.getLogger('EventHandler')
#
#     def __init__(self, config, livemanager):
#         # files that we actual care about
#         self.configfile = config.filename
#         self.scriptdir = config.script_dir
#         self.scriptfiles = [config.procScript, config.postProcScript]
#
#         # thing controlling the actual work
#         self.livemanager = livemanager
#
#     def filestowatch(self):
#         return [self.scriptdir, self.configfile]
#
#     def process_default(self, event):
#         if event.pathname == self.configfile or \
#            event.pathname in self.scriptfiles:
#             self.logger.info(event.maskname + ': \'' + event.pathname + '\'')
#
#         if event.pathname == self.configfile:
#             self.logger.warn('Modifying configuration file is not supported' +
#                              '- shutting down')
#             self.livemanager.stop()
#             raise KeyboardInterrupt('stop inotify')
#
#         if event.pathname in self.scriptfiles:
#             self.logger.info('Processing script \'' + event.pathname +
#                              '\' changed - restarting \'StartLiveData\'')
#             self.livemanager.stop()
#             time.sleep(1.)  # seconds
#             self.livemanager.start()


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

    def run(self):
        """

        :return:
        """
        import time
        # Test for script: whatever has all the log information...
        # and output_1, output_2 will do good still
        """
        mantidsimple.StartLiveData(UpdateEvery=5,
                                   Instrument='VULCAN',
                                   Listener='SNSLiveEventDataListener',
                                   Address='bl7-daq1.sns.gov:31415',
                                   StartTime='1990-01-01T00:00:00',
                                   ProcessingScriptFilename=self._live_reduction_script,
                                   PreserveEvents=False,
                                   # AccumulationWorkspace='live_vulcan_x',
                                   AccumulationMethod='Add',
                                   OutputWorkspace='whatever')
        """

        # wm = pyinotify.WatchManager()
        # notifier = pyinotify.Notifier(wm, handler)
        # # watched events
        # mask = pyinotify.IN_DELETE | pyinotify.IN_MODIFY | pyinotify.IN_CREATE
        # logger.info("WATCHING", handler.filestowatch())
        # wm.add_watch(handler.filestowatch(), mask)



        #
        # # start up the live data
        # liveDataMgr.start()
        #
        # # inotify will keep the program running
        # notifier.loop()

        mantidsimple.StartLiveData(UpdateEvery=5,
                                   Instrument='VULCAN',
                                   Listener='SNSLiveEventDataListener',
                                   Address='bl7-daq1.sns.gov:31415',
                                   StartTime='1990-01-01T00:00:00',
                                   #ProcessingScriptFilename=self._live_reduction_script,
                                   PreserveEvents=False,
                                   AccumulationMethod='Replace',
                                   OutputWorkspace='whatever')

        # while self._thread_continue:
        #     time.sleep(10)

        return

    def stop(self):
        """

        :return:
        """
        mantidsimple.cancelAll()

        self._thread_continue = False

        return


class LiveDataThread(QtCore.QThread):

    time_due = QtCore.pyqtSignal(object)

    def __init__(self, time_step, parent):
        QtCore.QThread.__init__(self)

        self._parent = parent

        self._continueTimerLoop = True


    def run(self):
        import time


        mantidsimple.StartLiveData(UpdateEvery=5,
                                   Instrument='VULCAN',
                                   Listener='SNSLiveEventDataListener',
                                   Address='bl7-daq1.sns.gov:31415',
                                   StartTime='1990-01-01T00:00:00',
                                   #ProcessingScriptFilename=self._live_reduction_script,
                                   PreserveEvents=False,
                                   AccumulationMethod='Replace',
                                   OutputWorkspace='whatever')

        while self._continueTimerLoop:
            time.sleep(1)
            #self._parent.update_timer()



        # self.data_downloaded.emit('%s\n%s' % (self.url, info))


    def stop(self):

        self._continueTimerLoop = False


def main():
    driver = LiveDataDriver()
    driver.start_live_data()


if __name__ == '__main__':
    main()
