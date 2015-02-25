####
# (Dialog) window for logs
####

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import ui.ui_AppLog

class MyAppLogDialog(QWidget):
    """
    """
    # Main
    def __init__(self, parent):
        """ Init
        """
        # Call base
        QWidget.__init__(self)

        # Parent
        self._myParent = parent

        # Set up widget
        self.ui = ui.ui_AppLog.Ui_Dialog()
        self.ui.setupUi(self)

        # Set up initial text
        self._myContent = "Welcome!\n\nHi, Dude!\n\n"
        self.ui.textBrowser_Log.setText(self._myContent)

    @QtCore.pyqtSlot(int)
    def setText(self, val):
        """
        """
        #Example: 
        #self.ui.textBrowser_Log.setHtml("""<body>
        #    <h1>Key</h1>
        #    <div style='color:red;'>
        #    GREEN = Overall Progress is 80% or above
        #    YELLOW = Overall Progress between 65%-79%
        #    Orange = Overall Progress is 64% or below
        #    </div>
        #    </body>"""
        #    )

        text = "Signal to add text:  Value = " + str(val) + "."

        self._myContent += text + "\n\n"

        # text = self._myParent.getLogText()
        self.ui.textBrowser_Log.setText(self._myContent)


        return


    def accept(self):
        """
        """
        self.close()


    def reject(self):
        """
        """
        self.close()

    def confirmExit(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
        "Are you sure to quit?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        if reply == QtGui.QMessageBox.Yes:
        #close application
            self.close()
        else:
        #do nothing and return
            pass     

    def closeEvent(self,event):
        #Here using an event handler to handle the case when the application is closed where the main app is informed that the child app has closed
        #Description for events can be found here: http://pyqt.sourceforge.net/Docs/PyQt4/qevent.html
        #The method name 'closeEvent' is formatted precisely as required in order to handle the application close event
        #See the QEvent Class Detailed Description for more information

        return
