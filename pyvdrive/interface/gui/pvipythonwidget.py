# iPython widgets including a ipython console, a workspace table and a figure canvas
# This QMainWindow is implemented in order to use WorkspaceViewWidget, which contains
# IPython console, table view and figure inside, while it cannot be called directly
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QSizePolicy, QLabel, QMenuBar, QStatusBar, QToolBar
    from PyQt5 import QtCore
except ImportError:
    from PyQt4.QtGui import QMainWindow, QWidget, QGridLayout, QSizePolicy, QLabel, QMenuBar, QStatusBar, QToolBar
    from PyQt4 import QtCore
from pyvdrive.interface.gui.workspaceviewwidget import WorkspaceViewWidget

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s  # noqa: E731


class IPythonWorkspaceViewer(QMainWindow):
    """Class for workspace viewer controlled by IPython
    """
    def __init__(self, parent=None):
        """
        initialization including setting up UI
        :param parent:
        """
        super(IPythonWorkspaceViewer, self).__init__(parent)

        # set up
        self.setObjectName(_fromUtf8("MainWindow"))
        self.resize(1600, 1200)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.widget = WorkspaceViewWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.gridLayout.addWidget(self.widget, 1, 0, 1, 1)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1005, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        self.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(self)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        # self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

        return
