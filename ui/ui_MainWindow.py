# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_MainWindow.ui'
#
# Created: Thu Jan 29 17:16:45 2015
#      by: PyQt4 UI code generator 4.11.2
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
        MainWindow.resize(1027, 814)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1027, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuVDrive_2_0 = QtGui.QMenu(self.menubar)
        self.menuVDrive_2_0.setObjectName(_fromUtf8("menuVDrive_2_0"))
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuReduction = QtGui.QMenu(self.menubar)
        self.menuReduction.setObjectName(_fromUtf8("menuReduction"))
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
        self.treeView = QtGui.QTreeView(self.dockWidgetContents)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.horizontalLayout.addWidget(self.treeView)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.dock_.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dock_)
        self.actionNew = QtGui.QAction(MainWindow)
        self.actionNew.setObjectName(_fromUtf8("actionNew"))
        self.actionOpen = QtGui.QAction(MainWindow)
        self.actionOpen.setObjectName(_fromUtf8("actionOpen"))
        self.actionClose = QtGui.QAction(MainWindow)
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionSave_As = QtGui.QAction(MainWindow)
        self.actionSave_As.setObjectName(_fromUtf8("actionSave_As"))
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionNewReduction = QtGui.QAction(MainWindow)
        self.actionNewReduction.setObjectName(_fromUtf8("actionNewReduction"))
        self.actionSave_Setup = QtGui.QAction(MainWindow)
        self.actionSave_Setup.setObjectName(_fromUtf8("actionSave_Setup"))
        self.menuVDrive_2_0.addAction(self.actionNew)
        self.menuVDrive_2_0.addAction(self.actionOpen)
        self.menuVDrive_2_0.addAction(self.actionClose)
        self.menuVDrive_2_0.addSeparator()
        self.menuVDrive_2_0.addAction(self.actionSave)
        self.menuVDrive_2_0.addAction(self.actionSave_As)
        self.menuVDrive_2_0.addSeparator()
        self.menuVDrive_2_0.addAction(self.actionQuit)
        self.menuReduction.addAction(self.actionNewReduction)
        self.menuReduction.addAction(self.actionSave_Setup)
        self.menubar.addAction(self.menuVDrive_2_0.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuReduction.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menuVDrive_2_0.setTitle(_translate("MainWindow", "File", None))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit", None))
        self.menuReduction.setTitle(_translate("MainWindow", "Reduction", None))
        self.actionNew.setText(_translate("MainWindow", "New", None))
        self.actionOpen.setText(_translate("MainWindow", "Open", None))
        self.actionClose.setText(_translate("MainWindow", "Close", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionSave_As.setText(_translate("MainWindow", "Save As...", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionNewReduction.setText(_translate("MainWindow", "New", None))
        self.actionSave_Setup.setText(_translate("MainWindow", "Save Setup", None))

