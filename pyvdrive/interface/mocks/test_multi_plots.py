from mplgraphicsview1d import MplGraphicsView1D
from PyQt4 import QtGui, QtCore
import sys
import ui_multplot_test


class MultiPlotsTester(QtGui.QMainWindow):
    """
    Launcher manager
    """
    def __init__(self):
        """

        """
        super(MultiPlotsTester, self).__init__(None)

        # set up UI
        self.ui = ui_multplot_test.Ui_MainWindow()
        self.ui.setupUi(self)

        # self.ui.graphicsView_multiPlot.setup(2, 1)

        self.connect(self.ui.pushButton_setSubPlots, QtCore.SIGNAL('clicked()'),
                     self.set_plots)

        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.do_plot)

        return

    def set_plots(self):
        """

        :return:
        """
        row_size = int(self.ui.lineEdit_rows.text())
        col_size = int(self.ui.lineEdit_columns.text())

        self.ui.graphicsView_multiPlot.setup(row_size, col_size)

        self.ui.graphicsView_multiPlot.draw()

    def do_plot(self):
        """

        :return:
        """
        row_index = int(self.ui.lineEdit_plotRowIndex.text())
        col_index = int(self.ui.lineEdit_plotColIndex.text())

        import numpy

        vec_x = numpy.arange(0, 10, 0.01)
        vec_y = (row_index+1) * numpy.sin(vec_x) + col_index

        # conclusion: (0, 0) up-left corner (0, 1) up-right corner, (1, 0) lower_right corner

        self.ui.graphicsView_multiPlot.add_plot(vec_x, vec_y, row_index=row_index, col_index=col_index)


# Main
# Main application
def tester_app():
    if QtGui.QApplication.instance():
        _app = QtGui.QApplication.instance()
    else:
        _app = QtGui.QApplication(sys.argv)
    return _app

# get arguments
args = sys.argv

app = tester_app()

tester = MultiPlotsTester()
tester.show()

app.exec_()
