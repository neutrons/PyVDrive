from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_ManualSlicerTable_ui
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

        self.ui = gui.ui_ManualSlicerTable_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self._init_widgets()

        # define widgets' event handling
        self.ui.pushButton_selectAll.clicked.connect(self.do_select_all_rows)

        self.ui.pushButton_expand2ndLevelChop.clicked.connect(self.do_expand_slicers)

        self.ui.pushButton_applyTimeSegs.clicked.connect(self.do_apply_slicers)

        self.ui.pushButton_saveTimeSegs.clicked.connect(self.do_save_slicers_to_file)

        self.ui.pushButton_loadSlicerFromFile.clicked.connect(self.do_load_slicers_from_file)

        self.ui.pushButton_hide.clicked.connect(self.do_hide_window)

        self.ui.pushButton_deselectAll.clicked.connect(self.do_set_target)

        # self.connect(self.ui.pushButton_selectAll, QtCore.SIGNAL('clicked()'),
        #              self.do_select_all_rows)
        #
        # self.connect(self.ui.pushButton_expand2ndLevelChop, QtCore.SIGNAL('clicked()'),
        #              self.do_expand_slicers)
        #
        # self.connect(self.ui.pushButton_applyTimeSegs, QtCore.SIGNAL('clicked()'),
        #              self.do_apply_slicers)
        #
        # self.connect(self.ui.pushButton_saveTimeSegs, QtCore.SIGNAL('clicked()'),
        #              self.do_save_slicers_to_file)
        #
        # self.connect(self.ui.pushButton_loadSlicerFromFile, QtCore.SIGNAL('clicked()'),
        #              self.do_load_slicers_from_file)
        #
        # self.connect(self.ui.pushButton_hide, QtCore.SIGNAL('clicked()'),
        #              self.do_hide_window)
        #
        # self.connect(self.ui.pushButton_deselectAll, QtCore.SIGNAL('clicked()'),
        #              self.do_set_target)

        # FIXME / FUTURE : it is not well defined to remove a slicer from table and reflected to pickers on plotting
        # self.connect(self.ui.pushButton_deleteSlicer, QtCore.SIGNAL('clicked()'),
        #              self.do_delete_slicer)
        self.ui.pushButton_deleteSlicer.setEnabled(False)

        # define handler to signals
        # TODO/ISSUE/NEXT - Implement this

        return

    def _init_widgets(self):
        """
        initialize widgets
        :return:
        """
        # slice segments table
        self.ui.tableWidget_segments.setup()

        # radio buttons
        self.ui.radioButton_timeStep.setChecked(True)

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
            self._myParent.generate_manual_slicer(split_tup_list, slicer_name=slicer_name)
        # END-IF

        return

    def do_delete_slicer(self):
        """ blabla
        """
        selected_rows = self.ui.tableWidget_segments.get_selected_rows(True)
        self.ui.tableWidget_segments.delete_rows(selected_rows)

        return

    def do_expand_slicers(self):
        """
        expand the selected slicers as the second-level choppers
        :return:
        """
        # get the selected slicers
        selected_rows = self.ui.tableWidget_segments.get_selected_rows(True)
        if len(selected_rows) == 0:
            GuiUtil.pop_dialog_information(self, 'No splitter (row) in the table is selected to expand.')
            return

        # get the slicers
        slicer_list = list()
        for row_index in sorted(selected_rows):
            slicer = self.ui.tableWidget_segments.get_splitter(row_index)
            slicer_list.append((row_index, slicer))
        # END-FOR

        # sort the slicers in reverse order in order to replace in the table
        slicer_list.sort(reverse=True)

        # get the slicing setup
        if self.ui.radioButton_timeStep.isChecked():
            # split by constant time step
            try:
                time_step = float(str(self.ui.lineEdit_timeStep.text()))
                log_step = None
            except ValueError:
                GuiUtil.pop_dialog_error(self, 'Time step {0} cannot be converted to float.'
                                         ''.format(self.ui.lineEdit_timeStep.text()))
                return

        elif self.ui.radioButton_logValueStep.isChecked():
            # split by constant log step
            try:
                time_step = None
                log_step = float(str(self.ui.lineEdit_logValueStepLevel2.text()))
            except ValueError:
                GuiUtil.pop_dialog_error(self, 'Log step {0} cannot be converted to float.'
                                               ''.format(self.ui.lineEdit_logValueStepLevel2.text()))
                return

        else:
            raise NotImplementedError('One of split by time step or split by log value step must be chosen.')

        # TODO/ISSUE/FUTURE
        if log_step is not None:
            raise NotImplementedError('It has not been implemented yet to split further by log value.')

        # expand
        for row_index, splitter in slicer_list:
            # get the splitter
            if time_step is not None:
                # split by log step
                new_splitter_list = self.generate_time_splitters(splitter, time_step)
            else:
                # log_step is not None:
                new_splitter_list = self._myParent.get_controller().generate_log_splitters(workspace_name,
                                                                                           splitter, log_step)
            # END-IF-ELSE

            # replace the selected splitter by the new splitters
            self.ui.tableWidget_segments.replace_splitter(row_index, new_splitter_list)
        # END-FOR

        return

    def do_hide_window(self):
        """

        :return:
        """
        self.setHidden(True)

        return

    def do_load_slicers_from_file(self):
        """
        Load data slicers from a csv-like file
        :return:
        """
        self._myParent.do_import_slicer_file()

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
        file_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Time slicer file name',
                                                          self.controller.get_working_dir(),
                                                          file_filter))
        if len(file_name) == 0:
            return

        # Call parent method
        if self._myParent is not None:
            # TODO/ISSUE/33/NOW - Let _myParent to handle this! send a signal to parent with list!
            status, err_msg = self.controller.save_time_slicers(split_tup_list, file_name)
            if not status:
                GuiUtil.pop_dialog_error(self, err_msg)
                return
        # END-IF

        return

    def do_select_all_rows(self):
        """
        select or de-select all rows
        :return:
        """
        if str(self.ui.pushButton_selectAll.text()) == 'Select All':
            self.ui.tableWidget_segments.select_all_rows(True)
            self.ui.pushButton_selectAll.setText('Deselect All')
        elif str(self.ui.pushButton_selectAll.text()) == 'Deselect All':
            self.ui.tableWidget_segments.select_all_rows(False)
            self.ui.pushButton_selectAll.setText('Select All')
        else:
            raise RuntimeError('Select button with text {0} is wrong!'.format(str(self.ui.pushButton_selectAll.text())))

        return

    def do_set_target(self):
        """
        set the target workspace/index to the slicers in case some of them will be merged
        :return:
        """
        # check whether any rows are selected
        row_list = self.ui.tableWidget_segments.get_selected_rows(True)
        if len(row_list) == 0:
            GuiUtil.pop_dialog_information(self, 'No row is selected to set target.')
            return

        # get the name of the target
        # pop a dialog for the name of the slicer
        target, status = QtGui.QInputDialog.getText(self, 'Input Target',
                                                    'Enter chopping target for selected rows:')
        # return if rejected with
        if status is False:
            return
        else:
            target = str(target)

        self.ui.tableWidget_segments.rename_chop_target(row_list, target)

        return

    def do_picker_process(self):
        """
        Process pickers by sorting and fill the stop time
        :return:
        """
        # TODO/ISSUE/33 - This method will be modified to an event-handling method for picker updating
        # Deselect all rows
        num_rows = self.ui.tableWidget_segments.rowCount()
        for i_row in xrange(num_rows):
            self.ui.tableWidget_segments.select_row(i_row, False)

        # Sort by start time
        self.ui.tableWidget_segments.sort_by_start_time()

        # Fill the stop by time by next star time
        self.ui.tableWidget_segments.fill_stop_time()

        return

    @staticmethod
    def generate_time_splitters(splitter, time_step):
        """
        generate a list of splitters by time
        :param splitter:
        :param time_step:
        :return:
        """
        # check input
        assert not isinstance(splitter, str), 'Splitter cannot be string.'
        assert len(splitter) == 3, 'A splitter {0} must have 3 terms but not {1}.' \
                                   ''.format(splitter, len(splitter))
        assert isinstance(time_step, float), 'Time step must be a float.'

        start_time = splitter[0]
        stop_time = splitter[1]
        target = splitter[2]

        num_child_splitters = int((stop_time - start_time) / time_step) + 1
        child_splitters = list()
        for i_child in range(num_child_splitters):
            start_i = float(i_child) * time_step + start_time
            if start_i >= stop_time:
                break
            stop_i = min(start_i + time_step, stop_time)
            target_i = '{0}s{1}'.format(target, i_child)
            child_splitters.append((start_i, stop_i, target_i))
        # END-FOR

        return child_splitters

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
