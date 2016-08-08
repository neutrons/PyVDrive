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

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class WorkspaceViewer(QtGui.QWidget):
    """ Class for general-purposed plot window
    """
    # reserved command
    Reserved_Command_List = ['plot', 'refresh', 'exit']

    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QWidget.__init__(self)

        # Parent & others
        self._myMainWindow = None
        self._myParent = parent

        # set up UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.tableWidget_dataStructure.setup()
        self.ui.widget_ipython.set_main_application(self)

        return

    def execute(self, script):
        """

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
            err_msg = self._myMainWindow.execute_command(script)

        return err_msg

    def is_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        command = script.strip().split()[0]

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
                self.ui.graphicsView_general.plot_workspace(ws_name)

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


class Ui_Form(object):
    """
    Ui form
    """
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(1175, 868)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tableWidget_dataStructure = WorkspaceTableWidget(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget_dataStructure.sizePolicy().hasHeightForWidth())
        self.tableWidget_dataStructure.setSizePolicy(sizePolicy)
        self.tableWidget_dataStructure.setObjectName(_fromUtf8("tableWidget_dataStructure"))
        self.tableWidget_dataStructure.setColumnCount(0)
        self.tableWidget_dataStructure.setRowCount(0)
        self.horizontalLayout.addWidget(self.tableWidget_dataStructure)
        self.graphicsView_general = WorkspaceGraphicView(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_general.sizePolicy().hasHeightForWidth())
        self.graphicsView_general.setSizePolicy(sizePolicy)
        self.graphicsView_general.setObjectName(_fromUtf8("graphicsView_general"))
        self.horizontalLayout.addWidget(self.graphicsView_general)
        self.treeView_plotControl = PlotControlTreeWidget(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeView_plotControl.sizePolicy().hasHeightForWidth())
        self.treeView_plotControl.setSizePolicy(sizePolicy)
        self.treeView_plotControl.setObjectName(_fromUtf8("tableView_workspaces"))
        self.horizontalLayout.addWidget(self.treeView_plotControl)
        self.verticalLayout.addWidget(self.groupBox)
        self.widget_ipython = MantidIPythonWidget(Form)
        self.widget_ipython.setObjectName(_fromUtf8("widget_ipython"))
        self.verticalLayout.addWidget(self.widget_ipython)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.groupBox.setTitle(_translate("Form", "Workspaces", None))


