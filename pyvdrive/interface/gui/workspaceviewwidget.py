########################################################################
#
# General-purposed plotting window
#
########################################################################
from mantidipythonwidget import MantidIPythonWidget

try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QWidget
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui

from mplgraphicsview import MplGraphicsView
import ndav_widgets.NTableWidget as baseTable
import ndav_widgets.CustomizedTreeView as baseTree
from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
# from pyvdrive.interface.gui.workspaceviewwidget import WorkspaceTableWidget
# from pyvdrive.interface.gui.workspaceviewwidget import WorkspaceGraphicView

from mantid.api import AnalysisDataService
import mantid.simpleapi
import os

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class WorkspaceViewWidget(QWidget):
    """ Class for general-purposed plot window
    """
    # reserved command
    Reserved_Command_List = ['plot', 'refresh', 'exit', 'vhelp', 'what']

    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QWidget.__init__(self)

        # Parent & others
        self._myMainWindow = None
        self._myParent = parent

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "WorkspacesView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        self.ui.tableWidget_dataStructure.setup()
        self.ui.widget_ipython.set_main_application(self)

        # define event handling methods
        self.ui.pushButton_plot.clicked.connect(self.do_plot_workspace)
        self.ui.pushButton_toIPython.clicked.connect(self.do_write_workspace_name)
        self.ui.pushButton_toIPythonMtd.clicked.connect(self.do_write_workspace_instance)
        self.ui.pushButton_toIPythonAssign.clicked.connect(self.do_assign_workspace)
        self.ui.pushButton_clear.clicked.connect(self.do_clear_canvas)
        self.ui.pushButton_fitCanvas.clicked.connect(self.do_fit_canvas)

        return

    def _promote_widgets(self):
        """ promote widgets
        :return:
        """
        tableWidget_dataStructure_layout = QVBoxLayout()
        self.ui.frame_tableWidget_dataStructure.setLayout(tableWidget_dataStructure_layout)
        self.ui.tableWidget_dataStructure = WorkspaceTableWidget(self)
        tableWidget_dataStructure_layout.addWidget(self.ui.tableWidget_dataStructure)

        graphicsView_general_layout = QVBoxLayout()
        self.ui.frame_graphicsView_general.setLayout(graphicsView_general_layout)
        self.ui.graphicsView_general = WorkspaceGraphicView(self)
        graphicsView_general_layout.addWidget(self.ui.graphicsView_general)

        widget_ipython_layout = QVBoxLayout()
        self.ui.frame_widget_ipython.setLayout(widget_ipython_layout)
        self.ui.widget_ipython = MantidIPythonWidget(self)
        widget_ipython_layout.addWidget(self.ui.widget_ipython)

        return

    def do_clear_canvas(self):
        """
        clear the plots on the canvas
        :return:
        """
        self.ui.graphicsView_general.reset_canvas()

        return

    def do_fit_canvas(self):
        """
        resize the canvas to make the plots fit (0 to 5% above max value)
        :return:
        """
        self.ui.graphicsView_general.resize_canvas(0, 1.05)

        return

    def do_plot_workspace(self):
        """
        plot selected workspace
        :return:
        """
        # get selected workspace name
        selected_workspace_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # get the data from main application
        # controller = self._myMainWindow.get_controller()

        for workspace_name in selected_workspace_name_list:
            # data_set = controller.get_data_from_workspace(workspace_name)
            self.ui.graphicsView_general.plot_workspace(workspace_name)

        return

    def do_assign_workspace(self):
        """
        write the workspace name to IPython console with assign the workspace instance to a variable
        :return:
        """
        # get workspace name
        ws_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # output string
        ipython_str = ''
        for ws_name in ws_name_list:
            ipython_str += 'ws_ = mtd["{0}"] '.format(ws_name)

        # export the ipython
        self.ui.widget_ipython.write_command(ipython_str)

        return

    def do_write_workspace_name(self):
        """
        write the workspace name to IPython console
        :return:
        """
        # get workspace name
        ws_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # output string
        ipython_str = ''
        for ws_name in ws_name_list:
            ipython_str += '"{0}"    '.format(ws_name)

        # export the ipython
        self.ui.widget_ipython.write_command(ipython_str)

        return

    def do_write_workspace_instance(self):
        """
        write the workspace name to IPython console
        :return:
        """
        # get workspace name
        ws_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # output string
        ipython_str = ''
        for ws_name in ws_name_list:
            ipython_str += 'mtd["{0}"] '.format(ws_name)

        # export the ipython
        self.ui.widget_ipython.write_command(ipython_str)

        return

    def execute_reserved_command(self, script):
        """ Execute command!
        :param script:
        :return:
        """
        script = script.strip()
        command = script.split(',')[0]

        print '[INFO] Executing reserved command: {}'.format(script)

        if command == 'plot':
            exec_message = self.plot(script)

        elif command == 'refresh':
            exec_message = self.refresh_workspaces()

        elif command == 'exit':
            self._myParent.close()
            # self.close()
            exec_message = None

        elif command == 'vhelp' or command == 'what':
            # output help
            exec_message = self.get_help_message()

        else:
            # Reserved VDRIVE-IDL command
            status, cmd_msg = self._myMainWindow.execute_command(script)
            # assertion error is not to be caught as it reflects coding error

            if status:
                exec_message = 'VDRIVE command {} is executed successfully ({}).'.format(command, cmd_msg)
            else:
                exec_message = 'VDRIVE command {} is failed to execute due to {}.'.format(command, cmd_msg)

        # ENDIF

        # TODO - 20181214 - More information to plainTextEdit_info - Refs #138
        # TODO            - update both plain text editors
        # TODO            - Use color and font to notify general information, warning and error
        self.ui.plainTextEdit_info.appendPlainText(exec_message)
        self.ui.plainTextEdit_loggingHistory.appendPlainText(exec_message)

        return exec_message

    @staticmethod
    def get_command_help(command):
        """
        get a help line for a specific command
        :param command:
        :return:
        """
        if command == 'plot':
            help_str = 'Plot a workspace.  Example: plot <workspace name>'

        elif command == 'refresh':
            help_str = 'Refresh the graph above.'

        elif command == 'exit':
            help_str = 'Exist the application.'

        elif command == 'vhelp' or command == 'what':
            # output help
            help_str = 'Get help.'

        else:
            help_str = 'Reserved VDRIVE command.  Run> %s' % command

        return help_str

    def get_help_message(self):
        """

        :return:
        """
        message = 'LAVA Reserved commands:\n'\

        for command in sorted(self.Reserved_Command_List):
            message += '%-15s: %s\n' % (command, self.get_command_help(command))

        return message

    def is_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        command = script.strip().split(',')[0].strip()

        is_reserved = command in self.Reserved_Command_List
        if is_reserved:
            print ('[DB...INFO] command: {} is reserved'.format(command))

        return is_reserved

    def plot(self, script):
        """

        :param script:
        :return:
        """
        # TODO - 20181215 - clean this section
        terms = script.split()

        if len(terms) == 1:
            # no given option, plot selected workspace
            return 'Not implemented yet'

        elif terms[1] == 'clear':
            # clear canvas
            self.ui.graphicsView_general.clear_all_lines()

        else:
            # plot workspace
            for i_term in range(1, len(terms)):
                ws_name = terms[i_term]
                try:
                    self.ui.graphicsView_general.plot_workspace(ws_name)
                except KeyError as key_err:
                    return str(key_err)

        return ''

    def process_workspace_change(self, diff_set):
        """

        :param diff_set:
        :return:
        """
        # TODO/NOW/ISSUE/51 - 20181214 - Implement!

        return

    def refresh_workspaces(self):
        """

        :return:
        """
        workspace_names = AnalysisDataService.getObjectNames()

        self.ui.tableWidget_dataStructure.remove_all_rows()
        error_message = ''
        for ws_name in workspace_names:
            try:
                self.ui.tableWidget_dataStructure.add_workspace(ws_name)
            except Exception as ex:
                error_message += 'Unable to add %s to table due to %s.\n' % (ws_name, str(ex))
        # END-FOR

        return error_message

    def set_main_window(self, main_window):
        """
        Set up the main window which generates this window
        :param main_window:
        :return:
        """
        # check
        assert main_window is not None
        try:
            main_window.get_reserved_commands
        except AttributeError as att_err:
            raise AttributeError('Parent window does not have required method get_reserved_command. FYI: {0}'
                                 ''.format(att_err))

        # set
        self._myMainWindow = main_window
        reserved_command_list = main_window.get_reserved_commands()
        self.Reserved_Command_List.extend(reserved_command_list)

        return


class PlotControlTreeWidget(baseTree.CustomizedTreeView):
    """

    """
    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        self._myParent = parent
        baseTree.CustomizedTreeView.__init__(self, None)

        return


class WorkspaceGraphicView(MplGraphicsView):
    """

    """
    def __init__(self, parent):
        """

        :param parent:
        """
        MplGraphicsView.__init__(self, None)

        # class variable
        self._rangeX = (0, 1.)
        self._rangeY = (0, 1.)

        return

    def plot_workspace(self, workspace_name):
        """

        :param workspace_name:
        :return:
        """
        # TODO - 20181214 - New requests:
        # TODO           1. Better label including X-unit, Legend (bank, # bins) and title (workspace name)
        # TODO           2. Use auto color
        # TODO           3. Use over-plot to compare
        # TODO           4. Change tab: ui.tabWidget_table_view
        # FIXME   -      This is a dirty shortcut because it is not suppose to access AnalysisDataService at this level

        ws = AnalysisDataService.retrieve(workspace_name)
        mantid.simpleapi.ConvertToPointData(InputWorkspace=ws, OutputWorkspace='temp_ws')
        point_ws = AnalysisDataService.retrieve('temp_ws')

        # get X and Y
        vec_x = point_ws.readX(0)
        vec_y = point_ws.readY(0)

        # get X and Y's range
        min_x = min(self._rangeX[0], vec_x[0])
        max_x = max(self._rangeX[1], vec_x[-1])

        min_y = min(self._rangeY[0], min(vec_y))
        max_y = max(self._rangeY[1], max(vec_y))

        self._rangeX = (min_x, max_x)
        self._rangeY = (min_y, max_y)

        # plot
        self.add_plot_1d(vec_x, vec_y)

        return

    def resize_canvas(self, y_min, y_max_ratio):
        """

        :param y_min:
        :param y_max_ratio:
        :return:
        """
        y_max = self._rangeY[1] * y_max_ratio

        self.setXYLimit(self._rangeX[0], self._rangeX[1], y_min, y_max)

        return

    def reset_canvas(self):
        """
        reset the canvas by removing all lines and registered values
        :return:
        """
        self.clear_all_lines()

        self._rangeX = (0., 1.)
        self._rangeY = (0., 1.)

        self.setXYLimit(0., 1., 0., 1.)

        return

    @staticmethod
    def setInteractive(status):
        """
        It is a native method of QtCanvas.  It is not used in MplGraphicView at all.
        But the auto-generated python file from .ui file have this method added anyhow.
        :param status:
        :return:
        """
        return


class WorkspaceTableWidget(baseTable.NTableWidget):
    """
    Table Widget for workspaces
    """
    SetupList = [('Workspace', 'str'),
                 ('', 'checkbox')]

    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        baseTable.NTableWidget.__init__(self, None)

    def setup(self):
        self.init_setup(self.SetupList)
        self.setColumnWidth(0, 360)
        return

    def add_workspace(self, ws_name):
        """

        :param ws_name:
        :return:
        """
        self.append_row([ws_name, False])

        return

    def get_selected_workspaces(self):
        """
        get the names of workspace in the selected rows
        :return:
        """
        selected_rows = self.get_selected_rows(True)

        print '[DB...BAT] selected rows: ', selected_rows

        ws_name_list = list()
        for i_row in selected_rows:
            ws_name = self.get_cell_value(i_row, 0)
            ws_name_list.append(ws_name)

        return ws_name_list



