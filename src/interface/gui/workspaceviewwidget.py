########################################################################
#
# General-purposed plotting window
#
########################################################################
from mantidipythonwidget import MantidIPythonWidget

from PyQt4 import QtCore, QtGui

from mplgraphicsview import MplGraphicsView
import ndav_widgets.NTableWidget as baseTable
import ndav_widgets.CustomizedTreeView as baseTree

from mantid.api import AnalysisDataService
import mantid.simpleapi

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class WorkspaceViewWidget(QtGui.QWidget):
    """ Class for general-purposed plot window
    """
    # reserved command
    Reserved_Command_List = ['plot', 'refresh', 'exit', 'vhelp', 'what']

    def __init__(self, parent=None):
        """ Init
        """
        import ui_WorkspacesView

        # call base
        QtGui.QWidget.__init__(self)

        # Parent & others
        self._myMainWindow = None
        self._myParent = parent

        # set up UI
        self.ui = ui_WorkspacesView.Ui_Form()
        self.ui.setupUi(self)

        self.ui.tableWidget_dataStructure.setup()
        self.ui.widget_ipython.set_main_application(self)

        # define event handling methods
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.do_plot_workspace)
        self.connect(self.ui.pushButton_toIPython, QtCore.SIGNAL('clicked()'),
                     self.do_write_to_console)
        self.connect(self.ui.pushButton_clear, QtCore.SIGNAL('clicked()'),
                     self.do_clear_canvas)
        self.connect(self.ui.pushButton_fitCanvas, QtCore.SIGNAL('clicked()'),
                     self.do_fit_canvas)

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

    def do_write_to_console(self):
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

    def execute_reserved_command(self, script):
        """
        override execute?
        :param script:
        :return:
        """
        script = script.strip()
        command = script.split()[0]

        print '[DB...BAT] Going to execute: ', script

        if command == 'plot':
            print 'run: ', script
            err_msg = self.plot(script)

        elif command == 'refresh':
            err_msg = self.refresh_workspaces()

        elif command == 'exit':
            self._myParent.close()
            # self.close()
            err_msg = None

        elif command == 'vhelp' or command == 'what':
            # output help
            err_msg = self.get_help_message()
        else:
            try:
                status, err_msg = self._myMainWindow.execute_command(script)
            except AssertionError as ass_err:
                status = False,
                err_msg = 'Failed to execute VDRIVE command due to %s.' % str(ass_err)
            # except KeyError as key_err:
            #     status = False
            #     err_msg = 'Failed to execute %s due to unrecognized key word: %s.' % (command, str(key_err))

            if status:
                err_msg = 'VDRIVE command %s is executed successfully.\n%s.' % (command, err_msg)
            else:
                err_msg = 'Failed to execute VDRIVE command %s failed due to %s.' % (command, err_msg)

        return err_msg

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
        print '[DB...Test Reserved] command = ', command, 'is reserved command'

        return command in self.Reserved_Command_List

    def plot(self, script):
        """

        :param script:
        :return:
        """
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
        # TODO/NOW/ISSUE/51 - Implement!

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
        # FIXME - This is a dirty shortcut because it is not suppose to access AnalysisDataService at this level
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



