from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_ManualSlicerTable
import gui.GuiUtility as GuiUtil


class ManualSlicerSetupTableDialog(QtGui.QDialog):
    """
    extended dialog to work with the manual event slicers (in time) table
    """
    myApplySlicerSignal = pyqtSignal(str, list)  # slicer name, slicer list
    mySaveSlicerSignal = pyqtSignal(str, list)  # file name, slicer list

    def __init__(self, parent):
        """
        initialization
        :param parent: parent window
        """
        super(ManualSlicerSetupTableDialog, self).__init__(parent)
        self._myParent = parent

        self.ui = gui.ui_ManualSlicerTable.Ui_Dialog()
        self.ui.setupUi(self)

        self._init_widgets()

        # define widgets' event handling
        self.connect(self.ui.pushButton_applyTimeSegs, QtCore.SIGNAL('clicked()'),
                     self.do_apply_slicers)

        self.connect(self.ui.pushButton_saveTimeSegs, QtCore.SIGNAL('clicked()'),
                     self.do_save_slicers_to_file)

        self.connect(self.ui.pushButton_hide, QtCore.SIGNAL('clicked()'),
                     self.do_hide_window)

        # define handler to signals

        return

    def _init_widgets(self):
        """
        initialize widgets
        :return:
        """
        # slice segments table
        self.ui.tableWidget_segments.setup()

        return

    @property
    def controller(self):
        """
        get project controller
        :return:
        """
        if self._myParent is None:
            raise RuntimeError('No (logical) parent')

        return self._myParent.get_controller()

    def do_apply_slicers(self):
        """
        generate the time slicers in controller/memory from this table
        :return:
        """
        # Get splitters
        try:
            split_tup_list = self.ui.tableWidget_segments.get_splitter_list()
        except RuntimeError as e:
            GuiUtil.pop_dialog_error(self, str(e))
            return

        # pop a dialog for the name of the slicer
        slicer_name, status = QtGui.QInputDialog.getText(self, 'Input Slicer Name', 'Enter slicer name:')
        # return if rejected with
        if status is False:
            return
        else:
            slicer_name = str(slicer_name)

        # Call parent method to generate random event slicer (splitters workspace or table)
        if self._myParent is not None:
            # TODO/ISSUE/33 - Let _myParent to handle this! send a signal to parent with list!
            self._myParent.get_controller().gen_data_slice_manual(run_number=self._currRunNumber,
                                                                  relative_time=True,
                                                                  time_segment_list=split_tup_list,
                                                                  slice_tag=slicer_name)
        # END-IF

        return

    def do_hide_window(self):
        """

        :return:
        """
        self.setHidden(True)

        return

    def do_save_slicers_to_file(self):
        """
        save current time slicers to a file
        :return:
        """
        # Get splitters
        try:
            split_tup_list = self.ui.tableWidget_segments.get_splitter_list()
        except RuntimeError as e:
            GuiUtil.pop_dialog_error(self, str(e))
            return

        # pop a dialog for the name of the slicer
        file_filter = 'Data Files (*.dat);; All Files (*.*)'
        file_name = QtGui.QFileDialog.getOpenFileName(self, 'Time slicer file name', self.controller.get_working_dir(),
                                                      file_filter)
        if len(file_name) == 0:
            return

        # Call parent method
        if self._myParent is not None:
            # TODO/ISSUE/33 - Let _myParent to handle this! send a signal to parent with list!
            self.controller.save_time_slicers(split_tup_list, file_name)
        # END-IF

        return

    def get_slicers(self):
        """
        return the slicers as
        :return: a list of 3-tuple as start time, stop time relative to run start
        """
        return self.ui.tableWidget_segments.get_splitter_list()

    def write_table(self, slicers_list):
        """

        :param slicers_list:
        :return:
        """
        self.ui.tableWidget_segments.set_time_slicers(slicers_list)

        return
