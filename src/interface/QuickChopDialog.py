# Dialog (main window) for quick-chopping
import os

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_ChopDialog


class QuickChopDialog(QtGui.QMainWindow):
    """
    A dialog box to do quick chopping
    """
    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        # base class init
        super(QuickChopDialog, self).__init__(parent)

        # set up parent
        self._myController = parent.get_controller()
        assert self._myController is not None, 'Workflow controller cannot be NONE.'

        # class variables
        self._rawFileName = None
        self._slicerType = None

        # init UI
        self.ui = gui.ui_ChopDialog.Ui_MainWindow()
        self.ui.setupUi(self)

        # set up event handlers
        self.connect(self.ui.pushButton_chop, QtCore.SIGNAL('clicked()'),
                     self.do_chop)
        self.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
                     self.do_browse_output)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
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
        Chop data
        :return:
        """
        # get slicer manager
        chop_manager = self._myController.chop_manager

        # chop data
        run_or_file = str(self.ui.lineEdit_run.text())
        if run_or_file.isdigit():
            # it is a run
            run_number = int(run_or_file)
            status, info_tup = self._myController.get_run_info(run_number)
            if status:
                raw_file_name = info_tup
            else:
                raise RuntimeError('Unable to find file for run %d.' % run_number)
        else:
            # it is a file name
            raw_file_name = run_or_file
        # END-IF

        output_dir = str(self.ui.lineEdit_outputDir.text())

        chop_manager.chop_data(raw_file_name, self._slicerType, output_dir)

        self.do_quit()

        return

    def do_quit(self):
        """

        :return:
        """
        self.close()

    def set_run(self, raw_file_name):
        """

        :param raw_file_name:
        :return:
        """
        if raw_file_name is None:
            return

        self._rawFileName = raw_file_name
        self.ui.lineEdit_run.setText(self._rawFileName)

        return

    def set_slicer_type(self, slicer_type):
        """

        :param slicer_type:
        :return:
        """
        self._slicerType = slicer_type

        return
