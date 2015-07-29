########################################################
# Beta Version: Add runs
########################################################
import os

from PyQt4 import QtGui, QtCore

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import DialogAddRunsIPTS as dlgrun

class AddRunsByIPTSDialog(QtGui.QDialog):
    """ Pop up dialog window to add runs by IPTS
    """
    def __init__(self, parent):
        """ Init
        """
        QtGui.QDialog.__init__(self)

        # Parent
        self._myParent = parent
        self.quit = False

        # Set up widgets
        self.ui = dlgrun.Ui_Dialog()
        self.ui.setupUi(self)

        # Init
        self.ui.radioButton_useNumber.setChecked(True)

        # Set event handler
        QtCore.QObject.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
                self.do_browse_ipts_folder)

        QtCore.QObject.connect(self.ui.pushButton_verify, QtCore.SIGNAL('clicked()'),
                self.do_verify_ipts_folder)

        QtCore.QObject.connect(self.ui.buttonBox_okAdd, QtCore.SIGNAL('accepted()'),
                               self.do_save_quit)

        QtCore.QObject.connect(self.ui.buttonBox_okAdd, QtCore.SIGNAL('rejected'),
                               self.do_reject_quit)

        # Data set
        self._iptsDir = ''

        return


    def do_browse_ipts_folder(self):
        """
        :return:
        """
        # TODO Doc
        home = '/home/wzz'

        iptsdir = str(QtGui.QFileDialog.getExistingDirectory(self,'Get Directory',home))
        self.ui.lineEdit_iptsDir.setText(iptsdir)

        return

    def do_verify_ipts_folder(self):
        """

        :return:
        """
        # TODO Doc
        if self.ui.radioButton_useNumber.isChecked():
            ipts = int(self.ui.lineEdit_iptsNumber.text())
            self._iptsDir = os.path.join('/SNS/VULCAN', 'IPTS-%d'%(ipts))
        elif self.ui.radioButton_useDir.isChecked():
            self._iptsDir = str(self.ui.lineEdit_iptsDir.text())
        else:
            # FIXME - Warning Popup
            print "[Pop] Not set up correctly!"

        return


    def do_save_quit(self):
        """

        :return:
        """
        # TODO Doc

        # FIXME - Message Pop-up
        print "[Pop] Not set up and quit?"

        return

    def do_reject_quit(self):
        """ Quit and abort the operation
        """
        print "Cancel and Quit"
        self.quit = True

        return


    def get_ipts_dir(self):
        """

        :return:
        """
        return self._iptsDir


""" Test Main """
if __name__=="__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = AddRunsByIPTSDialog(None)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)