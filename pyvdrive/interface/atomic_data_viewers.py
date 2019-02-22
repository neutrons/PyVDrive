import os
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QMainWindow, QFileDialog
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5 import QtCore
except ImportError:
    from PyQt4.QtGui import QMainWindow, QFileDialog
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4 import QtCore
from gui import GuiUtility
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

from pyvdrive.interface.gui.generalrunview import GeneralRunView
from pyvdrive.interface.gui.generalrunview import ContourPlotView
from pyvdrive.lib import datatypeutility
"""
Containing a set of "atomic" data viewers used by VIEW
"""


class AtomicReduced1DViewer(QMainWindow):
    """ Class for 1D reduced data viewer
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # base class initialization
        super(AtomicReduced1DViewer, self).__init__(parent)

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/SimpleReducedDataView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

    def _promote_widgets(self):
        """
        promote widgets
        :return:
        """
        graphicsView_mainPlot_layout = QVBoxLayout()
        self.ui.frame_mainPlot.setLayout(graphicsView_mainPlot_layout)
        self.ui.graphicsView_mainPlot = GeneralRunView(self)
        graphicsView_mainPlot_layout.addWidget(self.ui.graphicsView_mainPlot)

        return

    def plot_data(self, vec_x, vec_y):

        self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit='dSapcing',
                                                                      over_plot=False,
                                                                      run_id='ID', bank_id=1,
                                                                      chop_tag=None,
                                                                      label='whatever')

        return


class AtomicReduction2DViewer(QMainWindow):
    """ Class for 2D reduced data viewer
    """
    def __init__(self, parent=None):
        """
        Init
        :param parent:
        """
        super(AtomicReduction2DViewer, self).__init__(parent)

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), 'gui/Simple2DReductionView.ui')
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promte_widgets()

        return

    def _promote_widgets(self):
        """
        promote widgets
        :return:
        """
        graphicsView_mainPlot_layout = QVBoxLayout()
        self.ui.frame_mainPlot.setLayout(graphicsView_mainPlot_layout)
        self.ui.graphicsView_mainPlot = ContourPlotView(self)
        graphicsView_mainPlot_layout.addWidget(self.ui.graphicsView_mainPlot)

        return

    def plot_data(self, vec_x, vec_y):

        self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit='dSapcing',
                                                                      over_plot=False,
                                                                      run_id='ID', bank_id=1,
                                                                      chop_tag=None,
                                                                      label='whatever')
