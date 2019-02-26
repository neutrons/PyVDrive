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
from pyvdrive.interface.gui.generalrunview import LinePlot3DView
from pyvdrive.lib import datatypeutility
import numpy as np
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

    def plot_data(self, vec_x, vec_y, data_key, unit, bank_id):
        """ Plot 1D diffraction data
        :param vec_x:
        :param vec_y:
        :param data_key: data key
        :param unit: Unit (just as information)
        :param bank_id: bank ID (just as information)
        :return:
        """
        self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y),
                                                            unit=unit, over_plot=False,
                                                            run_id=data_key, bank_id=bank_id,
                                                            chop_tag=None, label='{} {}'.format(data_key, bank_id))

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
        self._promote_widgets()

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

    def plot_contour(self, y_indexes, data_set_list):
        """
        plot 2D contour figure
        :param y_indexes: Indexes for Y axis.  It can be (1) run numbers  (2) chop sequences
        :param data_set_list:
        :return:
        """
        # check
        datatypeutility.check_list('Y axis indexes', y_indexes)

        size_set = set()
        for data_set in data_set_list:
            vec_x, vec_y = data_set
            assert len(vec_x) == len(vec_y), 'Size of vector X (%d) and vector Y (%d) must be same!' % (len(vec_x), len(vec_y))
            size_set.add(len(vec_x))
        # END-FOR
        assert len(size_set) == 1, 'All the reduced data must have equal sizes but not %s.' % str(size_set)
        vec_x = data_set_list[0][0]

        # build mesh
        grid_x, grid_y = np.meshgrid(vec_x, y_indexes)

        matrix_y = np.ndarray(grid_x.shape, dtype='float')
        for i in range(len(y_indexes)):
            matrix_y[:i] = data_set_list[i][1]

        n = len(y_indexes)
        vec_y = np.ndarray(shape=(n,), dtype='int')
        for i in range(n):
            vec_y[i] = y_indexes[i]

        self.ui.graphicsView_mainPlot.canvas.add_contour_plot(vec_x, np.array(y_indexes), matrix_y)

        return


class AtomicReduction3DViewer(QMainWindow):
    """ Class for 2D reduced data viewer
    """
    def __init__(self, parent=None):
        """
        Init
        :param parent:
        """
        super(AtomicReduction3DViewer, self).__init__(parent)

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), 'gui/Simple2DReductionView.ui')
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        return

    def _promote_widgets(self):
        """
        promote widgets
        :return:
        """
        graphicsView_mainPlot_layout = QVBoxLayout()
        self.ui.frame_mainPlot.setLayout(graphicsView_mainPlot_layout)
        self.ui.graphicsView_mainPlot = LinePlot3DView(self)
        graphicsView_mainPlot_layout.addWidget(self.ui.graphicsView_mainPlot)

        return

    def plot_prototype(self):
        self.ui.graphicsView_mainPlot.plot_runs()
