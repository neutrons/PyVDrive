from PyQt4 import QtCore, QtGui
import gui.ui_LiveDataGPPlotSetup_ui as dialog_ui


class SampleLogPlotSetupDialog(QtGui.QDialog):
    """
    blabla
    """
    def __init__(self, parent=None):
        """
        blabla
        :param parent:
        """
        super(SampleLogPlotSetupDialog, self).__init__(parent)

        self.ui = dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # link
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

        return

    def do_quit(self):
        """
        blabla
        :return:
        """
        self.close()
