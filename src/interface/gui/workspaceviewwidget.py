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

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class WorkspaceViewWidget(QtGui.QWidget):
    """ Class for general-purposed plot window
    """
    # reserved command
    Reserved_Command_List = ['plot', 'refresh', 'exit']

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

        return

    def execute_reserved_command(self, script):
        """
        override execute?
        :param script:
        :return:
        """
        script = script.strip()
        command = script.split()[0]

        if command == 'plot':
            print 'run: ', script
            err_msg = self.plot(script)

        elif command == 'refresh':
            err_msg = self.refresh_workspaces()

        elif command == 'exit':
            self._myParent.close()
            # self.close()
            err_msg = None

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

    def is_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        command = script.strip().split(',')[0].strip()
        print '[DB...Test Reserved] command = ',command

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

    def refresh_workspaces(self):
        """

        :return:
        """
        workspace_names = AnalysisDataService.getObjectNames()

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
            raise AttributeError('Parent window does not have required method get_reserved_command')

        # set
        self._myMainWindow = main_window

        self.Reserved_Command_List.extend(main_window.get_reserved_commands())

        return


class PlotControlTreeWidget(baseTree.CustomizedTreeView):
    """

    """
    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
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

        return

    def plot_workspace(self, workspace_name):
        """

        :param workspace_name:
        :return:
        """
        ws = AnalysisDataService.retrieve(workspace_name)

        vec_x = ws.readX(0)
        vec_y = ws.readY(0)

        self.add_plot_1d(vec_x, vec_y)


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



