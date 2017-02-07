#import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

import gui.ui_ManualSlicerTable


class ManualSlicerSetupTableDialog(QtGui.QDialog):
    """
    extended dialog
    """
    def __init__(self, parent):
        """

        """
        super(ManualSlicerSetupTableDialog, self).__init__(parent)

        self.ui = gui.ui_ManualSlicerTable.Ui_Dialog()
        self.ui.setupUi(self)

        self._init_widgets()

        self.connect(self.ui.pushButton_hide, QtCore.SIGNAL('clicked()'),
                     self.do_hide_window)

        return

    def _init_widgets(self):
        """

        :return:
        """
        # slice segments table
        self.ui.tableWidget_segments.setup()

    def do_hide_window(self):
        """

        :return:
        """
        self.setHidden(True)

    def write_table(self, slicers_list):
        """

        :param slicers_list:
        :return:
        """
        self.ui.tableWidget_segments.remove_all_rows()

        for slicer_time in slicers_list:
            self.ui.tableWidget_segments.append_start_time(slicer_time)

        return
