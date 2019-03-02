import numpy as np
import mplgraphicsview
import mplgraphicsview2d
import mplgraphicsview3d


class GeneralRunView(mplgraphicsview.MplGraphicsView):
    """

    """
    ColorList = ['black', 'red', 'blue', 'green', 'yellow']
    BankMarkList = [None, None, None, '.', 'D', '*']  # user prefer uniform marker

    def __init__(self, parent):
        """
        An extension to the MplGraphicsView for plotting reduced run
        :param parent:
        """
        super(GeneralRunView, self).__init__(parent)

        # class state variables
        self._plotDimension = 1
        self._plotType = None

        # dictionary and etc for current line IDs
        # self._linesDict = dict()  : don't know how to deal with it!
        self._onCanvasIDList = list()
        self._currLineID = None

        # mode for diffraction (d) or sample logs (s)
        self._dataMode = None

        # a record for min and max X and Y
        self._maxX = None
        self._maxY = None

        # color index
        self._diffColorID = 0

        # 1D/2D flag
        self._has2DImage = False

        return

    def _get_next_diffraction_color(self, bank_id=None):
        """
        get the next color. if bank ID is present, then use color dedicated for that bank
        :param bank_id:
        :return:
        """
        # check
        if bank_id is None:
            color = GeneralRunView.ColorList[self._diffColorID]
            self._diffColorID = (self._diffColorID + 1) % len(GeneralRunView.ColorList)
        elif isinstance(bank_id, int):
            color = GeneralRunView.ColorList[bank_id % len(GeneralRunView.ColorList)]
        else:
            raise AssertionError('Bank ID {0} must be either integer or None'.format(bank_id))

        return color

    @staticmethod
    def _get_diffraction_marker(bank_id):
        """

        :return:
        """
        assert bank_id < len(GeneralRunView.BankMarkList), 'Bank ID {0} is out of range {1} of BankMarkList.' \
                                                           ''.format(bank_id, len(GeneralRunView.BankMarkList))

        return GeneralRunView.BankMarkList[bank_id]

    def plot_1d_data(self, vec_x, vec_y, x_unit, label, line_color, marker='.', title=None):
        """
        plot a 1-D data set
        :param vec_x:
        :param vec_y:
        :param x_unit:
        :param label:
        :param line_key:
        :param title:
        :param line_color
        :return:
        """
        if self._has2DImage:
            self.reset_2d_plots()

        print ('[DB...BAT] Plot 1D: size vecX = {}, size vecY = {}'.format(len(vec_x), len(vec_y)))

        # draw line
        line_id = self.add_plot_1d(vec_x=vec_x, vec_y=vec_y,
                                   label=label, x_label=x_unit,
                                   marker=marker, color=line_color)

        # add to title
        if title is not None:
            self.set_title(title)

        # record statistics
        if self._maxX is None or vec_x[-1] > self._maxX:
            self._maxX = vec_x[-1]

        if self._maxY is None or np.max(vec_y) > self._maxY:
            self._maxY = np.max(vec_y)

        return line_id

    def plot_diffraction_data(self, vec_xy_set, unit, run_id, bank_id, over_plot, label, line_color=None,
                              chop_tag=None):
        """
        plot diffraction data with proper unit... 1D
        :param vec_xy_set:
        :param unit:
        :param over_plot:
        :param run_id: information string
        :param chop_tag: information string
        :return:
        """
        # data mode blabla
        if self._dataMode != 'd':
            self.reset_1d_plots()
            self._dataMode = 'd'

        # get vectors
        vec_x = vec_xy_set[0]
        vec_y = vec_xy_set[1]

        # take are of label
        line_label = "{} Run {} Bank {}".format(label, run_id, bank_id)

        # process the current image
        if not over_plot:
            self.reset_1d_plots()

        # color & marker
        if line_color is None:
            line_color = self._get_next_diffraction_color(bank_id)
        line_marker = self._get_diffraction_marker(bank_id)

        if chop_tag is not None:
            title = 'Run {0} Chop Tag {1}'.format(run_id, chop_tag)
            self.set_title(title, 'blue')

        # plot 1D diffraction data
        self._currLineID = self.plot_1d_data(vec_x, vec_y, x_unit=unit, label=line_label,
                                             line_color=line_color, marker=line_marker,)
        self._onCanvasIDList.append(self._currLineID)

        # re-scale
        self.auto_rescale(vec_y)

        return self._currLineID

    def plot_2d_contour(self, run_number_list, data_set_list):
        """
        plot 2D contour figure
        :param run_number_list:
        :param data_set_list:
        :return:
        """
        # check
        size_set = set()
        for data_set in data_set_list:
            vec_x, vec_y = data_set
            assert len(vec_x) == len(vec_y), 'Size of vector X (%d) and vector Y (%d) must be same!' % (len(vec_x), len(vec_y))
            size_set.add(len(vec_x))
        # END-FOR
        assert len(size_set) == 1, 'All the reduced data must have equal sizes but not %s.' % str(size_set)
        vec_x = data_set_list[0][0]

        # build mesh
        grid_x, grid_y = np.meshgrid(vec_x, run_number_list)

        matrix_y = np.ndarray(grid_x.shape, dtype='float')
        for i in range(len(run_number_list)):
            matrix_y[:i] = data_set_list[i][1]

        n = len(run_number_list)
        vec_y = np.ndarray(shape=(n,), dtype='int')
        for i in range(n):
            vec_y[i] = run_number_list[i]

        self.canvas().add_contour_plot(vec_x, np.array(run_number_list), matrix_y)

        # 2D image
        self._has2DImage = True

        return

    def set_dimension_type(self, target_dim, target_type):
        """
        set dimension and type
        :param target_dim:
        :param target_type:
        :return:
        """
        # check
        assert isinstance(target_dim, int) and 1 <= target_dim <= 3, 'Target dimension must be an integer between 1 and 3.'

        # clear current canvas
        self.clear_canvas()

        # set the target dimension
        self._plotDimension = target_dim
        self._plotType = target_type

        return

    def reset_1d_plots(self):
        """
        reset all 1D plots
        :return:
        """
        # clear all lines
        self.clear_all_lines()

        # clear dictionary
        # self._linesDict.clear()
        self._currLineID = None
        self._onCanvasIDList = list()

        self._diffColorID = 0

        # reset X and Y
        self._maxX = None
        self._maxY = None

        return

    def reset_2d_plots(self):
        """

        :return:
        """
        self.clear_canvas()
        self._has2DImage = False


class ContourPlotView(mplgraphicsview2d.MplGraphicsView2D):
    """
    Contour plot 2D view
    """
    def __init__(self, parent):
        """
        An extension to the MplGraphicsView for plotting reduced run
        :param parent:
        """
        super(ContourPlotView, self).__init__(parent)

        # class state variables

        return

    def plot_2d_contour(self, run_number_list, data_set_list):
        """
        plot 2D contour figure
        :param run_number_list:
        :param data_set_list:
        :return:
        """
        # check
        size_set = set()
        for data_set in data_set_list:
            vec_x, vec_y = data_set
            assert len(vec_x) == len(vec_y), 'Size of vector X (%d) and vector Y (%d) must be same!' % (len(vec_x), len(vec_y))
            size_set.add(len(vec_x))
        # END-FOR
        assert len(size_set) == 1, 'All the reduced data must have equal sizes but not %s.' % str(size_set)
        vec_x = data_set_list[0][0]

        # build mesh
        grid_x, grid_y = np.meshgrid(vec_x, run_number_list)

        matrix_y = np.ndarray(grid_x.shape, dtype='float')
        for i in range(len(run_number_list)):
            matrix_y[:i] = data_set_list[i][1]

        n = len(run_number_list)
        vec_y = np.ndarray(shape=(n,), dtype='int')
        for i in range(n):
            vec_y[i] = run_number_list[i]

        self.canvas().add_contour_plot(vec_x, np.array(run_number_list), matrix_y)

        # 2D image
        self._has2DImage = True

        return


class LinePlot3DView(mplgraphicsview3d.MplPlot3dCanvas):
    """

    """
    def __init__(self, parent):
        super(LinePlot3DView, self).__init__(parent)

        return

    def plot_runs(self):

        self.plot_surface_prototype()

