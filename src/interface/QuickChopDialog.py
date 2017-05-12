# Dialog (main window) for quick-chopping
import os

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_ChopDialog
import gui.GuiUtility as GuiUtility


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

        # set up the default value of the widgets
        self.ui.lineEdit_runNumber.setText(str(run_number))
        self.ui.lineEdit_sourceFile.setText(str(raw_file_name))
        self.ui.radioButton_saveToArbitrary.setChecked(False)
        self.ui.radioButton_saveToArchive.setChecked(True)
        self.ui.checkBox_reduceToGSAS.setChecked(True)
        self.ui.checkBox_saveNeXus.setChecked(True)

        # default output directory
        self.ui.lineEdit_outputDir.setText(os.getcwd())

        # set up event handlers
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'),
                     self.do_chop)
        self.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
                     self.do_browse_output)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'),
                     self.do_quit)

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
        record the state to chop/reduce to be True and close the window
        Note: this is the OK button and thus dialog will be closed and be returned with 1
        :return:
        """
        # check output directory
        if self.ui.radioButton_saveToArbitrary.isChecked():
            # output directory
            target_dir = str(self.ui.lineEdit_outputDir.text())
            if len(target_dir) == 0:
                GuiUtility.pop_dialog_error(self, 'Output direcotry is not specified.')
                return

            # data processing options
            if self.ui.checkBox_saveNeXus.isChecked() is False and self.ui.checkBox_reduceToGSAS.isChecked() is False:
                GuiUtility.pop_dialog_error(self, 'At least one operation, save to Nexus and reduce to GSAS, '
                                                  'must be selected.')
                return
        # END-IF

        self.close()

        return

    def do_quit(self):
        """

        :return:
        """
        self.close()

        return

    @property
    def reduce_data(self):
        """
        Get the flag whether the sliced data will be reduced to GSAS
        :return:
        """
        return self.ui.checkBox_reduceToGSAS.isChecked()

    @property
    def save_to_nexus(self):
        """
        check whether the chopped data will be written to NeXus
        :return:
        """
        return self.ui.checkBox_saveNeXus.isChecked()

    @property
    def output_to_archive(self):
        """
        whether the result will be written to SNS archive?
        :return:
        """
        return self.ui.radioButton_saveToArchive.isChecked()

    @property
    def output_directory(self):
        """
        get output directory
        :return:
        """
        return str(self.ui.lineEdit_outputDir.text())
