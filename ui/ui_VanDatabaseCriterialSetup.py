# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_VanDatabaseCriterialSetup.ui'
#
# Created: Wed Feb 18 16:08:44 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(730, 385)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(730, 300))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tableWidgetTable1 = QtGui.QTableWidget(self.centralwidget)
        self.tableWidgetTable1.setMinimumSize(QtCore.QSize(451, 221))
        self.tableWidgetTable1.setRowCount(10)
        self.tableWidgetTable1.setColumnCount(5)
        self.tableWidgetTable1.setObjectName(_fromUtf8("tableWidgetTable1"))
        self.horizontalLayout.addWidget(self.tableWidgetTable1)
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QtCore.QSize(201, 250))
        self.groupBox.setMaximumSize(QtCore.QSize(201, 201))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.pushButtonSelectAll = QtGui.QPushButton(self.groupBox)
        self.pushButtonSelectAll.setObjectName(_fromUtf8("pushButtonSelectAll"))
        self.verticalLayout.addWidget(self.pushButtonSelectAll)
        self.pushButtonDeSelectAll = QtGui.QPushButton(self.groupBox)
        self.pushButtonDeSelectAll.setObjectName(_fromUtf8("pushButtonDeSelectAll"))
        self.verticalLayout.addWidget(self.pushButtonDeSelectAll)
        self.pushButtonRemoveEmptyRows = QtGui.QPushButton(self.groupBox)
        self.pushButtonRemoveEmptyRows.setMinimumSize(QtCore.QSize(181, 23))
        self.pushButtonRemoveEmptyRows.setObjectName(_fromUtf8("pushButtonRemoveEmptyRows"))
        self.verticalLayout.addWidget(self.pushButtonRemoveEmptyRows)
        self.pushButtonDeleteSelectedRows = QtGui.QPushButton(self.groupBox)
        self.pushButtonDeleteSelectedRows.setMinimumSize(QtCore.QSize(181, 23))
        self.pushButtonDeleteSelectedRows.setObjectName(_fromUtf8("pushButtonDeleteSelectedRows"))
        self.verticalLayout.addWidget(self.pushButtonDeleteSelectedRows)
        self.pushButtonAddRows = QtGui.QPushButton(self.groupBox)
        self.pushButtonAddRows.setMinimumSize(QtCore.QSize(181, 23))
        self.pushButtonAddRows.setObjectName(_fromUtf8("pushButtonAddRows"))
        self.verticalLayout.addWidget(self.pushButtonAddRows)
        self.pushButtonMoveRowsUp = QtGui.QPushButton(self.groupBox)
        self.pushButtonMoveRowsUp.setMinimumSize(QtCore.QSize(181, 23))
        self.pushButtonMoveRowsUp.setObjectName(_fromUtf8("pushButtonMoveRowsUp"))
        self.verticalLayout.addWidget(self.pushButtonMoveRowsUp)
        self.pushButtonMoveRowsDown = QtGui.QPushButton(self.groupBox)
        self.pushButtonMoveRowsDown.setMinimumSize(QtCore.QSize(181, 23))
        self.pushButtonMoveRowsDown.setObjectName(_fromUtf8("pushButtonMoveRowsDown"))
        self.verticalLayout.addWidget(self.pushButtonMoveRowsDown)
        self.horizontalLayout.addWidget(self.groupBox)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 730, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.tableWidgetTable1, QtCore.SIGNAL(_fromUtf8("clicked(QModelIndex)")), self.tableWidgetTable1.update)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "PyQt Table Example", None))
        self.groupBox.setTitle(_translate("MainWindow", "Table Controls", None))
        self.pushButtonSelectAll.setText(_translate("MainWindow", "Select All", None))
        self.pushButtonDeSelectAll.setText(_translate("MainWindow", "De-Select All", None))
        self.pushButtonRemoveEmptyRows.setText(_translate("MainWindow", "Remove Empty Rows", None))
        self.pushButtonDeleteSelectedRows.setText(_translate("MainWindow", "Delete Selected Row(s)", None))
        self.pushButtonAddRows.setText(_translate("MainWindow", "Add Row(s)", None))
        self.pushButtonMoveRowsUp.setText(_translate("MainWindow", "Move Selected Row(s) Up", None))
        self.pushButtonMoveRowsDown.setText(_translate("MainWindow", "Move Selected Row(s) Down", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionAbout.setText(_translate("MainWindow", "About", None))

