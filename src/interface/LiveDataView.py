from PyQt4 import QtCore
from PyQt4 import QtGui

import gui.ui_LiveDataView as ui_LiveDataView
import PyVDrive.lib.LiveDataDriver as ld


class VulcanLiveDataView(QtGui.QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    def __init__(self, parent, live_driver):
        """
        init
        :param parent:
        """
        # call parent
        super(VulcanLiveDataView, self).__init__(parent)

        # get hold of controller/driver
        self._controller = live_driver

        # define data structure
        self._myTimeStep = 10  # seconds
        self._myWorkspaceNumber = 360  # containing 1 hour data for dT = 10 seconds
        self._myWorkspaceList = [None] * self._myWorkspaceNumber  # a holder for workspace names
        self._myListIndex = 0

        self._currAccumulateIndex = 0  # index for accumulated workspaces

        # start UI
        self.ui = ui_LiveDataView.Ui_MainWindow()
        self.ui.setupUi(self)

        # set up the event handlers
        self.connect(self.ui.pushButton_startLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_start_live)
        self.connect(self.ui.pushButton_stopLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_stop_live)

        # multiple thread pool
        self._checkStateTimer = None

        return

    def do_start_live(self):
        """
        start live data reduction and view
        :return:
        """

        # start timer
        self._checkStateTimer = TimerThread(self._myTimeStep, self)
        self._checkStateTimer.start()

        # start start listener
        self._controller = ld.LiveDataDriver()
        self._controller.run()

        return

    def do_stop_live(self):
        """
        stop live data reduction and view
        :return:
        """
        self._checkStateTimer.stop()

        self._controller.stop()

        return

    def add_new_workspace(self, ws_name):
        """
        add a new workspace to the list.  if the list is full, then replace the existing one.
        :param ws_name:
        :return:
        """
        # replace previous one
        if self._myWorkspaceList[self._myListIndex] is not None:
            prev_ws_name = self._myWorkspaceList[self._myListIndex]
            self._controller.delete_workspace(prev_ws_name)

        # set the new one
        self._myWorkspaceList[self._myListIndex] = ws_name

        return

    def update_timer(self):
        """
        update timer
        :return:
        """

        self.ui.spinBox_currentIndex.setValue(self._currAccumulateIndex)

        self._currAccumulateIndex += 1

        total_index = self._controller.get_live_counter()
        self.ui.spinBox_totalIndex.setValue(total_index)

        return


class TimerThread(QtCore.QThread):

    time_due = QtCore.pyqtSignal(object)

    def __init__(self, time_step, parent):
        QtCore.QThread.__init__(self)

        self._parent = parent

        self._continueTimerLoop = True


    def run(self):
        import time

        while self._continueTimerLoop:
            time.sleep(1)
            self._parent.update_timer()

        # self.data_downloaded.emit('%s\n%s' % (self.url, info))


    def stop(self):

        self._continueTimerLoop = False

