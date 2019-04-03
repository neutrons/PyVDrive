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
from pyvdrive.lib import vdrive_constants
import numpy as np
"""
Containing a set of "atomic" data viewers used by VIEW
"""


class PlotInformation(object):
    """
    Record as the information for plot
    """
    def __init__(self, ipts_number, run_number, chop_index, norm_pc, van_run):
        """
        constructor for plotting information
        :param ipts_number: IPTS number
        :param run_number: run number
        :param chop_index: chop sequence index
        :param norm_pc: flag to set the current proton charge normalization state
        :param van_run: flag to set the vanadium run normalization state
        """
        # check
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 9999999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 999999999))
        if chop_index is not None:
            datatypeutility.check_int_variable('Chop index', chop_index, (0, None))
        datatypeutility.check_bool_variable('Flag for proton charge normalization', norm_pc)
        if van_run is not None:
            datatypeutility.check_int_variable('Vanadium run number', van_run, (1, 99999999))

        self._ipts_number = ipts_number
        self._run_number = run_number
        self._chop_index = chop_index
        self._norm_by_pc = norm_pc   # normalized by proton charge
        self._vanadium_run_number = van_run

        return

    def get_info(self):
        """ get all the information
        :return: tuple as (ipts, run, chop index, norm_pc, van_run)
        """
        return self._ipts_number, self._run_number, self._chop_index, self._norm_by_pc, self._vanadium_run_number


class AtomicReduced1DViewer(QMainWindow):
    """ Class for 1D reduced data viewer
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # base class initialization
        super(AtomicReduced1DViewer, self).__init__(parent)
        self._parent = parent

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/SimpleReducedDataView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        # set X: no line edits for X range
        self._x_min = None
        self._x_max = None

        # set X
        self.ui.pushButton_setXRange.clicked.connect(self.do_set_x_range)
        self.ui.pushButton_setYRange.clicked.connect(self.do_set_y_range)
        self.ui.pushButton_removeLine.clicked.connect(self.do_remove_line)
        self.ui.pushButton_addLine.clicked.connect(self.do_add_line)

        # list of plot IDs for add/remove
        self._plot_id_dict = dict()  # [run, (chop-sq)] = plot ID
        self._plot_id_list = list()  # for any non-registered plot
        self._norm_proton_charge = False  # normalized by proton charge
        self._van_number = None  # normalized by vanadium or not

        self._run_ipts_map = dict()   # [run number] = IPTS number

        return

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

    def do_add_line(self):
        """ Add a line
        :return:
        """
        # get value
        ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, True)
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber, True)
        chop_seq_index = GuiUtility.parse_integer(self.ui.lineEdit_chopSeqIndex, True)
        bank_id = GuiUtility.parse_integer(self.ui.lineEdit_bankNumber, True)

        # check
        if run_number is None or run_number < 1:
            GuiUtility.pop_dialog_error(self, 'Run number must be specified as a positive integer')
            return
        if bank_id is None or bank_id < 1:
            GuiUtility.pop_dialog_error(self, 'Bank ID must be specified as a positive integer')
            return

        # check
        if chop_seq_index is None:
            plot_key = run_number, bank_id
        else:
            plot_key = run_number, chop_seq_index, bank_id

        # if exists, then give a notice
        if plot_key in self._plot_id_dict:
            GuiUtility.pop_dialog_information(self, 'Run {} Chop-seq {} has been plotted'
                                                    ''.format(run_number, chop_seq_index))
            return

        # get data
        if not self._parent.has_data_loaded(run_number, chop_seq_index):
            # load data explicitly
            # check IPTS information
            if ipts_number is None and run_number in self._run_ipts_map:
                # loaded run but different chop sequence
                ipts_number = self._run_ipts_map[run_number]
                self.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))
            elif ipts_number is None:
                # information not adequet
                GuiUtility.pop_dialog_error(self, 'Run {} has not been loaded; Specify IPTS'
                                                  ''.format(run_number))
                return
            # END-IF-ELSE

            # load data via parent window
            try:
                # need to convert chop-sequence-index to list
                if chop_seq_index is not None:
                    chop_seq_index_list = [chop_seq_index]
                else:
                    chop_seq_index_list = None
                # load data
                self._parent.load_reduced_data(ipts_number, run_number, chop_seq_index_list)
                self._run_ipts_map[run_number] = ipts_number
                vdrive_constants.run_ipts_dict[run_number] = ipts_number
            except RuntimeError as run_err:
                if chop_seq_index is None:
                    chop_note = 'original GSAS'
                else:
                    chop_note = 'chopped run {}'.format(chop_seq_index)
                GuiUtility.pop_dialog_error(self, 'Unable to load {} of IPTS {} Run {}: '
                                                  ''.format(chop_note, ipts_number, run_number,
                                                            run_err))
                return
            # END-TRY-Catch
        elif ipts_number is None:
            # set the IPTS even the data has been loaded
            ipts_number = vdrive_constants.run_ipts_dict[run_number]
        # END-IF-ELSE

        try:
            data_key = self._parent.get_data_key(run_number, chop_seq_index)
            vec_x, vec_y = self._parent.retrieve_loaded_reduced_data(data_key, ipts_number, run_number,
                                                                     chop_seq_index, bank_id, unit='dSpacing',
                                                                     pc_norm=self._norm_proton_charge,
                                                                     van_run=self._van_number)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, 'Unable to retrieve data from Run {} Bank {} due to {}'
                                              ''.format(run_number, bank_id, run_err))
            return

        # plot
        plot_information = PlotInformation(ipts_number, run_number, chop_seq_index, self._norm_proton_charge,
                                           self._van_number)
        self.plot_data(vec_x, vec_y, 'data key', unit=None, bank_id=bank_id, plot_info=plot_information)

        return

    # TODO - TODAY 191 - Test new feature
    def do_remove_line(self):
        """ Remove a line
        :return:
        """
        # get value
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber, True)
        chop_seq_index = GuiUtility.parse_integer(self.ui.lineEdit_chopSeqIndex, True)
        bank_id = GuiUtility.parse_integer(self.ui.lineEdit_bankNumber, True)

        # check
        if run_number is None or run_number < 1:
            GuiUtility.pop_dialog_error(self, 'Run number must be specified as a positive integer')
            return
        if bank_id is None or bank_id < 1:
            GuiUtility.pop_dialog_error(self, 'Bank ID must be specified as a positive integer')
            return

        # check
        if chop_seq_index is None:
            plot_key = run_number, bank_id
        else:
            plot_key = run_number, chop_seq_index, bank_id

        # remove the line
        if plot_key in self._plot_id_dict:
            self.ui.graphicsView_mainPlot.remove_line(self._plot_id_dict[plot_key])
            del self._plot_id_dict[plot_key]
        else:
            GuiUtility.pop_dialog_error(self, 'Run {} Chop-Seq {} is not in figure to delete'
                                              ''.format(run_number, chop_seq_index))

        return

    def do_set_x_range(self):
        """ Set image X range from line edits
        :return:
        """
        min_x = GuiUtility.parse_float(self.ui.lineEdit_xMin, True, 0.)
        max_x = GuiUtility.parse_float(self.ui.lineEdit_xMax, True, 3.5)
        if min_x >= max_x:
            GuiUtility.pop_dialog_error(self, 'Lower X limit {} cannot be equal to or larger than upper X limit {}'
                                              ''.format(min_x, max_x))
            return

        self._x_min = min_x
        self._x_max = max_x
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=self._x_min, xmax=self._x_max)

        return

    def do_set_y_range(self):
        """ Set image X range from line edits
        :return:
        """
        y_min = GuiUtility.parse_float(self.ui.lineEdit_yMin, True, 0.)
        y_max = GuiUtility.parse_float(self.ui.lineEdit_yMax, True, None)
        if y_min >= y_max:
            GuiUtility.pop_dialog_error(self, 'Lower Y limit {} cannot be equal to or larger than upper Y limit {}'
                                              ''.format(y_min, y_max))
            return

        self.ui.graphicsView_mainPlot.setXYLimit(ymin=y_min, ymax=y_max)

        return

    # INFORMATION
    # TODO - TODAY 191 - TEST
    def plot_data(self, vec_x, vec_y, data_key, unit, bank_id, plot_info):
        """ Plot 1D diffraction data
        :param vec_x:
        :param vec_y:
        :param data_key: data key (just for information)
        :param unit: Unit (just as information)
        :param bank_id: bank ID (just as information)
        :param plot_info: PlotInformation object
        :return:
        """
        # check inputs
        assert isinstance(plot_info, PlotInformation), 'Input plotting information {} must be an instance of ' \
                                                       'PlotInformation but not {}' \
                                                       ''.format(plot_info, type(plot_info))

        ipts_number, run_number, chop_seq_index, self._norm_proton_charge, self._van_number = plot_info.get_info()

        vdrive_constants.run_ipts_dict[run_number] = ipts_number
        self._run_ipts_map[run_number] = ipts_number

        line_label = 'Run {}'.format(run_number)
        if chop_seq_index:
            line_label += ' Chop-index {}'.format(chop_seq_index)
        line_label += ' Bank {}'.format(bank_id)

        plot_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y),
                                                                      unit=unit, over_plot=True,
                                                                      run_id=data_key, bank_id=bank_id,
                                                                      chop_tag=None,
                                                                      label=line_label)
        # register
        if run_number is None:
            self._plot_id_list.append(plot_id)
        elif chop_seq_index is None:
            self._plot_id_dict[run_number, bank_id] = plot_id
        else:
            self._plot_id_dict[run_number, chop_seq_index, bank_id] = plot_id

        self.ui.lineEdit_runNumber.setText('{}'.format(run_number))

        # set X
        self.do_set_x_range()

        return

    def set_x_range(self, min_x, max_x):
        """
        set range on X-axis
        :param min_x:
        :param max_x:
        :return:
        """
        datatypeutility.check_float_variable('Lower limit of X for plot', min_x, (None, None))
        datatypeutility.check_float_variable('Upper limit of X for plot', max_x, (None, None))
        if min_x >= max_x:
            raise RuntimeError('Lower X limit {} cannot be equal to or larger than upper X limit {}'
                               ''.format(min_x, max_x))

        self._x_min = min_x
        self._x_max = max_x

        self.ui.lineEdit_xMin.setText('{}'.format(min_x))
        self.ui.lineEdit_xMax.setText('{}'.format(max_x))

        return

    def set_title(self, title):
        """
        Set title of the plot
        :param title:
        :return:
        """
        datatypeutility.check_string_variable('Plot title', title)
        self.label_title.setText(title)


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

        self.ui.pushButton_setXrange.clicked.connect(self.do_set_x_range)

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

    def do_set_x_range(self):
        """ Set image X range from line edits
        :return:
        """
        x_min = GuiUtility.parse_float(self.ui.lineEdit_xMin, True, 0.25)
        x_max = GuiUtility.parse_float(self.ui.lineEdit_xMax, True, 3.50)

        self.ui.graphicsView_mainPlot.setXYLimit(xmin=x_min, xmax=x_max)

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
            matrix_y[i] = data_set_list[i][1]

        n = len(y_indexes)
        vec_y = np.ndarray(shape=(n,), dtype='int')
        for i in range(n):
            vec_y[i] = y_indexes[i]

        self.ui.graphicsView_mainPlot.canvas.add_contour_plot(vec_x, np.array(y_indexes), matrix_y)

        return

    def set_x_range(self, min_x, max_x):
        """
        Set X range
        :param min_x:
        :param max_x:
        :return:
        """
        if min_x is not None:
            self.ui.lineEdit_xMin.setText('{}'.format(min_x))
        if max_x is not None:
            self.ui.lineEdit_xMax.setText('{}'.format(max_x))

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

    def plot_runs_3d(self, sequences, data_set_list):

        # data_set_list:  list of vec X and vec Y
        assert len(sequences) == len(data_set_list), 'blabla not equal'

        # convert
        line_points = data_set_list[0][0].size
        line_number = len(sequences)

        sequence_vec = np.array(sequences)
        matrix_shape = line_number, line_points

        sequence_matrix = np.ndarray(matrix_shape, dtype='float')
        vec_x_matrix = np.ndarray(matrix_shape, dtype='float')
        vec_y_matrix = np.ndarray(matrix_shape, dtype='float')

        for i in range(line_number):
            sequence_matrix[i] = sequence_vec[i]
            vec_x_matrix[i] = data_set_list[i][0]
            vec_y_matrix[i] = data_set_list[i][1]
        # END-FOR(i)

        flatten_vec_seq = sequence_matrix.flatten()
        flatten_vec_x = vec_x_matrix.flatten()
        flatten_vec_y = vec_y_matrix.flatten()

        self.ui.graphicsView_mainPlot.plot_surface_lines(flatten_vec_seq, flatten_vec_x, flatten_vec_y)

        return
