# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_GPPlot.ui'
#
# Created: Mon Apr 20 17:24:26 2015
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

from MplFigureCanvas import *
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1338, 1005)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.labe_currentRun = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labe_currentRun.sizePolicy().hasHeightForWidth())
        self.labe_currentRun.setSizePolicy(sizePolicy)
        self.labe_currentRun.setObjectName(_fromUtf8("labe_currentRun"))
        self.gridLayout_3.addWidget(self.labe_currentRun, 0, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_3)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem1)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.comboBox_runs = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_runs.sizePolicy().hasHeightForWidth())
        self.comboBox_runs.setSizePolicy(sizePolicy)
        self.comboBox_runs.setObjectName(_fromUtf8("comboBox_runs"))
        self.horizontalLayout_7.addWidget(self.comboBox_runs)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.lineEdit_run = QtGui.QLineEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_run.sizePolicy().hasHeightForWidth())
        self.lineEdit_run.setSizePolicy(sizePolicy)
        self.lineEdit_run.setObjectName(_fromUtf8("lineEdit_run"))
        self.horizontalLayout_8.addWidget(self.lineEdit_run)
        self.pushButton_plot = QtGui.QPushButton(self.centralwidget)
        self.pushButton_plot.setObjectName(_fromUtf8("pushButton_plot"))
        self.horizontalLayout_8.addWidget(self.pushButton_plot)
        self.verticalLayout_2.addLayout(self.horizontalLayout_8)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.verticalLayout_2.addItem(spacerItem2)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.pushButton_prevView = QtGui.QPushButton(self.centralwidget)
        self.pushButton_prevView.setObjectName(_fromUtf8("pushButton_prevView"))
        self.horizontalLayout_6.addWidget(self.pushButton_prevView)
        self.pushButton_nextView = QtGui.QPushButton(self.centralwidget)
        self.pushButton_nextView.setObjectName(_fromUtf8("pushButton_nextView"))
        self.horizontalLayout_6.addWidget(self.pushButton_nextView)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.pushButton_cancel = QtGui.QPushButton(self.centralwidget)
        self.pushButton_cancel.setObjectName(_fromUtf8("pushButton_cancel"))
        self.horizontalLayout_4.addWidget(self.pushButton_cancel)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        spacerItem4 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        self.verticalLayout_2.addItem(spacerItem4)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_5 = QtGui.QVBoxLayout()
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.verticalLayout_6 = QtGui.QVBoxLayout()
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.graphicsView_mainPlot = Qt4MplPlotView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_mainPlot.sizePolicy().hasHeightForWidth())
        self.graphicsView_mainPlot.setSizePolicy(sizePolicy)
        self.graphicsView_mainPlot.setObjectName(_fromUtf8("graphicsView_mainPlot"))
        self.verticalLayout_6.addWidget(self.graphicsView_mainPlot)
        self.verticalLayout_5.addLayout(self.verticalLayout_6)
        self.verticalLayout_7 = QtGui.QVBoxLayout()
        self.verticalLayout_7.setObjectName(_fromUtf8("verticalLayout_7"))
        self.horizontalLayout_13 = QtGui.QHBoxLayout()
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.pushButton_4 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.horizontalLayout_13.addWidget(self.pushButton_4)
        self.verticalLayout_7.addLayout(self.horizontalLayout_13)
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.textEdit = QtGui.QTextEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textEdit.sizePolicy().hasHeightForWidth())
        self.textEdit.setSizePolicy(sizePolicy)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.gridLayout_2.addWidget(self.textEdit, 0, 0, 1, 1)
        self.verticalLayout_7.addLayout(self.gridLayout_2)
        self.verticalLayout_5.addLayout(self.verticalLayout_7)
        self.horizontalLayout.addLayout(self.verticalLayout_5)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.pushButton_normByCurrent = QtGui.QPushButton(self.centralwidget)
        self.pushButton_normByCurrent.setObjectName(_fromUtf8("pushButton_normByCurrent"))
        self.horizontalLayout_10.addWidget(self.pushButton_normByCurrent)
        self.verticalLayout_3.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pushButton_normByVanadium = QtGui.QPushButton(self.centralwidget)
        self.pushButton_normByVanadium.setObjectName(_fromUtf8("pushButton_normByVanadium"))
        self.horizontalLayout_2.addWidget(self.pushButton_normByVanadium)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.pushButton_normVacant = QtGui.QPushButton(self.centralwidget)
        self.pushButton_normVacant.setObjectName(_fromUtf8("pushButton_normVacant"))
        self.horizontalLayout_11.addWidget(self.pushButton_normVacant)
        self.verticalLayout_3.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.pushButton_stripVPeaks = QtGui.QPushButton(self.centralwidget)
        self.pushButton_stripVPeaks.setObjectName(_fromUtf8("pushButton_stripVPeaks"))
        self.horizontalLayout_9.addWidget(self.pushButton_stripVPeaks)
        self.verticalLayout_3.addLayout(self.horizontalLayout_9)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1338, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuTool = QtGui.QMenu(self.menubar)
        self.menuTool.setObjectName(_fromUtf8("menuTool"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionNormalize_to_Vanadium = QtGui.QAction(MainWindow)
        self.actionNormalize_to_Vanadium.setObjectName(_fromUtf8("actionNormalize_to_Vanadium"))
        self.actionNormalize_to_Proton_Charge = QtGui.QAction(MainWindow)
        self.actionNormalize_to_Proton_Charge.setObjectName(_fromUtf8("actionNormalize_to_Proton_Charge"))
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuTool.addAction(self.actionNormalize_to_Vanadium)
        self.menuTool.addAction(self.actionNormalize_to_Proton_Charge)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuTool.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.labe_currentRun.setText(_translate("MainWindow", "TextLabel", None))
        self.pushButton_plot.setText(_translate("MainWindow", "Plot", None))
        self.pushButton_prevView.setText(_translate("MainWindow", "Previous", None))
        self.pushButton_nextView.setText(_translate("MainWindow", "Next", None))
        self.pushButton_cancel.setText(_translate("MainWindow", "Cancel", None))
        self.pushButton_4.setText(_translate("MainWindow", "PushButton", None))
        self.pushButton_normByCurrent.setToolTip(_translate("MainWindow", "<html><head/><body><p>Normalize by proton charge</p></body></html>", None))
        self.pushButton_normByCurrent.setText(_translate("MainWindow", "Normalize By Current", None))
        self.pushButton_normByVanadium.setText(_translate("MainWindow", "Normalize By Vanadium", None))
        self.pushButton_normVacant.setText(_translate("MainWindow", "Normalize By ", None))
        self.pushButton_stripVPeaks.setText(_translate("MainWindow", "Strip Vanadium Peaks", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuTool.setTitle(_translate("MainWindow", "Tools", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionNormalize_to_Vanadium.setText(_translate("MainWindow", "Normalize to Vanadium", None))
        self.actionNormalize_to_Proton_Charge.setText(_translate("MainWindow", "Normalize to Proton Charge", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionQuit.setShortcut(_translate("MainWindow", "Ctrl+Q", None))

