from PyQt4 import QtCore
from PyQt4 import QtGui

import gui.ui_LiveDataView as ui_LiveDataView


class VulcanLiveDataView(QtGui.QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    def __init__(self, parent):
        """
        init
        :param parent:
        """
        super(VulcanLiveDataView, self).__init__(parent)

        self.ui = ui_LiveDataView.Ui_MainWindow()
        self.ui.setupUi(self)

        return
