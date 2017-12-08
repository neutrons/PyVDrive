from PyQt4 import QtCore, QtGui
import gui.GuiUtility as GuiUtility
import gui.ui_LiveDataGPPlotSetup_ui as dialog_ui
import gui.ui_LiveDataViewSetup_ui as SetupDialogUi


class LiveViewSetupDialog(QtGui.QDialog):
    """
    A dialog to set up the Live data viewing parameters
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        # call base
        super(LiveViewSetupDialog, self).__init__(parent)

        # my parent
        self._myParent = parent

        # UI
        self.ui = SetupDialogUi.Ui_Dialog()
        self.ui.setupUi(self)

        # define the event handlers
        self.connect(self.ui.pushButton_setRefreshRate, QtCore.SIGNAL('clicked()'),
                     self.do_set_refresh_rate)
        self.connect(self.ui.pushButton_setLiveUpdate, QtCore.SIGNAL('clicked()'),
                     self.do_set_acc_plot)
        self.connect(self.ui.pushButton_setupMix2D, QtCore.SIGNAL('clicked()'),
                     self.do_set_run_view)
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_browseGSS, QtCore.SIGNAL('clicked()'),
                     self.do_browse_van_gss)
        self.connect(self.ui.pushButton_loadGSS, QtCore.SIGNAL('clicked()'),
                     self.do_load_van_gss)

        self.connect(self.ui.radioButton_plotRun, QtCore.SIGNAL('toggled(bool)'),
                     self.toggle_options)

        # initialize some widget
        self.ui.radioButton_plotAcc.setChecked(True)
        self.ui.radioButton_plotRun.setChecked(False)

        return

    def do_browse_van_gss(self):
        """
        launch a dialog to find smoothed Vanadium GSAS file
        :return:
        """
        # get file name
        file_name = str(QtGui.QFileDialog.getOpenFileName(self, '/SNS/VULCAN', 'GSAS (*.gda'))
        # add the line information
        self.ui.lineEdit_vanGSSName.setText(file_name)

        return

    def do_load_van_gss(self):
        """Load smoothed vanadium from GSAS file
        :return:
        """
        # get file name
        file_name = str(self.ui.lineEdit_vanGSSName.text())

        # let parent window to load
        self._myParent.controller.load_smoothed_vanadium(file_name)

        # set message
        self.ui.textEdit_info.setText('{0} is loaded'.format(file_name))

        # append the new message to main window
        info = 'Vanadium: {0}'.format(file_name)
        self._myParent.set_info(info, append=True, insert_at_beginning=False)
        self._myParent.set_vanadium_norm(True, van_file_name=file_name)

        return

    def do_set_refresh_rate(self):
        """
        set the update/refresh rate in unit as second
        :return:
        """
        try:
            refresh_unit_time = int(str(self.ui.lineEdit_updateFreq.text()))
            self._myParent.set_refresh_rate(refresh_unit_time)
        except ValueError as value_err:
            raise RuntimeError('Update/refresh time step {0} cannot be parsed to an integer due to {1}.'
                               ''.format(self.ui.lineEdit_updateFreq.text(), value_err))

        return

    def do_set_acc_plot(self):
        """
        set the accumulation/update unit
        :return:
        """
        try:
            accum_time = int(str(self.ui.lineEdit_collectionPeriod.text()))
            self._myParent.set_accumulation_time(accum_time)
        except ValueError as value_err:
            raise RuntimeError('Accumulation time {0} cannot be parsed to an integer due to {1}.'
                               ''.format(str(self.ui.lineEdit_collectionPeriod.text()), value_err))

        return

    def do_set_run_view(self):
        """
        set up the parameters that are required for showing reduced run in 2D view
        :return:
        """
        try:
            max_time = int(str(self.ui.lineEdit_maxRunTime.text()))
            start_run = int(str(self.ui.lineEdit_run0.text()))

            self._myParent.set_accumulation_time(max_time)
            self._myParent.set_plot_run(True, start_run)

        except ValueError as value_err:
            raise RuntimeError('Unable to set up maximum accumulation time and '
                               'start run due to {0}'.format(value_err))

        return

    def do_quit(self):
        """
        quit the window
        :return:
        """
        self.close()

    def toggle_options(self):
        """
        toggle the widgets between long-run live update and short-run reduced data
        :return:
        """
        enable_group1 = self.ui.radioButton_plotAcc.isChecked()
        enable_group2 = self.ui.radioButton_plotRun.isChecked()

        # group 1
        self.ui.pushButton_setLiveUpdate.setEnabled(enable_group1)
        self.ui.lineEdit_maxRunTime.setEnabled(enable_group1)
        self.ui.lineEdit_collectionPeriod.setEnabled(enable_group1)

        # group 2
        self.ui.pushButton_setupMix2D.setEnabled(enable_group2)
        self.ui.lineEdit_run0.setEnabled(enable_group2)

        return


class SampleLogPlotSetupDialog(QtGui.QDialog):
    """ A dialog for user to choose the X-axis and Y-axis to plot
    """
    # define signal # x, y-list, y_side_list, (dmin, dmax) list, norm-van-list
    PlotSignal = QtCore.pyqtSignal(str, list, list, list, list)

    def __init__(self, parent=None):
        """ Initialization
        :param parent:
        """
        super(SampleLogPlotSetupDialog, self).__init__(parent)

        self.ui = dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # init widget
        self._init_widgets()

        # link
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply)

        # push buttons to set up
        self.connect(self.ui.pushButton_addPeakParam, QtCore.SIGNAL('clicked()'),
                     self.do_add_peak_param)
        self.connect(self.ui.pushButton_addSampleLog, QtCore.SIGNAL('clicked()'),
                     self.do_add_sample_log)

        # other parameters
        self.connect(self.ui.pushButton_remove, QtCore.SIGNAL('clicked()'),
                     self.do_remove_item)
        self.connect(self.ui.pushButton_clear, QtCore.SIGNAL('clicked()'),
                     self.do_clear_selected_items)
        self.connect(self.ui.pushButton_filterLog, QtCore.SIGNAL('clicked()'),
                     self.do_filter_sample_logs)

        # other class variable
        self._myControlWindow = parent  # real parent window launch this dialog
        if parent is not None:
            self.PlotSignal.connect(self._myControlWindow.plot_log_live)

        # a record for being selected
        self._selectedParameters = list()

        # keep a copy of sample logs added
        self._sampleLogsList = list()

        return

    def _init_widgets(self):
        """
        initialize widgets
        :return:
        """
        # set up the Axes
        self.ui.tableWidget_sampleLogs.setup()
        self.ui.tableWidget_sampleLogs.setColumnWidth(0, 300)

        self.ui.tableWidget_plotYAxis.setup()
        # self.ui.tableWidget_plotYAxis.setColumnWidth(0, 200)

        # peak calculation special
        self.ui.checkBox_normByVan.setChecked(True)
        self.ui.comboBox_peakY.clear()
        self.ui.comboBox_peakY.addItem('Peak Center')
        self.ui.comboBox_peakY.addItem('Peak Intensity')

        return

    def do_add_peak_param(self):
        """

        :return:
        """
        # blabla
        peak_type = str(self.ui.comboBox_peakY.currentText()).lower()

        if peak_type.count('intensity'):
            peak_type = 'intensity'
        elif peak_type.count('center'):
            peak_type = 'center'
        else:
            raise RuntimeError('Who knows')

        # side
        side_str = self.ui.comboBox_plotPeak.currentText()
        if side_str == 'Left':
            is_main = True
        else:
            is_main = False

        # check whether there is any item related to peak integration
        min_d_str = str(self.ui.lineEdit_minDPeakIntegrate.text())
        max_d_str = str(self.ui.lineEdit_dMaxPeakIntegrate.text())
        try:
            min_d = float(min_d_str)
            max_d = float(max_d_str)
        except ValueError as value_err:
            err_msg = 'Min-D "{0}" or/and Max-D "{1}" cannot be parsed as a float due to {2}' \
                      ''.format(min_d_str, max_d_str, value_err)
            GuiUtility.pop_dialog_error(self, err_msg)
            return

        norm_by_van = self.ui.checkBox_normByVan.isChecked()

        peak_info_str = '* Peak: {0}'.format(peak_type)

        self.ui.tableWidget_plotYAxis.add_peak_parameter(peak_info_str, is_main, min_d, max_d, norm_by_van)

        return

    def do_add_sample_log(self):
        """
        add sample log that is selected to the sample-log table
        :return:
        """
        # get log name
        try:
            sample_log_name_list, plot_side_list = self.ui.tableWidget_sampleLogs.get_selected_items()
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, str(run_err))
            return
        finally:
            # reset the chosen ones
            self.ui.tableWidget_sampleLogs.deselect_all_rows()

        # strip some information from input
        for index, log_name in enumerate(sample_log_name_list):
            # add to the table.  default to right axis
            self.ui.tableWidget_plotYAxis.add_log_item(log_name, plot_side_list[index])
        # END-FOR

        return

    def do_apply(self):
        """Apply setup
        :return:
        """
        # get x-axis name and y-axis name
        x_axis_name = str(self.ui.comboBox_X.currentText())

        # get the Y axis and check
        y_axis_name_list, is_main_list, peak_range_list, norm_by_van_list = \
            self.ui.tableWidget_plotYAxis.get_selected_items()
        if len(y_axis_name_list) == 0:
            GuiUtility.pop_dialog_error(self, 'Y-axis list is empty!')
            return
        elif len(y_axis_name_list) > 2:
            GuiUtility.pop_dialog_error(self, 'More than 2 items are selected to plot.  It is NOT OK.')
            return
        elif len(y_axis_name_list) == 2 and is_main_list[0] == is_main_list[1]:
            GuiUtility.pop_dialog_error(self, 'Two items cannot be on the same side of axis.')
            return

        # now it is the time to send message
        self.PlotSignal.emit(x_axis_name, y_axis_name_list, is_main_list, peak_range_list, norm_by_van_list)

        return

    def do_clear_selected_items(self):
        """
        clear all the selected items from table
        :return:
        """
        self.ui.tableWidget_plotYAxis.remove_all_rows()

        return

    def do_quit(self):
        """Quit without doing any operation
        :return:
        """
        self.close()

        return

    def do_filter_sample_logs(self):
        """
        blabla
        :return:
        """
        # get filter
        filter_string = str(self.ui.lineEdit_logFilter.text())
        case_sensitive = self.ui.checkBox_caseSensitive.isChecked()
        if not case_sensitive:
            filter_string = filter_string.lower()

        # clear the table
        self.ui.tableWidget_sampleLogs.remove_all_rows()

        # filter
        if len(filter_string) == 0:
            # reset sample log table to original state
            self.ui.tableWidget_sampleLogs.add_axis_items(self._sampleLogsList)
        else:
            # do filter
            filtered_list = list()
            for log_name in self._sampleLogsList:
                if case_sensitive:
                    log_name_proc = log_name
                else:
                    log_name_proc = log_name.lower()
                if filter_string in log_name_proc:
                    filtered_list.append(log_name)
            # END-FOR

            # set
            self.ui.tableWidget_sampleLogs.add_axis_items(filtered_list)
        # END-IF

        return

    def do_remove_item(self):
        """
        remove selected items from the table
        :return:
        """
        row_index_list = self.ui.tableWidget_plotYAxis.get_selected_rows(True)

        self.ui.tableWidget_plotYAxis.remove_rows(row_number_list=row_index_list)

        return

    def set_control_window(self, control_window):
        """
        set the controlling window
        :param control_window:
        :return:
        """
        assert control_window is not None, 'Control window cannot be None'

        # set control window and link
        self._myControlWindow = control_window
        self.PlotSignal.connect(control_window.plot_log_live)

        return

    def set_axis_options(self, y_axis_list, reset):
        """
        set the X-axis and Y-axis item list
        :param y_axis_list:
        :param reset:
        :return:
        """
        assert isinstance(y_axis_list, list), 'Y-axis items {0} must be given as a list but not ' \
                                              'a {1}.'.format(y_axis_list, type(y_axis_list))

        if reset:
            # remove all rows
            self.ui.tableWidget_sampleLogs.remove_all_rows()
            # clear the recorded list
            self._sampleLogsList = list()

        # add/append
        self.ui.tableWidget_sampleLogs.add_axis_items(y_axis_list)
        self._sampleLogsList.extend(y_axis_list)

        return
