# Dialog (main window) for quick-chopping
import os

try:
    import qtconsole.inprocess
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QDialog, QFileDialog
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QDialog, QFileDialog

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


import gui.GuiUtility as GuiUtility


class QuickChopDialog(QDialog):
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
        ui_path = os.path.join(os.path.dirname(__file__), "gui/ChopDialog.ui")
        self.ui = load_ui(ui_path, baseinstance=self)

        # set up the default value of the widgets
        self.ui.lineEdit_runNumber.setText(str(run_number))
        self.ui.lineEdit_sourceFile.setText(str(raw_file_name))

        self.ui.radioButton_saveToArbitrary.setChecked(False)
        self.ui.radioButton_saveToArchive.setChecked(True)
        self.ui.lineEdit_outputDir.setEnabled(False)
        self.ui.pushButton_browse.setEnabled(False)

        self.ui.radioButton_chopOnly.setChecked(True)
        self.ui.radioButton_chopReduce.setChecked(True)

        # default output directory
        self.ui.lineEdit_outputDir.setText(os.getcwd())

        # set up event handlers
        self.ui.pushButton_browse.clicked.connect(self.do_browse_output)
        self.ui.radioButton_saveToArbitrary.toggled.connect(self.event_save_to_changed)
        self.ui.radioButton_saveToArchive.toggled.connect(self.event_save_to_changed)

        self.ui.buttonBox.accepted.connect(self.do_chop)
        self.ui.buttonBox.rejected.connect(self.do_quit)

        # self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'),
        #              self.do_chop)
        # self.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
        #              self.do_browse_output)
        # self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'),
        #              self.do_quit)
        #
        # self.connect(self.ui.radioButton_saveToArbitrary, QtCore.SIGNAL('toggled(bool)'),
        #              self.event_save_to_changed)
        # self.connect(self.ui.radioButton_saveToArchive, QtCore.SIGNAL('toggled(bool)'),
        #              self.event_save_to_changed)

        return

    def do_browse_output(self):
        """
        Browse output
        :return:
        """
        out_dir = str(QFileDialog.getExistingDirectory(self, 'Output Directory', os.getcwd()))
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
                GuiUtility.pop_dialog_error(self, 'Output directory is not specified.')
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

    def event_save_to_changed(self):
        """
        event with radio buttons for 'save to...' changed
        :return:
        """
        to_enable = self.ui.radioButton_saveToArbitrary.isChecked()

        self.ui.lineEdit_outputDir.setEnabled(to_enable)
        self.ui.pushButton_browse.setEnabled(to_enable)

        return

    @property
    def reduce_data(self):
        """
        Get the flag whether the sliced data will be reduced to GSAS
        :return:
        """
        return self.ui.radioButton_chopReduce.isChecked()

    @property
    def save_to_nexus(self):
        """
        from 2017.05.15: chopped data will be always saved to NeXus
        :return:
        """
        return True

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
