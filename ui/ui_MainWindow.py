# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_MainWindow.ui'
#
# Created: Tue Feb 24 11:46:33 2015
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
        MainWindow.resize(963, 769)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tableWidget_generalInfo = QtGui.QTableWidget(self.centralwidget)
        self.tableWidget_generalInfo.setObjectName(_fromUtf8("tableWidget_generalInfo"))
        self.tableWidget_generalInfo.setColumnCount(0)
        self.tableWidget_generalInfo.setRowCount(0)
        self.gridLayout_2.addWidget(self.tableWidget_generalInfo, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 963, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuVDrive_2_0 = QtGui.QMenu(self.menubar)
        self.menuVDrive_2_0.setObjectName(_fromUtf8("menuVDrive_2_0"))
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuReduction = QtGui.QMenu(self.menubar)
        self.menuReduction.setObjectName(_fromUtf8("menuReduction"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.dock_ = QtGui.QDockWidget(MainWindow)
        self.dock_.setObjectName(_fromUtf8("dock_"))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.gridLayout = QtGui.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.treeWidget_Project = QtGui.QTreeWidget(self.dockWidgetContents)
        self.treeWidget_Project.setObjectName(_fromUtf8("treeWidget_Project"))
        self.horizontalLayout.addWidget(self.treeWidget_Project)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.dock_.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dock_)
        self.action_OpenProject = QtGui.QAction(MainWindow)
        self.action_OpenProject.setObjectName(_fromUtf8("action_OpenProject"))
        self.actionClose = QtGui.QAction(MainWindow)
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.action_SaveProject = QtGui.QAction(MainWindow)
        self.action_SaveProject.setObjectName(_fromUtf8("action_SaveProject"))
        self.actionSave_As = QtGui.QAction(MainWindow)
        self.actionSave_As.setObjectName(_fromUtf8("actionSave_As"))
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionNewReduction = QtGui.QAction(MainWindow)
        self.actionNewReduction.setObjectName(_fromUtf8("actionNewReduction"))
        self.actionSave_Setup = QtGui.QAction(MainWindow)
        self.actionSave_Setup.setObjectName(_fromUtf8("actionSave_Setup"))
        self.actionFile_New_Reduction = QtGui.QAction(MainWindow)
        self.actionFile_New_Reduction.setObjectName(_fromUtf8("actionFile_New_Reduction"))
        self.actionAnalysis_Project = QtGui.QAction(MainWindow)
        self.actionAnalysis_Project.setObjectName(_fromUtf8("actionAnalysis_Project"))
        self.actionReduction_NewSetup = QtGui.QAction(MainWindow)
        self.actionReduction_NewSetup.setObjectName(_fromUtf8("actionReduction_NewSetup"))
        self.actionDelete = QtGui.QAction(MainWindow)
        self.actionDelete.setObjectName(_fromUtf8("actionDelete"))
        self.actionLoad_Setup = QtGui.QAction(MainWindow)
        self.actionLoad_Setup.setObjectName(_fromUtf8("actionLoad_Setup"))
        self.actionReset = QtGui.QAction(MainWindow)
        self.actionReset.setObjectName(_fromUtf8("actionReset"))
        self.actionLog_Window = QtGui.QAction(MainWindow)
        self.actionLog_Window.setCheckable(True)
        self.actionLog_Window.setObjectName(_fromUtf8("actionLog_Window"))
        self.actionFile_New = QtGui.QAction(MainWindow)
        self.actionFile_New.setObjectName(_fromUtf8("actionFile_New"))
        self.actionAdd_Runs = QtGui.QAction(MainWindow)
        self.actionAdd_Runs.setObjectName(_fromUtf8("actionAdd_Runs"))
        self.actionDelete_Runs = QtGui.QAction(MainWindow)
        self.actionDelete_Runs.setObjectName(_fromUtf8("actionDelete_Runs"))
        self.menuVDrive_2_0.addAction(self.actionFile_New)
        self.menuVDrive_2_0.addAction(self.action_OpenProject)
        self.menuVDrive_2_0.addAction(self.actionClose)
        self.menuVDrive_2_0.addSeparator()
        self.menuVDrive_2_0.addAction(self.action_SaveProject)
        self.menuVDrive_2_0.addAction(self.actionSave_As)
        self.menuVDrive_2_0.addSeparator()
        self.menuVDrive_2_0.addAction(self.actionQuit)
        self.menuVDrive_2_0.addSeparator()
        self.menuReduction.addAction(self.actionReduction_NewSetup)
        self.menuReduction.addAction(self.actionReset)
        self.menuReduction.addSeparator()
        self.menuReduction.addAction(self.actionLoad_Setup)
        self.menuReduction.addAction(self.actionSave_Setup)
        self.menuReduction.addSeparator()
        self.menuReduction.addAction(self.actionAdd_Runs)
        self.menuReduction.addAction(self.actionDelete_Runs)
        self.menuView.addAction(self.actionLog_Window)
        self.menubar.addAction(self.menuVDrive_2_0.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuReduction.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menuVDrive_2_0.setTitle(_translate("MainWindow", "File", None))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit", None))
        self.menuReduction.setTitle(_translate("MainWindow", "Reduction", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.treeWidget_Project.headerItem().setText(0, _translate("MainWindow", "Project", None))
        self.treeWidget_Project.headerItem().setText(1, _translate("MainWindow", "File", None))
        self.action_OpenProject.setText(_translate("MainWindow", "Open", None))
        self.action_OpenProject.setShortcut(_translate("MainWindow", "Ctrl+O", None))
        self.actionClose.setText(_translate("MainWindow", "Close", None))
        self.actionClose.setShortcut(_translate("MainWindow", "Ctrl+W", None))
        self.action_SaveProject.setText(_translate("MainWindow", "Save", None))
        self.action_SaveProject.setShortcut(_translate("MainWindow", "Ctrl+S", None))
        self.actionSave_As.setText(_translate("MainWindow", "Save As...", None))
        self.actionSave_As.setShortcut(_translate("MainWindow", "Ctrl+Shift+S", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionQuit.setShortcut(_translate("MainWindow", "Ctrl+Q", None))
        self.actionNewReduction.setText(_translate("MainWindow", "New", None))
        self.actionSave_Setup.setText(_translate("MainWindow", "Save Setup", None))
        self.actionFile_New_Reduction.setText(_translate("MainWindow", "Reduction Project", None))
        self.actionFile_New_Reduction.setToolTip(_translate("MainWindow", "New a Reduction Project", None))
        self.actionFile_New_Reduction.setShortcut(_translate("MainWindow", "Ctrl+N", None))
        self.actionAnalysis_Project.setText(_translate("MainWindow", "Analysis Project", None))
        self.actionReduction_NewSetup.setText(_translate("MainWindow", "Open Setup", None))
        self.actionReduction_NewSetup.setShortcut(_translate("MainWindow", "Ctrl+Shift+R", None))
        self.actionDelete.setText(_translate("MainWindow", "Delete", None))
        self.actionLoad_Setup.setText(_translate("MainWindow", "Load Setup", None))
        self.actionReset.setText(_translate("MainWindow", "Reset", None))
        self.actionLog_Window.setText(_translate("MainWindow", "Log Window", None))
        self.actionLog_Window.setShortcut(_translate("MainWindow", "Ctrl+L", None))
        self.actionFile_New.setText(_translate("MainWindow", "New", None))
        self.actionFile_New.setShortcut(_translate("MainWindow", "Ctrl+N", None))
        self.actionAdd_Runs.setText(_translate("MainWindow", "Add Runs", None))
        self.actionDelete_Runs.setText(_translate("MainWindow", "Delete Runs", None))

