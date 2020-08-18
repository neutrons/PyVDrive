####
# (Dialog) window for logs
####

try:
    import qtconsole.inprocess
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QMessageBox
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QMessageBox


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


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
        ui_path = os.path.join(os.path.dirname(__file__), "gui/import.ui")
        self.ui = load_ui(ui_path, baseinstance=self)

        # Set up initial text
        self._myContent = "Welcome!\n\nHi, Dude!\n\n"
        self.ui.textBrowser_Log.setText(self._myContent)

    @QtCore.pyqtSlot(int)
    def setText(self, val):
        """
        """
        # Example:
        # self.ui.textBrowser_Log.setHtml("""<body>
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
        """
        pop out the dialog to confirm existing
        :return:
        """
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # close application
            self.close()
        else:
            # do nothing and return
            pass

    def closeEvent(self, event):
        """
        handling an event calling to close widnow
        :param event:
        :return:
        """
        # Here using an event handler to handle the case when the application is closed
        # where the main app is informed that the child app has closed
        # Description for events can be found here: http://pyqt.sourceforge.net/Docs/PyQt4/qevent.html
        # The method name 'closeEvent' is formatted precisely as required in order
        # to handle the application close event
        # See the QEvent Class Detailed Description for more information

        return
