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
        # blabla
        file_name = str(QtGui.QFileDialog.getOpenFileName(self, '/SNS/VULCAN'))
        self.ui.lineEdit_vanGSSName.setText(file_name)

    def do_load_van_gss(self):
        """
        blabla
        :return:
        """
        file_name = str(self.ui.lineEdit_vanGSSName.text())

        self._myParent._controller.load_smoothed_vanadium(file_name)

        self.ui.textEdit_info.setText('{0} is loaded'.format(file_name))
        self._myParent.ui.label_info.setText('Vanadium: {0}'.format(file_name))

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
    # define signal
    PlotSignal = QtCore.pyqtSignal(str, str)
    PeakIntegrateSignal = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        """ Initialization
        :param parent:
        """
        super(SampleLogPlotSetupDialog, self).__init__(parent)

        self.ui = dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # init widget
        self.ui.tableWidget_AxisX.setup()
        self.ui.tableWidget_AxisY.setup()

        # link
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply)

        # other class variable
        self._myControlWindow = parent  # real parent window launch this dialog
        if parent is not None:
            self.PlotSignal.connect(self._myControlWindow.plot_log_live)
            self.PeakIntegrateSignal.connect(self._myControlWindow.integrate_peak_live)

        return

    def do_quit(self):
        """Quit without doing any operation
        :return:
        """
        self.close()

        return

    def do_apply(self):
        """Apply setup
        :return:
        """
        # get X-axis item
        try:
            x_axis_name = self.ui.tableWidget_AxisX.get_selected_item()
        except RuntimeError as run_err:
            err_msg = 'One and only one item can be selected for X-axis. Now {0} is selected.' \
                      ''.format(run_err)
            GuiUtility.pop_dialog_error(self, err_msg)
            return

        # high priority to integrate peaks
        if self.ui.checkBox_integratePeak.isChecked():
            # set up peak integration
            min_d_str = str(self.ui.lineEdit_minDPeakIntegrate.text())
            max_d_str = str(self.ui.lineEdit_dMaxPeakIntegrate.text())
            try:
                min_d = float(min_d_str)
                max_d = float(max_d_str)
            except ValueError as value_err:
                raise RuntimeError('Min-D {0} or/and Max-D {1} cannot be parsed as a float due to {2}'
                                   ''.format(min_d_str, max_d_str, value_err))

            self.PeakIntegrateSignal.emit(min_d, max_d)

        else:
            # get Y-axis item
            try:
                y_axis_name = self.ui.tableWidget_AxisY.get_selected_item()
            except RuntimeError as run_err:
                err_msg = 'One and only one item can be selected for Y-axis. Now {0} is selected.' \
                          ''.format(run_err)
                GuiUtility.pop_dialog_error(self, err_msg)
                return

            # send signal to parent window to plot
            self.PlotSignal.emit(x_axis_name, y_axis_name)
        # END-IF-ELSE

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

    def set_axis_options(self, x_axis_list, y_axis_list, reset):
        """
        set the X-axis and Y-axis item list
        :param x_axis_list:
        :param y_axis_list:
        :param reset:
        :return:
        """
        assert isinstance(x_axis_list, list), 'blabla1'
        assert isinstance(y_axis_list, list), 'blabla2'

        if reset:
            self.ui.tableWidget_AxisX.remove_all_rows()
            self.ui.tableWidget_AxisY.remove_all_rows()

        self.ui.tableWidget_AxisX.add_axis_items(x_axis_list)
        self.ui.tableWidget_AxisY.add_axis_items(y_axis_list)

        return
