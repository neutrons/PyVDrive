from PyQt4 import QtCore, QtGui
import gui.ui_LiveDataGPPlotSetup_ui as dialog_ui
import gui.ndav_widgets.NTableWidget as NTableWidget
import gui.GuiUtility as GuiUtility


class SampleLogPlotSetupDialog(QtGui.QDialog):
    """ A dialog for user to choose the X-axis and Y-axis to plot
    """
    # define signal
    PlotSignal = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        """ Initialization
        :param parent:
        """
        super(SampleLogPlotSetupDialog, self).__init__(parent)

        self.ui = dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # link
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply)

        # other class variable
        self._myControlWindow = parent  # real parent window launch this dialog
        if parent is not None:
            self.PlotSignal.connect(self._myControlWindow.plot_log_live)

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

    def set_axis_options(self, x_axis_list, y_axis_list):
        """
        set the X-axis and Y-axis item list
        :param x_axis_list:
        :param y_axis_list:
        :return:
        """
        assert isinstance(x_axis_list, list), 'blabla1'
        assert isinstance(y_axis_list, list), 'blabla2'

        self.ui.tableWidget_AxisX.add_axis_items(x_axis_list)
        self.ui.tableWidget_AxisY.add_axis_items(y_axis_list)

        return


class LogSelectorTable(NTableWidget):
    """ Extended table widget for show the K-shift vectors set to the output Fullprof file
    """
    # Table set up
    TableSetup = [('LogName', 'str'),
                  ('Select', 'checkbox')]

    def __init__(self, parent):
        """
        Initialization
        :param parent::

        :return:
        """
        # call super
        super(LogSelectorTable, self).__init__(parent)

        # column index of k-index
        self._iColAxisName = None
        self._iColSelected = None

        return

    def add_axis_items(self, items):
        """add axis items
        :param items:
        :return:
        """
        # check input
        assert isinstance(items, list), 'Items {0} must be given in a list but not a {1}.' \
                                        ''.format(items, type(items))

        # add
        for item_name in items:
            self.append_row([item_name, False])

        return

    def get_selected_item(self):
        """
        check all the rows to get the selected row
        :except: RuntimeError if there is zero or more than 1 rows are selected
        :return: item name of the row selected
        """
        row_numbers = self.get_selected_rows()
        if len(row_numbers) != 1:
            raise RuntimeError('{0}'.format(len(row_numbers)))

        return self.get_cell_value(row_numbers[0], self._iColAxisName)

    def setup(self):
        """ Set up the table
        :return:
        """
        self.init_setup(self.TableSetup)

        self._iColAxisName = self.TableSetup.index(('LogName', 'int'))
        self._iColSelected = self.TableSetup.index(('Select', 'checkbox'))

        return

