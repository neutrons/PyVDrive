# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_ProjectNameDialog.ui'
#
# Created: Wed May  6 13:56:06 2015
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(554, 272)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout_2.addWidget(self.lineEdit)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.comboBox_projectTypes = QtGui.QComboBox(Dialog)
        self.comboBox_projectTypes.setObjectName(_fromUtf8("comboBox_projectTypes"))
        self.comboBox_projectTypes.addItem(_fromUtf8(""))
        self.comboBox_projectTypes.addItem(_fromUtf8(""))
        self.horizontalLayout_2.addWidget(self.comboBox_projectTypes)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.pushButton_newProject = QtGui.QPushButton(Dialog)
        self.pushButton_newProject.setObjectName(_fromUtf8("pushButton_newProject"))
        self.horizontalLayout_3.addWidget(self.pushButton_newProject)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem4)
        self.gridLayout.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.comboBox_deltaDays = QtGui.QComboBox(Dialog)
        self.comboBox_deltaDays.setObjectName(_fromUtf8("comboBox_deltaDays"))
        self.comboBox_deltaDays.addItem(_fromUtf8(""))
        self.comboBox_deltaDays.addItem(_fromUtf8(""))
        self.comboBox_deltaDays.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.comboBox_deltaDays)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label.setText(_translate("Dialog", "Project Name", None))
        self.comboBox_projectTypes.setItemText(0, _translate("Dialog", "Reduction Project", None))
        self.comboBox_projectTypes.setItemText(1, _translate("Dialog", "Analysis Project", None))
        self.pushButton_newProject.setText(_translate("Dialog", "Create Project", None))
        self.pushButton_2.setText(_translate("Dialog", "Cancel", None))
        self.label_2.setText(_translate("Dialog", "For auto-loading complete IPTS", None))
        self.comboBox_deltaDays.setItemText(0, _translate("Dialog", "Per Day", None))
        self.comboBox_deltaDays.setItemText(1, _translate("Dialog", "Per Week", None))
        self.comboBox_deltaDays.setItemText(2, _translate("Dialog", "Per Month", None))

