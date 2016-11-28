# Dialog (main window) for quick-chopping
import os

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_ChopDialog


class QuickChopDialog(QtGui.QDialog):
    """
    A dialog box to do quick chopping
    """
    def __init__(self, parent, run_number, raw_file_name):
        """
        Initialization
        :param parent:
        """
        # base class init
        super(QuickChopDialog, self).__init__(parent)

        # init UI
        self.ui = gui.ui_ChopDialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.lineEdit_runNumber.setText(str(run_number))
        self.ui.lineEdit_sourceFile.setText(str(raw_file_name))
        self.ui.radioButton_toGSAS.setChecked(True)

        # set up event handlers
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'),
                     self.do_chop)
        self.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
                     self.do_browse_output)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'),
                     self.do_quit)

        # default output directory
        self._outputDir = os.getcwd()
        self.ui.lineEdit_outputDir.setText(self._outputDir)

        return

    def do_browse_output(self):
        """
        Browse output
        :return:
        """
        out_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'Output Directory', os.getcwd()))
        self.ui.lineEdit_outputDir.setText(out_dir)

        return

    def do_chop(self):
        """
        Chop data
        :return:
        """
        self._outputDir = str(self.ui.lineEdit_outputDir.text())

        self.close()

        return

    def do_quit(self):
        """

        :return:
        """
        self.close()

        return

    def get_output_dir(self):
        """
        get output directory
        :return:
        """
        return self._outputDir

    def to_reduce_data(self):
        """
        Get the flag whether the sliced data will be reduced to GSAS
        :return:
        """
        return self.ui.radioButton_toGSAS.isChecked()
